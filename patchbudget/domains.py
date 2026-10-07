"""Independent bounded input distributions and specification oracles."""
import itertools
import math
import random

PROGRAMS = ['bitcount', 'bucketsort', 'find_first_in_sorted', 'gcd',
            'get_factors', 'is_valid_parenthesization', 'knapsack', 'kth',
            'lcs_length', 'lis', 'max_sublist_sum', 'mergesort',
            'next_permutation', 'to_base', 'quicksort', 'sieve']

def draw(name, rng):
    def array(lo=-12, hi=12, minlen=0, maxlen=12):
        return [rng.randint(lo, hi) for _ in range(rng.randint(minlen, maxlen))]
    if name == 'bitcount': return [rng.randrange(0, 65536)]
    if name == 'bucketsort':
        k = rng.randrange(1, 20)
        return [array(0, k-1), k]
    if name == 'find_first_in_sorted': return [sorted(array()), rng.randint(-15, 15)]
    if name == 'gcd': return [rng.randint(0, 300), rng.randint(0, 300)]
    if name == 'get_factors': return [rng.randint(1, 4000)]
    if name == 'is_valid_parenthesization':
        return [''.join(rng.choice('()') for _ in range(rng.randint(0, 16)))]
    if name == 'knapsack':
        return [rng.randint(0, 30), [[rng.randint(1, 15), rng.randint(0, 20)]
                                  for _ in range(rng.randint(0, 8))]]
    if name == 'kth':
        a = array(minlen=1)
        return [a, rng.randrange(len(a))]
    if name == 'lcs_length':
        return [''.join(rng.choice('abcde') for _ in range(rng.randint(0, 9))) for _ in range(2)]
    if name in ['lis', 'max_sublist_sum', 'mergesort', 'quicksort']: return [array()]
    if name == 'next_permutation': return [array(0, 8, 0, 7)]
    # Larger finite domain than 64+256 distinct cases, with cheap reference runs.
    if name == 'pascal': return [rng.randint(1, 360)]
    if name == 'sieve': return [rng.randint(0, 600)]
    if name == 'to_base': return [rng.randint(1, 100000), rng.randint(2, 36)]
    raise KeyError(name)

def oracle(name, args):
    if name == 'bitcount': return args[0].bit_count()
    if name in ['bucketsort', 'mergesort', 'quicksort']: return sorted(args[0])
    if name == 'find_first_in_sorted':
        a, x = args
        return a.index(x) if x in a else -1
    if name == 'gcd': return math.gcd(*args)
    if name == 'get_factors':
        n, = args
        factors = []
        for d in range(2, n+1):
            while n % d == 0:
                factors.append(d)
                n //= d
            if n == 1: break
        return factors
    if name == 'is_valid_parenthesization':
        s, = args
        return s.count('(') == s.count(')') and all(
            s[:i].count('(') >= s[:i].count(')') for i in range(1, len(s)+1))
    if name == 'knapsack':
        capacity, items = args
        return max((sum(v for (w,v), b in zip(items, bits) if b)
                    for bits in itertools.product([0, 1], repeat=len(items))
                    if sum(w for (w,v), b in zip(items, bits) if b) <= capacity), default=0)
    if name == 'kth': return sorted(args[0])[args[1]]
    if name == 'lcs_length':
        # QuixBugs lcs_length means longest common SUBSTRING, not subsequence.
        s, t = args
        return max((j-i for i in range(len(s)) for j in range(i+1, len(s)+1)
                    if s[i:j] in t), default=0)
    if name == 'lis':
        a, = args
        best = []
        for i, x in enumerate(a):
            best.append(1 + max((best[j] for j in range(i) if a[j] < x), default=0))
        return max(best, default=0)
    if name == 'max_sublist_sum':
        a, = args
        return max([0] + [sum(a[i:j]) for i in range(len(a)) for j in range(i+1,len(a)+1)])
    if name == 'next_permutation':
        a, = args
        # Brute-force distinct permutations, only used on <=7 elements.
        return next((list(x) for x in sorted(set(itertools.permutations(a))) if x > tuple(a)), None)
    if name == 'pascal':
        return [[math.comb(n,k) for k in range(n+1)] for n in range(args[0])]
    if name == 'sieve':
        return [n for n in range(2,args[0]+1) if all(n % d for d in range(2, math.isqrt(n)+1))]
    if name == 'to_base':
        num, base = args
        digits = []
        while num:
            num, digit = divmod(num, base)
            digits.append('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[digit])
        return ''.join(reversed(digits))
    raise KeyError(name)
