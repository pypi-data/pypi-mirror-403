"""
Embedding utilities for GRKMemory.

Supports both OpenAI and Azure OpenAI APIs.
"""

import os
import math
from typing import List, Optional, Union
from openai import OpenAI, AzureOpenAI


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embedding vectors.
    
    Args:
        embedding1: First embedding vector.
        embedding2: Second embedding vector.
    
    Returns:
        Similarity score between 0 and 1.
    
    Example:
        >>> vec1 = [1.0, 0.0, 0.0]
        >>> vec2 = [1.0, 0.0, 0.0]
        >>> cosine_similarity(vec1, vec2)
        1.0
    """
    if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
        return 0.0
    
    dot = sum(a * b for a, b in zip(embedding1, embedding2))
    norm1 = math.sqrt(sum(a * a for a in embedding1))
    norm2 = math.sqrt(sum(b * b for b in embedding2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot / (norm1 * norm2)


class EmbeddingGenerator:
    """
    Generator for text embeddings using OpenAI or Azure OpenAI API.
    
    Supports both OpenAI and Azure OpenAI APIs. Azure is auto-detected
    from environment variables or can be explicitly configured.
    
    Example:
        # OpenAI (default)
        generator = EmbeddingGenerator(model="text-embedding-3-small")
        embedding = generator.generate("Hello world")
        
        # Azure OpenAI
        generator = EmbeddingGenerator(
            model="text-embedding-3-small",
            use_azure=True,
            azure_endpoint="https://your-resource.openai.azure.com",
            azure_deployment="your-embedding-deployment"
        )
        embedding = generator.generate("Hello world")
    """
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        client: Optional[Union[OpenAI, AzureOpenAI]] = None,
        use_azure: Optional[bool] = None,
        azure_endpoint: Optional[str] = None,
        azure_api_version: str = "2024-02-01",
        azure_deployment: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the embedding generator.
        
        Args:
            model: The embedding model to use.
            client: Optional OpenAI/AzureOpenAI client. If not provided, creates a new one.
            use_azure: Whether to use Azure OpenAI. Auto-detected from env if None.
            azure_endpoint: Azure OpenAI endpoint URL.
            azure_api_version: Azure API version (default: 2024-02-01).
            azure_deployment: Azure deployment name for embeddings.
            api_key: API key (uses env var if not provided).
        """
        self.model = model
        
        if client:
            self.client = client
            self.use_azure = isinstance(client, AzureOpenAI)
            self.azure_deployment = azure_deployment
        else:
            # Auto-detect Azure from environment
            if use_azure is None:
                use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
            
            self.use_azure = use_azure
            
            if use_azure:
                # Azure OpenAI
                self.azure_deployment = azure_deployment or os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT") or model
                azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
                api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
                
                if not azure_endpoint or not api_key:
                    # Lazy initialization - will create client when needed
                    self.client = None
                else:
                    self.client = AzureOpenAI(
                        api_key=api_key,
                        api_version=azure_api_version,
                        azure_endpoint=azure_endpoint
                    )
            else:
                # Standard OpenAI
                # Only create client if API key is available
                api_key = api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    # Lazy initialization - will create client when needed
                    self.client = None
                else:
                    self.client = OpenAI(api_key=api_key)
                self.azure_deployment = None
    
    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for a text string.
        
        Args:
            text: The text to embed.
        
        Returns:
            List of floats representing the embedding vector.
        """
        if not text or not text.strip():
            return []
        
        # Lazy initialization of client if needed
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
            if not api_key:
                print("⚠️ No API key available. Cannot generate embeddings.")
                return []
            
            if self.use_azure:
                azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                if not azure_endpoint:
                    print("⚠️ Azure endpoint not configured. Cannot generate embeddings.")
                    return []
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version=self.azure_api_version,
                    azure_endpoint=azure_endpoint
                )
            else:
                self.client = OpenAI(api_key=api_key)
        
        try:
            # Use deployment name for Azure, model name for OpenAI
            model_or_deployment = self.azure_deployment if self.use_azure else self.model
            
            response = self.client.embeddings.create(
                model=model_or_deployment,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️ Error generating embedding: {e}")
            return []
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed.
        
        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [[] for _ in texts]
        
        # Lazy initialization of client if needed
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
            if not api_key:
                print("⚠️ No API key available. Cannot generate embeddings.")
                return [[] for _ in texts]
            
            if self.use_azure:
                azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                if not azure_endpoint:
                    print("⚠️ Azure endpoint not configured. Cannot generate embeddings.")
                    return [[] for _ in texts]
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version=self.azure_api_version,
                    azure_endpoint=azure_endpoint
                )
            else:
                self.client = OpenAI(api_key=api_key)
        
        try:
            # Use deployment name for Azure, model name for OpenAI
            model_or_deployment = self.azure_deployment if self.use_azure else self.model
            
            response = self.client.embeddings.create(
                model=model_or_deployment,
                input=valid_texts
            )
            
            # Map back to original indices
            embeddings = [[] for _ in texts]
            valid_idx = 0
            for i, text in enumerate(texts):
                if text and text.strip():
                    embeddings[i] = response.data[valid_idx].embedding
                    valid_idx += 1
            
            return embeddings
        except Exception as e:
            print(f"⚠️ Error generating batch embeddings: {e}")
            return [[] for _ in texts]
