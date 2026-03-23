# Piano di Refactoring Architetturale: Multi-Layered Content Expansion System

## Obiettivo
Implementare un sistema avanzato per generare libri di 300+ pagine con coerenza narrativa e densità di contenuto garantita.

## Componenti da Implementare

### 1. Dynamic Chapter Subdivision System
- Monitora la densità di contenuto durante la generazione
- Splits automatico quando il contenuto è inferiore alla soglia target
- Calcola word count effettivo vs target per capitolo

### 2. Recursive Section Generation (Depth-First)
- Struttura ad albero: Capitolo → Sezioni → Sottosezioni → Paragrafi
- Generazione depth-first: completa una sezione prima di passare alla successiva
- Supporta: case studies, examples, technical deep-dives

### 3. Adaptive Token Budgeting
- Assegna token proporzionalmente in base alla complessità del capitolo
- Complexity scoring basato su: numero di sottosezioni, topic density, richieste di esempi
- Prioritizza modelli con 1M+ token (qwen3.5-plus)

### 4. Content Validation Loops
- Verifica word count minimo per capitolo
- Trigger di rigenerazione se sotto soglia
- Retry con prompt più enfatico

### 5. Progressive Outline Enrichment
- Fase 1: Outline base (titoli + descrizioni)
- Fase 2: Espansione in blueprint dettagliati (sezioni + sottosezioni)
- Fase 3: Generazione testo completo

### 6. Chapter-Level Checkpointing
- Salva stato dopo ogni capitolo completato
- Previene context drift mantenendo riassunti progressivi
- Supporta resume da checkpoint

### 7. Character-Density Heuristic
- Stima pagine basata su: caratteri / 3000 (standard editoriale)
- Considera overhead formattazione markdown
- Genera contenuto compensatorio se proiezione < 245 pagine

## Schema Architetturale

```
BookOrchestrator
├── ProgressiveOutlineEnricher
│   ├── Phase 1: Basic Outline
│   └── Phase 2: Detailed Blueprint
├── ChapterGenerator (per ogni capitolo)
│   ├── AdaptiveTokenBudget
│   ├── RecursiveSectionGenerator
│   │   └── Depth-first elaboration
│   ├── ContentValidator
│   │   └── Regeneration trigger
│   └── ChapterCheckpoint
└── BookCompiler
    ├── CharacterDensityEstimator
    └── CompensatoryContentGenerator (se necessario)
```

## Implementazione

### Nuove Classi

1. **ProgressiveOutlineEnricher**: Gestisce le 3 fasi di arricchimento outline
2. **RecursiveSectionGenerator**: Genera contenuto in modo ricorsivo depth-first
3. **AdaptiveTokenBudget**: Calcola allocazione token per capitolo
4. **ContentValidator**: Valida e triggera rigenerazione
5. **ChapterCheckpoint**: Gestisce checkpoint a livello capitolo
6. **CharacterDensityEstimator**: Stima pagine con euristica avanzata

### Modifiche a Classi Esistenti

1. **OutlineAgent**: Integra ProgressiveOutlineEnricher
2. **ChapterWriterAgent**: Usa RecursiveSectionGenerator
3. **BookOrchestrator**: Aggiunge ContentValidator e CharacterDensityEstimator

## Configurazione

```python
@dataclass
class Config:
    # ... existing ...
    min_chapter_words: int = 6000  # Minimo parole per capitolo
    chapter_density_threshold: float = 0.8  # 80% del target
    enable_recursive_sections: bool = True
    enable_content_validation: bool = True
    enable_progressive_outline: bool = True
    compensatory_content_threshold: int = 245  # Pagine minime
```

## Flusso di Esecuzione

1. **Outline Phase**:
   - Genera outline base
   - Arricchisce con blueprint dettagliati
   - Calcola complexity score per capitolo

2. **Chapter Generation Phase** (per ogni capitolo):
   - Alloca token budget basato su complexity
   - Genera sezioni in modo ricorsivo depth-first
   - Valida word count
   - Se insufficiente: rigenera con prompt più enfatico
   - Salva checkpoint capitolo

3. **Validation Phase**:
   - Compila libro
   - Stima pagine con character-density heuristic
   - Se < 245 pagine: genera contenuto compensatorio
   - Se < 70% target: errore

## Note Implementative

- Usare qwen3.5-plus per libri lunghi (1M token context)
- Implementare retry exponential backoff per API
- Mantenere retrocompatibilità con provider esistenti
- Aggiungere logging dettagliato per ogni fase
