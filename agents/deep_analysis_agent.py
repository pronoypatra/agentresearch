"""
Deep Mathematical Analysis Agent (Stage 1)

Performs complete mathematical analysis of Tier 1 papers.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from knowledge_base.theorem_db import TheoremDB, Theorem, Definition
from knowledge_base.paper_db import PaperDB


@dataclass
class MathematicalComponent:
    """Represents a mathematical component extracted from a paper"""
    component_type: str  # "theorem", "definition", "bound", "assumption"
    statement: str
    context: str
    paper_section: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


class DeepAnalysisAgent:
    """
    Performs deep mathematical analysis of papers.
    """
    
    def __init__(self, theorem_db: TheoremDB):
        """
        Initialize deep analysis agent.
        
        Args:
            theorem_db: Database for storing extracted theorems
        """
        self.theorem_db = theorem_db
    
    def analyze_paper(self, paper_id: str, paper_content: str) -> Dict:
        """
        Perform deep analysis of a paper.
        
        Args:
            paper_id: Identifier for the paper
            paper_content: LaTeX or text content of the paper
            
        Returns:
            Dictionary containing analysis results
        """
        # Extract mathematical components
        theorems = self._extract_theorems(paper_id, paper_content)
        definitions = self._extract_definitions(paper_id, paper_content)
        bounds = self._extract_bounds(paper_id, paper_content)
        assumptions = self._extract_assumptions(paper_id, paper_content)
        
        # Build dependency graph
        dependencies = self._build_dependencies(theorems, definitions)
        
        # Extract key contributions
        contributions = self._extract_contributions(paper_content)
        
        # Extract research themes
        themes = self._extract_themes(paper_content)
        
        return {
            'theorems': [t.to_dict() for t in theorems],
            'definitions': [d.to_dict() for d in definitions],
            'bounds': bounds,
            'assumptions': assumptions,
            'dependencies': dependencies,
            'contributions': contributions,
            'themes': themes,
        }
    
    def _extract_theorems(self, paper_id: str, content: str) -> List[Theorem]:
        """Extract theorems from paper content"""
        theorems = []
        
        # Look for theorem environments
        theorem_patterns = [
            r'\\begin\{theorem\}(.*?)\\end\{theorem\}',
            r'\\begin\{theorem\*?\}(.*?)\\end\{theorem\*?\}',
            r'\\textbf\{Theorem.*?\}:(.*?)(?=\\textbf|\\begin|$)',
        ]
        
        theorem_count = 0
        for pattern in theorem_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                theorem_count += 1
                theorem_text = match.group(1).strip()
                
                # Extract statement, assumptions, conclusion
                statement = theorem_text[:500]  # Simplified
                assumptions = self._extract_assumptions_from_text(theorem_text)
                conclusion = self._extract_conclusion(theorem_text)
                
                theorem = Theorem(
                    theorem_id=f"{paper_id}_theorem_{theorem_count}",
                    paper_id=paper_id,
                    statement=statement,
                    assumptions=assumptions,
                    conclusion=conclusion,
                    proof_technique=None,  # Would need proof analysis
                )
                theorems.append(theorem)
                self.theorem_db.add_theorem(theorem)
        
        return theorems
    
    def _extract_definitions(self, paper_id: str, content: str) -> List[Definition]:
        """Extract definitions from paper content"""
        definitions = []
        
        # Look for definition environments
        def_patterns = [
            r'\\begin\{definition\}(.*?)\\end\{definition\}',
            r'\\textbf\{Definition.*?\}:(.*?)(?=\\textbf|\\begin|$)',
        ]
        
        def_count = 0
        for pattern in def_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                def_count += 1
                def_text = match.group(1).strip()
                
                # Extract concept name (simplified)
                concept_match = re.search(r'\\textbf\{(.*?)\}', def_text)
                concept = concept_match.group(1) if concept_match else f"concept_{def_count}"
                
                definition = Definition(
                    definition_id=f"{paper_id}_def_{def_count}",
                    paper_id=paper_id,
                    concept=concept,
                    definition_text=def_text[:500],
                )
                definitions.append(definition)
                self.theorem_db.add_definition(definition)
        
        return definitions
    
    def _extract_bounds(self, paper_id: str, content: str) -> List[Dict]:
        """Extract complexity bounds and rates"""
        bounds = []
        
        # Look for bound patterns
        bound_patterns = [
            r'O\(([^)]+)\)',  # Big O notation
            r'\\mathcal\{O\}\(([^)]+)\)',  # LaTeX O
            r'\\Omega\(([^)]+)\)',  # Omega notation
            r'\\Theta\(([^)]+)\)',  # Theta notation
        ]
        
        for pattern in bound_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                bound_expr = match.group(1)
                bounds.append({
                    'expression': bound_expr,
                    'type': 'complexity',
                    'context': content[max(0, match.start()-100):match.end()+100],
                })
        
        return bounds
    
    def _extract_assumptions(self, paper_id: str, content: str) -> List[str]:
        """Extract assumptions from paper"""
        assumptions = []
        
        # Look for assumption sections
        assumption_patterns = [
            r'\\begin\{assumption\}(.*?)\\end\{assumption\}',
            r'\\textbf\{Assumption.*?\}:(.*?)(?=\\textbf|\\begin|$)',
            r'We assume (.*?)(?:\.|$)',
        ]
        
        for pattern in assumption_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                assumption_text = match.group(1).strip()
                assumptions.append(assumption_text[:200])
        
        return assumptions
    
    def _extract_assumptions_from_text(self, text: str) -> List[str]:
        """Extract assumptions from theorem text"""
        assumptions = []
        # Look for "Assume", "Suppose", etc.
        assume_pattern = r'(?:Assume|Suppose|Let)\s+(.*?)(?:\.|,|$)'
        matches = re.finditer(assume_pattern, text, re.IGNORECASE)
        for match in matches:
            assumptions.append(match.group(1).strip())
        return assumptions
    
    def _extract_conclusion(self, text: str) -> str:
        """Extract conclusion from theorem text"""
        # Look for "Then", "Therefore", etc.
        conclusion_pattern = r'(?:Then|Therefore|We have|It follows that)\s+(.*?)(?:\.|$)'
        match = re.search(conclusion_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text[-200:] if len(text) > 200 else text
    
    def _build_dependencies(self, theorems: List[Theorem], definitions: List[Definition]) -> Dict[str, List[str]]:
        """Build dependency graph of theorems and definitions"""
        dependencies = {}
        
        for theorem in theorems:
            deps = []
            # Check if theorem references other theorems or definitions
            statement = theorem.statement.lower()
            for other_theorem in theorems:
                if other_theorem.theorem_id != theorem.theorem_id:
                    # Simple check: if theorem ID or concept appears in statement
                    if other_theorem.paper_id in statement:
                        deps.append(other_theorem.theorem_id)
            
            for definition in definitions:
                if definition.concept.lower() in statement:
                    deps.append(definition.definition_id)
            
            if deps:
                dependencies[theorem.theorem_id] = deps
                theorem.dependencies = deps
        
        return dependencies
    
    def _extract_contributions(self, content: str) -> List[str]:
        """Extract key contributions from paper"""
        contributions = []
        
        # Look for contribution sections
        contrib_patterns = [
            r'\\textbf\{Contributions?\}:(.*?)(?=\\section|\\subsection|$)',
            r'Our main contributions? (?:are|is):(.*?)(?=\\.|$)',
        ]
        
        for pattern in contrib_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                contrib_text = match.group(1).strip()
                # Split into individual contributions
                contrib_items = re.split(r'[•\-\*]', contrib_text)
                contributions.extend([c.strip() for c in contrib_items if c.strip()])
        
        return contributions[:10]  # Limit to top 10
    
    def _extract_themes(self, content: str) -> List[str]:
        """Extract research themes and sub-topics"""
        themes = []
        
        # Look for keywords indicating themes
        theme_keywords = {
            'generalization': ['generalization', 'generalize', 'generalizing'],
            'optimization': ['optimization', 'optimize', 'gradient', 'convex'],
            'complexity': ['complexity', 'sample complexity', 'computational complexity'],
            'convergence': ['convergence', 'converge', 'rate'],
            'regularization': ['regularization', 'regularize', 'penalty'],
        }
        
        content_lower = content.lower()
        for theme, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                themes.append(theme)
        
        return themes

