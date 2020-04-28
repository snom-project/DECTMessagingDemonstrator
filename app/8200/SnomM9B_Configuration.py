#!/usr/bin/python3

import rtx8200_pb2
import wrappers_pb2
import sys
from lxml import etree as ET
import lxml.builder


from basic_utils.core import (
    clear,
    getattrs,
    map_getattr,
    rgetattr,
    rsetattr,
    slurp,
    to_string
)

import pandas as pd

def read_xls_into_data(file):
    print('Read xls file %s' % file)

    account_data_from_excel = pd.read_excel(file)

    return account_data_from_excel

def set_ConfigSetting_from_excel_data(data, column, line):
    val=None
    try:
        # check if value is ENUM type
        val = getattr(rtx8200_pb2, data[data.columns[column]][line])
        print(data.columns[column], 'with ENUM:', data[data.columns[column]][line])
    except (AttributeError, TypeError, ValueError, ) as e:
        #print(data.columns[column], 'is not an ENUM', e)
        # get the type from line 0 of excel. This must be the correct data-type
        try:
            # in case c.name name does not exist we cannot get a type, nTypeError
            protobuf_type = type(rgetattr(c, data.columns[column][2:]))
            print('protobuf_type=', protobuf_type)
            # check if we get a string  which needs to be a bytes sequence
            val = data[data.columns[column]][line]
            if type(val) is str and protobuf_type is bytes:
                print('A string instead of a byte sequence, try to decode to bytes', val)
                # convert string from utf-8 to ascii
                val = val.encode('ascii', 'replace')
            val = protobuf_type(val)

        except (TypeError, AttributeError) as e:
            print('Error - unknown c.name name.::', e)
            
    # take the next line of config data of setting with column name
    # check for type incompatibilites and wrong column key name in excel(data)
    try:
        print(data.columns[column], 'with value:', val)
        rsetattr(c, data.columns[column][2:], val)
    except (TypeError, ValueError) as e:
        print('Error (TypeError, ValueError)::', e)
    except (AttributeError, KeyError) as e:
        print('Error (AttributeError, KeyError)::', e)
    print('---------------------------------------------------------')


alarmServerAddress = beaconServerAddress = sys.argv[1]


c = rtx8200_pb2.ConfigSettings()

#c.rxModeSettings.statusUpdateInterval.value        = 10

#c.rfSettings.antennaArraySelection          = rtx8200_pb2.ACROSS
#c.rfSettings.beaconOperationMode            = rtx8200_pb2.RXMODE
#c.rfSettings.txAttenuationSelection         = rtx8200_pb2.TXATTZERO
#c.rfSettings.rxAttenuationSelection         = rtx8200_pb2.RXATTZERO
#
#c.txModeSettings.txInterval.value           = 10
#
#ibeacon = c.txModeSettings.beaconId.add()
#ibeacon.iBeaconSettings.uuid                = bytes([0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41,0x41])
#ibeacon.iBeaconSettings.major               = bytes([0x11, 0x11])
#ibeacon.iBeaconSettings.minor               = bytes([0x22, 0x22])
#
#altbeacon = c.txModeSettings.beaconId.add()
#altbeacon.altbeaconSettings.id              = bytes([0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42,0x42])
#altbeacon.altbeaconSettings.mfg             = 0x33
#
#c.rxModeSettings.proximityAlgorithm         = rtx8200_pb2.ALGORITHM4
#c.rxModeSettings.proximityMode              = rtx8200_pb2.NOTIFY_WHEN_EITHER
#c.rxModeSettings.sensitivitySetting         = rtx8200_pb2.SENSITIVITY_MAXIMUM
#
#c.rxModeSettings.rxModeFilter.filterBeaconType   = rtx8200_pb2.IBEACON
#c.rxModeSettings.rxModeFilter.filterLength.value = 20
#c.rxModeSettings.rxModeFilter.filterId           = bytes([0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60,0x60])

#c.dectSettings.dectLockCheckInterval.value  = 666





# generate the XML provisioning file
#<configs>
#   <devices>
#       <device type="rtx8200" ipei="0328D3C909" revision="1.0">
#           <data encoding="base64">CgQIARABEjYKFFJUWDgyMDAgSGVsbG8gV29ybGQhEgoxMjM0NTY3ODkwGgoxMTIyMzM0NDU1IgAqAggBMAEaCQoCCBoSAwjgEiIICAQYASABKAIqPgocChoKEEFBQUFBQUFBQUFBQUFBQUESAhERGgIiIgoaEhgKFEJCQkJCQkJCQkJCQkJCQkJCQkJCEDMSAghkMiQIAxABGhwIAhICCBQaFGBgYGBgYGBgYGBgYGBgYGBgYGBgMAQ=b'CgQIARABEjYKFFJUWDgyMDAgSGVsbG8gV29ybGQhEgoxMjM0NTY3ODkwGgoxMTIyMzM0NDU1IgAqAggBMAEaCQoCCBoSAwjgEiIICAQYASABKAIqPgocChoKEEFBQUFBQUFBQUFBQUFBQUESAhERGgIiIgoaEhgKFEJCQkJCQkJCQkJCQkJCQkJCQkJCEDMSAghkMiQIAxABGhwIAhICCBQaFGBgYGBgYGBgYGBgYGBgYGBgYGBgMAQ='
#           </data>
#       </device>
#   </devices>
#</configs>


import base64

E = lxml.builder.ElementMaker()
CONFIGS = E.configs
DEVICES = E.devices
DEVICE  = E.device
DATA  = E.data

config_doc = CONFIGS(
                    DEVICES()
                    )
                    
                    
data = read_xls_into_data('./SnomM9BConfigurationSet.xlsx')
#print(data)
# add <device> from configSettings  under <devices>
devices = config_doc.find("devices")

numGateways = data.shape[0]
numSettings = data.shape[1]
print('Add', numSettings, 'settings for', numGateways)
for i in range(0,numGateways,1):
    for column in range(0,numSettings,1):
        # example::
        # set_ConfigSetting_from_excel_data(data, 8, i)

        # example with ENUM
        # c.generalSettings.alarmSettings             = rtx8200_pb2.POWER_BATTERY_LOW
        # c.generalSettings.alarmSettings             = getattr(rtx8200_pb2, str(data['c.generalSettings.alarmSettings'][i]))
        # set_ConfigSetting_from_excel_data(data, 9, i)
        set_ConfigSetting_from_excel_data(data, column, i)

    # use config to generate byte stream
    data_stream = base64.b64encode(c.SerializeToString())
    data_stream = data_stream.decode('ascii')
    devices.insert(1,DEVICE(DATA(data_stream), type="SnomM9B", ipei=str(data['c.IPEI'][i]), revision="1.0"))

#  for i in range(1,numextensions+1,1):
#       data['xsi_username%s' % i] = account_data_from_excel['user'][i-1]
#       data['xsi_password%s' % i] = account_data_from_excel['password'][i-1]
#       data['device_id%s' % i] = account_data_from_excel['device_id'][i-1]
#       data['ipei%s' % i] = account_data_from_excel['ipei'][i-1]
#

                
xml_with_header = (bytes('<?xml version="1.0" encoding="UTF-8"?>\n', encoding='utf-8') + ET.tostring(config_doc))


#sys.stdout.buffer.write(c.SerializeToString())
#sys.stdout.buffer.write(encoded)
print(ET.tostring(config_doc, pretty_print=True, encoding="unicode"))
