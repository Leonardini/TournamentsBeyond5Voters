# =====================================================================================
# repro/env.sh — the FIXED environment contract for the arXiv 2607.26690 reproduction.
#
# Sourced by repro/run.sh on every experiment branch. This file is identical on every
# node: the run command (`bash repro/run.sh`) and this environment never vary, so all
# nodes' results stay comparable. Per-node work lives in repro/run.sh alone.
#
# Machine: the author's Mac (orx --backend local). 14 cores / 24 GB RAM, so the local
# safety rule is at most 10 cores and a combined RSS well inside physical RAM; THREADS
# is capped at 8 here and a watchdog samples swap so nothing runs the laptop into swap.
# =====================================================================================
set -euo pipefail

REPRO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPRO_ROOT
export THREADS="${THREADS:-8}"            # laptop rule: never more than 10 cores
export SCRATCH="${SCRATCH:-${TMPDIR:-/tmp}/orx-repro}"
mkdir -p "$SCRATCH"

# External inputs that are not committed (see the package's "Data policy"):
#   - nauty 2.8.6 gentourng, for whole-catalogue tournament generation
#     (brew install nauty / apt-get install nauty; both name it nauty-gentourng)
#   - McKay's order-9 / order-10 tournament catalogues, which ./get_data.sh puts in data/mckay/
export GENTOURNG="${GENTOURNG:-$(command -v gentourng || command -v nauty-gentourng || \
                                 echo "$HOME/Downloads/DownloadedSoftware/nauty2_8_6/gentourng")}"
export MCKAY_DIR="${MCKAY_DIR:-$REPRO_ROOT/data/mckay}"

banner() { printf '\n======== %s ========\n' "$*"; }

# claim <id> <paper-value> <observed-value> <verdict>
# One machine-greppable line per paper claim. In local mode the run log is the only
# evidence channel, so every number the report will quote has to appear here.
claim() { printf 'CLAIM\t%s\tpaper=%s\tobserved=%s\t%s\n' "$1" "$2" "$3" "$4"; }

# metric <name> <value>  — a scalar worth plotting (timings, counts, memory)
metric() { printf 'METRIC\t%s\t%s\n' "$1" "$2"; }

sysinfo() {
  banner "environment"
  printf 'date          %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'host          %s\n' "$(hostname -s)"
  printf 'uname         %s\n' "$(uname -mrs)"
  printf 'cores(total)  %s\n' "$(sysctl -n hw.ncpu)"
  printf 'THREADS       %s\n' "$THREADS"
  printf 'memory(GB)    %.1f\n' "$(echo "$(sysctl -n hw.memsize) / 1073741824" | bc -l)"
  printf 'disk avail    %s\n' "$(df -h "$SCRATCH" | tail -1 | awk '{print $4}')"
  printf 'commit        %s\n' "$(git rev-parse --short HEAD 2>/dev/null || echo n/a)"
  printf 'cc            %s\n' "$(cc --version | head -1)"
  printf 'R             %s\n' "$(Rscript --version 2>&1 | head -1)"
  printf 'python        %s\n' "$(python3 --version)"
  printf 'ortools       %s\n' "$(python3 -c 'import ortools;print(ortools.__version__)' 2>/dev/null || echo MISSING)"
  printf 'cplex         %s\n' "$(python3 -c 'import cplex;print(cplex.__version__)' 2>/dev/null || echo MISSING)"
  printf 'gentourng     %s\n' "$([ -x "$GENTOURNG" ] && echo "$GENTOURNG" || echo MISSING)"
  printf 'mckay dir     %s\n' "$([ -d "$MCKAY_DIR" ] && echo "$MCKAY_DIR" || echo MISSING)"
}

