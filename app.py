from flask import Flask, jsonify
import requests
import json
from miio import AirPurifierMB4

import time
import board
import adafruit_dht

app=Flask(__name__)
dhtDevice = adafruit_dht.DHT22(board.D18)


@app.route('/')
def index():
    a = {"/home": "our values", "/outside": "values of outside"}
    return jsonify(a)

@app.route('/home')
def ourHouse():
    ip = "192.168.18.101"
    token = "866d566ce43d391f4186777c7b048a4e"
    air = AirPurifierMB4(ip, token)
    
    temperature_c = dhtDevice.temperature
    humidity = dhtDevice.humidity
    return jsonify({"PM25": air.status().aqi, "HUMIDITIY":humidity, "TEMPERATURE": temperature_c})

@app.route('/outside')
def outside():
    airly_response = requests.get("https://airapi.airly.eu/v2/measurements/installation?installationId=10279", 
                                    headers={"Accept":"application/json", "apikey":"iAsKo5NKI0wibVLvSbxMZn6JBOteg148"})
    return jsonify(airly_response.json()['current']['values'])


app.run(debug=True, port=2137)