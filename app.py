from flask import Flask, render_template, request, jsonify
import json
from flask import jsonify
import requests
from cassandra.cluster import Cluster
import requests_cache
from flask import Response
from functools import wraps
from passlib.hash import sha256_crypt


requests_cache.install_cache('air_api_cache', backend='sqlite', expire_after=36000)

#This connection is for local service
cluster = Cluster(['127.0.0.1'])

#This connection is for cloud
#cluster = Cluster(['cassandra'])
KEYSPACE = "cloud"
session = cluster.connect()
#Create Keyspace it the keyspace is not exists
session.execute(""" CREATE KEYSPACE IF NOT EXISTS %s WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '3' }""" % KEYSPACE)
session.set_keyspace(KEYSPACE)
#Create table if the table is not exitss, the primary key is datetime
session.execute("""CREATE TABLE IF NOT EXISTS final (datetime text, category text, pollutant text, PRIMARY KEY (datetime))""")

#For Security,only save restful licence in config file
app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')
MY_API_KEY = app.config["MY_API_KEY"]

#Implementing hash-based authentication.Implementing user accounts and access management.
def auth_required(f):
    @wraps(f)
    def decorated(arg,arrg):
        auth=request.authorization
        if(auth and sha256_crypt.verify(auth.username,'$5$rounds=535000$4ARlC4uUsPS891B1$.Viz1CJRT9DzWQAqcghHOmoyTrqNIUXu9G2.2MdLzA6')):
            if sha256_crypt.verify(auth.password,'$5$rounds=535000$zntiMtiscaLiEPx8$Cr9GoP83laexyUWNnm7DTn4K5dcmw.dWqrpGj6O9uD6'):
                return f(arg,arrg)

        return Response('could not verify your login',401,{'WWW-Authenticate':'Basic  realm="Login Required"'})

    return decorated

# domain's address
air_url_template = "https://api.breezometer.com/air-quality/v2/historical/hourly?lat={lat}&lon={lng}&key={API_KEY}&start_datetime={start}&end_datetime={end}"
MY_API_KEY = '002c6c5aa7c94262ba52c4a4632d4522'

# provides a dynamically generated REST API:
#Getting all data in database ,saving to database and showing it by json
@app.route('/', methods=['GET'])
def Hello():
    #if request.authorization and request.authorization.username == '535000$AkGjfkT15YBb6kaX$UV7oJHjhC2u3dpg0jj73MVUBROpdax9xu6BgxL2lrN/'and request.authorization.password =='535000$C9j6qSq1IxFlJWmx$q/JvUQWxhzkszBFO3ORiiDKKEP5l8SFzdLTRjsZFMl1':
#    if (request.authorization and sha256_crypt.verify(request.authorization.username,'$5$rounds=535000$4ARlC4uUsPS891B1$.Viz1CJRT9DzWQAqcghHOmoyTrqNIUXu9G2.2MdLzA6') and sha256_crypt.verify(request.authorization.password ,'535000$t.KWEGtvsqd.chTy$wDeJbth1x1KWcVaeimnTHwEZZqxPCW5Sr3rgv0uH1wD')):
    if (request.authorization and sha256_crypt.verify(request.authorization.username, '$5$rounds=535000$4ARlC4uUsPS891B1$.Viz1CJRT9DzWQAqcghHOmoyTrqNIUXu9G2.2MdLzA6')and sha256_crypt.verify(request.authorization.password, '$5$rounds=535000$zntiMtiscaLiEPx8$Cr9GoP83laexyUWNnm7DTn4K5dcmw.dWqrpGj6O9uD6') ):
        my_latitude = request.args.get('lat','51.52369')
        my_longitude = request.args.get('lng','-0.0395857')
        my_start = request.args.get('start','2019-03-23T00:00:00Z')
        my_end = request.args.get('end','2019-03-24T13:00:00Z')
        air_url = air_url_template.format(lat=my_latitude, lng=my_longitude,API_KEY=MY_API_KEY, start=my_start, end=my_end)

        resp = requests.get(air_url)
        time=[]
        category=[]
        pollutant=[]
        x = range(24)
        for i in x:
            time.append(resp.json()['data'][i]['datetime'])
            category.append(resp.json()['data'][i]['indexes']['baqi']['category'])
            pollutant.append(resp.json()['data'][i]['indexes']['baqi']['dominant_pollutant'])
        for i in x:
            session.execute("""INSERT INTO final(datetime, category, pollutant)VALUES (%(datetime)s, %(category)s, %(pollutant)s)""",{'datetime': time[i], 'category': str(category[i]), 'pollutant': pollutant[i]})

            rows = session.execute('SELECT * FROM final')

            output=""
            for row in rows:
                output = output+"datetime:"+str(row.datetime)+"category:"+str(row.category)+"pollutant:"+str(row.pollutant)+"<br />"
    #    session.execute("DROP KEYSPACE " + KEYSPACE)
        if output=="":
            return("The database is empyty")
        else:
            return json.dumps(output)
    return Response('Could not verify',401,{'WWW-Authenticate': 'Basic realm="Login Required"'})

