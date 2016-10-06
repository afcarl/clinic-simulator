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

        n_pt = int(self.get_body_arguments('n_pt')[0])
        n_atp = int(self.get_body_arguments('n_atp')[0])
        n_ct = int(self.get_body_arguments('n_ct')[0])
        group_size = int(self.get_body_arguments('group_size')[0])
        spacing = int(self.get_body_arguments('spacing')[0])

        sched = schedule(n_pt, group_size, spacing)
        params = { 'n_atp': n_atp, 'n_ct': n_ct, 'schedule': sched }

        sim = Simulation()
        sim.initialize(params);
        while not sim.is_done():
            sim.step()

        self.write(sim.get_json())

if __name__ == "__main__":
    app = tornado.web.Application([
        (r"/", MainHandler),
    ])
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
