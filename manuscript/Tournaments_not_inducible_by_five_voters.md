---
output:
  pdf_document: default
  html_document: default
header-includes:
  - \usepackage{graphicx}
---
# Tournaments not inducible by five voters

**Leonid Chindelevitch$^{1}$ and Ararat Harutyunyan$^{2}$**

$^{1}$ MRC Centre for Global Infectious Disease Analysis, School of Public Health, Imperial
College London, London, United Kingdom. Email: `lchindel@ic.ac.uk`. ORCID: 0000-0002-6619-6013.

$^{2}$ University of Paris-Dauphine, PSL University, CNRS UMR7243, LAMSADE, Paris, France.
Email: `ararat.harutyunyan@lamsade.dauphine.fr`.

## Abstract

A tournament $T$ is *$k$-inducible* if there are $k$ linear orders on its vertex set such that,
for every arc $i \to j$ of $T$, a majority of the orders rank $i$ above $j$. For each odd $k$ some
tournament is not $k$-inducible, and $N(k)$ denotes the least order at which one occurs. Only
$N(3)$ is known exactly:
$N(3) = 8$, with $96$ of the $6{,}880$ tournaments on $8$ vertices not $3$-inducible [7]. The value
$N(5)$ is open. Bachmeier et al. [1] showed that *some* tournament on
$41$ vertices is not $5$-inducible, by an argument that compares how many tournaments exist with
how many five linear orders can produce; the smallest explicit such tournament known to them had 
about $6.0 \times 10^{8}$ vertices. Our companion paper [2] brought the
range to $12 \le N(5) \le 38$ and exhibited an explicit tournament of order $43$: the quadratic 
residue, or Paley, tournament $P_{43}$.

**Results.** We develop a bespoke search algorithm that improves both ends of the range, $$13 \le N(5) \le 23.$$
The upper bound comes from proving that the Paley tournament on $23$ vertices is not
$5$-inducible, the case [1] reported it could not decide, its solver having "not terminate[d]
within a total of six weeks". The lower bound comes from an exhaustive analysis at order
$12$. We obtain
several further results on the same problem. Paley(27) and Paley(31) are also not $5$-inducible.
Paley(19) is $5$-inducible, but is not $5$-inducible with *unit margin*, that is, by a profile in which
every arc is carried by exactly three voters against two. Paley(23) is arc-critical: reversing any 
of its arcs makes it $5$-inducible. Paley(43), by contrast, is *not* vertex-critical: 
deleting a vertex leaves a $42$-vertex tournament that is still not $5$-inducible. Additionally, 
we verify that every self-converse tournament on at most $13$ vertices and every regular tournament 
on at most $15$ vertices is $5$-inducible with unit margin.

**Method.** All of these results are proved by computer. Our search builds a profile one step at
a time, always making next the choice with the fewest options left open to it, and keeping for
every choice still outstanding a running list of the options that remain consistent with what has
been fixed. Together with the symmetries of
the tournament itself this bring within reach of a single laptop instances that neither integer
programming nor a general-purpose SAT solver can decide. The refutations at orders $19$ and $23$
are also formally certified: the search is split into independent subproblems, each is refuted by a
SAT solver that emits a machine-checkable proof, and a separate program rechecks every one of
them. The whole Paley(23) refutation took **$22$ hours on one laptop**, on the instance quoted above 
as undecided after six weeks. Everything is reproducible from a public repository, with only two 
simple combinatorial lemmas remaining human rather than machine-checked.

---

## 1. Introduction

Let $T$ be a tournament on the vertex set $V$, $|V| = n$: a digraph in which every unordered pair
$\{i,j\}$ carries exactly one of the arcs $i \to j$ or $j \to i$. A *$k$-profile* consists of $k$ 
linear orders $\pi_1, \dots, \pi_k$ on $V$. The *majority tournament* of such a profile puts an arc
from $i$ to $j$ whenever $|\{ v : i \prec_{\pi_v} j \}| > k/2$. For odd $k$ this is well defined on
every pair, and the result is a tournament. We say $T$ is **$k$-inducible** if some $k$-profile has 
$T$ as its majority tournament, and we call such a profile a *witness*.

Call the number of voters who rank $i$ above $j$ the **support** of the arc $i \to j$. In a
witness every arc's support exceeds $k/2$, so for $k = 5$ it is $3$, $4$ or $5$, and it is useful
to grade inducibility by how decisively the arcs are carried: a witness has **margin at most
$M$** if every arc has support $s$ with $2s - k \le M$. For $k = 5$ the possible margins are $1$
(every arc carried exactly three votes to two, which we call *unit margin*), $3$ (every support
in $\{3,4\}$) and $5$ (no restriction, i.e. plain majority). Unit margin is a strict
restriction, so a unit-margin witness is in particular a majority witness, while a unit-margin
*refutation* is strictly less informative than a majority one.

McGarvey's theorem [16] guarantees that every tournament is $k$-inducible for $k$ large enough, and
the least such $k$ is the *majority dimension* of $T$, written $\dim(T)$. The inverse question - which tournaments
are reachable with a *fixed* small number of voters — is the subject of this paper.

Counting arguments show that almost all tournaments fail to be $k$-inducible for any fixed $k$,
yet the *explicit* examples they yield are astronomically large, and it is small explicit examples
that structural results need. This paper closes much of that gap for $k = 5$.

Let $N(k)$ be the least order of a tournament that is not
$k$-inducible. The answer is only known exactly for $k = 3$. For $k = 5$ the state of the art before
this work was $$12 \le N(5) \le 38,$$
**both ends of which are due to our companion paper [2]**: the lower bound from its exhaustive
census of all $D_{11} \approx 9.0 \times 10^{8}$ tournaments on $11$ vertices, of which about
$3.8 \times 10^{8}$ are even $3$-inducible and every one of the remaining $5.2 \times 10^{8}$
admits a margin-1 five-voter profile. Bachmeier et al. [1] had previously reached $n \le 10$ exhaustively, giving
$N(5) \ge 11$.

We spell out the upper end because the bounds in the literature are of two different
kinds and they are not comparable. Some are obtained by counting: one compares the number of
tournaments of a given order with the number that $k$ linear orders can produce, and when the
first exceeds the second, some tournament of that order must be missed. Such an argument names no
example. Bachmeier et al. [1] argued this way to reach $41$, and [2] sharpened the comparison by
restricting it first to regular and then to near-regular tournaments, reaching $39$ and then $38$.
The other kind of bound exhibits a tournament and checks it. There the record was $603\,979\,799$
vertices [1], from a dominating-set theorem of Alon et al. [4] together with a construction of
Graham and Spencer [5], and then $43$ [2] — Paley(43), the first example of moderate order.

Our $N(5) \le 23$ exhibits a tournament, and it is below both lines at once: it improves the best
exhibited bound from $43$ to $23$, and since $23 < 38$ it also beats the counting-based upper bound. 
It is obtained by a bespoke algorithmic decision procedure that fits this problem particulary well.

### 1.1 Why Paley(23) is hard to classify

The Paley tournament $P_q$, for a prime $q \equiv 3 \pmod 4$, has vertex set
$\mathbb{F}_q$ and an arc from $i$ to $j$ whenever $j - i$ is a nonzero square. It is
*doubly regular*: every vertex has out-degree $(q-1)/2$ and every ordered pair of vertices has
exactly $(q-3)/4$ common out-neighbours. Its automorphism group — the relabellings of the vertices
carrying every arc to an arc, written $\mathrm{Aut}(P_q)$ and defined with the rest of our
group-theoretic notation in Section 2 — has order $q(q-1)/2$, which equals the number of arcs, so
exactly one automorphism carries any given arc to any other.

Paley tournaments are the natural candidates for non-inducibility because they are far from being
transitive, and because their symmetry makes an otherwise hopeless search merely very hard. 
Bachmeier et al. [1] call them *quadratic residue tournaments* and write $Q_p$; their orientation
is the converse of ours, which costs nothing, because reversing every voter's order reverses every
arc of the majority tournament and changes no support. A tournament and its converse therefore
have the same majority dimension and are inducible at exactly the same margins. We use the name
Paley and the notation $P_q$ throughout.

Their SAT study establishes
$$\dim(Q_3) = \dim(Q_7) = 3, \qquad \dim(Q_{11}) = \dim(Q_{19}) = 5,$$
where $\dim$ denotes majority dimension, and then stops exactly where the problem becomes hard:

> "Unfortunately, we were not able to check whether the majority dimension of $Q_{23}$ is equal to
> 5 or larger as the SAT solver did not terminate within a total of six weeks."

That sentence is the point of departure for this paper.

### 1.2 Why Paley(43) was easy to classify

By contrast, our earlier proof that Paley(43) is not $5$-inducible [2] never searched the profile
space in general. It rests on a quantity we call the *slack*,
$$\mathrm{slack}_5(T) = 5\,\mathrm{MAS}(T) - 3C, \qquad C = \binom{n}{2},$$
where $\mathrm{MAS}$ is the maximum number of arcs of $T$ that a single linear order can agree
with. Summing the majority condition over all arcs bounds how far the five voters can *collectively*
fall short of that maximum, by exactly $\mathrm{slack}_5(T)$. A small slack therefore pins the
voters into a shallow shell around the best orders, and at $q = 43$, where $\mathrm{slack}_5 = 6$,
that shell is small enough to enumerate outright — about $1.8$ million cases once its symmetries
are quotiented out —
which is how [2] settles the case without searching the profile space at all.

The essential point is that **this is not a threshold in $q$**. The argument is valid at every $q$;
what varies is whether the shell it must enumerate is small enough to enumerate. Slack controls
the depth of that shell, and it is *not* monotone in $q$:

| $q$ | 7 | 11 | 19 | 23 | 27 | 31 | 43 |
|---|---|---|---|---|---|---|---|
| $\mathrm{slack}_5$ | 7 | 10 | 22 | **46** | 27 | 30 | **6** |

Paley(43) has the smallest slack anywhere in the family, and Paley(23) has nearly eight times as
much. At slack $46$ the forced level is far deeper than $1$ and the shell explodes
combinatorially, so the screen is not so much silent at $q = 23$ as unusable there. As [2] puts
it, the proof "exploits a genuine numerical coincidence". Nothing in that approach descends toward
$N(5)$, and no amount of computation would make it.

**One quantity, two obstructions.** It is worth separating two arguments that this table runs
together, because they concern different methods even though they are governed by the same number.
Writing $\mathrm{slack}_5(T) = 5\,\mathrm{MAS}(T) - 3C$, and noting that
$\alpha^{*} = \mathrm{MAS}/C$ throughout this family, the two are related by
$$\mathrm{slack}_5 \;=\; 5C\left(\alpha^{*} - \tfrac{3}{5}\right).$$
Read as *slack*, a large value says the screen of [2] must enumerate a deep shell, and the
enumeration is what becomes impossible. Read as *predictability*, the same large value says the
necessary condition $\alpha^{*} \ge 3/5$ is far from binding, so **no argument resting on that
linear relaxation can certify the instance** — not the screen, and not a linear program either.
The second reading is the more damaging of the two, and it is what makes a decision procedure
necessary rather than merely convenient.

**It is also what separates $k = 5$ from $k = 3$.** At $k = 3$ predictability decides exactly at
$N(3)$: the $96$ obstructions on eight vertices have $\alpha^{*} = \tfrac{13}{20}$, which is
*below* $\tfrac{2}{3}$, so the relaxation detects them and $N(3) = 8$ follows. At $k = 5$ it does
not: the table above has $\alpha^{*} > \tfrac{3}{5}$ at every $q$, yet Paley(23), Paley(27),
Paley(31) and Paley(43) are all non-inducible — Paley(23), which supplies our bound, sits
$\tfrac{2}{55}$ *above* the threshold. The failure of sufficiency therefore arrives before
$N(5)$, whereas at $k = 3$ it arrives after $N(3)$: there the first instance where
$\alpha^{*} \ge \tfrac{2}{3}$ is not sufficient has eleven vertices [2], comfortably past
$N(3) = 8$, and its threshold is attained only by a distribution whose denominator does not divide
three. Predictability will eventually fall below $\tfrac{3}{5}$, since
$\alpha^{*} \le \mathrm{MAS}/C \to \tfrac12$ for almost all tournaments, and any instance
where it does is immediately non-inducible. But that crossing happens strictly later than $N(5)$,
so it cannot be the route to it.

