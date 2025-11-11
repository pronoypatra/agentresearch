"""
Stage 1: Tier 1 Paper Search Agent

Searches for and ranks the top 10 most relevant papers for deep analysis.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import requests
import time


@dataclass
class PaperMetadata:
    """Metadata for a research paper"""
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: Optional[str] = None
    publication_date: Optional[datetime] = None
    citation_count: int = 0
    url: Optional[str] = None
    source: str = "unknown"  # "arxiv", "semantic_scholar", etc.
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'arxiv_id': self.arxiv_id,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'citation_count': self.citation_count,
            'url': self.url,
            'source': self.source,
        }


class Stage1PaperSearchAgent:
    """
    Searches for Tier 1 papers from multiple sources.
    """
    
    def __init__(self, max_results: int = 10):
        """
        Initialize the search agent.
        
        Args:
            max_results: Maximum number of papers to return (default: 10)
        """
        self.max_results = max_results
        self.arxiv_base_url = "http://export.arxiv.org/api/query"
        self.semantic_scholar_base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def search(self, query: str, seed_papers: Optional[List[str]] = None) -> List[PaperMetadata]:
        """
        Search for papers and return top results.
        
        Args:
            query: Research query string
            seed_papers: Optional list of seed papers (arXiv IDs, URLs, or paper titles)
            
        Returns:
            List of top-ranked paper metadata
        """
        all_papers = []
        
        # Search arXiv
        arxiv_papers = self._search_arxiv(query)
        all_papers.extend(arxiv_papers)
        
        # Search Semantic Scholar
        semantic_papers = self._search_semantic_scholar(query)
        all_papers.extend(semantic_papers)
        
        # Process seed papers if provided
        if seed_papers:
            seed_metadata = self._process_seed_papers(seed_papers)
            all_papers.extend(seed_metadata)
        
        # Deduplicate and rank
        unique_papers = self._deduplicate(all_papers)
        ranked_papers = self._rank_papers(unique_papers, query)
        
        # Return top N
        return ranked_papers[:self.max_results]
    
    def _search_arxiv(self, query: str, max_results: int = 50) -> List[PaperMetadata]:
        """Search arXiv API"""
        papers = []
        
        try:
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            response = requests.get(self.arxiv_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse XML response (simplified - in production use proper XML parser)
            content = response.text
            
            # Extract entries (simplified parsing)
            entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
            
            for entry in entries:
                try:
                    # Extract title
                    title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                    title = title_match.group(1).strip() if title_match else "Unknown"
                    title = re.sub(r'\s+', ' ', title)  # Clean whitespace
                    
                    # Extract authors
                    authors = re.findall(r'<name>(.*?)</name>', entry)
                    
                    # Extract abstract
                    abstract_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                    abstract = abstract_match.group(1).strip() if abstract_match else ""
                    abstract = re.sub(r'\s+', ' ', abstract)
                    
                    # Extract arXiv ID
                    arxiv_id_match = re.search(r'arxiv.org/abs/(\d+\.\d+)', entry)
                    if not arxiv_id_match:
                        arxiv_id_match = re.search(r'<id>.*?arxiv.org/abs/(\d+\.\d+)</id>', entry)
                    arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else None
                    
                    # Extract publication date
                    published_match = re.search(r'<published>(.*?)</published>', entry)
                    published_str = published_match.group(1) if published_match else None
                    publication_date = None
                    if published_str:
                        try:
                            publication_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    # Extract URL
                    url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
                    
                    paper = PaperMetadata(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        arxiv_id=arxiv_id,
                        publication_date=publication_date,
                        url=url,
                        source="arxiv"
                    )
                    papers.append(paper)
                    
                except Exception as e:
                    print(f"Error parsing arXiv entry: {e}")
                    continue
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error searching arXiv: {e}")
        
        return papers
    
    def _search_semantic_scholar(self, query: str, max_results: int = 50) -> List[PaperMetadata]:
        """Search Semantic Scholar API"""
        papers = []
        
        try:
            # Note: Semantic Scholar API requires API key for higher rate limits
            # This is a simplified version that may need API key
            params = {
                'query': query,
                'limit': min(max_results, 100),
                'fields': 'title,authors,abstract,paperId,publicationDate,citationCount,url'
            }
            
            headers = {}
            # Add API key if available
            # headers['x-api-key'] = os.getenv('SEMANTIC_SCHOLAR_API_KEY', '')
            
            response = requests.get(
                self.semantic_scholar_base_url,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('data', [])[:max_results]:
                    try:
                        authors = [f"{a.get('name', '')}" for a in item.get('authors', [])]
                        
                        publication_date = None
                        if item.get('publicationDate'):
                            try:
                                pub_date_str = item['publicationDate']
                                publication_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
                            except:
                                pass
                        
                        paper = PaperMetadata(
                            title=item.get('title', 'Unknown'),
                            authors=authors,
                            abstract=item.get('abstract', ''),
                            arxiv_id=item.get('paperId'),  # Semantic Scholar ID, not arXiv
                            publication_date=publication_date,
                            citation_count=item.get('citationCount', 0),
                            url=item.get('url'),
                            source="semantic_scholar"
                        )
                        papers.append(paper)
                    except Exception as e:
                        print(f"Error parsing Semantic Scholar result: {e}")
                        continue
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error searching Semantic Scholar: {e}")
            # Fallback: return empty list if API fails
        
        return papers
    
    def _process_seed_papers(self, seed_papers: List[str]) -> List[PaperMetadata]:
        """Process seed papers provided by user"""
        processed = []
        
        for seed in seed_papers:
            try:
                # Try to extract arXiv ID
                arxiv_match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', seed)
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)
                    # Fetch paper details
                    paper = self._fetch_arxiv_paper(arxiv_id)
                    if paper:
                        processed.append(paper)
                else:
                    # Treat as title/query and search
                    results = self._search_arxiv(seed, max_results=1)
                    if results:
                        processed.append(results[0])
            except Exception as e:
                print(f"Error processing seed paper {seed}: {e}")
        
        return processed
    
    def _fetch_arxiv_paper(self, arxiv_id: str) -> Optional[PaperMetadata]:
        """Fetch a specific paper from arXiv"""
        try:
            params = {
                'id_list': arxiv_id,
            }
            
            response = requests.get(self.arxiv_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            content = response.text
            entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
            
            if entries:
                entry = entries[0]
                title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                title = title_match.group(1).strip() if title_match else "Unknown"
                title = re.sub(r'\s+', ' ', title)
                
                authors = re.findall(r'<name>(.*?)</name>', entry)
                
                abstract_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                abstract = abstract_match.group(1).strip() if abstract_match else ""
                abstract = re.sub(r'\s+', ' ', abstract)
                
                published_match = re.search(r'<published>(.*?)</published>', entry)
                published_str = published_match.group(1) if published_match else None
                publication_date = None
                if published_str:
                    try:
                        publication_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                return PaperMetadata(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    arxiv_id=arxiv_id,
                    publication_date=publication_date,
                    url=f"https://arxiv.org/abs/{arxiv_id}",
                    source="arxiv"
                )
        except Exception as e:
            print(f"Error fetching arXiv paper {arxiv_id}: {e}")
        
        return None
    
    def _deduplicate(self, papers: List[PaperMetadata]) -> List[PaperMetadata]:
        """Remove duplicate papers"""
        seen = set()
        unique = []
        
        for paper in papers:
            # Use arXiv ID if available, otherwise use title
            key = paper.arxiv_id if paper.arxiv_id else paper.title.lower()
            
            if key and key not in seen:
                seen.add(key)
                unique.append(paper)
        
        return unique
    
    def _rank_papers(self, papers: List[PaperMetadata], query: str) -> List[PaperMetadata]:
        """
        Rank papers by relevance.
        
        Scoring factors:
        - Relevance to query (simple keyword matching for now)
        - Citation count
        - Recency
        """
        scored_papers = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for paper in papers:
            score = 0.0
            
            # Relevance score (keyword matching)
            title_lower = paper.title.lower()
            abstract_lower = paper.abstract.lower()
            
            title_matches = sum(1 for word in query_words if word in title_lower)
            abstract_matches = sum(1 for word in query_words if word in abstract_lower)
            
            relevance_score = (title_matches * 2 + abstract_matches) / max(len(query_words), 1)
            score += relevance_score * 0.4
            
            # Citation score (normalized)
            citation_score = min(paper.citation_count / 100.0, 1.0)  # Cap at 100 citations
            score += citation_score * 0.3
            
            # Recency score (prefer recent papers)
            if paper.publication_date:
                years_ago = (datetime.now() - paper.publication_date.replace(tzinfo=None)).days / 365.0
                recency_score = max(0, 1.0 - years_ago / 10.0)  # Decay over 10 years
                score += recency_score * 0.3
            else:
                score += 0.1  # Small penalty for missing date
            
            scored_papers.append((score, paper))
        
        # Sort by score (descending)
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        
        return [paper for _, paper in scored_papers]

