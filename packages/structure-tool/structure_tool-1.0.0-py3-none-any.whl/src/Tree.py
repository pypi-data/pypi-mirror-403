from Node import TreeNode, BinaryTreeNode
class Tree:
    def __init__(self, root_data=None):
        if root_data:
            self.root = TreeNode(root_data)
        else:
            self.root = None
    def is_empty(self):
        return self.root is None
    def get_depth(self):
        return self._calculate_depth(self.root)
    def _calculate_depth(self, node):
        if node is None:
            return 0
        if not node.children:
            return 1
        max_child_depth = 0
        for child in node.children:
            child_depth = self._calculate_depth(child)
            max_child_depth = max(max_child_depth, child_depth)
        return 1 + max_child_depth
    def find_node(self, data, node=None):
        if node is None:
            node = self.root
        if node.data == data:
            return node
        for child in node.children:
            found = self.find_node(data, child)
            if found:
                return found
        return None
    def get_leaves(self):
        leaves = []
        self._collect_leaves(self.root, leaves)
        return leaves
    def _collect_leaves(self, node, leaves):
        if not node.children:
            leaves.append(node)
        else:
            for child in node.children:
                self._collect_leaves(child, leaves)
class BinaryTree:
    def __init__(self, root_value=None):
        if root_value is not None:
            self.root = BinaryTreeNode(root_value)
        else:
            self.root = None
    
    def preorder_traversal(self, node=None):
        if node is None:
            node = self.root
            result = []
            self._preorder(node, result)
            return result
        return self._preorder(node, [])
    
    def _preorder(self, node, result):
        if node:
            result.append(node.value)
            self._preorder(node.left, result)
            self._preorder(node.right, result)
    def inorder_traversal(self):
        result = []
        self._inorder(self.root, result)
        return result
    
    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append(node.value)