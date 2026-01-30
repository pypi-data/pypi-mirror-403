# -*- coding: utf-8 -*-
"""
FocusTree - Generates a dependency-aware tree of focused files.

This shows how focused files are connected via imports/dependencies
rather than just their filesystem location.
"""

from typing import List, Set, Dict, Any, Optional
from pathlib import Path

# Box-drawing characters
PIPE = "\u2502"      # │
ELBOW = "\u2514"     # └
TEE = "\u251c"       # ├
DASH = "\u2500"      # ─


class FocusTree:
    """Generates a dependency-aware tree for focused files."""

    def __init__(self, prism_session):
        """
        Args:
            prism_session: A PrismSession instance (local or remote)
        """
        self.session = prism_session
        self.project_root = Path(prism_session.project_root)

    def generate(self, focused_abs_paths: Set[str]) -> str:
        """
        Generate a dependency tree for the focused files.
        
        Args:
            focused_abs_paths: Set of absolute paths currently in focus
        """
        if not focused_abs_paths:
            return "(No files currently focused)"

        # 1. Convert absolute paths to relative paths as used in Prism
        focused_rel_paths = set()
        for abs_p in focused_abs_paths:
            try:
                rel = str(Path(abs_p).relative_to(self.project_root))
                focused_rel_paths.add(rel)
            except ValueError:
                # Path not under project root, skip
                continue

        if not focused_rel_paths:
            return "(Focused files are outside project root)"

        # 2. Get the dependency graph for all focused files
        # We build a adjacency list for only focused files
        adj = {}
        for rel_path in focused_rel_paths:
            adj[rel_path] = []
            
            # Get children (imports) for this file
            node = self.session.graph.get_node(self.project_root / rel_path)
            if node:
                # We only care about children that are ALSO focused
                children = self.session.graph.get_children(node, depth=1)
                for child in children:
                    child_rel = child.relative_path
                    if child_rel in focused_rel_paths:
                        adj[rel_path].append(child_rel)

        # 3. Find "roots" (files that aren't imported by any other focused file)
        # and "orphans" (files that don't import any other focused file)
        all_children = set()
        for children in adj.values():
            all_children.update(children)
        
        roots = sorted([path for path in focused_rel_paths if path not in all_children])
        
        # If every focused file imports something else (cycle), just pick the first one
        if not roots and focused_rel_paths:
            roots = [sorted(list(focused_rel_paths))[0]]

        # 4. Render the tree
        lines = ["FOCUS DEPENDENCY TREE", "====================="]
        
        seen = set()

        def render_node(node_path: str, prefix: str = "", is_last: bool = True):
            if node_path in seen:
                # Avoid infinite loops for circular deps
                connector = ELBOW + DASH + DASH + " " if is_last else TEE + DASH + DASH + " "
                lines.append(f"{prefix}{connector}{node_path} (already shown)")
                return
            
            seen.add(node_path)
            
            connector = ELBOW + DASH + DASH + " " if is_last else TEE + DASH + DASH + " "
            lines.append(f"{prefix}{connector}{node_path}")
            
            new_prefix = prefix + ("    " if is_last else PIPE + "   ")
            children = sorted(adj.get(node_path, []))
            
            for i, child in enumerate(children):
                render_node(child, new_prefix, i == len(children) - 1)

        for i, root in enumerate(roots):
            render_node(root, is_last=(i == len(roots) - 1))

        # 5. Add any focused files that were missed (shouldn't happen with roots logic but just in case)
        remaining = focused_rel_paths - seen
        if remaining:
            lines.append("\nUNCONNECTED / OTHER:")
            for path in sorted(list(remaining)):
                lines.append(f"  {path}")

        return "\n".join(lines)
