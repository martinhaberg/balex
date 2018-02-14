from pyomo.environ import *
from pyomo.core import Objective
from subproblem import solve_subproblem
from pyomo.opt import SolverFactory
import matplotlib.pyplot as plt

model = AbstractModel()

# Declare sets
model.AREAS = Set()
model.ARCS = Set(dimen=2)
# model.CUTS = Set()

def NodesOut_init(model, node):
    retval = []
    for (i,j) in model.ARCS:
        if i == node:
            retval.append(j)
    return retval
model.NodesOut = Set(model.AREAS, initialize=NodesOut_init)

def NodesIn_init(model, node):
    retval = []
    for (i,j) in model.ARCS:
        if j == node:
            retval.append(i)
    return retval
model.NodesIn = Set(model.AREAS, initialize=NodesIn_init)

# Declare parameters
model.ExchangeCapacity = Param(model.ARCS)
# model.CutOrigin = Param(model.AREAS, model.CUTS)
# model.CutSlope = Param(model.ARCS, model.CUTS)
model.Imbalance = Param(model.AREAS)

# Declare variables
model.AreaCost = Var(model.AREAS, within=NonNegativeReals)
model.AreaActivation = Var(model.AREAS)#, within=NonNegativeReals)
model.Exchange = Var(model.ARCS)#, within=NonNegativeReals)

# Objective
def objective_rule(m):
    return sum(m.AreaCost[a] for a in m.AREAS)
model.objective = Objective(rule=objective_rule, sense=minimize)

# Constraints
def energy_balance_rule(m, a):
    return m.AreaActivation[a] \
     - sum(m.Exchange[a, n] for n in m.NodesOut[a]) \
     - m.Imbalance[a] \
     == 0
model.energy_balance = Constraint(model.AREAS, rule=energy_balance_rule)

def exchange_capacity_rule(m, a, n):
    return m.Exchange[a, n] <= m.ExchangeCapacity[a,n]
model.exchange_capacity = Constraint(model.ARCS, rule=exchange_capacity_rule)

def area_coupling_rule(m,a,n):
    return m.Exchange[a,n] + m.Exchange [n,a] == 0
model.area_coupling = Constraint(model.ARCS, rule=area_coupling_rule)

# def optimality_cuts_rule(m, a, k):
#     return m.AreaCost[a] >= m.CutOrigin[a,k] + sum(m.CutSlope[a,n,k]*m.Exchange[a,n] for n in m.NodesOut[a])
# model.optimality_cuts = Constraint(model.AREAS, model.CUTS, rule=optimality_cuts_rule)
model.optimality_cuts = ConstraintList()



# Create model instance
instance = model.create_instance("data/mpdata3.dat")
solver = SolverFactory('gurobi')

# Solve model instance
result = solver.solve(instance)
instance.solutions.load_from(result)
print('MP solved')

# Initialize parameters
iteration = 0
exchange_suggestion = {}
lower_bound = []
upper_bound = []
max_iterations = 10
tolerance = 0.1

while iteration < max_iterations:
    ub = 0
    print("\nIteration:", iteration)
    for a in instance.AREAS:
        print("")
        # Extract exchange suggestions
        for n in instance.NodesOut[a]:
            if iteration == 0:
                exchange_suggestion[a, n] = 0 # initial SP solution at origin
            else:
                exchange_suggestion[a, n] = instance.Exchange[a, n].value
            print(a,'-', n, exchange_suggestion[a, n])


        # Solve one-area problem, generate cut
        cut_origin, cut_slope, cost = solve_subproblem(a, exchange_suggestion)
        ub += cost
        # print("ub", ub)
        # Add cut to constraint list in master problem
        if cut_origin != None:

            expr = instance.AreaCost[a] - cut_origin
            for n in instance.NodesOut[a]:
                expr -= cut_slope[a, n]*instance.Exchange[a, n]

            instance.optimality_cuts.add(expr >= 0)



        pass
    # Update upper bound - likely error here
    if iteration > 0 and ub > upper_bound[iteration-1]:
        upper_bound.append(upper_bound[iteration-1])
    else:
        upper_bound.append(ub)

    # Solve master problem
    print("\nSolving master problem")
    result = solver.solve(instance)
    instance.solutions.load_from(result)
    print(instance.objective())
    # instance.display()

    # Update lower bound
    lower_bound.append(instance.objective())

    # Compare upper and lower bounds to check convergence
    if upper_bound[iteration] <= lower_bound[iteration] + tolerance:
        break
    else:
        iteration += 1

# Plot bounds
plt.plot(range(len(lower_bound)), lower_bound, range(len(upper_bound)), upper_bound)
plt.ylabel('Total balancing cost')
plt.show()
