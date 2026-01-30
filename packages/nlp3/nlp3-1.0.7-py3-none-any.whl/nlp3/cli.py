"""CLI Interface for NLP3"""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree as RichTree
from typing import Optional, Any
from pathlib import Path
from datetime import datetime

from .core import TreeNavigator, TreeNode, NodeType
from .nlp import NLPEngine
from .adapters import FilesystemAdapter, JsonAdapter, YamlAdapter, HTMLAdapter, RESTAdapter, CodeTreeAdapter
from .adapters.universal_code_adapter import UniversalCodeAdapter
from .output.html import HTMLRenderer
from .output.yaml import YAMLRenderer
from .output.csv import CSVRenderer
from .output.markdown import MarkdownRenderer
from .output.xml import XMLRenderer
from .search import OptimizedSearchEngine, SearchQuery, SearchType


app = typer.Typer(help="NLP3 - Universal Context Navigator")
console = Console()

# Create search subcommand
search_app = typer.Typer(help="Optimized code search engine")
app.add_typer(search_app, name="search")


class TreeRenderer:
    """Render tree structures using Rich"""
    
    @staticmethod
    def render_table(nodes: list[TreeNode], title: str = "Results"):
        """Render results as a table"""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Size", justify="right", style="blue")
        table.add_column("Modified", style="yellow")
        table.add_column("Path", style="dim")
        
        for node in nodes:
            size_str = ""
            if hasattr(node, 'metadata') and node.metadata and hasattr(node.metadata, 'size'):
                size = node.metadata.size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024**2:
                    size_str = f"{size/1024:.1f}KB"
                elif size < 1024**3:
                    size_str = f"{size/1024**2:.1f}MB"
                else:
                    size_str = f"{size/1024**3:.1f}GB"
            
            modified_str = ""
            if hasattr(node, 'metadata') and node.metadata and hasattr(node.metadata, 'modified'):
                import datetime
                modified_str = datetime.datetime.fromtimestamp(node.metadata.modified).strftime("%Y-%m-%d %H:%M")
            
            table.add_row(
                node.name,
                getattr(node.node_type, 'value', 'unknown'),
                size_str,
                modified_str,
                getattr(node, 'path', 'unknown')
            )
        
        console.print(table)
    
    @staticmethod
    def render_tree(root_node: TreeNode, title: str = "Tree Structure"):
        """Render tree structure"""
        tree = RichTree(f"[bold blue]{title}[/bold blue]")
        
        def add_node(parent, node: TreeNode):
            # Create label for this node
            label = f"[cyan]{node.name}[/cyan]"
            if node.node_type == NodeType.LEAF:
                label += f" [dim]({node.node_type.value})[/dim]"
            
            # Add metadata
            if hasattr(node, 'metadata') and node.metadata and hasattr(node.metadata, 'size'):
                size = node.metadata.size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024**2:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size/1024**2:.1f}MB"
                label += f" [blue]{size_str}[/blue]"
            
            # Add to tree
            child = parent.add(label)
            
            # Add children
            children = node.children() if hasattr(node, 'children') and callable(node.children) else node.get_children()
            for child_node in children:
                add_node(child, child_node)
        
        add_node(tree, root_node)
        console.print(tree)


def create_navigator() -> TreeNavigator:
    """Create and configure TreeNavigator with adapters"""
    navigator = TreeNavigator()
    # Order matters - more specific adapters first
    navigator.register_adapter(UniversalCodeAdapter())  # Universal code parser (highest priority)
    navigator.register_adapter(CodeTreeAdapter())  # Code analysis adapter
    navigator.register_adapter(RESTAdapter())  # Most specific for URLs
    navigator.register_adapter(HTMLAdapter())  # HTML files
    navigator.register_adapter(JsonAdapter())  # JSON files
    navigator.register_adapter(YamlAdapter())  # YAML files
    navigator.register_adapter(FilesystemAdapter())  # Most generic, last
    return navigator


