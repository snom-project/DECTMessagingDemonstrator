# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
from gevent import monkey

monkey.patch_all()
import gevent

import requests

import logging

import bottle
from bottle import route, app, static_file, template, request, url, FormsDict
from bottle import Jinja2Template
from beaker.middleware import SessionMiddleware


from bottle_utils.i18n import I18NPlugin
from bottle_utils.i18n import lazy_gettext as _

# schedule the DB updates
import schedule


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

logger = logging.getLogger("DxSnomHateway")
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


@bottle.hook("before_request")
def setup_request():

    request.session = request.environ["beaker.session"]
    Jinja2Template.defaults["session"] = request.session
    # check if the session is still valid / check login status


TEMPERATURE = 0.0
IAQACC = 0
IAQ = 0
HUMIDITY = 0


@bottle.route("/airquality", method=["GET", "POST"], no_i18n=True)
def airquality():
    global TEMPERATURE
    global IAQACC
    global IAQ
    global HUMIDITY

    if request.method == "POST":
        d = request.json
        print("dict:", d)
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
    else:
        print("GET request of the page, do nothing")

    return d


# receives full list of DEVICES in json format DEVICES
@bottle.route("/snomair", name="Snom Air", no_i18n=True, method=["GET"])
def run_snomair():
    # data has been collected in
    global TEMPERATURE
    global IAQ
    global IAQACC
    global HUMIDITY
    global IAQ

    global last_state
    #global open # !!!! remove  
 
    open = False

    if IAQ < 100:
        qual_icon = "leaf-24px.png"
        iaq_text = "- good"
    if IAQ < 50:
        qual_icon = "leaf-24px.png"
        iaq_text = "- excellent"
    if IAQ > 100:
        qual_icon = "virus_yellow.png"
        iaq_text = "- pause and leave the room"
    if IAQ > 100:
        qual_icon = "virus_yellow.png"
        iaq_text = "- pause and leave the room"
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
        iaq_acc_text = "- calibrate, please"
        iaq_text = iaq_acc_text

    ### test open close switching
    #if open is True or open is None:
    #    open = False
    #else:
    #   open = True


    # check if we should open or close window.
    if open and last_state == "close":
        open_window()
        last_state = "open"
        logger.info("run_snomair: window opened")
    else:
        if if not open and last_state == "close":
            # we can close 
            close_window()
            last_state = "close"
            logger.info("run_snomair: window closed")


    # we got a response

    #   kIconTypeFkeyStats -- alternative Sensor Icon.
    # More than 2 lines are NOT WORKING
    snom_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<InfoBoxQueue>
 <InfoBox>
  <Line pos="1">
   <Icon>kIconTypeFkeyDispCode</Icon>
   <Text>Corona alert, airquality control </Text>
  </Line>
  <Line pos="2">
   <Icon>http://10.245.0.28/sensor/{qual_icon}</Icon>
   <Text>{IAQ} / 250 {iaq_text}</Text>
  </Line>
  <Line pos="3">
   <Icon>kIconTypeFkeyDispCode</Icon>
   <Text>{TEMPERATURE:.1f} C</Text>
  </Line>
  <Line pos="4">
   <Icon>kIconTypeFkeyDispCode</Icon>
   <Text>{HUMIDITY} Humidity</Text>
  </Line>
 </InfoBox>
</InfoBoxQueue>
"""

    snom_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<InfoBoxQueue loop="true">
 <InfoBox duration="1">
  <Line pos="1">
   <Icon>kIconTypeFkeyDispCode</Icon>
   <Text>Corona alert, airquality control </Text>
  </Line>
   <Line pos="2">
   <Icon>http://10.245.0.28/sensor/{qual_icon}</Icon>
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
    # fetch example TXT - not used
    snom_xmlt = f"""<?xml version="1.0" encoding="UTF-8"?>
<SnomIPPhoneText>
    <Title>Demo</Title>
    <Text>
   {IAQ} / 300+ {iaq_text}
        <br/>
   Corona alert, airquality control, {TEMPERATURE:.1f}
    </Text>
<Fetch mil="5000">http://10.245.0.28:8088/snomair</Fetch>
</SnomIPPhoneText>
 """
    print(snom_xml)
    return snom_xml


# receives full list of DEVICES in json format DEVICES
@bottle.route("/json_action", name="json_action", no_i18n=True, method=["GET", "POST"])
def run_ljson_action():

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
    # make sure close is powerless
    actors.set_expert_pc("2", "0") 

    actors.set_expert_pc("1", "1")
    gevent.sleep(5.0) 
    actors.set_expert_pc("1", "0")

def close_window():
    # make sure open is powerless
    actors.set_expert_pc("1", "0")

    actors.set_expert_pc("2", "1") 
    gevent.sleep(5.0) 
    actors.set_expert_pc("2", "0") 

def window_all_off():
    actors.set_expert_pc("1", "0")
    actors.set_expert_pc("2", "0") 


if __name__ == "__main__":

# Homematic connector (A. Thalmann)
    from actors import Actors

    actors = Actors("NoActorSystem", system_ip_addr='10.110.22.210')
    last_state = "close"
    open = False

    # inital turn off all power
    window_all_off()

    # run web server
    # HOST = "10.245.0.28"
    HOST = "0.0.0.0"
    # HOST = "10.110.11.132"
    # HOST = "10.110.16.75"
    # HOST = "192.168.188.21"
    # HOST = "192.168.55.23"

    # quiet=False adds http logs
    # bottle.run(app=app, server="gevent", host=host, port=8081, reloader=False, debug=True, quiet=True)
    bottle.run(
        app=app,
        #server="gunicorn",
        #workers=1,
        host=HOST,
        port=8088,
        reloader=False,
        debug=True,
        quiet=True,
    )
