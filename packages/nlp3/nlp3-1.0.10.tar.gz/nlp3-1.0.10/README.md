# NLP3 - Universal Context Navigator

**Navigate any data structure using natural language. Files, APIs, HTML, JSON, YAML and more.**

NLP3 to uniwersalny nawigator po strukturach danych, który pozwala eksplorować system plików, JSON, YAML, HTML, API i inne źródła danych za pomocą zapytań w języku naturalnym (polskim i angielskim).

## 🎯 Status: Production Ready ✅

- ✅ **Core System**: 100% Complete
- ✅ **Universal Adapters**: 75% Complete (5/7)
- ✅ **Output Formats**: 100% Complete (11/11)
- ✅ **Commands**: 100% Complete (Smart Search, Text Search, Function Search, Grep-like Commands, Query, Explore)
- ✅ **Function Granularity**: 100% Complete (name, content, input, output)
- ✅ **Direct Commands**: 100% Complete (function, class, method, variable, module, import)
- ✅ **Grep-like Commands**: 100% Complete (filename, path, content)
- ✅ **Optimized Search**: 100% Complete (Indexing, Semantic, Hybrid)
- ✅ **Multi-language Support**: 100% Complete (Python, JavaScript, TypeScript, Java, Go, Rust)
- ✅ **Examples**: 100% Complete (30/30)
- ✅ **E2E Tests**: 100% Complete (42/42 passing)
- ✅ **Documentation**: 100% Complete

## 🚀 Quick Start

```bash
# Instalacja
pip install -e ".[test]"

# Bezpośrednie komendy wyszukiwania (NOWE!)
nlp3 function "validate" ./src
nlp3 function-name "main" ./src
nlp3 function-content "return True" ./src
nlp3 function-input "username" ./src
nlp3 function-output "bool" ./src

# Dodatkowe komendy strukturalne
nlp3 class "User" ./src
nlp3 method "validate" ./src
nlp3 variable "config" ./src
nlp3 module "utils" ./src
nlp3 import "requests" ./src

# Szybkie komendy grep-like (NOWE!)
nlp3 filename "validate" .                      # Wyszukaj w nazwach plików (YAML)
nlp3 path "main" .                              # Znajdź ścieżki plików (YAML)
nlp3 content "TODO" . --limit 20               # Wyszukaj w treści plików (YAML)
nlp3 content "token" . --explain               # Z wyjaśnieniami (YAML)

# Inteligentne wyszukiwanie (automatycznie wybiera metodę)
nlp3 search "validate input" ./src
nlp3 search "wronai" ./docs

# Proste wyszukiwanie tekstowe (jak grep)
nlp3 search text "function" ./src --file-patterns "*.py"

# Nawigacja po danych
nlp3 query "users" users.json
nlp3 query "find .py files" ./src --format table

# Eksploracja struktur
nlp3 explore ./src --depth 2
nlp3 explore https://httpbin.org/json --depth 2

# Optymalizowane wyszukiwanie kodu (wymaga indeksu)
nlp3 search index . --force
nlp3 search search-command "authentication" --type semantic --explain
nlp3 search stats .

# Testowanie
make test-e2e
python3 examples/run_examples.py
```

## 🔍 Search Commands

### Direct Function Commands (NEW!)
Bezpośrednie wyszukuj funkcje z różnym stopniowaniem:

```bash
# Wyszukiwanie nazw funkcji
nlp3 function "validate" ./src                    # Ogólne wyszukiwanie funkcji
nlp3 function-name "validate" ./src              # Tylko nazwy funkcji
nlp3 function-name "main" ./src                   # Funkcje main

# Wyszukiwanie treści funkcji
nlp3 function-content "validate" ./src           # Treść funkcji
nlp3 function-content "return True" ./src        # Konkretne implementacje

# Wyszukiwanie parametrów
nlp3 function-input "username" ./src              # Parametry funkcji
nlp3 function-input "str" ./src                  # Typy parametrów
nlp3 function-input "Dict" ./src                  # Złożone typy

# Wyszukiwanie wartości zwracanych
nlp3 function-output "bool" ./src                # Typy zwracane
nlp3 function-output "dict" ./src                 # Zwracanie słowników
nlp3 function-output "None" ./src                 # Zwracanie None

# Opcje dla wszystkich komend
--limit 20          # Limit wyników
--json              # Wyjście JSON
--yaml              # Wyjście YAML (domyślny dla grep-like)
--explain           # Wyjaśnienia
--languages python  # Filtrowanie po językach
```

