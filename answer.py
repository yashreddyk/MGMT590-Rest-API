import os

from transformers.pipelines import pipeline
from flask import Flask
from flask import request
from flask import jsonify
import sqlite3
from sqlite3 import Error
import datetime, time
import urllib.parse

# Create my flask app
app = Flask(__name__)

# Define a handler for the / path, which
# returns "Hello World"
@app.route("/")
def hello_world():
    return "<p>Hello World!</p>"

@app.route("/models", methods=['GET','PUT','DELETE'])
def models():
    
    if request.method == 'PUT':
        #Get the request body data
        data = request.json
        params = (data['name'],data['model'],data['tokenizer'])
        query = '''insert into models(name,model,tokenizer) values(?,?,?)''' 
        runSqliteQuery(conn, query, 'INSERT', params)
    
        #Add to the existing models
        models[data['name']] = pipeline('question-answering', model=data['model'], tokenizer=data['tokenizer'])  
    elif request.method == 'DELETE':
        valuepairs = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query) 
        modelNameToDel = valuepairs['model']
        runSqliteQuery(conn, '''delete from models where name = ? ''', 'DELETE', modelNameToDel) 
        
        #Also delete the stored model in dictionary
        if modelNameToDel[0] in models.keys():
            del models[modelNameToDel[0]]


    response = runSqliteQuery(conn, 'select * from models;','SELECT')
    return jsonify(response)



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
        #
    
        #Get Model
        if 'model' in urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query).keys():
            modelName = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)['model'][0]
            # Answer the answer
            answer = models[modelName]({'question': data['question'], 'context': data['context']})['answer']
        else:
            modelName = 'distilled-bert' 
            answer = defaultModel({'question': data['question'], 'context': data['context']})['answer']

        ts = getUnixTimeStamp()
    
        params = (modelName,data['question'],data['context'],answer,ts)
        query = '''insert into answer_history(model_name, question, context, answer, timestamp) values(?,?,?,?,?)'''
        runSqliteQuery(conn, query, 'INSERT', params)
        out =  {
            "timestamp": ts, 
            "model": modelName, 
            "answer": answer, 
            "question": data['question'],
            "context": data['context']
            }

        return jsonify(out)
    else:
        modelName = None
        if 'model' in urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query).keys():
            modelName = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)['model'][0]

        start = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)['start'][0]
        end = urllib.parse.parse_qs(urllib.parse.urlsplit(request.url).query)['end'][0]
        if modelName == None:
            query = '''select timestamp, model_name as model, answer, question, context from answer_history where timestamp >= ? and timestamp <= ?'''
            params = (start, end)
        else:
            query = '''select timestamp, model_name as model, answer, question, context from answer_history where model_name = ? and timestamp >= ? and timestamp <= ?'''
            params = (modelName, start, end)
            
        ansHist = runSqliteQuery(conn, query, 'SELECT', params)
        return jsonify(ansHist)



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
    

    if qType == 'SELECT':
        #rows = cur.fetchall()
        #return rows
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()] 
    else:
        conn.commit()
        

def downloadModels(modelsToDownload):
    downloadedModel={} 
    for row in modelsToDownload:
        downloadedModel[row['name']] = pipeline('question-answering', model=row['model'], tokenizer=row['tokenizer'])

    return downloadedModel

def createTables(conn):
    try:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS models (name text, model text, tokenizer text);")
        c.execute("CREATE TABLE IF NOT EXISTS answer_history (model_name text, question text, context text, answer text, timestamp integer);") 
    except Error as e:
        print(e)

# Run if running "python answer.py"
if __name__ == '__main__':
    database = r"pythonsqlite.db"
    conn = create_connection(database)
    createTables(conn) 
    modelListQuery = 'select * from models;' 
    modelList = runSqliteQuery(conn, modelListQuery, 'SELECT')
    defaultModel = pipeline('question-answering', model='distilbert-base-uncased-distilled-squad', tokenizer='distilbert-base-uncased-distilled-squad')
    models={} 
    if len(modelList) > 0:
        models = downloadModels(modelList)
        print(models.keys()) 
    else:
        print('No preloaded models found !!')
    
    # Run our Flask app and start listening for requests!!!!
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), threaded=True)
