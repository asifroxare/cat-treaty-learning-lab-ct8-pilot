# CT8 Windows process-memory correction

The 25 September Windows bounded run succeeded for timing: 1 trial 0.043 s,
10 trials 0.099 s, 100 trials 0.335 s, and two 10-trial requests 0.053/0.130
s. All four samples reported an identical 4.08 MiB for the initial launched
PID. That figure is marked **invalid for API capacity**: the Windows virtual
environment executable can be a small launcher with a child interpreter, and
the observed flat value is implausible for a FastAPI process.

The revised probe enumerates the launcher and descendants using Windows Tool
Help, reads each process's peak working set, and reports their sampled PID list
and sum. It fails closed if the aggregate peak remains below 16 MiB. It also
terminates the whole process tree with `taskkill /T /F` after measurement, so
an interpreter child is not left running. Peak working-set sums can count
shared pages more than once; they are an upper-bound operational observation,
not a precise private-memory measure.

The timing data is only for 1/10/100 trials. No extrapolation to CT6 maximums,
public concurrency thresholds or hosting memory sizes is approved.
