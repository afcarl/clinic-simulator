import clinic
import json
import tornado.ioloop
import tornado.web

def get_post_dict(postdata):
    data = { }
    for pair in postdata.split('&'):
        tokens = pair.split('=')
        data[tokens[0]] = tokens[1]
    return data

def get_params(post_dict, metadata):
    params = { field['name']: int(post_dict[field['name']]) for field in metadata['fields'] }
    params['distributions'] = {}
    for dist in metadata['distributions']:
        params['distributions'][dist['name']] = dist
    return params

class MetaHandler(tornado.web.RequestHandler):

    def get(self):
        sim = clinic.ClinicSimulation()
        self.write(json.dumps(sim.get_metadata()))

    def post(self):
        sim = clinic.ClinicSimulation()
        self.write(json.dumps(sim.get_metadata()))

class SampleHandler(tornado.web.RequestHandler):

    def post(self):
        self.set_header("Content-Type", "application/javascript")
        sim = clinic.ClinicSimulation()
        meta = sim.get_metadata()
        data = get_post_dict(self.request.body)
        params = get_params(data, meta)
        sim.run(params)
        result = sim.get_json();
        self.write(result)

class MonteCarloHandler(tornado.web.RequestHandler):

    def post(self):
        self.set_header("Content-Type", "application/javascript")
        sim = clinic.ClinicSimulation()
        meta = sim.get_metadata()
        data = get_post_dict(self.request.body)
        params = get_params(data, meta)
        sim.run(params)

        n = 200
        print('Running %d simulations' % n)
        simulations = [ ]
        for i in range(n):
            simulations.append(clinic.ClinicSimulation())
            simulations[i].run(params)
        print('Done')

        # get structure of actor_times, and convert each 'state': time -> 'state': [time]
        actor_times = sim.get_times()
        total_times = {actor_id: {state: [ round(duration, 1) ] for (state, duration) in times.items()} for (actor_id, times) in  actor_times.items()}
        for i in range(n):
            actor_times = simulations[i].get_times()
            for actor_id, times in actor_times.items():
                for key, duration in times.items():
                    total_times[actor_id][key].append(round(duration, 1))

        result = json.dumps(total_times, sort_keys=True);
        self.write(result)

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.set_header("Content-Type", "text/html")
        with open('index.html', 'r') as file:
            self.write(file.read())

if __name__ == "__main__":
    app = tornado.web.Application([
        (r"/", MainHandler),
        (r"/meta", MetaHandler),
        (r"/sample", SampleHandler),
        (r"/monte_carlo", MonteCarloHandler),
    ])
    print 'started'
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
