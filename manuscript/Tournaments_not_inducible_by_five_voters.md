---
output:
  pdf_document:
    keep_tex: true
  html_document: default
header-includes:
  - \usepackage{graphicx}
  - \graphicspath{{figures/}{./}}
---
# Tournaments not inducible by five voters

**Leonid Chindelevitch$^{1}$ and Ararat Harutyunyan$^{2}$**

$^{1}$ MRC Centre for Global Infectious Disease Analysis, School of Public Health, Imperial
College London, London, United Kingdom. Email: `lchindel@ic.ac.uk`. ORCID: 0000-0002-6619-6013.

$^{2}$ University of Paris-Dauphine, PSL University, CNRS UMR7243, LAMSADE, Paris, France.
Email: `ararat.harutyunyan@lamsade.dauphine.fr`.

## Abstract

A tournament $T$ is $k$-inducible if there are $k$ linear orders on its vertex set such that, for
every arc $i \to j$ of $T$, a majority of the orders rank $i$ above $j$. For odd $k$, let $N(k)$ be
the least order at which some tournament is not $k$-inducible. Only $N(3) = 8$ is known exactly; for
$N(5)$ the best bounds were $12 \le N(5) \le 38$, from our previous paper [2], which also gave the
first explicit example of moderate order, the Paley tournament $P_{43}$.

**Results.** A bespoke search algorithm improves both ends: $13 \le N(5) \le 23$. The upper bound
comes from proving that $P_{23}$ is not $5$-inducible, the case Bachmeier et al. [1] reported they
could not decide, their SAT solver not having terminated within a cumulative six weeks; ours takes
$22$ hours on one laptop. The lower bound comes from an analysis at order $12$. We also show that
$P_{31}$ is not $5$-inducible, while $P_{19}$ is $5$-inducible but not with unit margin, that is,
not by a profile in which every arc is carried by exactly three voters against two. Both $P_{19}$
and $P_{23}$ are arc-critical for their respective properties, whereas $P_{31}$ and $P_{43}$ are not
vertex-critical: deleting a vertex leaves a tournament that is still not $5$-inducible.

**Method.** The search places one vertex at a time, always choosing the vertex with the fewest
options left, and propagates the consequences. Together with the automorphisms of the tournament,
this decides on a single laptop instances that neither integer programming nor a general-purpose SAT
solver can settle. The refutations for $P_{19}$ and $P_{23}$ are certified as well: the search is
split into independent subproblems, a SAT solver emits a machine-checkable proof for each, and a
separate program rechecks every proof. All results, subject to two human-checked lemmas, are
reproducible from `https://github.com/Leonardini/TournamentsBeyond5Voters`.

---

## 1. Introduction

We follow the notation of our previous paper [2] throughout, which we briefly restate here.
Let $T$ be a *tournament* on the vertex set $V$, $|V| = n$: a digraph in which every unordered pair
$\{i,j\}$ carries exactly one of the arcs $i \to j$ or $j \to i$. A *$k$-profile* consists of $k$ 
linear orders $\pi_1, \dots, \pi_k$ on $V$. The *majority tournament* of such a profile puts an arc
from $i$ to $j$ whenever $|\{ v : i \prec_{\pi_v} j \}| > k/2$. For odd $k$ this is well-defined on
every pair, and the result is a tournament. We say $T$ is *$k$-inducible* if some $k$-profile has 
$T$ as its majority tournament, and we call such a profile a *witness* for $T$. The *converse* of $T$ 
is the tournament obtained from $T$ by reversing the direction of every arc.

We call the number of voters who rank $i$ above $j$ the *support* of the arc $e: i \to j$, and denote it 
$c(e)$. If $c(e) > k/2$, the *margin* of $e$ is $2c(e) - k$. In a witness every arc's support 
exceeds $k/2$, so for $k = 5$ it is $3$, $4$ or $5$. A witness has *margin at most $M$* if every arc has 
margin at most $M$. For $k = 5$ the possible margins are $1$, which we call *unit margin*, $3$ 
(every support in $\{3,4\}$), and $5$ (no restriction, i.e. plain majority). Note that a unit-margin witness 
is in particular a majority witness. In [2] we conjectured that the margin-based hierarchy is strict, which
for $k = 5$ asserts two separate things: that some tournament is $5$-inducible with margin at most $3$
but not with unit margin, and that some tournament is $5$-inducible but not with margin at most $3$.
We settle the first here since $P_{19}$ is such a tournament (Section 3.3), while the second remains open
(Section 4.2).

One further quantity recurs below. Informally, the *predictability* $\alpha^{*}(T)$ is the largest
fraction $\alpha > 1/2$ for which there is some profile, on any number $t$ of voters, such that every arc 
of $T$ is supported by at least $\alpha t$ of them; it is the value of a linear program over the linear 
orders of $V$. Since every arc of a $k$-voter witness is supported by more than $k/2$ of the voters, 
$k$-inducibility forces $\alpha^{*}(T) \ge (k+1)/2k$, which is $\tfrac{2}{3}$ at $k = 3$ and $\tfrac{3}{5}$ 
at $k = 5$. The implication is only one-directional: $\alpha^{*}$ can meet the threshold and the tournament
still fail to be inducible. Shepardson and Tovey [7] introduced the notion; see Section 1.4 in [2] for the 
computations and the counterexamples at both $k = 3$ and $k = 5$.

Counting arguments show that almost all tournaments fail to be $k$-inducible for any fixed $k$, yet the 
*explicit* examples they yield are astronomically large. This paper closes much of the gap for $k = 5$.
Let $N(k)$ be the least order of a tournament that is not $k$-inducible. The answer is only known exactly 
for $k = 3$. For $k = 5$ the state of the art before this work was $$12 \le N(5) \le 38,$$
both ends of which are due to our previous paper [2]: the lower bound came from an exhaustive
census of all $\approx 9.0 \times 10^{8}$ tournaments on $11$ vertices, all of which 
admit a unit-margin five-voter profile, improving on Bachmeier et al.'s $N(5) \ge 11$ [1].

The upper bounds in the literature are of two different kinds and they are not always comparable. 
Some are non-constructive, and obtained by counting: one compares the number of tournaments of a given order 
with the number that $k$ linear orders can produce, and when the first exceeds the second, some tournament of 
that order must be missed. Bachmeier et al. [1] argued this way to reach $41$, and [2] sharpened the 
comparison by restricting it to regular and near-regular tournaments, reaching $38$.
Other bounds are constructive, and exhibit an explicit tournament. The record for $k = 5$ was $P_{z}$
on $z = 603{,}979{,}799$ vertices [1], from a dominating-set theorem of Alon et al. [4] together with a
construction of Graham and Spencer [5], which we improved to $P_{43}$ [2], the first example of moderate order. 
Our bespoke algorithmic decision procedure shows that $P_{23}$ is not $5$-inducible, which improves both the 
best non-constructive (counting) as well as the best constructive (explicit) upper bounds to $N(5) \le 23$.

### 1.1 Special properties of Paley tournaments

The Paley tournament $P_q$, for a prime $q \equiv 3 \pmod 4$, has vertex set
$\mathbb{F}_q$ and an arc from $i$ to $j$ whenever $j - i$ is a nonzero square, or *quadratic
residue*; we write $\mathrm{QR}$ for the set of these, so that $i \to j$ exactly when $j - i \in
\mathrm{QR}$. As everywhere in
this paper, vertices are numbered from $1$, vertex $i + 1$ being the field element $i$. It is
*doubly regular*: every vertex has out-degree $(q-1)/2$ and every ordered pair of vertices has
exactly $(q-3)/4$ common out-neighbours. Its automorphism group, written $\mathrm{Aut}(P_q)$ and 
formally defined in Section 2, has order $q(q-1)/2$. This makes $P_q$ *arc-transitive*, meaning that 
for every pair of arcs $e, e'$ of $P_q$ there is an automorphism of $P_q$ that takes $e$ into $e'$. 
It is also *self-converse*, meaning that it is isomorphic to its own converse; the relevant mapping is 
simply multiplication by $-1$, which is easily checked to not be an automorphism when $q \equiv 3 \pmod 4$.

### 1.2 Why Paley(23) is hard to classify and Paley(43) was easy

Paley tournaments are natural candidates for non-inducibility because they are far from being
transitive, and because their symmetry makes an otherwise hopeless search merely very hard. 
Bachmeier et al. [1] call them *quadratic residue tournaments* and write $Q_q$; their orientation
is the converse of ours. Since reversing every voter's order reverses every arc of the majority tournament 
and changes no support, a tournament and its converse have the same *majority dimension*, the least $k$ 
for which a tournament is $k$-inducible, and are inducible at exactly the same margins. We use the name
Paley and the notation $P_q$ throughout.

The SAT study in [1] establishes
$$\dim(Q_3) = \dim(Q_7) = 3, \qquad \dim(Q_{11}) = \dim(Q_{19}) = 5,$$
where $\dim$ denotes majority dimension, and then stops exactly where the problem becomes hard:

> "Unfortunately, we were not able to check whether the majority dimension of $Q_{23}$ is equal to
> 5 or larger as the SAT solver did not terminate within a total of six weeks."

By contrast, our previous proof that $P_{43}$ is not $5$-inducible [2] never searched the profile
space in general. It rests on a quantity we call the *slack*,
$$\mathrm{slack}_5(T) = 5\,\mathrm{MAS}(T) - 3C, \qquad C = \binom{n}{2},$$
where $\mathrm{MAS}$ is the maximum number of arcs of $T$ that a single linear order can agree
with. Summing the majority condition over all arcs bounds how far the five voters can *collectively*
fall short of that maximum. A small slack restricts the voters to be close to the best orders, and at $q = 43$, 
where $\mathrm{slack}_5 = 6$, that restriction allowed us to fully enumerate about $1.8$ million cases.

While the same argument is valid at every $q$, the slack is *not* a monotone function of $q$ (table from [2]):

