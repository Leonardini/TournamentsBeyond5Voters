#!/usr/bin/env Rscript
# ----------------------------------------------------------------------------
# Definitive 5-realizability of the n=10 tournaments, with a 3-realizability
# pre-pass. Hierarchy: 3-realizable => 5-realizable (pad 3 voters to 5 copying
# the majority), so a 3-feasible tournament is cleared WITHOUT the 5-ILP, and any
# 5-counterexample must be 3-infeasible. Each tournament:
#   3-ILP (k=3): feasible -> 5-realizable, done.
#   else 5-ILP (k=5), status-aware: feasible -> 5-realizable; status 103 ->
#        PROVEN 5-INFEASIBLE (N(5) <= 10, the prize); time-limit -> inconclusive.
# Symmetry breaking = pin voter 1 lex-min wrt Aut(T) + sort the rest
# (breakSymmetry + breakVoterSymmetry). The 3-ILP uses return_permutations=FALSE
# (just the boolean -- no status needed, infeasible/timeout both fall through);
# the 5-ILP uses TRUE to read $status and separate 103 from a timeout.
#
#   Usage: Rscript ILP10/solve_ilp10.R <worker_id> <num_workers> <data> [outdir] [t3] [t5]
# ----------------------------------------------------------------------------
suppressMessages(source("ilp_realizability.R"))

args   <- commandArgs(trailingOnly = TRUE)
w      <- as.integer(args[1]); W <- as.integer(args[2]); data <- args[3]
outdir <- if (length(args) >= 4) args[4] else "ILP10/results"
t3     <- if (length(args) >= 5) as.numeric(args[5]) else 30    # 3-ILP: usually settles in ms
t5     <- if (length(args) >= 6) as.numeric(args[6]) else 300   # 5-ILP: only on 3-infeasibles
ckpt_secs <- if (length(args) >= 7) as.numeric(args[7]) else 600 # checkpoint cadence (s); resume a timed-out slice
stopifnot(!is.na(w), !is.na(W), w >= 0L, w < W)
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
if (length(list.files(outdir, pattern = sprintf("^ilp10_w%03d\\.RData$", w))) > 0L) {
  cat(sprintf("[ilp10 w%03d] output present -- skipping\n", w)); quit(save = "no")   # resumable
}

load_one <- function(f) { e <- new.env(); load(f, envir = e); stopifnot(length(ls(e)) == 1L); get(ls(e), envir = e) }
if (dir.exists(data)) {                                        # chunk mode: just this worker's chunk (avoids the 6 GB load + OOM)
  G <- load_one(file.path(data, sprintf("chunk_%03d.RData", w))); idx <- seq_along(G)
} else {                                                       # whole file, strided -- heavy with CPLEX; prefer chunks (split first)
  G <- load_one(data); idx <- seq.int(w + 1L, length(G), by = W)
}
n <- nrow(G[[1]]); prog <- max(2000L, length(idx) %/% 20L)
cat(sprintf("[ilp10 w%03d/%d] %d of %d tournaments (n=%d)  t3=%.0fs t5=%.0fs\n",
            w, W, length(idx), length(G), n, t3, t5)); flush.console()

verdict <- character(length(idx)); ce <- list(); inconcl <- list(); n3 <- 0L; n5 <- 0L; start_p <- 0L
ckpt_path <- file.path(outdir, sprintf("ilp10_w%03d_ckpt.RData", w))
if (file.exists(ckpt_path)) {                                  # resume a timed-out/killed run from mid-slice
  ck <- load_one(ckpt_path)
  if (!identical(ck$W, W) || !identical(ck$len, length(idx)))
    stop(sprintf("[ilp10 w%03d] checkpoint W/len mismatch (ckpt W=%d len=%d vs now %d/%d) -- resubmit with the original num_workers or delete %s",
                 w, ck$W, ck$len, W, length(idx), ckpt_path))
  verdict <- ck$verdict; ce <- ck$ce; inconcl <- ck$inconcl; n3 <- ck$n3; n5 <- ck$n5; start_p <- ck$ndone
  cat(sprintf("[ilp10 w%03d] resuming from checkpoint: %d/%d already done\n", w, start_p, length(idx))); flush.console()
}
save_ckpt <- function(ndone) {                                 # atomic write (tmp + rename) so a kill mid-save can't corrupt it
  ck <- list(w = w, W = W, len = length(idx), ndone = ndone,
             verdict = verdict, ce = ce, inconcl = inconcl, n3 = n3, n5 = n5)
  tmp <- paste0(ckpt_path, ".tmp"); save(ck, file = tmp); file.rename(tmp, ckpt_path)
}
todo <- if (start_p < length(idx)) seq.int(start_p + 1L, length(idx)) else integer(0)
last_ckpt <- Sys.time()
for (p in todo) {
  E <- G[[idx[p]]]
  feas3 <- test_k_realizability_ilp(E, k = 3, time_limit = t3, trace = 0,
                                    return_permutations = FALSE, breakSymmetry = TRUE, breakVoterSymmetry = TRUE)
  if (isTRUE(feas3)) {
    verdict[p] <- "5-realizable(3)"; n3 <- n3 + 1L
  } else {
    r5 <- test_k_realizability_ilp(E, k = 5, time_limit = t5, trace = 0,
                                   return_permutations = TRUE, breakSymmetry = TRUE, breakVoterSymmetry = TRUE)
    if (isTRUE(r5$feasible)) {
      verdict[p] <- "5-realizable"; n5 <- n5 + 1L
    } else if (identical(r5$status, 103L)) {
      verdict[p] <- "5-INFEASIBLE"
      ce[[length(ce) + 1L]] <- list(index = idx[p], adj = E, status = r5$status)
      cat(sprintf("[ilp10 w%03d] *** PROVEN 5-INFEASIBLE at index %d  =>  N(5) <= %d ***\n", w, idx[p], n)); flush.console()
    } else {
      verdict[p] <- "5-inconclusive"
      inconcl[[length(inconcl) + 1L]] <- list(index = idx[p], adj = E, status5 = r5$status)
    }
  }
  if (p %% prog == 0L) {
    cat(sprintf("[ilp10 w%03d] %d/%d  (3feas=%d 5feas=%d 5INF=%d incon=%d)\n",
                w, p, length(idx), n3, n5, length(ce), length(inconcl))); flush.console()
  }
  if (p %% 2000L == 0L) invisible(gc(verbose = FALSE))         # keep per-call Rcplex churn from accumulating
  if (as.numeric(Sys.time() - last_ckpt, units = "secs") >= ckpt_secs) { save_ckpt(p); last_ckpt <- Sys.time() }
}
out <- list(w = w, W = W, n = n, count = length(idx),
            n_3feasible = n3, n_5feasible_via5 = n5,
            n_5infeasible = length(ce), n_inconclusive = length(inconcl),
            counterexamples = ce, inconclusive = inconcl, verdict_table = table(verdict))
save(out, file = file.path(outdir, sprintf("ilp10_w%03d.RData", w)))
if (file.exists(ckpt_path)) invisible(file.remove(ckpt_path))  # slice complete -> drop the checkpoint
cat(sprintf("[ilp10 w%03d] DONE  3feas=%d  5feas(via5)=%d  5INFEAS=%d  inconclusive=%d\n",
            w, n3, n5, length(ce), length(inconcl)))
