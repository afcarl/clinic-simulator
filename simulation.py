import numpy as np
import json
from numpy import random

class Actor(object):

    def __init__(self, name, id):
        self.name           = name
        self.state          = None
        self.time_remaining = 0
        self.id             = id
        self.event_log      = []

    def set_state(self, state, time, duration=0):
        if not self.state is None:
            self.event_log.append({'name': 'end_' + self.state, 'time': time})
        self.state = state
        if duration >= 0:
            self.event_log.append({'name': 'begin_' + state, 'time': time})
        self.time_remaining = duration

    def run(self, sim):
        pass

class Patient(Actor):

    def __init__(self, id):
        Actor.__init__(self, 'PT', id)
        self.ct_wait_begin  = 0
        self.ct_wait_time   = 0
        self.atp_wait_begin = 0
        self.atp_wait_time  = 0

    def run(self, sim):
        if self.time_remaining > 0:
            return
        if self.state == 'waiting_to_arrive':
            self.set_state('checking_in', sim.time, sim.get_duration('checkin'))
        elif self.state == 'checking_in':
            self.set_state('waiting_for_ct', sim.time)
            self.ct_wait_begin = sim.time
        elif self.state == 'meeting_with_ct':
            self.set_state('waiting_for_atp', sim.time)
            self.atp_wait_begin = sim.time
        elif self.state == 'meeting_with_atp':
            self.set_state('checking_out', sim.time, sim.get_duration('checkout'))
        elif self.state == 'checking_out':
            self.set_state('checked_out', sim.time, -1)
        if self.state == 'waiting_for_ct':
            available = sim.get_actors(name='CT', state='waiting_for_patient')
            if len(available) > 0:
                index = random.randint(0, len(available))
                self.ct_wait_time = sim.time - self.ct_wait_begin
                duration = sim.get_duration('ct_round')
                available[index].set_state('meeting_with_patient', sim.time, duration)
                available[index].pt_id = self.id
                self.ct_id = available[index].id
                self.set_state('meeting_with_ct', sim.time, duration)
        if self.state == 'waiting_for_atp':
            available = sim.get_actors(name='ATP', state='waiting_for_patient')
            if len(available) > 0:
                # check that patient is in ATP pt_ids, i.e.,
                # the ATP met with the CT that previously met with the patient
                for i, atp in enumerate(available):
                    if self.id in atp.pt_ids:
                        self.atp_wait_time = sim.time - self.atp_wait_begin
                        duration = sim.get_duration('atp_round')
                        available[i].set_state('meeting_with_patient', sim.time, duration)
                        self.set_state('meeting_with_atp', sim.time, duration)
                        break

class ClinicalTeam(Actor):

    def __init__(self, id):
        Actor.__init__(self, 'CT', id)
        self.pt_id          = ''
        self.atp_wait_times = [ ]
        self.atp_wait_begin = 0

    def run(self, sim):
        if self.time_remaining > 0:
            return
        if self.state == 'group_huddle':
            self.set_state('waiting_for_patient', sim.time)
        if self.state == 'meeting_with_patient':
            self.set_state('waiting_for_atp', sim.time)
            self.atp_wait_begin = sim.time
        elif self.state == 'ct_atp_meeting':
            self.set_state('waiting_for_patient', sim.time)

# ATP is on standby until CT needs to meet
# after CT meeting, ATP can only meet with patient
class AttendingPhysician(Actor):

    def __init__(self, id):
        Actor.__init__(self, 'ATP', id)
        self.pt_ids = []

    def run(self, sim):
        if self.time_remaining > 0:
            return
        if self.state == 'meeting_with_patient':
            self.set_state('waiting_for_ct', sim.time)
        if self.state == 'waiting_for_ct':
            cts = sim.get_actors('CT', 'waiting_for_atp')
            if len(cts) > 0:
                # sort by atp_wait time in decreasing order
                cts.sort(key=lambda ct: sim.time - ct.atp_wait_begin, reverse=True)
                duration = sim.get_duration('ct_atp_meeting')
                cts[0].atp_wait_times.append(sim.time - cts[0].atp_wait_begin)
                self.pt_ids.append(cts[0].pt_id)
                self.set_state('ct_atp_meeting', sim.time, duration)
                cts[0].set_state('ct_atp_meeting', sim.time, duration)

        elif self.state == 'ct_atp_meeting':
            self.set_state('waiting_for_patient', sim.time)