### ⚡ Grep-like Commands (NEW!)
Szybkie komendy inspirowane przez `grep` i `find`:

```bash
# Wyszukiwanie w nazwach plików (jak grep -r)
nlp3 filename "validate" .                      # Wyszukaj "validate" w nazwach plików
nlp3 filename "main" ./src --limit 10           # Tylko 10 wyników
nlp3 filename "config" . --case-sensitive     # Wrażliwość na wielkość liter
nlp3 filename "test" . --file-patterns "*.py"  # Tylko pliki Python

# Wyszukiwanie ścieżek plików (jak find)
nlp3 path "main" .                              # Znajdź pliki z "main" w nazwie
nlp3 path "config" ./src --limit 5            # Ścieżki w folderze src
nlp3 path "test" . --file-patterns "*.js"     # Tylko pliki JavaScript

# Wyszukiwanie treści plików (jak grep -r)
nlp3 content "validate" ./src                   # Wyszukaj "validate" w treści (YAML)
nlp3 content "TODO" . --limit 20               # Znajdź TODO w całym projekcie (YAML)
nlp3 content "import os" . --case-sensitive   # Wrażliwe na wielkość liter (YAML)
nlp3 content "password" . --file-patterns "*.py"  # Tylko w plikach Python (YAML)
nlp3 content "token" . --explain               # Z wyjaśnieniami (YAML)

# Opcje dla komend grep-like
--limit 50              # Limit wyników (domyślnie 50)
--case-sensitive        # Wrażliwość na wielkość liter
--file-patterns "*.py" # Wzorce plików
--json                  # Wyjście JSON
--yaml                  # Wyjście YAML (domyślny)
--explain               # Pokaż wyjaśnienia

# Opcje dla komend function search
--limit 20              # Limit wyników (domyślnie 20)
--min-score 0.1         # Minimalny score
--explain               # Pokaż wyjaśnienia
--json                  # Wyjście JSON
--yaml                  # Wyjście YAML (domyślny)
```

### Smart Search (Recommended)
Automatycznie wybiera między indeksem a wyszukiwaniem tekstowym:

```bash
nlp3 search "query" [directory]     # Inteligentne wyszukiwanie
nlp3 search "validate input" ./src
nlp3 search "python functions" . --node-types function
```

### Text Search (grep-like)
Proste wyszukiwanie tekstowe we wszystkich plikach (domyślnie YAML):

```bash
nlp3 search text "query" [directory]       # Wyszukiwanie tekstowe (YAML)
nlp3 search text "wronai" ./src --file-patterns "*.py"
nlp3 search text "import" . --case-sensitive --limit 50
nlp3 search text "function" . --explain      # Z wyjaśnieniami (YAML)
```

### Indexed Search (Advanced)
Wymaga zaindeksowanego repozytorium:

```bash
nlp3 search search-command "query" [directory]  # Wyszukiwanie w indeksie
nlp3 search index . --force                      # Indeksowanie
nlp3 search stats .                             # Statystyki
```

## 🌍 Multi-language Support

NLP3 wspiera wiele języków programowania z dedykowanymi komendami:

### Python
```bash
nlp3 function "validate_user" ./src
nlp3 function-input "username: str" ./src
nlp3 function-output "-> bool" ./src
```

### JavaScript/TypeScript
```bash
nlp3 function-content "validateUser" ./src
nlp3 function-input "userData: UserData" ./src
nlp3 function-output "Promise<UserData>" ./src
```

### Java
```bash
nlp3 function-name "validateUser" ./src
nlp3 function-input "String username" ./src
nlp3 function-output "boolean" ./src
```

