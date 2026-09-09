# Reproducing every published result with one binary

There is now a single engine, `kinduce.c`. It carries 26 flags, which are
exactly the flags that appear in a command line that produced a recorded
result; nothing else. `man ./kinduce.1` documents each one, and the
**SOUNDNESS** section of that page lists the three obligations the program
cannot check for itself.

    cc -O3 -march=native -o kinduce kinduce.c

## Provenance

The 25 historical implementations are retained in `versions/`. They are not
needed to reproduce anything — the table below is complete — but each published
result was *originally* produced by one of them, and that version is named in
the table so a reader can compare against the original if they wish.

The consolidated engine was built as **`kinduce24` + the `brec` supHI fix +
`--emit`, minus ten flags never used for a result**. It was not built by
stripping `kinduce25`, so the `--pin` machinery of that version is absent
entirely. `versions/kinduce25.c` is **excluded from the reproduction package**.

## The results

Every row is a complete run. Slice it with `--bs-from`/`--bs-to` across workers;
the slices are disjoint and their union is the whole space.

### N(5) <= 23 — Paley(23) is not 5-inducible

Two independent anchors, different bases and different breaks. Either is a
complete refutation; both were run.

    # anchor A  (originally kinduce16)   34.03 core-h
    ./kinduce --paley 23 --k 5 --margin majority --order mrv --inc \
              --pool-mb 512 --base 0 1 2 5 11 --top0rr 2 5 \
              --bs-from 0 --bs-to 8031

    # anchor B  (originally kinduce22)
    ./kinduce --paley 23 --k 5 --margin majority --order mrv --inc \
              --pool-mb 512 --base 0 1 2 6 7 --toppair 1 2 6 2 \
              --bs-from 0 --bs-to 8031

### Paley(27) is not 5-inducible

31.04 core-h, 1.14e8 nodes, coverage [0,8031). Originally kinduce22.
The host must be the GF(3^3) build: the Z/27 construction is not a tournament.

    ./kinduce --bits p27_paley.bits --n 27 --k 5 --margin majority --order mrv \
              --inc --pool-mb 512 --base 0 1 2 3 14 --toppair 0 14 2 1 \
              --bs-from 0 --bs-to 8031

### Paley(31) is not 5-inducible

26.89 core-h, 3.43e9 nodes, coverage [0,21009), 4,007 survivors under the
break. Originally kinduce22, base class mask 499.

    ./kinduce --paley 31 --k 5 --margin majority --order mrv --inc \
              --pool-mb 512 --base 0 1 2 3 6 --toppair 2 3 0 3 \
              --bs-from 0 --bs-to 21009

### Paley(43) is not vertex-critical

Paley(43) minus a vertex is not 5-inducible. 185.5 core-h, mean 83.2 s and max
313.2 s per base state, coverage [0,8031) exactly. Originally kinduce24.
Paley(43) is vertex-transitive, so this one run settles all 43 deletions.

    ./kinduce --bits p43_minus1v.bits --n 42 --k 5 --max-margin 3 --order mrv \
              --inc --pool-mb 512 --base 0 1 2 3 10 --toporb 0 1 \
              --bs-from 0 --bs-to 8031

Run at margin <= 3, which for this host is equivalent to unrestricted majority:
every arc of Paley(43)-v lies in at least 10 directed triangles, and by the
3-cycle bound an arc in any triangle can never be unanimous. The two
`--toporb` representatives are the QR and non-QR cosets, the two orbits of the
order-21 stabiliser; that orbit calculation is the caller's obligation.

### Paley(23) minus a vertex IS 5-inducible

A witness in about a minute. Originally kinduce21. This closes the descent
below Paley(23), since that tournament is unique up to isomorphism and
5-inducibility is hereditary.

    ./kinduce --bits p23_minus1v.bits --n 22 --k 5 --margin majority \
              --order mrv --inc --pool-mb 512 --toporb 0 4

### Paley(19) is 5-inducible at margin <= 3 but not at margin 1

The positive half. Witnesses are abundant: a shuffled ten-way sweep hit in all
ten workers at once, from ten different base states, with none refuted.

    ./kinduce --paley 19 --k 5 --max-margin 3 --order mrv --inc --base 0 1 2 3 5

The negative half is certified separately by SAT; see `certify_d6.py` and
`p19_margin1_VERDICT.txt`. The DFS route reaches the same verdict in about
2.5 core-hours:

    ./kinduce --paley 19 --k 5 --max-margin 1 --order mrv --inc --base 0 1 2 3 5 \
              --bs-from 0 --bs-to 2200

### The margin-1 family

Each cell is 2,200 base states, complete, no caps. Originally kinduce24; see
`m1_family/VERDICTS.md` for the table.

    ./kinduce --bits <host>.bits --n <n> --k 5 --margin exact --order mrv --inc \
              --pool-mb 512 --base <base> --bs-from 0 --bs-to 2200

### The second doubly regular tournament on 19 vertices

`dr19_g1` is Paley(19) relabelled; `dr19_g2` is the genuinely different one,
with |Aut| = 3 and seven vertex orbits, so `--toporb` needs all seven
representatives. SAT at margin <= 3 in 176 s, UNSAT at margin 1 in 2.70 core-h.

    ./kinduce --bits dr19_g2.bits --n 19 --k 5 --max-margin 3 --order mrv --inc \
              --toporb 0 1 4 6 7 8 12
    ./kinduce --bits dr19_g2.bits --n 19 --k 5 --max-margin 1 --order mrv --inc \
              --bs-from 0 --bs-to 2200

The margin-1 run deliberately carries **no** break: the orbit test is worth
0.0007% of nodes at margin 1, so dropping it removes the only caller-discharged
lemma at no measurable cost. At margin <= 3 the same break is worth about 20%
and is kept.

### Regular tournaments on 15 vertices

Batch mode, one bit string per line. Originally kinduce20; see `jz_n15/`.

    ./kinduce --batch <chunk>.d6 --n 15 --k 5 --margin exact --order mrv --inc

## Auditing a distributed run

A refutation is only as good as its coverage. For a run sliced across workers,
check the **index cover**, not the count:

    ls done | sort -n > /tmp/got.txt
    seq 0 8030 > /tmp/want.txt
    comm -13 /tmp/got.txt /tmp/want.txt | wc -l    # missing: must be 0
    comm -23 /tmp/got.txt /tmp/want.txt | wc -l    # extra:   must be 0

and confirm that no `SLICE` line reports a nonzero `capped` count. A driver
that writes a marker only on `RESULT UNSAT` makes the exact index cover the
completeness certificate, since a capped or aborted state leaves no marker; a
bare count would not, because gaps and duplicates can cancel.

## Regression evidence

`versions/REGRESSION.md` records the comparison of the consolidated engine
against each historical version on identical command lines, requiring
node-for-node agreement.
