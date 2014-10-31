#!/usr/local/bin/python3

import argparse
import json
import requests
import sys
import yaml

status = {}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='retrieve data from HiveAPI')
    parser.add_argument('--config', type=argparse.FileType('r'), nargs='?', default='pyhive.yml')
    parser.add_argument('--verbose', '-v', help='increase logging', action="store_true")
    args = parser.parse_args()
    config = yaml.load(args.config)

    session  = requests.Session()
    headers = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XmlHttpRequest',
    'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'
    }
    payload = { 'username': config['username'], 'password': config['password'] }

    try:
        # login to get session cookie
        r = session.post(config['baseURL'] + '/login', data=payload, allow_redirects=False)
    except requests.exceptions.HTTPError as error:
        status_code = r.status_code
        sys.exit( "Unable to login to Hive: %s" % (status_code) )

    if args.verbose:
        print("Login succeeded")

    try:
        weather = session.get(config['baseURL'] + '/myhive/weather', headers=headers)
        weather.raise_for_status()
        j = json.loads(weather.text)
        status['forecast'] = j['outside']
        status['temperature'] = j['inside']
        status['weather'] = j['weather']
        if args.verbose:
            print("Current Temp: %d Outside: %d Weather: %s" % (status[u'temperature'], status[u'forecast'], status[u'weather'] ))
    except requests.exceptions.HTTPError as error:
        status_code = weather.status_code
        sys.exit( "Requests to Hive failed: %s" % (status_code) )

    try:
        hotwater = session.get(config['baseURL'] + '/myhive/hotwater/schedule', headers=headers)
        j = json.loads(hotwater.text)
        if (j['current'] == 'OFF'):
            status['hotwater'] = 0
        else:
            status['hotwater'] = 1
        if args.verbose:
            print("Hot Water Status: %d" % (status[u'hotwater']))
    except requests.exceptions.HTTPError as error:
        status_code = hotwater.status_code
        sys.exit( "Requests to Hive failed: %s" % (status_code) )

    try:
        heating = session.get(config['baseURL'] + '/myhive/heating/target', headers=headers)
        j = json.loads(heating.text)
        status['target'] = j['target']
        if args.verbose:
            print("Target Temperature: %d" % (status[u'target']))
    except requests.exceptions.HTTPError as error:
        status_code = heating.status_code
        sys.exit( "Requests to Hive failed: %s" % (status_code) )

    try:
        logout = session.get(config['baseURL'] + '/logout')
    except requests.exceptions.HTTPError as error:
        sys.exit("Call to logout failed: %s" %(logout.status_code))

    try:
        emoncmsdata="{temperature:%.1f,target:%.1f,hotwater:%d,forecast:%.1f}" % (status['temperature'], status['target'], status['hotwater'], status['forecast'] )
        str="%s?node=%d&json=%s&apikey=%s" % ( config['emoncms_api_url'], config['nodeID'], emoncmsdata, config['emoncms_api_key'] )
        if args.verbose:
            print("POST to emoncms: %s" %(str))
        r = session.get(str)
    except requests.exceptions.HTTPError as error:
        status_code = r.status_code
        sys.exit( "POST to emoncms failed: %s" % (status_code) )