| $q$ | 7 | 11 | 19 | 23 | 31 | 43 |
|---|---|---|---|---|---|---|
| $\mathrm{slack}_5$ | 7 | 10 | 22 | **46** | 30 | **6** |

Since $P_{43}$ attains a locally minimal slack, while $P_{23}$ attains a local maximum, the method of [2] 
is unusable at $q = 23$. Note that for any $q$, 
$$\mathrm{slack}_5(P_q) \;=\; 5C\left(\alpha^{*}(P_q) - \tfrac{3}{5}\right),$$
where $\alpha^{*}$ is the predictability; equality holds because $P_q$ is arc-transitive [2]. 
In particular, the necessary condition $\alpha^{*} \ge 3/5$ is far from binding,
so no argument resting on the predictability can certify infeasibility.

**Predictability separates $k = 5$ from $k = 3$.** At $k = 3$ predictability decides exactly at
$N(3)$: the $96$ non-3-inducible tournaments on eight vertices have $\alpha^{*} = \tfrac{13}{20}$, which is
*below* $\tfrac{2}{3}$, so the relaxation detects them, while all other tournaments on eight vertices or 
fewer with at least one cycle have $\alpha^{*} = 2/3$ [7], and $N(3) = 8$ follows. 
At $k = 5$ it does not: the table above has $\alpha^{*} > \tfrac{3}{5}$ at every $q$, yet $P_{23}$, 
$P_{31}$ and $P_{43}$ are all non-inducible, with $P_{23}$ being the farthest *above* 
the threshold among the three. Though some tournament with order between 13 and 22 may have predictability 
below the $\tfrac{3}{5}$ threshold, we conjecture in Section 4 that this is not the case.

### 1.3 Contributions

1. **$P_{23}$ is not $5$-inducible** (Section 3.1). This settles the instance on
   which the SAT solver of [1] did not terminate within a cumulative six weeks, and improves the best
   upper bound on $N(5)$ from $38$ to $23$. We also decide $P_{31}$, which does not improve the
   bound but demonstrates the method's reach: the larger tournament is settled in less time
   than $P_{23}$.
   
2. **$P_{19}$ is $5$-inducible, but not $5$-inducible with unit margin** (Section 3.3). This is an example 
   suggesting that $k = 5$ may qualitatively differ from $k = 3$. For $k = 3$, the first $k$-inducible
   tournaments that are non-$k$-inducible with unit margin appear after $N(k)$, order 9 vs order 8 [2]. 
   If $P_{19}$ and $P_{23}$ are the minimal examples in their respective classes, which we provide evidence for
   in this paper, the reverse is true for $k = 5$.
   
3. **$P_{19}$ and $P_{23}$ are arc-critical** (Sections 3.2 and 3.5). Reversing an arc in $P_{19}$ restores 
    $5$-inducibility at unit margin, and reversing an arc in $P_{23}$ restores unrestricted $5$-inducibility.
   
4. **$P_{31}$ and $P_{43}$ are not vertex-critical** (Section 3.4). Deleting a vertex from $P_{31}$ or 
    $P_{43}$ leaves a tournament that is still not $5$-inducible.

5. **Two formally certified negative results** (Appendix B). $P_{19}$ is not $5$-inducible at unit
   margin and $P_{23}$ is not $5$-inducible. The search is split into independent subproblems
   (*cubes*); each is refuted by the SAT solver CaDiCaL, which emits its refutation as a machine-checkable 
   *LRAT* proof; and every one of those proofs is then rechecked by a separate program that shares no code 
   with the solver.
   
6. **Every tournament on $12$ vertices is $5$-inducible** (Appendix C). The analysis settles all $2{,}048$ 
   one-vertex extensions of each of the $\approx 9.0 \times 10^{8}$ tournaments on $11$ vertices, which is complete because 
   every $12$-vertex tournament is such an extension of each of its twelve one-vertex deletions.

### 1.4 Related work

Two papers stand immediately behind this one, in different ways. Our previous paper [2] is the
prior art for the *bound*: it produced the first explicit non-$5$-inducible tournament of modest
size, $P_{43}$, and its two bounds are what we measure against: $N(5) \le 38$ by counting and
$N(5) \le 43$ explicitly. Bachmeier et al. [1] is the prior art for the *problem and the method*: 
it brought SAT to bear on $k$-majority digraphs, characterised the $3$-majority case building on Dushnik 
and Miller [8], and established hardness results for voting with a constant number of voters.

The value of $N(3)$ is settled. Shepardson and Tovey [7] introduced the predictability
$\alpha^{*}(T)$ defined above. A $3$-voter profile is exactly a $\tfrac{2}{3}$-supermajority representation, 
so $\alpha^{*}(T) < \tfrac{2}{3}$ rules out $3$-inducibility; their $8$-vertex tournament has 
$\alpha^{*} = \tfrac{13}{20}$, which gives $N(3) \le 8$. They also prove that every tournament on at most 
$7$ vertices has $\alpha^{*} \in \{\tfrac{2}{3}, 1\}$, and Eggermont, Hurkens and Woeginger [6] then show by 
direct computation using an ILP formulation that every tournament on $7$ vertices is $3$-inducible, and 
every tournament on $8$ or $9$ vertices is $5$-inducible, yielding $N(3) = 8$ and $N(5) \ge 10$.

Our certified computation (Appendix B.1) is standard. It splits the problem into
independent subproblems, using the *cube-and-conquer* paradigm [9]: a SAT instance is split by
fixing a few variables at a time, giving many partial assignments called *cubes*, and each cube is
handed to the solver as a problem of its own. We adopt the standard of evidence set by
the Boolean Pythagorean triples proof [3, 11], in which every subproblem emits a machine-checkable
refutation that an independent checker validates. Our refutations are in the LRAT format [10]
(Appendix B.1), a format in which the solver records each clause it derives so that an independent
checker can replay and confirm the entire derivation.

---

## 2. Preliminaries

Throughout, $T$ is a tournament on $V = \{1, \dots, n\}$ and $k = 5$ unless stated otherwise. We
write $N^{+}(v)$ and $N^{-}(v)$ for the out- and in-neighbourhoods of $v$. A tournament is *regular* 
if $|N^{+}(v)| = |N^{-}(v)|$ for each $v \in V$; this can only happen for $n$ odd. Following [2], $D_n$, 
$R_n$ and $S_n$ denote the numbers of isomorphism classes of, respectively, all tournaments, regular 
tournaments and self-converse tournaments on $n$ vertices. The text gives them to two significant figures 
and Appendix D tabulates their exact values. For any $S \subseteq V$, the sub-tournament of $T$ induced by 
$S$ is the tournament obtained by restricting $T$ to the vertices in $S$ and the arcs between those vertices.

We call a tournament $T$ *vertex-critical* for $k$-inducibility at margin $M$ if $T$ is not $k$-inducible 
at margin $M$, but $T - v$ is $k$-inducible at margin $M$ for every vertex $v$. Similarly, we call $T$ 
*arc-critical* for such a property if $T$ has it, but any $T'$ obtained from $T$ by reversing an arc does not. 

### 2.1 Base states

Every search starts by fixing how the voters rank a handful of vertices and then looks for
ways to add the remaining ones. Choose a *base* $B \subseteq V$ of $b$ vertices (we use $b = 5$ or $b = 6$), 
and write $T|_B$ for the sub-tournament induced on $B$. When $B$ is a base, a *base state of $B$* (we omit 
$B$ when the context makes it clear) is a $k$-voter profile over $B$ that is consistent with $T|_B$, i.e. 
$k$ orderings of $B$ whose majorities reproduce $T|_B$ at the margin being asked for. Base states differing 
only by a relabelling of the voters are counted once (see Lemma 2.3 below).

Each base state of $B$ defines a self-contained subproblem: the rankings of $B$ are given, and the question 
is whether the remaining $n - |B|$ vertices can be inserted so that every arc of $T$ has the right support, 
so the search splits into independent components across base states. How many there are depends only on $|B|$, 
on $T|_B$ and on the margin regime, but *not* on $n$; thus, with the five-vertex bases we use on the Paley 
tournaments, which induce regular sub-tournaments, there are $8{,}031$ of them in both $P_{23}$ and $P_{47}$.

### 2.2 Symmetry reductions

