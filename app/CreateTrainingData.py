
from DB.DECTMessagingDb import DECTMessagingDb

import pandas as pd

import json
import time
import datetime

import schedule
import logging


def get_best_m9b(selected):
    # get the best visible rssi m9b
    # sort in place
    selected.sort(key=lambda item: item.get("rssi"))
    #print('sorted', selected)
    return selected[0]


# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def store_locations():
    if msgDb:
        
        result = msgDb.read_m9b_device_status_db()
        #print(result)
        ''' 
        [  
        List of:
            {'account': '000413B50038', 'bt_mac': '000413B50038', 
            'rssi': '-53', 'uuid': 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF90FF', 
            'beacon_type': 'a', 'proximity': '3', 
            'beacon_gateway_IPEI': '0328D3C918', 'beacon_gateway_name': 'Schreibtisch', 
            'time_stamp': '2020-10-29 10:44:22.489801', 'server_time_stamp': '2020-10-29 09:44:22', 'timeout': 96945} , 
        ... ]
        '''
        _btmacs = [ sub['bt_mac'] for sub in result ] 
        #print(_btmacs)

     

        # re-use time-stamp for all m9bs to mark them as same time
        time_stamp = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")
        #print(time_stamp)
        for elem in result:
            #if elem['bt_mac'] == '000413B40034':
            if elem['bt_mac'] == args.bt_mac:
                # attach first element 
                if len(all_results) == 0:
                    all_results.append(elem)

                elem['time_stamp'] = time_stamp
            
                is_in = False
                for res in all_results:

                    if res['bt_mac'] == elem['bt_mac'] and res['rssi'] == elem['rssi'] and res['proximity'] == elem['proximity'] and res['beacon_gateway_IPEI'] == elem['beacon_gateway_IPEI']:
                        is_in = True
                        
                if not is_in:
                    # add result list elem by elem to full result list
                    all_results.append(elem)
last_len = 0 
def move_check():
    global last_len
    global num_test_samples
    current_len = len(all_results)
    if current_len > last_len:
        last_len = current_len
    else:
        #print('Move, we only got {} unique BTLE  beacon records'.format(current_len))
        print(f'Move, we only got {current_len} out of {num_test_samples} unique BTLE beacon records')

       
all_results = []

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description='CreateTrainingData')
    parser.add_argument('num_samples', metavar='num_samples', type=int, default=10,
                   help='number of training data samples.')
    parser.add_argument('-out', 
                   default="./data.csv",
                   help='name of created training data file including path')
    parser.add_argument('-room_name', 
                   default="myroom",
                   help='room name')
    parser.add_argument('-bt_mac', 
                   default="000413B40038",
                   help='scanning device BTLE mac. e.g. 000413B40034')

    args = parser.parse_args()
    print(args)

    # prepare logger
    logger = logging.getLogger('CreateTrainingData')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # get access to the DB
    # DB reuse and type
    odbc=False
    initdb=False
    msgDb = DECTMessagingDb(odbc=odbc, initdb=initdb)

    # fire data with scheduler
    logger.debug("main: schedule.every(2).seconds.do(store_locations)")
    schedule.every(2).seconds.do(store_locations)
    schedule.every(10).seconds.do(move_check)

    num_test_samples = 100
    num_test_samples = args.num_samples

    #for i in range(0, num_test_samples+1):
    while len(all_results) < num_test_samples:
        printProgressBar (len(all_results), num_test_samples, prefix = 'Samples:', length = 50, fill = '█', printEnd = "\r")

        schedule.run_pending()
        time.sleep(2)
    print(all_results)

    data = pd.DataFrame(all_results)
    # add room column at the beginning
    #data[args.room_name]=1
    data.insert(0, args.room_name, '1')

    print(data)
    filename_and_path = args.out
    
    data.to_csv(filename_and_path, index=False)