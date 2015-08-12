# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 14:38:18 2015

@author: gaurav
"""

#import sys
#from json import loads as JSONLoad
#from os.path import exists as Exists
from math import sin, cos, sqrt, atan2, acos, radians
#from random import randint, random, seed
#from operator import itemgetter
from Queue import Queue
from sets import Set
#from prioritydictionary import priorityDictionary
#from prioritydictionary2 import priorityDictionary
#import pymysql as mdb
import pickle
import networkx as nx
import matplotlib.pyplot as plt
from random import randint, sample, choice
import operator
from geneticAlgorithm import geneticPath
from geojson import Feature, Point, FeatureCollection
""" 
DEFINE CONSTANTS
R = radius of Earth
meter* = estimate for Boston geocodes 
"""
R = 6373000
maxVal = 999999.9
meterPerLat = 82190.6
meterPerLng = 111230

"""
DISTANCE CALCULATION FUNCTIONS
"""
def cor2ID(cor):
    #convert list to tuple to serve as node key
    tp = (cor[0], cor[1])
    return tp

def distanceCal4par(lon1, lat1, lon2, lat2):
    #compute the distance between (lon1, lat1) and (lon2, lat2)
    lon1 = radians(lon1)
    lat1 = radians(lat1)
    lon2 = radians(lon2)
    lat2 = radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return distance  

def distanceCal(cor1, cor2):
#    print "distanceCal called!"
#    print "Here is cor1: " + str(cor1)
#    print "Here is cor2: " + str(cor2)
    return distanceCal4par(cor1[0], cor1[1], cor2[0], cor2[1])

def calPathDisSlow(linCor):
    #Calculate the tot dis of entire path from scratch
    print "calPathDisSlow called!"
    pathLen = 0
    for idx in xrange(1,len(linCor)):
        delLen = distanceCal(linCor[idx], linCor[idx-1])
        #print delLen
        pathLen += delLen
    return pathLen

def lenCal(vec):
    #length of vector
    return sqrt(vec[0]**2+vec[1]**2)

def directionalVec(u, v):
    #return the unit directional vetor from pt u to pt v
    vec = ((u[0]-v[0])*meterPerLng, (u[1]-v[1])*meterPerLat)
    vecLen = lenCal(vec)
    vec = (vec[0]/vecLen, vec[1]/vecLen)
    return vec

def innerProduct(u, v):
    #suppose u and v are already unit vector
    return u[0]*v[0]+u[1]*v[1]

###
#Scoring function
###    
def distScore(curDis, targetDis):
    #penalize on the difference between current
    #distance and target distance
    return (curDis-targetDis)**2/targetDis**2

#p is onePath <type list>
def turnScore(p):
    #penalize on turns
    score=0
    if (len(p)>=3):
        for i in xrange(0, (len(p) - 2)):
            u = directionalVec(p[i], p[i+1])
            v = directionalVec(p[i+1], p[i+2])
            prod = innerProduct(u, v)
            prod = min(1,max(prod,-1))
            angle = acos(prod)  #in radians
            score=score+angle            
    return score

#p is onePath <type list>
def repScore(p, curDis):
    #penalize on repetition of path
    score = 0
    edgeSet = Set()
    for idx in xrange(1, len(p)):
        key = (p[idx-1], p[idx])
        alterKey = (p[idx], p[idx-1])
        if key not in edgeSet:
            edgeSet.add(key)
        else:
            score += distanceCal(p[idx], p[idx-1])
        if alterKey not in edgeSet:
            edgeSet.add(alterKey)    
        else:
            score += distanceCal(p[idx], p[idx-1])
    return score/curDis


#p is onePath <type list>, curDis targDist double
def totScoreCal(path, curDis, targetDis):
    #total penalize score, ratios are chosen s.t. penalty 
    #coming from different sources have similar variance
    turnRatio = 0.02
    disRatio = 10
    repRatio = 10
    
    tScore = turnScore(path)
    dScore = distScore(curDis, targetDis)
    rScore = repScore(path, curDis)
    
    totScore = turnRatio*tScore + disRatio*dScore + repRatio*rScore      
    return totScore

"""
STAY CLASSY
Here's where we define Vertex and its metaclass Graph.
We'll use methods in these classes to generate a clean map and more!
"""
class Vertex:
    #cor is a tuple of (lon, lat)
    def __init__(self, cor):
        self.id = cor
        self.connectedTo = {}

    def addNeighbor(self, nbrID, dist=0, score=1):
        self.connectedTo[nbrID] = [dist, score]
      
    def __str__(self):
        #print overload 
        s = str(self.id) + ' connectedTo: '
        for x in self.connectedTo:
            s += str(x) + ' d='+str(self.connectedTo[x][0])
            s += ', s=' + str(self.connectedTo[x][1])+'; '
        return s
    
    def getConnections(self):
        return self.connectedTo.keys()
    
    def neighborNumber(self):
        return len(self.connectedTo)
 
    def getID(self):
        return self.id
    
    def getLon(self):
        return self.id[0]
    
    def getLat(self):
        return self.id[1]
    
    def getLength(self,nbrID):
        return self.connectedTo[nbrID][0]
    
    def getScore(self, nbrID):
        return self.connectedTo[nbrID][1]

class Graph(Vertex):
    
    def __init__(self):
        self.vertList = {}
        self.numVertices = 0
        self.numEdges= 0

    def recountVandE(self):
        self.numVertices = 0
        self.numEdges = 0
        for u in self.getVertices():
            self.numVertices += 1
            self.numEdges += len(self.vertList[u].getConnections())
        
    def addVertex(self, v):
        self.numVertices += 1
        newVertex = Vertex(v)
        self.vertList[v] = newVertex
        return newVertex

    def getVertex(self,n):
        if n in self.vertList:
            return self.vertList[n]
        else:
            return None

    def __contains__(self,n):
        return n in self.vertList

    #note that f, t are tuples cor(lon, lat) here
    def addEdge(self, f, t, dist=0, score=1, oneWay=False):
        if f not in self.vertList:
            nv = self.addVertex(f)
        if t not in self.vertList[f].getConnections():
            self.numEdges += 1
            self.vertList[f].addNeighbor(t, dist, score)
        if not oneWay:
            if t not in self.vertList:
                nv = self.addVertex(t)
            if f not in self.vertList[t].getConnections():
                self.numEdges += 1
                self.vertList[t].addNeighbor(f, dist, score)

    def getVertices(self):
        return self.vertList.keys()
            
    def __str__(self):
        for v in self.vertList:
            print self.vertList[v]
        return ''

    def removeVertex(self, delVID):
        if delVID in self.vertList:
            self.numVertices -= 1
            self.numEdges -= len(self.vertList[delVID].getConnections())
            del self.vertList[delVID]

    #Note this only delete the edge from u to v, not vice versa
    def removeEdge(self, u, v):
        if u in self.vertList:
            if v in self.vertList[u].getConnections():
                self.numEdges -= 1
                [dis, score] = self.vertList[u].connectedTo[v]
                del self.vertList[u].connectedTo[v]
                return (dis, score)  
            else:
                return (-1, 0)
    
    #This function remove the middle point u and concatenate its
    #in and out edge
    def removeMiddlePt(self, u):
        twoNeighbors = self.vertList[u].getConnections()
        for v in twoNeighbors:
            self.removeEdge(v, u)
        self.addEdge(twoNeighbors[0], twoNeighbors[1])
        self.removeVertex(u)
                 
    #combine all nodes in the combineSet, return their COM combined newNode
    def combine(self, combineSet):
        x=0
        y=0
        for u in combineSet:
            x+=u[0]
            y+=u[1]
        newND = (x/len(combineSet), y/len(combineSet))
        self.addVertex(newND)
        for u in combineSet:
            for nb in self.vertList[u].getConnections(): 
                if nb not in combineSet:
                    self.removeEdge(nb, u)
                    self.addEdge(nb, newND)
                    self.addEdge(newND, nb)
            self.removeVertex(u)
        return newND   

    def calPathDis(self, path):
        #Calculate the tot dis of entire path from preCalDist
        pathLen = 0
        for idx in xrange(1,len(path)):
            fNode = path[idx-1]
            tNode = path[idx]
            pathLen += self.vertList[fNode].connectedTo[tNode][0]
        return pathLen

    def findNearestNode(self, lookUpNode, NNnode):
        #"find the closest node to the geocoded location" 
        minDist = maxVal 
        for node in self.vertList:
            curDist = distanceCal(node, lookUpNode)
            if curDist < minDist:
                minDist = curDist
                NNnode[1] = node[1]
                NNnode[0] = node[0]
        return minDist

    def __iter__(self):
        return iter(self.vertList.values())   
    
    def ccBFS(self, startN, visited, conComponent):
        ###
        #This is to count the number of vertices inside each connected component
        #remove isolated islands
        ###
        visited.add(startN)
        conComponent['conND'].add(startN)
        conComponent['ct']+=1
        BFSqueue = Queue()
        BFSqueue.put(startN)
        while not BFSqueue.empty():
            nd = BFSqueue.get()        
            if nd in self.vertList:
                for conND in self.vertList[nd].getConnections():
                    if conND not in conComponent['conND']:
                        visited.add(conND)
                        conComponent['conND'].add(conND)
                        conComponent['ct']+=1
                        BFSqueue.put(conND)

"""
WEB STUFF!
Here, we have methods to:
1. convert an 'address' <type string> to a geocoordinate (GeoCode)
2. take a 'geoItem' and turn it into a geoJSON type (GeoJsonify)
3. define a boundary and check that our coordinates are within it (inBounds)
4. build a dictionary from a set (buildDict)
5. create a 'MiniWorld' map, in which we query our sql database for a subset
    of geolocation data for pathfinding (createMiniWorld)
