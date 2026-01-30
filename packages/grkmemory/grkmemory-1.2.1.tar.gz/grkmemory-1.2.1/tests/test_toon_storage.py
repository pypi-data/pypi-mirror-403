"""
Test: TOON vs JSON Storage Comparison
=====================================

This test compares the GRKMemory storage using:
- Traditional JSON format
- TOON (Token-Oriented Object Notation) format

TOON is a compact, human-readable format optimized for LLM prompts.
Reference: https://github.com/toon-format/toon

Expected benefits:
- 30-50% token reduction
- Human-readable format
- Schema-aware structure
"""

import json
import os
import sys
import tempfile
import uuid
import datetime
import time
import statistics
from typing import Dict, List, Optional, Callable

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from toon_format import encode as toon_encode, decode as toon_decode
    TOON_AVAILABLE = True
except ImportError:
    print("⚠️ toon_format not installed. Run: pip install toon_format")
    TOON_AVAILABLE = False


class ToonMemoryRepository:
    """
    Memory Repository using TOON format for storage.
    
    TOON (Token-Oriented Object Notation) provides:
    - Compact storage (30-50% smaller than JSON)
    - Schema-aware format
    - LLM-optimized token usage
    
    Example:
        repo = ToonMemoryRepository("memories.toon")
        repo.save({"summary": "AI discussion", "tags": ["ai", "ml"]})
        memories = repo.load_all()
    """
    
    def __init__(self, memory_file: str = "memories.toon", debug: bool = False):
        self.memory_file = memory_file
        self.debug = debug
        self.memories: List[Dict] = []
        self._load_memories()
    
    def _load_memories(self):
        """Load existing memories from TOON file."""
        if not TOON_AVAILABLE:
            self.memories = []
            return
            
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    self.memories = toon_decode(content)
                    if not isinstance(self.memories, list):
                        self.memories = [self.memories]
            if self.debug:
                print(f"📚 [TOON] Loaded {len(self.memories)} memories")
        except FileNotFoundError:
            self.memories = []
            if self.debug:
                print(f"📁 [TOON] File {self.memory_file} not found. Starting fresh.")
        except Exception as e:
            self.memories = []
            if self.debug:
                print(f"⚠️ [TOON] Error loading: {e}")
    
    def save(self, data: Dict) -> bool:
        """Save a memory in TOON format."""
        if not TOON_AVAILABLE:
            print("❌ toon_format not available")
            return False
            
        try:
            # Add metadata
            if "id" not in data:
                data["id"] = str(uuid.uuid4())[:8]  # Shorter IDs for TOON
            if "created_at" not in data:
                data["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
            
            self.memories.append(data)
            
            # Encode and save as TOON
            toon_content = toon_encode(self.memories)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                f.write(toon_content)
            
            if self.debug:
                print(f"✅ [TOON] Saved: {data.get('summary', 'No summary')}")
            
            return True
        except Exception as e:
            print(f"❌ [TOON] Error saving: {e}")
            return False
    
    def load_all(self) -> List[Dict]:
        """Return all memories."""
        return self.memories
    
    def get_raw_content(self) -> str:
        """Get raw TOON content for comparison."""
        if not TOON_AVAILABLE:
            return ""
        return toon_encode(self.memories)
    
    def clear(self):
        """Clear all memories."""
        self.memories = []
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)


