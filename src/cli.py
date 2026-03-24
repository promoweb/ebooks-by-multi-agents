#!/usr/bin/env python3
"""
BookWriterAI v2.0 - Command Line Interface

Interfaccia a riga di comando per la nuova API modulare.
Utilizzo: python -m src.cli --title "Il mio libro" --genre thriller --length 80000
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# Aggiungi la root al path per import
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.book_writer import ProfessionalBookWriter, BookConfig, GenerationProgress
from src.genre import GenreTemplateManager
from src.style import StyleProfileManager


def list_genres():
    """Lista tutti i generi disponibili."""
    manager = GenreTemplateManager()
    print("\n📚 Generi disponibili:")
    print("-" * 40)
    for genre_name in manager.list_genres():
        template = manager.get_template(genre_name)
        subgenres = f" ({', '.join(template.subgenres[:3])}...)" if template.subgenres else ""
        print(f"  • {genre_name}{subgenres}")
    print()


def list_styles():
    """Lista tutti gli stili disponibili."""
    manager = StyleProfileManager()
    print("\n🎨 Stili disponibili:")
    print("-" * 40)
    for style_name in manager.list_profiles():
        profile = manager.get_profile(style_name)
        print(f"  • {style_name}: {profile.primary_tone}")
    print()


def progress_callback(progress: GenerationProgress):
    """Callback per mostrare il progresso della generazione."""
    bar_length = 40
    filled = int(bar_length * progress.progress_percent)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    print(f"\r[{bar}] {progress.progress_percent:.0%} - {progress.message}", end="", flush=True)
    
    if progress.progress_percent >= 1.0:
        print()  # New line at completion


def main():
    parser = argparse.ArgumentParser(
        description="BookWriterAI v2.0 - Generazione automatica di libri con AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # Genera un thriller di 80k parole
  python -m src.cli --title "Il Mistero" --genre thriller --length 80000
  
  # Genera con stile letterario e tracking personaggi
  python -m src.cli --title "Romanzo" --genre literary_fiction --style literary --track-characters
  
  # Genera libro tecnico con citazioni
  python -m src.cli --title "AI Guide" --genre technical --style technical --citations apa
  
  # Lista generi disponibili
  python -m src.cli --list-genres
  
  # Lista stili disponibili
  python -m src.cli --list-styles
        """
    )
    
    # Argomenti obbligatori
    parser.add_argument(
        "--title", "-t",
        type=str,
        help="Titolo del libro"
    )
    
    parser.add_argument(
        "--genre", "-g",
        type=str,
        default="thriller",
        help="Genere del libro (default: thriller). Usa --list-genres per vedere tutti."
    )
    
    parser.add_argument(
        "--length", "-l",
        type=int,
        default=50000,
        help="Lunghezza target in parole (default: 50000)"
    )
    
    # Argomenti opzionali
    parser.add_argument(
        "--style", "-s",
        type=str,
        default="commercial",
        help="Stile di scrittura (default: commercial). Usa --list-styles per vedere tutti."
    )
    
    parser.add_argument(
        "--subgenre",
        type=str,
        help="Sottogenere specifico"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Directory di output (default: output)"
    )
    
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["markdown", "json", "both"],
        default="markdown",
        help="Formato di output (default: markdown)"
    )
    
    # Feature flags
    parser.add_argument(
        "--refinement",
        action="store_true",
        default=True,
        help="Abilita raffinamento iterativo (default: attivo)"
    )
    
    parser.add_argument(
        "--no-refinement",
        action="store_true",
        help="Disabilita raffinamento iterativo"
    )
    
    parser.add_argument(
        "--track-characters",
        action="store_true",
        default=True,
        help="Abilita tracking personaggi (default: attivo)"
    )
    
    parser.add_argument(
        "--no-track-characters",
        action="store_true",
        help="Disabilita tracking personaggi"
    )
    
    parser.add_argument(
        "--citations",
        type=str,
        choices=["apa", "mla", "chicago", "ieee", "harvard", "vancouver"],
        help="Stile citazioni per contenuti tecnici/accademici"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        help="Path a documenti di contesto (Knowledge Base)"
    )
    
    # Provider LLM
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "bailian", "qwen"],
        default="bailian",
        help="Provider LLM (default: bailian)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3.5-plus",
        help="Modello LLM (default: qwen3.5-plus)"
    )
    
    # Comandi informativi
    parser.add_argument(
        "--list-genres",
        action="store_true",
        help="Lista tutti i generi disponibili"
    )
    
    parser.add_argument(
        "--list-styles",
        action="store_true",
        help="Lista tutti gli stili disponibili"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula la generazione senza chiamare LLM"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Output dettagliato"
    )
    
    args = parser.parse_args()
    
    # Comandi informativi
    if args.list_genres:
        list_genres()
        return 0
    
    if args.list_styles:
        list_styles()
        return 0
    
    # Validazione argomenti obbligatori
    if not args.title:
        parser.error("--title è richiesto per generare un libro. Usa --help per vedere le opzioni.")
    
    # Crea directory output
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurazione
    enable_refinement = args.refinement and not args.no_refinement
    enable_character_tracking = args.track_characters and not args.no_track_characters
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                   BookWriterAI v2.0                          ║
╠══════════════════════════════════════════════════════════════╣
║  Titolo: {args.title:<50} ║
║  Genere: {args.genre:<50} ║
║  Lunghezza: {args.length:>6} parole{' ':<34} ║
║  Stile: {args.style:<51} ║
║  Provider: {args.provider} ({args.model}){' ':<30} ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Crea configurazione
    config = BookConfig(
        title=args.title,
        genre=args.genre,
        subgenre=args.subgenre,
        target_length=args.length,
        style=args.style,
        enable_refinement=enable_refinement,
        enable_character_tracking=enable_character_tracking,
        citation_style=args.citations,
        context_path=args.context,
        provider=args.provider,
        model=args.model,
    )
    
    # Inizializza writer
    writer = ProfessionalBookWriter(config)
    
    # Genera il libro
    print("🚀 Avvio generazione...\n")
    
    try:
        result = writer.generate_book(
            progress_callback=progress_callback if not args.dry_run else None,
            dry_run=args.dry_run
        )
        
        if result.success:
            print(f"\n✅ Generazione completata!")
            print(f"   📖 Parole totali: {result.book.total_word_count}")
            print(f"   📄 Capitoli: {len(result.book.chapters)}")
            print(f"   ⏱️ Tempo: {result.generation_time_seconds:.1f}s")
            
            # Esporta
            if args.format in ["markdown", "both"]:
                md_path = output_dir / f"{args.title.replace(' ', '_')}.md"
                writer.export_book(result.book, "markdown", str(md_path))
                print(f"   📝 Salvato in: {md_path}")
            
            if args.format in ["json", "both"]:
                json_path = output_dir / f"{args.title.replace(' ', '_')}.json"
                writer.export_book(result.book, "json", str(json_path))
                print(f"   📋 Salvato in: {json_path}")
            
            # Report qualità
            if result.quality_report:
                print(f"\n📊 Report Qualità:")
                print(f"   • Coerenza narrativa: {result.quality_report.narrative_coherence:.0%}")
                print(f"   • Consistenza stile: {result.quality_report.stylistic_consistency:.0%}")
                print(f"   • Qualità complessiva: {result.quality_report.overall_score:.0%}")
            
            return 0
        else:
            print(f"\n❌ Errore durante la generazione: {result.error_message}")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Generazione interrotta dall'utente")
        return 130
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())