### Go
```bash
nlp3 function-name "ValidateUser" ./src
nlp3 function-input "user User" ./src
nlp3 function-output "bool" ./src
```

### Rust
```bash
nlp3 function-name "validate_user" ./src
nlp3 function-input "&User" ./src
nlp3 function-output "bool" ./src
```

## 📊 Data Navigation

### 📁 System plików
```bash
nlp3 explore ./project --depth 2 --format table
nlp3 query "znajdź wszystkie pliki .py" ./src

# Filtrowanie po rozmiarze (działa!)
nlp3 query "pliki większe niż 10KB" ./docs

# Po dacie modyfikacji
nlp3 query "pliki zmodyfikowane w ostatnim tygodniu" ./src

# Po nazwie
nlp3 query "pliki z nazwą config" ./src
```

### 📄 JSON/YAML Data
```bash
# JSON jako string
nlp3 query "znajdź użytkowników" '{"users": [{"name": "Jan", "city": "Warszawa"}]}'

# Plik JSON
nlp3 query "znajdź konfiguracji bazy danych" ./config/database.json
nlp3 explore ./data/api_response.json --depth 3

# YAML jako string
nlp3 query "znajdź usług" 'services:\n  web:\n    image: nginx'

# Plik YAML
nlp3 query "znajdź porty" ./docker-compose.yml
nlp3 explore ./config/app.yml --depth 2
```

### 🌐 HTML Documents
```bash
# Nawigacja po tagach HTML
nlp3 query "znajdź tag h1" ./docs/index.html
nlp3 query "znajdź class navigation" ./docs/index.html
nlp3 query "znajdź id main-content" ./docs/index.html
nlp3 query "znajdź tag a" ./docs/index.html

# Eksploracja HTML
nlp3 explore ./docs/index.html --depth 3 --format tree
```

### 🚀 REST APIs
```bash
# Analiza odpowiedzi API
nlp3 query "znajdź status" https://httpbin.org/status/200
nlp3 query "znajdź użytkowników" https://jsonplaceholder.typicode.com/users
nlp3 query "znajdź headers" https://httpbin.org/json

# Eksploracja API
nlp3 explore https://api.example.com/users/1 --depth 2
```

## 🎮 CLI Commands Overview

### 🔥 Direct Function Commands (NEW!)
- **`nlp3 function`** - General function search
- **`nlp3 function-name`** - Search function names only
- **`nlp3 function-content`** - Search function bodies
- **`nlp3 function-input`** - Search function parameters
- **`nlp3 function-output`** - Search return types
- **`nlp3 search-class`** - Search classes
- **`nlp3 method`** - Search methods
- **`nlp3 variable`** - Search variables
- **`nlp3 module`** - Search modules
- **`nlp3 import`** - Search imports

### ⚡ Grep-like Commands (NEW!)
- **`nlp3 filename`** - Search filenames (like grep -r)
- **`nlp3 path`** - Search file paths (like find)
- **`nlp3 content`** - Search file contents (like grep -r)

### 🔍 Search Commands
- **`nlp3 search`** - Smart search (auto-chooses method)
- **`nlp3 search text`** - Text search (grep-like)
- **`nlp3 search search-command`** - Indexed search (advanced)
- **`nlp3 search index`** - Build search index
- **`nlp3 search stats`** - Repository statistics

### 📊 Data Navigation
- **`nlp3 query`** - Natural language queries
- **`nlp3 explore`** - Structure exploration

### 🛠️ Utility Commands
- **`nlp3 parse`** - Parse natural language
- **`nlp3 inspect`** - Metadata inspection

## 🔧 Advanced Features

### Function Search Granularity (NEW!)
Precyzyjne wyszukiwanie funkcji według różnych kryteriów:

```bash
# Nazwy funkcji
nlp3 function-name "validate" ./src
nlp3 function-name "get_" ./src          # Pattern matching

# Treść funkcji
nlp3 function-content "return True" ./src
nlp3 function-content "try:" ./src       # Error handling

# Parametry funkcji
nlp3 function-input "username" ./src
nlp3 function-input "Optional[str]" ./src
nlp3 function-input "= " ./src             # Default values

# Wartości zwracane
nlp3 function-output "bool" ./src
nlp3 function-output "List[str]" ./src
nlp3 function-output "None" ./src
```

