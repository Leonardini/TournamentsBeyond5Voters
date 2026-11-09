---
output:
  pdf_document:
    keep_tex: true
  html_document: default
header-includes:
  - \usepackage{graphicx}
  - \graphicspath{{figures/}{./}}
xref-external:
  - "Proposition 1 of Milosz, Hamel and Pierrot"
  - "Dummit and Foote 2004, Section 4.1, Proposition 2"
  - "Chung and Graham (1991, Section 6)"
  
  - "Conjecture 8.1 of our companion paper"
  - "Table 1 of Bachmeier et al. (2019)"
  - "Bachmeier et al. (2019, Table 4)"
xref-global-statements:
  - [quest, conj]
  - [prob]
---
# Tournaments not inducible by five voters {-}

*In loving memory of Adam Paton.*

**Leonid Chindelevitch$^{a}$ and Ararat Harutyunyan$^{b}$**

$^{a}$ MRC Centre for Global Infectious Disease Analysis, School of Public Health, Imperial
College London, 90 Wood Lane, London W12 0BZ, United Kingdom. Email: `lchindel@ic.ac.uk`. ORCID: 0000-0002-6619-6013.

$^{b}$ University of Paris-Dauphine, PSL University, CNRS UMR7243, LAMSADE, Place du Maréchal de Lattre
de Tassigny, 75775 Paris Cedex 16, France.
Email: `ararat.harutyunyan@lamsade.dauphine.fr`.

Corresponding author: Leonid Chindelevitch (`lchindel@ic.ac.uk`).

## Abstract {-}

How many voters are needed before their pairwise majorities can produce every tournament? For odd
$k$, let $N(k)$ be the least number of vertices on which some tournament arises from no $k$ voters.
Only $N(3) = 8$ is known (Shepardson and Tovey 2009; Eggermont et al. 2013). For five voters the best
bounds were $11 \le N(5)$ (Bachmeier et al. 2019) and $N(5) \le 41$ (Eggermont et al. 2013, p. 271;
Bachmeier et al. 2019). We show $13 \le N(5) \le 22$. The upper bound comes from nine tournaments on
22 vertices that five voters cannot produce: eight one-vertex deletions of doubly regular tournaments
on 23 vertices, including every deletion of one of them, and one arc reversal. The Paley tournament on
23 vertices, which Bachmeier et al. (2019) left open after six weeks of SAT solving, is beyond five
voters, and so is every other doubly regular tournament on 23 vertices. The lower bound comes from an
analysis of all tournaments on 12 vertices. An argument that searches no profiles shows that the
Paley tournament on 43 vertices is also beyond five voters. Its predictability, the largest share of
the voters that a profile can give to every majority at once, exceeds the threshold $3/5$ by only
$2/1505$, so this result refutes the conjecture that a predictability above the threshold lets five
voters produce a tournament. Our method is a search that places one vertex at a time and exploits
the tournament's symmetries. We certify four of the negative results with machine-checkable proofs,
and a public repository reproduces every result.

**Keywords:** majority voting; tournaments; McGarvey's theorem; Paley tournaments; constraint search; SAT

## Introduction {#sec:intro}

Let $T$ be a *tournament* on a vertex set $V$ with $|V| = n$: a digraph in which every unordered pair
$\{i, j\}$ carries exactly one of the arcs $i \to j$ and $j \to i$. A *profile* of $k$ *voters* is a list of $k$
linear orders $\pi_1, \dots, \pi_k$ of $V$, and its *majority tournament* has the arc
$i \to j$ whenever $|\{ v : i \prec_{\pi_v} j \}| > k/2$; for odd $k$ this decides every pair. We say
that $T$ is *$k$-inducible* if it is the majority tournament of some profile of $k$ voters, which we then call a
*witness* for $T$. McGarvey (1953) proved that every tournament is $k$-inducible for some $k$, and counting
profiles shows that for fixed $k$ almost all large tournaments are not. For odd $k$ we write $N(k)$ for the
least order of a tournament that is not $k$-inducible.

Only $N(3) = 8$ is known (Shepardson and Tovey 2009; Eggermont, Hurkens and Woeginger 2013). For
$k = 5$ the bounds were $11 \le N(5) \le 41$ (Bachmeier et al. 2019; Eggermont et al. 2013, p. 271), the
upper one by counting, and the smallest explicit tournament known not to be $5$-inducible had over
$6 \times 10^{8}$ vertices (Fidler 2011; Bachmeier et al. 2019). We show that $13 \le N(5) \le 22$;
Section @sec:contributions lists our results, and Figure @fig:ladder shows one of the eight tournaments on
$22$ vertices that give the upper bound.

\begin{figure}[!htbp]
\centering
\includegraphics[width=0.62\linewidth]{ladder_d000.pdf}
\caption{The tournament $\Delta_1 - v_{10}$ (notation of Section @sec:contributions), which is not $5$-inducible. Its $22$ vertices split into $X = \{x_0, \dots, x_{10}\}$
and $Y = \{y_0, \dots, y_{10}\}$, with indices taken modulo $11$, and each half induces a copy of
$P_{11}$: $x_i \to x_j$ exactly when $j - i$ is a non-zero square modulo $11$, that is, lies in
$\mathrm{QR} = \{1, 3, 4, 5, 9\}$, and $y_i \to y_j$ exactly when $j - i$ is a non-square.
Between the halves, $x_i \to y_j$ when $j - i$ is a non-square, and $y_j \to x_i$ otherwise, that is,
when $j - i$ lies in $\mathrm{QR} \cup \{0\}$. In particular every rung $y_i \to x_i$ of the ladder
points from $Y$ to $X$; only six rungs are drawn. Each $x_i$ therefore has out-degree $10$
and each $y_j$ has out-degree $11$. Adding $1$ to every index, and multiplying every index
by an element of $\mathrm{QR}$, are automorphisms; together they generate the full automorphism group,
of order $55$.}
\label{fig:ladder}
\end{figure}

What these *obstructions* (tournaments that are not $5$-inducible) share is balance rather than symmetry:
none of the $37$ doubly regular tournaments on $23$ vertices, in which every vertex has out-degree $11$
and every two vertices the same number of common out-neighbours, is $5$-inducible, although $32$ of them
have a trivial automorphism group (Section @sec:families).

The *support* $c(e)$ of an arc $e: i \to j$ is the number of voters ranking $i$ above $j$, and its
*margin* is $2c(e) - k$, so for $k = 5$ every margin in a witness is $1$, $3$ or $5$. A witness has
*margin at most $M$* if every arc does, and *unit margin* if every margin is $1$. Our companion paper
(Chindelevitch and Harutyunyan 2026), whose definitions we use, conjectures that this margin hierarchy
is strict; for $k = 5$, $P_{19}$ is $5$-inducible with margin at most $3$ but not with unit margin
(Section @sec:paley19). Reversing every voter reverses every arc and changes no support, so $T$ and its
converse $\bar{T}$ are $k$-inducible for the same $k$ and at the same margins; we count a family
enumerated in full up to isomorphism, and a family that our searches generated up to isomorphism and
converse.

The *predictability* $\alpha^{*}(T)$ (Shepardson and Tovey 2009) is the largest $\alpha > 1/2$ such that
some profile, on any number $t$ of voters, supports every arc of $T$ with at least $\alpha t$ of them.
A $k$-voter witness supports every arc with more than $k/2$ voters, so $k$-inducibility forces
$\alpha^{*}(T) \ge (k+1)/2k$, which is $3/5$ at $k = 5$; the converse, implicit in their work, we call
the *threshold conjecture*. Our companion paper refutes it at $k = 3$, where it fails only at the
threshold; at $k = 5$ it fails strictly above it, for $P_{23}$ with $\alpha^{*} = 7/11$
(Section @sec:paley23-31) and for $P_{43}$, where $\alpha^{*}$ exceeds $3/5$ by only $2/1505$
(Section @sec:paley43).

### Special properties of Paley tournaments {#sec:paley-properties}

The Paley tournament $P_q$, for a prime $q \equiv 3 \pmod 4$, has vertex set
$\mathbb{F}_q$ and an arc from $i$ to $j$ whenever $j - i$ is a nonzero square, or *quadratic
residue*; we write $\mathrm{QR}$ for the set of these, so that $i \to j$ exactly when $j - i \in
\mathrm{QR}$. As everywhere in
this paper, vertices are numbered from $1$, vertex $i + 1$ being the field element $i$. It is
*doubly regular*: every vertex has out-degree $(q-1)/2$ and every ordered pair of vertices has
exactly $(q-3)/4$ common out-neighbours. Its automorphism group $\mathrm{Aut}(P_q)$ (Section @sec:prelim) has order $q(q-1)/2$. This makes $P_q$ *arc-transitive*, meaning that 
for every pair of arcs $e, e'$ of $P_q$ there is an automorphism of $P_q$ that takes $e$ into $e'$. 
It is also *self-converse*, meaning that it is isomorphic to its own converse; the relevant mapping is 
multiplication by $-1$, which is easily checked to not be an automorphism when $q \equiv 3 \pmod 4$.

### Neither SAT nor the slack argument settles Paley(23) {#sec:why-hard}

Paley tournaments are natural candidates for non-inducibility because they are far from being
transitive, and because their symmetry makes an otherwise hopeless search merely very hard. 
Bachmeier et al. (2019) call them *quadratic residue tournaments*, with the converse orientation, which
changes no result here. Their SAT study shows that $P_3$ and $P_7$ are $3$-inducible and that $P_{11}$ and
$P_{19}$ are $5$-inducible but not $3$-inducible, and then stops at $P_{23}$, on which their solver did not terminate within six weeks.

Nor does the argument by which we settle $P_{43}$ (Section @sec:paley43), which searches no profiles. It
rests on the *slack*, the amount by which five voters can collectively fall short of the most arcs one order
can agree with; the slack is proportional to $\alpha^{*} - 3/5$, and it is $6$ at $q = 43$ but $46$ at $q = 23$
(Table @tbl:paley-family), which leaves the voters of a candidate profile for $P_{23}$ far too much room.

### Contributions {#sec:contributions}

1. **There are non-$5$-inducible tournaments on $22$ vertices, so $N(5) \le 22$** (Section @sec:twenty-two).
   We write $\Delta_i$ for the $i$-th of the $37$ doubly regular tournaments on $23$ vertices in the
   catalogue of McKay (2026), and $\Delta_i - v_j$ for $\Delta_i$ with its vertex $v_j$ deleted. Eight such
   tournaments, pairwise non-isomorphic even up to converse, are not $5$-inducible and are vertex-critical;
   three are the one-vertex deletions of $\Delta_1$, and reversing an arc of one of them, $\Delta_1 - v_{10}$,
   gives a ninth obstruction.

2. **$P_{23}$ is not $5$-inducible** (Section @sec:paley23-31). The SAT solver of Bachmeier et al. (2019) did
   not terminate on it within six weeks; our search settles it in twenty-two hours on a laptop. We also
   decide $P_{31}$.

3. **Counting gives $N(5) \le 38$, and $P_{43}$ is not $5$-inducible** (Sections @sec:bounds and @sec:paley43).
   The counting bounds of Bachmeier et al. (2019) improve for every odd $k \le 21$, and $P_{43}$, whose
   predictability exceeds $3/5$ by only $2/1505$, refutes the threshold conjecture at $k = 5$ strictly
   above the threshold.

4. **$P_{19}$ is $5$-inducible, but not with unit margin** (Section @sec:paley19). At $k = 3$ such
   tournaments first appear at order $9$, after $N(3) = 8$ (see our companion paper); at $k = 5$ they appear
   by order $19$, before $N(5)$ unless $N(5) \le 19$, which the search of Appendix @app:below22 makes unlikely.

5. **$P_{19}$ and $P_{23}$ are arc-critical, and $P_{31}$ and $P_{43}$ are not vertex-critical** (Sections
   @sec:paley23-31 and @sec:paley23-critical). Reversing an arc of $P_{19}$ restores $5$-inducibility at unit
   margin and reversing an arc of $P_{23}$ restores it unrestricted, while $P_{31}$ and $P_{43}$ minus a
   vertex are still not $5$-inducible.

6. **Four negative results are formally certified** (Appendix @app:certificates): $P_{19}$ at unit margin, and
   $P_{23}$, $\Delta_1 - v_{10}$ and $\Delta_6 - v_{5}$. Each subproblem (*cube*) is refuted by the SAT solver
   CaDiCaL with a machine-checkable *LRAT* proof (Section @sec:related), rechecked by a separate program.

7. **Every tournament on $12$ vertices is $5$-inducible, even at unit margin** (Appendix @app:order12), by
   settling all $2{,}048$ one-vertex extensions of each of the $\approx 9.0 \times 10^{8}$ tournaments on
   $11$ vertices.

### Related work {#sec:related}

This paper builds on two others. Our companion paper (Chindelevitch and Harutyunyan 2026) settles the
three-voter questions from which this one starts, and we use its definitions. Bachmeier et al. (2019) is the
prior art for both the *bounds* we improve and the *method*: besides the bounds above, it brought SAT to bear on $k$-majority digraphs, characterized the $3$-majority case building on Dushnik 
and Miller (1941), and established hardness results for several voting rules with a constant number of voters. Without a bound on $k$,
every tournament on $n$ vertices is $k$-inducible with $k = O(n/\log n)$ (Erdős and Moser 1964).

The value of $N(3)$ is settled. Shepardson and Tovey (2009) introduced the predictability
$\alpha^{*}(T)$ defined above. A $3$-voter profile is in particular a $2/3$-supermajority representation, 
so $\alpha^{*}(T) < 2/3$ rules out $3$-inducibility; their $8$-vertex tournament has 
$\alpha^{*} = 13/20$, which gives $N(3) \le 8$. They also prove that every tournament on at most 
$7$ vertices has $\alpha^{*} \in \{2/3, 1\}$, and Eggermont, Hurkens and Woeginger (2013) then show by 
direct computation using an integer linear programming (ILP) formulation that every tournament on $7$ vertices is $3$-inducible, and 
every tournament on $8$ or $9$ vertices is $5$-inducible, yielding $N(3) = 8$ and $N(5) \ge 10$.

So at $k = 3$ predictability decides exactly at $N(3)$; at
$k = 5$ it does not, as $P_{23}$, $P_{31}$ and $P_{43}$ show (Table @tbl:paley-family).

Our certified computation (Appendix @app:certificates) is standard. It splits the problem into
independent subproblems, using the *cube-and-conquer* method (Heule et al. 2012): a SAT instance is split by
fixing a few variables at a time, giving many partial assignments called *cubes*, and each cube is
handed to the solver as a problem of its own. We adopt the standard of evidence set by
the Boolean Pythagorean triples proof (Heule et al. 2016), later re-checked with a formally verified checker (Cruz-Filipe et al. 2019), in which every subproblem emits a machine-checkable
refutation that an independent checker validates. Our refutations are in the LRAT format (Cruz-Filipe et al. 2017)
(Appendix @sec:certified), a format in which the solver records each clause it derives so that an independent
checker can replay and confirm the entire derivation.