The gap between these two situations is the subject of this paper: the interesting instances are
precisely those too large for exhaustive profile search, too symmetric for SAT, and too slack for
a counting screen.

### 1.3 Contributions

1. **$N(5) \le 23$** (Section 3.1). Paley(23) is not $5$-inducible. This settles the instance on
   which the SAT solver of [1] ran for six weeks without terminating. It improves the best
   exhibited bound from $43$ to $23$, and since $23 < 38$ it is also below every bound reached by
   counting, so nothing in the bracket now rests on an argument that names no example. We also decide Paley(27) and Paley(31), which do not improve the
   bound but demonstrate the method's reach: each of the two larger tournaments is settled in
   less time than Paley(23).

2. **$N(5) \ge 13$** (Appendix C). Every tournament on $12$ vertices is $5$-inducible. The
   analysis settles all $2{,}048$ one-vertex extensions of each of the $D_{11}$
   tournaments on $11$ vertices, which is complete because every $12$-vertex tournament is such
   an extension — of each of its twelve one-vertex deletions.

3. **A formally certified negative result** (Appendix B.1). Paley(19) is not margin-1
   $5$-inducible. The search is split into independent subproblems (*cubes*); each is refuted by the
   SAT solver CaDiCaL, which emits its refutation as a machine-checkable *LRAT* proof; and every
   one of those proofs is then rechecked by a separate program that shares no code with the
   solver. We publish two root hashes and state
   precisely which one a third party must reproduce.

4. **Paley(43) is not vertex-critical** (Section 3.3). Deleting a vertex from Paley(43) leaves a
   42-vertex tournament that is still not $5$-inducible. Since Paley(43) is vertex-transitive, one
   computation settles all 43 deletions.

### 1.4 Related work

Two papers stand immediately behind this one, in different ways. Our companion paper [2] is the
prior art for the *bound*: it produced the first explicit non-$5$-inducible tournament of modest
size, Paley(43), and its two bounds are what we measure against: $N(5) \le 38$ by counting and
$N(5) \le 43$ explicitly. Bachmeier et
al. [1] is the prior art for the *problem and the method*: it introduces the computational study of
$k$-majority digraphs, characterises the $3$-majority case building on Dushnik and Miller [9], and
establishes hardness results for voting with a constant number of voters. Their
explicit non-$5$-inducible tournament rests on Alon et al.'s [4] dominating-set bound $F(k)$, on
Fidler's $F(5) \le 12$ [6], and on Graham and Spencer's construction. The case $k = 3$ is settled, and it is worth
separating the two halves. Shepardson and Tovey [8] introduced the *predictability*
$\alpha^{*}(T)$: the largest threshold $\alpha$ for which $T$ can be realised by a profile in
which every arc is supported by at least an $\alpha$ fraction of the voters. A $3$-voter profile
is exactly a $\tfrac{2}{3}$-supermajority representation, so $\alpha^{*}(T) < \tfrac{2}{3}$
rules out $3$-inducibility; their $8$-vertex tournament has $\alpha^{*} = \tfrac{13}{20}$, which
gives $N(3) \le 8$ at once. Our earlier paper [2] refuted their conjecture that
$\alpha^{*} \ge (m+1)/2m$ suffices for $m$-inducibility. The lower bound needs more, because the
converse implication is false — [2] exhibits an $11$-vertex tournament with $\alpha^{*} = \tfrac{2}{3}$ that is not
$3$-inducible — so $\alpha^{*} \ge \tfrac{2}{3}$ throughout $n \le 7$ does not settle it.
Eggermont, Hurkens and Woeginger [7] close that half by direct computation: every tournament on
$7$ vertices is $3$-inducible, exactly $96$ of the $6{,}880$ on $8$ vertices are not, and every
tournament on $8$ or $9$ vertices is $5$-inducible. Hence $N(3) = 8$ and $N(5) \ge 10$. The count
of $96$ is independently reported by [1], and our engine reproduces it as a known-answer test. Milosz, Hamel and Pierrot [17] studied the structure of minimum feedback arc sets in
tournaments, which supplies the counting arguments underlying the screen of [2].

Our certified computation (Appendix B.1) is standard in shape: it splits the problem into
independent subproblems, in the manner of *cube-and-conquer* [10] — a SAT instance is split by
fixing a few variables at a time, giving many partial assignments called *cubes*, and each cube is
handed to the solver as a problem of its own — and it adopts the standard of evidence set by
the Boolean Pythagorean triples proof [3, 12], in which every subproblem emits a machine-checkable
refutation in LRAT [11] that an independent checker validates. Appendix B.1 says what we take from
that line of work and in which two respects our artifact is weaker.

---

## 2. Preliminaries

Throughout, $T$ is a tournament on $V = \{1, \dots, n\}$ and $k = 5$ unless stated otherwise. We
write $N^{+}(v)$ and $N^{-}(v)$ for the out- and in-neighbourhoods of $v$.

Vertices are numbered from $1$ in all prose and tables. The accompanying software numbers them
from $0$; the translation is the obvious shift and is applied consistently in the repository's
verification scripts.

**Enumeration counts.** Several of the families swept here are large enough that their sizes are
better named than written out. Following [2], $D_n$, $R_n$ and $S_n$ denote the numbers of
isomorphism classes of, respectively, all tournaments, regular tournaments and self-converse
tournaments on $n$ vertices. In the text we give these to two significant figures; Appendix D
tabulates the exact values, which are what the completeness gates of Appendix C are checked
against.

**Notation for support and margin.** Recall from Section 1 that the *support* of an arc
$e = (i \to j)$ under a profile is the number of voters ranking $i$ above $j$; we write it $c(e)$.
A profile is a witness for $T$ when $c(e) \ge (k+1)/2$ for every arc, and the *margin* of $e$ is
$2c(e) - k$, positive for every arc of a witness. The three regimes for $k = 5$ are margin $1$
(every $c(e) = 3$), margin $3$ ($c(e) \in \{3,4\}$) and margin $5$ (no constraint beyond being a
witness).

**The base and its base states.** Every search in this paper starts by fixing how the voters
rank a handful of vertices, and then looks for ways to fit the rest around that. Choose a *base*
$B \subseteq V$ of a few vertices — five or six in practice — and write $T|_B$ for the
subtournament *induced* on $B$: the tournament on the vertex set $B$ that keeps exactly those arcs
of $T$ whose endpoints both lie in $B$.

A **base state** is one way for the $k$ voters to rank $B$ that is already consistent with what
$T$ demands there: $k$ orderings of $B$ whose majorities on $B$ reproduce $T|_B$, at the margin
being asked for. Base states that differ only by relabelling the voters are counted once, which
Lemma 2.3 below shows is legitimate.

Base states are the unit of work, and the loop over them is what we call the **outer loop**.
Each one is a self-contained subproblem — the voters' rankings
of $B$ are given, and the question is whether the remaining $n - |B|$ vertices can be inserted
into those rankings so that every arc of $T$ comes out right — so the search splits across base
states with no communication between them, and $T$ fails to be $k$-inducible exactly when every
base state fails. How many there are depends only on $|B|$, on $T|_B$ and on the margin regime,
and *not* on $n$: with the five-vertex base we use on the Paley tournaments there are $8{,}031$ of them
whether the tournament has $23$ vertices or $47$. Growing it therefore adds work inside each
subproblem but does not create more of them.

**Group-theoretic notation.** An *automorphism* of a digraph $D$ is a permutation of its vertices
carrying every arc to an arc; these form the **automorphism group** $\mathrm{Aut}(D)$ under
composition, and $D$ is **rigid** when $\mathrm{Aut}(D)$ contains only the identity. For a group
$\Gamma$ of permutations of a set $X$, the **orbit** of $x \in X$ is
$\Gamma x = \{\gamma(x) : \gamma \in \Gamma\}$, and the orbits partition $X$. We use orbits
of $\mathrm{Aut}(T)$ acting on three different sets: on the vertices, on the arcs, and — in
Lemma 2.1 below — on the **ordered pairs of distinct vertices**, where $\gamma$ sends $(u,v)$ to
$(\gamma(u), \gamma(v))$. An ordered pair is either an arc or the reverse of one, so that third
action has at least two orbits and refines neither of the first two.

**Symmetry.** Two symmetries act on witnesses, and both are exploited by every method in this
paper. The first is the $k!$ relabellings of the voters; the second is $\mathrm{Aut}(T)$ acting on
the vertices. Each yields a reduction that is without loss of generality.

The point of the second one is that a witness can be pushed around by an automorphism, so we may
decide in advance what some voter's top two vertices are going to be.

**Lemma 2.1 (orbit anchoring).** *Let $\mathrm{Aut}(T)$ act on the ordered pairs of distinct
vertices, and choose one representative pair from each orbit, say $(a_1, b_1), \dots, (a_m, b_m)$.
If $T$ is $k$-inducible, then $T$ has a witness in which, for at least one index $i$, some voter
ranks $a_i$ first and $b_i$ second.*

*Proof.* Let $\pi_1, \dots, \pi_k$ be a witness and let $(u, w)$ be the top two vertices of
$\pi_1$. The pair $(u,w)$ lies in one of the orbits; let $(a_i, b_i)$ be that orbit's chosen
representative, so there is $g \in \mathrm{Aut}(T)$ with $g(u) = a_i$ and $g(w) = b_i$. Applying
$g$ to every voter gives a profile $g\pi_1, \dots, g\pi_k$ whose majority tournament is
$g(T) = T$, so it is again a witness, and its first voter ranks $a_i$ first and $b_i$ second.
$\blacksquare$

Read it as a restriction we are entitled to impose. Before the lemma, the top two vertices of a
voter's ranking could be any of the $n(n-1)$ ordered pairs; after it, we may search only for
witnesses whose top two are one of the $m$ chosen pairs, and lose nothing — if any witness exists,
one of that restricted form does. The saving is the ratio $n(n-1)/m$, and for a Paley tournament
$m = 2$. The price is that **all $m$ representatives must be searched**: the lemma guarantees that
*some* $i$ works, not any particular one, so a run covering only one representative proves
nothing.

Why $m = 2$ for Paley: an ordered pair is either an arc or a non-arc, and $\mathrm{Aut}(P_q)$ is
transitive on each of the two sets, so there are exactly two orbits.

The same argument applied to the action on *vertices* gives a weaker restriction, which we also
use and therefore state.

**Corollary 2.2 (vertex anchoring).** *Let $\mathrm{Aut}(T)$ act on the vertices and choose one
representative $v_1, \dots, v_r$ from each orbit. If $T$ is $k$-inducible, then $T$ has a witness
in which some voter ranks some $v_i$ first.*

*Proof.* The proof of Lemma 2.1 verbatim, with the action on vertices in place of the action on
ordered pairs: the top vertex of $\pi_1$ lies in some orbit, and applying an automorphism carrying
it to that orbit's representative gives another witness. $\blacksquare$

A witness meeting either restriction — some voter's top *pair* is one of the chosen pairs, or some
voter's top *vertex* is one of the chosen vertices — is called **anchored**. The two are
alternatives rather than a sequence, each on its own without loss of generality, and which is the
better break depends on the tournament: for a vertex-transitive one the vertex form says only that some
voter ranks vertex $1$ first, a factor of about $n$, against $|\mathrm{Aut}(T)|$ for the pair
form, but the pair form costs more to test at every node, and where the vertex stabilisers are
trivial the vertex form is already as strong as anchoring can be.

For $P_q$ the pair form can be made concrete without computing the group. The map
$x \mapsto a(x - t)$ with $a$ a quadratic residue sends $(t,s)$ to $(0, a(s-t))$, and $a(s-t)$
sweeps the whole coset $\mathrm{QR}\cdot(s-t)$, so one representative per coset suffices; the two
cosets — top beats second, or does not — are mutually exclusive and exhaustive. **Both
representatives must be run, and completeness is the union of the two**; a single one is not a
valid break.

**Lemma 2.1 is only as good as the orbits it is given.** It licenses a search restricted to the
chosen representatives *provided* those representatives really do meet every orbit. Suppose they
miss one. Then every witness whose anchoring lies in the missed orbit is discarded unexamined, and
the search can report that no witness exists when in fact one does — the one error that would
matter here, since the results we are after are negative. Nothing inside the search can detect
this, because from the inside a discarded branch and an impossible branch look the same.

