# Paste-able command block for Jean-Zay: is Paley(23) arc-critical?

I do not connect to JZ. Run these yourself; each step names exactly what to
paste back, so one round trip per step is enough.

## What this decides

`T^e` is Paley(23) with the arc `(0,1)` reversed. Paley(23) itself is not
5-inducible. `Aut(Paley(23))` has order 253, which equals its number of arcs, so
the group is **regular on arcs** and every arc is equivalent to every other:
reversing one representative settles all 253.

* **SAT** — `T^e` is 5-inducible, so **Paley(23) IS arc-critical**. Arc-criticality
  implies vertex-criticality, so that question closes at the same time.
* **UNSAT** — Paley(23) is not arc-critical.

Reversing an arc destroys all symmetry: `|Aut(T^e)| = 1`, out-degrees `{10,11,12}`.
So **no symmetry break is available** and all 8031 base states are live. That is
the whole reason this costs ~500 core-h where the broken Paley(23) sweep cost 34.

Set once per shell — and **export**, so the variables survive `salloc`/`sbatch`:

    export REPO=<path to the repo on JZ>
    export GENTOURNG=<path to gentourng>     # not used here, but the array inherits it

---

## 1. Build

    cd $REPO/KInduceDFS/jz_p23arc && ./build.sh

**Send back:** the last 3 lines. It must end with `build OK.`

This builds the consolidated engine `kinduce`, not one of the archived
`versions/`. No generator is needed — the host is a fixed bit string in the
repo, unlike the n=15 kit.

---

## 2. Known-answer gate — MANDATORY

    cd $REPO/KInduceDFS && ./jz_p23arc/selftest.sh

**Send back:** the whole output. Every line must read PASS.

Two of the checks are genuinely discriminating rather than merely "it ran":

* `p19_arcrev` at margin 1 **must be SAT** — a witness exists and must be found.
  An engine that refutes everything fails here.
* `p27_arcrev` at margin 1, first 40 base states, **must be UNSAT** — that host
  is margin-1 UNSAT over all 2200 base states, so every slice of it is too. An
  engine that accepts anything fails here.

It also confirms the host really is Paley(23) with exactly `(0,1)` reversed, that
the base `{0,1,2,6,15}` gives 8031 base states, and that the driver writes and
respects its done markers.

**If any line says FAIL, do not submit.**

---

## 3. One base state interactively, to confirm the rate

    cd $REPO
    salloc --account=lia@cpu --partition=cpu_p1 --qos=qos_cpu-t3 \
           --ntasks=1 --cpus-per-task=1 --hint=nomultithread --time=00:30:00

then, in the allocated shell:

    echo "$REPO"                                   # must be non-empty
    time $REPO/KInduceDFS/jz_p23arc/screen_chunk.sh 0 /tmp/p23arctry
    exit

**Send back:** the `base=0 unsat time=...s` line and the `real` time.

Laptop reference is **224.1 s per base state**, measured at matched load. Under
~700 s means JZ is within about 3x and the array is comfortable. The `--time`
here is 30 min, so a base state slower than 1800 s is reported only as a kill —
if that happens, re-probe at `--time=02:00:00` before sizing the array.

`/tmp/p23arctry` is throwaway, deliberately: it must not write into
`jz_p23arc/results`, or the real array would skip base state 0.

---

## 4. Submit the array

    cd $REPO
    sbatch KInduceDFS/jz_p23arc/p23arc.slurm

**Send back:** the job id.

268 single-core tasks, ~30 base states each, `--time=20:00:00`. At the measured
rate that is ~1.9 h per task and **~500 core-h** in total.

Base states are assigned **strided** — task `T` takes `T, T+268, T+536, ...` —
not in blocks. A block assignment would concentrate any systematic cost gradient
into a few tasks; strided spreads it, so tasks finish in comparable time and
partial progress is even across the whole index range.

---

## 5. Progress, at any time

    cd $REPO && KInduceDFS/jz_p23arc/aggregate.sh

Prints base states screened, witnesses, core-hours, mean per base state, a
projected total, and the **index cover** — missing and unexpected indices. Safe
to run mid-job.

---

## 6. Resume after a timeout or cancel

Resubmit the identical line. Completed base states are skipped via their
`results/done/<b>` markers.

    cd $REPO && sbatch KInduceDFS/jz_p23arc/p23arc.slurm

A marker is written **only on `RESULT UNSAT`**, so a capped or wall-killed base
state leaves none and is retried automatically. This also means the exact index
cover of `done/` **is** the completeness certificate — never infer completeness
from a count, because gaps and duplicates can cancel.

---

## If a witness turns up

Every task checks for `results/STOP` before each base state, so the array winds
itself down within one base state of the find. The witness is in
`results/witness/b<n>.log`. **Verify it before believing it:**

    cd $REPO/KInduceDFS
    python3 verify_witness_bits.py jz_p23arc/results/witness/b<n>.log \
            p23_arcrev.bits 23 5 --majority

That script shares no code with the search. It must print `VERIFIED`, and the
support histogram must show every one of the 253 arcs at 3 or more of 5.
