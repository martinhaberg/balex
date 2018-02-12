from pyomo.environ import *
from subproblem import solve_subproblem

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
model.AreaCost = Var(model.AREAS)#, within=NonNegativeReals)
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


instance = model.create_instance("mpdata3.dat")
exchange_vector = [0, 0, 0, 0]
converged = 0
while converged <= 4:
    for a in instance.AREAS:
        cut_origin, cut_slope = solve_subproblem(a, exchange_vector)

        if cut_origin != None:
            print('Adding cut')
            expr = 0
            for n in instance.NodesOut[a]:
                expr += cut_origin - cut_slope*instance.Exchange[a, n]
            instance.optimality_cuts.add(expr >= 0)
        # Solve one-area problem
        # Generate cut
        # Add cut to constraint list in master problem
        pass
    # Update upper bound
    # Solve master problem
    # Update lower bound
    # Compare upper and lower bounds to check convergence
    pass
    converged += 1

# solver = SolverFactory('ipopt')
# result = solver.solve(instance)#, tee=True)
# instance.display()
