# Filtering methods
# MH, Dec 2018

from pypower import *
from pypower.api import *
from pypower.idx_brch import F_BUS
from customcases import case118_withcap, case118zone1
from plots import plot_gen, plot_load
import numpy as np

def run_area_opf(zone, scale):
    """Runs DCOPF based on pypower case file mapped to the area given as
    argument"""
    if zone == 'all':
        ppc = loadcase(case118_withcap())
    elif zone == 'zone1':
        ppc = loadcase(case118zone1())
    ppopt = ppoption(OUT_ALL = 0, VERBOSE = 0)
    ppc = scale_initial_load(ppc, scale, 0.1)
    r = rundcopf(ppc, ppopt)
    # printpf(r)

    return r

def scale_initial_load(ppc, factor, noise):
    # Pure scaling
    for i in range(118):
        old_load = ppc['bus'][i][2]
        sigma = round(old_load*0.1,1)
        sigma = max(sigma, 0.001)
        # print(sigma)

        new_load = old_load*factor # + np.random.normal(0,sigma,1)[0]
        new_load = max(new_load, 0)
        # print(old_load,"->",new_load)
        ppc['bus'][i][2] = new_load
    return ppc

def find_exchange(result):
    """Identifies exchange flows based on DCOPF result"""
    r = result
    # printpf(r)

    # Branches from zone 1 to zone 2: 44, 47, 53
    exchange_12 = r['branch'][44][13] + r['branch'][47][13] + \
        r['branch'][53][13]
    # Branches from zone 1 to zone 3: 108, 110
    exchange_13 = r['branch'][108][13] + r['branch'][110][13]
    # Branches from zone 2 to zone 3: 107, 115, 118, 125
    exchange_23 = r['branch'][107][13] + r['branch'][115][13] + \
        r['branch'][118][13] + r['branch'][125][13]

    # print(r['branch'][44][13])
    exchange = {}
    exchange[('zone1', 'zone2')] = round(exchange_12)
    exchange[('zone2', 'zone1')] = -round(exchange_12)
    exchange[('zone1', 'zone3')] = round(exchange_13)
    exchange[('zone3', 'zone1')] = -round(exchange_13)
    exchange[('zone2', 'zone3')] = round(exchange_23)
    exchange[('zone3', 'zone2')] = -round(exchange_23)
    # print(exchange)

    return exchange

def find_exchange_difference(initial_dispatch, final_dispatch):
    r1 = initial_dispatch
    r2 = final_dispatch
    # Branches from zone 1 to zone 2: 44, 47, 53
    exchange_12 = r2['branch'][44][13] + r2['branch'][47][13] + \
        r2['branch'][53][13] - \
        r1['branch'][44][13] + r1['branch'][47][13] + \
        r1['branch'][53][13]
    # Branches from zone 1 to zone 3: 108, 110
    exchange_13 = r2['branch'][108][13] + r2['branch'][110][13] - \
    r1['branch'][108][13] + r1['branch'][110][13]
    # Branches from zone 2 to zone 3: 107, 115, 118, 125
    exchange_23 = r2['branch'][107][13] + r2['branch'][115][13] + \
        r2['branch'][118][13] + r2['branch'][125][13] - \
        r1['branch'][107][13] + r1['branch'][115][13] + \
            r1['branch'][118][13] + r1['branch'][125][13]

    # print(r['branch'][44][13])
    exchange = {}
    exchange[('zone1', 'zone2')] = round(exchange_12)
    exchange[('zone2', 'zone1')] = -round(exchange_12)
    exchange[('zone1', 'zone3')] = round(exchange_13)
    exchange[('zone3', 'zone1')] = -round(exchange_13)
    exchange[('zone2', 'zone3')] = round(exchange_23)
    exchange[('zone3', 'zone2')] = -round(exchange_23)

    return exchange


def evaluate_dispatch_feasibility(scale, imbalance, bid_activations, bid_locations):
    """Applies imbalances and bid activations to assess flow feasibility"""
    ppc = loadcase(case118_withcap())
    ppc = scale_initial_load(ppc, scale, 0.1)
    # Subtract initial dispatch
    initial_dispatch = run_area_opf('all', scale)

    ppc = subtract_initial_dispatch(ppc, initial_dispatch)

    # Apply imbalances
    ppc = apply_imbalance(ppc, imbalance)

    # Apply bid activations
    ppc = apply_bid_activations(ppc, bid_activations, bid_locations)

    # Run DCOPF
    ppopt = ppoption(OUT_ALL = 0, VERBOSE = 0)
    r = rundcopf(ppc, ppopt)
    feasible = r['success']
    # print(r['raw'])


    return feasible