6. put it all together! (PathTestMashUp)
"""
def GeoCode(address):
    # take 'address' <type string> and get geocoordinates
    import json
    from urllib2 import urlopen
    from urllib import quote
    # encode address query into URL
    url = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&sensor=false&key={}'.format(quote(address, gAPI_key))
    # call API and extract json
    print 'Calling Google for the following address: ' + address
    jData = urlopen(url).read()
    jData = json.loads(jData.decode('utf-8')) # THIS MIGHT THROW AN ERROR
    # extract coordinates (latitude, longitude)
    if jData.get('status') == 'ZERO_RESULTS':
        latitude, longitude = None, None
        print 'The following address was not found: ' + address
    else:
        latitude, longitude = (value for _, value in sorted(jData.get('results')[0].get('geometry').get('location').items()))
        print 'Your location is at the following coordinates: {:f}, {:f}'.format(longitude, latitude)
    return (longitude, latitude)

def GeoJsonify(geoItem):
    if isinstance(geoItem, list):
        geoJSON = {  
                 'type' : 'Feature',
                 'properties': {'stroke': '#914791'},
                 'geometry' :{
                    'type' : 'LineString',
                    'coordinates': geoItem,
                 }
            }
    elif isinstance(geoItem, tuple):   
        geoJSON = {
            'type' : 'Feature',
            'geometry' : {
                'type' : 'Point',
                'coordinates' : [geoItem[1], geoItem[0]],
            }
        }
    return geoJSON

def GeoJsonifyMarkers(markerList):
    features_list = []
    for m in markerList:
        m_url = 'https://www.google.com/search?espv=2&biw=1600&bih=791&site=webhp&q=' + str(m[0])
        features_list.append(Feature(geometry=Point(tuple(m[1:])), properties={'title':str(m[0]), 'marker-color':'#751975', 'url': m_url}))
    return features_list
    
def GeoJsonifyEndpoints(start, end):
    start_url = 'https://www.google.com/search?espv=2&biw=1600&bih=791&site=webhp&q=' + str(start[0])
    end_url = 'https://www.google.com/search?espv=2&biw=1600&bih=791&site=webhp&q=' + str(end[0])
    start = Feature(geometry=Point(tuple(start[1:])), properties={'title':str(start[0]), 'marker-color':'#47D147', 'url': start_url})
    end = Feature(geometry=Point(tuple(end[1:])), properties={'title':str(end[0]), 'marker-color':'#FF3300', 'url': end_url})
    return start, end

def inBounds(node, bounds):
    #bounds = [[minX, minY], [maxX, maxY]]
    flag1 = (node.getLat()<bounds[1][1] and node.getLat()>bounds[0][1])
    flag2 = (node.getLon()<bounds[1][0] and node.getLon()>bounds[0][0])
    if  flag1 and flag2:
        return True
    return False

def buildDict(vSet, gDict):
    for v in vSet:
        gDict[v.getID()] = {'Dist': maxVal, 'pred':None}
    return  

def getMapBoundary(): 
    #define the boundary of the miniworld
    # In this toy version, you can load this pickle from the Static folder
    # The real version calls edges from a database
    bounds = pickle.load(open("./static/bostonMetroArea_bounds.p", "rb"))
    return bounds

def findNearestNodeNX(graph, lookUpNode):
    # Find the closest node to your geocoded location
    minDist = maxVal 
    for node in graph.nodes():
        curDist = distanceCal(node, lookUpNode)
        if curDist < minDist:
            minDist = curDist
            minNode = node
    return minDist, minNode
    
def miniGraph2NX(miniGraph):
    # Convert our miniGraph to NX object
    # NOTE: in the future, have SQL-->NX directly
    cleanG = miniGraph
    nxG = nx.Graph()
    nodes = cleanG.vertList.keys()
    nodes = dict(zip(nodes,nodes))
    for node in nodes:
        nxG.add_node(node)
        for neighbor in cleanG.vertList[node].getConnections():
            length = distanceCal(node, neighbor)
            nxG.add_edge(node, neighbor, weight=length)
    return nxG, nodes

def nxPlot(nxGraph, nxPos):
    plt.figure(1, figsize=(12,12))
    nx.draw(nxGraph, pos=nxPos, node_size=5)
    plt.show()
        
def nxShortestPath(nxGraph, nxPos, startPt, endPt, Dijk=0):
    if Dijk == 0:
        nxList = nx.shortest_path(nxGraph, source=startPt, target=endPt)
        score = nx.shortest_path_length(nxGraph, source=startPt, target=endPt)
        dist = nx.shortest_path_length(nxGraph, source=startPt, target=endPt, weight='distance')
    elif Dijk == 1:
        nxList = nx.dijkstra_path(nxGraph, source=startPt, target=endPt, weight='weight')
        score = nx.dijkstra_path_length(nxGraph, source=startPt, target=endPt, weight='weight')
        dist = nx.dijkstra_path_length(nxGraph, source=startPt, target=endPt, weight='distance')
    
    nxH = nx.subgraph(nxGraph, nxList)
    return nxList, nxH, score, dist

def getRealPathLength(myPath):
    pathLength = 0
    lengths = []
    for i in range(len(myPath)-1):
        lengths.append(distanceCal(myPath[i], myPath[i+1]))
        pathLength += lengths[-1]
    return pathLength

def plotPath(fullGraph, pathGraph, nodePos):
    nxGraph = fullGraph
    nxH = pathGraph
    nxPos = nodePos
    fig = plt.figure(figsize=(16,16))
    ax = fig.add_subplot(111)
    nx.draw(nxGraph, pos=nxPos, node_size=2)
    nx.draw(nxH, pos=nxPos, node_size=40, width=5, edge_color='r')
    ax.plot()
    
def PathTestMashUp(startPt, endPt, runDis=3):
    """
    WHERE THE MAGIC HAPPENS!
    The website will call this function. 
    """
    ## Load up your necessary variables
    # In this toy version, you can load this pickle from the Static folder
    # The real version calls edges from a database upon each query and rebuilds the map around your start and end coordinates
    nxGraph = pickle.load(open("./static/bostonMetroArea_Weighted_Locs.p", "rb"))
    nxPos = pickle.load(open("./static/bostonMetroArea_pos.p", "rb"))
    targetDis = runDis*1000+1 # convert km to m
    
     # Use the Google to find geolocation ,type tuple> for your start/endPt <type string>
    startCor = GeoCode(startPt)
    endCor = GeoCode(endPt)
    startDist, startNode = findNearestNodeNX(nxGraph, startCor)
    endDist, endNode = findNearestNodeNX(nxGraph, endCor)
    
    # to prevent crashes, shift one node slightly to a neighbor
    if startNode == endNode:
        endNode = nx.neighbors(nxGraph, endNode)[0]
        
    print 'The closest node found to startPt is {} from dist {}'.format(startNode, startDist)
    print 'The closest node found to endPt is {} with dist {}'.format(endNode, endDist)

    # Ensure you're within the boundaries of your world    
    bounds = getMapBoundary()
    print "Boundaries found: {}".format(bounds)
    
    ## PATHFINDERS
#     Calculate weighted and unweighted Dijkstras
    shortestPath_uw, nxH_uw, _, pathLength_uw = nxShortestPath(nxGraph, nxPos, startNode, endNode, Dijk=0)
    shortestPath_w, nxH_w, _, pathLength_w = nxShortestPath(nxGraph, nxPos, startNode, endNode, Dijk=1)
    
    # Run the genetic algorithm!
    gene = geneticPath(startNode, endNode, targetDis)
    shortestPath_g, pathLength_g, error_g = gene.Evolution()
    nxH_g = nx.subgraph(nxGraph, gene.finalSpecies)
    nxH = nxH_g
    shortestPath = shortestPath_g
    shortestPath.append(list(endCor))
    pathLength = pathLength_g  
    message = 'Here is a {:.0f} km path for you.'.format(pathLength_g/1000.0)

    # Get the locations for any interesting nodes
    pathLocations = []
    pathNodes = []
    pathLocales = []
    for edge in nxH.edges(data=True):
        if edge[2]['location'] is not None:
            pathLocations.append(edge[2]['location'])
            pathNodes.append(edge[1])
            pathLocales.append([edge[2]['location'], edge[1][0], edge[1][1]])
    pathLocations = list(set(pathLocations))
    pathNodes = list(set(pathNodes))
    pathLocales = [list(x) for x in set(tuple(x) for x in pathLocales)]
    
    unique_locales=[]
    unique_strings=[]

    for ls in pathLocales:
        if ls[0] not in unique_strings:
            unique_strings.append(ls[0])
            unique_locales.append(ls)
    pathLocales = unique_locales
    
    message += " Enjoy your ride!"

    # Create the new map layer with path and markers
    # turn locales in geojson object
    markers = GeoJsonifyMarkers(pathLocales)
    # add start and end
    startGeo, endGeo = GeoJsonifyEndpoints([startPt, startCor[0], startCor[1]], [endPt, endCor[0], endCor[1]])
    # add the path and endpoints as a geojson object
    markers.append(GeoJsonify(shortestPath))
    markers.append(startGeo)
    markers.append(endGeo)
    # create final layer as a Feature Collection
    geoMarkers = FeatureCollection(markers)

    # Create locales list of lists    
    json = {
            'bounds': bounds,
            'startPt': GeoJsonify(startCor),
            'endPt': GeoJsonify(endCor), 
            'dist': pathLength,
            'path': geoMarkers,
            'message': message,
            'locales': GeoJsonifyMarkers(pathLocales)
            }

    return json # FOR APP
    
#    return json, shortestPath, pathLength, nxH, pathLocales, pathNodes # FOR TESTING

if __name__ == "__main__":
    # Test run
    start = 'Fenway, Boston, MA'
    end = 'Fresh Pond, MA'
    distance = 16
    json = PathTestMashUp(start, end, distance)
