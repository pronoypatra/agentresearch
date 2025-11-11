"""
Notation Extraction Agent

Extracts mathematical notations from LaTeX papers and catalogs them with context.
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class NotationType(Enum):
    """Types of mathematical notations"""
    VARIABLE = "variable"
    VECTOR = "vector"
    MATRIX = "matrix"
    FUNCTION = "function"
    SET = "set"
    OPERATOR = "operator"
    CONSTANT = "constant"
    DISTRIBUTION = "distribution"
    UNKNOWN = "unknown"


@dataclass
class NotationContext:
    """Context information for a notation"""
    definition_text: Optional[str] = None
    surrounding_text: Optional[str] = None
    equation_context: Optional[str] = None
    domain_keywords: List[str] = field(default_factory=list)
    paper_section: Optional[str] = None
    citation_context: Optional[str] = None


@dataclass
class ExtractedNotation:
    """Represents an extracted mathematical notation"""
    symbol: str
    latex: str
    notation_type: NotationType
    context: NotationContext
    first_occurrence: int  # Line number or position
    occurrences: List[int] = field(default_factory=list)
    semantic_meaning: Optional[str] = None
    dimension: Optional[str] = None
    domain: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'symbol': self.symbol,
            'latex': self.latex,
            'type': self.notation_type.value,
            'context': {
                'definition': self.context.definition_text,
                'surrounding': self.context.surrounding_text,
                'equation': self.context.equation_context,
                'domain_keywords': self.context.domain_keywords,
                'section': self.context.paper_section,
            },
            'first_occurrence': self.first_occurrence,
            'occurrences': self.occurrences,
            'semantic_meaning': self.semantic_meaning,
            'dimension': self.dimension,
            'domain': self.domain,
        }


class NotationExtractor:
    """
    Extracts mathematical notations from LaTeX papers.
    """
    
    # Common notation patterns
    VECTOR_PATTERNS = [
        r'\\mathbf\{([a-zA-Z])\}',  # \mathbf{w}
        r'\\vec\{([a-zA-Z])\}',     # \vec{x}
        r'\\boldsymbol\{([a-zA-Z])\}',  # \boldsymbol{\theta}
    ]
    
    MATRIX_PATTERNS = [
        r'\\mathbf\{([A-Z])\}',  # Bold uppercase
        r'([A-Z])\\in\\mathbb\{R\}',  # Matrix in R^nxm
    ]
    
    SET_PATTERNS = [
        r'\\mathcal\{([A-Z])\}',  # Calligraphic
        r'\\mathbb\{([A-Z])\}',   # Blackboard bold
    ]
    
    # Domain keywords for context
    DOMAIN_KEYWORDS = {
        'optimization': ['gradient', 'loss', 'objective', 'minimize', 'convex', 'regularization'],
        'statistics': ['variance', 'expectation', 'distribution', 'likelihood', 'estimator'],
        'information_theory': ['entropy', 'mutual information', 'KL divergence', 'channel'],
        'deep_learning': ['neural network', 'layer', 'activation', 'backpropagation', 'weights'],
        'pac_learning': ['PAC', 'sample complexity', 'generalization', 'VC dimension'],
    }
    
    def __init__(self):
        self.extracted_notations: Dict[str, ExtractedNotation] = {}
    
    def extract_from_latex(self, latex_content: str, paper_id: str = None) -> List[ExtractedNotation]:
        """
        Extract all notations from LaTeX content.
        
        Args:
            latex_content: The LaTeX source of the paper
            paper_id: Optional identifier for the paper
            
        Returns:
            List of extracted notations
        """
        lines = latex_content.split('\n')
        extracted = []
        
        # Find all math environments
        math_blocks = self._find_math_blocks(latex_content)
        
        # Extract notations from each block
        for block, start_pos, end_pos in math_blocks:
            notations = self._extract_from_math_block(block, start_pos, lines)
            extracted.extend(notations)
        
        # Extract context from surrounding text
        for notation in extracted:
            self._enrich_with_context(notation, lines, latex_content)
        
        return extracted
    
    def _find_math_blocks(self, content: str) -> List[tuple]:
        """Find all math blocks in the content"""
        blocks = []
        
        # Find inline math
        for match in re.finditer(r'\$([^$]+)\$', content):
            blocks.append((match.group(1), match.start(), match.end()))
        
        # Find display math
        for match in re.finditer(r'\\\[([^\]]+)\\\]', content):
            blocks.append((match.group(1), match.start(), match.end()))
        
        # Find equation environments
        for match in re.finditer(
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            content, re.DOTALL
        ):
            blocks.append((match.group(1), match.start(), match.end()))
        
        return blocks
    
    def _extract_from_math_block(self, math_block: str, position: int, lines: List[str]) -> List[ExtractedNotation]:
        """Extract notations from a single math block"""
        notations = []
        
        # Extract vectors
        for pattern in self.VECTOR_PATTERNS:
            for match in re.finditer(pattern, math_block):
                symbol = match.group(1)
                latex = match.group(0)
                notation = ExtractedNotation(
                    symbol=symbol,
                    latex=latex,
                    notation_type=NotationType.VECTOR,
                    context=NotationContext(),
                    first_occurrence=position,
                    occurrences=[position]
                )
                notations.append(notation)
        
        # Extract matrices
        for pattern in self.MATRIX_PATTERNS:
            for match in re.finditer(pattern, math_block):
                symbol = match.group(1)
                latex = match.group(0)
                notation = ExtractedNotation(
                    symbol=symbol,
                    latex=latex,
                    notation_type=NotationType.MATRIX,
                    context=NotationContext(),
                    first_occurrence=position,
                    occurrences=[position]
                )
                notations.append(notation)
        
        # Extract sets
        for pattern in self.SET_PATTERNS:
            for match in re.finditer(pattern, math_block):
                symbol = match.group(1)
                latex = match.group(0)
                notation = ExtractedNotation(
                    symbol=symbol,
                    latex=latex,
                    notation_type=NotationType.SET,
                    context=NotationContext(),
                    first_occurrence=position,
                    occurrences=[position]
                )
                notations.append(notation)
        
        # Extract simple variables (Greek letters, single letters)
        variable_pattern = r'([a-zA-Z]|\\[a-zA-Z]+)'
        for match in re.finditer(variable_pattern, math_block):
            symbol = match.group(1)
            # Skip if already captured or is a command
            if any(n.symbol == symbol for n in notations):
                continue
            if symbol.startswith('\\') and len(symbol) > 2:
                continue  # Likely a LaTeX command, not a variable
            
            notation = ExtractedNotation(
                symbol=symbol,
                latex=symbol,
                notation_type=NotationType.VARIABLE,
                context=NotationContext(),
                first_occurrence=position,
                occurrences=[position]
            )
            notations.append(notation)
        
        return notations
    
    def _enrich_with_context(self, notation: ExtractedNotation, lines: List[str], full_content: str):
        """Enrich notation with contextual information"""
        # Find surrounding text
        line_num = notation.first_occurrence
        if line_num < len(lines):
            # Get surrounding lines
            start = max(0, line_num - 3)
            end = min(len(lines), line_num + 3)
            surrounding = '\n'.join(lines[start:end])
            notation.context.surrounding_text = surrounding
        
        # Detect domain from keywords
        domain_keywords = []
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(keyword in full_content.lower() for keyword in keywords):
                domain_keywords.append(domain)
        notation.context.domain_keywords = domain_keywords
        
        # Try to find definition
        definition_patterns = [
            rf'Let\s+{re.escape(notation.symbol)}\s+be',
            rf'Define\s+{re.escape(notation.symbol)}\s+as',
            rf'where\s+{re.escape(notation.symbol)}\s+is',
            rf'{re.escape(notation.symbol)}\s*=\s*',  # Direct definition
        ]
        
        for pattern in definition_patterns:
            match = re.search(pattern, full_content, re.IGNORECASE)
            if match:
                # Extract definition context
                start = max(0, match.start() - 100)
                end = min(len(full_content), match.end() + 100)
                notation.context.definition_text = full_content[start:end]
                break

