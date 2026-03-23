#!/usr/bin/env python3
"""
BookWriterAI – Generazione di libri con sub‑agent AI, supporta endpoint OpenAI compatibili.
Con sistema modulare di Knowledge Base Contestuale per documenti PDF, TXT e Markdown.

Autore: Emilio Petrozzi
Website: https://www.mrtux.it
"""

import os
import json
import time
import logging
import argparse
import re
import hashlib
import pickle
from typing import Dict, List, Optional, Any, Protocol, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from abc import ABC, abstractmethod
from collections import defaultdict
import heapq

# Try to import optional dependencies for document processing
try:
    from openai import OpenAI
    import tiktoken
    import requests
except ImportError:
    raise ImportError("Installa le dipendenze: pip install openai>=1.0.0 tiktoken requests python-dotenv")

# Optional dependencies for document parsing
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("PyPDF2 non installato. Supporto PDF disabilitato. Installa con: pip install PyPDF2")

try:
    import markdown
    MARKDOWN_SUPPORT = True
except ImportError:
    MARKDOWN_SUPPORT = False
    logging.warning("markdown non installato. Supporto Markdown HTML disabilitato. Installa con: pip install markdown")

from dotenv import load_dotenv

# ----------------------------------------------------------------------
# Configurazione e logging
# ----------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BookWriterAI")

@dataclass
class Config:
    topic: str = "Intelligenza artificiale e futuro del lavoro"
    output_file: str = "book_output.md"
    checkpoint_dir: str = "checkpoints"
    context_path: Optional[str] = None  # Percorso alla cartella dei documenti di riferimento
    provider: str = "openai"               # "openai", "qwen" o "bailian"
    model: str = "gpt-4"                   # modello da usare
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    endpoint: Optional[str] = None         # base_url personalizzato (solo per provider openai)
    temperature: float = 0.7
    max_tokens_per_call: int = 2000
    words_per_page: int = 400
    target_pages: int = 400
    num_chapters: int = 20
    words_per_chapter: int = 8000
    # Knowledge Base settings
    chunk_size: int = 1000                   # Dimensione chunk in token (approssimativi)
    chunk_overlap: int = 200                 # Sovrapposizione tra chunk
    max_context_chunks: int = 5              # Numero massimo di chunk da includere nel contesto
    use_semantic_retrieval: bool = True      # Usa retrieval semantico se disponibile
    # Multi-layered content expansion settings
    min_chapter_words: int = 6000            # Minimo parole per capitolo
    chapter_density_threshold: float = 0.8   # Soglia densità contenuto (80% del target)
    enable_recursive_sections: bool = True   # Abilita generazione ricorsiva sezioni
    enable_content_validation: bool = True   # Abilita validazione contenuto
    enable_progressive_outline: bool = True  # Abilita arricchimento progressivo outline
    compensatory_content_threshold: int = 245  # Pagine minime accettabili
    max_section_depth: int = 3               # Profondità massima sezioni annidate
    enable_adaptive_token_budget: bool = True  # Abilita budgeting token adattivo
    # Hard limits per prevenzione generazione eccessiva
    section_token_limit_multiplier: float = 1.3  # max_tokens = floor(target_words * multiplier)
    section_token_interrupt_threshold: float = 1.1  # 110% del target interrompe generazione
    section_timeout_seconds: int = 180  # 3 minuti timeout per sezione
    max_overgeneration_threshold: float = 1.2  # 120% del target, scarta e rigenera
    enable_section_checkpointing: bool = True  # Salva stato ogni sezione completata

    def __post_init__(self):
        if self.provider == "bailian" and not self.api_key:
            # Supporta sia BAILIAN_API_KEY che DASHSCOPE_API_KEY per retrocompatibilità
            self.api_key = os.getenv("BAILIAN_API_KEY", "") or os.getenv("DASHSCOPE_API_KEY", "")
        if self.provider == "qwen" and not self.api_key:
            self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if self.provider == "openai" and not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("API key non trovata. Imposta OPENAI_API_KEY, BAILIAN_API_KEY o DASHSCOPE_API_KEY nel .env")

# ----------------------------------------------------------------------
# Utilità per conteggio token (approssimato)
# ----------------------------------------------------------------------
def count_tokens(text: str, model: str = "gpt-4") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except:
        return len(text) // 4

# ==============================================================================
# KNOWLEDGE BASE SYSTEM - Sistema di Gestione Contestuale Modulare
# ==============================================================================

class DocumentParser(ABC):
    """Interfaccia astratta per i parser di documenti. Pattern: Strategy."""
    
    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse un documento e restituisce un dict con:
        - content: str - il contenuto testuale
        - metadata: Dict - metadati del documento
        - error: Optional[str] - errore se presente
        """
        pass
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Verifica se il parser supporta il file dato."""
        pass


