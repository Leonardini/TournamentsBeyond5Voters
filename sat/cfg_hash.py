import sys, hashlib, itertools, importlib.util
spec=importlib.util.spec_from_file_location("bs","base_survivors.py"); bs=importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)

def analyse(tag, host, q, base, arc, non):
    if host: bs.load_bits(host)
    else: bs.BEATS=None; bs.HOSTN=None
    beats=bs.beats_fn(q)
    S=sorted(base)
    assert beats(*arc), f"{arc} is not an arc"
    assert not beats(*non), f"{non} is not a non-arc"
    m=bs.mask_of(S,q)
    states,perms=bs.enumerate_base_states(S,q,5,'majority')
    b=len(S)
    ids={(a,c):k for k,(a,c) in enumerate((a,c) for a in range(b) for c in range(b) if a!=c)}
    fs=[ids[(p[0],p[1])] for p in perms]
    i1=ids[(S.index(arc[0]),S.index(arc[1]))]
    i2=ids[(S.index(non[0]),S.index(non[1]))]
    surv=[k for k,st in enumerate(states) if any(fs[p] in (i1,i2) for p in st)]
    h=hashlib.sha256((",".join(map(str,surv))).encode()).hexdigest()[:16]
    sh=hashlib.sha256(str(states).encode()).hexdigest()[:16]
    print(f"{tag:6s} base {S} mask={m} canon5={bs.canon5(m)} base_states={len(states)} "
          f"arc {arc}->idx{ (S.index(arc[0]),S.index(arc[1])) } non {non}->idx{ (S.index(non[0]),S.index(non[1])) } "
          f"survivors={len(surv)}")
    print(f"       state-list hash {sh}   survivor-set hash {h}")
    return surv

s23=analyse("P23", None, 23, [0,4,5,11,16], (0,16), (5,4))
s27=analyse("P27", "p27_paley.bits", 27, [0,1,2,3,14], (0,14), (2,1))
s31=analyse("P31", "p31_paley.bits", 31, [0,1,6,13,19], (0,19), (6,1))
print("\nsurvivor sets identical:  P23==P27 %s   P27==P31 %s"%(s23==s27, s27==s31))
