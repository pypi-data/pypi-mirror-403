"""Snapshot builder for generating formatted dependency reports."""
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import tiktoken

from .models import Node, SnapshotConfig, EntryPoint
from .graph import DependencyGraph


class SnapshotBuilder:
    """Builds formatted snapshot reports from dependency data."""

    def __init__(self, project_root: Path):
        """Initialize the snapshot builder.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root.resolve()
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def build_snapshot(
        self,
        graph: DependencyGraph,
        config: SnapshotConfig,
        entry_points: Optional[List[EntryPoint]] = None
    ) -> Dict[str, Any]:
        """Build a dependency snapshot.

        Args:
            graph: The dependency graph
            config: Snapshot configuration
            entry_points: Optional list of entry points for chain tracing

        Returns:
            Dictionary with 'content' and 'metrics' keys
        """
        target_path = self.project_root / config.target_path
        target_node = graph.get_node(target_path)

        if not target_node:
            return {"error": f"File not found: {config.target_path}"}

        output_parts: List[str] = []
        file_metrics: List[Dict[str, Any]] = []
        total_lines = 0

        # Get parents
        parent_nodes = []
        if config.parent_depth > 0:
            parent_nodes = graph.get_parents(target_node, config.parent_depth)

        # Get chains to entry points
        chains: Dict[str, Dict[str, Any]] = {}
        if config.include_chain and entry_points:
            chains = self._get_chains(graph, target_node, entry_points, config.chain_length)

        # Get children
        child_nodes = []
        child_tokens_used = 0
        excluded_paths = {
            self.project_root / p for p in config.excluded_children
        }

        if config.child_max_tokens > 0:
            selected, child_tokens_used = graph.get_children_with_token_limit(
                target_node, config.child_max_tokens
            )
            child_nodes = [n for n in selected if n.path not in excluded_paths]
        elif config.child_depth > 0:
            child_nodes = graph.get_children(target_node, config.child_depth)
            child_nodes = [n for n in child_nodes if n.path not in excluded_paths]
        else:
            child_nodes = graph.get_all_children_recursive(target_node)
            child_nodes = [n for n in child_nodes if n.path not in excluded_paths]

        # Get frontend children if requested
        frontend_nodes = []
        if config.include_frontend:
            frontend_nodes = self._get_frontend_children(
                graph, target_node, config.excluded_frontend
            )

        # Get extra files (manually selected from sidebar)
        extra_nodes = []
        if config.extra_files:
            for extra_path in config.extra_files:
                extra_full = self.project_root / extra_path
                extra_node = graph.get_node(extra_full)
                if extra_node:
                    extra_nodes.append(extra_node)

        # Build header
        header = self._build_header(
            target_node,
            parent_nodes,
            child_nodes,
            frontend_nodes,
            extra_nodes,
            chains,
            config
        )
        output_parts.append(header)

        # Add parent files
        if parent_nodes:
            output_parts.append("# " + "=" * 68)
            output_parts.append("# PARENT FILES")
            output_parts.append("# " + "=" * 68)
            output_parts.append("")

            for node in parent_nodes:
                content = self._read_file(node.path)
                total_lines += node.lines
                file_metrics.append({
                    "path": node.relative_path,
                    "lines": node.lines,
                    "type": "parent"
                })

                output_parts.append(
                    f"# --- START FILE: {node.relative_path} ({node.lines} lines) ---"
                )
                output_parts.append(content)
                output_parts.append(f"# --- END FILE: {node.relative_path} ---")
                output_parts.append("")

        # Add target file
        output_parts.append("# " + "=" * 68)
        output_parts.append("# TARGET FILE")
        output_parts.append("# " + "=" * 68)
        output_parts.append("")

        target_content = self._read_file(target_node.path)
        total_lines += target_node.lines
        file_metrics.append({
            "path": target_node.relative_path,
            "lines": target_node.lines,
            "type": "target"
        })

        output_parts.append(
            f"# --- START FILE: {target_node.relative_path} ({target_node.lines} lines) ---"
        )
        output_parts.append(target_content)
        output_parts.append(f"# --- END FILE: {target_node.relative_path} ---")
        output_parts.append("")

        # Add child files
        if child_nodes:
            output_parts.append("# " + "=" * 68)
            output_parts.append("# CHILD FILES (DEPENDENCIES)")
            output_parts.append("# " + "=" * 68)
            output_parts.append("")

            for node in child_nodes:
                content = self._read_file(node.path)
                total_lines += node.lines
                file_metrics.append({
                    "path": node.relative_path,
                    "lines": node.lines,
                    "type": "child"
                })

                output_parts.append(
                    f"# --- START FILE: {node.relative_path} ({node.lines} lines) ---"
                )
                output_parts.append(content)
                output_parts.append(f"# --- END FILE: {node.relative_path} ---")
                output_parts.append("")

        # Add frontend files
        if frontend_nodes:
            output_parts.append("# " + "=" * 68)
            output_parts.append("# FRONT-END FILES (HTML/JS/CSS)")
            output_parts.append("# " + "=" * 68)
            output_parts.append("")

            for node in frontend_nodes:
                content = self._read_file(node.path)
                total_lines += node.lines
                file_metrics.append({
                    "path": node.relative_path,
                    "lines": node.lines,
                    "type": "frontend"
                })

                output_parts.append(
                    f"# --- START FILE: {node.relative_path} ({node.lines} lines) ---"
                )
                output_parts.append(content)
                output_parts.append(f"# --- END FILE: {node.relative_path} ---")
                output_parts.append("")

        # Add extra files (manually selected from sidebar)
        if extra_nodes:
            output_parts.append("# " + "=" * 68)
            output_parts.append("# EXTRA FILES (MANUALLY SELECTED)")
            output_parts.append("# " + "=" * 68)
            output_parts.append("")

            for node in extra_nodes:
                content = self._read_file(node.path)
                total_lines += node.lines
                file_metrics.append({
                    "path": node.relative_path,
                    "lines": node.lines,
                    "type": "extra"
                })

                output_parts.append(
                    f"# --- START FILE: {node.relative_path} ({node.lines} lines) ---"
                )
                output_parts.append(content)
                output_parts.append(f"# --- END FILE: {node.relative_path} ---")
                output_parts.append("")

        # Build full content
        full_content = "\n".join(output_parts)
        token_count = self._count_tokens(full_content)

        # Add footer
        footer = self._build_footer(len(file_metrics), total_lines, token_count)
        full_content = full_content + "\n" + footer

        return {
            "content": full_content,
            "metrics": {
                "total_files": len(file_metrics),
                "total_lines": total_lines,
                "token_estimate": token_count,
                "files": file_metrics,
            }
        }

    def _build_header(
        self,
        target: Node,
        parents: List[Node],
        children: List[Node],
        frontend: List[Node],
        extra: List[Node],
        chains: Dict[str, Dict[str, Any]],
        config: SnapshotConfig
    ) -> str:
        """Build the snapshot header."""
        lines = []
        lines.append("=" * 70)
        lines.append("DEPENDENCY SNAPSHOT")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Target File: {target.relative_path}")
        lines.append(f"Parent Depth: {config.parent_depth} ({len(parents)} files)")

        if config.include_chain:
            lines.append(f"Chain to Entry Points: Yes ({len(chains)} chains)")

        child_info = f"Children: {len(children)} files"
        if config.child_max_tokens > 0:
            lines.append(child_info + f" (token limit: {config.child_max_tokens:,})")
        elif config.child_depth > 0:
            lines.append(child_info + f" (depth: {config.child_depth})")
        else:
            lines.append(child_info)

        if frontend:
            lines.append(f"Frontend Files: {len(frontend)} files")

        if extra:
            lines.append(f"Extra Files: {len(extra)} files")

        lines.append("")

        # List parents
        if parents:
            lines.append(f"PARENTS (depth {config.parent_depth}):")
            for p in parents:
                lines.append(f"  <- {p.relative_path} ({p.lines} lines)")
            lines.append("")

        # List chains
        if chains:
            lines.append("CHAINS TO ENTRY POINTS:")
            for label, info in chains.items():
                chain_str = " -> ".join(info["chain"])
                lines.append(f"  {info['emoji']} {label}: {chain_str}")
            lines.append("")

        # List children
        if children:
            lines.append("CHILDREN (recursive):")
            for c in children:
                lines.append(f"  -> {c.relative_path} ({c.lines} lines)")
            lines.append("")

        # List frontend
        if frontend:
            lines.append("FRONTEND FILES:")
            for f in frontend:
                lines.append(f"  -> {f.relative_path} ({f.lines} lines)")
            lines.append("")

        # List extra files
        if extra:
            lines.append("EXTRA FILES:")
            for e in extra:
                lines.append(f"  + {e.relative_path} ({e.lines} lines)")
            lines.append("")

        lines.append("=" * 70)
        lines.append("")

        return "\n".join(lines)

    def _build_footer(self, total_files: int, total_lines: int, token_count: int) -> str:
        """Build the snapshot footer."""
        lines = []
        lines.append("# " + "=" * 68)
        lines.append("# SNAPSHOT METRICS")
        lines.append("# " + "=" * 68)
        lines.append(f"# Total Files: {total_files}")
        lines.append(f"# Total Lines: {total_lines}")
        lines.append(f"# Estimated Tokens: ~{token_count:,}")
        lines.append("# " + "=" * 68)
        return "\n".join(lines)

    def _get_chains(
        self,
        graph: DependencyGraph,
        target: Node,
        entry_points: List[EntryPoint],
        max_length: Optional[int]
    ) -> Dict[str, Dict[str, Any]]:
        """Get chains from entry points to target."""
        chains = {}

        for ep in entry_points:
            if not ep.enabled:
                continue

            ep_path = self.project_root / ep.path
            ep_node = graph.get_node(ep_path)
            if not ep_node:
                continue

            # Trace from entry point
            _, connection_paths, _ = graph.trace_from_entry_point(ep_node)

            # Check if target is connected
            chain = graph.find_chain_to_entry_point(target, ep_node, connection_paths)
            if chain:
                if max_length and len(chain) > max_length + 1:
                    chain = chain[-(max_length + 1):]

                chains[ep.label] = {
                    "chain": chain,
                    "color": ep.color,
                    "emoji": ep.emoji,
                }

        return chains

    def _get_frontend_children(
        self,
        graph: DependencyGraph,
        target: Node,
        excluded: Set[str]
    ) -> List[Node]:
        """Get frontend file dependencies for a Python file."""
        frontend_nodes = []
        excluded_paths = {self.project_root / p for p in excluded}

        # Get all children
        all_children = graph.get_all_children_recursive(target)

        # Filter to frontend files
        for child in all_children:
            if child.node_type.value in ["html", "javascript", "typescript", "css"]:
                if child.path not in excluded_paths:
                    frontend_nodes.append(child)

        return frontend_nodes

    def _read_file(self, path: Path) -> str:
        """Read file content.

        Args:
            path: Path to file

        Returns:
            File content as string
        """
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return f"[Error reading file: {e}]"

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Token count
        """
        try:
            return len(self._encoding.encode(text))
        except Exception:
            return len(text.split())
