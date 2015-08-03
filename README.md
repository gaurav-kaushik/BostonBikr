# BostonBikr
Insight Health Data Science Project 2015
bostonbikr.com

Google will give you the fastest route from A to B and apps like Strava will let you record paths and race yourself and friends. But there are no apps that can generate scenic routes. Routes for the rider who wants to get out, get fit, and see something interesting in their city. That's why I made BostonBikr.

BostonBikr collects Open Source Map (OSM) data (obtained from overpassturbo.eu), cleans it to remove redundant notes (see geojsonProcessor.py), incorporate features from TripAdvisor to add weight your map (see reTrip.py), and allows you to plan novel routes using a custom genetic algorithm (see geneticAlgorithm.py). New features and additional pathfinding algorithms can be easily integrated into BostonBikr.py (see PathTestMashup method). I encourage anyone to try this pipeline on their city and see what they find!

