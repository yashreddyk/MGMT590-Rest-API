# API Objective:
Question Answering has become one of the most important problems in modern NLP research with chatbots taking over most of user preliminary interaction with the users. As a part of the course work, we've tried to build an API to the end. The primary objective of the API, mgmt-590-rest-api, is to have an system that interacts and provide answers using a specific models. Additionally, functionality to add, view and delete the models from the database has also been built in.
  
  URL of the API: https://mgmt590-rest-api-y37cncxzta-uc.a.run.app
  
# API Routes:
## 1. Route 1: "/models"
This route accepts methods 'GET', 'PUT' and 'DELETE'
### a. GET/models
Allows the user to access the list of models that are loaded in the server

Sample request url: https://mgmt590-rest-api-y37cncxzta-uc.a.run.app/models

Sample request body: NA

Sample response: [ { "name": "distilled-bert", "tokenizer": "distilbert-base-uncased-distilled-squad", "model": "distilbert-base-uncased-distilled-squad" }, { "name": "deepset-roberta", "tokenizer": "deepset/roberta-base-squad2", "model": "deepset/roberta-base-squad2" }, { "name": "bert-tiny", "tokenizer": "mrm8488/bert-tiny-5-finetuned-squadv2", "model": "mrm8488/bert-tiny-5-finetuned-squadv2" } ]

### b. PUT/models
Allows the user to load a new model into the server 

Sample request url: https://mgmt590-rest-api-y37cncxzta-uc.a.run.app/models

Sample request body: { "name": "bert-tiny", "tokenizer": "mrm8488/bert-tiny-5-finetuned-squadv2", "model": "mrm8488/bert-tiny-5-finetuned-squadv2" }

Sample response body: [ { "name": "distilled-bert", "tokenizer": "distilbert-base-uncased-distilled-squad", "model": "distilbert-base-uncased-distilled-squad" }, { "name": "deepset-roberta", "tokenizer": "deepset/roberta-base-squad2", "model": "deepset/roberta-base-squad2" }, { "name": "bert-tiny", "tokenizer": "mrm8488/bert-tiny-5-finetuned-squadv2", "model": "mrm8488/bert-tiny-5-finetuned-squadv2" } ]

### c. DELETE/models?model=<model name>:
Allows the user to delete an existing model from the server

Sample request url: https://mgmt590-rest-api-y37cncxzta-uc.a.run.app/models?model=bert-base

Sample request body: NA

Sample response: [ { "name": "distilled-bert", "tokenizer": "distilbert-base-uncased-distilled-squad", "model": "distilbert-base-uncased-distilled-squad" }, { "name": "deepset-roberta", "tokenizer": "deepset/roberta-base-squad2", "model": "deepset/roberta-base-squad2" } ]

## 2. Route 2: "/answers"
This route accepts POST and GET methods
### a. POST /answer?model = <model name>
This route uses the model in the user request to answer the questions

Sample request url: https://mgmt590-rest-api-y37cncxzta-uc.a.run.app/answer?model=bert-base

Sample request body: { "question": "who did holly matthews play in waterloo rd?", "context": "She attended the British drama school East 15 in 2005, and left after winning a high-profile role in the BBC drama Waterloo Road, playing the bully Leigh-Ann Galloway.[6] Since that role, Matthews has continued to act in BBC's Doctors, playing Connie Whitfield; in ITV's The Bill playing drug addict Josie Clarke; and she was back in the BBC soap Doctors in 2009, playing Tansy Flack." }

Sample response: { "answer": "Leigh-Ann Galloway", "context": "She attended the British drama school East 15 in 2005, and left after winning a high-profile role in the BBC drama Waterloo Road, playing the bully Leigh-Ann Galloway.[6] Since that role, Matthews has continued to act in BBC's Doctors, playing Connie Whitfield; in ITV's The Bill playing drug addict Josie Clarke; and she was back in the BBC soap Doctors in 2009, playing Tansy Flack.", "model": "bert-base", "question": "who did holly matthews play in waterloo rd?", "timestamp": 1622152488 }

### b. GET / answer?model=<model name>&start=<start datetime>&end=<end datetime>
This routes returns the most recently answered questions

Query Parameters:
  <model name> is optional
  <start timestamp> is mandatory
  <end timestamp> is mandatory

# Dependencies
  The API uses the libraries: Transformers, Flask, Sqlite3, Urllib, Datetime, Time, Os

# Docker Image: Building and Running
  1. It is mandatory to create a docker file with all the requirements
  2. Build a docker image using the command docker build. This creates a docker image
  3. The docker image can be executed using the command docker run
