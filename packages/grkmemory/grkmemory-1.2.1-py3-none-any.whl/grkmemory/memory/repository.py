"""
Memory Repository for GRKMemory.

This module provides persistent storage and retrieval of conversation memories.
Supports multiple storage formats: JSON (fast parsing) and TOON (token-efficient).
"""

import json
import uuid
import datetime
from typing import Dict, List, Optional, Literal
from collections import defaultdict

from ..graph.semantic_graph import SemanticGraph
from ..utils.text import normalize_term, extract_concepts
from ..utils.embeddings import EmbeddingGenerator, cosine_similarity

# Try to import TOON format
try:
    from toon_format import encode as toon_encode, decode as toon_decode
    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False
    toon_encode = None
    toon_decode = None

# Type aliases
StorageFormat = Literal["json", "toon"]
OutputFormat = Literal["json", "toon", "text"]


class MemoryRepository:
    """
    Repository for storing and retrieving conversation memories.
    
    Supports multiple storage formats:
    - JSON: Fast parsing (27x faster), universal compatibility
    - TOON: Token-efficient (25% smaller), optimized for LLM context
    
    Supports multiple search methods:
    - Graph-based semantic search (recommended)
    - Embedding similarity search
    - Tag-based search
    - Entity-based search
    
    Example:
        # Traditional JSON storage
        repo = MemoryRepository(
            memory_file="memories.json",
            storage_format="json",
            output_format="json"
        )
        
        # TOON storage (token-efficient)
        repo = MemoryRepository(
            memory_file="memories.toon",
            storage_format="toon",
            output_format="toon"
        )
        
        # Hybrid: JSON storage, TOON output (recommended for LLM apps)
        repo = MemoryRepository(
            memory_file="memories.json",
            storage_format="json",      # Fast parsing
            output_format="toon"        # 25% fewer tokens for LLM
        )
        
        # Save a conversation
        repo.save({
            "summary": "Discussion about AI",
            "tags": ["ai", "technology"],
            "entities": ["GPT-4", "OpenAI"],
            "key_points": ["AI is transforming industries"]
        })
        
        # Search memories (returns in configured output_format)
        results = repo.search("Tell me about AI", method="graph")
        
        # Get formatted context for LLM
        context = repo.format_for_llm(results)
    """
    
    def __init__(
        self,
        memory_file: str = "graph_retrieve_knowledge_memory.json",
        embedding_model: str = "text-embedding-3-small",
        enable_embeddings: bool = True,
        debug: bool = False,
        memory_limit: int = 5,
        threshold: float = 0.3,
        storage_format: StorageFormat = "json",
        output_format: OutputFormat = "json"
    ):
        """
        Initialize the memory repository.
        
        Args:
            memory_file: Path to file for persistent storage.
            embedding_model: Model for generating embeddings.
            enable_embeddings: Whether to generate embeddings.
            debug: Enable debug logging.
            memory_limit: Maximum memories to return from search.
            threshold: Minimum similarity threshold.
            storage_format: Format for storage ('json' or 'toon').
            output_format: Format for retrieve output ('json', 'toon', or 'text').
        """
        self.memory_file = memory_file
        self.enable_embeddings = enable_embeddings
        self.debug = debug
        self.memory_limit = memory_limit
        self.threshold = threshold
        self.storage_format = storage_format
        self.output_format = output_format
        
        # Validate TOON availability
        if storage_format == "toon" and not TOON_AVAILABLE:
            raise ImportError(
                "TOON format requested but toon_format is not installed. "
                "Install with: pip install toon_format"
            )
        if output_format == "toon" and not TOON_AVAILABLE:
            raise ImportError(
                "TOON output format requested but toon_format is not installed. "
                "Install with: pip install toon_format"
            )
        
        # Auto-detect format from file extension
        if memory_file.endswith(".toon"):
            self.storage_format = "toon"
        elif memory_file.endswith(".json"):
            self.storage_format = "json"
        
        self.memories: List[Dict] = []
        self.semantic_graph = SemanticGraph()
        
        if enable_embeddings:
            self.embedding_generator = EmbeddingGenerator(model=embedding_model)
        else:
            self.embedding_generator = None
        
        self._load_memories()
        self._rebuild_graph()
    
    def _load_memories(self):
        """Load existing memories from file (supports JSON and TOON formats)."""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                self.memories = []
                return
            
            if self.storage_format == "toon":
                if not TOON_AVAILABLE:
                    raise ImportError("TOON format requires toon_format package")
                self.memories = toon_decode(content)
                if not isinstance(self.memories, list):
                    self.memories = [self.memories]
            else:  # json
                self.memories = json.loads(content)
            
            if self.debug:
                print(f"📚 Loaded {len(self.memories)} memories ({self.storage_format.upper()})")
                
        except FileNotFoundError:
            self.memories = []
            if self.debug:
                print(f"📁 File {self.memory_file} not found. Starting fresh.")
        except (json.JSONDecodeError, Exception) as e:
            self.memories = []
            if self.debug:
                print(f"⚠️ Error loading file: {e}. Starting fresh.")
    
    def _rebuild_graph(self):
        """Rebuild the semantic graph from memories."""
        if self.debug:
            print("🧬 Rebuilding semantic graph...")
        
        self.semantic_graph.clear()
        
        for memoria in self.memories:
            self.semantic_graph.add_conversation(memoria)
        
        self.semantic_graph.calculate_densities()
        self.semantic_graph.calculate_centralities()
        
        if self.debug:
            stats = self.semantic_graph.get_stats()
            print(f"📊 Semantic graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
    
    def save(self, data: Dict) -> bool:
        """
        Save a conversation memory.
        
        Args:
            data: Dictionary with conversation data. Should include:
                - summary: Text summary
                - tags: List of tags
                - entities: List of entities
                - key_points: List of key points
                - Optional: sentiment, confidence, notes
        
        Returns:
            True if saved successfully.
        """
        try:
            # Add metadata if not present
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            if "created_at" not in data:
                data["created_at"] = datetime.datetime.now().isoformat()
            
            # Generate embedding if enabled
            if self.enable_embeddings and self.embedding_generator:
                if "embedding" not in data or not data["embedding"]:
                    summary = data.get("summary", "")
                    if summary:
                        if self.debug:
                            print("🧠 Generating summary embedding...")
                        data["embedding"] = self.embedding_generator.generate(summary)
                    else:
                        data["embedding"] = []
            
            # Add to memories
            self.memories.append(data)
            
            # Save to file in configured format
            self._save_to_file()
            
            # Rebuild graph
            self._rebuild_graph()
            
            if self.debug:
                print(f"✅ Saved: {data.get('summary', 'No summary')}")
                print(f"📁 File: {self.memory_file} ({self.storage_format.upper()}, {len(self.memories)} sessions)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving memory: {e}")
            return False
    
    def _save_to_file(self):
        """Save memories to file in configured format."""
        with open(self.memory_file, "w", encoding="utf-8") as f:
            if self.storage_format == "toon":
                if not TOON_AVAILABLE:
                    raise ImportError("TOON format requires toon_format package")
                f.write(toon_encode(self.memories))
            else:  # json
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
    
    def search(
        self,
        query: str,
        method: str = "graph",
        limit: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for relevant memories.
        
        Args:
            query: Search query string.
            method: Search method ('graph', 'embedding', 'tags', 'entities').
            limit: Maximum results to return.
            threshold: Minimum similarity threshold.
        
        Returns:
            List of dictionaries with 'memoria' and 'similaridade' keys.
        """
        if not self.memories:
            return []
        
        limit = limit or self.memory_limit
        threshold = threshold or self.threshold
        
        if method == "graph":
            return self._graph_search(query, threshold, limit)
        elif method == "embedding":
            return self._embedding_search(query, threshold, limit)
        elif method == "tags":
            return self._tag_search(query, threshold, limit)
        elif method == "entities":
            return self._entity_search(query, threshold, limit)
        else:
            return self._graph_search(query, threshold, limit)
    
    def _generate_query_profile(self, query: str) -> Dict:
        """Generate a profile for the query for graph-based search."""
        concepts = set(extract_concepts(query))
        embedding = []
        
        if self.enable_embeddings and self.embedding_generator:
            embedding = self.embedding_generator.generate(query)
        
        return {
            "tags": concepts,
            "entities": concepts,
            "key_points": concepts,
            "concepts": concepts,
            "terms": concepts,
            "embedding": embedding or [],
        }
    
    def _graph_search(self, query: str, threshold: float, limit: int) -> List[Dict]:
        """Graph-based semantic search."""
        query_profile = self._generate_query_profile(query)
        query_embedding = query_profile.get("embedding", [])
        query_terms = query_profile.get("terms", set())
        
        nodes = self.semantic_graph.nodes
        concept_match_map = {}
        
        for session_id, node in nodes.items():
            all_terms = node.tags | node.entities | node.key_points
            matches = len(all_terms & query_terms)
            
            if query_embedding:
                sim = cosine_similarity(query_embedding, node.embedding)
                if sim >= 0.5:
                    matches += 1
            
            if matches > 0:
                concept_match_map[session_id] = matches
        
        # Fallback to embedding search if no matches
        if not concept_match_map and query_terms:
            # Try neighbor propagation
            neighbor_scores = defaultdict(float)
            for session_id, node in nodes.items():
                all_terms = node.tags | node.entities | node.key_points
                direct_matches = len(all_terms & query_terms)
                if direct_matches > 0:
                    for neighbor_id, edge in node.neighbors.items():
                        neighbor_scores[neighbor_id] += edge["weight"] * direct_matches
            
            for session_id, score in sorted(
                neighbor_scores.items(), key=lambda x: x[1], reverse=True
            )[:limit]:
                if score > 0:
                    concept_match_map[session_id] = concept_match_map.get(session_id, 0) + 1
        
        # Still no matches? Fall back to embedding
        if not concept_match_map:
            return self._embedding_search(query, threshold, limit)
        
        # Build results
        relevant_memories = []
        for session_id, matches in concept_match_map.items():
            node = nodes[session_id]
            memoria = node.memoria
            
            concept_similarity = matches / max(len(query_terms), 1)
            graph_density = min(node.density, 1.0)
            
            # Temporal decay
            temporal_decay = 1.0
            created_at = memoria.get("created_at", "")
            if created_at:
                try:
                    created_date = datetime.datetime.fromisoformat(
                        created_at.replace('Z', '+00:00')
                    )
                    days_old = (datetime.datetime.now(created_date.tzinfo) - created_date).days
                    temporal_decay = max(0.1, 1.0 - (days_old / 365.0))
                except:
                    pass
            
            # Composite score
            alpha, beta, gamma = 0.5, 0.35, 0.15
            composite_similarity = (
                alpha * concept_similarity +
                beta * graph_density +
                gamma * temporal_decay
            )
            
            if composite_similarity >= threshold:
                relevant_memories.append({
                    "memoria": memoria,
                    "similaridade": composite_similarity,
                    "concept_matches": matches,
                    "graph_density": graph_density,
                    "temporal_decay": temporal_decay,
                    "method": "graph"
                })
        
        # Sort and limit
        relevant_memories.sort(key=lambda x: x["similaridade"], reverse=True)
        return relevant_memories[:limit]
    
    def _embedding_search(self, query: str, threshold: float, limit: int) -> List[Dict]:
        """Embedding similarity search."""
        if not self.enable_embeddings or not self.embedding_generator:
            return []
        
        query_embedding = self.embedding_generator.generate(query)
        if not query_embedding:
            return []
        
        results = []
        for memoria in self.memories:
            if memoria.get("embedding"):
                similarity = cosine_similarity(query_embedding, memoria["embedding"])
                if similarity >= threshold:
                    results.append({
                        "memoria": memoria,
                        "similaridade": similarity,
                        "method": "embedding"
                    })
        
        results.sort(key=lambda x: x["similaridade"], reverse=True)
        return results[:limit]
    
    def _tag_search(self, query: str, threshold: float, limit: int) -> List[Dict]:
        """Tag-based search."""
        query_words = [normalize_term(w) for w in query.lower().split()]
        
        results = []
        for memoria in self.memories:
            tags = [normalize_term(t) for t in memoria.get("tags", [])]
            matches = sum(1 for word in query_words if any(word in tag for tag in tags))
            
            if matches > 0:
                score = matches / len(query_words)
                if score >= threshold:
                    results.append({
                        "memoria": memoria,
                        "similaridade": score,
                        "method": "tags"
                    })
        
        results.sort(key=lambda x: x["similaridade"], reverse=True)
        return results[:limit]
    
    def _entity_search(self, query: str, threshold: float, limit: int) -> List[Dict]:
        """Entity-based search."""
        query_words = [normalize_term(w) for w in query.lower().split()]
        
        results = []
        for memoria in self.memories:
            entities = [normalize_term(e) for e in memoria.get("entities", [])]
            matches = sum(1 for word in query_words if any(word in entity for entity in entities))
            
            if matches > 0:
                score = matches / len(query_words)
                if score >= threshold:
                    results.append({
                        "memoria": memoria,
                        "similaridade": score,
                        "method": "entities"
                    })
        
        results.sort(key=lambda x: x["similaridade"], reverse=True)
        return results[:limit]
    
    def format_background(self, results: List[Dict], format: Optional[OutputFormat] = None) -> str:
        """
        Format search results as background context for prompts.
        
        Args:
            results: Search results from search() method.
            format: Output format ('json', 'toon', or 'text'). Uses configured output_format if None.
        
        Returns:
            Formatted string with memory context.
        """
        if not results:
            return ""
        
        output_fmt = format or self.output_format
        
        if output_fmt == "text":
            return self._format_as_text(results)
        elif output_fmt == "toon":
            return self._format_as_toon(results)
        else:  # json
            return self._format_as_json(results)
    
    def _format_as_text(self, results: List[Dict]) -> str:
        """Format results as human-readable text."""
        text = "\n\n🧠 BACKGROUND MEMORY (relevant conversations from previous sessions):\n"
        
        for i, item in enumerate(results, 1):
            memoria = item["memoria"]
            similarity = item["similaridade"]
            
            text += f"\n{i}. {memoria.get('summary', 'No summary')}\n"
            text += f"   Tags: {', '.join(memoria.get('tags', []))}\n"
            text += f"   Entities: {', '.join(memoria.get('entities', []))}\n"
            text += f"   Sentiment: {memoria.get('sentiment', 'N/A')}\n"
            text += f"   Relevance: {similarity:.3f}\n"
        
        text += "\nUse this information as additional context for more personalized responses.\n"
        return text
    
    def _format_as_json(self, results: List[Dict]) -> str:
        """Format results as JSON string."""
        # Extract memories without embeddings for context
        memories = []
        for item in results:
            mem = {k: v for k, v in item["memoria"].items() if k != "embedding"}
            mem["relevance"] = item["similaridade"]
            memories.append(mem)
        
        return json.dumps(memories, indent=2, ensure_ascii=False)
    
    def _format_as_toon(self, results: List[Dict]) -> str:
        """Format results as TOON string (25% fewer tokens)."""
        if not TOON_AVAILABLE:
            if self.debug:
                print("⚠️ TOON not available, falling back to JSON")
            return self._format_as_json(results)
        
        # Extract memories without embeddings for context
        memories = []
        for item in results:
            mem = {k: v for k, v in item["memoria"].items() if k != "embedding"}
            mem["relevance"] = round(item["similaridade"], 3)
            memories.append(mem)
        
        return toon_encode(memories)
    
    def format_for_llm(self, results: List[Dict], format: Optional[OutputFormat] = None) -> str:
        """
        Format search results optimized for LLM context.
        
        This is the recommended method for preparing memory context to send to an LLM.
        Use format='toon' for ~25% token savings.
        
        Args:
            results: Search results from search() method.
            format: Output format ('json', 'toon', or 'text'). Uses configured output_format if None.
        
        Returns:
            Formatted string optimized for LLM consumption.
        
        Example:
            results = repo.search("What about AI?")
            context = repo.format_for_llm(results, format="toon")  # 25% fewer tokens
            prompt = f"Context: {context}\\n\\nUser: {user_message}"
        """
        return self.format_background(results, format)
    
    def get_token_estimate(self, results: List[Dict]) -> Dict:
        """
        Estimate token counts for different output formats.
        
        Args:
            results: Search results from search() method.
        
        Returns:
            Dictionary with token estimates for each format.
        
        Example:
            estimates = repo.get_token_estimate(results)
            # {'json': 689, 'toon': 512, 'text': 580, 'savings_toon_vs_json': '25.7%'}
        """
        json_output = self._format_as_json(results)
        text_output = self._format_as_text(results)
        
        json_tokens = len(json_output) // 4
        text_tokens = len(text_output) // 4
        
        result = {
            "json": json_tokens,
            "text": text_tokens,
            "json_chars": len(json_output),
            "text_chars": len(text_output),
        }
        
        if TOON_AVAILABLE:
            toon_output = self._format_as_toon(results)
            toon_tokens = len(toon_output) // 4
            savings = ((json_tokens - toon_tokens) / json_tokens) * 100 if json_tokens > 0 else 0
            
            result["toon"] = toon_tokens
            result["toon_chars"] = len(toon_output)
            result["savings_toon_vs_json"] = f"{savings:.1f}%"
        
        return result
    
    def get_stats(self) -> Dict:
        """Get repository statistics."""
        return {
            "total_memories": len(self.memories),
            "graph_stats": self.semantic_graph.get_stats(),
            "memory_file": self.memory_file,
            "storage_format": self.storage_format,
            "output_format": self.output_format,
            "toon_available": TOON_AVAILABLE,
        }
    
    def clear(self):
        """Clear all memories (in memory only, does not delete file)."""
        self.memories.clear()
        self.semantic_graph.clear()
    
    def convert_storage_format(self, new_format: StorageFormat, new_file: Optional[str] = None) -> bool:
        """
        Convert storage to a different format.
        
        Args:
            new_format: Target format ('json' or 'toon').
            new_file: Optional new file path. If None, changes extension of current file.
        
        Returns:
            True if conversion successful.
        
        Example:
            # Convert from JSON to TOON
            repo.convert_storage_format("toon")
            
            # Convert to TOON with new filename
            repo.convert_storage_format("toon", "memories_optimized.toon")
        """
        if new_format == "toon" and not TOON_AVAILABLE:
            raise ImportError("TOON format requires toon_format package. Install: pip install toon_format")
        
        if new_file:
            self.memory_file = new_file
        else:
            # Change extension
            base = self.memory_file.rsplit(".", 1)[0]
            ext = ".toon" if new_format == "toon" else ".json"
            self.memory_file = base + ext
        
        self.storage_format = new_format
        self._save_to_file()
        
        if self.debug:
            print(f"✅ Converted to {new_format.upper()}: {self.memory_file}")
        
        return True
    
    def export(self, filepath: str, format: Optional[StorageFormat] = None) -> bool:
        """
        Export memories to a file in specified format.
        
        Args:
            filepath: Path to export file.
            format: Export format ('json' or 'toon'). Auto-detected from extension if None.
        
        Returns:
            True if export successful.
        
        Example:
            # Export to TOON for sharing
            repo.export("shared_memories.toon", format="toon")
            
            # Export to JSON for compatibility
            repo.export("backup.json")
        """
        if format is None:
            if filepath.endswith(".toon"):
                format = "toon"
            else:
                format = "json"
        
        if format == "toon" and not TOON_AVAILABLE:
            raise ImportError("TOON format requires toon_format package")
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                if format == "toon":
                    f.write(toon_encode(self.memories))
                else:
                    json.dump(self.memories, f, indent=2, ensure_ascii=False)
            
            if self.debug:
                print(f"✅ Exported to {filepath} ({format.upper()})")
            
            return True
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False
    
    @staticmethod
    def is_toon_available() -> bool:
        """Check if TOON format support is available."""
        return TOON_AVAILABLE