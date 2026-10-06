#! /usr/bin/env python3

from __future__ import print_function
import sys
from optparse import OptionParser
import random

EPS = 1e-9

# to make Python2 and Python3 act the same -- how dumb
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

parser = OptionParser()
parser.add_option("-s", "--seed", default=0, help="the random seed", action="store", type="int", dest="seed")
parser.add_option("-j", "--jobs", default=None, help="number of jobs in the system (default: len(alist) if given, else 3)", action="store", type="int", dest="jobs")
parser.add_option("-l", "--jlist", default="", help="instead of random jobs, provide a comma-separated list of run times", action="store", type="string", dest="jlist")
parser.add_option("-a", "--alist", default="", help="comma-separated list of arrival times (one per job); default: all jobs arrive at time 0", action="store", type="string", dest="alist")
parser.add_option("-A", "--maxarrival", default=0, help="max arrival time of random jobs (0 = all arrive at time 0)", action="store", type="int", dest="maxarrival")
parser.add_option("-m", "--maxlen", default=10, help="max length of job", action="store", type="int", dest="maxlen")
parser.add_option("-p", "--policy", default="FIFO", help="sched policy to use: SJF, FIFO, RR, STCF", action="store", type="string", dest="policy")
parser.add_option("-q", "--quantum", help="length of time slice for RR policy", default=1, action="store", type="int", dest="quantum")
parser.add_option("-c", help="compute answers for me", action="store_true", default=False, dest="solve")

(options, args) = parser.parse_args()

# If -j was not given, infer the number of jobs from the arrival list (when
# the lengths are random); otherwise fall back to the original default of 3.
if options.jobs is None:
    if options.alist != '' and options.jlist == '':
        options.jobs = len(options.alist.split(','))
    else:
        options.jobs = 3

random_seed(options.seed)

if options.policy not in ('FIFO', 'SJF', 'STCF', 'RR'):
    print('Error: Policy', options.policy, 'is not available.')
    sys.exit(1)

print('ARG policy', options.policy)
if options.jlist == '':
    print('ARG jobs', options.jobs)
    print('ARG maxlen', options.maxlen)
    print('ARG maxarrival', options.maxarrival)
    print('ARG seed', options.seed)
else:
    print('ARG jlist', options.jlist)
if options.alist != '':
    print('ARG alist', options.alist)
if options.policy == 'RR':
    print('ARG quantum', options.quantum)
print('')

# ---------------------------------------------------------------------------
# Build the job list: each job is a tuple (jobnum, arrival, runtime)
# ---------------------------------------------------------------------------
runtimes = []
if options.jlist == '':
    for jobnum in range(0, options.jobs):
        runtimes.append(int(options.maxlen * random.random()) + 1)
else:
    for runtime in options.jlist.split(','):
        runtimes.append(float(runtime))

if options.alist != '':
    arrivals = [float(a) for a in options.alist.split(',')]
    if len(arrivals) != len(runtimes):
        print('Error: alist has %d entries but there are %d jobs' % (len(arrivals), len(runtimes)))
        sys.exit(1)
elif options.jlist == '' and options.maxarrival > 0:
    # drawn AFTER the run times, so the lengths for a given seed stay the
    # same as in the original version of the homework
    arrivals = [int(options.maxarrival * random.random()) for _ in runtimes]
else:
    arrivals = [0 for _ in runtimes]

joblist = [(i, arrivals[i], runtimes[i]) for i in range(len(runtimes))]

print('Here is the job list, with the run time and arrival time of each job: ')
for job in joblist:
    print('  Job %d ( length = %g, arrival = %g )' % (job[0], job[2], job[1]))
print('\n')


# ---------------------------------------------------------------------------
# Simulators. Each one prints the execution trace and returns two dicts:
#   first_run[jobnum]  -> time of the first time the job gets the CPU
#   completion[jobnum] -> time at which the job finishes
# ---------------------------------------------------------------------------
def sorted_by_arrival(jobs):
    return sorted(jobs, key=lambda j: (j[1], j[0]))


def admit(pending, ready, t):
    """Move every job with arrival <= t from pending to ready."""
    while pending and pending[0][1] <= t + EPS:
        ready.append(pending.pop(0))


def print_idle(t, t_next):
    print('  [ time %5.2f ] CPU idle until %.2f' % (t, t_next))


def sim_nonpreemptive(jobs, policy):
    """FIFO and SJF (non-preemptive: once started, a job runs to completion)."""
    first_run, completion = {}, {}
    pending = sorted_by_arrival(jobs)
    ready = []
    t = 0.0
    while pending or ready:
        admit(pending, ready, t)
        if not ready:
            print_idle(t, pending[0][1])
            t = pending[0][1]
            continue
        if policy == 'SJF':
            ready.sort(key=lambda j: (j[2], j[1], j[0]))
        job = ready.pop(0)
        first_run[job[0]] = t
        t += job[2]
        completion[job[0]] = t
        print('  [ time %5.2f ] Run job %d for %.2f secs ( DONE at %.2f )' % (first_run[job[0]], job[0], job[2], t))
    return first_run, completion


