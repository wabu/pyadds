from collections import Counter

from .str import splitcamel

all = ['Modular', 'Co']


class Modular:
    """
    This type adds a simple class method to your class, allowing you to easily
    create new types by combining types at runtime.

    This is most helpfull for ABCs and other cooperative class hierarchies
    with exchangable implemnetations of some aspects of the hierarchie.

    >>> class A(Modular):
    ...     def foo(self):
    ...         return self.bar()
    ... class B:
    ...     def bar(self):
    ...         return 'b'
    ... class C:
    ...     def bar(self):
    ...         return 'c'

    >>> for i in range(2):
    ...     a = A.__with__(C if i else B)()
    ...     print(a.__class__.__name__+':', a.foo())
    A[B]: b
    A[C]: c
    """

    @classmethod
    def __with__(*classes):
        """
        create a dynamic type with the supplied classes as bases
        """
        return Co[classes]

    @classmethod
    def __using__(cls, *classes):
        """
        create a dynamic type with the supplied classes mixed onto this class
        """
        return Co[classes+(cls,)]


def extract_commons(limit, *lists):
    words = Counter()
    for lst in lists:
        words.update(lst)
    common = []
    for word, n in words.most_common():
        if n <= limit:
            break
        common.append(word)
    return common


def remove_common(common, *lists):
    for lst in lists:
        for elem in common:
            if elem in lst:
                lst.remove(elem)
    return lists


def base_names(cls):
    if ':' in cls.__name__:
        for base in cls.__bases__:
            yield from base_names(base)
    else:
        yield cls.__name__


class MetaWith(type):
    @staticmethod
    def __getitem__(classes):
        bases = Counter()
        for cls in classes:
            for base in cls.mro():
                if base in [Modular, object, type]:
                    break
                bases[base] += 1
        base = bases.most_common(1)[0][0]
        splits = [[split.capitalize() for split in splitcamel(name)]
                  for cls in classes for name in base_names(cls)]
        common = extract_commons(len(classes) // 2,
                                 splitcamel(base.__name__), *splits)

        if not common:
            common = [split.capitalize() for split in splitcamel(base.__name__)]
        short = ','.join(filter(len,
                                map(''.join, remove_common(common, *splits))))
        name = ''.join(common) + '[' + short + ']'
        return type(name, classes, {})

    def __or__(self, other):
        return self[other]


class Co(metaclass=MetaWith):
    """
    way to create compound classes
    >>> Co[AClass, BClass]
    ABClass
    """
