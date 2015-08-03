#!/home/gaurav/anaconda/bin/python
"""
Import:
1. main file "BostonBikr.py" 
2. necessary Flask methods
3. app
"""
import BostonBikr
from flask import Flask as Flask, jsonify as FlaskJSONify, render_template as FlaskRender,request as FlaskRequest              
#from app import app 

# Uncomment above and comment below to go back
app = Flask(__name__)
"""
VIEWS
These are handlers that deal with browser requests. This is how Python talks to your webpage. Each view is mapped to at least one request URL.
"""

# This should render the map on the browser
@app.route('/')
def index():
    return FlaskRender('basicTemplate.html') # this might require changing
#    return FlaskRender('myMap.html') # original code

# This should use store the variables from the website to hand to Python
@app.route('/findRoute')
def findRoute():
    # Get your variables from the url via Flask
    startPt = FlaskRequest.args.get('s', '')
    endPt = FlaskRequest.args.get('e', '')
    runDist = float(FlaskRequest.args.get('d', ''))
    # Input the variables into your PYTHON code and process
    # This code will:
    # 1. convert string to gelocation
    # 2. find the nodes in the SQL database(?)
    # 3. calculate the distances and aggregate score
    # 4. decide on a route and return coordinates to plot(?)
    print 'Inside /findRoute'
    print ('startPt is ').format(startPt)
    json = BostonBikr.PathTestMashUp(startPt, endPt, runDist)
    # Check for bad addresses and return empty dict
    if json is None:
        print 'json is None'
        return FlaskJSONify({})
    # Take the output from your Python code and turn it into Json
    # Presumably, the (geo)Json format will allow you to plot your path
    return FlaskJSONify(json)

@app.route('/about')
def about():
    return FlaskRender('about.html')

@app.route('/<other>')
def other(other):
    return about()

# run Flask in debug mode
if __name__ == '__main__':
    app.run(debug = True, port = 5000, host = '0.0.0.0')
