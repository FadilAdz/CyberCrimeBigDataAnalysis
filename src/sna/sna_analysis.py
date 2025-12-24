"""
Social Network Analysis Module
Maps relationships between cyber attack types and identifies patterns.
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import json


class SNAAnalyzer:
    """
    Social Network Analysis for cyber crime attack patterns.
    Builds network graphs and calculates centrality metrics.
    """
    
    def __init__(self, df: pd.DataFrame = None):
        self.df = df
        self.graph = None
        self.communities = None
        self.centrality_metrics = {}
    
    def load_data(self, df: pd.DataFrame) -> 'SNAAnalyzer':
        """Load data for analysis."""
        self.df = df
        return self
    
    def build_attack_network(
        self,
        relationship_type: str = 'sector',
        min_weight: int = 1
    ) -> nx.Graph:
        """
        Build network graph showing relationships between attack types.
        
        Nodes = Attack types
        Edges = Co-occurrence in same sector/province/time period
        Edge weight = Frequency of co-occurrence
        
        Args:
            relationship_type: 'sector', 'province', or 'temporal'
            min_weight: Minimum edge weight to include
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        # Create edge list based on co-occurrence
        edges = defaultdict(int)
        
        if relationship_type == 'sector':
            # Attacks targeting same sector are connected
            for sector in self.df['sector'].unique():
                sector_attacks = self.df[self.df['sector'] == sector]['attack_type'].unique()
                for i, attack1 in enumerate(sector_attacks):
                    for attack2 in sector_attacks[i+1:]:
                        edge = tuple(sorted([attack1, attack2]))
                        edges[edge] += 1
        
        elif relationship_type == 'province':
            # Attacks in same province are connected
            for province in self.df['province'].unique():
                province_attacks = self.df[self.df['province'] == province]['attack_type'].unique()
                for i, attack1 in enumerate(province_attacks):
                    for attack2 in province_attacks[i+1:]:
                        edge = tuple(sorted([attack1, attack2]))
                        edges[edge] += 1
        
        elif relationship_type == 'temporal':
            # Attacks occurring in same month are connected
            if 'date' in self.df.columns:
                self.df['year_month'] = pd.to_datetime(self.df['date']).dt.to_period('M')
                for period in self.df['year_month'].unique():
                    period_attacks = self.df[self.df['year_month'] == period]['attack_type'].unique()
                    for i, attack1 in enumerate(period_attacks):
                        for attack2 in period_attacks[i+1:]:
                            edge = tuple(sorted([attack1, attack2]))
                            edges[edge] += 1
        
        # Build graph
        self.graph = nx.Graph()
        
        # Add nodes with attributes
        attack_counts = self.df['attack_type'].value_counts()
        for attack_type in self.df['attack_type'].unique():
            self.graph.add_node(
                attack_type,
                count=int(attack_counts.get(attack_type, 0)),
                type='attack'
            )
        
        # Add edges
        for (node1, node2), weight in edges.items():
            if weight >= min_weight:
                self.graph.add_edge(node1, node2, weight=weight)
        
        return self.graph
    
    def calculate_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate all centrality metrics for the network.
        
        Returns:
            Dictionary with centrality metrics per node
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_attack_network first.")
        
        # Degree Centrality - Number of connections
        degree_centrality = nx.degree_centrality(self.graph)
        
        # Betweenness Centrality - Bridge role
        betweenness_centrality = nx.betweenness_centrality(self.graph, weight='weight')
        
        # Closeness Centrality - How quickly can reach other nodes
        closeness_centrality = nx.closeness_centrality(self.graph)
        
        # Eigenvector Centrality - Connected to important nodes
        try:
            eigenvector_centrality = nx.eigenvector_centrality(self.graph, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            eigenvector_centrality = {node: 0.0 for node in self.graph.nodes()}
        
        # PageRank
        pagerank = nx.pagerank(self.graph, weight='weight')
        
        self.centrality_metrics = {
            'degree': degree_centrality,
            'betweenness': betweenness_centrality,
            'closeness': closeness_centrality,
            'eigenvector': eigenvector_centrality,
            'pagerank': pagerank
        }
        
        return self.centrality_metrics
    
    def get_top_central_nodes(self, metric: str = 'degree', n: int = 5) -> List[Tuple[str, float]]:
        """Get top N nodes by centrality metric."""
        if not self.centrality_metrics:
            self.calculate_centrality_metrics()
        
        centrality = self.centrality_metrics.get(metric, {})
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_nodes[:n]
    
    def detect_communities(self, algorithm: str = 'louvain') -> Dict[str, int]:
        """
        Detect communities in the network.
        
        Args:
            algorithm: 'louvain', 'greedy', or 'label_propagation'
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_attack_network first.")
        
        if algorithm == 'louvain':
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(self.graph)
            except ImportError:
                # Fallback to greedy modularity
                communities = nx.community.greedy_modularity_communities(self.graph)
                partition = {}
                for i, comm in enumerate(communities):
                    for node in comm:
                        partition[node] = i
        
        elif algorithm == 'greedy':
            communities = nx.community.greedy_modularity_communities(self.graph)
            partition = {}
            for i, comm in enumerate(communities):
                for node in comm:
                    partition[node] = i
        
        elif algorithm == 'label_propagation':
            communities = nx.community.label_propagation_communities(self.graph)
            partition = {}
            for i, comm in enumerate(communities):
                for node in comm:
                    partition[node] = i
        
        self.communities = partition
        return partition
    
    def get_community_summary(self) -> Dict[int, List[str]]:
        """Get summary of detected communities."""
        if self.communities is None:
            self.detect_communities()
        
        community_members = defaultdict(list)
        for node, community_id in self.communities.items():
            community_members[community_id].append(node)
        
        return dict(community_members)
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get overall network statistics."""
        if self.graph is None:
            raise ValueError("Graph not built")
        
        stats = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'avg_clustering': nx.average_clustering(self.graph),
            'is_connected': nx.is_connected(self.graph),
        }
        
        if stats['is_connected']:
            stats['diameter'] = nx.diameter(self.graph)
            stats['avg_path_length'] = nx.average_shortest_path_length(self.graph)
        else:
            # Get stats for largest component
            largest_cc = max(nx.connected_components(self.graph), key=len)
            subgraph = self.graph.subgraph(largest_cc)
            stats['largest_component_size'] = len(largest_cc)
            stats['diameter'] = nx.diameter(subgraph)
            stats['avg_path_length'] = nx.average_shortest_path_length(subgraph)
        
        return stats
    
    def get_centrality_dataframe(self) -> pd.DataFrame:
        """Get centrality metrics as DataFrame for visualization."""
        if not self.centrality_metrics:
            self.calculate_centrality_metrics()
        
        df = pd.DataFrame(self.centrality_metrics)
        df.index.name = 'attack_type'
        df = df.reset_index()
        
        # Add community info
        if self.communities:
            df['community'] = df['attack_type'].map(self.communities)
        
        # Add node count from original data
        if self.df is not None:
            attack_counts = self.df['attack_type'].value_counts()
            df['incident_count'] = df['attack_type'].map(attack_counts)
        
        return df
    
    def export_graph_json(self, filepath: str = None) -> Dict:
        """Export graph to JSON format for visualization."""
        if self.graph is None:
            raise ValueError("Graph not built")
        
        data = {
            'nodes': [
                {
                    'id': node,
                    'count': self.graph.nodes[node].get('count', 0),
                    'community': self.communities.get(node, 0) if self.communities else 0,
                    'degree': self.centrality_metrics.get('degree', {}).get(node, 0),
                    'betweenness': self.centrality_metrics.get('betweenness', {}).get(node, 0)
                }
                for node in self.graph.nodes()
            ],
            'edges': [
                {
                    'source': u,
                    'target': v,
                    'weight': d.get('weight', 1)
                }
                for u, v, d in self.graph.edges(data=True)
            ]
        }
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        
        return data


