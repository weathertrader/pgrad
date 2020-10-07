
from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo
from flask_cors import CORS
from datetime import datetime as dt 
from datetime import timedelta as td 

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

app.config['MONGO_DBNAME'] = 'models_avail'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/models_avail'
#app.config['MONGO_DBNAME'] = 'restdb'
#app.config['MONGO_URI'] = 'mongodb://localhost:27017/restdb'


#app.config['MONGODB_SETTINGS'] = {
#    'db': 'models_avail',
#    'host': 'localhost',
#    'port': 27017}
#db = MongoEngine()
#db.init_app(app)

#mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
#mongo_db = mongo_client.models_avails
#coll = mongo_db.models_avail

mongo = PyMongo(app)

#mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
#mongo_db = mongo_client.models_avail
#coll = mongo_db.models_avail
 
# query mongodb to see if it exists
#result = coll.find_one({'model':model_name, 'dt_init':dt_init})
# print(result)

# images/del_slp_all_init_KWMC-KSFO_hrrr_2.png

dt_min = dt.utcnow() - td(hours=48)

#@cross_origin()
@app.route('/models_avail_page', methods=['GET'])
def get_all_models_avail():
    #result = coll.find_one({'model':model_name, 'dt_init':dt_init})
    coll = mongo.db.models_avail
    print(coll)
    output = []
    model_name = 'gfs'
    models = ['gfs', 'nam', 'hrrr']

    #for result in coll.find({"model": "gfs"}):
    cursor = coll.find({"dt_proc_lt": {"$gte": dt_min}}).sort([('model', 1), ('dt_init', -1)]).limit(20)
    for result in cursor:
        print(result)
        output.append({'model':result['model'].upper(), 'dt_init':result['dt_init'].strftime('%Y-%m-%d_%H'), 'hrs_avail':result['hrs_avail'], 'dt_proc_lt':result['dt_proc_lt'].strftime('%Y-%m-%d_%H-%M')})
    #for result in coll.find():
    #    print(result)
    #    output.append({'model':result['model'], 'dt_init':result['dt_init'], 'hrs_avail':result['hrs_avail']})
    #collection.find({"title": {"$in": titles}})
    #for result in coll.find_one({'model':model_name}):
    #for result in coll.find({"model": {"$in": models}}):
    #output = []    
    # for result in coll.find({"model": {"$eq": 'nam'}}):
    #    output.append({'dt_init':result['dt_init'], 'hrs_avail':result['hrs_avail']})
    #for result in coll.find():
    #    output.append({'model':result['model'], 'dt_init':result['dt_init'], 'hrs_avail':result['hrs_avail']})
    #"model": "GFS", 
    #"dt_init": dt_init, 
    #"hrs_avail": 241}
     #results_one = coll.find_one({'model':model_name})
    #if results_one:
    #    output.append({'model':result['model'], 'dt_init':result['dt_init'], 'hrs_avail':result['hrs_avail']})
    #else:
    #    output = "No such name"
    # return jsonify({'result' : output})
    return jsonify(output)

if __name__ == '__main__':
    app.run(debug=True)
    #app.run()
    
#@app.route('/star', methods=['GET'])
#def get_all_stars():
#  star = mongo.db.stars
#  output = []
# for s in star.find():
#   output.append({'name' : s['name'], 'distance' : s['distance']})
# s = star.find_one({'name' : name})
# if s:
#    output = {'name' : s['name'], 'distance' : s['distance']}
#  else:
#    output = "No such name"
#  return jsonify({'result' : output})

#@app.route('/star/', methods=['GET'])
#def get_one_star(name):
#  star = mongo.db.stars
#  s = star.find_one({'name' : name})
#  if s:
#    output = {'name' : s['name'], 'distance' : s['distance']}
#  else:
#    output = "No such name"
#  return jsonify({'result' : output})

#@app.route('/star', methods=['POST'])
#def add_star():
#  star = mongo.db.stars
#  name = request.json['name']
#  distance = request.json['distance']
#  star_id = star.insert({'name': name, 'distance': distance})
#  new_star = star.find_one({'_id': star_id })
# output = {'name' : new_star['name'], 'distance' : new_star['distance']}
#  return jsonify({'result' : output})

    