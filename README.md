# BostonBikr
Insight Health Data Science Project 2015 by Gaurav Kaushik

Website: www.bostonbikr.com

Google will give you the fastest route from A to B and apps like Strava will let you record paths and race against yourself and your friends. But I couldn't find an app for the rider that wants to get outside and get fit while taking in the best scenery their city has to offer. That's why I made BostonBikr.

The code behind BostonBikr includes a pipeline that takes Open Source Map (OSM) data and removes redundant nodes and edges to clean it and allows the user to store their map as a Python Graph() object, a Pandas dataframe, or My/Postrgres-SQL database (see geojsonProcessor.py), incorporate features from TripAdvisor to add weight your map (see reTrip.py), and uses a custom genetic algorithm to generate novel routes (see geneticAlgorithm.py). New features and additional pathfinding algorithms can be easily integrated into BostonBikr.py (see PathTestMashup method). The files for a Flask-based webapp are included here as well. I encourage anyone to try this pipeline on their city and see what they find, or try adding more data to the feature set and optimize it to your desired experience!

Please check out the app at www.bostonbikr.com and feel free to send me feedback!
