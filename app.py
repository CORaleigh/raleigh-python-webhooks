#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import datetime

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))
    if req.get('result').get('action') != 'find_events':
        res = processGeocodeRequest(req) 
    else:
        res = processEventResult(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def processEventResult(req):
    baseurl = "https://maps.raleighnc.gov/arcgis/rest/services/SpecialEvents/SpecialEventsView/MapServer/0/query?"
    query = {'where' : "(EVENT_STARTDATE <= CURRENT_DATE + 7 AND EVENT_STARTDATE >= CURRENT_DATE) AND STATUS = 'Approved'", 'returnGeometry': 'false', 'outFields': '*'}
    if query is None:
        return {}
    url = baseurl + urlencode(query) + "&f=json"

    result = urlopen(url).read()
    data = json.loads(result)
    res = makeEventWebhookResult(data)
    return res  

def makeEventWebhookResult(data):
    features = data.get('features')
    if features is None:
        return {}
    if len(features) == 0:
        return {}

    speech = "The following events are scheduled in the next week. "
    names = []
    for f in features:
        name = f.get('attributes').get('EVENT_NAME')
        when = datetime.datetime.fromtimestamp(int(f.get('attributes').get('EVENT_STARTDATE')) / 1000).strftime("%A %B %d")
        speech += name.replace('St.', 'Saint ') + " on " + when + ", "
    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }

def processGeocodeRequest(req):
    baseurl = "https://maps.raleighnc.gov/arcgis/rest/services/Locators/CompositeLocator/GeocodeServer/FindAddressCandidates?"
    geocode_query = makeGeocodeQuery(req)
    if geocode_query is None:
        return {}
    geocode_url = baseurl + urlencode({'SingleLine': geocode_query, 'outSR': 4326}) + "&f=json"
    result = urlopen(geocode_url).read()
    data = json.loads(result)
    res = getGeocodeResult(data, req)
    return res
def getGeocodeResult(data, req):
    candidates = data.get('candidates')
    if candidates is None:
        return {}
    if len(candidates) == 0:
        return {}
    candidate = candidates[0]
    location = candidate.get('location')
    lon = location.get('x')
    lat = location.get('y')
    info = getServiceInfo(req)
    baseurl = "https://maps.raleighnc.gov/arcgis/rest/services/Services/PortalServices/MapServer/" + str(info.get('id')) + "/query?"
    query = makeQuery(lon, lat, info)
    if query is None:
        return {}
    url = baseurl + urlencode(query) + "&f=json"
    result = urlopen(url).read()
    data = json.loads(result)

    res = makeWebhookResult(data, info, req)
    return res        
def makeGeocodeQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    address = parameters.get("street-address")
    if address is None:
        return None
    return address

def makeQuery(lon, lat, info):
    param = {'geometry': {'x': str(lon), 'y': str(lat)}, 'inSR': 4326, 'geometryType': 'esriGeometryPoint', 'returnGeometry': 'false', 'outFields': info.get('outField')}
    if param is None:
        return None
    return param

def makeWebhookResult(data, info, req):
    features = data.get('features')
    if features is None:
        return {}
    if len(features) == 0:
        return {}

    feature = features[0]
    attributes = feature.get('attributes')
    att = attributes.get(info.get('outField'))
    
    speech = info.get('speech') + att

    if req.get('result').get('action') == 'find_recycling_week':
        week = int(datetime.datetime.today().strftime("%V")) % 2
        speech = "No this is not your recycling week"
        if att == 'A' and week == 1:
            speech = "Yes this is your recycling week"
        elif att == 'B' and week == 0:
            speech = "Yes this is your recycling week"


    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }

def getServiceInfo(req):
    action = req.get("result").get("action")
    
    if action == 'find_trash_day':
        parameter = req.get("result").get("parameters").get("solidwaste")
        return {'id': 12, 'outField': 'DAY', 'speech': 'Your ' + parameter + ' day is '}
    elif action == 'find_person':
        parameter = req.get("result").get("parameters").get("persons")
        if parameter == 'city council person':
            return {'id': 2, 'outField': 'COUNCIL_PERSON', 'speech': 'Your ' + parameter + ' is '}
    elif action == 'find_district':
        parameter = req.get("result").get("parameters").get("districts")
        if parameter == 'city council':
            return {'id': 2, 'outField': 'COUNCIL_DIST', 'speech': 'Your ' + parameter + ' district is '}
        elif parameter == 'citizen advisory committee':
            return {'id': 1, 'outField': 'NAME', 'speech': 'Your ' + parameter + ' district is '}
        elif parameter == 'police':
            return {'id': 3, 'outField': 'DISTRICT', 'speech': 'Your ' + parameter + ' district is '}
    elif action == 'find_recycling_week':
        #parameter = req.get("result").get("parameters").get("solidwaste")
        return {'id': 12, 'outField': 'WEEK', 'speech':''}
    else:
        return {}




if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
