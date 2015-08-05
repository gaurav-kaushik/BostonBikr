"""
reTrip will take text files of TripAdvisor data and turn them into Geocoded locations to transpose onto the map.
This uses a rather hacky text-based method because of time constraints. A full-featured web crawler that could be used for many pages or other sites at once would be much better. But since we only collect data once, this works OK for now.
Created on Wed Jul 22 09:47:51 2015
@author: gaurav
"""

import os
import re
import pickle
from math import sin, cos, sqrt, atan2, radians
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.vq import kmeans, vq
from pylab import plot
from BostonBikr import findNearestNodeNX, distanceCal, distanceCal4par
# Import your TripAdvisor data
try:
    txt = open('bostontext.txt')
    boston = txt.read() 
except:
    os.chdir('./anaconda/BostonBikr/')
    txt = open('bostontext.txt')
    boston = txt.read()

# Run that through regex    
try:
    reBoston = pickle.load(open("reBoston.p","rb"))
except:
    # reBoston has the strings for each location
    reBoston = re.findall("\n(.*?)\n#", boston)
    print reBoston
    reBoston = list(set(reBoston))
    reBoston_original = reBoston
    pickle.dump(reBoston, open("reBoston.p","wb"))

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
        try:
            latitude, longitude = (value for _, value in sorted(jData.get('results')[0].get('geometry').get('location').items()))
            print 'Your location is at the following coordinates: {:f}, {:f}'.format(longitude, latitude)
        except IndexError:
            latitude, longitude = None, None
    return (longitude, latitude)

# Define map boundary   
bounds = [[42.33289, -71.173794], [42.420644, -71.040413]]
# Put it down flip it and reverse it
bounds = [[y,x] for [x,y] in bounds]
minLong = bounds[0][0]
maxLong = bounds[1][0]
minLat = bounds[1][0]
maxLat = bounds[1][1]

# Get our variables (or generate if not found)
try:
    reBostonGeoBound = pickle.load(open("reBostonGeoBound.p","rb"))
    reBostonGeoLoc = pickle.load(open("reBostonLoc.p","rb"))
except:
    # Use Geocode to transform into coordinates   
    reBostonGeo = []
    reBostonLoc = []
    for location in reBoston:
        reBostonGeo.append(GeoCode(location))
    reBostonGeo_original = reBostonGeo
    
    # Use the boundaries to discard locations outside your matrix
    reBostonGeoBound = []
    for index, location in enumerate(reBostonGeo):
        if (minLong <= location[0] < maxLong) and (minLat <= location[1] <= maxLat):
            reBostonGeoBound.append(location)
            reBostonLoc.append(reBoston[index])

# Call our giant Boston map and the nodes
bostonGraphNX = pickle.load(open("/home/gaurav/anaconda/BostonBikr/app/static/bostonMetroArea.p", "rb"))
bostonGraphNXPos = pickle.load(open("/home/gaurav/anaconda/BostonBikr/app/static/bostonMetroArea_pos.p", "rb"))

## Reassign nodes to proximal node in bostonGraphNX
for idx, node in enumerate(reBostonGeoBound):
    _, newNode = findNearestNodeNX(bostonGraphNX, node)
    reBostonGeoBound[idx] = newNode

# Dump these pickles once you have them transposed onto your graph
pickle.dump(reBostonGeoBound, open("reBostonGeoBound.p","wb"))
pickle.dump(reBostonLoc, open("reBostonLoc.p","wb"))

# Let's take these nodes and create a 2D Gaussian function
def bostonGauss(node, sigma=2355.0):
    xNode, yNode = node[0], node[1]
    metersPerLat = 82190.6
    metersPerLng = 111230.0
    # Transform your sigma into Lat and Long Space (m --> deg lat or lng)
    # Note that sigmaX != sigmaY because real planets have curves
    sigmaX = sigma/metersPerLng
    sigmaY = sigma/metersPerLat
    bounds = [[-71.173794, 42.33289], [-71.040413, 42.420644]]
    xSpace = np.linspace(bounds[0][0], bounds[1][0], 1000)
    ySpace = np.linspace(bounds[0][1], bounds[1][1], 1000)
    x, y = np.meshgrid(xSpace, ySpace)
    Z = (100/(2*np.pi*sigmaX*sigmaY)) * np.exp(-((x-xNode)**2/(2*sigmaX**2) + (y-yNode)**2/(2*sigmaY**2)))
    Z = Z/np.max(Z)
    return x, y, Z

