"""
Tests for Tree Adapter Module
"""

import pytest
from src.tree_adapter import (
    TreeNode,
    NodeType,
    TreeBuilder,
    TreeNavigator,
    APITreeAdapter,
)


class TestTreeNode:
    """Tests for TreeNode"""

    def test_create_leaf_node(self):
        node = TreeNode(
            name="email",
            path="$.user.email",
            node_type=NodeType.LEAF,
            value="test@example.com"
        )
        assert node.name == "email"
        assert node.node_type == NodeType.LEAF
        assert node.value == "test@example.com"

    def test_add_child(self):
        parent = TreeNode(name="parent", path="$", node_type=NodeType.BRANCH)
        child = TreeNode(name="child", path="$.child", node_type=NodeType.LEAF)
        parent.add_child(child)
        
        assert len(list(parent.children())) == 1
        assert child.parent() == parent

    def test_find_in_tree(self):
        root = TreeNode(name="root", path="$", node_type=NodeType.ROOT)
        child1 = TreeNode(name="users", path="$.users", node_type=NodeType.ARRAY)
        child2 = TreeNode(name="config", path="$.config", node_type=NodeType.OBJECT)
        root.add_child(child1)
        root.add_child(child2)
        
        results = root.find(lambda n: n.node_type == NodeType.ARRAY)
        assert len(results) == 1
        assert results[0].name == "users"

    def test_to_dict(self):
        node = TreeNode(
            name="test",
            path="$.test",
            node_type=NodeType.LEAF,
            value=42
        )
        d = node.to_dict()
        assert d["name"] == "test"
        assert d["value"] == 42
        assert d["type"] == "leaf"


class TestTreeBuilder:
    """Tests for TreeBuilder"""

    def test_build_from_simple_dict(self):
        data = {"name": "John", "age": 30}
        tree = TreeBuilder.from_json(data, "user")
        
        assert tree.name == "user"
        assert tree.node_type == NodeType.OBJECT
        assert len(list(tree.children())) == 2

    def test_build_from_nested_dict(self):
        data = {
            "user": {
                "profile": {
                    "name": "John"
                }
            }
        }
        tree = TreeBuilder.from_json(data)
        nav = TreeNavigator(tree)
        
        name_nodes = nav.find_by_name("name")
        assert len(name_nodes) == 1
        assert name_nodes[0].value == "John"

    def test_build_from_array(self):
        data = {"items": [1, 2, 3]}
        tree = TreeBuilder.from_json(data)
        nav = TreeNavigator(tree)
        
        items_node = nav.find_by_name("items")[0]
        assert items_node.node_type == NodeType.ARRAY
        assert items_node.metadata["length"] == 3

    def test_build_from_complex_structure(self):
        data = {
            "users": [
                {"id": 1, "name": "Jan"},
                {"id": 2, "name": "Anna"},
            ],
            "meta": {"total": 2}
        }
        tree = TreeBuilder.from_json(data)
        nav = TreeNavigator(tree)
        
        # Find all name nodes
        names = nav.find_by_name("name")
        assert len(names) == 2
        
        # Find all leaves
        leaves = nav.get_leaves()
        assert len(leaves) == 5  # 2x id, 2x name, 1x total


class TestTreeNavigator:
    """Tests for TreeNavigator"""

    @pytest.fixture
    def sample_tree(self):
        data = {
            "data": {
                "users": [
                    {"id": 1, "name": "Jan", "email": "jan@example.com"},
                    {"id": 2, "name": "Anna", "email": "anna@example.com"},
                ]
            },
            "meta": {"total": 2, "page": 1}
        }
        tree = TreeBuilder.from_json(data, "response")
        return TreeNavigator(tree)

    def test_find_by_name(self, sample_tree):
        nodes = sample_tree.find_by_name("email")
        assert len(nodes) == 2
        values = [n.value for n in nodes]
        assert "jan@example.com" in values
        assert "anna@example.com" in values

    def test_find_by_type(self, sample_tree):
        arrays = sample_tree.find_by_type(NodeType.ARRAY)
        assert len(arrays) == 1
        assert arrays[0].name == "users"

    def test_find_by_value(self, sample_tree):
        nodes = sample_tree.find_by_value(2)
        assert len(nodes) >= 1

    def test_search(self, sample_tree):
        nodes = sample_tree.search("user")
        assert len(nodes) >= 1

    def test_get_leaves(self, sample_tree):
        leaves = sample_tree.get_leaves()
        assert len(leaves) == 8  # id, name, email x2 + total, page

    def test_get_branches(self, sample_tree):
        branches = sample_tree.get_branches()
        assert len(branches) >= 3  # data, users, meta


class TestAPITreeAdapter:
    """Tests for APITreeAdapter"""

    def test_add_response(self):
        adapter = APITreeAdapter()
        data = {"users": [{"id": 1}]}
        
        nav = adapter.add_response("users_response", data)
        assert nav is not None
        assert "users_response" in adapter.list_trees()

    def test_get_navigator(self):
        adapter = APITreeAdapter()
        adapter.add_response("test", {"key": "value"})
        
        nav = adapter.get_navigator("test")
        assert nav is not None
        
        nav2 = adapter.get_navigator("nonexistent")
        assert nav2 is None

    def test_multiple_responses(self):
        adapter = APITreeAdapter()
        adapter.add_response("response1", {"a": 1})
        adapter.add_response("response2", {"b": 2})
        
        assert len(adapter.list_trees()) == 2
