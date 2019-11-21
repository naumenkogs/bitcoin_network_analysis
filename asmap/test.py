from enum import Enum
import bitnodes_asns
import siphash
import ipaddress
import statistics
import random

class Mode(Enum):
    NETGROUP_BUCKETS = 1
    ASN_BUCKETS = 2

class PlacementStrategy(Enum):
    RANDOM = 1,
    FROM_RARE_ASNS = 2,
    FROM_RARE_NETGROUPS = 3,
    FROM_TOP_ASNS = 4,

### SETTINGS

MODE = Mode.ASN_BUCKETS
STRATEGY = PlacementStrategy.FROM_RARE_ASNS

###

### PARAMETERS TO ADJUST

BUCKETS = 256
NODES_TO_CHOOSE = 32
FRACTION_MALICIOUS = 0.1

###

node_to_asn = bitnodes_asns.get_asn_map()
node_to_netgroup = dict()
asn_to_nodes = dict()
netgroup_to_nodes = dict()
all_nodes = node_to_asn.keys()
valid_nodes = []

for node in all_nodes: # parse netgroups and assign
    if node.find('onion') != -1: # Ignore tor for now
        continue
    asn = node_to_asn[node]
    asn_to_nodes.setdefault(asn, []).append(node)
    valid_nodes.append(node)
    ip = node
    port_starts = ip.rfind(':', ) # remove port
    if port_starts != -1:
        ip = ip[:port_starts]
    ip = ip.replace(']', '')
    ip = ip.replace('[', '')
    ip = ipaddress.ip_address(ip)
    if isinstance(ip, ipaddress.IPv4Address):
        node_to_netgroup[node] = (ip.packed[0] << 8) | ip.packed[1]
    elif isinstance(ip, ipaddress.IPv6Address):
        node_to_netgroup[node] = (ip.packed[0] << 24) | (ip.packed[1] << 16) |\
            (ip.packed[2] << 8) | ip.packed[3]
    netgroup = node_to_netgroup[node]
    netgroup_to_nodes.setdefault(netgroup, []).append(node)


## Split asns to reduce variance (can be disabled)
def split_asns(asns_to_split):
    SPLIT_IN_PARTS = 20
    for asn in asns_to_split:
        nodes_to_split = asn_to_nodes[asn]
        part = int(len(nodes_to_split)/SPLIT_IN_PARTS)
        for i in range(SPLIT_IN_PARTS):
            new_asn = asn + '_' + str(i)
            for node in nodes_to_split[i*part:(i+1)*part]:
                asn_to_nodes.setdefault(new_asn, []).append(node)
                node_to_asn[node] = new_asn
        asn_to_nodes.pop(asn)

top_asns = sorted(asn_to_nodes, key = lambda k: len(asn_to_nodes[k]), reverse=True)
split_asns(top_asns[:25])
##


HASH_KEY = b'\x00' * 16
def get_bucket(target, salt, mode):
    if node_to_asn[target] == None or target.find('onion') != -1:
        return -1
    if mode == Mode.ASN_BUCKETS:
        val = node_to_asn[target].replace('AS', '')
    elif mode == Mode.NETGROUP_BUCKETS:
        val = node_to_netgroup[target]
    else:
        assert(0)
    val = str(int(val) + salt)
    hash = siphash.SipHash_2_4(HASH_KEY, val.encode()).hash()
    return hash % BUCKETS

MALICIOUS = int(len(valid_nodes) * FRACTION_MALICIOUS)

# Example of source list is rare ASNs
# Example of mapping is asn_to_nodes
def pick_nodes(source_list, mapping):
    i = 0
    result = []
    source_size = len(source_list)
    while len(result) < MALICIOUS:
        round = int(i / source_size)
        nodes = mapping[source_list[i % source_size]]
        i += 1
        if round >= len(nodes):
            del source_list[i % source_size]
            source_size -= 1
            if source_size == 0:
                print("Not enough nodes to choose from a list")
                assert(0)
            continue
        result.append(nodes[round])
    return result

def mark_malicious_nodes(strategy):
    malicious_nodes = []
    if strategy == PlacementStrategy.RANDOM:
        malicious_nodes = random.sample(valid_nodes, MALICIOUS)
    elif strategy == PlacementStrategy.FROM_RARE_ASNS:
        n_rare_asns = int(len(asn_to_nodes) * 1)
        rare_asns = sorted(asn_to_nodes, key = lambda k: len(asn_to_nodes[k]))[:n_rare_asns]
        malicious_nodes = pick_nodes(rare_asns, asn_to_nodes)
    elif strategy == PlacementStrategy.FROM_RARE_NETGROUPS:
        n_rare_netgroups = int(len(netgroup_to_nodes) * 1)
        rare_netgroups = sorted(netgroup_to_nodes, key = lambda k: len(netgroup_to_nodes[k]))[:n_rare_netgroups]
        malicious_nodes = pick_nodes(rare_netgroups, netgroup_to_nodes)
    elif strategy == PlacementStrategy.FROM_TOP_ASNS:
        top_asns = sorted(asns_to_nodes, key = lambda k: len(asn_to_nodes[k]), reverse=True)[:4]
        malicious_nodes = pick_nodes(top_asns, asn_to_nodes)
        return
    return malicious_nodes

def intersection(lst1, lst2): 
    lst3 = [value for value in lst1 if value in lst2] 
    return lst3 

def choose_nodes(nodes_to_choose):
    added_buckets = []
    added_nodes = []
    salt = random.randint(0, 10000)
    while len(added_nodes) != nodes_to_choose:
        random_node = random.sample(valid_nodes, 1)[0]
        if random_node in added_nodes:
            continue
        bucket = get_bucket(random_node, salt, MODE)
        if bucket in added_buckets:
            continue
        added_buckets.append(bucket)
        added_nodes.append(random_node)
    return added_nodes

def multi_choose_nodes_experiment(tries = 1000):
    results = []
    for i in range (tries):
        malicious_nodes = mark_malicious_nodes(STRATEGY)
        chosen_nodes = choose_nodes(NODES_TO_CHOOSE)
        malicious_chosen_nodes = intersection(malicious_nodes, chosen_nodes)
        results.append(len(malicious_chosen_nodes) / NODES_TO_CHOOSE)
    print("Malicious success: mean ", statistics.mean(results), " stdev ", statistics.stdev(results))

multi_choose_nodes_experiment()



### Analysis of buckets
# bucket_content = dict()
# bucket_asns = dict()

# def assign_buckets(salt = 1):
#     for node, _ in node_to_asn.items():
#         bucket = get_bucket(node, salt, MODE)
#         if bucket == -1: # not assigned
#             continue
#         bucket_content.setdefault(bucket, []).append(node)
#         bucket_asns.setdefault(bucket, set()).append(node)


# # Gives an idea of the bucket content distribution for a particular strategy
# def smallest_buckets_experiment():
#     SMALLEST_N = 32
#     salt = 100
#     assign_buckets(salt)
#     smallest_buckets = sorted(bucket_content, key = lambda k: len(bucket_content[k]))[:SMALLEST_N]
#     smallest_bucket_sizes = [len(bucket_content[x]) for x in smallest_buckets]
#     print('Mean size of N smallest buckets: ', statistics.mean(smallest_bucket_sizes))
