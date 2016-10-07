from simulation import *
import sys

def schedule(n_pt, size=4, spacing=15):
    times = []
    for i in range(n_pt):
        times.append(i / size * spacing)
    return times

def main():

    prefix = sys.argv[1]

    sched = schedule(12, size=3, spacing=30)

    params = {
        'n_pt': sys.argv[1],
        'n_atp': sys.argv[2],
        'n_ct': sys.argv[3]
    }

    sim = Simulation()

    data = { 'pt_wait_ct': [ ], 'pt_wait_atp': [ ], 'ct_wait_atp': [ ], 'end_time': [ ] }

    for i in range(1000):

        if (i + 1) % 100 == 0: print(i + 1)

        sim.initialize(params);
        while not sim.is_done():
            sim.step()

        summary = sim.get_summary()
        # aggregate data
        for key in data.keys():
            if isinstance(summary[key], list):
                data[key] += summary[key]
            else:
                data[key].append(summary[key])

    with open('%s_data.json' % prefix, 'w') as outfile:
        outfile.write(json.dumps(data))

if __name__ == "__main__":
    main()
