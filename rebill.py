import pymongo
import datetime
import time
import tornado.httpclient
import torndb
import hashlib


# md5 of weatherman login for usenet
m = hashlib.md5()
password = m.update("zuskejje44")

mongoconn = pymongo.Connection('ec2-50-17-28-132.compute-1.amazonaws.com', 27017)
mongo = mongoconn.bitusenet

authdb = torndb.Connection(
    host='10.114.97.213', database='auth',
    user='nick', password='mohair94')

users = mongo.users.find()

def deactivate_weatherman(user):
    print ""
    print "Making call to weatherman api to deactivate user %s"%user['username']
    attempts = 0
    while attempts < 4:
        attempts += 1
        try:
            http_client = tornado.httpclient.HTTPClient()
            # account group id, auth type 2=user/pass, service class,                                                                                                                                                                                                                                                                       
            body = "x_username=mikereilly&x_password=%s&x_command=update_customer&x_cust_id=%s&x_acct_status_id=%s"%(m.hexdigest(), user['cust_id'], 3)
            http_response = http_client.fetch("https://wm.highwinds-media.com/wm/api/http_post.php", method="POST", body=body)
        except Exception, e:
            print "Exception deactivating user in weatherman:", e
            time.sleep(2)
            continue
        # 1:x_status, 2:x_error, 3:x_acct_id, 4:x_cust_id                                                                                                                                                                                                                                                                                   
        print "RESPONSE:", http_response.body
        resp = http_response.body.split(",")
        if resp[0] == "0":
            print "FAILED"
            return False
        else:
            print "SUCCESS"
            return True
    return False


for user in users:
    if user['billing'] < datetime.datetime.utcnow() and user['active']:
        print user['username'], user['billing'], datetime.datetime.utcnow()
        worked = deactivate_weatherman(user)
        if worked:
            mongo.users.update({'username':user['username']},{"$set":{'active':False}})
            