def analyze_attack_relationships(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Convenience function to run full SNA analysis.
    
    Returns dictionary with all analysis results.
    """
    analyzer = SNAAnalyzer(df)
    
    # Build network
    graph = analyzer.build_attack_network(relationship_type='sector')
    
    # Calculate metrics
    centrality = analyzer.calculate_centrality_metrics()
    
    # Detect communities
    communities = analyzer.detect_communities()
    
    # Get stats
    stats = analyzer.get_network_stats()
    
    return {
        'graph': graph,
        'centrality': centrality,
        'communities': communities,
        'community_summary': analyzer.get_community_summary(),
        'network_stats': stats,
        'centrality_df': analyzer.get_centrality_dataframe(),
        'top_attacks': {
            'by_degree': analyzer.get_top_central_nodes('degree', 5),
            'by_betweenness': analyzer.get_top_central_nodes('betweenness', 5),
            'by_pagerank': analyzer.get_top_central_nodes('pagerank', 5)
        }
    }


if __name__ == '__main__':
    from pathlib import Path
    
    # Test with sample data
    data_path = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'sample_government_data.csv'
    
    if data_path.exists():
        df = pd.read_csv(data_path)
        results = analyze_attack_relationships(df)
        
        print("Network Statistics:")
        for key, value in results['network_stats'].items():
            print(f"  {key}: {value}")
        
        print("\nTop 5 Attack Types by Degree Centrality:")
        for attack, score in results['top_attacks']['by_degree']:
            print(f"  {attack}: {score:.4f}")
        
        print("\nCommunities Detected:")
        for comm_id, members in results['community_summary'].items():
            print(f"  Community {comm_id}: {', '.join(members)}")
