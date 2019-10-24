import time
import random
import sys
import statistics

N_PUB_NODES = 10000
N_PRIV_NODES = 50000
N_TOTAL_NODES = N_PRIV_NODES + N_PUB_NODES

N_SPV_NODES = 600
FRACTION_EXOTIC_NODES = 0.05 # Multi-homed by default
FRACTION_EXOTIC_ONLY_NODES = 0.3 # Fraction of EXOTIC_NODES, which connect only to other exotic nodes


PUBLIC_NODES = range(0, N_PUB_NODES)
PRIVATE_NODES = range(N_PUB_NODES, N_TOTAL_NODES)

SPV_NODES = range(N_PUB_NODES, N_PUB_NODES + N_SPV_NODES)
EXOTIC_NODES = list(range(0, int(N_PUB_NODES * FRACTION_EXOTIC_NODES))) + list(range(N_PUB_NODES + N_SPV_NODES, int(N_PRIV_NODES * FRACTION_EXOTIC_NODES)))
EXOTIC_ONLY_NODES = random.sample(EXOTIC_NODES, int(len(EXOTIC_NODES) * FRACTION_EXOTIC_ONLY_NODES))

OUT_CONNECTIVITY = 8
IN_CONNECTIVITY = 117

def is_exotic(node):
    return node in EXOTIC_NODES

def is_exotic_only(node):
    return node in EXOTIC_ONLY_NODES

def is_spv(node):
    return node in SPV_NODES 

def try_connect(node, pub_node, connectivity_graph):
    if node != pub_node and node not in connectivity_graph[pub_node]:
        connectivity_graph[node].append(pub_node)
        connectivity_graph[pub_node].append(node)
        return True
    return False

def intersection(lst1, lst2): 
    lst3 = [value for value in lst1 if value in lst2] 
    return lst3

def build_random_graph():
    connectivity_graph = [[] for _ in range(0, N_PUB_NODES + N_PRIV_NODES)]
    available_pub_nodes = list(PUBLIC_NODES)
    available_exotic_nodes = intersection(available_pub_nodes, EXOTIC_ONLY_NODES)
    out_connections = [0 for _ in range(0, N_PUB_NODES + N_PRIV_NODES)]
    in_connections = [0 for _ in range(0, N_PUB_NODES)]
    for node in range(0, N_PUB_NODES + N_PRIV_NODES):
        while out_connections[node] != OUT_CONNECTIVITY:
            if is_exotic_only(node):
                pub_node = random.choice(available_exotic_nodes)
            else:
                pub_node = random.choice(available_pub_nodes)

            connected = try_connect(node, pub_node, connectivity_graph)
            if connected:
                out_connections[node] += 1
                in_connections[pub_node] += 1
                if in_connections[pub_node] >= IN_CONNECTIVITY:
                    available_pub_nodes.remove(pub_node)
                    available_exotic_nodes.remove(pub_node)
                    
    return connectivity_graph

WAVES = 360
REMOVE_SPV = true

def relay(connectivity_graph):
    cur_nodes = random.sample(PUBLIC_NODES, 1)
    cur_wave = 0
    knowing_nodes = set()
    while cur_wave != WAVES:
        next_wave_nodes = set()
        for node in cur_nodes:
            to_nodes = 2 if is_exotic(node) else 1
            relay_to = random.sample(connectivity_graph[node], to_nodes)
            # Remove SPVs
            while True:
                good_relays = 0
                for relay_node in relay_to:
                    if relay_node not in SPV_NODES:
                        good_relays += 1
                if good_relays == to_nodes:
                    break
                else:
                    relay_to = random.sample(connectivity_graph[node], to_nodes)
            for receiver in relay_to:
                knowing_nodes.add(receiver)
                if receiver not in SPV_NODES:
                    next_wave_nodes.add(receiver)
        cur_wave += 1
        cur_nodes = list(next_wave_nodes)
        if cur_wave % 30 == 0:
            print(cur_wave)
            # print('Knowing nodes', len(knowing_nodes))
            # knowing_ex = intersection(knowing_nodes, EXOTIC_NODES)
            # print('Knowing exotic nodes', len(knowing_ex))
            # if cur_wave == 50:
            #     break
    return knowing_nodes
                

def experiment():
    connectivity_graph = build_random_graph()
    result_all = relay(connectivity_graph)
    result_exotic = intersection(result_all, EXOTIC_NODES)
    return len(result_all), len(result_exotic)

results_all = []
results_exotic = []
EXPERIMENTS = 20

for i in range(EXPERIMENTS):
    res_all, result_exotic = experiment()
    results_all.append(res_all)
    results_exotic.append(result_exotic)

# TODO remove spvs?

print('All nodes results')
print(statistics.mean(results_all) / N_TOTAL_NODES)
print('Exotic nodes results')
print(statistics.mean(results_exotic) / len(EXOTIC_NODES))
