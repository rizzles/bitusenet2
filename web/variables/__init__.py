import pymongo
import torndb
#import elasticsearch

authdb = torndb.Connection(
    host='10.114.97.213', database='auth',
    user='nick', password='mohair94')

mongoconnection = pymongo.Connection('50.17.28.132', 27017)
mongodb = mongoconnection.bitusenet
mongocurrencies = mongoconnection.currencies

#es = elasticsearch.Elasticsearch("54.196.227.209:9200")

