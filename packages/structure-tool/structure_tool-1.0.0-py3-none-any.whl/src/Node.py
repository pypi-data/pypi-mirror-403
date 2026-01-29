class Node():
    def __init__(self, data):
        self.data = data
        self.next = None
class DoubleNode():
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None
class TreeNode:
    def __init__(self, data):
        self.data = data
        self.children = []
        self.parent = None
    def __str__(self):
        return str(self.data)
    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)
    def remove_child(self, child_node):
        if child_node in self.children:
            child_node.parent = None
            self.children.remove(child_node)
    def get_level(self):
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level
    def print_tree(self, level=None):
        prefix = "  " * self.get_level() + "|__" if self.get_level() > 0 else ""
        print(prefix + str(self.data))
        if level is None or self.get_level() < level:
            for child in self.children:
                child.print_tree(level)
class BinaryTreeNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.parent = None
    def __str__(self):
        return str(self.value)
    def insert_left(self, value):
        if self.left is None:
            self.left = BinaryTreeNode(value)
            self.left.parent = self
        else:
            new_node = BinaryTreeNode(value)
            new_node.left = self.left
            self.left.parent = new_node
            self.left = new_node
            new_node.parent = self
    def insert_right(self, value):
        if self.right is None:
            self.right = BinaryTreeNode(value)
            self.right.parent = self
        else:
            new_node = BinaryTreeNode(value)
            new_node.right = self.right
            self.right.parent = new_node
            self.right = new_node
            new_node.parent = self
    def get_height(self):
        left_height = self.left.get_height() if self.left else 0
        right_height = self.right.get_height() if self.right else 0
        return 1 + max(left_height, right_height)