from simulation import *
import os
import sys
import webbrowser

def schedule(n_pt, size=4, spacing=15):
    times = []
    for i in range(n_pt):
        times.append(i / size * spacing)
    return times

def main():

    distributions = {
        'arrival_delay':  {'type': 'poisson', 'offset':  0, 'lambda': 30},
        'checkin':        {'type': 'poisson', 'offset':  2, 'lambda':  4},
        'ct_round':       {'type': 'poisson', 'offset': 15, 'lambda': 10},
        'ct_atp_meeting': {'type': 'poisson', 'offset':  2, 'lambda':  3},
        'atp_round':      {'type': 'poisson', 'offset': 12, 'lambda':  5},
        'checkout':       {'type': 'poisson', 'offset':  1, 'lambda':  5}
    }

    sched = schedule(20, size=8, spacing=15)

    params = {
        'n_atp': 4,
        'n_ct': 8,
        'schedule': sched
    }

    sim = Simulation(distributions)

    if 'json' in sys.argv or len(sys.argv) == 1:
        sim.initialize(params);
        while not sim.is_done():
            sim.step()
        with open('data.js', 'w') as of:
            of.write('var data = ' + sim.get_json() + ';')
        url = 'file://' + os.getcwd() + '/chart.html'
        webbrowser.open(url)

    if 'hist' in sys.argv:
        n_trials = 1000
        data = { 'pt_wait_ct': [ ], 'pt_wait_atp': [ ], 'ct_wait_atp': [ ] }
        for i in range(n_trials):
            if (i + 1) % 100 == 0: print(i + 1)
            sim.initialize(params);
            while not sim.is_done():
                sim.step()
            summary = sim.get_summary()
            for key in summary:
                data[key] += summary[key]

        from matplotlib import pyplot as plt
        plt.subplot(231)
        plt.title('PT waiting room time')
        plt.hist(data['pt_wait_ct'], 20, normed=True, histtype='stepfilled')
        plt.axvline(x=np.mean(data['pt_wait_ct']), color='red')
        plt.xlim([0,60])
        plt.subplot(232)
        plt.title('PT waiting time for ATP')
        plt.hist(data['pt_wait_atp'], np.linspace(0,60,20), normed=True, histtype='stepfilled')
        plt.axvline(x=np.mean(data['pt_wait_atp']), color='red')
        plt.xlim([0,60])
        plt.subplot(233)
        plt.title('CT waiting time for ATP')
        plt.hist(data['ct_wait_atp'], np.linspace(0,60,20), normed=True, histtype='stepfilled')
        plt.axvline(x=np.mean(data['ct_wait_atp']), color='red')
        plt.xlim([0,60])
        plt.subplot(234)
        plt.boxplot(data['pt_wait_ct'], vert=False)
        plt.xlim([0,60])
        plt.subplot(235)
        plt.boxplot(data['pt_wait_atp'], vert=False)
        plt.xlim([0,60])
        plt.subplot(236)
        plt.boxplot(data['ct_wait_atp'], vert=False)
        plt.xlim([0,60])
        plt.show()

if __name__ == "__main__":
    main()
