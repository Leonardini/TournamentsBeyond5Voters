# Paley(43) is not the majority of 5 voters

**Claim.** The Paley tournament $P = \mathrm{Paley}(43)$ is *not 5-realizable*: there is no multiset of
5 linear orders (voters) on the 43 vertices whose pairwise-majority tournament equals $P$.
Equivalently, $P$ is not the Kemeny median of any 5 voters. Consequently $N(5) \le 43$ (there exists a
43-vertex tournament that is not the majority of 5 voters).

**Corollary — refutation of "Conjecture A".** Because
$\alpha^{*}(\mathrm{Paley43}) = \mathrm{MAS}/C = 543/903 = 181/301 > 3/5$, Paley(43) is an explicit
**counterexample to the conjecture that $\alpha^{*} > 3/5$ implies 5-realizability**. The
$\alpha^{*} \ge 3/5$ density threshold is *necessary* for 5-realizability but, as this shows, **not
sufficient**.

*Every count referenced below is collected in **Appendix A**; the body is self-contained without it.
The mathematics of Section 1–Section 6 is unconditional; the single computational input is the exhaustive screen of
Section 6, whose result is stated in Section 7.*

**The idea in one paragraph.** A 5-realization would force two facts that collide. *(i) Counting.*
$\mathrm{MAS}(\mathrm{Paley43}) = 543$ is barely above $3C/5 = 541.8$, so the two highest-agreement
voters must each have forward-count within $1$ of the maximum ($\mathrm{fwd} \in \{542, 543\}$) — they
sit in the "level $\le 1$" shell of near-maximum-acyclic orders. *(ii) Co-backing.* On any directed
$3$-cycle, a majority of $5$ leaves at most one voter disagreeing with two of its three arcs, so the
five voters' *double-back sets* (the cyclic triangles a voter gets "doubly wrong") are pairwise
disjoint. Together these say a realization needs two level-$\le 1$ orders whose double-back sets are
disjoint. We then check, exhaustively and with proof, that **no two level-$\le 1$ orders have disjoint
double-back sets** — so no realization exists. The engineering (a "razor" that groups the level-$\le 1$
orders into far fewer classes, and an automorphism reduction that shrinks one side by $|\mathrm{Aut}|$)
only makes the exhaustive check finish in seconds; its soundness is proved in Section 6.

---

## 1. Setup and notation

$P = \mathrm{Paley}(43)$: vertices $\mathbb{Z}_{43}$, arc $u\to v$ iff $v-u$ is a nonzero quadratic
residue mod $43$ ($43 \equiv 3 \bmod 4$, so $-1$ is a non-residue and exactly one of $u\to v$, $v\to u$
holds). Throughout, $q = 43$. The number of arcs is $C = \binom{q}{2} = q(q-1)/2 = 903$.

A **voter** is a linear order (equivalently a permutation) $O$ of the $43$ vertices. Arc $u\to v$ of
$P$ is **forward** in $O$ if $O$ ranks $u$ before $v$, else **backward** ("backed"). Let
$\mathrm{fwd}(O)$ be the number of forward arcs; $\mathrm{back}(O) = C - \mathrm{fwd}(O)$.

A tournament $T$ is **5-realized** by voters $O_1,\dots,O_5$ if for every arc $u\to v$ of $T$, a strict
majority ($\ge 3$) of the voters rank $u$ before $v$. We assume, for contradiction, that such
$O_1,\dots,O_5$ realize $P$.

**Maximum acyclic subgraph.** $\mathrm{MAS}(P) = \max_O \mathrm{fwd}(O)$. A voter with
$\mathrm{fwd}(O) = \mathrm{MAS} - \delta$ is said to be at **level $\delta$**. Level $0$ = a
maximum-acyclic (MAS) order.

**Cyclic triangles and double-backing.** A $3$-subset $\{a,b,c\}$ is a **cyclic triangle** if $P$
induces a directed $3$-cycle on it. Since $P$ is regular (every out-degree $(q-1)/2 = 21$), the number
of transitive triangles is $q\binom{(q-1)/2}{2}$, so the number of cyclic ones is

