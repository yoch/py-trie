import collections.abc

class End:
    # used for internal representation only
    def __repr__(self):
        return '$'


_END = End()    # sentinel (end of key)



#TODO: implement pattern search
#TODO: implement proper copy
#TODO: implement sortest and longest prefix lookups
#TODO: implement pop and setdefault for efficiency

class Trie(collections.abc.MutableMapping):
    "keys must be a sequence"

    _NodeFactory = dict
    _KeyFactory = tuple

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

    @classmethod
    def _get_size(cls, node):
        # maybe replaced by nodes which store size ?
        return sum(1 if k is _END else cls._get_size(nd) for k, nd in node.items())

    def __init__(self, **kwargs):
        self._root = self._NodeFactory()
        self._size = 0
        # initialize values
        for key, value in kwargs.items():
            self[key] = value

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
        def rec_del(node, i=0):
            if i == len(key):
                node.pop(_END)
            else:
                k = key[i]
                nd = node[k]
                rec_del(nd, i + 1)
                if not nd:
                    node.pop(k)
        try:
            rec_del(self._root)
            self._size -= 1
        except KeyError:
            raise KeyError(key) from None

    def __getitem__(self, key):
        try:
            node = self._root
            for sym in key:
                node = node[sym]
            return node[_END]
        except KeyError:
            raise KeyError(key) from None

    def update(self, other):
        # efficient update: merge trie 2 to trie 1
        def merge(t1, t2):
            for k, nd in t2.items():
                if k in t1 and k is not _END:
                    merge(t1[k], nd)
                else:
                    t1[k] = nd
        merge(self._root, other._root)
        self._size += other._size

    def clear(self):
        # clear directly all the trie
        self._root.clear()
        self._size = 0

    def __iter__(self):
        return iter(k for k, v in self.items())

    def items(self, prefix=None):
        if prefix is None:
            return self._iterate_items(self._root, [])
        else:
            root = self._get_subtrie(prefix)
            return self._iterate_items(root, list(prefix))

    def keys(self, prefix=None):
        return iter(k for k, v in self.items(prefix))

    def values(self, prefix=None):
        # more efficient than use items
        root = self._root if prefix is None else self._get_subtrie(prefix)
        return self._iterate_values(root)

    def remove(self, prefix):
        parent, node = None, self._root
        for k in prefix:
            parent, node = node, node[k]
        del parent[k]
        self._size -= self._get_size(node)

    def _get_subtrie(self, prefix):
        try:
            nd = self._root
            for sym in prefix:
                nd = nd[sym]
            return nd
        except KeyError:
            raise KeyError(prefix) from None

    def __repr__(self):
        return self.__class__.__name__ + '()'



class StringTrie(Trie):
    _KeyFactory = ''.join



class DefaultTrie(Trie):
    "same as defaultdict, but for tries"

    def __getitem__(self, key):
        try:
            value = super().__getitem__(key)
        except KeyError:
            self[key] = value = self.default_factory()
        return value

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self.default_factory) + ')'


# factory function
def defaulttrie(typ):
    mapping = DefaultTrie()
    mapping.default_factory = typ
    return mapping
