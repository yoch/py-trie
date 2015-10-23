import collections.abc

class End:
    # used for internal representation only
    def __repr__(self):
        return '$'
    def __reduce__(self):
        return '_END'


_END = End()    # sentinel (end of key)


#TODO: implement proper copy
#TODO: implement sortest and longest prefix lookups
#TODO: implement pattern search ?

# avoid using collections.abc implementation
# because it use __getitem__ for get, pop, setdefault
# and __contains__, which breaks DefaultTrie

class Trie:
    "keys must be a sequence"

    _NodeFactory = dict
    _KeyFactory = tuple
    __marker = object()

    @classmethod
    def _iterate_values(cls, node):
        for k, v in node.items():
            if k is not _END:
                yield from cls._iterate_values(v)
            else:
                yield v

    @classmethod
    def _iterate_items(cls, node, lkey):
        nlkey = lkey + [None]   # placeholder
        for k, v in node.items():
            if k is _END:
                yield cls._KeyFactory(lkey), v
            else:
                nlkey[-1] = k
                yield from cls._iterate_items(v, nlkey)

    @staticmethod
    def _get_size(node):
        # maybe replaced by nodes which store size ?
        return sum(1 if k is _END else Trie._get_size(nd) for k, nd in node.items())

    def _get_subtrie(self, prefix):
        try:
            nd = self._root
            for sym in prefix:
                nd = nd[sym]
            return nd
        except KeyError:
            # return Node object ?
            return None

    def __get(self, key):
        node = self._root
        for sym in key:
            node = node[sym]
        return node[_END]

    def __pop(self, key):
        def rec_pop(node, i=0):
            if i == len(key):
                ret = node.pop(_END)
                self._size -= 1
                return ret
            else:
                k = key[i]
                nd = node[k]
                ret = rec_pop(nd, i + 1)
                if not nd:
                    del node[k]
                return ret
        return rec_pop(self._root)

    def __init__(self, *args, **kwargs):
        self._root = self._NodeFactory()
        self._size = 0
        # initialize values
        self.update(*args, **kwargs)

    def __len__(self):
        return self._size

    def __setitem__(self, key, val):
        node = self._root
        for sym in key:
            node = node.setdefault(sym, self._NodeFactory())
        if _END not in node:
            self._size += 1
        node[_END] = val

    def __delitem__(self, key):
        try:
            self.__pop(key)
        except KeyError:
            raise KeyError(key) from None

    def __getitem__(self, key):
        try:
            return self.__get(key)
        except KeyError:
            raise KeyError(key) from None

    def __contains__(self, key):
        try:
            node = self._root
            for sym in key:
                node = node[sym]
            return _END in node
        except KeyError:
            return False

    def __iter__(self):
        return iter(k for k, v in self.items())

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self._root == other._root

    def __ne__(self, other):
        return not (self == other)

    def get(self, key, default=None):
        try:
            return self.__get(key)
        except KeyError:
            return default

    def pop(self, key, default=__marker):
        try:
            return self.__pop(key)
        except KeyError:
            if default is self.__marker:
                raise KeyError(key) from None
            return default

    def setdefault(self, key, default=None):
        try:
            return self.__get(key)
        except KeyError:
            self[key] = default
            return default

    def update(self, *args, **kwargs):
        # efficient merge trie 2 to trie 1
        def merge(t1, t2):
            for k, nd in t2.items():
                if k in t1 and k is not _END:
                    merge(t1[k], nd)
                else:
                    t1[k] = nd
        other = args[0] if len(args) >= 1 else ()
        if isinstance(other, Trie):
            merge(self._root, other._root)
            self._size += other._size
        elif isinstance(other, collections.abc.Mapping):
            for key in other:
                self[key] = other[key]
        else:
            for key, value in other:
                self[key] = value
        # update kwargs
        for key, value in kwargs.items():
            self[key] = value

    def clear(self):
        # clear directly the whole trie
        self._root.clear()
        self._size = 0

    def items(self, prefix=None):
        if prefix is None:
            yield from self._iterate_items(self._root, [])
        else:
            root = self._get_subtrie(prefix)
            if root:
                yield from self._iterate_items(root, list(prefix))

    def keys(self, prefix=None):
        return iter(k for k, v in self.items(prefix))

    def values(self, prefix=None):
        # more efficient than use items
        root = self._root if prefix is None else self._get_subtrie(prefix)
        if root:
            yield from self._iterate_values(root)

    #TODO: return subtrie ?
    def remove(self, prefix):
        try:
            parent, node = None, self._root
            for k in prefix:
                parent, node = node, node[k]
            del parent[k]
            self._size -= self._get_size(node)
        except KeyError:
            pass

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, dict(self))



class StringTrie(Trie):
    _KeyFactory = ''.join



import operator

class SortedTrie(Trie):
    "trie implementation with iterators in lexicographic keys order"

    @staticmethod
    def _iter_nodes_sorted(node):
        yield from sorted([(k, v) for k, v in node.items() if k is not _END],
                          key=operator.itemgetter(0))

    @classmethod
    def _iterate_values(cls, node):
        if _END in node:
            yield node[_END]
        for k, v in cls._iter_nodes_sorted(node):
            yield from cls._iterate_values(v)

    @classmethod
    def _iterate_items(cls, node, lkey):
        if _END in node:
            yield cls._KeyFactory(lkey), node[_END]
        nlkey = lkey + [None]   # placeholder
        for k, v in cls._iter_nodes_sorted(node):
            nlkey[-1] = k
            yield from cls._iterate_items(v, nlkey)


class DefaultTrie(Trie):
    "same as defaultdict, but for tries"

    def __init__(self, default_factory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            value = super().__getitem__(key)
        except KeyError:
            self[key] = value = self.default_factory()
        return value

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self.default_factory) + ')'