$$T \;=\; \binom{q}{3} - q\binom{(q-1)/2}{2} \;=\; \frac{q^{3}-q}{24} \;=\; \frac{q(q-1)(q+1)}{24} \;=\; 3311.$$

A linear order restricted to a $3$-cycle backs either $1$ or $2$ of its $3$ arcs; it **double-backs**
the triangle if it backs $2$. The **double-back set** is
$\mathrm{DB}(O) = \{\, \text{cyclic triangles double-backed by } O \,\}$.

---

## 2. MAS(Paley 43) = 543

$\mathrm{MAS}(P) = 543$, certified by an exact unanchored subset-DP modulo $\mathrm{Aut}(P)$ with
meet-in-the-middle at the equator (`dp43.c`; the join step reports $\mathrm{maxtot} = 543$ over all
alive equator splits, sound in both directions on completion). The engine is validated on small cases
and reproduces known MAS values (Appendix A).

**The density threshold is necessary but not sufficient (refuting Conjecture A).** From
$\sum \mathrm{fwd} \ge 3C$ and $\mathrm{fwd} \le \mathrm{MAS}$ (Section 3) we get $5\,\mathrm{MAS} \ge 3C$, i.e.
$\alpha^{*}(P) := \mathrm{MAS}/C \ge 3/5$ is a *necessary* condition for 5-realizability — any tournament
with $\mathrm{MAS}/C < 3/5$ is automatically non-realizable (the "$\alpha^{*}$-obstruction"). Paley(43)
*passes* this test: $5\,\mathrm{MAS} = 2715 = 3C + 6$, so $\alpha^{*}(43) = 181/301 > 3/5$, exceeding the
threshold by $181/301 - 3/5 = 2/1505$. Yet it is non-realizable (this paper). Hence
**$\alpha^{*} > 3/5$ does not imply 5-realizability**: the obstruction is a genuinely global fact,
invisible to any single-parameter density bound. (The slack $5\,\mathrm{MAS} - 3C = 6$ is exactly what
pins the two top voters to level $\lfloor 6/4 \rfloor = 1$ in Section 3 — the phenomenon is razor-tight.)

---

## 3. The top two voters lie at level ≤ 1

Every arc is forward in $\ge 3$ of the $5$ voters, so summing over all arcs

$$\sum_{i=1}^{5} \mathrm{fwd}(O_i) \;\ge\; 3C \;=\; 2709.$$

Order the voters so $f_1 \ge f_2 \ge \dots \ge f_5$, $f_i = \mathrm{fwd}(O_i) \le \mathrm{MAS} = 543$. Then

$$f_2 + f_3 + f_4 + f_5 \;\ge\; 2709 - f_1 \;\ge\; 2709 - 543 \;=\; 2166,$$

and since $f_3,f_4,f_5 \le f_2$, we get $4 f_2 \ge 2166$, i.e. $f_2 \ge 541.5$, so $f_2 \ge 542$. As
$f_1 \ge f_2$, **both top voters satisfy $\mathrm{fwd} \ge 542$, i.e. lie at level $\le 1$.**

---

## 4. Co-backing lemma ⇒ pairwise-disjoint DB-sets

**Lemma (co-backing).** In any 5-realization, every cyclic triangle is double-backed by **at most one**
voter.

*Proof.* Fix a cyclic triangle with arcs $e_1,e_2,e_3$. Each $e_k$ is forward in $\ge 3$ voters, hence
backed by $\le 2$ voters, so the total number of (voter, backed-arc) incidences on this triangle is
$\sum_k \mathrm{back}(e_k) = 15 - \sum_k \mathrm{fwd}(e_k) \le 15 - 9 = 6$. Each of the $5$ voters, being
a linear order on a $3$-cycle, backs **$\ge 1$** of the three arcs, contributing $\ge 1$ incidence. If
$d$ voters double-back (contribute $2$), the incidence total is $5 + d \le 6$, so $d \le 1$.
$\blacksquare$

The lemma is universal (it uses only "majority of $5$" and the $3$-cycle), so it holds for $P$.
Consequently the five voters' double-back sets are **pairwise disjoint**:
$\mathrm{DB}(O_i) \cap \mathrm{DB}(O_j) = \varnothing$ for $i \ne j$. In particular the **two top
voters** (Section 3) are two orders at level $\le 1$ whose double-back sets are disjoint.

