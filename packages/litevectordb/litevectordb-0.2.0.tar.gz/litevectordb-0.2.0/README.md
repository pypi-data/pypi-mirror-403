# LiteVectorDB

> **Banco de dados vetorial local, leve e simples. Sem servidor, sem complicação.**

## 🎯 Slogan e Descrição

**Slogan:** *"Vector Search, Zero Fuss"*

**Descrição curta:** LiteVectorDB é um banco de dados vetorial local construído sobre SQLite e NumPy. Perfeito para prototipagem rápida, aplicações desktop, e sistemas que precisam de busca semântica sem a complexidade de soluções enterprise.

---

## 📖 Por Que Existe / Missão do Projeto

### O Problema

A busca vetorial e bancos de dados semânticos estão se tornando essenciais para aplicações modernas de IA. No entanto, as soluções existentes frequentemente apresentam barreiras significativas:

- **Complexidade de setup**: Soluções como Chroma, Pinecone ou Weaviate requerem servidores dedicados, configuração de infraestrutura e dependências pesadas
- **Overhead desnecessário**: Para projetos pequenos, protótipos ou aplicações desktop, você não precisa de toda a infraestrutura de um banco vetorial distribuído
- **Dependências externas**: Muitas soluções dependem de serviços em nuvem ou APIs externas, limitando a portabilidade e privacidade
- **Curva de aprendizado**: Configuração e uso podem ser intimidantes para desenvolvedores que só querem adicionar busca semântica rapidamente

### A Missão

LiteVectorDB existe para democratizar o acesso à busca vetorial, oferecendo:

1. **Simplicidade**: Uma biblioteca Python que você instala e usa imediatamente, sem configuração complexa
2. **Portabilidade**: Um único arquivo SQLite que contém tudo - perfeito para distribuir com sua aplicação
3. **Privacidade**: Tudo roda localmente, sem necessidade de conexões externas ou serviços em nuvem
4. **Leveza**: Dependências mínimas (SQLite + NumPy), sem overhead de servidores ou infraestrutura
5. **Flexibilidade**: Interface simples para uso direto, mas também APIs de baixo nível para casos avançados

### Para Quem?

- **Desenvolvedores de protótipos** que precisam de busca semântica rápida sem setup complexo
- **Aplicações desktop** que precisam de memória vetorial local
- **Projetos educacionais** que querem entender como funciona busca vetorial na prática
- **Sistemas embarcados** ou edge computing que precisam de busca vetorial offline
- **Desenvolvedores que valorizam simplicidade** sobre features enterprise

---

## 🏗️ Arquitetura do Banco

### Visão Geral

LiteVectorDB utiliza uma arquitetura em camadas, construída sobre SQLite para persistência e NumPy para operações vetoriais:

```
┌────────────────────────────────────────────────────────┐
│                    Camada de Aplicação                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ LocalVectorDB│  │  MemoryDB    │  │  FastAPI     │  │
│  │  (Interface  │  │  (Memória    │  │  (API REST)  │  │
│  │   Simples)   │  │   de Sessão) │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼─────────────────┼─────────────────┼──────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────┐
│              Camada de Armazenamento                     │
│                    VectorStore                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  • Gerenciamento de conexão SQLite               │    │
│  │  • Encode/Decode de vetores (BLOB)               │    │
│  │  • Operações CRUD (add, get, delete, upsert)     │    │
│  │  • Busca por similaridade de cosseno             │    │
│  └──────────────────────────────────────────────────┘    │
└───────────────────────────┬──────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│              Camada de Persistência                     │
│                    SQLite Database                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Tabela: documents                               │   │
│  │  ┌────┬─────┬─────────┬──────────┬───────┬─────┐ │   │
│  │  │ id │ key │ content │ metadata │ vector│ dim │ │   │
│  │  └────┴─────┴─────────┴──────────┴───────┴─────┘ │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Estrutura do Banco de Dados

A tabela `documents` armazena todos os dados vetoriais:

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE,              -- Chave opcional para upsert
    content TEXT,                 -- Texto original do documento
    metadata TEXT,                -- JSON com metadados adicionais
    vector BLOB NOT NULL,         -- Vetor de embedding (float32[])
    dim INTEGER NOT NULL,         -- Dimensão do vetor
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Componentes Principais

#### 1. **VectorStore** (`vector_store.py`)
- **Responsabilidade**: Camada de baixo nível para operações vetoriais
- **Funcionalidades**:
  - Armazenamento de vetores como BLOB no SQLite
  - Busca por similaridade de cosseno (em memória)
  - Operações CRUD completas (add, get, delete, upsert)
  - Gerenciamento de conexão SQLite com WAL mode

#### 2. **LocalVectorDB** (`client.py`)
- **Responsabilidade**: Interface de alto nível simplificada
- **Funcionalidades**:
  - Adicionar textos com geração automática de embeddings
  - Busca semântica com resultados tipados
  - Gerenciamento automático de metadados

#### 3. **MemoryDB** (`memory.py`)
- **Responsabilidade**: Sistema de memória por sessão
- **Funcionalidades**:
  - Armazenamento de memórias por `session_id`
  - Recuperação contextual de memórias relevantes
  - Filtragem automática por sessão

#### 4. **Embeddings** (`embeddings.py`)
- **Responsabilidade**: Geração de embeddings
- **Nota**: Inclui função `fake_embed` para testes. Em produção, substitua por OpenAI, Ollama, ou outro provedor.

### Algoritmo de Busca

A busca vetorial utiliza **similaridade de cosseno**:

1. **Normalização**: Cada vetor é normalizado (L2 norm)
2. **Cálculo de Similaridade**: `score = dot(query, vector) / (||query|| * ||vector||)`
3. **Filtragem**: Apenas resultados com `score >= min_score` são retornados
4. **Ordenação**: Resultados ordenados por score (decrescente)
5. **Top-K**: Retorna apenas os `top_k` melhores resultados

**Nota**: A busca atual é linear (O(n)) e funciona bem para até alguns milhares de vetores. Para datasets maiores, considere implementar índices como HNSW ou IVF.

---

## 🚀 Instalação

```bash
pip install litevectordb
```

Ou instale a partir do código:

```bash
git clone https://github.com/seuuser/litevectordb
cd litevectordb
pip install -e .
```

### Dependências

- Python >= 3.9
- numpy >= 1.21
- sqlite3 (incluído no Python padrão)

---

## 📊 Limitações e Considerações

### Performance

- **Busca Linear**: A busca atual é O(n) e funciona bem para até ~10.000 documentos
- **Em Memória**: Todos os vetores são carregados em memória durante a busca
- **Sem Índices**: Não há índices vetoriais (HNSW, IVF) para otimização

### Escalabilidade

Para datasets maiores (>50k documentos), considere:
- Implementar índices vetoriais (HNSW via `hnswlib`)
- Usar busca aproximada (ANN)
- Particionar dados em múltiplos bancos

### Embeddings

- A função `fake_embed` é apenas para testes/demos
- Em produção, use embeddings reais (OpenAI, Sentence Transformers, etc.)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Abrir issues para bugs ou sugestões
2. Fazer fork e criar pull requests
3. Melhorar a documentação
4. Adicionar novos exemplos

---

## 📝 Licença

MIT License - veja o arquivo LICENSE para detalhes.

---

## 🔗 Links Úteis

- [Documentação SQLite](https://www.sqlite.org/docs.html)
- [NumPy Documentation](https://numpy.org/doc/)
- [Vector Search Concepts](https://www.pinecone.io/learn/vector-database/)

---

**Desenvolvido com ❤️ para a comunidade Python**

