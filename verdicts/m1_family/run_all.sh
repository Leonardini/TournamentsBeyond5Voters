#!/bin/bash
set -u
cd "$(dirname "$0")"
{
./sweep.sh p23mv p23_minus1v.bits 22 "0 1 2 5 11"
./sweep.sh p27   p27_paley.bits   27 "0 1 2 3 14"
./sweep.sh p27e  p27_arcrev.bits  27 "0 1 2 4 6"
./sweep.sh p27mv p27_minus1v.bits 26 "0 1 2 6 12"
./sweep.sh p31   p31_paley.bits   31 "0 1 2 3 12"
./sweep.sh p31e  p31_arcrev.bits  31 "0 1 2 4 12"
./sweep.sh p31mv p31_minus1v.bits 30 "0 1 2 3 12"
} 2>&1 | tee -a results.txt
echo ALL_DONE >> results.txt
