from simulation import *
import time

class Patient(Actor):

    def __init__(self, id):
        Actor.__init__(self, id)
        self.time_in_state = {'waiting_for_ct': 0, 'waiting_for_atp': 0}

    def update(self, sim):
        if self.state == 'waiting_to_arrive':
            self.set_state('checking_in', sim.time, sim.get_duration('checkin'))
        elif self.state == 'checking_in':
            self.set_state('waiting_for_ct', sim.time)
        if self.state == 'pt_ct_meeting':
            self.set_state('waiting_for_atp', sim.time)
        if self.state == 'pt_atp_meeting':
            self.set_state('checking_out', sim.time, sim.get_duration('checkout'))
        elif self.state == 'checking_out':
            self.set_state('checked_out', sim.time, -1)


class ClinicalTeam(Actor):

    def __init__(self, id):
        Actor.__init__(self, id)
        self.assigned_pt_ids = [ ]
        self.time_in_state = {'waiting_for_pt': 0, 'waiting_for_atp': 0}

    def update(self, sim):
        if self.state == 'group_huddle':
            self.set_state('waiting_for_pt', sim.time)
        if self.state == 'pt_ct_meeting':
            self.set_state('waiting_for_atp', sim.time)
        if self.state == 'ct_atp_meeting':
            self.set_state('waiting_for_pt', sim.time)


class AttendingPhysician(Actor):

    def __init__(self, id):
        Actor.__init__(self, id)
        self.assigned_ct_ids = [ ]
        self.assigned_pt_ids = [ ]
        self.can_see_pt_ids = [ ] # atp can only see pt after meeting with ct
        self.time_in_state = {'waiting_for_ct': 0}

    def update(self, sim):
        if self.state == 'pt_atp_meeting':
            self.set_state('waiting_for_ct', sim.time)
        if self.state == 'ct_atp_meeting':
            self.set_state('waiting_for_pt', sim.time)


class Scheduler(object):

    def initialize(self, sim):

        pts, cts, atps = [ ], [ ], [ ]

        self.scheduled_arrival_times = [i / sim.params['group_size'] * sim.params['group_interval'] for i in range(sim.params['n_pt'])]

        for i, time in enumerate(self.scheduled_arrival_times):
            pt = Patient('PT %02d' % i)
            arrival_time = time + sim.get_duration('pt_arrival_delay')
            pt.set_state('waiting_to_arrive', 0, arrival_time)
            pts.append(pt)

        for i in range(sim.params['n_ct']):
            ct = ClinicalTeam('CT %02d' % i)
            ct.set_state('group_huddle', 0, 15)
            cts.append(ct)

        for i in range(sim.params['n_atp']):
            atp = AttendingPhysician('ATP %02d' % i)
            atp.set_state('waiting_for_ct', 0)
            atps.append(atp)

        # assign CTs to patients using round-robin
        if sim.params['assign_pts'] == 1:
            ct_idx = 0
            for i, pt in enumerate(pts):
                cts[ct_idx].assigned_pt_ids.append(pt.id)
                pt.meta['assigned_ct'] = cts[ct_idx].id
                ct_idx = (ct_idx + 1) % sim.params['n_ct'];

        # assign ATPs to CTs using round-robin
        if sim.params['assign_cts'] == 1:
            atp_idx = 0
            for i, ct in enumerate(cts):
                atps[atp_idx].assigned_ct_ids.append(ct.id)
                ct.meta['assigned_atp'] = atps[atp_idx].id
                # ATP inherits PTs from the CT
                atps[atp_idx].assigned_pt_ids += ct.assigned_pt_ids
                atp_idx = (atp_idx + 1) % sim.params['n_atp'];

        sim.actors = atps + cts + pts

    def run(self, sim):
        def create_pt_ct_meeting(pt, ct):
            duration = sim.get_duration('pt_ct_meeting')
            pt.set_state('pt_ct_meeting', sim.time, duration, {'meeting_with': ct.id})
            ct.set_state('pt_ct_meeting', sim.time, duration, {'meeting_with': pt.id})
            ct.pt_id = pt.id # carried over to atp when ct_atp_meeting is scheduled

        def create_pt_atp_meeting(pt, atp):
            duration = sim.get_duration('pt_atp_meeting')
            pt.set_state('pt_atp_meeting', sim.time, duration, {'meeting_with': atp.id})
            atp.set_state('pt_atp_meeting', sim.time, duration, {'meeting_with': pt.id})

        def create_ct_atp_meeting(ct, atp):
            duration = sim.get_duration('ct_atp_meeting')
            ct.set_state('ct_atp_meeting', sim.time, duration, {'meeting_with': atp.id})
            atp.set_state('ct_atp_meeting', sim.time, duration, {'meeting_with': ct.id})
            atp.can_see_pt_ids.append(ct.pt_id) # atp can only see pt after meeting with ct

        # schedule pt_ct_meetings
        pts_waiting_for_ct = sim.get_actors('Patient', 'waiting_for_ct', sort_by_time=True)
        available_cts = sim.get_actors('ClinicalTeam', 'waiting_for_pt', sort_by_time=True)
        for pt in pts_waiting_for_ct:
            for i, ct in enumerate(available_cts):
                if len(ct.assigned_pt_ids) == 0:
                    create_pt_ct_meeting(pt, available_cts.pop(i))
                    break
                elif pt.id in ct.assigned_pt_ids:
                    create_pt_ct_meeting(pt, available_cts.pop(i))
                    break

        # schedule pt_atp_meetings
        pts_waiting_for_atp = sim.get_actors('Patient', 'waiting_for_atp', sort_by_time=True)
        available_atps = sim.get_actors('AttendingPhysician', 'waiting_for_pt', sort_by_time=True)
        for pt in pts_waiting_for_atp:
            for i, atp in enumerate(available_atps):
                if pt.id not in atp.can_see_pt_ids:
                    continue
                if len(atp.assigned_pt_ids) == 0:
                    create_pt_atp_meeting(pt, available_atps.pop(i))
                    break
                elif pt.id in atp.assigned_pt_ids:
                    create_pt_atp_meeting(pt, available_atps.pop(i))
                    break

        # schedule ct_atp meetings
        cts_waiting_for_atp = sim.get_actors('ClinicalTeam', 'waiting_for_atp', sort_by_time=True)
        available_atps = sim.get_actors('AttendingPhysician', 'waiting_for_ct', sort_by_time=True)
        for ct in cts_waiting_for_atp:
            for i, atp in enumerate(available_atps):
                if len(atp.assigned_pt_ids) == 0:
                    create_ct_atp_meeting(ct, available_atps.pop(i))
                    break
                elif ct.pt_id in atp.assigned_pt_ids:
                    create_ct_atp_meeting(ct, available_atps.pop(i))
                    break


