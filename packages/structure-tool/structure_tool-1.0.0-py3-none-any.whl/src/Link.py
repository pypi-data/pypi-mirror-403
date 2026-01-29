from Node import Node, DoubleNode
class LinkNode():
    def __init__(self):
        self.head = None
    def append(self, data):
        if self.head:
            new_Node = Node(data)
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = new_Node
        else:
            self.head = Node(data)
    def delete(self, data):
        if not self.head:
            return
        if self.head.data == data:
            self.head = self.head.next
            return
        cur = self.head
        while cur.next:
            prev, cur = cur, cur.next
            if cur.data == data:
                prev.next = cur.next
                return
    def pop(self, loc):
        if not self.head:
            return
        cur = self.head
        co = 1
        while co <= loc:
            prev, cur = cur, cur.next
            co += 1
        prev.next = cur.next
    def insert(self, data, loc):
        new_Node = Node(data)
        if loc <= 1 or not self.head:
            new_Node.next = self.head
            self.head = new_Node
            return
        cur = self.head
        co = 1
        while co < loc:
            prev, cur = cur, cur.next
            co += 1
        prev.next = new_Node
        new_Node.next = cur
    def index(self, data):
        if not self.head:
            return -1
        cur = self.head
        co = 1
        while cur.next:
            if cur.data == data:
                return co
            cur = cur.next
            co += 1
        return -1
    def find(self, key):
        if not self.head:
            return
        cur = self.head
        co = 1
        while co < key:
            cur = cur.next
            if not cur:
                return
            co += 1
        return cur.data
    def out(self):
        if not self.head:
            return
        cur = self.head
        result = []
        while cur:
            result.append(str(cur.data))
            cur = cur.next
        return ' -> '.join(result)
class DoubleNodeLink():
    def __init__(self):
        self.head = None
    def append(self, data):
        new_node = DoubleNode(data)
        if self.head:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = new_node
            new_node.prev = cur
        else:
            self.head = new_node
    def delete(self, data):
        if not self.head:
            return
        cur = self.head
        while cur.data != data:
            prev, cur = cur, cur.next
        if not cur:
            return
        if cur == self.head:
            cur.next.prev = None
            return
        prev.next = cur.next
        if cur.next:
            cur.next.prev = prev
    def pop(self, loc):
        if not self.head:
            return
        cur = self.head
        co = 1
        while co < loc:
            prev, cur = cur, cur.next
            co += 1
        if not cur:
            return
        prev.next = cur.next
        if cur.next:
            cur.next.prev = prev
    def insert(self, data, key):
        new_node = DoubleNode(data)
        if key <= 1 or not self.head:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
            return
        cur = self.head
        co = 1
        while co < key:
            prev, cur = cur, cur.next
            co += 1
        prev.next = new_node
        new_node.prev = prev
        new_node.next = cur
        cur.prev = new_node
    def index(self, data):
        if not self.head:
            return -1
        cur = self.head
        co = 1
        while cur.next:
            if cur.data == data:
                return co
            cur = cur.next
            co += 1
        return -1
    def find(self, key):
        if not self.head:
            return
        cur = self.head
        co = 1
        while co < key:
            cur = cur.next
            if not cur:
                return
            co += 1
        return cur.data
    def out(self):
        if not self.head:
            return
        cur = self.head
        result = []
        while cur:
            result.append(str(cur.data))
            cur = cur.next
        return ' <-> '.join(result)