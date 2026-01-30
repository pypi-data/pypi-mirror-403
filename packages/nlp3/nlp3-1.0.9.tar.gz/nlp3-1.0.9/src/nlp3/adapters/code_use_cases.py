"""Code Analysis Use Cases - 30 Real-world Examples"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..adapters.code_intelligence import CodeIntelligenceEngine
from ..adapters.semantic_search import SemanticSearchEngine
from ..adapters.code_adapter import CodeElement


console = Console()


class CodeAnalysisUseCases:
    """30 real-world code analysis use cases"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.code_engine = CodeIntelligenceEngine()
        self.semantic_engine = SemanticSearchEngine()
        
        # Build indexes
        print("Building code analysis indexes...")
        self.code_engine.build_index(root_path)
        try:
            self.semantic_engine.build_semantic_index(self.code_engine, root_path)
            self.semantic_available = True
        except RuntimeError:
            print("Semantic search not available")
            self.semantic_available = False
    
    def run_all_use_cases(self) -> Dict[str, Any]:
        """Run all 30 use cases and return results"""
        results = {}
        
        use_cases = [
            (self.find_functions_by_name, "1) Znajdowanie funkcji po nazwie i opisie"),
            (self.find_logging_classes, "2) Znajdowanie klas odpowiedzialnych za logowanie"),
            (self.find_api_usage, "3) Szukanie miejsc użycia konkretnego API"),
            (self.find_retry_logic, "4) Wyszukiwanie funkcji zawierających 'retry'"),
            (self.find_entry_points, "5) Lokalizowanie punktów wejścia aplikacji"),
            (self.find_database_operations, "6) Znajdowanie funkcji modyfikujących bazę danych"),
            (self.find_todo_comments, "7) Znajdowanie 'TODO' i 'FIXME'"),
            (self.find_input_validation, "8) Znajdowanie funkcji walidujących dane wejściowe"),
            (self.find_exception_handling, "9) Wyszukiwanie miejsc obsługi wyjątków"),
            (self.find_singleton_pattern, "10) Szukanie implementacji wzorca Singleton"),
            (self.find_side_effects, "11) Znajdowanie funkcji z 'side effects'"),
            (self.find_authorization_logic, "12) Znajdowanie logiki autoryzacji"),
            (self.find_memory_leaks, "13) Wyszukiwanie potencjalnych miejsc wycieków pamięci"),
            (self.find_caching_logic, "14) Znajdowanie funkcji odpowiedzialnych za caching"),
            (self.find_heavy_imports, "15) Znajdowanie miejsc importu ciężkich bibliotek"),
            (self.find_unused_functions, "16) Znajdowanie 'dead code'"),
            (self.find_security_hotspots, "17) Szukanie 'security hotspots'"),
            (self.find_file_upload, "18) Wyszukiwanie funkcji obsługujących upload plików"),
            (self.find_api_endpoints, "19) Znajdowanie endpointów API w kodzie"),
            (self.find_tests_for_function, "20) Znajdowanie testów dotyczących konkretnej funkcji"),
            (self.find_todo_in_docs, "21) Szukanie TODO w dokumentacji"),
            (self.find_html_reports, "22) Znajdowanie kodu generującego raport HTML"),
            (self.find_chart_generation, "23) Wyszukiwanie kodu tworzącego wykresy"),
            (self.find_json_serialization, "24) Znajdowanie funkcji do serializacji danych"),
            (self.find_cli_code, "25) Wyszukiwanie kodu do obsługi CLI"),
            (self.find_config_loading, "26) Znajdowanie funkcji do obsługi konfiguracji"),
            (self.find_socket_usage, "27) Znajdowanie miejsc z użyciem socketów"),
            (self.find_async_code, "28) Znajdowanie kodu asynchronicznego"),
            (self.find_multiprocessing, "29) Znajdowanie kodu używającego multiprocessing"),
            (self.find_feature_flags, "30) Wyszukiwanie 'feature flags'"),
        ]
        
        for use_case_func, description in use_cases:
            console.print(f"\n[bold blue]{description}[/bold blue]")
            try:
                result = use_case_func()
                results[description] = result
                self._display_result(result, description)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                results[description] = {"error": str(e)}
        
        return results
    
    def _display_result(self, result: Any, title: str):
        """Display results in a formatted way"""
        if isinstance(result, list):
            if not result:
                console.print("[yellow]No results found[/yellow]")
                return
            
            table = Table(title=f"Results: {len(result)} items")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Location", style="blue")
            
            for item in result[:10]:  # Limit to 10 items
                if isinstance(item, CodeElement):
                    table.add_row(item.name, item.type, f"Line {item.line_start}")
                elif isinstance(item, tuple) and len(item) == 2:
                    if isinstance(item[0], CodeElement):
                        table.add_row(item[0].name, item[0].type, f"Line {item[0].line_start}")
                    else:
                        table.add_row(str(item[0]), str(item[1]), "")
                elif isinstance(item, tuple) and len(item) == 3:
                    table.add_row(str(item[0]), str(item[1]), str(item[2]))
                elif isinstance(item, tuple) and len(item) > 2:
                    # Handle tuples with CodeElement and other data
                    first_item = item[0]
                    if isinstance(first_item, CodeElement):
                        table.add_row(first_item.name, first_item.type, f"Line {first_item.line_start}")
                    else:
                        table.add_row(str(first_item), str(item[1]) if len(item) > 1 else "", str(item[2]) if len(item) > 2 else "")
                else:
                    # Handle other types
                    table.add_row(str(item), "", "")
            
            console.print(table)
            if len(result) > 10:
                console.print(f"[dim]... and {len(result) - 10} more items[/dim]")
        
        elif isinstance(result, dict):
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                console.print(result)
        else:
            console.print(result)
    
    # Use Case Implementations
    
    def find_functions_by_name(self) -> List[CodeElement]:
        """1) Znajdowanie funkcji po nazwie i opisie"""
        if self.semantic_available:
            # Semantic search for functions
            results = self.semantic_engine.find_functions_by_description("parse JSON data")
        else:
            # Keyword search
            results = self.code_engine.search("parse json")
        
        # Convert results to CodeElement list
        code_elements = []
        for r in results:
            if isinstance(r, tuple) and len(r) >= 1:
                if isinstance(r[0], CodeElement):
                    code_elements.append(r[0])
            elif isinstance(r, CodeElement):
                code_elements.append(r)
        
        return code_elements
    
    def find_logging_classes(self) -> List[CodeElement]:
        """2) Znajdowanie klas odpowiedzialnych za logowanie"""
        logging_patterns = ["log", "logger", "logging", "loguru"]
        results = []
        
        for pattern in logging_patterns:
            pattern_results = self.code_engine.search(pattern)
            # Convert results to CodeElement list
            for r in pattern_results:
                if isinstance(r, tuple) and len(r) >= 1:
                    if isinstance(r[0], CodeElement):
                        results.append(r[0])
                elif isinstance(r, CodeElement):
                    results.append(r)
        
        # Filter for classes and functions related to logging
        filtered_results = []
        for element in results:
            if isinstance(element, CodeElement):
                if "log" in element.name.lower() or \
                   (element.docstring and "log" in element.docstring.lower()):
                    filtered_results.append(element)
        
        return filtered_results
    
    def find_api_usage(self) -> List[CodeElement]:
        """3) Szukanie miejsc użycia konkretnego API"""
        api_patterns = ["/users", "GET", "POST", "PUT", "DELETE", "endpoint", "api"]
        results = []
        
        for pattern in api_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_retry_logic(self) -> List[CodeElement]:
        """4) Wyszukiwanie funkcji zawierających 'retry'"""
        retry_patterns = ["retry", "tenacity", "backoff", "attempt"]
        results = []
        
        for pattern in retry_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_entry_points(self) -> List[CodeElement]:
        """5) Lokalizowanie punktów wejścia aplikacji"""
        return self.code_engine.find_entry_points()
    
    def find_database_operations(self) -> List[CodeElement]:
        """6) Znajdowanie funkcji modyfikujących bazę danych"""
        return self.code_engine.find_database_operations()
    
    def find_todo_comments(self) -> List[Tuple[str, int, str]]:
        """7) Znajdowanie 'TODO' i 'FIXME'"""
        return self.code_engine.find_todo_comments(self.root_path)
    
    def find_input_validation(self) -> List[CodeElement]:
        """8) Znajdowanie funkcji walidujących dane wejściowe"""
        validation_patterns = ["validate", "validation", "schema", "pydantic", "check"]
        results = []
        
        for pattern in validation_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_exception_handling(self) -> List[CodeElement]:
        """9) Wyszukiwanie miejsc obsługi wyjątków"""
        exception_patterns = ["try", "except", "catch", "throw", "raise", "error"]
        results = []
        
        for pattern in exception_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_singleton_pattern(self) -> List[CodeElement]:
        """10) Szukanie implementacji wzorca Singleton"""
        singleton_patterns = ["singleton", "instance", "_instance"]
        results = []
        
        for pattern in singleton_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_side_effects(self) -> List[CodeElement]:
        """11) Znajdowanie funkcji z 'side effects'"""
        side_effect_patterns = ["global", "write", "save", "delete", "modify", "update"]
        results = []
        
        for pattern in side_effect_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_authorization_logic(self) -> List[CodeElement]:
        """12) Znajdowanie logiki autoryzacji"""
        auth_patterns = ["auth", "token", "jwt", "login", "permission", "role"]
        results = []
        
        for pattern in auth_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_memory_leaks(self) -> List[CodeElement]:
        """13) Wyszukiwanie potencjalnych miejsc wycieków pamięci"""
        leak_patterns = ["append", "while True", "for.*in.*append", "open.*without.*close"]
        results = []
        
        for pattern in leak_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_caching_logic(self) -> List[CodeElement]:
        """14) Znajdowanie funkcji odpowiedzialnych za caching"""
        cache_patterns = ["cache", "redis", "memcached", "lru", "@cache"]
        results = []
        
        for pattern in cache_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_heavy_imports(self) -> List[CodeElement]:
        """15) Znajdowanie miejsc importu ciężkich bibliotek"""
        heavy_imports = ["pandas", "numpy", "tensorflow", "torch", "django", "flask"]
        results = []
        
        for library in heavy_imports:
            pattern_results = self.code_engine.search(f"import {library}")
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_unused_functions(self) -> List[CodeElement]:
        """16) Znajdowanie 'dead code'"""
        return self.code_engine.find_unused_functions()
    
    def find_security_hotspots(self) -> List[CodeElement]:
        """17) Szukanie 'security hotspots'"""
        return self.code_engine.find_security_hotspots()
    
    def find_file_upload(self) -> List[CodeElement]:
        """18) Wyszukiwanie funkcji obsługujących upload plików"""
        upload_patterns = ["upload", "file", "multipart", "form", "attachment"]
        results = []
        
        for pattern in upload_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_api_endpoints(self) -> List[CodeElement]:
        """19) Znajdowanie endpointów API w kodzie"""
        endpoint_patterns = ["route", "endpoint", "@app.route", "router", "api"]
        results = []
        
        for pattern in endpoint_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_tests_for_function(self, function_name: str = "parse") -> List[CodeElement]:
        """20) Znajdowanie testów dotyczących konkretnej funkcji"""
        test_patterns = ["test", "spec", "unittest", "pytest"]
        results = []
        
        for pattern in test_patterns:
            pattern_results = self.code_engine.search(f"{pattern} {function_name}")
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_todo_in_docs(self) -> List[Tuple[str, int, str]]:
        """21) Szukanie TODO w dokumentacji"""
        doc_extensions = ['.md', '.rst', '.txt']
        todos = []
        
        for ext in doc_extensions:
            for file_path in self.root_path.rglob(f'*{ext}'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if 'TODO' in line.upper() or 'FIXME' in line.upper():
                            todos.append((str(file_path), line_num, line.strip()))
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        return todos
    
    def find_html_reports(self) -> List[CodeElement]:
        """22) Znajdowanie kodu generującego raport HTML"""
        html_patterns = ["html", "report", "template", "render"]
        results = []
        
        for pattern in html_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_chart_generation(self) -> List[CodeElement]:
        """23) Wyszukiwanie kodu tworzącego wykresy"""
        chart_patterns = ["plot", "chart", "graph", "matplotlib", "plotly", "seaborn"]
        results = []
        
        for pattern in chart_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_json_serialization(self) -> List[CodeElement]:
        """24) Znajdowanie funkcji do serializacji danych"""
        json_patterns = ["json", "serialize", "dumps", "loads", "to_dict"]
        results = []
        
        for pattern in json_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_cli_code(self) -> List[CodeElement]:
        """25) Wyszukiwanie kodu do obsługi CLI"""
        cli_patterns = ["argparse", "click", "typer", "cli", "command", "parser"]
        results = []
        
        for pattern in cli_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_config_loading(self) -> List[CodeElement]:
        """26) Znajdowanie funkcji do obsługi konfiguracji"""
        config_patterns = ["config", "settings", "yaml", "json", "env", "load"]
        results = []
        
        for pattern in config_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_socket_usage(self) -> List[CodeElement]:
        """27) Znajdowanie miejsc z użyciem socketów"""
        socket_patterns = ["socket", "websocket", "connection", "network", "tcp", "udp"]
        results = []
        
        for pattern in socket_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_async_code(self) -> List[CodeElement]:
        """28) Znajdowanie kodu asynchronicznego"""
        return self.code_engine.find_async_functions()
    
    def find_multiprocessing(self) -> List[CodeElement]:
        """29) Znajdowanie kodu używającego multiprocessing"""
        multiprocessing_patterns = ["process", "thread", "pool", "multiprocessing", "concurrent"]
        results = []
        
        for pattern in multiprocessing_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results
    
    def find_feature_flags(self) -> List[CodeElement]:
        """30) Wyszukiwanie 'feature flags'"""
        feature_patterns = ["feature", "flag", "toggle", "enable", "disable", "beta"]
        results = []
        
        for pattern in feature_patterns:
            pattern_results = self.code_engine.search(pattern)
            results.extend([r[0] if isinstance(r, tuple) else r for r in pattern_results])
        
        return results


def run_code_analysis_demo(root_path: str = "."):
    """Run demonstration of all 30 use cases"""
    console.print(Panel.fit("🚀 NLP3Tree Code Analysis Demo - 30 Use Cases", style="bold blue"))
    
    root = Path(root_path)
    if not root.exists():
        console.print(f"[red]Path {root_path} does not exist[/red]")
        return
    
    analyzer = CodeAnalysisUseCases(root)
    results = analyzer.run_all_use_cases()
    
    # Summary
    console.print("\n[bold green]📊 Summary[/bold green]")
    console.print(f"Total use cases executed: {len(results)}")
    
    successful = sum(1 for r in results.values() if not isinstance(r, dict) or "error" not in r)
    console.print(f"Successful: {successful}")
    console.print(f"Failed: {len(results) - successful}")
    
    return results


if __name__ == "__main__":
    run_code_analysis_demo()
