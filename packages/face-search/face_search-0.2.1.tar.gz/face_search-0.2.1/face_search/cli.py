#!/usr/bin/env python3
"""
CLI for face-search
"""

import sys
from pathlib import Path
import shutil
import click

from face_search import FaceFinder
from face_search.detectors import DetectorFactory


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """face-search: AI-powered face search for photo libraries"""
    pass


@cli.command()
@click.argument('source', type=click.Path(exists=True, file_okay=False))
@click.option('--detector', default='opencv', 
              type=click.Choice(DetectorFactory.available()),
              help='Face detector to use')
@click.option('--conf', default=0.3, type=float,
              help='Minimum face detection confidence (0-1)')
@click.option('--batch-size', default=500, type=int,
              help='Batch size for FAISS inserts')
@click.option('--max-size', default=1024, type=int,
              help='Max image dimension (0=no resize, best quality)')
@click.option('--workers', default=0, type=int,
              help='Parallel workers (0=auto, 1=single-thread)')
@click.option('--incremental/--no-incremental', default=True,
              help='Only index new files (keep existing index)')
@click.option('--min-face-size', default=0, type=int,
              help='Min face size in pixels (0=no filter, 40+ recommended)')
@click.option('--index', default='./face_index.faiss',
              help='Index file path')
def build(source, detector, conf, batch_size, max_size, workers, incremental, min_face_size, index):
    """Build face index from photos."""
    click.echo(f"🔧 Building index from {source}")
    click.echo(f"   Detector: {detector}")
    click.echo(f"   Min confidence: {conf}")
    click.echo(f"   Max image size: {max_size}px")
    if min_face_size > 0:
        click.echo(f"   Min face size: {min_face_size}px")
    if incremental:
        click.echo("   Mode: Incremental (new files only)")
    click.echo("")
    
    try:
        finder = FaceFinder(
            index_file=Path(index),
            min_confidence=conf
        )
        finder.build(
            Path(source),
            detector_name=detector,
            batch_size=batch_size,
            max_size=max_size,
            workers=workers,
            incremental=incremental,
            min_face_size=min_face_size
        )
        
        stats = finder.stats()
        
        click.echo(f"\n{'='*50}")
        click.echo("✓ BUILD COMPLETE")
        click.echo(f"{'='*50}")
        click.echo(f"  Faces indexed:  {stats.total_faces:,}")
        click.echo(f"  Unique images:  {stats.total_images:,}")
        click.echo(f"  Index size:     {stats.index_size_mb:.1f} MB")
        click.echo(f"  Saved to:       {index}\n")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--ref', default='./reference_faces',
              type=click.Path(exists=True, file_okay=False),
              help='Reference faces directory')
@click.option('--threshold', default=0.35, type=float,
              help='Distance threshold (0-1, lower=stricter)')
@click.option('--top', default=0, type=int,
              help='Max results (0=unlimited)')
@click.option('--output', default=None,
              type=click.Path(),
              help='Output directory to copy matched files')
@click.option('--preserve-structure', is_flag=True,
              help='Keep original folder structure when copying')
@click.option('--output-file', default=None,
              type=click.Path(),
              help='Write matched file paths to a text file')
@click.option('--index', default='./face_index.faiss',
              help='Index file path')
def search(ref, threshold, top, output, preserve_structure, output_file, index):
    """Search for faces matching references."""
    try:
        finder = FaceFinder(index_file=Path(index))
        finder.load()
        
        stats = finder.stats()
        click.echo(f"📊 Index: {stats.total_faces:,} faces")
        click.echo(f"🎯 Threshold: {threshold}\n")
        
        click.echo("📁 Loading reference faces...")
        num_refs = finder.load_references(Path(ref))
        click.echo(f"   ✓ {num_refs} reference embedding(s)\n")
        
        click.echo("🔍 Searching...")
        # top=0 means unlimited
        k = top if top > 0 else stats.total_faces
        matches = finder.search(threshold=threshold, top_k=k)
        
        if not matches:
            click.echo("   No matches found. Try increasing --threshold.\n")
            return
        
        click.echo(f"\n{'='*50}")
        click.echo(f"✓ Found {len(matches)} unique matches")
        click.echo(f"{'='*50}\n")
        
        # Show results with paths
        for i, match in enumerate(matches[:10], 1):
            click.echo(f"  {i:2}. {match.distance:.4f} | {match.file_path}")
        
        if len(matches) > 10:
            click.echo(f"\n  ... and {len(matches)-10} more\n")
        
        # Copy files if output specified
        if output:
            output_dir = Path(output)
            
            # Clear old results (only if not preserving structure)
            if output_dir.exists() and not preserve_structure:
                for f in output_dir.glob("*"):
                    if f.is_file():
                        f.unlink()
            
            click.echo(f"📦 Copying to {output_dir}...")
            if preserve_structure:
                click.echo("   (preserving folder structure)")
            
            with click.progressbar(matches, label='Copying') as bar:
                for match in bar:
                    src = Path(match.file_path)
                    if not src.exists():
                        continue
                    
                    if preserve_structure:
                        # Keep original folder structure
                        # Extract relative path and create same structure
                        try:
                            rel_path = src.relative_to(src.parent.parent.parent)
                            dst = output_dir / rel_path
                        except ValueError:
                            # If relative path fails, just use filename
                            dst = output_dir / src.name
                    else:
                        # Flat output with distance prefix for sorting
                        dst = output_dir / f"{match.distance:.4f}_{src.name}"
                    
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            
            click.echo(f"   ✓ Copied {len(matches)} files\n")
        
        # Write output file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                for match in matches:
                    f.write(f"{match.file_path}\n")
            click.echo(f"📝 Wrote {len(matches)} paths to {output_path}\n")
        
        if not output and not output_file:
            click.echo()
    
    except FileNotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        click.echo("   Run 'face-search build' first.\n", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--index', default='./face_index.faiss',
              help='Index file path')
