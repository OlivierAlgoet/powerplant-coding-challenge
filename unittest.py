#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 15:12:40 2021

@author: Olivier Algoet

@summary: Simple unit test of the GEM challenge
"""

import json
import os
import requests

URL="http://localhost:8888/productionplan"
textfile = open("unit_test_results.txt", "w")
#Get loads
LoadDir="example_payloads"
LoadList=os.listdir(LoadDir)

def ConclusionWriter(file,LoadJson, RespJson):
    if len(RespJson)!=0:
        file.write(json.dumps(RespJson)+"\n")
        totalLoad=0
        for item in RespJson:
            totalLoad+=abs(item["p"]) # abs to be certain no negative powers slip in
        desiredLoad=LoadJson["load"]
        if totalLoad==desiredLoad:
            file.write("Solution correct: The desired load equals the delivered load!\n")
        else:
            file.write("Solution wrong: The desired load DOES NOT equal the delivered load\n")
    else:
        file.write("No solution found!\n")
        
# Testing example loads
for load in LoadList:
    loadfile=os.path.join(LoadDir,load)
    with open(loadfile,"rb") as f:
        loadJson=json.load(f)
    resp=requests.post(URL,json=loadJson)
    JsonResp=resp.json()
    textfile.write("Testing {}\n".format(loadfile))
    ConclusionWriter(textfile,loadJson,JsonResp)
    
            

# Testing example loads from 0 to total max load of plants
textfile.write("Testing for different kinds of loads\n")
for load in LoadList:
    loadfile=os.path.join(LoadDir,load)
    with open(loadfile,"rb") as f:
        loadJson=json.load(f)
    MaxLoad=0
    for item in loadJson["powerplants"]:
        MaxLoad+=item["pmax"]
    
    iters=MaxLoad//10
    for i in range(iters):
        loadJson["load"]=i*10
        resp=requests.post(URL,json=loadJson)
        JsonResp=resp.json()
        textfile.write("Testing {} with load {}\n".format(loadfile,loadJson["load"]))
        ConclusionWriter(textfile,loadJson,JsonResp)