try:
    Z_master = pickle.load(open("Z_master_final.p","rb"))
    Z_centr = pickle.load(open("Z_centr_final.p","rb"))
    centroids = pickle.load(open("centroids6_final.p","rb"))
except:
    # Let's make that Gaussian map -- no bias for node clusters yet
    sig = 1500.0
    x, y, Z = bostonGauss(reBostonGeoBound[0], sigma=sig)
    for locale in reBostonGeoBound[1:]:
        Z = np.add(Z, bostonGauss(locale, sigma=sig)[2])
    bostonLocaleGraph = nx.Graph()
    bostonLocales = dict(zip(reBostonGeoBound,reBostonGeoBound))
    bostonLocaleGraph.add_nodes_from(reBostonGeoBound)
    fig = plt.figure(figsize=(24,24))
    plt.contour(x,y,Z)
    nx.draw(bostonLocaleGraph, pos=bostonLocales, node_size=100, node_color='g')
    nx.draw(bostonGraphNX, pos=bostonGraphNXPos, node_size=1, node_color='g')
    
    # K-means clustering!
    ### K = 6!
    data = np.array(reBostonGeoBound)
    centroids,_ = kmeans(data,6)
    # assign each sample to a cluster
    # WRAP THIS INTO ITS OWN FUNCTION
    idx,_ = vq(data,centroids)
    fig = plt.figure(figsize=(24,24))
    ax = fig.add_subplot(111)
    plot(data[idx==0,0],data[idx==0,1],'ob',
         data[idx==1,0],data[idx==1,1],'or',
         data[idx==2,0],data[idx==2,1],'og',
         data[idx==3,0],data[idx==3,1],'oy',
         data[idx==4,0],data[idx==4,1],'om',
         data[idx==5,0],data[idx==5,1],'oc', markersize=20) 
    nx.draw(bostonGraphNX, pos=bostonGraphNXPos, node_size=1, node_color='k')
    plot(centroids[:,0],centroids[:,1],'8k',markersize=30)
    ax.plot()
    
    # We can do TWO THINGS:
    # 1. We can normalize each Gaussian by the cluster
    # You get a more oblong Gaussian with possibility of local optima
    # 2. Feed the Centroids into a Gaussian and convolve 6
    # with Sigma scaled by # of nodes in cluster
    
    # APPROACH 1 -- normalize per cluster and then add them all up
    # First, let's get our data points per centroid
    # These are all lists of tuples. Good job!
    c0 = (zip(data[idx==0,0], data[idx==0,1]))
    c1 = (zip(data[idx==1,0], data[idx==1,1]))
    c2 = (zip(data[idx==2,0], data[idx==2,1]))
    c3 = (zip(data[idx==3,0], data[idx==3,1]))
    c4 = (zip(data[idx==4,0], data[idx==4,1]))
    c5 = (zip(data[idx==5,0], data[idx==5,1]))
    #c6 = (zip(data[idx==5,0], data[idx==5,1]))
    c_list = [c0, c1, c2, c3, c4, c5]
    
    # Now we find the Z values for each cluster
    # Z_list[kcluster_index] will have len(k)
    Z_list = []
    x, y, _ = bostonGauss(c_list[0][0], sigma=sig)
    for tup in c_list:
        x, y, Z = bostonGauss(tup[0], sigma=sig)
        Z = Z/np.max(Z)
        for locale in tup[1:]:
    #        Z = np.divide(np.add(Z, bostonGauss(locale)[2], sigma=sig),len(tup))
            Z = np.add(Z, bostonGauss(locale, sigma=sig)[2])
        Z_list.append(Z/np.max(Z))
    
    Z_list_normal = []
    for item in Z_list:
         item = item/np.max(item)
         Z_list_normal.append(item)
         
    Z_master = Z_list_normal[0]
    for arr in Z_list_normal:
        Z_master = np.add(Z_master, arr)

    # APPROACH 2 -- fit our centroids
    # 1. Feed the Centroids into a Gaussian and convolve 6
    # with Sigma scaled by # of nodes in cluster
    centroids_orig = centroids
    centroids = list(tuple(map(tuple, centroids)))
    x, y, Z_centr = bostonGauss(centroids[0], sigma=sig)
    for locale in centroids[1:]:
        newZ = bostonGauss(locale, sigma=sig)[2]
        Z_centr = np.add(Z_centr, newZ)

