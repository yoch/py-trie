import collections.abc

class End:
    # used for internal representation only
    def __repr__(self):
        return '$'


_END = End()    # sentinel (end of key)

_node = dict    # node factory, currently simple dict


def _iterate_values(node):
    for k, v in node.items():
        if k is not _END:
            yield from _iterate_values(v)
        else:
            yield v

def _iterate_items(node, lkey):
    if _END in node:
        yield tuple(lkey), node[_END]
    lkey.append(None)   # placeholder
    for k, d in node.items():
        if k is not _END:
            lkey[-1] = k
            yield from _iterate_items(d, lkey)
    lkey.pop()


#TODO: implement pattern search
#TODO: implement delete subtrie by prefix
#TODO: implement proper copy
#TODO: implement sortest and longest prefix lookups
#TODO: implement pop and setdefault for efficiency

class Trie(collections.abc.MutableMapping):
    "keys must be a sequence"

    __slots__ = ('_root', '_size')

    def __init__(self, **kwargs):
        self._root = _node()
        self._size = 0
        # initialize values
        for key, value in kwargs.items():
            self[key] = value

    def __len__(self):
        return self._size

    def __setitem__(self, key, val):
        node = self._root
        for sym in key:
            node = node.setdefault(sym, _node())
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
        lpre = [] if prefix is None else list(prefix)
        root = self._root if prefix is None else self._get_subtrie(prefix)
        return _iterate_items(root, lpre)

    def keys(self, prefix=None):
        return iter(k for k, v in self.items(prefix))

    def values(self, prefix=None):
        # more efficient than use items
        root = self._root if prefix is None else self._get_subtrie(prefix)
        return _iterate_values(root)

    def _getsize(self):
        # maybe replaced by nodes which store size
        def rec_count(node):
            return sum(1 if k is _END else rec_count(nd) for k, nd in node.items())
        return rec_count(self._root)

    def _get_subtrie(self, prefix):
        try:
            nd = self._root
            for sym in prefix:
                nd = nd[sym]
            return nd
        except KeyError:
            raise KeyError(prefix) from None

    #def __repr__(self):
        #return repr(self._root)



class DefaultTrie(Trie):
    "same as defaultdict, but for tries"

    __slots__ = ('_default')

    def __init__(self, default_factory):
        self._default = default_factory

    def __getitem__(self, key):
        try:
            value = super().__getitem__(key)
        except KeyError:
            self[key] = value = self._default()
        return value
