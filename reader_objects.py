class Token:
    def __init__(self, ty, val):
        self.type = ty
        self.val = val

    def __repr__(self):
        return "{type} - {val}".format(type=self.type, val=self.val)
    
class Node:
    def __init__(self, val, left=None, right=None):
        from smile import SmileError
        
        if type(left) != type(right):  # left, right both either None or Node
            raise SmileError("malformed nodes :^(")
        self.left = left
        self.right = right
        self.val = val

    def is_leaf(self):
        return self.left is None and self.right is None

    def __repr__(self):
        return (
            "({left} << {val} >> {right})".format(
                left=self.left, val=self.val, right=self.right
            )
            if self.left
            else "({val})".format(val=self.val)
        )