@app.command()
def query(
    query_text: str = typer.Argument(..., help="Natural language query"),
    source: str = typer.Argument(..., help="Data source (path, URL, etc.)"),
    format_output: str = typer.Option("table", "--format", "-f", help="Output format (table, tree, json, html, yaml, csv, markdown, xml, toon)"),
    preload: bool = typer.Option(False, "--preload", help="Preload all children"),
):
    """Execute natural language query on data source"""
    async def run_query():
        navigator = create_navigator()
        nlp_engine = NLPEngine()
        
        try:
            # Parse query
            parsed_query = nlp_engine.parse_query(query_text)
            # Only show parsed intent in debug mode or for specific formats
            if format_output in ["tree", "table"]:
                console.print(f"[dim]Parsed intent: {parsed_query.intent.type.value}[/dim]")
            
            # Determine source type
            # First try to parse as JSON, then check if it's a file path
            try:
                import json
                source_obj = json.loads(source)
            except (json.JSONDecodeError, TypeError):
                # Not valid JSON, check if it's a file path
                source_path = Path(source)
                if source_path.exists():
                    source_obj = source_path
                else:
                    source_obj = source
            
            # Execute query
            results = await navigator.query(query_text, source_obj, preload=preload)
            
            # Render results
            if format_output == "table":
                TreeRenderer.render_table(results, f"Query: '{query_text}'")
            elif format_output == "tree":
                if results:
                    TreeRenderer.render_tree(results[0], f"Query: '{query_text}'")
                else:
                    console.print("[yellow]No results found[/yellow]")
            elif format_output == "json":
                import json
                nodes = []
                for node in results:
                    node_metadata = {}
                    if hasattr(node, 'metadata') and node.metadata:
                        node_metadata = {
                            "size": getattr(node.metadata, 'size', 0),
                            "modified": getattr(node.metadata, 'modified', None),
                            "mime_type": getattr(node.metadata, 'mime_type', 'unknown'),
                        }
                    nodes.append({
                        "name": node.name,
                        "path": getattr(node, 'path', 'unknown'),
                        "type": getattr(node.node_type, 'value', 'unknown'),
                        "metadata": node_metadata
                    })
                output = {
                    "metadata": {
                        "query": query_text,
                        "total_results": len(nodes),
                        "timestamp": datetime.now().isoformat()
                    },
                    "nodes": nodes
                }
                console.print(json.dumps(output, indent=2))
            elif format_output == "html":
                html_content = HTMLRenderer.render_tree(results, f"Query: '{query_text}'")
                
                # Save to file
                output_file = f"nlp3_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                console.print(f"[green]HTML report saved to: {output_file}[/green]")
            
            elif format_output in ["yaml", "yml"]:
                yaml_content = YAMLRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(yaml_content)
            
            elif format_output == "csv":
                csv_content = CSVRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(csv_content)
            
            elif format_output in ["markdown", "md", "toon"]:
                md_content = MarkdownRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(md_content)
            
            elif format_output == "xml":
                xml_content = XMLRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(xml_content)
            
            else:
                console.print(f"[red]Unknown format: {format_output}[/red]")
                console.print("Available formats: table, tree, json, html, yaml, yml, csv, markdown, md, toon, xml")
                raise typer.Exit(1)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(run_query())


@app.command()
def explore(
    source: str = typer.Argument(..., help="Data source to explore"),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum depth to show"),
    format_output: str = typer.Option("tree", "--format", "-f", help="Output format (tree, table)"),
):
    """Explore data source structure"""
    async def run_explore():
        navigator = create_navigator()
        
        try:
            # Determine source type
            # First try to parse as JSON, then check if it's a file path
            try:
                import json
                source_obj = json.loads(source)
            except (json.JSONDecodeError, TypeError):
                # Not valid JSON, check if it's a file path
                source_path = Path(source)
                if source_path.exists():
                    source_obj = source_path
                else:
                    source_obj = source
            
            # Build tree
            adapter = navigator._find_adapter(source_obj)
            if not adapter:
                console.print(f"[red]No adapter found for source: {type(source_obj)}[/red]")
                raise typer.Exit(1)
            
            tree = await adapter.build_tree(source_obj, preload=True)
            
            # Render tree
            if format_output == "tree":
                TreeRenderer.render_tree(tree, f"Exploring: {source}")
            elif format_output == "table":
                # Collect all nodes up to specified depth
                def collect_nodes(node: TreeNode, current_depth: int = 0) -> list[TreeNode]:
                    if current_depth >= depth:
                        return [node]
                    nodes = [node]
                    for child in node.children():
                        nodes.extend(collect_nodes(child, current_depth + 1))
                    return nodes
                
                all_nodes = collect_nodes(tree)
                TreeRenderer.render_table(all_nodes, f"Exploring: {source}")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(run_explore())


