# Arc-reversal witnesses: Paley(q) with a single arc reversed

**2026-09-03.**  Companion to `WITNESSES_paley_minus_vertex.md`.  Written the
moment each witness was found -- the earlier lesson was that verifying a witness
is not the same as persisting one, and `certs/` is gitignored.

## Exactly one tournament per q, up to isomorphism

`Aut(Paley(q))` acts **regularly** on arcs for prime `q` (`|Aut| = q(q-1)/2 =`
the number of arcs: 171 at `q=19`, 253 at `q=23`), hence transitively, so all
single-arc reversals are isomorphic and "reverse an arc of Paley(q)" names ONE
tournament.  Verified not merely from the group order but constructively: for
every one of the 171 and 253 arcs, the explicit affine map carrying `(0,1)` to
that arc was checked to carry the reversed tournament onto the reversed
tournament.  0 failures.

**All symmetry is destroyed by the reversal: `|Aut| = 1` for both hosts**
(out-degrees go from regular to `[8,9,10]` and `[10,11,12]`).  So `--toppair`,
`--top0` and `--toporb` are all UNSOUND here and none is used; only the voter
lex-sort applies, being a WLOG on voter ordering and independent of the host.

Hosts are tracked as `p19_arcrev.bits` and `p23_arcrev.bits`, built by reversing
the arc `(0,1)` of the `Z/q` quadratic-residue tournament.

## Paley(19), arc reversed: MARGIN-1 5-INDUCIBLE

Found in ~50 s (base `{0,1,2,9,16}`, mask 668, 2200 base states, base-state
slice `[1460,1464)`, 673,336 nodes, 1.749 s in the chunk that hit it).
Re-verified independently by `verify_witness_bits.py`:
**`all 171 arcs at exactly 3:2, 5 valid permutations -- witness is GENUINE`**.

    voter 0: 13 10 7 8 14 18 0 5 6 11 12 16 17 4 15 2 3 9 1
    voter 1: 13 15 3 1 12 17 0 4 5 7 2 11 18 16 8 9 6 10 14
    voter 2: 5 3 14 4 1 6 10 2 11 0 8 17 9 15 7 16 12 13 18
    voter 3: 9 16 17 14 11 1 2 6 18 3 7 4 8 15 5 12 13 0 10
    voter 4: 12 9 18 10 15 16 8 2 0 6 7 4 13 11 1 17 5 3 14

Reproduce:

```sh
./kinduce22 --bits p19_arcrev.bits --n 19 --k 5 --margin exact --order mrv --inc \
            --pool-mb 512 --base 0 1 2 9 16 --bs-from 1460 --bs-to 1464
python3 verify_witness_bits.py <log> p19_arcrev.bits 19 5
```

## Arc-criticality implies vertex-criticality (Leonid, 2026-09-03)

> **Theorem.** Let `T` be not `k`-inducible.  If for every vertex `v` there is
> SOME arc `e` incident to `v` whose reversal `T^e` is `k`-inducible, then
> `T - v` is `k`-inducible for every `v`.  In particular arc-critical implies
> vertex-critical.

*Proof.*  `k`-inducibility is hereditary: restrict the voters' orders to a
subset and every surviving arc keeps its support exactly.  Given `v`, take `e`
incident to `v`; `T^e` is `k`-inducible, hence so is `T^e - v`.  But
`T^e - v = T - v`, because `T` and `T^e` differ only in the orientation of `e`
and `e` is destroyed by deleting `v`.  QED

Holds for margin-1 as well as majority, since restriction preserves the exact
3:2 margin, not merely the majority.  Note the hypothesis is weaker than full
arc-criticality -- one incident arc per vertex suffices -- and for Paley hosts
the two coincide, Aut being transitive on arcs.