def run_nodal_optimization(initial_dispatch, imbalance, bid_capacities, bid_locations, bid_prices):
    """Runs residual DC OPF using balancing bids"""
    # ppc = loadcase(case118())   # error on
    ppc = initial_dispatch
    ppc = subtract_initial_dispatch(ppc, initial_dispatch)
    ppc = apply_imbalance(ppc, imbalance)
    ppc = add_balancing_bids(ppc, bid_capacities, bid_locations, bid_prices)

    # Run DCOPF
    ppopt = ppoption(OUT_ALL = 0, VERBOSE = 0)
    r = rundcopf(ppc, ppopt)

    feasible = r['success']

    # print('Total cost: ', r['f'])
    return r


def add_balancing_bids(ppc, bid_capacities, bid_locations, bid_prices):

    for idx, gen in enumerate(ppc['gen']):
        # Identify generator bus
        # print(idx)
        gen_bus = int(gen[0]-1)

        # Check for bids on this bus
        for bid in bid_capacities:
            bid_bus = int(bid_locations[bid]) - 1
            bid_price = bid_prices[bid]

            if gen_bus == bid_bus:
                # Update gen capacity
                gen[8] = gen[8] + bid_capacities[bid]
                # print("Bid ", bid, " at bus ", bid_bus +1, ' set to ', gen[8], ' MW')

                # Update cost data
                ppc['gencost'][idx][4] = 0
                ppc['gencost'][idx][5] = bid_price
                ppc['gencost'][idx][6] = 0

                # print(ppc['gencost'][idx])
    return ppc

def subtract_initial_dispatch(ppc, initial_dispatch):
    # Return ppc with negative generator loads and gen caps to 0
    # plot_load(ppc)
    for gen in initial_dispatch['gen']:
        gen_bus = int(gen[0]-1)
        gen_power = gen[1]
        if gen_power > 0.1:
            # Subract initial generation from bus load
            ppc['bus'][gen_bus][2] = ppc['bus'][gen_bus][2] - gen_power
            # print('Subracted ', round(gen_power,1), ' MW from bus ', gen_bus+ 1)
    # Set generator capacity to zero
    for gen in ppc['gen']:
        gen[8] = 0

    # To avoid singular problem
    ppc['gen'][0][8] = 0.0001

    return ppc

def apply_imbalance(ppc, imbalance):
        # Return ppc with adjusted nodal injections
        ppc['bus'][9][2] = imbalance['zone1'].value + ppc['bus'][9][2]
        ppc['bus'][68][2] = imbalance['zone2'].value + ppc['bus'][68][2]
        ppc['bus'][88][2] = imbalance['zone3'].value + ppc['bus'][88][2]
        return ppc

def apply_bid_activations(ppc, bid_activations, bid_locations):
    # Return ppc with adjusted nodal injections
    for bid in bid_activations:
        loc = bid_locations[bid] - 1
        act = bid_activations[bid]
        ppc['bus'][loc][2] = ppc['bus'][loc][2] - act

    return ppc

def run_area_opf_with_exchange(zone, exchange):
    if zone == 'zone1':
        ppc = loadcase(case118zone1())
        neighbours = {'zone2': 33, 'zone3': 34}
        for z in neighbours.keys():
            print('Original')
            print(ppc['bus'][neighbours[z]][2])
            ppc['bus'][neighbours[z]][2] = exchange[(zone, z)]# set exchange demand
            print('Adjusted')
            print(ppc['bus'][neighbours[z]][2])
    ppopt = ppoption(OUT_ALL = 0, VERBOSE = 0)
    r = rundcopf(ppc, ppopt)
    # printpf(r)
    return r

def generate_exchange_ranges(ATC_list):
    """Generates balancing energy exchange ranges for each border. Creates
    dictionary of possible flow ranges """
    exchange_ranges = dict()

    # Set range limits from ATC in each direction
    for key in ATC_list:
        from_area, to_area = key
        exchange_ranges[key] = [-ATC_list[to_area, from_area], ATC_list[key]]

    return exchange_ranges
