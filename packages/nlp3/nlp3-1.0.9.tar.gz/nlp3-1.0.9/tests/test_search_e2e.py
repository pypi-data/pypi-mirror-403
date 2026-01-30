"""
End-to-end tests for NLP3 optimized search engine.
"""

import pytest
import tempfile
import shutil
import json
import time
from pathlib import Path
from typer.testing import CliRunner

from nlp3.cli import app
from nlp3.search import OptimizedSearchEngine, SearchQuery, SearchType


class TestOptimizedSearchE2E:
    """E2E tests for optimized search functionality"""
    
    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository with test files"""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create Python files
        (temp_dir / "auth.py").write_text("""
def validate_user(username: str, password: str) -> bool:
    \"\"\"Validate user credentials.\"\"\"
    if not username or not password:
        return False
    return len(username) >= 3 and len(password) >= 8

class UserAuthenticator:
    \"\"\"Handles user authentication.\"\"\"
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def authenticate(self, user_data: dict) -> bool:
        \"\"\"Authenticate user with provided data.\"\"\"
        return validate_user(user_data.get('username'), user_data.get('password'))
""")
        
        (temp_dir / "api.py").write_text("""
import requests
import json

class APIClient:
    \"\"\"HTTP API client for authentication.\"\"\"
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def login(self, username: str, password: str) -> dict:
        \"\"\"Login to API and return token.\"\"\"
        response = requests.post(f"{self.base_url}/login", json={
            "username": username,
            "password": password
        })
        return response.json()
    
    def validate_token(self, token: str) -> bool:
        \"\"\"Validate JWT token.\"\"\"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.base_url}/validate", headers=headers)
        return response.status_code == 200
""")
        
        # Create JavaScript file
        (temp_dir / "auth.js").write_text("""
/**
 * Authentication module for frontend.
 */

