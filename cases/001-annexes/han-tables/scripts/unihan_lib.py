import glob, os, collections
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'unihan', 'x')
def load():
    F = collections.defaultdict(dict)
    for p in glob.glob(os.path.join(D, 'Unihan_*.txt')):
        for line in open(p, encoding='utf-8'):
            if line.startswith('#') or not line.strip():
                continue
            cp, fld, val = line.rstrip('\n').split('\t', 2)
            F[fld][int(cp[2:], 16)] = val
    return F

import sys
sys.stdout.reconfigure(encoding='utf-8')
