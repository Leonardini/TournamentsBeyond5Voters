# Paste-able command block for Jean-Zay

I do not connect to JZ. Run these yourself; each step names exactly what to
paste back, so one round trip per step is enough.

Set this once per shell:

    REPO=$WORK/KemenyMedian        # wherever the repo lives on JZ

---

## 1. Update the code and build

    cd $REPO && git pull
    cd $REPO/KInduceDFS/jz_n15 && ./build.sh

**Send back:** the last 5 lines. It must end with `build OK.`

Nauty is already on JZ, so nothing is fetched. Known-good tree:

    NAUTY=/lustre/fswork/projects/rech/lia/uex76wa/nauty2_9_3

`gentourng` is a separate build target from nauty's library, so a tree set up
for pynauty may not have the binary yet. Build only that target — it touches
nothing else:

    ls -l $NAUTY/gentourng || {
      cd $NAUTY
      [ -f makefile ] || ./configure          # only if not already configured
      make gentourng
    }
    export GENTOURNG=$NAUTY/gentourng
    $GENTOURNG -help | head -3                # must list -d# -D# and res/mod

    cd $REPO/KInduceDFS/jz_n15 && ./build.sh

`build.sh` then only compiles `kinduce20`. Every script resolves the
generator as `$GENTOURNG` → `$NAUTY_DIR/gentourng` → `gentourng` on `PATH` →
a local build, so any of those works. **Keep `GENTOURNG` exported in the shell
you submit from** — `sbatch` passes your environment to the job by default, and
the array tasks need it. If in doubt, submit it explicitly:

    sbatch --export=ALL,GENTOURNG="$GENTOURNG" KInduceDFS/jz_n15/n15_margin1.slurm

---

## 2. Known-answer gate — MANDATORY

    cd $REPO/KInduceDFS/jz_n15 && ./selftest.sh

**Send back:** the whole output, about 15 lines. Every line must read PASS.

It checks the generator against OEIS A096368 counts (1, 3, 15, 1223,
1495297) and the engine against verdicts established locally on 2026-09-02:
regular n=9 → `15/0` at k=5 and `7/8` at k=3; regular n=11 → `1223/0` at k=5
and `48/1175` at k=3 (those pairs are SAT/UNSAT).

**If any line says FAIL, do not submit** — the toolchain there is not
reproducing known results and the sweep would be worthless.

---

## 3. One residue interactively, to confirm shape and rate

    cd $REPO
    srun --account=lia@cpu --partition=cpu_p1 --qos=qos_cpu-t3 \
         --ntasks=1 --cpus-per-task=1 --hint=nomultithread --time=00:30:00 \
         KInduceDFS/jz_n15/screen_residue.sh 0 6000 /tmp/n15try exact

**Send back:** the single `res=0 instances=... unsat=... secs=...` line.

Residue 0 holds **3,205,018** instances (measured, not the 2.0M average the
first version of this file assumed -- `gentourng` balances tree shape, not
output count; residues range 2.16M..5.02M, see `residue_sizes.txt`).  On the
laptop that residue takes **417 s** end to end: 94 s generation (29.3 us/inst)
+ 323 s search (100.8 us/inst).  So `secs` near 420 means JZ matches the
laptop; the 2026-09-02 attempt was killed at the 1800 s wall, i.e. >= 4.3x
slower, which is more than the ~2-2.5x a Cascade Lake core should cost.
Report `secs` before submitting the array either way.

---

## 4. Submit the array

    cd $REPO
    mkdir -p KInduceDFS/jz_n15/slurm          # normally already present from git
    sbatch KInduceDFS/jz_n15/n15_margin1.slurm

**Send back:** the job id.

600 single-core tasks, 10 residues each. **~69 min per task, ~694 core-h
total** at the laptop rate. The slurm file carries `--time=20:00:00`, which is
ample headroom for uneven residues (they range 2.16M..5.02M instances).

These figures are the CORRECTED ones. An earlier version of this file said
~52 min and ~523 core-h, from an instance total of 12,007,554,066 that appears
in no term of OEIS A096368. The true count is **A096368(7) = 18,400,989,629**,
1.53x higher. If you see the old numbers anywhere, they are wrong.

---

## 5. Progress, at any time

    cd $REPO && KInduceDFS/jz_n15/aggregate.sh

**Send back:** the whole output. It prints residues done of 6000, instances
screened, total UNSAT, aborted count, core-hours spent, and a projected total.
Safe to run mid-job.

---

## 6. Resume after a timeout or cancel

Resubmit the identical line. Finished residues are skipped via their
`results_margin1/done/r<res>` markers, so nothing is recomputed.

    cd $REPO && sbatch KInduceDFS/jz_n15/n15_margin1.slurm

To rerun a subset deliberately, delete just those markers first.

---

## If any UNSAT turns up

That is the result: a non-5-inducible regular tournament on 15 vertices, which
gives **N(5) ≤ 15** once the majority check confirms it.

    cd $REPO && cat KInduceDFS/jz_n15/results_margin1/unsat/*.bits

**Send back:** that output. Each is one 105-character line, so paste it
directly — no transfer needed. I will verify it locally against an independent
checker and run the stage-2 majority confirmation.
