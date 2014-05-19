import logging
import os
import time
import uuid
import hashlib
import datetime

import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import tornado.escape
import tornado.websocket
import tornado.gen
import tornado.httpclient

from variables import *

clients = {}

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/signup", SignupHandler),

            (r"/transaction", TransactionReceivedHandler),
            (r"/socket", WebSocketHandler),

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

        self.mongodb = mongodb


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        """
        user_json = self.get_secure_cookie("revamaps")
        if not user_json:
            return None
        return tornado.escape.json_decode(user_json)
        """
        return None

    @property
    def mongodb(self):
        return self.application.mongodb


class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")


class LoginHandler(BaseHandler):
    def get(self):
        aff = self.get_argument('aff', None)
        uid = self.get_argument('uid', None)
        self.render('login.html', errors=None, aff=aff, uid=uid)


class SignupHandler(BaseHandler):
    def get(self):
        aff = self.get_argument('aff', None)
        uid = self.get_argument('uid', None)
        price = self.mongodb.currencies.find_one()
        del(price['_id'])

        self.render('signup.html', errors=None, aff=aff, uid=uid, priceobject=price, price=tornado.escape.json_encode(price))

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        username = self.get_argument('uname', None)
        password = self.get_argument('password', None)
        email = self.get_argument('email', None)
        aff = self.get_argument('aff', None)
        uid = self.get_argument('uid', None)
        currency = self.get_argument('currency', None)
        price = self.mongodb.currencies.find_one()[currency]['bitusenet']

        if not username:
            logging.error('username is empty on signup')  
            price = self.mongodb.currencies.find_one()          
            self.render('signup.html', errors="usernameempty", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return
        if not password:
            logging.error('password is empty on signup')
            price = self.mongodb.currencies.find_one()
            self.render('signup.html', errors="passwordempty", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return
        if email:
            email = email.lower()

        """
        # Check to see if username already exists
        exists = self.mongodb.users.find_one({'username': username})
        if exists:
            logging.error('username exists on website')
            price = self.mongodb.currencies.find_one()
            self.render('signup.html', errors="usernameexists", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return

        # Check if username exists in auth db.
        exists = authdb.get("SELECT * FROM auth.logins WHERE username = %s LIMIT 1", username)
        if exists:
            logging.error('username exists in auth db.')
            self.render('signup.html', errors="usernameexists", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return
        """

        logging.info('making request for new addres for %s'%currency)
        client = tornado.httpclient.AsyncHTTPClient()
        response = yield tornado.gen.Task(client.fetch, 'http://ec2-54-82-35-88.compute-1.amazonaws.com:8000/new_address/%s'%currency)        
        address = response.body
        logging.info('address received %s'%address)

        # password salt and hash
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512(salt + password).hexdigest()

        user = {'password': hashed_password,
                'salt': salt,
                'raw': password,
                'username': username,
                'email': email,
                'active': False,
                'currency': currency,
                'address': address,
                'created': datetime.datetime.utcnow(),
                'aff': aff,
                'uid': uid
                }

        self.mongodb.users.insert(user)
        self.set_cookie('bitusenet', username)
        logging.info('Account created for %s with aff of %s'%(username, aff))
        price = self.mongodb.currencies.find_one()
        del(price['_id'])
        self.render("success.html", address=address, priceobject=price, price=tornado.escape.json_encode(price), currency=currency)


class TransactionReceivedHandler(BaseHandler):
    def get(self):
        address = self.get_argument('address')
        currency = self.get_argument('currency')
        amount = self.get_argument('amount')

        print address, amount, currency

        if address in clients:
            clients[address]['object'].write_message(tornado.escape.json_encode({'amount':str(amount),'currency':currency}))


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        self.address = self.get_argument("address")
        clients[self.address] = {"address": self.address, "object": self}

    def on_message(self, message):
        pass

    def on_close(self):
        if self.address in clients:
            del clients[self.address]


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('bitusent')
        self.clear_all_cookie()
        self.redirect('/')


class JavascriptHandler(BaseHandler):
    def get(self):
        self.render("javascript.html")


class BrandHandler(BaseHandler):
    def get(self):
        self.render("brand.html")


class TypeHandler(BaseHandler):
    def get(self):
        price = self.mongodb.currencies.find_one()
        del(price['_id'])
        self.render("type.html", price=tornado.escape.json_encode(price))


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 8000")

    main()
