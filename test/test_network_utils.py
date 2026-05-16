import sys
sys.path.insert(0, '../scripts')

import networkx as nx
from network_utils import network_summary, compute_all_centrality, top_nodes

# You'll need to import or copy build_trafficking_network here
# simplest: paste the function at the top of this file

def test_network_size():
    G = build_trafficking_network()
    assert G.number_of_nodes() == 26
    assert G.number_of_edges() > 0

def test_network_connected():
    G = build_trafficking_network()
    assert nx.is_connected(G)

def test_top_nodes_returns_correct_length():
    G = build_trafficking_network()
    centrality = compute_all_centrality(G)
    result = top_nodes(centrality['betweenness'], n=5)
    assert len(result) == 5

def test_summary_keys():
    G = build_trafficking_network()
    s = network_summary(G)
    assert 'nodes' in s and 'density' in s