plot_opt = 0
if plot_opt == 1:
    #Plot this shizz if you want
    x, y, _ = bostonGauss(reBostonGeoBound[0])
    fig = plt.figure(1,figsize=(24,24))
    ax1 = fig.add_subplot(111)
    nx.draw(bostonGraphNX, pos=bostonGraphNXPos, node_size=1, node_color='k')
    plot(centroids_orig[:,0],centroids_orig[:,1],'8k',markersize=30)
    plt.contour(x,y,Z_master, linewidths=3)
    ax1.plot()
    fig2 = plt.figure(2,figsize=(24,24))
    ax2 = fig2.add_subplot(111)
    nx.draw(bostonGraphNX, pos=bostonGraphNXPos, node_size=1, node_color='k')
    plot(centroids_orig[:,0],centroids_orig[:,1],'8k',markersize=30)
    plt.contour(x,y,Z_centr, linewidths=3)
    ax2.plot()

print "You're done processing!"
# NEATO! The plots are done and you have your topography map
# Now, you just need to assign a weight to each node
# in your original map "bostonGraphNX"
# To do this: iterate through bostonGraphNX.nodes
# Find the point in Z_master that minimizes delta(x,y)
# Make a dict of dicts where: {node: {weight=number}
# where number is actually your weight number

x, y, _ = bostonGauss(reBostonGeoBound[0])
def findNearestIndex(node, x_vec = x[0], y_vec = y[0]):
    # find the nearest (x,y) to get Z for a node
    x_val = node[0]
    y_val = node[1]
    (k_x, v_x) = min(enumerate(x_vec), key=lambda x: abs(x[1]-x_val))
    (k_y, v_y) = min(enumerate(y_vec), key=lambda x: abs(x[1]-y_val))
    return (k_x, k_y)

def harmonicWeight(node1, node2, Z=Z_master):
    x1, y1 = findNearestIndex(node1)[0], findNearestIndex(node1)[1]
    x2, y2 = findNearestIndex(node2)[0], findNearestIndex(node2)[1]
    Z1 = Z[x1, y1]
    Z2 = Z[x2, y2]
#    A = Z1 + Z2
#    return A
    H = 2*Z1*Z2/(Z1+Z2)
    if H > 0:
        return H
    else: 
        return 0.0001

# You will now create a new NetworkX Graph with the following:
# Each edge has a distance and weight
# The distance is distance (in m) between u and v
# The weight is the score given by your gaussian function above
# You can also add a 'location' tag to nodes so the user
# can see where they're going to be near on your route.
newNX = nx.Graph()
for edge in bostonGraphNX.edges(data=True):
    # Get existing edge properties
    u = edge[0]
    v = edge[1]
    if u in reBostonGeoBound:
        nodeIndex = reBostonGeoBound.index(u)
        nodeLoc = reBostonGeoLoc[nodeIndex]
    elif v in reBostonGeoBound:
        nodeIndex = reBostonGeoBound.index(v)
        nodeLoc = reBostonGeoLoc[nodeIndex]
    else:
        nodeLoc = None        
    dist = edge[2]['weight']
    newNX.add_edge(u,v, distance=dist, weight=harmonicWeight(u,v), location=nodeLoc)

## Save your weighted graph of Boston!
try:
    pickle.dump(newNX, open("/home/gaurav/anaconda/BostonBikr/app/static/bostonMetroArea_Weighted_Locs.p", "wb"))
except:
    print "This file already exists. Try saving as a different filename."
