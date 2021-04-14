# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
from gevent import monkey

monkey.patch_all()
import gevent

import requests

import logging

import bottle
from bottle import app, template, request, url, FormsDict
from bottle import Jinja2Template
from beaker.middleware import SessionMiddleware


from bottle_utils.i18n import I18NPlugin
from bottle_utils.i18n import lazy_gettext as _

import redis

POOL = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)

def getVariable(variable_name):
    my_server = redis.Redis(connection_pool=POOL)
    response = my_server.get(variable_name)
    return response

def setVariable(variable_name, variable_value):
    my_server = redis.Redis(connection_pool=POOL)
    my_server.set(variable_name, variable_value)

template.settings = {
    "autoescape": True,
}

template.defaults = {
    "url": url,
    "site_name": "SnomLocationViewer",
}

LANGS = [
    ("de_DE", "Deutsch"),
    ("en_US", "English")
    # ('fr_FR', 'français'),
    # ('es_ES', 'español')
]

DEFAULT_LOCALE = "en_US"
LOCALES_DIR = "./locales"


session_opts = {
    "session.type": "file",
    "session.cookie_expires": 300,
    "session.data_dir": "/tmp/data",
    "session.auto": True,
    "session.encrypt_key": "invoipwetrust",
    "session.validate_key": "invoipwetrust",
}


bottle.debug(False)
# used for templates with multiple urls to download images etc.

bottle.TEMPLATE_PATH = ("./views", "./templates")

css_root = "/css/"
css_root_path = ".%s" % css_root
images_root = "/images/"
images_root_path = ".%s" % images_root
save_root = "/uploads/"
save_root_path = ".%s" % save_root

tapp = bottle.default_app()
wsgi_app = I18NPlugin(
    tapp,
    langs=LANGS,
    default_locale=DEFAULT_LOCALE,
    locale_dir=LOCALES_DIR,
    domain="base",
)

app = SessionMiddleware(wsgi_app, session_opts)

logger = logging.getLogger("DxSnomGateway")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s  %(name)s  %(levelname)s: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

## helper
class PrettyFormsDict(FormsDict):
    def __repr__(self):
        # Return a string that could be eval-ed to create this instance.
        args = ", ".join("{}={!r}".format(k, v) for (k, v) in sorted(self.items()))
        return "{}({})".format(self.__class__.__name__, args)

    def __str__(self):
        # Return a string that is a pretty representation of this instance.
        args = " ,\n".join(
            "\t{!r}: {!r}".format(k, v) for (k, v) in sorted(self.items())
        )
        return "{{\n{}\n}}".format(args)
## end helper


# define redis shared variables across threads from gunicorn
setVariable("WINDOWOPEN", "off")

TEMPERATURE = 0.0
IAQACC = 0
IAQ = 0
HUMIDITY = 0


@bottle.route("/window_open", method=["GET"], no_i18n=True)
def run_window_open():
    open_window()
    return 'Trying to open window...'


@bottle.route("/window_close", method=["GET"], no_i18n=True)
def run_window_close():
    close_window()
    return 'Trying to close window...'


@bottle.route("/window_off", method=["GET"], no_i18n=True)
def run_window_off():
    window_all_off()
    return 'Trying to close window...'


@bottle.route("/state", method=["GET"], no_i18n=True)
def run_state():
    global TEMPERATURE
    global IAQACC
    global IAQ
    global HUMIDITY
    
    return f'TEMPERATURE:{TEMPERATURE} IAQACC:{IAQACC} IAQ:{IAQ} HUMIDITY:{HUMIDITY} WINDOWOPEN:{getVariable("WINDOWOPEN").decode()}'


@bottle.route("/airquality", method=["GET", "POST"], no_i18n=True)
def run_airquality():
    global TEMPERATURE
    global IAQACC
    global IAQ
    global HUMIDITY

    if request.method == "POST":
        d = request.json
        logger.info("dict:%s", d)
        try:
            TEMPERATURE = float(d["TEMP"])
        except:
            pass
        try:
            IAQACC = int(d["IAQ-ACC"])
        except:
            pass
        try:
            IAQ = int(d["IAQ"])
        except:
            pass
        try:
            HUMIDITY = int(d["HUM"])
        except:
            pass
        try:
            setVariable("WINDOWOPEN", d["window"])
        except:
            pass
        return d

    else:
        logger.warning("GET request of the page, do nothing")
        return "GET request of the page, do nothing"