# manages the actors
class Simulation(object):

    default_distributions = {
        'arrival_delay':  {'min':  0, 'max':  60, 'mean': 10, 'type': 'pois'},
        'checkin':        {'min':  2, 'max':  10, 'mean':  5, 'type': 'pois'},
        'ct_round':       {'min': 10, 'max':  60, 'mean': 25, 'type': 'pois'},
        'ct_atp_meeting': {'min':  2, 'max':   8, 'mean':  4, 'type': 'pois'},
        'atp_round':      {'min': 12, 'max':  18, 'mean': 15, 'type': 'pois'},
        'checkout':       {'min':  2, 'max':  10, 'mean':  5, 'type': 'pois'}
    }

    def __init__(self):
        pass

    def get_duration(self, name):
        dist = self.distributions[name]
        if dist['type'] == 'pois':
            duration = dist['min'] + random.poisson(dist['mean'] - dist['min'])
        elif dist['type'] == 'unif':
            duration = random.uniform(dist['min'], dist['max'])
        elif dist['type'] == 'exp':
            duration = dist['min'] + random.exponential(dist['mean'] - dist['min'])
        return max(dist['min'], min(dist['max'], duration))

    def get_actors(self, name, state):
        return [actor for actor in self.actors if actor.name == name and actor.state == state]

    def step(self, stepsize=None):
        if stepsize is None:
            times = [actor.time_remaining for actor in self.actors if actor.time_remaining > 0]
            stepsize = min(times) if len(times) > 0 else 1
        for actor in self.actors:
            if actor.time_remaining > 0:
                actor.time_remaining -= stepsize
        self.time += stepsize
        for actor in self.actors:
            actor.run(self)
        for actor in self.actors:
            actor.run(self)

    def initialize(self, params):
        self.params = params
        self.distributions = params['distributions'] if 'distributions' in params else self.default_distributions
        self.time = 0
        self.actors = []
        for i in range(params['n_atp']):
            atp = AttendingPhysician('ATP %d' % i)
            atp.set_state('waiting_for_ct', 0)
            self.actors.append(atp)
        for i in range(params['n_ct']):
            ct = ClinicalTeam('CT %d' % i)
            ct.set_state('group_huddle', 0, 15)
            self.actors.append(ct)
        for i, time in enumerate(params['schedule']):
            pt = Patient('PT %d' % i)
            arrival_time = time + self.get_duration('arrival_delay')
            pt.set_state('waiting_to_arrive', 0, arrival_time)
            self.actors.append(pt)

    def is_done(self):
        for actor in self.actors:
            if actor.name == 'PT' and actor.state != 'checked_out':
                return False
        return True

    def get_summary(self):
        pt_wait_ct, pt_wait_atp, ct_wait_atp = [ ], [ ], [ ]
        for actor in self.actors:
            if actor.name == 'PT':
                pt_wait_ct.append(actor.ct_wait_time)
                pt_wait_atp.append(actor.atp_wait_time)
            if actor.name == 'CT':
                ct_wait_atp += actor.atp_wait_times
        return {
            'pt_wait_ct': pt_wait_ct,
            'pt_wait_ct_mean': np.mean(pt_wait_ct),
            'pt_wait_atp': pt_wait_atp,
            'pt_wait_atp_mean': np.mean(pt_wait_atp),
            'ct_wait_atp': ct_wait_atp,
            'ct_wait_atp_mean': np.mean(ct_wait_atp),
            'end_time': self.time
        }

    def get_json(self):
        pt_data, ct_data, atp_data = [ ], [ ], [ ]
        for actor in self.actors:
            if actor.name == 'PT':
                pt_data.append({'id': actor.id, 'events': actor.event_log })
            if actor.name == 'CT':
                ct_data.append({'id': actor.id, 'events': actor.event_log })
            if actor.name == 'ATP':
                atp_data.append({'id': actor.id, 'events': actor.event_log })
        return json.dumps({
            'params': self.params, 'summary': self.get_summary(),
            'pt_data': pt_data, 'ct_data': ct_data, 'atp_data': atp_data,
            'end_time': self.time }, indent=2)