#Check the one specific record(example:/23/04 for 2019-3-23 4:00 data)
@app.route('/<day>/<time>', methods=['GET'])
def DataLook(day,time):
    output=""
    rows = session.execute("""SELECT * FROM final""")
    time = "2019-03-"+day+"T"+time+":00:00Z"
    for row in rows:
        if (row.datetime==time):
            output = output+"datetime:"+str(row.datetime)+"category:"+str(row.category)+"pollutant:"+str(row.pollutant)+"<br />"

    if output=="":
        return("There is no time like this")
    else:
        return json.dumps(output)

#Post one new record (example:/04/04/goodcondition/12 for 2019-03-04 04:00 the category belongs to good conditon, and the pollutant number is 12)
@app.route('/<day>/<time>/<category>/<pollutant>', methods=['GET','POST'])
def DataAdd(day,time,category,pollutant):
    output=""
    rows = session.execute("""SELECT * FROM final""")
    for row in rows:
        time = "2019-03-"+day+"T"+time+":00:00Z"
        pollutant = "pm"+pollutant
        if ((row.datetime)!=time):
            session.execute("""INSERT INTO final(datetime, category, pollutant)VALUES (%(datetime)s, %(category)s, %(pollutant)s)""",{'datetime': time, 'category': category, 'pollutant': pollutant})
            output = output+"datetime:"+time+"category:"+category+"pollutant:"+pollutant+"<br />"
            return json.dumps("Insert is successful!    "+"<br />"+output)
    return ("The data is exists!")

#Delete one record (example:d/04/04 for delete 2019-03-04 04:00,Only deleting the data from user create)
@app.route('/d/<day>/<time>', methods=['GET','DELETE'])
def DataDelete(day,time):
    time = "2019-03-"+day+"T"+time+":00:00Z"
    session.execute( """DELETE From final WHERE datetime = '{}'""".format(time))
    rows = session.execute("""SELECT * FROM final""")
    for row in rows:
        if (row.datetime==time):
            return "This is basic data, you can't delete"
    return "delect succesful!"

#Modify one record's some information (example:p/04/04/12 for Reset 2019-04-04 04:00,Only resetting the data from user create)
@app.route('/p/<day>/<time>/<pollutant>', methods=['GET','PUT'])
def DataSet(day,time,pollutant):
    rows = session.execute("""SELECT * FROM final""")
    time = "2019-03-"+day+"T"+time+":00:00Z"
    for row in rows:
        if (row.datetime==time):
            category = row.category
            session.execute("""DELETE From final WHERE datetime = '{}'""".format(time))
            session.execute("""INSERT INTO final(datetime, category, pollutant)VALUES (%(datetime)s, %(category)s, %(pollutant)s)""",{'datetime': time, 'category': category, 'pollutant': pollutant})
            return "reset ok!,but if it is the original data,we will keep it from original one"
        else:
            return  "Sorry,can't find the data!"

if __name__=="__main__":
        app.run(host='0.0.0.0', port=8080, debug=True)
