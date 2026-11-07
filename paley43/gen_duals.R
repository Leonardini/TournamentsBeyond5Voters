#!/usr/bin/env Rscript
# gen_duals.R — build a diverse family of triangle-packing dual certificates on
# Paley(43) for the budget-DP complement bound (Leonid's design, 2026-07-07).
#
# Soundness: a packing y with per-arc load <= 1 on the FULL graph stays feasible
# on every induced sub, so W_y(T) = sum of y over triangles inside T is a valid
# lower bound on minback(T); max over a family is valid too. We steer diversity
# through the DUAL objective (rewards r on triangles) — capacities stay 1, and
# the certificate is always evaluated UNWEIGHTED. r = indicator(triangle in R)
# makes the solve exactly the max packing of the induced sub on R (localized).
# Engine complements never contain vertex 1 (the anchor), so regions and the
# scoring panel are sampled from vertices 2..43.
#
# Usage: Rscript gen_duals.R <nsolves> <out.rds> [seed]
# Prints, every 10 solves: behavioral novelty (distinct restricted behavior on
# the panel), weight-multiset novelty (Aut-invariant), and the recovery curve
# mean(bestW/tau*) — tau* itself recovers ~94% of exact minback (tri_lp.R).
# Checkpoints every 50 solves (out.rds is complete/loadable at any time).
suppressMessages({ source("cert_pool.R"); library(slam); library(Rcplex) })

a <- commandArgs(trailingOnly = TRUE)
nsolves <- as.integer(a[1]); outrds <- a[2]
set.seed(if (length(a) >= 3) as.integer(a[3]) else 4343)

q <- 43L
A <- paley_adj(q)
arcs <- which(A == 1L, arr.ind = TRUE)
narc <- nrow(arcs)
aid <- matrix(0L, q, q)
for (e in seq_len(narc)) aid[arcs[e, 1], arcs[e, 2]] <- e

# cyclic 3-subsets and the arc x triangle incidence
triples <- t(combn(q, 3))
ori1 <- A[triples[, c(1, 2)]] & A[triples[, c(2, 3)]] & A[triples[, c(3, 1)]]
ori2 <- A[triples[, c(1, 3)]] & A[triples[, c(3, 2)]] & A[triples[, c(2, 1)]]
cyc <- ori1 | ori2
tri <- triples[cyc, , drop = FALSE]
fwd <- ori1[cyc]                      # TRUE: x->y->z->x, else x->z->y->x
ntri <- nrow(tri)
stopifnot(ntri == q * (q - 1) * (q + 1) / 24)   # 3311 for q=43
ii <- integer(0); jj <- integer(0)
for (k in seq_len(ntri)) {
  x <- tri[k, 1]; y <- tri[k, 2]; z <- tri[k, 3]
  es <- if (fwd[k]) c(aid[x, y], aid[y, z], aid[z, x]) else c(aid[x, z], aid[z, y], aid[y, x])
  ii <- c(ii, es); jj <- c(jj, rep(k, 3))
}
Ainc <- simple_triplet_matrix(ii, jj, rep(1, length(ii)), nrow = narc, ncol = ntri)

in_region <- function(R) tri[, 1] %in% R & tri[, 2] %in% R & tri[, 3] %in% R

solve_pack <- function(robj) {
  s <- Rcplex(cvec = robj, Amat = Ainc, bvec = rep(1, narc), sense = "L",
              objsense = "max", lb = 0, ub = Inf, vtype = "C",
              control = list(trace = 0))
  y <- s$xopt
  y[y < 1e-9] <- 0
  y
}

# scoring panel: fixed complements T (t = 21, no vertex 1) with exact tau*(T)
npanel <- 40L
panel <- lapply(seq_len(npanel), function(i) sort(sample(2:q, 21)))
MT <- do.call(rbind, lapply(panel, in_region)) * 1        # npanel x ntri
tauT <- sapply(panel, function(T) sum(solve_pack(as.numeric(in_region(T))) * in_region(T)))
cat(sprintf("[gen_duals] q=43 arcs=%d cyclic-triangles=%d | panel %d complements t=21, tau* mean %.1f\n",
            narc, ntri, npanel, mean(tauT)))

packs <- list()
bestW <- rep(0, npanel)
sigs_w <- character(0)                 # Aut-invariant weight-multiset signatures
sigs_b <- character(0)                 # behavioral signatures on the panel
for (k in seq_len(nsolves)) {
  mode <- k %% 3L
  if (mode == 1L) {
    r <- runif(ntri)
  } else {
    R <- sample(2:q, sample(c(21, 25, 30), 1))
    r <- as.numeric(in_region(R))
    if (mode == 0L) r <- r + 0.05 * runif(ntri)
  }
  yk <- solve_pack(r)
  Wp <- as.vector(MT %*% yk)
  bestW <- pmax(bestW, Wp)
  sigs_w <- union(sigs_w, paste(sort(round(yk[yk > 0], 6)), collapse = ","))
  sigs_b <- union(sigs_b, paste(round(Wp, 3), collapse = ","))
  nz <- which(yk > 0)
  packs[[k]] <- list(idx = nz, val = yk[nz], mode = mode)
  if (k %% 10L == 0L)
    cat(sprintf("[%4d] novel: behavior %d, multiset %d | recovery mean(bestW/tau*) = %.3f (min %.3f)\n",
                k, length(sigs_b), length(sigs_w), mean(bestW / tauT), min(bestW / tauT)))
  if (k %% 50L == 0L || k == nsolves)
    saveRDS(list(q = q, tri = tri, fwd = fwd, packs = packs, panel = panel,
                 tauT = tauT, bestW = bestW, nsolved = k), outrds)
}
cat(sprintf("[gen_duals] done: %d packings -> %s | final recovery %.3f\n",
            nsolves, outrds, mean(bestW / tauT)))
