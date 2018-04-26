import networkx as nx
import matplotlib.pyplot as plt


def plot_bounds(lower_bound, upper_bound):
    plt.plot(range(len(lower_bound)), lower_bound, 
             range(len(upper_bound)), upper_bound)
    plt.ylabel('Total balancing cost')
    plt.xlabel('Iteration')
    plt.title('Bounds')
    plt.legend(['Lower bound','Upper bound'])
    plt.show()

def plot_network(exchange):
    # print('Plotting network')
    G = nx.DiGraph()
    # print(exchange)
    locations = {'NO1': [0,0],
                'NO2': [-1,-1],
                'SE3': [2,0]}

    
    for arc, flow in exchange.items():
        # print(arc)
        # print(flow)
        if flow > 0:
            G.add_edge(*arc, weight = flow)
            locations[arc] = []


    # Alternatively, use default positioning
    # pos = nx.spring_layout(G)
    
    # Draw graph
    nx.draw(G, pos = locations, with_labels = True)
    
    # Create nicer edge labels
    edge_labels=dict([((u,v,),round(d['weight']))
        for u,v,d in G.edges(data=True)])
    
    # Draw edge labels
    nx.draw_networkx_edge_labels(G, pos = locations, edge_labels = edge_labels)
    
    plt.show()

def plot_exchange_suggestion(history):
    # plt.plot(range(len()))
    iterations = len(history['NO1','NO2'])
    print(history)
    print(len(history['NO1','NO2']))
    # print(len(history[0:2]))
    
    plt.plot(range(iterations), history['NO1','NO2'],
             range(iterations), history['NO1','SE3'])
    plt.ylabel('Exchange suggestion (MW)')
    plt.xlabel('Iteration')
    plt.title('Exchange suggestions')
    plt.legend(['NO1-NO2','NO1-SE3'])
    plt.xticks()
    plt.show()
    
# def plot_cuts():
    