The check therefore has to happen outside the search. For every tournament we compute
$\mathrm{Aut}(T)$ separately, with `nauty`, and record its orbits alongside the run. When only a
subgroup $\Gamma \le \mathrm{Aut}(T)$ is known, using the orbits of $\Gamma$ is safe rather than
risky: $\Gamma$-orbits are finer, so a representative set meeting all of them meets every
$\mathrm{Aut}(T)$-orbit too. Such a set may be larger than necessary, and the only cost of that is
searching more than we had to.

**Lemma 2.3 (voter lex-ordering).** *If $T$ is $k$-inducible, then $T$ has a witness whose $k$
orders are non-decreasing under any fixed total order on linear orders.*

*Proof.* The support $c(e)$ counts voters and is therefore invariant under permuting them, so any
profile with the same multiset of orders induces the same tournament. Sorting the multiset gives
the required witness. $\blacksquare$

**What the two lemmas do to the base states.** The two lemmas reduce the running time by more
than two orders of magnitude, and it is worth seeing where each one bites.

Lemma 2.3 acts first, and it is absorbed into the definition of a base state itself. Since
permuting the voters changes no support, the $k$ orderings of $B$ can be held in a fixed sorted
order and each multiset counted once, which divides the count by a factor approaching
$k! = 120$. Lemma 2.1 acts second, and it *deletes* base states outright. A base state can extend
to an anchored witness only if one of its voters already ranks one of the chosen representative
pairs at the very top of $B$ — and that is a property of the base state alone, so it can be
tested before any search begins. What survives we call the **live** base states. For the
five-vertex base we use on the Paley tournaments, the representatives we run leave $2{,}591$ of the
$8{,}031$ live, and the best available choice of representatives would leave $2{,}537$; the
remaining three quarters are discarded for free.

Both reductions are available to all three formulations we compare, which is what makes
Appendix A a comparison of search strategies rather than of symmetry handling. Where they differ
is when the Lemma 2.1 condition is checked. Our depth-first search tests it *inside* the search
rather than only at the leaves, which it may do because the condition is monotone: once a partial
profile has lost the chance to satisfy it, inserting further vertices cannot restore it, so
failing the test is a sound reason to abandon a whole subtree. It also chooses per tournament between
anchoring an ordered pair and anchoring a single vertex, whichever is stronger there. The SAT
route checks the same condition once, at the root, where it decides which cubes are handed to the
solver at all. In an integer program it would appear as a disjunction over representatives, one
indicator per orbit summing to at least one, with lexicographic constraints between consecutive
voter blocks for Lemma 2.3 — though our ILP arm imposes neither, for reasons given in
Appendix A.1; we record the encodings only to show that nothing in the comparison turns on their
absence.

One point of hygiene is what makes the two lemmas compose rather than conflict. Every condition
above is phrased as "*some* voter ranks …", never "voter $1$ ranks …". A condition on a
*particular* voter would be destroyed by the re-sorting of Lemma 2.3, whereas one invariant under
permuting the voters survives it, so the two reductions multiply. The two engines therefore rest
on the same two reductions while sharing no implementation, and where they agree the agreement is
evidence about the implementations rather than about the lemmas.

**The search in five steps.** What the engine does, in one sentence, is *extend base states*.
A base state fixes how the $k$ voters rank the base $B$; the search then inserts the remaining
$n - |B|$ vertices into those $k$ rankings, one vertex at a time, and backtracks as soon as the
arcs already decided contradict $T$. A base state that can be extended all the way to $k$ full
rankings yields a witness; one that cannot is eliminated; and $T$ fails to be $k$-inducible exactly
when every base state is eliminated. That is the whole algorithm, and the rest of this paper is
about how to choose the base, how to cut the number of base states down, and how to make the
insertion step cheap.

The engine of Appendix A is then easiest to read as a fixed pipeline, in which the tournament $T$ and
the margin regime are the inputs and everything below is a choice made about them.

1. **Pick a size.** Choose $b$, the number of vertices of the base. In practice $b = 5$ or
   $b = 6$: the work of steps 3 and 4 grows steeply in $b$ while the depth it removes from step 5
   grows only linearly, so there is an optimum and it is small.
2. **Pick a subtournament.** Choose a base $B \subseteq V$ with $|B| = b$. Only the induced
   $T|_B$ matters for what follows, which is why the choice can be optimised cheaply
   (Appendix A.4) — and it should be, since the base-state count varies by more than two orders
   of magnitude across the twelve isomorphism classes at $b = 5$.
3. **Find its bases.** Enumerate the base states of $B$: the $k$-tuples of linear orders of $B$
   whose induced supports agree with $T|_B$, counted up to voter permutation by Lemma 2.3. Their
   number depends only on $|B|$, on $T|_B$ and on the margin regime — not on $n$.
4. **Determine the usable symmetries.** Compute $\mathrm{Aut}(T)$, or a subgroup, and its orbits,
   then choose one of three things to impose: the ordered-pair anchoring of Lemma 2.1, the vertex
   anchoring of Corollary 2.2, or neither. Whichever is imposed, discard the base states that no
   anchored witness can use; those that remain are the *live* ones. Imposing neither is sometimes
   the right choice. At unit margin the anchoring rules out so few partial profiles that it does
   not repay the cost of testing it at every node, and anchoring is the only step in the engine
   that discards profiles at all — a risk not worth running when the verdict being chased is a
   negative one.
5. **Run to completion, in parallel across base states.** Each live base state is an independent
   subproblem, so the outer loop parallelises with no communication. The verdict is positive as
   soon as any base state yields a witness. It is negative — $T$ is not $k$-inducible — only when
   *every* live base state has been searched to exhaustion and no search was stopped by its node
   or time cap. A run that hit a cap is not a verdict.

Steps 1–4 are cheap and are what a human chooses; step 5 is the computation. The same five steps
describe the SAT route, with step 5 replaced by "hand each live base state to a CDCL solver as a
*cube*, the partial assignment that fixes the voters' rankings of $B$" — which is why the two share their decomposition and their two lemmas, and differ only in
what refutes a leaf.

**Paley tournaments.** For $q \equiv 3 \pmod 4$ a prime power, $P_q$ is as defined in Section 1.1.
For prime $q$ the construction over $\mathbb{Z}/q$ is valid; for a prime power such as $q = 27$ it
is not, and the tournament must be built over $\mathbb{F}_q$. We note this because the naive
$\mathbb{Z}/27$ construction silently fails to be a tournament — 81 pairs receive no arc — and
searching such an object produces confident nonsense. Our implementation refuses it. Built over
$\mathbb{F}_{3^3}$, the tournament is, by canonical form, the unique most symmetric doubly regular
tournament on $27$ vertices.

The automorphism count also changes, and Section 1.1 states it for primes only. In general
$|\mathrm{Aut}(P_q)| = q(q-1)e/2$ with $e = [\mathbb{F}_q : \mathbb{F}_p]$, since the field
automorphisms contribute, so the coincidence with the arc count $q(q-1)/2$ is special to
prime $q$. At $q = 27$ the group has order $1053$ and is still transitive on arcs, which is all
Lemma 2.1 needs, on arcs and on non-arcs, and that holds at every $q$; we verified all of these
group orders independently.

---

## 3. Results

Two regimes recur below, so we recall them. *Unrestricted* (or plain majority) inducibility asks
only that each arc be carried by three, four or five of the five voters. *Unit margin* asks that
every arc be carried by exactly three against two — a strict restriction, so a unit-margin
witness is also an unrestricted one, while a unit-margin refutation is weaker than an
unrestricted one. Only an unrestricted refutation bounds $N(5)$.

All runs in this section were performed on a single laptop (Apple M-series, 14 cores, 24 GB RAM),
using at most 11 cores concurrently, with three exceptions that used a compute cluster: the
census of regular tournaments on $15$ vertices below, the self-converse census of order $13$
below, which was split between the two machines, and the computation of Appendix C. Costs are collected in one table at the end of this section and
reported in *core-hours*, the product of wall time and the number of workers; they are not
repeated in the text. Core-hours are comparable across our own runs but are **not**
machine-independent: Appendix A.5 records this laptop running $2.6$ to $3.3$ times faster per core
than the cluster we also used. The
quantity that does not depend on the machine is the *node count*, which we give wherever it was
recorded; Section 5.3 sets out exactly what a replication must hold fixed for it to match.

### 3.1 Paley(23), Paley(27) and Paley(31) are not 5-inducible

**Theorem.** *Paley(23) is not $5$-inducible. Consequently $N(5) \le 23$.*

The proof is a search that runs to completion. The base is $\{1,2,3,6,12\}$, which gives
$8{,}031$ base states; each is searched exhaustively for a five-voter profile inducing Paley(23);
and none contains one. The pieces were run and logged separately, which lets us verify three
things afterwards that a single aggregate figure would hide: that the pieces between them account
for every base state exactly once, neither missing one nor counting one twice; that no piece was
stopped early by a limit on time or on the size of its search; and that no piece reported a
profile. The file of witnesses is empty.

The same method settles two larger cases, checked the same way: Paley(27) is not $5$-inducible,
over the same $8{,}031$ base states, and Paley(31) is not $5$-inducible, over $21{,}009$ base
states with a different base. In both, the logs account for every base state exactly once, nothing
was stopped early, and no profile was found. Appendix A.5 gives the costs.

Neither Paley(27) nor Paley(31) improves the bound on $N(5)$. Since $5$-inducibility is
hereditary, any tournament containing a non-inducible subtournament is itself non-inducible, so
non-inducible tournaments already exist at every order $\ge 23$; exhibiting two more at $27$ and
$31$ adds nothing to the bound. Their value is *method reach* — they show that the
approach decides 27- and 31-vertex instances on one laptop, where SAT and integer programming do
not reach at all.

### Criticality across the family

Since arc-criticality implies vertex-criticality (Section 3.3), each cell below records only the
*strongest* property established, at each of the two margins. "Not vertex-critical" therefore also
rules out arc-criticality.

| $q$ | margin $\le 1$ | unrestricted |
|---|---|---|
| 19 | **arc-critical** | $5$-inducible, so criticality does not apply |
| 23 | not vertex-critical | **arc-critical** (Section 3.4) |
| 27 | not vertex-critical | open |
| 31 | not vertex-critical | open |
| 43 | not vertex-critical | **not vertex-critical** (Section 3.3) |

Three remarks. Paley(19) is the only member critical at either margin, and it is critical in the
strongest sense: reversing any one arc makes it margin-1 inducible, which by the implication also
gives vertex-criticality. At the other end, Paley(43) fails to be vertex-critical at *both*
margins, so the obstruction there is not concentrated at a vertex in either regime.

The interesting cell is $q = 23$: it is **vertex-critical unrestricted** — deleting any vertex
leaves a $5$-inducible tournament, and Paley(23)
is vertex-transitive so one deletion settles all $23$ — while being **not** vertex-critical at
margin $1$, since Paley(23) $-\,v$ is not margin-1 inducible either. Criticality is therefore not
monotone in the margin, and a tournament can be a minimal obstruction in one regime and not in the
other.

The two open cells are open by choice, not by obstacle: reversing an arc destroys the symmetry
that makes these tournaments tractable, so every base state becomes live and the scan is a large
multiple of the $q = 23$ one (Section 3.4), while neither answer would move $N(5)$ or bear on any
other statement here.


### 3.2 Paley(19) is 5-inducible, but not with unit margin

That Paley(19) is $5$-inducible is due to Bachmeier et al. [1], who computed
$\dim(Q_{19}) = 5$. Our search recovers it, and we verify the witness independently
with a script that shares no code with the search: it reads the witness and the tournament and
confirms that all $171$ arcs are supported by at least $3$ of the $5$ orders. We record the
agreement because it is the cheapest available check that our engine and their encoding are
deciding the same problem.

Our contribution at $q = 19$ is the negative half, and its certificate.

It is *not* $5$-inducible with unit margin. This is a complete refutation over all $2{,}200$
base states of the base $\{1,2,3,4,6\}$, and it is the statement we certify formally in
Appendix B.1.

The two facts together locate Paley(19) precisely on the margin scale: it is inducible, but every
witness must carry some arc by $4$–$1$ rather than $3$–$2$. Indeed the witnesses are not delicate.
A shuffled ten-way sweep at margin $\le 3$ found witnesses in all ten workers simultaneously, from
ten different base states, with no base state refuted; the support histogram of one such witness
is $159$ arcs at $3$–$2$ and $12$ at $4$–$1$, with none unanimous.