### Grep-like Commands (NEW!)
Szybkie komendy inspirowane przez `grep` i `find`:

```bash
# Wyszukiwanie w nazwach plików (jak grep -r)
nlp3 filename "validate" .                      # Wyszukaj "validate" w nazwach plików
nlp3 filename "main" ./src --limit 10           # Tylko 10 wyników
nlp3 filename "config" . --case-sensitive     # Wrażliwość na wielkość liter
nlp3 filename "test" . --file-patterns "*.py"  # Tylko pliki Python

# Wyszukiwanie ścieżek plików (jak find)
nlp3 path "main" .                              # Znajdź pliki z "main" w nazwie
nlp3 path "config" ./src --limit 5            # Ścieżki w folderze src
nlp3 path "test" . --file-patterns "*.js"     # Tylko pliki JavaScript

# Wyszukiwanie treści plików (jak grep -r)
nlp3 content "validate" ./src                   # Wyszukaj "validate" w treści (YAML)
nlp3 content "TODO" . --limit 20               # Znajdź TODO w całym projekcie (YAML)
nlp3 content "import os" . --case-sensitive   # Wrażliwe na wielkość liter (YAML)
nlp3 content "password" . --file-patterns "*.py"  # Tylko w plikach Python (YAML)
nlp3 content "token" . --explain               # Z wyjaśnieniami (YAML)

# Opcje dla komend grep-like
--limit 50              # Limit wyników (domyślnie 50)
--case-sensitive        # Wrażliwość na wielkość liter
--file-patterns "*.py" # Wzorce plików
--json                  # Wyjście JSON
--yaml                  # Wyjście YAML (domyślny)
--explain               # Pokaż wyjaśnienia

# Opcje dla komend function search
--limit 20              # Limit wyników (domyślnie 20)
--min-score 0.1         # Minimalny score
--explain               # Pokaż wyjaśnienia
--json                  # Wyjście JSON
--yaml                  # Wyjście YAML (domyślny)
```

### Use Cases Examples

#### Security Audit
```bash
# Znajdź potencjalne problemy bezpieczeństwa
nlp3 content "password" . --limit 20
nlp3 content "secret" . --case-sensitive
nlp3 content "token" . --explain
nlp3 filename "config" . --file-patterns "*.yml"

# Wynik w YAML (domyślny)
nlp3 content "password" . --yaml
```

#### Multi-language Development
```bash
# Znajdź funkcje we wszystkich językach
nlp3 function "validate" .                     # Python, JS, TS, Java, Go, Rust
nlp3 function-name "main" .                      # Entry points
nlp3 function-input "string" .                   # String parameters
nlp3 function-output "bool" .                    # Boolean returns

# JavaScript/TypeScript
nlp3 function "async" . --file-patterns "*.js"  # Async functions
nlp3 content "useState" . --file-patterns "*.tsx" # React hooks

# Java
nlp3 function "public static" . --file-patterns "*.java"  # Static methods
nlp3 content "@Override" . --file-patterns "*.java"     # Annotations

# Go
nlp3 function "func.*Error" . --file-patterns "*.go"  # Error handling
nlp3 content "defer" . --file-patterns "*.go"           # Defer statements

# Rust
nlp3 function "impl" . --file-patterns "*.rs"         # Implementations
nlp3 content "Result<" . --file-patterns "*.rs"        # Error handling
```

#### AI & Machine Learning

```bash
# Znajdź kod AI/ML
nlp3 content "import torch" . --limit 10
nlp3 content "tensorflow" . --limit 10
nlp3 content "sklearn" . --limit 10
nlp3 function "predict" . --limit 15
nlp3 function "train" . --limit 10

# Deep Learning patterns
nlp3 content "nn.Linear" . --limit 5
nlp3 content "Conv2d" . --limit 5
nlp3 content "BatchNorm" . --limit 5
nlp3 function "forward" . --limit 10
```

