"""
Query Generation Agent (Stage 2)

Generates diverse search queries from Tier 1 context and user input.
"""

from typing import List, Dict
from agents.context_builder import ContextBuilder
from knowledge_base.paper_db import PaperDB
from knowledge_base.theorem_db import TheoremDB


class QueryGenerationAgent:
    """
    Generates multiple diverse search queries for Tier 2 paper discovery.
    """
    
    def __init__(self, context_builder: ContextBuilder):
        """
        Initialize query generation agent.
        
        Args:
            context_builder: Context builder for accessing Tier 1 insights
        """
        self.context_builder = context_builder
    
    def generate_queries(self, user_query: str, tier1_context: Dict) -> List[str]:
        """
        Generate diverse search queries.
        
        Args:
            user_query: Additional user query for Tier 2
            tier1_context: Context from Tier 1 analysis
            
        Returns:
            List of diverse search queries
        """
        queries = []
        
        # Start with user query
        queries.append(user_query)
        
        # Generate variations based on Tier 1 context
        themes = tier1_context.get('themes', [])
        frameworks = tier1_context.get('frameworks', [])
        concepts = tier1_context.get('concepts', [])
        directions = tier1_context.get('research_directions', [])
        
        # Query variations based on themes
        for theme in themes[:3]:  # Top 3 themes
            queries.append(f"{user_query} {theme}")
            queries.append(f"{theme} extensions")
            queries.append(f"{theme} applications")
        
        # Query variations based on frameworks
        for framework in frameworks[:2]:  # Top 2 frameworks
            queries.append(f"{user_query} {framework}")
            queries.append(f"{framework} improvements")
        
        # Query variations based on concepts
        for concept in concepts[:3]:  # Top 3 concepts
            queries.append(f"{concept} {user_query}")
        
        # Query variations for extensions
        queries.append(f"{user_query} extensions")
        queries.append(f"{user_query} generalizations")
        queries.append(f"{user_query} improvements")
        queries.append(f"{user_query} applications")
        
        # Historical/evolutionary queries
        queries.append(f"{user_query} evolution")
        queries.append(f"{user_query} history")
        queries.append(f"{user_query} development")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)
        
        return unique_queries[:10]  # Return top 10 queries
    
    def rank_queries(self, queries: List[str], tier1_context: Dict) -> List[tuple]:
        """
        Rank queries by importance and diversity.
        
        Args:
            queries: List of queries
            tier1_context: Tier 1 context
            
        Returns:
            List of (query, score) tuples, sorted by score
        """
        scored_queries = []
        
        for query in queries:
            score = 0.0
            
            # Base score for user query
            if query == queries[0]:  # First query is user's original
                score += 1.0
            
            # Diversity score (penalize very similar queries)
            similarity_penalty = 0.0
            query_words = set(query.lower().split())
            for other_query in queries:
                if other_query != query:
                    other_words = set(other_query.lower().split())
                    overlap = len(query_words.intersection(other_words))
                    similarity = overlap / max(len(query_words), len(other_words), 1)
                    if similarity > 0.8:  # Very similar
                        similarity_penalty += 0.1
            
            score -= similarity_penalty
            
            # Relevance to Tier 1 context
            context_words = set()
            for theme in tier1_context.get('themes', []):
                context_words.update(theme.lower().split())
            for framework in tier1_context.get('frameworks', []):
                context_words.update(framework.lower().split())
            
            query_words = set(query.lower().split())
            context_overlap = len(query_words.intersection(context_words))
            if len(context_words) > 0:
                relevance = context_overlap / len(context_words)
                score += relevance * 0.5
            
            scored_queries.append((query, score))
        
        # Sort by score
        scored_queries.sort(key=lambda x: x[1], reverse=True)
        return scored_queries