**So arc-criticality is the STRONGER notion**, which matches the intuition that
reversing one arc is a far smaller repair than deleting a vertex (which drops
`n-1` arcs' worth of constraints at once).  It also means known
vertex-criticality is a NECESSARY condition for arc-criticality -- satisfied for
both `Paley(19)` at margin 1 and `Paley(23)` at majority, so neither is excluded
a priori.

**Verified constructively on the witness below.**  Restricting those same five
orders to `V \ {0}` and to `V \ {1}` -- the two endpoints of the reversed arc
`(0,1)` -- yields margin-1 witnesses for `Paley(19) - v` on the ORIGINAL host:
153 arcs, every support exactly 3, 0 bad.  Restricting instead to a
NON-endpoint (`v = 5`) fails on exactly one arc, namely the reversed `(0,1)`
sitting at support 2 -- precisely the failure the proof predicts when `v` is not
an endpoint.  This also re-derives a margin-1 certificate for `Paley(19) - v` by
a second, independent route.

### Consequence: Paley(19) is ARC-CRITICAL for margin-1 5-inducibility

`Paley(19)` is not margin-1 5-inducible (machine-verified, 22,876 cubes, every
LRAT proof checked by `lrat-trim`), the single-arc reversal is unique up to
isomorphism, and that reversal **is** margin-1 5-inducible.  So the obstruction
dies on reversing *any* arc.  This complements the known **vertex**-criticality
(`Paley(19) - v` is margin-1 5-inducible), so `Paley(19)` is critical in both
senses at margin 1.

Calibration for the notion: the 20-arc obstacle `G_8` (denoted `H_8` in earlier
accounts) is likewise arc-critical for 3-inducibility -- all 20 single-arc
reversals become 3-inducible, minFAS dropping 7 -> 6 in every case, and none is
isomorphic to `G_8`.  The degenerate escape route (a reversal isomorphic to the
original) is therefore real enough to be worth checking, and empty in all three
cases here.

## Paley(23), arc reversed: majority 5-inducibility -- OPEN

**Not settled.**  Evidence to date, and the two routes priced.

### The reduction (complete, but not cheaper)

A witness for `T^e` restricted to an endpoint of `e` is a witness for
`T^e - u = T - u ~= Paley(23) - v`.  Hence

> `Paley(23)` is arc-critical **iff** SOME `Paley(23) - v` witness extends, by
> re-inserting the deleted vertex, to a witness of `Paley(23)` with exactly one
> arc at that vertex flipped.

Min-distance is invariant under `Aut(Paley(23) - v)` (order 11, cyclic -- those
maps fix the deleted vertex and permute its out-neighbourhood among itself), and
voter permutations are already quotiented by the lex break, so one
representative per orbit suffices.  `insert_scan` / `insert_stream` implement the
extension test exactly; `kinduce23` (`--emit`) streams every witness instead of
stopping at the first.

**But the reduction does not save work for a NEGATIVE.**  Enumerating all
`Paley(23) - v` witnesses costs ~220 core-h, because most base states hold ZERO
witnesses and proving that is exactly the refutation work.  Measured: of 12 base
states probed, 10 were barren; base state 6560 alone holds 3,068,928.

### Evidence so far: no extension in 5.93 million witnesses

**5,928,928** `Paley(23) - v` witnesses scanned, **0** single-arc extensions.
The saved `n22` certificate is 3 flips away (exhaustively, unpruned).  The
distance-1 test is exact; the "min distance" reported by `insert_stream` is NOT,
since it prunes subtrees carrying >= 2 definite violations.

### Prices

**RE-PRICED 2026-09-03 by paired probes at matched 8-way load.  The 113 s
figure below was a partial-load single-probe reading and is 2x too low; the
defect-1 route has been BUILT, validated and measured, and it LOSES.**

| route | base states | per base | total |
|---|---|---|---|
| blind `T^e` scan, no symmetry (`|Aut(T^e)| = 1`) | 8031 | **224.1 s** measured | **500 core-h** |
| enumerate all `Paley(23) - v` witnesses | 8031 | ~100 s (unloaded) | ~220 core-h, re-price |
| defect-1, `--top0` + 23-arc `R` (`kinduce24 --defect`) | 8031 | **>= 328.2 s** | **>= 732 core-h** |
| defect-0 control, `--top0` only | 8031 | 66.4 s | 148 core-h |
| route (a) branch A, full break + defect over 243 | 2591 surv | >= 913 s | **>= 657 core-h** |
| route (a) branch B, defect over the 10 base arcs | 8031 | >= 298 s | **>= 666 core-h** |
| route (a) branch B, defect spent IN the base | 65,169 surv | 47 s | ~851 core-h |
| **route (a) total** | | | **>= 1,320 core-h** |

Branch B alone, built either way, already costs more than the whole blind scan,
so route (a) cannot win whatever branch A turns out to be.  The branch A
control reproduces the recorded 47.5 s/survivor at 46.3 s under the same load,
which anchors the protocol and shows the 113 -> 224 s change for the blind scan
is a sampling disagreement, not a load penalty.

The relaxation factor is `4.94` cost-weighted (range 3.93..5.93 over 8 base
states, 2 of 8 censored at 600 s so the total is a lower bound), against `1.35`
when only ONE arc is allowed to be the defect -- so the 5x is the intrinsic
price of 23 simultaneously-live defect positions, not loose bookkeeping.
**Recommendation: run the blind scan.**  See `RESEARCH_LOG.md` 2026-09-03
(afternoon) for the full derivation, including why `--toppair` and "the defect
avoids the base" cannot both be assumed.

### The defect-1 reformulation (Leonid's, and the best next step)

Run the ORIGINAL `Paley(23)` search, symmetry break and all, but accept a
placement that leaves **exactly one** arc under-supported, short-circuiting on a
second violation.  That is precisely arc-criticality, and crucially **the
`--toppair` break survives the relaxation**: `Aut` acts on relaxed solutions by
`g(sigma_1..sigma_5, e) = (g sigma_1 .. g sigma_5, g(e))`, so normalising voter
0's `(top, second)` to an orbit representative is still WLOG, and the defect just
travels with it.  That restores the 8031 -> 2537 base-state reduction that
reversing an arc destroys.

Defect-0 on `T` ran at 48 s per base state, so the relaxation wins if it costs
under **7.5x**.  **MEASURED 2026-09-03: it costs 4.94x on the `--top0` arm,
which sounds like a win and is not** -- because the base-state reduction it was
supposed to buy is exactly the one that is UNSOUND to combine with, so the
comparison has to be made against the honest configurations, and there the
route comes out at >= 732 core-h against 500 for the blind scan.  See the
re-priced table above and `RESEARCH_LOG.md` 2026-09-03 (afternoon).

**And the base-state reduction does NOT come for free with `--toppair`.**
`Aut(P_23)` is REGULAR on arcs, so `Stab(ordered pair) = 1`: normalising a
voter's `(top, second)` uses the whole group and leaves nothing with which to
push the defect out of the base's 10 internal arcs.  Enumerating the 10 in-base
flips honestly costs 65,169 surviving base states against 2,591 -- 25x.  The
sound repairs are (a) a case split on `g(e) in arcs(S)` with a re-chosen base
for the second branch, or (b) downgrade to `--top0` (23-fold) and spend the
residual `Z_11` on confining the defect to 23 arcs chosen to miss the base,
which is a theorem for `q >= 23` because `(q-1)/2 = 11 > 10 = C(5,2)`.

**Implementation warning:** the defect budget belongs in the incremental-domain
refinement, which is exactly where the engine's soundness lives.  It must be
re-validated against the full suite (96/6880 at n=8 k=3; the n=9 separation
17,674 / 17,928 / 254 / 0; regular n=11 48/1175; regular n=13) before any
verdict from it is trusted.
