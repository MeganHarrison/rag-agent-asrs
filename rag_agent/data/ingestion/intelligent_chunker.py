"""
Intelligent Document Chunking with Semantic Awareness

This module provides advanced chunking strategies:
- Semantic chunking based on topic boundaries
- Hierarchical chunking with parent-child relationships
- Sentence-window retrieval
- Structure-aware chunking for different document types
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class ChunkType(Enum):
    """Types of chunks for different retrieval strategies."""
    PARAGRAPH = "paragraph"
    SECTION = "section"
    SENTENCE_WINDOW = "sentence_window"
    SEMANTIC = "semantic"
    HIERARCHICAL_PARENT = "hierarchical_parent"
    HIERARCHICAL_CHILD = "hierarchical_child"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    LIST = "list"


@dataclass
class IntelligentChunk:
    """Enhanced chunk with hierarchical and semantic information."""
    id: str
    content: str
    chunk_type: ChunkType
    index: int
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Hierarchical information
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    depth_level: int = 0
    
    # Semantic information
    topic_signature: Optional[str] = None
    key_entities: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    
    # Positional information
    start_char: int = 0
    end_char: int = 0
    start_line: int = 0
    end_line: int = 0
    
    # Contextual information
    preceding_context: Optional[str] = None
    following_context: Optional[str] = None


class IntelligentChunker:
    """Advanced chunking with multiple strategies."""
    
    def __init__(
        self,
        base_chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
        sentence_window_size: int = 3,
        enable_hierarchical: bool = True,
        enable_semantic: bool = True
    ):
        self.base_chunk_size = base_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.sentence_window_size = sentence_window_size
        self.enable_hierarchical = enable_hierarchical
        self.enable_semantic = enable_semantic
    
    async def chunk_document(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[IntelligentChunk], Dict[str, Any]]:
        """
        Chunk document using multiple strategies.
        
        Returns:
            Tuple of (chunks, chunking_metadata)
        """
        
        chunks = []
        chunk_relationships = {}
        
        # Detect document structure
        doc_structure = self._analyze_document_structure(content)
        
        # Strategy 1: Hierarchical chunking (sections -> paragraphs)
        if self.enable_hierarchical:
            hierarchical_chunks = self._create_hierarchical_chunks(
                content, document_id, doc_structure
            )
            chunks.extend(hierarchical_chunks)
            
            # Build parent-child relationships
            for chunk in hierarchical_chunks:
                if chunk.parent_id:
                    if chunk.parent_id not in chunk_relationships:
                        chunk_relationships[chunk.parent_id] = []
                    chunk_relationships[chunk.parent_id].append(chunk.id)
        
        # Strategy 2: Semantic chunking (topic-based boundaries)
        if self.enable_semantic:
            semantic_chunks = await self._create_semantic_chunks(
                content, document_id
            )
            chunks.extend(semantic_chunks)
        
        # Strategy 3: Sentence-window chunks for precise retrieval
        sentence_chunks = self._create_sentence_window_chunks(
            content, document_id
        )
        chunks.extend(sentence_chunks)
        
        # Strategy 4: Structure-aware chunks (tables, code, lists)
        structure_chunks = self._create_structure_chunks(
            content, document_id, doc_structure
        )
        chunks.extend(structure_chunks)
        
        # Add metadata to all chunks
        for i, chunk in enumerate(chunks):
            chunk.metadata.update(metadata or {})
            chunk.metadata['document_id'] = document_id
            chunk.metadata['total_chunks'] = len(chunks)
            chunk.index = i
        
        chunking_metadata = {
            "total_chunks": len(chunks),
            "chunk_types": {
                chunk_type.value: sum(1 for c in chunks if c.chunk_type == chunk_type)
                for chunk_type in ChunkType
            },
            "relationships": chunk_relationships,
            "document_structure": doc_structure
        }
        
        return chunks, chunking_metadata
    
    def _analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analyze document structure for intelligent chunking."""
        
        structure = {
            "has_sections": False,
            "has_code_blocks": False,
            "has_tables": False,
            "has_lists": False,
            "sections": [],
            "code_blocks": [],
            "tables": [],
            "lists": []
        }
        
        lines = content.split('\n')
        
        # Detect sections (markdown headers)
        section_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        for i, line in enumerate(lines):
            match = section_pattern.match(line)
            if match:
                structure["has_sections"] = True
                structure["sections"].append({
                    "level": len(match.group(1)),
                    "title": match.group(2),
                    "line": i
                })
        
        # Detect code blocks
        code_block_pattern = re.compile(r'```[\w]*')
        code_blocks = code_block_pattern.finditer(content)
        for match in code_blocks:
            structure["has_code_blocks"] = True
            structure["code_blocks"].append(match.start())
        
        # Detect tables (simple markdown tables)
        table_pattern = re.compile(r'^\|.*\|$')
        for i, line in enumerate(lines):
            if table_pattern.match(line.strip()):
                structure["has_tables"] = True
                if not structure["tables"] or i > structure["tables"][-1]["end"] + 1:
                    structure["tables"].append({"start": i, "end": i})
                else:
                    structure["tables"][-1]["end"] = i
        
        # Detect lists
        list_pattern = re.compile(r'^[\s]*[-*+]\s+.+$|^[\s]*\d+\.\s+.+$')
        for i, line in enumerate(lines):
            if list_pattern.match(line):
                structure["has_lists"] = True
                if not structure["lists"] or i > structure["lists"][-1]["end"] + 1:
                    structure["lists"].append({"start": i, "end": i})
                else:
                    structure["lists"][-1]["end"] = i
        
        return structure
    
    def _create_hierarchical_chunks(
        self,
        content: str,
        document_id: str,
        structure: Dict[str, Any]
    ) -> List[IntelligentChunk]:
        """Create hierarchical chunks with parent-child relationships."""
        
        chunks = []
        lines = content.split('\n')
        
        if not structure["has_sections"]:
            # No clear sections, create basic hierarchical chunks
            return self._create_basic_hierarchical_chunks(content, document_id)
        
        # Create parent chunks for sections
        sections = structure["sections"]
        for i, section in enumerate(sections):
            # Find section content boundaries
            start_line = section["line"]
            end_line = sections[i + 1]["line"] if i < len(sections) - 1 else len(lines)
            
            # Extract section content
            section_lines = lines[start_line:end_line]
            section_content = '\n'.join(section_lines)
            
            # Create parent chunk for section
            parent_id = self._generate_chunk_id(
                document_id, f"section_{i}_{section['title']}"
            )
            
            parent_chunk = IntelligentChunk(
                id=parent_id,
                content=section_content[:self.max_chunk_size],
                chunk_type=ChunkType.HIERARCHICAL_PARENT,
                index=i,
                token_count=self._count_tokens(section_content),
                depth_level=section["level"],
                metadata={
                    "section_title": section["title"],
                    "section_level": section["level"]
                },
                start_line=start_line,
                end_line=end_line
            )
            chunks.append(parent_chunk)
            
            # Create child chunks for section content
            child_chunks = self._chunk_section_content(
                section_content,
                document_id,
                parent_id,
                start_line
            )
            
            parent_chunk.child_ids = [c.id for c in child_chunks]
            chunks.extend(child_chunks)
        
        return chunks
    
    def _create_basic_hierarchical_chunks(
        self,
        content: str,
        document_id: str
    ) -> List[IntelligentChunk]:
        """Create basic hierarchical chunks when no clear structure exists."""
        
        chunks = []
        paragraphs = content.split('\n\n')
        
        # Group paragraphs into parent chunks
        parent_chunks = []
        current_parent = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > self.base_chunk_size and current_parent:
                parent_chunks.append('\n\n'.join(current_parent))
                current_parent = [para]
                current_size = para_size
            else:
                current_parent.append(para)
                current_size += para_size
        
        if current_parent:
            parent_chunks.append('\n\n'.join(current_parent))
        
        # Create hierarchical structure
        for i, parent_content in enumerate(parent_chunks):
            parent_id = self._generate_chunk_id(document_id, f"parent_{i}")
            
            parent_chunk = IntelligentChunk(
                id=parent_id,
                content=parent_content,
                chunk_type=ChunkType.HIERARCHICAL_PARENT,
                index=i,
                token_count=self._count_tokens(parent_content),
                depth_level=0
            )
            chunks.append(parent_chunk)
            
            # Create child chunks
            child_chunks = self._chunk_section_content(
                parent_content,
                document_id,
                parent_id,
                0
            )
            
            parent_chunk.child_ids = [c.id for c in child_chunks]
            chunks.extend(child_chunks)
        
        return chunks
    
    def _chunk_section_content(
        self,
        content: str,
        document_id: str,
        parent_id: str,
        start_line: int
    ) -> List[IntelligentChunk]:
        """Chunk section content into child chunks."""
        
        chunks = []
        paragraphs = content.split('\n\n')
        
        for i, para in enumerate(paragraphs):
            if len(para) < self.min_chunk_size:
                continue
            
            # Split large paragraphs
            if len(para) > self.base_chunk_size:
                sentences = sent_tokenize(para)
                current_chunk = []
                current_size = 0
                
                for sentence in sentences:
                    sentence_size = len(sentence)
                    
                    if current_size + sentence_size > self.base_chunk_size and current_chunk:
                        chunk_content = ' '.join(current_chunk)
                        chunks.append(self._create_child_chunk(
                            chunk_content,
                            document_id,
                            parent_id,
                            len(chunks)
                        ))
                        current_chunk = [sentence]
                        current_size = sentence_size
                    else:
                        current_chunk.append(sentence)
                        current_size += sentence_size
                
                if current_chunk:
                    chunks.append(self._create_child_chunk(
                        ' '.join(current_chunk),
                        document_id,
                        parent_id,
                        len(chunks)
                    ))
            else:
                chunks.append(self._create_child_chunk(
                    para,
                    document_id,
                    parent_id,
                    len(chunks)
                ))
        
        return chunks
    
    def _create_child_chunk(
        self,
        content: str,
        document_id: str,
        parent_id: str,
        index: int
    ) -> IntelligentChunk:
        """Create a child chunk."""
        
        chunk_id = self._generate_chunk_id(
            document_id, f"child_{parent_id}_{index}"
        )
        
        return IntelligentChunk(
            id=chunk_id,
            content=content,
            chunk_type=ChunkType.HIERARCHICAL_CHILD,
            index=index,
            token_count=self._count_tokens(content),
            parent_id=parent_id,
            depth_level=1
        )
    
    async def _create_semantic_chunks(
        self,
        content: str,
        document_id: str
    ) -> List[IntelligentChunk]:
        """Create chunks based on semantic boundaries."""
        
        chunks = []
        sentences = sent_tokenize(content)
        
        if not sentences:
            return chunks
        
        # Group sentences by semantic similarity
        semantic_groups = await self._group_sentences_semantically(sentences)
        
        for i, group in enumerate(semantic_groups):
            group_content = ' '.join(group)
            
            # Skip if too small
            if len(group_content) < self.min_chunk_size:
                continue
            
            # Split if too large
            if len(group_content) > self.max_chunk_size:
                group_content = group_content[:self.max_chunk_size]
            
            chunk_id = self._generate_chunk_id(document_id, f"semantic_{i}")
            
            # Extract key entities (simplified)
            entities = self._extract_entities(group_content)
            
            chunk = IntelligentChunk(
                id=chunk_id,
                content=group_content,
                chunk_type=ChunkType.SEMANTIC,
                index=i,
                token_count=self._count_tokens(group_content),
                key_entities=entities,
                topic_signature=self._generate_topic_signature(group_content)
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _group_sentences_semantically(
        self,
        sentences: List[str]
    ) -> List[List[str]]:
        """Group sentences by semantic similarity."""
        
        # Simplified semantic grouping based on word overlap
        # In production, use embeddings for better semantic similarity
        
        groups = []
        current_group = []
        current_topic_words = set()
        
        for sentence in sentences:
            sentence_words = set(word_tokenize(sentence.lower()))
            
            # Remove stop words (simplified)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
            sentence_words = sentence_words - stop_words
            
            if not current_group:
                current_group = [sentence]
                current_topic_words = sentence_words
            else:
                # Check similarity with current group
                overlap = len(current_topic_words & sentence_words)
                similarity = overlap / max(len(current_topic_words), len(sentence_words), 1)
                
                if similarity > 0.3:  # Threshold for semantic similarity
                    current_group.append(sentence)
                    current_topic_words.update(sentence_words)
                else:
                    # Start new group
                    groups.append(current_group)
                    current_group = [sentence]
                    current_topic_words = sentence_words
            
            # Check size constraint
            group_size = sum(len(s) for s in current_group)
            if group_size >= self.base_chunk_size:
                groups.append(current_group)
                current_group = []
                current_topic_words = set()
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _create_sentence_window_chunks(
        self,
        content: str,
        document_id: str
    ) -> List[IntelligentChunk]:
        """Create sentence-window chunks for precise retrieval."""
        
        chunks = []
        sentences = sent_tokenize(content)
        
        for i in range(len(sentences)):
            # Get window of sentences
            start_idx = max(0, i - self.sentence_window_size)
            end_idx = min(len(sentences), i + self.sentence_window_size + 1)
            
            window_sentences = sentences[start_idx:end_idx]
            target_sentence = sentences[i]
            
            # Create chunk with context
            chunk_content = ' '.join(window_sentences)
            
            chunk_id = self._generate_chunk_id(document_id, f"sentence_window_{i}")
            
            chunk = IntelligentChunk(
                id=chunk_id,
                content=chunk_content,
                chunk_type=ChunkType.SENTENCE_WINDOW,
                index=i,
                token_count=self._count_tokens(chunk_content),
                metadata={
                    "target_sentence": target_sentence,
                    "window_size": self.sentence_window_size,
                    "sentence_index": i
                },
                preceding_context=' '.join(sentences[start_idx:i]) if i > 0 else None,
                following_context=' '.join(sentences[i+1:end_idx]) if i < len(sentences)-1 else None
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_structure_chunks(
        self,
        content: str,
        document_id: str,
        structure: Dict[str, Any]
    ) -> List[IntelligentChunk]:
        """Create chunks for structured content (tables, code, lists)."""
        
        chunks = []
        lines = content.split('\n')
        
        # Process code blocks
        if structure["has_code_blocks"]:
            code_chunks = self._extract_code_blocks(content, document_id)
            chunks.extend(code_chunks)
        
        # Process tables
        if structure["has_tables"]:
            for table_info in structure["tables"]:
                table_lines = lines[table_info["start"]:table_info["end"]+1]
                table_content = '\n'.join(table_lines)
                
                chunk_id = self._generate_chunk_id(
                    document_id, f"table_{table_info['start']}"
                )
                
                chunk = IntelligentChunk(
                    id=chunk_id,
                    content=table_content,
                    chunk_type=ChunkType.TABLE,
                    index=len(chunks),
                    token_count=self._count_tokens(table_content),
                    start_line=table_info["start"],
                    end_line=table_info["end"],
                    metadata={"structure_type": "table"}
                )
                chunks.append(chunk)
        
        # Process lists
        if structure["has_lists"]:
            for list_info in structure["lists"]:
                list_lines = lines[list_info["start"]:list_info["end"]+1]
                list_content = '\n'.join(list_lines)
                
                chunk_id = self._generate_chunk_id(
                    document_id, f"list_{list_info['start']}"
                )
                
                chunk = IntelligentChunk(
                    id=chunk_id,
                    content=list_content,
                    chunk_type=ChunkType.LIST,
                    index=len(chunks),
                    token_count=self._count_tokens(list_content),
                    start_line=list_info["start"],
                    end_line=list_info["end"],
                    metadata={"structure_type": "list"}
                )
                chunks.append(chunk)
        
        return chunks
    
    def _extract_code_blocks(
        self,
        content: str,
        document_id: str
    ) -> List[IntelligentChunk]:
        """Extract code blocks as separate chunks."""
        
        chunks = []
        code_pattern = re.compile(r'```([\w]*)\n(.*?)```', re.DOTALL)
        
        for match in code_pattern.finditer(content):
            language = match.group(1) or 'plaintext'
            code_content = match.group(2)
            
            chunk_id = self._generate_chunk_id(
                document_id, f"code_{match.start()}"
            )
            
            chunk = IntelligentChunk(
                id=chunk_id,
                content=code_content,
                chunk_type=ChunkType.CODE_BLOCK,
                index=len(chunks),
                token_count=self._count_tokens(code_content),
                start_char=match.start(),
                end_char=match.end(),
                metadata={
                    "language": language,
                    "structure_type": "code"
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities from text (simplified)."""
        
        entities = []
        
        # Extract capitalized words (potential entities)
        words = word_tokenize(text)
        for i, word in enumerate(words):
            if word[0].isupper() and i > 0:  # Not start of sentence
                entities.append(word)
        
        # Extract quoted strings
        quoted_pattern = re.compile(r'"([^"]*)"')
        for match in quoted_pattern.finditer(text):
            entities.append(match.group(1))
        
        return list(set(entities))[:10]  # Limit to 10 entities
    
    def _generate_topic_signature(self, text: str) -> str:
        """Generate a topic signature for the text."""
        
        # Extract most frequent meaningful words
        words = word_tokenize(text.lower())
        
        # Remove stop words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'was', 'are', 'were'}
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Get word frequency
        word_freq = {}
        for word in meaningful_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Create signature
        signature = '_'.join([word for word, _ in top_words])
        return signature
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (simple approximation)."""
        return len(text.split())
    
    def _generate_chunk_id(self, document_id: str, suffix: str) -> str:
        """Generate unique chunk ID."""
        
        unique_string = f"{document_id}_{suffix}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]