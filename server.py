from simulation import *
from plotting import get_b64_plots
import tornado.ioloop
import tornado.web

def schedule(n_pt, size=4, spacing=15):
    times = []
    for i in range(n_pt):
        times.append(i / size * spacing)
    return times

def get_post_params(handler):
    get = lambda name: handler.get_body_arguments(name)[0]
    fields = ['n_pt', 'n_atp', 'n_ct', 'group_size', 'spacing']
    dist_names = ['arrival_delay', 'checkin', 'ct_round', 'ct_atp_meeting', 'atp_round', 'checkout']
    dist_fields = ['min', 'max', 'mean']
    distributions = {}
    for name in dist_names:
        distributions[name] = {}
        for field in dist_fields:
            distributions[name][field] = int(get(name + '_' + field))
        distributions[name]['type'] = 'pois'
    params = {}
    for field in fields:
        params[field] = int(get(field))
    params['distributions'] = distributions
    params['schedule'] = schedule(params['n_pt'], params['group_size'], params['spacing'])
    return params

class MonteCarloHandler(tornado.web.RequestHandler):

    def get(self):
        pass

    def post(self):
        params = get_post_params(self)
        print params
        data = { 'pt_wait_ct': [ ], 'pt_wait_atp': [ ], 'ct_wait_atp': [ ], 'end_time': [ ] }
        sim = Simulation()
        for i in range(500):
            sim.initialize(params);
            while not sim.is_done():
                sim.step()
            summary = sim.get_summary()
            for key in data.keys():
                if isinstance(summary[key], list):
                    data[key] += summary[key]
                else:
                    data[key].append(summary[key])
        b64_plots = get_b64_plots(data)
        self.write(json.dumps(b64_plots))

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.set_header("Content-Type", "text/html")
        with open('visualizer.html', 'r') as file:
            self.write(file.read())

    def post(self):
        self.set_header("Content-Type", "application/javascript")
        params = get_post_params(self)
        print params
        sim = Simulation()
        sim.initialize(params);
        while not sim.is_done():
            sim.step()

        self.write(sim.get_json())

if __name__ == "__main__":
    app = tornado.web.Application([
        (r"/", MainHandler),
        (r"/mc", MonteCarloHandler),
    ])
    print 'started'
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