class PDFParser(DocumentParser):
    """Parser per documenti PDF."""
    
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf' and PDF_SUPPORT
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        if not PDF_SUPPORT:
            return {
                "content": "",
                "metadata": {"source": str(file_path), "error": "PyPDF2 non installato"},
                "error": "PyPDF2 non installato. Installa con: pip install PyPDF2"
            }
        
        try:
            text_parts = []
            metadata = {"source": str(file_path), "pages": 0}
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                # Estrai metadati dal PDF se disponibili
                if pdf_reader.metadata:
                    pdf_meta = pdf_reader.metadata
                    metadata["title"] = pdf_meta.get('/Title', '')
                    metadata["author"] = pdf_meta.get('/Author', '')
                    metadata["subject"] = pdf_meta.get('/Subject', '')
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Errore estrazione pagina {page_num + 1} da {file_path}: {e}")
                        continue
            
            content = "\n".join(text_parts)
            
            if not content.strip():
                return {
                    "content": "",
                    "metadata": metadata,
                    "error": "Nessun testo estratto dal PDF (potrebbe essere scansionato o corrotto)"
                }
            
            return {
                "content": content,
                "metadata": metadata,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Errore parsing PDF {file_path}: {e}")
            return {
                "content": "",
                "metadata": {"source": str(file_path)},
                "error": f"Errore durante il parsing: {str(e)}"
            }


class TXTParser(DocumentParser):
    """Parser per file di testo semplice."""
    
    SUPPORTED_ENCODINGS = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252', 'ascii']
    
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.txt', '.text']
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        metadata = {"source": str(file_path)}
        
        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                metadata["encoding"] = encoding
                return {
                    "content": content,
                    "metadata": metadata,
                    "error": None
                }
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Errore lettura file {file_path} con encoding {encoding}: {e}")
                return {
                    "content": "",
                    "metadata": metadata,
                    "error": f"Errore lettura file: {str(e)}"
                }
        
        return {
            "content": "",
            "metadata": metadata,
            "error": f"Impossibile decodificare il file con nessuno degli encoding supportati: {self.SUPPORTED_ENCODINGS}"
        }


class MarkdownParser(DocumentParser):
    """Parser per file Markdown."""
    
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.md', '.markdown', '.mdown']
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        metadata = {"source": str(file_path)}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Estrai metadati YAML frontmatter se presente
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    content = parts[2].strip()
                    # Parse semplice del frontmatter
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip().strip('"\'')
            
            # Estrai titoli per struttura
            headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
            if headers:
                metadata["headers"] = headers
                metadata["title"] = headers[0] if headers else ""
            
            return {
                "content": content,
                "metadata": metadata,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Errore parsing Markdown {file_path}: {e}")
            return {
                "content": "",
                "metadata": metadata,
                "error": f"Errore durante il parsing: {str(e)}"
            }


@dataclass
class TextChunk:
    """Rappresenta un chunk di testo con metadati."""
    content: str
    source: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    
    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = count_tokens(self.content)


class TextChunker:
    """
    Sistema di chunking intelligente che rispetta i limiti di contesto.
    Implementa sliding window con sovrapposizione.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_document(self, content: str, source: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        Divide un documento in chunk intelligenti.
        Cerca di mantenere la coerenza spezzando ai confini di paragrafo quando possibile.
        """
        chunks = []
        
        # Dividi in paragrafi mantenendo la struttura
        paragraphs = self._split_into_paragraphs(content)
        
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = count_tokens(paragraph)
            
            # Se il paragrafo singolo supera la dimensione del chunk, dividilo
            if paragraph_tokens > self.chunk_size:
                # Salva il chunk corrente se presente
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, source, chunk_index, metadata))
                    chunk_index += 1
                    current_chunk = []
                    current_size = 0
                
                # Dividi il paragrafo lungo
                sub_chunks = self._chunk_large_paragraph(paragraph)
                for sub_chunk in sub_chunks:
                    chunks.append(self._create_chunk(sub_chunk, source, chunk_index, metadata))
                    chunk_index += 1
            
            # Se aggiungere il paragrafo supera la dimensione, salva e inizia nuovo chunk
            elif current_size + paragraph_tokens > self.chunk_size:
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, source, chunk_index, metadata))
                    chunk_index += 1
                
                # Inizia nuovo chunk con sovrapposizione
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = [overlap_text, paragraph] if overlap_text else [paragraph]
                current_size = count_tokens("\n\n".join(current_chunk))
            
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_tokens
        
        # Salva l'ultimo chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(self._create_chunk(chunk_text, source, chunk_index, metadata))
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Divide il testo in paragrafi mantenendo la struttura."""
        # Normalizza le linee vuote multiple
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Dividi ai doppi a capo
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs
    
    def _chunk_large_paragraph(self, paragraph: str) -> List[str]:
        """Divide un paragrafo lungo in chunk più piccoli."""
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_tokens = count_tokens(sentence)
            
            if current_size + sentence_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_size += sentence_tokens
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _get_overlap_text(self, previous_chunk: List[str]) -> str:
        """Estrae il testo di sovrapposizione dal chunk precedente."""
        if not previous_chunk or self.chunk_overlap <= 0:
            return ""
        
        overlap_parts = []
        overlap_size = 0
        
        # Prendi i paragrafi dalla fine fino a raggiungere la dimensione di sovrapposizione
        for paragraph in reversed(previous_chunk):
            para_tokens = count_tokens(paragraph)
            if overlap_size + para_tokens <= self.chunk_overlap:
                overlap_parts.insert(0, paragraph)
                overlap_size += para_tokens
            else:
                break
        
        return "\n\n".join(overlap_parts)
    
    def _create_chunk(self, content: str, source: str, index: int, metadata: Dict[str, Any]) -> TextChunk:
        """Crea un oggetto TextChunk."""
        chunk_id = hashlib.md5(f"{source}:{index}:{content[:100]}".encode()).hexdigest()[:12]
        return TextChunk(
            content=content,
            source=source,
            chunk_id=chunk_id,
            metadata={**metadata, "chunk_index": index}
        )


class ContextRetriever:
    """
    Sistema di retrieval per selezionare i chunk più rilevanti.
    Implementa retrieval per keyword e TF-IDF semplificato.
    """
    
    def __init__(self, chunks: List[TextChunk]):
        self.chunks = chunks
        self.keyword_index = self._build_keyword_index()
    
    def _build_keyword_index(self) -> Dict[str, List[Tuple[str, float]]]:
        """Costruisce un indice inverso di keyword."""
        index = defaultdict(list)
        
        for chunk in self.chunks:
            # Estrai keyword significative (parole con più di 3 caratteri)
            words = re.findall(r'\b[a-zA-Zàèéìòù]{4,}\b', chunk.content.lower())
            word_freq = defaultdict(int)
            
            for word in words:
                word_freq[word] += 1
            
            # Calcola TF semplificato
            total_words = len(words)
            if total_words > 0:
                for word, freq in word_freq.items():
                    tf = freq / total_words
                    index[word].append((chunk.chunk_id, tf))
        
        return index
    
    def retrieve(self, query: str, top_k: int = 5) -> List[TextChunk]:
        """
        Recupera i chunk più rilevanti per la query.
        Usa un approccio ibrido: keyword matching + scoring di rilevanza.
        """
        query_lower = query.lower()
        
        # Estrai keyword dalla query
        query_words = set(re.findall(r'\b[a-zA-Zàèéìòù]{4,}\b', query_lower))
        
        # Calcola score per ogni chunk
        chunk_scores = defaultdict(float)
        
        for word in query_words:
            if word in self.keyword_index:
                for chunk_id, tf in self.keyword_index[word]:
                    # IDF semplificato: log(N / df)
                    idf = 1.0  # Semplificato
                    chunk_scores[chunk_id] += tf * idf
        
        # Bonus per match esatti della query nel contenuto
        for chunk in self.chunks:
            if query_lower in chunk.content.lower():
                chunk_scores[chunk.chunk_id] += 2.0
            
            # Bonus per match nel titolo/fonte
            if query_lower in chunk.source.lower():
                chunk_scores[chunk.chunk_id] += 1.5
        
        # Ordina per score e prendi i top_k
        top_chunk_ids = heapq.nlargest(top_k, chunk_scores.keys(), key=lambda x: chunk_scores[x])
        
        # Crea mappa chunk_id -> chunk
        chunk_map = {c.chunk_id: c for c in self.chunks}
        
        result = []
        for chunk_id in top_chunk_ids:
            if chunk_id in chunk_map:
                chunk = chunk_map[chunk_id]
                # Aggiungi score ai metadati
                chunk.metadata["relevance_score"] = chunk_scores[chunk_id]
                result.append(chunk)
        
        return result
    
    def retrieve_by_chapter_context(self, chapter_title: str, chapter_description: str, 
                                     top_k: int = 5) -> List[TextChunk]:
        """
        Recupera chunk rilevanti per un capitolo specifico.
        Combina titolo e descrizione del capitolo.
        """
        combined_query = f"{chapter_title} {chapter_description}"
        return self.retrieve(combined_query, top_k)


class KnowledgeBase:
    """
    Facade che coordina il sistema di Knowledge Base.
    Gestisce il caricamento, parsing, chunking e retrieval dei documenti.
    """
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.text', '.md', '.markdown', '.mdown'}
    
    def __init__(self, config: Config):
        self.config = config
        self.context_path = config.context_path
        self.parsers: List[DocumentParser] = [
            PDFParser(),
            TXTParser(),
            MarkdownParser()
        ]
        self.chunker = TextChunker(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        self.chunks: List[TextChunk] = []
        self.retriever: Optional[ContextRetriever] = None
        self._index_cache_path: Optional[Path] = None
        self._loaded = False
        self._errors: List[str] = []
    
    def initialize(self) -> bool:
        """
        Inizializza la knowledge base caricando e indicizzando i documenti.
        Restituisce True se l'inizializzazione ha successo.
        """
        if not self.context_path:
            logger.info("Nessun percorso contestuale specificato. Knowledge base disabilitata.")
            return False
        
        context_dir = Path(self.context_path)
        if not context_dir.exists():
            logger.warning(f"Percorso contestuale non trovato: {self.context_path}")
            return False
        
        if not context_dir.is_dir():
            logger.warning(f"Il percorso contestuale non è una directory: {self.context_path}")
            return False
        
        # Setup cache path
        cache_dir = Path(self.config.checkpoint_dir) / "kb_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_cache_path = cache_dir / "index.pkl"
        
        # Prova a caricare da cache
        if self._load_from_cache():
            logger.info(f"Knowledge base caricata da cache: {len(self.chunks)} chunk")
            self._loaded = True
            return True
        
        # Carica e processa i documenti
        logger.info(f"Caricamento documenti da: {self.context_path}")
        documents = self._load_documents(context_dir)
        
        if not documents:
            logger.warning("Nessun documento valido trovato nel percorso contestuale")
            return False
        
        # Chunking
        logger.info("Indicizzazione documenti...")
        for doc in documents:
            doc_chunks = self.chunker.chunk_document(
                content=doc["content"],
                source=doc["source"],
                metadata=doc["metadata"]
            )
            self.chunks.extend(doc_chunks)
        
        logger.info(f"Creati {len(self.chunks)} chunk da {len(documents)} documenti")
        
        # Inizializza retriever
        self.retriever = ContextRetriever(self.chunks)
        
        # Salva cache
        self._save_to_cache()
        
        self._loaded = True
        return True
    
    def _load_documents(self, directory: Path) -> List[Dict[str, Any]]:
        """Carica tutti i documenti supportati dalla directory."""
        documents = []
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                doc = self._parse_file(file_path)
                if doc and not doc.get("error"):
                    # Assicurati che il campo 'source' esista
                    if "source" not in doc:
                        doc["source"] = str(file_path)
                    documents.append(doc)
                elif doc and doc.get("error"):
                    self._errors.append(f"{file_path}: {doc['error']}")
                # Se doc è None, nessun parser ha supportato il file (non dovrebbe succedere con SUPPORTED_EXTENSIONS)
        
        if self._errors:
            logger.warning(f"Errori durante il caricamento di {len(self._errors)} file:")
            for error in self._errors[:5]:  # Mostra solo i primi 5 errori
                logger.warning(f"  - {error}")
        
        return documents
    
    def _parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse un singolo file usando il parser appropriato."""
        for parser in self.parsers:
            if parser.supports(file_path):
                try:
                    result = parser.parse(file_path)
                    logger.debug(f"Parsato {file_path}: {len(result.get('content', ''))} caratteri")
                    return result
                except Exception as e:
                    logger.error(f"Errore imprevisto parsing {file_path}: {e}")
                    return {
                        "content": "",
                        "metadata": {"source": str(file_path)},
                        "error": f"Errore imprevisto: {str(e)}"
                    }
        
        return None
    
    def _load_from_cache(self) -> bool:
        """Carica l'indice dalla cache se valida."""
        if not self._index_cache_path or not self._index_cache_path.exists():
            return False
        
        try:
            with open(self._index_cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verifica che la cache sia valida (stessi parametri)
            if (cache_data.get('chunk_size') == self.config.chunk_size and
                cache_data.get('chunk_overlap') == self.config.chunk_overlap and
                cache_data.get('context_path') == self.context_path):
                
                self.chunks = cache_data['chunks']
                self.retriever = ContextRetriever(self.chunks)
                return True
            
        except Exception as e:
            logger.warning(f"Errore caricamento cache: {e}")
        
        return False
    
    def _save_to_cache(self):
        """Salva l'indice in cache."""
        if not self._index_cache_path:
            return
        
        try:
            cache_data = {
                'chunk_size': self.config.chunk_size,
                'chunk_overlap': self.config.chunk_overlap,
                'context_path': self.context_path,
                'chunks': self.chunks
            }
            with open(self._index_cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.info(f"Cache knowledge base salvata in: {self._index_cache_path}")
        except Exception as e:
            logger.warning(f"Errore salvataggio cache: {e}")
    
    def get_relevant_context(self, query: str, top_k: Optional[int] = None) -> str:
        """
        Recupera il contesto rilevante come stringa formattata.
        """
        if not self._loaded or not self.retriever:
            return ""
        
        k = top_k or self.config.max_context_chunks
        chunks = self.retriever.retrieve(query, k)
        
        if not chunks:
            return ""
        
        context_parts = ["\n=== CONTESTO DI RIFERIMENTO ===\n"]
        
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get('title', chunk.source)
            context_parts.append(f"\n[Documento {i}: {source}]\n{chunk.content}\n")
        
        context_parts.append("=== FINE CONTESTO ===\n")
        
        return "\n".join(context_parts)
    
    def get_context_for_chapter(self, chapter_info: Dict[str, Any]) -> str:
        """
        Recupera il contesto rilevante per un capitolo specifico.
        """
        title = chapter_info.get('title', '')
        description = chapter_info.get('description', '')
        
        query = f"{title} {description}"
        return self.get_relevant_context(query)
    
    def is_loaded(self) -> bool:
        """Verifica se la knowledge base è stata caricata."""
        return self._loaded
    
    def get_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche sulla knowledge base."""
        if not self._loaded:
            return {"status": "not_loaded"}
        
        total_tokens = sum(c.token_count for c in self.chunks)
        sources = set(c.source for c in self.chunks)
        
        return {
            "status": "loaded",
            "total_chunks": len(self.chunks),
            "total_tokens": total_tokens,
            "unique_sources": len(sources),
            "sources": list(sources)[:10]  # Primi 10 sorgenti
        }


# ----------------------------------------------------------------------
# Classe base per i sub‑agent (supporta endpoint personalizzato)
# ----------------------------------------------------------------------
class BaseAgent:
    def __init__(self, config: Config, name: str, knowledge_base: Optional[KnowledgeBase] = None):
        self.config = config
        self.name = name
        self.knowledge_base = knowledge_base
        self._setup_client()

    def _setup_client(self):
        if self.config.provider == "openai":
            # Crea client OpenAI con base_url personalizzato se fornito
            client_kwargs = {
                "api_key": self.config.api_key,
            }
            if self.config.endpoint:
                client_kwargs["base_url"] = self.config.endpoint
            self.client = OpenAI(**client_kwargs)
        elif self.config.provider == "bailian":
            # Bailian (OpenClaw/Coding Plan) usa endpoint OpenAI-compatible
            # Endpoint: https://coding-intl.dashscope.aliyuncs.com/v1
            self.client = OpenAI(
                api_key=self.config.api_key,
                base_url="https://coding-intl.dashscope.aliyuncs.com/v1"
            )
        elif self.config.provider == "qwen":
            # Qwen usa l'API DashScope nativa (legacy)
            self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            self.headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Provider non supportato: {self.config.provider}")

    def call_ai(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        max_tokens = max_tokens or self.config.max_tokens_per_call
        retries = 3
        for attempt in range(retries):
            try:
                if self.config.provider in ["openai", "bailian"]:
                    # Entrambi usano client OpenAI (bailian è OpenAI-compatible)
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})
                    response = self.client.chat.completions.create(
                        model=self.config.model,
                        messages=messages,
                        temperature=self.config.temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content.strip()
                elif self.config.provider == "qwen":
                    payload = {
                        "model": self.config.model,
                        "input": {
                            "messages": [
                                {"role": "system", "content": system_prompt or "Sei un assistente utile."},
                                {"role": "user", "content": prompt}
                            ]
                        },
                        "parameters": {
                            "temperature": self.config.temperature,
                            "max_tokens": max_tokens
                        }
                    }
                    resp = requests.post(self.base_url, headers=self.headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    return data["output"]["text"].strip()
            except Exception as e:
                logger.warning(f"Tentativo {attempt+1} fallito per {self.name}: {e}")
                time.sleep(2 ** attempt)
        raise RuntimeError(f"Impossibile completare la chiamata AI per {self.name} dopo {retries} tentativi")

    def get_context_for_query(self, query: str) -> str:
        """Recupera contesto dalla knowledge base se disponibile."""
        if self.knowledge_base and self.knowledge_base.is_loaded():
            return self.knowledge_base.get_relevant_context(query)
        return ""

# =============================================================================
# MULTI-LAYERED CONTENT EXPANSION SYSTEM
# Sistema avanzato per generazione libri lunghi (300+ pagine)
# =============================================================================

class CharacterDensityEstimator:
    """
    Stima il numero di pagine basandosi su euristica di densità caratteri.
    Considera overhead formattazione markdown e genera proiezioni accurate.
    """
    
    # Standard editoriale: ~3000 caratteri per pagina A4
    CHARS_PER_PAGE = 3000
    # Overhead markdown (headers, formattazione): ~15%
    MARKDOWN_OVERHEAD = 0.15
    
    @classmethod
    def estimate_pages(cls, text: str) -> int:
        """Stima pagine basata su caratteri, considerando overhead formattazione."""
        # Rimuovi overhead markdown per stima contenuto effettivo
        clean_text = re.sub(r'[#*_\[\]()|`\-]', '', text)
        clean_text = re.sub(r'\n+', ' ', clean_text)
        
        effective_chars = len(clean_text) * (1 - cls.MARKDOWN_OVERHEAD)
        return max(1, int(effective_chars / cls.CHARS_PER_PAGE))
    
    @classmethod
    def estimate_from_chapters(cls, chapters: List[Dict[str, str]]) -> Dict[str, Any]:
        """Stima pagine da lista capitoli con statistiche dettagliate."""
        total_chars = sum(len(ch['content']) for ch in chapters)
        total_words = sum(len(ch['content'].split()) for ch in chapters)
        estimated_pages = cls.estimate_pages(''.join(ch['content'] for ch in chapters))
        
        return {
            "total_chars": total_chars,
            "total_words": total_words,
            "estimated_pages": estimated_pages,
            "chars_per_chapter_avg": total_chars // len(chapters) if chapters else 0,
            "words_per_chapter_avg": total_words // len(chapters) if chapters else 0
        }


class AdaptiveTokenBudget:
    """
    Allocazione adattiva del budget token basata su complessità capitolo.
    Prioritizza modelli con 1M+ token context window.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.model_context_windows = {
            "qwen3.5-plus": 1_000_000,
            "qwen3-coder-plus": 1_000_000,
            "qwen3-max-2026-01-23": 262_144,
            "qwen3-coder-next": 262_144,
            "kimi-k2.5": 262_144,
            "MiniMax-M2.5": 196_608,
            "glm-5": 202_752,
            "glm-4.7": 202_752,
            "gpt-4": 8_192,
            "gpt-4-turbo": 128_000,
            "gpt-3.5-turbo": 16_384,
        }
    
    def get_available_context(self) -> int:
        """Restituisce la context window disponibile per il modello corrente."""
        return self.model_context_windows.get(self.config.model, 8_192)
    
    def calculate_complexity_score(self, chapter_info: Dict) -> float:
        """
        Calcola punteggio complessità capitolo (0.5 - 2.0).
        Basato su: numero sottosezioni, topic density, richieste esempi.
        """
        score = 1.0  # Base
        
        # Fattore numero sottosezioni
        subsections = chapter_info.get('subsections', [])
        if len(subsections) >= 5:
            score += 0.3
        elif len(subsections) <= 2:
            score -= 0.2
        
        # Fattore target words
        target_words = chapter_info.get('target_words', 8000)
        if target_words >= 10000:
            score += 0.3
        elif target_words <= 5000:
            score -= 0.2
        
        # Fattore descrizione (keyword che indicano complessità)
        description = chapter_info.get('description', '').lower()
        complexity_keywords = ['analisi', 'tecnico', 'dettagliato', 'approfondito',
                              'caso studio', 'esempio', 'implementazione', 'architettura']
        keyword_count = sum(1 for kw in complexity_keywords if kw in description)
        score += keyword_count * 0.1
        
        return max(0.5, min(2.0, score))
    
    def allocate_tokens(self, chapter_info: Dict, outline_context: str = "") -> int:
        """Alloca token per capitolo basato su complessità e contesto disponibile."""
        available_context = self.get_available_context()
        complexity = self.calculate_complexity_score(chapter_info)
        
        # Riserva token per outline e contesto
        reserved_tokens = len(outline_context) // 4 if outline_context else 1000
        reserved_tokens = min(reserved_tokens, available_context // 4)
        
        # Token disponibili per generazione
        available_for_generation = available_context - reserved_tokens - 1000  # Margine sicurezza
        
        # Allocazione basata su complessità
        allocated = int(available_for_generation * complexity / 2.0)
        
        # Limiti min/max pratici
        return max(2000, min(allocated, 8000))


class ContentValidator:
    """
    Validazione contenuto con trigger rigenerazione.
    Verifica word count minimo e densità contenuto.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.validation_attempts = 0
        self.max_attempts = 3
    
    def validate_chapter(self, chapter_content: str, chapter_info: Dict) -> Dict[str, Any]:
        """
        Valida capitolo generato.
        Restituisce dict con: valid (bool), word_count, density_ratio, needs_regeneration
        """
        word_count = len(chapter_content.split())
        target_words = chapter_info.get('target_words', self.config.words_per_chapter)
        min_words = self.config.min_chapter_words
        
        # Calcola densità rispetto al target
        density_ratio = word_count / target_words if target_words > 0 else 0
        
        # Criteri validazione
        is_valid = word_count >= min_words
        needs_regeneration = density_ratio < self.config.chapter_density_threshold
        
        result = {
            "valid": is_valid and not needs_regeneration,
            "word_count": word_count,
            "target_words": target_words,
            "density_ratio": density_ratio,
            "needs_regeneration": needs_regeneration,
            "reason": None
        }
        
        if not is_valid:
            result["reason"] = f"Word count insufficiente: {word_count} < {min_words}"
        elif needs_regeneration:
            result["reason"] = f"Densità contenuto bassa: {density_ratio:.1%} < {self.config.chapter_density_threshold:.1%}"
        
        return result
    
    def should_regenerate(self, validation_result: Dict) -> bool:
        """Determina se rigenerare basato su risultato validazione e tentativi."""
        if validation_result["valid"]:
            return False
        
        self.validation_attempts += 1
        if self.validation_attempts > self.max_attempts:
            logger.warning(f"Max tentativi raggiunti ({self.max_attempts}), accetto capitolo non ottimale")
            return False
        
        logger.warning(f"Validazione fallita: {validation_result['reason']}. "
                      f"Tentativo {self.validation_attempts}/{self.max_attempts}")
        return True
    
    def get_enhanced_prompt(self, original_prompt: str, validation_result: Dict) -> str:
        """Genera prompt più enfatico per rigenerazione."""
        enhancement = f"""

⚠️ ATTENZIONE: Il capitolo precedente era insufficiente ({validation_result['word_count']} parole).
REQUISITI CRITICI:
- Devi generare ALMENO {validation_result['target_words']} parole
- Sii estremamente dettagliato e approfondito
- Aggiungi esempi pratici, casi studio, spiegazioni approfondite
- Non riassumere, espandi ogni concetto al massimo
"""
        return original_prompt + enhancement


class RecursiveSectionGenerator:
    """
    Generatore ricorsivo di sezioni con elaborazione depth-first.
    Supporta: sottosezioni annidate, case studies, examples, technical deep-dives.
    
    Include:
    - Hard token limits per sezione
    - Real-time token counter con 110% interrupt
    - Timeout 3 minuti per sezione con fallback troncato
    - Section-level checkpointing
    """
    
    def __init__(self, agent: BaseAgent, config: Config, chapter_target_words: int = 0):
        self.agent = agent
        self.config = config
        self.token_budget = AdaptiveTokenBudget(config)
        self.chapter_target_words = chapter_target_words
        self.total_tokens_generated = 0
        self.section_checkpoints: Dict[str, str] = {}
    
    def _calculate_section_token_limit(self, section_title: str, num_sections: int) -> int:
        """
        Calcola hard limit token per sezione: max_tokens = floor(target_words * 1.3 / num_sections)
        """
        if self.chapter_target_words > 0:
            target_per_section = self.chapter_target_words // num_sections
            return int(target_per_section * self.config.section_token_limit_multiplier)
        # Fallback: usa default
        return int(self.config.words_per_chapter * self.config.section_token_limit_multiplier // num_sections)
    
    def _check_token_interrupt(self, current_tokens: int, target_tokens: int) -> bool:
        """
        Controlla se raggiungere 110% del target e interrompe generazione.
        """
        threshold = int(target_tokens * self.config.section_token_interrupt_threshold)
        return current_tokens >= threshold
    
    def _generate_with_timeout(self, prompt: str, system_prompt: str, max_tokens: int,
                                section_id: str) -> str:
        """
        Genera contenuto con timeout di 3 minuti. Se scade, restituisce contenuto troncato.
        """
        import signal
        
        class TimeoutError(Exception):
            pass
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Timeout {self.config.section_timeout_seconds}s per sezione '{section_id}'")
        
        # Imposta timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.config.section_timeout_seconds)
        
        try:
            result = self.agent.call_ai(prompt, system_prompt=system_prompt, max_tokens=max_tokens)
            signal.alarm(0)  # Cancella timeout
            return result
        except TimeoutError as e:
            logger.warning(str(e))
            # Fallback: contenuto troncato
            return f"[Contenuto troncato per timeout - sezione '{section_id}']"
        finally:
            signal.signal(signal.SIGALRM, old_handler)
    
    def generate_section(self, section_title: str, section_description: str,
                        depth: int = 0, parent_context: str = "",
                        num_sections: int = 1) -> str:
        """
        Genera una sezione in modo ricorsivo depth-first con hard token limits.
        
        Args:
            section_title: Titolo della sezione
            section_description: Descrizione/dettagli della sezione
            depth: Profondità corrente (0 = sezione principale)
            parent_context: Contesto dal genitore per coerenza
            num_sections: Numero totale di sezioni per calcolo token limit
        
        Returns:
            Contenuto generato della sezione
        """
        section_id = f"{'  ' * depth}{section_title}"
        
        # Calcola token limit per questa sezione
        section_token_limit = self._calculate_section_token_limit(section_title, num_sections)
        interrupt_threshold = int(section_token_limit * self.config.section_token_interrupt_threshold)
        
        # Checkpoint: verifica se sezione già generata
        if self.config.enable_section_checkpointing and section_id in self.section_checkpoints:
            logger.info(f"Sezione '{section_id}' caricata da checkpoint")
            return self.section_checkpoints[section_id]
        
        if depth > self.config.max_section_depth:
            # Profondità massima raggiunta, genera contenuto foglia
            content = self._generate_leaf_content_with_limits(
                section_title, section_description, parent_context, section_token_limit, section_id
            )
        else:
            # Genera contenuto principale della sezione con timeout
            main_content = self._generate_section_content_with_limits(
                section_title, section_description, depth, parent_context,
                section_token_limit, section_id
            )
            
            # Aggiorna token counter
            self.total_tokens_generated += count_tokens(main_content)
            
            # Check interrupt 110%
            if self._check_token_interrupt(self.total_tokens_generated, interrupt_threshold):
                logger.warning(f"INTERRUPT: Raggiunto 110% token limit per sezione '{section_id}'")
                return main_content[:int(len(main_content) * 0.9)]  # Tronca al 90%
            
            # Se abbiamo abbastanza profondità, genera sottosezioni
            if depth < self.config.max_section_depth - 1:
                subsections = self._plan_subsections(section_title, section_description)
                num_subsections = len(subsections) if subsections else 2
                
                for i, sub in enumerate(subsections or [{'title': f'{section_title}.1', 'description': ''},
                                                         {'title': f'{section_title}.2', 'description': ''}]):
                    # Calcola token limit per sottosezione
                    sub_token_limit = section_token_limit // num_subsections
                    
                    sub_content = self.generate_section(
                        sub['title'],
                        sub['description'],
                        depth + 1,
                        parent_context + "\n" + main_content[:500],
                        num_subsections
                    )
                    
                    # Check interrupt dopo ogni sottosezione
                    self.total_tokens_generated += count_tokens(sub_content)
                    if self._check_token_interrupt(self.total_tokens_generated, interrupt_threshold):
                        logger.warning(f"INTERRUPT: Raggiunto 110% token limit in sottosezione '{sub['title']}'")
                        break
                    
                    main_content += f"\n\n### {sub['title']}\n\n{sub_content}"
            
            content = main_content
        
        # Salva checkpoint
        if self.config.enable_section_checkpointing:
            self.section_checkpoints[section_id] = content
        
        return content
    
    def _generate_section_content_with_limits(self, title: str, description: str,
                                              depth: int, context: str,
                                              token_limit: int, section_id: str) -> str:
        """Genera contenuto per una sezione specifica con hard token limit e timeout."""
        indent = "  " * depth
        
        # Calcola max_tokens per la chiamata API
        max_tokens = min(
            int(token_limit * 0.8),  # 80% del token limit per margine sicurezza
            self.config.max_tokens_per_call
        )
        
        prompt = f"""
{indent}Scrivi la sezione "{title}" in modo CONCISO e MIRATO.

{indent}Descrizione: {description}

{indent}Contesto: {context[:500] if context else 'Nessuno'}

{indent}VINCOLI RIGIDI:
{indent}- Scrivi ESATTAMENTE 2-3 paragrafi (non di più)
{indent}- Massimo {int(token_limit // 4)} parole (~{token_limit} token)
{indent}- Sii diretto, evita ripetizioni
{indent}- Usa formattazione markdown leggera
"""
        system = "Sei uno scrittore tecnico CONCISO. Rispetta rigorosamente i limiti di lunghezza."
        
        # Genera con timeout
        content = self._generate_with_timeout(prompt, system, max_tokens, section_id)
        
        # Post-generation validation: scarta se >120% target
        content_tokens = count_tokens(content)
        if content_tokens > int(token_limit * self.config.max_overgeneration_threshold):
            logger.warning(f"OVERGENERATION: Sezione '{section_id}' ha {content_tokens} token (limite: {token_limit}). Troncamento...")
            # Tronca al token limit
            words = content.split()
            max_words = int(token_limit * 0.75)  # 1 token ≈ 1.33 parole
            content = ' '.join(words[:max_words]) + " [...]"
        
        return content
    
    def _generate_leaf_content_with_limits(self, title: str, description: str,
                                           context: str, token_limit: int,
                                           section_id: str) -> str:
        """Genera contenuto foglia con hard token limit e timeout."""
        max_tokens = min(
            int(token_limit * 0.8),
            self.config.max_tokens_per_call
        )
        
        prompt = f"""
Scrivi contenuto CONCISO per "{title}".

Descrizione: {description}
Contesto: {context[:300] if context else 'Nessuno'}

VINCOLI RIGIDI:
- Massimo {int(token_limit // 4)} parole (~{token_limit} token)
- 1-2 paragrafi brevi
- Niente ripetizioni
"""
        content = self._generate_with_timeout(prompt, "Scrivi contenuto TECNICO e CONCISO.",
                                               max_tokens, section_id)
        
        # Post-generation validation
        content_tokens = count_tokens(content)
        if content_tokens > int(token_limit * self.config.max_overgeneration_threshold):
            logger.warning(f"OVERGENERATION foglia: '{section_id}' ha {content_tokens} token. Troncamento...")
            words = content.split()
            max_words = int(token_limit * 0.75)
            content = ' '.join(words[:max_words]) + " [...]"
        
        return content
    
    def _generate_leaf_content(self, title: str, description: str, context: str) -> str:
        """Genera contenuto foglia (senza ulteriori sottosezioni)."""
        # Metodo legacy mantenuto per retrocompatibilità
        return self._generate_leaf_content_with_limits(title, description, context,
                                                        int(self.config.words_per_chapter * 0.1),
                                                        title)
    
    def _generate_section_content(self, title: str, description: str,
                                   depth: int, context: str) -> str:
        """Genera contenuto per una sezione specifica."""
        indent = "  " * depth
        prompt = f"""
{indent}Scrivi la sezione "{title}" in modo approfondito e dettagliato.

{indent}Descrizione: {description}

{indent}Contesto: {context[:1000] if context else 'Nessuno'}

{indent}REQUISITI:
{indent}- Scrivi almeno 3-4 paragrafi dettagliati
{indent}- Includi esempi pratici e spiegazioni approfondite
{indent}- Usa formattazione markdown (titoli, elenchi, enfasi)
{indent}- Sii completo, non riassumere
"""
        system = "Sei uno scrittore tecnico esperto. Scrivi contenuto denso, dettagliato e professionale."
        return self.agent.call_ai(prompt, system_prompt=system, max_tokens=2000)
    
    def _generate_leaf_content(self, title: str, description: str, context: str) -> str:
        """Genera contenuto foglia (senza ulteriori sottosezioni)."""
        prompt = f"""
Scrivi contenuto dettagliato per "{title}".

Descrizione: {description}
Contesto: {context[:500] if context else 'Nessuno'}

REQUISITI:
- Contenuto denso e approfondito
- Almeno 2-3 paragrafi sostanziali
- Esempi concreti dove applicabile
"""
        return self.agent.call_ai(prompt, system_prompt="Scrivi contenuto tecnico dettagliato.",
                                  max_tokens=1500)
    
    def _plan_subsections(self, parent_title: str, parent_description: str) -> List[Dict]:
        """Pianifica sottosezioni per una sezione data."""
        prompt = f"""
Per la sezione "{parent_title}" (desc: {parent_description}),
genera 2-3 sottosezioni pertinenti.

Rispondi con JSON:
[
  {{"title": "Titolo sottosezione", "description": "Breve descrizione"}},
  ...
]
"""
        try:
            response = self.agent.call_ai(prompt, max_tokens=1000)
            # Estrai JSON
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning(f"Errore pianificazione sottosezioni: {e}")
        
        return []  # Fallback: nessuna sottosezione


class ProgressiveOutlineEnricher:
    """
    Arricchimento progressivo dell'outline in 3 fasi:
    1. Outline base (titoli + descrizioni)
    2. Espansione in blueprint dettagliati
    3. Finalizzazione con metadati
    """
    
    def __init__(self, agent: BaseAgent, config: Config):
        self.agent = agent
        self.config = config
    
    def enrich(self, basic_outline: Dict) -> Dict:
        """
        Arricchisce l'outline attraverso fasi progressive.
        """
        logger.info("Fase 1: Outline base completato")
        
        # Fase 2: Espansione blueprint
        enriched_chapters = []
        for i, chapter in enumerate(basic_outline.get('chapters', []), 1):
            logger.info(f"Fase 2: Arricchimento capitolo {i}/{len(basic_outline['chapters'])}")
            enriched_chapter = self._enrich_chapter_blueprint(chapter)
            enriched_chapters.append(enriched_chapter)
        
        enriched_outline = {
            "title": basic_outline.get('title', 'Libro'),
            "chapters": enriched_chapters
        }
        
        logger.info("Fase 3: Finalizzazione outline")
        return self._finalize_outline(enriched_outline)
    
    def _enrich_chapter_blueprint(self, chapter: Dict) -> Dict:
        """Arricchisce un singolo capitolo con blueprint dettagliato."""
        prompt = f"""
Per il capitolo "{chapter['title']}", crea un blueprint dettagliato.

Descrizione originale: {chapter.get('description', '')}
Target words: {chapter.get('target_words', 8000)}

Genera:
1. Sezioni principali (almeno 4-5)
2. Per ogni sezione: 2-3 sottosezioni specifiche
3. Key points da coprire

Rispondi con JSON:
{{
  "sections": [
    {{
      "title": "Titolo sezione",
      "subsections": ["Sottosezione 1", "Sottosezione 2"],
      "key_points": ["Punto chiave 1", "Punto chiave 2"]
    }}
  ]
}}
"""
        try:
            response = self.agent.call_ai(prompt, max_tokens=2000)
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                blueprint = json.loads(match.group())
                chapter['blueprint'] = blueprint
                # Aggiorna sottosezioni con quelle dettagliate
                all_subsections = []
                for sec in blueprint.get('sections', []):
                    all_subsections.extend(sec.get('subsections', []))
                if all_subsections:
                    chapter['subsections'] = all_subsections
        except Exception as e:
            logger.warning(f"Errore arricchimento capitolo: {e}")
        
        return chapter
    
    def _finalize_outline(self, outline: Dict) -> Dict:
        """Finalizza l'outline con metadati e validazione."""
        total_target_words = sum(
            ch.get('target_words', self.config.words_per_chapter)
            for ch in outline['chapters']
        )
        outline['metadata'] = {
            'total_chapters': len(outline['chapters']),
            'total_target_words': total_target_words,
            'estimated_pages': total_target_words // self.config.words_per_page,
            'enriched': True
        }
        return outline


# ----------------------------------------------------------------------
# Sub‑agent specializzati
# ----------------------------------------------------------------------

class OutlineAgent(BaseAgent):
    """Genera la struttura del libro."""
    def generate(self) -> Dict:
        # Recupera contesto rilevante per l'outline
        context = ""
        if self.knowledge_base and self.knowledge_base.is_loaded():
            context = self.knowledge_base.get_relevant_context(self.config.topic)
            logger.info("Contesto aggiunto alla generazione dell'outline")
        
        # Calcola il numero esatto di capitoli necessari
        total_words = self.config.target_pages * self.config.words_per_page
        num_chapters = max(15, min(30, round(total_words / self.config.words_per_chapter)))
        words_per_chapter = total_words // num_chapters
        
        prompt = f"""
Crea una struttura dettagliata per un libro di ESATTAMENTE {self.config.target_pages} pagine (circa {total_words} parole totali)
sul tema: "{self.config.topic}".

REQUISITI OBBLIGATORI:
- Il libro DEVE avere ESATTAMENTE {num_chapters} capitoli (non di più, non di meno)
- Ogni capitolo deve avere circa {words_per_chapter} parole
- Il totale delle parole di tutti i capitoli deve essere circa {total_words}
- Struttura il contenuto in modo approfondito per coprire tutte le pagine richieste

{context if context else ""}

Per ogni capitolo fornisci:
- titolo
- una descrizione dettagliata del contenuto (3-5 righe)
- parole obiettivo (circa {words_per_chapter})
- sottosezioni specifiche (almeno 3-5 per capitolo)

Rispondi SOLO con un JSON valido con questa struttura:
{{
  "title": "Titolo del libro",
  "chapters": [
    {{
      "title": "Titolo capitolo 1",
      "description": "Descrizione dettagliata...",
      "target_words": {words_per_chapter},
      "subsections": ["Sottosezione 1", "Sottosezione 2", "Sottosezione 3", "Sottosezione 4"]
    }},
    ... (totale ESATTAMENTE {num_chapters} capitoli)
  ]
}}

IMPORTANTE: Genera ESATTAMENTE {num_chapters} capitoli, né più né meno.
"""
        system = "Sei un esperto scrittore e organizzi strutture di libri dettagliate. Rispondi solo con JSON valido. Assicurati di generare il numero esatto di capitoli richiesto."
        response = self.call_ai(prompt, system_prompt=system, max_tokens=3000)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        
        # Tentativo di parsing JSON con gestione errori avanzata
        outline = self._parse_outline_json(response)
        
        # Validazione: assicurati che ci sia il numero minimo di capitoli
        chapters = outline.get("chapters", [])
        min_chapters = max(10, self.config.target_pages // 40)  # Almeno 1 capitolo ogni 40 pagine
        
        if len(chapters) < min_chapters:
            logger.warning(f"Outline ha solo {len(chapters)} capitoli, ne richiede almeno {min_chapters}. Rigenerazione...")
            # Richiama ricorsivamente con un prompt più enfatico
            return self._generate_enforced_outline(min_chapters)
        
        return outline
    
    def _parse_outline_json(self, response: str) -> Dict:
        """
        Parsing JSON con gestione avanzata errori per JSON troncato o malformato.
        """
        try:
            outline = json.loads(response)
            return outline
        except json.JSONDecodeError as e:
            logger.warning(f"Errore parsing JSON: {e}")
            
            # Tentativo 1: Estrai solo la parte valida del JSON usando regex
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    partial_json = match.group()
                    # Aggiungi chiusura forzata se manca
                    if not partial_json.endswith('}'):
                        # Conta parentesi aperte/chiuse
                        open_braces = partial_json.count('{')
                        close_braces = partial_json.count('}')
                        missing_braces = open_braces - close_braces
                        partial_json += '}' * missing_braces
                    
                    outline = json.loads(partial_json)
                    logger.info(f"JSON parzialmente recuperato con successo")
                    return outline
                except json.JSONDecodeError:
                    pass
            
            # Tentativo 2: Usa fallback
            logger.error(f"Impossibile recuperare JSON. Uso fallback.")
            return self._create_fallback_outline()
    
    def _generate_enforced_outline(self, min_chapters: int) -> Dict:
        """Genera un outline con enforcement del numero di capitoli."""
        total_words = self.config.target_pages * self.config.words_per_page
        words_per_chapter = total_words // min_chapters
        
        prompt = f"""
CRITICO: Devi generare ESATTAMENTE {min_chapters} capitoli per un libro di {self.config.target_pages} pagine.

Tema: "{self.config.topic}"

REQUISITI NON NEGOZIABILI:
1. Genera ESATTAMENTE {min_chapters} capitoli (conta attentamente)
2. Ogni capitolo deve avere target_words = {words_per_chapter}
3. La somma di tutti i target_words deve essere circa {total_words}
4. Distribuisci gli argomenti in modo approfondito su tutti i {min_chapters} capitoli

Rispondi SOLO con JSON valido.
"""
        system = "Sei un esperto di strutture editoriali. DEVI generare ESATTAMENTE il numero di capitoli richiesto. Conta i capitoli prima di rispondere."
        response = self.call_ai(prompt, system_prompt=system, max_tokens=4000)
        
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            outline = json.loads(response)
            
            # Verifica finale
            chapters = outline.get("chapters", [])
            if len(chapters) < min_chapters:
                logger.warning(f"Secondo tentativo fallito: {len(chapters)} capitoli. Uso fallback.")
                return self._create_fallback_outline()
            return outline
        except Exception as e:
            logger.error(f"Errore nel secondo tentativo: {e}")
            return self._create_fallback_outline()
    
    def _create_fallback_outline(self) -> Dict:
        """Crea un outline di fallback con la struttura corretta."""
        total_words = self.config.target_pages * self.config.words_per_page
        num_chapters = max(15, self.config.target_pages // 25)  # Circa 1 capitolo ogni 25 pagine
        words_per_chapter = total_words // num_chapters
        
        chapters = []
        for i in range(1, num_chapters + 1):
            if i == 1:
                title = "Introduzione"
                desc = f"Presentazione del tema '{self.config.topic}', contestualizzazione e obiettivi del libro."
            elif i == num_chapters:
                title = "Conclusioni"
                desc = "Sintesi dei concetti principali, riflessioni finali e prospettive future."
            else:
                title = f"Capitolo {i}: Approfondimento tematico"
                desc = f"Analisi dettagliata degli aspetti centrali di '{self.config.topic}', con esempi pratici e casi studio."
            
            chapters.append({
                "title": title,
                "description": desc,
                "target_words": words_per_chapter,
                "subsections": [f"Sezione {i}.1", f"Sezione {i}.2", f"Sezione {i}.3", f"Sezione {i}.4"]
            })
        
        logger.info(f"Creato outline di fallback con {len(chapters)} capitoli")
        return {
            "title": f"{self.config.topic}",
            "chapters": chapters
        }

class ChapterWriterAgent(BaseAgent):
    def __init__(self, config: Config, name: str, knowledge_base: Optional[KnowledgeBase] = None):
        super().__init__(config, name, knowledge_base)
        self.section_generator = RecursiveSectionGenerator(self, config)
        self.content_validator = ContentValidator(config)
        self.token_budget = AdaptiveTokenBudget(config)
    
    def write_chapter(self, chapter_info: Dict, outline_context: str, previous_summary: str = "") -> str:
        """
        Scrive un capitolo con validazione e rigenerazione automatica.
        Supporta generazione ricorsiva sezioni se abilitato.
        """
        # Recupera contesto specifico per questo capitolo
        kb_context = ""
        if self.knowledge_base and self.knowledge_base.is_loaded():
            kb_context = self.knowledge_base.get_context_for_chapter(chapter_info)
            if kb_context:
                logger.info(f"Contesto recuperato per capitolo: {chapter_info.get('title', 'Unknown')}")
        
        # Calcola budget token adattivo
        max_tokens = self.token_budget.allocate_tokens(chapter_info, outline_context)
        logger.info(f"Token budget allocato per '{chapter_info['title']}': {max_tokens}")
        
        # Genera capitolo (con eventuale rigenerazione)
        attempt = 0
        chapter_content = ""
        
        while attempt < self.content_validator.max_attempts:
            attempt += 1
            
            if self.config.enable_recursive_sections:
                # Usa generazione ricorsiva sezioni
                chapter_content = self._write_chapter_recursive(
                    chapter_info, outline_context, previous_summary, kb_context, max_tokens
                )
            else:
                # Usa generazione tradizionale
                chapter_content = self._write_chapter_traditional(
                    chapter_info, outline_context, previous_summary, kb_context, max_tokens
                )
            
            # Valida contenuto
            if self.config.enable_content_validation:
                validation = self.content_validator.validate_chapter(chapter_content, chapter_info)
                logger.info(f"Validazione capitolo '{chapter_info['title']}': "
                          f"{validation['word_count']}/{validation['target_words']} parole "
                          f"(densità: {validation['density_ratio']:.1%})")
                
                if validation['valid']:
                    logger.info(f"Capitolo '{chapter_info['title']}' validato con successo")
                    break
                elif attempt < self.content_validator.max_attempts:
                    logger.warning(f"Rigenerazione capitolo (tentativo {attempt + 1})")
                    continue
                else:
                    logger.warning(f"Max tentativi raggiunti, uso capitolo non ottimale")
            else:
                break
        
        return chapter_content
    
    def _write_chapter_recursive(self, chapter_info: Dict, outline_context: str,
                                  previous_summary: str, kb_context: str, max_tokens: int) -> str:
        """
        Scrive capitolo usando generazione ricorsiva sezioni con hard token limits.
        
        Include:
        - Calibrazione lunghezza attesa con CharacterDensityEstimator
        - Hard token limit per sezione (max_tokens = floor(target_words * 1.3))
        - Real-time token counter con 110% interrupt
        - Timeout 3 minuti per sezione
        - Post-generation validation (discard se >120% target)
        - Section-level checkpointing
        """
        sections = chapter_info.get('subsections', [])
        blueprint = chapter_info.get('blueprint', {})
        target_words = chapter_info.get('target_words', self.config.words_per_chapter)
        
        # Calibra lunghezza attesa con CharacterDensityEstimator
        # 1 parola ≈ 4 token, 1 pagina ≈ 3000 caratteri ≈ 750 parole
        expected_tokens_per_section = int((target_words * 1.3) / max(len(sections), 1))
        logger.info(f"Calibrazione: {expected_tokens_per_section} token/sectione (target: {target_words} parole)")
        
        # Inizializza section generator con target specifico per capitolo
        self.section_generator = RecursiveSectionGenerator(self, self.config, target_words)
        
        # Introduzione capitolo con hard limit
        intro_max_tokens = min(500, expected_tokens_per_section // 4)
        intro_prompt = f"""
Scrivi l'introduzione del capitolo "{chapter_info['title']}".

Descrizione: {chapter_info.get('description', '')}

VINCOLI RIGIDI:
- Scrivi ESATTAMENTE 1-2 paragrafi brevi
- Massimo {intro_max_tokens * 4} parole
- Sii conciso, vai dritto al punto
"""
        intro = self.call_ai(intro_prompt, system_prompt="Scrivi introduzioni BREVI e MIRATE.",
                            max_tokens=intro_max_tokens)
        
        content_parts = [f"# {chapter_info['title']}\n\n{intro}"]
        running_token_count = count_tokens(intro)
        interrupt_threshold = int(target_words * 1.3 * 1.1)  # 110% del target
        
        # Genera ogni sezione in modo ricorsivo
        blueprint_sections = blueprint.get('sections', [])
        num_sections = len(blueprint_sections) if blueprint_sections else max(len(sections), 1)
        
        for i, section in enumerate(blueprint_sections if blueprint_sections else
                                    [{'title': s, 'description': ''} for s in sections]):
            section_title = section.get('title', str(section))
            logger.info(f"  Generazione sezione {i+1}/{num_sections}: {section_title}")
            
            # Check interrupt prima di generare
            if running_token_count > interrupt_threshold:
                logger.warning(f"INTERRUPT: Raggiunto 110% token limit ({running_token_count} token). "
                              f"Salto sezioni rimanenti.")
                break
            
            section_content = self.section_generator.generate_section(
                section_title,
                section.get('description', ''),
                depth=0,
                parent_context=outline_context + "\n" + previous_summary,
                num_sections=num_sections
            )
            
            running_token_count += count_tokens(section_content)
            content_parts.append(section_content)
            
            # Log token usage
            logger.info(f"  Sezione completata: {count_tokens(section_content)} token, "
                       f"totale capitolo: {running_token_count} token")
        
        # Post-generation validation: scarta se >120% target
        if running_token_count > int(target_words * 1.3 * self.config.max_overgeneration_threshold):
            logger.warning(f"OVERGENERATION: Capitolo ha {running_token_count} token "
                          f"(limite: {int(target_words * 1.2)}). Troncamento...")
            # Tronca contenuto all'80%
            truncate_at = int(len(content_parts) * 0.8)
            content_parts = content_parts[:truncate_at]
            content_parts.append("\n\n[... contenuto troncato per eccessiva lunghezza ...]")
        
        # Conclusione capitolo solo se non abbiamo superato il limite
        if running_token_count < interrupt_threshold:
            conclusion_max_tokens = min(400, expected_tokens_per_section // 5)
            conclusion_prompt = f"""
Scrivi una conclusione BREVE per il capitolo "{chapter_info['title']}".

VINCOLI RIGIDI:
- Massimo 1 paragrafo
- Massimo {conclusion_max_tokens * 4} parole
- Riassumi in 2-3 frasi
"""
            conclusion = self.call_ai(conclusion_prompt, max_tokens=conclusion_max_tokens)
            content_parts.append(f"\n\n## Conclusione\n\n{conclusion}")
        
        return "\n\n".join(content_parts)
    
    def _write_chapter_traditional(self, chapter_info: Dict, outline_context: str,
                                    previous_summary: str, kb_context: str, max_tokens: int) -> str:
        """Scrive capitolo usando metodo tradizionale."""
        prompt = f"""
Stai scrivendo un capitolo per un libro.

Traccia del capitolo:
Titolo: {chapter_info['title']}
Descrizione: {chapter_info.get('description', '')}
Sottosezioni: {chapter_info.get('subsections', [])}
Parole obiettivo: {chapter_info.get('target_words', 8000)}

Contesto del libro (struttura generale):
{outline_context[:2000]}

Sommario dei capitoli precedenti (se presente):
{previous_summary[:1000]}

{kb_context if kb_context else ""}

REQUISITI CRITICI:
- Genera ALMENO {chapter_info.get('target_words', 8000)} parole
- Sii estremamente dettagliato e approfondito
- Aggiungi esempi pratici, casi studio, spiegazioni approfondite
- Usa formattazione markdown completa (titoli, paragrafi, elenchi, enfasi)
- Non riassumere, espandi ogni concetto al massimo

Scrivi il capitolo in modo completo, dettagliato, con uno stile professionale e coinvolgente.
"""
        system = "Sei uno scrittore professionista di saggistica. Scrivi capitoli estremamente dettagliati, densi di contenuto e ben strutturati."
        return self.call_ai(prompt, system_prompt=system, max_tokens=max_tokens)

class EditorAgent(BaseAgent):
    def edit_chapter(self, chapter_text: str, chapter_title: str) -> str:
        prompt = f"""
Rivedi e migliora il seguente capitolo dal titolo "{chapter_title}".
Correggi errori grammaticali, migliora lo stile, rendi il testo più fluido e coerente.
Mantieni lo stesso livello di dettaglio e la struttura markdown.

Capitolo originale:
{chapter_text}

Versione revisionata:
"""
        system = "Sei un editor professionista esperto in saggistica. Migliora il testo mantenendo il contenuto originale."
        return self.call_ai(prompt, system_prompt=system, max_tokens=3000)

class CompilerAgent(BaseAgent):
    def compile_book(self, title: str, chapters: List[Dict[str, str]]) -> str:
        book_md = f"# {title}\n\n"
        book_md += f"*Generato automaticamente con BookWriterAI*\n\n---\n\n"
        book_md += "## Indice\n\n"
        for i, ch in enumerate(chapters, 1):
            book_md += f"{i}. {ch['title']}\n\n"
        book_md += "---\n\n"
        for i, ch in enumerate(chapters, 1):
            book_md += f"# Capitolo {i}: {ch['title']}\n\n"
            book_md += ch['content']
            book_md += "\n\n---\n\n"
        return book_md

# ----------------------------------------------------------------------
# Orchestratore con checkpoint e knowledge base
# ----------------------------------------------------------------------
class BookOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        
        # Inizializza Knowledge Base
        self.knowledge_base = KnowledgeBase(config)
        kb_loaded = self.knowledge_base.initialize()
        
        if kb_loaded:
            stats = self.knowledge_base.get_stats()
            logger.info(f"Knowledge Base caricata: {stats.get('total_chunks', 0)} chunk, "
                       f"{stats.get('total_tokens', 0)} token")
        
        # Inizializza agenti con knowledge base
        self.outline_agent = OutlineAgent(config, "OutlineAgent", self.knowledge_base)
        self.writer_agent = ChapterWriterAgent(config, "WriterAgent", self.knowledge_base)
        self.editor_agent = EditorAgent(config, "EditorAgent", self.knowledge_base)
        self.compiler_agent = CompilerAgent(config, "CompilerAgent", self.knowledge_base)
        
        # Inizializza sistema multi-layered
        self.outline_enricher = ProgressiveOutlineEnricher(self.outline_agent, config)
        self.density_estimator = CharacterDensityEstimator()
        
        self.checkpoint_dir = Path(config.checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.state = self._load_checkpoint()

    def _load_checkpoint(self) -> Dict:
        checkpoint_file = self.checkpoint_dir / "state.json"
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Errore nel caricamento checkpoint: {e}")
        return {"outline": None, "chapters": [], "current_chapter_idx": 0, "completed": False}

    def _save_checkpoint(self):
        checkpoint_file = self.checkpoint_dir / "state.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        logger.info("Checkpoint salvato.")

    def _save_chapter(self, idx: int, title: str, content: str, edited: str):
        chapter_data = {
            "title": title,
            "content": content,
            "edited": edited,
            "timestamp": time.time()
        }
        chapter_file = self.checkpoint_dir / f"chapter_{idx:03d}.json"
        with open(chapter_file, 'w', encoding='utf-8') as f:
            json.dump(chapter_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Capitolo {idx} salvato su disco.")

    def _load_chapter(self, idx: int) -> Optional[Dict]:
        chapter_file = self.checkpoint_dir / f"chapter_{idx:03d}.json"
        if chapter_file.exists():
            with open(chapter_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def generate_book(self):
        if self.state["outline"] is None:
            logger.info("Generazione outline del libro...")
            basic_outline = self.outline_agent.generate()
            
            # Fase di arricchimento progressivo dell'outline
            if self.config.enable_progressive_outline:
                logger.info("Arricchimento progressivo dell'outline...")
                outline = self.outline_enricher.enrich(basic_outline)
            else:
                outline = basic_outline
            
            self.state["outline"] = outline
            self._save_checkpoint()
        else:
            outline = self.state["outline"]
            logger.info("Outline caricato da checkpoint.")

        title = outline.get("title", f"Libro su {self.config.topic}")
        chapters_info = outline.get("chapters", [])
        if not chapters_info:
            raise ValueError("L'outline non contiene capitoli.")
        
        # Validazione: verifica che il numero di capitoli sia sufficiente
        min_chapters = max(10, self.config.target_pages // 40)
        if len(chapters_info) < min_chapters:
            logger.warning(f"L'outline ha solo {len(chapters_info)} capitoli, ne sono consigliati almeno {min_chapters} per {self.config.target_pages} pagine.")

        start_idx = self.state["current_chapter_idx"]
        for idx in range(start_idx, len(chapters_info)):
            ch_info = chapters_info[idx]
            ch_title = ch_info["title"]

            existing = self._load_chapter(idx)
            if existing:
                raw_content = existing["content"]
                edited_content = existing["edited"]
                logger.info(f"Capitolo {idx+1} già presente, uso versione esistente.")
            else:
                logger.info(f"Scrittura capitolo {idx+1}: {ch_title}")
                outline_context = json.dumps(outline, indent=2, ensure_ascii=False)
                prev_summary = ""
                if idx > 0 and self.state["chapters"]:
                    prev_ch = self.state["chapters"][-1]
                    prev_summary = f"Riassunto del capitolo {idx}: {prev_ch['title']}\n{prev_ch['edited'][:500]}..."
                raw_content = self.writer_agent.write_chapter(ch_info, outline_context, prev_summary)
                logger.info(f"Editing capitolo {idx+1}")
                edited_content = self.editor_agent.edit_chapter(raw_content, ch_title)
                self._save_chapter(idx, ch_title, raw_content, edited_content)

            self.state["chapters"].append({
                "title": ch_title,
                "content": raw_content,
                "edited": edited_content
            })
            self.state["current_chapter_idx"] = idx + 1
            self._save_checkpoint()

        logger.info("Compilazione del libro finale...")
        chapters_final = [{"title": c["title"], "content": c["edited"]} for c in self.state["chapters"]]
        book_md = self.compiler_agent.compile_book(title, chapters_final)

        # Calcola statistiche usando CharacterDensityEstimator
        density_stats = self.density_estimator.estimate_from_chapters(chapters_final)
        estimated_pages = density_stats["estimated_pages"]
        target_pages = self.config.target_pages
        
        logger.info(f"Statistiche libro (CharacterDensityEstimator):")
        logger.info(f"  - Caratteri totali: {density_stats['total_chars']:,}")
        logger.info(f"  - Parole totali: {density_stats['total_words']:,}")
        logger.info(f"  - Pagine stimate: ~{estimated_pages} (target: {target_pages})")
        logger.info(f"  - Media caratteri/capitolo: {density_stats['chars_per_chapter_avg']:,}")
        logger.info(f"  - Media parole/capitolo: {density_stats['words_per_chapter_avg']:,}")
        logger.info(f"  - Capitoli: {len(chapters_final)}")
        
        # Controllo di validazione: interrompi se il libro è significativamente più corto del target
        min_acceptable_pages = max(self.config.compensatory_content_threshold, int(target_pages * 0.7))
        if estimated_pages < min_acceptable_pages:
            error_msg = (
                f"ERRORE VALIDAZIONE: Il libro generato ha solo ~{estimated_pages} pagine "
                f"({density_stats['total_chars']:,} caratteri), ma il target era di {target_pages} pagine. "
                f"Il risultato è inferiore al minimo accettabile di {min_acceptable_pages} pagine. "
                f"Possibili cause: numero insufficiente di capitoli ({len(chapters_final)}), "
                f"capitoli troppo brevi, o problemi nella generazione del contenuto. "
                f"Prova a: 1) Aumentare il numero di capitoli, 2) Verificare il parametro --pages, "
                f"3) Rigenerare l'outline con una struttura più dettagliata, "
                f"4) Usare un modello con maggiore context window (es. qwen3.5-plus)."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        elif estimated_pages < target_pages * 0.9:
            logger.warning(f"AVVISO: Il libro generato (~{estimated_pages} pagine) è leggermente inferiore al target ({target_pages} pagine).")

        output_path = Path(self.config.output_file)
        output_path.write_text(book_md, encoding='utf-8')
        logger.info(f"Libro completato e salvato in {output_path.absolute()}")

        self.state["completed"] = True
        self._save_checkpoint()

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Genera un libro con sub‑agent AI, supporta endpoint personalizzati e knowledge base contestuale"
    )
    parser.add_argument("--topic", type=str, default="Intelligenza artificiale e futuro del lavoro",
                        help="Tema principale del libro")
    parser.add_argument("--output", type=str, default="book_output.md",
                        help="File di output (Markdown)")
    parser.add_argument("--pages", type=int, default=400,
                        help="Numero di pagine desiderato (300-500)")
    parser.add_argument("--context", type=str, default=None,
                        help="Percorso alla cartella contenente documenti di riferimento (PDF, TXT, MD)")
    parser.add_argument("--provider", choices=["openai", "qwen", "bailian"], default="openai",
                        help="Provider AI (openai per endpoint compatibili, bailian per Coding Plan/OpenClaw, qwen per DashScope nativo)")
    parser.add_argument("--model", type=str, default=None,
                        help="Modello specifico (es. gpt-4, qwen3.5-plus, kimi-k2.5). Se omesso usa default del provider")
    parser.add_argument("--endpoint", type=str, default=None,
                        help="Base URL personalizzato per API OpenAI-compatibile (es. https://coding-intl.dashscope.aliyuncs.com/v1)")

    args = parser.parse_args()

    # Scegli modello di default in base al provider
    if not args.model:
        if args.provider == "openai":
            args.model = "gpt-4"
        elif args.provider == "bailian":
            args.model = "qwen3.5-plus"  # Default per Coding Plan/OpenClaw
        else:  # qwen
            args.model = "qwen-max"

    config = Config(
        topic=args.topic,
        output_file=args.output,
        context_path=args.context,
        provider=args.provider,
        model=args.model,
        endpoint=args.endpoint,
        target_pages=args.pages,
        words_per_page=400,
        words_per_chapter=(args.pages * 400) // 20
    )

    orchestrator = BookOrchestrator(config)
    orchestrator.generate_book()

if __name__ == "__main__":
    main()