def info(index):
    """Show index statistics."""
    try:
        finder = FaceFinder(index_file=Path(index))
        finder.load()
        
        stats = finder.stats()
        
        click.echo(f"\n{'='*50}")
        click.echo("  INDEX INFO")
        click.echo(f"{'='*50}\n")
        click.echo(f"  Index file:     {index}")
        click.echo(f"  Total faces:    {stats.total_faces:,}")
        click.echo(f"  Unique images:  {stats.total_images:,}")
        click.echo(f"  Embedding dim:  {stats.embedding_dim}")
        click.echo(f"  Detector used:  {stats.detector_used}")
        click.echo(f"  Index size:     {stats.index_size_mb:.1f} MB")
        
        # Show sources
        sources = finder.index.get_sources()
        if sources:
            click.echo(f"\n  📁 Sources ({len(sources)}):")
            for src, info in sources.items():
                click.echo(f"     • {src}")
                click.echo(f"       {info['count']:,} faces | added {info.get('added', 'unknown')[:10]}")
        click.echo()
        
    except FileNotFoundError:
        click.echo(f"❌ Index not found: {index}", err=True)
        click.echo("   Run 'face-search build' first.\n", err=True)
        sys.exit(1)


@cli.command()
@click.option('--index', default='./face_index.faiss',
              help='Index file path')
def sources(index):
    """List all indexed source directories."""
    try:
        finder = FaceFinder(index_file=Path(index))
        finder.load()
        
        sources = finder.index.get_sources()
        
        if not sources:
            click.echo("📭 No sources tracked yet.")
            click.echo("   (Older indexes may not have source tracking)")
            click.echo("   Run 'face-search build <dir>' to index with tracking.\n")
            return
        
        click.echo(f"\n{'='*50}")
        click.echo(f"  INDEXED SOURCES ({len(sources)})")
        click.echo(f"{'='*50}\n")
        
        total_faces = 0
        for i, (src, info) in enumerate(sources.items(), 1):
            click.echo(f"  {i}. {src}")
            click.echo(f"     Faces: {info['count']:,}")
            click.echo(f"     Added: {info.get('added', 'unknown')[:10]}")
            if info.get('updated'):
                click.echo(f"     Updated: {info['updated'][:10]}")
            click.echo()
            total_faces += info['count']
        
        click.echo(f"  Total: {total_faces:,} faces from {len(sources)} sources\n")
        
    except FileNotFoundError:
        click.echo(f"❌ Index not found: {index}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('source_path', type=click.Path())
@click.option('--index', default='./face_index.faiss',
              help='Index file path')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def remove(source_path, index, yes):
    """Remove a source directory from index."""
    try:
        finder = FaceFinder(index_file=Path(index))
        finder.load()
        
        # Resolve path
        source_path = str(Path(source_path).resolve())
        
        # Check if source exists in index
        sources = finder.index.get_sources()
        if source_path not in sources:
            # Try partial match
            matches = [s for s in sources if source_path in s or s in source_path]
            if matches:
                click.echo(f"Source not found exactly. Did you mean:")
                for m in matches:
                    click.echo(f"  • {m}")
                return
            click.echo(f"❌ Source not found in index: {source_path}", err=True)
            click.echo("   Use 'face-search sources' to list indexed sources.\n", err=True)
            sys.exit(1)
        
        face_count = sources[source_path]['count']
        
        if not yes:
            click.confirm(
                f"Remove {face_count:,} faces from {source_path}?",
                abort=True
            )
        
        click.echo(f"🗑️  Removing faces from {source_path}...")
        removed = finder.index.remove_source(source_path)
        finder.save()
        
        click.echo(f"   ✓ Removed {removed:,} faces")
        click.echo(f"   Index now has {finder.index.size():,} faces\n")
        
    except FileNotFoundError:
        click.echo(f"❌ Index not found: {index}", err=True)
        sys.exit(1)
    except click.Abort:
        click.echo("Aborted.")


@cli.command()
@click.option('--port', default=7860, type=int, help='Port for web interface')
@click.option('--share', is_flag=True, help='Create public link')
def gui(port, share):
    """Launch web GUI."""
    try:
        from face_search.gui import launch_gui
        click.echo(f"🎨 Launching GUI on http://localhost:{port}")
        if share:
            click.echo("   Creating public link...")
        launch_gui(port=port, share=share)
    except ImportError:
        click.echo("❌ GUI requires Gradio. Install with:", err=True)
        click.echo("   pip install face-search[gui]", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
