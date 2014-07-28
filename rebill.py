import pymongo
import datetime
import time
import tornado.httpclient
import torndb

mongoconn = pymongo.Connection('ec2-50-17-28-132.compute-1.amazonaws.com', 27017)
mongo = mongoconn.bitusenet

authdb = torndb.Connection(
    host='10.114.97.213', database='auth',
    user='nick', password='mohair94')

users = mongo.users.find()

for user in users:
    if user['billing'] < datetime.datetime.utcnow() and user['active']:
        print user['username'], user['billing'], datetime.datetime.utcnow()
        print authdb.execute("DELETE FROM auth.logins WHERE username = %s", user['username'])
        mongo.users.update({'username':user['username']},{"$set":{'active':False}})
