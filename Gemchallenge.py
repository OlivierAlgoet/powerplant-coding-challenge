#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  3 20:34:42 2021

@author: Olivier Algoet

@summary: Solution for the GEM challenge using recursive forward and backtracking

"""

#imports
from flask import Flask, request, jsonify
import json
import sys



# Increasing recursion limit for loads with a lot of plants
sys.setrecursionlimit(10**6)


    

class MeritOrder:
    
    "This class calculates the merit order given the payload"

    def __init__(self, payload):
        """
        
        Parameters
        ----------
        payload : json
            Load, fuels and plants

        """
        self.load = payload["load"]
        self.fuels = payload['fuels']
        self.powerplants = payload["powerplants"]
        self.payload = payload
        
        
        
    @property
    def MeritOrder(self):
        """
        
        Returns
        -------
        merit_order : list of dictionaries
            All powerplants from low to high cost.

        """
        for plant in self.powerplants:
            self.PlantCost(plant) # add cost per MWh to powerplant
            if plant["type"] == "windturbine":
                # correct dependent on the wind percentage
                plant['pmax'] * self.fuels['wind(%)'] / 100
             

        # sort the powerplants from low to high cost
        merit_order = sorted(self.powerplants, key=lambda k: k['cpm'])

        return merit_order
    
    
    def PlantCost(self, powerplant):
        """
        

        Parameters
        ----------
        powerplant : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if powerplant["type"] == "gasfired":  
             powerplant["cpm"] = self.fuels["gas(euro/MWh)"] / powerplant["efficiency"]
    
        elif powerplant["type"] == "turbojet":
            powerplant["cpm"] = self.fuels["kerosine(euro/MWh)"] / powerplant["efficiency"]
            
        else:
            powerplant["cpm"] = 0 #Windturbine energy is free
           
            
    
