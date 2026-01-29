class stick():
    def __init__(self):
        self.datas = []
    def append(self, data):
        self.datas.append(data)
    def pop(self):
        self.datas.pop()
    def out(self):
        return "\n^\n|\n".join(map(str, self.datas))
    def get(self):
        return self.datas