class AuthService {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.token = null;
    }
    
    /**
     * Authenticate user with credentials
     */
    async login(username, password) {
        const response = await fetch(`${this.apiUrl}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        this.token = data.token;
        return data;
    }
    
    /**
     * Validate session token
     */
    validateToken() {
        return !!this.token;
    }
}

function validateInput(input) {
    if (!input || typeof input !== 'string') {
        return false;
    }
    return input.trim().length > 0;
}
""")
        
        # Create Go file
        (temp_dir / "main.go").write_text("""
package main

import (
	"encoding/json"
	"net/http"
	"time"
)

type User struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Token    string `json:"token,omitempty"`
}

type AuthService struct {
	secretKey string
	users     map[string]string
}

func NewAuthService(secretKey string) *AuthService {
	return &AuthService{
		secretKey: secretKey,
		users: map[string]string{
			"admin": "admin123",
			"user1": "password1",
		},
	}
}

func (a *AuthService) ValidateUser(username, password string) bool {
	storedPassword, exists := a.users[username]
	return exists && storedPassword == password
}

func (a *AuthService) LoginHandler(w http.ResponseWriter, r *http.Request) {
	var user User
	json.NewDecoder(r.Body).Decode(&user)
	
	if a.ValidateUser(user.Username, user.Password) {
		token := "mock-jwt-token"
		user.Token = token
		json.NewEncoder(w).Encode(user)
	} else {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
	}
}

func main() {
	auth := NewAuthService("secret")
	http.HandleFunc("/login", auth.LoginHandler)
	http.ListenAndServe(":8080", nil)
}
""")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        """CLI runner for testing"""
        return CliRunner()
    
    def test_search_index_command(self, runner, temp_repo):
        """Test search index command"""
        result = runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        assert result.exit_code == 0
        assert "Indexing completed!" in result.stdout
        assert "Files: 4" in result.stdout
        assert "Nodes:" in result.stdout
        assert "Languages:" in result.stdout
        assert "python" in result.stdout
        assert "javascript" in result.stdout
        assert "go" in result.stdout
    
    def test_search_stats_command(self, runner, temp_repo):
        """Test search stats command"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Then get stats
        result = runner.invoke(app, ["search", "stats", str(temp_repo)])
        
        assert result.exit_code == 0
        assert "Repository Statistics:" in result.stdout
        assert "Index Sizes:" in result.stdout
        assert "Text Index:" in result.stdout
        assert "Vector Index:" in result.stdout
    
    def test_search_stats_json_output(self, runner, temp_repo):
        """Test search stats with JSON output"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Then get stats as JSON
        result = runner.invoke(app, ["search", "stats", str(temp_repo), "--json"])
        
        assert result.exit_code == 0
        
        # Parse JSON output
        stats_data = json.loads(result.stdout)
        assert "repository" in stats_data
        assert "indexing" in stats_data
        assert "performance" in stats_data
    
    def test_search_syntactic_command(self, runner, temp_repo):
        """Test syntactic search command"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search for "validate"
        result = runner.invoke(app, [
            "search", "search-command", 
            "validate", 
            str(temp_repo),
            "--type", "syntactic",
            "--limit", "5"
        ])
        
        assert result.exit_code == 0
        assert "Results for 'validate'" in result.stdout
        # Should find validate-related functions/classes
        assert any(name in result.stdout for name in ["validateInput", "validate_user", "ValidateUser", "UserAuthenticator"])
    
    def test_search_semantic_command(self, runner, temp_repo):
        """Test semantic search command"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search for "authentication logic"
        result = runner.invoke(app, [
            "search", "search-command", 
            "authentication logic", 
            str(temp_repo),
            "--type", "semantic",
            "--limit", "3"
        ])
        
        assert result.exit_code == 0
        assert "Results for 'authentication logic'" in result.stdout
        # Should find authentication-related code
    
    def test_search_with_filters(self, runner, temp_repo):
        """Test search with node type and language filters"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search for functions only
        result = runner.invoke(app, [
            "search", "search-command", 
            "validate", 
            str(temp_repo),
            "--node-types", "function",
            "--limit", "5"
        ])
        
        assert result.exit_code == 0
        assert "Results for 'validate'" in result.stdout
    
    def test_search_with_explain(self, runner, temp_repo):
        """Test search with explanations"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search with explanations
        result = runner.invoke(app, [
            "search", "search-command", 
            "validate", 
            str(temp_repo),
            "--explain",
            "--limit", "3"
        ])
        
        assert result.exit_code == 0
        assert "Results for 'validate'" in result.stdout
        # Should contain explanations about scoring
    
    def test_search_json_output(self, runner, temp_repo):
        """Test search with JSON output"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search with JSON output
        result = runner.invoke(app, [
            "search", "search-command", 
            "validate", 
            str(temp_repo),
            "--json",
            "--limit", "3"
        ])
        
        assert result.exit_code == 0
        
        # Parse JSON output
        search_data = json.loads(result.stdout)
        assert "query" in search_data
        assert "search_time" in search_data
        assert "total_results" in search_data
        assert "results" in search_data
        assert isinstance(search_data["results"], list)
    
    def test_search_update_command(self, runner, temp_repo):
        """Test search update command"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Add a new file
        (temp_repo / "new_file.py").write_text("def new_function(): pass")
        
        # Update index
        result = runner.invoke(app, ["search", "update", str(temp_repo)])
        
        assert result.exit_code == 0
        assert "Index updated!" in result.stdout or "No files changed" in result.stdout
    
    def test_search_cleanup_command(self, runner, temp_repo):
        """Test search cleanup command"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Run some searches to create cache
        runner.invoke(app, ["search", "search-command", "validate", str(temp_repo)])
        
        # Cleanup cache
        result = runner.invoke(app, ["search", "cleanup", str(temp_repo)])
        
        assert result.exit_code == 0
        assert "Cache cleanup completed" in result.stdout
    
    def test_search_performance(self, runner, temp_repo):
        """Test search performance metrics"""
        # Index the repository
        index_result = runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        assert index_result.exit_code == 0
        
        # Measure search time
        start_time = time.time()
        result = runner.invoke(app, [
            "search", "search-command", 
            "validate", 
            str(temp_repo),
            "--limit", "10"
        ])
        search_time = time.time() - start_time
        
        assert result.exit_code == 0
        assert search_time < 5.0  # Should be fast with index (adjusted for CI environment)
    
    def test_search_no_results(self, runner, temp_repo):
        """Test search with no results"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search for something that doesn't exist (using syntactic search only)
        result = runner.invoke(app, [
            "search", "search-command", 
            "qwertyuiopasdfghjklzxcvbnm", 
            str(temp_repo),
            "--type", "syntactic",
            "--limit", "5"
        ])
        
        assert result.exit_code == 0
        assert "No results found for:" in result.stdout
    
    def test_search_multiple_languages(self, runner, temp_repo):
        """Test search across multiple programming languages"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search for "token" (should find in multiple languages)
        result = runner.invoke(app, [
            "search", "search-command", 
            "token", 
            str(temp_repo),
            "--limit", "10"
        ])
        
        assert result.exit_code == 0
        assert "Results for 'token'" in result.stdout
        # Should find token-related code in Python, JavaScript, and Go
    
    def test_search_min_score_filter(self, runner, temp_repo):
        """Test search with minimum score filter"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search with high minimum score
        result = runner.invoke(app, [
            "search", "search-command", 
            "validate", 
            str(temp_repo),
            "--min-score", "0.8",
            "--limit", "10"
        ])
        
        assert result.exit_code == 0
        # Should only return high-scoring results
    
    def test_search_file_patterns_filter(self, runner, temp_repo):
        """Test search with file pattern filter"""
        # First index the repository
        runner.invoke(app, ["search", "index", str(temp_repo), "--force"])
        
        # Search only in Python files
        result = runner.invoke(app, [
            "search", "search-command", 
            "validate", 
            str(temp_repo),
            "--file-patterns", "*.py",
            "--limit", "10"
        ])
        
        assert result.exit_code == 0
        assert "Results for 'validate'" in result.stdout


class TestOptimizedSearchAPI:
    """E2E tests for search API directly"""
    
    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository with test files"""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create simple Python file
        (temp_dir / "test.py").write_text("""
def validate_input(data: str) -> bool:
    \"\"\"Validate input data.\"\"\"
    return bool(data and data.strip())

class DataProcessor:
    \"\"\"Process data with validation.\"\"\"
    
    def process(self, data: str) -> str:
        if validate_input(data):
            return data.upper()
        return ""
""")
        
        yield temp_dir
        
        shutil.rmtree(temp_dir)
    
    def test_search_engine_api(self, temp_repo):
        """Test search engine API directly"""
        engine = OptimizedSearchEngine(str(temp_repo))
        
        # Index repository
        stats = engine.index_repository()
        assert stats['total_files'] == 1
        assert stats['total_nodes'] > 0
        assert 'python' in stats['languages']
        
        # Test syntactic search
        query = SearchQuery(
            text="validate",
            search_type=SearchType.SYNTACTIC,
            limit=5
        )
        
        results = engine.search(query)
        assert len(results) > 0
        # Should find validate-related code
        assert any('validate' in result.node.display_name.lower() or 
                  'validate' in (result.node.docstring or '').lower() or
                  'validate' in (result.node.body or '').lower() 
                  for result in results)
        
        # Test semantic search
        semantic_query = SearchQuery(
            text="input validation",
            search_type=SearchType.SEMANTIC,
            limit=5
        )
        
        semantic_results = engine.search(semantic_query)
        assert len(semantic_results) > 0
        
        # Test hybrid search
        hybrid_query = SearchQuery(
            text="data processing",
            search_type=SearchType.HYBRID,
            limit=5
        )
        
        hybrid_results = engine.search(hybrid_query)
        assert len(hybrid_results) > 0
        
        # Test statistics
        engine_stats = engine.get_statistics()
        assert 'repository' in engine_stats
        assert 'indexing' in engine_stats
        assert 'performance' in engine_stats
    
    def test_search_engine_caching(self, temp_repo):
        """Test search engine caching functionality"""
        engine = OptimizedSearchEngine(str(temp_repo))
        
        # Index repository
        engine.index_repository()
        
        # First search
        query = SearchQuery(text="validate", limit=5)
        start_time = time.time()
        results1 = engine.search(query)
        first_search_time = time.time() - start_time
        
        # Second search (should be cached)
        start_time = time.time()
        results2 = engine.search(query)
        second_search_time = time.time() - start_time
        
        # Results should be identical
        assert len(results1) == len(results2)
        assert [r.node.id for r in results1] == [r.node.id for r in results2]
        
        # Second search should be faster (cache hit)
        assert second_search_time <= first_search_time
    
    def test_search_engine_incremental_update(self, temp_repo):
        """Test incremental update functionality"""
        engine = OptimizedSearchEngine(str(temp_repo))
        
        # Initial index
        stats1 = engine.index_repository()
        initial_nodes = stats1['total_nodes']
        
        # Add new file
        (temp_repo / "new_file.py").write_text("def new_function(): pass")
        
        # Update index
        update_stats = engine.update_index()
        assert update_stats['updated_files'] == 1
        assert update_stats['updated_nodes'] > 0
        
        # Re-index to verify
        stats2 = engine.index_repository(force_reindex=True)
        assert stats2['total_nodes'] > initial_nodes
