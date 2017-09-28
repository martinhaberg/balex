# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 15:57:06 2017

@author: martinhab
"""

from balancing import *
    
# Define areas
NO1 = Area("NO1", 54)
NO2 = Area("NO2", -12)
areas = [NO1, NO2]

# Add links
links = []
links.append(Link(NO1, NO2, 100))

# Populate bids
ha = Bid("Hafslund", 48, 20, NO1)
ec = Bid("E-CO", 35, 50, NO1)
bids = [ha, ec]
# Assign bids to area

for bid in bids:
    bid.area.bids.append(bid)
    
# Process lists for each area
# Compile safe list
for area in areas:
    # As a starting point, all areas are safe, repeated in sorted order
    area.safe_list = sorted(area.bids, key=lambda bid: bid.price)

for area in areas:
    activated = 0
    remaining_imbalance = area.forecast
    while remaining_imbalance != 0:
        for bid in area.bids:
            actVol = min([remaining_imbalance, bid.capacity-bid.activated_volume])
            bid.activated_volume = actVol
            remaining_imbalance -= actVol
            print(actVol, " MW activated in ", bid.name)
