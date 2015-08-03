# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 14:46:16 2015

@author: gaurav
"""

"""
Your one-stop solution to importing, process, and writing geojson data!
This implementation will allow you to play with your data as a pandas df
or write to SQL and play there.

Steps:
1. Import geoJson file.
2. Begin the process of cleaning the data.
3. Write to pandas df while calculating distances between nodes.
4. Commit df to SQL database for future use.
5. Recall if a pickle exists for this file.
6. Convert to NetworkX format

Later, we will figure out how to import the SQL table into NetworkX.

The pertinent things you want from this:
self.cleanGraph: your cleaned up geoJSON file as a Graph() object
self.nxG: your Graph() as a NetworkX-Graph() object, which is what
            you will do your calculations on.
"""

import os
import json
from distanceCalculations import *
import pickle
from iRun_modified import *
from BostonBikr import *
import pandas as pd
import distanceCalculations as disCal
import pymysql as mdb
import matplotlib.pyplot as plt
import networkx as nx

class GeoData:
    
    def __init__(self, jFilename):
        self.jFilename = jFilename
        jData = open(jFilename)
        roadData = json.load(jData)
        self.roadListOSM = roadData['features']
        jData.close()
        self.roadListPY = Graph()
        self.lineNum = 0
        
    def addPath2roadList(self, lineCoord):
        x = [i for i,j in lineCoord]
        y = [j for i,j in lineCoord]
        for idx in xrange(1,len(lineCoord)):
            Coord1 = lnglat2Tuple(x[idx-1], y[idx-1])
            Coord2 = lnglat2Tuple(x[idx], y[idx])
            self.roadListPY.addEdge(f=Coord1, t=Coord2, dist=distanceCal(lineCoord[idx-1], lineCoord[idx]), score=0)

    def getRoadList(self):
        # USE THE BOTTOM IMPLEMENTATION FOR BIKE PATHS
        for lineObj in self.roadListOSM:
            if lineObj['geometry']['type']=='LineString':
                lineCoord = lineObj['geometry']['coordinates']
                self.lineNum += len(lineCoord)
                self.addPath2roadList(lineCoord)  
            elif lineObj['geometry']['type']=='MultiLineString':
                for i in range(len(lineObj['geometry']['coordinates'])):            
                    lineCoord = lineObj['geometry']['coordinates'][i]
                    self.lineNum += len(lineCoord)
                    self.addPath2roadList(lineCoord) 
            else:
                print 'type '+ lineObj['geometry']['type'] +' unspecified'   

    def cleanThatMap(self):
        """
        Initiate data cleanup.
        """
        self.dirtyGraph = self.roadListPY
        # Status update
        print 'Before cleanup we have ' + str(self.lineNum) + ' line segments and ' + str(len(self.roadListPY.getVertices())) + ' vertices.'

        # Clean small but CONNECTED components
        # Filter isolated objects with minConCt < 50 vertices
        minConCt = 50
        visited = set()
        ndKeys = self.roadListPY.getVertices()
        print len(ndKeys)
        for nd in ndKeys:
            if nd not in visited:
                conComponent = {'conND': set(), 'ct': 0}
                self.roadListPY.ccBFS(nd, visited, conComponent)
                if conComponent['ct'] < minConCt:
                    for delnd in conComponent['conND']:
                        self.roadListPY.removeVertex(delnd)

        # Clean up spur nodes (nodes with but one neighbor)
        delVnum = 1
        roundNum= 0
        totalDelN = 0
        ndKeys = self.roadListPY.getVertices()
        ndKeys = Set(ndKeys)
        delVnum = 1
        while (delVnum>0):
            roundNum += 1
            delVnum = 0
            delVertex = Set() 
            for u in ndKeys:
                if self.roadListPY.vertList[u].neighborNumber()==1:
                    delVnum += 1
                    v = self.roadListPY.vertList[u].getConnections()[0]
                    self.roadListPY.removeVertex(u)
                    self.roadListPY.removeEdge(v, u)
                    delVertex.add(u)
            for u in delVertex:
                ndKeys.remove(u)
            totalDelN += delVnum
        print ('total number of spur nodes removed is {}'.format(totalDelN))

        # Coarse gran representation
        # Combine redunant nodes at road intersection
        delVnum = 1
        roundNum= 0
        totalDelN = 0
        ndKeys = self.roadListPY.getVertices()
        ndKeys = Set(ndKeys)
        delVnum = 1
        while (delVnum>0):
            roundNum += 1
            delVnum = 0
            delVertex = Set() 
            for u in ndKeys:
                if self.roadListPY.vertList[u].neighborNumber()==1:
                    delVnum += 1
                    v = self.roadListPY.vertList[u].getConnections()[0]
                    self.roadListPY.removeVertex(u)
                    self.roadListPY.removeEdge(v, u)
                    delVertex.add(u)
            for u in delVertex:
                ndKeys.remove(u)
            totalDelN += delVnum
            print ('{} spur nodes removed in round {}').format(delVnum, roundNum)
        print ('total number of spur nodes removed is {}'.format(totalDelN))


        ###
        #Step 3
        #Coarse Grain representation of the graph
        #Combine nodes at the road intersection, s.t. 
        #I can combine parallel roads in step 4
        ###
        print 'Clean redundant nodes...'
        delVnum = 1
        roundNum= 0
        resDis = 20
        totalDelN = 0
        ndKeys = self.roadListPY.getVertices()
        ndKeys = Set(ndKeys)
        delVnum = 1
        while (delVnum>0):
            roundNum += 1
            delVnum = 0
            delVset = Set()
            addVset = Set()
            for u in ndKeys:
                #if u is an intersection
                if (u in self.roadListPY.vertList) and (self.roadListPY.vertList[u].neighborNumber()>2):
                    combineSet = Set()
                    checkQueue = Queue()
                    visited = Set()

                    visited.add(u)
                    checkQueue.put(u)
                    #if the connected node v is also an intersection and dis(u, v)<minDis, combine
                    while not checkQueue.empty():
                        curNd = checkQueue.get()
                        for v in self.roadListPY.vertList[curNd].getConnections():
                            if (v in self.roadListPY.vertList and\
                                self.roadListPY.vertList[v].neighborNumber()>2 \
                                and distanceCal(v, curNd)< resDis):
                               if curNd not in combineSet:
                                   combineSet.add(curNd)
                               if v not in combineSet:
                                   combineSet.add(v)
                               if v not in visited:
                                   visited.add(v)
                                   checkQueue.put(v)       
                    if combineSet:       
                        delVnum = delVnum+len(combineSet)-1    
                        newKey = self.roadListPY.combine(combineSet)
                        delVset = delVset.union(combineSet)
                        addVset.add(newKey)
            for u in delVset: 
                ndKeys.discard(u)
            for u in addVset:
                ndKeys.add(u)            
            totalDelN += delVnum 
            print ('{} nearby intersection nodes removed in round {}').format(delVnum, roundNum)
        print ('total number of nearby intersection nodes removed is {}'.format(totalDelN))

        print 'Clean redundant intermediate nodes...'
        delVnum = 1
        roundNum= 0
        totalDelN = 0
        ndKeys = self.roadListPY.getVertices()
        ndKeys = Set(ndKeys)
        delVnum = 1
        while (delVnum>0):
            roundNum += 1
            delVnum = 0
            delVertex = Set() 
            for u in ndKeys:
                nb = self.roadListPY.vertList[u].getConnections()
                if len(nb)==2:
                    vec1 = directionalVec(nb[0], u)  
                    vec2 = directionalVec(nb[1], u)           
                    prod = innerProduct(vec1, vec2)
                    if abs(prod)>0.9:
                        self.roadListPY.removeMiddlePt(u)
                    delVnum += 1
                    delVertex.add(u)
            for u in delVertex:
                ndKeys.remove(u)
            totalDelN += delVnum
            print ('{} intermediate nodes removed in round {}').format(delVnum, roundNum)
        print ('total number of intermediate nodes removed is {}'.format(totalDelN))
        self.roadListPY.recountVandE() 
        self.cleanGraph = self.roadListPY
        return self.cleanGraph

    def storeAsPickle(self, pickle_filename):
        self.clean_pickle_filename = pickle_filename+'.p'
        self.dirty_pickle_filename = 'dirty'+pickle_filename+'.p'
        self.dirtyPickle = pickle.dump(self.dirtyGraph, open(self.dirty_pickle_filename, 'wb'))
        self.cleanPickle = pickle.dump(self.cleanGraph, open(self.clean_pickle_filename, 'wb'))
    
    def getDirtyPickle(self):
        # peter piper picked a pack of (dirty) pickles
        return pickle.load(open(str(self.dirty_pickle_filename),"rb"))
        
    def getCleanPickle(self):
        # peter piper picked a pack of (clean) pickles
        return pickle.load(open(str(self.clean_pickle_filename),"rb"))

    def py2Pandas(self):
        columnLabels = ['lng1', 'lat1', 'lng2', 'lat2', 'dist', 'score']
        df = pd.DataFrame(columns=columnLabels)
        for node in self.roadListPY.vertList:
            for cnode in self.roadListPY.vertList[node].getConnections():
                indexer = str(node)
                distance = disCal.distanceCal(node, cnode)
                score = 1 # replace this with a scoring algorithm
                df.loc[indexer] = [node[0], node[1], cnode[0], cnode[1], distance, score]
        self.df = df

    def pandas2SQL(self, database_name, table_name):
        default = '/home/gaurav/anaconda/BostonBikr/.my.cnf'
        db = mdb.connect(read_default_file=default)
        cur = db.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS {};".format(database_name))
        cur.execute("USE {};".format(database_name))
        try:
            self.df.to_sql(name=table_name, con=db, flavor='mysql')
            print "The table {} has been placed in database {}.".format(table_name, database_name)
        except ValueError:
            print "The table {} already exists in {}.".format(table_name, database_name)
        db.commit()
        cur.close()
        db.close()
        
    def plotNodes(self, dpi=400, fs=20, ms=4, cleanFlag=True):
        if cleanFlag:
            roads = self.cleanGraph.getVertices()
        else:
            roads = self.dirtyGraph.getVertices()            
        fig = plt.figure(figsize=(fs,fs), dpi=dpi)
        ax = fig.gca()
        try:
            for linObj in roads:
                x = [i for i, j in linObj]
                y = [j for i, j in linObj]
                ax.plot(x, y, '.', markersize=ms)
        except TypeError:
            for linObj in roads:
                x = linObj[0]
                y = linObj[1]
                ax.plot(x, y, '.', markersize=ms)           
        ax.axis('scaled')
        plt.show()

    def plotEdges(self, dpi=400, fs=20, ms=4, cleanFlag=True):
        # Currently broken and must be fixed
        if cleanFlag:
            roads = self.cleanGraph.getVertices()
        else:
            roads = self.dirtyGraph.getVertices()
        fig = plt.figure(figsize=(fs,fs), dpi=dpi)
        ax = fig.gca()
        for linObj in roads:
            w = linObj[0]
            z = linObj[1]
            ax.plot(w, z, '-', markersize=ms)           
        ax.axis('scaled') 
        plt.show()
        
    def upToSQL(self, databasename, filename):
        if os.path.isfile('{}.p'.format(filename)):
            print "You have processed this file already."
            self.clean_pickle_filename = filename+'.p'
            self.cleanGraph = self.getCleanPickle()
        else:
            self.getRoadList()
            self.cleanThatMap()
            self.storeAsPickle(pickle_filename=filename)
            self.py2Pandas()
            self.pandas2SQL(database_name=databasename, table_name=filename)
        
    def connectToDB(self, databasename, filename):
        try:
            default = '/home/gaurav/anaconda/BostonBikr/.my.cnf'
            self.connection = mdb.connect(read_default_file=default)
            self.cursor = self.connection.cursor()
        except:
            print 'Network connection \ errors persist. How sad. How \ unlucky for you.'

    def disconnectFromDB(self, databasename, filename):
        if self.connection is not None and self.cursor is not None:
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            
    def clean2NX(self):
        cleanG = self.cleanGraph
        nxG = nx.Graph()
        nodes = cleanG.vertList.keys()
        nodes = dict(zip(nodes,nodes))
        for node in nodes:
            nxG.add_node(node)
            for neighbor in cleanG.vertList[node].getConnections():
                length = disCal.distanceCal(node, neighbor)
                nxG.add_edge(node, neighbor, weight=length)
        self.nxG = nxG
        self.nxPos = nodes

    def nxPlot(self):
        if self.nxG and self.nxPos:
            plt.figure(1, figsize=(12,12))
            nx.draw(self.nxG, pos=self.nxPos, node_size=5)
            plt.show()
            
    def nxShortestPath(self, startPt=10, endPt=200):
        if self.nxG:
            start = self.nxG.nodes()[startPt]
            end = self.nxG.nodes()[endPt]
            self.nxList = nx.shortest_path(self.nxG, source=start, target=end)
            self.nxH = nx.subgraph(self.nxG, self.nxList)
#            nx.draw(self.nxH,pos=self.nxPos, node_size=10)
    
    def GeoJsonify(self, geoItem):
        if isinstance(geoItem, list):
            self.geoJSON = {
                        'type': 'Feature',
                        'properties': {},
                        'geometry': {
                                    'type': 'LineString',
                                    'coordinates': geoItem}
                            }
        elif isinstance(geoItem, tuple):
            self.geoJSON = {
                        'type': 'Feature',
                        'geometry': {
                                    'type': 'Point',
                                    'coordinates': [geoItem[1], geoItem[0]]
                                    }
                            }
        return self.geoJSON
    
    def findBounds(self):
        lats, lngs = [], []
        nodes = nxG.nodes(data=True)
        for tup in nodes:
            lngs.append(tup[0][0])
            lats.append(tup[0][1])
        minLat = min(lats)
        maxLat = max(lats)
        maxLng = max(lngs)
        minLng = min(lngs)
        return [[minLat, minLng],[maxLat, maxLng]]        
        
if __name__ == "__main__":
    pathname = '/home/gaurav/anaconda/BostonBikr/app/'
    os.chdir(pathname)
    G = GeoData(jFilename='HUGE_BOSTON_MAP.geojson')
#    G.upToSQL(databasename='mapDB', filename='bostonMetroArea')
#    G.clean2NX()
#    nxG = G.nxG
#    nxPos = G.nxPos
#    G.nxShortestPath()
#    fig = plt.figure(figsize=(16,16))
#    ax = fig.add_subplot(111)
#    nx.draw(G.nxG, pos=G.nxPos, node_size=2)
#    nx.draw(G.nxH, pos=G.nxPos, node_size=40, width=5, edge_color='r')
#    ax.plot()
#    geoFile = G.GeoJsonify(G.nxList)
#    pickle.dump(nxG, open("/home/gaurav/anaconda/BostonBikr/app/static/bostonMetroArea.p", "wb"))
#    pickle.dump(nxPos, open("/home/gaurav/anaconda/BostonBikr/app/static/bostonMetroArea_pos.p", "wb"))
#    pickle.dump(G.findBounds(), open("/home/gaurav/anaconda/BostonBikr/app/static/bostonMetroArea_bounds.p", "wb"))


    # NOTE nxH is the subgraph that you are PLOTTING
    # nxH is what you need to convert to JSON