#!/usr/bin/python3
"""
.. codeauthor:: Andreas Thalmann <andreas.thalmann@snom.com>

Modul for interconnection to:

* Homematic (SmartHome solution)
* Gude Expert Power Control: http://wiki.gude.info/EPC_HTTP_Interface

"""
import json
import requests

def _get_homematic_port(interface):
    """

    :param interface:
    :return:
    """
    if interface == 'wired':
        port = 2000
    elif interface == 'system':
        port = 2002
    else:
        # interface == 'wireless'
        port = 2001
    return port


def _get_value(action):
    """

    :param action:
    :return:
    """
    if action:
        value = "true"
    else:
        value = "false"
    return value


class Actors:
    """
    I/O Class for actors
    """
    def __init__(self, actor_system, system_ip_addr='127.0.0.1'):
        """
        Init actor object of actor_system

        :param actor_system:
        """
        self.components = 513

        if actor_system != "NoActorSystem":
            print('do nothing')        
        else:
            self.system_ip_addr = system_ip_addr


    def get_json_expert_pc(self, params):
        """

        :param params:
        :return:
        """
        url = "http://{}/statusjsn.js".format(self.system_ip_addr)
        r = requests.get(url, params=params, verify=False, auth=None)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            return None


    def set_expert_pc(self, port, action):
        """

        :param port:
        :param action:
        :return:
        """
        if action == "1":
            switch = "1"
        else:
            switch = "0"
        if port is not None and switch is not None:
            params = {'components': self.components, 'cmd': 1, 'p': port, 's': switch}
        else:
            return None
        self.get_json_expert_pc(params)
        return params


    def get_expert_pc(self, port):
        """

        :param port:
        :return:
        """
        params = {'components': self.components}
        if port and port <= 8:
            port_json = self.get_json_expert_pc(params)
            return port_json["outputs"][port-1]["state"]
        else:
            return None
