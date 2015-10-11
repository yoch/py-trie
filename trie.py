import collections.abc

# used for internal representation only
class End:
    def __repr__(self):
        return '$'

_END = End()
_node = dict    # node factory, currently simple dict


#TODO: implement prefix and pattern
#TODO: implement delete subtrie by prefix
#TODO: implement proper copy
#TODO: implement sortest and longest prefix lookups ?
#TODO: maybe implement pop and setdefault for efficiency ?

class Trie(collections.abc.MutableMapping):
    "keys must be a sequence"

    __slots__ = ('_root', '_size')

    def __init__(self):
        self._root = _node()
        self._size = 0

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

##    def __contains__(self, key):
##        node = self._root
##        for sym in key:
##            if sym not in node:
##                return False
##            else:
##                node = node[sym]
##        return _END in node

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

    def iter_items(self):
        def iterate(node, lkey):
            if _END in node:
                yield tuple(lkey), node[_END]
            lkey = lkey + [None]
            for k, d in node.items():
                if k is not _END:
                    lkey[-1] = k
                    yield from iterate(d, lkey)
        return iterate(self._root, [])

    def iter_keys(self):
        return iter(k for k, v in self.iter_items())

    def __iter__(self):
        return self.iter_keys()

    def iter_values(self):
        # more efficient than use iter_items()
        def iterate(node):
            for k, v in node.items():
                if k is not _END:
                    yield from iterate(v)
                else:
                    yield v
        return iterate(self._root)

    def _getsize(self):
        # costly operation, may be replaced by nodes which store size
        def rec_count(node):
            return sum(1 if k is _END else rec_count(nd) for k, nd in node.items())
        return rec_count(self._root)

##    def subtrie(self, prefix):
##        nd = self._root
##        for sym in prefix:
##            if sym in nd:
##                nd = nd[sym]
##            else:
##                nd = _node()
##                break
##        # mauvais...
##        retval = Trie()
##        retval._root = nd
##        retval._size = retval._getsize()
##        return retval


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
