import logging
import os
import time

import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import tornado.escape
import tornado.websocket

from variables import *


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/forms", FormsHandler),
            (r"/javascript", JavascriptHandler),
            (r"/brand", BrandHandler),
            (r"/type", TypeHandler),
        ]
        settings = dict(
            cookie_secret="43oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            site_name='design',
            xsrf_cookies=False,
            autoescape=None,
            debug=True,
            gzip=True
        )

        tornado.web.Application.__init__(self, handlers, **settings)

        #self.mongodb = mongodb
        self.es = es

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        """
        user_json = self.get_secure_cookie("revamaps")
        if not user_json:
            return None
        return tornado.escape.json_decode(user_json)
        """
        return None

    #@property
    #def mongodb(self):
    #    return self.application.mongodb

    @property
    def es(self):
        return self.application.es


class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")


class FormsHandler(BaseHandler):
    def get(self):
        self.render("forms.html")


class JavascriptHandler(BaseHandler):
    def get(self):
        self.render("javascript.html")


class BrandHandler(BaseHandler):
    def get(self):
        self.render("brand.html")


class TypeHandler(BaseHandler):
    def get(self):
        self.render("type.html")


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 8000")

    main()
