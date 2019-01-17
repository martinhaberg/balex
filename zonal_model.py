from pyomo.environ import *
from pyomo.core import Objective
from pyomo.opt import SolverFactory
from powerflow import find_exchange, evaluate_dispatch_feasibility, \
run_nodal_optimization, run_area_opf, find_exchange_difference

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
model.Imbalance =   Param(model.AREAS, within=Reals, mutable=True)
model.Flow_cap =    Param(model.AREAS, model.AREAS, within=NonNegativeReals, mutable=True)

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


# Scripting section
# Generate zonal model instance
instance = model.create_instance("basecasedata.dat")
solver = SolverFactory('gurobi')

zonal_model_feasible = []

print_result = False
# Fetch load scenario
load_base_factor = 1.2  # max 1.8
scale_list = [0.70, 0.66, 0.64, 0.62, 0.65, 0.76, 0.92, 1.05, 1.09, 1.06, \
  1.08, 1.06, 1.02, 1.04, 1.07, 1.15, 1.23, 1.27, 1.25, 1.23, 1.17, 1.17, 1.11, 1.00]
imbalance_range = [0,100]
for scale_factor in scale_list:
    scale = scale_factor*load_base_factor
    print("Load scaled by factor ", round(scale,2))
    initial_dispatch = run_area_opf('all', scale)
    if initial_dispatch['success'] == False:
        print('***Initial dispatch infeasible***')
        pass
    initial_exchange = find_exchange(initial_dispatch)

    # Overwrite ATC limits
    for a in instance.AREAS:
        for z in instance.AREAS:
            if a != z:
                    instance.Flow_cap[a,z] = instance.Flow_cap[a,z]-initial_exchange[a,z]
                    # print(instance.Flow_cap[a,z].value)

    for value in imbalance_range:
        instance.Imbalance['zone1'] = value
        for value in imbalance_range:
            instance.Imbalance['zone2'] = value
            for value in imbalance_range:
                instance.Imbalance['zone3'] = value
                print('Imbalance: ', instance.Imbalance['zone1'].value, instance.Imbalance['zone2'].value, instance.Imbalance['zone3'].value)


                # Solve MODEL instance
                result = solver.solve(instance)
                # print(result.solver.return_code)
                if result.solver.return_code != "0":
                    print("Zonal optimization infeasible")
                    pass
                else:
                    instance.solutions.load_from(result)

                    if print_result:
                        print("\n------ INITIAL DISPATCH ------")
                        print(" EXHANGE")
                        print("  Exch 1-2:", initial_exchange["zone1","zone2"])
                        print("  Exch 1-3:", initial_exchange["zone1","zone3"])
                        print("  Exch 2-3:", initial_exchange["zone2","zone3"])

                    # Result handling
                    bid_activation = {}
                    bid_capacity = {}
                    bid_location = {}

                    for b in instance.BIDS:
                        bid_activation[b] = instance.activation[b].value
                        bid_capacity[b] = instance.Cap[b]
                        bid_location[b] = instance.Node[b]

                    # Nodal benchmark
                    nodal_dispatch = run_nodal_optimization(initial_dispatch, instance.Imbalance, \
                                        bid_capacity, bid_location, instance.Bid_price)
                    a1 = round(nodal_dispatch['gen'][0][1] + nodal_dispatch['gen'][1][1] + \
                        nodal_dispatch['gen'][2][1] + nodal_dispatch['gen'][3][1] + \
                        nodal_dispatch['gen'][4][1] + nodal_dispatch['gen'][5][1] + \
                        nodal_dispatch['gen'][9][1],1)
                    a2 = round(nodal_dispatch['gen'][17][1] + nodal_dispatch['gen'][18][1] + \
                        nodal_dispatch['gen'][19][1] + nodal_dispatch['gen'][20][1] + \
                        nodal_dispatch['gen'][21][1] + nodal_dispatch['gen'][23][1],1)
                    a3 = round(nodal_dispatch['gen'][31][1] + nodal_dispatch['gen'][32][1] + \
                        nodal_dispatch['gen'][36][1] + nodal_dispatch['gen'][38][1] + \
                        nodal_dispatch['gen'][39][1] + nodal_dispatch['gen'][40][1],1)
                    nodal_balancing_exchange = find_exchange_difference(initial_dispatch, nodal_dispatch)

                    if print_result == True:
                        print("\n------ NODAL MODEL ------")
                        if nodal_dispatch['success'] == True:
                            print('Dispatch is feasible')
                        else:
                            print('Dispatch is infeasible')
                        print("Activation cost:", round(nodal_dispatch['f'], 1))
                        print(" ACTIVATED VOLUME")
                        print("  Z1: ", a1)
                        print("  Z2: ", a2)
                        print("  Z3: ", a3)
                        print(" NET POSITION")
                        print("  Z1: ", a1 - instance.Imbalance['zone1'])
                        print("  Z2: ", a2 - instance.Imbalance['zone2'])
                        print("  Z3: ", a3 - instance.Imbalance['zone3'])
                        print(" EXHANGE")
                        print("  Exch 1-2:", nodal_balancing_exchange["zone1","zone2"], "MW")
                        print("  Exch 1-3:", nodal_balancing_exchange["zone1","zone3"], "MW")
                        print("  Exch 2-3:", nodal_balancing_exchange["zone2","zone3"], "MW")

                    # Zonal  MODEL
                    feasible = evaluate_dispatch_feasibility(scale, instance.Imbalance, \
                                bid_activation, bid_location)
                    zonal_model_feasible.append(feasible)
                    if print_result == True:
                        print("\n------ ZONAL MODEL ------")
                        if feasible == True:
                            print('Dispatch is feasible')
                        else:
                            print('Dispatch is infeasible')
                        print("Activation cost: ", round(instance.activation_cost(),1))
                        print(" ACTIVATED VOLUME")
                        print("  Z1: ", sum(instance.activation[b].value for b in instance.BIDS_1))
                        print("  Z2: ", sum(instance.activation[b].value for b in instance.BIDS_2))
                        print("  Z3: ", sum(instance.activation[b].value for b in instance.BIDS_3))
                        print(" NET POSITION")
                        print("  Z1: ", sum(instance.activation[b].value for b in instance.BIDS_1) - \
                                        instance.Imbalance["zone1"])
                        print("  Z2: ", sum(instance.activation[b].value for b in instance.BIDS_2) - \
                                        instance.Imbalance["zone2"])
                        print("  Z3: ", sum(instance.activation[b].value for b in instance.BIDS_3) - \
                                        instance.Imbalance["zone3"])
                        print(" EXHANGE")
                        print("  Exch 1-2:", instance.flow["zone1","zone2"].value, "MW")
                        print("  Exch 1-3:", instance.flow["zone1","zone3"].value, "MW")
                        print("  Exch 2-3:", instance.flow["zone2","zone3"].value, "MW")

# print(zonal_model_feasible)
nFeasible = sum(zonal_model_feasible)
nInfeasible = len(zonal_model_feasible)-nFeasible
print("Zonal dispatches feasible: ", nFeasible)
print("Zonal dispatches infeasible: ", nInfeasible)
