# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
from gevent import monkey; monkey.patch_all()
import gevent

import os

import logging
import requests

import bottle
from bottle import route, app, static_file, template, request, url, FormsDict
from bottle import Jinja2Template
from bottle import response

from beaker.middleware import SessionMiddleware


from bottle_utils.i18n import I18NPlugin
from bottle_utils.i18n import lazy_gettext as _

# read from DB
from DB.DECTMessagingDb import DECTMessagingDb

# schedule the DB updates
import schedule
import time

from DECTMessagingConfig import *

VIEWER_AUTONOMOUS = True
MINIMUM_VIEWER = False

#examples
#msgDb.delete_db()

DEVICES = []
COUNTDEVICES = []

#DEVICES = [
#           {'bt_mac': '00087B18E4DB', 'name': 'TAG 1', 'account': 'Passive', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : 'None', 'user_image': '/images/xray.jpeg', 'device_loggedin' : '1'},
#           {'bt_mac': '00087B18E51B', 'name': 'TAG 2', 'account': 'Passive', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': '1', 'beacon_gateway' : 'None', 'user_image': '/images/bed.jpeg', 'device_loggedin' : '1'},
#           {'bt_mac': '000413B50047', 'name': 'M90 Snom Medical', 'account': '7008', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : 'None', 'user_image': '/images/Heidi_MacMoran_small.jpg', 'device_loggedin' : '1'},
#           {'bt_mac': '00087B177E9F', 'name': 'M80 Alarm Message', 'account': '7003', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : '0815', 'user_image': '/images/Michelle_Simmons_small.jpg', 'device_loggedin' : '1'},
#           {'bt_mac': '000413B40044', 'name': 'M80 Alarm Call', 'account': '7004', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : 'None','user_image': '/images/Steve_Fuller_small.jpg', 'device_loggedin' : '1'},
#           {'bt_mac': '00087B177B4A', 'name': 'M70', 'account': '7001', 'uuid': 'empty', 'beacon_type': 'None', 'proximity': '1', 'beacon_gateway' : 'None','user_image': '/images/depp.jpg', 'device_loggedin' : '1'}
#
#           ]

# triggers redraw of the full page an change of num of elements
LAST_NUM_OF_DEVICES = 0


template.settings = {
    'autoescape': True,
}

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

logger = logging.getLogger('DMViewer')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

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
    if VIEWER_AUTONOMOUS:
        # viewer needs to periodically update the database.
        schedule.run_pending()
        #schedule.run_continuously()

    request.session = request.environ['beaker.session']
    Jinja2Template.defaults['session'] = request.session
    # check if the session is still valid / check login status


import subprocess
import shlex

@route('/restart', method=['GET'], no_i18n = True)
def do_restart():
    subprocess.call(shlex.split('./restart_all.sh 10 no'))
    return 'restarting... wait approx. 1min'
 

@route('/upload', method=['GET','POST'], no_i18n = True)
def do_upload():
    if request.method == 'POST':
        category = request.forms.get('category')
        upload = request.files.get('upload')
        name, ext = os.path.splitext(upload.filename)
        if ext not in ('.py'):
            return "File extension not allowed."

        save_path = save_root_path
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        file_path = "{path}/{file}".format(path=save_path, file=upload.filename)
        upload.save(file_path)
        return "File successfully saved to '{0}'.".format(save_path)

    else:
       return '''<form action="/upload" method="post" enctype="multipart/form-data">
  Category:      <input type="text" name="category" />
  Select a file: <input type="file" name="upload" />
  <input type="submit" value="Start upload" />
</form>'''
    


# absolute path to tabular
@bottle.get('/tabulator/<filename:path>', no_i18n = True)
def load_tabulator(filename):
    return static_file(filename, root="%s" % (tabulator_root_path))

# css directory 
@route('/css/<filepath:path>')
def css_static(filepath):
    return static_file(filepath, root="%s" % (css_root_path))

# absolute css path
#@bottle.get('/css/<filename>', no_i18n = True)
#def load_css(filename):
#    return static_file(filename, root="%s" % (css_root_path))

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


