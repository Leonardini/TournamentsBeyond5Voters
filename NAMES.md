# What the tournament names mean

Files and tables here name tournaments by short working labels: `d005_mv04`, `h02`,
`g21_00048`. The manuscript uses its own notation instead, and only for the tournaments its
argument needs. This table gives each label's number of vertices, what the tournament is and
where it comes from, and its name in the manuscript where it has one. Vertex numbers inside a
label are **0-based**. The manuscript numbers vertices from 1, so `d005_mv04` deletes the
manuscript's vertex 5.

| label | vertices | what it is, and where it comes from | in the manuscript |
|---|---|---|---|
| `pq_paley`, `paleyq`, `pq` | q | The Paley tournament on the field of q elements (`tournaments/make_paley_gf.py`) | $P_q$ |
| `pq_minus1v`, `pq_minus2v` | q − 1, q − 2 | Paley(q) with one vertex deleted, or two (`tournaments/make_paley_minus.py`) | $P_q - v$ |
| `pq_arcrev`, `p23_flip_a_b` | q | Paley(q) with one arc reversed; `flip_a_b` names the arc | — |
| `p23_source0`, `p23_sink0` | 23 | Paley(23) with vertex 0 made a source or a sink | — |
| `dNNN` | 23 | The doubly regular tournament on line NNN + 1 of McKay's catalogue (`tournaments/drt23/`) | $\Delta_{NNN+1}$ |
| `dNNN_mvVV` | 22 | `dNNN` with vertex VV deleted, the rest kept in order (`tournaments/drt23_del/`) | $\Delta_{NNN+1} - (VV+1)$; e.g. `d005_mv04` is $\Delta_6 - 5$ |
| `dNNN_mvAA_BB`, `dNNN_mvAA_BB_CC` | 21, 20 | `dNNN` with two or three vertices deleted: the levels of Appendix G (`HOSTS_level2.tsv`, `HOSTS_level3.tsv`) | — |
| `d000mv09_rAA_BB` | 22 | Δ₁ − 10 with the arc between AA and BB reversed (Section 3.3) | — |
| `t25_tmin6` | 25 | The circulant tournament on 25 vertices in which every arc lies in six directed triangles (Appendix G) | the circulant tournament on 25 vertices |
| `p27_mv00_01` | 25 | Paley(27) with vertices 0 and 1 deleted (Appendix G) | $P_{27}$ less two vertices |
| `t25_tmin6_mv…`, `p27_mv00_01_mv…` | 21 | Four further deletions from those two (Appendix G) | — |
| `dr19_g1`, `dr19_g2` | 19 | The two doubly regular tournaments on 19 vertices; `g1` is Paley(19) | $P_{19}$ and the other one |
| `g2_fKK` | 19 | `dr19_g2` with one arc of orbit KK reversed (`tournaments/dr19_arcflip/`) | — |
| `hNN` | 21 | Seven vertex-transitive tournaments on 21 vertices, `h00` to `h06`, screened together at unit margin (`tournaments/vt21_hosts/`). The four that are not unit-margin inducible are h01, h02, h04 and h05; the others are inducible at unit margin, which is why the four are not numbered consecutively | Appendix F's $h_1$, $h_2$, $h_4$, $h_5$ |
| `hNN_fKK`, `hNN_fKK_mvVV` | 21, 20 | `hNN` with one arc of orbit KK reversed, then possibly vertex VV deleted (Section 3.6, Appendix F) | — |
| `h02_f00` | 21 | `h02` with one arc of orbit 0 reversed: the certified 21-vertex unit-margin obstruction | — |
| `vNNN` | 23 | The vertex-transitive tournaments on 23 vertices, all circulant since 23 is prime, by index in `tournaments/vt23_gen.py` | — |
| `cNNN` | 15, 17, 19 | The vertex-transitive tournaments on 15, 17 and 19 vertices, all circulant, by index (`tournaments/vt_small_gen.py`) | — |
| `eNNN` | 15 | The doubly regular tournaments on 15 vertices (`tournaments/drt15_gen.py`) | — |
| `p03`, `p07`, `p11` | 3, 7, 11 | The small doubly regular tournaments, which are Paley | $P_3$, $P_7$, $P_{11}$ |
| `g21_NNNNN` | 21 | Near-doubly regular tournaments built by gluing two regular 10-tournaments through an apex, with an automorphism of order 5 (`tournaments/near_dr21/`, from the working repository's `glue10/`) | Appendix G's family "with a bisector and an automorphism of order 5" |
| `zf21_K` | 21 | Near-doubly regular, with a fixed-point-free automorphism of order 3, from our construction | Appendix G's family "with a fixed-point-free automorphism of order 3" |
| `zr21_K` | 21 | The same family, found by a random SAT search rather than the construction | the same |
| `z3f21_NN` | 21 | The other 55 classes of that family's enumeration (the cluster screen) | the same |
| `nd21_NN` | 21 | Rigid near-doubly regular tournaments drawn at random | Appendix G's "rigid, drawn at random" |
| `tN_KKK` | N | An isomorphism class in `verdicts/verdict_ledger.tsv`, numbered within order N by `sat/registry.py`; ids are reassigned when classes are added | — |

A tournament on n vertices is stored as a `.bits` file: the C(n, 2) entries above the diagonal
of its adjacency matrix, row by row, with `1` meaning the row vertex beats the column vertex.
