#!/usr/bin/env Rscript
#
# ILP-based k-realizability checker using CPLEX
# Uses "before" variables and transitivity constraints

library(Rcplex)
library(igraph)
library(Matrix)
source("Utilities.R")

#' Extract permutations from ILP solution
#' @param solution The xopt vector from CPLEX
#' @param k Number of permutations
#' @param n Number of vertices
#' @return List of k permutations, or NULL if solution is invalid
extract_permutations <- function(solution, k, n) {
  if (is.null(solution) || length(solution) != k * n * n) {
    return(NULL)
  }
  
  # Round to nearest integer (should be binary already)
  solution <- round(solution)
  
  # Extract b[i,u,v] values
  get_b <- function(i, u, v) {
    idx <- (i-1)*n*n + (u-1)*n + v
    return(solution[idx])
  }
  
  permutations <- vector("list", k)
  names(permutations) = paste0("pi", 1:k)
  
  for (i in 1:k) {
    # Build adjacency matrix for this permutation
    # b[i,u,v] = 1 means u comes before v
    adj <- matrix(0, n, n)
    for (u in 1:n) {
      for (v in 1:n) {
        if (u != v) {
          adj[u, v] <- get_b(i, u, v)
        }
      }
    }
    
    # Use igraph to check if it's a DAG and get topological order
    G <- graph_from_adjacency_matrix(adj, mode = "directed")
    if (!is_dag(G)) {
      warning(sprintf("Permutation %d: Graph is not a DAG", i))
      return(NULL)
    }
    permutations[[i]] <- as.integer(topo_sort(G, mode = "out"))
  }

  return(permutations)
}

#' Convert adjacency matrix to edge list
#' @param adj_matrix n×n matrix where adj_matrix[i,j]=1 means edge i→j
#' @return 2-column matrix of edges
adj_matrix_to_edges <- function(adj_matrix) {
  n <- nrow(adj_matrix)
  edges <- which(adj_matrix == 1, arr.ind = TRUE)
  colnames(edges) <- c("from", "to")
  return(edges)
}

