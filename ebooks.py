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
    provider: str = "openai"               # "openai" o "qwen"
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

    def __post_init__(self):
        if self.provider == "qwen" and not self.api_key:
            self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if self.provider == "openai" and not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("API key non trovata. Imposta OPENAI_API_KEY o DASHSCOPE_API_KEY nel .env")

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
                    documents.append(doc)
                elif doc and doc.get("error"):
                    self._errors.append(f"{file_path}: {doc['error']}")
        
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
        elif self.config.provider == "qwen":
            # Qwen usa l'API DashScope nativa
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
                if self.config.provider == "openai":
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
        
        prompt = f"""
Crea una struttura dettagliata per un libro di {self.config.target_pages} pagine (circa {self.config.target_pages * self.config.words_per_page} parole) 
sul tema: "{self.config.topic}".

{context if context else ""}

Il libro deve essere diviso in capitoli e, se necessario, sottocapitoli.
Per ogni capitolo fornisci:
- titolo
- una breve descrizione del contenuto (2-3 righe)
- parole obiettivo (circa {self.config.words_per_chapter})

Rispondi SOLO con un JSON valido con questa struttura:
{{
  "title": "Titolo del libro",
  "chapters": [
    {{
      "title": "Titolo capitolo 1",
      "description": "...",
      "target_words": 8000,
      "subsections": ["Sottosezione 1", "Sottosezione 2"]
    }},
    ...
  ]
}}
"""
        system = "Sei un esperto scrittore e organizzi strutture di libri. Rispondi solo con JSON valido."
        response = self.call_ai(prompt, system_prompt=system, max_tokens=3000)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        try:
            outline = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Errore parsing JSON dall'OutlineAgent: {e}\nRisposta:\n{response}")
            outline = {
                "title": f"Libro su {self.config.topic}",
                "chapters": [
                    {"title": "Introduzione", "description": "Introduzione al tema.", "target_words": 5000},
                    {"title": "Sviluppo", "description": "Contenuto principale.", "target_words": 10000},
                    {"title": "Conclusioni", "description": "Riflessioni finali.", "target_words": 5000}
                ]
            }
        return outline

class ChapterWriterAgent(BaseAgent):
    def write_chapter(self, chapter_info: Dict, outline_context: str, previous_summary: str = "") -> str:
        # Recupera contesto specifico per questo capitolo
        kb_context = ""
        if self.knowledge_base and self.knowledge_base.is_loaded():
            kb_context = self.knowledge_base.get_context_for_chapter(chapter_info)
            if kb_context:
                logger.info(f"Contesto recuperato per capitolo: {chapter_info.get('title', 'Unknown')}")
        
        prompt = f"""
Stai scrivendo un capitolo per un libro.

Traccia del capitolo:
Titolo: {chapter_info['title']}
Descrizione: {chapter_info.get('description', '')}
Sottosezioni: {chapter_info.get('subsections', [])}
Parole obiettivo: {chapter_info.get('target_words', 8000)}

Contesto del libro (struttura generale):
{outline_context}

Sommario dei capitoli precedenti (se presente):
{previous_summary}

{kb_context if kb_context else ""}

Scrivi il capitolo in modo completo, dettagliato, con uno stile professionale e coinvolgente.
Assicurati di raggiungere circa le parole obiettivo. Formatta con markdown (titoli, paragrafi, elenchi).
"""
        system = "Sei uno scrittore professionista di saggistica. Scrivi capitoli ben strutturati, chiari e approfonditi."
        return self.call_ai(prompt, system_prompt=system, max_tokens=3000)

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
            outline = self.outline_agent.generate()
            self.state["outline"] = outline
            self._save_checkpoint()
        else:
            outline = self.state["outline"]
            logger.info("Outline caricato da checkpoint.")

        title = outline.get("title", f"Libro su {self.config.topic}")
        chapters_info = outline.get("chapters", [])
        if not chapters_info:
            raise ValueError("L'outline non contiene capitoli.")

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
    parser.add_argument("--provider", choices=["openai", "qwen"], default="openai",
                        help="Provider AI (openai per endpoint compatibili, qwen per DashScope nativo)")
    parser.add_argument("--model", type=str, default=None,
                        help="Modello specifico (es. gpt-4, qwen-max, kimi-k2.5). Se omesso usa default del provider")
    parser.add_argument("--endpoint", type=str, default=None,
                        help="Base URL personalizzato per API OpenAI-compatibile (es. https://coding-intl.dashscope.aliyuncs.com/v1)")

    args = parser.parse_args()

    # Scegli modello di default in base al provider
    if not args.model:
        if args.provider == "openai":
            args.model = "gpt-4"
        else:
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
