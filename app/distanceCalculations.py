from math import sin, cos, sqrt, atan2, acos, radians
from sets import Set

R = 6373000 # ~radius of Earth
metersPerLng = 111230.0
metersPerLat = 82190.6
# Note: ~0.3% error with mapbox calculation

def lnglat2Tuple(lng, lat):
    return (lng, lat) # returns a tuple of lng, lat

def coord2Tuple(coord):
    return (coord[0], coord[1]) # returns a tuple of coordinate

#def distanceCal4par(coordList):
#    # take a LIST of lng and lat [lng1, lat1, lng2, lat2]
#    coordListRads = [radians(x) for x in coordList]
#    d_lng = coordListRads[2] - coordListRads[0]
#    d_lat = coordListRads[3] - coordListRads[1]
#    a = (sin(d_lat/2))**2 + cos(coordListRads[1]) * cos(coordListRads[3]) * (sin(d_lng/2))**2
#    c = 2 * atan2(sqrt(a), sqrt(1-a))
#    return R*c

def distanceCal(coords1, coords2):
    # take two LISTS of coords tuples
    print coords1, coords2
#    coordList = list(coords1+coords2)
    coordListRads = [radians(x) for x in list(coords1 + coords2)]
    d_lng = coordListRads[2] - coordListRads[0]
    d_lat = coordListRads[3] - coordListRads[1]
    a = (sin(d_lat/2))**2 + cos(coordListRads[1]) * cos(coordListRads[3]) * (sin(d_lng/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    dist = R*c
    return dist
    
def scoreError(currentDist, targetDist): # previously distScore
    # calculate sqError of current distance vs user-defined target
    	return (currentDist - targetDist)**2/targetDist**2

def vectorLength(vector):
    return sqrt(vector[0]**2 + vector[1]**2)

def directionVector(u, v):
    dirVec = ((u[0]-v[0])*metersPerLng, (u[1]-v[1])*metersPerLat)
    dirVecLen = vectorLength(dVec)
    dirVecNormalized = (Vec[0]/VecLen, Vec[1]/VecLen)
    return dirVec

def innerProduct(u, v):
    return u[0]*v[0] + u[1]*v[1]

# path is onePath <type list>
def turnScore(path):
    score=0
    if len(path)>3:
        for i in xrange(0, len(path)-2):
            u = directionVector(path[i], path[i+1])
            v = directionVector(path[i+1], path[i+2])
            prod = min(1, max(innerProduct(u,v),-1))
            ang = acos(prod)
            score += ang
    return score

# path is onePath <type list>
def repScore(path, currentDist):
    score = 0
    edgeSet = Set()
    for idx in xrange(1, len(path)):
        key = (path[idx-1], path[idx])
        alterKey = (path[idx], path[idx-1])
        if key not in edgeSet:
            edgeSet.add(key)
        else:
            score += distanceCal(path[idx], path[idx-1])
        if alterKey not in edgeSet:
            edgeSet.add(alterKey)    
        else:
            score += distanceCal(path[idx], path[idx-1])
    return score/currentDist

def Score(path, currentDist, targetDist): # formerly totScoreCal
    # HERE IS WHERE YOU CAN CALCULATE YOUR SCORE
    # YOU CAN CODE IN PENALTIES TO OPTIMIZE HERE
    # CHANGE THESE TO OPTIMIZE
    turnRatio = 0.2
    distRatio = 10
    repRatio = 10

    tScore = turnScore(path)
    dScore = scoreError(currentDist, targetDist)
    rScore = repScore(path, currentDist)

    totalScore = turnRatio*tScore + distRatio*dScore + repRatio*rScore
    return (tScore, dScore, rScore, totalScore)

def calPathDist(lineCoord):
    # no fucking clue wtf this is lollercopter
    pathLength = 0
    try:
        for idx in xrange(1, len(lineCoord)):
            delLen = distanceCal(lineCoord[idx], lineCoord[idx-1])
            pathLength += delLen
    except TypeError:
        return pathLength