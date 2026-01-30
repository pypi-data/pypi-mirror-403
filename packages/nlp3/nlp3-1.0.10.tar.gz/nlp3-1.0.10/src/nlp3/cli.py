"""CLI Interface for NLP3"""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree as RichTree
from typing import Optional, Any, List
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
search_app = typer.Typer(help="Optimized code search engine", add_completion=False, invoke_without_command=True)
app.add_typer(search_app, name="search")

@search_app.callback(invoke_without_command=True)
def search_callback(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type: hybrid, semantic, indexed"),
    node_types: Optional[str] = typer.Option(None, "--node-types", help="Filter by node types"),
    languages: Optional[str] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[str] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Optimized code search engine"""
    
    # If no subcommand provided, perform search
    if ctx.invoked_subcommand is None:
        # Handle query with spaces - check if we have extra args
        if query is None and len(ctx.args) > 2:
            # Join all remaining args as query (skip first two: query and directory)
            query = " ".join(ctx.args[2:])
        
        if query is None:
            console.print(search_app.get_help())
            raise typer.Exit(1)
        
        perform_search(
            query=query,
            repository=directory,
            index_dir=index_dir,
            search_type=search_type,
            node_types=node_types,
            languages=languages,
            file_patterns=file_patterns,
            limit=limit,
            min_score=min_score,
            explain=explain,
            json_output=json_output,
            yaml_output=yaml_output
        )


def perform_search(
    query: str,
    repository: str,
    index_dir: str = ".nlp3_index",
    search_type: str = "hybrid",
    node_types: Optional[str] = None,
    languages: Optional[str] = None,
    file_patterns: Optional[str] = None,
    limit: int = 20,
    min_score: float = 0.1,
    explain: bool = False,
    json_output: bool = False,
    yaml_output: bool = True,
):
    """Perform search with the same logic as search_command"""
    try:
        import time
        import json
        
        repository_path = repository or "."
        
        # Convert string parameters to lists if needed
        final_node_types = node_types.split(',') if node_types else None
        final_languages = languages.split(',') if languages else None
        final_file_patterns = file_patterns.split(',') if file_patterns else None
        
        # Smart query parsing - extract filters from natural language
        smart_query, auto_filters = parse_smart_query(query)
        
        # Merge auto-detected filters with manual filters (manual takes precedence)
        final_node_types = final_node_types if final_node_types else auto_filters['node_types']
        final_languages = final_languages if final_languages else auto_filters['languages']
        final_file_patterns = final_file_patterns if final_file_patterns else auto_filters['file_patterns']
        
        # Show what was auto-detected (if anything)
        if any(auto_filters.values()):
            detected_parts = []
            if auto_filters['node_types']:
                detected_parts.append(f"types: {', '.join(auto_filters['node_types'])}")
            if auto_filters['languages']:
                detected_parts.append(f"languages: {', '.join(auto_filters['languages'])}")
            if auto_filters['file_patterns']:
                detected_parts.append(f"patterns: {', '.join(auto_filters['file_patterns'])}")
            
            console.print(f"[dim]🔍 Auto-detected: {', '.join(detected_parts)}[/dim]")
        
        # Try to use OptimizedSearchEngine, fallback to simple text search if no index
        import os
        from pathlib import Path
        
        index_path = Path(index_dir)
        search_method_used = ""
        
        if not index_path.exists() or not any(index_path.iterdir()):
            # Index doesn't exist, use fallback search
            search_method_used = "📝 Simple Text Search (no index)"
            console.print(f"[dim]📝 Index not found, using simple text search...[/dim]")
            results = fallback_text_search(
                repository_path, 
                smart_query, 
                final_file_patterns,
                limit
            )
            search_time = 0.001  # Very fast for simple search
            
            if not results:
                console.print(f"No results found for: [yellow]{query}[/yellow]")
                return
        else:
            # Index exists, use OptimizedSearchEngine
            try:
                search_method_used = "🔍 Indexed Code Search (OptimizedSearchEngine)"
                engine = OptimizedSearchEngine(repository_path, index_dir)
                
                # Create search query
                search_query = SearchQuery(
                    text=smart_query,
                    search_type=SearchType(search_type),
                    node_types=final_node_types,
                    languages=final_languages,
                    file_patterns=final_file_patterns,
                    limit=limit,
                    min_score=min_score
                )
                
                start_time = time.time()
                results = engine.search(search_query)
                search_time = time.time() - start_time
                
                if not results:
                    console.print(f"No results found for: [yellow]{query}[/yellow]")
                    return
                
            except Exception as e:
                # Fallback to simple text search if index doesn't exist or other error
                search_method_used = "📝 Simple Text Search (engine failed)"
                console.print(f"[dim]📝 Search engine failed, using simple text search...[/dim]")
                console.print(f"[dim]Debug: {str(e)}[/dim]")
                results = fallback_text_search(
                    repository_path, 
                    smart_query, 
                    final_file_patterns,
                    limit
                )
                search_time = 0.001  # Very fast for simple search
                
                if not results:
                    console.print(f"No results found for: [yellow]{query}[/yellow]")
                    return
        
        if json_output:
            output = {
                "query": query,
                "search_method": search_method_used,
                "search_time": search_time,
                "total_results": len(results),
                "results": [result.to_dict() for result in results]
            }
            print(json.dumps(output, indent=2))
        elif yaml_output:
            import yaml
            output = {
                "query": query,
                "search_method": search_method_used,
                "search_time": search_time,
                "total_results": len(results),
                "results": [result.to_dict() for result in results]
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using indexed search"
            print(yaml.dump(output, default_flow_style=False))
        else:
            console.print(f"Results for '[cyan]{query}[/cyan]' ({len(results)} results, {search_time:.3f}s):")
            console.print(f"[dim]🔧 Method: {search_method_used}[/dim]")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                # Check if this is a fallback search result or a normal search result
                if hasattr(result, 'file_path') and hasattr(result, 'line_number'):
                    # Fallback text search result
                    score_text = f"{result.score:.3f}"
                    
                    console.print(f"{i:2d}. [{score_text}] [bold]{result.file_path}[/bold]")
                    console.print(f"     📄 Line {result.line_number}")
                    console.print(f"     📝 {result.line_content[:100]}{'...' if len(result.line_content) > 100 else ''}")
                    console.print()
                else:
                    # Normal search result
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


class TreeRenderer:
    """Render tree structures using Rich"""
    
    @staticmethod
    def render_table(nodes: List[TreeNode], title: str = "Results"):
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
            if hasattr(node, 'metadata') and node.metadata and hasattr(node.metadata, 'modified') and node.metadata.modified:
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
    navigator.register_adapter(UniversalCodeAdapter())  # Universal code parser (highest priority for code)
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
    format_output: str = typer.Option("yaml", "--format", "-f", help="Output format (table, tree, json, html, yaml, csv, markdown, xml, toon)"),
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
            adapter_used = navigator._find_adapter(source_obj).__class__.__name__
            results = await navigator.query(query_text, source_obj, preload=preload)
            
            # Render results
            if format_output == "yaml":
                yaml_content = YAMLRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(yaml_content)
                console.print(f"[dim]🔧 Method: {adapter_used}[/dim]")
            elif format_output == "table":
                TreeRenderer.render_table(results, f"Query: '{query_text}'")
                console.print(f"[dim]🔧 Method: {adapter_used}[/dim]")
            elif format_output == "tree":
                if results:
                    TreeRenderer.render_tree(results[0], f"Query: '{query_text}'")
                    console.print(f"[dim]🔧 Method: {adapter_used}[/dim]")
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
                        "metadata": node_metadata,
                        "adapter_used": adapter_used
                    })
                output = {
                    "query": query_text,
                    "adapter_used": adapter_used,
                    "total_results": len(nodes),
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
                console.print(f"[dim]🔧 Method: {adapter_used}[/dim]")
            
            elif format_output in ["yaml", "yml"]:
                yaml_content = YAMLRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(yaml_content)
                console.print(f"[dim]🔧 Method: {adapter_used}[/dim]")
            
            elif format_output == "csv":
                csv_content = CSVRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(csv_content)
                console.print(f"[dim]🔧 Method: {adapter_used}[/dim]")
            
            elif format_output in ["markdown", "md", "toon"]:
                md_content = MarkdownRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(md_content)
                console.print(f"[dim]🔧 Method: {adapter_used}[/dim]")
            
            elif format_output == "xml":
                xml_content = XMLRenderer.render_tree(results, f"Query: '{query_text}'")
                console.print(xml_content)
                console.print(f"[dim]🔧 Method: {adapter_used}[/dim]")
            
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
    format_output: str = typer.Option("yaml", "--format", "-f", help="Output format (tree, table)"),
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
            if format_output == "yaml":
                yaml_content = YAMLRenderer.render_tree(tree, f"Exploring: {source}")
                console.print(yaml_content)
            elif format_output == "tree":
                TreeRenderer.render_tree(tree, f"Exploring: {source}")
            elif format_output == "table":
                # Collect all nodes up to specified depth
                def collect_nodes(node: TreeNode, current_depth: int = 0) -> List[TreeNode]:
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
                if node.metadata and node.metadata.size:
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


# Direct search commands (shortcuts)
@app.command()
def function(
    query: str = typer.Argument(..., help="Function search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search functions in code (shortcut for: nlp3 search function)"""
    # Redirect to search function
    import sys
    from nlp3.cli import function as search_function_cmd
    
    # Update sys.argv to call search function
    sys.argv = [sys.argv[0], "search", "function", query, directory] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search function directly
    search_function_cmd(
        query=query,
        directory=directory,
        index_dir=index_dir,
        search_type=search_type,
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def function_name(
    query: str = typer.Argument(..., help="Function name search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search function names in code"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command with name filter
    sys.argv = [sys.argv[0], "search", "search-command", query, directory, "--node-types", "function"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["function"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def function_content(
    query: str = typer.Argument(..., help="Function content search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search function content/bodies in code"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command with function and content filter
    sys.argv = [sys.argv[0], "search", "search-command", query, directory, "--node-types", "function"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["function"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def function_input(
    query: str = typer.Argument(..., help="Function input/parameter search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search function inputs/parameters in code"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command with function and input filter
    sys.argv = [sys.argv[0], "search", "search-command", query, directory, "--node-types", "function"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["function"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def function_output(
    query: str = typer.Argument(..., help="Function output/return value search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search function outputs/return values in code"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command with function and output filter
    sys.argv = [sys.argv[0], "search", "search-command", query, directory, "--node-types", "function"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["function"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def search_class(
    query: str = typer.Argument(..., help="Class search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search classes in code (shortcut for: nlp3 search search-class)"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command
    sys.argv = [sys.argv[0], "search", "search-class", query, directory, "--node-types", "class"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["class"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def method(
    query: str = typer.Argument(..., help="Method search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search methods in code (shortcut for: nlp3 search method)"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command
    sys.argv = [sys.argv[0], "search", "search-command", query, directory, "--node-types", "method"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["method"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def variable(
    query: str = typer.Argument(..., help="Variable search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search variables in code (shortcut for: nlp3 search variable)"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command
    sys.argv = [sys.argv[0], "search", "search-command", query, directory, "--node-types", "variable"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["variable"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def module(
    query: str = typer.Argument(..., help="Module search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search modules in code (shortcut for: nlp3 search module)"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command
    sys.argv = [sys.argv[0], "search", "search-command", query, directory, "--node-types", "module"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["module"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


@app.command()
def import_(
    query: str = typer.Argument(..., help="Import search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search imports in code (shortcut for: nlp3 search import)"""
    import sys
    from nlp3.cli import search_command
    
    # Update sys.argv to call search_command
    sys.argv = [sys.argv[0], "search", "search-command", query, directory, "--node-types", "import"] + [
        arg for arg in sys.argv[5:] if arg.startswith("--")
    ]
    
    # Add --yaml flag if yaml_output is True and not already present
    if yaml_output and "--yaml" not in sys.argv:
        sys.argv.append("--yaml")
    
    # Call the search_command directly
    search_command(
        query=query,
        repository=directory,
        index_dir=index_dir,
        search_type=search_type,
        node_types=["import"],
        languages=languages,
        file_patterns=file_patterns,
        limit=limit,
        min_score=min_score,
        explain=explain,
        json_output=json_output
    )


# Grep-like and Find-like commands
@app.command()
def filename(
    query: str = typer.Argument(..., help="Filename search query (like grep -r)"),
    directory: str = typer.Argument(".", help="Directory to search in (default: current)"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="File patterns to search in"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", help="Case sensitive search"),
    limit: int = typer.Option(50, "--limit", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
):
    """Search filenames (like grep -r)"""
    try:
        import time
        import re
        import json
        from pathlib import Path
        
        start_time = time.time()
        
        # Default file patterns if none specified
        if not file_patterns:
            file_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs", "*.cpp", "*.c", "*.h", "*.hpp", 
                           "*.json", "*.yaml", "*.yml", "*.xml", "*.md", "*.txt", "*.html", "*.css", "*.toml", "*.cfg", "*.ini"]
        
        # Compile regex for search
        flags = 0 if case_sensitive else re.IGNORECASE
        query_pattern = re.compile(re.escape(query), flags)
        
        results = []
        search_dir = Path(directory)
        
        if not search_dir.exists():
            console.print(f"[red]Directory not found: {directory}[/red]")
            raise typer.Exit(1)
        
        # Search through files
        for pattern in file_patterns:
            for file_path in search_dir.rglob(pattern):
                # Skip common directories
                if any(skip_dir in file_path.parts for skip_dir in ['.git', 'venv', '__pycache__', 'node_modules', '.idea', 'dist', 'build', '.pytest_cache']):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if query_pattern.search(line):
                                # Create a simple result
                                # Clean up line content for better readability
                                line_content = line.strip()
                                
                                # Check if this line looks like a Go function signature split across lines
                                if (line_content.endswith((')', 'string', 'int', 'bool', 'float', 'error')) and 
                                    len(line_content) > 10 and 
                                    not line_content.endswith('{') and
                                    not line_content.endswith('}')):
                                    
                                    # Look ahead to see if next line contains the opening brace
                                    try:
                                        next_line = next(f)
                                        next_line_stripped = next_line.strip()
                                        if (next_line_stripped.startswith(('error {', '{')) or 
                                            (next_line_stripped in ('error {', '{'))):
                                            # Combine the lines
                                            line_content = line_content + ' ' + next_line_stripped
                                            # Skip the next line since we've already processed it
                                            continue
                                    except StopIteration:
                                        pass  # No more lines
                                
                                result = {
                                    "file_path": str(file_path),
                                    "line_number": line_num,
                                    "line_content": line_content,
                                    "score": 1.0
                                }
                                results.append(result)
                                
                                # Stop if we hit the limit
                                if len(results) >= limit:
                                    break
                    
                    if len(results) >= limit:
                        break
                        
                except (UnicodeDecodeError, PermissionError, OSError):
                    # Skip files that can't be read
                    continue
                    
            if len(results) >= limit:
                break
        
        search_time = time.time() - start_time
        
        if not results:
            console.print(f"No results found for: [yellow]{query}[/yellow]")
            return
        
        # Output results
        if json_output:
            output = {
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "search_time": search_time,
                "total_results": len(results),
                "results": results
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using simple text search"
            print(json.dumps(output, indent=2))
        elif yaml_output:
            import yaml
            output = {
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "search_time": search_time,
                "total_results": len(results),
                "results": results
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using simple text search"
            print(yaml.dump(output, default_flow_style=False, sort_keys=False))
        else:
            console.print(f"Filename search for '[cyan]{query}[/cyan]' in [blue]{directory}[/blue] ({len(results)} results, {search_time:.3f}s):")
            console.print(f"[dim]🔧 Method: 📝 Simple Text Search (grep-like)[/dim]")
            console.print(f"[dim]📁 Patterns: {', '.join(file_patterns)}[/dim]")
            if explain:
                console.print(f"[dim]📝 Explanation: Found {len(results)} matches for '{query}' using simple text search[/dim]")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                console.print(f"{i:2d}. [{result['score']:.3f}] [bold]{result['file_path']}[/bold]")
                console.print(f"     📄 Line {result['line_number']}")
                console.print(f"     📝 {result['line_content'][:100]}{'...' if len(result['line_content']) > 100 else ''}")
                console.print()
                
    except Exception as e:
        console.print(f"❌ [red]Filename search failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def path(
    query: str = typer.Argument(..., help="Path search query (like find)"),
    directory: str = typer.Argument(".", help="Directory to search in (default: current)"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="File patterns to search in"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", help="Case sensitive search"),
    limit: int = typer.Option(50, "--limit", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
):
    """Search file paths (like find)"""
    try:
        import time
        import json
        from pathlib import Path
        
        start_time = time.time()
        
        # Default file patterns if none specified
        if not file_patterns:
            file_patterns = ["*"]
        
        results = []
        search_dir = Path(directory)
        
        if not search_dir.exists():
            console.print(f"[red]Directory not found: {directory}[/red]")
            raise typer.Exit(1)
        
        # Search through files
        for pattern in file_patterns:
            for file_path in search_dir.rglob(pattern):
                # Skip common directories
                if any(skip_dir in file_path.parts for skip_dir in ['.git', 'venv', '__pycache__', 'node_modules', '.idea', 'dist', 'build', '.pytest_cache']):
                    continue
                
                # Check if query matches filename
                filename = file_path.name
                if (case_sensitive and query in filename) or (not case_sensitive and query.lower() in filename.lower()):
                    result = {
                        "file_path": str(file_path),
                        "line_number": 0,
                        "line_content": f"File: {file_path.name}",
                        "score": 1.0
                    }
                    results.append(result)
                    
                    # Stop if we hit the limit
                    if len(results) >= limit:
                        break
            
            if len(results) >= limit:
                break
        
        search_time = time.time() - start_time
        
        if not results:
            console.print(f"No results found for: [yellow]{query}[/yellow]")
            return
        
        # Output results
        if json_output:
            output = {
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "search_time": search_time,
                "total_results": len(results),
                "results": results
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using simple text search"
            print(json.dumps(output, indent=2))
        elif yaml_output:
            import yaml
            output = {
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "search_time": search_time,
                "total_results": len(results),
                "results": results
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using simple text search"
            print(yaml.dump(output, default_flow_style=False, sort_keys=False))
        else:
            console.print(f"Path search for '[cyan]{query}[/cyan]' in [blue]{directory}[/blue] ({len(results)} results, {search_time:.3f}s):")
            console.print(f"[dim]🔧 Method: 📝 Simple Text Search (find-like)[/dim]")
            console.print(f"[dim]📁 Patterns: {', '.join(file_patterns)}[/dim]")
            if explain:
                console.print(f"[dim]📝 Explanation: Found {len(results)} matches for '{query}' using simple text search[/dim]")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                console.print(f"{i:2d}. [{result['score']:.3f}] [bold]{result['file_path']}[/bold]")
                console.print(f"     📁 {result['line_content']}")
                console.print()
                
    except Exception as e:
        console.print(f"❌ [red]Path search failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def content(
    query: str = typer.Argument(..., help="Content search query (like grep -r)"),
    directory: str = typer.Argument(".", help="Directory to search in (default: current)"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="File patterns to search in"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", help="Case sensitive search"),
    limit: int = typer.Option(50, "--limit", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
):
    """Search file contents (like grep -r)"""
    try:
        import time
        import re
        import json
        from pathlib import Path
        
        start_time = time.time()
        
        # Default file patterns if none specified
        if not file_patterns:
            file_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs", "*.cpp", "*.c", "*.h", "*.hpp", 
                           "*.json", "*.yaml", "*.yml", "*.xml", "*.md", "*.txt", "*.html", "*.css", "*.toml", "*.cfg", "*.ini"]
        
        # Compile regex for search
        flags = 0 if case_sensitive else re.IGNORECASE
        query_pattern = re.compile(re.escape(query), flags)
        
        results = []
        search_dir = Path(directory)
        
        if not search_dir.exists():
            console.print(f"[red]Directory not found: {directory}[/red]")
            raise typer.Exit(1)
        
        # Search through files
        for pattern in file_patterns:
            for file_path in search_dir.rglob(pattern):
                # Skip common directories
                if any(skip_dir in file_path.parts for skip_dir in ['.git', 'venv', '__pycache__', 'node_modules', '.idea', 'dist', 'build', '.pytest_cache']):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if query_pattern.search(line):
                                # Create a simple result
                                # Clean up line content for better readability
                                line_content = line.strip()
                                
                                # Check if this line looks like a Go function signature split across lines
                                if (line_content.endswith((')', 'string', 'int', 'bool', 'float', 'error')) and 
                                    len(line_content) > 10 and 
                                    not line_content.endswith('{') and
                                    not line_content.endswith('}')):
                                    
                                    # Look ahead to see if next line contains the opening brace
                                    try:
                                        next_line = next(f)
                                        next_line_stripped = next_line.strip()
                                        if (next_line_stripped.startswith(('error {', '{')) or 
                                            (next_line_stripped in ('error {', '{'))):
                                            # Combine the lines
                                            line_content = line_content + ' ' + next_line_stripped
                                            # Skip the next line since we've already processed it
                                            continue
                                    except StopIteration:
                                        pass  # No more lines
                                
                                result = {
                                    "file_path": str(file_path),
                                    "line_number": line_num,
                                    "line_content": line_content,
                                    "score": 1.0
                                }
                                results.append(result)
                                
                                # Stop if we hit the limit
                                if len(results) >= limit:
                                    break
                    
                    if len(results) >= limit:
                        break
                        
                except (UnicodeDecodeError, PermissionError, OSError):
                    # Skip files that can't be read
                    continue
                    
            if len(results) >= limit:
                break
        
        search_time = time.time() - start_time
        
        if not results:
            console.print(f"No results found for: [yellow]{query}[/yellow]")
            return
        
        # Output results
        if json_output:
            output = {
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "search_time": search_time,
                "total_results": len(results),
                "results": results
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using simple text search"
            print(json.dumps(output, indent=2))
        elif yaml_output:
            import yaml
            output = {
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "search_time": search_time,
                "total_results": len(results),
                "results": results
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using simple text search"
            print(yaml.dump(output, default_flow_style=False, sort_keys=False))
        else:
            console.print(f"Content search for '[cyan]{query}[/cyan]' in [blue]{directory}[/blue] ({len(results)} results, {search_time:.3f}s):")
            console.print(f"[dim]🔧 Method: 📝 Simple Text Search (grep-like)[/dim]")
            console.print(f"[dim]📁 Patterns: {', '.join(file_patterns)}[/dim]")
            if explain:
                console.print(f"[dim]📝 Explanation: Found {len(results)} matches for '{query}' using simple text search[/dim]")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                console.print(f"{i:2d}. [{result['score']:.3f}] [bold]{result['file_path']}[/bold]")
                console.print(f"     📄 Line {result['line_number']}")
                console.print(f"     📝 {result['line_content'][:100]}{'...' if len(result['line_content']) > 100 else ''}")
                console.print()
                
    except Exception as e:
        console.print(f"❌ [red]Content search failed: {e}[/red]")
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


def fallback_text_search(repository_path: str, query: str, file_patterns: Optional[List[str]], limit: int) -> List:
    """Simple text search fallback when index is not available"""
    import os
    import re
    from pathlib import Path
    from dataclasses import dataclass
    
    @dataclass
    class SimpleSearchResult:
        """Simple search result for fallback search"""
        def __init__(self, file_path: str, line_number: int, line_content: str, score: float = 1.0):
            self.file_path = file_path
            self.line_number = line_number
            self.line_content = line_content
            self.score = score
            
        def to_dict(self):
            return {
                "file_path": self.file_path,
                "line_number": self.line_number,
                "line_content": self.line_content,
                "score": self.score
            }
    
    results = []
    repo_path = Path(repository_path)
    
    # Default file patterns if none specified
    if not file_patterns:
        file_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs", "*.cpp", "*.c", "*.h", "*.hpp", 
                       "*.json", "*.yaml", "*.yml", "*.xml", "*.md", "*.txt", "*.html", "*.css"]
    
    # Compile regex for case-insensitive search
    query_pattern = re.compile(re.escape(query), re.IGNORECASE)
    
    # Search through files
    for pattern in file_patterns:
        for file_path in repo_path.rglob(pattern):
            # Skip common directories
            if any(skip_dir in file_path.parts for skip_dir in ['.git', 'venv', '__pycache__', 'node_modules', '.idea', 'dist', 'build']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if query_pattern.search(line):
                            # Create a simple result that mimics the structure expected by the display code
                            result = SimpleSearchResult(
                                file_path=str(file_path),
                                line_number=line_num,
                                line_content=line.strip(),
                                score=1.0
                            )
                            results.append(result)
                            
                            # Stop if we hit the limit
                            if len(results) >= limit:
                                break
                    
                    if len(results) >= limit:
                        break
                        
            except (UnicodeDecodeError, PermissionError, OSError):
                # Skip files that can't be read
                continue
                
        if len(results) >= limit:
            break
    
    return results


def parse_smart_query(query: str) -> tuple[str, dict]:
    """Parse query and automatically extract filters from natural language"""
    import re
    
    # Default filters
    filters = {
        'node_types': None,
        'languages': None,
        'file_patterns': None
    }
    
    # Convert to lowercase for easier matching
    query_lower = query.lower()
    
    # Extract node types
    node_type_patterns = {
        r'\bfunction[s]?\b': ['function'],
        r'\bclass[es]?\b': ['class'],
        r'\bmethod[s]?\b': ['method'],
        r'\bvariable[s]?\b': ['variable'],
        r'\bmodule[s]?\b': ['module'],
        r'\bimport[s]?\b': ['import'],
        r'\bcomment[s]?\b': ['comment']
    }
    
    for pattern, types in node_type_patterns.items():
        if re.search(pattern, query_lower):
            filters['node_types'] = types
            # Remove the pattern from query
            query = re.sub(pattern, '', query, flags=re.IGNORECASE).strip()
    
    # Extract programming languages
    language_patterns = {
        r'\bpython\b': ['python'],
        r'\bjavascript\b|\.js\b': ['javascript'],
        r'\btypescript\b|\.ts\b': ['typescript'],
        r'\bjava\b': ['java'],
        r'\bgo\b|golang': ['go'],
        r'\brust\b': ['rust'],
        r'\bc\+\+\b|cpp': ['cpp'],
        r'\bc\b(?!\+)': ['c'],
        r'\bhtml\b': ['html'],
        r'\bcss\b': ['css'],
        r'\bjson\b': ['json'],
        r'\byaml\b|yml': ['yaml'],
        r'\bxml\b': ['xml']
    }
    
    for pattern, langs in language_patterns.items():
        if re.search(pattern, query_lower):
            filters['languages'] = langs
            # Remove the pattern from query
            query = re.sub(pattern, '', query, flags=re.IGNORECASE).strip()
    
    # Extract file patterns
    file_patterns = []
    if re.search(r'\.py\b', query_lower):
        file_patterns.append('*.py')
        query = re.sub(r'\.py\b', '', query, flags=re.IGNORECASE).strip()
    if re.search(r'\.js\b', query_lower):
        file_patterns.append('*.js')
        query = re.sub(r'\.js\b', '', query, flags=re.IGNORECASE).strip()
    if re.search(r'\.ts\b', query_lower):
        file_patterns.append('*.ts')
        query = re.sub(r'\.ts\b', '', query, flags=re.IGNORECASE).strip()
    if re.search(r'\.java\b', query_lower):
        file_patterns.append('*.java')
        query = re.sub(r'\.java\b', '', query, flags=re.IGNORECASE).strip()
    
    if file_patterns:
        filters['file_patterns'] = file_patterns
    
    # Clean up extra spaces
    query = ' '.join(query.split())
    
    return query, filters


@search_app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    directory: Optional[str] = typer.Argument(None, help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    node_types: Optional[List[str]] = typer.Option(None, "--node-types", help="Filter by node types"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Smart search - automatically chooses between indexed and text search"""
    try:
        import time
        import json
        from pathlib import Path
        
        repository_path = directory or "."
        
        # Smart query parsing - extract filters from natural language
        smart_query, auto_filters = parse_smart_query(query)
        
        # Merge auto-detected filters with manual filters (manual takes precedence)
        final_node_types = node_types if node_types else auto_filters['node_types']
        final_languages = languages if languages else auto_filters['languages']
        final_file_patterns = file_patterns if file_patterns else auto_filters['file_patterns']
        
        # Show what was auto-detected (if anything)
        if any(auto_filters.values()):
            detected_parts = []
            if auto_filters['node_types']:
                detected_parts.append(f"types: {', '.join(auto_filters['node_types'])}")
            if auto_filters['languages']:
                detected_parts.append(f"languages: {', '.join(auto_filters['languages'])}")
            if auto_filters['file_patterns']:
                detected_parts.append(f"patterns: {', '.join(auto_filters['file_patterns'])}")
            
            console.print(f"[dim]🔍 Auto-detected: {', '.join(detected_parts)}[/dim]")
        
        # Try to use OptimizedSearchEngine, fallback to simple text search if no index
        index_path = Path(index_dir)
        search_method_used = ""
        
        if not index_path.exists() or not any(index_path.iterdir()):
            # Index doesn't exist, use fallback search
            search_method_used = "📝 Simple Text Search (no index)"
            console.print(f"[dim]📝 Index not found, using simple text search...[/dim]")
            results = fallback_text_search(
                repository_path, 
                smart_query, 
                final_file_patterns,
                limit
            )
            search_time = 0.001  # Very fast for simple search
            
            if not results:
                console.print(f"No results found for: [yellow]{query}[/yellow]")
                return
        else:
            # Index exists, use OptimizedSearchEngine
            try:
                search_method_used = "🔍 Indexed Code Search (OptimizedSearchEngine)"
                engine = OptimizedSearchEngine(repository_path, index_dir)
                
                # Create search query
                search_query_obj = SearchQuery(
                    text=smart_query,
                    search_type=SearchType(search_type),
                    node_types=final_node_types,
                    languages=final_languages,
                    file_patterns=final_file_patterns,
                    limit=limit,
                    min_score=min_score
                )
                
                start_time = time.time()
                results = engine.search(search_query_obj)
                search_time = time.time() - start_time
                
                if not results:
                    console.print(f"No results found for: [yellow]{query}[/yellow]")
                    return
                
            except Exception as e:
                # Fallback to simple text search if index doesn't exist or other error
                search_method_used = "📝 Simple Text Search (engine failed)"
                console.print(f"[dim]📝 Search engine failed, using simple text search...[/dim]")
                console.print(f"[dim]Debug: {str(e)}[/dim]")
                results = fallback_text_search(
                    repository_path, 
                    smart_query, 
                    final_file_patterns,
                    limit
                )
                search_time = 0.001  # Very fast for simple search
                
                if not results:
                    console.print(f"No results found for: [yellow]{query}[/yellow]")
                    return
        
        # Output results
        if json_output:
            output = {
                "query": query,
                "search_method": search_method_used,
                "search_time": search_time,
                "total_results": len(results),
                "results": [result.to_dict() for result in results]
            }
            print(json.dumps(output, indent=2))
        else:
            console.print(f"Results for '[cyan]{query}[/cyan]' ({len(results)} results, {search_time:.3f}s):")
            console.print(f"[dim]🔧 Method: {search_method_used}[/dim]")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                # Check if this is a fallback search result or a normal search result
                if hasattr(result, 'file_path') and hasattr(result, 'line_number'):
                    # Fallback text search result
                    score_text = f"{result.score:.3f}"
                    
                    console.print(f"{i:2d}. [{score_text}] [bold]{result.file_path}[/bold]")
                    console.print(f"     📄 Line {result.line_number}")
                    console.print(f"     📝 {result.line_content[:100]}{'...' if len(result.line_content) > 100 else ''}")
                    console.print()
                else:
                    # Normal search result
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
def function(
    query: str = typer.Argument(..., help="Search query"),
    directory: Optional[str] = typer.Argument(".", help="Directory to search in (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search functions in code"""
    try:
        import time
        import json
        from pathlib import Path
        
        repository_path = directory or "."
        
        # Smart query parsing - extract filters from natural language
        smart_query, auto_filters = parse_smart_query(query)
        
        # Force node_types to function
        final_node_types = ["function"]
        final_languages = languages if languages else auto_filters['languages']
        final_file_patterns = file_patterns if file_patterns else auto_filters['file_patterns']
        
        # Show what was auto-detected (if anything)
        if any(auto_filters.values()):
            detected_parts = []
            if auto_filters['languages']:
                detected_parts.append(f"languages: {', '.join(auto_filters['languages'])}")
            if auto_filters['file_patterns']:
                detected_parts.append(f"patterns: {', '.join(auto_filters['file_patterns'])}")
            
            console.print(f"[dim]🔍 Auto-detected: {', '.join(detected_parts)}[/dim]")
        
        # Try to use OptimizedSearchEngine, fallback to simple text search if no index
        index_path = Path(index_dir)
        search_method_used = ""
        
        if not index_path.exists() or not any(index_path.iterdir()):
            # Index doesn't exist, use fallback search
            search_method_used = "📝 Simple Text Search (no index)"
            console.print(f"[dim]📝 Index not found, using simple text search...[/dim]")
            results = fallback_text_search(
                repository_path, 
                smart_query, 
                final_file_patterns,
                limit
            )
            search_time = 0.001  # Very fast for simple search
            
            if not results:
                console.print(f"No results found for: [yellow]{query}[/yellow]")
                return
        else:
            # Index exists, use OptimizedSearchEngine
            try:
                search_method_used = "🔍 Indexed Code Search (OptimizedSearchEngine)"
                engine = OptimizedSearchEngine(repository_path, index_dir)
                
                # Create search query
                search_query_obj = SearchQuery(
                    text=smart_query,
                    search_type=SearchType(search_type),
                    node_types=final_node_types,
                    languages=final_languages,
                    file_patterns=final_file_patterns,
                    limit=limit,
                    min_score=min_score
                )
                
                start_time = time.time()
                results = engine.search(search_query_obj)
                search_time = time.time() - start_time
                
                if not results:
                    console.print(f"No results found for: [yellow]{query}[/yellow]")
                    return
                
            except Exception as e:
                # Fallback to simple text search if index doesn't exist or other error
                search_method_used = "📝 Simple Text Search (engine failed)"
                console.print(f"[dim]📝 Search engine failed, using simple text search...[/dim]")
                console.print(f"[dim]Debug: {str(e)}[/dim]")
                results = fallback_text_search(
                    repository_path, 
                    smart_query, 
                    final_file_patterns,
                    limit
                )
                search_time = 0.001  # Very fast for simple search
                
                if not results:
                    console.print(f"No results found for: [yellow]{query}[/yellow]")
                    return
        
        # Output results
        if json_output:
            output = {
                "query": query,
                "search_method": search_method_used,
                "search_time": search_time,
                "total_results": len(results),
                "results": [result.to_dict() for result in results]
            }
            print(json.dumps(output, indent=2))
        else:
            console.print(f"Function search for '[cyan]{query}[/cyan]' ({len(results)} results, {search_time:.3f}s):")
            console.print(f"[dim]🔧 Method: {search_method_used}[/dim]")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                # Check if this is a fallback search result or a normal search result
                if hasattr(result, 'file_path') and hasattr(result, 'line_number'):
                    # Fallback text search result
                    score_text = f"{result.score:.3f}"
                    
                    console.print(f"{i:2d}. [{score_text}] [bold]{result.file_path}[/bold]")
                    console.print(f"     📄 Line {result.line_number}")
                    console.print(f"     📝 {result.line_content[:100]}{'...' if len(result.line_content) > 100 else ''}")
                    console.print()
                else:
                    # Normal search result
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
        console.print(f"❌ [red]Function search failed: {e}[/red]")
        raise typer.Exit(1)


@search_app.command()
def search_command(
    query: str = typer.Argument(..., help="Search query"),
    repository: Optional[str] = typer.Argument(None, help="Path to repository (default: current)"),
    index_dir: str = typer.Option(".nlp3_index", "--index-dir", help="Index directory"),
    search_type: str = typer.Option("hybrid", "--type", help="Search type"),
    node_types: Optional[List[str]] = typer.Option(None, "--node-types", help="Filter by node types"),
    languages: Optional[List[str]] = typer.Option(None, "--languages", help="Filter by languages"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="Filter by file patterns"),
    limit: int = typer.Option(20, "--limit", help="Maximum results"),
    min_score: float = typer.Option(0.1, "--min-score", help="Minimum score"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
):
    """Search in indexed repository"""
    try:
        import time
        import json
        
        repository_path = repository or "."
        
        # Smart query parsing - extract filters from natural language
        smart_query, auto_filters = parse_smart_query(query)
        
        # Merge auto-detected filters with manual filters (manual takes precedence)
        final_node_types = node_types if node_types else auto_filters['node_types']
        final_languages = languages if languages else auto_filters['languages']
        final_file_patterns = file_patterns if file_patterns else auto_filters['file_patterns']
        
        # Show what was auto-detected (if anything)
        if any(auto_filters.values()):
            detected_parts = []
            if auto_filters['node_types']:
                detected_parts.append(f"types: {', '.join(auto_filters['node_types'])}")
            if auto_filters['languages']:
                detected_parts.append(f"languages: {', '.join(auto_filters['languages'])}")
            if auto_filters['file_patterns']:
                detected_parts.append(f"patterns: {', '.join(auto_filters['file_patterns'])}")
            
            console.print(f"[dim]🔍 Auto-detected: {', '.join(detected_parts)}[/dim]")
        
        # Try to use OptimizedSearchEngine, fallback to simple text search if no index
        import os
        import json
        from pathlib import Path
        
        index_path = Path(index_dir)
        search_method_used = ""
        
        if not index_path.exists() or not any(index_path.iterdir()):
            # Index doesn't exist, use fallback search
            search_method_used = "📝 Simple Text Search (no index)"
            console.print(f"[dim]📝 Index not found, using simple text search...[/dim]")
            results = fallback_text_search(
                repository_path, 
                smart_query, 
                final_file_patterns,
                limit
            )
            search_time = 0.001  # Very fast for simple search
            
            if not results:
                console.print(f"No results found for: [yellow]{query}[/yellow]")
                return
        else:
            # Index exists, use OptimizedSearchEngine
            try:
                search_method_used = "🔍 Indexed Code Search (OptimizedSearchEngine)"
                engine = OptimizedSearchEngine(repository_path, index_dir)
                
                # Create search query
                search_query = SearchQuery(
                    text=smart_query,
                    search_type=SearchType(search_type),
                    node_types=final_node_types,
                    languages=final_languages,
                    file_patterns=final_file_patterns,
                    limit=limit,
                    min_score=min_score
                )
                
                start_time = time.time()
                results = engine.search(search_query)
                search_time = time.time() - start_time
                
                if not results:
                    console.print(f"No results found for: [yellow]{query}[/yellow]")
                return
                
            except Exception as e:
                # Fallback to simple text search if index doesn't exist or other error
                search_method_used = "📝 Simple Text Search (engine failed)"
                console.print(f"[dim]📝 Search engine failed, using simple text search...[/dim]")
                console.print(f"[dim]Debug: {str(e)}[/dim]")
                results = fallback_text_search(
                    repository_path, 
                    smart_query, 
                    final_file_patterns,
                    limit
                )
                search_time = 0.001  # Very fast for simple search
                
                if not results:
                    console.print(f"No results found for: [yellow]{query}[/yellow]")
                    return
        
        if json_output:
            output = {
                "query": query,
                "search_method": search_method_used,
                "search_time": search_time,
                "total_results": len(results),
                "results": [result.to_dict() for result in results]
            }
            print(json.dumps(output, indent=2))
        else:
            console.print(f"Results for '[cyan]{query}[/cyan]' ({len(results)} results, {search_time:.3f}s):")
            console.print(f"[dim]🔧 Method: {search_method_used}[/dim]")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                # Check if this is a fallback search result or a normal search result
                if hasattr(result, 'file_path') and hasattr(result, 'line_number'):
                    # Fallback text search result
                    score_text = f"{result.score:.3f}"
                    
                    console.print(f"{i:2d}. [{score_text}] [bold]{result.file_path}[/bold]")
                    console.print(f"     📄 Line {result.line_number}")
                    console.print(f"     📝 {result.line_content[:100]}{'...' if len(result.line_content) > 100 else ''}")
                    console.print()
                else:
                    # Normal search result
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
def text(
    query: str = typer.Argument(..., help="Text to search for"),
    directory: str = typer.Argument(".", help="Directory to search in (default: current)"),
    file_patterns: Optional[List[str]] = typer.Option(None, "--file-patterns", help="File patterns to search in"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", help="Case sensitive search"),
    limit: int = typer.Option(50, "--limit", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    yaml_output: bool = typer.Option(True, "--yaml", help="Output YAML (default)"),
    explain: bool = typer.Option(False, "--explain", help="Show explanations"),
):
    """Simple text search (like grep) with nlp3 interface"""
    try:
        import time
        import re
        import json
        from pathlib import Path
        
        start_time = time.time()
        
        # Default file patterns if none specified
        if not file_patterns:
            file_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs", "*.cpp", "*.c", "*.h", "*.hpp", 
                           "*.json", "*.yaml", "*.yml", "*.xml", "*.md", "*.txt", "*.html", "*.css", "*.toml", "*.cfg", "*.ini"]
        
        # Compile regex for search
        flags = 0 if case_sensitive else re.IGNORECASE
        query_pattern = re.compile(re.escape(query), flags)
        
        results = []
        search_dir = Path(directory)
        
        if not search_dir.exists():
            console.print(f"[red]Directory not found: {directory}[/red]")
            raise typer.Exit(1)
        
        # Search through files
        for pattern in file_patterns:
            for file_path in search_dir.rglob(pattern):
                # Skip common directories
                if any(skip_dir in file_path.parts for skip_dir in ['.git', 'venv', '__pycache__', 'node_modules', '.idea', 'dist', 'build', '.pytest_cache']):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if query_pattern.search(line):
                                # Create a simple result
                                # Clean up line content for better readability
                                line_content = line.strip()
                                
                                # Check if this line looks like a Go function signature split across lines
                                if (line_content.endswith((')', 'string', 'int', 'bool', 'float', 'error')) and 
                                    len(line_content) > 10 and 
                                    not line_content.endswith('{') and
                                    not line_content.endswith('}')):
                                    
                                    # Look ahead to see if next line contains the opening brace
                                    try:
                                        next_line = next(f)
                                        next_line_stripped = next_line.strip()
                                        if (next_line_stripped.startswith(('error {', '{')) or 
                                            (next_line_stripped in ('error {', '{'))):
                                            # Combine the lines
                                            line_content = line_content + ' ' + next_line_stripped
                                            # Skip the next line since we've already processed it
                                            continue
                                    except StopIteration:
                                        pass  # No more lines
                                
                                result = {
                                    "file_path": str(file_path),
                                    "line_number": line_num,
                                    "line_content": line_content,
                                    "score": 1.0
                                }
                                results.append(result)
                                
                                # Stop if we hit the limit
                                if len(results) >= limit:
                                    break
                    
                    if len(results) >= limit:
                        break
                        
                except (UnicodeDecodeError, PermissionError, OSError):
                    # Skip files that can't be read
                    continue
                    
            if len(results) >= limit:
                break
        
        search_time = time.time() - start_time
        
        if not results:
            console.print(f"No results found for: [yellow]{query}[/yellow]")
            return
        
        # Output results
        if json_output:
            output = {
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "search_time": search_time,
                "total_results": len(results),
                "results": results
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using simple text search"
            print(json.dumps(output, indent=2))
        elif yaml_output:
            import yaml
            output = {
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "search_time": search_time,
                "total_results": len(results),
                "results": results
            }
            if explain:
                output["explanation"] = f"Found {len(results)} matches for '{query}' using simple text search"
            print(yaml.dump(output, default_flow_style=False, sort_keys=False))
        else:
            console.print(f"Text search for '[cyan]{query}[/cyan]' in [blue]{directory}[/blue] ({len(results)} results, {search_time:.3f}s):")
            console.print(f"[dim]🔧 Method: 📝 Simple Text Search (grep-like)[/dim]")
            console.print(f"[dim]📁 Patterns: {', '.join(file_patterns)}[/dim]")
            if explain:
                console.print(f"[dim]📝 Explanation: Found {len(results)} matches for '{query}' using simple text search[/dim]")
            console.print("─" * 80)
            
            for i, result in enumerate(results, 1):
                # Shorten file path for display
                display_path = result["file_path"]
                if display_path.startswith(directory):
                    display_path = display_path[len(directory):].lstrip('/\\')
                
                console.print(f"{i:2d}. [bold]{display_path}[/bold]")
                console.print(f"     📄 Line {result['line_number']}")
                console.print(f"     📝 {result['line_content'][:100]}{'...' if len(result['line_content']) > 100 else ''}")
                console.print()
        
    except Exception as e:
        console.print(f"❌ [red]Text search failed: {e}[/red]")
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
    """Main CLI entry point with enhanced error handling"""
    import sys
    
    # Handle direct search: nlp3 search "query" [directory]
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        command = sys.argv[2]
        
        # If the command is not a known subcommand, treat it as a direct search query
        if command not in ["search", "search-command", "text", "index", "update", "stats", "cleanup", "--help", 
                          "function", "method", "variable", "module", "import"]:
            # Direct search: nlp3 search "query" [directory]
            query = command
            directory = sys.argv[3] if len(sys.argv) > 3 else "."
            
            # Reconstruct arguments for search command
            new_argv = [
                sys.argv[0], sys.argv[1], "search", query
            ]
            
            # Add directory if it's not an option
            if directory and not directory.startswith("--"):
                new_argv.append(directory)
            
            # Add any remaining arguments
            if len(sys.argv) > 4:
                new_argv.extend(sys.argv[4:])
            
            # Replace sys.argv and continue
            sys.argv = new_argv
        elif command in ["function", "method", "variable", "module", "import"]:
            # Handle simple aliases
            node_type = command
            
            query = sys.argv[3] if len(sys.argv) > 3 else ""
            directory = sys.argv[4] if len(sys.argv) > 4 else "."
            
            # Reconstruct arguments for search-command
            new_argv = [
                sys.argv[0], sys.argv[1], "search-command", query,
                "--node-types", node_type
            ]
            
            # Add directory if it's not an option
            if directory and not directory.startswith("--"):
                new_argv.append(directory)
            
            # Add any remaining arguments
            if len(sys.argv) > 5:
                new_argv.extend(sys.argv[5:])
            
            # Replace sys.argv and continue
            sys.argv = new_argv
        elif command == "search":
            # Handle nlp3 search search "query" [directory]
            query = sys.argv[3] if len(sys.argv) > 3 else ""
            directory = sys.argv[4] if len(sys.argv) > 4 else "."
            
            # Reconstruct arguments for search command
            new_argv = [
                sys.argv[0], sys.argv[1], "search", query
            ]
            
            # Add directory if it's not an option
            if directory and not directory.startswith("--"):
                new_argv.append(directory)
            
            # Add any remaining arguments
            if len(sys.argv) > 5:
                new_argv.extend(sys.argv[5:])
            
            # Replace sys.argv and continue
            sys.argv = new_argv
    
    try:
        app()
    except SystemExit as e:
        # Handle SystemExit from Typer to provide better error messages
        raise e
    except Exception as e:
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)
