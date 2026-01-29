"""Optimized HTML Parser Strategy with multiple backends.

ОПТИМІЗАЦІЯ v4.1:
1. Native Cython parser (найшвидший) - 5-10x швидше
2. selectolax (C-based) - 3-5x швидше за lxml
3. lxml (середній)
4. BeautifulSoup (fallback)
"""

import logging
import re
from typing import Any, Dict, List, Optional

from graph_crawler.application.use_cases.crawling.parsers.base import BaseHTMLParser

logger = logging.getLogger(__name__)

# Special link prefixes to skip
_SPECIAL_PREFIXES = ('javascript:', 'mailto:', 'tel:', '#', 'data:', 'void(')


def _is_special_link(href: str) -> bool:
    """Check if link is special (mailto, javascript, etc.)."""
    return href.startswith(_SPECIAL_PREFIXES)


class HTMLParser(BaseHTMLParser):
    """
    Optimized HTML парсер з автоматичним вибором backend.
    
    Пріоритет backend-ів:
    1. Native Cython (найшвидший) - якщо скомпільовано
    2. selectolax (C-based, 3-5x швидше за lxml)
    3. lxml (середній)
    4. BeautifulSoup (fallback)
    """
    
    _backend: str = None
    _selectolax_available: bool = None
    _native_available: bool = None
    
    def __init__(self):
        """Initialize parser with best available backend."""
        self._detect_backends()
    
    @classmethod
    def _detect_backends(cls):
        """Detect available parsing backends."""
        # Check Native Cython
        if cls._native_available is None:
            try:
                import sys
                sys.path.insert(0, '/app/web_graf/graph_crawler/native')
                from _html_parser import parse_links_fast
                cls._native_available = True
                logger.info("✅ Native Cython HTML parser available")
            except ImportError:
                cls._native_available = False
        
        # Check selectolax
        if cls._selectolax_available is None:
            try:
                from selectolax.parser import HTMLParser as SelectolaxParser
                cls._selectolax_available = True
                logger.info("✅ selectolax HTML parser available")
            except ImportError:
                cls._selectolax_available = False
        
        # Set backend
        if cls._native_available:
            cls._backend = "native_cython"
        elif cls._selectolax_available:
            cls._backend = "selectolax"
        else:
            cls._backend = "beautifulsoup"
        
        logger.info(f"🔧 Using HTML parser backend: {cls._backend}")

    @property
    def name(self) -> str:
        return self._backend or "beautifulsoup"

    def parse(self, html: str) -> Any:
        """
        Парсить HTML через найкращий доступний backend.
        
        Args:
            html: HTML string
            
        Returns:
            Parsed tree object
        """
        if not html:
            return None
        
        if self._backend == "selectolax":
            from selectolax.parser import HTMLParser as SelectolaxParser
            return SelectolaxParser(html)
        else:
            from bs4 import BeautifulSoup
            return BeautifulSoup(html, 'lxml')

    def extract_links(self, tree: Any, base_url: Optional[str] = None) -> List[str]:
        """
        Витягує всі <a href> посилання.
        
        ОПТИМІЗОВАНО:
        - Native Cython: 5-10x швидше
        - selectolax: 3-5x швидше за BeautifulSoup
        
        Args:
            tree: Parsed HTML tree або raw HTML string
            base_url: Base URL for relative links
            
        Returns:
            List of extracted URLs
        """
        # If tree is string, use optimized path
        if isinstance(tree, str):
            return self._extract_links_from_html(tree, base_url)
        
        links = []
        seen = set()
        
        if self._backend == "selectolax" and hasattr(tree, 'css'):
            # selectolax path
            for node in tree.css('a[href]'):
                href = node.attributes.get('href')
                if href and href not in seen and not _is_special_link(href):
                    seen.add(href)
                    links.append(href)
        elif hasattr(tree, 'find_all'):
            # BeautifulSoup path
            for a in tree.find_all('a', href=True):
                href = a.get('href', '')
                if href and href not in seen and not _is_special_link(href):
                    seen.add(href)
                    links.append(href)
        
        return links
    
    def _extract_links_from_html(self, html: str, base_url: Optional[str] = None) -> List[str]:
        """Extract links directly from HTML string using best method."""
        
        # Try Native Cython first
        if self._native_available:
            try:
                import sys
                sys.path.insert(0, '/app/web_graf/graph_crawler/native')
                from _html_parser import parse_links_fast
                return parse_links_fast(html, base_url)
            except Exception as e:
                logger.debug(f"Native parser failed: {e}")
        
        # Try selectolax
        if self._selectolax_available:
            try:
                from selectolax.parser import HTMLParser as SelectolaxParser
                tree = SelectolaxParser(html)
                links = []
                seen = set()
                for node in tree.css('a[href]'):
                    href = node.attributes.get('href')
                    if href and href not in seen and not _is_special_link(href):
                        seen.add(href)
                        links.append(href)
                return links
            except Exception as e:
                logger.debug(f"selectolax parser failed: {e}")
        
        # Fallback to BeautifulSoup
        from bs4 import BeautifulSoup
        tree = BeautifulSoup(html, 'lxml')
        links = []
        seen = set()
        for a in tree.find_all('a', href=True):
            href = a.get('href', '')
            if href and href not in seen and not _is_special_link(href):
                seen.add(href)
                links.append(href)
        return links

    def extract_metadata(self, tree: Any) -> Dict[str, Any]:
        """
        Витягує метадані сторінки.
        
        Returns:
            Dict with title, description, keywords, h1, og tags
        """
        metadata = {
            'title': None,
            'description': None,
            'keywords': None,
            'h1': None,
            'og_title': None,
            'og_description': None,
        }
        
        if tree is None:
            return metadata
        
        if self._backend == "selectolax" and hasattr(tree, 'css_first'):
            # selectolax path
            title = tree.css_first('title')
            metadata['title'] = title.text(strip=True) if title else None
            
            h1 = tree.css_first('h1')
            metadata['h1'] = h1.text(strip=True) if h1 else None
            
            # Meta tags
            for meta in tree.css('meta'):
                name = meta.attributes.get('name', '').lower()
                prop = meta.attributes.get('property', '').lower()
                content = meta.attributes.get('content', '')
                
                if name == 'description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = content
                elif prop == 'og:title':
                    metadata['og_title'] = content
                elif prop == 'og:description':
                    metadata['og_description'] = content
        
        elif hasattr(tree, 'find'):
            # BeautifulSoup path
            title = tree.find('title')
            metadata['title'] = title.get_text(strip=True) if title else None
            
            h1 = tree.find('h1')
            metadata['h1'] = h1.get_text(strip=True) if h1 else None
            
            desc = tree.find('meta', {'name': 'description'})
            metadata['description'] = desc.get('content') if desc else None
            
            keywords = tree.find('meta', {'name': 'keywords'})
            metadata['keywords'] = keywords.get('content') if keywords else None
            
            og_title = tree.find('meta', {'property': 'og:title'})
            metadata['og_title'] = og_title.get('content') if og_title else None
            
            og_desc = tree.find('meta', {'property': 'og:description'})
            metadata['og_description'] = og_desc.get('content') if og_desc else None
        
        return metadata

    def extract_text(self, tree: Any) -> str:
        """
        Витягує весь текст зі сторінки.
        
        Returns:
            Clean text content
        """
        if tree is None:
            return ""
        
        if self._backend == "selectolax" and hasattr(tree, 'text'):
            # Remove script and style tags
            for tag in tree.css('script, style, noscript'):
                tag.decompose()
            return tree.text(separator=' ', strip=True) or ""
        
        elif hasattr(tree, 'get_text'):
            # BeautifulSoup path - remove scripts/styles first
            for tag in tree.find_all(['script', 'style', 'noscript']):
                tag.decompose()
            text = tree.get_text(separator=' ', strip=True)
            # Clean extra whitespace
            return re.sub(r'\s+', ' ', text).strip()
        
        return ""


# Convenience function for quick link extraction
def extract_links_fast(html: str, base_url: Optional[str] = None) -> List[str]:
    """
    Fast link extraction using best available backend.
    
    ОПТИМІЗОВАНО:
    1. Native Cython (5-10x швидше)
    2. selectolax (3-5x швидше)
    3. BeautifulSoup (fallback)
    
    Args:
        html: HTML content
        base_url: Base URL for relative links
        
    Returns:
        List of extracted URLs
    """
    parser = HTMLParser()
    return parser._extract_links_from_html(html, base_url)

