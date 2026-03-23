# Documentazione Architetturale: BookWriterAI Multi-Layered Content Expansion System

## Panoramica

BookWriterAI implementa un **sistema avanzato di espansione contenuto multi-layered** progettato per generare libri di 300+ pagine con coerenza narrativa e densità di contenuto garantita. Il sistema combina:

- **Multi-Layered Content Expansion**: Generazione ricorsiva depth-first con validazione
- **Knowledge Base Contestuale**: RAG (Retrieval-Augmented Generation) per documenti PDF, TXT, Markdown
- **Adaptive Token Budgeting**: Allocazione intelligente del budget token basata su complessità
- **Progressive Outline Enrichment**: Arricchimento progressivo dell'outline in 3 fasi

## Novità: Multi-Layered Content Expansion System (v2.0)

### Componenti Principali

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-LAYERED CONTENT EXPANSION SYSTEM                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────┐ │
│  │ ProgressiveOutline  │───▶│  ChapterGenerator   │───▶│ ContentValidator│ │
│  │     Enricher        │    │  (RecursiveSection  │    │  (with retry)   │ │
│  │                     │    │    Generator)       │    │                 │ │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────┘ │
│           │                           │                           │         │
│           ▼                           ▼                           ▼         │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────┐ │
│  │  Blueprint Detail   │    │ AdaptiveTokenBudget │    │ CharacterDensity│ │
│  │   (sections/subsec) │    │  (complexity-based) │    │   Estimator     │ │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Progressive Outline Enrichment

Arricchimento dell'outline in 3 fasi:

**Fase 1: Outline Base**
- Titoli capitoli
- Descrizioni generali
- Target words per capitolo

**Fase 2: Blueprint Dettagliato**
- Sezioni principali (4-5 per capitolo)
- Sottosezioni specifiche (2-3 per sezione)
- Key points da coprire

**Fase 3: Finalizzazione**
- Metadati aggregate
- Stima pagine totali
- Validazione struttura

### 2. Recursive Section Generator

Generazione depth-first del contenuto:

```
Capitolo
├── Sezione 1 (depth=0)
│   ├── Contenuto principale
│   ├── Sottosezione 1.1 (depth=1)
│   │   └── Contenuto foglia
│   └── Sottosezione 1.2 (depth=1)
│       └── Contenuto foglia
├── Sezione 2 (depth=0)
│   └── ...
```

**Caratteristiche:**
- Profondità massima configurabile (`max_section_depth`)
- Contesto ereditato dal parent
- Supporto per case studies, examples, technical deep-dives

### 3. Adaptive Token Budget

Allocazione token basata su:

| Fattore | Peso | Descrizione |
|---------|------|-------------|
| Numero sottosezioni | +0.3 | ≥5 sottosezioni = più complesso |
| Target words | +0.3 | ≥10,000 parole = più complesso |
| Keyword complessità | +0.1×N | "analisi", "tecnico", "caso studio" |

**Context Windows Supportati:**

| Modello | Context Window | Raccomandato per |
|---------|---------------|------------------|
| qwen3.5-plus | 1,000,000 token | Libri 500+ pagine |
| qwen3-coder-plus | 1,000,000 token | Libri tecnici |
| kimi-k2.5 | 262,144 token | Libri 200-300 pagine |
| GPT-4 | 8,192-128K token | Libri brevi |

### 4. Content Validator

Validazione con trigger rigenerazione:

```python
{
    "valid": bool,              # Capitolo accettabile
    "word_count": int,          # Parole effettive
    "target_words": int,        # Parole target
    "density_ratio": float,     # Rapporto effettivo/target
    "needs_regeneration": bool  # Richiede rigenerazione
}
```

**Criteri:**
- Minimo 6,000 parole per capitolo (`min_chapter_words`)
- Densità minima 80% del target (`chapter_density_threshold`)
- Max 3 tentativi di rigenerazione

### 5. Character Density Estimator

Euristica avanzata per stima pagine:

```
pagine = (caratteri_effettivi × 0.85) / 3000
```

Dove:
- `0.85` = fattore correzione overhead markdown (15%)
- `3000` = caratteri per pagina A4 (standard editoriale)

**Vantaggi rispetto a word count:**
- Considera formattazione markdown
- Più accurato per layout tecnici
- Compensazione automatica per codice/tabelle

## Configurazione Multi-Layered

```python
@dataclass
class Config:
    # ... config esistente ...
    
    # Multi-layered content expansion settings
    min_chapter_words: int = 6000            # Minimo parole per capitolo
    chapter_density_threshold: float = 0.8   # Soglia densità (80%)
    enable_recursive_sections: bool = True   # Generazione ricorsiva
    enable_content_validation: bool = True   # Validazione contenuto
    enable_progressive_outline: bool = True  # Arricchimento outline
    compensatory_content_threshold: int = 245  # Pagine minime
    max_section_depth: int = 3               # Profondità max sezioni
    enable_adaptive_token_budget: bool = True  # Budget adattivo
```

## Flusso di Generazione (v2.0)

