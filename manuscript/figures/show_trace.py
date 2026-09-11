"""Human-readable dump of a trace written by paley7_trace.py --json."""
import json, sys

d = json.load(open(sys.argv[1]))
k = d["k"]
print(f"base {d['base']} regime {d['regime']} reps {d['reps']} nodes {d['nodes']} "
      f"witnesses {len(d['witnesses'])}")
for r in d["trace"]:
    if r["kind"] != "node":
        print(f"  [{r['kind']}] " + (str(r.get('orders')) if r['kind'] != 'node' else ''))
        continue
    depth = len(r["path"])
    ind = "  " * depth
    print(f"{ind}node d={depth} bs={r['bs']} S={r['S']} path={r['path']}")
    for i, o in enumerate(r["orders"]):
        print(f"{ind}   voter {i}: {' '.join(map(str, o))}")
    dom = r["dom"]
    print(f"{ind}   |D|: " + ", ".join(f"{v}:{len(dom[v])}" for v in sorted(dom, key=int))
          + f"   -> v* = {r['vstar']}")
    for v in sorted(dom, key=int):
        print(f"{ind}     D({v}) = " + " ".join("".join(map(str, p)) for p in dom[v]))
    for c in r["children"]:
        extra = f" empty at {c['empty_at']}" if c.get("empty_at") is not None else ""
        print(f"{ind}   slot {''.join(map(str,c['slot']))} -> {c['status']}{extra}")
