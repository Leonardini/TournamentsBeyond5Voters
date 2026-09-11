#!/bin/bash
# Ten-worker driver for the Paley(31)-v majority hunt (see one.sh for the
# question and the three facts that make one run enough).  Shuffled base-state
# order, so a partial run still samples the space uniformly -- which is what
# makes an abandoned sweep's cost estimate unbiased and its coverage honest.
#
# Concurrency is xargs -P, not a jobs-count throttle: the latter ran 7.5 h on
# the P43-2v sweep and then deadlocked across a restart, reporting ten running
# jobs with no children alive.  The deadline lives in a DEADLINE_AT file that
# every worker reads, so the driver holds no clock and needs no signal handling.
#
# Stops on: STOP (a witness), an empty queue, or the deadline.
#   J=10        ten cores, the machine-wide cap
#   DEADLINE    seconds; a backstop, not the plan
# Stop by hand, PARENT FIRST:
#   pkill -f p31mv_majority/drive.sh; pkill -f "xargs -P"; pkill -f "kinduce --bits p31_minus1v"
set -u
cd "$(dirname "$0")/.."
D=p31mv_majority
J=${J:-10}; DEADLINE=${DEADLINE:-36000}
export BASE=${BASE:-$(cat $D/BASE)} ENG=${ENG:-kinduce}
START=$(date +%s)
mkdir -p $D/done $D/log
# Cross-check, every launch: the queue must be exactly the space the engine will
# search.  Both numbers come from the engine, neither is written down.
NB=$(./${ENG} --bits $(cat $D/HOST) --n $(cat $D/N) --k 5 --max-margin 3 --order mrv --inc \
      --pool-mb 512 --base $BASE --bs-from 0 --bs-to 0 2>&1 |
     sed -nE 's/^n=[0-9]+.*base_states=([0-9]+).*/\1/p' | head -1)
L=$(wc -l < $D/order.txt | tr -d " ")
[ -n "$NB" ] && [ "$L" = "$NB" ] || { echo "FATAL: order.txt has $L indices but the engine reports base_states=$NB for base {$BASE} -- rerun setup.sh" >&2; exit 1; }
# Existing markers must have been produced under THIS base, or they answer a
# different question.  Markers written before mask= was recorded are exempt.
BM=$(./${ENG} --bits $(cat $D/HOST) --n $(cat $D/N) --k 5 --max-margin 3 --order mrv --inc \
      --pool-mb 512 --base $BASE --bs-from 0 --bs-to 0 2>&1 |
     sed -nE 's/^n=[0-9]+.*base_mask=([0-9]+).*/\1/p' | head -1)
BAD=$(grep -rl 'mask=' $D/done 2>/dev/null | tr '\n' '\0' | xargs -0 grep -L "mask=$BM" 2>/dev/null | wc -l | tr -d " ")
[ "$BAD" = 0 ] || { echo "FATAL: $BAD markers in done/ carry a base_mask other than $BM" >&2; exit 1; }
echo "  cross-check OK: base={$BASE} base_mask=$BM base_states=$NB == order.txt lines"

echo "$((START + DEADLINE))" > $D/DEADLINE_AT
echo "$(date '+%F %T')  drive.sh start  J=$J deadline=${DEADLINE}s (stops by $(date -r $((START+DEADLINE)) '+%F %T'))  pid=$$  done=$(ls $D/done | wc -l)"

# The queue is the shuffled order minus what is already settled.  Concurrency is
# xargs -P: the previous `while [ "$(jobs -rp | wc -l)" -ge $J ]` throttle
# deadlocked on a restart -- the job table went on reporting ten running jobs
# with no children alive -- and cost 25 minutes of idle machine.
Q=$(mktemp); trap 'rm -f $Q' EXIT
# NOTE the empty case.  The two-file awk idiom `NR==FNR{...;next}` is WRONG when
# the first file is empty: awk never reads a record from it, so NR==FNR is still
# true on the first line of the SECOND file and order.txt gets eaten as the
# done-list, yielding an empty queue and a driver that exits instantly claiming
# "0 base states left".  Happened on the first P31-v launch.
DONE_N=$(ls $D/done | wc -l | tr -d " ")
if [ "$DONE_N" -eq 0 ]; then cp $D/order.txt $Q
else awk 'NR==FNR{d[$1];next} !($1 in d)' <(ls $D/done) $D/order.txt > $Q; fi
QN=$(wc -l < $Q | tr -d " ")
# The check that would have caught the above in one second.
[ "$QN" -eq "$((NB - DONE_N))" ] || { echo "FATAL queue holds $QN base states but $NB - $DONE_N = $((NB - DONE_N)) are outstanding" >&2; exit 1; }
echo "  queue: $QN base states left of $NB (done $DONE_N)"
xargs -P $J -n 1 $D/one.sh < $Q

echo "$(date '+%F %T')  drive.sh end  done=$(ls $D/done | wc -l) / $NB"
if [ -f $D/STOP ]; then echo "RESULT: WITNESS FOUND -- see $D/WITNESSES.txt"
elif [ "$(ls $D/done | wc -l | tr -d " ")" -eq "$NB" ]; then
  echo "RESULT: FULL COVER -- run  comm -3 <(ls $D/done | sort -n) <(seq 0 $((NB-1)))  to certify it"
else echo "PARTIAL: re-run drive.sh to resume"; fi
