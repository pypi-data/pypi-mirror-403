class queue():
    def __init__(self):
        self.datas = []
    def append(self, data):
        self.datas.append(data)
    def pop(self):
        self.datas.pop(0)
    def out(self):
        return ' <- '.join(map(str, self.datas))
    def get(self):
        return self.datas