#' Test k-realizability using ILP formulation
#' @param edges Either a 2-column matrix of edges (from, to) OR an adjacency matrix
#' @param k Number of permutations
#' @param require_margin1 If TRUE, require exactly (k+1)/2 split; if FALSE, allow >= (k+1)/2
#' @param time_limit Time limit in seconds (default: 300)
#' @param return_permutations If TRUE, return list with 'feasible' and 'permutations'; if FALSE, just return TRUE/FALSE
#' @param breakSymmetry If TRUE, break the vertex-automorphism symmetry of T by pinning voter 1
#'        to the lexicographically minimal order in its Aut(T)-orbit (via computeComparisons)
#' @param breakVoterSymmetry If TRUE, break the voter-interchange (S_k) symmetry by requiring the
#'        voters to be sorted lexicographically on their precedence-bit encoding. When voter 1 is
#'        pinned by breakSymmetry, only voters 2..k are sorted (which is still valid); otherwise all
#'        voters 1..k are sorted.
#' @return If return_permutations=FALSE: TRUE if k-realizable, FALSE otherwise
#'         If return_permutations=TRUE: list(feasible = TRUE/FALSE, permutations = list of k perms or NULL)
test_k_realizability_ilp <- function(edges, k, require_margin1 = FALSE, time_limit = 300,
                                     return_permutations = FALSE, breakSymmetry = TRUE,
                                     breakVoterSymmetry = TRUE, trace = 1, mipemphasis = 1) {
  # Auto-detect format: if square matrix, assume adjacency matrix
  if (ncol(edges) == nrow(edges)) {
    edges <- adj_matrix_to_edges(edges)
  }
  
  n <- max(edges)

  # Variables: b[i,u,v] for i=1..k, u,v in 1..n
  # b[i,u,v] = 1 if vertex u comes before vertex v in permutation i
  # Diagonal variables (u=v) are unused but simplify indexing
  var_index <- function(i, u, v) {
    return((i-1)*n*n + (u-1)*n + v)
  }

  n_base <- k * n * n

  # Upper-triangle pair list (u < v) in a fixed order. The bits b[i,u,v] over these pairs
  # uniquely encode voter i's linear order, so lexicographic order on this bit vector is a
  # valid total order on permutations -- used below for voter symmetry breaking.
  coordPairs <- t(combn(n, 2))   # m x 2, rows (u, v) with u < v
  m <- nrow(coordPairs)

  # ----- Symmetry handling -----
  # Two symmetries can be broken: the vertex-automorphism group Aut(T) (acting on vertex
  # labels) and the voter-interchange group S_k (the k voters are interchangeable). They are
  # broken by two valid schemes:
  #   (A) "pin" voter 1 to the lexicographically minimal order in its Aut(T)-orbit (via
  #       computeComparisons) AND sort voters 2..k lexicographically -> reduction |Aut(T)|*(k-1)!
  #   (B) sort all k voters lexicographically, no pin                  -> reduction k!
  # (A) and (B) tie at |Aut(T)| = k; since (A) uses one fewer lex block (cheaper in auxiliary
  # variables), we prefer (A) whenever |Aut(T)| >= k and use (B) only when |Aut(T)| < k.
  # Sorting voters 2..k on top of a pinned voter 1 is valid because Aut(T) acts on vertex
  # labels while S_{k-1} permutes only voters 2..k, so every orbit retains a representative
  # satisfying both. The lex order is non-strict (pi_lo <=_lex pi_hi), so identical voter
  # profiles are permitted and no realization is excluded.
  iG <- graph_from_edgelist(edges, directed = TRUE)
  autSize <- if (breakSymmetry || breakVoterSymmetry) {
    as.numeric(count_automorphisms(iG)$group_size)
  } else {
    1
  }
  if (breakSymmetry && breakVoterSymmetry) {
    use_pin <- autSize >= k              # scheme (A) iff it ties or beats full voter sort
  } else {
    use_pin <- breakSymmetry             # single-flag use: pin iff Aut-breaking requested
  }
  comps <- if (use_pin) computeComparisons(iGraph = iG) else NULL
  voter1_pinned <- use_pin && !is.null(comps)

  voterPairs <- matrix(integer(0), ncol = 2)
  if (breakVoterSymmetry && k >= 2) {
    firstVoter <- if (voter1_pinned) 2L else 1L
    if (firstVoter <= k - 1L) {
      voterPairs <- cbind(firstVoter:(k - 1L), (firstVoter + 1L):k)
    }
  }
  P <- nrow(voterPairs)

  # Auxiliary binaries for the lexicographic comparisons: per ordered voter pair p and per
  # coordinate t we add eq[p,t] (= 1 iff the two voters agree on coordinate t) and g[p,t]
  # (= 1 iff they agree on all coordinates 1..t). g[p,0] := 1 is inlined.
  aux_offset <- n_base
  eq_index <- function(p, t) aux_offset + (p - 1L) * (2L * m) + t
  g_index  <- function(p, t) aux_offset + (p - 1L) * (2L * m) + m + t
  num_vars <- n_base + P * 2L * m

  # Build constraints as sparse rows. Per constraint we record only its nonzero column
  # indices and values (plus sense and rhs) in preallocated parallel structures -- O(1) per
  # row, avoiding both the dense coefficient vectors and the O(n^2) list growth of the old
  # build -- then assemble a single slam sparse matrix for Rcplex. (This is what lets larger
  # orders, e.g. Paley(19), build at all.)
  target <- (k + 1) / 2
  edge_sense <- if (require_margin1) "E" else "G"
  n_edges <- nrow(edges)

  maxRows <- k * m +                                       # antisymmetry (one row per pair)
             k * n * (n - 1) * (n - 2) +                   # transitivity (ordered triples)
             n_edges +                                     # majority
             (if (voter1_pinned) nrow(comps) else 0L) +    # voter-1 pin
             P * 8L * m + 10L                              # voter lex (<= 8 rows / coord) + slack

  Lcols  <- vector("list", maxRows)
  Lvals  <- vector("list", maxRows)
  Lsense <- character(maxRows)
  Lrhs   <- numeric(maxRows)
  cpos   <- 0L

  # 1. Antisymmetry: b[i,u,v] + b[i,v,u] = 1  (one row per unordered pair {u,v})
  for (i in 1:k) {
    for (t in 1:m) {
      u <- coordPairs[t, 1]; v <- coordPairs[t, 2]
      cpos <- cpos + 1L
      Lcols[[cpos]] <- c(var_index(i, u, v), var_index(i, v, u))
      Lvals[[cpos]] <- c(1, 1)
      Lsense[cpos]  <- "E"; Lrhs[cpos] <- 1
    }
  }

  # 2. Transitivity: b[i,u,v] + b[i,v,w] - b[i,u,w] <= 1  (all ordered triples)
  verts <- 1:n
  for (i in 1:k) {
    for (u in verts) {
      for (v in setdiff(verts, u)) {
        for (w in setdiff(verts, c(u, v))) {
          cpos <- cpos + 1L
          Lcols[[cpos]] <- c(var_index(i, u, v), var_index(i, v, w), var_index(i, u, w))
          Lvals[[cpos]] <- c(1, 1, -1)
          Lsense[cpos]  <- "L"; Lrhs[cpos] <- 1
        }
      }
    }
  }

  # 3. Edge satisfaction (majority): each edge u->v supported by >= (k+1)/2 voters
  #    (exactly (k+1)/2 if require_margin1)
  for (e in 1:n_edges) {
    u <- edges[e, 1]; v <- edges[e, 2]
    cpos <- cpos + 1L
    Lcols[[cpos]] <- var_index(1:k, u, v)
    Lvals[[cpos]] <- rep(1, k)
    Lsense[cpos]  <- edge_sense; Lrhs[cpos] <- target
  }

  # 4. Symmetry breaking (1): pin voter 1 to be lexicographically minimal in its Aut(T)-orbit
  if (voter1_pinned) {
    for (ind in 1:nrow(comps)) {
      cpos <- cpos + 1L
      Lcols[[cpos]] <- var_index(1, comps[ind, 1], comps[ind, 2])
      Lvals[[cpos]] <- 1
      Lsense[cpos]  <- "E"; Lrhs[cpos] <- 1
    }
  }

  # 5. Symmetry breaking (2): voter-interchange (S_k). Require pi_lo <=_lex pi_hi for each
  #    consecutive voter pair, comparing the precedence bits b[voter, u, v] over coordPairs.
  #    Lexicographic order is encoded with prefix-equality auxiliaries:
  #      eq[p,t] = (X_t == Y_t),  g[p,t] = (X_1..t == Y_1..t),  g[p,0] := 1,
  #    where X_t = b[lo,u,v], Y_t = b[hi,u,v]; the lex condition is X_t - Y_t <= 1 - g[p,t-1].
  for (p in seq_len(P)) {
    lo <- voterPairs[p, 1]
    hi <- voterPairs[p, 2]
    for (t in 1:m) {
      u <- coordPairs[t, 1]; v <- coordPairs[t, 2]
      xt <- var_index(lo, u, v)   # X_t
      yt <- var_index(hi, u, v)   # Y_t
      et <- eq_index(p, t)        # eq[p,t]
      gt <- g_index(p, t)         # g[p,t]

      # eq[p,t] == (X_t == Y_t): four inequalities
      cpos <- cpos + 1L; Lcols[[cpos]] <- c(et, xt, yt); Lvals[[cpos]] <- c(1,  1,  1); Lsense[cpos] <- "G"; Lrhs[cpos] <-  1
      cpos <- cpos + 1L; Lcols[[cpos]] <- c(et, xt, yt); Lvals[[cpos]] <- c(1, -1, -1); Lsense[cpos] <- "G"; Lrhs[cpos] <- -1
      cpos <- cpos + 1L; Lcols[[cpos]] <- c(et, xt, yt); Lvals[[cpos]] <- c(1,  1, -1); Lsense[cpos] <- "L"; Lrhs[cpos] <-  1
      cpos <- cpos + 1L; Lcols[[cpos]] <- c(et, xt, yt); Lvals[[cpos]] <- c(1, -1,  1); Lsense[cpos] <- "L"; Lrhs[cpos] <-  1

      # g[p,t] = g[p,t-1] AND eq[p,t]; g[p,0] := 1
      cpos <- cpos + 1L; Lcols[[cpos]] <- c(gt, et); Lvals[[cpos]] <- c(1, -1); Lsense[cpos] <- "L"; Lrhs[cpos] <- 0  # g_t <= eq_t
      if (t == 1) {
        cpos <- cpos + 1L; Lcols[[cpos]] <- c(gt, et); Lvals[[cpos]] <- c(1, -1); Lsense[cpos] <- "G"; Lrhs[cpos] <- 0  # g_1 >= eq_1
        cpos <- cpos + 1L; Lcols[[cpos]] <- c(xt, yt); Lvals[[cpos]] <- c(1, -1); Lsense[cpos] <- "L"; Lrhs[cpos] <- 0  # X_1 - Y_1 <= 0
      } else {
        gprev <- g_index(p, t - 1)   # g[p,t-1]
        cpos <- cpos + 1L; Lcols[[cpos]] <- c(gt, gprev);     Lvals[[cpos]] <- c(1, -1);     Lsense[cpos] <- "L"; Lrhs[cpos] <-  0  # g_t <= g_{t-1}
        cpos <- cpos + 1L; Lcols[[cpos]] <- c(gt, gprev, et); Lvals[[cpos]] <- c(1, -1, -1); Lsense[cpos] <- "G"; Lrhs[cpos] <- -1  # g_t >= g_{t-1}+eq_t-1
        cpos <- cpos + 1L; Lcols[[cpos]] <- c(xt, yt, gprev); Lvals[[cpos]] <- c(1, -1,  1); Lsense[cpos] <- "L"; Lrhs[cpos] <-  1  # X_t - Y_t + g_{t-1} <= 1
      }
    }
  }

  # Assemble the sparse constraint matrix for Rcplex. We use a Matrix dgCMatrix (canonical
  # compressed-sparse-column): Rcplex's simple_triplet_matrix path silently assumes the
  # triplets are in column-major order and mis-assembles row-major input (giving spurious
  # "infeasible" verdicts), whereas dgCMatrix is unambiguous.
  num_constraints <- cpos
  lens <- lengths(Lcols[seq_len(cpos)])
  ii <- rep.int(seq_len(cpos), lens)
  jj <- unlist(Lcols[seq_len(cpos)], use.names = FALSE)
  vv <- unlist(Lvals[seq_len(cpos)], use.names = FALSE)
  Amat <- sparseMatrix(i = ii, j = jj, x = as.double(vv),
                       dims = c(num_constraints, num_vars))
  sense_vec <- Lsense[seq_len(cpos)]
  rhs <- Lrhs[seq_len(cpos)]

  # Solve with CPLEX. The objective is zero (pure feasibility), so mipemphasis steers the
  # search: 1 = CPX_MIPEMPHASIS_FEASIBILITY (default here; best for *hunting* a realisation),
  # 0 = balanced (better when an infeasibility proof is equally likely, e.g. a long decide run).
  result <- Rcplex(
    cvec = rep(0, num_vars),  # Zero objective = pure feasibility problem
    Amat = Amat,
    bvec = rhs,
    sense = sense_vec,
    vtype = rep("B", num_vars),
    control = list(
      trace = trace,
      tilim = time_limit,
      mipemphasis = mipemphasis
    )
  )
  
  # Determine the verdict from the CPLEX status. Rcplex returns an NA-filled xopt of the
  # correct length when no feasible point is available (proven infeasible OR timed out
  # without one), so a length check alone is not enough -- we test for a genuine solution.
  #   status 101/102 = optimal (here: a feasible point, since the objective is zero)
  #   status 103      = proven infeasible (NOT k-realizable, given enough time)
  #   status 107      = feasible point found at the time limit
  #   status 108      = time limit reached with no feasible point (INCONCLUSIVE)
  status <- result$status
  has_solution <- !is.null(result$xopt) && length(result$xopt) == num_vars && !anyNA(result$xopt)
  is_feasible <- has_solution
  if (!has_solution && !(status %in% c(103))) {
    warning(sprintf("CPLEX returned status %s with no solution: verdict INCONCLUSIVE (e.g. time limit). Treating as not feasible.", status))
  }

  if (return_permutations) {
    perms <- if (is_feasible) extract_permutations(result$xopt[seq_len(n_base)], k, n) else NULL
    if (!is.null(perms)) {
      maj_tournament = solution_to_tournament(perms)
      if (!(validate_solution(edges, maj_tournament))) {
        is_feasible = FALSE
      }
    }
    return(list(feasible = is_feasible, permutations = perms, status = status))
  } else {
    return(is_feasible)
  }
}

