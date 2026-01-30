"""
Configuration module for GRKMemory.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Literal

# Storage format types
StorageFormat = Literal["json", "toon"]
OutputFormat = Literal["json", "toon", "text"]


@dataclass
class MemoryConfig:
    """
    Configuration for GRKMemory memory system.
    
    Supports both OpenAI and Azure OpenAI APIs.
    
    Attributes:
        api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
        model: OpenAI model to use for processing.
        embedding_model: Model for generating embeddings.
        memory_file: Path to the file storing memories (extension auto-detected or use storage_format).
        enable_embeddings: Whether to generate embeddings for semantic search.
        debug: Enable debug logging.
        background_memory_enabled: Enable background memory retrieval.
        background_memory_limit: Maximum number of memories to retrieve.
        background_memory_method: Search method ('graph', 'embedding', 'tags', 'entities').
        background_memory_threshold: Minimum similarity threshold for retrieval.
        storage_format: Format for storing memories ('json' or 'toon').
        output_format: Format for retrieve output ('json', 'toon', or 'text').
        
        # Azure OpenAI Configuration
        use_azure: Whether to use Azure OpenAI instead of OpenAI.
        azure_endpoint: Azure OpenAI endpoint URL.
        azure_api_version: Azure OpenAI API version.
        azure_deployment: Azure OpenAI deployment name for chat model.
        azure_embedding_deployment: Azure OpenAI deployment name for embeddings.
    
    Example:
        # OpenAI (default)
        config = MemoryConfig(
            api_key="sk-...",
            model="gpt-4o",
            memory_file="my_memories.json"
        )
        
        # Azure OpenAI
        config = MemoryConfig(
            use_azure=True,
            api_key="your-azure-api-key",
            azure_endpoint="https://your-resource.openai.azure.com",
            azure_deployment="gpt-4o",
            azure_embedding_deployment="text-embedding-3-small",
            azure_api_version="2024-02-01"
        )
        
        # Hybrid: JSON storage, TOON output (recommended)
        config = MemoryConfig(
            model="gpt-4o",
            memory_file="my_memories.json",
            storage_format="json",      # Fast parsing
            output_format="toon"        # Token-efficient for LLM
        )
    """
    
    # OpenAI Configuration
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))
    model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    memory_file: str = "graph_retrieve_knowledge_memory.json"
    enable_embeddings: bool = True
    debug: bool = False
    background_memory_enabled: bool = True
    background_memory_limit: int = 5
    background_memory_method: str = "graph"
    background_memory_threshold: float = 0.3
    storage_format: StorageFormat = "json"
    output_format: OutputFormat = "json"
    
    # Azure OpenAI Configuration
    use_azure: bool = field(default_factory=lambda: os.getenv("USE_AZURE_OPENAI", "false").lower() == "true")
    azure_endpoint: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT"))
    azure_api_version: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"))
    azure_deployment: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_OPENAI_DEPLOYMENT"))
    azure_embedding_deployment: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"))
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError(
                "API key is required. Set OPENAI_API_KEY (or AZURE_OPENAI_API_KEY for Azure) "
                "environment variable or pass api_key to MemoryConfig."
            )
        
        # Validate Azure configuration
        if self.use_azure:
            if not self.azure_endpoint:
                raise ValueError(
                    "Azure endpoint is required when use_azure=True. "
                    "Set AZURE_OPENAI_ENDPOINT environment variable or pass azure_endpoint."
                )
            if not self.azure_deployment:
                raise ValueError(
                    "Azure deployment name is required when use_azure=True. "
                    "Set AZURE_OPENAI_DEPLOYMENT environment variable or pass azure_deployment."
                )
        
        valid_methods = {"graph", "embedding", "tags", "entities"}
        if self.background_memory_method not in valid_methods:
            raise ValueError(
                f"Invalid background_memory_method: {self.background_memory_method}. "
                f"Must be one of: {valid_methods}"
            )
        
        # Validate storage format
        valid_storage_formats = {"json", "toon"}
        if self.storage_format not in valid_storage_formats:
            raise ValueError(
                f"Invalid storage_format: {self.storage_format}. "
                f"Must be one of: {valid_storage_formats}"
            )
        
        # Validate output format
        valid_output_formats = {"json", "toon", "text"}
        if self.output_format not in valid_output_formats:
            raise ValueError(
                f"Invalid output_format: {self.output_format}. "
                f"Must be one of: {valid_output_formats}"
            )
        
        # Auto-detect storage format from file extension if not explicitly set
        if self.memory_file.endswith(".toon"):
            self.storage_format = "toon"
        elif self.memory_file.endswith(".json"):
            self.storage_format = "json"
        
        # Set API key in environment for OpenAI client
        if self.use_azure:
            os.environ["AZURE_OPENAI_API_KEY"] = self.api_key
            os.environ["AZURE_OPENAI_ENDPOINT"] = self.azure_endpoint
        else:
            os.environ["OPENAI_API_KEY"] = self.api_key
    
    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """
        Create configuration from environment variables.
        
        Environment variables:
            # OpenAI Configuration
            OPENAI_API_KEY: API key for OpenAI
            OPENAI_MODEL: Model name (default: gpt-4o)
            OPENAI_EMBEDDING_MODEL: Embedding model (default: text-embedding-3-small)
            
            # Azure OpenAI Configuration
            USE_AZURE_OPENAI: true/false (default: false)
            AZURE_OPENAI_API_KEY: API key for Azure OpenAI
            AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
            AZURE_OPENAI_API_VERSION: API version (default: 2024-02-01)
            AZURE_OPENAI_DEPLOYMENT: Deployment name for chat model
            AZURE_OPENAI_EMBEDDING_DEPLOYMENT: Deployment name for embeddings
            
            # General Configuration
            MEMORY_FILE: Memory file path
            ENABLE_EMBEDDINGS: true/false
            DEBUG: true/false
            BACKGROUND_MEMORY_ENABLED: true/false
            BACKGROUND_MEMORY_LIMIT: integer
            BACKGROUND_MEMORY_METHOD: graph/embedding/tags/entities
            BACKGROUND_MEMORY_THRESHOLD: float
            STORAGE_FORMAT: json/toon (default: json)
            OUTPUT_FORMAT: json/toon/text (default: json)
        """
        use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
        
        # Get API key from appropriate source
        api_key = os.getenv("AZURE_OPENAI_API_KEY") if use_azure else os.getenv("OPENAI_API_KEY")
        
        return cls(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            memory_file=os.getenv("MEMORY_FILE", "graph_retrieve_knowledge_memory.json"),
            enable_embeddings=os.getenv("ENABLE_EMBEDDINGS", "true").lower() == "true",
            debug=os.getenv("DEBUG", "false").lower() == "true",
            background_memory_enabled=os.getenv("BACKGROUND_MEMORY_ENABLED", "true").lower() == "true",
            background_memory_limit=int(os.getenv("BACKGROUND_MEMORY_LIMIT", "5")),
            background_memory_method=os.getenv("BACKGROUND_MEMORY_METHOD", "graph"),
            background_memory_threshold=float(os.getenv("BACKGROUND_MEMORY_THRESHOLD", "0.3")),
            storage_format=os.getenv("STORAGE_FORMAT", "json"),
            output_format=os.getenv("OUTPUT_FORMAT", "json"),
            use_azure=use_azure,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            azure_embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        )