Both negative results in this section are additionally certified formally, by cube-and-conquer
computations in which every leaf is refuted by CaDiCaL [18] in LRAT and rechecked by `lrat-trim`,
a different program by a different author, with the solver's own proof checking deliberately
disabled. Both are complete on *both* halves — the
leaves and the claim that the leaves are exhaustive — and both reduce to the same two human
lemmas, 2.1 and 2.2. Appendix B gives the construction, the published root hashes, the two
respects in which our artifact is weaker than the Boolean Pythagorean triples proof it is modelled
on, and one episode in which the certificate asserted more than it had established.

### 3.3 Paley(43) is not vertex-critical

Call a tournament $T$ *vertex-critical* for $k$-inducibility if $T$ is not $k$-inducible but
$T - v$ is $k$-inducible for every vertex $v$. Vertex-criticality is the natural minimality notion
for an obstruction, and Paley(43) — the first explicit non-$5$-inducible tournament [2] — is the
natural candidate.

**Theorem.** *Paley(43) minus a vertex is not $5$-inducible. Hence Paley(43) is not
vertex-critical.*

Since Paley(43) is vertex-transitive, all 43 one-vertex deletions are isomorphic and a single
computation settles them all. The instance has $n = 42$; the sweep is complete over all $8{,}031$
base states of the base $\{1,2,3,4,11\}$, using the orbit break of Appendix A.3 with the two
representatives described below. The audit is exact: markers for base-state indices
$0, \dots, 8030$ with none missing, none duplicated, nothing capped or aborted.

**The orbit break.** $\mathrm{Aut}(P_{43} - v)$ contains the stabiliser of $v$ in
$\mathrm{Aut}(P_{43})$, which is cyclic of order $21$ and splits the remaining $42$ vertices into
exactly two orbits of size $21$ — the quadratic residues and the non-residues. Two representatives,
one from each, therefore meet every orbit; and since the stabiliser is a subgroup of the full
automorphism group of the deleted tournament, its orbits refine the true ones and the check is
conservative.

**Why a margin-$3$ sweep settles the unrestricted question.** The computation was run at margin
$\le 3$, which is cheaper than the unrestricted problem. For this tournament the two coincide, by the
following observation.

**Lemma (3-cycle bound).** *Let $u \to v \to w \to u$ be a directed triangle of $T$ and let
$\pi_1,\dots,\pi_k$ be any linear orders. Then*
$$c(u\to v) + c(v \to w) + c(w \to u) \le 2k.$$
*Consequently, in any majority witness, every arc lying in a directed triangle has support at
most $2k - 2\lceil (k+1)/2 \rceil$, which is $4$ when $k = 5$.*

*Proof.* A linear order cannot rank $u$ above $v$, $v$ above $w$ and $w$ above $u$ simultaneously,
so each voter agrees with at most two of the three arcs; summing over the $k$ voters gives the
inequality. If $c(u \to v) = 5$ then the other two supports sum to at most $5$, contradicting the
majority requirement that each be at least $3$. $\square$

Every arc of $P_{43} - v$ lies in at least $10$ directed triangles — indeed no arc lies in none —
so no arc of a majority witness could be unanimous, and margin $\le 3$ is not a restriction at
all. The margin-$3$ refutation is therefore an unrestricted refutation.

The same observation applies to every tournament in this paper, and more generally: in any *regular*
tournament every arc lies in a triangle, because for an arc $u \to v$ both $N^{+}(v)$ and
$N^{-}(u)$ are subsets of $V \setminus \{u,v\}$ of size $(n-1)/2$ each, so they intersect. We use
the lemma only where stated.

**A corollary: Paley(43) reconfirmed independently.** Since $5$-inducibility is hereditary on
subtournaments, a non-inducible subtournament forces the whole tournament to be non-inducible.
Paley(43) $-\,v$ is a subtournament of Paley(43), so the theorem above re-derives the main result
of [2], $N(5) \le 43$, *by a different method*: a complete decision procedure over the profile
space rather than the counting screen of [2], sharing no code and no argument with it. We record
this because a computational bound that has been obtained only once, by only one method, is worth
less than the same bound obtained twice; the reader who doubts the co-backing screen of [2] can
take Paley(43) from here instead.

**What the theorem does not give.** It does not improve $N(5) \le 23$: the instance has 42
vertices. Its content is that the obstruction in Paley(43) is not concentrated at any single
vertex, so the search for a minimal obstruction must descend further.

### 3.4 Vertex and arc criticality for Paley(23)

**Theorem.** *Paley(23) is arc-critical: reversing any single arc yields a $5$-inducible
tournament. Consequently it is vertex-critical.*

Let $T^{e}$ denote Paley(23) with the arc $(1,2)$ reversed. One instance settles all $253$ arcs,
and the reduction is an explicit orbit calculation rather than an appeal to symmetry in general:
the group $\{x \mapsto ax + b : a \text{ a nonzero square}\}$ has order
$253 = q(q-1)/2$, every one of its elements preserves the arc set, the orbit of $(1,2)$ is the
full arc set, and the stabiliser is trivial. So $\mathrm{Aut}(P_{23})$ is transitive on arcs, and
any two single-arc reversals of Paley(23) are isomorphic.

The computation is a scan of the $8{,}031$ base states of $T^{e}$ for a $5$-voter profile inducing
it. Reversing an arc destroys all symmetry, $|\mathrm{Aut}(T^{e})| = 1$, so no break is available
and every base state is live. A witness was found at base state $1{,}161$, after which the scan
was stopped; the remaining $6{,}996$ states were never examined, which is sound here precisely
because a witness is a positive certificate — completeness of the enumeration is what a negative
verdict needs, and this is not one.

The witness was verified independently of the search that produced it, by three checks on the
five ballots alone: that each is a permutation of the $23$ vertices; that the majority tournament
they induce agrees with $T^{e}$ in every one of the $253$ arcs and therefore differs from
Paley(23) in exactly the reversed one; and that the support of every arc lies in $\{3,4\}$. The
last is a consistency check against the $3$-cycle bound of Section 3.3 rather than a requirement:
no arc is unanimous, as none can be, since every arc of $T^{e}$ lies in at least five cyclic
triangles.

Two consequences. First, since arc-criticality implies vertex-criticality, this reproves by a
different route the vertex-criticality already established directly. Second, it does *not* extend
to margin $1$: the witness has arcs at support $4$ as well as $3$, and independently, Paley(23)
is not vertex-critical at margin $1$, so by the same implication it cannot be arc-critical there
either. Paley(23) is thus arc-critical unrestricted and not even vertex-critical at unit margin —
the sharpest instance in the family of the non-monotonicity noted in Section 3.1.


**Vertex-critical but maximally not arc-critical.** Arc-criticality implies vertex-criticality, so
it is natural to ask whether the two coincide. They do not, and the gap is as wide as it can be.
Let $h$ be one of the four unit-margin obstructions among the $110$ vertex-transitive tournaments
on $21$ vertices (Section 3.5). Then $h$ is *vertex-critical* at unit margin: $h - v$ has a
unit-margin witness, and since $\mathrm{Aut}(h)$ is transitive on the vertices, all $21$
deletions are isomorphic and one computation settles every one of them. Yet no
arc reversal helps at all. Trivial vertex stabilisers force trivial arc stabilisers, so the $210$
arcs fall into exactly ten orbits of size $21$, and each of the ten representatives is refuted by
an exhaustive sweep of its $2{,}200$ base states — $736$ separate runs in total, every one exhausted
with no cap and no witness, tiling each tournament's range exactly. So all $210$ single-arc reversals of
$h$ remain unit-margin obstructions. Deleting a vertex always restores inducibility; reversing an
arc never does.

Note the contrast with Paley(23), which is arc-critical unrestricted: there *every* arc reversal
restores inducibility. The two notions therefore come apart in both directions across the tournaments we
have, and neither implies anything about the other beyond the one implication above.

**And arc-criticality is not a property of the tournament.** All four unit-margin obstructions among the
$110$ have $|\mathrm{Aut}| = 21$ with trivial stabilisers, so each has exactly ten arc orbits of
size $21$; we take as representative the lexicographically least arc of each orbit. Sweeping those
representatives at unit margin gives four different pictures, and they line up with the group
rather than with the arcs:

| tournament | $\mathrm{Aut}$ | the ten orbits | obstructions |
|---|---|---|---|
| $h_1$ | $\mathbb{Z}_{21}$ | `U U U U U U U U U U` | $10$ |
| $h_2$ | $\mathbb{Z}_{21}$ | `U S U S S U U S S U` | $5$ |
| $h_4$ | $\mathbb{Z}_7 \rtimes \mathbb{Z}_3$ | `S S S S S S S S S S` | $0$ |
| $h_5$ | $\mathbb{Z}_7 \rtimes \mathbb{Z}_3$ | `S S S S S S S S S S` | $0$ |

`U` marks a reversal that is still not unit-margin inducible and `S` one that is. The rows are to
be read as multisets: the number of orbits, their common size and the verdicts they carry are
isomorphism invariants, but the order in which the ten appear is not, since the lexicographic rule
is relative to each tournament's supplied vertex numbering and only two of the four are labelled
canonically. Nothing below compares orbit $i$ of one tournament with orbit $i$ of another.

Three things follow. First, **arc-criticality at unit margin is carried by the arc and not by the
tournament**: $h_2$ has five orbits whose reversal stays an obstruction and five whose reversal does
not, interleaved, so no statement of the form "this tournament is or is not arc-critical" captures it.
Since every orbit has size $21$, that is exactly $105$ of its $210$ arcs whose reversal restores
inducibility and $105$ whose reversal does not; we call such a tournament **arc-semi-critical**. The
three possibilities are then all realised among the tournaments we have: Paley(23) is arc-critical at
unrestricted margin, every one of its arcs being critical; $h_2$ is arc-semi-critical; and $h_1$
has no critical arc at all.
Second, $h_1$ and $h_2$ sit at the two extremes of that scale, $10$ of $10$ and exactly $5$ of
$10$, with nothing between them among the tournaments we have. Third, and the reason we report the
automorphism groups: **every one of the $15$ reversals that remains an obstruction belongs to a
tournament with cyclic automorphism group**, and all $20$ orbits of the two with the nonabelian
group of order $21$ are inducible. That is exhaustive over these four tournaments — $40$ orbits, no
undecided cases — but it is four tournaments, two of each kind, and we have no mechanism to offer for
it; we record the alignment rather than claim a law.

**The picture at $21$ vertices, in summary.** Taken together with the vertex deletions, the four
tournaments settle the question of how far the two notions of criticality can come apart inside a single
family, and the answer is: as far as possible in one direction and not at all in the other. Every
unit-margin obstruction we know at $21$ vertices is *vertex-critical*, and exhaustively so: the
four tournaments and the $15$ arc reversals that remain obstructions have $319$ one-vertex deletions
between them, $289$ of them pairwise non-isomorphic by canonical form, and every one of the $289$
has an exhibited unit-margin witness. There is no exception anywhere. Arc-criticality, by contrast, takes all
three of its possible values among four tournaments of the same order with automorphism groups of the
same size. Deleting a vertex therefore always restores inducibility at these orders, while
reversing an arc restores it always, half the time, or never, according to the tournament. A corollary
worth stating for its own sake: since no one-vertex deletion of any of them is an obstruction, none
of these tournaments descends to a unit-margin obstruction on $20$ vertices. Neither does anything at
$19$: both doubly regular tournaments there are vertex-critical as well, the second one across all
$7$ of its deletion classes (Section 3.5). The smallest unit-margin obstruction we know of
therefore remains at $19$ vertices, and it is not for want of having looked one step below.

What the distinction is *not* is visible to the predictability relaxation, which assigns $h_2$'s
critical and free arcs alike no certificate at all, in line with Section 1.2.

### 3.5 Vertex-transitive and doubly regular tournaments

Beyond the Paley family we swept the structured families exhaustively up to $23$ vertices. Every
verdict is negative for the bound, so we report them briefly; what they buy is a map of where
obstructions sit and where they do not.