#' Test multiple tournaments for k-realizability
#' @param tournament_list List of edge matrices
#' @param k Number of permutations
#' @param require_margin1 If TRUE, require margin-1; if FALSE, allow any margin
#' @param time_limit Time limit per tournament in seconds
#' @return List of pairs; the first one indicates if the tournament is k-realizable, and the second one, how
test_tournaments <- function(tournament_list, k, require_margin1 = FALSE, time_limit = 3600) {
  n_tournaments <- length(tournament_list)
  results <- vector("list", n_tournaments)
  
  cat(sprintf("Testing %d tournaments for %d-realizability%s\n", 
              n_tournaments, k, 
              if (require_margin1) " with margin-1" else ""))
  cat(sprintf("Time limit: %d seconds per tournament\n", time_limit))
  cat("========================================\n")
  
  start_time <- Sys.time()
  
  for (i in seq_along(tournament_list)) {
    if (i %% 100 == 0) {
      elapsed <- as.numeric(difftime(Sys.time(), start_time, units = "secs"))
      rate <- i / elapsed
      remaining <- (n_tournaments - i) / rate
      cat(sprintf("Progress: %d/%d (%.1f%%) - %.2f tournaments/sec - ETA: %.1f min\n", 
                  i, n_tournaments, 100*i/n_tournaments, rate, remaining/60))
    }
    
    results[[i]] <- test_k_realizability_ilp(
      tournament_list[[i]], 
      k, 
      require_margin1 = require_margin1,
      time_limit = time_limit,
      return_permutations = TRUE
    )
  }
  
  elapsed <- as.numeric(difftime(Sys.time(), start_time, units = "secs"))
  cat("========================================\n")
  cat(sprintf("Completed in %.2f seconds (%.2f tournaments/sec)\n", 
              elapsed, n_tournaments/elapsed))
  cat(sprintf("Results: %d realizable, %d not realizable\n", 
              sum(sapply(results, first)), sum(!sapply(results, first))))
  
  return(results)
}