An *automorphism* of a tournament $T$ is a permutation of its vertices carrying every arc to an arc;
these form a group $\mathrm{Aut}(T)$ under composition, and $T$ is *rigid* when $\mathrm{Aut}(T)$ is
trivial. For a permutation group $\Gamma$ on a set $X$, the *orbit* of $x$ is
$\Gamma x = \{\gamma(x) : \gamma \in \Gamma\}$, and the orbits partition $X$. This group is *transitive* 
on $X$ when this partition is trivial (equivalently, for any $x, x' \in X$ there is a $g \in \Gamma$ 
with $g(x) = x'$). We use orbits of
$\mathrm{Aut}(T)$ on the vertices, on the arcs, and on the *ordered pairs* of distinct vertices,
where $\gamma$ sends $(u,v)$ to $(\gamma(u), \gamma(v))$. An ordered pair is either an arc or the
reverse of one, so that third action has at least two orbits.

Two symmetries act on witnesses and both are exploited by every method here: the $k!$ relabellings
of the voters, and $\mathrm{Aut}(T)$ acting on the vertices. Each yields a reduction without loss
of generality. As a witness can be transformed by an automorphism, we may in some cases decide in 
advance what some voter's top two vertices are.

**Lemma 2.1 (orbit anchoring).** *Let $\mathrm{Aut}(T)$ act on the ordered pairs of distinct
vertices, and choose one representative pair from each orbit, say $(a_1, b_1), \dots, (a_m, b_m)$.
If $T$ is $k$-inducible, then $T$ has a witness in which, for at least one index $i$, some voter
ranks $a_i$ first and $b_i$ second.*

*Proof.* Let $\pi_1, \dots, \pi_k$ be a witness and let $(u, w)$ be the top two vertices of
$\pi_1$. The pair $(u,w)$ lies in one of the orbits; let $(a_i, b_i)$ be that orbit's
representative, so there is $g \in \mathrm{Aut}(T)$ with $g(u) = a_i$ and $g(w) = b_i$. Applying
$g$ to every voter gives a profile whose majority tournament is $g(T) = T$, so it is again a
witness, and its first voter ranks $a_i$ first and $b_i$ second. $\blacksquare$

Thus we may search only for witnesses whose top pair is one of the $m$ chosen pairs. Note that 
the lemma only guarantees that *some* $i$ works, not any particular one. 

For a Paley tournament $m = 2$, and the representatives can be exhibited without computing
$\mathrm{Aut}(P_q)$. For $a \in \mathrm{QR}$ and any $t$, the map $x \mapsto a(x-t)$ multiplies
every difference by $a$, which cannot change whether a difference lies in $\mathrm{QR}$, so it is
an automorphism; it sends the ordered pair $(t,s)$ to $(0, a(s-t))$, and as $a$ ranges over
$\mathrm{QR}$, $a(s-t)$ ranges over the coset $\mathrm{QR}\cdot(s-t)$. Since $\mathbb{F}_q^{*}$ is
the disjoint union of $\mathrm{QR}$ and its complement, each of them one such coset, these maps
alone leave only two orbits, separated by whether the difference lies in $\mathrm{QR}$. The orbits
of the full group are unions of these, so there are at most two, and since automorphisms carry arcs
to arcs, at least two. They are therefore exactly the arcs and the non-arcs, and any arc together
with any non-arc serves as representatives. On $P_7$, worked through in Figure 1 of Appendix A.2,
$\mathrm{QR} = \{1,2,4\}$, so the representatives are $(1,2)$, whose difference $1$ lies in
$\mathrm{QR}$, and $(1,4)$, whose difference $3$ does not; both lie inside the base
$B = \{1,2,4\}$ used there, which is what makes the anchoring decidable from the base state alone,
and panel (c) rejects an insertion that would lift a vertex above an anchored pair.

**Corollary 2.2 (vertex anchoring).** *Let $\mathrm{Aut}(T)$ act on the vertices and choose one
representative $v_1, \dots, v_r$ from each orbit. If $T$ is $k$-inducible, then $T$ has a witness
in which some voter ranks some $v_i$ first.*

*Proof.* The proof of Lemma 2.1 verbatim, with the action on vertices in place of the one on
ordered pairs. $\blacksquare$

We say that a witness meeting either restriction is *anchored*. The two are alternatives rather than
a sequence, each without loss of generality, and which is better depends on the tournament's number 
of vertex pair orbits vs vertex orbits, as well as the relative complexity of testing each restriction.

**Lemma 2.1 must be given the full set of orbits.** It licenses the restricted search
*provided* the representatives meet every orbit. For every tournament we
compute $\mathrm{Aut}(T)$ separately, with `nauty` 2.8.6 [16], and record its orbits alongside the
run. Every automorphism group, orbit set and canonical form reported in this paper comes from that
same tool.

**Lemma 2.3 (voter lex-ordering).** *If $T$ is $k$-inducible, then $T$ has a witness whose $k$
orders are non-decreasing under any fixed total order on linear orders.*

*Proof.* The support $c(e)$ counts voters and is therefore invariant under permuting them, so any
profile with the same multiset of orders induces the same tournament. Sorting the multiset gives
the required witness. $\blacksquare$

The two lemmas may be applied simultaneously, which is not automatic: each is proved by transforming
a witness, and the second transformation must not undo the first. Apply Lemma 2.1 to a witness, then
sort the resulting $k$ orders as in Lemma 2.3. Sorting only permutes the voters, while the property
Lemma 2.1 delivers — "*some* voter ranks $a_i$ first and $b_i$ second" — depends on the multiset of
orders and not on which voter carries it, so it survives the sort. Had Lemma 2.1 been phrased as
"voter $1$ ranks …", the composition would fail. Both lemmas are therefore available to every
formulation in Appendix A.

Together they reduce the running time substantially, in two different places. Lemma 2.3 is absorbed
into the definition of a base state: the $k$ orderings of $B$ are required to be non-decreasing,
dividing the count by almost $k! = 120$ — almost, because a tuple with two equal orders is fixed by
some permutations and so is not counted $k!$ times before sorting.

Lemma 2.1 acts earlier still, *invalidating* base states outright, but only when *all* the
representative pairs lie inside $B$. Suppose they do, and that a base state extends to an anchored
witness, some voter of which ranks $a_i$ first and $b_i$ second overall. As $a_i, b_i \in B$, that
voter ranks $a_i$ first and $b_i$ second *within* $B$, which the base state alone reveals.
Contrapositively, a base state no voter of which tops $B$ with a chosen pair extends to no anchored
witness, hence to no witness at all, and may be discarded. If one representative has an endpoint
outside $B$ this fails at the first step: a base state failing the test on the representatives it
sees may still extend to a witness anchored on the one it cannot. We call a base state *live* if it
survives. On the five-vertex base we use on the Paley tournaments $2{,}591$ of the $8{,}031$ are live.

The search and the certification differ in *when* the condition is tested. Both test it at the
start, which determines the live base states. Our algorithmic approach keeps testing it during the
search, since a base state fixes the orders only on $B$ whereas the condition constrains the full
orders: a voter topping $B$ with $(a_i, b_i)$ ceases to be anchored once a later vertex is inserted
above $b_i$. Pruning is sound once every representative has both endpoints placed, for then the test
is monotone — an insertion can destroy an anchor but never create one, the placed vertices' relative
order being already fixed — so a partial profile with no anchored voter has no extension with one.
While some representative still has an unplaced endpoint, no pruning is done. The SAT certification
instead tests the condition once, at the root, where it decides which cubes reach the solver.

### 2.3 The search in five steps

The search extends base states. A base state fixes how the $k$ voters rank $B$; the search inserts
the remaining $n - |B|$ vertices into those rankings one at a time, backtracking as soon as the
arcs already decided contradict $T$. A base state extended to $k$ full rankings yields a witness;
one that cannot be is eliminated; and $T$ fails to be $k$-inducible exactly when every base state
is eliminated. Algorithmically, with $T$ and the margin regime as inputs, our approach has 5 steps:

1. **Pick a size.** Choose $b = |B|$, in practice $5$ or $6$.
2. **Pick a subtournament.** Choose $B$ with $|B| = b$. Only $T|_B$ matters for what follows, so
   the choice can and should be optimised quickly (see Appendix A.2), since the base-state count
   varies by more than two orders of magnitude across the $12$ isomorphism classes at $b = 5$.
3. **Find its base states.** Enumerate the $k$-tuples of linear orders of $B$ whose supports agree
   with $T|_B$, counted up to voter permutation by Lemma 2.3.
4. **Determine the usable symmetries.** Compute $\mathrm{Aut}(T)$ with `nauty` and its orbits,
   then impose the ordered-pair anchoring of Lemma 2.1, the vertex anchoring of Corollary 2.2, or
   neither, discarding the base states no anchored witness can use.
5. **Run to completion, in parallel across base states.** The verdict is positive as soon as any
   base state yields a witness. It is negative only when *every* live base state has been searched
   to exhaustion.

Figure 1, in Appendix A.2, works all five steps through on $P_7$ at $k = 3$, where the
witness is unique up to symmetry. Steps 1–4 are fast and user-chosen; step 5 is the
parallel computation. The same five steps
describe the SAT route, with step 5 replaced by handing each live base state to a CDCL solver as a
*cube* (the partial assignment fixing the voters' rankings of $B$), so the two share their
decomposition and their two lemmas and differ only in what refutes a leaf in the search tree.

---

## 3. Results

The two regimes we explore are *unrestricted* (or plain majority) inducibility, and *unit margin*. 
The former is the standard notion of inducibility, and the latter asks that
every arc be carried by exactly three voters against two. Only an unrestricted refutation bounds $N(5)$. 
However, the lemma below shows that for the Paley family and most tournaments derived from it, the 
unrestricted inducibility is equivalent to inducibility with margin at most $3$ (i.e. support at most 4).

**Lemma (3-cycle bound).** *Let $u \to v \to w \to u$ be a directed triangle of $T$ and let
$\pi_1,\dots,\pi_k$ be any linear orders with $k$ odd. Then*
$$c(u\to v) + c(v \to w) + c(w \to u) \le 2k.$$
*Consequently, in any majority witness, no arc lying in a directed triangle has unanimous support $k$.*

*Proof.* A linear order cannot rank $u$ above $v$, $v$ above $w$ and $w$ above $u$ simultaneously,
so each voter agrees with at most two of the three arcs; summing over the $k$ voters gives the
inequality. If $c(u \to v) = k$, the other two supports sum to at most $k$, contradicting the
majority requirement that each be at least $(k+1)/2$. $\square$

For $k = 3$ the second conclusion is Proposition 1 of Milosz, Hamel and Pierrot [27], with the same
argument; we need it for every odd $k$, and in the summed form above.

### 3.1 Paley(23) and Paley(31) are not 5-inducible

**Theorem.** *$P_{23}$ is not $5$-inducible. Consequently $N(5) \le 23$.*

The proof is a search that runs to completion. The base is $\{1,2,3,6,12\}$, which induces the regular 
tournament on $5$ vertices and gives $8{,}031$ base states. They are reduced to $2{,}591$ by Lemma 2.1, 
by requiring one voter to rank either $(1,3)$ or $(1,6)$ as the first pair. None of them produces a witness. 
This statement is also formally certified in Appendix B.1.

The same method settles a larger case: $P_{31}$ is not $5$-inducible, over $21{,}009$ base states with 
a different base, reduced to $4{,}007$ by Lemma 2.1. Appendix A.3 shows how the runtime scales in $q$,
and Appendix A.4 tabulates the cost of every computation in this paper.
The value of settling $P_{31}$ is to show that the bespoke approach decides $31$-vertex instances on
a single laptop within a day, something that SAT and ILP solvers are unable to do.

### 3.2 Criticality across the Paley family

Arc-criticality implies vertex-criticality: reversing an arc incident to $v$ leaves $T - v$
unchanged, and the restriction of a witness to $V \setminus \{v\}$ is a witness for $T - v$. Each
cell below therefore records only the *strongest* property established, at each of the two margins. 
"Not vertex-critical" therefore also rules out arc-criticality.

| $q$ | unit margin | unrestricted |
|---|---|---|
| 19 | **arc-critical** | $5$-inducible, so criticality does not apply |
| 23 | not vertex-critical | **arc-critical** (Section 3.5) |
| 31 | not vertex-critical | **not vertex-critical** (Section 3.4) |
| 43 | not vertex-critical | **not vertex-critical** (Section 3.4) |

Note that $P_{19}$ is the only member critical at unit margin, and it is critical in the
strongest sense: reversing any one arc makes it unit-margin inducible, which by the implication also
gives vertex-criticality. At the other end, $P_{31}$ and $P_{43}$ fail to be vertex-critical at
*both* margins. The interesting cell is $q = 23$: it is *vertex-critical unrestricted*, 
but *not* vertex-critical at unit margin. In other words, $P_{23} -\,v$ is 5-inducible, but not with unit 
margin, analogous to the following result.

### 3.3 Paley(19) is 5-inducible, but not with unit margin

That $P_{19}$ is $5$-inducible is due to Bachmeier et al. [1], who computed
$\dim(Q_{19}) = 5$. Our search recovers it independently and contributes the negative half: it is *not* 
$5$-inducible with unit margin. This is a complete refutation over all $2{,}200$ base states of the base 
$\{1,2,3,4,6\}$, and it is the second statement we certify formally in
Appendix B.1. These two facts supply the separation in Section 1: no arc of $P_{19}$ can be unanimous, by the
$3$-cycle bound above, so it is $5$-inducible with margin at most $3$ and not with unit margin, so the inclusion of the unit-margin regime in margin at most $3$ is strict.

Both of our certified refutations, $P_{23}$ at unrestricted margin in Section 3.1 and $P_{19}$ at
unit margin, are established formally by cube-and-conquer
computations in which every leaf is refuted by CaDiCaL 2.0.0 [15, 20] in LRAT and rechecked by
`lrat-trim` [20], a separate program that shares no code with the solver, with the solver's own
proof checking deliberately disabled. Both are complete on *both* halves (the leaves and the claim that the 
leaves are exhaustive), and both reduce to the same two human-checked lemmas, 2.1 and 2.3 (see Appendix B).

### 3.4 Paley(31) and Paley(43) are not vertex-critical

Vertex-criticality is the natural minimality notion for an *obstruction*, a tournament that is
not $5$-inducible, and $P_{43}$, the first explicit
non-$5$-inducible tournament [2], is the natural candidate.

**Theorem.** *Neither $P_{31}$ nor $P_{43}$ is vertex-critical for 5-inducibility.*

**The orbit break.** For any $q \equiv 3 \mod 4$, $\mathrm{Aut}(P_{q} - v)$ is *exactly* the
stabiliser of $v$ in $\mathrm{Aut}(P_{q})$. One inclusion is immediate; for the other, deleting $v$
removes an out-arc from every vertex of $N^{-}(v)$ and from no vertex of $N^{+}(v)$, so $P_q - v$
has just two out-degrees, $(q-1)/2$ on $N^{+}(v)$ and $(q-1)/2 - 1$ on $N^{-}(v)$, and an
automorphism preserves out-degree, hence those two sets, hence extends to $P_q$ by fixing $v$.
Translating so that $v = 0$, that stabiliser is $\{x \mapsto ax : a \in \mathrm{QR}\}$, cyclic
of order $(q-1)/2$, and it splits the remaining $q - 1$ vertices into exactly two orbits of size
$(q-1)/2$, namely $\mathrm{QR}$ and its complement. Two representatives, one from each,
therefore meet every orbit, and the vertex anchoring of Corollary 2.2 applies with those two.

Each sweep runs over all $8{,}031$ base states of a five-vertex base inducing the regular tournament
on five vertices: $\{1,2,3,4,13\}$ in $P_{31} - v$ and $\{1,2,3,4,11\}$ in $P_{43} - v$. The two counts
coincide because, as in Section 2.1, the number of base states depends only on the induced
subtournament and on the margin, and not on $n$.

Every arc of $P_{q} - v$ lies in at least $(q-3)/4$ directed triangles, so no arc of a majority witness 
could be unanimous, and margin $\le 3$ is not a restriction at all. The refutation at margin $\le 3$ is therefore
an unrestricted refutation. We use the same approach for both $q = 31$ and $q = 43$.  
We thus independently reconfirm the main result of [2], that $P_{43}$ is not $5$-inducible: if it were,
so would be $P_{43} - v$, by deleting $v$ from every voter's order.

### 3.5 Vertex and arc criticality for Paley(23)

**Theorem.** *$P_{23}$ is arc-critical: reversing any single arc yields a $5$-inducible
tournament. Consequently it is vertex-critical.*

Let $T^{e}$ denote $P_{23}$ with the arc $(1,2)$ reversed; since $\mathrm{Aut}(P_{23})$ is transitive on 
arcs, any two single-arc reversals of $P_{23}$ are isomorphic, so we may pick $(1,2)$ without loss of 
generality. The computation is a scan of the $8{,}031$ base states of $T^{e}$, but now $T^{e}$ is rigid, 
so Lemma 2.1 and Corollary 2.2 do not apply. The witness we found was verified independently of the search 
that produced it, by two checks on the five orders: each is a permutation of the $23$ vertices, and the 
majority tournament they induce agrees with $T^{e}$ in every one of the $253$ arcs and therefore 
differs from $P_{23}$ in exactly $e$.

**Vertex- and arc-criticality come apart, as far as they can.** Arc-criticality implies
vertex-criticality, so it is natural to ask whether the two coincide. They do not. Among the $110$
vertex-transitive tournaments on $21$ vertices, four are unit-margin obstructions, and all four are
vertex-critical. However, arc-criticality takes all three of its possible values among those same four: 
two of them have every arc critical, one has exactly half, and one has none at all, so no statement of 
the form "this tournament is or is not arc-critical" captures the situation (full details in Appendix F).

### 3.6 Other structured tournament families

Beyond the Paley family we swept the structured families catalogued by McKay [26] exhaustively for
$n < 23$. Every verdict is negative for the bound, so we only report them briefly.

First, *the vertex-transitive family contains no majority obstruction at all for $n < 23$*: all
$110$ are $5$-inducible, $106$ of them already at unit margin and the remaining four by exhibited
majority witnesses. Since only a majority refutation can move $N(5)$, that family is closed as a
source of candidates below $23$, and the closure survives one-arc perturbation, since reversing
any single arc of the four unit-margin obstructions, one representative per arc orbit, again
leaves a majority-inducible tournament in all $40$ cases. 

Second, *both* doubly regular tournaments on $19$ vertices, $P_{19}$ and the one other of that order, are 
unit-margin obstructions and both are majority-inducible, so the separation that makes $P_{19}$ interesting
is not a property of $P_{19}$ in particular. Nor is its criticality: the second one is
*arc-critical* at unit margin too. Its automorphism group has order $3$, so its $171$ arcs fall
into $57$ orbits of size $3$, and reversing the representative of any one of them yields a
tournament with a unit-margin witness: $57$ orbits and $57$ witnesses. Arc-criticality at unit margin is 
therefore shared by both doubly regular tournaments of order $19$. 

Third, every regular tournament on at most $15$ vertices is inducible at unit margin, over all 
$R_{15} \approx 1.8 \times 10^{10}$ of those on $15$ vertices, and with the 
instance counts summing to OEIS A096368(7) [17]. Likewise, every self-converse tournament on $13$ vertices is 
inducible at unit margin, over all $S_{13} \approx 9.5 \times 10^{7}$ of them. With the order-$11$ census of 
[2] and the order-$12$ analysis of Appendix C, that settles every self-converse tournament on at most $13$ 
vertices.

Taken together with the Paley results above, these sweeps turn up ten tournaments that are not
$5$-inducible with unit margin: 2 doubly regular ones at order 19, 4 vertex-transitive ones at order 21, and 
4 circulant ones at order 23.

**One family needs no search.** A tournament is *locally transitive* if every in- and
out-neighbourhood induces a transitive subtournament. Every such tournament is $k$-inducible at
unit margin for every odd $k \geq 3$, by an explicit construction rather than a computation; Appendix E
provides it. This is the one structural family for which the inducibility question is settled outright.

---

## 4. Discussion and open problems

### 4.1 Other applications of incremental depth-first search with MRV

Subject to the caveats of Appendix A.4, the shape of the engine may transfer: a placement search in
which each decision *refines*, rather than recomputes, the candidate sets of all remaining
objects, with a dynamic minimum-remaining-values (MRV) order and an externally discharged symmetry break. The conditions
are specific: the extensions of a partial solution must factor as a product that shrinks
monotonically under each decision, and the symmetry group must be computable; a general-purpose solver 
may win if they do not apply.

Neither device is new in isolation, and the closest antecedent is Knuth's Algorithm X with dancing
links [18]. Its column-choice rule (take the column with the fewest remaining ones) is our MRV
order, and its link surgery does what our refinement does: the state is altered in place and put
back on backtrack, so a node costs what changed rather than what the whole state contains. The
constraint is what differs. Exact cover partitions, whereas an arc of a tournament imposes a
threshold, at least three of five voters, so the search here is not an exact cover instance and
dancing links does not apply to it as it stands.

Two design lessons do seem to generalise. First, the incremental refinement, not the heuristic order, 
carried most of the speedup here, a factor of $110$ against a factor of a few. Second, a symmetry break 
should be *parameterised* by its representatives rather than hard-coded, so that its correctness
obligation becomes a separate computation instead of an assumption buried in the
search; Section 3.4 is a case where discharging that obligation required an explicit orbit calculation
that the engine could not have performed for itself.

### 4.2 Conjectures and open problems

**Conjecture 1:** The true value of $N(5)$ is 23, so every tournament of order less than 23 is 5-inducible.

Both ends of $13 \le N(5) \le 23$ are constructive and improved from [2]; the margin-$1$ obstructions
at $n = 19$ and $21$ cannot move the upper one, since every one of them is majority-inducible.

**Conjecture 2:** $P_{q}$ is not $5$-inducible for any eligible prime $q \geq 23$, i.e. $q \equiv 3 \pmod 4$.

It holds at $q = 23$, $31$ and $43$, and only finitely many $q$ are in doubt:
$\alpha^{*}(P_q) = \mathrm{MAS}(P_q)/C$ tends to $\tfrac{1}{2}$, so the predictability eventually falls
below $\tfrac{3}{5}$, past which the necessary condition of Section 1.2 refutes $5$-inducibility with
no search at all. What is missing is a bound on where that range ends; the values in Section 1.2 fall
too irregularly to extrapolate one.

**Open problem 1: Vertex- and arc-criticality.** Whether $P_{q}$ minus *two* vertices is $5$-inducible,
equivalently whether $P_{q}$ minus one vertex is vertex-critical, is open at $q = 31$ and $q = 43$.

**Open problem 2: The margin hierarchy.** The first of unit margin $\subseteq$ margin $\le 3$ $\subseteq$
unrestricted is strict (Sections 3.3 and 3.6); whether the second ever is, that is, whether some
tournament is inducible by five voters but not at margin $\le 3$, is open. The 3-cycle lemma forces
such a tournament to have an arc in *no* directed triangle, which rules out every regular tournament.
The conjecture of [2] is that the inclusion is strict at every odd $k > 3$.

---

## 5. Reproducibility

### 5.1 The repository

The code, data and verdict files are at
`https://github.com/Leonardini/TournamentsBeyond5Voters`. Its `CLAIMS.md` carries one row per
statement made here, naming the artifact that holds the verdict and the command that re-derives
it, and it ends with an explicit list of what the package does not establish. A permanent archive
of the commit corresponding to the accepted version will be deposited on acceptance and its DOI
recorded here.

The repository contains the search engine as a single C translation unit, the SAT encoding and
cube tooling in Python, the certification driver, the independent witness verifiers, the
tournaments as bit strings, and a verdict record for every result reported here. Each verdict
records the exact command line, the base and break used, the coverage audit, the runtime, and the two 
root hashes for the formally certified results.

### 5.2 What must and what may not replicate

The certified computations publish two root hashes, and only one of them is portable.

**ROOT (CNF)** commits to the SHA-256 of every cube's CNF, in cube order. These files are
generated by the repository's own code from the tournament and the base, and are reproducible on
any machine: a third party who regenerates the cube set *must* obtain this exact value. It is the
meaningful cross-check, because it proves they solved the same problems.

**ROOT (proofs)** additionally commits to the LRAT proof bytes. These are *not* portable, as they 
depend on the exact SAT solver and version used. A mismatch here is not evidence of an error.

We have run that check: on the cluster, under a different compiler and CaDiCaL build, both
refutations gave matching roots at $70.9$ and $567.6$ cluster core-hours against the $25.1$ and
$236.0$ of Appendix A.4, and both coverage instances rebuilt to their committed CNF hashes and were
refuted again.

**Search runtimes: nodes replicate, hours do not.** A three-way version of that distinction applies to the
uncertified sweeps. *Verdicts* replicate under any correct implementation, which is the claim the
paper makes. *Node counts* replicate exactly, but only with five choices held fixed:

1. the same tie-breaking rule in the variable order and in the domain
   refinement; ties are common and a different rule explores a different tree of the same size
   class but not the same size;
2. the same vertex numbering of the tournament;
3. the same base size and base;
4. the same resulting set of base states, which follows from (2) and (3);
5. the same margin regime.

The engine prints all of these except (2) in a header on every run (margin, variable order,
tie-break mode, symmetry break, base size, base, base arc pattern and base-state count), so a run
log is a self-describing fingerprint. Condition (2) is the tournament file itself, which is why
the repository stores tournaments rather than regenerating them from their constructions. 
*Core-hours* replicate only in order of magnitude; Appendix A.3 measures a factor of $2$ to $5$ per core
between the two machines we used.

---

## Motivation and statement of AI use

This paper grew out of our previous paper [2], whose constructive bound $N(5) \le 43$ came from a
structural argument, and whose counting bound $N(5) \le 38$ names no explicit tournament. The question of 
what a genuine decision procedure would reach, at the orders the screen cannot speak about, 
led to the engine of Appendix A.

During the preparation of this work, the authors used Claude for exploratory reasoning,
implementation assistance, drafting and editing. The authors reviewed and edited the output 
and take full responsibility for the contents of the published article.

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

[6] C. Eggermont, C. Hurkens, G. J. Woeginger. Realizing small tournaments through few
permutations. *Acta Cybernetica*, 21(2):267–271, 2013.

[7] D. Shepardson, C. A. Tovey. Smallest tournaments not realizable by
$\tfrac{2}{3}$-majority voting. *Social Choice and Welfare*, 33(3):495–503, 2009.
doi:10.1007/s00355-009-0375-7.

[8] B. Dushnik, E. W. Miller. Partially ordered sets. *American Journal of Mathematics*,
63(3):600–610, 1941.

[9] M. J. H. Heule, O. Kullmann, S. Wieringa, A. Biere. Cube and conquer: guiding CDCL SAT
solvers by lookaheads. In *Haifa Verification Conference (HVC 2011)*, LNCS 7261, pages 50–65,
2012.

[10] L. Cruz-Filipe, M. J. H. Heule, W. A. Hunt Jr., M. Kaufmann, P. Schneider-Kamp. Efficient
certified RAT verification. In *Automated Deduction (CADE 2017)*, LNCS 10395, pages 220–236, 2017.
This is the paper introducing the LRAT format that `lrat-trim` consumes.

[11] L. Cruz-Filipe, J. Marques-Silva, P. Schneider-Kamp. Formally verifying the solution to the
Boolean Pythagorean triples problem. *Journal of Automated Reasoning*, 63(3):695–722, 2019.
doi:10.1007/s10817-018-9490-4.

[12] M. J. H. Heule. Everything's bigger in Texas: the largest math proof ever. ACL2 Seminar,
University of Texas at Austin, 9 September 2016. Joint work with O. Kullmann and V. W. Marek.
`https://www.cs.utexas.edu/~moore/acl2/seminar/2016.09.09-heule/ACL2.pdf`
Cited for the compressed size of the published cube certificate; the
re-verification runtimes quoted in Appendix B.1 are stated in [3] itself.

[13] M. J. H. Heule. Schur number five. In *AAAI 2018*, pages 6598–6606, 2018.

[14] J. Brakensiek, M. Heule, J. Mackey, D. Narváez. The resolution of Keller's conjecture.
In *Automated Reasoning (IJCAR 2020)*, LNCS 12166, pages 48–65, 2020.

[15] A. Biere, K. Fazekas, M. Fleury, M. Heisinger. CaDiCaL, Kissat, Paracooba, Plingeling and
Treengeling entering the SAT Competition 2020. In *Proceedings of SAT Competition 2020: Solver and Benchmark
Descriptions*, volume B-2020-1 of *Department of Computer Science Series of Publications B*,
pages 50–53. University of Helsinki, 2020. The solver description; for the LRAT support we use,
and for `lrat-trim`, see [20].

[16] B. D. McKay, A. Piperno. Practical graph isomorphism, II. *Journal of Symbolic Computation*,
60:94–112, 2014. The `nauty` and `gentourng` tools, used for all tournament enumeration.

[17] OEIS Foundation Inc. Entry A096368, *Number of unlabeled regular tournaments with $2n+1$ nodes*.
The On-Line Encyclopedia of Integer Sequences, `https://oeis.org/A096368`.

[18] D. E. Knuth. Dancing links. In J. Davies, B. Roscoe, J. Woodcock, editors, *Millennial
Perspectives in Computer Science*, pages 187–214. Palgrave, 2000. arXiv:cs/0011047.

[19] N. Wetzler, M. J. H. Heule, W. A. Hunt Jr. DRAT-trim: efficient checking and trimming using
expressive clausal proofs. In *Theory and Applications of Satisfiability Testing (SAT 2014)*,
LNCS 8561, pages 422–429, 2014. doi:10.1007/978-3-319-09284-3_31.

[20] F. Pollitt, M. Fleury, A. Biere. Faster LRAT checking than solving with CaDiCaL. In
*Theory and Applications of Satisfiability Testing (SAT 2023)*, LIPIcs 271, pages 21:1–21:12,
2023. doi:10.4230/LIPIcs.SAT.2023.21. Introduces `lrat-trim` and CaDiCaL's native LRAT output,
which is the capability we use; it postdates the solver description [15].

[21] OEIS Foundation Inc. Entry A000568, *Number of outcomes of unlabeled $n$-team round-robin
tournaments*. The On-Line Encyclopedia of Integer Sequences, `https://oeis.org/A000568`.

[22] OEIS Foundation Inc. Entry A002785, *Number of self-complementary oriented graphs with $n$
nodes*. The On-Line Encyclopedia of Integer Sequences, `https://oeis.org/A002785`. McKay's note
on that entry records that these are also the self-converse tournaments.

[23] A. E. Brouwer. The enumeration of locally transitive tournaments. Report ZW 138/80,
Mathematisch Centrum, Afdeling Zuivere Wiskunde, Amsterdam, 1980.

[24] B. Alspach, C. Tabib. A note on the number of 4-circuits in a tournament. *Annals of
Discrete Mathematics*, 12:13–19, 1982.

[25] B. Debord. Caractérisation des matrices des préférences nettes et méthodes d'agrégation
associées. *Mathématiques et sciences humaines*, 97:5–17, 1987.

[26] B. D. McKay. Combinatorial data: digraphs.
`https://users.cecs.anu.edu.au/~bdm/data/digraphs.html`. Source of the circulant,
vertex-transitive and doubly regular tournament catalogues swept in Section 3.6.

[27] R. Milosz, S. Hamel, A. Pierrot. Median of 3 permutations, 3-cycles and 3-hitting set
problem. In *Combinatorial Algorithms (IWOCA 2018)*, LNCS 10979, pages 224–236, 2018.
doi:10.1007/978-3-319-94667-2_19.



---

## Appendix A. The search engine

Both integer programming and satisfiability are central to this project rather than foils for it.
Every computational claim in the previous paper [2] is certified by an integer or linear program,
and the integer program of A.1 below is that paper's formulation B.1, verbatim; the only machine-checked theorem in this paper
is a SAT computation from end to end, with CaDiCaL [15] emitting LRAT proofs that `lrat-trim`
checks. The claim here is narrow: on this one decision problem, at this one range of sizes, neither
tool reaches the answer while a search built around the problem's own structure does, and the same
SAT machinery is then indispensable for turning that answer into a proof.

### A.1 Integer programming and SAT are both too slow

The natural integer program has one binary $x_{v,ij}$ per voter $v$ and pair $i < j$, meaning that
$v$ ranks $i$ above $j$, with $x_{v,ji}$ read as $1 - x_{v,ij}$ so that antisymmetry is structural.
Each voter is forced to be a linear order by forbidding both orientations of every $3$-cycle,
$$0 \;\le\; x_{v,ij} + x_{v,jl} - x_{v,il} \;\le\; 1 \qquad (i < j < l),$$
and the profile is forced to induce $T$ by one majority row per arc,
$\sum_{v} x_{v,ij} \ge (k+1)/2$. This is a pure feasibility problem. At
$q = 23$, $k = 5$ it has $1{,}265$ binaries, $17{,}710$ transitivity rows and $253$ majority rows.

The obstruction is structural rather than a deficiency of the solver. Put $x_{v,ij} = 3/5$ on every
arc of $T$ and $2/5$ on every non-arc, the same for all voters. Every cyclic triple then reads
$3/5 + 3/5 - 2/5 = 4/5$ and every transitive one $3/5$, both interior to $[0,1]$, while every
majority row is tight at exactly $3$. The relaxation is therefore feasible, and since the problem
carries no objective, LP feasibility yields no bound whatever: branch-and-bound is left with
nothing to prune by except infeasibility discovered deep in the tree. That fractional point is also
invariant under both symmetry groups acting on the problem (the $k!$ voter relabellings and
$\mathrm{Aut}(T)$), so it supplies no branching direction either, and orbital branching recovers
only the $k!$ factor. CPLEX and Gurobi both failed to close instances at $n = 19$ within a day.

The satisfiability encoding is *dissent-Boolean*: one variable per voter $v$ and arc $i \to j$ of
$T$, true when $v$ ranks $j$ above $i$ and so dissents from that arc. Each arc bounds its dissents,
at most $(k-1)/2$ of them for majority and exactly $(k-1)/2$ for unit margin, and each voter's
dissent set is forced to leave a linear order triple by triple: a tournament is transitive exactly
when it has no directed $3$-cycle, so it is enough to forbid, for every voter and every triple, the
two dissent patterns that would make that triple cyclic. For $k = 5$ that is $5\binom{n}{2}$
variables, $15$ clauses per arc at unit margin and $10$ per triple. It is compact and propagates
well locally, and it is what both certified refutations of Appendix B are built on.

Table 4 of [1] reports their `Sat-Check-k-Majority` on uniform random tournaments, tabulating only
entries whose average stays under 20 seconds. The $k = 5$ column reads

| $n$ | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|---|
| seconds | $0.23$ | $0.35$ | $0.54$ | $5.87$ | $11.07$ | $18.95$ | — |

so on *random* instances the method leaves the table between $n = 23$ and $n = 24$, roughly
doubling per added vertex. Random tournaments are the easy case: no automorphisms to rediscover
and, being far from extremal, many witnesses. On the structured instance of the same order,
$P_{23}$, the same solver did not terminate within a cumulative six weeks. The gap between
$18.95$ seconds and six weeks at equal $n$ is the cost of symmetry.

A better encoding and an explicit symmetry break both help substantially and are still not enough (results 
not shown). What does work is supplying the solver with the decomposition itself: cube-and-conquer over base
states, which is how both refutations are certified in Appendix B. A CDCL solver must otherwise
discover that decomposition for itself, and cannot exploit $\mathrm{Aut}(T)$ at all without an
explicit break in the encoding.

### A.2 Depth-first placement search

The search maintains a partial profile: a set $S \subseteq V$ of *placed* vertices together with,
for each voter, a linear order of $S$. It begins from a base state, which places $B$, and extends
by inserting one unplaced vertex at a time. Inserting $v$ means choosing, for each voter
independently, a slot among the $|S| + 1$ available; the *domain* $D(v \mid S)$ is the set of
$k$-tuples of slots consistent with every arc between $v$ and $S$. A partial profile is extendable
only if every unplaced vertex has a non-empty domain, and domains shrink monotonically as $S$
grows, which makes the search a constraint-propagation problem rather than a blind enumeration.

Two decisions in the pseudocode below carry nearly all of its speed. The first is *which* unplaced
vertex to insert next: the search always takes one of currently smallest domain — the
minimum-remaining-values rule, marked MRV below — recomputed at every node rather than fixed once
per base state. The second is that a child's domains are refined from its parent's. Both are
quantified after Figure 1.

```
ALGORITHM 1.  Placement search for k-inducibility of T

Input :  tournament T on vertex set V;  number of voters k; margin regime (majority or unit)
Output:  a witness profile, or a refutation

MAIN
  for each base state  (a lex-canonical assignment of the base B to k orders):
      S <- B
      D(v | S) <- fresh enumeration, for every v not in S
      if any D(v | S) is empty:  continue     // this base state is dead
      if DFS(S) succeeds:        return its witness
  return "not k-inducible"                    // no base state extends

DFS(S)
  if S = V:  return the profile               // all vertices placed
  v* <- argmin  |D(v | S)|   over v not in S  // MRV, recomputed at EVERY node
        ties broken toward  max | |out(v) & S| - |in(v) & S| |
  for each slot tuple p in D(v* | S):
      insert v* at p in each of the k orders;  S' <- S u {v*}
      for each w not in S':
          D(w | S') <- REFINE( D(w | S), p, w, v* )
          if D(w | S') is empty:  undo;  continue with the next p
      if DFS(S') succeeds:  return its witness
      undo                                    // arena pointer reset
  return failure

REFINE(D, q, w, u)                            // q = the slot tuple just used for u
  D' <- {}
  for each p in D:
      lift p to p' voter by voter:
          p_i <  q_i  ->  p'_i = p_i          // w stays before u
          p_i >  q_i  ->  p'_i = p_i + 1      // w stays after u, shifted by the insertion
          p_i == q_i  ->  BOTH are legal, so the tuple splits in two
      keep those lifts whose support  c_w(u) = #{ i : w before u }
      meets the requirement of the single new arc between w and u
  return D'
```

\begin{figure}[!t]
\centering
\includegraphics[width=\linewidth]{paley7_alg1.pdf}
\caption{Algorithm 1 on $P_7$ at $k = 3$, which is $3$-inducible, so the run ends in a witness. A
\emph{slot triple} is one gap per voter, of the $4^{3} = 64$ available, and a vertex's domain is
those triples its arcs to $B$ admit.
\textbf{(a)} The base $T|_B$ on $B = \{1,2,4\}$ in bold; dashed, the arcs at the first vertex
inserted. \textbf{(b)} Steps 2--4: the base state is forced, and MRV takes the smallest domain.
\textbf{(c)} Two insertions the search rejects, one by Lemma 2.1 and one by leaving $5$ no slot at all.
\textbf{(d)} One that survives, and what it leaves of (b). \textbf{(e)} REFINE lifts each parent
tuple past the slot just used (unchanged below it, shifted above it, split where the two
coincide, which is what green marks), and the one new arc then keeps or kills each lift.
\textbf{(f)} The witness, every arc at support exactly $2$. Without Lemma 2.1 the search returns
all $7$ witnesses, a single orbit of $\mathrm{Aut}(P_7)$, of order $21$, so the profile is unique
up to symmetry, as Shepardson and Tovey [7] report; $\pi$ generates the other two under the $g$
shown, the map $x \mapsto 2x + 4$ of $\mathbb{F}_7$.}
\end{figure}

Four choices make it fast, and the second is the one that made $n = 19$ and $n = 23$ decidable at all.

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

**Symmetry breaking.** The $k!$ voter symmetry is absorbed exactly by the base-state definition,
which counts non-decreasing tuples only. For $\mathrm{Aut}(T)$ the engine imposes the anchoring of
Lemma 2.1 or of Corollary 2.2, whichever is stronger on the tournament: the condition is invariant under
permuting voters, so it composes with the base lex-order, and monotone under insertion, so it can
be tested during the search rather than only at the leaves.

**Early termination and caching by arc pattern.** A quick per-voter agreement bound, obtained by counting the
agreement between voter $i$ and the arcs between $v$ and $S$ two ways, proves $D(v \mid S)$ empty
in $O(k|S|)$ time without enumerating it. And the per-base-state work is keyed by the *arc pattern* of
$T|_B$ rather than by $B$ itself, so base-state counts, which depend only on that pattern, are 
reused across every copy of the same base class and across every $q$.

**Choosing the base.** The base set is not a free parameter, and the fewest live base states is not
the fastest choice: at $q = 31$ the class with $4{,}007$ live states beat the class with $2{,}537$,
whose states are individually slower, so we rank the twelve $5$-vertex classes by the product of the
live count and a sampled time per state rather than by the count alone.

### A.3 How the runtime scales in $q$

**A note on $q = 27$.** The series below includes $q = 27$, the one prime power among the orders we
computed with. Since $27 = 3^3$, $P_{27}$ must be built over $\mathbb{F}_{27}$ and not over
$\mathbb{Z}/27$. $P_{27}$ is the unique most symmetric doubly regular tournament on $27$ vertices,
with $|\mathrm{Aut}(P_{27})| = 1053 = 3q(q-1)/2$, because the field automorphisms
contribute (in general $|\mathrm{Aut}(P_q)| = q(q-1)e/2$ when $q = p^e$).
It is still transitive on arcs and on non-arcs, which is what Lemma 2.1 needs. We ran $q = 27$
to completion and it is not $5$-inducible; since that does not bear on $N(5)$ we report it here
only as a runtime datapoint.

On a fixed base decomposition the total runtime *decreases* as the tournament grows, and so does the
node count: a larger Paley tournament is *more* constrained, so the search is refuted nearer the root
and the tree above each base state is smaller rather than larger. The work per node moves the other
way, rising monotonically from $10.8$ to $57.4$ microseconds across the four runs below, because a
larger tournament carries larger domains and each refinement step costs more. The node count falls
faster than the per-node cost rises, which is what makes the total fall. The full runs:

| $q$ | live base states | core-hours | nodes | seconds per live base state |
|:------|:-------------------|:-------------|:--------|:------------------------------|
| 23 | $2{,}591$ | $34.03$ | $1.14 \times 10^{10}$ | $47.3$ |
| 27 | $2{,}537$ | $31.04$ | $6.22 \times 10^{9}$ | $44.0$ |
| 31 | $4{,}007$ | $26.89$ | $3.43 \times 10^{9}$ | $24.2$ |
| 43 | $2{,}537$ | $22.87$ | $1.43 \times 10^{9}$ | $32.5$ |

$P_{43}$ is decided in *less time than $P_{27}$*, and explores $4.3$ times fewer nodes to do it.
The last column is the third divided by the second, so only the core-hours and the live
base states are measured. Just two of these four runs share a decomposition, $q = 27$ and
$q = 43$, on the same five-vertex base class and the same $2{,}537$ live base states; $q = 23$ and
$q = 31$ each used their own best configuration, and $q = 31$'s is the cheaper class of Appendix
A.2, which is why its per-state figure is the lowest of the four.
The core-hours fall monotonically in $q$ either way. Note, however, that $P_{43}$ minus a vertex 
takes $185.5$ core-hours, far more than $P_{43}$ itself, as vertex deletion shrinks the 
automorphism group.

Additionally, the search gets faster as the margin is
tightened. On the identical tournament ($P_{43} -\,v$), engine and $5$-vertex base class, there is a 
factor of about $90$. Requiring every arc to be at unit margin admits $2{,}200$ base states where 
majority admits $8{,}031$; additionally, under exact margin the last voter is *forced*, since the support 
accumulated over the first $k-1$ voters determines what the last must contribute, so a whole level of the 
search collapses.

**Two machines, and why their runtimes are not comparable.** Some computations ran on a cluster
rather than the laptop. Measured across six independent experiments, the cluster ran at $2$ to
$5$ times the laptop's runtime per unit of work.

We are not claiming that bespoke search beats integer programming or satisfiability in general. Our 
engine is narrow: it exploits the specific facts that a partial profile's extensions
form a product of per-voter slot choices, that this product refines monotonically, and that
$\mathrm{Aut}(T)$ is large and computable. For the specific Paley instances in this paper that the 
general-purpose methods did not settle for us, the search settles in hours on a single laptop.

### A.4 Runtimes for every computation

All runs in this manuscript were performed on a single laptop (Apple M-series, 14 cores, 24 GB RAM),
using at most 11 cores concurrently, with three exceptions that used a compute cluster: the census
of regular tournaments on $15$ vertices, the self-converse census of order $13$, and the order-$12$
census of Appendix C. Runtimes are reported in *core-hours*, the workers' running times summed.

| computation | margin | verdict | core-hours |
|-------------------------------------------------------|--------------|---------------|-----------:|
| $P_{19}$, certified refutation | unit | not inducible | $25.1$ |
| $P_{23}$, certified refutation | unrestricted | not inducible | $236.0$ |
| $P_{31} -\,v$, sweep | unrestricted | not inducible | $239.5$ |
| $P_{23}$, one arc reversed | unrestricted | inducible | $210.4$ |
| second doubly regular $19$, all $57$ arc reversals | unit | all inducible | $3.59$ |
| regular tournaments on $15$ vertices | unit | all inducible | $3{,}106$ |
| self-converse tournaments on $13$ vertices | unit | all inducible | $1{,}310$ |
| all tournaments on $12$ vertices | unit | all inducible | $\approx 10{,}000$ |

The four full Paley sweeps, $q = 23$, $27$, $31$ and $43$, are tabulated with their node counts in
A.3 above.

## Appendix B. The formal certificates

### B.1 The certified refutations

Both machine-checked results follow an established design rather than a new one. *Cube-and-conquer*
is due to Heule, Kullmann, Wieringa and Biere [9]: split a hard instance into many partial
assignments (*cubes*), hand each to a CDCL solver, and let the splitting supply the global structure
the solver cannot find for itself. The standard of *proof* is the one Heule, Kullmann and Marek set
for the Boolean Pythagorean triples problem [3], and Schur number five [13] and the Keller
conjecture [14] after it: every subproblem emits a machine-checkable refutation, validated by an
independent checker rather than trusted. We claim no methodological novelty.

**What an LRAT proof is.** A solver's verdict of unsatisfiability is not self-evidently checkable,
so the solver writes a *proof log*: a file recording, in order, the clauses it derives, each of
which must follow from the input formula together with the clauses already recorded, the last being
the empty clause. A separate checker replays that file and confirms every step, so what one trusts
is the checker rather than the solver. The available formats record essentially this same
derivation and differ mainly in how much work the replay costs. We use LRAT [10], the format
CaDiCaL emits natively and `lrat-trim` consumes, in which checking is a single pass over the file.

Two differences are consequences of our setting. Our cubes are *base states*, a combinatorial 
decomposition, which lets the coverage of the cube set be certified separately (B.2) instead
of resting on a splitting heuristic. And where [3] published a cube certificate from which its
refutations can be regenerated, we *verify and discard*:
each LRAT proof is checked, hashed and deleted, and we only publish the hash value. 
The choice suits the scale. Verifying the Boolean Pythagorean triples
proof costs about $13{,}000$ core-hours to regenerate the refutations from the published cube
certificate [12], and about $16{,}000$ to check them [3]. Our
certificates are orders of magnitude smaller: $25.1$ core-hours for $P_{19}$ and $236.0$ for
$P_{23}$ cover solving *and* checking. Portable root values, which is exactly the check Section 5.2 supports, 
can be easily compared by anyone replicating our computation.

For $P_{19}$ at unit margin the instance is the dissent-Boolean encoding of Appendix A.1 at
$q = 19$, $k = 5$: $855$ variables and $12{,}255$ clauses. The cubes are the $142{,}251$ base 
states of the $6$-vertex base $\{1,2,3,4,5,12\}$, of which $22{,}876$ survive the arc-orbit
break, and each is handed whole to CaDiCaL with `--lrat=true --checkproof=0`. Each LRAT proof is 
checked by `lrat-trim`. The runtime was $2.64$ hours on ten cores. Its coverage half is the
same construction as the one below, at $143{,}032$ clauses, and solves in $7.56$ seconds.

For the $P_{23}$ refutation of Section 3.1, the base is $\{1,2,3,4,6,7\}$ with $3{,}414{,}729$ 
base states, of which $343{,}896$ survive the arc-orbit
and non-arc-orbit breaks; every one is unsatisfiable, with an LRAT proof independently
verified by `lrat-trim`. The runtime was $21.72$ hours on eleven cores.
The coverage half of the proof is a single unsatisfiable instance of $350$ constraint 
clauses, $356$ symmetry-breaking clauses and $3{,}414{,}729$ negated
cubes, one per base state, since coverage must see *every* base state whereas the orbit breaks
apply to the search half only. It solves in just under $20$ minutes on one core and emits a $2.05$ GiB LRAT proof.

### B.2 What the certificates do and do not establish

The trust chain has four links:

| link | status |
|-------------------------------------------------------|-------------------------------------------------------|
| every live cube is unsatisfiable | machine-checked: CaDiCaL, rechecked by `lrat-trim` |
| the cubes cover every lex-canonical base assignment | machine-checked: LRAT, verified by `lrat-trim`; also as DRAT by `drat-trim` [19] |
| (L1) orbit anchoring loses no generality | human-checked: Lemma 2.1 |
| (L2) lex-ordering the voters loses no generality | human-checked: Lemma 2.3 |

The two human-checked links are proved in Section 2. Lemma 2.1 is what licenses solving only the *live*
cubes, in its arc/non-arc form: $\mathrm{Aut}(P_q)$ is transitive on arcs and on non-arcs, so a
voter's top pair may be assumed to be a fixed arc or a fixed non-arc. Lemma 2.3 licenses the lex
chain in the coverage computation. They are human-checked links not because they are doubtful but because
nothing in the pipeline checks them; the depth-first engine inherits them, but shares no
implementation with this one, so their agreement is evidence about the implementations, not the lemmas.

## Appendix C. The order-12 case analysis

Every tournament on $12$ vertices is $5$-inducible, so $N(5) \ge 13$. This appendix describes that
computation. It is one of the results in this paper that was not run on the laptop of Section 3: it ran
on a shared cluster, and its runtime is reported in cluster core-hours (see Appendix A.3).

### C.1 Reduction to one-vertex extensions

A direct census is out of reach: $D_{12} \approx 1.5 \times 10^{11}$ classes, $170$ times the
order-$11$ census of [2]. We use that census as the outer loop instead. Let us write $L + S$ for the 
tournament obtained from an order-$11$ tournament $L$ by adding a vertex $v$
whose out-neighbourhood is $S \subseteq V(L)$. Two observations simplify the analysis.

**(C1)** Every order-$12$ tournament is $L + S$ for some order-$11$ $L$ and some $S$.

**(C2)** Restricting a profile that realises $L + S$ to $V(L)$ gives a profile that realises $L$.

By (C1), enumerating all $D_{11}$ order-$11$ classes and settling all $2^{11} = 2{,}048$
extensions of each settles every order-$12$ tournament; all of the former are $5$-inducible by the
census of [2], which is what makes the outer loop available. By (C2), a
profile realising $L + S$ may be sought by *inserting* $v$ into a profile realising $L$ with no
loss of generality, since every profile for $L+S$ arises that way. That is what phase 1 exploits.

### C.2 Three phases

The census is organised into three phases, with the fastest ones occurring earlier.

**Phase 1, the covering search.** Rather than $2{,}048$ separate instances per order-$11$ tournament, one 
search enumerates profiles realising $L$ *at unit margin* and, for each, records every
out-neighbourhood obtainable by inserting $v$ into its five orders: $v$'s position in each order is a threshold, and the support of $v \to u$ 
is the number of orders that place $v$ above $u$, so one traversal certifies many extensions at once. This
is the engine of Appendix A.2 with $v$'s placement read off rather than fixed in advance. The
margin makes this phase pay twice: it keeps the enumeration of profiles for $L$ small, and a
unit-margin witness is in particular a majority witness, so every extension the phase covers is
settled in both regimes at once. The phase is one-sided: an extension it covers is certified $5$-inducible, but one left over is not refuted.
This phase settles every one of the $2{,}048$ extensions of $99.5\%$ of the order-$11$
tournaments.

**Phase 2, deciding what is left.** Each extension phase 1 leaves open is materialised as an order-$12$
tournament $L + S$ and decided by the same engine, again at unit margin, where a witness
settles it positively. About one extension in $200{,}000$ reached this phase, and every one of
them is $5$-inducible with unit margin.

**Phase 3, plain majority.** Only a *majority* refutation would be a counterexample, so any
instance negative at unit margin is re-run without the margin restriction. Phase 3 was never
invoked: every tournament was settled at unit margin, so the weaker question never had to be asked.

### C.3 One tournament of each converse pair

If $\pi_1, \dots, \pi_5$ realise $T$, their reversals realise the converse $\bar{T}$, with the same 
margins, so $T$ is $5$-inducible if and only if $\bar{T}$ is. Moreover
$\overline{L + S} = \bar{L} + (V(L) \setminus S)$, so settling all $2{,}048$ extensions of $L$ settles
all $2{,}048$ of $\bar{L}$ as well. We therefore keep one tournament of each converse pair, by the
rule that $L$ is kept if and only if $\mathrm{canon}(L) \le \mathrm{canon}(\bar{L})$. This keeps
exactly one of each pair together with every self-converse tournament, $(D_{11} + S_{11})/2$ in all,
where $S_{11}$ is the number of self-converse order-$11$ classes; this saves a factor of
$\lessapprox 2$. We also check the number of tournaments kept is $(D_{11} + S_{11})/2$.

Total runtime: approximately $10{,}000$ cluster core-hours. The search code, the per-part
records and the roll-up are at `cluster/jz_n12cover` in the 
repository of Section 5.

## Appendix D. Exact enumeration counts

The counts the main text gives to two significant figures, in full. $D_n$, $R_n$ and $S_n$ are the
numbers of isomorphism classes of all, of regular, and of self-converse tournaments on $n$
vertices. They match OEIS A000568 [21], A096368 [17], and A002785 [22].

| $n$ | $D_n$ | $R_n$ | $S_n$ |
|---:|---:|---:|---:|
| $11$ | $903{,}753{,}248$ | $1{,}223$ | $279{,}968$ |
| $12$ | $154{,}108{,}311{,}168$ | — | $1{,}492{,}288$ |
| $13$ | — | $1{,}495{,}297$ | $95{,}458{,}560$ |
| $15$ | — | $18{,}400{,}989{,}629$ | — |

## Appendix E. Locally transitive tournaments, at unit margin, for every odd $k \geq 3$

A tournament is *locally transitive* if for every vertex $v$ both $N^{+}(v)$ and $N^{-}(v)$ induce
transitive subtournaments. Equivalently it is *round*: the vertices admit a cyclic order in which
every $N^{-}(v) \cup \{v\}$ and $\{v\} \cup N^{+}(v)$ is an interval. The equivalence is due to
Brouwer [23], who proved it in the course of enumerating the class, and to Alspach and Tabib [24],
who state it for tournaments under the name *domination orientable*; Bang-Jensen later generalised
it to digraphs.

**Theorem E.1.** *Every locally transitive tournament is $3$-inducible with unit margin, and hence
$k$-inducible with unit margin for every odd $k \ge 3$.*

Only the strongly connected case arises, because a locally transitive tournament that is not
strong is transitive: a strong component $C$ with $|C| \geq 3$ contains a directed triangle, and
any vertex outside $C$ either beats all of $C$ or loses to all of it, which would put that triangle
inside its out- or in-neighbourhood. A transitive tournament is $1$-inducible, and this profile can 
be padded by any linear order together with its reverse to achieve margin 1 with $k = 3$ and, by 
induction, any other odd $k$.

Let $T$ be strong and round. Cutting the cyclic order at $v_0$ yields the linear order
$A = (v_0, \dots, v_{n-1})$, and we write $d_i$ for the out-degree of $v_i$ and $r_i = i + d_i$ for
the position of its last out-neighbour before reduction. The round condition says that
$j \le d_i \iff d_{i+j} \le n-1-j$ for $1 \le j \le n-1$, from which
$r_0 \le r_1 \le \dots \le r_{n-1}$, so that the arcs $A$ ranks *wrongly* form a nested staircase.
The sources of that staircase, $H = \{i : r_i \ge n\}$, are a suffix $\{q, \dots, n-1\}$; the
ceilings $t_i = r_i - n$ satisfy $t_q \le \dots \le t_{n-1}$; and the back-targets of $v_i$ are
exactly $v_0, \dots, v_{t_i}$. Setting $L = \{0, \dots, q-1\}$, one checks that $t_{n-1} < q$, so
that $H$ and the back-targets are disjoint, and for $h \in H$ and $l \in L$ the round rule reads
$v_h \to v_l \iff l \le t_h$. We now take the three orders

$$A = (v_0, \dots, v_{n-1}), \qquad B = (v_q, \dots, v_{n-1}, v_0, \dots, v_{q-1}),$$

with $C$ listing the vertices by *decreasing* key, where $\mathrm{key}(v_l) = l$ for $l \in L$ and
$\mathrm{key}(v_h) = t_h + \tfrac12$ for $h \in H$, ties among equal $t_h$ broken by larger
index first. The integer and half-integer keys never collide, so only that one tie-break is at
issue, and by construction $C$ ranks $v_h$ before $v_l$ exactly when $l \le t_h$, that is exactly
when $v_h \to v_l$.

Every arc is then ranked correctly by exactly two of the three. An arc inside $L$ or inside $H$ is
ranked correctly by $A$ and by $B$, and wrongly by $C$: inside $L$ because the keys are the indices
and $C$ reverses them, inside $H$ because the ceilings are monotone, so the head's key is at least
the tail's and the tie-break settles equality the same way. A forward arc from $L$ to $H$ is
correct in $A$ and $C$ and wrong in $B$; a back arc from $H$ to $L$ is correct in $B$ and $C$ and
wrong in $A$. Every arc therefore has support exactly $2$, none is unanimous, and the profile
realises $T$ at unit margin; the padding argument above extends this margin to any odd $k \geq 3$. 
That *some* profile realises a tournament with all margins equal to $1$ is a consequence of Debord's 
parity theorem [25]; the content of Theorem E.1 is that three voters suffice, uniformly over the family.

## Appendix F. Criticality at $21$ vertices

This appendix carries the detail behind Section 3.5. Throughout, $h$ ranges over the four
unit-margin obstructions among the $110$ vertex-transitive tournaments on $21$ vertices (Section 3.6).

**Vertex-critical but maximally not arc-critical.** Arc-criticality implies vertex-criticality,
and the converse fails here as widely as it can. Each $h$ is *vertex-critical* at unit margin, and
for $h_1$ every single-arc reversal remains a unit-margin obstruction.

**Arc-criticality is not a property of the tournament.** All four have ten arc orbits of size $21$; 
we sweep one representative per orbit at unit margin and get results that differ by tournament *and* by
arc, `U` marking a reversal that is still not unit-margin inducible and `S` one that is:

| tournament | $\mathrm{Aut}$ | the ten orbits | obstructions |
|---|---|---|---|
| $h_1$ | $\mathbb{Z}_{21}$ | `U U U U U U U U U U` | $10$ |
| $h_2$ | $\mathbb{Z}_{21}$ | `U S U S S U U S S U` | $5$ |
| $h_4$, $h_5$ | $\mathbb{Z}_7 \rtimes \mathbb{Z}_3$ | `S S S S S S S S S S` | $0$ |

Two things follow. First, arc-criticality at unit margin is *determined by the arc* and not by the
tournament: $h_2$ splits five orbits to five, so exactly half its arcs are critical and we call it
*arc-semi-critical*; with $P_{23}$ arc-critical unrestricted and $h_1$ critical nowhere, all three
possibilities occur among our tournaments. Second, every one of the $15$ reversals that remains an obstruction belongs to a tournament with
*cyclic automorphism group*, while all $20$ orbits of the two with the nonabelian group of order $21$ 
are inducible.
