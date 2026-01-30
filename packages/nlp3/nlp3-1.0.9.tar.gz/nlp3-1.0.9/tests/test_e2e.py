#!/usr/bin/env python3
"""
NLP3 End-to-End Tests

Comprehensive E2E tests for NLP3 Universal Context Navigator.
Tests various queries on different file formats and output formats.
"""

import pytest
import subprocess
import json
import yaml
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
import tempfile
import os
from typing import List, Dict, Any

class TestE2E:
    """End-to-end tests for NLP3"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.test_dir = Path(tempfile.mkdtemp(prefix="nlp3_e2e_"))
        cls.create_test_files()
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(cls.test_dir)
    
    @classmethod
    def create_test_files(cls):
        """Create test files for E2E testing"""
        # Create test directory structure
        (cls.test_dir / "src").mkdir(exist_ok=True)
        (cls.test_dir / "docs").mkdir(exist_ok=True)
        (cls.test_dir / "data").mkdir(exist_ok=True)
        (cls.test_dir / "config").mkdir(exist_ok=True)
        
        # Create Python files
        (cls.test_dir / "src" / "main.py").write_text("""
def main():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    main()
""")
        
        (cls.test_dir / "src" / "utils.py").write_text("""
def helper():
    return "helper function"

def calculate(x, y):
    return x + y
""")
        
        (cls.test_dir / "src" / "__init__.py").write_text("")
        
        # Create JSON files
        (cls.test_dir / "data" / "users.json").write_text(json.dumps({
            "users": [
                {"id": 1, "name": "Jan", "city": "Warszawa", "age": 30},
                {"id": 2, "name": "Anna", "city": "Kraków", "age": 25},
                {"id": 3, "name": "Piotr", "city": "Gdańsk", "age": 35}
            ]
        }, indent=2))
        
        (cls.test_dir / "data" / "config.json").write_text(json.dumps({
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "testdb"
            },
            "api": {
                "base_url": "https://api.example.com",
                "timeout": 30
            }
        }, indent=2))
        
        # Create YAML files
        (cls.test_dir / "config" / "docker-compose.yml").write_text("""
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html
  database:
    image: postgres:13
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
    ports:
      - "5432:5432"
""")
        
        (cls.test_dir / "config" / "app.yml").write_text("""
app:
  name: "NLP3 Test App"
  version: "1.0.0"
  debug: true
  features:
    - logging
    - metrics
    - monitoring
""")
        
        # Create HTML files
        (cls.test_dir / "docs" / "index.html").write_text("""
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>NLP3 Documentation</title>
    <meta name="description" content="Universal Context Navigator">
</head>
<body>
    <header class="main-header">
        <h1>NLP3 - Universal Context Navigator</h1>
        <nav id="main-nav">
            <ul class="navigation">
                <li><a href="#features">Features</a></li>
                <li><a href="#examples">Examples</a></li>
                <li><a href="#api">API</a></li>
            </ul>
        </nav>
    </header>
    <main id="main-content">
        <section id="features">
            <h2>Features</h2>
            <table class="feature-table">
                <thead>
                    <tr><th>Feature</th><th>Description</th></tr>
                </thead>
                <tbody>
                    <tr><td>NLP</td><td>Natural Language Processing</td></tr>
                    <tr><td>Universal</td><td>Works with any data</td></tr>
                </tbody>
            </table>
        </section>
        <section id="examples">
            <h2>Examples</h2>
            <pre><code>nlp3 query "find python files" ./src</code></pre>
        </section>
    </main>
    <footer>
        <p>&copy; 2026 NLP3</p>
    </footer>
</body>
</html>
""")
        
        # Create large files for size testing
        large_content = "x" * 15000  # ~15KB
        (cls.test_dir / "src" / "large_file.py").write_text(f"# Large file\n{large_content}")
        
        small_content = "small"
        (cls.test_dir / "src" / "small_file.py").write_text(f"# Small file\n{small_content}")
        
        # Create log files
        (cls.test_dir / "logs").mkdir(exist_ok=True)
        (cls.test_dir / "logs" / "app.log").write_text("""
