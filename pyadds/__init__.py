class AnythingType(set):
    def __contains__(self, other):
        return True

    def intersection(self, other):
        return other

    def union(self, other):
        return self

    def __str__(self):
        return '*'

    def __repr__(self):
        return "Anything"

Anything = AnythingType()
