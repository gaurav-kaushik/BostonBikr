# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 10:35:26 2015

@author: gaurav
"""

import networkx as nx
import pickle 
#from BostonBikr import nxShortestPath, plotPath, distanceCal
from BostonBikr_Week4_backup import *
from random import randint, sample, choice
import operator

class geneticPath():
    
    def __init__(self, start, end, targetDistance):
        self.startPt = start
        self.endPt = end
        self.targetDistance = targetDistance
        # Load our values of interest
        self.nxGraph = pickle.load(open("/home/gaurav/anaconda/BostonBikr/app/static/bostonMetroArea_Weighted_Locs.p", "rb"))
        self.nxPos = pickle.load(open("/home/gaurav/anaconda/BostonBikr/app/static/bostonMetroArea_pos.p", "rb"))
        self.reBostonGeoBound = pickle.load(open("/home/gaurav/anaconda/BostonBikr/app/static/reBostonGeoBound.p","rb"))
        self.reBostonGeoLoc = pickle.load(open("/home/gaurav/anaconda/BostonBikr/app/static/reBostonLoc.p","rb"))
        self.immutableGraph = self.nxGraph
        self.shortestPath, _, _, self.shortestDist = nxShortestPath(self.nxGraph, self.nxPos, start, end, Dijk=0)
        self.shortestDijkPath, _, _, self.shortestDijkDist = nxShortestPath(self.nxGraph, self.nxPos, start, end, Dijk=1)
        self.distanceCheck()
        self.bostonLocales = nx.subgraph(self.immutableGraph, self.reBostonGeoBound)

#    def distanceCheck(self):
#        error = self.pathError(self.shortestDijkDist)
#        if self.targetDistance < self.shortestDist:
#            return self.shortestPath, self.shortestDist
#        elif error < 0.02:
#            return self.shortestDijkPath, self.shortestDijkDist          
    def distanceCheck(self):
        error = self.pathError(self.shortestDijkDist)
        if error < 0.02:
            return 1
        elif self.targetDistance < self.shortestDist:
            return 2
        else:
            return 0
            
    def returnGraph(self):
        self.nxGraph = self.immutableGraph
        
#    def pathError(self, input_distance):
#        error = (input_distance-self.targetDistance)**2/self.targetDistance
#        return error
    def pathError(self, input_distance):
        error = abs(input_distance-self.targetDistance)/self.targetDistance
        return error

    def calcDistance(self, path):
        distance = 0
        for n in range(len(path)-1):
            try:
                distance += self.immutableGraph.edge[path[n]][path[n+1]]['distance']
            except:
#                self.checkPathSmoothness(path)
                self.filterBrokenPaths()
        return distance            
    
    def removeDuplicates(self, path):
        # removes duplicate nodes without affecting order
        seen = set()
        seen_add = seen.add
        return [x for x in path if not (x in seen or seen_add(x))]

    def checkPathSmoothness(self, path):
        try:
            for n in range(len(path)-1):
                if not self.immutableGraph.has_edge(path[n], path[n+1]):
                    print "Your path is broken at nodes {},{}.".format(n, n+1)
                    return False
                else:
                    return True
    #            else:
    #                print "Smoother than peanut butter."
        except:
            return False
        
    def filterBrokenPaths(self):
        unbroken_paths = []
        for path in self.Species:
            if self.checkPathSmoothness(path) == True:
                unbroken_paths.append(path)   
            else:
                path = self.joinDisjointedPath(path)
                unbroken_paths.append(path)
        if not unbroken_paths:
            unbroken_paths = self.shortestDijkDist
        self.Species = unbroken_paths
        
    def joinDisjointedPath(self, disj_nodes, Dijk=0):
        # Fill in the gaps between disjointed nodes in a list
        total_distance, total_score, total_path = 0, 0, []
        # Find and fill in breaks in the path
        newPath = []
        try:
            for n in range(len(disj_nodes)-1):
                if not self.immutableGraph.has_edge(disj_nodes[n], disj_nodes[n+1]):
                    if nx.has_path(self.immutableGraph, disj_nodes[n], disj_nodes[n+1]):
                        try:
                            nxList, _,_, dist = nxShortestPath(self.nxGraph, self.nxPos, disj_nodes[n], disj_nodes[n+1], Dijk=1)
                            newPath += nxList[:-1]
                        except:
                            nxList = self.shortestDijkPath
                            dist = self.shortestDijkDist
                    else:
                        newPath = self.shortestDijkPath
    #                    total_distance = self.shortestDijkDist
                else:
                    newPath += [disj_nodes[n]]
        except:
            newPath = self.shortestDijkPath
                    
        total_path = newPath
#        total_path = self.removeDuplicates(total_path)
        total_distance = self.calcDistance(total_path)
        error = self.pathError(total_distance)
#        self.total_path = total_path
#        self.total_distance = total_distance
        return total_path, total_distance, total_score, error

    def findNearestLocales(self, lookUpNode):
        # Find the closest node to your geocoded location
        # path[mutIndex]
        distLocales = {}
        for node in self.bostonLocales.nodes():
            distLocales[distanceCal(node,lookUpNode)] = node
        nearest = sorted(distLocales.items(), key=operator.itemgetter(0))
        # get top 5 nearest locales
        locales = [near[1] for near in nearest[:5]]
        return locales
            
    def randomGeneticStart(self, num_species=12):
        # Let's get genetic
        self.species_dist = []
        self.species_score = []
        self.species_error = []
        self.Species = []
        for spec in range(num_species):
            # initialize our first route
            initPath = sample(self.reBostonGeoBound, randint(1, 2))
            
            # Sort initPath by proximity to start            
            path = [self.startPt] + initPath + [self.endPt]
            # Stitch the disjointed path together with Dijkstra
            total_path, total_distance, total_score, error = self.joinDisjointedPath(path)
    
            self.species_error.append(error)
            self.Species.append(total_path)
            self.species_score.append(total_score)
            self.species_dist.append(total_distance)
        
        # also add shortest paths in case you start from near the lower end
        self.Species.append(self.shortestDijkPath)
        self.species_dist.append(self.shortestDijkDist)
        self.species_error.append(self.pathError(self.shortestDijkDist))
        self.Species.append(self.shortestPath)
        self.species_dist.append(self.shortestDist)
        self.species_error.append(self.pathError(self.shortestDist))
        self.species_score.append(0)
        self.species_score.append(0)                
        
        self.SpeciesFirstGen = self.Species
        self.filterBrokenPaths()

    def plotSpecies(self, species):
        nxH = nx.subgraph(self.immutableGraph, species)
        plotPath(self.immutableGraph, nxH, self.nxPos)
    
    def getMinSpecies(self):
        errors = []
        for species in self.Species:
            dist = self.calcDistance(species)
            errors.append(self.pathError(dist))
        minErrIndex = errors.index(min(errors))
        self.minSpecies = self.Species[minErrIndex]
        self.minDistance = self.calcDistance(self.minSpecies)
        return self.minSpecies, self.minDistance
        
    def getNovelNeighbors(self, path, nodeIndex=None, nodeList=None):
        novel_nbrs = []
        if nodeIndex:
            nbrs = self.nxGraph.neighbors(path[nodeIndex])
            for nbr in nbrs:
                if nbr not in path:
                    novel_nbrs.append(nbr)
        elif nodeList:
            for nbr in nodeList:
                if nbr not in path:
                    novel_nbrs.append(nbr)
        return novel_nbrs
    
    def getDegNeighbors(self, node=None, degrees=1):
        # 0 will give immediate neighbors, 1 will give neighbors' neighbors, etc.
        # you can get all neighbors within a set # of degrees
        if node:
            nbrs = self.immutableGraph.neighbors(node)
            if nbrs:
                for i in range(degrees):
                    new_nbrs = [self.nxGraph.neighbors(x) for x in nbrs]
                    nbrs = [item for sublist in new_nbrs for item in sublist]
        if nbrs:
            return nbrs

    # Now let's mutate that new species
    def mutationShiftNeighbors(self, path, max_mutations=3):
        # Define a random number of mutations (at least one, at most your max)
        num_mutations = randint(1, max_mutations)
        for mutation in range(num_mutations):
            # for each mutation, pick an arbitary point in the MIDDLE of the path
            mutIndex = randint(1, len(path)-2)
            # You've got the index for your path, now get the neighbors
            neighbors = self.getDegNeighbors(node=path[mutIndex], degrees=4)
            # Check to make sure they're novel
            nbrs = self.getNovelNeighbors(path=path, nodeList=neighbors)
            if nbrs and len(nbrs) > 1:
                nbrIndex = randint(0, len(nbrs)-1)
                path = path[:mutIndex] + [nbrs[nbrIndex]] + [self.endPt]            
#                path[mutIndex] = nbrs[nbrIndex]
            else:
                print "No neighbors found."
        path, _, _, _ = self.joinDisjointedPath(path)
        return path
    
    def getFrags(self, path, n=7):
        # This will split your path into:
        #   [[startPt], ...nChunks...[endPt]]
        # Use this later to mutate your paths
        # Note that as n --> 0, fragment size gets bigger
        fragpath = path[1:-1]
        fraglen = len(fragpath)
        frags=[fragpath[x:x+n] for x in xrange(0, fraglen, n)]
        frags.insert(0,[path[0]])
        frags.insert(-1,[path[-1]])
        return frags
        
    def mutationFrag(self, path):
        # delete a fragment of your graph
        frags = self.getFrags(path)
        mutIndex = randint(1, len(path)-2)
        for frag in frags:
            if path[mutIndex] in frag:
                delIndex = frags.index(frag)
#        del(frags[delIndex])
        # find new nodes to insert
        locs = self.findNearestLocales(path[mutIndex])
#        print "locs: {}".format(locs)
        newLoc = locs[randint(0,len(locs)-1)]
#        print "newLoc: {}".format(newLoc)
#        print "[(newLoc)]: {}".format([(newLoc)])
        frags[delIndex] = [(newLoc)]
        newPath = []
        for frag in frags:
            newPath += frag
        newPath, _, _, _ = self.joinDisjointedPath(newPath)
        return newPath
        
    def mutationDelNode(self, path):
        frags = self.getFrags(path)
        mutIndex = randint(1, len(path)-2)
        for frag in frags:
            if path[mutIndex] in frag:
                delIndex = frags.index(frag)
        del(frags[delIndex])
        # don't insert new nodes, just find new shortest path
        newPath = []
        for frag in frags:
            newPath += frag
        newPath, _, _, _ = self.joinDisjointedPath(newPath)
        return newPath
        
#    def mutationAddNode(self, path, max_mutations=3):
#        # Define a random number of mutations (at least one, at most your max)
#        num_mutations = randint(1, max_mutations)
#        for mutation in range(num_mutations):
#            addNode = sample(self.reBostonGeoBound, 1)
#            # for each mutation, pick an arbitary point in the MIDDLE of the path
#            mutIndex = randint(1, len(path)-2) # randomly select non-endpoint
#            # You've got the index for your path, now get the neighbors
#            newPath = path[:mutIndex] + addNode + [self.endPt]
#        newPath, _, _, _ = self.joinDisjointedPath(newPath)
#        return newPath
    
    def multiplySpecies(self, single_species):
        multi_species = []
        for i in range(10):
            multi_species.append(single_species)
        self.Species = multi_species
    
#    def Mutate(self):
#        mutants = []
#        for species in self.Species:
#            mutations = [self.mutationShiftNeighbors, self.mutationAddNode, self.mutationDelNode]
#            mutant = choice(mutations)(species)
#            mutants.append(mutant)
#        self.Species = mutants
#        self.filterBrokenPaths()
    
#    def Mutate(self):
#        mutants = []
#        for species in self.Species:
#            mutants.append(self.mutationAddNode(species))
#        self.Species = mutants
#
#    def Mutate(self):
#        mutants = []
#        for species in self.Species:
#            mutants.append(self.mutationFrag(species))
#        self.Species = mutants        
#        
    def Mutate(self):
        mutants = []
        for species in self.Species:
#            mutations = [self.mutationFrag, self.mutationAddNode, self.mutationDelNode]
            mutations = [self.mutationFrag, self.mutationDelNode]
            mutant = choice(mutations)(species)
            mutants.append(mutant)
        self.Species = mutants
        self.filterBrokenPaths()
        
    def Evolution(self):
        self.iterations = 0
        check = self.distanceCheck()
        if check == 0:
            self.randomGeneticStart()
            self.getMinSpecies()
            self.TestSpecies = []
            self.TestDistance = []
            self.TestDistance.append(self.minDistance)
            self.error = self.pathError(self.minDistance)
            while self.error > 0.5:
                self.iterations += 1
                if self.iterations > 10:
                    self.finalSpecies = self.minSpecies
                    self.finalDistance = self.minDistance
                    return self.finalSpecies, self.finalDistance, self.error
                self.multiplySpecies(self.minSpecies)
                self.Mutate()
                self.getMinSpecies()
                self.error = self.pathError(self.minDistance)
                self.TestSpecies.append(self.minSpecies)
                self.TestDistance.append(self.minDistance)
            self.finalSpecies = self.minSpecies
            self.finalDistance = self.minDistance
            return self.finalSpecies, self.finalDistance, self.error
        elif check == 1:
            self.iterations += 1
            self.finalSpecies = self.shortestDijkPath
            self.finalDistance = self.shortestDijkDist
            self.error = self.pathError(self.shortestDijkDist)
            return self.finalSpecies, self.finalDistance, self.error
        else:
            self.iterations += 1
            self.finalSpecies = self.shortestPath
            self.finalDistance = self.shortestDist
            self.error = self.pathError(self.shortestDist)
            return self.finalSpecies, self.finalDistance, self.error
            
if __name__ == "__main__":
    g = geneticPath(start=(-71.1046291, 42.3456904), end=(-71.1470952, 42.3863525), targetDistance=10000)
#    g = geneticPath(start=(-71.1046291, 42.3456904), end=(-71.1046291, 42.3456904), targetDistance=5000)
    spec, dist, err = g.Evolution()
    g.plotSpecies(spec)
    print dist, err