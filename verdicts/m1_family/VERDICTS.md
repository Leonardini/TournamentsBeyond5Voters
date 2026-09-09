# Margin-1 criticality sweeps, k = 5 (2026-09-03)

Every cell: 2200 base states, complete per base state (no caps), done-marker per state, STOP on first witness.
Per-state times in `<cell>_times.txt`; the markers themselves are not tracked (11,749 files).

| cell | host | states | coverage [0,2200) exact | witness | core-h |
|---|---|---|---|---|---|
| `p23mv` | Paley(23) - v (n=22) | 2200 | yes | none -> UNSAT | 2.60 |
| `p27` | Paley(27) (n=27, PARTIAL) | 694 | NO -- partial | none -> UNSAT | 0.71 |
| `p27e` | Paley(27) arc-reversed (n=27) | 2200 | yes | none -> UNSAT | 2.60 |
| `p27mv` | Paley(27) - v (n=26) | 2200 | yes | none -> UNSAT | 2.86 |
| `p31mv` | Paley(31) - v (n=30) | 2200 | yes | none -> UNSAT | 2.21 |
| `p43mv` | Paley(43) - v (n=42) | 2200 | yes | none -> UNSAT | 2.07 |

`p27` was abandoned deliberately: Paley(27) is already refuted at majority and margin-1 restricts majority, so that cell is implied.
`p27e`/`p31e`/`p43e` arc cells: p27e ran (UNSAT); p31e and p43e are implied by their vertex cells via ¬vertex-critical => ¬arc-critical.
