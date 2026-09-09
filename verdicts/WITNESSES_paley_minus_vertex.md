# Positive certificates: Paley(q) minus a vertex IS 5-inducible

Two saved witnesses, for the two questions the deletions were run to answer.
Both are **verified independently of the search** — see *Verification* below.

| instance | n | margin | verdict | cost | witness |
|---|---|---|---|---|---|
| Paley(19) − v | 18 | exact (margin-1) | **SAT** | 18,841 nodes, 0.034 s | `p19_minus1v_witness.log` |
| Paley(23) − v | 22 | majority | **SAT** | 8,507,042 nodes, 62.1 s | `n22_witness_slice.log`, `n22_witness_raw.txt` |

**One witness per q suffices.** `RESEARCH_LOG.md` (§ on the arc-orbit break)
proves Aut(P_q) is *regular* on arcs, hence transitive on vertices, so `P_q − v`
is **unique up to isomorphism** — the choice of deleted vertex is immaterial.
The earlier README claim of "inducible for all 19" was therefore redundant as
mathematics, and in any case no witness from that run was ever saved; the
`P19 − v` witness below was regenerated from scratch on 2026-09-02.

Hosts are reproducible: `make_paley_minus.py` emits the `.bits` files and
self-checks against the tracked ones (`python3 make_paley_minus.py 23 --selfcheck`
→ both `p23_minus1v.bits` and `p23_minus2v.bits` OK).

## What each one settles

**`P19 − v`, margin-1** — Paley(19) is not margin-1 5-inducible, but deleting any
single vertex makes it so.  So **Paley(19) is vertex-critical** for margin-1
5-inducibility: it is a *minimal* obstruction, not merely an obstruction.

**`P23 − v`, majority** — Paley(23) is not 5-inducible unrestricted (two complete
refutations, the clean replication costing 34.03 core-h), giving **N(5) ≤ 23**.
`P23 − v` came back SAT, so n = 22 does **not** improve the bound.  Because
5-inducibility is **hereditary** — restrict the five orders to a subset — and
`P23 − v` is unique up to isomorphism, `P23 − 2v` and every deeper deletion is
5-inducible **for free**, with no further search.  The Paley(23) descent is
finished; going below 23 needs a *different* 22-vertex family.

Note the contrast: Paley(19) is vertex-critical for margin-1, and Paley(23) is
likewise vertex-critical for the unrestricted problem — in both cases one
deletion is enough to tip the instance from obstruction to realizable.

## The witnesses

Vertices `0..n−1` are Paley(q) with vertex 0 deleted, survivors relabelled in
increasing order.  Orders are **most preferred first**.

### Paley(19) − v, n = 18, margin-1 (every arc exactly 3–2)

```
voter 0: 11  8 12  0  9 16  1  6 17  4  2 15 13  3 10  7  5 14
voter 1:  8 13 17  9 14 15  0  1  7 12  4  5 10  2  6 11 16  3
voter 2: 10  7 14 15 13 16 17  2  3  0  4 11  1  8  5  9  6 12
voter 3:  6  5 11  3 10  4 15  1 12  2  0 17  9  7 16  8 13 14
voter 4:  5  3 16 14  2  6  7 12  4  9 13  1 10  8  0 11 17 15
```

### Paley(23) − v, n = 22, majority

```
voter 0: 18 21  1 20  0  2  3  4  6  5  7  8  9 10 11 12 13 14 15 16 17 19
voter 1: 13  6 15  8  1 17 10  3 19 12  5 21 14  7  0 16  9  2 18 11  4 20
voter 2: 10 13 16 19  2  5  8 11 14 17 20  0  3  6  9 12 15 18 21  1  4  7
voter 3:  9  4 17 12  7  2 20 21 16 15 10  5 11  6  0 18  1 19 14 13  8  3
voter 4: 14 18  3  7 11 15 19  4  0 12  8 16 20  1  9  5 17 13 21  6  2 10
```

## Verification

`verify_paley_minus_witness.py` shares no code with the search or with
kinduce's internal verifier: it rebuilds Paley(q) from its quadratic residues,
deletes the vertex, reads the orders out of the log, and recomputes every
pairwise majority from scratch.

```bash
python3 verify_paley_minus_witness.py p19_minus1v_witness.log --q 19 --drop 0 --margin exact
python3 verify_paley_minus_witness.py n22_witness_slice.log   --q 23 --drop 0 --margin majority
```

| | P19 − v | P23 − v |
|---|---|---|
| Orders are permutations of `0..n−1` | 5 / 5 | 5 / 5 |
| Pairs checked | **153 = C(18,2)** | **231 = C(22,2)** |
| Mismatches vs. target | **0** | **0** |
| Winner-support histogram | `{3: 153}` | `{3: 208, 4: 23}` |
| Margin claim | exactly 3–2 on **every** arc ⇒ margin-1 | every arc ≥ 3 of 5 ⇒ majority |

The P19 histogram `{3: 153}` is the substantive check: margin-1 requires *every*
arc at exactly 3–2, which a plain majority witness would not satisfy.  The P23
histogram shows no unanimous arc (max support 4), which is incidental.

## Provenance

```
P19-v   ./kinduce21 --bits p19_minus1v.bits --n 18 --k 5 --margin exact \
                    --order mrv --inc --pool-mb 512 --time 900
        no symmetry break used (none needed at this size)
        RESULT SAT nodes=18841 sols=1 base_states=2200 time=0.034s
        (12 s wall, essentially all of it building the minFAS table)

P23-v   ./kinduce21 --bits p23_minus1v.bits --n 22 --k 5 --margin majority \
                    --order mrv --inc --pool-mb 512 --toporb 0 4 \
                    --bs-from 6560 --bs-to 6564
        driver n22.sh, 10 workers, 2008 chunks of 4 base states, seed 2209
        RESULT SAT nodes=8507042 sols=1 base_states=8031 time=62.100s
```

`--toporb 0 4` was verified directly rather than assumed: |Aut(P23−v)| = 11 with
exactly **two** vertex orbits of size 11,

```
orbit(0) = {0,1,2,3,5,7,8,11,12,15,17}
orbit(4) = {4,6,9,10,13,14,16,18,19,20,21}
```

so `{0,4}` is a complete set of orbit representatives.  The score sequence is
11×10 + 11×11, i.e. `P23 − v` is **not** vertex-transitive, so `--top0rr` — valid
on Paley itself — would have been *unsound* here.

A symmetry break can only affect the completeness of a *refutation*, never the
soundness of a *witness*: both SATs above are checked directly against the target
tournament and stand independently of any symmetry argument.

## Side benefit: two-sided validation of the engine

The same binary and search that returned UNSAT on 2008 of 2008 slices for
Paley(23) produce genuine, externally verified SATs here.  So the Paley(23)
refutations are not the artifact of a search incapable of finding witnesses — a
known-answer validation in the positive direction, obtained for free.

## Status of the surrounding claims

- `N(5) ≥ 12` — proven (n = 11 census).
- `N(5) ≤ 23` — **a computation, not yet a certificate.** Two complete
  refutations agree, but they share a base placement, and DRAT certification via
  the cube route remains the outstanding proof obligation.
- Bracket: **12 ≤ N(5) ≤ 23**.
