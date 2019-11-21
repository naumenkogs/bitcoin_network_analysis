import json
try:
    from urllib.request import Request, urlopen  # Python 3
except ImportError:
    from urllib2 import Request, urlopen  # Python 2

req = Request('https://bitnodes.earn.com/api/v1/snapshots/latest/')
req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')
response = urlopen(req).read()

data = json.loads(response.decode())
nodes_info = data['nodes']


def count_meta():
    # print(nodes_info)
    asn_counts = dict()

    for node, info in nodes_info.items():
        asn = info[11]
        if asn in asn_counts:
            asn_counts[asn] += 1
        else:
            asn_counts[asn] = 1

    asn_counts_sorted = sorted(asn_counts, key=asn_counts.get, reverse=True)

    LIMIT = 5
    TOTAL = 10000
    total_in_limit = 0

    i = 0
    for asn in asn_counts_sorted[:LIMIT]:
        if i < 5:
            print(asn)
        i += 1 
        total_in_limit += asn_counts[asn]

    print(LIMIT, 'asns has: ', total_in_limit * 1.0 / TOTAL)
    print(len(asn_counts))


def get_asn_map():
    result = dict()
    for node, info in nodes_info.items():
        result[node] = info[11] # asn
    return result


