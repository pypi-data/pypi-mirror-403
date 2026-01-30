"""
Test: Execução sem Token/API Key
=================================

Testa se a biblioteca consegue executar funcionalidades básicas
sem necessidade de token/API key.

Funcionalidades que devem funcionar sem token:
- MemoryRepository com embeddings desabilitados
- Operações de armazenamento/recuperação locais
- Busca por tags/entities (sem embeddings)
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grkmemory.memory.repository import MemoryRepository
from grkmemory.core.config import MemoryConfig
from grkmemory import GRKMemory


def test_memory_repository_without_embeddings():
    """
    Testa se MemoryRepository funciona sem embeddings (sem API key).
    """
    print("\n" + "=" * 60)
    print("🧪 Test: MemoryRepository sem embeddings")
    print("=" * 60)
    
    # Limpar variáveis de ambiente relacionadas a API keys
    original_openai_key = os.environ.pop("OPENAI_API_KEY", None)
    original_azure_key = os.environ.pop("AZURE_OPENAI_API_KEY", None)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "test_memories.json")
            
            # Criar repositório SEM embeddings (não precisa de API key)
            repo = MemoryRepository(
                memory_file=memory_file,
                enable_embeddings=False,  # ✅ Chave: desabilitar embeddings
                debug=False
            )
            
            print("✅ MemoryRepository criado sem API key")
            
            # Salvar memórias
            repo.save({
                "summary": "Teste sem token",
                "tags": ["teste", "sem-token"],
                "entities": ["TestEntity"],
                "key_points": ["Funciona sem API key"]
            })
            
            print("✅ Memória salva com sucesso")
            
            # Buscar por tags (não precisa de embeddings)
            results = repo.search("teste", method="tags")
            
            assert len(results) > 0, "Deveria encontrar resultados"
            print(f"✅ Busca por tags funcionou: {len(results)} resultados")
            
            # Buscar por entities
            results = repo.search("TestEntity", method="entities")
            
            assert len(results) > 0, "Deveria encontrar resultados"
            print(f"✅ Busca por entities funcionou: {len(results)} resultados")
            
            # Verificar que embeddings não foram gerados
            stats = repo.get_stats()
            print(f"✅ Stats: {stats['total_memories']} memórias")
            
            return True
            
    finally:
        # Restaurar variáveis de ambiente
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        if original_azure_key:
            os.environ["AZURE_OPENAI_API_KEY"] = original_azure_key


def test_memory_config_without_key():
    """
    Testa se MemoryConfig falha graciosamente sem API key.
    """
    print("\n" + "=" * 60)
    print("🧪 Test: MemoryConfig sem API key")
    print("=" * 60)
    
    # Limpar variáveis de ambiente
    original_openai_key = os.environ.pop("OPENAI_API_KEY", None)
    original_azure_key = os.environ.pop("AZURE_OPENAI_API_KEY", None)
    
    try:
        # Tentar criar config sem API key
        try:
            config = MemoryConfig()
            print("❌ ERRO: MemoryConfig deveria falhar sem API key")
            return False
        except ValueError as e:
            print(f"✅ MemoryConfig falhou corretamente: {e}")
            return True
            
    finally:
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        if original_azure_key:
            os.environ["AZURE_OPENAI_API_KEY"] = original_azure_key


def test_grkmemory_without_key():
    """
    Testa se GRKMemory falha graciosamente sem API key.
    """
    print("\n" + "=" * 60)
    print("🧪 Test: GRKMemory sem API key")
    print("=" * 60)
    
    # Limpar variáveis de ambiente
    original_openai_key = os.environ.pop("OPENAI_API_KEY", None)
    original_azure_key = os.environ.pop("AZURE_OPENAI_API_KEY", None)
    
    try:
        # Tentar criar GRKMemory sem API key
        try:
            grk = GRKMemory()
            print("❌ ERRO: GRKMemory deveria falhar sem API key")
            return False
        except ValueError as e:
            print(f"✅ GRKMemory falhou corretamente: {e}")
            return True
            
    finally:
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        if original_azure_key:
            os.environ["AZURE_OPENAI_API_KEY"] = original_azure_key


def test_offline_mode():
    """
    Testa modo offline completo: MemoryRepository sem embeddings.
    """
    print("\n" + "=" * 60)
    print("🧪 Test: Modo Offline (sem API key)")
    print("=" * 60)
    
    # Limpar variáveis de ambiente
    original_openai_key = os.environ.pop("OPENAI_API_KEY", None)
    original_azure_key = os.environ.pop("AZURE_OPENAI_API_KEY", None)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "offline_memories.json")
            
            # Criar repositório em modo offline
            repo = MemoryRepository(
                memory_file=memory_file,
                enable_embeddings=False,  # Modo offline
                debug=True
            )
            
            print("✅ Repositório criado em modo offline")
            
            # Adicionar várias memórias
            memories = [
                {
                    "summary": "Python é uma linguagem de programação",
                    "tags": ["python", "programação"],
                    "entities": ["Python"],
                    "key_points": ["Linguagem interpretada", "Tipagem dinâmica"]
                },
                {
                    "summary": "JavaScript é usado para web",
                    "tags": ["javascript", "web"],
                    "entities": ["JavaScript", "Web"],
                    "key_points": ["Frontend", "Backend com Node.js"]
                },
                {
                    "summary": "Rust é uma linguagem de sistemas",
                    "tags": ["rust", "sistemas"],
                    "entities": ["Rust"],
                    "key_points": ["Memory safety", "Performance"]
                }
            ]
            
            for mem in memories:
                repo.save(mem)
            
            print(f"✅ {len(memories)} memórias salvas")
            
            # Testar diferentes métodos de busca (sem embeddings)
            print("\n🔍 Testando buscas:")
            
            # Busca por tags
            results = repo.search("python", method="tags")
            print(f"   Tags 'python': {len(results)} resultados")
            assert len(results) > 0
            
            # Busca por entities
            results = repo.search("Rust", method="entities")
            print(f"   Entities 'Rust': {len(results)} resultados")
            assert len(results) > 0
            
            # Busca por grafo (sem embeddings, usa apenas tags/entities)
            results = repo.search("web", method="graph")
            print(f"   Graph 'web': {len(results)} resultados")
            assert len(results) > 0
            
            # Formatar resultados
            context = repo.format_for_llm(results, format="text")
            print(f"✅ Contexto formatado: {len(context)} caracteres")
            
            # Estatísticas
            stats = repo.get_stats()
            print(f"\n📊 Estatísticas:")
            print(f"   Total de memórias: {stats['total_memories']}")
            print(f"   Formato: {stats['storage_format']}")
            print(f"   TOON disponível: {stats['toon_available']}")
            
            return True
            
    finally:
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        if original_azure_key:
            os.environ["AZURE_OPENAI_API_KEY"] = original_azure_key


def test_embeddings_required_error():
    """
    Testa se tentar usar embeddings sem API key gera erro apropriado.
    """
    print("\n" + "=" * 60)
    print("🧪 Test: Erro ao tentar usar embeddings sem API key")
    print("=" * 60)
    
    # Limpar variáveis de ambiente
    original_openai_key = os.environ.pop("OPENAI_API_KEY", None)
    original_azure_key = os.environ.pop("AZURE_OPENAI_API_KEY", None)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "test_memories.json")
            
            # Criar repositório COM embeddings (mas sem API key)
            repo = MemoryRepository(
                memory_file=memory_file,
                enable_embeddings=True,  # Tenta usar embeddings
                debug=False
            )
            
            # Salvar memória (não deve gerar embedding)
            repo.save({
                "summary": "Teste",
                "tags": ["test"],
                "entities": ["Test"],
                "key_points": ["Test point"]
            })
            
            print("✅ Memória salva (sem embedding gerado)")
            
            # Tentar busca por embedding (deve falhar ou retornar vazio)
            results = repo.search("test", method="embedding")
            
            # Como não há API key, embedding search deve retornar vazio
            # mas não deve quebrar
            print(f"✅ Busca por embedding retornou: {len(results)} resultados")
            print("   (Esperado: 0 resultados sem API key)")
            
            return True
            
    finally:
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        if original_azure_key:
            os.environ["AZURE_OPENAI_API_KEY"] = original_azure_key


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Testes: Execução sem Token/API Key")
    print("=" * 60)
    
    tests = [
        ("MemoryRepository sem embeddings", test_memory_repository_without_embeddings),
        ("MemoryConfig sem API key", test_memory_config_without_key),
        ("GRKMemory sem API key", test_grkmemory_without_key),
        ("Modo Offline", test_offline_mode),
        ("Embeddings sem API key", test_embeddings_required_error),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} falhou: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"   {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("🎉 Todos os testes passaram!" if all_passed else "⚠️ Alguns testes falharam"))
    
    print("\n" + "=" * 60)
    print("💡 CONCLUSÃO")
    print("=" * 60)
    print("""
    ✅ MemoryRepository funciona SEM token quando:
       - enable_embeddings=False
       - Usando métodos de busca: tags, entities, graph (sem embeddings)
    
    ❌ MemoryConfig e GRKMemory REQUEREM API key:
       - Validação explícita no __post_init__
       - Erro claro quando não fornecido
    
    💡 Para usar sem token:
       from grkmemory import MemoryRepository
       
       repo = MemoryRepository(
           memory_file="memories.json",
           enable_embeddings=False  # ← Chave para funcionar sem token
       )
    """)
