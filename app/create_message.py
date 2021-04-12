import pyproxy as pp
from lxml import etree as ET
import lxml.builder
import datetime
import schedule
import time

import random

class create_message:

    def __init__(self):
        E = lxml.builder.ElementMaker()
        self.RESPONSE = E.response
        self.REQUEST = E.request
        self.SYSTEMDATA = E.systemdata
        self.NAME = E.name
        self.DATETIME = E.datetime
        self.TIMESTAMP = E.timestamp
        self.STATUS = E.status
        self.STATUSINFO = E.statusinfo
        self.EXTERNALID = E.externalid

        self.JOBDATA = E.jobdata
        self.ALARMNUMBER = E.alarmnumber
        self.REFERENCENUMBER = E.referencenumber
        self.PRIORITY = E.priority
        self.FLASH = E.flash
        self.RINGS = E.rings
        self.CONFIRMATIONTYPE = E.confirmationtype
        self.MESSAGES = E.messages
        self.MESSAGE1 = E.message1
        self.MESSAGE2 = E.message2
        self.MESSAGEUUID = E.messageuui

        self.SENDERDATA = E.senderdata
        self.LOCATION = E.location

        self.PERSONDATA = E.persondata
        self.ADDRESS = E.address


    # systeminfo: MS confirm response to FP:
    def response_systeminfo(self, externalid, _status, _statusinfo):
        final_doc = self.RESPONSE(
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  ),
                                  self.EXTERNALID(externalid),
                                  self.STATUS("1"),
                                  self.STATUSINFO("Accepted by external system")
                                  , version="1.0", type="systeminfo",)

        return final_doc


    # keep_alive: MS confirm response to FP:
    def response_keepalive(self, externalid, status, statusinfo):
        return self.response_systeminfo(externalid, status, statusinfo)


    # login: MS confirm response to FP:
    def response_login(self, externalid, _status, _statusinfo):
        final_doc = self.RESPONSE(
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  ),
                                  self.EXTERNALID(externalid),
                                  self.STATUS("1"),
                                  self.STATUSINFO("Accepted by external system")
                                  , version="1.0", type="login")

        return final_doc

if __name__ == "__main__":
    cm = create_message()
    print('Data generated')
    print(f'date:{datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")}, time:{format(int(datetime.datetime.utcnow().strftime("%s")), "x")}')
  
    xml_msg = cm.response_systeminfo('extID0001', 'status', 'info')
    print(f'XML Message response_systeminfo: {ET.tostring(xml_msg, pretty_print=True, encoding="unicode")}')

    xml_msg = cm.response_keepalive('extID0001', 'status', 'info')
    print(f'XML Message response_keepalive: {ET.tostring(xml_msg, pretty_print=True, encoding="unicode")}')
    
    xml_msg = cm.response_login('extID0001', 'status', 'info')
    print(f'XML Message response_login: {ET.tostring(xml_msg, pretty_print=True, encoding="unicode")}')
    