def sim_stcf(jobs):
    """STCF = preemptive SJF: at every arrival, the job with the shortest
    remaining time gets the CPU."""
    first_run, completion = {}, {}
    remaining = dict((j[0], float(j[2])) for j in jobs)
    pending = sorted_by_arrival(jobs)
    ready = []
    t = 0.0
    seg = None  # [jobnum, start, end] of the slice currently being merged

    def flush(done_at=None):
        if seg is None:
            return
        dur = seg[2] - seg[1]
        if done_at is not None:
            print('  [ time %5.2f ] Run job %d for %.2f secs ( DONE at %.2f )' % (seg[1], seg[0], dur, done_at))
        else:
            print('  [ time %5.2f ] Run job %d for %.2f secs' % (seg[1], seg[0], dur))

    while pending or ready:
        admit(pending, ready, t)
        if not ready:
            flush()
            seg = None
            print_idle(t, pending[0][1])
            t = pending[0][1]
            continue

        job = min(ready, key=lambda j: (remaining[j[0]], j[1], j[0]))
        jobnum = job[0]
        if jobnum not in first_run:
            first_run[jobnum] = t

        # run until the job finishes or the next job arrives, whichever is first
        run = remaining[jobnum]
        if pending:
            run = min(run, pending[0][1] - t)

        if seg is not None and seg[0] == jobnum and abs(seg[2] - t) < EPS:
            seg[2] = t + run          # same job continues: merge the slices
        else:
            flush()                   # a different job preempted the previous one
            seg = [jobnum, t, t + run]

        t += run
        remaining[jobnum] -= run
        if remaining[jobnum] <= EPS:
            ready.remove(job)
            completion[jobnum] = t
            flush(done_at=t)
            seg = None
    flush()
    return first_run, completion


def sim_rr(jobs, quantum):
    first_run, completion = {}, {}
    remaining = dict((j[0], float(j[2])) for j in jobs)
    pending = sorted_by_arrival(jobs)
    runlist = []
    t = 0.0
    while pending or runlist:
        admit(pending, runlist, t)
        if not runlist:
            print_idle(t, pending[0][1])
            t = pending[0][1]
            continue
        job = runlist.pop(0)
        jobnum = job[0]
        if jobnum not in first_run:
            first_run[jobnum] = t
        ranfor = min(quantum, remaining[jobnum])
        remaining[jobnum] -= ranfor
        start = t
        t += ranfor
        # jobs arriving during the slice enter the queue BEFORE the preempted job
        admit(pending, runlist, t)
        if remaining[jobnum] <= EPS:
            completion[jobnum] = t
            print('  [ time %5.2f ] Run job %3d for %.2f secs ( DONE at %.2f )' % (start, jobnum, ranfor, t))
        else:
            print('  [ time %5.2f ] Run job %3d for %.2f secs' % (start, jobnum, ranfor))
            runlist.append(job)
    return first_run, completion


# ---------------------------------------------------------------------------
if options.solve:
    print('** Solutions **\n')
    print('Execution trace:')

    if options.policy in ('FIFO', 'SJF'):
        first_run, completion = sim_nonpreemptive(joblist, options.policy)
    elif options.policy == 'STCF':
        first_run, completion = sim_stcf(joblist)
    else:  # RR
        first_run, completion = sim_rr(joblist, float(options.quantum))

    print('\nFinal statistics:')
    responseSum = turnaroundSum = waitSum = 0.0
    for jobnum, arrival, runtime in joblist:
        response   = first_run[jobnum] - arrival
        turnaround = completion[jobnum] - arrival
        wait       = turnaround - runtime
        print('  Job %3d -- Response: %3.2f  Turnaround %3.2f  Wait %3.2f' % (jobnum, response, turnaround, wait))
        responseSum   += response
        turnaroundSum += turnaround
        waitSum       += wait
    count = len(joblist)
    print('\n  Average -- Response: %3.2f  Turnaround %3.2f  Wait %3.2f\n' % (responseSum/count, turnaroundSum/count, waitSum/count))
else:
    print('Compute the turnaround time, response time, and wait time for each job.')
    print('Remember that times are measured from the ARRIVAL of each job:')
    print('  response   = first run  - arrival')
    print('  turnaround = completion - arrival')
    print('  wait       = turnaround - run time')
    print('When you are done, run this program again, with the same arguments,')
    print('but with -c, which will thus provide you with the answers. You can use')
    print('-s <somenumber> or your own job list (-l 10,15,20 -a 0,5,8 for example)')
    print('to generate different problems for yourself.')
    print('')
