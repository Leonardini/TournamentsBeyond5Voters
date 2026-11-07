# Counting bounds on N(k)  (`counting_bounds/`)

**What it shows.** The paper's counting bounds: some tournament on 38 vertices is not 5-inducible
(N(5) ≤ 38), and for every odd k ≤ 21 the upper bounds on the largest order at which every
tournament is k-inducible improve on Table 1 of Bachmeier et al. (2019). Both rest on completion
uniqueness: k − 1 voters and an out-degree sequence determine the tournament of the k-th.

- `extended_table1_bounds.py` — the table of bounds for odd k from 3 to 21: the published bounds
  (recomputed from their counting lemma, as a self-check), the exact multiset count, and the regular
  and near-regular bounds of the paper. Its k = 5 regular entry gives N(5) ≤ 39.
- `nearreg_table_bounds.py` — the near-regular refinement for even orders, through the bijection
  between near-regular tournaments on n vertices and regular ones on n + 1 (checked by brute force
  at small even n); it gives N(5) ≤ 38.

**How to run.** `python3 extended_table1_bounds.py` and `python3 nearreg_table_bounds.py`, each in
under a second, Python standard library only. Each stops with an assertion error if a check fails: the
first must reproduce the published bounds of Bachmeier et al., and both check that the counting
inequality keeps holding above each threshold they report.
