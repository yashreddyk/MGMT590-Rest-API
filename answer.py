import os

from transformers.pipelines import pipeline
from flask import Flask
from flask import request
from flask import jsonify
import sqlite3
from sqlite3 import Error
import urllib.parse
import datetime, time

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
        query = '''insert into models(name,model,tokenizer) values(?,?,?)''' 
        runSqliteQuery(conn, query, 'INSERT', params)
    
        #Also download the new model and add to the dictionary
        #models[data['name']] = pipeline('question-answering', model=data['model'], tokenizer=data['tokenizer'])  
    elif request.method == 'DELETE':
        
        #Get the model name from the query that needs to be deleted. 
        valuepairs = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query) 
        modelNameToDel = valuepairs['model']
        
        #Run the delete query to remove the requested model
        runSqliteQuery(conn, '''delete from models where name = ? ''', 'DELETE', modelNameToDel) 
        


    response = runSqliteQuery(conn, 'select * from models;','SELECT')
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
            dbrow = runSqliteQuery(conn, '''select * from models where name = ?''','SELECT',model_tup)
            if len(dbrow) == 0:
                return "Model not found in the database"
            else:
                #download the model using pipeline#
                hc_comp = pipeline('question-answering', model=dbrow[0]['model'], tokenizer=dbrow[0]['tokenizer']) 
                #Get the answer
                answer = hc_comp({'question': data['question'], 'context': data['context']})['answer']
        else:
            modelName = 'distilled-bert' 
            
            #Get the answer using the default model
            answer = defaultModel({'question': data['question'], 'context': data['context']})['answer']

        ts = getUnixTimeStamp()
        
        #Insert a record in answer_history table for tracking of the history.
        params = (modelName,data['question'],data['context'],answer,ts)
        query = '''insert into answer_history(model_name, question, context, answer, timestamp) values(?,?,?,?,?)'''
        runSqliteQuery(conn, query, 'INSERT', params)
        

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
            query = '''select timestamp, model_name as model, answer, question, context from answer_history where timestamp >= ? and timestamp <= ?'''
            params = (start, end)
        else:
            query = '''select timestamp, model_name as model, answer, question, context from answer_history where model_name = ? and timestamp >= ? and timestamp <= ?'''
            params = (modelName, start, end)
        

        #Execute the select qury to retrieve the history
        ansHist = runSqliteQuery(conn, query, 'SELECT', params)
        return jsonify(ansHist)


#Function to create DB connection
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file,check_same_thread=False)
    except Error as e:
        print(e)

    return conn


#Function to run the sql queries.
def runSqliteQuery(conn, query, qType, params = None):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
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
        


#Function to create DB tables
def createTables(conn):
    try:
        c = conn.cursor()
        
        #Create table models to store models added
        c.execute("CREATE TABLE IF NOT EXISTS models (name text primary key, model text, tokenizer text);")
        
        #Create answer_histroy table to maintain the history of the questions answered along with models and timestamps.
        c.execute("CREATE TABLE IF NOT EXISTS answer_history (model_name text, question text, context text, answer text, timestamp integer primary key);") 
    except Error as e:
        print(e)

# Run if running "python answer.py"
if __name__ == '__main__':
    
    #Database file
    database = r"pythonsqlite.db"
    
    #Create DB connection
    conn = create_connection(database)
    
    #Create tables if not exists.
    createTables(conn) 
    

    #Download default model to be used
    defaultModel = pipeline('question-answering', model='distilbert-base-uncased-distilled-squad', tokenizer='distilbert-base-uncased-distilled-squad')
    
    
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), threaded=True)
