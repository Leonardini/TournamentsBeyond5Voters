#!/usr/bin/env Rscript
# ----------------------------------------------------------------------------
# Combine the ILP10 worker slices into the n=10 5-realizability verdict:
# how many cleared by the 3-ILP, how many needed the 5-ILP, any proven
# 5-INFEASIBLE (status 103 => N(5)=10), and any inconclusive (5-ILP timed out).
#   Usage: Rscript ILP10/ilp10_aggregate.R [outdir] [expected_workers=200]
# ----------------------------------------------------------------------------
args     <- commandArgs(trailingOnly = TRUE)
outdir   <- if (length(args) >= 1) args[1] else "ILP10/results"
expected <- if (length(args) >= 2) as.integer(args[2]) else 200L
files    <- list.files(outdir, pattern = "^ilp10_w[0-9]+\\.RData$", full.names = TRUE)
stopifnot(length(files) > 0)
present  <- sort(as.integer(sub(".*_w0*([0-9]+)\\.RData$", "\\1", basename(files))))
missing  <- setdiff(seq.int(0L, expected - 1L), present)

total <- 0L; n3 <- 0L; n5 <- 0L; ninf <- 0L; ninc <- 0L; ce <- list(); inc <- list(); n <- NA
for (f in files) { e <- new.env(); load(f, envir = e); o <- e$out
  total <- total + o$count; n3 <- n3 + o$n_3feasible; n5 <- n5 + o$n_5feasible_via5
  ninf <- ninf + o$n_5infeasible; ninc <- ninc + o$n_inconclusive
  ce <- c(ce, o$counterexamples); inc <- c(inc, o$inconclusive); n <- o$n
}
cat(sprintf("ILP 5-realizability sweep of %d tournaments on n=%d across %d workers\n", total, n, length(files)))
cat(sprintf("  3-feasible  (=> 5-realizable, cleared by 3-ILP): %d  (%.1f%%)\n", n3, 100 * n3 / total))
cat(sprintf("  3-infeasible then 5-realizable (via 5-ILP):      %d  (%.1f%%)\n", n5, 100 * n5 / total))
cat(sprintf("  5-INFEASIBLE (status 103):                       %d\n", ninf))
cat(sprintf("  inconclusive (5-ILP hit the time limit):         %d\n", ninc))

summary <- list(total = total, n = n, n_3feasible = n3, n_5feasible_via5 = n5,
                n_5infeasible = ninf, n_inconclusive = ninc, counterexamples = ce, inconclusive = inc)
save(summary, file = file.path(outdir, sprintf("ilp10_summary_n%02d.RData", n)))

if (ninf > 0L) {                                                # a counterexample is definitive regardless of coverage
  cat(sprintf("\n*** %d tournament(s) PROVEN 5-INFEASIBLE => N(5) = %d! (summary$counterexamples) ***\n", ninf, n))
} else if (length(missing) > 0L) {                             # INCOMPLETE: do NOT claim a definitive lower bound
  cat(sprintf("\nINCOMPLETE: %d of %d workers reported; %d MISSING: %s\n", length(present), expected, length(missing),
              paste(missing, collapse = " ")))
  cat(sprintf("  0 infeasible / %d inconclusive across %d tournaments SO FAR -- N(5)>%d is NOT yet settled.\n", ninc, total, n))
  cat(sprintf("  Finish the missing workers (resubmit --array=0-%d keeping W=%d so the slices stay correct; done ones skip), then re-aggregate.\n",
              expected - 1L, expected))
} else if (ninc > 0L) {
  cat(sprintf("\nNone proven 5-infeasible, but %d inconclusive (route to longer 5-ILP / DFS / cplexAPI_obstacle.R).\n", ninc))
} else {
  cat(sprintf("\nAll %d workers reported. Every n=%d tournament is 5-realizable => N(5) > %d, settled definitively.\n", expected, n, n))
}
