#coding=utf8

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.gen
import tornado.escape
import os
import json
import urllib2
import datetime

from tornado.options import parse_command_line
from config import options


class Application(tornado.web.Application):
    def __init__(self):
        routes = [
            (r"/add_event", EventHandler),
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
        # event = {
        #     "summary": "测试",
        #     "start": {
        #         "dateTime": "2014-03-30T15:55:00.000+08:00",
        #         "timeZone": "Asia/Shanghai",
        #     },
        #     "end": {
        #         "dateTime": "2014-03-30T16:00:00.000+08:00",
        #     },
        # }
        # calendar_id = "ksbdholahhb53br6gdrjk9v284%40group.calendar.google.com"
        # data = json.dumps(event)
        # req = urllib2.Request(url="https://www.googleapis.com/calendar/v3/calendars/"+calendar_id+"/events", data=data, headers={"Authorization": user['token_type'] + " " + user['access_token'], "content-type": "application/json"})
        # try:
        #     response = urllib2.urlopen(req).read()
        # except urllib2.HTTPError, e:
        #     print e.code
        #     print e.reason
        #     response="%s:%s" % (e.code, e.reason)

        self.render("index.html", content=user, response='hehe')


class AuthHandler(BaseHandler, tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            user = yield self.get_authenticated_user(
                redirect_uri=options.domain + 'auth/login', code=self.get_argument('code'))
            # Save the user with e.g. set_secure_cookie
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
            self.redirect("/index")
        else:
            yield self.authorize_redirect(
                redirect_uri=options.domain + 'auth/login',
                client_id=self.settings['google_oauth']['key'],
                client_secret=self.settings['google_oauth']['secret'],
                scope=['profile', 'email', 'https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.readonly'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")


class EventHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.gen.coroutine
    def post(self):
        user = self.get_current_user()
        nextDate = self.get_argument("startDate", None)
        startTime = self.get_argument("startTime", None)
        endTime = self.get_argument("endTime", None)
        summary = self.get_argument("summary", None)

        events = []
        # event = dict()
        # event['summary'] = summary
        #
        # event['start'] = dict(
        #     dateTime=nextDate.__str__()+"T"+startTime+":00.000+08:00"
        # )
        # event['end'] = dict(
        #     dateTime=nextDate.__str__()+"T"+endTime+":00.000+08:00"
        # )

        nextDate = nextDate.split('-')
        nextDate = datetime.date(year=int(nextDate[0]), month=int(nextDate[1]), day=int(nextDate[2]))
        calendar_id = "ksbdholahhb53br6gdrjk9v284%40group.calendar.google.com"
        next = [1, 2, 4, 8, 15]
        i = 0
        while i < 5:
            event = dict()
            event['summary'] = summary
            nextDate = self.nextDate(nextDate, next[i])
            event['start'] = dict(
                dateTime=nextDate.__str__()+"T"+startTime+":00.000+08:00"
            )
            event['end'] = dict(
                dateTime=nextDate.__str__()+"T"+endTime+":00.000+08:00"
            )
            events.append(event)
            i += 1

        responses = []
        for event in events:
            data = json.dumps(event)
            req = urllib2.Request(url="https://www.googleapis.com/calendar/v3/calendars/"+calendar_id+"/events", data=data, headers={"Authorization": user['token_type'] + " " + user['access_token'], "content-type": "application/json"})
            try:
                response = urllib2.urlopen(req).read()
                responses.append(response)
            except urllib2.URLError, e:
                print e.reason

        self.render("index.html", content=user, response=responses)

    def nextDate(self, originDate, interval):
        term = datetime.timedelta(days=interval)
        return originDate + term


def main():
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8002)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
