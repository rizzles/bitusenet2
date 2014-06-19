#!/usr/bin/python

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
longname = {'btc':'bit', 'ltc':'lite', 'drk':'dark', 'ppc':'peer', 'vtc':'vert', 'doge':'doge', 'max':'max'}

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/signup", SignupHandler),
            (r"/dashboard", DashboardHandler),
            (r"/dashboard-add", DashboardAddHandler),
            (r"/dashboard-transactions", DashboardTransactionsHandler),
            (r"/add-coin", AddCoinHandler),

            (r"/transaction", TransactionReceivedHandler),
            (r"/socket", WebSocketHandler),

            (r"/javascript", JavascriptHandler),
            (r"/brand", BrandHandler),
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
        self.mongocurrencies = mongocurrencies


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("bitusenet")
        if not user:
            user = self.get_cookie("bitusenet")
        if not user:
            return None
        user = self.mongodb.users.find_one({'username':user})
        return user

    @property
    def mongodb(self):
        return self.application.mongodb

    @property
    def mongocurrencies(self):
        return self.application.mongocurrencies

    def get_currencies(self):
        price = self.mongocurrencies.currencies.find_one(sort=[("_id", pymongo.DESCENDING)])
        del(price['_id'])
        del(price['timestamp'])
        return price

    def get_currency(self, currency):
        price = self.mongocurrencies.currencies.find_one(sort=[("_id", pymongo.DESCENDING)])[currency]['bitusenet']
        return price

    def check_price_age(self):
        for k,v in self.current_user['price'].iteritems():
            if (datetime.datetime.utcnow() - v[-1]['timestamp']).seconds > 1800:
                sent = self.current_user['price'][k][-1]['sent']
                currency = self.current_user['price'][k][-1]['currency']
                price = self.get_currency(currency)
                logging.info("price is old for user %s. Setting new price for currency %s"%(self.current_user['username'],currency))                
                newcharge = {'price':price, 'created':int(time.time()), 'currency':currency, 'sent':sent, 'transactions':{}, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet' }
                self.mongodb.users.update({'_id':self.current_user['_id']}, {"$addToSet": {'price.%s'%k: newcharge}})
                self.get_current_user()


class MainHandler(BaseHandler):
    def get(self):
        price = self.get_currency('btc')
        self.render("index.html", price=price['onemonth'])


class LoginHandler(BaseHandler):
    def get(self):
        aff = self.get_argument('aff', None)
        uid = self.get_argument('uid', None)
        self.render('login.html', errors=None, aff=aff, uid=uid)

    def post(self):
        aff = self.get_argument('aff', None)
        uid = self.get_argument('uid', None)
        uname = self.get_argument('uname', None)
        password = self.get_argument('password', None)

        users = list(self.mongodb.users.find({'username':uname}))
        if len(users) == 0:
            logging.info("Could not match username on login %s, %s"%(uname, password))
            self.render('login.html', errors='wronguname', aff=aff, uid=uid)
            return

        # find salted password
        for user in users:
            salt = user['salt']
            hashed_password = hashlib.sha512(salt + password).hexdigest()
            if hashed_password == user['password']:
                self.set_secure_cookie('bitusenet', uname)
                self.redirect("/dashboard")
                return

        logging.info("Could not match password on login %s, %s"%(uname, password))
        self.render('login.html', errors='wrongpassword', aff=aff, uid=uid)


class SignupHandler(BaseHandler):
    def get(self):
        aff = self.get_argument('aff', None)
        uid = self.get_argument('uid', None)
        price = self.get_currencies()

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
        price = self.get_currency(currency)

        if not username:
            logging.error('username is empty on signup')  
            price = self.get_currencies()   
            self.render('signup.html', errors="usernameempty", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return
        if not password:
            logging.error('password is empty on signup')
            price = self.get_currencies()
            self.render('signup.html', errors="passwordempty", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return
        if email:
            email = email.lower()


        # Check to see if username already exists
        exists = self.mongodb.users.find_one({'username': username})
        if exists:
            logging.error('username exists on website')
            price = self.get_currencies()
            self.render('signup.html', errors="usernameexists", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return

        # Check if username exists in auth db.
        exists = authdb.get("SELECT * FROM auth.logins WHERE username = %s LIMIT 1", username)
        if exists:
            logging.error('username exists in auth db.')
            self.render('signup.html', errors="usernameexists", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return

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
                'addresses': {currency:address},
                'transactions': {address: []},
                'price': { address: [{'price':price, 'created':int(time.time()), 'currency':currency, 'sent':0, 'transactions':{}, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet' }]},
                'created': datetime.datetime.utcnow(),
                'billing': datetime.datetime.utcnow(),
                'aff': aff,
                'uid': uid
                }

        self.mongodb.users.insert(user)
        self.set_secure_cookie('bitusenet', username)
        logging.info('Account created for %s with aff of %s'%(username, aff))
        price = self.get_currencies()
        self.render("success.html", address=address, priceobject=price, price=tornado.escape.json_encode(price), currency=currency, longname=longname)


class TransactionReceivedHandler(BaseHandler):
    def get(self):
        address = self.get_argument('address')
        currency = self.get_argument('currency')
        amount = self.get_argument('amount')
        active = self.get_argument('active')

        print address, amount, currency

        if address in clients:
            clients[address]['object'].write_message(tornado.escape.json_encode({'amount':str(amount),'currency':currency, 'active':active}))


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        self.address = self.get_argument("address")
        clients[self.address] = {"address": self.address, "object": self}

    def on_message(self, message):
        pass

    def on_close(self):
        if self.address in clients:
            del clients[self.address]


class DashboardHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('dashboard.html')


class DashboardAddHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.check_price_age()
        self.render('dashboardadd.html', longname=longname)


class DashboardTransactionsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('dashboardtransactions.html', longname=longname)


class AddCoinHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        currency = self.get_argument('currency')

        for k,v in self.current_user['addresses'].iteritems():
            if k == currency:
                logging.info('currency %s already found for user %s'%(currency, self.current_user['username']))
                self.redirect('/dashboard-add')
                return

        logging.info('making request for new addres for %s for user %s'%(currency, self.current_user['username']))

        client = tornado.httpclient.AsyncHTTPClient()        
        response = yield tornado.gen.Task(client.fetch, 'http://ec2-54-82-35-88.compute-1.amazonaws.com:8000/new_address/%s'%currency)
        address = response.body

        price = self.get_currency(currency)
        newaddress = [{'price':price, 'created':int(time.time()), 'currency':currency, 'sent':0, 'transactions':{}, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet' }]
        self.mongodb.users.update({'_id':self.current_user['_id']}, {'$set':{'price.%s'%address: newaddress, 'addresses.%s'%currency: address, 'transactions.%s'%address: []}}, True)
        self.redirect('/dashboard-add')


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('bitusent')
        self.clear_all_cookies()
        self.redirect('/')


class JavascriptHandler(BaseHandler):
    def get(self):
        address = "1DogUco8GeDDGCkXb2R4GXWZPxfjDFov3g"
        amount = 180
        currency = 'btc'
        active = False
        print clients
        clients[address]['object'].write_message(tornado.escape.json_encode({'amount':str(amount),'currency':currency, 'active':active}))
        #clients[address]['object'].write_message({'amount':str(amount),'currency':currency, 'active':active})

class BrandHandler(BaseHandler):
    def get(self):
        self.render("brand.html")


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 8000")

    main()
