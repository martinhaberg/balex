# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 14:07:04 2017

@author: martinhab
"""

# Algorithm simulation spec
# Collect list of available BSP offers
# Collect TSO needs
# Load available transport capacities
# Alternative 1: Solve transport problem
    # use pyomo or gurobi model
    # result: activated volumes, netted volumes, satisfied TSO needs etc
    
# What should have a separate class? What are the required functions?
    # Let's start with a simple structure, the market clearing model in the journal article
    # Simple gurobi implementation:

from gurobipy import *


nodes = ['Oslo', 'Drammen', 'NO2']
internalNodes = ['Oslo', 'Drammen']
extAreas = ['NO2', 'SE3']

arcs, arcCapacity = multidict({
    ('Oslo', 'Drammen'):    50,
    ('Drammen', 'Oslo'):    80,
    ('Drammen', 'NO2'):     400,
    ('NO2', 'Drammen'):     100,
    ('Oslo', 'SE3'):        120,
    ('SE3', 'Oslo'):        500})

# intra-area level
imbalanceShare = {
    ('Oslo'):    0.7,
    ('Drammen'): 0.3}


offersUp, offerSizeUp = multidict({
    ('Oslo', 'Hafslund'):       20,
    ('Oslo', 'E-CO'):           70,
    ('Drammen', 'Skagerrak'):   80,
    ('Drammen', 'Statkraft'):   160})

offerPriceUp = {
    ('Oslo', 'Hafslund'):       34,
    ('Oslo', 'E-CO'):           38,
    ('Drammen', 'Skagerrak'):   60,
    ('Drammen', 'Statkraft'):   61}

internalImbalance = 36

externalImbalance = {
    ('NO2'):    100,
    ('SE3'):    100}

# initialize model
m = Model('oneAreaModel')

# add decision variables
flow = m.addVars(arcs, obj=0.1, name='flow')
actUp = m.addVars(offersUp, obj=offerPriceUp, name='activationUp')

# add constraints
m.addConstrs(
    (flow[i,j] <= arcCapacity[i,j] for i,j in arcs), 'flowCap')

# energy balance constraints: internal and external

m.addConstrs(
    (actUp.sum(i,'*') + flow.sum('*', i) - flow.sum(i,'*') - imbalanceShare[i]*internalImbalance == 0 for i in internalNodes), 'eBalInt')
m.addConstrs(
    (actUp.sum(i,'*') + flow.sum('*', i) - flow.sum(i,'*') - externalImbalance[i] == 0 for i in extAreas), 'eBalExt')

m.addConstrs(
    (actUp[i,b] <= offerSizeUp[i,b] for i, b in offersUp), 'offerUpCap')

# Optimize model
m.modelSense = GRB.MINIMIZE
m.optimize()


# Print solution
if m.status == GRB.Status.OPTIMAL:
    flowSolution = m.getAttr('x', flow)
    print('\nOptimal flows:')
    for i,j in arcs:
        if flowSolution[i,j] > 0:
            print('%s -> %s: %g' % (i, j, flowSolution[i,j]))
    actUpSolution = m.getAttr('x', actUp)
    print('\nOptimal upward activation:')
    for i,b in offersUp:
        if actUpSolution[i,b] > 0:
            print('%s, %s: %g' %(i, b, actUpSolution[i,b]))
