import numpy as np
from numpy import random

# actors have state with time_remaining
# once time_remaining <= 0, the state can change during run()
# or if the state is updated by another actor
class Actor(object):

    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.log = []
        self.time_remaining = 0

    # set initial state and time_remaining
    def initialize(self, time, state, duration=0):
        self.state = state
        self.log.append({'event': 'begin_' + state, 'time': time})
        self.time_remaining = duration

    # add final log entry
    def finalize(self, time):
        self.log.append({'event': 'end_' + self.state, 'time': time})
        self.time_remaining = 0

    # update state, time_remaining and insert new log entry
    def set_state(self, time, state, duration=0):
        if not self.state is None:
            self.log.append({'event': 'end_' + self.state, 'time': time})
        self.state = state
        self.log.append({'event': 'begin_' + state, 'time': time})
        self.time_remaining = duration

    def run(self):
        pass

# PT wait to arrive, then check in, wait/meet available CT
# then wait/meet ATP who has met with corresponding CT
class Patient(Actor):

    def __init__(self, id):
        Actor.__init__(self, 'PT', id)

    def run(self, sim):
       
        if self.time_remaining > 0:
            return

        if self.state == 'waiting_to_arrive':
            self.set_state(sim.time, 'checking_in', sim.get_duration('checkin'))

        elif self.state == 'checking_in':
            self.set_state(sim.time, 'waiting_for_ct')

        elif self.state == 'meeting_with_ct':
            self.set_state(sim.time, 'waiting_for_atp')

        elif self.state == 'meeting_with_atp':
            self.set_state(sim.time, 'checking_out', sim.get_duration('checkout'))

        elif self.state == 'checking_out':
            self.state = 'checked_out'
            self.finalize(sim.time)

        if self.state == 'waiting_for_ct':
            available = sim.get_actors(name='CT', state='waiting_for_patient')
            if len(available) > 0:
                duration = sim.get_duration('ct_round')
                available[0].set_state(sim.time, 'meeting_with_patient', duration)
                available[0].pt_id = self.id
                self.ct_id = available[0].id
                self.set_state(sim.time, 'meeting_with_ct', duration)

        if self.state == 'waiting_for_atp':
            available = sim.get_actors(name='ATP', state='waiting_for_patient')
            if len(available) > 0:
                # check that patient is in ATP pt_ids, i.e.,
                # the ATP has met with the CT that previously met with the patient
                for i, atp in enumerate(available):
                    if self.id in atp.pt_ids:
                        duration = sim.get_duration('atp_round')
                        available[i].set_state(sim.time, 'meeting_with_patient', duration)
                        self.set_state(sim.time, 'meeting_with_atp', duration)
                        break

# CT is on standby (waiting_for_patient) until PT needs to be seen
# after PT meeting, CT waits for ATP
# after ATP meeting, CT returns to standby 
class ClinicalTeam(Actor):

    def __init__(self, id):

        Actor.__init__(self, 'CT', id)
        self.pt_id = ''

    def run(self, sim):
        
        if self.time_remaining > 0:
            return

        if self.state == 'meeting_with_patient':
            self.set_state(sim.time, 'waiting_for_atp')

        elif self.state == 'ct_atp_meeting':
            self.set_state(sim.time, 'waiting_for_patient')

        if self.state == 'waiting_for_atp':
            available = sim.get_actors(name='ATP', state='waiting')
            if len(available) > 0:
                duration = sim.get_duration('ct_atp_meeting')
                available[0].set_state(sim.time, 'ct_atp_meeting', duration)
                available[0].pt_ids.append(self.pt_id)
                self.set_state(sim.time, 'ct_atp_meeting', duration)

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
            self.set_state(sim.time, 'waiting')
        elif self.state == 'ct_atp_meeting':
            self.set_state(sim.time, 'waiting_for_patient')

# manages the actors
class Simulation(object):

    def __init__(self, distributions):
        self.distributions = distributions

    def get_duration(self, name):
        dist = self.distributions[name]
        if dist['type'] == 'poisson':
            return dist['offset'] + random.poisson(dist['lambda'])

    def get_actors(self, name, state):
        return [actor for actor in self.actors if actor.name == name and actor.state == state]

    def step(self):
        times = [actor.time_remaining for actor in self.actors if actor.time_remaining > 0]
        delta = min(times) if len(times) > 0 else 1
        delta = 1
        for actor in self.actors:
            if actor.time_remaining > 0:
                actor.time_remaining -= delta
        for actor in self.actors:
            actor.run(self)
        self.time += delta

    def initialize(self, params):
        self.time = 0
        self.actors = []
        for i in range(params['n_atp']):
            atp = AttendingPhysician('ATP %d' % i)
            atp.initialize(0, 'waiting')
            self.actors.append(atp)
        for i in range(params['n_ct']):
            ct = ClinicalTeam('CT %d' % i)
            ct.initialize(0, 'waiting_for_patient')
            self.actors.append(ct)
        for i, time in enumerate(params['schedule']):
            pt = Patient('PT %d' % i)
            arrival_time = time - (30) + self.get_duration('arrival_delay')
            pt.initialize(0, 'waiting_to_arrive', arrival_time)
            self.actors.append(pt)

    def is_done(self):
        for actor in self.actors:
            if actor.name == 'PT' and actor.state != 'checked_out':
                return False
        return True
    
    def format_time(self, minutes):
        return 

    def table_header(self):
        columns = ['<th>Time</th>']
        for actor in self.actors:
            columns.append('<th>%s</th>' % actor.id)
        return ''.join(columns)

    def table_row(self):
        columns = ['<td>%d:%02d</td>' % (self.time / 60 + 5, self.time % 60)]
        for actor in self.actors:
            columns.append('<td class="%s %s">%2d</td>' % (actor.name, actor.state, actor.time_remaining))
        return ''.join(columns)
