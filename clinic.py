from simulation import *
import time

class Patient(Actor):

    def __init__(self, id):
        Actor.__init__(self, id)
        self.time_in_state = {'waiting_for_ct_after': 0, 'waiting_for_atp': 0}

    def update(self, sim):
        if self.state == 'waiting_to_arrive':
            self.set_state('checking_in', sim.time, sim.get_duration('checkin'))
        elif self.state == 'checking_in':
            if sim.time <= self.scheduled_time:
                self.set_state('waiting_for_ct_before', sim.time, self.scheduled_time - sim.time)
            else:
                self.set_state('waiting_for_ct_after', sim.time)
        elif self.state == 'waiting_for_ct_before':
            self.set_state('waiting_for_ct_after', sim.time)
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
        self.time_in_state = {'waiting_for_ct': 0, 'waiting_for_first_ct': 0}

    def update(self, sim):
        if self.state == 'pt_atp_meeting':
            self.set_state('waiting_for_ct', sim.time)
        if self.state == 'ct_atp_meeting':
            self.set_state('waiting_for_pt', sim.time)

class Scheduler(object):

    def initialize(self, sim):

        pts, cts, atps = [ ], [ ], [ ]

        #self.scheduled_apt_times = [15 + i / sim.params['group_size'] * sim.params['group_interval'] for i in range(len(sim.params['schedule']))]

        for i, time in enumerate(sim.params['schedule']):
            pt = Patient('PT_%02d' % (i+1))
            arrival_time = time + sim.get_duration('pt_arrival_delay')
            arrival_time = max(0, arrival_time)
            pt.set_state('waiting_to_arrive', 0, arrival_time)
            pt.scheduled_time = time
            pt.meta['scheduled_time'] = time
            pts.append(pt)

        for i in range(sim.params['n_ct']):
            ct = ClinicalTeam('CT_%02d' % (i+1))
            ct.set_state('group_huddle', 0, 15)
            cts.append(ct)

        for i in range(sim.params['n_atp']):
            atp = AttendingPhysician('ATP_%02d' % (i+1))
            atp.set_state('waiting_for_first_ct', 0)
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
                atp_idx = (atp_idx + 1) % sim.params['n_atp']

        # add pt_ids to ct metadata
        for i, ct in enumerate(cts):
            ct.meta['assigned_pt_ids'] = ct.assigned_pt_ids

        # add pt_ids to atp metadata
        for i, atp in enumerate(atps):
            atp.meta['assigned_pt_ids'] = atp.assigned_pt_ids
            atp.meta['assigned_ct_ids'] = atp.assigned_ct_ids
            for j, pt in enumerate(pts):
                if pt.id in atp.assigned_pt_ids:
                    pt.meta['assigned_atp'] = atp.id

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
        pts_waiting_for_ct = sim.get_actors('Patient', ['waiting_for_ct_before', 'waiting_for_ct_after'], sort_by_time=True)
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
        available_atps = sim.get_actors('AttendingPhysician', ['waiting_for_ct', 'waiting_for_first_ct'], sort_by_time=True)
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
            {'name': 'n_atp', 'label': 'Attendings', 'default': 2, 'type': 'int'},
            {'name': 'n_ct', 'label': 'Clinical Teams', 'default': 4, 'type': 'int'},
            {'name': 'assign_pts', 'label': 'Pre-assign patients', 'default': 1, 'type': 'int'},
            {'name': 'assign_cts', 'label': 'Pre-assign CTs', 'default': 1, 'type': 'int'},
            {'name': 'schedule', 'label': 'Scheduled times', 'default': "15,15,15,15,30,30,45,60,75,75", 'type': 'list'}
        ]

        distributions = [
            {'name': 'pt_arrival_delay', 'min':-60, 'max':  60, 'mean':  5, 'variance': 266},
            {'name': 'checkin',          'min':  2, 'max':  10, 'mean':  5, 'variance':   3},
            {'name': 'pt_ct_meeting',    'min': 10, 'max':  60, 'mean': 33, 'variance': 253},
            {'name': 'ct_atp_meeting',   'min':  0, 'max':  25, 'mean': 10, 'variance':  25},
            {'name': 'pt_atp_meeting',   'min':  2, 'max':  45, 'mean': 20, 'variance':  96},
            {'name': 'checkout',         'min':  0, 'max':  32, 'mean':  5, 'variance':  48}
        ]
        return {'fields': fields, 'distributions': distributions}

    def get_default_params(self):
        meta = self.get_metadata()
        params = {field['name']: field['default'] for field in meta['fields']}
        params['distributions'] = {dist['name'] : dist for dist in meta['distributions']}
        return params
