# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 17:23:23 2017

@author: martinhab
"""

class Bid:
    
    def __init__(self, name, price, capacity, bidding_zone):
        self.price = price
        self.capacity = capacity
        self.area = bidding_zone
        self.name = name
        self.activated_volume = 0
        self.links_out
        self.links_in
        
    def __repr__(self):
        return repr((self.name, self.price, self.capacity, self.area.name, self.activated_volume))
    
class Area:
    
    def __init__(self, name, imb_forecast):
        self.name = name
        self.forecast = imb_forecast
        self.bids = []
        self.safe_list = []
    
    def __repr__(self):
        return repr((self.name, self.forecast))
    
class Link:
    
    def __init__(self, area1, area2, capacity):
        self.area1 = area1
        self.area2 = area2
        self.capacity = capacity
    
    def __repr__(self):
        return(self.area1, "-", self.area2)