"""
network_utils.py
────────────────
Reusable helper functions for drug trafficking network analysis.

Author : Fahad Hameed Khan
License: MIT
"""

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import Counter
from community import community_louvain
from typing import Dict, List, Tuple, Optional


# ── Colour constants ──────────────────────────────────────────────────────────
BG     = '#0d1117'
EDGE_C = '#30363d'
TEXT_C = '#e6edf3'
ACCENT = '#58a6ff'
RED    = '#f85149'
GREEN  = '#3fb950'
YELLOW = '#d29922'

ROLE_COLOR = {
    'Supplier':       RED,
    'Transshipment':  YELLOW,
    'Distributor':    ACCENT,
    'Market':         GREEN,
}


# ── Network descriptives ──────────────────────────────────────────────────────

def network_summary(G: nx.Graph) -> Dict:
    """
    Return a dictionary of key descriptive statistics for a graph.

    Parameters
    ----------
    G : nx.Graph

    Returns
    -------
    dict with keys: nodes, edges, density, connected, avg_degree,
                    clustering, avg_path_length, diameter
    """
    summary = {
        'nodes':           G.number_of_nodes(),
        'edges':           G.number_of_edges(),
        'density':         round(nx.density(G), 4),
        'connected':       nx.is_connected(G),
        'avg_degree':      round(sum(dict(G.degree()).values()) / G.number_of_nodes(), 3),
        'clustering':      round(nx.average_clustering(G), 4),
    }
    if nx.is_connected(G):
        summary['avg_path_length'] = round(nx.average_shortest_path_length(G), 4)
        summary['diameter']        = nx.diameter(G)
    else:
        summary['avg_path_length'] = None
        summary['diameter']        = None
    return summary


def print_summary(G: nx.Graph) -> None:
    """Pretty-print network summary statistics."""
    s = network_summary(G)
    print('=' * 40)
    print('  NETWORK SUMMARY')
    print('=' * 40)
    for k, v in s.items():
        print(f'  {k:<20}: {v}')
    print('=' * 40)


# ── Centrality ────────────────────────────────────────────────────────────────

def compute_all_centrality(G: nx.Graph) -> Dict[str, Dict]:
    """
    Compute degree, betweenness, closeness, and eigenvector centrality.

    Returns
    -------
    dict with keys 'degree', 'betweenness', 'closeness', 'eigenvector'
    """
    return {
        'degree':      nx.degree_centrality(G),
        'betweenness': nx.betweenness_centrality(G, weight='weight'),
        'closeness':   nx.closeness_centrality(G),
        'eigenvector': nx.eigenvector_centrality(G, max_iter=500),
    }


def top_nodes(centrality_dict: Dict, n: int = 10) -> List[Tuple]:
    """
    Return the top-n nodes sorted by centrality score.

    Parameters
    ----------
    centrality_dict : dict  node → score
    n               : int   number of nodes to return

    Returns
    -------
    list of (node, score) tuples
    """
    return sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)[:n]


def print_centrality_table(G: nx.Graph, centrality: Dict[str, Dict], top_n: int = 10) -> None:
    """Print a formatted centrality comparison table."""
    bc   = centrality['betweenness']
    dc   = centrality['degree']
    cc   = centrality['closeness']
    ec   = centrality['eigenvector']
    nodes = [n for n, _ in sorted(bc.items(), key=lambda x: x[1], reverse=True)[:top_n]]

    header = f"{'Node':<6} {'Role':<16} {'Degree':>8} {'Betweenness':>13} {'Closeness':>11} {'Eigenvector':>13}"
    print(header)
    print('-' * len(header))
    for n in nodes:
        role = G.nodes[n].get('role', '?')
        print(f"{n:<6} {role:<16} {dc[n]:>8.3f} {bc[n]:>13.4f} {cc[n]:>11.3f} {ec[n]:>13.4f}")


# ── Community detection ───────────────────────────────────────────────────────

def detect_communities(G: nx.Graph, random_state: int = 42) -> Tuple[Dict, float, int]:
    """
    Run Louvain community detection.

    Returns
    -------
    partition  : dict  node → community_id
    modularity : float
    n_communities : int
    """
    partition     = community_louvain.best_partition(G, random_state=random_state)
    modularity    = community_louvain.modularity(partition, G)
    n_communities = max(partition.values()) + 1
    return partition, modularity, n_communities


def print_communities(G: nx.Graph, partition: Dict) -> None:
    """Print community membership with node roles."""
    n_comms = max(partition.values()) + 1
    for c in range(n_comms):
        members = [n for n, comm in partition.items() if comm == c]
        roles   = Counter([G.nodes[n].get('role', '?') for n in members])
        print(f"Community {c + 1}: {members}")
        print(f"  Role breakdown: {dict(roles)}")


