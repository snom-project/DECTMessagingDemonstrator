#!/usr/bin/python
# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
from gevent import monkey; monkey.patch_all()
import gevent

import bottle
import os
import multiprocessing
import logging
import random

import datetime
import time

from bottle import Bottle, app, run, static_file, template, request, FormsDict
from multiprocessing import Process, Queue, cpu_count
from beaker.middleware import SessionMiddleware

from bottle_utils import html
from bottle_utils.i18n import I18NPlugin

from bottle_utils.i18n import lazy_ngettext as ngettext, lazy_gettext as _

from bottle import jinja2_view, route

# read from DB
from DB.DECTMessagingDb import DECTMessagingDb

viewer_autonomous = True

#examples
#msgDb.delete_db(account='1000')
#msgDb.delete_db()

devices = []
#devices = [
#           {'bt_mac': '00087B18E4DB', 'name': 'TAG 1', 'account': 'Passive', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : 'None', 'user_image': '/images/xray.jpeg', 'device_loggedin' : '1'},
#           {'bt_mac': '00087B18E51B', 'name': 'TAG 2', 'account': 'Passive', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': '1', 'beacon_gateway' : 'None', 'user_image': '/images/bed.jpeg', 'device_loggedin' : '1'},
#           {'bt_mac': '000413B50047', 'name': 'M90 Snom Medical', 'account': '7008', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : 'None', 'user_image': '/images/Heidi_MacMoran_small.jpg', 'device_loggedin' : '1'},
#           {'bt_mac': '00087B177E9F', 'name': 'M80 Alarm Message', 'account': '7003', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : '0815', 'user_image': '/images/Michelle_Simmons_small.jpg', 'device_loggedin' : '1'},
#           {'bt_mac': '000413B40044', 'name': 'M80 Alarm Call', 'account': '7004', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : 'None','user_image': '/images/Steve_Fuller_small.jpg', 'device_loggedin' : '1'},
#           {'bt_mac': '00087B177B4A', 'name': 'M70', 'account': '7001', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': '1', 'beacon_gateway' : 'None','user_image': '/images/depp.jpg', 'device_loggedin' : '1'}
#           
#           ]

# triggers redraw of the full page an change of num of elements
lastNumOfDevices = 0


template.settings = {
    'autoescape': True,
}

from bottle import url

template.defaults = {
    'url': url,
    'site_name': 'SnomLocationViewer',
}

LANGS = [
         ('de_DE', 'Deutsch'),
         ('en_US', 'English')
         #('fr_FR', 'français'),
         #('es_ES', 'español')
         ]

DEFAULT_LOCALE = 'en_US'
LOCALES_DIR = './locales'


session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': '/tmp/data',
    'session.auto': True,
    'session.encrypt_key': 'invoipwetrust',
    'session.validate_key': 'invoipwetrust'
}


bottle.debug(False)
# used for templates with multiple urls to download images etc.

bottle.TEMPLATE_PATH=("./views", "./templates")

tabulator_root="/tabulator/"
tabulator_root_path = ".%s" % tabulator_root

css_root="/css/"
css_root_path = ".%s" % css_root
images_root="/images/"
images_root_path = ".%s" % images_root
save_root="/uploads/"
save_root_path = ".%s" % save_root

tapp = bottle.default_app()
wsgi_app = I18NPlugin(tapp,
                      langs=LANGS,
                      default_locale=DEFAULT_LOCALE,
                      locale_dir=LOCALES_DIR,
                      domain='base'
                      )

app = SessionMiddleware(wsgi_app, session_opts)

from bottle import Jinja2Template


logger = logging.getLogger('myDM')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)

# login user
user = ''
password = ''
login_firstname = ''
login_lastname = ''

## helper
class PrettyFormsDict(FormsDict):
    
    def __repr__(self):
        # Return a string that could be eval-ed to create this instance.
        args = ', '.join('{}={!r}'.format(k, v) for (k, v) in sorted(self.items()))
        return '{}({})'.format(self.__class__.__name__, args)
    
    def __str__(self):
        # Return a string that is a pretty representation of this instance.
        args = ' ,\n'.join('\t{!r}: {!r}'.format(k, v) for (k, v) in sorted(self.items()))
        return '{{\n{}\n}}'.format(args)
## end helper