---

## 5. Reduction to a finite check

Combining Section 3–Section 4: *if $P$ is 5-realizable, there exist two distinct orders $O, O'$ at level $\le 1$ with
$\mathrm{DB}(O) \cap \mathrm{DB}(O') = \varnothing$.* Therefore:

> **If no two level-$\le 1$ orders of $P$ have disjoint double-back sets, then $P$ is not
> 5-realizable.**

The level-$\le 1$ shell (all orders with $\mathrm{fwd} \ge 542$) is finite. Enumerating it via
slack-budget backtracking over the `dp43` layer tables at $\tau = 542$ produces its orbits under
$\mathrm{Aut}(P)$; a count identity (orbit count $\times |\mathrm{Aut}|$ = raw order count) certifies
the enumeration is complete — no orbit is missed (Appendix A). So the criterion above is a decidable
finite check.

---

## 6. The screen (algorithm and soundness)

We must decide whether any two of the level-$\le 1$ orders (about $1.7$ billion of them) have disjoint
DB-sets. Two devices make this exhaustive check tractable; both are proved sound here, and the exact
counts they produce are in Appendix A.

### 6.1 Razor (grouping)

Fix a vertex subset $W = \{0,\dots,23\}$ ($|W| = 24$) and let $R$ be the cyclic triangles whose three
vertices all lie in $W$. For an order $O$, write $O|_{W}$ for its **restriction to $W$** — the linear
order that $O$ induces on the vertices of $W$ (their relative ranking, ignoring everything outside
$W$). Define $\mathrm{rmask}(O) = \mathrm{DB}(O) \cap R$. Whether a triangle in $R$ is double-backed by
$O$ depends only on the relative order of its three vertices, all of which lie in $W$; hence a triangle
in $R$ is double-backed by $O$ iff it is double-backed by $O|_{W}$, so **$\mathrm{rmask}(O)$ depends
only on $O|_{W}$**.

*Soundness of the razor.* If $\mathrm{rmask}(O) \cap \mathrm{rmask}(O') \ne \varnothing$ then
$\mathrm{DB}(O) \cap \mathrm{DB}(O') \ne \varnothing$. Hence a DB-disjoint pair must have **disjoint
rmasks** — the razor is a sound (necessary-condition) filter.

*Collapse.* Because $\mathrm{rmask}(O)$ depends only on $O|_{W}$, the whole shell takes only a few
million distinct rmask values (a several-hundred-fold reduction in the number of objects to compare).
We compute all disjoint distinct-rmask pairs; only these are candidates for the exact check.

### 6.2 Automorphism reduction (one side)

Let $G = \{\, \sigma_{a,b} : x \mapsto ax+b,\ a \in \mathrm{QR},\ b \in V \,\}$, with
$|G| = q(q-1)/2 = 903$ — the group the engine canonicalises over and expands by (for the prime
$q = 43$, $G$ is the full $\mathrm{Aut}(P)$). The shell is $G$-closed ($G$ preserves $\mathrm{fwd}$) and
is the union of the reps' $G$-orbits (Section 5). The reduction rests on one lemma, **proved below**, not
merely sampled.

**Theorem (overlap size is $G$-invariant).** For every $\sigma \in G$ and all orders $O_1, O_2$,

$$\big|\,\mathrm{DB}(\sigma O_1) \cap \mathrm{DB}(\sigma O_2)\,\big| \;=\; \big|\,\mathrm{DB}(O_1) \cap \mathrm{DB}(O_2)\,\big|.$$

*Proof.* **(0)** Each $\sigma_{a,b}$ ($a \in \mathrm{QR}$) is a tournament automorphism: for an arc
$u\to v$, $\sigma v - \sigma u = a(v-u) \in \mathrm{QR}$ since $\mathrm{QR}$ is closed under
multiplication; being an arc-preserving bijection, $\sigma$ maps directed $3$-cycles to directed
$3$-cycles, so $t \mapsto \sigma(t)$ is a **bijection** $\Delta \to \Delta$ on the cyclic triangles.
**(1)** *Equivariance* $\mathrm{DB}(\sigma O) = \sigma(\mathrm{DB}(O))$: write $\sigma O$ for the order
with $\mathrm{pos}_{\sigma O}(\sigma v) = \mathrm{pos}_O(v)$. For an arc $p\to r$ of a triangle $t$,

$$O \text{ backs } p\to r \iff \mathrm{pos}_O(r) < \mathrm{pos}_O(p) \iff \mathrm{pos}_{\sigma O}(\sigma r) < \mathrm{pos}_{\sigma O}(\sigma p) \iff \sigma O \text{ backs } \sigma p \to \sigma r.$$

So $\sigma$ matches backed arcs of $t$ with backed arcs of $\sigma(t)$ one-for-one, giving
$b_{\sigma O}(\sigma t) = b_O(t)$; hence $t \in \mathrm{DB}(O) \iff \sigma(t) \in \mathrm{DB}(\sigma O)$.
**(2)** Since $\sigma$ is a bijection on $\Delta$,
$\mathrm{DB}(\sigma O_1) \cap \mathrm{DB}(\sigma O_2) = \sigma\big(\mathrm{DB}(O_1) \cap \mathrm{DB}(O_2)\big)$,
and taking cardinalities gives the claim. $\blacksquare$

Only two facts about $\sigma$ are used: it permutes $V$ (for
$\mathrm{pos}_{\sigma O}(\sigma v) = \mathrm{pos}_O(v)$) and it preserves arcs (step 0). **No
transitivity, regularity, or double-regularity is invoked** — indeed $G$ is *not* transitive on
$\Delta$ (its orbit structure is in Appendix A), and some triangles have nontrivial stabilisers; the
argument is pointwise in $t$ and uniform in $\sigma$, so this is irrelevant.

**Corollary (one-side reduction).** A DB-disjoint pair exists in the shell iff some canonical rep is
DB-disjoint from a pool order: if $(A,B)$ is disjoint and $A = \sigma R_A$, then by the Theorem
$(R_A, \sigma^{-1}B)$ is disjoint, with $R_A$ a rep and $\sigma^{-1}B$ in the ($G$-closed) shell. So it
suffices to test the orbit representatives against the pool — a factor $|\mathrm{Aut}| = 903$ fewer on
one side.

### 6.3 Exact double-check

For each "dangerous" rmask $r$ (one that has a razor-disjoint partner) we compute the full $3311$-bit
DBs of its group **once** and test them (early-break on the first shared triangle) against exactly the
reps whose rmask is a razor-disjoint partner of $r$. This examines precisely the set of (rep,
pool-order) razor-disjoint pairs; any pair with overlap $=0$ is a genuine DB-disjoint pair, recorded as
an explicit seed. Correctness safeguards — an exhaustive level-$0$ run, a positive-detection test that
confirms coverage, and the exhaustive check of the $G$-invariance theorem — are summarised in
Appendix A.

---

## 7. Result

Run on the complete level-$\le 1$ shell, the screen finds **no razor-disjoint pair whose full
double-back sets are disjoint** ($\texttt{TRUE\_DISJOINT} = 0$; the full count table is Appendix A). By
Section 3–Section 5 a 5-realization would produce exactly such a pair (its top two voters), so no 5-realization
exists:

> **$\mathrm{Paley}(43)$ is not 5-realizable; equivalently it is not the Kemeny median of any 5 voters.
> Hence $N(5) \le 43$.** $\blacksquare$

---

## 8. Reproducing

`./reproduce_paley43.sh` builds the tools and runs stages 0–4 (self-tests → layer tables → level-$\le 1$
reps with census check → the screen). Peak $\le 8$ threads, $\approx 5$ GB RAM, $\approx 50$ GB disk
(layer tables). The final stage prints the verdict and writes any seeds to `razor_disjoint_hits.txt`.

---

## Appendix A — Counts and computational results

Everything numerical is gathered here; the body's argument does not depend on any specific value below
except $\mathrm{MAS}=543$ (Section 2) and the derived thresholds.

**A.1 Structural constants (all closed-form in $q=43$).**

| quantity | formula | value |
|---|---|---|
| arcs $C$ | $q(q-1)/2$ | $903$ |
| cyclic triangles $T$ | $(q^3-q)/24$ | $3311$ |
| automorphisms $\lvert\mathrm{Aut}(P)\rvert=\lvert G\rvert$ | $q(q-1)/2$ | $903$ |
| out-degree (regular) | $(q-1)/2$ | $21$ |
| triangles per arc (doubly-regular) | $(q+1)/4$ | $11$ |
| $\mathrm{MAS}(P)$ (computed, `dp43`) | — | $543$ |
| $\alpha^{*}=\mathrm{MAS}/C$ | — | $181/301$ |
| realization slack $5\,\mathrm{MAS}-3C$ | — | $6$ |
| forced level of top two voters $\lfloor(5\,\mathrm{MAS}-3C)/4\rfloor$ | — | $1$ |

**A.2 Level-$\le 1$ shell census** (enum at $\tau=542$, canonicalised by `canon_reps`).

| | orbits | orders |
|---|---|---|
| level $0$ ($\mathrm{fwd}=543$) | $19{,}651$ | $17{,}744{,}853$ |
| level $1$ ($\mathrm{fwd}=542$) | $1{,}821{,}652$ | $1{,}644{,}951{,}756$ |
| **total (level $\le 1$)** | $\mathbf{1{,}841{,}303}$ | $\mathbf{1{,}662{,}696{,}609}$ |

Completeness identity: $1{,}841{,}303 \times 903 = 1{,}662{,}696{,}609$ = raw order count (every orbit
stabiliser-free, none missed).

**A.3 The screen** (razor $W=\{0,\dots,23\}$, $|R|=538$; `razor_screen`, 8 threads).

| quantity | value |
|---|---|
| distinct rmasks $M$ | $4{,}709{,}640$ |
| disjoint (candidate) rmask-pairs | $5{,}092{,}111$ |
| dangerous rmasks | $678{,}686$ |
| dangerous pool orders $K$ | $347{,}694{,}990$ |
| largest rmask group | $186{,}362$ |
| orbit reps tested (one side) | $1{,}841{,}303$ |
| **(rep, pool) pairs checked** | $\mathbf{4{,}376{,}325{,}129}$ |
| **$\texttt{TRUE\_DISJOINT}$ (seeds)** | $\mathbf{0}$ |
| double-check wall time | $22.6$ s |

**A.4 Verification ledger.**

- **$\mathrm{MAS}=543$** certified by `dp43` (two independent rebuilds); MAS gauntlet reproduces
  brute-force $q=7,11$ and the known $\mathrm{MAS}=107/161/285$ for $q=19/23/31$ byte-identically.
- **Shell completeness**: the identity in A.2.
- **$G$-invariance of DB-overlap size** (the sole property the reduction uses): **proved** (Section 6.2), and
  additionally cross-checked **exhaustively over all $903$ $\sigma$** — hence over every triangle
  orbit. $G$ acts on the $3311$ cyclic triangles with $5$ orbits of sizes $903,903,903,301,301$; the
  two size-$301$ orbits are the $602$ triangles with a nontrivial (order-$3$) stabiliser.
- **Level-$0$ proved exhaustively**: the screen on the level-$0$ pool checks all
  $\approx 1.6\cdot10^{14}$ pairs of the $17{,}744{,}853$ MAS orders and returns
  $\texttt{TRUE\_DISJOINT}=0$; the minimum overlap over razor-disjoint candidates is $68$ (every
  non-candidate pair overlaps by construction).
- **Positive-detection (coverage) test**: replacing the full DB by the razor triangles makes every
  candidate a seed, and the double-check then reports $\text{seedcount}=\text{checked}$ — at level $0$
  ($333{,}809 = 333{,}809$) and at full level-$\le 1$ scale
  ($4{,}376{,}325{,}129 = 4{,}376{,}325{,}129$) — confirming detection fires and coverage is complete.
- **Independent cross-check available**: the exhaustive pool-vs-pool screen (no Aut reduction)
  reproduces the level-$0$ result; running it to completion on level $\le 1$ is an optional overnight
  confirmation.