First, **the $21$-vertex vertex-transitive family contains no majority obstruction at all**: all
$110$ are $5$-inducible, $106$ of them already at unit margin and the remaining four by exhibited
majority witnesses. Since only a majority refutation can move $N(5)$, that family is closed as a
source of candidates below $23$ — and the closure survives one-arc perturbation, since reversing
any single arc of the four unit-margin obstructions, one representative per arc orbit, again
leaves a majority-inducible tournament in all $40$ cases. Second, *both* doubly regular
tournaments on $19$ vertices, Paley(19) and the one other of that order, are unit-margin
obstructions and both are majority-inducible, so the separation that makes Paley(19) interesting
is not a property of Paley(19) in particular. **Nor is its criticality**: the second one is
*arc-critical* at unit margin too. Its automorphism group has order $3$, so its $171$ arcs fall
into $57$ orbits of size $3$, and reversing the representative of any one of them yields a
tournament with a unit-margin witness — $57$ orbits, $57$ witnesses, none of the searches stopped
by a cap. Arc-criticality at unit margin is therefore shared by both
doubly regular tournaments of order $19$, which is the strongest form of criticality either could have
and matches Paley(23)'s behaviour at unrestricted margin. Third, every regular tournament on at
most $15$ vertices is inducible at unit margin, over all $R_{15} \approx 1.8 \times 10^{10}$ of those on $15$
vertices, with no instance left capped and with the instance counts of the $6{,}000$ residues of
`nauty`'s tournament generator [20] summing to OEIS A096368(7) [21] exactly. Fourth, every
self-converse tournament on $13$ vertices is inducible at unit margin, over all
$S_{13} \approx 9.5 \times 10^{7}$ of them, with nothing capped; the sweep was split across the
cluster and the laptop, and the listing of hosts is gated to exactly $S_{13}$ lines before any of
it is swept, so a truncated or duplicated catalogue stops the run rather than shrinking the claim.
With the order-$11$ census of [2] and the order-$12$ analysis of Appendix C, that settles every
self-converse tournament on at most $13$ vertices. Across the structured families swept here, ten tournaments are
unit-margin obstructions, six of them proved majority-inducible as well: two at $19$ vertices,
four at $21$, and four at $23$, of which only Paley(23) is settled at both margins. That count is
a census of these families and not of every obstruction known — the arc reversals of Section 3.4
supply $210$ further ones at $21$ vertices, none of them vertex-transitive.

**A refuted conjecture.** Write $t(T)$ for the least number of cyclic triangles containing an arc
of $T$. Every unit-margin obstruction we knew of had $t = 5$, and the one majority obstruction had
$t = 6$, which suggested that a large $t$ might be *necessary* for non-inducibility — an
attractive possibility, since $t$ is computable in $O(n^{3})$ and would have given a cheap filter
on candidates. At unit margin it is false: among the $23$-vertex vertex-transitive tournaments with
$t = 4$, three are obstructions while $36$ others are inducible, so the triangle load neither
implies nor precludes an obstruction. The unrestricted form of the conjecture survives, every
majority obstruction we have satisfying $t \ge 6$; refuting it would require a majority
obstruction with an arc lying in at most five cyclic triangles.

**Costs.** Every computation reported above, with its cost. A core-hour is the product of wall
time and worker count. All were run on the machine described at the head of this section except
the last two rows, which include cluster time and so are not comparable with the others;
Appendix A.5 records the factor between the two machines.

| computation | margin | verdict | core-hours |
|-------------------------------------------------------|--------------|---------------|-----------:|
| Paley(19), certified refutation | unit | not inducible | $25.1$ |
| Paley(23), certified refutation | unrestricted | not inducible | $236.0$ |
| Paley(23), sweep | unrestricted | not inducible | $34.03$ |
| Paley(27), sweep | unrestricted | not inducible | $31.04$ |
| Paley(31), sweep | unrestricted | not inducible | $26.89$ |
| Paley(43) $-\,v$, sweep | unrestricted | not inducible | $185.5$ |
| Paley(23), one arc reversed | unrestricted | inducible | $210.4$ |
| second doubly regular $19$, all $57$ arc reversals | unit | all inducible | $3.59$ |
| the $15$ obstruction reversals at $21$, every vertex deletion | unit | all inducible | $14.3$ |
| regular tournaments on $15$ vertices | unit | all inducible | $3{,}106$ |
| self-converse tournaments on $13$ vertices | unit | all inducible | *[PLACEHOLDER]* |

---

## 4. Discussion and open problems

### 4.1 Other applications of incremental depth-first search with MRV

Subject to the caveats of Appendix A.6, the shape of the engine may transfer: a placement search in
which each decision *refines*, rather than recomputes, the candidate sets of all remaining
objects, with a dynamic MRV order and an externally discharged symmetry break. The preconditions
are specific - the extensions of a partial solution must factor as a product that shrinks
monotonically under each decision, and the symmetry group must be large and computable — and
where they fail we would expect a general-purpose solver to win. Problems that appear to share the
shape include other tournament realisation questions and the construction of combinatorial designs
with prescribed automorphisms, but we have not tested it outside the present setting.

Neither device is new in isolation, and the closest antecedent is Knuth's Algorithm X with dancing
links [22]. Its column-choice rule — take the column with the fewest remaining ones — is our MRV
order, and its link surgery does what our refinement does: the state is altered in place and put
back on backtrack, so a node costs what changed rather than what the whole state contains. The
constraint is what differs. Exact cover partitions, whereas an arc of a tournament imposes a
threshold, at least three of five voters, so the search here is not an exact cover instance and
dancing links does not apply to it as it stands. What carries over is the pair of devices rather
than the algorithm, and the reason it carries over is the product structure of Appendix A.3: the
extensions of a partial profile factor as a choice of slot per voter, and it is the monotone
refinement of that product, not a covering structure, that lets one empty factor prune a subtree.

Two design lessons do seem to generalise, being about how to build such a search rather than
about when to prefer one. First, the incremental refinement, not the heuristic order, carried most
of the speedup here, a factor of $110$ against a factor of a few. Second, a symmetry break should
be *parameterised* by its representatives rather than hard-coded, so that its correctness
obligation becomes a separate computation instead of an assumption buried in the
search; Section 3.3 is a case where discharging that obligation required an explicit orbit calculation
that the engine could not have performed for itself.

### 4.2 Open problems

**The value of $N(5)$.** The bracket is now $13 \le N(5) \le 23$, with both ends constructive and
both moved from [2]. Closing it requires either a non-inducible tournament on fewer than 23
vertices or an exhaustive argument at $n = 13, \dots, 22$. Note that only a *majority* refutation
can move the upper end: the margin-1 obstructions below, at $n = 19$ and $21$, bound nothing about
$N(5)$, since every one of them is majority-inducible.

**Where to look next.** The state of the art for regular tournaments is that every one on
at most $15$ vertices is $5$-inducible at unit margin (Section 3.5). Regularity is a strong
hypothesis, and that bounds nothing about $n = 15$ in general. Since the regular ceiling on the
number of voters required already exceeds the general one at $n = 11$, we would not expect the
extremal instances to be regular, and the self-converse tournaments are the better next family.

**Vertex- and arc-criticality.** The state of the art is that Paley(23) is arc-critical
unrestricted (Section 3.4). Whether Paley(43) minus *two* vertices is $5$-inducible —
equivalently whether Paley(43) minus one vertex is vertex-critical — is open, and within reach:
$\mathrm{Aut}(P_{43})$ is transitive on arcs and hence on pairs of vertices, so that tournament
is unique up to isomorphism and one computation decides it.

**The margin hierarchy.** The first of the inclusions margin $1$ $\subseteq$ margin $3$
$\subseteq$ unrestricted is known to be strict (Sections 3.2 and 3.5). Whether the second is ever
strict — a tournament inducible by five voters but not at margin $\le 3$ — is open. The 3-cycle
bound of Section 3.3 shows that such a tournament must have an arc lying in *no* directed
triangle, that is an arc $u \to v$ with $N^{+}(v) \cap N^{-}(u) = \emptyset$, which forces
$d^{+}(u) \ge d^{+}(v) + 1$ and in particular rules out every regular tournament. The search
should therefore be directed at lopsided tournaments, not at perturbations of regular ones.

---

## 5. Reproducibility

### 5.1 The repository

The code, data and verdict files are at
`https://github.com/Leonardini/TournamentsBeyond5Voters`. Its `CLAIMS.md` carries one row per
statement made here, naming the artifact that holds the verdict and the command that re-derives
it, and it ends with an explicit list of what the package does not establish. A permanent archive
of the commit corresponding to the accepted version will be deposited on acceptance and its DOI
recorded here; readers of the preprint should take the commit hash from the version they are
reading.

The repository contains the search engine as a single C translation unit, the SAT encoding and
cube tooling in Python, the certification driver, the independent witness verifiers, the
tournaments as bit strings, and a verdict record for every result reported here. Each verdict
records the exact command line, the base and break used, the coverage audit, the cost, and — for
the certified results — the two root hashes. An acceptance script rebuilds both published
certificate roots from the per-cube hash chain and audits the coverage of every distributed sweep;
each of its checks is paired with a control that must fail, so that a check which has stopped
testing anything is visible as such.

### 5.2 What has been reproduced so far

Two independent implementations decide the same instances: the depth-first engine of Appendix A and
the SAT pipeline of Appendix B.1. They share the two human lemmas of Appendix B.2 and no code. The
margin-1 statements for Paley(19) and Paley(23) have six independent complete refutations across
three different base decompositions; the unrestricted Paley(23) statement has two, from
independent runs with different bases and different anchors.

Witness verification is likewise independent of the search: a separate script reads the tournament
from its bit-string, reads the witness from the run log, and recomputes every arc's support.

### 5.3 Which hashes must replicate and which may not

The certified computations publish two root hashes, and only one of them is portable.

**ROOT (CNF)** commits to the SHA-256 of every cube's CNF, in cube order. These files are
generated by the repository's own code from the tournament and the base, and are reproducible on
any machine: a third party who regenerates the cube set *must* obtain this exact value. It is the
meaningful cross-check, because it proves they solved the same problems.

**ROOT (proofs)** additionally commits to the LRAT proof bytes. These are **not** portable.
CaDiCaL is deterministic run to run on a fixed binary — we verified this, three runs identical —
but its heuristics use floating-point scoring, so a different version, architecture or
optimisation level may search differently and emit a different, equally valid proof. A different
solver differs entirely: Glucose emits $2.36$ MB of DRAT where CaDiCaL emits $2.79$ MB of LRAT for
the same leaf. This hash therefore detects corruption or tampering *within* a run and reproduces
only on an identical build. **A mismatch here is not evidence of an error.**

**Search costs: nodes replicate, hours do not.** The same three-way distinction applies to the
uncertified sweeps. *Verdicts* replicate under any correct implementation — that is the claim the
paper makes. *Node counts* replicate exactly, but only with five things held fixed, every one of
which can differ silently between two people running what they believe is the same computation:

1. the same binary, or at least identical tie-breaking in the variable order and in the domain
   refinement — ties are common and a different rule explores a different tree of the same size
   class but not the same size;
2. the same vertex numbering of the tournament;
3. the same base size and base;
4. the same resulting set of base states, which follows from (2) and (3) but is worth checking
   directly, since it is the width of the outer loop;
5. the same margin regime.

The engine prints all of these except (2) in a header on every run — margin, variable order, MRV
cap, tie-break mode, symmetry break, base size, base, base arc pattern and base-state count — so a run
log is a self-describing fingerprint. Condition (2) is the tournament file itself, which is why
the repository stores tournaments rather than regenerating them from their constructions: one rebuilt
from its Cayley presentation need not carry the numbering we used, and two of the four $21$-vertex
tournaments of Section 3.4 are in fact *not* in the canonical labelling that a fresh
isomorphism-class enumeration produces. *Wall-clock and core-hours* replicate only in order of
magnitude; Appendix A.5 measures a factor of $2.6$ to $3.3$ per core between the two machines we
used, and a loaded machine distorts them further.

One practical note for anyone rerunning the checker: `lrat-trim` signals success with
`s VERIFIED` and exit code $20$, following the SAT-solver convention, not exit code $0$.

---

## Motivation and statement of AI use

This paper grew out of the companion work [2], whose explicit bound $N(5) \le 43$ came from a
structural argument that does not descend, and whose counting bound $N(5) \le 38$ names no
tournament at all. The question of what a genuine decision procedure would
reach, at the orders the screen cannot speak about, is what led to the engine of Appendix A.

During the preparation of this work, the authors used Claude for exploratory reasoning,
implementation assistance, drafting and editing. The authors reviewed and edited the output as
needed and take full responsibility for the content of the published article.

---

## Acknowledgments

This work was granted access to the HPC resources of IDRIS under an allocation made by GENCI. LC
acknowledges funding from the MRC Centre for Global Infectious Disease Analysis (reference
MR/X020258/1), funded by the UK Medical Research Council (MRC). This UK funded award is carried
out in the frame of the Global Health EDCTP3 Joint Undertaking.

