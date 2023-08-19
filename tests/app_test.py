import pytest
from pathlib import Path
import json
from project.app import app, init_db

TEST_DB = "test.db"

#pytest uses this function to access testing
@pytest.fixture
def client():
    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config["TESTING"] = True
    app.config["DATABASE"] = BASE_DIR.joinpath(TEST_DB)

    init_db() #clean database set up
    yield app.test_client() #tests run
    init_db() #fresh new database again

#the next two functions help us test auth features
def login(client, username, password):
    return client.post(
        "/login",
        data=dict(username=username, password=password), 
        follow_redirects=True,
    )

def logout(client):
    return client.get("/logout", follow_redirects=True)

def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200

def test_database():
    #first test, to make sure db exists!
    tester = Path("ltpdfs.db").is_file()
    assert tester

def test_empty_db(client):
    rv = client.get("/") #seems like we'll have some observer
    #                       in "/" that will check the db and display
    assert b"No entries yet. Add some!" in rv.data

def test_login_logout(client):
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"])
    assert b"You were logged in" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, app.config["USERNAME"] + "x", app.config["PASSWORD"])
    assert b"Invalid username" in rv.data
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"] + "x")
    assert b"Invalid password" in rv.data

def test_messages(client):
    login(client, app.config["USERNAME"],app.config["PASSWORD"])
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries here so far" not in rv.data #how does this not conflict with ln 43?
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data

def test_delete_message(client):
    rv = client.get('/delete/1')
    data = json.loads(rv.data)
    assert data["status"] == 1

def test_upload_file(client):
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.post(
        "/upload_file",
        data = dict(file=Path("upload_test_file.pdf").absolute()),
        follow_redirects=True,
    )
    assert Path("uploads/upload_test_file.pdf").exists() == True