# ── Structural vulnerability ──────────────────────────────────────────────────

def simulate_targeted_removal(
    G:                nx.Graph,
    centrality_dict:  Dict,
    n_removals:       int = 8,
) -> List[Dict]:
    """
    Simulate sequential targeted removal of high-centrality nodes.

    Parameters
    ----------
    G               : original graph (not modified)
    centrality_dict : node → score dict (e.g. betweenness centrality)
    n_removals      : number of nodes to remove

    Returns
    -------
    list of dicts with keys: removals, nodes, components, aspl
    """
    G_copy       = G.copy()
    sorted_nodes = sorted(centrality_dict, key=centrality_dict.get, reverse=True)
    results      = []

    for i in range(n_removals + 1):
        aspl = (
            nx.average_shortest_path_length(G_copy)
            if nx.is_connected(G_copy) and G_copy.number_of_nodes() > 1
            else None
        )
        results.append({
            'removals':   i,
            'nodes':      G_copy.number_of_nodes(),
            'components': nx.number_connected_components(G_copy),
            'aspl':       aspl,
        })
        if i < n_removals and sorted_nodes:
            node_to_remove = sorted_nodes.pop(0)
            if node_to_remove in G_copy:
                G_copy.remove_node(node_to_remove)

    return results


def print_removal_results(results: List[Dict]) -> None:
    """Print formatted removal simulation results."""
    print(f"{'Removed':>8} {'Nodes':>7} {'Components':>12} {'ASPL':>18}")
    print('-' * 50)
    for r in results:
        aspl_str = f"{r['aspl']:.3f}" if r['aspl'] is not None else 'N/A (fragmented)'
        print(f"{r['removals']:>8} {r['nodes']:>7} {r['components']:>12} {aspl_str:>18}")


# ── Plotting helpers ──────────────────────────────────────────────────────────

def styled_axis(ax: plt.Axes) -> None:
    """Apply dark-theme styling to a matplotlib Axes."""
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_edgecolor(EDGE_C)
    ax.tick_params(colors=TEXT_C)


def draw_network(
    G:          nx.Graph,
    pos:        Optional[Dict]  = None,
    ax:         Optional[plt.Axes] = None,
    color_by:   str             = 'role',
    title:      str             = 'Network Graph',
    figsize:    Tuple           = (14, 9),
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Draw a network with dark-theme styling.

    Parameters
    ----------
    G        : graph to draw
    pos      : layout dict (computed if None)
    ax       : existing axes (new figure if None)
    color_by : 'role' uses ROLE_COLOR; 'betweenness' uses plasma colormap
    title    : figure title
    figsize  : figure size

    Returns
    -------
    (fig, ax)
    """
    if pos is None:
        pos = nx.spring_layout(G, seed=42, k=2.2)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, facecolor=BG)
    else:
        fig = ax.get_figure()

    ax.set_facecolor(BG)
    ax.axis('off')
    ax.set_title(title, color=TEXT_C, fontsize=15, fontweight='bold', pad=12)

    if color_by == 'role':
        node_colors = [ROLE_COLOR.get(G.nodes[n].get('role', ''), ACCENT) for n in G.nodes]
    elif color_by == 'betweenness':
        bc     = nx.betweenness_centrality(G, weight='weight')
        bc_arr = np.array([bc[n] for n in G.nodes])
        bc_n   = (bc_arr - bc_arr.min()) / (bc_arr.max() - bc_arr.min() + 1e-9)
        node_colors = [plt.cm.plasma(v) for v in bc_n]
    else:
        node_colors = [ACCENT] * G.number_of_nodes()

    node_sizes   = [G.nodes[n].get('weight', 3) * 180 for n in G.nodes]
    edge_weights = [G[u][v].get('weight', 1) for u, v in G.edges]

    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.35,
                           width=[w * 0.6 for w in edge_weights], edge_color=EDGE_C)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=node_sizes, alpha=0.95)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=7,
                            font_color=TEXT_C, font_weight='bold')

    if color_by == 'role':
        handles = [mpatches.Patch(color=c, label=r) for r, c in ROLE_COLOR.items()
                   if r in set(nx.get_node_attributes(G, 'role').values())]
        ax.legend(handles=handles, loc='lower left',
                  facecolor='#161b22', edgecolor=EDGE_C, labelcolor=TEXT_C, fontsize=9)

    return fig, ax
