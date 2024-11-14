import sys
import gevent.queue
from gevent.queue import JoinableQueue
import time
import timeit

import logging

logger = logging.getLogger('Parallel_Alarm')
loglevel = logging.DEBUG
logger.setLevel(loglevel)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

pa_queue = JoinableQueue(maxsize=5)

def alarm_worker():
    """main worker thread that runs the alarm message queue
    """    
    while True:
        exception_name = None
        gevent.sleep(0.0)
        starttime = timeit.default_timer()
        try:
            # unpack params
            msg_server, devices_per_base_ip, alarm_txt, alarm_prio, alarm_conf_type, alarm_status = pa_queue.get()

            logger.debug('#### alarm serial request task started')
            request_alarms_serial(msg_server, devices_per_base_ip, alarm_txt, alarm_prio, alarm_conf_type, alarm_status)
        except Exception as e:
            exception_name, exception_value, _ = sys.exc_info()
            #raise   # or don't -- it's up to you
        finally:
            if exception_name:
                logger.debug('alarm_worker: call to request_alarms_serial: %s %s', exception_name, exception_value)
            elapsed = 1000 * (timeit.default_timer() - starttime)
            pa_queue.task_done()
            logger.debug(f'#### Queue of size {pa_queue.qsize()}: current task took {elapsed:.2f}ms')
            break
    #print(gevent.getcurrent())
    # kill greenlet - otherwise mem leak
    gevent.kill(gevent.getcurrent())


def group_by_base_connection(data):
    """Groups a list of dictionaries by the 'base_connection' key.

    Args:
        data: A list of dictionaries, each containing a 'base_connection' key.

    Returns:
        A dictionary where keys are 'base_connection' values and values are lists of dictionaries with that 'base_connection'.
    """
    grouped_data = {}
    for item in data:
        base_connection = item['base_connection']
        if base_connection not in grouped_data:
            grouped_data[base_connection] = []
        grouped_data[base_connection].append(item)
    return grouped_data

def request_alarms_serial(msg_server, devices, alarm_txt, alarm_prio='1', alarm_conf_type='2', alarm_status='0'):
    if len(devices) > 0:
        logger.debug('Send %d alarm(s) to base %s.', len(devices)
                                                    , devices[0]["base_connection"]
                    )
        for device in devices:
            # yield for each alarm
            gevent.sleep(0.0)
            # fire alarm 
            msg_server.request_alarm(device["account"], 
                                alarm_txt, 
                                alarm_prio, 
                                alarm_conf_type, 
                                alarm_status)
            
            
            # self.request_alarm(device["account"], alarm_txt, alarm_prio, alarm_conf_type, alarm_status)
            # wait until next alarm can be sent on the same base
            time.sleep(1.5)
    return(len(devices))

def request_alarm_parallel(msg_server, devices, alarm_txt, alarm_prio='1', alarm_conf_type='2', alarm_status='0'):
    # plit devices into groups of base IPs.
    func_list = []
    grouped_result = group_by_base_connection(devices)
    #parallel = Parallel(n_jobs=len(grouped_result), verbose=100, return_as="generator")
    for key in grouped_result.keys():
        devices_per_base_ip = grouped_result[key]
        packed_params = (msg_server, devices_per_base_ip,
                         alarm_txt,
                         alarm_prio,
                         alarm_conf_type,
                         alarm_status
                        )
        pa_queue.put(packed_params)

        gevent.spawn(alarm_worker)
        # yield to worker
        gevent.sleep(0)
    return True

if __name__ == '__main__':
    msg_object = None
    devices = [{'account': '111', 'device_type': 'handset', 'bt_mac': '000413B50038', 'name': 'no name', 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': 'alarm', 'beacon_gateway': 'None', 'beacon_gateway_name': 'None', 'user_image': '/images/depp.jpg', 'device_loggedin': '1', 'base_location': 'M900', 'base_connection': '("192.168.188.47", 10300)', 'time_stamp': '2024-10-27 19:21:24.286572', 'tag_time_stamp': '2024-10-27 18:40:47.983782'}, 
               {'account': '500500500', 'device_type': 'handset', 'bt_mac': '000413B40F91', 'name': '3x500', 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': 'alarm', 'beacon_gateway': 'None', 'beacon_gateway_name': 'None', 'user_image': '/images/depp.jpg', 'device_loggedin': '1', 'base_location': 'M900', 'base_connection': '("192.168.188.47", 10300)', 'time_stamp': '2024-10-27 19:21:24.287795', 'tag_time_stamp': '2024-10-27 18:40:46.449513'}, 
               {'account': '600600600', 'device_type': 'handset', 'bt_mac': '000413B40B91', 'name': '3x600', 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': 'alarm', 'beacon_gateway': 'None', 'beacon_gateway_name': 'None', 'user_image': '/images/depp.jpg', 'device_loggedin': '1', 'base_location': 'M900', 'base_connection': '("192.168.188.85", 10300)', 'time_stamp': '2024-10-27 19:21:26.681126', 'tag_time_stamp': '2024-10-27 18:40:58.940385'},
               {'account': '600600600', 'device_type': 'handset', 'bt_mac': '000413B40B91', 'name': '3x600', 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': 'alarm', 'beacon_gateway': 'None', 'beacon_gateway_name': 'None', 'user_image': '/images/depp.jpg', 'device_loggedin': '1', 'base_location': 'M900', 'base_connection': '("192.168.188.85", 10300)', 'time_stamp': '2024-10-27 19:21:26.681126', 'tag_time_stamp': '2024-10-27 18:40:58.940385'},
               {'account': '600600600', 'device_type': 'handset', 'bt_mac': '000413B40B91', 'name': '3x600', 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': 'alarm', 'beacon_gateway': 'None', 'beacon_gateway_name': 'None', 'user_image': '/images/depp.jpg', 'device_loggedin': '1', 'base_location': 'M900', 'base_connection': '("192.168.188.99", 10300)', 'time_stamp': '2024-10-27 19:21:26.681126', 'tag_time_stamp': '2024-10-27 18:40:58.940385'},
               ]
    #request_alarm_parallel(msg_object, devices, '1', '1', '2', '0')
    request_alarm_parallel(msg_object, devices, 1, 1, 2, 0)

    for i in range(10):        # yield to worker
        gevent.sleep(0)
        time.sleep(0.1)
