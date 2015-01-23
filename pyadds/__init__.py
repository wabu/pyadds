class AnythingType:
    def __contains__(self, other):
        return True

    def __str__(self):
        return '*'

    def __repr__(self):
        return "Anything"

Anything = AnythingType()
