# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
# copy from breakout_main.py
import config as cf

size = cf.size

num_m9bs = cf.num_m9bs
x_width, _ = size
x_step =  float(x_width) / float(num_m9bs)
m9bpositions = [
    
    # studerus
    {'m9b_IPEI': '0328DD5EF7','x': 0.0 * x_step, 'y':float(size[1])*0.90, 'z':0.0}, # left
    {'m9b_IPEI': '0328D7848C','x': 1.0 * x_step, 'y':float(size[1])*0.90, 'z':0.0}, # midleft
    {'m9b_IPEI': '0328DD5D8E','x': 2.0 * x_step, 'y':float(size[1])*0.90, 'z':0.0}, # midright
    {'m9b_IPEI': '0328DD5EFC','x': 3.0 * x_step, 'y':float(size[1])*0.90, 'z':0.0}, # right
    
    # home
    {'m9b_IPEI': '0328D3C918','x': 0.0 * x_step, 'y':float(size[1])*0.90, 'z':0.0},
    {'m9b_IPEI': '0328D7830E','x': 1.0 * x_step, 'y':float(size[1])*0.90, 'z':0.0},
    {'m9b_IPEI': '0328D3C922','x': 2.0 * x_step, 'y':float(size[1])*0.90, 'z':0.0},
] 

def sort_m9b_rssi(selected):
    ''' Return the M9B with the nearest rssi from the M9B list '''
    # get the best visible rssi m9b
    # sort in place
    selected.sort(key=lambda item: item.get("rssi"))
    #print('sorted', selected)
    return selected
    
def get_m9bposition(ipei):
    ''' return the M9B position to matching ipei from m9bpositions list '''
    match = next( (item for item in m9bpositions if item["m9b_IPEI"] == ipei ), None )
    return match

def update_all_devices(msgDb):
    '''
        All devices and their corresponding M9Bs are updated.

        DB sample record:
        [{'account': '000413B50038', 'bt_mac': '000413B50038',
        'rssi': '-53', 'uuid': 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF90FF',
        'beacon_type': 'a', 'proximity': '3',
        'beacon_gateway_IPEI': '0328D3C918', 'beacon_gateway_name': 'Schreibtisch',
        'time_stamp': '2020-10-29 10:44:22.489801', 'server_time_stamp': '2020-10-29 09:44:22',
        'timeout': 96945}]

        real location is defined in list m9bpositions, e.g.
        {'m9b_IPEI': '000413666660', 'x': 0.0, 'y':0.0},
    '''
    if msgDb:
        result = msgDb.read_m9b_device_status_db()
        #print(result)

        btmacs_non_unique = [ sub['bt_mac'] for sub in result ]
        btmacs_set = set(btmacs_non_unique)
        btmacs = list(btmacs_set)
        #print('unique btmacs:', btmacs)
        position_list = []
        for idx, btmac in enumerate(btmacs):
            # get m9b data for btmac
            selected_items = [{k:d[k] for k in d if k!="a"} for d in result if d.get("bt_mac") == btmac]
            #print('selected_items:' , selected_items)
            # create list of visible m9bs
            gateway_list = []
            for elem in selected_items:
                if elem['proximity'] != '0' and get_m9bposition(elem['beacon_gateway_IPEI']):
                    gateway_list.append({'ipei': elem['beacon_gateway_IPEI'],
                                        'proximity': elem['proximity'],
                                        'rssi': elem['rssi']})

            #print("gateway_list:", gateway_list)
            if len(gateway_list) > 0:
                # sort for the best
                m9bs_sorted = sort_m9b_rssi(gateway_list)
                #print("sorted gateway_list:", gateway_list)
                #print("final position for %s: %s" % (btmac, get_m9bposition(m9bs_sorted[0]["ipei"])))
                position = []
                position = get_m9bposition(m9bs_sorted[0]["ipei"]).copy()
                position['btmac'] = btmac
                print("final position for %s: %s" % (btmac, get_m9bposition(m9bs_sorted[0]["ipei"])))

                position_list.append(position)
        return position_list