#' Convenience wrapper for 3-realizability
test_three_realizability_ilp <- function(edges, require_margin1 = FALSE, time_limit = 300, 
                                        return_permutations = FALSE) {
  test_k_realizability_ilp(edges, k = 3, require_margin1 = require_margin1, 
                          time_limit = time_limit, return_permutations = return_permutations)
}

#' Convenience wrapper for 5-realizability
test_five_realizability_ilp <- function(edges, require_margin1 = FALSE, time_limit = 300,
                                       return_permutations = FALSE) {
  test_k_realizability_ilp(edges, k = 5, require_margin1 = require_margin1,
                          time_limit = time_limit, return_permutations = return_permutations)
}

#' Functions exported from Ramsey package, Permutations.R (1 and 2) and Utilities.R (3)


### This function constructs a permutation group of given size from its generators
### The construction works by an implicit breadth-first search of the Cayley graph
### NOTE: The generators are specified by row, but the group is returned by column
### This functon was improved by ChatGPT's suggestion (namely, using a hash table)
constructPermGroup <- function(generatorList, numElts = NA) {
  n <- ncol(generatorList)
  L <- nrow(generatorList)
  if (is.na(numElts)) {
    numElts <- factorial(n)
  }
  # Initialise storage
  allElts <- matrix(NA_integer_, numElts, n)
  identity <- seq_len(n)
  if (L == 1 && all(generatorList[1,] == identity)) {
    # If only the identity generator is provided, return it
    return(t(generatorList))
  }
  allElts[1:(L + 1), ] <- rbind(identity, generatorList)
  pos <- L + 1
  # Use a hash set of seen permutations (via string keys)
  seen <- new.env(hash = TRUE, parent = emptyenv())
  key <- function(x) paste(x, collapse = ",")
  seen[[key(identity)]] <- TRUE
  for (index in 1:L) seen[[key(generatorList[index, ])]] <- TRUE
  curActive <- 2:(L + 1)
  while (length(curActive) > 0) {
    newActive <- integer(0)
    for (genIndex in 1:L) {
      gen <- generatorList[genIndex, ]
      for (active in curActive) {
        # Apply generator
        newElt <- allElts[active, gen]
        newKey <- key(newElt)
        if (!exists(newKey, envir = seen, inherits = FALSE)) {
          pos <- pos + 1
          allElts[pos, ] <- newElt
          newActive <- c(newActive, pos)
          seen[[newKey]] <- TRUE
        }
      }
    }
    curActive <- newActive
  }
  output <- t(allElts[1:pos, , drop = FALSE])
  output
}

