from statistics import mean
from random import sample

BLOCKS = 51

def read_connectivity_matrix(connectivity_file, nodes):
    connectivity_matrix = [ [] for _ in range(nodes)]
    cur_node = 0
    for line in connectivity_file.readlines():
        line = line[line.find(':')+1:]
        connectivity_matrix[cur_node] = [int(x) for x in line.split()]
        cur_node += 1
    return connectivity_matrix

def read_spy_data(spy_data_file):
    spy_data = [ dict() for _ in range(BLOCKS)]
    cur_node = 0
    line_count = -1
    for line in spy_data_file.readlines():
        line_count += 1
        if line_count % 2 == 0:
            continue
        timestamps = line.split(';')
        for val in timestamps:
            if val.find(':') == -1:
                continue
            node, time = val.split(':')
            spy_data[int(line_count / 2)][int(node)] = int(time)
    return spy_data


f1 = open("spy_data", "r")
spy_data = read_spy_data(f1)


NODES = 1000
PUBLIC_NODES = 100
PUBLIC_SPIES = 0
PRIVATE_SPIES = 500

spies = range(PUBLIC_NODES, PUBLIC_NODES + PRIVATE_SPIES)

SMALL_RNG = 50
LARGE_RNG = 75

f2 = open("connectivity_data", "r")
connectivity_data = read_connectivity_matrix(f2, NODES)

def make_connectivity_guess(spy_data):
    nodes_order = []
    for block_data in spy_data:
        block_nodes_order = sorted(block_data, key=block_data.get)
        nodes_order.append(block_nodes_order)
    connectivity_guess = [dict() for _ in range(PUBLIC_NODES)]
    for target_node in range(0, PUBLIC_NODES):
        for block_nodes_order in nodes_order:
            if not target_node in block_nodes_order:
                continue
            block_nodes_order = [item for item in block_nodes_order if item not in set(spies)]
            node_position = block_nodes_order.index(target_node)
            start_close = max(0, node_position - SMALL_RNG)
            start_far = max(0, node_position - LARGE_RNG)
            end_close = min(len(block_nodes_order), node_position + SMALL_RNG)
            end_far = min(len(block_nodes_order), node_position + LARGE_RNG)
            for candidate in block_nodes_order[start_close:end_close]:
                if candidate == target_node:
                    continue
                if not candidate in connectivity_guess[target_node]:
                    connectivity_guess[target_node][candidate] = 2
                else:
                    connectivity_guess[target_node][candidate] += 2
            for candidate in block_nodes_order[start_far:end_far]:
                if candidate == target_node:
                    continue
                if not candidate in connectivity_guess[target_node]:
                    connectivity_guess[target_node][candidate] = 1
                else:
                    connectivity_guess[target_node][candidate] += 1
    return connectivity_guess

WINDOW = 11

guesses = []
real_connectivities = []

def analyze_guess(connectivity_guess):
    precisions = []
    recalls = []
    cur_node = 0
    for node_connectivity_guess in connectivity_guess:
        node_connectivity_sorted = sorted(node_connectivity_guess, key=node_connectivity_guess.get)
        real_connectivity = set(connectivity_data[cur_node]) - set(spies)
        real_connectivity = [x for x in real_connectivity if x < PUBLIC_NODES] # exclude private nodes
        if len(real_connectivity) == 0: # All connected to spies
            cur_node += 1
            continue
        guessed_nodes = node_connectivity_sorted[:int(len(real_connectivity) * WINDOW)]
        if len(guessed_nodes) == 0: # No data no guess
            cur_node += 1
            continue
        intersect = list(set(real_connectivity) & set(guessed_nodes))
        right_guess = len(intersect)
        precision = right_guess / len(guessed_nodes)
        precisions.append(precision)
        recall = right_guess / len(real_connectivity)
        recalls.append(recall)
        real_connectivities.append(real_connectivity)
        cur_node += 1
        break

    # print('Precisions: ', mean(precisions))
    # print('Recalls: ', mean(recalls))
    # print(real_connectivity)
    # print(guessed_nodes)
    guesses.append(guessed_nodes)
    # print(guessed_nodes)

connectivity_guesses = []

STEP = 3
for i in range (0, BLOCKS, STEP):
    connectivity_guess = make_connectivity_guess(spy_data[i:i+STEP])
    connectivity_guesses.append(connectivity_guess)
    analyze_guess(connectivity_guess)
    # print(connectivity_guess)

guess_intersect = set(guesses[0])

# print(guesses)

for guess in guesses:
    guess_intersect = set(guess) & guess_intersect


THRESHOLD = 8
# if at least THRESHOLD
# guess_intersect = []
# for i in range(0, PUBLIC_NODES):
#     found = [i in x for x in guesses]
#     if found.count(True) >= THRESHOLD:
#         guess_intersect.append(i)


print('Guesses intersection: ', guess_intersect)
print('Real connectivity: ', real_connectivities[0])

# guess_intersect = sample(range(0,100), 80)

intersect = list(set(real_connectivities[0]) & set(guess_intersect))
right_guess = len(intersect)
precision = right_guess / len(guess_intersect)
recall = right_guess / len(real_connectivities[0])

print('Precision: ', precision)
print('Recall: ', recall)
