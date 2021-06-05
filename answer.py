import os

from transformers.pipelines import pipeline
from flask import Flask
from flask import request
from flask import jsonify
import sqlite3
from sqlite3 import Error
import urllib.parse
import datetime, time
import psycopg2

def create_app():
    
    # Create my flask app
    app = Flask(__name__)
    
    # Define a handler for the / path, which
    # returns "Hello World"
    @app.route("/")
    def hello_world():
        return "<p>Hello World!</p>"
    
    
    # Define a handler for the / path, which
    # is used to get, add and delete the model
    @app.route("/models", methods=['GET','PUT','DELETE'])
    def models():
    
        if request.method == 'PUT':
            #Get the request body data
            data = request.json
            params = (data['name'],data['model'],data['tokenizer'])
    
            #Insert the new model into db table models
            query = '''insert into models(name,model,tokenizer) values(%s,%s,%s)'''
            runSqlQuery(query, 'INSERT', params)
    
            #Also download the new model and add to the dictionary
            #models[data['name']] = pipeline('question-answering', model=data['model'], tokenizer=data['tokenizer'])
        elif request.method == 'DELETE':
    
            #Get the model name from the query that needs to be deleted.
            valuepairs = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)
            modelNameToDel = valuepairs['model']
    
            #Run the delete query to remove the requested model
            runSqlQuery('''delete from models where name = %s ''', 'DELETE', modelNameToDel)
    
    
    
        response = runSqlQuery('select * from models;','SELECT')
        return jsonify(response)
    
    
    #Function to get Unixtimestamp
    def getUnixTimeStamp():
        systime = datetime.datetime.now()
        unixTimeStamp = int(time.mktime(systime.timetuple()))
        return unixTimeStamp
    
    
    # Define a handler for the /answer path, which
    # processes a JSON payload with a question and
    # context and returns an answer using a Hugging
    # Face model.
    @app.route("/answer", methods=['POST','GET'])
    def answer():
        # Get the request body data
        data = request.json
    
        if request.method == 'POST':
    
            #Get Modelname from query parameters. If not passed used default model
            if 'model' in urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query).keys():
                model_tup = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)['model']
                modelName = model_tup[0]
                #Check if model exists in DB
                dbrow = runSqlQuery('''select * from models where name = %s''','SELECT',model_tup)
                if len(dbrow) == 0:
                    return "Model not found in the database"
                else:
                    #download the model using pipeline#
                    hc_comp = pipeline('question-answering', model=dbrow[0]['model'], tokenizer=dbrow[0]['tokenizer'])
                    #Get the answer
                    answer = hc_comp({'question': data['question'], 'context': data['context']})['answer']
            else:
                modelName = 'distilled-bert'
    
                #Download default model to be used
                defaultModel = pipeline('question-answering', model='distilbert-base-uncased-distilled-squad', tokenizer='distilbert-base-uncased-distilled-squad')

                #Get the answer using the default model
                answer = defaultModel({'question': data['question'], 'context': data['context']})['answer']
    
            ts = getUnixTimeStamp()
    
            #Insert a record in answer_history table for tracking of the history.
            params = (modelName,data['question'],data['context'],answer,ts)
            query = '''insert into answer_history(model_name, question, context, answer, timestamp) values(%s,%s,%s,%s,%s)'''
            runSqlQuery(query, 'INSERT', params)
    
    
            #Prepare JSON response
            out =  {
                "timestamp": ts,
                "model": modelName,
                "answer": answer,
                "question": data['question'],
                "context": data['context']
                }
    
            return jsonify(out)
        else:
    
            #When request.method is GET
    
            modelName = None
    
    
            #Check if the ModelName is passed in the request.Get ModelName if passed
            if 'model' in urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query).keys():
                modelName = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)['model'][0]
    
            #Get Start and end timestamps from the request
            start = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)['start'][0]
            end = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)['end'][0]
    
    
            #Prepare SQL select query based on whetehr ModelName is passed or not.
            if modelName == None:
                query = '''select timestamp, model_name as model, answer, question, context from answer_history where timestamp >= %s and timestamp <= %s'''
                params = (start, end)
            else:
                query = '''select timestamp, model_name as model, answer, question, context from answer_history where model_name = %s and timestamp >= %s and timestamp <= %s'''
                params = (modelName, start, end)
    
    
            #Execute the select qury to retrieve the history
            ansHist = runSqlQuery(query, 'SELECT', params)
            return jsonify(ansHist)

    return app


#Function to get Unixtimestamp
def getUnixTimeStamp():
    systime = datetime.datetime.now()
    unixTimeStamp = int(time.mktime(systime.timetuple()))
    return unixTimeStamp


#Function to create DB connection
def create_connection():
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
      #  conn = sqlite3.connect(db_file,check_same_thread=False)
      
      #Read SSL certificate content from env
      rootcert_content = format(os.environ.get('PG_SSLROOTCERT'))
      fcert_content = format(os.environ.get('PG_SSLCERT'))
      fkey_content = format(os.environ.get('PG_SSLKEY'))
      
      #Write SSL content into temp files
      frootcert = open("sslrootcert.txt","w")
      frootcert.write(rootcert_content.replace("@","="))
      frootcert.close()
      fcert = open("sslcert.txt","w")
      fcert.write(fcert_content.replace("@","="))
      fcert.close()
      fkey = open("sslkey.txt","w")
      fkey.write(fkey_content.replace("@","="))
      fkey.close()

      #Change unix permissions to restricted
      os.chmod("sslrootcert.txt",0o600)
      os.chmod("sslcert.txt",0o600)
      os.chmod("sslkey.txt",0o600)

      sslmode="sslmode=verify-ca"
      sslrootcert = "sslrootcert=sslrootcert.txt"
      sslcert = "sslcert=sslcert.txt"
      sslkey = "sslkey=sslkey.txt"
      hostaddr = "hostaddr={}".format(os.environ.get('PG_HOST'))
      user = "user=postgres"
      password = "password={}".format(os.environ.get('PG_PASSWORD'))
      dbname="dbname=mgmt590"

      dbconnect = " ".join([sslmode,
                            sslrootcert,
                            sslcert,
                            sslkey,
                            hostaddr,
                            user,
                            dbname,password])
      conn = psycopg2.connect(dbconnect)
    except Error as e:
        print(e)

    return conn


#Function to run the sql queries..
def runSqlQuery(query, qType, params = None):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    conn = create_connection() 
    cur = conn.cursor()
    if params == None:
        cur.execute(query)
    else:
        cur.execute(query,params)

    #Return the resultset only when the query type is SELECT
    if qType == 'SELECT':
        #rows = cur.fetchall()
        #return rows
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    else:
        conn.commit()

    conn.close()

#Function to create DB tables
def createTables():
    
    conn = create_connection()

    try:
        c = conn.cursor()

        #Create table models to store models added
        c.execute("CREATE TABLE IF NOT EXISTS models (name text primary key, model text, tokenizer text);")

        #Create answer_histroy table to maintain the history of the questions answered along with models and timestamps.
        c.execute("CREATE TABLE IF NOT EXISTS answer_history (model_name text, question text, context text, answer text, timestamp integer primary key);")
    except Error as e:
        print(e)

    conn.close()


# Run if running "python answer.py"
if __name__ == '__main__':
    
    # Create our Flask App
    app = create_app()

    #Create tables if not exists..
    createTables()

    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), threaded=True)