class JsonMemoryRepository:
    """Traditional JSON storage for comparison."""
    
    def __init__(self, memory_file: str = "memories.json", debug: bool = False):
        self.memory_file = memory_file
        self.debug = debug
        self.memories: List[Dict] = []
        self._load_memories()
    
    def _load_memories(self):
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                self.memories = json.load(f)
            if self.debug:
                print(f"📚 [JSON] Loaded {len(self.memories)} memories")
        except FileNotFoundError:
            self.memories = []
        except json.JSONDecodeError:
            self.memories = []
    
    def save(self, data: Dict) -> bool:
        try:
            if "id" not in data:
                data["id"] = str(uuid.uuid4())[:8]
            if "created_at" not in data:
                data["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
            
            self.memories.append(data)
            
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
            
            if self.debug:
                print(f"✅ [JSON] Saved: {data.get('summary', 'No summary')}")
            
            return True
        except Exception as e:
            print(f"❌ [JSON] Error saving: {e}")
            return False
    
    def load_all(self) -> List[Dict]:
        return self.memories
    
    def get_raw_content(self) -> str:
        return json.dumps(self.memories, indent=2, ensure_ascii=False)
    
    def clear(self):
        self.memories = []
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count (approximation: ~4 chars per token for English).
    For more accurate results, use tiktoken.
    """
    return len(text) // 4


def run_comparison_test():
    """
    Run comparison test between JSON and TOON storage.
    """
    print("\n" + "=" * 60)
    print("🧪 TOON vs JSON Storage Comparison Test")
    print("=" * 60)
    
    if not TOON_AVAILABLE:
        print("\n❌ TOON not available. Install with: pip install toon_format")
        return False
    
    # Sample memories to test
    sample_memories = [
        {
            "summary": "Discussed artificial intelligence and machine learning applications in healthcare",
            "tags": ["ai", "ml", "healthcare", "technology"],
            "entities": ["GPT-4", "OpenAI", "TensorFlow", "PyTorch"],
            "key_points": [
                "AI improves diagnostic accuracy",
                "ML models predict patient outcomes",
                "Privacy concerns with medical data"
            ],
            "sentiment": "positive",
            "confidence": 0.92
        },
        {
            "summary": "Conversation about Python web development with FastAPI and async programming",
            "tags": ["python", "fastapi", "async", "web", "api"],
            "entities": ["FastAPI", "Uvicorn", "Pydantic", "SQLAlchemy"],
            "key_points": [
                "FastAPI is faster than Flask",
                "Async improves performance",
                "Type hints improve code quality"
            ],
            "sentiment": "positive",
            "confidence": 0.88
        },
        {
            "summary": "Discussion about graph databases and knowledge management systems",
            "tags": ["graph", "database", "knowledge", "neo4j"],
            "entities": ["Neo4j", "GraphQL", "Knowledge Graph", "RDF"],
            "key_points": [
                "Graph databases excel at relationships",
                "Knowledge graphs enable semantic search",
                "Integration with LLMs is promising"
            ],
            "sentiment": "neutral",
            "confidence": 0.85
        },
        {
            "summary": "Explored memory optimization techniques for AI agents and context management",
            "tags": ["memory", "optimization", "ai-agents", "context"],
            "entities": ["GRKMemory", "LangChain", "Vector DB", "Embeddings"],
            "key_points": [
                "Semantic graphs reduce token usage",
                "Embeddings enable similarity search",
                "Context window management is critical"
            ],
            "sentiment": "positive",
            "confidence": 0.91
        },
        {
            "summary": "Analyzed token efficiency strategies for large language model prompts",
            "tags": ["tokens", "efficiency", "llm", "prompts", "optimization"],
            "entities": ["TOON", "JSON", "YAML", "Tiktoken"],
            "key_points": [
                "TOON reduces tokens by 30-50%",
                "Schema-aware formats are compact",
                "Human readability is preserved"
            ],
            "sentiment": "positive",
            "confidence": 0.95
        }
    ]
    
    # Create temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "test_memories.json")
        toon_file = os.path.join(tmpdir, "test_memories.toon")
        
        # Initialize repositories
        json_repo = JsonMemoryRepository(json_file, debug=False)
        toon_repo = ToonMemoryRepository(toon_file, debug=False)
        
        # Save memories
        print("\n📝 Saving 5 sample memories...")
        for memory in sample_memories:
            json_repo.save(memory.copy())
            toon_repo.save(memory.copy())
        
        # Get raw content
        json_content = json_repo.get_raw_content()
        toon_content = toon_repo.get_raw_content()
        
        # Calculate sizes
        json_size = len(json_content)
        toon_size = len(toon_content)
        
        json_tokens = estimate_tokens(json_content)
        toon_tokens = estimate_tokens(toon_content)
        
        reduction_bytes = ((json_size - toon_size) / json_size) * 100
        reduction_tokens = ((json_tokens - toon_tokens) / json_tokens) * 100
        
        # Print results
        print("\n" + "-" * 60)
        print("📊 RESULTS")
        print("-" * 60)
        
        print(f"\n📁 JSON Format:")
        print(f"   Size: {json_size:,} bytes")
        print(f"   Estimated tokens: ~{json_tokens:,}")
        
        print(f"\n📦 TOON Format:")
        print(f"   Size: {toon_size:,} bytes")
        print(f"   Estimated tokens: ~{toon_tokens:,}")
        
        print(f"\n💰 SAVINGS:")
        print(f"   Bytes reduction: {reduction_bytes:.1f}%")
        print(f"   Token reduction: {reduction_tokens:.1f}%")
        print(f"   Bytes saved: {json_size - toon_size:,} bytes")
        print(f"   Tokens saved: ~{json_tokens - toon_tokens:,}")
        
        # Show sample of both formats
        print("\n" + "-" * 60)
        print("📄 JSON Sample (first 500 chars):")
        print("-" * 60)
        print(json_content[:500] + "...")
        
        print("\n" + "-" * 60)
        print("📦 TOON Sample (first 500 chars):")
        print("-" * 60)
        print(toon_content[:500] + "...")
        
        # Verify data integrity
        print("\n" + "-" * 60)
        print("✅ Data Integrity Check")
        print("-" * 60)
        
        json_memories = json_repo.load_all()
        toon_memories = toon_repo.load_all()
        
        print(f"   JSON memories loaded: {len(json_memories)}")
        print(f"   TOON memories loaded: {len(toon_memories)}")
        
        # Compare first memory
        if json_memories and toon_memories:
            json_first = json_memories[0]
            toon_first = toon_memories[0]
            
            fields_match = all(
                json_first.get(k) == toon_first.get(k) 
                for k in ["summary", "tags", "entities"]
            )
            print(f"   Data matches: {'✅ Yes' if fields_match else '❌ No'}")
        
        print("\n" + "=" * 60)
        print("🎉 Test completed successfully!")
        print("=" * 60)
        
        return True


def test_toon_encode_decode():
    """Test basic TOON encode/decode functionality."""
    print("\n" + "=" * 60)
    print("🧪 TOON Encode/Decode Test")
    print("=" * 60)
    
    if not TOON_AVAILABLE:
        print("❌ TOON not available")
        return False
    
    # Test simple data
    data = {
        "name": "GRKMemory",
        "version": "1.0.0",
        "features": ["graph", "semantic", "memory"]
    }
    
    print(f"\n📥 Input (dict): {data}")
    
    encoded = toon_encode(data)
    print(f"\n📦 TOON Encoded:\n{encoded}")
    
    decoded = toon_decode(encoded)
    print(f"\n📤 Decoded: {decoded}")
    
    # Verify
    assert decoded["name"] == data["name"], "Name mismatch!"
    assert decoded["version"] == data["version"], "Version mismatch!"
    
    print("\n✅ Encode/Decode test passed!")
    return True


def test_toon_with_list():
    """Test TOON with array of objects (common pattern for memories)."""
    print("\n" + "=" * 60)
    print("🧪 TOON Array Test")
    print("=" * 60)
    
    if not TOON_AVAILABLE:
        print("❌ TOON not available")
        return False
    
    # Simulating memory storage
    memories = [
        {"id": 1, "summary": "First conversation", "tags": ["intro", "greeting"]},
        {"id": 2, "summary": "Second conversation", "tags": ["followup", "question"]},
        {"id": 3, "summary": "Third conversation", "tags": ["conclusion", "summary"]},
    ]
    
    print(f"\n📥 Input: {len(memories)} memories")
    
    # JSON comparison
    json_output = json.dumps(memories, indent=2)
    toon_output = toon_encode(memories)
    
    print(f"\n📄 JSON ({len(json_output)} chars):")
    print(json_output)
    
    print(f"\n📦 TOON ({len(toon_output)} chars):")
    print(toon_output)
    
    reduction = ((len(json_output) - len(toon_output)) / len(json_output)) * 100
    print(f"\n💰 Reduction: {reduction:.1f}%")
    
    # Decode and verify
    decoded = toon_decode(toon_output)
    assert len(decoded) == 3, "Wrong number of items!"
    
    print("\n✅ Array test passed!")
    return True


def benchmark_retrieve_efficiency():
    """
    Benchmark retrieve efficiency: JSON vs TOON
    
    Measures:
    - File load time
    - Decode/parse time
    - Search/filter time
    - Memory content size for LLM context
    """
    print("\n" + "=" * 60)
    print("⚡ RETRIEVE EFFICIENCY BENCHMARK")
    print("=" * 60)
    
    if not TOON_AVAILABLE:
        print("❌ TOON not available")
        return False
    
    # Generate larger dataset for meaningful benchmarks
    num_memories = 100
    print(f"\n📊 Generating {num_memories} sample memories...")
    
    sample_memories = []
    topics = ["AI", "Python", "Web", "Database", "Security", "Cloud", "DevOps", "ML"]
    sentiments = ["positive", "neutral", "negative"]
    
    for i in range(num_memories):
        topic = topics[i % len(topics)]
        sample_memories.append({
            "id": f"mem_{i:04d}",
            "summary": f"Discussion about {topic} - conversation {i} covering various aspects of {topic.lower()} development and best practices",
            "tags": [topic.lower(), "development", f"topic_{i % 10}", "conversation"],
            "entities": [f"Entity_{i}", f"Tool_{i % 5}", topic],
            "key_points": [
                f"Key insight {i}.1 about {topic}",
                f"Key insight {i}.2 about implementation",
                f"Key insight {i}.3 about best practices"
            ],
            "sentiment": sentiments[i % 3],
            "confidence": 0.7 + (i % 30) / 100,
            "created_at": f"2026-01-{(i % 28) + 1:02d}"
        })
    
    # Create temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "bench_memories.json")
        toon_file = os.path.join(tmpdir, "bench_memories.toon")
        
        # Save JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(sample_memories, f, indent=2, ensure_ascii=False)
        
        # Save TOON
        toon_content = toon_encode(sample_memories)
        with open(toon_file, "w", encoding="utf-8") as f:
            f.write(toon_content)
        
        # File sizes
        json_size = os.path.getsize(json_file)
        toon_size = os.path.getsize(toon_file)
        
        print(f"\n📁 File Sizes:")
        print(f"   JSON: {json_size:,} bytes")
        print(f"   TOON: {toon_size:,} bytes")
        print(f"   Reduction: {((json_size - toon_size) / json_size) * 100:.1f}%")
        
        # Benchmark parameters
        iterations = 50
        
        # ==========================================
        # BENCHMARK 1: File Load + Parse Time
        # ==========================================
        print(f"\n⏱️  BENCHMARK 1: Load + Parse ({iterations} iterations)")
        print("-" * 40)
        
        # JSON load times
        json_load_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            json_load_times.append((time.perf_counter() - start) * 1000)
        
        # TOON load times
        toon_load_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            with open(toon_file, "r", encoding="utf-8") as f:
                content = f.read()
                data = toon_decode(content)
            toon_load_times.append((time.perf_counter() - start) * 1000)
        
        json_avg = statistics.mean(json_load_times)
        toon_avg = statistics.mean(toon_load_times)
        
        print(f"   JSON: {json_avg:.3f} ms (avg)")
        print(f"   TOON: {toon_avg:.3f} ms (avg)")
        
        if json_avg < toon_avg:
            print(f"   ⚡ JSON is {toon_avg/json_avg:.2f}x faster to parse")
        else:
            print(f"   ⚡ TOON is {json_avg/toon_avg:.2f}x faster to parse")
        
        # ==========================================
        # BENCHMARK 2: Search/Filter Performance
        # ==========================================
        print(f"\n⏱️  BENCHMARK 2: Search/Filter ({iterations} iterations)")
        print("-" * 40)
        
        search_terms = ["AI", "Python", "Database"]
        
        def search_memories(memories: List[Dict], term: str) -> List[Dict]:
            """Simple search by tag or summary."""
            results = []
            term_lower = term.lower()
            for mem in memories:
                if term_lower in mem.get("summary", "").lower():
                    results.append(mem)
                elif any(term_lower in tag.lower() for tag in mem.get("tags", [])):
                    results.append(mem)
            return results
        
        # Load data once
        with open(json_file, "r") as f:
            json_data = json.load(f)
        with open(toon_file, "r") as f:
            toon_data = toon_decode(f.read())
        
        # JSON search times
        json_search_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            for term in search_terms:
                results = search_memories(json_data, term)
            json_search_times.append((time.perf_counter() - start) * 1000)
        
        # TOON search times (after decode, same structure)
        toon_search_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            for term in search_terms:
                results = search_memories(toon_data, term)
            toon_search_times.append((time.perf_counter() - start) * 1000)
        
        json_search_avg = statistics.mean(json_search_times)
        toon_search_avg = statistics.mean(toon_search_times)
        
        print(f"   JSON data search: {json_search_avg:.3f} ms (avg)")
        print(f"   TOON data search: {toon_search_avg:.3f} ms (avg)")
        print(f"   ℹ️  After decode, both have same structure (dict)")
        
        # ==========================================
        # BENCHMARK 3: Full Retrieve Pipeline
        # ==========================================
        print(f"\n⏱️  BENCHMARK 3: Full Retrieve Pipeline ({iterations} iterations)")
        print("-" * 40)
        print("   (Load file → Parse → Search → Format for LLM)")
        
        def full_pipeline_json(filepath: str, search_term: str) -> str:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            results = search_memories(data, search_term)
            # Format for LLM context
            return json.dumps(results[:5], indent=2)
        
        def full_pipeline_toon(filepath: str, search_term: str) -> str:
            with open(filepath, "r", encoding="utf-8") as f:
                data = toon_decode(f.read())
            results = search_memories(data, search_term)
            # Format for LLM context (in TOON)
            return toon_encode(results[:5])
        
        # JSON pipeline
        json_pipeline_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            output = full_pipeline_json(json_file, "AI")
            json_pipeline_times.append((time.perf_counter() - start) * 1000)
        json_output_size = len(output)
        
        # TOON pipeline
        toon_pipeline_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            output = full_pipeline_toon(toon_file, "AI")
            toon_pipeline_times.append((time.perf_counter() - start) * 1000)
        toon_output_size = len(output)
        
        json_pipe_avg = statistics.mean(json_pipeline_times)
        toon_pipe_avg = statistics.mean(toon_pipeline_times)
        
        print(f"   JSON pipeline: {json_pipe_avg:.3f} ms (avg)")
        print(f"   TOON pipeline: {toon_pipe_avg:.3f} ms (avg)")
        
        # ==========================================
        # BENCHMARK 4: LLM Context Efficiency
        # ==========================================
        print(f"\n📊 BENCHMARK 4: LLM Context Efficiency")
        print("-" * 40)
        
        # Get 5 results and format for LLM
        results = search_memories(json_data, "AI")[:5]
        
        json_context = json.dumps(results, indent=2)
        toon_context = toon_encode(results)
        
        json_tokens = len(json_context) // 4
        toon_tokens = len(toon_context) // 4
        
        print(f"   JSON context: {len(json_context):,} chars (~{json_tokens} tokens)")
        print(f"   TOON context: {len(toon_context):,} chars (~{toon_tokens} tokens)")
        print(f"   Token reduction: {((json_tokens - toon_tokens) / json_tokens) * 100:.1f}%")
        
        # ==========================================
        # SUMMARY
        # ==========================================
        print("\n" + "=" * 60)
        print("📋 BENCHMARK SUMMARY")
        print("=" * 60)
        
        print("\n┌─────────────────────────┬──────────────┬──────────────┐")
        print("│ Metric                  │ JSON         │ TOON         │")
        print("├─────────────────────────┼──────────────┼──────────────┤")
        print(f"│ File Size               │ {json_size:>10,} B │ {toon_size:>10,} B │")
        print(f"│ Load+Parse (avg)        │ {json_avg:>10.3f} ms │ {toon_avg:>10.3f} ms │")
        print(f"│ Full Pipeline (avg)     │ {json_pipe_avg:>10.3f} ms │ {toon_pipe_avg:>10.3f} ms │")
        print(f"│ Context Size (5 items)  │ {len(json_context):>10,} ch │ {len(toon_context):>10,} ch │")
        print(f"│ Est. Tokens (5 items)   │ {json_tokens:>10,}    │ {toon_tokens:>10,}    │")
        print("└─────────────────────────┴──────────────┴──────────────┘")
        
        # Conclusion
        print("\n🎯 CONCLUSION:")
        storage_winner = "TOON" if toon_size < json_size else "JSON"
        parse_winner = "JSON" if json_avg < toon_avg else "TOON"
        token_winner = "TOON" if toon_tokens < json_tokens else "JSON"
        
        print(f"   • Storage efficiency: {storage_winner} wins ({((json_size - toon_size) / json_size) * 100:.1f}% smaller)")
        print(f"   • Parse speed: {parse_winner} is faster")
        print(f"   • Token efficiency: {token_winner} wins ({((json_tokens - toon_tokens) / json_tokens) * 100:.1f}% fewer tokens)")
        
        if toon_tokens < json_tokens:
            cost_reduction = ((json_tokens - toon_tokens) / json_tokens) * 100
            print(f"\n   💰 Using TOON for LLM context reduces costs by ~{cost_reduction:.0f}%")
        
        print("\n" + "=" * 60)
        print("✅ Benchmark completed!")
        print("=" * 60)
        
        return True


if __name__ == "__main__":
    print("\n🚀 GRKMemory TOON Storage Tests")
    print("Reference: https://github.com/toon-format/toon")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Basic Encode/Decode", test_toon_encode_decode),
        ("Array Handling", test_toon_with_list),
        ("Full Comparison", run_comparison_test),
        ("Retrieve Efficiency", benchmark_retrieve_efficiency),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️ Some tests failed"))