# XML Minibrowser server simulation
# http://ipphones.onenet.acs.vodafone.gr:7548/provision.xml?mac=000413907100
@route('/sim/<provision>', no_i18n = True)
def handle_provision(provision):
    if provision=='provision.xml':
        userid=''
        mac = request.GET.get('mac', '').strip()
        userid = request.GET.get('userid', '').strip()
        print(mac, userid)
        
        if request.method == 'GET':
            if mac == '000413907100' and userid=='':
                response.status = 200
                print(f'ALLOWED={mac}')
                return '''<SnomIPPhoneInput>
    <Title>Enter ID</Title>
    <Promt></Promt>
    <URL>http://52.29.201.238:8081/sim/provision2.xml</URL>
    <InputItem>
    <DisplayName>Enter Login ID</DisplayName>
    <QueryStringParam>mac=000413907100&amp;type=password&amp;userid</QueryStringParam>
    <InputFlags>n</InputFlags>
    </InputItem>
    </SnomIPPhoneInput>
                '''
            else:
                response.status = 404
                return 'fail - no mac specified, use ?mac=000413907100'
    
    elif provision=='provision2.xml':
        password=''
        userid=''
        mac = request.GET.get('mac', '').strip()
        type = request.GET.get('type', '').strip()
        userid = request.GET.get('userid', '').strip()
        password = request.GET.get('password', '').strip()
        print(mac, userid)
        
        if request.method == 'GET':
            if mac == '000413907100' and userid!='' and type=='password' and password=='':
                response.status = 200
                print(f'ALLOWED=MAC={mac}, userID={userid} -> request password')
                return f'<SnomIPPhoneInput><Title></Title><Promt></Promt><URL>http://52.29.201.238:8081/sim/provision2.xml?</URL><InputItem><DisplayName>Enter Login PIN</DisplayName><QueryStringParam>mac=000413907100&userid={userid}&password</QueryStringParam><InputFlags>pn</InputFlags></InputItem></SnomIPPhoneInput>'
            elif mac == '000413907100' and userid!='' and password!='':
                response.status = 200
                print(f'ALLOWED={mac}, {userid}, {password}')
                return f'<SnomIPPhoneText><Title>Demo</Title><Text>Welcome to Snom!<br/>user:{userid} -> Connection granted!</Text></SnomIPPhoneText>'
            else:
                response.status = 404
                return 'fail - no password specified'
    else:
        return 'fail, wrong xml requested'
               

@route('/devicessync', no_i18n = True)
def devicessync():
    global DEVICES

    return dict(data=DEVICES)


@route('/table', no_i18n = True)
def table():
    print('tabulator')
    global DEVICES

    # the data will be locally accesed, we need to know our server host
    current_host = request.get_header('host')
    print(current_host)

    return bottle.jinja2_template('m9bstatustable', title=_("M9B Device Location Status"), host=current_host)

@route('/count', no_i18n = True)
def count():
    global DEVICES

    # the data will be locally accesed, we need to know our server host
    current_host = request.get_header('host')

    return bottle.jinja2_template('m9bstatustablegroupm9b', title=_("M9B Number of Devices Status"), host=current_host)

# the content of the m9b count element triggered by AJAX reload
@bottle.route('/countelement/<deviceIdx>/<search_term>', name='element', method=['GET','POST'], no_i18n = True)
def run_countelement(deviceIdx,search_term):
    global COUNTDEVICES

    # the data will be locally accesed, we need to know our server host
    current_host = request.get_header('host')

    if msgDb:
        # MAX(time_stamp) is hard coded
        COUNTDEVICES = msgDb.read_m9b_device_status_4_db(search_term)
  
        # filter is prepared as POST from the page.. 
        # COUNTDEVICES need to be reduced in this case. 
   
    try:
        device_count_element = COUNTDEVICES[int(deviceIdx)]
    except IndexError:
        logger.debug("deviceIdx:%s unknown, refresh browser" % deviceIdx)
        return ""
    # yield to greenlet queue
    gevent.sleep(0)
    return bottle.jinja2_template('countelement', title=_("M9B # Element"), i=device_count_element, search_term=search_term, host=current_host)

