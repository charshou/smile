# LISTS/LINK

class Link:
    empty = None

    def __init__(self, val, prev=empty):  # reverse linked list
        if isinstance(prev, Link):
            self.prev = prev
        elif prev is Link.empty:
            self.prev = Link.empty
        else:
            self.prev = Link(prev)
        self.val = val

    def get(self, i):
        if i >= len(self):
            return None
        index = len(self) - 1 - i
        while index > 0:
            self = self.prev
            index -= 1
        return self.val

    def __repr__(self):
        string = ")"
        while not self.prev is Link.empty:
            string = " " + str(self.val) + string
            self = self.prev
        return "(" + str(self.val) + string

    def __len__(self):
        if self.prev is Link.empty:
            return 1
        return 1 + len(self.prev)