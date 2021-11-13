from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import requests
import json
from miio import AirPurifierMB4
import os
import random
from datetime import date
import datetime
import time

import adafruit_dht
import board
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(6, GPIO.OUT)
GPIO.output(6, GPIO.HIGH)
global dht
dht = adafruit_dht.DHT11(board.D12, use_pulseio=False)

app=Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

with open('config.json', 'r') as f:
    config = json.load(f)

#purifier config
ip = config['purifier_ip']
token = config['purifier_token']
global air
air = AirPurifierMB4(ip, token)

#forecast config
openweathermap_key = config['openweathermap_key']

#airly config
global keys, airly_installation
keys = [y for (x,y) in config['airly_keys'].items()]
airly_installation = config['airly_installation_id']

#global conf
global lat,lng
lat = config['lat']
lng = config['lng']


@app.errorhandler(404)
@cross_origin()
def hehe(e):
    return index()

@app.route('/')
@cross_origin()
def index():
    a = {"/home_stats": "our values", "/outside_stats": "values of outside", "/suntime":"returns data of sunrise, sunset and daytime for 3 days", "/forecast": "returns data of temperature for 7 days forward"}
    return jsonify(a)

def getTemps():
    global dht
    print("===fetching data from DHT===")
    return dht.temperature, dht.humidity

def getAqi():
    global air
    print("===fetching data from miio===")
    return air.status().aqi

@app.route('/home_stats')
@cross_origin()
def ourHouse():
    temperature_c="n/a"
    humidity="n/a"
    pm25="n/a"
    try:
        pm25 = getAqi()
        print("===miio fetched===")
    except:
        print("error aqi")
    
    try:
        temperature_c, humidity = getTemps()
        print("===DHT fetched===")
    except:
        print("error dht")
    
    return jsonify({"PM25": pm25, "HUMIDITIY":humidity, "TEMPERATURE": temperature_c})

def airlyHelperFunc(*args):
    global keys
    parsed_keys = [item for item in keys if item not in args]
    return parsed_keys[random.randint(0, len(parsed_keys)-1)]

@app.route('/outside_stats')
@cross_origin()
def outside(*args):
    global airly_installation
    key=airlyHelperFunc(*args)
    airly_response = requests.get(f"https://airapi.airly.eu/v2/measurements/installation?installationId={airly_installation}", 
                                        headers={"Accept":"application/json", "apikey":f"{key}"})
    if airly_response.status_code!=200:
        return outside(key)
    return jsonify(airly_response.json()['current']['values'])

@app.route('/suntime')
@cross_origin()
def suntime():
    global lat,lng
    today=date.today()
    today_1 = date.today() + datetime.timedelta(days=1)
    today_2 = date.today() + datetime.timedelta(days=2)
    dates=[today,today_1,today_2]
    all_data=[]
    for x in dates:
        response = requests.get(f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&date={x}&formatted=0").json()['results']
        parsed_data = {'sunrise':response['sunrise'], 'sunset':response['sunset'], 'day_length': time.strftime('%H:%M:%S', time.gmtime(response['day_length']))}
        all_data.append(parsed_data)
    return jsonify(all_data)

@app.route('/forecast')
@cross_origin()
def forecast():
    global lat,lng, openweathermap_key
    result = requests.get(f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lng}&lang=pl&exclude=current,minutely,hourly,alerts&appid={openweathermap_key}").json()

    all_data=[]
    c=0
    for x in result['daily']:
        date=time.strftime('%Y-%m-%d', time.gmtime(x['dt']))
        temp = {k:round(v-273.15,1) for (k,v) in x['temp'].items()}
        feels_like = {k:round(v-273.15,1) for (k,v) in x['feels_like'].items()}
        icon_link = f"http://openweathermap.org/img/wn/{x['weather'][0]['icon']}@2x.png"
        data = {"date":date, "temp":temp, "feels_like": feels_like, "icon_id": icon_link, "desc":x['weather'][0]['description']}
        all_data.append(data)
        c+=1
        if c>=4:
            break
    return jsonify(all_data)

@app.route('/ip')
@cross_origin()
def return_ip():
    return jsonify({"ip": os.popen("hostname -I").read().strip()})



app.run(host='0.0.0.0', debug=True, port=2137)