@bottle.hook('before_request')
def setup_request():
    if viewer_autonomous:
        # viewer needs to periodically update the database.
        schedule.run_pending()
        #schedule.run_continuously()

    request.session = request.environ['beaker.session']
    Jinja2Template.defaults['session'] = request.session
    # check if the session is still valid / check login status


# absolute path to tabular
@bottle.get('/tabulator/<filename:path>', no_i18n = True)
def load_tabulator(filename):
    return static_file(filename, root="%s" % (tabulator_root_path))

# absolute css path
@bottle.get('/css/<filename>', no_i18n = True)
def load_css(filename):
    return static_file(filename, root="%s" % (css_root_path))

#@bottle.get('/<filepath:path>/css/<filename>', no_i18n = True)
#def load_css(filepath, filename):
#    #    print("%s..%s." % (images_root_path, filepath))
#    return static_file(filename, root="%s" % (css_root_path))

@bottle.get('/images/<filename>', no_i18n = True)
def load_image(filename):
    #print("########################0")
    return static_file(filename, root="%s" % (images_root_path))

#@bottle.get('/<filepath:path>/images/<filename>', no_i18n = True)
#def load_image(filepath, filename):
#    #print("########################1")
#    return static_file(filename, root="%s" % (images_root_path))


import socket
import json
import sys

@route('/devicessync', no_i18n = True)
def devicessync():
    global devices

    return dict(data=devices)
    

@route('/table', no_i18n = True)
def table():
    print('tabulator')
    global devices

    # the data will be locally accesed, we need to know our server host
    host = bottle.request.get_header('host')
    print(host)
    
    return bottle.jinja2_template('m9bstatustable', title=_("M9B Device Location Status"), host=host)


@route('/get_m9b_device_status', no_i18n = True)
def get_m9b_device_status():
    global devices
    if msgDb:
        # MAX(time_stamp) is hard coded
        result = msgDb.read_m9b_device_status_db()
        
    return dict(data=result)


@route('/get_device/<bt_mac_key>', no_i18n = True)
def get_device(bt_mac_key):
    global devices
    if msgDb:
        result = msgDb.read_db(account=None, device_type='',  bt_mac=bt_mac_key, name='', rssi='', uuid='', beacon_type='', proximity='', beacon_gateway='', device_loggedin='', base_location='', base_connection='')
        
    return dict(data=result)


@route('/get_beacons/<bt_mac_key>', no_i18n = True)
def get_beacons(bt_mac_key):
    global devices
    if msgDb:
        result = msgDb.read_db(table='Beacons',
                               order_by="time_stamp DESC ",
                               account=None, device_type='',  bt_mac=bt_mac_key,
                               name='', rssi='', uuid='', beacon_type='',
                               proximity='', beacon_gateway='', beacon_gateway_name='',
                               time_stamp='', server_time_stamp='')
        
    return dict(data=result)


@route('/get_device_locations/<bt_mac_key>', no_i18n = True)
def get_device_locations(bt_mac_key):
    global devices
    if msgDb:
        # MAX(time_stamp) is hard coded
        result = msgDb.read_last_locations_db(table='Beacons',
                               order_by="MAX(time_stamp) DESC ",
                               group_by='beacon_gateway',
                               account=None, device_type='',  bt_mac=bt_mac_key,
                               name='', rssi='', uuid='', beacon_type='',
                               proximity='1', beacon_gateway='', beacon_gateway_name='',
                               time_stamp='', server_time_stamp='')
        
    return dict(data=result)


@bottle.route('/btmactable', method=['GET','POST'])
def btmactable():
    global devices
    
    if bottle.request.method == 'POST':
        # update all bt_macs.
        if len(bottle.request.forms):
            for idx, btmac in enumerate(bottle.request.forms):
                #print(btmac)
                #print(idx, bottle.request.forms.get(btmac))
                devices[idx]['bt_mac'] = bottle.request.forms.get(btmac)
                # save directly in DB
                # db is changed but not the memory data from Server!?
                if msgDb:
                    msgDb.update_db(account=devices[idx]['account'] , bt_mac=devices[idx]['bt_mac'])
        
    return bottle.jinja2_template('btmactable', title=_("BT-Mac Table"), devices=devices)


