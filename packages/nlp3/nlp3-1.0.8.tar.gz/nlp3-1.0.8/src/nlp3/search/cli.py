"""
CLI interface for the optimized search engine.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

from .core import OptimizedSearchEngine, SearchQuery, SearchType
from .cache import CacheManager


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="NLP3 Optimized Code Search Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a repository
  nlp3-search index /path/to/repo --force
  
  # Search for functions
  nlp3-search search "validate input" --type function --limit 10
  
  # Semantic search
  nlp3-search search "authentication logic" --semantic --limit 5
  
  # Update index for changed files
  nlp3-search update /path/to/repo
  
  # Show statistics
  nlp3-search stats /path/to/repo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Index repository')
    index_parser.add_argument('repository', help='Path to repository')
    index_parser.add_argument('--force', action='store_true', help='Force complete reindexing')
    index_parser.add_argument('--index-dir', default='.nlp3_index', help='Index directory')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search in repository')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('repository', nargs='?', help='Path to repository (default: current)')
    search_parser.add_argument('--index-dir', default='.nlp3_index', help='Index directory')
    search_parser.add_argument('--type', choices=['syntactic', 'semantic', 'hybrid'], 
                              default='hybrid', help='Search type')
    search_parser.add_argument('--node-types', nargs='+', help='Filter by node types')
    search_parser.add_argument('--languages', nargs='+', help='Filter by languages')
    search_parser.add_argument('--file-patterns', nargs='+', help='Filter by file patterns')
    search_parser.add_argument('--limit', type=int, default=20, help='Maximum results')
    search_parser.add_argument('--min-score', type=float, default=0.1, help='Minimum score')
    search_parser.add_argument('--json', action='store_true', help='Output JSON')
    search_parser.add_argument('--explain', action='store_true', help='Show explanations')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update index for changed files')
    update_parser.add_argument('repository', help='Path to repository')
    update_parser.add_argument('--index-dir', default='.nlp3_index', help='Index directory')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show repository statistics')
    stats_parser.add_argument('repository', help='Path to repository')
    stats_parser.add_argument('--index-dir', default='.nlp3_index', help='Index directory')
    stats_parser.add_argument('--json', action='store_true', help='Output JSON')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup expired cache entries')
    cleanup_parser.add_argument('repository', help='Path to repository')
    cleanup_parser.add_argument('--index-dir', default='.nlp3_index', help='Index directory')
    
    return parser


def handle_index_command(args) -> int:
    """Handle index command"""
    try:
        print(f"Indexing repository: {args.repository}")
        
        engine = OptimizedSearchEngine(args.repository, args.index_dir)
        stats = engine.index_repository(force_reindex=args.force)
        
        print(f"✅ Indexing completed!")
        print(f"   Files: {stats['total_files']}")
        print(f"   Nodes: {stats['total_nodes']}")
        print(f"   Time: {stats['total_time']:.2f}s")
        print(f"   Languages: {', '.join(stats['languages'].keys())}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Indexing failed: {e}", file=sys.stderr)
        return 1


def handle_search_command(args) -> int:
    """Handle search command"""
    try:
        repository = args.repository or '.'
        
        engine = OptimizedSearchEngine(repository, args.index_dir)
        
        # Create search query
        query = SearchQuery(
            text=args.query,
            search_type=SearchType(args.type),
            node_types=args.node_types,
            languages=args.languages,
            file_patterns=args.file_patterns,
            limit=args.limit,
            min_score=args.min_score
        )
        
        start_time = time.time()
        results = engine.search(query)
        search_time = time.time() - start_time
        
        if not results:
            print(f"No results found for: {args.query}")
            return 0
        
        if args.json:
            output = {
                "query": args.query,
                "search_time": search_time,
                "total_results": len(results),
                "results": [result.to_dict() for result in results]
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Results for '{args.query}' ({len(results)} results, {search_time:.3f}s):")
            print("-" * 80)
            
            for i, result in enumerate(results, 1):
                node = result.node
                score_text = f"{result.score:.3f}"
                
                print(f"{i:2d}. [{score_text}] {node.display_name}")
                print(f"     Type: {node.node_type.value} | Lang: {node.language.value}")
                print(f"     File: {node.file_path}:{node.range.start.line if node.range else '?'}")
                
                if args.explain and result.explanation:
                    print(f"     Explain: {result.explanation}")
                
                if result.matched_terms:
                    print(f"     Terms: {', '.join(result.matched_terms)}")
                
                if node.docstring:
                    doc_preview = node.docstring[:100] + "..." if len(node.docstring) > 100 else node.docstring
                    print(f"     Doc: {doc_preview}")
                
                print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Search failed: {e}", file=sys.stderr)
        return 1


def handle_update_command(args) -> int:
    """Handle update command"""
    try:
        print(f"Updating index: {args.repository}")
        
        engine = OptimizedSearchEngine(args.repository, args.index_dir)
        stats = engine.update_index()
        
        if stats['updated_files'] == 0:
            print("✅ No files changed, index up to date")
        else:
            print(f"✅ Index updated!")
            print(f"   Files: {stats['updated_files']}")
            print(f"   Nodes: {stats['updated_nodes']}")
            print(f"   Time: {stats['time']:.2f}s")
        
        return 0
        
    except Exception as e:
        print(f"❌ Update failed: {e}", file=sys.stderr)
        return 1


def handle_stats_command(args) -> int:
    """Handle stats command"""
    try:
        engine = OptimizedSearchEngine(args.repository, args.index_dir)
        stats = engine.get_statistics()
        
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"Repository Statistics: {args.repository}")
            print("=" * 50)
            
            # Repository stats
            repo_stats = stats['repository']
            print(f"Files: {repo_stats['total_files']}")
            print(f"Nodes: {repo_stats['total_nodes']}")
            print(f"Languages: {', '.join(repo_stats['language_distribution'].keys())}")
            
            # Node types
            if repo_stats['node_types']:
                print(f"\nNode Types:")
                for node_type, count in sorted(repo_stats['node_types'].items()):
                    print(f"  {node_type}: {count}")
            
            # Index stats
            index_stats = stats['indexing']
            print(f"\nIndex Sizes:")
            print(f"  Text Index: {index_stats['text_index_size']['total_nodes']} nodes")
            print(f"  Vector Index: {index_stats['vector_index_size']['total_nodes']} nodes")
            print(f"  AST Cache: {index_stats['ast_cache_size']['active_entries']} entries")
            print(f"  Query Cache: {index_stats['query_cache_size']['active_entries']} entries")
            
            # Performance stats
            perf_stats = stats['performance']
            if perf_stats['cache_hit_rate'] > 0:
                print(f"\nPerformance:")
                print(f"  Cache Hit Rate: {perf_stats['cache_hit_rate']:.2%}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Stats failed: {e}", file=sys.stderr)
        return 1


def handle_cleanup_command(args) -> int:
    """Handle cleanup command"""
    try:
        print(f"Cleaning up cache: {args.repository}")
        
        cache_manager = CacheManager(Path(args.index_dir))
        cache_manager.cleanup_all()
        
        print("✅ Cache cleanup completed")
        
        return 0
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate handler
    handlers = {
        'index': handle_index_command,
        'search': handle_search_command,
        'update': handle_update_command,
        'stats': handle_stats_command,
        'cleanup': handle_cleanup_command
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