@route('/m9b_count_devices',method=['GET','POST'], no_i18n = True)
def m9b_count_devices():
    global COUNTDEVICES

    if request.method == 'POST':
        search_term = request.forms.get("myDeviceSearch")
    else:
        search_term='%'

    # the data will be locally accesed, we need to know our server host
    current_host = request.get_header('host')

    if msgDb:
        # MAX(time_stamp) is hard coded
        COUNTDEVICES = msgDb.read_m9b_device_status_4_db(search_term)
        print("M9B Status Count:")
        print(COUNTDEVICES)

    return bottle.jinja2_template('m9bcountdevicesview', title=_("Number of Devices per M9B"), host=current_host, devices=COUNTDEVICES, search_term=search_term)


@route('/get_m9b_device_status', no_i18n = True)
def get_m9b_device_status():
    global DEVICES
    if msgDb:
        # MAX(time_stamp) is hard coded
        result = msgDb.read_m9b_device_status_db()
                
    return dict(data=result)


@route('/get_m9b_device_status_count', no_i18n = True)
def get_m9b_device_status_count():
    global DEVICES
    if msgDb:
        # MAX(time_stamp) is hard coded
        result = msgDb.read_m9b_device_status_3_db()
        #print("M9B Status Count:")
        #print(result)

    return dict(data=result)


@route('/get_device/<bt_mac_key>', no_i18n = True)
def get_device(bt_mac_key):
    global DEVICES
    if msgDb:
        result = msgDb.read_db(account=None, device_type='',  bt_mac=bt_mac_key, name='', rssi='', uuid='', beacon_type='', proximity='', beacon_gateway='', device_loggedin='', base_location='', base_connection='')

    return dict(data=result)


@route('/get_beacons/<bt_mac_key>', no_i18n = True)
def get_beacons(bt_mac_key):
    global DEVICES
    if msgDb:
        result = msgDb.read_db(table='Beacons',
                               order_by="time_stamp DESC ",
                               account=None, device_type='',  bt_mac=bt_mac_key,
                               name='', rssi='', uuid='', beacon_type='',
                               proximity='', beacon_gateway='', beacon_gateway_name='',
                               time_stamp='', server_time_stamp='')

    return dict(data=result)


@route('/get_alarms/<account>', no_i18n = True)
def get_alarms(account):
    global DEVICES
    if msgDb:
        result = msgDb.read_db(table='Alarms',
                               order_by="time_stamp DESC ",
                               account=account,
                               name='',
                               alarm_type='',
                               beacon_type='',
                               beacon_broadcastdata='',
                               beacon_bdaddr='',
                               rssi_s='', rfpi_s='',
                               rssi_m='', rfpi_m='',
                               rssi_w='', rfpi_w='',
                               time_stamp='', server_time_stamp='')

    return dict(data=result)


@route('/get_device_locations/<bt_mac_key>', no_i18n = True)
def get_device_locations(bt_mac_key):
    global DEVICES
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


# receives full list of DEVICES in json format DEVICES
@bottle.route('/location', name='location', no_i18n = True, method=['GET','POST'])
def run_location():
    global DEVICES
    logger.debug("run_location: location update triggered.")

    if msgDb:
        DEVICES = []
        DEVICES = msgDb.read_devices_db()
    else:
        updated_devices = request.json
        tmplist = []
        tmplist.append(updated_devices)
        DEVICES = tmplist[0]

    logger.debug('Number of devices:%s', len(DEVICES))
    return True


