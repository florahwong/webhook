# -*- coding:utf8 -*-
# !/usr/bin/env python

import os
import json
import urllib

from flask import Flask
from flask import request
from flask import make_response

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)
    res = json.dumps(res, indent=4)
    print(res)
    
    resp = make_response(res)
    resp.headers['Content-Type'] = 'application/json'
    return resp


def processRequest(req):
    if req.get("result").get("action") != "my-weather-action":
        return {}
    
    url = "https://query.yahooapis.com/v1/public/yql?"
    my_query = makeWeatherQuery(req)
    if my_query is None:
        return {}
    
    query = url + urllib.urlencode({'q': my_query}) + "&format=json"
    result = urllib.urlopen(query).read()
    result_data = json.loads(result)
    res = makeWebhookResult(result_data)
    return res


def makeWeatherQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(result_data):
    query = result_data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "weather-webhook"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')