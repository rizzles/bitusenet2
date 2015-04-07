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

import emailer

from variables import *

clients = {}
longname = {'btc':'bit', 'ltc':'lite', 'drk':'dark', 'ppc':'peer', 'vtc':'vert', 'doge':'doge', 'max':'max', 'rzr':'razor', 'vrc':'veri', 'via':'via'}

# md5 of weatherman login for usenet
m = hashlib.md5()
password = m.update("zuskejje44")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/signup", SignupHandler),
            (r"/privacy", PrivacyHandler),
            (r"/tos", TosHandler),
            (r"/dmca", DmcaHandler),
            (r"/support", SupportHandler),
            (r"/qrcode", QRCodeHandler),
            (r"/faq", FaqHandler),

            (r"/dashboard", DashboardHandler),
            (r"/dashboard-add", DashboardAddHandler),
            (r"/dashboard-transactions", DashboardTransactionsHandler),
            (r"/add-coin", AddCoinHandler),

            (r"/transaction", TransactionReceivedHandler),
            (r"/socket", WebSocketHandler),

            (r"/reset", ResetHandler),
            (r"/passwordreset", ActualResetHandler),
            (r"/resetsent", ResetSentHandler),
            (r"/resetexpired", ResetExpiredHandler),

            (r"/javascript", JavascriptHandler),
            (r"/brand", BrandHandler),
        ]
        settings = dict(
            cookie_secret="43oETzKXQAGaYqkL5gfmGeJJFuYh7sQnp2Xd4P1o/Vo=",
            login_url="/",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            site_name='design',
            xsrf_cookies=True,
            autoescape=None,
            debug=False,
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

    def user_exists(self, username):
        # Check to see if username already exists
        exists = self.mongodb.users.find_one({'username': username})
        if exists:
            logging.error('username exists on website')
            return True

        # Check if username exists in auth db.
        exists = authdb.get("SELECT * FROM auth.logins WHERE username = %s LIMIT 1", username)
        if exists:
            logging.error('username exists in auth db.')
            return True

        logging.info("making a call to weatherman to see if username %s exists"%username)
        http_client = tornado.httpclient.HTTPClient()
        body = "x_username=mikereilly&x_password=%s&x_command=username_exists&x_cust_user_id=%s"%(m.hexdigest(), username)
        http_response = http_client.fetch("https://wm.highwinds-media.com/wm/api/http_post.php", method="POST", body=body)
        if http_response.body[0] == "1":
            logging.error(http_response.body)
            return True
        # user does not exist. Should be good to go.
        logging.info(http_response.body)
        return False

    def change_password_weatherman(self, user, newpassword):
        logging.info("Making call to weatherman api to change password for user %s"%user['username'])
        attempts = 0
        while attempts < 4:
            attempts += 1
            try:
                http_client = tornado.httpclient.HTTPClient()
                body = """x_username=mikereilly&x_password=%s&x_command=update_customer_password&x_cust_id=%s&x_cust_password=%s&x_cust_new_password=%s"""%(m.hexdigest(), user['cust_id'], user['raw'], newpassword)
                http_response = http_client.fetch("https://wm.highwinds-media.com/wm/api/http_post.php", method="POST", body=body)
            except Exception, e:
                logging.error("Exception adding user to weatherman: %s"%e)
                time.sleep(1)
                continue
            logging.info("RESPONSE: %s"%http_response.body)
            resp = http_response.body.split(",")
            if resp[0] == "0":
                logging.error("FAILED updating password")
                return False
            else:
                logging.info("SUCCESS updating password")
                return True
        return False

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
            if type(v) is list:
                currency = self.current_user['price'][k][-1]['currency']
                price = self.get_currency(currency)
                logging.info("price is old for user %s. Setting new price for currency %s"%(self.current_user['username'],currency))                
                newprice = {'price':price, 'created':int(time.time()), 'currency':currency, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet' }
                self.mongodb.users.update({'_id':self.current_user['_id']}, {"$set": {'price.%s'%k: newprice}})
                self.current_user = self.get_current_user()

            elif (datetime.datetime.utcnow() - v['timestamp']).seconds > 1800:
                currency = self.current_user['price'][k]['currency']
                price = self.get_currency(currency)
                logging.info("price is old for user %s. Setting new price for currency %s"%(self.current_user['username'],currency))                
                newprice = {'price':price, 'created':int(time.time()), 'currency':currency, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet' }
                self.mongodb.users.update({'_id':self.current_user['_id']}, {"$set": {'price.%s'%k: newprice}})
                self.current_user = self.get_current_user()


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


class FaqHandler(BaseHandler):
    def get(self):
        self.render('faq.html')


class ResetHandler(BaseHandler):
    def get(self):
        self.render('reset.html', errors=None)
    
    def post(self):
        email = self.get_argument('email', None)
        
        if not email:
            self.render('reset.html', errors='emailempty')
            return
        
        email = email.lower()
        
        logging.info("Searching db for user with email address %s", email)
        user = self.mongodb.users.find_one({'email':email})

        if not user:
            logging.error('password reset requested for unknown email address')
            self.redirect("/resetsent")
            return

        resetid = uuid.uuid4().hex
        self.mongodb.users.update({'email':email}, {"$set": {'resetid':resetid, 'resettime':time.time()}})
        emailer.send_user_password(email, resetid)
        
        self.redirect('/resetsent')


class ResetSentHandler(BaseHandler):
    def get(self):
        self.render('resetsent.html')


class ResetExpiredHandler(BaseHandler):
    def get(self):
        self.render('resetexpired.html', errors=None)


class ActualResetHandler(BaseHandler):
    def get(self):
        logging.info('password reset link from email received')
        id = self.get_argument('id', None)
        
        if not id:
            logging.error('no id was included with password reset request')
            self.redirect('/reset')
            return

        user = self.mongodb.users.find_one({'resetid':id})
        if not user:
            logging.error('password reset id not found in database')
            self.redirect('/reset')
            return

        age = time.time() - user['resettime']
        # request is over an hour old.
        if age > 3600:
            logging.error('password reset link is over an hour old')
            self.render('resetexpired.html')
            return

        self.render('actualreset.html', errors=None, resetid=id)

    def post(self):
        resetid = self.get_argument("resetid", None)
        newpassword = self.get_argument("password", None)
        
        if not resetid:
            logging.error('No resetid sent along with password reset attempt')
            self.redirect('/reset')
            return

        if not newpassword:
            logging.error('No password sent along with password reset attempt')
            self.render('actualreset.html', errors="passwordempty", resetid=resetid)
            return

        user = self.mongodb.users.find_one({'resetid': resetid})
        
        if not user:
            logging.error('Could not find resetid associated to any users')
            self.redirect('/reset')
            return

        logging.info("Resetting password to %s"%newpassword)
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512(salt + newpassword).hexdigest()
        worked = self.change_password_weatherman(user, newpassword)
        if worked:
            self.mongodb.users.update({"_id":user['_id']}, {"$set": {'resetid':None, 'resettime':None, 'salt':salt, 'password':hashed_password, 'raw':newpassword}})
        #authdb.execute("""UPDATE auth.logins SET password = %s WHERE username = %s""", newpassword, user['username'])
        self.redirect('/login')


class SignupHandler(BaseHandler):
    def get(self):
        aff = self.get_argument('aff', None)
        uid = self.get_argument('uid', None)
        price = self.get_currencies()

        self.render('signup.html', errors=None, aff=aff, uid=uid, priceobject=price, price=tornado.escape.json_encode(price))

#    @tornado.web.asynchronous
#    @tornado.gen.engine
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

        exists = self.user_exists(username)
        if exists:
            price = self.get_currencies()
            self.render('signup.html', errors="usernameexists", aff=aff, uid=uid, price=tornado.escape.json_encode(price), priceobject=price)
            return

        logging.info('making request for new addres for %s'%currency)

        client = tornado.httpclient.HTTPClient()
        try:
            response = client.fetch('http://ec2-54-82-35-88.compute-1.amazonaws.com:8000/new_address/%s'%currency)
        except tornado.httpclient.HTTPError as e:
            logging.error('BIG error: %s'% e)
            self.set_status(500)            
            client.close()
            return

        address = response.body
        logging.info('address received %s'%address)

        """
        client = tornado.httpclient.AsyncHTTPClient()
        response = yield tornado.gen.Task(client.fetch, 'http://ec2-54-82-35-88.compute-1.amazonaws.com:8000/new_address/%s'%currency)        
        if response.error:
            logging.error('BIG error: %s'%response.error)
            self.set_status(500)
            self.finish()
            return
        else:
            address = response.body
            logging.info('address received %s'%address)
        """

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
                'price': { address: {'price':price, 'created':int(time.time()), 'currency':currency, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet' }},
                'created': datetime.datetime.utcnow(),
                'billing': datetime.datetime.utcnow(),
                'aff': aff,
                'uid': uid
                }

        self.mongodb.users.insert(user)
        self.set_secure_cookie('bitusenet', username)
        logging.info('Account created for %s with aff of %s'%(username, aff))
        price = self.get_currencies()
        #self.render("success.html", address=address, priceobject=price, price=tornado.escape.json_encode(price), currency=currency, longname=longname)
        self.redirect("/dashboard-add?currency=%s"%currency)


class TransactionReceivedHandler(BaseHandler):
    def get(self):
        address = self.get_argument('address')
        currency = self.get_argument('currency')
        amount = self.get_argument('amount')
        active = self.get_argument('active')

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
        for address, value in self.current_user['price'].iteritems():
            if isinstance(value, list):
                currency = value[0]['currency']
                price = self.get_currency(currency)
                newprice = {'price':price, 'created':int(time.time()), 'currency':currency, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet' }
                self.mongodb.users.update({'_id':self.current_user['_id']}, {'$set':{'price.%s'%address: newprice, 'addresses.%s'%currency:address}}, True)
                logging.info("Changed price style for %s"%self.current_user['username'])
                self.current_user = self.mongodb.users.find_one({'username':self.current_user['username']})

        self.render('dashboard.html')


class DashboardAddHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        currency = self.get_argument('currency', 'btc')
        self.check_price_age()
        self.render('dashboardadd.html', longname=longname, currency=currency)


class DashboardTransactionsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('dashboardtransactions.html', longname=longname)


class AddCoinHandler(BaseHandler):
    #@tornado.web.asynchronous
    #@tornado.gen.engine
    def get(self):
        currency = self.get_argument('currency')

        for k,v in self.current_user['addresses'].iteritems():
            if k == currency:
                logging.info('currency %s already found for user %s'%(currency, self.current_user['username']))
                self.redirect('/dashboard-add?currency=%s'%currency)
                return

        logging.info('making request for new addres for %s for user %s'%(currency, self.current_user['username']))

        client = tornado.httpclient.HTTPClient()
        try:
            response = client.fetch('http://ec2-54-82-35-88.compute-1.amazonaws.com:8000/new_address/%s'%currency)
        except tornado.httpclient.HTTPError as e:
            logging.error("BIG error getting new coin: %s"%e)
            self.set_status(500)
            return
        address = response.body

        """
        client = tornado.httpclient.AsyncHTTPClient()        
        response = yield tornado.gen.Task(client.fetch, 'http://ec2-54-82-35-88.compute-1.amazonaws.com:8000/new_address/%s'%currency)
        address = response.body
        """

        price = self.get_currency(currency)
        newprice = {'price':price, 'created':int(time.time()), 'currency':currency, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet' }
        self.mongodb.users.update({'_id':self.current_user['_id']}, {'$set':{'price.%s'%address: newprice, 'addresses.%s'%currency: address, 'transactions.%s'%address: []}}, True)
        self.redirect('/dashboard-add?currency=%s'%currency)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('bitusent')
        self.clear_all_cookies()
        self.redirect('/')


class PrivacyHandler(BaseHandler):
    def get(self):
        self.render('privacy.html')


class TosHandler(BaseHandler):
    def get(self):
        self.render('tos.html')


class DmcaHandler(BaseHandler):
    def get(self):
        self.render('dmca.html')


class SupportHandler(BaseHandler):
    def get(self):
        self.render('support.html')


class QRCodeHandler(BaseHandler):
    def get(self):
        self.render('qrcode.html')


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