class UnitCommitmentProblem:
    
    def __init__(self,MeritOrderObject):
        self.MeritOrderObject=MeritOrderObject
    

    def solve(self):
        solution=self._forwardtracking(self.MeritOrderObject.MeritOrder,self.MeritOrderObject.load,[],0)
        
        if solution==None:
            return []
        solution=solution["solution"]
        solution=[round(s,1) for s in solution]
        solution+=(len(self.MeritOrderObject.MeritOrder)-len(solution))*[0]
        
        ParsedSolution=[]
        for mo,s in zip(self.MeritOrderObject.MeritOrder,solution):
            ParsedSolution.append({"name":mo["name"],"p":s})
        return ParsedSolution
        
    
    def _backtracking(self,MeritOrder,CurrentProposal,LoadNeeded,i):
        """
        _backtracking is a recursive function which tries to free energy in more 
        efficient plants to be able to satify the minimum constraint of a gasfired
        plant.
        The merit order is iterated backwards to free energy first from the least
        efficient plants
        When the minimum current load of a gasfired plant is bigger than the 
        needed load 2 solutions are proposed (One with P=0 and one with P=Pmin)
        The _backtracking function is worst case exponential in calculation.
        This will however not occur since not all plants are gasfired and not all
        gasfired plants will give 2 proposed solutions.
        
        
    
        Parameters
        ----------
        MeritOrder : List of dictionaries
            All plants from low to high cost
        CurrentProposal : List of floats
            List of MWh
        LoadNeeded : Float
            Needed load to free to obtain minimum power constraint of gasfired plant
        i : Integer
            Iterator of plant to check
            
    
        Returns
        -------
        List of dictionaries with new proposals 
        None if the proposal does not satisfy the constraints
        """
        print("currentprop",CurrentProposal)
        NewProposal=CurrentProposal.copy() #Copy to prevent pass by reference
        MO=MeritOrder[i] #Current proposal plant
        
        #Termination condition
        if LoadNeeded<=0 or i<0: 
            NextIndex=len(CurrentProposal)
            NextLoad=MeritOrder[NextIndex]["pmin"]-LoadNeeded
            # Check new load feasibility
            if NextLoad<MeritOrder[NextIndex]["pmin"]:
                
                print("error feas")
                print("backtrack:",NextLoad,MeritOrder[NextIndex]["pmin"])
                print(NewProposal)
                return [None]
            else:
                #Limit proposed load to pmax
                if NextLoad>MeritOrder[NextIndex]["pmax"]:
                    NextLoad=MeritOrder[NextIndex]["pmax"]
                NewProposal.append(NextLoad)
                print("In here end ok")
                cost=0
                #Calculate cost of proposed solution
                for np,mo in zip(NewProposal,MeritOrder):
                    cost+=np*mo["cpm"]
                return [{"cost":cost,"solution":NewProposal}]
            
        #Gasfired
        if MO["type"]=="gasfired":
            print("in here gas")
            # Gasfired plant has enough additional power above pmin
            if (NewProposal[i]-MO["pmin"])>=LoadNeeded:
                NewProposal[i]=NewProposal[i]-LoadNeeded
                LoadNeeded=0
                return self._backtracking(MeritOrder,NewProposal,LoadNeeded,i-1)
            
            # The needed load is more than the current gasfired plant load
            elif NewProposal[i]<=LoadNeeded:
                LoadNeeded-=NewProposal[i]
                NewProposal[i]=0
                return self._backtracking(MeritOrder,NewProposal,LoadNeeded,i-1)
            
            # All other cases
            else: 
                LoadNeeded-=(NewProposal[i]-MO["pmin"])
                NewProposal[i]=MO["pmin"] #First proposal Pmin
                PMinProposal=self._backtracking(MeritOrder,NewProposal,LoadNeeded,i-1)
                LoadNeeded-=NewProposal[i]
                NewProposal[i]=0
                PMinZero=self._backtracking(MeritOrder,NewProposal,LoadNeeded,i-1)
                return PMinProposal+PMinZero
        
        #Windturbine        
        elif MO["type"]=="windturbine":
            print("tubine")
            LoadNeeded-=NewProposal[i]
            NewProposal[i]=0
            
            #Add energy to most efficient next plants if to much energy has been freed
            #Forwarding
            if LoadNeeded<0:
                
                for k in range(i,len(NewProposal)):
                    
                    #Gasfired forward
                    if MeritOrder[k]["type"]=="gasfired":
                        if (NewProposal[k]-LoadNeeded)>MeritOrder[k]["pmin"]:
                            if (NewProposal[k]-LoadNeeded)<MeritOrder[k]["pmax"]:
                                NewProposal[k]-=LoadNeeded
                                LoadNeeded=0
                            else:
                                LoadNeeded+=(MeritOrder[k]["pmax"]-NewProposal[k])
                                NewProposal[k]=MeritOrder[k]["pmax"]
                                
                    #Windturbine forward
                    elif MeritOrder[k]["type"]=="windturbine":
                        if (NewProposal[k]-LoadNeeded)>=MeritOrder[k]["pmax"]:
                            LoadNeeded+=(MeritOrder[k]["pmax"]-NewProposal[k])
                            NewProposal[k]=MeritOrder[k]["pmax"]
                            
                    #Turbojet forward
                    else:
                        if (NewProposal[k]-LoadNeeded)<=MeritOrder[k]["pmax"]:
                            NewProposal[k]-=LoadNeeded
                            LoadNeeded=0
                        else:
                            LoadNeeded+=(MeritOrder[k]["pmax"]-NewProposal[k])
                            NewProposal[k]=MeritOrder[k]["pmax"]
            print("Windturbn",NewProposal)
            return self._backtracking(MeritOrder,NewProposal,LoadNeeded,i-1)
        
        #Turbojet
        else: 
            if NewProposal[i]>LoadNeeded:
                NewProposal[i]-=LoadNeeded
                LoadNeeded=0
            else:
                LoadNeeded-=NewProposal[i]
                NewProposal[i]=0
            return self._backtracking(MeritOrder,NewProposal,LoadNeeded,i-1)
                    
    def _forwardtracking(self,MeritOrder,load,CurrentProposal=[],cost=0):
        """
        _forwardtracking is a recursive function whichs assigns power to the 
        powerplants in the merit order.
        When a plant constraint cannot be satisfied a backtracking is done 
        to free up energy or the plant is not turned on.
    
        Parameters
        ----------
        MeritOrder : List of dictionaries
            All plants from low to high cost
        load : Float
            The total load
        CurrentProposal : List, optional
            List of power plant loads
        cost : Float, optional
            Total cost of proposal
    
        Returns
        -------
        Dictionary
            With solution and cost
    
        """
        
        i=len(CurrentProposal)
        LoadLeft=load-sum(CurrentProposal)
        print(CurrentProposal)
        #Termination condition
        if LoadLeft==0:
            return {"solution":CurrentProposal,"cost":cost}
        
        #Termination with unsatisfactory solution
        if len(CurrentProposal)==len(MeritOrder) and LoadLeft!=0:
            return None
        
        #Windturbine forwarding
        if MeritOrder[i]["type"]=="windturbine":
            if LoadLeft>=MeritOrder[i]["pmax"]:
                CurrentProposal.append(MeritOrder[i]["pmax"])
                cost+=CurrentProposal[i]*MeritOrder[i]["cpm"]
            else:
                CurrentProposal.append(0)
                cost+=CurrentProposal[i]*MeritOrder[i]["cpm"]
                
            return self._forwardtracking(MeritOrder,load,CurrentProposal,cost)
        
        #Turbojet forwarding
        elif MeritOrder[i]["type"]=="turbojet":
            if LoadLeft>MeritOrder[i]["pmax"]:
                CurrentProposal.append(MeritOrder[i]["pmax"])
            else:
                CurrentProposal.append(LoadLeft)
            cost+=CurrentProposal[-1]*MeritOrder[i]["cpm"]
            return self._forwardtracking(MeritOrder,load,CurrentProposal,cost)
        
        #Gasfired forwarding
        elif MeritOrder[i]["type"]=="gasfired":
            
            #Case 1 enough load to fulfill Pmin constraint
            if LoadLeft>MeritOrder[i]["pmin"]:
                if LoadLeft>MeritOrder[i]["pmax"]:
                    CurrentProposal.append(MeritOrder[i]["pmax"])
                    cost+=CurrentProposal[i]*MeritOrder[i]["cpm"]
                    return self._forwardtracking(MeritOrder,load,CurrentProposal,cost)
                else:
                    CurrentProposal.append(LoadLeft)
                    cost+=CurrentProposal[-1]*MeritOrder[i]["cpm"]
                    return self._forwardtracking(MeritOrder,load,CurrentProposal,cost)
                
            #Case 2 load can't fulfill Pmin constraint
            # backtracking needed
            else:
                LoadNeeded=MeritOrder[i]["pmin"]-LoadLeft
                BacktrackList=self._backtracking(MeritOrder,CurrentProposal,LoadNeeded,len(CurrentProposal)-1)
                print("backtrackl",BacktrackList)
                BacktrackProposals=[]
                for bi in BacktrackList:
                    if bi!=None:
                        print("In here")
                        bp=self._forwardtracking(MeritOrder,load,bi["solution"],bi["cost"])
                        if bp!=None:
                            BacktrackProposals.append(bp)
                            
                #Also add 0 load to proposal list
                CurrentProposal.append(0)
                print("zero",CurrentProposal)
                cost+=CurrentProposal[i]*MeritOrder[i]["cpm"]
                ZeroLoadProposal=self._forwardtracking(MeritOrder,load,CurrentProposal,cost)
                print(ZeroLoadProposal)
                if ZeroLoadProposal!=None:
                    BacktrackProposals.append(ZeroLoadProposal)
                print(BacktrackProposals)
                SortedProposals = sorted(BacktrackProposals, key=lambda k: k['cost'])       
                if len(SortedProposals)>0:
                    return SortedProposals[0]
                else:
                    return None
           
            
           
# Simple flask app with desired endpoint
app = Flask(__name__)


@app.route('/productionplan', methods=['POST'])
def GEMChallenge():
    payload = request.get_json()
    print("the payload is :",payload)
    MOObj=MeritOrder(payload)
    solver = UnitCommitmentProblem(MOObj)
    solution = solver.solve()
    print(solution)
    return jsonify(solution)


if __name__ == '__main__':
    app.run(port=8888, debug=False)   

       
    
"""        
import time


for i in range(400):
    with open("load.json","r") as f:
        payload=json.load(f)
    payload["load"]=i*10
    
    prep=UnitCommitmentProblem(payload)
    merit_order=prep.compute_merit_order()
    print(merit_order)
    
    load=prep.load 
    out=_forwardtracking(merit_order,load,[],0)
    start=time.time()

    if out!=None:
        print("The solution is:",out, "the load is: ",payload["load"]," The total sum is ",sum(out["solution"]))
    else:
        print("out is None")

    print("total time is",time.time()-start)
    input()
"""   
       
        
    