---

## References

[1] G. Bachmeier, F. Brandt, C. Geist, P. Harrenstein, K. Kardel, D. Peters, H. G. Seedig.
$k$-Majority digraphs and the hardness of voting with a constant number of voters.
*Journal of Computer and System Sciences*, 105:130–157, 2019.

[2] L. Chindelevitch, A. Harutyunyan. Tournaments determined by three and five voters. *Submitted*.

[3] M. J. H. Heule, O. Kullmann, V. W. Marek. Solving and verifying the Boolean Pythagorean triples
problem via cube-and-conquer. In *Theory and Applications of Satisfiability Testing (SAT 2016)*,
LNCS 9710, pages 228–245, 2016. arXiv:1605.00723.

[4] N. Alon, G. Brightwell, H. A. Kierstead, A. V. Kostochka, P. Winkler. Dominating sets in
$k$-majority tournaments. *Journal of Combinatorial Theory, Series B*, 96(3):374–387, 2006.

[5] R. L. Graham, J. H. Spencer. A constructive solution to a tournament problem.
*Canadian Mathematical Bulletin*, 14(1):45–48, 1971.

[6] D. Fidler. A recurrence for bounds on dominating sets in $k$-majority tournaments.
*Electronic Journal of Combinatorics*, 18(1):P138, 2011.

[7] C. Eggermont, C. Hurkens, G. J. Woeginger. Realizing small tournaments through few
permutations. *Acta Cybernetica*, 21(2):267–271, 2013.

[8] D. Shepardson, C. A. Tovey. Smallest tournaments not realizable by
$\tfrac{2}{3}$-majority voting. *Social Choice and Welfare*, 33(3):495–503, 2009.
doi:10.1007/s00355-009-0375-7.

[9] B. Dushnik, E. W. Miller. Partially ordered sets. *American Journal of Mathematics*,
63(3):600–610, 1941.

[10] M. J. H. Heule, O. Kullmann, S. Wieringa, A. Biere. Cube and conquer: guiding CDCL SAT
solvers by lookaheads. In *Haifa Verification Conference (HVC 2011)*, LNCS 7261, pages 50–65,
2012.

[11] L. Cruz-Filipe, M. J. H. Heule, W. A. Hunt Jr., M. Kaufmann, P. Schneider-Kamp. Efficient
certified RAT verification. In *Automated Deduction (CADE 2017)*, LNCS 10395, pages 220–236, 2017.
This is the paper introducing the LRAT format that `lrat-trim` consumes.

[12] L. Cruz-Filipe, J. Marques-Silva, P. Schneider-Kamp. Formally verifying the solution to the
Boolean Pythagorean triples problem. *Journal of Automated Reasoning*, 63(3):695–722, 2019.
doi:10.1007/s10817-018-9490-4.

[13] M. J. H. Heule. Solving and verifying the Boolean Pythagorean triples problem. ACL2 Seminar,
University of Texas at Austin, 9 September 2016.
`https://www.cs.utexas.edu/~moore/acl2/seminar/2016.09.09-heule/ACL2.pdf`
Source of the scale and validation-cost figures quoted in Appendix B.1, which are not stated in
[3] or [12]; the talk is their citable origin.

[14] M. J. H. Heule. Schur number five. In *AAAI 2018*, pages 6598–6606, 2018.

[15] J. Brakensiek, M. Heule, J. Mackey, D. Narváez. The resolution of Keller's conjecture.
In *Automated Reasoning (IJCAR 2020)*, LNCS 12166, pages 48–65, 2020.

[16] D. C. McGarvey. A theorem on the construction of voting paradoxes. *Econometrica*,
21(4):608–610, 1953.

[17] R. Milosz, S. Hamel, A. Pierrot. Median of 3 permutations, 3-cycles and 3-hitting set
problem. In *Combinatorial Algorithms (IWOCA 2018)*, LNCS 10979, pages 224–236, 2018.

[18] A. Biere, K. Fazekas, M. Fleury, M. Heisinger. CaDiCaL, Kissat, Paracooba, Plingeling and
Treengeling entering the SAT Competition 2020. In *Proceedings of SAT Competition 2020*, pages
51–53, 2020. We use CaDiCaL as the leaf solver and Biere's `lrat-trim` as the independent
checker.

[19] M. J. H. Heule, W. A. Hunt Jr., N. Wetzler. Trimming while checking clausal proofs. In
*Formal Methods in Computer-Aided Design (FMCAD 2013)*, pages 181–188, 2013. The `drat-trim`
checker.

[20] B. D. McKay, A. Piperno. Practical graph isomorphism, II. *Journal of Symbolic Computation*,
60:94–112, 2014. The `nauty` and `gentourng` tools, used for all tournament enumeration.

[21] OEIS Foundation Inc. Entry A096368, *Number of regular tournaments on $2n+1$ labeled nodes*.
The On-Line Encyclopedia of Integer Sequences, `https://oeis.org/A096368`.

[22] D. E. Knuth. Dancing links. In J. Davies, B. Roscoe, J. Woodcock, editors, *Millennial
Perspectives in Computer Science*, pages 187–214. Palgrave, 2000. arXiv:cs/0011047.



---

## Appendix A. The search engine

Both integer programming and satisfiability are central to this project rather than foils for it.
Every computational claim in the companion paper [2] is certified by an integer or linear program,
and the integer program of A.1 below is that paper's formulation B.1, verbatim; the only machine-checked theorem in this paper
is a SAT computation from end to end, with CaDiCaL [18] emitting LRAT proofs that `lrat-trim`
checks. The claim here is narrow: on this one decision problem, at this one range of sizes, neither
tool reaches the answer while a search built around the problem's own structure does — and the same
SAT machinery is then indispensable for turning that answer into a proof.

### A.1 Integer programming is too slow

The natural integer program has one binary $x_{v,ij}$ per voter $v$ and pair $i < j$, meaning that
$v$ ranks $i$ above $j$, with $x_{v,ji}$ read as $1 - x_{v,ij}$ so that antisymmetry is structural.
Each voter is forced to be a linear order by forbidding both orientations of every $3$-cycle,
$$0 \;\le\; x_{v,ij} + x_{v,jl} - x_{v,il} \;\le\; 1 \qquad (i < j < l),$$
and the profile is forced to induce $T$ by one majority row per arc,
$\sum_{v} x_{v,ij} \ge (k+1)/2$. There is no objective: this is a pure feasibility problem. At
$q = 23$, $k = 5$ it has $1{,}265$ binaries, $17{,}710$ transitivity rows and $253$ majority rows.

The obstruction is structural rather than a deficiency of the solver. Put $x_{v,ij} = 3/5$ on every
arc of $T$ and $2/5$ on every non-arc, the same for all voters. Every cyclic triple then reads
$3/5 + 3/5 - 2/5 = 4/5$ and every transitive one $3/5$, both interior to $[0,1]$, while every
majority row is tight at exactly $3$. The relaxation is therefore feasible, and since the problem
carries no objective, LP feasibility yields no bound whatever: branch-and-bound is left with
nothing to prune by except infeasibility discovered deep in the tree. That fractional point is also
invariant under both symmetry groups acting on the problem — the $k!$ voter relabellings and
$\mathrm{Aut}(T)$ — so it supplies no branching direction either, and orbital branching recovers
only the $k!$ factor. CPLEX and Gurobi both failed to close instances at $n = 19$ within a day.

### A.2 SAT is too slow

The dissent-Boolean encoding of Section 1.1 is compact and propagates well locally. It is the right
encoding — we use it ourselves for the certified result — but as a *decision procedure* on a
symmetric instance it is dominated by the search below.

Table 4 of [1] reports their `Sat-Check-k-Majority` on uniform random tournaments, tabulating only
entries whose average stays under 20 seconds. The $k = 5$ column reads

| $n$ | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|---|
| seconds | $0.23$ | $0.35$ | $0.54$ | $5.87$ | $11.07$ | $18.95$ | — |

so on *random* instances the method leaves the table between $n = 23$ and $n = 24$, roughly
doubling per added vertex. Random tournaments are the easy case: no automorphisms to rediscover
and, being far from extremal, many witnesses. On the structured instance of the same order,
Paley(23), the same solver ran for six weeks without terminating. The gap between $18.95$ seconds
and six weeks at equal $n$ is the cost of symmetry.

A better encoding and an explicit symmetry break both help substantially and are still not enough.
The algorithm of [1] encodes each voter by order variables over $k n^2$ literals and expresses the
majority condition through a Tseitin transformation; the dissent-Boolean encoding carries one
variable per (arc, voter) pair, $k\binom{n}{2}$ in all, and needs no auxiliaries, the majority
condition being exactly the $\binom{5}{3} = 10$ clauses forbidding each $3$-subset of dissenters.
On doubly regular test tournaments, CaDiCaL conflict counts were $2{,}399$ for the order-variable
family, $1{,}491$ for an intermediate pair-label encoding and $57$ for the dissent-Boolean one, a
$26$ to $42$-fold reduction. We then implemented three breaks: a lex chain on the voters' dissent
vectors, a strengthening forbidding repeated voters, and an $\mathrm{Aut}$-based pin fixing a
cyclic triangle. (The last two must not be combined with the first, for the reason in Appendix A.3:
a pin and a lex chain can spend the same group twice.) With these active, neither Paley(19) nor the
second doubly regular tournament of order $19$ returned a verdict.

So a $40$-fold better encoding and a sound symmetry break together leave the instance out of reach.
What does work is supplying the solver with the decomposition itself — cube-and-conquer over base
states, which is how both refutations are certified in Appendix B. A CDCL solver must otherwise
discover that decomposition for itself, and cannot exploit $\mathrm{Aut}(T)$ at all without an
explicit break in the encoding. SAT earns its place in this paper as a *proof format* rather than
as a decision procedure; and once one has the decomposition, one may as well run it directly, which
is the search below.

### A.3 Depth-first placement search

The search maintains a partial profile: a set $S \subseteq V$ of *placed* vertices together with,
for each voter, a linear order of $S$. It begins from a base state, which places $B$, and extends
by inserting one unplaced vertex at a time. Inserting $v$ means choosing, for each voter
independently, a slot among the $|S| + 1$ available; the *domain* $D(v \mid S)$ is the set of
$k$-tuples of slots consistent with every arc between $v$ and $S$. A partial profile is extendable
only if every unplaced vertex has a non-empty domain, and domains shrink monotonically as $S$
grows, which makes the search a constraint-propagation problem rather than a blind enumeration.

```
ALGORITHM 1.  Placement search for k-inducibility of T

Input :  tournament T on vertex set V;  number of voters k;
         margin regime  (majority: support >= (k+1)/2;  unit: support == (k+1)/2)
Output:  a witness profile, or a refutation

MAIN
  for each base state  (a lex-canonical assignment of the base B to k orders):
      S <- B
      D(v | S) <- fresh enumeration, for every v not in S
      if any D(v | S) is empty:  continue          // this base state is dead
      if DFS(S) succeeds:        return its witness
  return "not k-inducible"                         // no base state extends

DFS(S)
  if S = V:  return the profile                    // all vertices placed
  v* <- argmin  |D(v | S)|   over v not in S       // MRV, recomputed at EVERY node
        ties broken toward  max | |out(v) & S| - |in(v) & S| |
  for each slot tuple p in D(v* | S):
      insert v* at p in each of the k orders;  S' <- S u {v*}
      for each w not in S':
          D(w | S') <- REFINE( D(w | S), p, w, v* )
          if D(w | S') is empty:  undo;  continue with the next p
      if DFS(S') succeeds:  return its witness
      undo                                         // arena pointer reset
  return failure

REFINE(D, q, w, u)        // q = the slot tuple just used for u
  D' <- {}
  for each p in D:
      lift p to p' voter by voter:
          p_i <  q_i  ->  p'_i = p_i        // w stays before u
          p_i >  q_i  ->  p'_i = p_i + 1    // w stays after u, shifted by the insertion
          p_i == q_i  ->  BOTH are legal, so the tuple splits in two
      keep those lifts whose support  c_w(u) = #{ i : w before u }
      meets the requirement of the single new arc between w and u
  return D'
```

Four choices make it fast, and the second is the one that made $n = 19$ decidable at all.

**A dynamic variable order.** At every node we insert the unplaced vertex minimising
$|D(v \mid S)|$, breaking ties toward the vertex whose arcs to $S$ are most imbalanced. The
important part is that the order is recomputed at every node rather than fixed per base state: on
Paley instances a static order is not competitive, because how constrained a vertex is depends
strongly on which part of the tournament has already been placed.

