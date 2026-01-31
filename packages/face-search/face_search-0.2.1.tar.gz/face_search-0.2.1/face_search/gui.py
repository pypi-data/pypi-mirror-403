"""
Simple Gradio GUI for face-finder
"""

from pathlib import Path
from typing import List, Tuple, Dict, Optional
import json
import tempfile
import shutil
import numpy as np


# Labels file path
LABELS_FILE = Path(".face_labels.json")


def launch_gui(port: int = 7860, share: bool = False):
    """Launch the Gradio web interface."""
    try:
        import gradio as gr
    except ImportError:
        raise ImportError(
            "Gradio not installed. Install with: pip install face-search[gui]"
        )
    
    from face_search import FaceFinder
    
    # Global state
    state = {
        "finder": None,
        "matches": [],
        "ref_dir": None,
        "gallery_dir": None,
        "current_page": 0,
        "page_size": 50,  # Images per page
        "labels": {},  # name -> [embeddings]
        "text_matches": [],  # For filename search
        "selected_idx": None  # Currently selected image index
    }
    
    # Load saved labels
    def load_labels() -> Dict:
        if LABELS_FILE.exists():
            try:
                return json.loads(LABELS_FILE.read_text())
            except:
                pass
        return {}
    
    def save_labels(labels: Dict):
        LABELS_FILE.write_text(json.dumps(labels, indent=2))
    
    state["labels"] = load_labels()

    def update_status(msg: str, status: str = "info") -> str:
        icons = {"success": "✅", "error": "❌", "info": "ℹ️", "loading": "⏳"}
        return f"{icons.get(status, '•')} {msg}"
    
    def get_index_info() -> str:
        """Get current index information."""
        try:
            finder = FaceFinder()
            if finder.index_file.with_suffix('.faiss').exists():
                finder.load()
                state["finder"] = finder
                stats = finder.stats()
                sources = finder.index.get_sources()
                
                lines = [f"📊 Index: {stats.total_faces:,} faces from {stats.total_images:,} images"]
                if sources:
                    lines.append(f"\n📁 Sources ({len(sources)}):")
                    for src, info in sources.items():
                        count = info.get("count", 0)
                        lines.append(f"  • {src} ({count} faces)")
                return "\n".join(lines)
            return "ℹ️ No index found. Build one first."
        except Exception as e:
            return f"❌ Error loading index: {e}"

    def build_index(source_dir: str, detector: str, max_size: int, 
                    workers: int, incremental: bool, progress=gr.Progress()) -> str:
        """Build face index from photos."""
        if not source_dir:
            return update_status("Please enter a directory path", "error")
        
        source_path = Path(source_dir.strip())
        if not source_path.exists():
            return update_status(f"Directory not found: {source_dir}", "error")
        
        try:
            progress(0.1, desc="Starting...")
            state["finder"] = FaceFinder(min_confidence=0.3)
            
            progress(0.2, desc="Building index...")
            state["finder"].build(
                source_path,
                detector_name=detector,
                max_size=max_size if max_size > 0 else 0,
                workers=workers,
                incremental=incremental,
                show_progress=True
            )
            
            stats = state["finder"].stats()
            return update_status(
                f"Done! {stats.total_faces:,} faces from {stats.total_images:,} images",
                "success"
            )
        except Exception as e:
            return update_status(str(e), "error")

    def handle_reference_upload(files) -> Tuple[str, List]:
        """Handle reference file uploads."""
        if not files:
            return update_status("No files uploaded", "error"), []
        
        try:
            ref_dir = Path(tempfile.gettempdir()) / "face_search_refs"
            ref_dir.mkdir(exist_ok=True)
            
            for f in ref_dir.glob("*"):
                f.unlink()
            
            gallery_items = []
            for file_obj in files:
                file_path = Path(file_obj.name) if hasattr(file_obj, 'name') else Path(file_obj)
                if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}:
                    dest = ref_dir / file_path.name
                    shutil.copy2(file_path, dest)
                    gallery_items.append(str(dest))
            
            state["ref_dir"] = str(ref_dir)
            return update_status(f"{len(gallery_items)} photos loaded", "success"), gallery_items
        except Exception as e:
            return update_status(str(e), "error"), []

    def search_faces(threshold: float, strong_threshold: float, progress=gr.Progress()) -> Tuple[str, List]:
        """Search for matching faces."""
        if state["finder"] is None:
            try:
                state["finder"] = FaceFinder()
                state["finder"].load()
            except Exception:
                return update_status("No index found. Build one first.", "error"), []
        
        if not state["ref_dir"]:
            return update_status("Upload reference photos first.", "error"), []
        
        try:
            progress(0.3, desc="Loading references...")
            state["finder"].load_references(Path(state["ref_dir"]))
            
            # Check reference quality
            quality = state["finder"].check_reference_quality()
            warning_msg = ""
            if quality['warning']:
                warning_msg = f" {quality['warning']}"
            
            progress(0.5, desc="Searching...")
            top_k = state["finder"].stats().total_faces
            matches = state["finder"].search(
                threshold=threshold, 
                top_k=top_k,
                strong_match_threshold=strong_threshold
            )
            
            if not matches:
                return update_status("No matches found. Try higher threshold." + warning_msg, "info"), []
            
            state["matches"] = matches
            state["current_page"] = 0  # Reset to first page
            state["selected_idx"] = None  # Clear selection
            
            # Build gallery for first page
            gallery_items, page_info = build_gallery_page(0)
            
            msg = f"Found {len(matches)} matches! {page_info}{warning_msg}"
            return update_status(msg, "success"), gallery_items
        except Exception as e:
            return update_status(str(e), "error"), []

    def build_gallery_page(page: int) -> Tuple[List, str]:
        """Build gallery items for a specific page."""
        matches = state["matches"]
        if not matches:
            return [], ""
        
        page_size = state["page_size"]
        total_pages = (len(matches) + page_size - 1) // page_size
        page = max(0, min(page, total_pages - 1))
        state["current_page"] = page
        
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(matches))
        page_matches = matches[start_idx:end_idx]
        
        gallery_items = []
        try:
            # Clean up old gallery dir
            if state.get("gallery_dir"):
                shutil.rmtree(state["gallery_dir"], ignore_errors=True)
            temp_dir = Path(tempfile.mkdtemp(prefix="face_search_results_"))
            state["gallery_dir"] = str(temp_dir)
            
            for i, m in enumerate(page_matches):
                global_idx = start_idx + i
                if Path(m.file_path).exists():
                    dest = temp_dir / f"{global_idx:03d}_{m.distance:.3f}_{Path(m.file_path).name}"
                    shutil.copy2(m.file_path, dest)
                    label = f"#{global_idx+1} | d={m.distance:.3f}\n{m.file_name}"
                    gallery_items.append((str(dest), label))
        except Exception:
            pass
        
        page_info = f"Page {page+1}/{total_pages}"
        return gallery_items, page_info

    def go_prev_page() -> Tuple[str, str, List]:
        """Go to previous page."""
        if not state["matches"]:
            return update_status("No results yet.", "info"), "Page 1", []
        new_page = max(0, state["current_page"] - 1)
        gallery_items, page_info = build_gallery_page(new_page)
        return update_status(f"{len(state['matches'])} matches", "success"), page_info, gallery_items

    def go_next_page() -> Tuple[str, str, List]:
        """Go to next page."""
        if not state["matches"]:
            return update_status("No results yet.", "info"), "Page 1", []
        total_pages = (len(state["matches"]) + state["page_size"] - 1) // state["page_size"]
        new_page = min(total_pages - 1, state["current_page"] + 1)
        gallery_items, page_info = build_gallery_page(new_page)
        return update_status(f"{len(state['matches'])} matches", "success"), page_info, gallery_items

    def on_image_select(evt: gr.SelectData) -> str:
        """Track selected image when clicked."""
        if not state["matches"]:
            return "No selection"
        
        page = state["current_page"]
        page_size = state["page_size"]
        global_idx = page * page_size + evt.index
        
        if 0 <= global_idx < len(state["matches"]):
            state["selected_idx"] = global_idx
            m = state["matches"][global_idx]
            return f"Selected #{global_idx + 1}: {m.file_name} (dist: {m.distance:.3f})"
        return "No selection"

    def remove_selected_image() -> Tuple[str, str, List]:
        """Remove the currently selected image from results."""
        if not state["matches"]:
            return update_status("No results.", "info"), "Page 1", []
        
        if state["selected_idx"] is None:
            return update_status("Click an image first to select it.", "error"), f"Page {state['current_page']+1}", build_gallery_page(state["current_page"])[0]
        
        global_idx = state["selected_idx"]
        page_size = state["page_size"]
        
        if 0 <= global_idx < len(state["matches"]):
            removed = state["matches"].pop(global_idx)
            state["selected_idx"] = None  # Clear selection
            
            # Adjust page if needed
            if state["matches"]:
                total_pages = (len(state["matches"]) + page_size - 1) // page_size
                if state["current_page"] >= total_pages:
                    state["current_page"] = max(0, total_pages - 1)
                
                gallery_items, page_info = build_gallery_page(state["current_page"])
                return update_status(f"Removed '{removed.file_name}'. {len(state['matches'])} left", "success"), page_info, gallery_items
            else:
                return update_status("All removed.", "info"), "Page 0", []
        
        return update_status("Could not remove.", "error"), f"Page {state['current_page']+1}", []

    def go_to_page(page_num: int) -> Tuple[str, List]:
        """Go to specific page (1-indexed for UI)."""
        if not state["matches"]:
            return update_status("No results yet.", "info"), []
        gallery_items, page_info = build_gallery_page(int(page_num) - 1)
        return update_status(f"Found {len(state['matches'])} matches! {page_info}", "success"), gallery_items

    def export_results() -> str:
        """Export all match paths as TXT."""
        if not state["matches"]:
            return "No results to export."
        return "\n".join(m.file_path for m in state["matches"])

    def export_json() -> str:
        """Export all matches as JSON with distances."""
        if not state["matches"]:
            return "[]"
        data = [
            {
                "path": m.file_path,
                "name": m.file_name,
                "distance": round(m.distance, 4)
            }
            for m in state["matches"]
        ]
        return json.dumps(data, indent=2)

    def export_copy_cmd() -> str:
        """Generate copy command for all matches."""
        if not state["matches"]:
            return "# No results"
        
        import shlex
        output_dir = "./face_matches"
        lines = [f"mkdir -p {shlex.quote(output_dir)}"]
        
        for m in state["matches"]:
            lines.append(f"cp {shlex.quote(m.file_path)} {shlex.quote(output_dir)}/")
        
        return "\n".join(lines)

    # ============ FILENAME SEARCH ============
    def search_by_filename(query: str) -> Tuple[str, List]:
        """Search indexed photos by filename/path. Case-insensitive, partial match."""
        if state["finder"] is None:
            try:
                state["finder"] = FaceFinder()
                state["finder"].load()
            except Exception:
                return update_status("No index found. Build one first.", "error"), []
        
        if not query.strip():
            return update_status("Enter a search term", "info"), []
        
        # Split query into terms (space or comma separated)
        query_terms = [t.strip().lower() for t in query.replace(",", " ").split() if t.strip()]
        
        # Get all unique files from index
        seen_files = set()
        matches = []
        for meta in state["finder"].index.metadata:
            file_path = meta['file_path']
            if file_path in seen_files:
                continue
            seen_files.add(file_path)
            
            # Check if ALL query terms match (case-insensitive, partial)
            path_lower = file_path.lower()
            if all(term in path_lower for term in query_terms):
                from .models import SearchResult
                matches.append(SearchResult(
                    file_path=file_path,
                    file_name=meta['file_name'],
                    distance=0.0,
                    face_index=meta.get('face_index', 0)
                ))
        
        if not matches:
            return update_status(f"No files matching '{query}'", "info"), []
        
        state["text_matches"] = matches
        state["matches"] = matches
        state["current_page"] = 0
        
        gallery_items, page_info = build_gallery_page(0)
        return update_status(f"Found {len(matches)} files matching '{query}' {page_info}", "success"), gallery_items

    def use_text_results_as_refs(threshold: float, strong_threshold: float, progress=gr.Progress()) -> Tuple[str, List]:
        """Use current text search results as reference faces and search."""
        if not state.get("text_matches"):
            return update_status("Do a text search first to get results", "error"), []
        
        if state["finder"] is None:
            return update_status("No index found. Build one first.", "error"), []
        
        try:
            progress(0.2, desc="Loading embeddings from text results...")
            
            # Get embeddings for faces in text search results
            ref_embs = []
            ref_names = []
            
            for m in state["text_matches"][:20]:  # Limit to first 20 results
                # Find embedding in index - match BOTH file_path AND face_index
                for idx, meta in enumerate(state["finder"].index.metadata):
                    if meta['file_path'] == m.file_path and meta.get('face_index', 0) == m.face_index:
                        emb = state["finder"].index.index.reconstruct(idx)
                        ref_embs.append(emb)
                        ref_names.append(m.file_name)
                        break
            
            if not ref_embs:
                return update_status("No face embeddings found in text results", "error"), []
            
            # Set as references
            state["finder"].ref_embeddings = ref_embs
            state["finder"].ref_names = ref_names
            
            progress(0.5, desc="Searching...")
            top_k = state["finder"].stats().total_faces
            matches = state["finder"].search(
                threshold=threshold,
                top_k=top_k,
                strong_match_threshold=strong_threshold
            )
            
            if not matches:
                return update_status("No matches found.", "info"), []
            
            state["matches"] = matches
            state["current_page"] = 0
            
            gallery_items, page_info = build_gallery_page(0)
            msg = f"Found {len(matches)} matches using {len(ref_embs)} refs from text search! {page_info}"
            return update_status(msg, "success"), gallery_items
        except Exception as e:
            return update_status(str(e), "error"), []

    # ============ FACE LABELING ============
    def get_labels_list() -> str:
        """Get list of saved labels."""
        if not state["labels"]:
            return "No labels saved yet."
        lines = ["**Saved Labels:**"]
        for name, embs in state["labels"].items():
            lines.append(f"• **{name}** ({len(embs)} embeddings)")
        return "\n".join(lines)

    def save_current_as_label(label_name: str, threshold: float) -> str:
        """Save matches from current results as a named label using the search threshold."""
        if not label_name.strip():
            return update_status("Enter a label name", "error")
        
        if state["finder"] is None:
            return update_status("No index loaded", "error")
        
        if not state["matches"]:
            return update_status("Do a search first to get matches", "error")
        
        name = label_name.strip()
        
        # Use the current threshold setting (what user sees as results)
        save_threshold = threshold
        matches_to_save = [m for m in state["matches"] if m.distance <= save_threshold]
        
        if not matches_to_save:
            return update_status(f"No matches below threshold ({save_threshold:.2f})", "error")
        
        # Limit to best 15 matches
        matches_to_save = matches_to_save[:15]
        
        # Get embeddings for matches
        embeddings = []
        for m in matches_to_save:
            for idx, meta in enumerate(state["finder"].index.metadata):
                if meta['file_path'] == m.file_path and meta.get('face_index', 0) == m.face_index:
                    emb = state["finder"].index.index.reconstruct(idx)
                    embeddings.append(emb.tolist())
                    break
        
        if not embeddings:
            return update_status("Could not extract embeddings from matches", "error")
        
        # REPLACE existing label (don't append - avoids corruption)
        state["labels"][name] = embeddings
        
        save_labels(state["labels"])
        return update_status(f"Saved {len(embeddings)} matches as '{name}' (dist < {save_threshold:.2f})", "success")

    def search_by_label(label_names: str, threshold: float, use_context: bool = True, 
                        progress=gr.Progress()) -> Tuple[str, List]:
        """
        Search using saved labels as reference embeddings.
        
        Uses a smart selection of representative embeddings (not all) to avoid
        overly broad searches. Supports intersection with comma separation.
        """
        if state["finder"] is None:
            try:
                state["finder"] = FaceFinder()
                state["finder"].load()
            except Exception:
                return update_status("No index found. Build one first.", "error"), []
        
        if not label_names.strip():
            return update_status("Enter label name(s)", "error"), []
        
        # Parse label names (comma separated for intersection)
        input_names = [n.strip() for n in label_names.split(",") if n.strip()]
        
        # Case-insensitive label lookup
        labels_lower = {k.lower(): k for k in state["labels"].keys()}
        names = []
        for input_name in input_names:
            actual_name = labels_lower.get(input_name.lower())
            if actual_name is None:
                available = ", ".join(state["labels"].keys()) or "none"
                return update_status(f"Label '{input_name}' not found. Available: {available}", "error"), []
            names.append(actual_name)
        
        progress(0.2, desc="Loading label embeddings...")
        
        def select_representative_embeddings(all_embs: List[np.ndarray], max_refs: int = 5) -> List[np.ndarray]:
            """
            Select representative embeddings to avoid overly broad search.
            Uses simple clustering: pick diverse samples that cover the embedding space.
            """
            if len(all_embs) <= max_refs:
                return all_embs
            
            # Start with the first embedding (usually a good one)
            selected = [all_embs[0]]
            selected_indices = {0}
            
            # Greedily add the most different embeddings
            while len(selected) < max_refs:
                best_idx = -1
                best_min_dist = -1
                
                for i, emb in enumerate(all_embs):
                    if i in selected_indices:
                        continue
                    # Find minimum distance to any selected embedding
                    min_dist = min(np.linalg.norm(emb - s) for s in selected)
                    if min_dist > best_min_dist:
                        best_min_dist = min_dist
                        best_idx = i
                
                if best_idx >= 0:
                    selected.append(all_embs[best_idx])
                    selected_indices.add(best_idx)
                else:
                    break
            
            return selected
        
        # If single label, do normal search
        if len(names) == 1:
            all_embs = [np.array(e) for e in state["labels"][names[0]]]
            
            # Select representative subset (max 5) to avoid overly broad search
            embs = select_representative_embeddings(all_embs, max_refs=5)
            
            state["finder"].ref_embeddings = embs
            state["finder"].ref_names = [names[0]] * len(embs)
            
            top_k = min(500, state["finder"].stats().total_faces)  # Limit results
            
            progress(0.5, desc=f"Searching with {len(embs)} refs...")
            
            # Use regular search (hybrid matching already handles multiple refs well)
            matches = state["finder"].search(threshold=threshold, top_k=top_k)
            
            if not matches:
                return update_status(f"No matches for '{names[0]}'", "info"), []
            
            state["matches"] = matches
            state["current_page"] = 0
            gallery_items, page_info = build_gallery_page(0)
            return update_status(f"Found {len(matches)} matches for '{names[0]}' (using {len(embs)}/{len(all_embs)} refs) {page_info}", "success"), gallery_items
        
        # Multiple labels = intersection (find photos with ALL people)
        progress(0.3, desc=f"Searching for {len(names)} people...")
        all_match_sets = []
        for i, name in enumerate(names):
            all_embs = [np.array(e) for e in state["labels"][name]]
            embs = select_representative_embeddings(all_embs, max_refs=5)
            
            state["finder"].ref_embeddings = embs
            state["finder"].ref_names = [name] * len(embs)
            
            top_k = min(500, state["finder"].stats().total_faces)
            matches = state["finder"].search(threshold=threshold, top_k=top_k)
            match_paths = {m.file_path for m in matches}
            all_match_sets.append((name, match_paths, {m.file_path: m for m in matches}))
            progress(0.3 + 0.5 * (i + 1) / len(names), desc=f"Searched {name}...")
        
        # Find intersection
        intersection = all_match_sets[0][1]
        for _, paths, _ in all_match_sets[1:]:
            intersection = intersection & paths
        
        if not intersection:
            return update_status(f"No photos contain ALL: {', '.join(names)}", "info"), []
        
        # Build result list from intersection
        matches = [all_match_sets[0][2][p] for p in intersection]
        matches.sort(key=lambda x: x.distance)
        
        state["matches"] = matches
        state["current_page"] = 0
        gallery_items, page_info = build_gallery_page(0)
        return update_status(f"Found {len(matches)} photos with ALL: {', '.join(names)} {page_info}", "success"), gallery_items

    def delete_label(label_name: str) -> Tuple[str, str]:
        """Delete a saved label (case-insensitive)."""
        input_name = label_name.strip()
        # Case-insensitive lookup
        labels_lower = {k.lower(): k for k in state["labels"].keys()}
        name = labels_lower.get(input_name.lower())
        if name is None:
            return update_status(f"Label '{input_name}' not found", "error"), get_labels_list()
        
        del state["labels"][name]
        save_labels(state["labels"])
        return update_status(f"Deleted label '{name}'", "success"), get_labels_list()

    def clear_all_labels() -> Tuple[str, str]:
        """Delete ALL saved labels - start fresh."""
        count = len(state["labels"])
        state["labels"] = {}
        save_labels(state["labels"])
        return update_status(f"Cleared all {count} labels", "success"), get_labels_list()

    def find_companions(label_name: str, min_count: int = 2) -> str:
        """Find people who frequently appear with a labeled person (case-insensitive)."""
        if state["finder"] is None:
            try:
                state["finder"] = FaceFinder()
                state["finder"].load()
            except Exception:
                return "❌ No index found. Build one first."
        
        if not state["finder"].cooccurrence_tracker:
            return "❌ Co-occurrence tracking not available. Rebuild index."
        
        input_name = label_name.strip()
        if not input_name:
            return "Enter a label name"
        
        # Case-insensitive lookup
        labels_lower = {k.lower(): k for k in state["labels"].keys()}
        name = labels_lower.get(input_name.lower())
        if name is None:
            available = ", ".join(state["labels"].keys()) or "none"
            return f"❌ Label '{input_name}' not found. Available: {available}"
        
        # Get embedding for this label
        embs = [np.array(e) for e in state["labels"][name]]
        if not embs:
            return f"❌ No embeddings for '{name}'"
        
        # Find companions
        companions = state["finder"].get_companions(embs[0], min_count=min_count)
        
        if not companions:
            return f"No frequent companions found for '{name}'. Try lower min count or add more photos."
        
        # Format results
        lines = [f"**People who frequently appear with '{name}':**\n"]
        for cluster_id, count in companions[:10]:  # Top 10
            # Try to find a label for this cluster
            cluster_label = None
            for other_name, other_embs in state["labels"].items():
                if other_name == name:
                    continue
                for emb in other_embs:
                    cid, dist = state["finder"].cooccurrence_tracker.get_cluster_for_embedding(np.array(emb))
                    if cid == cluster_id and dist < 0.4:
                        cluster_label = other_name
                        break
                if cluster_label:
                    break
            
            if cluster_label:
                lines.append(f"• **{cluster_label}** - seen together {count}x")
            else:
                lines.append(f"• Unknown (cluster #{cluster_id}) - seen together {count}x")
        
        return "\n".join(lines)

    def get_cooccurrence_stats() -> str:
        """Get co-occurrence graph statistics."""
        if state["finder"] is None:
            try:
                state["finder"] = FaceFinder()
                state["finder"].load()
            except Exception:
                return "No index loaded."
        
        if not state["finder"].cooccurrence_tracker:
            return "Co-occurrence tracking not enabled or data not available."
        
        stats = state["finder"].cooccurrence_tracker.stats()
        
        if stats['total_clusters'] == 0:
            return "**⚠️ No co-occurrence data yet.**\n\nClick 'Build Co-occurrence' below to analyze which faces appear together."
        
        lines = [
            "**📊 Co-occurrence Statistics:**",
            f"• Total face clusters: {stats['total_clusters']}",
            f"• Images with multiple faces: {stats['total_images']}",
            f"• Unique co-occurring pairs: {stats['unique_pairs']}",
            f"• Total co-occurrences: {stats['total_cooccurrences']}",
            f"• Avg faces per multi-face image: {stats['avg_faces_per_image']:.1f}",
        ]
        
        if stats['top_pairs']:
            lines.append("\n**Top co-occurring pairs:**")
            for (c1, c2), count in stats['top_pairs'][:5]:
                lines.append(f"  Cluster {c1} ↔ Cluster {c2}: {count}x")
        
        return "\n".join(lines)

    def build_cooccurrence_data(progress=gr.Progress()) -> str:
        """Build co-occurrence data from existing index."""
        if state["finder"] is None:
            try:
                state["finder"] = FaceFinder()
                state["finder"].load()
            except Exception:
                return "❌ No index found. Build one first."
        
        if state["finder"].index.size() == 0:
            return "❌ Index is empty. Build index first."
        
        progress(0.1, desc="Initializing...")
        
        # Ensure tracker exists
        if not state["finder"].cooccurrence_tracker:
            from .cooccurrence import CooccurrenceTracker
            state["finder"].cooccurrence_tracker = CooccurrenceTracker(cluster_threshold=0.4)
        
        progress(0.2, desc="Building co-occurrence graph...")
        
        try:
            state["finder"]._build_cooccurrence_data(show_progress=True)
            state["finder"].save()  # Save the co-occurrence data
            
            stats = state["finder"].cooccurrence_tracker.stats()
            return f"✅ Built co-occurrence graph!\n\n• {stats['total_clusters']} face clusters\n• {stats['unique_pairs']} co-occurring pairs\n• {stats['total_images']} images with multiple faces"
        except Exception as e:
            return f"❌ Error: {e}"

    # ============ BUILD UI ============
    css = """
    .header { text-align: center; margin-bottom: 20px; }
    .header h1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 font-size: 2.5em; margin: 0; font-weight: 800; }
    .results-header { align-items: center; margin-bottom: 5px; }
    """
    
    with gr.Blocks(title="face-finder", theme=gr.themes.Soft(), css=css) as app:
        gr.HTML('<div class="header"><h1>🔍 face-finder</h1></div>')
        
        with gr.Tabs():
            # ============ TAB 1: MAIN SEARCH (combined) ============
            with gr.TabItem("🔍 Search"):
                with gr.Row():
                    # LEFT PANEL - Controls
                    with gr.Column(scale=1):
                        # 1. PRIMARY INPUT (Reference Images)
                        gr.Markdown("### 1. Who to find?")
                        ref_upload = gr.File(
                            label="Upload Photos (Drag & Drop)",
                            file_count="multiple",
                            file_types=["image"],
                            height=100,
                            min_width=100
                        )
                        ref_gallery = gr.Gallery(
                            label="Reference Faces",
                            columns=4, rows=1, height=120,
                            object_fit="cover", preview=False, show_label=False,
                            allow_preview=False
                        )
                        ref_status = gr.Textbox(show_label=False, interactive=False, container=False, text_align="center")
                        
                        # 2. SEARCH BUTTON (Prominent)
                        search_btn = gr.Button("🔍 FIND FACES", variant="primary", size="lg")
                        search_status = gr.Textbox(show_label=False, interactive=False, lines=2, placeholder="Ready to search...")

                        # 3. ADVANCED SETTINGS (Collapsed by default)
                        with gr.Accordion("⚙️ Sensitivity Settings", open=False):
                            gr.Markdown("Adjust how strict the match should be.")
                            threshold_input = gr.Slider(0.05, 0.8, value=0.50, step=0.01, label="Overall Threshold (Lower = Stricter)")
                            strong_threshold_input = gr.Slider(0.1, 0.4, value=0.18, step=0.01, label="Strict 'Sniper' Match")

                        # 4. ALTERNATIVE SEARCH METHODS (Collapsed)
                        with gr.Accordion("📝 Search by Name / Text", open=False):
                            gr.Markdown("**Label Search**")
                            with gr.Row():
                                label_search_input = gr.Textbox(placeholder="e.g. John, Mary", show_label=False, scale=3)
                                label_search_btn = gr.Button("🔍", scale=1)
                            
                            gr.Markdown("**Filename Search**")
                            with gr.Row():
                                filename_query = gr.Textbox(placeholder="e.g. 'holiday 2024'", show_label=False, scale=3)
                                filename_search_btn = gr.Button("🔍", scale=1)

                    # RIGHT PANEL - Results
                    with gr.Column(scale=3):
                        # Results Header & Tools
                        with gr.Row(elem_classes="results-header"):
                            gr.Markdown("### 2. Results")
                            with gr.Column(scale=2):
                                pass # Spacer
                            with gr.Column(scale=1):
                                selected_display = gr.Textbox(placeholder="Click image to select...", show_label=False, interactive=False, max_lines=1)
                            with gr.Column(scale=0):
                                remove_btn = gr.Button("🗑️ Remove", variant="stop", size="sm")

                        # The Main Gallery
                        results_gallery = gr.Gallery(
                            label="Matches",
                            columns=6, rows=4, height=600,
                            object_fit="contain", preview=True, show_label=True
                        )
                        
                        # Pagination & Actions Footer
                        with gr.Row():
                            prev_btn = gr.Button("◀ Prev Page", size="sm")
                            page_info_display = gr.Textbox(value="Page 0/0", show_label=False, interactive=False, text_align="center", scale=2)
                            next_btn = gr.Button("Next Page ▶", size="sm")
                        
                        gr.Markdown("---")
                        
                        # Post-Search Actions
                        with gr.Row():
                            with gr.Column(scale=1):
                                gr.Markdown("**Save Selection as Label**")
                                with gr.Row():
                                    label_name_input = gr.Textbox(placeholder="Enter Name...", show_label=False, scale=2)
                                    save_label_btn = gr.Button("💾 Save", scale=1)
                            
                            with gr.Column(scale=1):
                                gr.Markdown("**Refine Search**")
                                use_as_refs_btn = gr.Button("↩️ Use These Results as New Refs", size="sm")
                
                # Wire up search tab events
                ref_upload.change(handle_reference_upload, inputs=[ref_upload], outputs=[ref_status, ref_gallery])
                search_btn.click(search_faces, inputs=[threshold_input, strong_threshold_input], outputs=[search_status, results_gallery])
                label_search_btn.click(search_by_label, inputs=[label_search_input, threshold_input], outputs=[search_status, results_gallery])
                label_search_input.submit(search_by_label, inputs=[label_search_input, threshold_input], outputs=[search_status, results_gallery])
                filename_search_btn.click(search_by_filename, inputs=[filename_query], outputs=[search_status, results_gallery])
                filename_query.submit(search_by_filename, inputs=[filename_query], outputs=[search_status, results_gallery])
                use_as_refs_btn.click(use_text_results_as_refs, inputs=[threshold_input, strong_threshold_input], outputs=[search_status, results_gallery])
                save_label_btn.click(save_current_as_label, inputs=[label_name_input, threshold_input], outputs=[search_status])
                prev_btn.click(go_prev_page, outputs=[search_status, page_info_display, results_gallery])
                next_btn.click(go_next_page, outputs=[search_status, page_info_display, results_gallery])
                results_gallery.select(on_image_select, outputs=[selected_display])
                remove_btn.click(remove_selected_image, outputs=[search_status, page_info_display, results_gallery])
            
            # ============ TAB 2: EXPORT ============
            with gr.TabItem("📤 Export"):
                gr.Markdown("### Export Search Results")
                with gr.Row():
                    with gr.Column():
                        export_btn = gr.Button("📄 Export Paths", variant="primary")
                        paths_output = gr.Textbox(label="Paths (one per line)", lines=12, interactive=True)
                    with gr.Column():
                        json_btn = gr.Button("📋 Export JSON", variant="primary")
                        json_output = gr.Textbox(label="JSON", lines=12, interactive=True)
                    with gr.Column():
                        cmd_btn = gr.Button("💻 Shell Command", variant="primary")
                        cmd_output = gr.Code(language="shell", label="Copy files", lines=12)
                
                export_btn.click(export_results, outputs=[paths_output])
                json_btn.click(export_json, outputs=[json_output])
                cmd_btn.click(export_copy_cmd, outputs=[cmd_output])
            
            # ============ TAB 3: LABELS ============
            with gr.TabItem("🏷️ Labels"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📋 Saved Labels")
                        labels_display = gr.Markdown(get_labels_list())
                        refresh_labels_btn = gr.Button("🔄 Refresh", size="sm")
                        gr.Markdown("---")
                        delete_label_input = gr.Textbox(label="Delete Label", placeholder="Enter name to delete")
                        with gr.Row():
                            delete_label_btn = gr.Button("🗑️ Delete", variant="secondary", scale=2)
                            clear_all_btn = gr.Button("🗑️ Clear All", variant="stop", scale=1)
                        delete_status = gr.Textbox(label="Status", interactive=False, lines=1)
                    
                    with gr.Column(scale=2):
                        gr.Markdown("""
                        ### 💡 How to Use Labels
                        
                        **Step 1: Create a Label**
                        1. Upload reference photos of a person
                        2. Click "🔍 FIND FACES" to search
                        3. Review results - make sure top matches are correct
                        4. Enter a name and click "💾 Save"
                        
                        **Step 2: Search by Label**
                        - Type the name in "Label Search" box on Search tab
                        - Finds ALL photos of that person in your library
                        - Use comma for multiple: `John, Mary` = photos with BOTH
                        
                        **Tips:**
                        - Only very close matches (dist < 0.15) are saved
                        - Better reference photos = better results
                        - Re-save a label to replace it (doesn't append)
                        """)
                
                refresh_labels_btn.click(lambda: get_labels_list(), outputs=[labels_display])
                delete_label_btn.click(delete_label, inputs=[delete_label_input], outputs=[delete_status, labels_display])
                clear_all_btn.click(clear_all_labels, outputs=[delete_status, labels_display])
            
            # ============ TAB 4: INDEX (collapsed) ============
            with gr.TabItem("⚙️ Index"):
                gr.Markdown("### 📊 Index Management")
                gr.Markdown("*Build once, search forever. Only rebuild when adding new photos.*")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        index_info = gr.Textbox(label="Current Index", lines=8, interactive=False)
                        refresh_index_btn = gr.Button("🔄 Refresh", size="sm")
                    
                    with gr.Column(scale=1):
                        with gr.Accordion("🔨 Build New Index", open=False):
                            source_input = gr.Textbox(label="Photo Directory", placeholder="/Users/you/Photos", lines=1)
                            with gr.Row():
                                detector_input = gr.Dropdown(choices=["opencv", "ssd", "mtcnn", "retinaface"], value="opencv", label="Detector")
                                workers_input = gr.Slider(1, 8, value=4, step=1, label="Workers")
                            size_input = gr.Slider(0, 2048, value=1280, step=128, label="Max Size (0=full)")
                            incremental_input = gr.Checkbox(value=True, label="➕ Add to existing")
                            build_btn = gr.Button("🔨 Build", variant="primary", size="lg")
                            build_output = gr.Textbox(label="Status", interactive=False, lines=2)
                
                build_btn.click(build_index, inputs=[source_input, detector_input, size_input, workers_input, incremental_input], outputs=[build_output])
                refresh_index_btn.click(get_index_info, outputs=[index_info])
        
        gr.HTML('<p style="text-align:center;color:#888;font-size:11px;margin-top:10px;">🔍 face-finder • AGPL-3.0</p>')
        app.load(get_index_info, outputs=[index_info])
    
    app.launch(server_port=port, share=share)


if __name__ == "__main__":
    launch_gui()
