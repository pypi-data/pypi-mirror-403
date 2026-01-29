"""
client.py
====================================
The core module provides access to the WDC-API. 
It provides a consistent interface for handling 
the data as JSON, DataFrame or Graph and transparently handles 
paging for large result-sets.
"""

import requests
import logging
import os
import sys
import time
import json
import json_stream
from pathlib import Path
from typing import Any
from collections.abc import Callable
import networkx as nx

import pandas as pd
from dotenv.main import load_dotenv

class WDCException(Exception):
    """
    An exception which is raised when an error within the WDCClient 
    occurs.
    """
    
    def __init__(self, message, query = None, state = None):
        super().__init__(message)
        self.query = query
        self.state = state;
        
    def __str__(self):
        return (
            super().__str__() +
            ", query: " + self.query + 
            ", state: " + self.state)

class WDCClient: 
    """
    Client for the WDC-API.
    """
    
    @staticmethod
    def fromEnv():
        """
        Creates a WDCClient from the 'Environment'. 
        
        Uses the environment variables 'WDC_HOST' and 'WDC_TOKEN' from the current
        environment. Thus, you can make use of modules such as python-dotenv
        or other variants more easily.
        
        If the WDC_HOST has not been previously set, the method tries to load 
        the configuration from "~/.wdc". This allows a easy central setup 
        for the configuration without the risk of exposing the config-file 
        in a git-/cloud-repository. 
        
        Remember: Using passwords or tokens in source code is dangerous!
        
        :return: A new WDCClient configured from the environment values.
        """
        logger = logging.getLogger(__name__)
       
        # 2. ~/.wdc
        loaded = WDCClient._loadEnvironment(Path(Path.home(), ".wdc"))
            
        _host = os.getenv('WDC_HOST')
        _token = os.getenv('WDC_TOKEN')
                
        logger.info(f"Creating WDCClient with: host = {_host}, token = {_token}") 
        
        client = WDCClient(host = _host, token = _token)
        
        return client
    
    @staticmethod
    def _loadEnvironment(file: Path) -> bool:
        logger = logging.getLogger(__name__)
        
        if not os.getenv('WDC_HOST'):
            logger.info("WDC_HOST not set. Trying: " + str(file))
            
            if file.exists():
                logger.info("Loading WDC-Config from: " + str(file))
                load_dotenv(str(file))
                return True
            
        return False

    def __init__(self, host: str, token = None):
        self.logger = logging.getLogger(__name__)
        self.host = host 
        self.token = token
        
        if self.host == None:
            raise WDCException("Could not create WDCClient with host = None")
        
        self.session = requests.Session()
        if self.token != None: 
            self.session.headers.update({'token': self.token})
            
    def loadAsDF(self, endpoint: str, **params) -> pd.DataFrame:
        """
        Short-Cut for loadAsDataFrame with keyword arguments to 
        specify the parameters for the endpoint. Same as 
        calling self.loadAsDataFrame(endpoint, params)
        """
        return self.loadAsDataFrame(endpoint, params) 
        
    def loadAsDataFrame(self, endpoint: str, params: dict[str, Any] = {}) -> pd.DataFrame:
        """
        Loads the *complete* tabular data from the endpoint and returns a 
        Pandas-DataFrame. The method transparently pages through the
        complete results.
        
        :param endpoint: the endpoint
        :param params: a dictionary with possible parameters for the 
            query-string of the request. Values will be properly encoded.
            A param named 'body' will be sent as BODY in a GET-Request.
        
        :return: the data as Pands-DataFrame
        """ 
        jsonRes = self.loadAsJson(endpoint, params);
        
        return pd.json_normalize(jsonRes)
    
    def loadAsJson(self, endpoint: str, params: dict[str, Any] = {}) -> []:
        """
        Loads the tabular data from the endpoint and returns it as 
        JSON-Array. The method transparently pages through the
        complete results.
        
        :param endpoint: the endpoint
        :param params: a dictionary with possible parameters for the 
            query-string of the request. Values will be properly encoded.
        
        :return: the data as JSON-Array
        """
        res = []
        
        def collect_it(e, pos, maxPos):
            nonlocal res
            res.append(e)
            
        self.loadForEach(endpoint, params, collect_it)
        
        return res
        
    def loadForEach(self, endpoint: str, params: dict[str, Any] = {}, f: Callable[[Any, int, int], None] = None) -> None:
        """
        Provides the means to work on larger resultsets by providing a Callback. 
        
        :param endpoint: the endpoint
        :param params: a dictionary with possible parameters for the 
            query-string of the request. Values will be properly encoded.
        :param f: a Callable-Object (function, ...) with the signature (row, currentPos, maxPos) as a callback to work on 
            each entry in the dataset.
        """
        url = self.host + "/" + endpoint
        
        self.logger.debug('endpoint:' + url + ', params:' + str(params))
        
        counter = 1
        while url != None: 
            # nur beim ersten request dürfen die Params genutzt werden
            # Ansonsten kommt es ja über den nextLink
            usedParams = None
            if counter == 1: 
                usedParams = params
                # dicts und lists in json umwandeln
                for key, value in usedParams.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        usedParams[key] = json.dumps(value)
            
            # Falls ein Param "body" vorhanden ist, wird dieser als als 
            # BODY genutzt
            body = None
            if usedParams is not None and 'body' in usedParams:
                body = usedParams['body']
                del usedParams['body']
                
            self.logger.info("using body: " + str(body))
            
            # Retry wegen RateLimit
            retryCount = 0
            response = None
            while response == None and ++retryCount < 5:
                # Header müssen nur explizit gesetzt werden, wenn der Body 
                # mitgesendet wird.
                headers = dict()
                if body != None:
                   headers = {'Content-type': 'application/json'}
                    
                res = self.session.get(url, params = usedParams, data = body, headers = headers)
                
                #self.logger.debug("status: %s", res.status_code)
                #self.logger.debug("headers: %s", res.headers)
                
                if res.status_code == 429:
                    wait = res.headers.get('Retry-After', 5)
                    self.logger.warning("Too many requests. Wait for sec: %s", wait)
                    time.sleep(int(wait))
                else:
                    response = res
    
            jsonRes = response.json()
            
            # Everything ok? 
            if jsonRes['responseHeader']['state'] != 'OK':
                raise WDCException(
                    jsonRes['responseHeader']['msg'], 
                    query = jsonRes['responseHeader']['query'], 
                    state = jsonRes['responseHeader']['state'])
            
            self.logger.debug("jsonRes: %s", jsonRes)
            
            for e in jsonRes["content"]:
                f(e, counter, jsonRes['page']['totalElements'])
                counter += 1
            
            # gehts weiter?
            if 'links' in jsonRes and 'next' in jsonRes['links']:
                url = jsonRes['links']['next']
                self.logger.debug("nextLink %s", url)
            else: 
                url = None
                
    def put(self, endpoint: str, body: str, params: dict[str, Any] = {}) -> None:
        """
        Executes a PUT request to the specified endpoint with a body.
        Raises a WDCException if the response is not "OK". 
        
        :param endpoint: the endpoint
        :param body: the body to send with the PUT-Request
        """
        url = self.host + "/" + endpoint
        
        response = self.session.put(url, data=body, **params)
        
        #self.logger.debug("headers: %s", response.headers)
        #self.logger.debug("response: %s", response.status_code)
        
        if response.status_code != 200 and response.status_code != 201: 
            raise WDCException("Could not send PUT for url: " + url)
    
    
    def _rateLimitedGet(self, url, params = { }, headers = { }, body = None, stream = False): 
        # Retry wegen RateLimit
        retryCount = 0
        response = None
        while response == None and ++retryCount < 5:
            # Header müssen nur explizit gesetzt werden, wenn der Body 
            # mitgesendet wird.
            if body != None:
               headers = {'Content-type': 'application/json'}
                
            res = self.session.get(url, params = params, data = body, headers = headers)
            
            self.logger.debug("status: %s", res.status_code)
            self.logger.debug("headers: %s", res.headers)
            
            if res.status_code == 429:
                wait = res.headers.get('Retry-After', 5)
                res.close()
                
                self.logger.warning("Too many requests. Wait for sec: %s", wait)
                
                time.sleep(int(wait))
            else:
                response = res
        
        if response.status_code != 200:
            raise WDCException(
                "Endpoint did not return Status 200. Status was: " + 
                response.status_code)

        return response
    
    
    def streamForEach(self, endpoint: str, params: dict[str, Any] = {}, f: Callable[[Any, int], None] = None) -> None:
        """
        Calls the endpoint and streams the results to enable the 
        handling of *large* results. The endpoint must support the 
        Content-Type 'application/x-ndjson'. 
        
        :param: endpoint: the endpoint
        :param: params: a dict with parameters for the request
        :param: f: callback-function which is called for each object
        """
        
        url = self.host + "/" + endpoint
        
        self.logger.debug('endpoint:' + url + ', params:' + str(params))
        
        # TODO: Body unterstüzten. Sihe loadForEach - als Parameter übergeben
        with self._rateLimitedGet(url, params = params, stream = True) as response:
            if response.headers["content-type"] != "application/x-ndjson":
                raise WDCException("This endpoint is not streamable: " + url)
            
            i = 0
            for o in json_stream.load_many(response):
                i = i + 1
                f(json_stream.to_standard_types(o), i)
                
    
    def __str__(self) -> str:
        return "[host=" + str(self.host) + ", token=" + str(self.token) + "}"
    
    def loadDomainGraph(self, snapshot: str, selection: str = None, variant: str = 'ONLY_SEEDS') -> nx.DiGraph:
        """
        Loads a DomainGraph as a DiGraph. 
        
        Note: If you intend to "merge" other data to nodes or edges, it 
        might be simpler to use the methods loadDomainGraphNodes() 
        and lodDomainGraphEdges() to load the data, modify it and 
        create the graph with createGraph(). 
        
        :param snapshot: The machineName of the snapshot.
        :param selection: A selection of the snapshot.
        :param variant: A value of an enumeration of the variant of the DomainGraph.
            
        :return: DiGraph of the DomainGraph
        """
        domainGraphId = self.findDomainGraphId(snapshot, selection, variant)
        
        nodes, edges = self.loadDomainGraphData(snapshot, selection, variant)
        
        return self.createDomainGraph(nodes, edges)
       
    
    def findDomainGraphId(self, snapshot: str, selection: str = None, variant: str = 'ONLY_SEEDS'):
        """
        Finds the DomainGraphId of the specified Graph.
        
        :param snapshot: The machineName of the snapshot.
        :param selection: A selection of the snapshot.
        :param variant: A value of an enumeration of the variant of the DomainGraph.
        
        :return: the ID of the specified DomainGraph. 
        """
        domainGraphs = self.loadAsJson(
            f"/api/domaingraph/list", 
            { 
                "snapshot": snapshot, 
                "selection": selection, 
                "variant": variant
            })
        
        self.logger.debug("domainGraphs:" + str(domainGraphs))
        
        # es darf nur einer sein
        if len(domainGraphs) != 1: 
            raise WDCException("There must be exactly one DomainGraph but found: " + len(domainGraphs))
        
        return domainGraphs[0]['id']

    def loadDomainGraphData(self, snapshot: str, selection: str = None, variant: str = 'ONLY_SEEDS'):
        """
        Convienence method load the nodes *and* edges of a DomainGraph.
        
        :return: a tuple of (nodes, edges) as JSON.
        """
        domainGraphId = self.findDomainGraphId(snapshot, selection, variant)
        nodes = self.loadAsJson(f"/api/domaingraph/{domainGraphId}/nodes")
        edges = self.loadAsJson(f"/api/domaingraph/{domainGraphId}/edges")
        
        return nodes, edges
    
    def createDomainGraph(self, nodes, edges) -> nx.DiGraph: 
        """
        Create a DiGraph from a list of nodes and a list of edges. 
        
        :param nodes    a JSON-Object or a DataFrame
        :param edges    a JSON-Object or a DataFrame
        
        :return the created DiGraph.
        """
        
        if isinstance(nodes, pd.DataFrame):
            nodes = json.loads(nodes.to_json(orient="records"));
    
        if isinstance(edges, pd.DataFrame):
            edges = json.loads(edges.to_json(orient="records"));
        
         # Graph bauen
        graph = nx.DiGraph()
        for n in nodes:
            _id = n.pop("id")
            graph.add_node(_id, **n)
            
        for e in edges:
            graph.add_edge(e['source'], e['target'], weight=e['weight'])
        
        return graph                    