**Incremental domain refinement.** Recomputing $D(v \mid S)$ from scratch at each node is the
dominant cost of a naive implementation; instead the child's domain is derived from the parent's by
the three cases in `REFINE` above, after which the single new arc filters the lifted tuples by
their support. Child domains are therefore refinements of parent domains, computed in time
proportional to the surviving tuples rather than to the whole slot space, and domains live in a
stack-disciplined arena indexed by (depth, vertex) so that backtracking is a pointer reset. Like
for like this is worth a factor of about $110$ in wall time.

Only part of that factor is speed per node, and the rest is a point worth separating. Before
incremental maintenance, computing $|D(v \mid S)|$ meant a fresh enumeration, so the implementation
counted each domain only up to a cap. A cap suffices to detect the empty domain — which is what
prunes — but it destroys the ordering among everything above it, and the argmin degenerates to an
arbitrary choice. On a $29$-instance benchmark drawn from Paley(19), with identical verdicts
throughout, the search visited $992{,}378$ nodes under the capped rule and $294{,}964$ under the
exact one: a factor of $3.4$ in tree size that is pure decision quality, leaving roughly $32$ of
the $110$ as cost per node. The domain statistics explain why the cap hurt so much here — the mean
$|D(v \mid S)|$ on Paley(19) is $64$ at $|S| = 5$, falling to $8.2$ at $|S| = 11$, where most of
the search lives, and $4.8$ at $|S| = 12$ — so a cap of five sat *below* the mean almost everywhere
the search spent its time. Raising the cap is no fix on its own, since under fresh enumeration a
higher cap costs proportionally more at every node; that is what made the capped design right
*before* the refinement existed. Exact selection was not worth having until it became free.

**Symmetry breaking.** The $k!$ voter symmetry is absorbed exactly by the base-state definition,
which counts non-decreasing tuples only. For $\mathrm{Aut}(T)$ the engine imposes the anchoring of
Lemma 2.1 or of Corollary 2.2, whichever is stronger on the tournament: the condition is invariant under
permuting voters, so it composes with the base lex-order, and monotone under insertion, so it can
be tested during the search rather than only at the leaves. Its soundness obligation is external —
the engine cannot compute $\mathrm{Aut}(T)$ and so cannot check that the supplied representatives
meet every orbit — and Section 2 sets out how we discharge it.

**Early termination and caching by arc pattern.** A cheap per-voter agreement bound, obtained by counting the
agreement between voter $i$ and the arcs between $v$ and $S$ two ways, proves $D(v \mid S)$ empty
in $O(k|S|)$ time without enumerating it. And the per-base-state work is keyed by the *arc pattern* of
$T|_B$ rather than by $B$ itself, so base-state counts — which depend only on that pattern — are
computed once and reused across every copy of the same base class and across every $q$.

### A.4 Choosing the decomposition

The base set is not a free parameter: different bases give wildly different total cost, and the
ranking is not by base-state count. For each of the twelve isomorphism classes of $5$-vertex
tournament we compute, without search, the number of base states and the number surviving the
automorphism break, then measure seconds per base state on a sample and rank configurations by the
*product*. This matters: in our Paley(31) experiments the class with $4{,}007$ surviving base
states beat the class with $2{,}537$ on total cost, because its states are individually much
cheaper, so ranking by count alone would have chosen the worse configuration.

### A.5 How the cost scales in $q$

On a fixed base decomposition the total cost **decreases** as the tournament grows. Measured on 24
bit-identical base states of the same $5$-vertex base class, on one core with the other nine busy:

| ratio | total time | nodes | $\mu$s per node |
|---|---|---|---|
| $q = 31$ over $q = 27$ | $0.933$ | $0.614$ | $1.521$ |
| $q = 43$ over $q = 31$ | $0.746$ | $0.385$ | $1.935$ |
| $q = 43$ over $q = 27$ | $0.739$ | $0.237$ | $2.94$ |

Two steep opposing trends, not a plateau: node counts fall roughly like $n^{-3}$, because a larger
Paley tournament is *more* constrained and refutation fires higher in the tree, while per-node work
rises roughly like $n^{+2.3}$, and the fall keeps winning. It can win only because the outer loop
is independent of $q$: a $5$-vertex base class has the same number of base states at every $q$,
that being a property of the base pattern and not of the tournament, so growing the tournament
adds work per node without widening the decomposition. The full runs bear this out:

| $q$ | core-hours | nodes | seconds per live base state |
|---|---|---|---|
| 23 | $34.03$ | — | $47.5$ |
| 27 | $31.04$ | $1.14 \times 10^{8}$ | $44.0$ |
| 43 | $22.87$ | $1.43 \times 10^{9}$ | $32.5$ |

Paley(43) is decided in **less time than Paley(27)**, despite exploring an order of magnitude more
nodes, and that run is an independent re-derivation of the main theorem of [2] by a method sharing
nothing with the co-backing screen. The scope of the claim is exactly those three values of $q$ on
this one decomposition, where growing $q$ tightens the constraints. It is not a claim that every
larger instance is cheaper — Paley(43) minus a vertex costs $185.5$ core-hours, far more than
Paley(43) itself, because deleting a vertex *removes* constraints and weakens the automorphism
group at once, and it averages $83.2$ seconds per base state with a maximum of $313.2$ — nor that
the trend continues past the range measured.

A second, independent gain runs the same way: the search gets much cheaper as the margin is
tightened. On the identical tournament, engine and $5$-vertex base class,

| Paley(43) $-\,v$, $n = 42$ | base states | core-hours |
|---|---|---|
| margin $\le 1$ | $2{,}200$ | $2.07$ |
| unrestricted | $8{,}031$ | $185.5$ |

a factor of about $90$. Part is the outer loop — requiring every arc to sit at exactly $3$–$2$
admits $2{,}200$ base states where majority admits $8{,}031$ — and the rest is per state: under
exact margin the last voter is *forced*, since the support accumulated over the first $k-1$ voters
determines what the last must contribute, so a whole level of the search collapses. The pattern
holds across the family and again improves with $n$: complete margin-$1$ refutations cost $2.86$
core-hours at $n = 26$, $2.21$ at $n = 30$ and $2.07$ at $n = 42$. We do *not* claim the converse
for the general-purpose methods: tightening the margin adds constraints to both encodings, which
usually makes a refutation easier, so the effect there could run either way and we have not
measured it. Our claim is one-sided and about our own engine — faster on the more constrained
question and faster on the larger tournament, which is the opposite of what one expects from a search
procedure, and is what makes the approach usable at these sizes.

**Two machines, and why their costs are not comparable.** Some computations ran on a cluster
rather than the laptop. Measured across three independent campaigns, the cluster ran at $2.6$ to
$3.3$ times the laptop's cost per unit of work, the larger machine being *slower* per core, so a
core-hour figure means nothing here without the machine that produced it.

### A.6 The scope of the comparison

We are not claiming that bespoke search beats integer programming or satisfiability in general — it
does not, and the reasons general-purpose solvers dominate most of combinatorial optimisation still
apply. This engine is narrow: it exploits the specific facts that a partial profile's extensions
form a product of per-voter slot choices, that this product refines monotonically, and that
$\mathrm{Aut}(T)$ is large and computable, and removing any one of those leaves it with no
advantage. The claim is bounded three ways at once — it concerns $k$-inducibility of highly
symmetric tournaments at $k = 5$ for $19 \le n \le 43$; it reflects *our* implementations, so a
better-tuned model or a cleverer CNF might change the numbers; and it uses the best formulations we
could construct for each method, which for SAT means an encoding measured $26$ to $42$ times better
than the published one and for the integer program means formulation B.1 of [2] rather than a straw
man. Within those bounds the comparison is real: instances the general-purpose methods did not
settle for us, the search settles in hours.

---

## Appendix B. The formal certificates

### B.1 The certified refutations

Both machine-checked results follow an established design rather than a new one. *Cube-and-conquer*
is due to Heule, Kullmann, Wieringa and Biere [10]: split a hard instance into many partial
assignments (*cubes*), hand each to a CDCL solver, and let the splitting supply the global structure
the solver cannot find for itself. The standard of *proof* is the one Heule, Kullmann and Marek set
for the Boolean Pythagorean triples problem [3], and Schur number five [14] and the Keller
conjecture [15] after it: every subproblem emits a machine-checkable refutation, validated by an
independent checker rather than trusted. We claim no methodological novelty.

Two departures are worth stating, both consequences of our setting. Our cubes are not produced by
lookahead splitting but are *base states*, a combinatorial decomposition we have independently from
Appendix A — which is what lets the coverage of the cube set be certified separately (B.2) instead
of resting on a splitting heuristic. And where [3] published its proof, we *verify and discard*:
each LRAT proof is checked, hashed and deleted, so peak storage is one proof per worker rather than
terabytes, and what we publish is a hash commitment. That is the weaker artifact — a reader cannot
re-check our proofs without regenerating them — and Section 5.3 says which published hashes a third
party must reproduce. The choice suits the scale. Re-verifying the Boolean Pythagorean triples
proof costs about $13{,}000$ CPU-hours to decompress and $16{,}000$ to validate [13], so at that
scale publishing the bytes is essential because no referee will reproduce the search. Our
certificates are three orders of magnitude smaller: $25.1$ core-hours for Paley(19) and $236.0$ for
Paley(23) cover solving *and* checking from nothing, so a reader who distrusts our hashes can
regenerate an entire computation for between a thousandth and a hundredth of what validating that
proof costs, and compare portable roots — which is exactly the check Section 5.3 supports.

For Paley(19) at margin $1$ the instance is the dissent-Boolean encoding of Section 1.1 at
$q = 19$, $k = 5$: $855$ variables and $12{,}265$ clauses. The cubes are the base states of the
$6$-vertex base $\{1,2,3,4,5,12\}$ — $142{,}251$ of them, of which $22{,}876$ survive the arc-orbit
break — and each is handed whole to CaDiCaL with `--lrat=true --checkproof=0`. The self-check is
*deliberately disabled*: the point is that a different program validates the proof, so the solver
must never be permitted to validate its own work. Each LRAT proof is checked by `lrat-trim`, then
hashed and discarded. The cost was $24.3$ core-hours to solve and $0.8$ to check, $2.64$ hours wall
on ten workers. We chose LRAT over DRAT on measurement: on real leaves from this instance, Glucose
with DRAT plus `drat-trim` cost $1.043$ s per leaf against CaDiCaL with LRAT plus `lrat-trim` at
$0.295$ s — a factor of $3.5$ end to end and of $29$ in checking alone, because LRAT carries
explicit clause hints and the checker performs no backward search. Because the cubes are base
states, no *deepening* step is involved and no uncertified enumeration enters the trust chain.

The same two-part certificate has since been completed for the Paley(23) refutation of Section 3.1,
at margin *unrestricted*, so that theorem is machine-checked on both halves. Its parameters are the
base $\{1,2,3,4,6,7\}$ with $3{,}414{,}729$ base states, of which $343{,}896$ survive the arc-orbit
and non-arc-orbit breaks and become live cubes; every one is UNSAT with an LRAT proof independently
verified by `lrat-trim`, at $228.3$ core-hours to solve and $7.7$ to check, $21.72$ hours wall on
eleven workers, with the cube split adding $0.39$ hours for the $22.11$-hour end-to-end figure
quoted in the abstract. The coverage half is a single unsatisfiable instance of $3{,}415{,}435$
clauses — $350$ constraint clauses, $356$ symmetry-breaking clauses and $3{,}414{,}729$ negated
cubes, one per base state, since coverage must see *every* base state whereas the orbit breaks
apply to the search half only, which is why it is ten times the live cube count. It solves in
$1{,}182.95$ seconds and emits a $2{,}097$ MiB LRAT proof, verified by `lrat-trim`, with peak
resident memory $5.6$ GB; reaching that required streaming the clauses to disk rather than building
the instance in memory, two earlier in-memory attempts having been killed at $8.99$ GB.

### B.2 What the certificates do and do not establish

The trust chain has four links:

| link | status |
|-------------------------------------------------------|-------------------------------------------------------|
| every live cube is unsatisfiable | machine: CaDiCaL, rechecked by `lrat-trim` |
| the cubes cover every lex-canonical base assignment | machine: DRAT, verified by `drat-trim` [19] |
| (L1) orbit anchoring loses no generality | human (Lemma 2.1) |
| (L2) lex-ordering the voters loses no generality | human (Lemma 2.3) |

