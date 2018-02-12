# subproblem
from pypower import *
from pypower.api import *
# case9, ppoption, rundcpf, printpf




# r = rundcpf(ppc, ppopt)

# printpf(r)


def solve_subproblem(area, exchange_demand):
    if area == 'NO1':
        print('Area', area,' recognized. Running 9 bus')
        ppc = loadcase(case9())
        neighbours = ['NO2']
        extnode = {'NO2': 1}

    elif area == 'NO2':
        print('Area', area,' recognized. Running 9 bus')
        ppc = loadcase(case9())
        neighbours = ['NO1', 'NO5']
        extnode = {'NO1': 2, 'NO5': 9}

    elif area == 'NO5':
        print('Area', area,' recognized. Running 9 bus')
        ppc = loadcase(case9())
        neighbours = ['NO2']
        extnode = {'NO2': 3}

    else:
        return None, None, None

    ppopt = ppoption(OUT_ALL = 0, VERBOSE = 0)

    for neighbour in neighbours:
        ppc['bus'][extnode[neighbour]-1][2] += exchange_demand[area,neighbour]
    # Add exchange to active power demand
    # for i in range(len(neigbours)):
    #     ppc['bus'][extnode[i]-1][2] += exchange[i]

    r = rundcopf(ppc, ppopt)
    cost = r['f']

    # Nodal price in exchange node
    sigma = cost
    lambda_exchange = {}

    for neigbour in neighbours:
        # Round not necessary
        lambda_exchange[area, neigbour] = round(r['mu']['lin']['u'][extnode[neigbour]-1])
        sigma -= exchange_demand[area, neigbour] * lambda_exchange[area, neigbour]
    # for i in range(len(extnode)):
    #
    #     lambda_exchange.append(r['mu']['lin']['u'][extnode[i]-1])
    #     sigma -= exchange[i]*lambda_exchange[i]




    print('Balancing cost:', cost)
    # print('Marginal exchange cost:', lambda_exchange)
    # print('Cost at origin:', sigma)

    return sigma, lambda_exchange, cost
