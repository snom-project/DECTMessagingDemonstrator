""" DECT_KNX_gateway_connector fires action_urls to KNX gateway defined as
    ACTION_URLS = [
        #snom inhouse
        {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-an' , 'proximity': '2'},
        {'m9b_IPEI': '0328D783C6', 'device_bt_mac': '000413B40F91', 'url': '/1/1/10-an' , 'proximity': '2'}
    ]
    initialize Connector with:
    KNX_gateway = DECT_KNX_gateway_connector(knx_url='http://10.110.16.66:1234')
    fire an action:
    KNX_gateway.fire_KNX_action(bt_mac, beacon_gateway, proximity)
"""
from gevent import monkey; monkey.patch_all()
import gevent
from gevent.pool import Pool
#import gevent.queue
from gevent.queue import JoinableQueue
import requests
import logging
import random

## GLOBALS no longer used if DB connection is done
KNX_URL = 'http://192.168.178.22:1234'

# base is not used, we assume one KNX GW ..
ACTION_URLS = [
#snom inhouse
    {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-aus', 'proximity': '0'},
    {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-an' , 'proximity': '1'},
    {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-an' , 'proximity': '2'},
    {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-an' , 'proximity': '3'},
    {'m9b_IPEI': '0328D783C6', 'device_bt_mac': '000413B40F91', 'url': '/1/1/10-an' , 'proximity': '2'}
]

class DECT_KNX_gateway_connector:
    """handles all triggers from DECT messaging server

    For each trigger a get asynchronous requests is fired to the KNX Gateway.

    Returns:
        OK: in case it could be fired.
    """
    def __init__(self, knx_url='http://192.168.178.22:1234', maxsize=5, loglevel=logging.DEBUG):
        global ACTION_URLS

        # logging
        self.logger = logging.getLogger('DECT_KNX_Gateway')
        self.logger.setLevel(loglevel)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # queue for greenlets
        self.queue = JoinableQueue(maxsize)
        # greenlet pool
        self.pool = Pool(maxsize)

        self.knx_url = knx_url
        self.action_urls = ACTION_URLS

    def update_actions(self, list_of_actions):
        """Adds or updates a list of actions of the fornm
        [ {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-aus', 'proximity': '0'},
            ...
          {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-aus', 'proximity': '0'}
        ]
        """
        global ACTION_URLS

        if len(list_of_actions) > 0:
            # delete actions when existing first
            for action in list_of_actions:

                try:
                    idx = ACTION_URLS.index(action)
                    ACTION_URLS.remove(idx)
                except ValueError:
                    pass
                finally:
                    ACTION_URLS.append(action)
                    self.logger.debug('update_actions: add action=%s', action)
        else:
            self.logger.warning('update_actions: empty list of actions - do nothing!')


    # KNX Gateway actions get queued and worked on as greenlets
    def fire_KNX_action(self, device_bt_mac, gateway, trigger):
        """Fires an action URL to the KNX Gateway, if
        an action url for device_bt_mac=000413B5004B, gateway=0328D3C8FC, trigger='2',
        e.g. {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-an' , 'proximity': '2'}
        is defined.

        action url requests are added to a greenlet queue to support parallelism.

        Args:
            device_bt_mac (string): BTLE mac address of the handset
            gateway (string): IPEI of m9b
            trigger (string): trigger is M9B proximity, 0=outside, 1,2,3=inside
        """
        try:
            worker_task = self.pool.spawn(self.worker)
            # queue the parameters for the worker to fetch
            self.queue.put((worker_task, device_bt_mac, gateway, trigger))
            # yield to worker
            gevent.sleep(0)
        except:
            self.logger.error('pool full, action discarded')
            gevent.sleep(0)

        self.logger.debug('Pool free: %s', self.pool.free_count())



    # gevent greenlet worker working on queue item
    def worker(self):
        """worker for greenlet Pool executing _fire_KNX_action
        """
        while True:
            gevent.sleep(0) # make sure queue is responsive, without this queue is always fully consumed.
            (wt, device_bt_mac, gateway, trigger) = self.queue.get()
            try:
                # fire KNX
                self._fire_KNX_action(device_bt_mac, gateway, trigger)
            finally:
                self.queue.task_done()
                self.pool.killone(wt, block=False)
                self.logger.info(f'task {wt} finished, pool_free={self.pool.free_count()}')


    # the real work
    def _fire_KNX_action(self, device_bt_mac, gateway, trigger):
        """Fires action url base=knx_url action=matched["url"]
        only when list of Actions contain an action matching
        an action url for device_bt_mac=000413B5004B, gateway=0328D3C8FC, trigger='2',
        e.g. {'m9b_IPEI': '0328D3C8FC', 'device_bt_mac': '000413B5004B', 'url': '/1/1/10-an' , 'proximity': '2'}.

        Args:
            device_bt_mac (string): BTLE mac address of the handset
            gateway (string): IPEI of m9b
            trigger (string): trigger is M9B proximity, 0=outside, 1,2,3=inside

        Returns:
            Boolean: Always True when executed.
        """
        matched_bt_mac = next((item for item in self.action_urls
                                if item['m9b_IPEI'] == gateway and item['device_bt_mac'] == device_bt_mac and item['proximity'] == trigger
                             ), False)
        self.logger.info(f'match in list of actionURLS: {matched_bt_mac}')

        if not matched_bt_mac:
            self.logger.warning(f'No match in list of actionURLS for { device_bt_mac}, {gateway}, {trigger}')
            return False

        #request_url = f'{matched_bt_mac["base"]}{matched_bt_mac["url"]}'
        request_url = f'{self.knx_url}{matched_bt_mac["url"]}'

        beacon_action = True
        if beacon_action:
            try:
                s = requests.Session()
                s.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))

                r = s.get(request_url, timeout=1.0)
                self.logger.debug('fire_KNX_action: %s, response=%s', request_url, r)
            except:
                self.logger.debug('fire_KNX_action: cannot connect %s', request_url)
        else:
            self.logger.debug('fire_KNX_action: KXN disabled: %s', request_url)

        return True

if __name__ == "__main__":
    KNX_gateway = DECT_KNX_gateway_connector(knx_url='http://10.110.16.63:1234', maxsize=5, loglevel=logging.WARNING)

    for p in range(5):
        w = random.randint(1,10)
        print('add', w)
        for i in range(w):
            proximity = str(random.randint(0, 3))
            KNX_gateway.fire_KNX_action('000413B5004B', '0328D3C8FC', proximity)

    # wait until all actions are completed
    gevent.wait()