### This function constructs a minimal set of constraints of the form s[a] < s[b]
### that the lexicographically smallest element of a coset of its input satisfies
### The input is the permutation group with one column per element minus identity
### The output is a two-column matrix where a row [ab] corresponds to s[a] < s[b]
### If count is TRUE, provides the number of elements implied by the comparisons!
### NOTE: assumes that if the identity is included, then it has to be in column 1
### Added minor improvements suggested by ChatGPT
getComparisons <- function(permGroup, count = FALSE) {
  nr <- nrow(permGroup)
  nc <- ncol(permGroup)
  # Remove identity if present in first column
  if (all(permGroup[, 1] == 1:nr)) {
    permGroup <- permGroup[, -1, drop = FALSE]
    nc <- nc - 1
  }
  # Find first index where each permutation differs from identity
  autoComp <- integer(nc)
  autoNext <- integer(nc)
  for (i in seq_len(nc)) {
    diff_pos <- which(permGroup[, i] != seq_len(nr))
    autoComp[i] <- diff_pos[1]
    autoNext[i] <- permGroup[autoComp[i], i]
  }
  # Remove duplicate (a, b) pairs
  goodComps <- unique(cbind(autoComp, autoNext))
  # Keep only the pair with maximum 'first' for each 'second'
  second_vals <- unique(goodComps[, 2])
  rows <- integer(0)
  for (s in second_vals) {
    idxs <- which(goodComps[, 2] == s)
    firsts <- goodComps[idxs, 1]
    max_first <- max(firsts)
    rows <- c(rows, idxs[firsts == max_first][1])
  }
  finalComps <- goodComps[rows, , drop = FALSE]
  finalComps <- finalComps[order(finalComps[, 1], finalComps[, 2]), , drop = FALSE]
  # If count is TRUE, compute the number of elements implied by the comparisons
  if (count) {
    desc <- rep(1L, nr)
    for (i in rev(seq_len(nrow(finalComps)))) {
      a <- finalComps[i, 1]
      b <- finalComps[i, 2]
      desc[a] <- desc[a] + desc[b]
    }
    return(list(comps = finalComps, count = prod(desc)))
  } else {
    return(finalComps)
  }
}

### This function computes a graph's full automorphism group from its generators.
### The group is not returned, only the lexicographic comparisons it entails are.
computeComparisons = function(iGraph) {
  autoGens = automorphism_group(iGraph) %>%
    do.call(rbind, .)
  autoSize = as.integer(count_automorphisms(iGraph)$group_size)
  if (autoSize > 1) {
    testComparisons = getComparisons(t(autoGens), count = TRUE)
    if (testComparisons$count == autoSize) {
      comps = testComparisons$comps
    } else {
      permGroup = constructPermGroup(autoGens, autoSize)
      comps = getComparisons(permGroup, count = FALSE)
    }
  } else {
    comps = NULL
  }
  comps
}