# receives full list of DEVICES in json format DEVICES
@bottle.route("/snomair", name="Snom Air", no_i18n=True, method=["GET"])
def run_snomair():
    # data has been collected in
    global TEMPERATURE
    global IAQ
    global IAQACC
    global HUMIDITY
    global IAQ

    open = False
    switch = False

    # get the state for this worker
    last_state = getVariable("last_state").decode()
    last_IAQ = int(getVariable("last_IAQ").decode())

    if IAQ < 100:
        qual_icon = "leaf-24px.png"
        iaq_text = "- good"
    if IAQ < 50:
        qual_icon = "leaf-24px.png"
        iaq_text = "- excellent"
    if IAQ >= 100:
        qual_icon = "virus_yellow.png"
        iaq_text = "- pause and leave the room"
        open = True
    if IAQ > 150:
        qual_icon = "virus_red.png"
        iaq_text = "- open windows shortly"
        open = True
    if IAQ > 200:
        qual_icon = "virus_red.png"
        iaq_text = "- open windows and leave"
        open = True
    if IAQ > 300:
        qual_icon = "virus_red.png"
        iaq_text = "- ! RUN !"
        open = True
    if IAQACC != 3:
        iaq_acc_text = "- calibrate"
        iaq_text = f'{iaq_text}{iaq_acc_text}'


    # we need a switching tolerance to avoid toggling
    if abs(IAQ - last_IAQ) >= 10:
        if last_state == "open":
            # do not close, tolerance not reached
            logger.info("last state=open, wish=%s", open)
        else:
            if last_state == "close":
                # respect the IAQ open threshhold
                logger.info("respect the current IAQ open threshhold=%s", open)

        # ok to switch, take next threshold
        last_IAQ = IAQ
        switch = True
    else:
        switch = False
        logger.info("tolerance not reached")

    
    logger.info("Final State: %s %s %s %s", IAQ, abs(IAQ - last_IAQ), open, last_state)
    logger.info("Window Open Sensor: %s", getVariable("WINDOWOPEN"))

    # check if we should open or close window.
    if switch and open and last_state == "close":
        open_window()
        last_state = "open"
        logger.info("run_snomair: window opened")
    else:
        if switch and not open and last_state == "open":
            # we can close
            close_window()
            last_state = "close"
            logger.info("run_snomair: window closed")

    setVariable("last_state", last_state)
    setVariable("last_IAQ", last_IAQ)

    # we got a response

    snom_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<InfoBoxQueue loop="true">
 <InfoBox duration="1">
  <Line pos="1">
   <Icon>kIconTypeFkeyDispCode</Icon>
   <Text>Corona alert, airquality control </Text>
  </Line>
   <Line pos="2">
   <Icon>http://10.110.16.63/sensor/{qual_icon}</Icon>
   <Text>{IAQ} / 300+ {iaq_text}</Text>
  </Line>
  </InfoBox>
  <InfoBox duration="1">
  <Line pos="1">
   <Icon>kIconTypeFkeyDispCode</Icon>
   <Text>Corona alert, airquality control, {TEMPERATURE:.1f} C</Text>
  </Line>
   </InfoBox>
  <InfoBox duration="1">
  <Line pos="1">
   <Icon>kIconTypeFkeyDispCode</Icon>
   <Text>Corona alert, airquality control, {HUMIDITY}% Humidity</Text>
  </Line>
 </InfoBox>
</InfoBoxQueue>
"""

    print(snom_xml)
    return snom_xml


# receives full list of DEVICES in json format DEVICES
@bottle.route("/json_action", name="json_action", no_i18n=True, method=["GET", "POST"])
def run_json_action():

    # run action to device
    request_url = "http://10.245.0.136:12380/cm?cmnd=Power%20TOGGLE"
    r_json = None
    snom_xml = '<?xml version="1.0" encoding="UTF-8"?><SnomIPPhoneText><Title>Error</Title><Text>Cannot access sensor</Text></SnomIPPhoneText>'
    beacon_action = True
    if beacon_action:
        try:
            s = requests.Session()
            s.mount("http://", requests.adapters.HTTPAdapter(max_retries=3))

            r = s.get(request_url, timeout=1.0)
            r_json = r.json()
            logger.debug("fire_action: %s, response=%s", request_url, r)
        except:
            logger.debug("fire_action: cannot connect %s", request_url)
    else:
        logger.debug("fire_action: Dx disabled: %s", request_url)
    # we got a response
    if r_json:
        print(r_json)
        json_dict = r_json
        val1 = json_dict["POWER"]
        # if val1=='OFF':
        #    val1 = 'Bad airquality'
        #    qual_icon='virus_red.png'
        if val1 == "OFF":
            val1 = "Excellent airquality"
            qual_icon = "leaf-24px.png"
        if val1 == "ON":
            val1 = "Medium airquality"
            qual_icon = "virus_yellow.jpg"

        #   kIconTypeFkeyStats -- alternative Sensor Icon.
        snom_xml = f"""
        <?xml version="1.0" encoding="UTF-8"?>
