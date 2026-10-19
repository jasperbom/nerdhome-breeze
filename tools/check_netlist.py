"""Compare a KiCad-exported netlist with circuit.py (exact pin-level match)."""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import circuit
t = open(sys.argv[1]).read()
t = t[t.find('(nets'):]
got = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)', t, re.S):
    nodes = set(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)))
    nodes = {n for n in nodes if not n[0].startswith('#')}
    if nodes:
        got[m.group(1)] = nodes
want = {n: set(v) for n, v in circuit.nets().items()}
# map exported names (may be "/NET" or "NET") to ours
norm = {k.lstrip('/'): v for k, v in got.items() if not k.startswith('unconnected')}
ok = True
for n, v in want.items():
    if norm.get(n) != v:
        ok = False
        print("MISMATCH", n, "\n  want", sorted(v), "\n  got ", sorted(norm.get(n, [])))
for n, v in norm.items():
    if n not in want and len(v) > 1:
        ok = False
        print("EXTRA NET", n, sorted(v))
unc = [k for k in got if k.startswith('unconnected')]
print("nets ok" if ok else "NETLIST DIFFERS", "| nets:", len(norm), "| unconnected pins:", len(unc))
