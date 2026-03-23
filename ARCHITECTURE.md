# Documentazione Architetturale: Knowledge Base System

## Panoramica

Il sistema di Knowledge Base Contestuale è un modulo aggiuntivo a `BookWriterAI` che permette di arricchire la generazione di libri con contenuto da documenti di riferimento in formato PDF, TXT e Markdown.

## Architettura del Sistema

### Diagramma dei Componenti

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BookOrchestrator                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      Knowledge Base System                            │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────┐ │  │
│  │  │   Document  │──▶│   Document  │──▶│    Text     │──▶│  Index   │ │  │
│  │  │   Loader    │   │   Parser    │   │   Chunker   │   │  Manager │ │  │
│  │  │  (Factory)  │   │  (Strategy) │   │   (Window)  │   │ (Cache)  │ │  │
│  │  └─────────────┘   └─────────────┘   └─────────────┘   └──────────┘ │  │
│  │         │                 │                  │               │        │  │
│  │         ▼                 ▼                  ▼               ▼        │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │              ContextRetriever (TF-IDF + Keywords)              │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐       │
│  │OutlineAgent │           │ChapterWriter│           │ EditorAgent │       │
│  │             │           │   Agent     │           │             │       │
│  └─────────────┘           └─────────────┘           └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Pattern di Design Utilizzati

### 1. Strategy Pattern - DocumentParser

**Scopo**: Permettere l'aggiunta di nuovi formati di documento senza modificare il codice esistente.

```python
class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]: ...
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool: ...

class PDFParser(DocumentParser): ...
class TXTParser(DocumentParser): ...
class MarkdownParser(DocumentParser): ...
```

**Vantaggi**:
- Estensibilità: nuovi formati aggiungibili implementando `DocumentParser`
- Testabilità: ogni parser può essere testato isolatamente
- Separazione delle responsabilità: ogni parser gestisce un solo formato

### 2. Sliding Window - TextChunker

**Scopo**: Dividere documenti lunghi in chunk gestibili mantenendo la coerenza semantica.

**Algoritmo**:
1. Suddivisione in paragrafi ai confini di linee vuote
2. Raggruppamento di paragrafi fino al limite di token
3. Sovrapposizione configurabile tra chunk consecutivi
4. Spezzettamento di paragrafi troppo lunghi a livello di frase

**Parametri configurabili**:
- `chunk_size`: dimensione target in token (default: 1000)
- `chunk_overlap`: token di sovrapposizione (default: 200)

### 3. TF-IDF Semplificato - ContextRetriever

**Scopo**: Selezionare i chunk più rilevanti per una query data.

**Implementazione**:
- **Term Frequency (TF)**: frequenza relativa delle parole nel chunk
- **Inverse Document Frequency (IDF)**: semplificato a 1.0 (può essere esteso)
- **Scoring**: somma di TF-IDF per tutte le keyword della query
- **Bonus**: match esatti della query (+2.0), match nel titolo (+1.5)

### 4. Facade Pattern - KnowledgeBase

**Scopo**: Fornire una interfaccia semplificata per l'intero sistema.

```python
class KnowledgeBase:
    def initialize() -> bool
    def get_relevant_context(query: str) -> str
    def get_context_for_chapter(chapter_info: Dict) -> str
    def get_stats() -> Dict[str, Any]
```

### 5. Caching - IndexManager

**Scopo**: Evitare di re-indicizzare documenti già processati.

**Chiave di cache**: hash dei parametri (chunk_size, chunk_overlap, context_path)
**Formato**: pickle binario per efficienza
**Invalidazione**: automatica quando cambiano i parametri

## Flusso di Dati

### Inizializzazione

```
1. BookOrchestrator.__init__()
   └─▶ KnowledgeBase.initialize()
       ├─▶ Verifica path contestuale
       ├─▶ Caricamento da cache (se valida)
       └─▶ Altrimenti:
           ├─▶ DocumentLoader.scansiona directory
           ├─▶ Per ogni file: DocumentParser.parse()
           ├─▶ TextChunker.chunk_document()
           ├─▶ ContextRetriever.__init__()
           └─▶ Salvataggio cache
```

