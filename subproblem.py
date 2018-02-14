# subproblem
from pypower import *
from pypower.api import *
# case9, ppoption, rundcpf, printpf




# r = rundcpf(ppc, ppopt)

# printpf(r)


def solve_subproblem(area, exchange_demand):
    if area == 'NO1':
        print('Area', area,': 6 bus')
        ppc = loadcase(case6ww())
        neighbours = ['NO2', 'SE3']
        extnode = {'NO2': 4, 'SE3': 6}
        ppc['gencost'][0][5] += 20
        ppc['gencost'][1][5] += 20
        ppc['gencost'][2][5] += 20


    elif area == 'NO2':
        print('Area', area,': 14 bus')
        ppc = loadcase(case14())
        neighbours = ['NO1']
        extnode = {'NO1': 14}

    elif area == 'SE3':
        print('Area', area,': 9 bus')
        ppc = loadcase(case9())
        neighbours = ['NO1']
        extnode = {'NO1': 9}
        # ppc['gencost'][0][5] += 10
        # ppc['gencost'][1][5] += 10

    else:
        return None, None, None

    ppopt = ppoption(OUT_ALL = 0, VERBOSE = 0)

    for neighbour in neighbours:
        print(ppc['bus'][extnode[neighbour]-1][2])
        ppc['bus'][extnode[neighbour]-1][2] += exchange_demand[area,neighbour]
        print(ppc['bus'][extnode[neighbour]-1][2])
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
        # print(neighbour, r['mu']['lin']['u'][extnode[neigbour]-1]/100)
        lambda_exchange[area, neigbour] = r['mu']['lin']['u'][extnode[neigbour]-1]/100
        sigma -= exchange_demand[area, neigbour] * lambda_exchange[area, neigbour]
    # for i in range(len(extnode)):
    #
        # lambda_exchange.append(r['mu']['lin']['u'][extnode[i]-1])
        # sigma -= exchange[i]*lambda_exchange[i]




    print('Balancing cost:', round(cost))
    print('Marginal exchange cost:', lambda_exchange)
    print('Cost at origin:', sigma)

    return sigma, lambda_exchange, cost
