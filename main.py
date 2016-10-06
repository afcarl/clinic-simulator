from simulation import *
import sys

def schedule(n_pt, size=4, spacing=15):
    times = []
    for i in range(n_pt):
        times.append(i / size * spacing)
    return times

def main():

    prefix = sys.argv[1]

    distributions = {
        'arrival_delay':  {'min':  0, 'max':  60, 'mean': 10, 'type': 'pois'},
        'checkin':        {'min':  2, 'max':  10, 'mean':  5, 'type': 'pois'},
        'ct_round':       {'min': 10, 'max':  60, 'mean': 25, 'type': 'pois'},
        'ct_atp_meeting': {'min':  2, 'max':   8, 'mean':  4, 'type': 'pois'},
        'atp_round':      {'min': 12, 'max':  18, 'mean': 15, 'type': 'pois'},
        'checkout':       {'min':  2, 'max':  10, 'mean':  5, 'type': 'pois'}
    }

    sched = schedule(12, size=3, spacing=30)

    params = {
        'n_atp': 2,
        'n_ct': 4,
        'schedule': sched,
        'distributions': distributions
    }

    sim = Simulation()

    n_trials = 4000
    data = { 'pt_wait_ct': [ ], 'pt_wait_atp': [ ], 'ct_wait_atp': [ ], 'end_time': [ ] }
    for i in range(n_trials):
        if (i + 1) % 100 == 0: print(i + 1)
        sim.initialize(params);
        while not sim.is_done():
            sim.step()
        summary = sim.get_summary()
        for key in data.keys():
            if isinstance(summary[key], list):
                data[key] += summary[key]
            else:
                data[key].append(summary[key])
    with open('%s_data.json' % prefix, 'w') as outfile:
        outfile.write(json.dumps(data))

if __name__ == "__main__":
    main()