```
1. Generazione Outline Base
   └─▶ OutlineAgent.generate()

2. Arricchimento Progressivo (se abilitato)
   └─▶ ProgressiveOutlineEnricher.enrich()
       ├─▶ Fase 1: Outline base ✓
       ├─▶ Fase 2: Blueprint dettagliato
       └─▶ Fase 3: Finalizzazione

3. Generazione Capitoli (per ogni capitolo)
   └─▶ ChapterWriterAgent.write_chapter()
       ├─▶ Calcolo token budget adattivo
       ├─▶ Generazione ricorsiva sezioni
       ├─▶ Validazione contenuto
       └─▶ Rigenerazione se necessario (max 3x)

4. Validazione Finale
   └─▶ CharacterDensityEstimator
       ├─▶ Stima pagine accurata
       ├─▶ Confronto con target
       └─▶ Errore se < 245 pagine (o 70% target)

5. Compilazione e Salvataggio
   └─▶ CompilerAgent.compile_book()
```

## Knowledge Base System (Legacy)

Il sistema di Knowledge Base Contestuale è un modulo aggiuntivo che permette di arricchire la generazione di libri con contenuto da documenti di riferimento in formato PDF, TXT e Markdown.

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
    --provider bailian \
    --model "qwen3.5-plus"
```

### Provider Supportati

| Provider | Endpoint | Tipo API | Modelli |
|----------|----------|----------|---------|
| `openai` | https://api.openai.com/v1 | OpenAI nativa | gpt-4, gpt-3.5-turbo |
| `bailian` | https://coding-intl.dashscope.aliyuncs.com/v1 | OpenAI-compatible | qwen3.5-plus, kimi-k2.5, etc. |
| `qwen` | https://dashscope.aliyuncs.com/api/v1 | DashScope nativa | qwen-max (legacy) |

### Modelli Bailian (Coding Plan/OpenClaw)

| Modello | Context Window | Max Tokens | Input | Raccomandato per |
|---------|---------------|------------|-------|------------------|
| **`qwen3.5-plus`** ⭐ | **1,000,000** | 65,536 | text, image | **Libri lunghi (300+ pagine), documenti estesi** |
| `qwen3-max-2026-01-23` | 262,144 | 65,536 | text | Qualità massima |
| `qwen3-coder-next` | 262,144 | 65,536 | text | Codice e tecnico |
| `qwen3-coder-plus` | 1,000,000 | 65,536 | text | Codice e libri tecnici |
| `MiniMax-M2.5` | 196,608 | 32,768 | text | Generale purpose |
| `glm-5` | 202,752 | 16,384 | text | Generale purpose |
| `glm-4.7` | 202,752 | 16,384 | text | Generale purpose |
| `kimi-k2.5` | 262,144 | 32,768 | text, image | Generale purpose |

#### 🏆 Modello Consigliato: `qwen3.5-plus`

**Vantaggio competitivo**: Con **1 milione di token di context window** (~750,000 parole), `qwen3.5-plus` supera di gran lunga i modelli concorrenti:

| Modello | Context Window | Rapporto |
|---------|---------------|----------|
| **qwen3.5-plus** | **1,000,000 token** | **1x (baseline)** |
| Claude 3 Opus | 200,000 token | 5x inferiore |
| GPT-4 Turbo | 128,000 token | 8x inferiore |
| kimi-k2.5 | 262,144 token | 4x inferiore |

**Casi d'uso ideali per `qwen3.5-plus`:**

1. **Ebook di grandi dimensioni** (500+ pagine): L'intero outline e i capitoli precedenti rimangono in memoria
2. **Analisi di documenti estesi**: Report aziendali, contratti, documentazione tecnica completa
3. **Elaborazione di codebase**: Interi repository in un singolo prompt
4. **Traduzione di libri**: Mantenimento di coerenza terminologica su volumi completi
5. **Sintesi di ricerca**: Elaborazione simultanea di centinaia di paper scientifici

**Esempio pratico**: Un libro di 400 pagine (~200,000 parole) richiede circa 270,000 token. Con `qwen3.5-plus`, l'intero libro sta comodamente nel contesto, permettendo coerenza narrativa perfetta tra tutti i capitoli.

### Parametri Config

```python
@dataclass
class Config:
    provider: str = "openai"                     # "openai", "bailian" o "qwen"
    model: str = "gpt-4"                         # Modello specifico
    api_key: str = ""                            # Chiave API
    endpoint: Optional[str] = None               # URL personalizzato (solo openai)
    context_path: Optional[str] = None           # Path alla cartella documenti
    chunk_size: int = 1000                       # Token per chunk
    chunk_overlap: int = 200                     # Token di sovrapposizione
    max_context_chunks: int = 5                  # Chunk max nel prompt
    use_semantic_retrieval: bool = True          # Usa retrieval semantico
```

### Variabili d'Ambiente

```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# Bailian (Coding Plan/OpenClaw)
BAILIAN_API_KEY=your-bailian-api-key-here

# DashScope Legacy (fallback per bailian)
DASHSCOPE_API_KEY=your-dashscope-api-key-here
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
