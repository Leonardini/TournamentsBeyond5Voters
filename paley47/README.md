# Paley(47): the lower bound of the Paley table

The paper's table of Paley tournaments (Section 3) gives, for q = 47, only lower bounds: MAS ≥ 658,
α\* ≥ 14/23 and slack ≥ 47. They come from one linear order of the 47 vertices that makes 658 of the
1,081 arcs forward; the exact MAS of P₄₇ is not claimed.

| file | content |
|---|---|
| `paley47_order658.txt` | the order, on the line starting `ORDER:` (vertices 0–46, first to last); it lists the residues in arithmetic progression with step −10 |
| `verify_paley47_order.py` | builds P₄₇ (an arc u → v whenever v − u is a nonzero square modulo 47), checks that the order lists every vertex once, and counts its forward arcs; standard library only, under a second |

```sh
python3 verify_paley47_order.py
# P_47: the order makes 658 of 1081 arcs forward, so MAS >= 658 and alpha* >= 14/23
```

Since P₄₇ is arc-transitive, α\*(P₄₇) = MAS(P₄₇)/1081, so the order bounds α\* from below as well. The
gate (`tools/check_package.sh`, section 5) runs this check.