if not MINIMUM_VIEWER:
    @bottle.route('/btmactable', method=['GET','POST'])
    def btmactable():
        global DEVICES

        if request.method == 'POST':
            # update all bt_macs.
            if len(request.forms) > 0:
                for idx, btmac in enumerate(request.forms):
                    #print(btmac)
                    #print(idx, bottle.request.forms.get(btmac), btmac)
                    DEVICES[idx]['bt_mac'] = request.forms.get(btmac)
                    # save directly in DB
                    # db is changed but not the memory data from Server!?
                    if msgDb:
                        msgDb.update_with_key_db(account=DEVICES[idx]['account'] , bt_mac=DEVICES[idx]['bt_mac'])

        return bottle.jinja2_template('btmactable', title=_("BT-Mac Table"), devices=DEVICES)


    @bottle.route('/sms', method=['GET','POST'])
    def sms():
        """SMS messaging page. Let's you select reciepients and message to send to M900 multicell.

        Returns:
            web page : Post or Get request answer resulting from the sms template
        """
        global DEVICES
        
        # select only devices able to receive smss.
        smsDevices = [d for d in DEVICES if d['device_type'] == "handset"]

        if request.method == 'POST':
            ip = '127.0.0.1'
            port = 10300

            print('init socket...')

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect((ip, port))
                s.settimeout(500)
            except socket.error as exc:
                print('Caught exception socket.error: {0}'.format(exc))
                sys.exit(0)
            print("init socket successfull")


            d = json.dumps(request.json).encode("ascii")
            #print('data:', d)

            # prepare XML data request
            xml_message = "<?xml version='1.0' encoding='UTF-8'?> <request version='1.0' type='json-data'><json-data><![CDATA[ {0} ]]></json-data> <jobtype>sms</jobtype> </request>".format(d.decode('ascii'))
            #print(xml_message)

            s.send(bytes(xml_message, 'utf-8'))
            #print('data sent')

            s.close()
        else:
            print('GET request of the page, do nothing')

        return bottle.jinja2_template('sms', title=_("SMS View"), devices=smsDevices)


    @bottle.route('/send_sms', no_i18n = True, method=['POST'], )
    def send_sms():
        """SMS POST requests listener. 
            Expects necessary data for a single SMS in JSON format.

            JSON format example:
            {
                "externalid": "id_3x100", 
                "name": "3x100", 
                "account": "100100100",
                "message": "SMS sample message",
                "priority": "0",
                "confirmationtype": "2",
                "rings": "1"
            }

        Returns:
            text : Post request answer 'Success' or 'Failure'
        """
        if request.method == 'POST':
            # prepare to send the data to the messaging viewer.
            ip = '127.0.0.1'
            port = 10300

            print('init socket...')

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect((ip, port))
                s.settimeout(500)
            except socket.error as exc:
                print('Caught exception socket.error: {0}'.format(exc))
                return "Failure"
            print("init socket successfull")

            # convert to JSON payload
            try:
                d = json.dumps(request.json).encode("ascii")
                # prepare XML data request
                xml_message = "<?xml version='1.0' encoding='UTF-8'?> <request version='1.0' type='json-data'><json-data><![CDATA[ {0} ]]></json-data> <jobtype>send_sms</jobtype> </request>".format(d.decode('ascii'))
        
                s.send(bytes(xml_message, 'utf-8'))
                #print('data sent')
            except :
                e = sys.exc_info()[0]
                logger.debug("send_sms: failed to convert JSON post and send. Error: %s", e)
            finally:
                s.close()
        else:
            print('GET request of the page, do nothing')

        return "Success"


    @bottle.route('/alarm', method=['GET','POST'])
    def alarm():
        global DEVICES

        # select only devices able to receive alarms.
        alarmDevices = [d for d in DEVICES if d['device_type'] == "handset"]

        if request.method == 'POST':
            ip = '127.0.0.1'
            port = 10300

            #print('init socket...')

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect((ip, port))
                s.settimeout(500)
            except socket.error as exc:
                print('Caught exception socket.error: {0}'.format(exc))
                sys.exit(0)
            #print("init socket successfull")

            d = json.dumps(request.json).encode("ascii")

            # prepare XML data request
            xml_message = "<?xml version='1.0' encoding='UTF-8'?> <request version='1.0' type='json-data'><json-data><![CDATA[ {0} ]]></json-data> <jobtype>alarm</jobtype> </request>".format(d.decode('ascii'))
            #print(xml_message)

            s.send(bytes(xml_message, 'utf-8'))
            #print('data sent')

            s.close()
        else:
            print('show alarm page')

        return bottle.jinja2_template('alarm', title=_("Alarm View"), devices=alarmDevices)


    # the content of the element triggered by AJAX reload
    @bottle.route('/element/<deviceIdx>', name='element', method=['GET','POST'], no_i18n = True)
    def run_element(deviceIdx):
        global DEVICES

        # the data will be locally accesed, we need to know our server host
        current_host = request.get_header('host')

        try:
            device = DEVICES[int(deviceIdx)]
        except IndexError:
            #logger.debug("deviceIdx:%s unknown, refresh browser" % deviceIdx)
            return ""
        #print('vorher:', datetime.datetime.today())
        # yield to greenlet queue
        gevent.sleep(0)
        return bottle.jinja2_template('element', title=_("Element View"), i=device, host=current_host)


    @bottle.route('/removeDevice/<account>', name='removeDevice', method=['GET'], no_i18n = True)
    def run_removeDevice(account):
        global msgDb

        logger.debug("removeDevice: Delete device with account %s from DB", account)

        if msgDb and account:
            # if we get a permanent update from account via e.g. beacon, we cannot really delete
            msgDb.delete_db(table='Devices', account=account)
            msgDb.delete_db(table='Alarms', account=account)
            msgDb.delete_db(table='Beacons', account=account)
            msgDb.delete_db(table='m9bdevicestatus', account=account)
  
  
    # the content of the element triggered by AJAX reload
    @bottle.route('/tagelement/<deviceIdx>', name='element', method=['GET','POST'], no_i18n = True)
    def run_tagelement(deviceIdx):
        global DEVICES

        # the data will be locally accesed, we need to know our server host
        current_host = request.get_header('host')
        
         # filter devices for TAGs only /// for each tag its way to often!
        tagDevices = [d for d in DEVICES if d['device_type'] == "BTLETag"]
        
        try:
            device = tagDevices[int(deviceIdx)]
        except IndexError:
            #logger.debug("deviceIdx:%s unknown, refresh browser" % deviceIdx)
            return ""
        
        # yield to greenlet queue
        gevent.sleep(0)
        return bottle.jinja2_template('tagelement', title=_("Tag Element"), i=device, host=current_host)


    @bottle.route('/resetTAG/<deviceAccount>', name='resetTAG', method=['GET'], no_i18n = True)
    def run_resetTAG(deviceAccount):
        global DEVICES
        global msgDb

        # get Device with account
        tag_device = [d for d in DEVICES if d['account'] == deviceAccount]

        if msgDb and len(tag_device) == 1:
            accountx=tag_device[0]['account']
            msgDb.update_with_key_db(account=accountx, 
                                     proximity='holding')


    @bottle.route('/outsideAllTAGs/<m9bIPEI>', name='outsideAllTAGs', method=['GET'], no_i18n = True)
    def run_outsideAllTAGs(m9bIPEI):
        global DEVICES
        global msgDb

        logger.debug("outsideAllTAGs: Delete all devices from M9B:%s", m9bIPEI)
        if msgDb and m9bIPEI:
            msgDb.remove_all_devices_from_m9b_db(m9bIPEI)

    
    @bottle.route('/tags', name='tags', method=['GET','POST'], no_i18n = False)
    def run_tags():
        global DEVICES
        # get the latest 
        DEVICES = msgDb.read_devices_db()

        # filter devices for TAGs only 
        tagDevices = [d for d in DEVICES if d['device_type'] == "BTLETag"]

        return bottle.jinja2_template('tagview', title=_("Tag View"), devices=tagDevices)


    @bottle.route('/', name='main', method=['GET','POST'])
    def run_main():
        request.session['test'] = request.session.get('test',0) + 1
        request.session.save()
        logger.debug("Session: %d", request.session['test'])

        request.session['profile_firstname'] = 'NA'
        request.session['profile_lastname'] = 'NA'

        return bottle.jinja2_template('locationview', title=_("Location View"), devices=DEVICES)


if __name__ == "__main__":
    # connect DB
    msgDb = DECTMessagingDb(beacon_queue_size=5, odbc=False, initdb=False)

    # run web server
    #bottle.run(app=app, host="10.245.0.28", port=8080, reloader=True, debug=True)
    #host = "10.245.0.28"
    HOST = "0.0.0.0"

    if VIEWER_AUTONOMOUS:
        # schedule db re_read
        logger.debug("main: schedule.every(5).seconds.do(run_location)")
        schedule.every(5).seconds.do(run_location)

    # quiet=False adds http logs
    #bottle.run(app=app, server="gevent", host=host, port=8081, reloader=False, debug=True, quiet=True)
    #bottle.run(app=app, server='gunicorn', workers=4, host=HOST, port=8081, reloader=False, debug=True, quiet=True)
    # windows compatible 
    bottle.run(app=app, server='waitress', threads=8, host=HOST, port=8081, reloader=False, debug=True, quiet=True)
