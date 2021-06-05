import pytest
import json
import requests
from answer import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    r = client.get("/")
    assert 200 == r.status_code
    
def test_models_put(client):

    #Test /models PUT
    payload = json.dumps({
        "name": "bert-tiny",
        "tokenizer": "mrm8488/bert-tiny-5-finetuned-squadv2",
        "model": "mrm8488/bert-tiny-5-finetuned-squadv2"}
        )
    
    r = client.put("/models",data=payload,headers={"Content-Type":"application/json"})
    assert 200 == r.status_code

def test_models_get(client):

    #test /models GET
    r = client.get("/models")
    assert 200 == r.status_code
   

def test_answer_post(client):

    #Test /answer POST
    payload = json.dumps({
        "question": "who did holly matthews play in waterloo rd?",
        "context": "She attended the British drama school East 15 in 2005, and left after winning a high-profile role in the BBC drama Waterloo Road, playing the bully Leigh-Ann Galloway.[6] Since that role, Matthews has continued to act in BBC's Doctors, playing Connie Whitfield; in ITV's The Bill playing drug addict Josie Clarke; and she was back in the BBC soap Doctors in 2009, playing Tansy Flack."}
        )
    
    model_string = ['?model=bert-tiny','']

    for m in model_string:
        
        r = client.post("/answer"+m,data=payload,headers={"Content-Type":"application/json"})
        assert 200 == r.status_code


def test_answer_get(client):
   

    #Test route /answer GET

    query_string = ["?model=bert-tiny&start=1522081879&end=1722081879","?start=1522081879&end=1722081879"]
    
    for q in query_string:
        r = client.get("/answer"+q)
        assert 200 == r.status_code

def test_models_delete(client):
    
    #Test /models DELETE
    r = client.delete("/models?model=bert-tiny")
    assert 200 == r.status_code
