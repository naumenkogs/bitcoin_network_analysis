from dijkstar import Graph, find_path
import random
import sys
import statistics


def read_connectivity_matrix(connectivity_file, nodes):
    connectivity_matrix = [ [] for _ in range(nodes)]
    cur_node = 0
    for line in connectivity_file.readlines():
        line = line[line.find(':')+1:]
        connectivity_matrix[cur_node] = [int(x) for x in line.split()]
        cur_node += 1
    return connectivity_matrix

def add_random_connectivity(nodes, public_nodes, connectivity, connectivity_matrix):
    random.seed(1)
    for cur_node in range(nodes):
        while len(connectivity_matrix[cur_node]) < connectivity:
            random_node = random.randint(0, public_nodes)
            if random_node == cur_node:
                continue
            connectivity_matrix[cur_node].append(random_node)
            connectivity_matrix[random_node].append(cur_node)
    return connectivity_matrix

# Helper
def read_tx_missing_matrix(tx_missing_file, nodes):
    tx_missing_matrix = [ [] for _ in range(nodes)]
    cur_node = 0
    for line in tx_missing_file.readlines():
        line = line[line.find(':')+1:]
        elements = [int(x) for x in line.split()]
        for el in elements:
            tx_missing_matrix[cur_node].append(el)
        cur_node += 1
    return tx_missing_matrix

# Takes a connectivity graph (as adj matrix) and transactions missing by nodes (as set of lists)
def compute_path(adj_matrix, tx_missing_matrix, node1, node2, nodes):
    graph = Graph()
    # Update tx_missing_matrix so that we don't count txs missing by node1
    source_missing_txs = tx_missing_matrix[node1]
    for cur_node in range (nodes):
        tx_missing_matrix[cur_node] = list(set(tx_missing_matrix[cur_node]) - set(source_missing_txs))

    cur_node = 0
    for cur_node in range (nodes):
        cur_node_peers = adj_matrix[cur_node]

        for peer in cur_node_peers:
            if tx_missing_matrix[peer] == []:
                graph.add_edge(cur_node, peer, {'cost': 0.5})
            else:
                graph.add_edge(cur_node, peer, {'cost': 1.5})
        cur_node += 1
    cost_func = lambda u, v, e, prev_e: e['cost']
    return find_path(graph, node1, node2, cost_func=cost_func), tx_missing_matrix


## @separate_block_relay: 0 if no separate network, N=connectivity of separate network otherwise
def analyze(nodes, protocol, connectivity, node1, node2, public_nodes, separate_block_relay=0, empty_blocks=False):
    f1 = open("connectivity_data/" + connectivity, "r")
    connectivity_matrix = read_connectivity_matrix(f1, nodes)
    if separate_block_relay != 0:
        connectivity_matrix = add_random_connectivity(nodes, public_nodes, int(connectivity) + separate_block_relay, connectivity_matrix)

    if empty_blocks:
        tx_missing_matrix = [ [] for _ in range(nodes)]
    else:
        f2 = open("tx_missing_data/" + protocol + '_' + connectivity, "r")
        tx_missing_matrix = read_tx_missing_matrix(f2, nodes)


    missing_txs_counts_public = []
    missing_txs_counts_private = []
    all_results = []
    edges = []

    random.seed(1)
    for _ in range(30):
        node1 = random.randint(public_nodes, nodes)
        node2 = random.randint(public_nodes, nodes)
        assert(node1 != node2)

        path, tx_missing_matrix_after = compute_path(connectivity_matrix, tx_missing_matrix, node1, node2, nodes)

        for lst in tx_missing_matrix_after[:public_nodes]:
            missing_txs_counts_public.append(len(lst))

        for lst in tx_missing_matrix_after[public_nodes:]:
            missing_txs_counts_private.append(len(lst))

        all_results.append(path.total_cost)
        edges.append(len(path.edges))
    return all_results, edges, missing_txs_counts_public, missing_txs_counts_private

nodes = 60000
public_nodes = 10000

protocol_name = sys.argv[1]
connectivity = sys.argv[2]
separate_block_relay_connectivity = int(sys.argv[3])
empty_blocks = bool(sys.argv[4]) if len(sys.argv) > 4 else False

results, edges, missing_txs_counts_public, missing_txs_counts_private = analyze(nodes,
    protocol_name, connectivity, 0, 0, public_nodes, separate_block_relay_connectivity, empty_blocks)

print(protocol_name, connectivity, separate_block_relay_connectivity)
print('Mean, RTT: ', statistics.mean(results))
# # print('Standard deviation, RTT', statistics.stdev(results))
print('Mean, hops:', statistics.mean(edges))
print('Missing transactions avg, public: ', statistics.mean(missing_txs_counts_public))
print('Missing transactions avg, private: ', statistics.mean(missing_txs_counts_private))
