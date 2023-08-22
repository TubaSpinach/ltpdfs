from pathlib import Path
import sqlite3
from flask import Flask, g, render_template, flash, request, session, redirect, url_for, abort, jsonify, send_from_directory
from werkzeug.utils import secure_filename
#config -- only uppercase properties are used by config.from_object
DATABASE = "ltpdfs.db"
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
USERNAME = "admin"
PASSWORD = "admin"
SECRET_KEY = "change_me"

#create/init Flask app
app = Flask(__name__)

app.config.from_object(__name__)

#file checking
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#database functions
def connect_db():
    rv = sqlite3.connect(app.config["DATABASE"])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    if not hasattr(g, "sqlite_db"):
        g.sqlite_db = connect_db()
    return g.sqlite_db

#tell the app how to close the db
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "sqlite_db"):
        g.sqlite_db.close()

#send info to index.html
@app.route("/")
def index():
    db = get_db()
    cur = db.execute('select * from entries order by id desc')
    entries = cur.fetchall()
    return render_template('index.html', entries=entries)

@app.route("/upload_file", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        #catch empty files submitted by browser
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print(filename)
            file.save(Path('project/uploads/' + filename).resolve())  
            return redirect(url_for('download_file', name=filename))
        
    return render_template('upload_file.html')

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory('./uploads', name)

#send and receive info from login.html
@app.route("/login", methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    session.pop('logged_in',None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route("/add",methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    
    db = get_db()
    db.execute(
        'insert into entries (title, text) values (?, ?)',
        [request.form['title'],request.form['text']]
    )
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('index'))

@app.route('/delete/<post_id>',methods=['GET'])
def delete_entry(post_id):
    result = {'status': 0, 'message': 'Error'}
    try:
        db = get_db()
        db.execute('delete from entries where id=' + post_id)
        db.commit()
        result = {'status': 1, 'message': "Post Deleted"}
    
    except Exception as e:
        result = {'status': 0, 'message': repr(e)}
    
    return jsonify(result)

@app.route("/bio", methods=['GET','POST'])
def bio():
    return render_template('bio.html')

if __name__ == "__main__":
    app.run()