@bottle.route('/sms', method=['GET','POST'])
def sms():
    global devices
   
    if bottle.request.method == 'POST':
        IP = '127.0.0.1'
        PORT = 10300

        print('init socket...')

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((IP, PORT))
            s.settimeout(500)
        except socket.error as exc:
            print('Caught exception socket.error: {0}'.format(exc))
            sys.exit(0)
        print("init socket successfull")
        
       
        d = json.dumps(request.json).encode("ascii")
        #print('data:', d)
       
        # prepare XML data request
        xml_message = "<?xml version='1.0' encoding='UTF-8'?> <request version='1.0' type='json-data'><json-data><![CDATA[ {0} ]]></json-data> </request>".format(d.decode('ascii'))
        #print(xml_message)

        s.send(bytes(xml_message, 'utf-8'))
        #print('data sent')

        s.close()
    else:
        print('GET request of the page, do nothing')
    
    return bottle.jinja2_template('sms', title=_("SMS View"), devices=devices)


@bottle.route('/alarm', method=['GET','POST'])
def alarm():
    global devices
   
    if bottle.request.method == 'POST':
        IP = '127.0.0.1'
        PORT = 10300

        print('init socket...')

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((IP, PORT))
            s.settimeout(500)
        except socket.error as exc:
            print('Caught exception socket.error: {0}'.format(exc))
            sys.exit(0)
        print("init socket successfull")
        
       
        d = json.dumps(request.json).encode("ascii")
        #print('data:', d)
       
        # prepare XML data request
        xml_message = "<?xml version='1.0' encoding='UTF-8'?> <request version='1.0' type='json-data'><json-data><![CDATA[ {0} ]]></json-data> <jobtype>alarm</jobtype> </request>".format(d.decode('ascii'))
        #print(xml_message)

        s.send(bytes(xml_message, 'utf-8'))
        #print('data sent')
        
        s.close()
    else:
        print('GET request of the page, do nothing')
          
    return bottle.jinja2_template('alarm', title=_("Alarm View"), devices=devices)


# the content of the element triggered by AJAX reload
@bottle.route('/element/<deviceIdx>', name='element', method=['GET','POST'])
def run_element(deviceIdx):
    global devices
    
#    global lastNumOfDevices
#    
#    if not devices:
#        bottle.redirect('/location')
#    
#    print(len(devices))
#    # added and deleted elements need a full redraw
#    if len(devices) != int(lastNumOfDevices):
#        lastNumOfDevices = len(devices)
#        bottle.redirect('/location')
    try:
        device = devices[int(deviceIdx)]
    except:
        #logger.debug("deviceIdx:%s unknown, refresh browser" % deviceIdx)
        return ""
    #print('vorher:', datetime.datetime.today())
    # yield to greenlet queue
    gevent.sleep(0)
    return bottle.jinja2_template('element', title=_("Element View"), i=device)


# receives full list of devices in json format devices
@bottle.route('/location', name='location', no_i18n = True, method=['GET','POST'])
def run_location():
    global devices
    logger.debug("run_location: location update triggered.")

    if msgDb:
        result = msgDb.read_devices_db()
        devices = result
    else:
        updated_devices = request.json
        tmplist = []
        tmplist.append(updated_devices)
        devices = tmplist[0]
    
    logger.debug('Number of devices:%s' % len(devices))
    return('done')
    

@bottle.route('/', name='main', method='GET')
def run_main():
    request.session['test'] = request.session.get('test',0) + 1
    request.session.save()
    logger.debug("Session: %d" % request.session['test'])
    
    request.session['profile_firstname'] = 'NA'
    request.session['profile_lastname'] = 'NA'
    
    return bottle.jinja2_template('locationview', title=_("Location View"), devices=devices)

import schedule

if __name__ == "__main__":

    # connect DB
    msgDb = DECTMessagingDb(beacon_queue_size=5, odbc=False, initdb=True)

    # run web server
    #bottle.run(app=app, host="10.245.0.28", port=8080, reloader=True, debug=True)
    #host = "10.245.0.28"
    host = "0.0.0.0"
    #host = "10.110.11.132"

    #host = "10.110.16.75"
    #host = "192.168.188.21"
    #host = "192.168.55.23"

    if viewer_autonomous:
        # schedule db re_read
        logger.debug("main: schedule.every(5).seconds.do(run_location)")
        schedule.every(5).seconds.do(run_location)

    # quiet=False adds http logs
    #bottle.run(app=app, server="gevent", host=host, port=8081, reloader=False, debug=True, quiet=True)
    
    bottle.run(app=app, server='gunicorn', workers=4, host=host, port=8081, reloader=False, debug=True, quiet=True)
    
   
