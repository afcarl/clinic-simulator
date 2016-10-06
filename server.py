from simulation import *
import tornado.ioloop
import tornado.web

def schedule(n_pt, size=4, spacing=15):
    times = []
    for i in range(n_pt):
        times.append(i / size * spacing)
    return times

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.set_header("Content-Type", "text/html")
        with open('visualizer.html', 'r') as file:
            self.write(file.read())

    def post(self):
        self.set_header("Content-Type", "application/javascript")

        get = lambda name: self.get_body_arguments(name)[0]
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

        sim = Simulation()
        sim.initialize(params);
        while not sim.is_done():
            sim.step()

        self.write(sim.get_json())

if __name__ == "__main__":
    app = tornado.web.Application([
        (r"/", MainHandler),
    ])
    print 'started'
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
