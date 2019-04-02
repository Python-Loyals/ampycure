from flask import Flask, request
from flask import jsonify
from werkzeug.utils import secure_filename
import threading, os
from flask_sqlalchemy import SQLAlchemy
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'


done = False
result_list = [0, 0, 0]

db = SQLAlchemy(app)
ip = "localhost"


class file_results(db.Model):
    time = db.Column( db.Integer, primary_key = True)
    ip = db.Column(db.String(16), primary_key=True)
    filename = db.Column(db.String(100))
    Aresult = db.Column(db.Integer)
    Presult = db.Column(db.Integer)
    Dresult = db.Column(db.Integer)

    def __init__(self, filename, ip, file_result):
        self.time = int(time.time())
        self.ip = ip
        self.filename = filename
        self.Aresult = file_result[0]
        self.Presult = file_result[1]
        self.Dresult = file_result[2]


# db.create_all()


def autism_check(filename):
    from Autism.AutismCheck import predict
    prediction = predict(filename)
    result_list[0] = int(prediction[0])


def parkinson_check(filename):
    from Parkinson.ParkinsonCheck import predict
    prediction = predict(filename)
    result_list[1] = int(prediction[0])


def depression_check(filename):
    from Depression.DepressionCheck import predict
    prediction = predict(filename)
    result_list[2] = int(prediction[0])


@app.route('/')
def index():
    return "Apmycure Homepage"


def diagnose(filename):
    autism_thread = threading.Thread(target=autism_check, args=[filename])
    parkinson_thread = threading.Thread(target=parkinson_check, args=[filename])
    depression_thread = threading.Thread(target=depression_check, args=[filename])

    autism_thread.start()
    parkinson_thread.start()
    depression_thread.start()

    autism_thread.join()
    parkinson_thread.join()
    depression_thread.join()

    global done
    done = True

    os.remove(filename)

    file_result = file_results(filename, ip, result_list)
    db.session.add(file_result)
    db.session.commit()


@app.route('/upload', methods=['POST'])
def upload():
    f = request.files['file']
    filename = secure_filename(f.filename)
    f.save(filename)
    global done, ip
    done = False
    ip = str(request.remote_addr)
    diagnose_thread = threading.Thread(target=diagnose, args=[filename])
    diagnose_thread.daemon = True
    diagnose_thread.start()

    return "upload done"


@app.route('/done', methods=['POST', 'GET'])
def done_func():
    return "true" if done else "false"


@app.route('/getresult', methods=['POST', 'GET'])
def return_result():
    global done
    done = False
    return jsonify(result_list)


@app.route('/history', methods=['POST'])
def get_history():
    file_result = file_results.query.filter_by(ip=str(request.remote_addr)).all()
    return jsonify({"file_results": list(map(lambda x: {"filename": x.filename, "Autism": x.Aresult, "Parkinson": x.Presult, "Depression": x.Dresult}, file_result))})


if __name__ == '__main__':
    app.run()

