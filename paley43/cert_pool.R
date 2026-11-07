#!/usr/bin/env Rscript
# 5-realizability certificate WITHOUT alpha*: build a pool of good orders (insertion local
# search for high forward-edge count) + their Aut(Paley) orbits, then a 5-cover ILP, then an
# INDEPENDENT majority check.  A hit certifies 5-inducibility; a miss is inconclusive.
# NB: Rcplex is loaded lazily inside solve_cover (its only user) so that merely sourcing
# this file for paley_adj/majority_equals (e.g. real5_ilp.R's cplexAPI-only HPC path) does
# not require Rcplex, which is not reliably available on every cluster.

# pick multiplicities x>=0 int, sum=5, cons %*% x >= 3 (every edge agreed by >=3 of the 5)
solve_cover <- function(cons) {
  suppressMessages(library(Rcplex))   # lpSolve B&B chokes on 1000+ binary cover vars; CPLEX is instant
  P <- ncol(cons); C <- nrow(cons)
  res <- Rcplex(cvec = rep(0, P), Amat = rbind(rep(1, P), cons), bvec = c(5, rep(3, C)),
                sense = c("E", rep("G", C)), vtype = rep("I", P),
                lb = rep(0, P), ub = rep(5, P), objsense = "min",
                control = list(trace = 0, tilim = 180))   # cap: feasible covers are found fast
  x <- res$xopt
  if (is.null(x) || anyNA(x)) return(NULL)                          # infeasible -> Rcplex returns NA xopt
  x <- round(x)
  if (sum(x) != 5 || any(as.vector(cons %*% x) < 3)) return(NULL)   # invalid
  rep(seq_len(P), x)
}

paley_adj <- function(q) {
  qr <- sort(unique(((1:((q - 1) / 2))^2) %% q))
  A <- matrix(0L, q, q)
  for (i in 0:(q - 1)) for (j in 0:(q - 1))
    if (i != j && ((j - i) %% q) %in% qr) A[i + 1, j + 1] <- 1L
  A
}
paley_auts <- function(q) {                          # {v -> a v + b : a in QR}, order q(q-1)/2
  qr <- sort(unique(((1:((q - 1) / 2))^2) %% q)); out <- list()
  for (a in qr) for (b in 0:(q - 1)) out[[length(out) + 1]] <- ((a * (0:(q - 1)) + b) %% q) + 1L
  out
}
fwd_count <- function(ord, A) { pos <- integer(nrow(A)); pos[ord] <- seq_along(ord)
  idx <- which(A == 1L, arr.ind = TRUE); sum(pos[idx[, 1]] < pos[idx[, 2]]) }

# insertion local search: reinsert each vertex at its forward-optimal position.
# Move ONLY on STRICT improvement vs v's current slot (ties would otherwise oscillate forever).
insertion_ls <- function(A, ord) {
  n <- length(ord); improved <- TRUE
  while (improved) { improved <- FALSE
    for (v in ord) {
      curpos <- match(v, ord)                                  # v sits after (curpos-1) of rest
      rest <- ord[ord != v]
      a_uv <- A[cbind(rest, v)]; a_vu <- A[cbind(v, rest)]      # u->v ; v->u  for u in rest
      gains <- c(0, cumsum(a_uv)) + (sum(a_vu) - c(0, cumsum(a_vu)))  # k=0..n-1 -> index k+1
      best <- which.max(gains)
      if (gains[best] > gains[curpos] + 1e-9) {                # strict gain only
        ord <- append(rest, v, after = best - 1L); improved <- TRUE
      }
    }
  }
  ord
}
majority_equals <- function(orders, A) {
  n <- nrow(A); pref <- matrix(0L, n, n)
  for (ord in orders) { pos <- integer(n); pos[ord] <- 1:n
    pref <- pref + outer(1:n, 1:n, function(i, j) as.integer(pos[i] < pos[j])) }
  M <- (pref > t(pref)) * 1L; diag(M) <- 0L; all(M == A)
}

cert5_pool <- function(A, auts, label, n_restart = 80L) {
  n <- nrow(A); pairs <- t(combn(n, 2))
  af <- ifelse(A[pairs] == 1L, pairs[, 1], pairs[, 2])
  at <- ifelse(A[pairs] == 1L, pairs[, 2], pairs[, 1])
  agree <- function(ord) { pos <- integer(n); pos[ord] <- 1:n; as.integer(pos[af] < pos[at]) }
  orbit_cons <- function(s) { pool <- lapply(auts, function(P) P[s]); cs <- sapply(pool, agree)
    k <- !duplicated(t(cs)); list(pool = pool[k], cons = cs[, k, drop = FALSE]) }
  report <- function(o, sel, src) {
    five <- o$pool[sel]; ok <- majority_equals(five, A)
    marg <- as.vector(o$cons[, sel, drop = FALSE] %*% rep(1, length(sel)))
    cat(sprintf("  5-COVER (%s): independent majority==T: %s | margins %s\n", src, ok,
                paste(sprintf("%d@%d", tabulate(marg, 5)[3:5], 3:5), collapse = ", "))); flush.console()
    invisible(list(certified = ok, orders = five)) }

  base <- lapply(1:n_restart, function(i) insertion_ls(A, sample(n)))
  fc <- sapply(base, fwd_count, A = A); mx <- max(fc)
  maxord <- base[fc == mx]; maxord <- maxord[!duplicated(sapply(maxord, paste, collapse = ","))]
  cat(sprintf("[%s] n=%d C=%d | MAS=%d | %d distinct max-acyclic seeds | |Aut|=%d\n",
              label, n, nrow(pairs), mx, length(maxord), length(auts))); flush.console()

  # (1) the alpha*-support pool = a SINGLE Aut-orbit of one max-acyclic order (small ILP, instant)
  orbits <- lapply(maxord, orbit_cons)
  for (i in seq_along(orbits)) {
    sel <- solve_cover(orbits[[i]]$cons)
    if (!is.null(sel)) return(report(orbits[[i]], sel, sprintf("orbit %d of %d", i, length(orbits))))
  }
  cat(sprintf("  no single-orbit 5-cover (%d max-orbits)\n", length(orbits))); flush.console()
  # (2) fallback: union of all max-orbits
  pool <- do.call(c, lapply(orbits, function(o) o$pool)); cs <- sapply(pool, agree)
  k <- !duplicated(t(cs)); o <- list(pool = pool[k], cons = cs[, k, drop = FALSE])
  cat(sprintf("  union pool: %d distinct orders\n", ncol(o$cons))); flush.console()
  sel <- solve_cover(o$cons)
  if (!is.null(sel)) return(report(o, sel, "union of max-orbits"))
  cat("  INCONCLUSIVE (no 5-cover in max-acyclic orbit pools)\n"); invisible(list(certified = NA))
}

if (sys.nframe() == 0L) {            # run only when executed directly, not when sourced
  args <- commandArgs(trailingOnly = TRUE)
  qs <- if (length(args)) as.integer(args) else c(11, 23)
  for (q in qs) cert5_pool(paley_adj(q), paley_auts(q), sprintf("Paley(%d)", q))
}