@app.command()
def inspect(
    source: str = typer.Argument(..., help="Data source to inspect"),
    depth: int = typer.Option(3, "--depth", "-d", help="Inspection depth"),
):
    """Inspect data source structure and metadata"""
    async def run_inspect():
        navigator = create_navigator()
        
        try:
            # Determine source type
            try:
                import json
                source_obj = json.loads(source)
            except (json.JSONDecodeError, TypeError):
                # Not valid JSON, check if it's a file path
                source_path = Path(source)
                if source_path.exists():
                    source_obj = source_path
                else:
                    source_obj = source
            
            # Build tree
            adapter = navigator._find_adapter(source_obj)
            if not adapter:
                console.print(f"[red]No adapter found for source: {type(source_obj)}[/red]")
                raise typer.Exit(1)
            
            tree = await adapter.build_tree(source_obj, preload=True)
            
            # Show inspection info
            console.print(f"[bold blue]🔍 Inspecting: {source}[/bold blue]")
            console.print(f"[dim]Adapter: {type(adapter).__name__}[/dim]")
            console.print()
            
            # Tree structure
            def inspect_node(node: TreeNode, current_depth: int = 0):
                if current_depth >= depth:
                    return
                
                indent = "  " * current_depth
                
                # Node info
                node_info = f"{node.name} ({node.node_type.value})"
                if node.metadata.size:
                    size = node.metadata.size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024**2:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/1024**2:.1f}MB"
                    node_info += f" [dim]{size_str}[/dim]"
                
                console.print(f"{indent}📁 {node_info}")
                
                # Extra metadata
                if node.metadata.extra:
                    for key, value in node.metadata.extra.items():
                        if key in ['tag', 'type', 'class', 'id']:
                            console.print(f"{indent}   {key}: {value}")
                
                # Children count
                children = list(node.children())
                if children:
                    console.print(f"{indent}   └─ {len(children)} children")
                    
                    # Recursively inspect
                    for child in children[:5]:  # Limit to first 5 children
                        inspect_node(child, current_depth + 1)
                    
                    if len(children) > 5:
                        console.print(f"{indent}     ... and {len(children) - 5} more")
            
            inspect_node(tree)
            
            # Summary
            def count_nodes(node: TreeNode) -> int:
                count = 1
                for child in node.children():
                    count += count_nodes(child)
                return count
            
            total_nodes = count_nodes(tree)
            console.print()
            console.print(f"[bold]Summary:[/bold]")
            console.print(f"  Total nodes: {total_nodes}")
            console.print(f"  Tree depth: {depth}")
            console.print(f"  Root type: {tree.node_type.value}")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(run_inspect())


