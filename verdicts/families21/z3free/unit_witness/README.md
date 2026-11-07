# The one order-3 class that five voters produce at unit margin

`z3c21_15.log` is a unit-margin (every arc 3–2) five-voter witness for host `z3c21_15` of `../HOSTS.tsv`,
the 31st class of the family with a fixed-point-free automorphism of order 3; the other 30 classes are
5-inducible only at majority (manuscript Appendix C, Table of the families on 21 vertices).

The host string is identical to `z3f21_15`, under which the search first found this witness. To rerun:

    cc -O3 -o kinduce engine/kinduce.c -lm
    awk '$1=="z3c21_15"{print $2}' verdicts/families21/z3free/HOSTS.tsv > z3c21_15.bits
    ./kinduce --bits z3c21_15.bits --n 21 --k 5 --margin exact --order mrv --inc \
              --base 9 11 13 16 20 --bs-from 143 --bs-to 144      # about 5 s
    python3 verify/unit_margin_witness.py z3c21_15.bits verdicts/families21/z3free/unit_witness/z3c21_15.log 5