#### Testing & Quality Assurance

```bash
# Znajdź testy
nlp3 filename "test_" . --limit 20
nlp3 content "assert" . --limit 30
nlp3 function "test_" . --limit 15
nlp3 content "unittest" . --limit 10

# Test patterns
nlp3 content "setUp" . --limit 10
nlp3 content "tearDown" . --limit 10
nlp3 content "@pytest" . --limit 15
nlp3 content "describe(" . --file-patterns "*.js"  # Jest tests
```

#### Dependency Analysis
```bash
# Analiza zależności
nlp3 content "import requests" .
nlp3 content "from flask" .
nlp3 content "import os" .
nlp3 content "import json" .
```

#### Code Refactoring
```bash
# Znajdź funkcje do refaktoryzacji
nlp3 function-name "get_" --limit 20
nlp3 content "TODO" . --limit 20
nlp3 content "FIXME" --limit 15
nlp3 filename "test" . --file-patterns "*.py"

# Wynik w YAML
nlp3 content "TODO" . --limit 10 --yaml
```

#### Multi-language Development

```bash
# Znajdź funkcje we wszystkich językach
nlp3 function "validate" .                     # Python, JS, TS, Java, Go, Rust
nlp3 function-name "main" .                      # Entry points
nlp3 function-input "string" .                   # String parameters
nlp3 function-output "bool" .                    # Boolean returns

# JavaScript/TypeScript
nlp3 function "async" . --file-patterns "*.js"  # Async functions
nlp3 content "useState" . --file-patterns "*.tsx" # React hooks

# Java
nlp3 function "public static" . --file-patterns "*.java"  # Static methods
nlp3 content "@Override" . --file-patterns "*.java"     # Annotations

# Go
nlp3 function "func.*Error" . --file-patterns "*.go"  # Error handling
nlp3 content "defer" . --file-patterns "*.go"           # Defer statements

# Rust
nlp3 function "impl" . --file-patterns "*.rs"         # Implementations
nlp3 content "Result<" . --file-patterns "*.rs"        # Error handling
```

#### AI & Machine Learning

```bash
# Znajdź kod AI/ML
nlp3 content "import torch" . --limit 10
nlp3 content "tensorflow" . --limit 10
nlp3 content "sklearn" . --limit 10
nlp3 function "predict" . --limit 15
nlp3 function "train" . --limit 10

# Deep Learning patterns
nlp3 content "nn.Linear" . --limit 5
nlp3 content "Conv2d" . --limit 5
nlp3 content "BatchNorm" . --limit 5
nlp3 function "forward" . --limit 10
```

#### Testing & Quality Assurance

```bash
# Znajdź testy
nlp3 filename "test_" . --limit 20
nlp3 content "assert" . --limit 30
nlp3 function "test_" . --limit 15
nlp3 content "unittest" . --limit 10

# Test patterns
nlp3 content "setUp" . --limit 10
nlp3 content "tearDown" . --limit 10
nlp3 content "@pytest" . --limit 15
nlp3 content "describe(" . --file-patterns "*.js"  # Jest tests
```

#### Documentation Search
```bash
# Znajdź dokumentację i komentarze
nlp3 content "# TODO" .
nlp3 content "# FIXME" .
nlp3 content "TODO:" --case-sensitive
nlp3 content "NOTE:" .
```

#### Advanced Query Examples
```bash
# Complex queries with explanations
nlp3 search search "authentication system with JWT tokens" --explain
nlp3 search search "database connection pooling" --explain
nlp3 search search "REST API endpoints with validation" --explain

# Performance optimization
nlp3 content "cache" . --explain
nlp3 content "async" . --explain
nlp3 content "pool" . --explain

# Security patterns
nlp3 content "password" . --case-sensitive --explain
nlp3 content "token" . --explain
nlp3 content "hash" . --explain
nlp3 content "encrypt" . --explain
```

#### Performance Optimization
```bash
# Fast grep-like commands
nlp3 filename "config" . --limit 10          # ~1ms
nlp3 path "main" . --limit 5                 # ~1ms
nlp3 content "import" . --limit 20           # ~10ms

# Smart search with caching
nlp3 search index . --force                  # Build index
nlp3 search search "validation" ./src               # ~50ms with index
nlp3 search stats .                          # Index statistics
```