The two human links are proved in Section 2. Lemma 2.1 is what licenses solving only the *live*
cubes, in its arc/non-arc form: $\mathrm{Aut}(P_q)$ is transitive on arcs and on non-arcs, so a
voter's top pair may be assumed to be a fixed arc or a fixed non-arc. Lemma 2.3 licenses the lex
chain in the coverage computation. They are human links not because they are doubtful but because
nothing in the pipeline checks them; the depth-first engine inherits the same two, shares no
implementation with this one, and where the two agree the agreement is evidence about the
implementations rather than about the lemmas.

One episode is worth recording, because for a period this certificate asserted more than it had
established. The script that writes the verdict emitted "coverage of the cube set: certified
separately" *unconditionally*, without running the coverage check, which is a different program.
The claim was true of Paley(19), where coverage had been run, and false of Paley(23) at the time it
was printed. It now reports coverage status rather than asserting it. A certificate that describes
its own scope incorrectly is the failure mode this section exists to guard against, and no check
caught it: it was caught by re-reading the verdict against the log of what had actually run.

The combined Paley(23) certificate, binding split and search into one value, is
`ff60539e16abf2ec...`, with the search root at `7e6c9c26ac386e67...` and the coverage instance at
`4876f077e85b7b56...`; Section 5.3 says which a third party must reproduce. Total cost on one
laptop was $22.11$ hours: an instance a general-purpose solver did not finish in six weeks [1] is
settled, with an independently rechecked proof of every subproblem, in under a day on commodity
hardware.

## Appendix C. The order-12 case analysis

Every tournament on $12$ vertices is $5$-inducible, so $N(5) \ge 13$. This appendix describes that
computation. It is the one result in this paper that was not run on the laptop of Section 3: it ran
on a shared cluster, and its cost is reported in cluster core-hours, which Appendix A.5 records as
$2.6$ to $3.3$ times more per unit of work than this laptop's.

### C.1 Reduction to one-vertex extensions

A direct census is out of reach: $D_{12} \approx 1.5 \times 10^{11}$ classes, $170$ times the
order-$11$ census of [2]. We use that census as the outer loop instead.

Write $L + S$ for the tournament obtained from an order-$11$ tournament $L$ by adding a vertex $v$
whose out-neighbourhood is $S \subseteq V(L)$. Two observations organise the analysis.

**(C1)** Every order-$12$ tournament is $L + S$ for some order-$11$ $L$ and some $S$ — indeed for
each of its twelve one-vertex deletions.

**(C2)** Restricting a profile that realises $L + S$ to $V(L)$ gives a profile that realises $L$.

By (C1), enumerating all $D_{11}$ order-$11$ classes and settling all $2^{11} = 2{,}048$
extensions of each settles every order-$12$ tournament; all of the former are $5$-inducible by the
census of [2], which is what makes the outer loop available. The twelvefold redundancy is harmless:
this is a case analysis, not a minimum cover, and each class need only be settled once. By (C2), a
profile realising $L + S$ may be sought by *inserting* $v$ into a profile realising $L$ with no
loss of generality, since every profile for $L+S$ arises that way. That is what phase 1 exploits.

### C.2 Three phases

The phases differ in what they can conclude, and are ordered by cost.

**Phase 1, the covering search.** Rather than $2{,}048$ separate instances per order-$11$ tournament, one search
enumerates profiles realising $L$ and, for each, records every out-neighbourhood obtainable by inserting $v$
into its five orders: $v$'s position in each order is a threshold, and the support of $v \to u$ is
the number of orders that place $v$ above $u$, so one traversal certifies many extensions at once. This
is the engine of Appendix A.3 with $v$'s placement read off rather than fixed in advance. The phase
is one-sided and limited by a work allowance — an extension it covers is thereby certified
$5$-inducible, one left over is not thereby refuted — and it settles every extension of
*[PLACEHOLDER — final share settled at phase 1; $99.32\%$ at $41.6\%$ of the census]*
of the order-$11$ tournaments.

**Phase 2, deciding what is left.** Each extension phase 1 leaves is materialised as an order-$12$
tournament $L + S$ in its own right and decided by the same engine at unit margin, where a witness
settles it positively. *[PLACEHOLDER — final count reaching phase 2; $2{,}257{,}151$ so
far]* extensions reached this phase, and every one of them is $5$-inducible with unit margin.

**Phase 3, plain majority.** Only a *majority* refutation would be a counterexample, so any
instance negative at unit margin is re-run without the margin restriction. **Phase 3 was never
invoked**: nothing was negative at unit margin, so the weaker question never had to be asked.

The division of labour between the phases is not a tuning choice. An earlier design gave a
stubborn $L$ more covering time instead of deciding the remainder directly, and on the structured
tournaments that sit at the top of the generator's enumeration tree it terminated at no limit we
tried: those leave hundreds of extensions uncovered, and no amount of further traversal covers an extension
that no insertion into any profile for $L$ can reach. Deciding it as an instance of its
own is what makes the analysis finite.

### C.3 One tournament of each converse pair

If $\pi_1, \dots, \pi_5$ realise $T$, their reversals realise the converse $\bar{T}$, arc for arc
and with the same margins, so $T$ is $5$-inducible if and only if $\bar{T}$ is. Moreover
$\overline{L + S} = \bar{L} + (V(L) \setminus S)$, so settling all $2{,}048$ extensions of $L$ settles
all $2{,}048$ of $\bar{L}$ as well. We therefore keep one tournament of each converse pair, by the
rule that $L$ is kept if and only if $\mathrm{canon}(L) \le \mathrm{canon}(\bar{L})$. This keeps
exactly one of each pair together with every self-converse tournament, $(D_{11} + S_{11})/2$ in all,
where $S_{11}$ is the number of self-converse order-$11$ classes; the saving is a factor just under
two.

Both halves of that argument are tested against enumeration at orders $5$ to $8$, where the truth
is small enough to compute directly: the rule keeps $10$, $34$, $272$ and $3{,}528$ of the $12$,
$56$, $456$ and $6{,}880$ classes, matching $(D_n + S_n)/2$ for $S_n = 8$, $12$, $88$, $176$; and
the identity $\overline{L + S} = \bar{L} + (V(L) \setminus S)$ is checked on all $384$, $3{,}584$
and $58{,}368$ pairs $(L, S)$ at orders $5$, $6$ and $7$.

### C.4 The completeness gate

A count of zero counterexamples is equally consistent with a complete sweep and with a sweep that
examined nothing, so it is not the quantity to check. The gate is the census: the number of
order-$11$ classes generated, summed over the parts, must equal $D_{11}$ exactly. Each part records itself complete only on success, so one that is interrupted or that runs
out of its allowance simply remains outstanding and is redone, and the set of recorded parts is the
certificate; the aggregate reports no verdict until the census total is met. It also checks the
number of tournaments kept against $(D_{11} + S_{11})/2$ — a quantity no part can verify alone, since
the two members of a converse pair generally fall in different parts.

We are explicit about this because an earlier run of this pipeline reported every part complete,
no counterexamples and no failures, while examining zero tournaments: the generator was not
present on the compute nodes, its error output was discarded, and a part that produced nothing
was recorded as a part that had found nothing. No line of that report was false. It was simply
consistent with both outcomes, which is the same failure of scope as the certificate episode of
Appendix B.2, one layer up.

Total cost: *[PLACEHOLDER — final figure; $4{,}015$ cluster core-hours at $41.6\%$ of the
census]*. The search code, the per-part records and the roll-up are at
`cluster/jz_n12cover` in the repository of Section 5.

---

## Appendix D. Exact enumeration counts

The counts the main text gives to two significant figures, in full. $D_n$, $R_n$ and $S_n$ are the
numbers of isomorphism classes of all, of regular, and of self-converse tournaments on $n$
vertices. The values at $n \le 8$ are the ones the arguments of Appendix C.3 are tested against,
and $D_{11}$ is the completeness gate of Appendix C.4.

| $n$ | $D_n$ | $R_n$ | $S_n$ |
|---:|---:|---:|---:|
| $5$ | $12$ | $1$ | $8$ |
| $6$ | $56$ | — | $12$ |
| $7$ | $456$ | $3$ | $88$ |
| $8$ | $6{,}880$ | — | $176$ |
| $9$ | $191{,}536$ | $15$ | $2{,}752$ |
| $10$ | $9{,}733{,}056$ | — | $8{,}784$ |
| $11$ | $903{,}753{,}248$ | $1{,}223$ | not published |
| $12$ | $154{,}108{,}311{,}168$ | — | — |
| $13$ | — | $1{,}495{,}297$ | $95{,}458{,}560$ |
| $15$ | — | $18{,}400{,}989{,}629$ | — |

A dash marks a value this paper does not use; [2] follows the same convention and collects its
own censuses in its Appendix H, with which this table agrees where the two overlap. Note that
[2] reads $R_n$ as *semi*-regular in even order, and that we need it in odd order only. The
$R_n$ column is OEIS A096368 [21], whose $n = 13$ term our own exhaustive run reproduces, which
is what anchors the indexing. $S_{11}$ is
not published and we do not need it: the converse-halving check of Appendix C.4 compares the
number of tournaments kept against $(D_{11} + S_{11})/2$, and since $S_n / D_n$ is falling
through $176/6{,}880$, $2{,}752/191{,}536$ and $8{,}784/9{,}733{,}056$, the resulting factor is
pinned between $1.99$ and $2$ — which is a tight enough bracket to catch the failure the check
exists for, namely a keep rule that halves nothing or halves twice.

For the record, the explicit tournament of [1] mentioned in Section 1 has $603{,}979{,}799$
vertices.

---

*No figures. The one worth drawing is a worked example of the search on Paley(7) at $k = 3$,
small enough to print in full, and it would earn its space only if a referee finds Appendix A.3
hard to follow. The other planned appendices — base-class tables, verdict files verbatim, the
Paley(19) witness with its support histogram — are in the repository of Section 5 instead.*

<!-- ===========================================================================
KEPT, NOT PRINTED.  Bonus material parked on Leonid's instruction 2026-09-07:
unlikely to be resurrected, but retained in the source rather than deleted.
HTML comments are dropped by the LaTeX writer, so none of this reaches the PDF.
To bring any of it back, delete this opening marker and the closing one.
============================================================================

FIGURE 1, never drawn. A fully worked example of Algorithm 1 on the smallest
instance that exercises every part of it: $T = \mathrm{Paley}(7)$ with $k = 3$, which is
$3$-inducible, so the figure ends in a witness rather than a refutation.

What it should show, in three panels.

**(a) The partial profile.** Three columns, one per voter, each a linear order of the placed set
$S$; the base $B$ shaded. Beside them the unplaced vertices with $|D(v \mid S)|$ against each, and
the MRV choice $v^{*}$ circled. This is the state DFS carries.

**(b) The domain of $v^{*}$.** The surviving slot tuples listed explicitly — at $n = 7$, $k = 3$
there are few enough to print in full, which is the whole reason for choosing this instance. Each
tuple annotated with the support $c_{v^{*}}(u)$ it induces on the arcs to $S$, showing which
tuples the margin regime admits.

**(c) The refinement.** A second vertex $u$ inserted at tuple $q$, and $D(v \mid S)$ mapped to
$D(v \mid S \cup \{u\})$ with the three cases of Appendix A.3.2 drawn as three kinds of arrow:
$p_i < q_i$ unchanged, $p_i > q_i$ shifted by one, $p_i = q_i$ **splitting into two**. Tuples
killed by the new arc struck through. The point the picture must make is that the child domain is
computed *from the parent's* — the cost is proportional to surviving tuples, not to the
$(|S|+2)^{k}$ slot space — which is the factor of $110$ of Appendix A.3.2.

Worth stating in the caption: the same figure read right to left is the argument that domains
shrink monotonically, and hence that an empty domain anywhere prunes the whole subtree.

Paley(7) at $k = 3$ is small enough that the entire search tree fits in a table if wanted —
an optional panel (d) — which would also let a reader check the MRV claim of Appendix A.3.1 by eye
against a static order.]*

*Note for whoever adds it: the companion paper hard-codes figure numbers in the prose as
"Figure N" rather than using `\ref`, so inserting a figure means renumbering every later
reference by hand. With no figures here yet, the first one added is trivially Figure 1 and the
problem does not arise — but it will the moment there are two.]*

=========================================================================== -->

