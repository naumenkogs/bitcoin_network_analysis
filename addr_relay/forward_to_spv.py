import time
import random
import sys
import statistics

N_PUB_NODES = 10000
N_PRIV_NODES = 50000
N_SPV_NODES = 600

PUBLIC_NODES = range(0, N_PUB_NODES)
PRIVATE_NODES = range(N_PUB_NODES, N_PUB_NODES + N_PRIV_NODES)
SPV_NODES = range(N_PUB_NODES, N_PUB_NODES + N_SPV_NODES)


OUT_CONNECTIVITY = 8
IN_CONNECTIVITY = 117

def try_connect(node, pub_node, connectivity_graph):
    if node != pub_node and node not in connectivity_graph[pub_node]:
        connectivity_graph[node].append(pub_node)
        connectivity_graph[pub_node].append(node)
        return True
    return False


def build_random_graph():
    connectivity_graph = [[] for _ in range(0, N_PUB_NODES + N_PRIV_NODES)]
    available_pub_nodes = list(PUBLIC_NODES)
    out_connections = [0 for _ in range(0, N_PUB_NODES + N_PRIV_NODES)]
    in_connections = [0 for _ in range(0, N_PUB_NODES)]
    for node in range(0, N_PUB_NODES + N_PRIV_NODES):
        while out_connections[node] != OUT_CONNECTIVITY:
            pub_node = random.choice(available_pub_nodes)
            connected = try_connect(node, pub_node, connectivity_graph)
            if connected:
                out_connections[node] += 1
                in_connections[pub_node] += 1
                if in_connections[pub_node] >= IN_CONNECTIVITY:
                    available_pub_nodes.remove(pub_node)
    return connectivity_graph

WAVES = 360

reachability = 0.05

# returns true with probability of *prob*, otherwise false
def my_rand(prob):
    max = 100
    val = random.randint(0, max)
    return val >= (max * prob)




def relay(connectivity_graph):
    cur_nodes = [PUBLIC_NODES[0]]
    cur_wave = 0
    knowing_nodes = set()
    while cur_wave != WAVES:
        next_wave_nodes = set()
        for node in cur_nodes:
            to_nodes = 1 if my_rand(reachability) else 2
            relay_to = random.sample(connectivity_graph[node], to_nodes)
            # Remove SPVs
            # while True:
            #     good_relays = 0
            #     for relay_node in relay_to:
            #         if relay_node not in SPV_NODES:
            #             good_relays += 1
            #     if good_relays == to_nodes:
            #         break
            #     else:
            #         relay_to = random.sample(connectivity_graph[node], to_nodes)
            for receiver in relay_to:
                knowing_nodes.add(receiver)
                if receiver not in SPV_NODES:
                    next_wave_nodes.add(receiver)
        cur_wave += 1
        cur_nodes = list(next_wave_nodes)
        print(cur_wave)
    return knowing_nodes
                

def experiment():
    connectivity_graph = build_random_graph()
    result = relay(connectivity_graph)
    return len(result)



results = []
for i in range(10):
    res = experiment()
    results.append(res)

print(results)
print(statistics.mean(results))