class ClinicSimulation(Simulation):

    def is_done(self):
        """Simulation is complete when all patients are checked out"""
        for actor in self.actors:
            if actor.__class__.__name__ == 'Patient' and actor.state != 'checked_out':
                return False
        return True

    def run(self, params):
        self.params = params
        self.actors = []
        self.time = 0
        # let the scheduler create actors
        self.scheduler = Scheduler()
        self.scheduler.initialize(self)
        start_time = time.time()
        while not self.is_done():
            if time.time() - start_time > 2:
                raise TimeoutError('iteration time exceeded in ClinicSimulation')
            self.scheduler.run(self)
            self.step()
        self.cleanup()

    def get_times(self):
        return { actor.id: actor.time_in_state for actor in self.actors}

    def get_metadata(self):
        fields = [
            {'name': 'n_pt', 'label': 'Patients', 'default': 12, 'type': 'int'},
            {'name': 'n_atp', 'label': 'Attendings', 'default': 2, 'type': 'int'},
            {'name': 'n_ct', 'label': 'Clinical Teams', 'default': 4, 'type': 'int'},
            {'name': 'group_size', 'label': 'Size of groups', 'default': 3, 'type': 'int'},
            {'name': 'group_interval', 'label': 'Arrival interval ', 'default': 15, 'type': 'int'},
            {'name': 'assign_pts', 'label': 'Pre-assign patients', 'default': 1, 'type': 'int'},
            {'name': 'assign_cts', 'label': 'Pre-assign CTs', 'default': 1, 'type': 'int'}

        ]
        distributions = [
            {'name': 'pt_arrival_delay', 'min':  0, 'max':  60, 'mean':  5, 'variance': 30},
            {'name': 'checkin',          'min':  2, 'max':  10, 'mean':  5, 'variance':  3},
            {'name': 'pt_ct_meeting',    'min': 10, 'max':  60, 'mean': 25, 'variance': 30},
            {'name': 'ct_atp_meeting',   'min':  2, 'max':   8, 'mean':  4, 'variance':  2},
            {'name': 'pt_atp_meeting',   'min': 12, 'max':  18, 'mean': 15, 'variance':  3},
            {'name': 'checkout',         'min':  2, 'max':  10, 'mean':  5, 'variance':  3}
        ]
        return {'fields': fields, 'distributions': distributions}

    def get_default_params(self):
        meta = self.get_metadata()
        params = {field['name']: field['default'] for field in meta['fields']}
        params['distributions'] = {dist['name'] : dist for dist in meta['distributions']}
        return params
