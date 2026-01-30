class Any:
    "Object that is considered equal to any object of the given type"

    def __init__(self, type_):
        self.type_ = type_

    def __eq__(self, other):
        return isinstance(other, self.type_)