### Performance Comparison

| Command | Speed | Use Case | When to Use |
|----------|-------|----------|-------------|
| `nlp3 filename` | ~1ms | Search filenames | Quick file discovery |
| `nlp3 path` | ~1ms | Find file paths | Locate specific files |
| `nlp3 content` | ~10ms | Search file contents | grep-like text search |
| `nlp3 function-name` | ~100ms | Function names | Precise function search |
| `nlp3 search search` | ~50ms | Smart search | General purpose search |

### Smart Query Parsing
Automatyczne wykrywanie filtrów z języka naturalnego:

```bash
nlp3 search search "python functions for validation"  # Auto-detects: function, python
nlp3 search search "javascript classes in .js files" # Auto-detects: class, javascript, *.js
nlp3 search search "import statements"               # Auto-detects: import
```

### Multiple Output Formats
```bash
nlp3 query "users" users.json --format table     # Table format
nlp3 query "users" users.json --format tree      # Tree format  
nlp3 query "users" users.json --format json      # JSON format
nlp3 query "users" users.json --format yaml      # YAML format
nlp3 query "users" users.json --format csv       # CSV format
nlp3 query "users" users.json --format markdown   # Markdown format
nlp3 query "users" users.json --format xml       # XML format
nlp3 query "users" users.json --format html      # HTML report
```

### Search Methods Transparency
Każda komenda pokazuje, która funkcja została użyta:

```
🔧 Method: 📝 Simple Text Search (no index)
🔧 Method: 🔍 Indexed Code Search (OptimizedSearchEngine)  
🔧 Method: JsonAdapter
🔧 Method: UniversalCodeAdapter
```

## 📦 Installation

```bash
# Basic installation
pip install nlp3

# Development installation with all features
pip install -e ".[test]"

# From source
git clone https://github.com/wronai/nlp3.git
cd nlp3
pip install -e ".[test]"
```

## 🧪 Testing

```bash
# Run all tests (42 tests passing)
make test-e2e

# Run specific test categories
pytest tests/test_e2e.py::TestSearchCommands      # 15 tests
pytest tests/test_e2e.py::TestFunctionSearchGranularity  # 25 tests
pytest tests/test_e2e.py::TestJSONQueries          # JSON tests
pytest tests/test_e2e.py::TestYAMLQueries          # YAML tests
pytest tests/test_search_e2e.py
pytest tests/test_api_tester.py
pytest tests/test_code_analysis.py

# Run examples
python3 examples/run_examples.py
```

## 📊 Test Coverage

### ✅ E2E Tests: 42/42 Passing
- **Search Commands**: 15/15 tests
- **Function Granularity**: 25/25 tests  
- **JSON Queries**: 1/1 tests
- **YAML Queries**: 1/1 tests
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, Go, Rust

### 🎯 Tested Features
- ✅ Direct function commands (function, function-name, function-content, function-input, function-output)
- ✅ Grep-like commands (filename, path, content)
- ✅ Smart search with fallback
- ✅ Text search with patterns and options
- ✅ Multi-language function detection
- ✅ Complex type parameters and returns
- ✅ JSON/YAML data search
- ✅ All output formats (table, tree, json, yaml, csv, xml, markdown)

## 📚 Documentation

- **[Quick Start Guide](docs/quick-start.md)** - Getting started
- **[API Reference](docs/api-reference.md)** - Complete API documentation  
- **[Examples](examples/)** - 30+ practical examples
- **[Architecture](docs/architecture.md)** - System design
- **[Contributing](CONTRIBUTING.md)** - Development guide

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **[NLP2CMD](https://github.com/wronai/nlp2cmd)** - Natural language to command line
- **[Data API Tester](https://github.com/wronai/data-api-tester)** - Universal API testing
- **[WronAI Organization](https://github.com/wronai)** - More AI/ML projects

---

**Made with ❤️ by [WronAI](https://github.com/wronai)**