@app.command()
def parse(
    query_text: str = typer.Argument(..., help="Natural language query to parse"),
):
    """Parse and analyze natural language query"""
    nlp_engine = NLPEngine()
    
    try:
        parsed = nlp_engine.parse_query(query_text)
        
        console.print(f"[bold]Original:[/bold] {parsed.original}")
        console.print(f"[bold]Intent:[/bold] {parsed.intent.type.value} (confidence: {parsed.intent.confidence:.2f})")
        
        if parsed.intent.predicates:
            console.print("[bold]Predicates:[/bold]")
            for pred in parsed.intent.predicates:
                console.print(f"  • {pred.type.value} {pred.operator} {pred.value} (confidence: {pred.confidence:.2f})")
        
        if parsed.entities:
            console.print("[bold]Entities:[/bold]")
            for key, value in parsed.entities.items():
                console.print(f"  • {key}: {value}")
        
        console.print(f"[bold]Tokens:[/bold] {', '.join(parsed.tokens)}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# Search commands
@search_app.command()
def index(
    repository: str = typer.Argument(..., help="Path to repository to index"),
    force: bool = typer.Option(False, "--force", help="Force complete reindexing"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
):
    """Index repository for fast search"""
    try:
        console.print(f"🔍 Indexing repository: {repository}")
        
        engine = OptimizedSearchEngine(repository, index_dir)
        stats = engine.index_repository(force_reindex=force)
        
        console.print("✅ [bold green]Indexing completed![/bold green]")
        console.print(f"   📁 Files: {stats['total_files']}")
        console.print(f"   🌳 Nodes: {stats['total_nodes']}")
        console.print(f"   ⏱️  Time: {stats['total_time']:.2f}s")
        console.print(f"   🌐 Languages: {', '.join(stats['languages'].keys())}")
        
    except Exception as e:
        console.print(f"❌ [red]Indexing failed: {e}[/red]")
        raise typer.Exit(1)


@search_app.command()
def search_command(
    query: str = typer.Argument(..., help="Search query"),
    repository: Optional[str] = typer.Argument(None, help="Path to repository (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    node_types: Optional[list[str]] = typer.Option(None, "--node-types", help="Filter by node types"),
    languages: Optional[list[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[list[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Search in indexed repository"""
    try:
        import time
        import json
        
        repository_path = repository or "."
        
        engine = OptimizedSearchEngine(repository_path, index_dir)
        
        # Create search query
        search_query = SearchQuery(
            text=query,
            search_type=SearchType(search_type),
            node_types=node_types,
            languages=languages,
            file_patterns=file_patterns,
            limit=limit,
            min_score=min_score
        )
        
        start_time = time.time()
        results = engine.search(search_query)
        search_time = time.time() - start_time
        
        if not results:
            console.print(f"No results found for: [yellow]{query}[/yellow]")
            return
        
        if json_output:
            output = {
                "query": query,
                "search_time": search_time,
                "total_results": len(results),
                "results": [result.to_dict() for result in results]
            }
            print(json.dumps(output, indent=2))
        else:
            console.print(f"Results for '[cyan]{query}[/cyan]' ({len(results)} results, {search_time:.3f}s):")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                node = result.node
                score_text = f"{result.score:.3f}"
                
                console.print(f"{i:2d}. [{score_text}] [bold]{node.display_name}[/bold]")
                console.print(f"     🏷️  {node.node_type.value} | 🌐 {node.language.value}")
                console.print(f"     📄 {node.file_path}:{node.range.start.line if node.range else '?'}")
                
                if explain and result.explanation:
                    console.print(f"     💡 {result.explanation}")
                
                if result.matched_terms:
                    console.print(f"     🔍 Terms: {', '.join(result.matched_terms)}")
                
                if node.docstring:
                    doc_preview = node.docstring[:100] + "..." if len(node.docstring) > 100 else node.docstring
                    console.print(f"     📖 Doc: {doc_preview}")
                
                console.print()
        
    except Exception as e:
        console.print(f"❌ [red]Search failed: {e}[/red]")
        raise typer.Exit(1)


@search_app.command()
def update(
    repository: str = typer.Argument(..., help="Path to repository"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
):
    """Update index for changed files"""
    try:
        console.print(f"🔄 Updating index: {repository}")
        
        engine = OptimizedSearchEngine(repository, index_dir)
        stats = engine.update_index()
        
        if stats['updated_files'] == 0:
            console.print("✅ [green]No files changed, index up to date[/green]")
        else:
            console.print("✅ [bold green]Index updated![/bold green]")
            console.print(f"   📁 Files: {stats['updated_files']}")
            console.print(f"   🌳 Nodes: {stats['updated_nodes']}")
            console.print(f"   ⏱️  Time: {stats['time']:.2f}s")
        
    except Exception as e:
        console.print(f"❌ [red]Update failed: {e}[/red]")
        raise typer.Exit(1)


@search_app.command()
def stats(
    repository: str = typer.Argument(..., help="Path to repository"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Show repository statistics"""
    try:
        import json
        
        engine = OptimizedSearchEngine(repository, index_dir)
        stats = engine.get_statistics()
        
        if json_output:
            print(json.dumps(stats, indent=2))
        else:
            console.print(f"[bold]Repository Statistics:[/bold] {repository}")
            console.print("=" * 50)
            
            # Repository stats
            repo_stats = stats['repository']
            console.print(f"📁 Files: {repo_stats['total_files']}")
            console.print(f"🌳 Nodes: {repo_stats['total_nodes']}")
            console.print(f"🌐 Languages: {', '.join(repo_stats['language_distribution'].keys())}")
            
            # Node types
            if repo_stats['node_types']:
                console.print(f"\n[bold]Node Types:[/bold]")
                for node_type, count in sorted(repo_stats['node_types'].items()):
                    console.print(f"  {node_type}: {count}")
            
            # Index stats
            index_stats = stats['indexing']
            console.print(f"\n[bold]Index Sizes:[/bold]")
            console.print(f"  🔍 Text Index: {index_stats['text_index_size']['total_nodes']} nodes")
            console.print(f"  🧠 Vector Index: {index_stats['vector_index_size']['total_nodes']} nodes")
            console.print(f"  💾 AST Cache: {index_stats['ast_cache_size']['active_entries']} entries")
            console.print(f"  ⚡ Query Cache: {index_stats['query_cache_size']['active_entries']} entries")
            
            # Performance stats
            perf_stats = stats['performance']
            if perf_stats['cache_hit_rate'] > 0:
                console.print(f"\n[bold]Performance:[/bold]")
                console.print(f"  🎯 Cache Hit Rate: {perf_stats['cache_hit_rate']:.2%}")
        
    except Exception as e:
        console.print(f"❌ [red]Stats failed: {e}[/red]")
        raise typer.Exit(1)


@search_app.command()
def cleanup(
    repository: str = typer.Argument(..., help="Path to repository"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
):
    """Cleanup expired cache entries"""
    try:
        console.print(f"🧹 Cleaning up cache: {repository}")
        
        from .search.cache import CacheManager
        cache_manager = CacheManager(Path(index_dir))
        cache_manager.cleanup_all()
        
        console.print("✅ [bold green]Cache cleanup completed[/bold green]")
        
    except Exception as e:
        console.print(f"❌ [red]Cleanup failed: {e}[/red]")
        raise typer.Exit(1)


def main():
    """Main CLI entry point"""
    app()
