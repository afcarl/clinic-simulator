import numpy as np
from numpy import random
import json

class Actor(object):

    def __init__(self, id):
        self.id = id
        self.state = None
        self.time_remaining = 0
        self.timeline = [ ]
        self.meta = { }
        self.time_in_state = { }

    def set_state(self, state, timestamp, duration=0, metadata=None):
        if self.state is not None:
            self.timeline[-1]['end'] = timestamp
            self.timeline[-1]['duration'] = timestamp - self.timeline[-1]['start']
            if self.state in self.time_in_state:
                self.time_in_state[self.state] += self.timeline[-1]['duration']
        if duration >= 0:
            event = {'state': state, 'start': timestamp, 'end': None, 'duration': None}
            if metadata is not None:
                event['meta'] = metadata
            self.timeline.append(event)
        self.state = state
        self.time_remaining = duration

    def get_last_event_time(self):
        return self.timeline[-1]['start']

    def update(self, sim):
        pass


class Simulation(object):

    def __init__(self):
        pass

    def get_duration(self, name, integer=False):
        dist = self.params['distributions'][name]
        # rescale mu, sigma^2 onto [0, 1]
        mu = float(dist['mean'] - dist['min']) / (dist['max'] - dist['min'])
        sigma = np.sqrt(float(dist['variance'])) / (dist['max'] - dist['min'])
        s2 =  sigma**2
        # solve for a, b for beta distribution
        a = (mu**2 - mu**3 - mu * s2) / s2
        b = (mu - 1) * (mu**2 - mu + s2) / s2
        # print('%s: beta(%0.1f, %0.1f) * %0.1f + %0.1f' % (name, a, b, (dist['max'] - dist['min']), dist['min']))
        duration = random.beta(a, b) * (dist['max'] - dist['min']) + dist['min']
        return int(duration) if integer else duration

    def get_actors(self, class_name, states, sort_by_time=False, shuffle=False):
        if type(states) not in [list, tuple]:
            states = (states,)
        actors = [actor for actor in self.actors if actor.__class__.__name__ ==
                  class_name and actor.state in states]
        if shuffle:
            np.random.shuffle(actors)
        elif sort_by_time:
            key = lambda actor: self.time - actor.get_last_event_time()
            actors.sort(key=key, reverse=True)
        return actors

    def get_min_time_remaining(self):
        times = [actor.time_remaining for actor in self.actors if actor.time_remaining > 0]
        return min(times) if len(times) > 0 else 0

    def step(self, step=None):
        # time step is minimum time_remaining among all actors
        step = self.get_min_time_remaining();
        for actor in self.actors:
            if actor.time_remaining > 0:
                actor.time_remaining -= step
        self.time += step
        # run twice to skip 0-length events
        for actor in self.actors:
            if actor.time_remaining <= 0:
                actor.update(self)
        for actor in self.actors:
            if actor.time_remaining <= 0:
                actor.update(self)

    def run(self, params=None):
        pass

    def cleanup(self):
        for actor in self.actors:
            if actor.timeline[-1]['end'] is None:
                actor.timeline.pop()

    def is_done(self):
        return True

    def get_json(self):
        actors = [{'id': actor.id, 'type': actor.__class__.__name__, 'timeline': actor.timeline, 'meta': actor.meta} for actor in self.actors]
        return json.dumps({'params': self.params, 'actors': actors, 'time': self.time}, indent=2)