### Retrieval durante la Generazione

```
1. ChapterWriterAgent.write_chapter()
   └─▶ KnowledgeBase.get_context_for_chapter()
       ├─▶ ContextRetriever.retrieve_by_chapter_context()
       │   ├─▶ Estrazione keyword da titolo + descrizione
       │   ├─▶ Lookup nell'indice inverso
       │   └─▶ Ranking per rilevanza
       └─▶ Formattazione contesto
           └─▶ Iniezione nel prompt
```

## Gestione Errori

### Livelli di Errore

| Livello | Componente | Azione | Log |
|---------|-----------|--------|-----|
| Warning | DocumentParser | Salta file, continua | `logger.warning()` |
| Error | KnowledgeBase.initialize() | Disabilita KB, continua senza contesto | `logger.error()` |
| Critical | Config.__post_init__() | Termina esecuzione | `raise ValueError()` |

### Errori Gestiti

1. **File corrotto**: catturato nel parser, restituito in `result["error"]`
2. **Encoding non supportato**: tentativi multipli con encoding diversi
3. **PDF scansionato**: rilevato quando `extract_text()` restituisce stringa vuota
4. **Dipendenza mancante**: graceful degradation (es. PDF senza PyPDF2)

## Configurazione

### Parametri CLI

```bash
python ebooks.py \
    --topic "Il futuro dell'educazione con l'IA" \
    --pages 400 \
    --context "/home/user/context" \
    --provider openai \
    --endpoint "https://coding-intl.dashscope.aliyuncs.com/v1" \
    --model "kimi-k2.5"
```

### Parametri Config

```python
@dataclass
class Config:
    context_path: Optional[str] = None          # Path alla cartella documenti
    chunk_size: int = 1000                       # Token per chunk
    chunk_overlap: int = 200                     # Token di sovrapposizione
    max_context_chunks: int = 5                  # Chunk max nel prompt
    use_semantic_retrieval: bool = True          # Usa retrieval semantico
```

## Estensione del Sistema

### Aggiungere un Nuovo Formato

```python
class DOCXParser(DocumentParser):
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.docx'
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        # Implementazione parsing DOCX
        ...

# In KnowledgeBase.__init__():
self.parsers = [
    PDFParser(),
    TXTParser(),
    MarkdownParser(),
    DOCXParser(),  # Nuovo!
]
```

### Aggiungere Retrieval Semantico (Embeddings)

```python
class SemanticRetriever:
    def __init__(self, chunks: List[TextChunk], embedding_model):
        self.embeddings = self._compute_embeddings(chunks, embedding_model)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[TextChunk]:
        query_embedding = self.embeddings.encode(query)
        similarities = cosine_similarity(query_embedding, self.embeddings)
        return top_k_chunks_by_similarity(similarities)
```

## Performance Considerazioni

### Ottimizzazioni Implementate

1. **Caching**: l'indice viene salvato in `checkpoints/kb_cache/index.pkl`
2. **Lazy Loading**: i documenti sono caricati solo all'inizializzazione
3. **Indice Invertito**: lookup O(1) per keyword
4. **Token Counting Approssimativo**: fallback a `len(text) // 4` se tiktoken fallisce

### Metriche Attese

| Operazione | Complessità | Tempo tipico (1000 pagine) |
|------------|-------------|---------------------------|
| Parsing PDF | O(n) | 2-5 secondi |
| Chunking | O(n) | < 1 secondo |
| Build indice | O(n × m) | < 1 secondo |
| Retrieval | O(k × log n) | < 100ms |

## Sicurezza

### Validazioni

- **Path traversal**: risolto usando `Path.resolve()`
- **File size**: nessun limite implementato (da aggiungere se necessario)
- **Pickle cache**: caricato solo da directory controllata (`checkpoints/`)

## Conclusioni

L'architettura modulare permette:
- **Manutenibilità**: ogni componente ha una responsabilità singola
- **Testabilità**: componenti isolati testabili unitariamente
- **Estensibilità**: nuovi formati e strategie di retrieval aggiungibili
- **Resilienza**: graceful degradation in caso di errori
