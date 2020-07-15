"""
MedAI Assistant
Copyright (C) 2020  Abdullah Humayun, Abdul Razaque Soomro, Danysh Soomro

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from flask import Flask, render_template, url_for, request, redirect, session, jsonify,Response
import sqlite3
import pandas as pd
import importlib.util
import sklearn
import pickle
import shap
import os
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = "lightupskecher"
conn = sqlite3.connect("MedAi.db", check_same_thread=False)
app.config['UPLOAD_FOLDER'] = '/preprocess' 


def get_models():
    query = "select id, name, description from models"

    cur = conn.execute(query)

    return cur.fetchall()

def fetch_all_patients():
    cur = conn.execute('SELECT * from Patients')
    return cur.fetchall()

def fetch_all_doctors():
    cur = conn.execute('SELECT * from Doctors')
    return cur.fetchall()

def insert_into_users(name,email,password, admin):
    cur = conn.execute("INSERT INTO Users (name, email, password, admin) VALUES (?,?,?,?)", (name,email,password, admin))
    conn.commit()
    print("Row inserted: ", cur.lastrowid)

def get_features(model_id):
    """
    can we get an alternate type for easier to understand input?
    """
    query = 'select name,type,feat_order,model_id from features where model_id = ?'
    cur = conn.execute(query,(model_id,))
    result = cur.fetchall()
    return result

def add_features(model_id,features, feature_types, feat_order=None):

    feature_query = 'insert into features (name, type, model_id, feat_order) values (?,?,?,?)'
    i = 0
    for feature in features:
        if feat_order is None:
            if feature_types is None:
                conn.execute(feature_query,[feature,'string',model_id,i])
            else:
                conn.execute(feature_query,[feature,feature_types[i],model_id,i])
        else:
            if feature_types is None:
                conn.execute(feature_query,[feature,'string',model_id,feat_order[i]])
            else:
                conn.execute(feature_query,[feature,feature_types[i],model_id,feat_order[i]])
        i = i + 1
    conn.commit()

#TODO: validation
def add_model(model, model_name, desc, features=None,feature_types=None, feat_order=None, preprocess=None):
    print('reached')
    loaded_model = pickle.dumps(model)
    model_query = 'insert into models (name,description,model) values (?,?,?)'
    conn.execute(model_query,[model_name,desc,loaded_model])
    conn.commit()

    get_id_query = 'select MAX(id) from models'
    cur = conn.execute(get_id_query)
    model_id = cur.fetchone()
    model_id = model_id[0]

    if features is not None:
        add_features(model_id,features,feature_types, feat_order)
    
    if preprocess is not None:
        filename = secure_filename(preprocess.filename)
        # file.save(os.path.join('preprocess', preprocess.filename))
        with open('.\\preprocess\\' + str(filename), 'w') as file:
            file.write(filename)
        preprocess_query = 'insert into preprocess (file_name,model_id) values (?,?)'
        conn.execute(preprocess_query,[preprocess.filename, model_id])
        conn.commit()
    
    return model_id

#TODO: finish method
def convert_input(request):
    """
    convert input given through form into a model readable form. can be done through calling preprocess after converting to something like a dataframe
    additional arguements for further customization?
    """
    keys = [str(k) for k in request.keys()]
    print(request)
    feature_names = [k.split('-')[0] for k in keys]
    print(feature_names)
    feature_order = [int(k.split('-')[1]) for k in keys]
    feature_values = [request[keys[i]] for i in range(len(feature_names))]
    
    print(feature_order)
    print(feature_values)
    print('------------------------------------------------------------------------------------------------------')
    print(request)

    

    df = pd.DataFrame(columns=feature_names)
    df.loc[0] = feature_values
    print(df.head())

    query = 'select file_name from preprocess where model_id = ?'
    cur = conn.execute(query,(str(keys[0]).split('-')[2],))
    file_name = cur.fetchone()

    
    spec = importlib.util.spec_from_file_location("module.name", 'preprocess/' + file_name[0])
    preprocess = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preprocess)

    # preprocess = importlib.import_module('preprocess/' + file_name[0] + ".py")
    df = preprocess.preprocess(df)
    # df.to_csv("test.csv")
    return prediction(str(keys[0]).split('-')[2],df)

# finish
def prediction(model_id, df):
    """
    give input to model for prediction

    """
    query = "select model from models where id = ?"
    cur = conn.execute(query,(model_id,))

    model = cur.fetchone()[0]

    model = pickle.loads(model)
    results = model.predict(df)
    # return Response((explain(model,df)).getvalue(), mimetype='image/png')
    return explain(model,df)
        
def explain(model, df):
    """
    explain the results of the model prediction in this method

    """
    shap.initjs()
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(df)
    prediction = model.predict(df)
    fig = shap.force_plot(explainer.expected_value[0], shap_values[0], df.loc[0],matplotlib=True,show=False)
    
    fig = plt.gcf()
    output = BytesIO()
    plt.savefig(output,format='png',dpi=250, bbox_inches='tight')
    output.seek(0)
    plt.close(fig)
    # shap.summary_plot(shap_values[0], df.columns, plot_type="bar")
    return [output,prediction]

#login page
@app.route('/', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        email = request.form["inputEmail"]
        res = conn.execute('SELECT * from Users where email=?', (email,)).fetchone()
        if res == None:
            return render_template('login.html', message="Email does not exist")
        elif res[3] == request.form["inputPassword"]:
            session["email"] = email
            session["admin"] = res[4]
            session["name"] = res[1]
            if res[4] == 1:
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("home"))
        else:
            return render_template('login.html', message="Incorrect password")
    else:
        if "email" in session:
            return redirect(url_for("home"))
        return render_template('login.html', message="  ")

#route to doctor home page
@app.route('/home')
def home():
    if check_session():
        if check_admin() == 0:
            return render_template('home.html')
        else:
            return redirect(url_for("admin"))
    else:
        return redirect(url_for("login"))

#route to data entry page
@app.route('/entry',methods=['POST','GET'])
def entry():

    if check_session():
        if check_admin() == 0:
            return render_template('entry.html')
        else:
            return redirect(url_for("admin"))
    else:
        return redirect(url_for("login"))

#route to patient history
@app.route('/pathist')
def pathist():
    if check_session():
        if check_admin() == 0:
            return render_template('pathist.html')
        else:
            return redirect(url_for("admin"))
    else:
        return redirect(url_for("login"))

#route to diagnosis
@app.route('/diagnosis', methods=['POST'])
def diagnosis():
    img = None
    if request.method == "POST":
        req = request.form
        results = convert_input(req)
        img = results[0]
        prediction = results[1]
        print(prediction)
        buffer = b''.join(img)
        b2 = base64.b64encode(buffer)
        sunalt2=b2.decode('utf-8')
        if prediction[0] == 1:
            prediction = 'positive'
        else:
            prediction = 'negative'
    return render_template('diagnosis.html', image=sunalt2, prediction=prediction)

#route to admin home page
@app.route('/admin', methods=['GET','POST'])
def admin():
    
    if request.method == "POST":
        if request.form.get('btn-user') == "submitted":
            insert_into_users(request.form['name-user'], request.form['email-user'], request.form['pass-user'], request.form['check-admin'])
        elif request.form.get('btn-model') == "submitted":
            print(request.files)
            if 'upload-model' in request.files and 'upload-file' in request.files and 'upload-feat' in request.files:
                model = request.files['upload-model']
                model = pickle.load(model)
                features = request.files['upload-feat']
                features = pd.read_csv(features)
                preprocess = request.files['upload-file']
                
                add_model(model, request.form['name-model'], request.form['desc-model'],list(features['name']),list(features['type']),list(features['feat_order']),preprocess)

    if check_session():
        if check_admin() == 1:
            return render_template('admin.html')
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("login"))

#route to doctor history page
@app.route('/dochist')
def dochist():
    if check_session():
        if check_admin() == 1:
            return render_template('dochist.html')
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("login"))

#route to model list page
@app.route('/model_list', methods=['GET','POST'])
def model_list():
    if request.method == "POST":
        print('hey')
        req = request.form
        model_id = req['model_id']

        get_name = 'select file_name from preprocess where model_id = ?'
        cur = conn.execute(get_name, (model_id,))
        file_name = cur.fetchone()

        delete_queries = ['delete from preprocess where model_id = ?', 'delete from features where model_id = ?', 'delete from models where id = ?']

        for query in delete_queries:
            conn.execute(query,(model_id,))
            conn.commit()
        if os.path.exists('.\\preprocess\\' + str(file_name[0])):
            os.remove('.\\preprocess\\' + str(file_name[0]))

    if check_session():
        if check_admin() == 1:
            return render_template('model_list.html')
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("login"))

#login function
@app.route('/logout')
def logout():
    session.pop("email", None)
    session.pop("name", None)
    session.pop("admin", None)
    return redirect(url_for("login"))

#method to check if session is valid
def check_session():
    if "email" in session:
        return True
    else:
        False

#Method to check if the user is an admin or doctor
def check_admin():
    if session["admin"] == 1:
        return True
    else:
        return False

@app.route('/entry/_get_data/', methods=['POST'])
def _get_data():
    button_id = request.form["data"]
    app.logger.info(button_id)
    return jsonify({'data': render_template('response.html', button_id=button_id)})

app.jinja_env.globals.update(get_features=get_features)
app.jinja_env.globals.update(get_models=get_models)
app.jinja_env.globals.update(fetch_all_patients=fetch_all_patients)
app.jinja_env.globals.update(fetch_all_doctors=fetch_all_doctors)

if __name__ == "__main__":
    print("\nMedAI Assistant\nCopyright (C) 2020  Abdullah Humayun, Abdul Razaque Soomro, Danysh Soomro\n")
    app.run(debug=True)
    #app.run()