from powerflow import find_initial_exchange, evaluate_dispatch_feasibility, run_nodal_optimization
from plots import plot_network
from pyomo.environ import *
from pyomo.core import Objective
from pyomo.opt import SolverFactory




# Pyomo model
model = AbstractModel()

# Sets
model.BIDS = Set()
model.BIDS_1 = Set()
model.BIDS_2 = Set()
model.BIDS_3 = Set()
model.AREAS = Set()

# Parameters
model.Bid_price =   Param(model.BIDS, within=NonNegativeReals)
model.Cap =         Param(model.BIDS, within=NonNegativeReals)
model.Node =        Param(model.BIDS, within=NonNegativeReals)
model.Imbalance =   Param(model.AREAS, within=Reals)
model.Flow_cap =    Param(model.AREAS, model.AREAS, within=NonNegativeReals)

# Variables
model.activation = Var(model.BIDS, within=NonNegativeReals)
model.flow = Var(model.AREAS, model.AREAS)
model.flow_pos = Var(model.AREAS, model.AREAS, within=NonNegativeReals)

# Objective
def activation_cost_rule(model):
    return sum(model.Bid_price[b]*model.activation[b] for b in model.BIDS) + \
    0.00001*sum(sum(model.flow_pos[a_from, a_to] for a_from in model.AREAS) for a_to in model.AREAS)
model.activation_cost = Objective(rule=activation_cost_rule)

# # Energy balance Constraints
# def energy_balance_rule(model):
#     return sum(model.activation[b] for b in model.BIDS) == 16
# model.energy_balance = Constraint(rule=energy_balance_rule)

# Individual area energy energy_balance
def zonal_energy_balance_1_rule(model):
    return sum(model.activation[b] for b in model.BIDS_1) + \
    sum(model.flow[z_from, "zone1"] for z_from in model.AREAS) == model.Imbalance["zone1"]
model.zonal_energy_balance_1 = Constraint(rule=zonal_energy_balance_1_rule)

def zonal_energy_balance_2_rule(model):
    return sum(model.activation[b] for b in model.BIDS_2) + \
    sum(model.flow[z_from, "zone2"] for z_from in model.AREAS) == model.Imbalance["zone2"]
model.zonal_energy_balance_2 = Constraint(rule=zonal_energy_balance_2_rule)

def zonal_energy_balance_3_rule(model):
    return sum(model.activation[b] for b in model.BIDS_3) + \
    sum(model.flow[z_from, "zone3"] for z_from in model.AREAS) == model.Imbalance["zone3"]
model.zonal_energy_balance_3 = Constraint(rule=zonal_energy_balance_3_rule)

# Bid capacity Constraints
def bid_capacity_rule(model, b):
    return model.activation[b] <= model.Cap[b]
model.bid_capacity = Constraint(model.BIDS, rule = bid_capacity_rule)

# Flow capacity Constraints
def flow_capacity_rule(model, a_from, a_to):
    return model.flow[a_from, a_to] <= model.Flow_cap[a_from, a_to]
model.flow_capacity = Constraint(model.AREAS, model.AREAS, rule=flow_capacity_rule)

def flow_positive_term_rule(model, a_from, a_to):
    return model.flow[a_from, a_to] <= model.flow_pos[a_from, a_to]
model.flow_positive_term = Constraint(model.AREAS, model.AREAS, rule=flow_positive_term_rule)

# Flow consistency Constraints
def flow_consistency_rule(model, a_from, a_to):
    return model.flow[a_to, a_from] == - model.flow[a_from, a_to]
model.flow_consistency = Constraint(model.AREAS, model.AREAS, rule=flow_consistency_rule)

instance = model.create_instance("filtering_model_data.dat")
solver = SolverFactory('gurobi')
result = solver.solve(instance)
instance.solutions.load_from(result)
print("Activation cost: ", instance.activation_cost())
# instance.display()
balancing_flow = {}


for a in instance.AREAS:
    for z in instance.AREAS:
        if a != z:
                balancing_flow[a,z] = instance.flow[a,z].value

bid_activation = {}
bid_capacity ={}
bid_location = {}

for b in instance.BIDS:
    bid_activation[b] = instance.activation[b].value
    bid_capacity[b] = instance.Cap[b]
    bid_location[b] = instance.Node[b]
#
# print(balancing_flow)
# # plot_network(balancing_flow)
#
# # Find initial exchange situation
initial_exchange = find_initial_exchange()
# print(initial_exchange)

# plot_network(initial_exchange)

feasible = evaluate_dispatch_feasibility(instance.Imbalance, bid_activation, \
                            bid_location)



# nodal = run_nodal_optimization(instance.Imbalance, bid_capacity, bid_location, instance.Bid_price)