The rest of this paper is organized as follows. Section @sec:prelim sets out the notation. Section @sec:bounds bounds $N(k)$ by counting, and Section @sec:paley43
proves that $P_{43}$ is not $5$-inducible by an argument that searches no profiles. Section @sec:search describes the search: its symmetry
reductions, the algorithm and what makes it fast. Section @sec:results presents the results of the search: the Paley tournaments
(Sections @sec:paley23-31 to @sec:paley23-critical), the other structured families (Section @sec:families), and the eight
$22$-vertex obstructions that give $N(5) \le 22$ (Section @sec:twenty-two). Section @sec:discussion
states what remains open and describes the reproducibility material. 

## Preliminaries {#sec:prelim}

In this section we fix the notation used throughout.

Throughout, $T$ is a tournament on $V = \{1, \dots, n\}$ and $k = 5$ unless stated otherwise. We
write $N^{+}(v)$ and $N^{-}(v)$ for the out- and in-neighbourhoods of $v$. A tournament is *regular* 
if $|N^{+}(v)| = |N^{-}(v)|$ for each $v \in V$; this can only happen for $n$ odd. For even $n$ it is *near-regular*
if every out-degree is $n/2 - 1$ or $n/2$; since the out-degrees sum to $\binom{n}{2}$, exactly $n/2$ vertices
then have each of the two. Following our companion paper, $D_n$, 
$R_n$ and $S_n$ denote the numbers of isomorphism classes of, respectively, all tournaments, regular 
tournaments and self-converse tournaments on $n$ vertices, which are OEIS A000568, A096368 and A002785
(OEIS Foundation Inc. 2026a, 2026c, 2026b). For any $S \subseteq V$, the sub-tournament of $T$ induced by $S$, written $T[S]$, is the tournament obtained by restricting $T$ to the vertices in $S$ and the arcs between those vertices.

We call a tournament $T$ *vertex-critical* for $k$-inducibility at margin $M$ if $T$ is not $k$-inducible 
at margin $M$, but $T - v$ is $k$-inducible at margin $M$ for every vertex $v$. Similarly, we call $T$ 
*arc-critical* for such a property if $T$ has it, but any $T'$ obtained from $T$ by reversing an arc does not. 

An *automorphism* of a tournament $T$ is a permutation of its vertices carrying every arc to an arc;
these form a group $\mathrm{Aut}(T)$ under composition. The identity is always an automorphism; any
other automorphism is *non-trivial*, and $T$ is *rigid* when it has none. For a permutation group
$\Gamma$ on a set $X$, the *orbit* of $x$ is $\Gamma x = \{\gamma(x) : \gamma \in \Gamma\}$, and
the orbits partition $X$. The group is *transitive* on $X$ when there is a single orbit, that is,
when for any $x, x' \in X$ there is a $g \in \Gamma$ with $g(x) = x'$. We use orbits of
$\mathrm{Aut}(T)$ on the vertices, on the arcs, and on the *ordered pairs* of distinct vertices,
where $\gamma$ sends $(u,v)$ to $(\gamma(u), \gamma(v))$. An ordered pair is either an arc or the
reverse of one, so that third action has at least two orbits.


The next section uses this notation to bound $N(k)$ by counting.

## Counting bounds on $N(k)$ {#sec:bounds}

In this section we bound $N(k)$ by counting, without exhibiting a tournament: some tournament on $38$ vertices is not $5$-inducible, and the counting bounds of Bachmeier et al. (2019) improve for every odd $k \le 21$.

Comparing counts of profiles and tournaments gives $N(5) \le 41$ (Eggermont et al. 2013, p. 271; Bachmeier et al. 2019). 
Restricting the count to *regular* tournaments tightens this to $N(5) \le 39$, and to *near-regular* 
tournaments to $N(5) \le 38$, because four voters determine a tournament of prescribed 
out-degrees.

### Four voters determine a tournament with given out-degrees {#sec:completion}

The fifth voter of a profile is constrained only on the pairs that the other four split evenly, and there
a prescribed out-degree sequence leaves it no choice.

