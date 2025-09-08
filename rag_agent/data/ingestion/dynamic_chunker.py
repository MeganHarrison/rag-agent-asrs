"""
Dynamic Chunk Sizing for FM Global Content

This module provides intelligent chunking strategies that adapt based on content type
and structure, ensuring better preservation of important information.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of FM Global content requiring different chunking strategies."""
    TABLE = "table"
    FIGURE_CAPTION = "figure_caption"
    REQUIREMENT = "requirement"
    EQUATION = "equation"
    PROCEDURE = "procedure"
    GENERAL_TEXT = "general_text"
    LIST = "list"
    TECHNICAL_SPEC = "technical_spec"


@dataclass
class ChunkConfig:
    """Configuration for chunking based on content type."""
    size: int
    overlap: int
    min_size: int
    max_size: int
    preserve_structure: bool
    split_on: List[str]  # Patterns to split on
    
    def __post_init__(self):
        """Validate configuration."""
        if self.overlap >= self.size:
            self.overlap = min(self.overlap, self.size // 4)
        if self.min_size > self.size:
            self.min_size = self.size // 2
        if self.max_size < self.size:
            self.max_size = self.size * 2


class DynamicChunker:
    """Adaptive chunking based on FM Global content characteristics."""
    
    def __init__(self):
        # Content type detection patterns
        self.content_patterns = {
            ContentType.TABLE: [
                r'table\s+[\d\-\.]+',
                r'\|.*\|.*\|',  # Markdown tables
                r'┌─.*─┐',  # ASCII tables
                r'protection\s+scheme.*commodity'
            ],
            ContentType.FIGURE_CAPTION: [
                r'figure\s+[\d\-\.]+',
                r'fig\.\s*[\d\-\.]+',
                r'diagram\s+showing',
                r'illustration\s+of'
            ],
            ContentType.EQUATION: [
                r'=\s*[\d\.\s\+\-\*\/\(\)]+',
                r'calculated\s+as:',
                r'formula:',
                r'where:.*=',
                r'Σ',  # Mathematical symbols
                r'√',
                r'∫'
            ],
            ContentType.REQUIREMENT: [
                r'\bshall\b',
                r'\bmust\b',
                r'\brequired\b',
                r'\bminimum\b.*\bmaximum\b',
                r'not\s+less\s+than',
                r'not\s+exceed'
            ],
            ContentType.PROCEDURE: [
                r'step\s+\d+',
                r'^\d+\.\s+',  # Numbered steps
                r'first.*then.*finally',
                r'procedure:',
                r'follow\s+these\s+steps'
            ],
            ContentType.LIST: [
                r'^\s*[-*+]\s+',  # Bullet points
                r'^\s*\d+\)\s+',  # Numbered with parenthesis
                r'^\s*[a-z]\)\s+',  # Lettered lists
            ],
            ContentType.TECHNICAL_SPEC: [
                r'\d+\s*(ft|feet|m|meters)',
                r'\d+\s*(psi|bar|kpa)',
                r'\d+\s*(gpm|lpm)',
                r'k-factor',
                r'spacing.*\d+',
                r'pressure.*\d+'
            ]
        }
        
        # Chunking configurations by content type
        self.chunk_configs = {
            ContentType.TABLE: ChunkConfig(
                size=2000,      # Keep tables whole if possible
                overlap=100,
                min_size=500,
                max_size=3000,
                preserve_structure=True,
                split_on=[r'\n\n', r'---', r'═══']
            ),
            ContentType.FIGURE_CAPTION: ChunkConfig(
                size=500,       # Captions are typically short
                overlap=50,
                min_size=100,
                max_size=800,
                preserve_structure=True,
                split_on=[r'\n\n', r'\.\s+']
            ),
            ContentType.EQUATION: ChunkConfig(
                size=1500,      # Keep equations with context
                overlap=300,
                min_size=400,
                max_size=2000,
                preserve_structure=True,
                split_on=[r'\n\n', r'Where:', r'Given:']
            ),
            ContentType.REQUIREMENT: ChunkConfig(
                size=1200,      # Requirements need full context
                overlap=200,
                min_size=300,
                max_size=1800,
                preserve_structure=True,
                split_on=[r'\n\n', r'\.\s+(?=[A-Z])', r';\s+']
            ),
            ContentType.PROCEDURE: ChunkConfig(
                size=1500,      # Keep procedure steps together
                overlap=150,
                min_size=400,
                max_size=2500,
                preserve_structure=True,
                split_on=[r'\nStep\s+\d+', r'\n\d+\.', r'\n\n']
            ),
            ContentType.LIST: ChunkConfig(
                size=1000,      # Lists should stay together
                overlap=100,
                min_size=200,
                max_size=1500,
                preserve_structure=True,
                split_on=[r'\n\n', r'\n(?=[-*+]\s+)', r'\n(?=\d+\))']
            ),
            ContentType.TECHNICAL_SPEC: ChunkConfig(
                size=1300,      # Technical specs need precision
                overlap=250,
                min_size=400,
                max_size=1800,
                preserve_structure=True,
                split_on=[r'\n\n', r'\.\s+', r';\s+']
            ),
            ContentType.GENERAL_TEXT: ChunkConfig(
                size=1000,      # Default for general content
                overlap=200,
                min_size=300,
                max_size=1500,
                preserve_structure=False,
                split_on=[r'\n\n', r'\.\s+(?=[A-Z])', r'\n']
            )
        }
    
    def detect_content_type(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ContentType:
        """
        Detect the type of content for optimal chunking strategy.
        
        Args:
            content: Text content to analyze
            metadata: Optional metadata hints
            
        Returns:
            Detected content type
        """
        # Check metadata hints first
        if metadata:
            if metadata.get('content_type'):
                try:
                    return ContentType(metadata['content_type'])
                except ValueError:
                    pass
            
            if metadata.get('is_table') or metadata.get('table_number'):
                return ContentType.TABLE
            
            if metadata.get('is_figure') or metadata.get('figure_number'):
                return ContentType.FIGURE_CAPTION
        
        # Analyze content patterns
        content_lower = content.lower()
        pattern_scores = {}
        
        for content_type, patterns in self.content_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    score += 1
            if score > 0:
                pattern_scores[content_type] = score
        
        # Return highest scoring type
        if pattern_scores:
            return max(pattern_scores.items(), key=lambda x: x[1])[0]
        
        # Default to general text
        return ContentType.GENERAL_TEXT
    
    def chunk_content(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        force_type: Optional[ContentType] = None
    ) -> List[Dict[str, Any]]:
        """
        Dynamically chunk content based on its type and structure.
        
        Args:
            content: Content to chunk
            metadata: Optional metadata
            force_type: Force a specific content type
            
        Returns:
            List of chunks with metadata
        """
        if not content.strip():
            return []
        
        # Determine content type
        content_type = force_type or self.detect_content_type(content, metadata)
        config = self.chunk_configs[content_type]
        
        logger.info(f"Using {content_type.value} chunking strategy - "
                   f"size: {config.size}, overlap: {config.overlap}")
        
        # Apply appropriate chunking strategy
        if content_type == ContentType.TABLE:
            chunks = self._chunk_table(content, config, metadata)
        elif content_type == ContentType.FIGURE_CAPTION:
            chunks = self._chunk_figure(content, config, metadata)
        elif content_type == ContentType.EQUATION:
            chunks = self._chunk_equation(content, config, metadata)
        elif content_type == ContentType.PROCEDURE:
            chunks = self._chunk_procedure(content, config, metadata)
        elif content_type == ContentType.LIST:
            chunks = self._chunk_list(content, config, metadata)
        elif content_type == ContentType.REQUIREMENT:
            chunks = self._chunk_requirement(content, config, metadata)
        elif content_type == ContentType.TECHNICAL_SPEC:
            chunks = self._chunk_technical(content, config, metadata)
        else:
            chunks = self._chunk_general(content, config, metadata)
        
        # Add chunk metadata
        for i, chunk in enumerate(chunks):
            chunk['chunk_index'] = i
            chunk['total_chunks'] = len(chunks)
            chunk['content_type'] = content_type.value
            chunk['chunk_config'] = {
                'size': config.size,
                'overlap': config.overlap
            }
        
        return chunks
    
    def _chunk_table(self, content: str, config: ChunkConfig, metadata: Optional[Dict]) -> List[Dict]:
        """Special chunking for tables - try to keep whole."""
        chunks = []
        
        # Try to keep the entire table as one chunk if possible
        if len(content) <= config.max_size:
            chunks.append({
                'content': content,
                'metadata': {
                    **(metadata or {}),
                    'preserved_whole': True,
                    'chunk_type': 'table'
                }
            })
        else:
            # Split on row boundaries if table is too large
            rows = content.split('\n')
            current_chunk = []
            current_size = 0
            
            # Keep header rows
            header_lines = []
            for i, row in enumerate(rows[:5]):  # Check first 5 lines for header
                if '|' in row or '─' in row or '═' in row:
                    header_lines.append(row)
                else:
                    break
            
            for row in rows[len(header_lines):]:
                row_size = len(row)
                
                if current_size + row_size > config.size and current_chunk:
                    # Create chunk with header
                    chunk_content = '\n'.join(header_lines + current_chunk)
                    chunks.append({
                        'content': chunk_content,
                        'metadata': {
                            **(metadata or {}),
                            'has_header': True,
                            'chunk_type': 'table_segment'
                        }
                    })
                    current_chunk = []
                    current_size = 0
                
                current_chunk.append(row)
                current_size += row_size
            
            # Add final chunk
            if current_chunk:
                chunk_content = '\n'.join(header_lines + current_chunk)
                chunks.append({
                    'content': chunk_content,
                    'metadata': {
                        **(metadata or {}),
                        'has_header': True,
                        'chunk_type': 'table_segment'
                    }
                })
        
        return chunks
    
    def _chunk_figure(self, content: str, config: ChunkConfig, metadata: Optional[Dict]) -> List[Dict]:
        """Special chunking for figure captions - keep concise."""
        # Figures are usually short, try to keep whole
        if len(content) <= config.max_size:
            return [{
                'content': content,
                'metadata': {
                    **(metadata or {}),
                    'preserved_whole': True,
                    'chunk_type': 'figure_caption'
                }
            }]
        
        # If too long, split on sentences
        return self._split_on_sentences(content, config, metadata, 'figure_caption')
    
    def _chunk_equation(self, content: str, config: ChunkConfig, metadata: Optional[Dict]) -> List[Dict]:
        """Special chunking for equations - preserve mathematical context."""
        chunks = []
        
        # Find equation blocks
        equation_pattern = r'(?:^|\n)([^=\n]*=.*?)(?=\n\n|\n[A-Z]|\Z)'
        equations = re.findall(equation_pattern, content, re.MULTILINE | re.DOTALL)
        
        if equations:
            for eq in equations:
                # Include surrounding context
                start = max(0, content.find(eq) - 200)
                end = min(len(content), content.find(eq) + len(eq) + 200)
                chunk_content = content[start:end].strip()
                
                chunks.append({
                    'content': chunk_content,
                    'metadata': {
                        **(metadata or {}),
                        'has_equation': True,
                        'chunk_type': 'equation'
                    }
                })
        else:
            # No clear equations, use general chunking
            chunks = self._chunk_general(content, config, metadata)
        
        return chunks
    
    def _chunk_procedure(self, content: str, config: ChunkConfig, metadata: Optional[Dict]) -> List[Dict]:
        """Special chunking for procedures - keep steps together."""
        chunks = []
        
        # Split on step boundaries
        step_pattern = r'(?:Step\s+\d+|^\d+\.|\n\d+\.)'
        steps = re.split(step_pattern, content)
        
        current_chunk = []
        current_size = 0
        
        for step in steps:
            step = step.strip()
            if not step:
                continue
            
            step_size = len(step)
            
            if current_size + step_size > config.size and current_chunk:
                chunks.append({
                    'content': '\n\n'.join(current_chunk),
                    'metadata': {
                        **(metadata or {}),
                        'chunk_type': 'procedure_steps'
                    }
                })
                current_chunk = []
                current_size = 0
            
            current_chunk.append(step)
            current_size += step_size
        
        if current_chunk:
            chunks.append({
                'content': '\n\n'.join(current_chunk),
                'metadata': {
                    **(metadata or {}),
                    'chunk_type': 'procedure_steps'
                }
            })
        
        return chunks if chunks else self._chunk_general(content, config, metadata)
    
    def _chunk_list(self, content: str, config: ChunkConfig, metadata: Optional[Dict]) -> List[Dict]:
        """Special chunking for lists - keep related items together."""
        chunks = []
        
        # Identify list items
        list_pattern = r'^[\s]*[-*+•]\s+|^\s*\d+[.)]\s+|^\s*[a-z][.)]\s+'
        lines = content.split('\n')
        
        current_chunk = []
        current_size = 0
        in_list = False
        
        for line in lines:
            is_list_item = bool(re.match(list_pattern, line))
            
            if is_list_item:
                in_list = True
            elif in_list and line.strip() == '':
                in_list = False
            
            line_size = len(line)
            
            # Check if we need to start a new chunk
            if current_size + line_size > config.size and current_chunk:
                # Try to break at list boundaries
                if not in_list or is_list_item:
                    chunks.append({
                        'content': '\n'.join(current_chunk),
                        'metadata': {
                            **(metadata or {}),
                            'chunk_type': 'list'
                        }
                    })
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(line)
            current_size += line_size
        
        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'metadata': {
                    **(metadata or {}),
                    'chunk_type': 'list'
                }
            })
        
        return chunks
    
    def _chunk_requirement(self, content: str, config: ChunkConfig, metadata: Optional[Dict]) -> List[Dict]:
        """Special chunking for requirements - preserve complete requirements."""
        chunks = []
        
        # Split on requirement keywords but keep them
        req_pattern = r'(?=\b(?:shall|must|required|minimum|maximum)\b)'
        requirements = re.split(req_pattern, content)
        
        current_chunk = []
        current_size = 0
        
        for req in requirements:
            req = req.strip()
            if not req:
                continue
            
            req_size = len(req)
            
            if current_size + req_size > config.size and current_chunk:
                chunks.append({
                    'content': ' '.join(current_chunk),
                    'metadata': {
                        **(metadata or {}),
                        'is_requirement': True,
                        'chunk_type': 'requirement'
                    }
                })
                current_chunk = []
                current_size = 0
            
            current_chunk.append(req)
            current_size += req_size
        
        if current_chunk:
            chunks.append({
                'content': ' '.join(current_chunk),
                'metadata': {
                    **(metadata or {}),
                    'is_requirement': True,
                    'chunk_type': 'requirement'
                }
            })
        
        return chunks if chunks else self._chunk_general(content, config, metadata)
    
    def _chunk_technical(self, content: str, config: ChunkConfig, metadata: Optional[Dict]) -> List[Dict]:
        """Special chunking for technical specifications."""
        # Keep technical specs with their context
        chunks = self._split_on_sentences(content, config, metadata, 'technical_spec')
        
        # Ensure measurements stay with their context
        for chunk in chunks:
            chunk['metadata']['has_measurements'] = bool(
                re.search(r'\d+\s*(?:ft|m|psi|gpm)', chunk['content'])
            )
        
        return chunks
    
    def _chunk_general(self, content: str, config: ChunkConfig, metadata: Optional[Dict]) -> List[Dict]:
        """General chunking strategy for unstructured text."""
        return self._split_on_sentences(content, config, metadata, 'general')
    
    def _split_on_sentences(
        self,
        content: str,
        config: ChunkConfig,
        metadata: Optional[Dict],
        chunk_type: str
    ) -> List[Dict]:
        """Split content on sentence boundaries."""
        chunks = []
        
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
        
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > config.size and current_chunk:
                chunks.append({
                    'content': ' '.join(current_chunk),
                    'metadata': {
                        **(metadata or {}),
                        'chunk_type': chunk_type
                    }
                })
                
                # Add overlap from end of current chunk
                if config.overlap > 0:
                    overlap_sentences = current_chunk[-2:] if len(current_chunk) > 1 else current_chunk
                    current_chunk = overlap_sentences
                    current_size = sum(len(s) for s in overlap_sentences)
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        if current_chunk:
            chunks.append({
                'content': ' '.join(current_chunk),
                'metadata': {
                    **(metadata or {}),
                    'chunk_type': chunk_type
                }
            })
        
        return chunks


# Singleton instance
dynamic_chunker = DynamicChunker()


# Convenience function
def chunk_dynamically(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    force_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Dynamically chunk content based on its type.
    
    Args:
        content: Content to chunk
        metadata: Optional metadata
        force_type: Force a specific content type
        
    Returns:
        List of chunks with metadata
    """
    content_type = ContentType(force_type) if force_type else None
    return dynamic_chunker.chunk_content(content, metadata, content_type)