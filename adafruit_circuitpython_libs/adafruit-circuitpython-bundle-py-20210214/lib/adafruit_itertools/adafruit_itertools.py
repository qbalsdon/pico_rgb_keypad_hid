# SPDX-FileCopyrightText: 2001-2019 Python Software Foundation
#
# SPDX-License-Identifier: PSF-2.0

"""
`adafruit_itertools`
================================================================================

Python's itertools adapted for CircuitPython by Dave Astels

Copyright 2001-2019 Python Software Foundation; All Rights Reserved

* Author(s): The PSF and Dave Astels

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""
# pylint:disable=invalid-name,redefined-builtin,attribute-defined-outside-init
# pylint:disable=stop-iteration-return,anomalous-backslash-in-string

__version__ = "1.1.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Itertools.git"


def accumulate(iterable, func=lambda x, y: x + y):
    """Make an iterator that returns accumulated sums, or accumulated
    results of other binary functions (specified via the optional func
    argument). If func is supplied, it should be a function of two
    arguments that returns a value. Elements of the input iterable may
    be any type that can be accepted as arguments to func.  (For
    example, with the default operation of addition, elements may be any
    addable type including Decimal or Fraction.) If the input iterable
    is empty, the output iterable will also be empty.

    :param iterable: the source of values to be accumulated
    :param func: the function to combine the accumulated value with the next one"""
    it = iter(iterable)
    try:
        acc = next(it)
    except StopIteration:
        return
    yield acc
    for element in it:
        acc = func(acc, element)
        yield acc


def chain(*iterables):
    """Make an iterator that returns elements from the first iterable until it
    is exhausted, then proceeds to the next iterable, until all of the iterables
    are exhausted. Used for treating consecutive sequences as a single sequence.

    :param p: a list of iterable from which to yield values

    """
    # chain('ABC', 'DEF') --> A B C D E F
    for i in iterables:
        yield from i


def chain_from_iterable(iterables):
    """Alternate constructor for chain(). Gets chained inputs from a
    single iterable argument that is evaluated lazily.

    :param iterables: an iterable of iterables

    """
    # chain_from_iterable(['ABC', 'DEF']) --> A B C D E F
    for it in iterables:
        for element in it:
            yield element


def combinations(iterable, r):
    """Return r length subsequences of elements from the input iterable.
    Combinations are emitted in lexicographic sort order. So, if the input
    iterable is sorted, the combination tuples will be produced in sorted order.

    Elements are treated as unique based on their position, not on their value.
    So if the input elements are unique, there will be no repeat values in each
    combination.

    :param iterable: the iterable containing the the items to combine
    :param r: the length of the resulting combinations

    """
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(pool[i] for i in indices)
    while True:
        index = 0
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                index = i
                break
        else:
            return
        indices[index] += 1
        for j in range(index + 1, r):
            indices[j] = indices[j - 1] + 1
        yield tuple(pool[i] for i in indices)


def combinations_with_replacement(iterable, r):
    """Return r length subsequences of elements from the input iterable allowing
    individual elements to be repeated more than once.

    Combinations are emitted in lexicographic sort order. So, if the input
    iterable is sorted, the combination tuples will be produced in sorted order.

    Elements are treated as unique based on their position, not on their value.
    So if the input elements are unique, the generated combinations will also be
    unique.

    :param iterable: the iterable containing the the items to combine
    :param r: the length of the resulting combinations

    """
    # combinations_with_replacement('ABC', 2) --> AA AB AC BB BC CC
    pool = tuple(iterable)
    n = len(pool)
    if not n and r:
        return
    indices = [0] * r
    yield tuple(pool[i] for i in indices)
    while True:
        index = 0
        for i in reversed(range(r)):
            if indices[i] != n - 1:
                index = i
                break
        else:
            return
        indices[index:] = [indices[index] + 1] * (r - index)
        yield tuple(pool[i] for i in indices)


def compress(data, selectors):
    """Make an iterator that filters elements from data returning only those
    that have a corresponding element in selectors that evaluates to True.
    Stops when either the data or selectors iterables has been exhausted.

    :param data: the source of values
    :param selector: the source of selection values

    """
    # compress('ABCDEF', [1,0,1,0,1,1]) --> A C E F
    return (d for d, s in zip(data, selectors) if s)


def count(start=0, step=1):
    """Make an iterator that returns evenly spaced values starting with number
    start. Often used as an argument to map() to generate consecutive data
    points. Also, used with zip() to add sequence numbers.

    :param start: the initial value of the sequence
    :param step: how far apart subsequent values are

    """
    while True:
        yield start
        start += step


def cycle(p):
    """Make an iterator returning elements from the iterable and saving a copy
    of each. When the iterable is exhausted, return elements from the saved
    copy. Repeats indefinitely.

    :param p: the iterable from which to yield elements

    """
    try:
        len(p)
    except TypeError:
        # len() is not defined for this type. Assume it is
        # a finite iterable so we must cache the elements.
        cache = []
        for i in p:
            yield i
            cache.append(i)
        p = cache
    while p:
        yield from p


def dropwhile(predicate, iterable):
    """Make an iterator that drops elements from the iterable as long as the
    predicate is true; afterwards, returns every element. Note, the iterator
    does not produce any output until the predicate first becomes false, so it
    may have a lengthy start-up time.

    :param predicate: used to test each element until it returns False
    :param iterable: source of values

    """
    # dropwhile(lambda x: x<5, [1,4,6,4,1]) --> 6 4 1
    iterable = iter(iterable)
    for x in iterable:
        if not predicate(x):
            yield x
            break
    for x in iterable:
        yield x


def filterfalse(predicate, iterable):
    """Make an iterator that filters elements from iterable returning only those
    for which the predicate is False. If predicate is None, return the items
    that are false.

    :param predicate: used to test each value
    :param iterable: source of values

    """
    # filterfalse(lambda x: x%2, range(10)) --> 0 2 4 6 8
    if predicate is None:
        predicate = bool
    for x in iterable:
        if not predicate(x):
            yield x


class groupby:
    """Make an iterator that returns consecutive keys and groups from the

    iterable. The key is a function computing a key value for each element. If
    not specified or is None, key defaults to an identity function and returns
    the element unchanged. Generally, the iterable needs to already be sorted
    on the same key function.

    The operation of groupby() is similar to the uniq filter in Unix. It
    generates a break or new group every time the value of the key
    function changes (which is why it is usually necessary to have
    sorted the data using the same key function). That behavior differs
    from SQL’s GROUP BY which aggregates common elements regardless of
    their input order.

    The returned group is itself an iterator that shares the underlying
    iterable with groupby(). Because the source is shared, when the
    groupby() object is advanced, the previous group is no longer
    visible. So, if that data is needed later, it should be stored as a
    list.

    :param iterable: the source of values
    :param key: the key computation function (default is None)

    """

    # [k for k, g in groupby('AAAABBBCCDAABBB')] --> A B C D A B
    # [list(g) for k, g in groupby('AAAABBBCCD')] --> AAAA BBB CC D

    def __init__(self, iterable, key=None):
        if key is None:
            key = lambda x: x
        self.keyfunc = key
        self.it = iter(iterable)
        self.tgtkey = self.currkey = self.currvalue = object()

    def __iter__(self):
        return self

    def __next__(self):
        self.id = object()
        while self.currkey == self.tgtkey:
            self.currvalue = next(self.it)  # Exit on StopIteration
            self.currkey = self.keyfunc(self.currvalue)
        self.tgtkey = self.currkey
        return (self.currkey, self._grouper(self.tgtkey, self.id))

    def _grouper(self, tgtkey, id):
        while self.id is id and self.currkey == tgtkey:
            yield self.currvalue
            try:
                self.currvalue = next(self.it)
            except StopIteration:
                return
            self.currkey = self.keyfunc(self.currvalue)


def islice(p, start, stop=(), step=1):
    """Make an iterator that returns selected elements from the
    iterable. If start is non-zero and stop is unspecified, then the
    value for start is used as end, and start is taken to be 0. Thus the
    supplied value specifies how many elements are to be generated,
    starting the the first one.If stop is specified, then elements from
    iterable are skipped until start is reached. Afterward, elements are
    returned consecutively unless step is set higher than one which
    results in items being skipped. If stop is None, then iteration
    continues until iterable is exhausted, if at all; otherwise, it
    stops at the specified position. If stop is specified and is not
    None, and is not greater than start then nothing is returned. Unlike
    regular slicing, islice() does not support negative values for
    start, stop, or step. Can be used to extract related fields from
    data where the internal structure has been flattened (for example, a
    multi-line report may list a name field on every third line).

    :param p: the iterator items come from
    :param start: the index of the first item
    :param stop: the index one past the final item, None (the default) means
                 no end
    :param step: how far to move to subsequent items (default is 1)

    """

    if stop == ():
        stop = start
        start = 0
    # TODO: optimizing or breaking semantics?
    if stop is not None and start >= stop:
        return
    it = iter(p)
    for _ in range(start):
        next(it)

    while True:
        yield next(it)
        for _ in range(step - 1):
            next(it)
        start += step
        if stop is not None and start >= stop:
            return


def permutations(iterable, r=None):
    """Return successive r length permutations of elements in the iterable.

    If r is not specified or is None, then r defaults to the length of the
    iterable and all possible full-length permutations are generated.

    Permutations are emitted in lexicographic sort order. So, if the input
    iterable is sorted, the permutation tuples will be produced in sorted
    order.

    Elements are treated as unique based on their position, not on their
    value. So if the input elements are unique, there will be no repeat
    values in each permutation.

    :param iterable: the source of values
    :param r: the permutation length

    """
    # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) --> 012 021 102 120 201 210
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = list(range(n))
    cycles = list(range(n, n - r, -1))
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i + 1 :] + indices[i : i + 1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return


def product(*args, r=1):
    """Cartesian product of input iterables.

    Roughly equivalent to nested for-loops in a generator expression. For
    example, product(A, B) returns the same as ((x,y) for x in A for y in
    B).

    The nested loops cycle like an odometer with the rightmost element
    advancing on every iteration. This pattern creates a lexicographic
    ordering so that if the input’s iterables are sorted, the product tuples
    are emitted in sorted order.

    To compute the product of an iterable with itself, specify the number of
    repetitions with the optional repeat keyword argument. For example,
    product(A, repeat=4) means the same as product(A, A, A, A).

    :param args: sources of values
    :param r: number of times to duplicate the (single) arg for taking a
              product with itself (default is 1)

    """
    # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
    pools = [tuple(pool) for pool in args] * r
    result = [[]]
    for pool in pools:
        result = [x + [y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)


def repeat(el, n=None):
    """Make an iterator that returns object over and over again. Runs
    indefinitely unless the times argument is specified. Used as argument to
    map() for invariant parameters to the called function. Also used with zip()
    to create an invariant part of a tuple record.

    :param el: the object to yield
    :param n: the number of time to yield, None (the default) means infinitely.

    """
    if n is None:
        while True:
            yield el
    else:
        for _ in range(n):
            yield el


def starmap(function, iterable):
    """Make an iterator that computes the function using arguments obtained from
    the iterable. Used instead of map() when argument parameters are already
    grouped in tuples from a single iterable (the data has been “pre-zipped”).
    The difference between map() and starmap() parallels the distinction between
    function(a,b) and function(\*c).

    :param function: the function to apply
    :param iterable: where groups of arguments come from

    """
    for args in iterable:
        yield function(*args)


def takewhile(predicate, iterable):
    """Make an iterator that returns elements from the iterable as long
    as the predicate is true.

    :param predicate: used to test values
    :param iterable: source of values

    """
    # takewhile(lambda x: x<5, [1,4,6,4,1]) --> 1 4
    for x in iterable:
        if predicate(x):
            yield x
        else:
            break


def tee(iterable, n=2):
    """Return n independent iterators from a single iterable.

    :param iterable: the iterator from which to make iterators.
    :param n: the number of iterators to make (default is 2)

    """
    return [iter(iterable) for _ in range(n)]


def zip_longest(*args, fillvalue=None):
    """Make an iterator that aggregates elements from each of the
    iterables. If the iterables are of uneven length, missing values are
    filled-in with fillvalue. Iteration continues until the longest
    iterable is exhausted.

    :param args: the iterables to combine
    :param fillvalue: value to fill in those missing from shorter iterables
    """
    # zip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
    iterators = [iter(it) for it in args]
    num_active = len(iterators)
    if not num_active:
        return
    while True:
        values = []
        for i, it in enumerate(iterators):
            try:
                value = next(it)
            except StopIteration:
                num_active -= 1
                if not num_active:
                    return
                iterators[i] = repeat(fillvalue)
                value = fillvalue
            values.append(value)
        yield tuple(values)
