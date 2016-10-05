from simulation import *
import os

def main():

    distributions = {
        'arrival_delay':  {'type': 'poisson', 'offset':  0, 'lambda': 30},
        'checkin':        {'type': 'poisson', 'offset':  2, 'lambda':  4},
        'ct_round':       {'type': 'poisson', 'offset': 15, 'lambda': 10},
        'ct_atp_meeting': {'type': 'poisson', 'offset':  2, 'lambda':  3},
        'atp_round':      {'type': 'poisson', 'offset': 12, 'lambda':  5},
        'checkout':       {'type': 'poisson', 'offset':  1, 'lambda':  5}
    }

    params = {
        'n_atp': 2,
        'n_ct': 4,
        'schedule': [0, 0, 0, 0, 15, 15, 30, 30, 45, 45, 45, 60, 60]
    }

    sim = Simulation(distributions)
    sim.initialize(params);
    
    sim.step()
    of = open('output.html', 'w')
    for line in open('header.html', 'r'):
        of.write(line)
    of.write('<table>\n')
    of.write('<thead><tr>%s</tr></thead>\n' % sim.table_header())
    while not sim.is_done():
        sim.step()
        of.write('<tr>%s</tr>\n' % sim.table_row())
    of.write('<tr>%s</tr>\n' % sim.table_row())
    of.write('</table>\n')
    of.close()

    os.system('output.html')

if __name__ == "__main__":
    main()
