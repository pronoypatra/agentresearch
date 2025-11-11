"""
Temporal Graph

Stores temporal relationships between papers and concepts.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import networkx as nx


@dataclass
class TemporalEdge:
    """Edge in temporal graph"""
    source: str
    target: str
    edge_type: str  # "cites", "extends", "contradicts", etc.
    timestamp: Optional[datetime] = None


class TemporalGraph:
    """
    Graph representing temporal evolution of research.
    """
    
    def __init__(self):
        """Initialize temporal graph"""
        self.graph = nx.DiGraph()  # Directed graph
        self.paper_timestamps: Dict[str, datetime] = {}
    
    def add_paper(self, paper_id: str, timestamp: Optional[datetime] = None):
        """Add a paper node"""
        self.graph.add_node(paper_id, node_type='paper')
        if timestamp:
            self.paper_timestamps[paper_id] = timestamp
    
    def add_edge(self, source: str, target: str, edge_type: str = "cites"):
        """Add an edge between papers"""
        self.graph.add_edge(source, target, edge_type=edge_type)
    
    def get_temporal_sequence(self) -> List[str]:
        """Get papers in chronological order"""
        papers_with_dates = [
            (pid, ts) for pid, ts in self.paper_timestamps.items()
        ]
        papers_with_dates.sort(key=lambda x: x[1])
        return [pid for pid, _ in papers_with_dates]
    
    def get_evolution_path(self, start_paper: str, end_paper: str) -> Optional[List[str]]:
        """Get evolution path between two papers"""
        try:
            path = nx.shortest_path(self.graph, start_paper, end_paper)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_temporal_clusters(self) -> Dict[int, List[str]]:
        """Get papers clustered by time period (e.g., by year)"""
        clusters: Dict[int, List[str]] = {}
        for paper_id, timestamp in self.paper_timestamps.items():
            year = timestamp.year
            if year not in clusters:
                clusters[year] = []
            clusters[year].append(paper_id)
        return clusters

