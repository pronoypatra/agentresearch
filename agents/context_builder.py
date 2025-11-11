"""
Context Builder (Stage 1)

Synthesizes insights from Tier 1 deep analysis to build research context.
"""

from typing import Dict, List, Set
from knowledge_base.theorem_db import TheoremDB
from knowledge_base.paper_db import PaperDB


class ContextBuilder:
    """
    Builds research context from Tier 1 analysis.
    """
    
    def __init__(self, theorem_db: TheoremDB, paper_db: PaperDB):
        """
        Initialize context builder.
        
        Args:
            theorem_db: Database with extracted theorems
            paper_db: Database with paper metadata
        """
        self.theorem_db = theorem_db
        self.paper_db = paper_db
    
    def build_context(self, tier1_paper_ids: List[str]) -> Dict:
        """
        Build research context from Tier 1 papers.
        
        Args:
            tier1_paper_ids: List of Tier 1 paper IDs
            
        Returns:
            Dictionary containing research context
        """
        # Extract key themes
        themes = self._extract_themes(tier1_paper_ids)
        
        # Extract key concepts
        concepts = self._extract_concepts(tier1_paper_ids)
        
        # Extract theoretical frameworks
        frameworks = self._extract_frameworks(tier1_paper_ids)
        
        # Extract research directions
        directions = self._extract_research_directions(tier1_paper_ids)
        
        # Build summary
        summary = self._build_summary(themes, concepts, frameworks, directions)
        
        return {
            'themes': themes,
            'concepts': concepts,
            'frameworks': frameworks,
            'research_directions': directions,
            'summary': summary,
        }
    
    def _extract_themes(self, paper_ids: List[str]) -> List[str]:
        """Extract common themes across papers"""
        all_themes = set()
        
        for paper_id in paper_ids:
            paper = self.paper_db.get_paper(paper_id)
            if paper and paper.content:
                # Simple keyword-based theme extraction
                content_lower = paper.content.lower()
                theme_keywords = {
                    'generalization': ['generalization', 'generalize'],
                    'optimization': ['optimization', 'gradient', 'convex'],
                    'complexity': ['complexity', 'sample complexity'],
                    'convergence': ['convergence', 'rate'],
                    'regularization': ['regularization', 'penalty'],
                    'deep_learning': ['neural network', 'deep learning', 'backpropagation'],
                    'pac_learning': ['PAC', 'VC dimension', 'sample complexity'],
                }
                
                for theme, keywords in theme_keywords.items():
                    if any(kw in content_lower for kw in keywords):
                        all_themes.add(theme)
        
        return list(all_themes)
    
    def _extract_concepts(self, paper_ids: List[str]) -> List[str]:
        """Extract key mathematical concepts"""
        concepts = set()
        
        for paper_id in paper_ids:
            definitions = self.theorem_db.get_paper_definitions(paper_id)
            for definition in definitions:
                concepts.add(definition.concept)
        
        return list(concepts)
    
    def _extract_frameworks(self, paper_ids: List[str]) -> List[str]:
        """Extract theoretical frameworks"""
        frameworks = set()
        
        for paper_id in paper_ids:
            paper = self.paper_db.get_paper(paper_id)
            if paper and paper.content:
                content_lower = paper.content.lower()
                
                framework_keywords = {
                    'VC Theory': ['VC dimension', 'VC theory', 'shattering'],
                    'Rademacher Complexity': ['Rademacher', 'Rademacher complexity'],
                    'PAC Learning': ['PAC', 'probably approximately correct'],
                    'Information Theory': ['entropy', 'mutual information', 'KL divergence'],
                    'Convex Optimization': ['convex', 'convex optimization', 'gradient descent'],
                }
                
                for framework, keywords in framework_keywords.items():
                    if any(kw in content_lower for kw in keywords):
                        frameworks.add(framework)
        
        return list(frameworks)
    
    def _extract_research_directions(self, paper_ids: List[str]) -> List[str]:
        """Extract research directions and extensions"""
        directions = []
        
        for paper_id in paper_ids:
            paper = self.paper_db.get_paper(paper_id)
            if paper and paper.content:
                # Look for "future work", "extensions", etc.
                future_work_pattern = r'(?:future work|extensions?|open problems?):(.*?)(?=\\section|$)'
                import re
                matches = re.finditer(future_work_pattern, paper.content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    directions.append(match.group(1).strip()[:200])
        
        return directions[:10]  # Limit to top 10
    
    def _build_summary(self, themes: List[str], concepts: List[str], 
                      frameworks: List[str], directions: List[str]) -> str:
        """Build a summary of the research context"""
        summary_parts = []
        
        if themes:
            summary_parts.append(f"Key themes: {', '.join(themes)}")
        
        if frameworks:
            summary_parts.append(f"Theoretical frameworks: {', '.join(frameworks)}")
        
        if concepts:
            summary_parts.append(f"Key concepts: {', '.join(concepts[:5])}")
        
        if directions:
            summary_parts.append(f"Research directions identified: {len(directions)}")
        
        return ". ".join(summary_parts) if summary_parts else "Context building in progress..."