<InfoBoxQueue>
 <InfoBox>
  <Line pos="1">
   <Icon>kIconTypeFkeyDispCode</Icon>
   <Text>Corona alert, airquality control </Text>
  </Line>
  <Line pos="2">
   <Icon>http://10.245.0.28/sensor/{qual_icon}</Icon>
   <Text>{val1}</Text>
  </Line>
 </InfoBox>
</InfoBoxQueue>
"""

    return snom_xml


@bottle.route("/", name="main", method="GET")
def run_main():
    request.session["test"] = request.session.get("test", 0) + 1
    request.session.save()
    logger.debug("Session: %d", request.session["test"])

    request.session["profile_firstname"] = "NA"
    request.session["profile_lastname"] = "NA"

    return "nothing here."

def open_window():
    logger.debug("ow LOCK: %s", getVariable("LOCK").decode())

    if getVariable("LOCK").decode() != "locked":
        setVariable("LOCK", "locked")
        # make sure close is powerless
        if getVariable("WINDOWOPEN").decode() != "on":
            actors.set_expert_pc("2", "0")

            actors.set_expert_pc("1", "1")
            gevent.sleep(6.0)
            actors.set_expert_pc("1", "0")
        else:
            # to make sure we turn all off
            window_all_off()
            logger.debug("ow: WINDOWOPEN sensor was %s, we didnt do anything", getVariable("WINDOWOPEN").decode())

        setVariable("LOCK", "unlocked")
        logger.debug("ow window now opened LOCK: %s", getVariable("LOCK").decode())
    else:
        logger.debug("ow: another worker is running: %s", getVariable("LOCK").decode())
     

def close_window():
    logger.debug("cw LOCK: %s", getVariable("LOCK").decode())

    if getVariable("LOCK").decode() != "locked":
        setVariable("LOCK", "locked")
    
        if getVariable("WINDOWOPEN").decode() != "off":
            # make sure open is powerless
            actors.set_expert_pc("1", "0")

            actors.set_expert_pc("2", "1")
            gevent.sleep(6.0)
            actors.set_expert_pc("2", "0")
        else:
            # to make sure we turn all off
            window_all_off()
            logger.debug("cw: WINDOWOPEN sensor was %s, we didnt do anything", getVariable("WINDOWOPEN").decode())

        setVariable("LOCK", "unlocked")
        logger.debug("cw window now closed LOCK: %s", getVariable("LOCK").decode())
    else:
        logger.debug("cw: another worker is running: %s", getVariable("LOCK").decode())



def window_all_off():
    actors.set_expert_pc("1", "0")
    actors.set_expert_pc("2", "0")


if __name__ == "__main__":

    # Homematic connector (A. Thalmann)
    from actors import Actors

    actors = Actors("NoActorSystem", system_ip_addr='10.110.22.210')
    
    setVariable("last_state", "close")
    #open = False
    setVariable("last_IAQ", 0)
    setVariable("LOCK", "unlocked")


    # initally turn off all power
    window_all_off()

    # run web server
    # HOST = "10.245.0.28"
    HOST = "0.0.0.0"
    # HOST = "10.110.11.132"
    # HOST = "10.110.16.75"
    # HOST = "192.168.188.21"
    # HOST = "192.168.55.23"

    # quiet=False adds http logs
    #bottle.run(app=app, server="gevent", host=host, port=8081, reloader=False, debug=True, quiet=True)
    
    bottle.run(
        app=app,
        server="gunicorn",
        workers=2,
        host=HOST,
        port=8088,
        reloader=False,
        debug=True,
        quiet=True,
    )
