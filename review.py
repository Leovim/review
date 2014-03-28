#coding=utf8

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.gen
import os
import base64

from tornado.options import parse_command_line
from config import options


class Application(tornado.web.Application):
    def __init__(self):
        routes = [
            (r"/auth/oauth2callback", CallbackHandler),
            (r"/auth/login", AuthHandler),
            (r"/logout", LogoutHandler),
            (r"/index", IndexHandler),
            (r"/", IndexHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret=options.cookie_secret,
            google_oauth=dict(
                key=options.client_id,
                secret=options.client_secret
            ),
            debug=True,
        )
        tornado.web.Application.__init__(self, routes, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if not user_json: return None
        import json
        user_json = json.loads(user_json)
        return user_json


class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user()
        import urllib
        import urllib2
        data = {
            "end": {
                "dateTime": "2014-03-28T22:00:00.000+08:00",
            },
            "start": {
                "dateTime": "2014-03-28T21:55:00.000+08:00"
            },
            "summary": "测试"
        }
        req = urllib2.Request("https://www.googleapis.com/calendar/v3/users/me/calendars/changtong1993%40gmail.com/events", data, headers={"Authorization": user['token_type'] + " " + user['access_token']})
        #req = urllib2.Request("https://www.googleapis.com/calendar/v3/users/me/calendarList", headers={"Authorization": user['token_type'] + " " + user['access_token']})
        response = urllib2.urlopen(req).read()
        self.render("index.html", content=user, response=response)


class AuthHandler(BaseHandler, tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            user = yield self.get_authenticated_user(
                redirect_uri='http://localhost:8002/auth/login', 
                code=self.get_argument('code'))
            # Save the user with e.g. set_secure_cookie
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
            self.redirect("/index")
        else:
            yield self.authorize_redirect(
                redirect_uri='http://localhost:8002/auth/login',
                client_id=self.settings['google_oauth']['key'],
                client_secret=self.settings['google_oauth']['secret'],
                scope=['profile', 'email', 'https://www.googleapis.com/auth/calendar'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")

class CallbackHandler(BaseHandler):
    def get(self):
        pass


def main():
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8002)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
