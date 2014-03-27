#coding=utf8

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import parse_command_line


class Application(tornado.web.Application):
    def __init__(self):
        routes = [
            (r"/index", IndexHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        tornado.web.Application.__init__(self, routes, **settings)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        pass

def main():
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8003)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
