#!/usr/bin/env python3
"""
Esempio di utilizzo della nuova API modulare v2.0 di BookWriterAI.

Questo script dimostra come utilizzare ProfessionalBookWriter per generare
libri con la nuova architettura modulare.

Utilizzo:
    python generate_book.py

Per personalizzare, modifica le variabili di configurazione sotto.
"""

import sys
from pathlib import Path

# Aggiungi la root al path per import
sys.path.insert(0, str(Path(__file__).parent))

from src.book_writer import ProfessionalBookWriter, BookConfig, GenerationProgress


# ============================================================================
# CONFIGURAZIONE - Modifica questi parametri per personalizzare la generazione
# ============================================================================

TITLE = "Il Mistero della Villa Oscura"
GENRE = "thriller"           # Opzioni: thriller, romance, fantasy, mystery, scifi, horror, literary_fiction, nonfiction, technical, academic
SUBGENRE = "psychological"   # Sottogenere (opzionale)
TARGET_LENGTH = 80000        # Numero di parole target
STYLE = "commercial"         # Opzioni: literary, commercial, academic, technical

# Feature flags
ENABLE_REFINEMENT = True     # Abilita raffinamento iterativo per migliorare la qualità
ENABLE_CHARACTER_TRACKING = True  # Abilita tracking consistenza personaggi

# Provider LLM
PROVIDER = "bailian"         # Opzioni: openai, bailian, qwen
MODEL = "qwen3.5-plus"       # Modello (qwen3.5-plus raccomandato per 1M context)

# Output
OUTPUT_DIR = "output"

# Citazioni (per contenuti tecnici/accademici)
CITATION_STYLE = None        # Opzioni: apa, mla, chicago, ieee, harvard, vancouver, None

# Documenti di contesto (opzionale)
CONTEXT_PATH = None          # Path a directory con documenti PDF/TXT/MD

# ============================================================================
# CODICE - Non modificare sotto questa linea
# ============================================================================

def progress_callback(progress: GenerationProgress):
    """
    Callback chiamato durante la generazione per mostrare il progresso.
    """
    # Barra di progresso
    bar_length = 50
    filled = int(bar_length * progress.progress_percent)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    # Stampa con sovrascrittura
    print(f"\r[{bar}] {progress.progress_percent:>5.1%} | {progress.current_phase}: {progress.message}", end="", flush=True)
    
    # Nuova riga al completamento
    if progress.progress_percent >= 1.0:
        print()


def main():
    """Funzione principale per la generazione del libro."""
    
    # Stampa intestazione
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    BookWriterAI v2.0 - API Modulare                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  Titolo: {TITLE:<56} ║
║  Genere: {GENRE:<56} ║
║  Lunghezza target: {TARGET_LENGTH:>6} parole{' ':<31} ║
║  Stile: {STYLE:<58} ║
║  Provider: {PROVIDER} ({MODEL}){' ':<38} ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Crea configurazione
    config = BookConfig(
        title=TITLE,
        genre=GENRE,
        subgenre=SUBGENRE,
        target_length=TARGET_LENGTH,
        style=STYLE,
        enable_refinement=ENABLE_REFINEMENT,
        enable_character_tracking=ENABLE_CHARACTER_TRACKING,
        citation_style=CITATION_STYLE,
        context_path=CONTEXT_PATH,
        provider=PROVIDER,
        model=MODEL,
    )
    
    # Inizializza il writer
    print("🔧 Inizializzazione BookWriter...")
    writer = ProfessionalBookWriter(config)
    
    # Crea directory output
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Avvia generazione
    print("🚀 Avvio generazione libro...\n")
    
    try:
        result = writer.generate_book(progress_callback=progress_callback)
        
        if result.success:
            print(f"\n{'='*70}")
            print("✅ GENERAZIONE COMPLETATA CON SUCCESSO!")
            print(f"{'='*70}")
            
            # Statistiche
            print(f"\n📊 Statistiche:")
            print(f"   • Parole totali: {result.book.total_word_count:,}")
            print(f"   • Capitoli: {len(result.book.chapters)}")
            print(f"   • Tempo di generazione: {result.generation_time_seconds:.1f} secondi")
            
            # Esporta in Markdown
            md_path = output_dir / f"{TITLE.replace(' ', '_')}.md"
            writer.export_book(result.book, "markdown", str(md_path))
            print(f"\n📝 Esportato in Markdown: {md_path}")
            
            # Esporta in JSON
            json_path = output_dir / f"{TITLE.replace(' ', '_')}.json"
            writer.export_book(result.book, "json", str(json_path))
            print(f"📋 Esportato in JSON: {json_path}")
            
            # Report qualità
            if result.quality_report:
                print(f"\n📈 Report Qualità:")
                print(f"   • Coerenza narrativa: {result.quality_report.narrative_coherence:.0%}")
                print(f"   • Consistenza stilistica: {result.quality_report.stylistic_consistency:.0%}")
                print(f"   • Profondità contenuti: {result.quality_report.content_depth:.0%}")
                print(f"   • Punteggio complessivo: {result.quality_report.overall_score:.0%}")
            
            # Mostra primi capitoli
            print(f"\n📖 Anteprima capitoli:")
            for i, chapter in enumerate(result.book.chapters[:3], 1):
                preview = chapter.content[:200].replace('\n', ' ') + "..."
                print(f"   {i}. {chapter.title}")
                print(f"      {preview}")
            
            if len(result.book.chapters) > 3:
                print(f"   ... e altri {len(result.book.chapters) - 3} capitoli")
            
            return 0
        else:
            print(f"\n{'='*70}")
            print("❌ ERRORE DURANTE LA GENERAZIONE")
            print(f"{'='*70}")
            print(f"\nMessaggio di errore: {result.error_message}")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Generazione interrotta dall'utente")
        print("I progressi sono stati salvati nei checkpoint.")
        return 130
        
    except Exception as e:
        print(f"\n\n❌ Errore imprevisto: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())