2026-01-25 10:00:00 INFO Application started
2026-01-25 10:01:00 DEBUG Loading configuration
2026-01-25 10:02:00 INFO Database connected
2026-01-25 10:03:00 ERROR Failed to connect to cache
2026-01-25 10:04:00 WARNING Retrying connection
2026-01-25 10:05:00 INFO Cache connected successfully
""")
    
    def run_nlp3_command(self, cmd: str) -> Dict[str, Any]:
        """Run NLP3 command and return parsed result"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=self.test_dir
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timeout",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def parse_table_output(self, output: str) -> List[Dict[str, str]]:
        """Parse table output from NLP3"""
        lines = output.strip().split('\n')
        if not lines or len(lines) < 4:
            return []
        
        # Skip header and separator lines
        data_lines = [line for line in lines if line.strip() and not line.startswith('┏') and not line.startswith('┡') and not line.startswith('└')]
        if not data_lines:
            return []
        
        # Parse each line (split by │)
        results = []
        for line in data_lines:
            parts = [part.strip() for part in line.split('│')]
            # Filter out empty parts except for size (index 3) which can be empty
            filtered_parts = []
            for i, part in enumerate(parts):
                if part or i == 3:  # Keep index 3 (size) even if empty
                    filtered_parts.append(part)
            
            if len(filtered_parts) >= 5:  # Name, Type, Size, Modified, Path
                # Ensure we have exactly 5 parts by padding if necessary
                while len(filtered_parts) < 5:
                    filtered_parts.append('')
                
                results.append({
                    "name": filtered_parts[0],
                    "type": filtered_parts[1],
                    "size": filtered_parts[2],
                    "modified": filtered_parts[3],
                    "path": filtered_parts[4]
                })
        return results

    def parse_json_output(self, output: str) -> Dict[str, Any]:
        """Parse JSON output from NLP3"""
        try:
            # Find JSON in output (it might be mixed with other text)
            lines = output.strip().split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                stripped = line.strip()
                # Start JSON collection when we see an opening brace
                if stripped.startswith('{') or stripped.startswith('['):
                    in_json = True
                if in_json:
                    json_lines.append(line)
                # End JSON collection when we see a closing brace
                if (stripped.endswith('}') or stripped.endswith(']')) and stripped.count('{') == stripped.count('}') and stripped.count('[') == stripped.count(']'):
                    in_json = False
            
            if json_lines:
                return json.loads('\n'.join(json_lines))
        except json.JSONDecodeError:
            pass
        return {}

    def parse_yaml_output(self, output: str) -> Dict[str, Any]:
        """Parse YAML output from NLP3"""
        try:
            # Find YAML in output
            lines = output.strip().split('\n')
            yaml_lines = []
            in_yaml = False
            
            for line in lines:
                if line.strip().startswith('metadata:') or line.strip().startswith('nodes:'):
                    in_yaml = True
                if in_yaml:
                    yaml_lines.append(line)
            
            if yaml_lines:
                return yaml.safe_load('\n'.join(yaml_lines))
        except yaml.YAMLError:
            pass
        return {}

    def parse_csv_output(self, output: str) -> List[Dict[str, str]]:
        """Parse CSV output from NLP3"""
        try:
            lines = output.strip().split('\n')
            if len(lines) < 2:
                return []
            
            # Filter out lines that don't look like CSV (like warnings)
            csv_lines = []
            for line in lines:
                # Skip lines that don't contain commas and look like warnings/messages
                if ',' in line and not line.startswith('Warning:') and not line.startswith('Parsed intent:'):
                    csv_lines.append(line)
            
            if len(csv_lines) < 2:
                return []
            
            reader = csv.DictReader(csv_lines)
            return list(reader)
        except Exception:
            return []

    def parse_xml_output(self, output: str) -> Dict[str, Any]:
        """Parse XML output from NLP3"""
        try:
            # Find XML in output
            lines = output.strip().split('\n')
            xml_lines = []
            in_xml = False
            
            for line in lines:
                if line.strip().startswith('<?xml') or line.strip().startswith('<nlp3tree'):
                    in_xml = True
                if in_xml:
                    xml_lines.append(line)
                if line.strip().endswith('</nlp3tree>'):
                    in_xml = False
            
            if xml_lines:
                root = ET.fromstring('\n'.join(xml_lines))
                return {"root": root.tag, "attrib": root.attrib}
        except ET.ParseError:
            pass
        return {}

    def parse_markdown_output(self, output: str) -> Dict[str, Any]:
        """Parse Markdown output from NLP3"""
        lines = output.strip().split('\n')
        
        result = {
            "title": "",
            "summary": {},
            "sections": []
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract title
            if line.startswith('# '):
                result["title"] = line[2:]
            # Extract summary
            elif line.startswith('- **Total Nodes:**'):
                result["summary"]["total_nodes"] = line.split(':')[1].strip()
            elif line.startswith('- **Root Nodes:**'):
                result["summary"]["root_nodes"] = line.split(':')[1].strip()
            # Extract sections
            elif line.startswith('## '):
                current_section = line[3:]
                result["sections"].append(current_section)
        
        return result

# Test Cases
class TestFilesystemQueries(TestE2E):
    """Test filesystem queries"""
    
    def test_01_find_python_files_table(self):
        """Test finding Python files with table output"""
        cmd = 'nlp3 query "znajdź pliki .py" ./src --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 3, f"Expected at least 3 Python files, got {len(data)}"
        
        # Check for specific files
        file_names = [item["name"] for item in data]
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "__init__.py" in file_names
        
        # Check file types
        for item in data:
            assert item["type"] == "leaf"
    
    def test_02_find_python_files_json(self):
        """Test finding Python files with JSON output"""
        cmd = 'nlp3 query "znajdź pliki .py" ./src --format json'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_json_output(result["stdout"])
        assert "nodes" in data
        assert len(data["nodes"]) >= 3
    
    def test_03_find_python_files_yaml(self):
        """Test finding Python files with YAML output"""
        cmd = 'nlp3 query "znajdź pliki .py" ./src --format yaml'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_yaml_output(result["stdout"])
        assert "metadata" in data
        assert "nodes" in data
        assert len(data["nodes"]) >= 3
    
    def test_04_find_python_files_csv(self):
        """Test finding Python files with CSV output"""
        cmd = 'nlp3 query "znajdź pliki .py" ./src --format csv'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_csv_output(result["stdout"])
        assert len(data) >= 3
        assert "name" in data[0]
        assert "type" in data[0]
    
    def test_05_find_python_files_xml(self):
        """Test finding Python files with XML output"""
        cmd = 'nlp3 query "znajdź pliki .py" ./src --format xml'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_xml_output(result["stdout"])
        assert "root" in data
        assert data["root"] == "nlp3tree"
    
    def test_06_find_python_files_markdown(self):
        """Test finding Python files with Markdown output"""
        cmd = 'nlp3 query "znajdź pliki .py" ./src --format markdown'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_markdown_output(result["stdout"])
        assert "title" in data
        assert "summary" in data
    
    def test_07_find_large_files(self):
        """Test finding files by size"""
        cmd = 'nlp3 query "pliki większe niż 10KB" ./src --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 large file"
        
        # Check if large_file.py is found
        file_names = [item["name"] for item in data]
        assert "large_file.py" in file_names
    
    def test_08_find_small_files(self):
        """Test finding small files"""
        cmd = 'nlp3 query "pliki mniejsze niż 1KB" ./src --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 small file"
        
        # Check if small_file.py is found
        file_names = [item["name"] for item in data]
        assert "small_file.py" in file_names
    
    def test_09_find_files_by_name(self):
        """Test finding files by name"""
        cmd = 'nlp3 query "znajdź main" ./src --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 file with 'main' in name"
        
        # Check if main.py is found
        file_names = [item["name"] for item in data]
        assert "main.py" in file_names
    
    def test_10_explore_structure_tree(self):
        """Test exploring directory structure"""
        cmd = 'nlp3 explore ./src --depth 2 --format tree'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        # Tree output should contain directory structure
        assert "src" in result["stdout"]
        assert "main.py" in result["stdout"]
        assert "utils.py" in result["stdout"]
    
    def test_11_explore_structure_table(self):
        """Test exploring directory structure with table"""
        cmd = 'nlp3 explore ./src --depth 2 --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 item in structure"
        
        # Should show directory and files
        types = [item["type"] for item in data]
        assert "branch" in types  # Directory
        assert "leaf" in types    # Files
    
    def test_12_inspect_directory(self):
        """Test inspecting directory"""
        cmd = 'nlp3 inspect ./src --depth 2'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        # Inspect output should show metadata
        assert "Adapter:" in result["stdout"]
        assert "Total nodes:" in result["stdout"]
        assert "Tree depth:" in result["stdout"]
    
    def test_13_parse_query(self):
        """Test parsing NLP query"""
        cmd = 'nlp3 parse "znajdź pliki python większe niż 5KB"'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        # Parse output should show intent and predicates
        assert "Intent:" in result["stdout"]
        assert "Predicates:" in result["stdout"]
        assert "size >" in result["stdout"]  # Size predicate should be parsed

class TestJSONQueries(TestE2E):
    """Test JSON file queries"""
    
    def test_14_find_users_json(self):
        """Test finding data in JSON files"""
        cmd = 'nlp3 query "znajdź users" ./data/users.json --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 user found"
        
        # Check if users array is found
        paths = [item["path"] for item in data]
        assert any("users" in path for path in paths)
    
    def test_15_find_database_config(self):
        """Test finding database configuration"""
        cmd = 'nlp3 query "znajdź database" ./data/config.json --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 database config found"
        
        # Check if database object is found
        paths = [item["path"] for item in data]
        assert any("database" in path for path in paths)
    
    def test_16_explore_json_structure(self):
        """Test exploring JSON structure"""
        cmd = 'nlp3 explore ./data/config.json --depth 3 --format tree'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        # Tree output should show JSON structure
        assert "database" in result["stdout"]
        assert "api" in result["stdout"]
        assert "host" in result["stdout"]
        assert "port" in result["stdout"]
    
    def test_17_json_string_query(self):
        """Test querying JSON string"""
        json_str = '{"users": [{"name": "Jan", "city": "Warszawa"}]}'
        cmd = f'nlp3 query "znajdź users" \'{json_str}\' --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 user found"

class TestYAMLQueries(TestE2E):
    """Test YAML file queries"""
    
    def test_18_find_services_yaml(self):
        """Test finding services in YAML"""
        cmd = 'nlp3 query "znajdź services" ./config/docker-compose.yml --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 service found"
        
        # Check if services array is found
        paths = [item["path"] for item in data]
        assert any("services" in path for path in paths)
    
    def test_19_find_ports_yaml(self):
        """Test finding ports in YAML"""
        cmd = 'nlp3 query "znajdź port" ./config/docker-compose.yml --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 port found"
        
        # Check if ports are found
        paths = [item["path"] for item in data]
        assert any("ports" in path for path in paths)
    
    def test_20_explore_yaml_structure(self):
        """Test exploring YAML structure"""
        cmd = 'nlp3 explore ./config/docker-compose.yml --depth 3 --format tree'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        # Tree output should show YAML structure
        assert "services" in result["stdout"]
        assert "web" in result["stdout"]
        assert "database" in result["stdout"]
        assert "ports" in result["stdout"]
    
    def test_21_yaml_string_query(self):
        """Test querying YAML string"""
        yaml_str = 'services:\n  web:\n    image: nginx'
        cmd = f'nlp3 query "znajdź services" \'{yaml_str}\' --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 service found"

class TestHTMLQueries(TestE2E):
    """Test HTML file queries"""
    
    def test_22_find_h1_tags(self):
        """Test finding H1 tags"""
        cmd = 'nlp3 query "znajdź tag h1" ./docs/index.html --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 H1 tag found"
        
        # Check if h1 tags are found
        paths = [item["path"] for item in data]
        assert any("h1" in path for path in paths)
    
    def test_23_find_navigation_class(self):
        """Test finding elements by CSS class"""
        cmd = 'nlp3 query "znajdź class navigation" ./docs/index.html --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 navigation class found"
        
        # Check if navigation class is found
        paths = [item["path"] for item in data]
        assert any("navigation" in path for path in paths)
    
    def test_24_find_main_content_id(self):
        """Test finding elements by ID"""
        cmd = 'nlp3 query "znajdź id main-content" ./docs/index.html --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 main-content ID found"
        
        # Check if main-content ID is found
        paths = [item["path"] for item in data]
        assert any("main-content" in path for path in paths)
    
    def test_25_find_links(self):
        """Test finding links"""
        cmd = 'nlp3 query "znajdź tag a" ./docs/index.html --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 link found"
        
        # Check if a tags are found
        paths = [item["path"] for item in data]
        assert any("a" in path for path in paths)
    
    def test_26_find_code_tags(self):
        """Test finding code tags"""
        cmd = 'nlp3 query "znajdź tag code" ./docs/index.html --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 code tag found"
        
        # Check if code tags are found
        paths = [item["path"] for item in data]
        assert any("code" in path for path in paths)
    
    def test_27_find_tables(self):
        """Test finding tables"""
        cmd = 'nlp3 query "znajdź tag table" ./docs/index.html --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 table found"
        
        # Check if table tags are found
        paths = [item["path"] for item in data]
        assert any("table" in path for path in paths)
    
    def test_28_inspect_html_structure(self):
        """Test inspecting HTML structure"""
        cmd = 'nlp3 inspect ./docs/index.html --depth 2'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        # Inspect output should show HTML metadata
        assert "Adapter:" in result["stdout"]
        assert "HTMLAdapter" in result["stdout"]
        assert "tag:" in result["stdout"]
        assert "Total nodes:" in result["stdout"]
    
    def test_29_explore_html_tree(self):
        """Test exploring HTML structure"""
        cmd = 'nlp3 explore ./docs/index.html --depth 3 --format tree'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        # Tree output should show HTML structure
        assert "html" in result["stdout"]
        assert "head" in result["stdout"]
        assert "body" in result["stdout"]
        assert "h1" in result["stdout"]

class TestComplexQueries(TestE2E):
    """Test complex queries and edge cases"""
    
    def test_30_complex_predicate_query(self):
        """Test complex query with multiple predicates"""
        cmd = 'nlp3 query "znajdź pliki python większe niż 1KB" ./src --format table'
        result = self.run_nlp3_command(cmd)
        
        assert result["success"], f"Command failed: {result['stderr']}"
        
        data = self.parse_table_output(result["stdout"])
        assert len(data) >= 1, "Expected at least 1 file matching complex criteria"
        
        # Check if Python files are found
        file_names = [item["name"] for item in data]
        assert any(name.endswith('.py') for name in file_names)
        
        # Check if files are larger than 1KB
        for item in data:
            if item["size"] != "":
                size_str = item["size"]
                if size_str.endswith('B'):
                    if size_str.endswith('KB'):
                        size = float(size_str[:-2])
                        if size > 1:  # 1KB
                            assert True
                    elif size_str.endswith('MB'):
                        size = float(size_str[:-2])
                        if size > 0.001:  # 1KB in MB
                            assert True
                    else:  # Just B
                        size = float(size_str[:-1])
                        if size > 1024:  # 1KB
                            assert True

if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
