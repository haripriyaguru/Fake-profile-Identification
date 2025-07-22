from flask import Flask, render_template, request, redirect, url_for, session
import requests
import pandas as pd
import joblib
import json
import urllib.request
from model import train
from csv import DictWriter

model = joblib.load('insta_model.joblib')
app = Flask(__name__)
new_data = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    global new_data
    if request.method == 'POST':
        username = request.form['username']
        url = "https://instagram130.p.rapidapi.com/account-info"
        querystring = {"username": username}

        headers = {
            "X-RapidAPI-Key": "c7666bf527msh04c8f982fe47338p1f9b41jsn2782de9a6756",
            "X-RapidAPI-Host": "instagram130.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring).json()
        p_url = response['profile_pic_url_hd']
        urllib.request.urlretrieve(p_url, 'static/pp.jpg')
        new_data = {
            'profile pic': 0 if "44884218_345707102882519_2446069589734326272_n.jpg" in response[
                'profile_pic_url'] else 1,
            'nums/length username': sum([1 for x in username if x.isdigit()]) / len(username),
            'fullname words': len(list(response['full_name'].split())),
            'nums/length fullname': sum([1 for x in response['full_name'] if x.isdigit()]) / len(response['full_name']),
            'name==username': 1 if username == response['full_name'] else 0,
            'description length': len(response['biography']),
            'external URL': 1 if response['external_url'] != "null" else 0,
            '#posts': response['edge_owner_to_timeline_media']['count'],
            '#followers': response['edge_followed_by']['count'],
            '#follows': response['edge_follow']['count'],
            'private': 1 if response['is_private'] else 0
        }
        new_df = pd.DataFrame([new_data])
        prediction = model.predict(new_df)
        final_result = "Fake" if prediction[0] == 1 else "Real"
        with open('result_data.json', 'w') as file:
            json.dump({'result': final_result, 'response': response}, file)
        return url_for('result')


@app.route('/result')
def result():
    with open('result_data.json', 'r') as file:
        data = json.load(file)
        final_result = data['result']
        response_data = data['response']

    return render_template('result.html', result=final_result, response=response_data)


@app.route('/report')
def report():
    with open('result_data.json', 'r') as file:
        data = json.load(file)
        final_result = data['result']
    print(new_data)
    new_data['fake'] = 1 if final_result =="Real" else 0
    field_names = ['profile pic', 'nums/length username', 'fullname words', 'nums/length fullname', 'name==username',
                   'description length', 'external URL', 'private', '#posts', '#followers', '#follows', 'fake'
                   ]
    with open('dataset.csv', 'a') as f_object:
        dict_writer_object = DictWriter(f_object, fieldnames=field_names)
        dict_writer_object.writerow(new_data)
        f_object.close()
    train()
    global model
    model = joblib.load('insta_model.joblib')
    return render_template('index.html')


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run()