**Proposition []{#prop:completion} (completion uniqueness).** *Fix odd $k$, linear orders
$\pi_1, \dots, \pi_{k-1}$ on $[n]$ and a sequence $d \colon [n] \to \mathbb{Z}_{\ge 0}$. At most one
tournament with out-degree sequence $d$ is the majority tournament of $\pi_1, \dots, \pi_{k-1}$ and some
$k$-th order, and it can be found in $O(n^2)$ time.*

*Proof.* Pairs that $\pi_1, \dots, \pi_{k-1}$ split with margin at least $2$ are decided whatever
$\pi_k$ does; the evenly split pairs form a graph $D$ on which the majority follows $\pi_k$. The tournament
is therefore determined by the orientation $R$ of $D$ that $\pi_k$ induces, which is acyclic, and every
acyclic orientation of $D$ arises from some $\pi_k$. The sequence $d$ fixes the out-degree $b(x)$ of each
$x$ in $R$: $d(x)$ minus the number of decided arcs leaving $x$. An acyclic orientation has a sink, a vertex
with $b(x) = 0$, and such a vertex must have all its remaining edges oriented into it. Repeatedly deleting a
vertex with $b(x) = 0$, orienting its remaining edges into it and decrementing its neighbours' budgets
therefore either fails, when no such vertex exists or a budget turns negative, and then no completion
exists, or orients every edge in the only possible way; the reverse deletion order is then a valid
$\pi_k$ (Kahn 1962). Each vertex and edge is handled once, in $O(n^2)$ time. $\blacksquare$

### Counting near-regular tournaments gives $N(5) \le 38$ {#sec:count-38}

For even $n$ there are no regular tournaments, but the near-regular ones (Section @sec:prelim) substitute
for them: deleting a vertex $v$ from a regular tournament on $n + 1$ vertices leaves a near-regular
tournament on $n$, and each near-regular tournament arises from exactly one regular tournament in this
way, by re-adding $v$ beating the $n/2$ vertices of out-degree $n/2 - 1$. Hence
$$\#\{\text{near-regular tournaments on } n\} \;=\; R^{L}_{n+1}, \label{eq:near-regular-count}$$
where $R^{L}_{\nu}$ is the number of *labelled* regular tournaments on $\nu$ vertices, the counting taking
place in the labelled world, unlike the isomorphism count $R_n$.

**Theorem []{#thm:n5-38}.** *Some near-regular tournament on 38 vertices is not 5-inducible; hence
$N(5) \le 38$.*

*Proof.* Deleting a voter from a witness shows, by Proposition @prop:completion, that a $5$-inducible
tournament with a prescribed out-degree sequence is determined by a $4$-multiset of orders. The near-regular
sequences on even $n$ number $\binom{n}{n/2}$, so
$$\log_2 \#\{\text{5-inducible near-regular on } n\} \;\le\;
\log_2\Bigl[\binom{n}{n/2}\binom{n! + 3}{4}\Bigr] \;<\; 624.7 \quad (n = 38).$$
By (@eq:near-regular-count) and Schrijver's (1983) lower bound on Eulerian orientations of $K_{39}$, of
which the regular tournaments on $39$ vertices are an instance,
$$\log_2 \#\{\text{near-regular on } 38\} \;=\; \log_2 R^{L}_{39} \;\ge\;
\log_2\Bigl[2^{-\binom{39}{2}} \binom{38}{19}^{39}\Bigr] \;>\; 625.5 ,$$
which exceeds $624.7$. $\blacksquare$

The regular count alone gives only $N(5) \le 39$: $\log_2 R^{L}_{39} > 625.5 > 610.8 >
\log_2 \binom{39! + 3}{4}$, so all but a $2^{-14.8}$ fraction of regular tournaments on $39$ vertices are not
$5$-inducible. At $k = 3$ the same argument shows only that some regular tournaments on $17$ or more vertices
are not $3$-inducible, far weaker than $N(3) = 8$.

### The counting bound improves for every odd $k \le 21$ {#sec:all-odd-k}

The argument is not specific to five voters: Proposition @prop:completion holds for every odd $k$, and
the near-regular bijection (@eq:near-regular-count) does not depend on $k$. Counting both classes gives:

**Theorem []{#thm:all-odd-m} (all odd $k$).** *For odd $k \ge 3$: (a) at most $\binom{n! + k - 2}{k - 1}$
regular tournaments on odd $[n]$ are $k$-inducible, so a non-$k$-inducible regular tournament
exists once $R^{L}_{n} > \binom{n! + k - 2}{k - 1}$; (b) at most
$\binom{n}{n/2}\binom{n! + k - 2}{k - 1}$ near-regular tournaments on even $[n]$ are
$k$-inducible, so a non-$k$-inducible near-regular tournament exists once
$R^{L}_{n+1} > \binom{n}{n/2}\binom{n! + k - 2}{k - 1}$, using in both cases Schrijver's
bound $R^{L}_{\nu} \ge 2^{-\binom{\nu}{2}}\binom{\nu-1}{(\nu-1)/2}^{\nu}$ (odd $\nu$).*

Together with the exact multiset count of profiles, this extends Table 1 of Bachmeier et al. (2019); Table @tbl:expressiveness lists both. Their counting
lemma bounds the majoritarian expressiveness $n^{\mathcal{T}}(k)$, the largest $n$ such that every $n$-vertex tournament is $k$-inducible, via the estimate $\binom{n! + k - 1}{k} \le (2 \cdot n!)^k / k!$. 
Using the exact multiset count in place of their estimate, which uses the bound of Fiol (1992) (the "exact" row), already sharpens 
three entries (the $k = 5$ case noted in a footnote of Bachmeier et al. 2019); the regular and near-regular bounds of 
Theorem @thm:all-odd-m then sharpen all ten. The 10 best bounds are equally split between *regular* tournaments of 
odd size and *near-regular* tournaments of even size. The smallest non-$k$-inducible tournament has 
$N(k) = n^{\mathcal{T}}(k) + 1$ vertices, so that $n^{\mathcal{T}}(5) \le 37$ is exactly the bound 
$N(5) \le 38$ of Theorem @thm:n5-38.

|  | 3 | 5 | 7 | 9 | 11 | 13 | 15 | 17 | 19 | 21 |
|------------------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| Bachmeier et al. (2019) | 18 | 41 | 66 | 93 | 122 | 152 | 183 | 216 | 249 | 282 |
| exact | 18 | **40** | **65** | 93 | 122 | 152 | 183 | **215** | 249 | 282 |
| Thm @thm:all-odd-m | **16** | **37** | **62** | **89** | **117** | **147** | **178** | **210** | **243** | **276** |

Table: Upper bounds on the majoritarian expressiveness $n^{\mathcal{T}}(k)$, the largest $n$
such that every $n$-vertex tournament is $k$-inducible. Columns are indexed by the odd voter
count $k$; bold marks a strict improvement on Table 1 of Bachmeier et al. (2019). {#tbl:expressiveness}

Each threshold is sharp: the count wins at order $n^{\mathcal{T}}(k) + 1$ and fails one vertex lower.

These bounds show that a non-5-inducible tournament exists on 38 vertices, but they do not exhibit
one. The next section gives an explicit example on $43$ vertices.

## Paley(43) is not 5-inducible {#sec:paley43}

$P_{43}$ is not $5$-inducible, although its predictability exceeds the threshold $3/5$. Section @sec:bounds showed that a non-5-inducible tournament exists on $38$ vertices; in this section we prove that $P_{43}$ is one, by an argument that searches no profiles. Among the Paley tournaments of Table @tbl:paley-family, $P_{43}$ is the only one that the margin of its predictability over $3/5$ settles on its own: that margin is just $2/1505$, and it leaves five voters too little room. $P_{23}$, with $\alpha^{*} = 7/11$, refutes the threshold conjecture further above the threshold (Section @sec:paley23-31), but only through the search. We write $P = P_{43}$ throughout the section.

**Theorem []{#thm:paley43}.** *$P = P_{43}$ satisfies $\alpha^{*}(P) = \mathrm{MAS}/C = 543/903
= 181/301 > 3/5$, yet $P$ is not 5-inducible. Hence $\alpha^{*} > \frac{k+1}{2k}$ does not
imply $k$-inducibility, and $N(5) \le 43$ with an explicit tournament.*

Here $\mathrm{MAS}(T)$ is the maximum number of arcs of $T$ that a single linear order agrees with. An arc
$u \to v$ is *forward* in an order $\pi$ if $\pi$ ranks $u$ above $v$ and *backward* otherwise, and
$\mathrm{fwd}_T(\pi)$ is the set of forward arcs. The identity $\alpha^{*} = \mathrm{MAS}/C$ holds
because $P$ is arc-transitive, that is, $\mathrm{Aut}(P)$ acts transitively on its arcs. No order has
more than $\mathrm{MAS}$ forward arcs, so in any profile the average support of an arc is at most a
fraction $\mathrm{MAS}/C$ of the voters, and the smallest support is no larger. Conversely, the profile
formed by the images under $\mathrm{Aut}(P)$ of one order with $\mathrm{MAS}$ forward arcs gives every
arc exactly that fraction (the symmetrization lemma of our companion paper). Throughout, $q = 43$, 
$C = \binom{q}{2} = 903$, the number of cyclic triangles is $N_{\Delta} = (q^3 - q)/24 = 3311$, 
and $|\mathrm{Aut}(P)| = q(q-1)/2 = 903$.

### The slack forces two near-optimal voters {#sec:mas-shell}

In a witness every arc is forward for at least three of the five voters, so the voters have at least $3C$ forward arcs between them, while none has more than $\mathrm{MAS}$. The *slack*
$$\mathrm{slack}_5(T) \;=\; 5\,\mathrm{MAS}(T) - 3C$$
therefore bounds how far the voters can collectively fall short of the maximum. For an arc-transitive $T$ it equals $5C\,(\alpha^{*}(T) - 3/5)$, so it grows in proportion to $C$ whenever the predictability stands off from the threshold. A subset dynamic program modulo $\mathrm{Aut}(P)$ with a meet-in-the-middle step (Appendix @app:mas-dp) gives $\mathrm{MAS}(P) = 543$, so $\mathrm{slack}_5(P) = 2715 - 2709 = 6$, the smallest value in Table @tbl:paley-family; the others are at least $7$.

For an inducing profile $(\pi_1, \dots, \pi_5)$, let $f_i = |\mathrm{fwd}_P(\pi_i)|$
and relabel the voters so that $f_1 \ge f_2 \ge \cdots \ge f_5$. Then $\sum_{i=1}^{5} f_i \ge 3C = 2709$ and $f_1 \le 543$, so
the other four sum to at least $2166$, and $4 f_2 \ge 2166$, i.e. $f_2 \ge 542$. The *level* of an order $\pi$ is
$\delta(\pi) = \mathrm{MAS} - |\mathrm{fwd}_P(\pi)|$, so **at least two voters lie at level $\le 1$**, and the five levels sum to at most
$\mathrm{slack}_5(P) = 6$.

A cyclic triangle is *double-backed* by an order that ranks two of its three arcs backward, and the
*double-back set* $\mathrm{DB}(\pi)$ of $\pi$ is the set of cyclic triangles it double-backs.

**Lemma []{#lem:co-backing} (co-backing).** *In a $5$-voter witness, no cyclic triangle is double-backed by two voters.*

*Proof.* Each arc of the triangle is ranked backward by $\le 2$ of the 5 voters,
so there are at most six backward incidences; each voter ranks $\ge 1$ arc of a cyclic triangle backward (a
linear order cannot agree with all three arcs of a cycle); if $d$ voters double-back,
incidences $= 5 + d \le 6$, so $d \le 1$.
$\blacksquare$

The five voters' double-back sets are therefore pairwise disjoint, so the two voters at level $\le 1$ have
disjoint double-back sets. **If no such pair exists, $P$ is not
5-inducible**, and this is a finite criterion.

### No two near-optimal orders have disjoint double-back sets {#sec:screen}

The orders of level at most $1$, which we call the *shell*, number $1{,}662{,}696{,}609$, in $1{,}841{,}303$ orbits of $\mathrm{Aut}(P)$ (Appendix @app:paley43-ledger). We decide the criterion by checking every pair, which two reductions make practical:

* **A window of 24 vertices.** We fix the window $\mathcal{W} = \{0, 1, \dots, 23\}$ and its 538 cyclic
  triangles. The restriction of $\mathrm{DB}(\pi)$ to these triangles depends only on how $\pi$ ranks
  $\mathcal{W}$, so the shell has only $4{,}709{,}640$ distinct restrictions, and two orders with disjoint
  double-back sets have disjoint restrictions; only the $5{,}092{,}111$ disjoint pairs of restrictions
  need the exact check.
* **Orbit representatives on one side.** $\mathrm{DB}(\sigma \pi) = \sigma(\mathrm{DB}(\pi))$ for
  $\sigma \in \mathrm{Aut}(P)$, where $\sigma \pi$ ranks $\sigma(v)$ where $\pi$ ranks $v$, because $\sigma$ maps forward arcs of $\pi$ to forward arcs of $\sigma \pi$. Overlap sizes are thus $\mathrm{Aut}$-invariant, so testing
  one representative per orbit against the shell suffices, saving a factor of $903$.

The exact check compared all $4{,}376{,}325{,}129$ pairs of an orbit representative and a shell order whose restrictions are disjoint, and **none has disjoint double-back sets**; the smallest overlap is $68$ triangles. With the co-backing lemma, this proves Theorem @thm:paley43. $\blacksquare$

| $q$ | $C$ | $\mathrm{MAS}$ | $\alpha^{*}$ | $\approx$ | $\mathrm{slack}_5$ | 5-inducible?     |
|----|-----|------|--------|--------|-------|---------------------|
| 7  | 21   | 14        | $2/3$      | 0.6667 | 7        | yes; 3 voters suffice |
| 11 | 55   | 35        | $7/11$     | 0.6364 | 10       | yes; 5 voters needed |
| 19 | 171  | 107       | $107/171$  | 0.6257 | 22       | yes; 5 voters needed |
| 23 | 253  | 161       | $7/11$     | 0.6364 | 46       | no (Thm @thm:paley23) |
| 31 | 465  | 285       | $19/31$    | 0.6129 | 30       | no (Sec. @sec:paley23-31) |
| 43 | 903  | 543       | $181/301$  | 0.6013 | **6**    | **no (Thm @thm:paley43)**    |
| 47 | 1081 | $\ge 658$ | $\ge 14/23$ | 0.6087 | $\ge 47$ | open |

Table: The Paley family: size, MAS, predictability, slack and status. For $q = 47$ the entries are lower bounds, from an order with $658$ forward arcs. {#tbl:paley-family}

The table shows that $\alpha^{*}$ is not monotone in $q$: it coincides at $q = 11$ and $q = 23$, and is larger at $q = 47$ than at $q = 43$, so it cannot be extrapolated. The slack is small only at $q = 43$, so the proof above exploits a numerical coincidence. $P_{11}$ and $P_{19}$ are 5-inducible, so non-5-inducibility is not generic to the family; the slack argument does not reach $P_{23}$ or $P_{31}$, which the search of Section @sec:results decides, and $P_{47}$ remains open.

Whether $\alpha^{*} > \frac{k+1}{2k}$ implies $k$-inducibility for odd $k \ge 7$ is open. Adding an order and its reverse changes no margin, so $k$-inducibility implies $(k+2)$-inducibility, and a counterexample at $k = 7$ must be non-5-inducible. $P_{43}$ meets the $k = 7$ threshold ($181/301 > 4/7$), but the slack arithmetic and the co-backing lemma both fail at $k = 7$. Theorem @thm:all-odd-m guarantees non-7-inducible tournaments on $63$ vertices, without exhibiting one.

Before this work, the smallest explicit non-5-inducible tournament had over $6 \times 10^{8}$ vertices, from a theorem of Fidler (2011) (Bachmeier et al. 2019). The slack argument reaches no further than $P_{43}$, so the next section describes the search, which settles $P_{23}$ and $P_{31}$ and finds the obstructions on $22$ vertices.

## The search {#sec:search}

In this section we describe the search that decides the instances of Section @sec:results: the symmetry
reductions it relies on (Section @sec:symmetry), the algorithm (Section @sec:algorithm) and what makes it
fast (Section @sec:fast). Appendix @app:engine proves the reductions and explains why
integer programming and SAT alone fall short here.

### Base states and symmetry reductions {#sec:symmetry}

Every search starts from a small set $B$ of vertices, the *base*, and a *base state* of $B$: $k$ linear
orders of $B$ whose majorities reproduce $T[B]$ at the margin being asked for, counted up to relabelling
the voters. Each base state is a self-contained subproblem, namely whether the remaining $n - |B|$
vertices can be inserted so that every arc of $T$ gets the right support, and $T$ is $k$-inducible
exactly when some base state extends to a witness. The number of base states depends on $|B|$, on
$T[B]$ and on the margin, but not on $n$: the five-vertex bases we use on the Paley tournaments have
$8{,}031$ of them in both $P_{23}$ and $P_{47}$.

Two symmetries act on witnesses: the $k!$ relabellings of the voters, which form the symmetric group
$S_k$, and $\mathrm{Aut}(T)$ acting on the vertices. A permutation $\sigma$ of the voters acts
on a profile $\pi = (\pi_1, \dots, \pi_k)$ by reordering it, and a permutation $h$ of $V$ acts on a
linear order by relabelling, so that $h\pi_j$ ranks $h(u)$ above $h(w)$ exactly when $\pi_j$ ranks
$u$ above $w$, and on a profile voter by voter. The two actions commute, so the group
$S_k \times \mathrm{Aut}(T)$ acts on profiles. It maps witnesses to witnesses: permuting voters
does not change any margin, and the margin of $h(u) \to h(w)$ after relabelling by an
automorphism $h$ equals that of $u \to w$ before. A witness *extends* the base state formed by its
orders restricted to $B$, and the *restriction* of a base state of $B$ to $C \subseteq B$ is the multiset
of its orders restricted to $C$. Every reduction we use is a case of the following lemma, which
Appendix @sec:symmetry-details proves.

**Lemma []{#lem:symmetry} (symmetry reductions).** *Let $T$ be $k$-inducible.*

*(a) (Orbit principle.) Let $G$ be a subgroup of $S_k \times \mathrm{Aut}(T)$ acting on a set $\Omega$, let
$\varphi$ map profiles to $\Omega$ with $\varphi(g\pi) = g\,\varphi(\pi)$ for every $g \in G$, and let
$R \subseteq \Omega$ meet every $G$-orbit. Then $T$ has a witness $\pi$ with $\varphi(\pi) \in R$.*

*(b) (Orbit anchoring.) If $(a_1, b_1), \dots, (a_m, b_m)$ represent the orbits of $\mathrm{Aut}(T)$ on
ordered pairs of distinct vertices, then $T$ has a witness in which, for some $i$, some voter ranks
$a_i$ first and $b_i$ second.*

*(c) (Vertex anchoring.) If $v_1, \dots, v_r$ represent the vertex orbits, a voter of some witness ranks some $v_i$ first.*

*(d) (Voter sorting.) For any total order on linear orders, $T$ has a witness whose $k$ orders are
non-decreasing, and this witness can also be taken to satisfy (b) or (c).*

*(e) (Base-stabilizer quotient.) Let $H$ be a subgroup of $\mathrm{Aut}(T)$ mapping $C \subseteq B$ onto
itself, choose one base state of $C$ from each $H$-orbit, and call a base state of $B$ chosen if its
restriction to $C$ is chosen. Then some chosen base state of $B$ extends to a witness. If every element
of $H$ fixes each representative of (b), or of (c), then that witness can also be taken to satisfy (b),
or (c), respectively.*

We call a witness satisfying (b) or (c) *anchored*. Sorting the voters (part (d)) is built into the
definition of a base state and divides their number by almost $120$. Anchoring discards base states
outright when every representative lies in $B$, leaving $2{,}591$ of the $8{,}031$ *live* on a Paley
tournament, and otherwise it prunes during the search. The quotient (e) divides the work by up to $|H|$. The two combine when $H$ fixes every representative, so we take $H$ to be their common stabilizer,
and together they use all of $\mathrm{Aut}(T)$ (Table @tbl:group-use).

### The placement search {#sec:algorithm}

The search maintains a partial profile: a set $S \subseteq V$ of *placed* vertices together with, for
each voter, a linear order of $S$. It begins from a base state, which places $B$, and inserts one
unplaced vertex at a time. Inserting $v$ means choosing, for each voter independently, a slot among the
$|S| + 1$ available; the *domain* $D(v \mid S)$ is the set of $k$-tuples of slots consistent with every
arc between $v$ and $S$. A partial profile is extendable only if every unplaced vertex has a non-empty
domain, and domains shrink as $S$ grows. Algorithm @alg:placement gives the search, and
Figure @fig:paley7 (Appendix @sec:base-states) runs it on $P_7$ at $k = 3$. The base states are searched in
parallel; the verdict is positive as soon as one yields a witness, and negative only when every live
base state has been searched to exhaustion. The certified refutations of Appendix @app:certificates use the
same decomposition, handing each live base state to a conflict-driven clause-learning (CDCL) solver as a
*cube* (the partial assignment fixing the voters' rankings of $B$), so the two share their symmetry
reductions and differ only in what refutes a leaf.

### What makes the search fast {#sec:fast}

Five choices make the search fast; the second is the one that made $n = 19$ and $n = 23$ reasonable to
compute.

1. **A dynamic variable order.** At every node we insert the unplaced vertex of smallest domain (the
   minimum-remaining-values, or MRV, rule), breaking ties toward the vertex whose arcs to $S$ are most
   imbalanced. On Paley instances a static order is not competitive, because how constrained a vertex is
   depends strongly on which part of the tournament has already been placed.
2. **Incremental domain refinement.** A child's domains are derived from its parent's by `REFINE`, in time
   proportional to the surviving tuples rather than to the whole slot space, and they live in a
   stack-disciplined arena indexed by (depth, vertex), so that backtracking is a pointer reset. Like for
   like this is worth a factor of about $110$ in wall time.
3. **Symmetry reductions.** Base states are sorted and taken one per orbit of $H$, and the anchors are
   tested at every node once all representatives are placed (Section @sec:symmetry).
4. **Early termination and caching.** A per-voter agreement bound, counting the agreement between a voter
   and the arcs between $v$ and $S$ two ways, proves $D(v \mid S)$ empty in $O(k|S|)$ time without
   enumerating it. Base-state counts depend only on the arc pattern of $T[B]$, so they are reused across
   every copy of the same base class and across every $q$.
5. **Choosing the base.** The fewest live base states is not the fastest choice: at $q = 31$ the class
   with $4{,}007$ live states beat the one with $2{,}537$, whose states are individually slower, so we
   rank the twelve five-vertex classes by the live count times a sampled time per state.

```
ALGORITHM {#alg:placement}.  Placement search for k-inducibility of T

Input :  tournament T on V;  k voters;  margin (majority or unit);  base B
         Q: chosen base states of B    // Lem @lem:symmetry(d), (e): sorted, one per H-orbit
         R: anchoring representatives  // Lem @lem:symmetry(c), (b): vertices, pairs, or none
Output:  a witness profile, or a refutation

MAIN
  for each base state in Q  (a lex-canonical assignment of the base B to k orders):
      S <- B
      D(v | S) <- fresh enumeration, for every v not in S
      if any D(v | S) is empty:  continue     // this base state is dead
      if DFS(S) succeeds:        return its witness
  return "not k-inducible"                    // no base state extends

DFS(S)
  if S = V:  return the profile               // all vertices placed
  if every vertex of R is placed and no voter is anchored:
      return failure                          // Lem @lem:symmetry(b),(c); at the root if R is in B
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
          p_i <  q_i  ->  p'_i = p_i        // w stays before u
          p_i >  q_i  ->  p'_i = p_i + 1    // w stays after u, shifted by the insertion
          p_i == q_i  ->  BOTH are legal, so the tuple splits in two
      keep those lifts whose support  c_w(u) = #{ i : w before u }
      meets the requirement of the single new arc between w and u
  return D'
```

The next section reports what this search decides.

## Results {#sec:results}

In this section we present our results, first for the Paley tournaments and the other structured families, then for the eight obstructions on 22 vertices. Table @tbl:evidence in Appendix @sec:trust lists what each result rests on.

The two regimes we explore are *unrestricted* (or plain majority) inducibility, and *unit margin*. 
The former is the standard notion of inducibility, and the latter asks that
every arc be carried by exactly three voters against two. Only an unrestricted refutation bounds $N(5)$. 
However, the lemma below shows that for the Paley family and most tournaments derived from it, the 
unrestricted inducibility is equivalent to inducibility with margin at most $3$ (i.e. support at most 4).

We also use unit margin as a fast filter for unrestricted inducibility. A unit-margin witness is in
particular a majority witness, and the unit-margin search is much faster (Appendix @sec:runtimes), so when the
question is only whether a tournament is $5$-inducible we search at unit margin first and at plain
majority only if no unit-margin witness exists. The order-$12$ analysis of Appendix @app:order12 works this way, and so do several of
the family searches on $21$ vertices (Appendix @app:below22). A tournament that fails the filter but has a
majority witness is then a unit-margin obstruction found as a by-product, and several of those
reported below arose this way.

**Lemma []{#lem:three-cycle} (3-cycle bound).** *Let $u \to v \to w \to u$ be a directed triangle of $T$ and let
$\pi_1,\dots,\pi_k$ be any linear orders with $k$ odd. Then*
$$c(u\to v) + c(v \to w) + c(w \to u) \le 2k.$$
*Consequently, in any majority witness, no arc lying in a directed triangle has unanimous support $k$.*

*Proof.* A linear order cannot rank $u$ above $v$, $v$ above $w$ and $w$ above $u$ simultaneously,
so each voter agrees with at most two of the three arcs; summing over the $k$ voters gives the
inequality. If $c(u \to v) = k$, the other two supports sum to at most $k$, contradicting the
majority requirement that each be at least $(k+1)/2$. $\blacksquare$

For $k = 3$ the second conclusion is Proposition 1 of Milosz, Hamel and Pierrot (2018), with a transitivity
argument; we need it for every odd $k$, and in the summed form above.

### Paley(23) and Paley(31) are not 5-inducible {#sec:paley23-31}

**Theorem []{#thm:paley23}.** *$P_{23}$ is not $5$-inducible. Consequently $N(5) \le 23$.*

The proof is a search that runs to completion. The base is $\{1,2,3,6,12\}$, which induces the regular 
tournament on $5$ vertices and gives $8{,}031$ base states. They are reduced to $2{,}591$ by Lemma @lem:symmetry(b), 
by requiring one voter to rank either $(1,3)$ or $(1,6)$ as the first pair. None of them produces a witness. 
This statement is also formally certified in Appendix @sec:certified.

Thus none of the $23!^{5}$ five-voter profiles on $23$ vertices has $P_{23}$ as its majority tournament.
It is the first explicit tournament of order below $43$ shown not to be $5$-inducible, and the first
whose non-inducibility a general-purpose solver could not settle.

The same method settles a larger case: $P_{31}$ is not $5$-inducible, over $21{,}009$ base states with 
a different base, reduced to $4{,}007$ by Lemma @lem:symmetry(b). Appendix @sec:runtimes shows how the runtime scales in $q$,
and Appendix @sec:runtimes tabulates the cost of every computation in this paper.
Settling $P_{31}$ shows that our search decides $31$-vertex instances on a single laptop within a day, which the SAT and ILP solvers we tried did not.

Arc-criticality implies vertex-criticality: reversing an arc incident to $v$ leaves $T - v$
unchanged, and the restriction of a witness to $V \setminus \{v\}$ is a witness for $T - v$. Each cell of Table @tbl:criticality therefore records only the *strongest* property established, at each of the two margins. 
"Not vertex-critical" also rules out arc-criticality.

| $q$ | unit margin | unrestricted |
|---|---|---|
| 19 | **arc-critical** | $5$-inducible, so criticality does not apply |
| 23 | not vertex-critical | **arc-critical** (Section @sec:paley23-critical) |
| 31 | not vertex-critical | **not vertex-critical** (Section @sec:paley23-critical) |
| 43 | not vertex-critical | **not vertex-critical** (Section @sec:paley23-critical) |

Table: The strongest criticality property established for each Paley tournament, at each margin. {#tbl:criticality .natural}

$P_{19}$ is the only member critical at unit margin, and it is critical in the
strongest sense: reversing any one arc makes it unit-margin inducible, which by the implication also
gives vertex-criticality. At the other end, $P_{31}$ and $P_{43}$ fail to be vertex-critical at
*both* margins. The interesting cell is $q = 23$: it is *vertex-critical unrestricted*, 
but *not* vertex-critical at unit margin. That is, $P_{23} -\,v$ is 5-inducible, but not with unit 
margin.

### Paley(19) is not 5-inducible with unit margin {#sec:paley19}

That $P_{19}$ is $5$-inducible is due to Bachmeier et al. (2019). Our search recovers it independently and contributes the negative half: it is *not* 
$5$-inducible with unit margin. This is a complete refutation over all $2{,}200$ base states of the base 
$\{1,2,3,4,6\}$, and it is the second statement we certify formally in
Appendix @sec:certified. These two facts supply the separation in Section @sec:intro: no arc of $P_{19}$ can be unanimous, by the
$3$-cycle bound above, so it is $5$-inducible with margin at most $3$ and not with unit margin.

### Paley(23) is arc-critical, unlike Paley(31) and Paley(43) {#sec:paley23-critical}

**Theorem []{#thm:arc-critical}.** *$P_{23}$ is arc-critical, and hence vertex-critical.*

As $\mathrm{Aut}(P_{23})$ is transitive on arcs, it suffices to reverse the arc $(1,2)$. The result,
$T^{e}$, is rigid, so the search scans all $8{,}031$ base states without anchoring, and the witness it finds
is checked independently: its five orders are permutations of the $23$ vertices whose majority tournament
agrees with $T^{e}$ on all $253$ arcs. The two notions come apart among the four vertex-transitive
unit-margin obstructions on $21$ vertices: all four are vertex-critical, but two have every arc critical,
one exactly half and one none (Appendix @app:criticality21).

**Theorem []{#thm:not-vertex-critical}.** *Neither $P_{31}$ nor $P_{43}$ is vertex-critical for 5-inducibility.*

*Proof.* $\mathrm{Aut}(P_{q} - v)$ is the stabilizer of $v$ in $\mathrm{Aut}(P_{q})$: an automorphism of
$P_q - v$ preserves its two out-degrees, $(q-1)/2$ on $N^{+}(v)$ and $(q-1)/2 - 1$ on $N^{-}(v)$, hence those
two sets, and so extends to $P_q$ by fixing $v$. With $v = 0$ the stabilizer is
$\{x \mapsto ax : a \in \mathrm{QR}\}$, whose vertex orbits are $\mathrm{QR}$ and its complement, so vertex
anchoring (Lemma @lem:symmetry(c)) applies with one representative from each. Every arc of $P_q - v$ lies
in at least $(q-3)/4$ directed triangles, so by Lemma @lem:three-cycle margin at most $3$ is no restriction,
and a complete search at that margin over all $8{,}031$ base states of a five-vertex base inducing the
regular tournament on five vertices, $\{1,2,3,4,13\}$ in $P_{31} - v$ and $\{1,2,3,4,11\}$ in
$P_{43} - v$, finds no witness. $\blacksquare$

This reconfirms Theorem @thm:paley43 independently, since a witness for $P_{43}$ would restrict to one for
$P_{43} - v$.

### Other structured tournament families {#sec:families}

Beyond the Paley family we swept the structured families catalogued by McKay (2026) exhaustively for
$n < 23$, and two families of order $23$ completely; Table @tbl:families gives the verdicts. A tournament
is *locally transitive* if every in- and out-neighbourhood induces a transitive subtournament.

| family | order | unrestricted | unit margin |
|:------------------------------------|:---------|:----------------------|:----------------------------------|
| vertex-transitive | $n < 23$ | all inducible | all but $P_{19}$ and $4$ of $110$ at $n = 21$ |
| those $4$, one arc reversed | $21$ | all $40$ inducible | — |
| doubly regular | $19$ | both inducible | neither inducible |
| regular | $\le 15$ | all inducible | all inducible |
| self-converse | $\le 13$ | all inducible | all inducible |
| vertex-transitive, not $P_{23}$ | $23$ | all inducible | — |
| doubly regular | $23$ | none of the $37$ | none of the $37$ |
| locally transitive | any | all inducible | all inducible, for every odd $k$ |

Table: Verdicts for five voters on the structured families; a dash marks a regime we did not settle. The arc reversals are one per arc orbit. {#tbl:families}

Since only an unrestricted refutation can move $N(5)$, the vertex-transitive family is closed as a
source of candidates below $23$ vertices. The other doubly regular tournament on $19$ vertices is
arc-critical at unit margin like $P_{19}$: its $171$ arcs fall into $57$ orbits of size $3$, and reversing
a representative of each yields a tournament with a unit-margin witness, $57$ orbits and $57$ witnesses.
The searches over the $R_{15} = 18{,}400{,}989{,}629$ regular tournaments on $15$ vertices and the
$S_{13} = 95{,}458{,}560$ self-converse ones on $13$ vertices cover these counts in full. Every
vertex-transitive tournament on $23$ vertices other than $P_{23}$ is $5$-inducible, while none of the $37$ doubly regular ones is, at unit margin or unrestricted; up to converse they form $19$ classes,
each settled by a complete search (Appendix @sec:runtimes). We do not search McKay's locally transitive
tournaments: our companion paper shows that all are $k$-inducible with unit margin for every odd $k \ge 3$.

Taken together with the Paley results above and the families of Appendix @app:below22, these searches turn up
$75$ tournaments, up to isomorphism and converse, that five voters can produce but not with unit
margin: $2$ doubly regular ones at order $19$; at order $21$, $3$ vertex-transitive ones (the four of
Section @sec:paley23-critical, two of which are converses of each other), $15$ arc reversals of two of them (Appendix @app:criticality21) and $42$ near-doubly regular ones (Appendix @app:below22); at order $22$, $P_{23} - v$; and at order $23$, $11$ circulant ones and $P_{23}$ with one arc reversed.

### Eight tournaments on 22 vertices are not 5-inducible {#sec:twenty-two}

None of the $37$ doubly regular tournaments on $23$ vertices in the catalogue of McKay (2026) is
$5$-inducible (Table @tbl:families), which makes their one-vertex deletions natural candidates. We write
$\Delta_i$ for the $i$-th, with vertices $v_1, \dots, v_{23}$ in the catalogue's labelling, and
$\Delta_i - v_j$ for $\Delta_i$ with $v_j$ deleted.

**Theorem []{#thm:twenty-two}.** *The tournaments $\Delta_1 - v_{1}$, $\Delta_1 - v_{2}$, $\Delta_1 - v_{10}$, $\Delta_6 - v_{5}$,
$\Delta_{11} - v_{2}$, $\Delta_{11} - v_{5}$, $\Delta_{11} - v_{20}$ and $\Delta_{28} - v_{5}$, on $22$ vertices, are
not $5$-inducible.
In particular, no tournament obtained from $\Delta_1$ by deleting one vertex is $5$-inducible.
Consequently $N(5) \le 22$.*

The second statement holds because $\mathrm{Aut}(\Delta_1)$, of order $55$, has three vertex orbits, of
sizes $11$, $11$ and $1$, containing $v_1$, $v_2$ and $v_{10}$. The eight are pairwise non-isomorphic, even
up to converse, and each has eleven vertices of out-degree $10$ and eleven of out-degree $11$; every arc
lies in at least five directed triangles, so by the $3$-cycle bound no arc of a witness is unanimous.
Appendix @app:obstructions22 gives their adjacency matrices.

Deleting a vertex $v$ of a doubly regular tournament on $23$ vertices leaves two regular *halves* on $11$
vertices, $N^{+}(v)$ and $N^{-}(v)$, each out-neighbour of $v$ beating $6$ in-neighbours and each in-neighbour
$5$ out-neighbours. We call $v$ a *bisector* if its halves are isomorphic, or converse, to each other (an
*isomorphic* or a *converse* bisector), and a tournament *bisectable* if it has a bisector or arises from
one by deleting a bisector; one tournament on half the vertices then fixes both halves, which makes
bisectable tournaments much easier to enumerate. Every doubly regular tournament on at most $23$ vertices
is bisectable, whereas $118$ of the $722$ on $27$ vertices are not. Our obstructions cover every case. In
$\Delta_1 - v_{10}$ and $\Delta_{11} - v_{20}$ both halves are $P_{11}$; in the four other deletions of $\Delta_1$ and
$\Delta_{11}$ they are isomorphic to each other and to each other's converse, with automorphism groups of
order $5$; in $\Delta_{28} - v_{5}$ they are converses of each other, with trivial automorphism groups; and in
$\Delta_6 - v_{5}$ they are neither, and no other split works, so $\Delta_6 - v_{5}$ is non-bisectable.

Figure @fig:ladder shows $\Delta_1 - v_{10}$ as two copies of $P_{11}$ on $X = \{x_0, \dots, x_{10}\}$ and
$Y = \{y_0, \dots, y_{10}\}$ joined by a ladder. Its automorphism group, of order $55$, has vertex orbits $X$
and $Y$, and the automorphisms multiplying every index by a non-zero square fix $x_0$ and $y_0$ and form a
subgroup $H$ of order $5$ mapping $B = \{x_1, x_3, x_4, x_5, x_9\}$, the out-neighbours of $x_0$ in $X$,
onto itself. $B$ induces the regular tournament on five vertices, whose $8{,}031$ base states $H$ groups into
$1{,}611$ orbits, so Lemma @lem:symmetry(e) keeps one per orbit while anchoring on $x_0$ and $y_0$
(Lemma @lem:symmetry(c)); the complete search over the $1{,}611$ finds no witness. The certificate
(Appendix @sec:certified) uses the quotient without anchoring on $B' = \{y_1, y_3, y_4, y_5, y_9\}$, the
in-neighbours of $y_0$ in $Y$, again keeping $1{,}611$ of the $8{,}031$. The other five deletions with an
automorphism group of order $5$, two of $\Delta_1$ and the three of $\Delta_{11}$, whose group fixes $v_2$, $v_5$
and $v_{20}$, are refuted in the same way over $1{,}611$ chosen base states each, without certificates.
$\Delta_6 - v_{5}$ and $\Delta_{28} - v_{5}$ have trivial automorphism groups, so their searches cover all
$8{,}031$ base states; $\Delta_6 - v_{5}$ is also certified (Appendix @sec:certified).

All eight obstructions are *vertex-critical*, so none yields a $21$-vertex obstruction by a further
deletion, and the wider search below $22$ vertices (Appendix @app:below22) has found none.

**A ninth obstruction.** The $231$ arcs of $\Delta_1 - v_{10}$ fall into five orbits: inside $X$, inside $Y$,
the rungs $y_i \to x_i$, the other arcs from $Y$ to $X$, and the arcs from $X$ to $Y$. Reversing a rung yields
a $5$-inducible tournament, but reversing an arc $y_j \to x_i$ with $j - i \in \mathrm{QR}$ does not: the
result is rigid, and a complete search over all $8{,}031$ base states finds no witness. This ninth
obstruction is not isomorphic to any of the eight or to their converses, and it is vertex-critical:
deleting an endpoint of the reversed arc leaves a deletion of $\Delta_1 - v_{10}$, and the other $20$
deletions have explicit witnesses. Whether reversing an arc of the remaining three orbits restores
$5$-inducibility is open, as is the arc-criticality of the other seven; Section @sec:discussion collects the
open questions.

## Discussion and open problems {#sec:discussion}

In this section we state the questions that our results leave open (Section @sec:open) and describe how
every result can be reproduced (Section @sec:reproducibility).

### Conjectures and open problems {#sec:open}

**Question []{#quest:n5-22}.** *Is $N(5) = 22$, that is, is every tournament on $21$ vertices $5$-inducible?*

The first version of this paper (arXiv:2609.13924v1), whose upper bound was $N(5) \le 23$,
conjectured that $N(5) = 23$. The obstructions of Section @sec:twenty-two refute that
conjecture, so we pose the question one order lower.

Both ends of $13 \le N(5) \le 22$ are constructive, unlike the counting bound of Section @sec:bounds. The unit-margin
obstructions at $n = 19$ and $21$ cannot move the upper one, since every one of them is
majority-inducible. The evidence below $22$ comes mostly from the descendants of the doubly regular
tournaments on $23$ vertices (Appendix @app:below22): every tournament on $20$ vertices obtained from one of them
by deleting three vertices is $5$-inducible, and so is every one on $21$ vertices below any of the
nine $22$-vertex obstructions.

Every class we searched below $22$ vertices was chosen because
symmetry, a construction, or descent from a known obstruction made it searchable, and Appendix @app:below22
lists them all. These classes cluster around the doubly regular tournaments, where every obstruction
we know of lies. What they show is that no obstruction on $21$ vertices lies *among them*; they say
little about the roughly $3 \times 10^{43}$ tournaments on $21$ vertices.

**Conjecture []{#conj:paley}.** *$P_{q}$ is not $5$-inducible for any eligible prime $q \ge 23$, i.e. $q \equiv 3 \pmod 4$.*

It holds at $q = 23$, $31$ and $43$, and only finitely many $q$ are in doubt:
$\alpha^{*}(P_q) = \mathrm{MAS}(P_q)/C$ tends to $1/2$, because Paley tournaments are
quasi-random in the sense of Chung and Graham (1991, Section 6), and one of their equivalent quasi-random properties ($P_9$) is that every linear order of the vertices agrees with $(1/2 + o(1))\binom{q}{2}$ arcs. Hence the predictability eventually falls
below $3/5$, past which the necessary condition $\alpha^{*} \ge 3/5$ refutes $5$-inducibility with
no search at all. What is missing is a bound on where that range ends; the values in Table @tbl:paley-family fall
too irregularly to extrapolate one.

**Open problem []{#prob:criticality} (vertex- and arc-criticality).** Whether $P_{q}$ minus *two* vertices is $5$-inducible,
equivalently whether $P_{q}$ minus one vertex is vertex-critical, is open at $q = 31$ and $q = 43$. For $q = 43$,
$P_{43} - 2v$ is unique up to isomorphism, since $\mathrm{Aut}(P_{43})$ acts transitively on unordered pairs of
vertices, and the screen of Section @sec:screen extends to it. The two deleted vertices can be chosen after the
screen rather than before: a pair of orders survives the deletion exactly when some set of at most two
vertices meets every cyclic triangle that both orders double-back, a property invariant under
$\mathrm{Aut}$, so the reduction by a factor of $903$ survives the deletion. The condition on the two
voters that agree with the most arcs sharpens to $\delta_1 + 4 \delta_2 \le 5\,\mathrm{MAS} - 3C$, where
$\delta_1, \delta_2$ are their levels; the right-hand side is $45$ for $P_{43} - 2v$.

**Open problem []{#prob:margin-hierarchy} (the margin hierarchy).** The first of unit margin $\subseteq$ margin $\le 3$ $\subseteq$
unrestricted is strict (Sections @sec:paley19 and @sec:families); whether the second ever is, that is, whether some
tournament is inducible by five voters but not at margin $\le 3$, is open. Lemma @lem:three-cycle forces
such a tournament to have an arc in *no* directed triangle, which rules out every regular tournament.
Conjecture 8.1 of our companion paper states that the inclusion is strict at every odd $k > 3$.

**Conjecture []{#conj:unit-margin-k2}.** *For every odd $k$, every $k$-inducible tournament is
$(k+2)$-inducible with unit margin.*

Conjecture @conj:unit-margin-k2 extends Conjecture 8.1 of our companion paper, which concerns the classes for a
single $k$, to classes across different $k$. Adding an order together with its reverse raises every support by one, so $k$-inducibility with
margin at most $M$ implies $(k+2)$-inducibility with margin at most $M$. Conjecture @conj:unit-margin-k2 strengthens
this to unit margin, and with the inclusions within each $k$ it would nest every class at a lower
$k$ inside every class at a higher $k$, whatever the margins. It trivially holds at $k = 1$, since a
transitive tournament is the majority of an order taken twice and its reverse once, with every arc
carried two against one. At $k = 3$, Appendix @app:order12 shows that every tournament on at most $12$
vertices is $5$-inducible with unit margin, so a counterexample needs at least $13$ vertices. At
$k = 5$, both doubly regular tournaments on $19$ vertices, which are $5$-inducible but not with unit
margin, are $7$-inducible with unit margin.

### Reproducibility {#sec:reproducibility}

The code, data and verdict files are at
`https://github.com/Leonardini/TournamentsBeyond5Voters`. Its `CLAIMS.md` carries one row per
statement made here, naming the artifact that holds the verdict and the command that re-derives
it, and it ends with an explicit list of what the package does not establish. A permanent archive
of the accepted version will be deposited on acceptance, with its DOI recorded here.

The repository contains the search engine as a single C translation unit, the SAT encoding and
cube tooling in Python, the certification driver, the independent witness verifiers, the
tournaments as bit strings, and a verdict record for every result reported here. Each verdict
records the exact command line, the base and break used, the coverage audit (the check that the cubes miss no base state, Appendix @sec:trust), the runtime, and the two 
root hashes for the formally certified results. Three further folders hold the counting bounds (`counting_bounds/`), the proof for $P_{43}$, which rebuilds from one script (`paley43/`), and
every check that the tournaments on at most $12$ vertices are $5$-inducible with unit margin
(`n12_unit_margin/`). The last ships explicit profiles for the non-3-inducible tournaments on $8$ and $9$ vertices;
at larger orders the same code regenerates them, for a single tournament in milliseconds and for all
tournaments of an order in minutes at $n = 10$, in about $44$ core-hours at $n = 11$ and in $2{,}616$ cluster core-hours at $n = 12$.

Of the two root hashes published with each certified computation, ROOT (CNF) commits to the SHA-256 of
every cube's CNF and must be reproduced exactly by anyone who regenerates the cube set, whereas ROOT
(proofs) also commits to the LRAT proof bytes, which depend on the solver build, so a mismatch there is
not evidence of an error. A rerun of both refutations on a compute cluster, under a different compiler and
CaDiCaL build, matched both CNF roots, and both coverage instances rebuilt to their committed CNF
hashes and were refuted again. Search verdicts replicate under any correct implementation, node
counts replicate exactly when the tie-breaking rule, the vertex numbering, the base and the margin are
held fixed (the engine prints all but the numbering on every run, and the repository stores the
tournaments themselves), and core-hours replicate only in order of magnitude (Appendix @sec:runtimes).

## Declaration of competing interest {-}

The authors declare that they have no known competing financial interests or personal relationships
that could have appeared to influence the work reported in this paper.

## Funding {-}

LC acknowledges funding from the MRC Centre for Global Infectious Disease Analysis (reference
MR/X020258/1), funded by the UK Medical Research Council (MRC). This UK funded award is carried
out in the frame of the Global Health EDCTP3 Joint Undertaking.

## CRediT authorship contribution statement {-}

**Leonid Chindelevitch:** Conceptualization, Methodology,
Software, Formal analysis, Investigation, Writing – original draft, Writing – review and editing.
**Ararat Harutyunyan:** Conceptualization, Formal analysis, Writing – review and editing.

## Data availability {-}

The code, data and verdict files supporting the findings of this study are at
`https://github.com/Leonardini/TournamentsBeyond5Voters`, described in Section @sec:reproducibility.

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process {-}

During the preparation of this work the authors used Claude (Anthropic) for exploratory reasoning,
implementation assistance, and drafting and editing. After using this tool, the authors reviewed and
edited the content as needed and take full responsibility for the content of the published article.

## Acknowledgements {-}

This work was granted access to the HPC resources of IDRIS under the allocation
2025-AD010616623R1 made by the Grand Équipement National de Calcul Intensif (GENCI).

## References {-}

Bachmeier G, Brandt F, Geist C, Harrenstein P, Kardel K, Peters D, Seedig HG (2019) $k$-Majority
digraphs and the hardness of voting with a constant number of voters. *Journal of Computer and
System Sciences* 105:130–157

Biere A, Faller T, Fazekas K, Fleury M, Froleyks N, Pollitt F (2024) CaDiCaL 2.0. In: *Computer Aided Verification (CAV 2024)*, LNCS 14681, Springer, pp 133–152. doi:10.1007/978-3-031-65627-9_7

Brakensiek J, Heule M, Mackey J, Narváez D (2020) The resolution of Keller's conjecture. In:
*Automated Reasoning (IJCAR 2020)*, LNCS 12166, Springer, pp 48–65

Chindelevitch L, Harutyunyan A (2026) Tournaments not inducible by three voters. Submitted to
*Mathematical Social Sciences* jointly with this paper

Chung FRK, Graham RL (1991) Quasi-random tournaments. *Journal of Graph Theory* 15(2):173–198

Cruz-Filipe L, Heule MJH, Hunt WA Jr, Kaufmann M, Schneider-Kamp P (2017) Efficient certified RAT
verification. In: *Automated Deduction (CADE 2017)*, LNCS 10395, Springer, pp 220–236

Cruz-Filipe L, Marques-Silva J, Schneider-Kamp P (2019) Formally verifying the solution to the
Boolean Pythagorean triples problem. *Journal of Automated Reasoning* 63(3):695–722.
doi:10.1007/s10817-018-9490-4

Dummit DS, Foote RM (2004) *Abstract Algebra*, 3rd edn. Wiley, Hoboken, NJ

Dushnik B, Miller EW (1941) Partially ordered sets. *American Journal of Mathematics* 63(3):600–610

Eggermont C, Hurkens C, Woeginger GJ (2013) Realizing small tournaments through few permutations.
*Acta Cybernetica* 21(2):267–271

Erdős P, Moser L (1964) On the representation of directed graphs as unions of orderings. *Publications of the Mathematical Institute of the Hungarian Academy of Sciences* 9(1–2):125–132

Fidler D (2011) A recurrence for bounds on dominating sets in $k$-majority tournaments. *The Electronic Journal of Combinatorics* 18(1):#P166. doi:10.37236/653

Fiol MA (1992) A note on the voting problem. *Stochastica* 13(1):155–158

Held M, Karp RM (1962) A dynamic programming approach to sequencing problems. *Journal of the Society for Industrial and Applied Mathematics* 10(1):196–210. doi:10.1137/0110015

Heule MJH, Kullmann O, Marek VW (2016) Solving and verifying the Boolean Pythagorean triples problem
via cube-and-conquer. In: *Theory and Applications of Satisfiability Testing (SAT 2016)*, LNCS 9710,
Springer, pp 228–245

Heule MJH, Kullmann O, Wieringa S, Biere A (2012) Cube and conquer: guiding CDCL SAT solvers by
lookaheads. In: *Haifa Verification Conference (HVC 2011)*, LNCS 7261, Springer, pp 50–65

Heule MJH (2018) Schur number five. In: *Proceedings of the AAAI Conference on Artificial
Intelligence (AAAI 2018)*, pp 6598–6606

Kahn AB (1962) Topological sorting of large networks. *Communications of the ACM* 5(11):558–562. doi:10.1145/368996.369025

McGarvey DC (1953) A theorem on the construction of voting paradoxes. *Econometrica* 21(4):608–610

McKay BD (2026) Combinatorial data: digraphs (tournament catalogues). Accessed 10 August 2026.
`https://users.cecs.anu.edu.au/~bdm/data/digraphs.html`

McKay BD, Piperno A (2014) Practical graph isomorphism, II. *Journal of Symbolic Computation*
60:94–112

Milosz R, Hamel S, Pierrot A (2018) Median of 3 permutations, 3-cycles and 3-hitting set problem.
In: *Proceedings of IWOCA 2018*, LNCS 10979, Springer, pp 224–236.
doi:10.1007/978-3-319-94667-2_19

OEIS Foundation Inc. (2026a) Entry A000568, Number of outcomes of unlabeled $n$-team round-robin
tournaments. The On-Line Encyclopedia of Integer Sequences. `https://oeis.org/A000568`

OEIS Foundation Inc. (2026b) Entry A002785, Number of self-complementary oriented graphs with $n$
nodes. The On-Line Encyclopedia of Integer Sequences. `https://oeis.org/A002785`

OEIS Foundation Inc. (2026c) Entry A096368, Number of unlabeled regular tournaments with $2n+1$
nodes. The On-Line Encyclopedia of Integer Sequences. `https://oeis.org/A096368`

Pollitt F, Fleury M, Biere A (2023) Faster LRAT checking than solving with CaDiCaL. In: *Theory and
Applications of Satisfiability Testing (SAT 2023)*, LIPIcs 271, pp 21:1–21:12.
doi:10.4230/LIPIcs.SAT.2023.21

Schrijver A (1983) Bounds on the number of Eulerian orientations. *Combinatorica* 3(3–4):375–380. doi:10.1007/BF02579193

Shepardson D, Tovey CA (2009) Smallest tournaments not realizable by $2/3$-majority voting.
*Social Choice and Welfare* 33(3):495–503. doi:10.1007/s00355-009-0375-7


## The order-12 case analysis {#app:order12 .appendix}

Every tournament on $12$ vertices is $5$-inducible, so $N(5) \ge 13$. This appendix describes that
computation, which starts from a census of order $11$. It is one of the results in this paper that was not run on the laptop of Section @sec:results: it ran
on a shared cluster, and its runtime is converted as Appendix @sec:runtimes describes.

### Every tournament on eleven vertices is 5-inducible {#sec:eleven}

Our first census shows that every tournament on at most $11$ vertices is $5$-inducible, so $N(5) \ge 12$. Through
$n = 10$ each tournament is decided by the integer program of Appendix @sec:ip-sat-slow. At $n = 11$ no integer program was
needed: of the $D_{11} = 903{,}753{,}248$ tournaments, $382{,}625{,}248$ are 3-inducible by the triple-local test of our
companion paper, and
every one of the remaining $521{,}128{,}000$ admits a *unit-margin* five-voter profile, found by a constraint search and
re-checked independently. A tournament with a non-3-inducible subtournament is itself non-3-inducible, and
restricting a profile to a subset of the vertices preserves every pairwise split, so every non-3-inducible tournament on
at most $11$ vertices is $5$-inducible with unit margin.

### Reduction to one-vertex extensions {#sec:extensions}

A direct census is out of reach: $D_{12} \approx 1.5 \times 10^{11}$ classes, $170$ times the
order-$11$ census of Appendix @sec:eleven. We use that census as the outer loop. We write $L + S$ for the 
tournament obtained from an order-$11$ tournament $L$ by adding a vertex $v$
whose out-neighbourhood is $S \subseteq V(L)$. Two observations simplify the analysis.

**(i)** Every order-$12$ tournament is $L + S$ for some order-$11$ $L$ and some $S$.

**(ii)** Restricting a profile that realizes $L + S$ to $V(L)$ gives a profile that realizes $L$.

By (i), enumerating all $D_{11}$ order-$11$ classes and settling all $2{,}048$
extensions of each settles every order-$12$ tournament; all of the former are $5$-inducible by the
census of Appendix @sec:eleven, which is what makes the outer loop available. By (ii), a
profile realizing $L + S$ may be sought by *inserting* $v$ into a profile realizing $L$ with no
loss of generality, since every profile for $L+S$ arises that way. That is what phase 1 uses.

### Three phases {#sec:phases}

The census runs in three phases, fastest first.

**Phase 1, the covering search.** Rather than $2{,}048$ separate instances per order-$11$ tournament, one 
search enumerates profiles realizing $L$ *at unit margin* and, for each, records every
out-neighbourhood obtainable by inserting $v$ into its five orders: $v$'s position in each order is a threshold, and the support of $v \to u$ 
is the number of orders that place $v$ above $u$, so one traversal certifies many extensions at once. This
is the engine of Section @sec:algorithm with $v$'s placement read off rather than fixed in advance. The
margin makes this phase pay twice: it keeps the enumeration of profiles for $L$ small, and a
unit-margin witness is in particular a majority witness, so every extension the phase covers is
settled in both regimes at once. The phase is one-sided: an extension it covers is certified $5$-inducible, but one left over is not refuted.
This phase settles every one of the $2{,}048$ extensions of $99.5\%$ of the order-$11$
tournaments.

**Phase 2, deciding what is left.** Each extension phase 1 leaves open is materialized as an order-$12$
tournament $L + S$ and decided by the same engine, again at unit margin, where a witness
settles it positively. About one extension in $200{,}000$ reached this phase, and every one of
them is $5$-inducible with unit margin.

**Phase 3, plain majority.** Only a *majority* refutation would be a counterexample, so any
instance negative at unit margin is re-run without the margin restriction. Phase 3 was never
invoked: every tournament was settled at unit margin, so the weaker question never had to be asked.

### One tournament of each converse pair {#sec:converse-pairs}

$T$ is $5$-inducible if and only if its converse $\bar{T}$ is (Section @sec:intro). Moreover
$\overline{L + S} = \bar{L} + (V(L) \setminus S)$, so settling all $2{,}048$ extensions of $L$ settles
all $2{,}048$ of $\bar{L}$ as well. We therefore keep one tournament of each converse pair, by the
rule that $L$ is kept if and only if $\mathrm{canon}(L) \le \mathrm{canon}(\bar{L})$. This keeps
exactly one of each pair together with every self-converse tournament, $(D_{11} + S_{11})/2$ in all,
with $S_{11} = 279{,}968$; this saves a factor of
$\lessapprox 2$. We also check the number of tournaments kept is $(D_{11} + S_{11})/2$.

Total runtime: $2{,}615.6$ core-hours. The search code, the per-part
records and the roll-up are at `n12_unit_margin/n12_cover` in the 
repository of Section @sec:reproducibility.

## The formal certificates {#app:certificates}

In this appendix we describe how the four certified negative results are proved (Appendix @sec:certified) and what the certificates do and do not establish (Appendix @sec:trust).

### The certified refutations {#sec:certified}

The four certified refutations follow an established design, and we claim no methodological novelty.
*Cube-and-conquer* (Heule, Kullmann, Wieringa and Biere 2012) splits a hard instance into partial
assignments, the *cubes*, each handed to a CDCL solver; the standard of proof is that of the Boolean
Pythagorean triples problem (Heule et al. 2016), later re-checked with a formally verified checker
(Cruz-Filipe et al. 2019), of Schur number five (Heule 2018) and of the Keller conjecture (Brakensiek
et al. 2020), in which every cube's refutation is validated by an independent checker. Each cube is
refuted by CaDiCaL 2.0.0 (`--lrat=true --checkproof=0`), which writes an LRAT proof (Cruz-Filipe et al.
2017): each derived clause lists the earlier clauses it follows from, so `lrat-trim` (Pollitt et al. 2023)
checks it without search. Our cubes are base states, a combinatorial decomposition, so the coverage of
the cube set is certified separately (Appendix @sec:trust). Where Heule et al. (2016) published a cube
certificate from which the refutations can be regenerated, at about $13{,}000$ core-hours to regenerate
and $16{,}000$ to check, we *verify and discard*: each LRAT proof is checked, hashed and deleted, and
only the hash is published (Section @sec:reproducibility). Table @tbl:certificates summarizes the four
certificates.

| refutation | base | cubes solved | core-hours | coverage |
|:----------------------|:----------------------|:----------------------------|---------:|---------:|
| $P_{19}$, unit margin | $\{1,2,3,4,5,12\}$ | $22{,}876$ of $142{,}251$ | $25.1$ | $7.56$ s |
| $P_{23}$ | $\{1,2,3,4,6,7\}$ | $343{,}896$ of $3{,}414{,}729$ | $236.0$ | $20$ min |
| $\Delta_6 - v_{5}$ | $\{1,2,3,4,13,19\}$ | all $742{,}374$ | $1{,}292.7$ | $82.8$ s |
| $\Delta_1 - v_{10}$ | $\{13,15,16,20,22\}$ | $1{,}611$ of $8{,}031$ | $\approx 732$ | $0.08$ s |

Table: The four certified refutations. The cubes solved are those left by the arc-orbit breaks ($P_{19}$, $P_{23}$) or the quotient ($\Delta_1 - v_{10}$); bases are in each tournament's labelling; core-hours cover solving and checking; the last column is the time to solve the coverage instance. {#tbl:certificates}

For $P_{19}$ at unit margin the dissent-Boolean encoding of Appendix @sec:ip-sat-slow has $855$ variables and $12{,}255$ clauses;
for $\Delta_6 - v_{5}$ and $\Delta_1 - v_{10}$ it is taken at $n = 22$ and plain majority: $1{,}155$ variables and $17{,}710$ clauses. The coverage half is a single unsatisfiable instance that negates every base state,
since coverage must see all of them whereas the orbit breaks apply only to the search half. For
$P_{23}$ it has $350$ constraint
clauses, $356$ symmetry-breaking clauses and $3{,}414{,}729$ negated cubes, and its LRAT proof takes
$2.05$ GiB; for $\Delta_6 - v_{5}$ it is the same construction with
$742{,}374$ negated cubes. $\Delta_6 - v_{5}$ is the most expensive certificate although it is smaller
than $P_{23}$: with no automorphisms every base state reaches the solver, against one in ten for $P_{23}$.

### What the certificates do and do not establish {#sec:trust}

The trust chain has five links:

| link | status |
|----------------------------------------------------------|----------------------------------------------------|
| every live cube is unsatisfiable | machine-checked: CaDiCaL, then `lrat-trim` |
| the cubes cover every lex-canonical base assignment | machine-checked: LRAT, verified by `lrat-trim` |
| (L1) orbit anchoring loses no generality | human-checked: Lemma @lem:symmetry(b) |
| (L2) lex-ordering the voters loses no generality | human-checked: Lemma @lem:symmetry(d) |
| (L3) one base state per orbit loses no generality | human-checked: Lemma @lem:symmetry(e) |

Table: The five links of the trust chain. {#tbl:trust-chain}

Appendix @sec:symmetry-details proves the human-checked links, which nothing in the pipeline checks. $P_{19}$
and $P_{23}$ use (L1) and (L2), $\Delta_1 - v_{10}$ uses (L2) and (L3), and $\Delta_6 - v_{5}$ uses (L2)
alone. Table @tbl:evidence says what decided each result and what independent check, if any, stands
behind it. A negative verdict from the depth-first engine alone rests on the engine's correctness; a
positive one never does, as a separate program checks each witness.

| result | decided by | independent check |
|:------------------------------|:-----------------------|:------------------------|
| $P_{23}$ | engine, twice | LRAT certificate |
| $\Delta_1 - v_{10}$, $\Delta_6 - v_{5}$ | engine | LRAT certificate |
| $P_{19}$, at unit margin | engine | LRAT certificate |
| the other $22$-vertex obstructions | engine | none |
| $P_{27}$, $P_{31}$, $P_{31} - v$ | engine | none |
| $P_{43}$ | proof, two programs | $P_{43} - v$, by the engine |
| all orders $\le 11$ inducible | ILP, constraint search | verifier, per profile |
| all of order $12$ inducible | extension search | check inside the search |
| positive results of Section @sec:results | engine | verifier, per witness |
| counting bounds | proof | none needed |

Table: What each result rests on. The first six rows are refutations (not $5$-inducible, at unit margin where stated);
"engine" is the depth-first search of Appendix @app:engine, run twice on $P_{23}$ with different bases and anchors,
and a verifier, sharing no code with the search, checks a profile's majority tournament against the target. {#tbl:evidence}

## The search below 22 vertices {#app:below22}

This appendix summarizes the search for an obstruction on fewer than $22$ vertices, which would
improve the upper bound of Section @sec:twenty-two. It has found none.

The search runs downward, because $5$-inducibility is inherited by subtournaments: restricting a
witness for $T$ to a subset of the vertices gives a witness for the subtournament. An obstruction on
fewer vertices therefore lies below some larger one, and the natural place to look is among the
vertex deletions of known obstructions. A tournament is settled positively as soon as one base state
yields a witness, which is cheap, and negatively only by a complete search, which is not; so the tournaments
of each order are first screened for witnesses, and only tournaments that survive the screen are searched further.

The starting points are the $36$ doubly regular tournaments on $23$ vertices other than $P_{23}$,
all of which are obstructions (Section @sec:families). $P_{23}$ itself is excluded, since $P_{23} - v$ is
$5$-inducible (Section @sec:paley23-critical) and so, by inheritance, is every tournament below it. Table @tbl:levels lists them
up to isomorphism and converse.

| vertices | deleted | classes | status |
|---------:|--------:|----------:|:-------------------------------------------------------|
| $22$ | $1$ | $378$ | $8$ searched completely, all obstructions (Section @sec:twenty-two) |
| $21$ | $2$ | $4{,}108$ | $1{,}192$ settled, all $5$-inducible |
| $20$ | $3$ | $28{,}724$ | all $5$-inducible |

Table: Tournaments below the $36$ doubly regular ones on $23$ vertices, up to isomorphism and converse. {#tbl:levels}

At $22$ vertices all $378$ classes were first screened at up to $50$ base states each, without a
single witness, and the eight complete searches were chosen from among them. At $21$ vertices the $1{,}192$ settled classes include all $506$ two-vertex deletions of $\Delta_6$ and $\Delta_{28}$, so every
$21$-vertex subtournament of either parent is $5$-inducible, and in particular $\Delta_6 - v_{5}$ and
$\Delta_{28} - v_{5}$ are vertex-critical. The other settled classes are a stratified random sample of $400$; all
$53$ classes below $\Delta_{11}$; every class obtained by deleting $v_5$ together with one
other vertex, the deletion that produced those two obstructions; and $19$ classes settled by inserting the missing vertex into a known witness of one of their $20$-vertex subtournaments, as in phase 1 of Appendix @sec:phases; the remaining $2{,}916$ classes are open. At $20$ vertices every class is $5$-inducible, and so, by inheritance, is every
tournament on $19$ vertices or fewer below the $36$.

Two obstructions on $25$ vertices from other families were descended the same way: $P_{27}$ with two
vertices deleted, and the circulant tournament on $25$ vertices in which every arc lies in six
directed triangles. Neither is $5$-inducible, by complete searches, and every $21$-vertex
subtournament of either is $5$-inducible, so neither family yields an obstruction below $22$.

**Other families on $21$ vertices.** We also searched families on $21$ vertices that a
symmetry or a construction makes enumerable, all of them close to doubly regular. A regular
tournament on $21$ vertices cannot be doubly regular, since $(21 - 3)/4$ is not an integer; we
call it *near-doubly regular* if every pair of vertices has $4$ or $5$ common out-neighbours. The
table below lists every family we searched on $21$ vertices, again up to isomorphism and converse,
with the number of classes settled; the vertex-transitive tournaments on $21$ vertices, a family
enumerated in full, are covered in Section @sec:families. Every settled class is $5$-inducible, by a witness verified
independently of the search; none was settled negatively.

| family on $21$ vertices | classes | settled |
|:------------------------------------------------------------------|------:|------:|
| two vertices deleted from a doubly regular tournament on $23$ vertices | $4{,}108$ | $1{,}192$ |
| four vertices deleted from the circulant tournament on $25$ vertices | $286$ | $286$ |
| six vertices deleted from $P_{27}$ | $150$ | $150$ |
| near-doubly regular, rigid, drawn at random | $78$ | $78$ |
| near-doubly regular, with a bisector and an automorphism of order $5$ | $28$ | $28$ |
| near-doubly regular, with a fixed-point-free automorphism of order $3$ | $31$ | $31$ |

Table: The families searched on $21$ vertices, up to isomorphism and converse. {#tbl:families21}

The $31$ classes of the last family are likely, but not confirmed, to be all of it: the enumeration
found no new class after its first $225$ solutions, and we stopped it at $4{,}567$ without running it
to completion. Two of the $31$ are bisectable and the other $29$ are not. In the two families
with an automorphism, several classes have only majority witnesses: $12$ of the $28$ with a bisector, and $30$ of the $31$ with an automorphism of order $3$.

## The MAS algorithm: orbit subset-DP, meet-in-the-middle, and the negation/converse join key {#app:mas-dp}

This appendix describes the dynamic program that certifies $\mathrm{MAS}(P_{43}) = 543$
(Section @sec:mas-shell) and enumerates the level-$\le 1$ shell (Section @sec:screen).

**[]{#sec:dp-base} Base recurrence (Held–Karp 1962).** For $S \subseteq V$ let $g(S) = \mathrm{MAS}(T[S])$. The last
vertex $v$ of an order of $S$ gains its in-arcs from $S \setminus \{v\}$, so
$$g(\varnothing) = 0, \qquad g(S) = \max_{v \in S}\bigl[\, g(S \setminus \{v\}) + |\{u \in S \setminus \{v\} : u \to v\}| \,\bigr],$$
and $\mathrm{MAS}(T) = g(V)$. 

**[]{#sec:dp-quotient} Automorphism quotient.** As $T[\sigma S] \cong T[S]$ for $\sigma \in \mathrm{Aut} =
\{x \mapsto ax+b : a \in \mathrm{QR}\}$, we keep one representative per orbit: $4.9 \times 10^{9}$ states up to $|S| = 21$
(almost $903$ times fewer). The representative is the minimum bit-mask over the images that send a vertex of
maximum out-degree within $S$ to $0$. Layer $j+1$ comes from layer $j$: a stored $S$ yields, for each
$v \notin S$, the record $(\mathrm{canon}(S \cup \{v\}),\, g(S) + |\{u \in S : u \to v\}|)$, with the gain computed before
canonicalizing; equal keys keep the largest value, $g(S \cup \{v\})$.

**[]{#sec:dp-equator} Meet-in-the-middle at the equator.** Storing every layer up to $|S| = 43$ is out of reach,
so we build layers $0$ to $22$ only and split every order in the middle. Let $\pi$ be an order of $V$ and $S$ the
set of its first $21$ vertices (the **equator** is $h = 21$). An arc of $T$ lies inside $S$, inside $V \setminus S$,
or between the two, and an arc between them is forward in $\pi$ exactly when it goes from $S$ to $V \setminus S$. Hence
$$\mathrm{fwd}(\pi) = \mathrm{fwd}(\pi|_S) + \mathrm{cross}(S) + \mathrm{fwd}(\pi|_{V \setminus S}),$$
where $\mathrm{cross}(S)$ counts the arcs from $S$ to $V \setminus S$, and maximizing the two halves separately gives
$$\mathrm{MAS}(T) = \max_{|S| = 21} \bigl[\, g(S) + \mathrm{cross}(S) + g(V \setminus S) \,\bigr].$$
The first term is read from layer $21$. The suffix $V \setminus S$ has $22$ vertices, but the tables were built from
the front of an order, so we read the suffix through a twin order. Negation $x \mapsto -x$ maps $T$ onto its
converse, because $-1$ is a non-residue; so reversing $\pi$ and negating every vertex gives an order $\pi^{*}$ with
$\mathrm{fwd}(\pi^{*}) = \mathrm{fwd}(\pi)$, whose first $22$ vertices form the set $-(V \setminus S)$. In particular
$g(V \setminus S) = g(-(V \setminus S))$, which layer $22$ stores under the key $\mathrm{canon}(-(V \setminus S))$.

**[]{#sec:dp-join} The join: the negation/complement commutes with the quotient by $\mathrm{Aut}$.** Layer $21$ holds one
representative per orbit, so the maximum above must be taken over orbits, and the key of the suffix must not depend on
which representative was stored. Let $\nu(S) = -S$, $\kappa(S) = V \setminus S$ and $\varphi = \nu \circ \kappa$, so that the suffix
of $S$ is looked up at $\mathrm{canon}(\varphi(S))$. (i) $\kappa$ commutes with every bijection of $V$; (ii)
$\nu \circ \sigma_{a,b} = \sigma_{a,-b} \circ \nu$, so negation normalizes $\mathrm{Aut}$ while lying outside it; hence (iii)
$\varphi \circ \sigma_{a,b} = \sigma_{a,-b} \circ \varphi$. So if $S$ and $S'$ lie in one orbit, so do $\varphi(S)$ and
$\varphi(S')$: $\mathrm{canon}(\varphi(S))$ is constant on orbits, and $\varphi$ induces a one-to-one map from the orbits
of $21$-sets to the orbits of $22$-sets. As $g$ and $\mathrm{cross}$ are constant on orbits as well, the maximum over all
$21$-sets equals the maximum over the stored representatives.

We stream layer $21$ and form, for each representative $S$, the pair $(\mathrm{canon}(\varphi(S)),\, g(S) + \mathrm{cross}(S))$;
we sort these pairs by key and merge them with the stored layer-$22$ table, which is sorted by the same key. Each match
gives $\mu(S) = g(S) + \mathrm{cross}(S) + g(\varphi(S))$, the largest number of forward arcs of an order whose first $21$
vertices form $S$, and $\mathrm{MAS}(T) = \max_S \mu(S) = 543$. Backtracking through the stored values from the splits with
$\mu(S) \ge 542$ lists every order of level $\le 1$, the shell of Section @sec:screen (orbit counts in
Appendix @app:paley43-ledger).

## Counts for the Paley(43) proof {#app:paley43-ledger}

This appendix gives the counts behind the proof that $N(5) \le 43$ (Section @sec:paley43): the structural counts of Paley(43) and the certified value $\mathrm{MAS} = 543$ (Table @tbl:paley43-ledger), then the sizes of the shell and of the screen.

| quantity | formula | value |
|---|---|---|
| arcs $C$ | $q(q-1)/2$ | 903 |
| cyclic triangles $N_{\Delta}$ | $(q^3 - q)/24$ | 3311 |
| $\lvert \mathrm{Aut}(P) \rvert$ | $q(q-1)/2$ | 903 |
| out-degree | $(q-1)/2$ | 21 |
| triangles per arc | $(q+1)/4$ | 11 |
| $\mathrm{MAS}(P)$ | dynamic program (Appendix @app:mas-dp), certified | 543 |
| $\alpha^{*} = \mathrm{MAS}/C$ | | 181/301 |
| slack $5\,\mathrm{MAS} - 3C$ | | 6 |
| forced top-two level | $\lfloor \mathrm{slack}/4 \rfloor$ | 1 |

Table: Structural counts and certified quantities for Paley(43). {#tbl:paley43-ledger}

The level-$\le 1$ shell has 1,841,303 $\mathrm{Aut}$-orbits and 1,662,696,609 orders: 19,651 orbits (17,744,853 orders) at level 0 and 1,821,652 orbits (1,644,951,756 orders) at level 1. In the screen (Section @sec:screen), the shell orders have 4,709,640 distinct restrictions to the cyclic triangles inside the window $\mathcal{W}$, and 5,092,111 pairs of these restrictions are disjoint. Only the 678,686 restrictions that belong to such a pair, and the 347,694,990 shell orders that have one of them, need the exact check. It compared 4,376,325,129 pairs of an orbit representative and such an order, and found no pair with disjoint double-back sets (0 of 4,376,325,129).

## The search engine {#app:engine}

Integer programming and satisfiability are both central to this project.
Every optimum reported in the companion paper is certified by an integer or linear program, and the integer program of Appendix @sec:ip-sat-slow below is that paper's $k$-inducibility formulation with antisymmetry substituted out; the only machine-checked theorem in this paper
is a SAT computation from end to end, with CaDiCaL (Biere et al. 2024; Pollitt et al. 2023) emitting LRAT proofs that `lrat-trim` (Pollitt et al. 2023) checks. The claim here is narrow: on this one decision problem, at these sizes, neither
tool reaches the answer while a search built around the problem's own structure does, and the same
SAT machinery is then indispensable for turning that answer into a proof.

### Integer programming and SAT are both too slow {#sec:ip-sat-slow}

The natural integer program has one binary $x_{v,ij}$ per voter $v$ and pair $i < j$, meaning that $v$
ranks $i$ above $j$, with $x_{v,ji}$ read as $1 - x_{v,ij}$; transitivity rows
$0 \le x_{v,ij} + x_{v,jl} - x_{v,il} \le 1$ for $i < j < l$; and one majority row
$\sum_{v} x_{v,ij} \ge (k+1)/2$ per arc. At $q = 23$, $k = 5$ it has $1{,}265$ binaries, $17{,}710$ transitivity rows and $253$ majority rows. Setting $x_{v,ij} = 3/5$
on every arc of $T$ and $2/5$ on every non-arc satisfies every row, so the linear programming (LP)
relaxation is feasible and, the problem having no objective, gives branch-and-bound nothing to prune by;
that point is invariant under both symmetry groups, so it gives no branching direction either. CPLEX and
Gurobi both failed to close instances at $n = 19$ within a day.

The satisfiability encoding is *dissent-Boolean*: one variable per voter $v$ and arc of $T$, true when $v$
dissents from the arc. Each arc has at most $(k-1)/2$ dissents for majority and exactly $(k-1)/2$ for unit
margin, and for every voter and triple the two dissent patterns that would make the triple cyclic are
forbidden. For $k = 5$ that is $5\binom{n}{2}$ variables, $15$ clauses per arc at unit margin and $10$ per
triple, and the certified refutations of Appendix @app:certificates are built on it. On uniform random
tournaments the `Sat-Check-k-Majority` of Bachmeier et al. (2019, Table 4) averages $0.23$ seconds at
$n = 18$ and $18.95$ at $n = 23$, roughly doubling per vertex, whereas on $P_{23}$ the same solver did not
terminate within six weeks: random tournaments have no automorphisms to rediscover and many witnesses.
Better encodings and explicit symmetry breaks help but do not suffice; supplying the decomposition into
base states as cubes does (Section @sec:symmetry).

### The symmetry reductions in full {#sec:symmetry-details}

In this subsection we prove Lemma @lem:symmetry and explain how its parts are used.

*Proof of Lemma @lem:symmetry.* (a) Let $w$ be a witness and choose $g \in G$ with $g\,\varphi(w) \in R$.
Then $gw$ is a witness, since permuting voters changes no margin and relabelling by an automorphism
carries the margin of each arc to its image, and $\varphi(gw) = g\,\varphi(w) \in R$. Parts (b) and (c)
are (a) with $G = \mathrm{Aut}(T)$, $\varphi(\pi)$ the top pair, respectively the top vertex, of $\pi_1$,
and $R$ the representatives. Part (d) is (a) with $G = S_k$, $\varphi$ the identity and $R$ the sorted
profiles, every $S_k$-orbit containing one. A second application of (a) may use any group element that
preserves what the first guaranteed, and permuting voters preserves "some voter ranks $a_i$ first and
$b_i$ second" (or "$v_i$ first"), which depends on the multiset of orders and not on which voter carries
it; so (d) applies after (b) or (c). For (e), relabelling by $h \in H$ maps a base state of $C$ to one,
since $h(C) = C$ and $h$ restricts to an automorphism of $T[C]$, while $S_k$ acts trivially on base
states, which are multisets; and the base state of $C$ that $h\pi$ extends is $h$ applied to the one
$\pi$ extends. So (a) with $G = S_k \times H$ and $\varphi(\pi)$ that base state gives a witness extending
a chosen base state of $C$, and its orders restricted to $B$ form a chosen base state of $B$ that it
extends. If $H$ fixes the representatives, each $h \in H$ maps an anchored voter to an anchored voter, so
the same argument applies after (b) or (c). $\blacksquare$

Part (b) guarantees only that *some* $i$ works, not any particular one, and it is this weak form that
lets (d) follow it; had it said "voter $1$ ranks $a_i$ first", the composition would fail. For a Paley
tournament there are two orbits on ordered pairs, the arcs and the non-arcs: the maps $x \mapsto a(x-t)$
with $a \in \mathrm{QR}$ are automorphisms, they send $(t,s)$ to $(0, a(s-t))$, and as $a$ ranges over
$\mathrm{QR}$ they leave exactly two orbits, separated by whether $s - t \in \mathrm{QR}$. On $P_7$
(Figure @fig:paley7) the representatives are $(1,2)$ and $(1,4)$. Otherwise we compute $\mathrm{Aut}(T)$
and its orbits with `nauty` 2.8.6 (McKay and Piperno 2014), which also provides every automorphism
group, orbit set and canonical form reported in this paper; (b) and (c) are alternatives, and the better
one depends on the numbers of orbits on pairs and on vertices.

When every representative pair lies inside $B$, a voter ranking $a_i$ first and $b_i$ second overall does
so within $B$, which the base state reveals, so a base state in which no voter tops $B$ with a chosen
pair extends to no anchored witness and may be discarded; the survivors are the *live* base states.
Otherwise the search tests the anchor once every representative has both endpoints placed: an insertion
can destroy an anchor but never create one, so a partial profile with no anchored voter has no anchored
extension. The SAT certification tests it only once, to decide which cubes reach the solver.

In part (e) the condition on the representatives cannot be dropped: if $H$ moves one, mapping an anchored
witness into a chosen base state can destroy its anchor. Automorphism groups of tournaments have odd
order, since an automorphism of order $2$ would swap the endpoints of some arc, and an automorphism $h$
maps $B$ onto itself exactly when $B$ is a union of its cycles; a $5$-cycle of an automorphism of order
$5$ is such a base. When no subgroup maps a base of the size we use onto itself, $C \subsetneq B$ helps:
a fixed-point-free automorphism of order $3$ maps no five vertices onto itself but maps each of its
$3$-cycles onto itself, and with $C$ one of them the search keeps only the base states of $B$ above a
chosen base state of $C$, choosing in each orbit the one with fewest base states above it. Three
unit-margin searches of Appendix @app:below22 kept $600$ of $2{,}200$ in this way.

**Using the whole group.** We take $H = G_R$, the common stabilizer of the representatives. For a single
representative $r$ the orbit–stabilizer theorem (Dummit and Foote 2004, Section 4.1, Proposition 2)
gives $|\mathrm{Aut}(T)| = |\mathrm{Aut}(T) \cdot r| \cdot |G_r|$, so anchoring and the quotient between
them use the whole group; with several representatives we choose them to keep $G_R$ large, and the base
among the unions of cycles of $G_R$ or the sets containing one. Table @tbl:group-use shows the split: for
the Paley tournaments the stabilizer of a representative pair is trivial, so the whole group goes to
anchoring, and for $\Delta_1 - v_{10}$ it splits into orbits of $11$ and a stabilizer of order $5$; Figure @fig:symmetry-flow
summarizes which parts of Lemma @lem:symmetry apply to a given tournament and base.

| tournament | $\lvert \mathrm{Aut}(T) \rvert$ | anchoring | quotient | base states kept |
|:-------------------------|--------:|:-------------------------|:----------|------------------------:|
| $P_{19}$, unit, certificate | $171$ | ordered pairs | none | $22{,}876$ of $142{,}251$ |
| $P_{23}$, search | $253$ | ordered pairs | none | $2{,}591$ of $8{,}031$ |
| $P_{23}$, certificate | $253$ | ordered pairs | none | $343{,}896$ of $3{,}414{,}729$ |
| $\Delta_1 - v_{10}$, search | $55$ | $x_0$, $y_0$ (orbits of $11$) | order $5$ | $1{,}611$ of $8{,}031$ |
| $\Delta_1 - v_{1}$, $\Delta_1 - v_{2}$ | $5$ | none | order $5$ | $1{,}611$ of $8{,}031$ |
| $\Delta_{11} - v_{2}$, $- v_{5}$, $- v_{20}$ | $5$ | none | order $5$ | $1{,}611$ of $8{,}031$ |
| $\Delta_6 - v_{5}$, $\Delta_{28} - v_{5}$ | $1$ | none | none | $8{,}031$ of $8{,}031$ |

Table: How the searches and certificates of Section @sec:results use the automorphism group. Anchoring uses the orbits of the representatives and the quotient their common stabilizer. In the $\Delta_1 - v_{10}$ search the representatives lie outside the base, so the count of base states kept reflects the quotient alone. {#tbl:group-use}

\begin{figure}[!htbp]
\centering
\includegraphics[width=0.78\linewidth]{symbreak_flow.pdf}
\caption{Which symmetry reductions apply to a tournament $T$ and a base $B$. Anchoring by Lemma @lem:symmetry(b)
or (c) can discard base states only when every representative lies in $B$, since a base
state reveals the orders on $B$ alone; otherwise the search enforces it during insertion, and the SAT route
cannot use it. The quotient of Lemma @lem:symmetry(e) combines with
anchoring only when $H$ fixes every representative.}
\label{fig:symmetry-flow}
\end{figure}

### The five steps on a small example {#sec:base-states}

Given $T$ and the margin regime, the search has five steps:

1. **Pick a size.** Choose the base size $b$, in practice $5$ or $6$.
2. **Pick a subtournament.** Choose a set $B$ of $b$ vertices. Only $T[B]$ matters for what follows, so
   the choice can and should be optimized quickly (Section @sec:fast), since the base-state count
   varies by more than two orders of magnitude across the $12$ isomorphism classes at $b = 5$.
3. **Find its base states.** Enumerate the $k$-tuples of linear orders of $B$ whose supports agree
   with $T[B]$, counted up to voter permutation by Lemma @lem:symmetry(d).
4. **Determine the usable symmetries.** Compute $\mathrm{Aut}(T)$ with `nauty` and its orbits,
   then impose the ordered-pair anchoring of Lemma @lem:symmetry(b), the vertex anchoring of Lemma @lem:symmetry(c), or
   neither, discarding the base states no anchored witness can use. If a subgroup $H$ maps $B$, or a
   subset $C$ of it, onto itself, also keep only the base states above one representative of each
   $H$-orbit (Lemma @lem:symmetry(e)), checking that $H$ fixes the anchoring representatives
   (Figure @fig:symmetry-flow).
5. **Run to completion, in parallel across base states.** The verdict is positive as soon as any
   base state yields a witness. It is negative only when *every* live base state has been searched
   to exhaustion.

Figure @fig:paley7 shows all five steps on $P_7$ at $k = 3$. Steps 1–4 are fast; step 5 runs in parallel.

\begin{figure}[!t]
\centering
\includegraphics[width=\linewidth]{paley7_alg1.pdf}
\caption{Algorithm @alg:placement on $P_7$ at $k = 3$, which is $3$-inducible, so the run ends in a witness. 
A \emph{slot triple} is one gap per voter, of the $64$ available, and a vertex's domain is
those triples its arcs to $B$ admit. Here the base is $B = \mathrm{QR}$, the squares modulo 7, 
and Lemma @lem:symmetry(b) guarantees that at least one voter must rank 1 first and either 2 or 4 second. 
Ranking 4 second forces the other two voters to $241$, the only order getting both $4 \to 1$ and
$2 \to 4$ right, and $1 \to 2$ is then left with support $1$; so the base state in (b) is the only one.
\textbf{(a)} The base $T[B]$ on $B = \{1,2,4\}$ in bold; dashed, the arcs at the first vertex
inserted. \textbf{(b)} Steps 2--4: the base state is forced, and MRV takes the smallest domain.
\textbf{(c)} Two insertions the search rejects, one by Lemma @lem:symmetry(b) and one by leaving $5$ no slot at all.
\textbf{(d)} One that survives, and what it leaves of (b). \textbf{(e)} REFINE lifts each parent
tuple past the slot just used (unchanged below it, shifted above it, split where the two
coincide, which is what green marks), and the one new arc then keeps or kills each lift.
\textbf{(f)} The witness, every arc at support exactly $2$. Without Lemma @lem:symmetry(b) the search returns
all $7$ witnesses, a single orbit of $\mathrm{Aut}(P_7)$, of order $21$, so the profile is unique
up to symmetry, as Shepardson and Tovey (2009) report; $\pi$ generates the other two under the $g$
shown, the map $x \mapsto 2x + 4$ of $\mathbb{F}_7$.}
\label{fig:paley7}
\end{figure}

### Runtimes for every computation {#sec:runtimes}

All runs used a single laptop (Apple M-series, 14 cores, 24 GB RAM, at most 11 cores at once) except
the following, which used a compute cluster: the census of regular tournaments on $15$ vertices, the self-converse census of order $13$, the
order-$12$ census of Appendix @app:order12, six of the $22$-vertex sweeps of Section @sec:twenty-two, part of the certificate
for $\Delta_1 - v_{10}$, $16$ of the $19$
unrestricted sweeps of doubly regular tournaments on $23$ vertices in Section @sec:families, and most of the
search of Appendix @app:below22.

Runtimes are in *core-hours*, the workers' running times summed. The cluster ran $2$ to $5$ times slower per
unit of work, so we convert its runtimes to the laptop's scale as follows, unless marked as cluster core-hours.

The certificate for $\Delta_1 - v_{10}$ ran partly on each machine; on the $133$ groups of five cubes
solved on both, the cluster took on average $2.1$ times as long ($1.6$ to $3.1$ for individual groups),
and we divide its cluster time by that average, so the converted total is approximate. The searches of
$\Delta_1 - v_{1}$, $\Delta_1 - v_{2}$, $\Delta_{11} - v_{5}$ and $\Delta_{11} - v_{20}$ run a different
program: on $355$ base states of $\Delta_{11} - v_{5}$ searched on both machines, the cluster took $3.55$ times as long in total,
and we use that factor; we apply it also to the sweeps of $\Delta_6 - v_{5}$, $\Delta_{28} - v_{5}$
and $16$ of the doubly regular tournaments on $23$ vertices, for which no paired measurement exists. The
self-converse census of order $13$ ran partly on each machine, and there the cluster took $5.13$ times as long per tournament.
The censuses of orders $12$ and $15$ ran on the cluster alone; on random samples of $8$ and $12$ of their
parts rerun on the laptop, the cluster took $3.85$ and $4.28$ times as long respectively. Table @tbl:runtimes lists the result.

| computation | margin | verdict | core-hours |
|-------------------------------------------------------|--------------|---------------|-----------:|
| $P_{19}$, certified refutation | unit | not inducible | $25.1$ |
| $P_{23}$, certified refutation | unrestricted | not inducible | $236.0$ |
| $\Delta_1 - v_{10}$, sweep (Lemma @lem:symmetry(e)) | unrestricted | not inducible | $96.9$ |
| $\Delta_1 - v_{10}$, certified refutation | unrestricted | not inducible | $732$ |
| $\Delta_6 - v_{5}$, certified refutation | unrestricted | not inducible | $1{,}292.7$ |
| $\Delta_6 - v_{5}$, sweep | unrestricted | not inducible | $437.0$ |
| $\Delta_{28} - v_{5}$, sweep | unrestricted | not inducible | $433.2$ |
| $16$ doubly regular on $23$ vertices | unrestricted | not inducible | $7{,}458.2$ |
| $\Delta_1 - v_{1}$, sweep (Lemma @lem:symmetry(e)) | unrestricted | not inducible | $136.8$ |
| $\Delta_1 - v_{2}$, sweep (Lemma @lem:symmetry(e)) | unrestricted | not inducible | $122.9$ |
| $\Delta_{11} - v_{2}$, sweep (Lemma @lem:symmetry(e)) | unrestricted | not inducible | $108.5$ |
| $\Delta_{11} - v_{5}$, sweep (Lemma @lem:symmetry(e)) | unrestricted | not inducible | $124.2$ |
| $\Delta_{11} - v_{20}$, sweep (Lemma @lem:symmetry(e)) | unrestricted | not inducible | $93.6$ |
| $P_{31} -\,v$, sweep | unrestricted | not inducible | $239.5$ |
| $P_{23}$, one arc reversed | unrestricted | inducible | $210.4$ |
| second doubly regular $19$, all $57$ arc reversals | unit | all inducible | $3.59$ |
| regular on $15$ vertices | unit | all inducible | $726.1$ |
| self-converse on $13$ vertices | unit | all inducible | $294.2$ |
| all on $12$ vertices | unit | all inducible | $2{,}615.6$ |

Table: The runtime of every computation in this paper. {#tbl:runtimes}

Table @tbl:sweeps gives the four full Paley sweeps; $P_{27}$, built over $\mathbb{F}_{27}$, is not
$5$-inducible but does not bear on $N(5)$. On a fixed base decomposition the runtime falls as $q$ grows,
because a larger Paley tournament is more constrained and its search is refuted nearer the root, even
though the work per node rises from $10.8$ to $57.4$ microseconds. Deleting a vertex, which shrinks the
automorphism group, has the opposite effect ($P_{43} - v$ takes $185.5$ core-hours), and on $P_{43} - v$ unit
margin is about $90$ times faster than plain majority, with $2{,}200$ base states instead of $8{,}031$ and the
last voter forced.

| $q$ | live base states | core-hours | nodes | seconds per live base state |
|:------|:-------------------|:-------------|:-----------|:---------------------------|
| 23 | $2{,}591$ | $34.03$ | $1.14 \times 10^{10}$ | $47.3$ |
| 27 | $2{,}537$ | $31.04$ | $6.22 \times 10^{9}$ | $44.0$ |
| 31 | $4{,}007$ | $26.89$ | $3.43 \times 10^{9}$ | $24.2$ |
| 43 | $2{,}537$ | $22.87$ | $1.43 \times 10^{9}$ | $32.5$ |

Table: The four full Paley sweeps. {#tbl:sweeps}

## The obstructions on 22 vertices {#app:obstructions22}

Each obstruction of Section @sec:twenty-two is given as in McKay's (2026) catalogue: $231$ bits, the upper
triangle of its adjacency matrix row by row ($1$ when the $u$-th vertex beats the $w$-th, in the parent's
labelling minus the deleted vertex), under the order of its automorphism group and any generators.

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_1 - v_{1}$}\quad {\small $|\mathrm{Aut}| = 5$, generated by (2 9 11 7 5)(3 8 4 12 6)(13 22 15 16 20)(14 17 19 23 18)}\\[2pt]
{\small\ttfamily 11111000001111110000001100011110001111100100111000010110011111100110110010101\\
11011010101100110101011100101100110100110000101110010101101101010101100011100\\
10101011001011101101001100010110101011010101111000001101010001000101011110011}
\end{minipage}
\medskip

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_1 - v_{2}$}\quad {\small $|\mathrm{Aut}| = 5$, generated by (1 19 12 23 8)(3 6 4 18 14)(5 16 15 13 7)(9 22 11 20 21)}\\[2pt]
{\small\ttfamily 11111111110000000000001100011110001111100100111000010110011111100110110010101\\
11011010101100110101011100101100110100110000101110010101101101010101100011100\\
10101011001011101101001100010110101011010101111000001101010001000101011110011}
\end{minipage}
\medskip

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_1 - v_{10}$}\quad {\small $|\mathrm{Aut}| = 55$, generated by (2 9 11 7 5)(3 8 4 12 6)(13 22 15 16 20)(14 17 19 23 18) and\\
(1 18 4 14 23 19 12 6 8 17 3)(2 16 21 7 13 5 11 9 22 15 20)}\\[2pt]
{\small\ttfamily 11111111110000000000011111000011111100000011000111000111110010011000010110011\\
11110110110010101110101010110011010111100101100110001100001011101010110110100\\
10101011001011101101001100010110101011010101111000001101010001000101011110011}
\end{minipage}
\medskip

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_{11} - v_{2}$}\quad {\small $|\mathrm{Aut}| = 5$, generated by (1 21 12 22 9)(3 14 13 7 16)(4 17 18 15 6)(8 11 10 23 19)}\\[2pt]
{\small\ttfamily 11111111110000000000001110110001100001111001010110011101001110101100010111100\\
11101011001010011111011010111011000101011100111000101011001011010110001110101\\
11001001011100011101010001011110010011001010101000101010110010001011101110111}
\end{minipage}
\medskip

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_{11} - v_{5}$}\quad {\small $|\mathrm{Aut}| = 5$, generated by (1 21 12 22 9)(3 14 13 7 16)(4 17 18 15 6)(8 11 10 23 19)}\\[2pt]
{\small\ttfamily 11111111110000000000011110000011111100000011011000110000111101010110011101001\\
11101011001010011111011010111011000101011100111000101011001011010110001110101\\
11001001011100011101010001011110010011001010101000101010110010001011101110111}
\end{minipage}
\medskip

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_{11} - v_{20}$}\quad {\small $|\mathrm{Aut}| = 5$, generated by (1 21 12 22 9)(3 14 13 7 16)(4 17 18 15 6)(8 11 10 23 19)}\\[2pt]
{\small\ttfamily 11111111111000000000011111000001111110000011101100011000011100101011001110101\\
11010110001011100111010110010101111101101011101000101011100110001010110011101\\
01100011010111001000111000111101000101110010010010101100010010110100101101111}
\end{minipage}
\medskip

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_6 - v_{5}$}\quad {\small $|\mathrm{Aut}| = 1$}\\[2pt]
{\small\ttfamily 11111111110000000000011110000011111100000011001101001001111001100010000111101\\
11011100010110110111111110111100001010110010010111010101010111010011010101101\\
10110011001101001101011000110011011010101000111001001010100110010011100101110}
\end{minipage}
\medskip

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_{28} - v_{5}$}\quad {\small $|\mathrm{Aut}| = 1$}\\[2pt]
{\small\ttfamily 11111111110000000000011110000011111100000011101001000101011101010100001011101\\
11100110010110111011111110111100000110110100011100011100010101110101010110011\\
01101010110001101101011000110101011011010000111000100110000011010011100101110}
\end{minipage}
\medskip

\noindent\begin{minipage}{\linewidth}
\textbf{$\Delta_1 - v_{10}$ with the arc between $v_2$ and $v_3$ reversed}\quad {\small $|\mathrm{Aut}| = 1$}\\[2pt]
{\small\ttfamily 11111111110000000000001111000011111100000011000111000111110010011000010110011\\
11110110110010101110101010110011010111100101100110001100001011101010110110100\\
10101011001011101101001100010110101011010101111000001101010001000101011110011}
\end{minipage}
\medskip

## Criticality at $21$ vertices {#app:criticality21}

Table @tbl:reversals21 reverses one arc per arc orbit, at unit margin, in the four vertex-transitive
unit-margin obstructions on $21$ vertices (Section @sec:paley23-critical): `U` if the result is still not
unit-margin inducible, `S` if it is.

| tournament | $\mathrm{Aut}$ | the ten orbits | obstructions |
|---|---|---|---|
| $C_a$ | $\mathbb{Z}_{21}$ | `U U U U U U U U U U` | $10$ |
| $C_b$ | $\mathbb{Z}_{21}$ | `U S U S S U U S S U` | $5$ |
| $F_a$, $F_b$ | $\mathbb{Z}_7 \rtimes \mathbb{Z}_3$ | `S S S S S S S S S S` | $0$ |

Table: One arc reversal per arc orbit of the four vertex-transitive unit-margin obstructions on $21$ vertices. {#tbl:reversals21}
