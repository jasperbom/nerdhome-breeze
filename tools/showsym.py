import sys
sys.path.insert(0, '/home/claude/toshiba-c6/tools')
from sexp import parse, find, find1
LIB = '/usr/share/kicad/symbols/'
def load(lib, name):
    t = parse(open(LIB + lib + '.kicad_sym').read())
    for s in find(t, 'symbol'):
        if s[1] == name:
            return s, t
    raise KeyError(name)
def pins(sym):
    out = []
    def walk(n):
        for x in n:
            if isinstance(x, list) and x:
                if x[0] == 'pin':
                    at = find1(x, 'at'); ln = find1(x, 'length')
                    nm = find1(x, 'name'); nu = find1(x, 'number')
                    out.append((str(nu[1]), str(nm[1]), str(x[1]), float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0, float(ln[1])))
                else:
                    walk(x)
    walk(sym)
    return out
if __name__ == '__main__':
    for spec in sys.argv[1:]:
        lib, name = spec.split(':')
        s, _ = load(lib, name)
        ext = find1(s, 'extends')
        print('##', spec, 'extends', ext[1] if ext else '-')
        for p in pins(s):
            print('  ', p)
