library(tidyverse)
library(magrittr)
library(stringr)
library(igraph)
library(combinat)
library(testthat)

# Validation functions
perm_to_matrix <- function(perm) {
  n <- length(perm)
  mat <- matrix(0, n, n)
  for (i in 1:(n - 1)) {
    for (j in (i + 1):n) {
      mat[perm[i], perm[j]] <- 1
    }
  }
  return(mat)
}

solution_to_tournament <- function(realization, simplify = TRUE) {
  permPos = which(str_starts(names(realization), "pi"))
  stopifnot(length(permPos) %% 2 == 1)
  marginNeeded = (length(permPos) + 1) / 2
  perms = realization[permPos]
  permsFull = lapply(perms, perm_to_matrix)
  adj_matrix <- Reduce(magrittr::add, permsFull)
  if (simplify) {
    adj_matrix <- ifelse(adj_matrix >= marginNeeded, 1, 0)
  }
  adj_matrix
}

validate_solution <- function(tournament_edges, solution_matrix) {
  n <- nrow(solution_matrix)
  adj_matrix <- matrix(0, n, n)
  adj_matrix[tournament_edges] <- 1
  result <- isTRUE(all.equal.numeric(adj_matrix, solution_matrix))
  result
}

### This function reads a collection of graphs from files made by McKay's nauty
### Make sure that the conversion is done with the -el0o1 option in nauty::showg
readGraphFile = function(inputFile, numVerts, extremeOnly = FALSE) {
  curText = readLines(inputFile)
  L = length(curText)
  goodLines = 4 * (1:(L/4))
  numGraphs = L/4
  numEdges = curText[goodLines - 1] %>%
    str_split_fixed(" ", n = 2) %>%
    magrittr::extract(, 2) %>%
    as.integer()
  curText = curText[goodLines]
  curText = split(curText, numEdges)
  numByEdge = lengths(curText)
  numCounts = length(curText)
  allG = vector("list", numCounts)
  pos = 1
  for (index in 1:numCounts) {
    curNumber = numByEdge[index]
    curCounts = as.integer(names(curText)[index])
    print(paste("Processing the", curNumber, "graphs with", curCounts, "edges"))
    if (curCounts == 0) { next }
    if (!extremeOnly || (curCounts <= numVerts) || (curCounts >= choose(numVerts, 2) - 1)) {
      curX = curText[[index]] %>%
        str_split("  ") %>%
        unlist() %>%
        str_split_fixed(" ", n = 2)
      mode(curX) = "integer"
      tails = curX[,1]
      dim(tails) = c(curCounts, length(tails)/curCounts)
      heads = curX[,2]
      dim(heads) = c(curCounts, length(heads)/curCounts)
      curX = rbind(tails, heads)
      allG[[pos]] = as.list(as.data.frame(curX)) %>%
        set_names(NULL)
      pos = pos + 1
    }
  }
  allG = allG[1:(pos - 1)]
  allG = do.call(c, allG)
  allG
}

parse_tournament = function(string, n = NA) {
  if (is.na(n)) {
    N = nchar(string)
    n = (sqrt(8 * N + 1) + 1)/2
  }
  adj_matrix = matrix(0, n, n)
  adj_matrix[lower.tri(adj_matrix)] = 1 - as.integer(unlist(strsplit(string, "")))
  adj_matrix[upper.tri(adj_matrix)] = 1 - t(adj_matrix)[upper.tri(adj_matrix)]
  adj_matrix
}

parse_tournament_file = function(inputFile) {
  Lines = readLines(inputFile)
  allTournaments = lapply(Lines, parse_tournament)
  allTournaments
}

getConverse = function(adj_matrix) {
  G = graph_from_adjacency_matrix(t(adj_matrix), mode = "directed")
  G = permute(G, canonical_permutation(G)$labeling)
  converse_matrix = as.matrix(as_adjacency_matrix(G))
  converse_matrix
}
