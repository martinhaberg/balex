# subproblem
from pypower import *
from pypower.api import *
# case9, ppoption, rundcpf, printpf




# r = rundcpf(ppc, ppopt)

# printpf(r)


def solve_subproblem(area, exchange_demand):
    if area == 'NO1':
        print('Area NO1 recognized. Running 9 bus')
        ppc = loadcase(case9())
        print('case loaded')
        extnode = 1
        exchange = exchange_demand[0]

        ppopt = ppoption(VERBOSE = 0)

        # Add exchange to active power demand
        ppc['bus'][extnode-1][2] += exchange

        r = rundcopf(ppc, ppopt)
        cost = r['f']
        # Nodal price in exchange node
        lambda_exchange = r['mu']['lin']['u'][extnode-1]
        sigma = cost - exchange*lambda_exchange
        return sigma, lambda_exchange
    

    else:
        print('Area not recognized, using case 9')
        ppc = case9()
        exchange = 0

    #ppopt = ppoption(verbose=VERBOSE)
    #, ppopt)
    return None, None