# ---- memory / disk watchdog ---------------------------------------------------------
# Samples this run's process-tree RSS and the machine's swap every 30 s into the log, and
# kills the run if it is the cause of memory pressure. Peak RSS is reported as a METRIC so
# the report can quote a real memory cost per node instead of an estimate.
#
# Two things have to be true for a kill to be correct: memory pressure exists, AND this run
# is the cause of it. Both halves matter, and getting either wrong kills healthy runs:
#
#   * NOT absolute swap. This laptop routinely sits at 7-18 GB of swap in use from unrelated
#     applications, so an absolute threshold fires immediately on a run using 10 MB.
#   * NOT swap growth alone either. Other processes on this machine (the user's own long
#     compute) can drive swap up several GB while this run holds 100 MB. Blaming the run for
#     that killed an 8-hour census at the 71-minute mark.
#
# So: kill outright if the run's OWN resident set passes RSS_LIMIT_GB (default 12, half of
# physical RAM) — then it is unambiguously the problem. Kill on swap growth past
# SWAP_GROWTH_GB (default 3) only when the run's RSS is at least SWAP_BLAME_RSS_GB (default 2),
# i.e. large enough to plausibly be the cause. Otherwise warn and keep going: the machine is
# under pressure from elsewhere and killing this run would not relieve it.
WD_PID=""
swap_used_gb() { sysctl -n vm.swapusage | awk '{for(i=1;i<=NF;i++) if($i=="used"){gsub(/M/,"",$(i+2)); print $(i+2)/1024; exit}}'; }
watchdog_start() {
  local grow="${SWAP_GROWTH_GB:-3}" rmax="${RSS_LIMIT_GB:-12}" blame="${SWAP_BLAME_RSS_GB:-2}" root=$$ base
  base=$(swap_used_gb); base=${base:-0}
  printf 'WATCHDOG baseline: swap already in use by the machine = %.2f GB (growth budget %s GB chargeable only above %s GB run RSS, RSS cap %s GB)\n' "$base" "$grow" "$blame" "$rmax"
  ( peak=0
    while :; do
      sleep 30
      local swap rss
      swap=$(swap_used_gb); swap=${swap:-0}
      rss=$(ps -Ao rss=,ppid=,pid= | awk -v r="$root" '
        { rssv[$3]=$1; par[$3]=$2 }
        END { for (p in par) { q=p; d=0
                while (q!="" && q!=1 && d<40) { if (q==r) { s+=rssv[p]; break } q=par[q]; d++ } }
              print s+0 }')
      rss=$(awk -v k="$rss" 'BEGIN{print k/1048576}')
      awk -v s="$swap" -v b="$base" -v m="$rss" 'BEGIN{printf "WATCHDOG  swap=%.2fGB (+%.2f vs baseline)  run_rss=%.2fGB\n", s, s-b, m}'
      peak=$(awk -v a="$peak" -v b="$rss" 'BEGIN{print (b>a)?b:a}')
      printf 'METRIC\tpeak_rss_gb\t%.2f\n' "$peak"
      if awk -v m="$rss" -v l="$rmax" 'BEGIN{exit !(m > l)}'; then
        echo "WATCHDOG: run RSS passed ${rmax}GB — killing it to protect the laptop" >&2
        kill -TERM -"$root" 2>/dev/null || kill -TERM "$root"; exit 1
      fi
      if awk -v s="$swap" -v b="$base" -v g="$grow" 'BEGIN{exit !(s-b > g)}'; then
        if awk -v m="$rss" -v c="$blame" 'BEGIN{exit !(m >= c)}'; then
          echo "WATCHDOG: swap grew past ${grow}GB while this run holds ${rss}GB — this run is the likely cause, killing it" >&2
          kill -TERM -"$root" 2>/dev/null || kill -TERM "$root"; exit 1
        fi
        awk -v s="$swap" -v b="$base" -v m="$rss" 'BEGIN{
          printf "WATCHDOG WARNING: machine swap is up %.2fGB since this run started, but the run holds only %.2fGB — other processes are the cause, not this run. Continuing.\n", s-b, m }' >&2
      fi
    done ) &
  WD_PID=$!
}
watchdog_stop() { [ -n "$WD_PID" ] && kill "$WD_PID" 2>/dev/null || true; }
