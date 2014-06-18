import pymongo
#import torndb
#import elasticsearch

mongoconnection = pymongo.Connection('50.17.28.132', 27017)
mongodb = mongoconnection.bitusenet
mongocurrencies = mongoconnection.currencies

#es = elasticsearch.Elasticsearch("54.196.227.209:9200")

