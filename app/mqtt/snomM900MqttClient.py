import paho.mqtt.client as mqtt
import json
import time

RFPI = "site_UNKNOWN"
reconnect_interval = 1
    
class snomM900MqttClient(mqtt.Client):
    # site specific RFPI Address:
    def __init__(self, enable=True):
        mqtt.Client.__init__(self)

        self.enable = enable
    
    def on_connect(self, mqttc, obj, flags, rc):
        print("rc: "+str(rc))

    def on_disconnect(self, client, userdata, rc):
        print("disconnecting reason: "+str(rc))
        self.loop_stop()

    def on_message(self, mqttc, obj, msg):
        print('Message:', msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    #def on_publish(self, mqttc, obj, mid):
    #    print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_message_sms(self, mqttc, obj, msg):
        print('SMS:', msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    def on_message_alarm(self, mqttc, obj, msg):
        print('Alarm:', msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    def on_message_cloudservice(self, mqttc, obj, msg):
        print('RTX:', msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def publish_login(self, device_type, login_name, login_address, login, base_location, ip_connection, bt_mac):
        if self.enable:
            print(f'Publish: snomM900/{RFPI}/device/login {device_type}')
        
            # publish a complete device sub-tree topic
            #device_topic = "snomM900/{RFPI}/devices/%s" % login_address
            device_topic = f"snomM900/{RFPI}/device/{login_address}"

            self.publish("%s/name" % device_topic, login_name)
            self.publish("%s/type" % device_topic, device_type)
            self.publish("%s/loggedIn" % device_topic, login)
            self.publish("%s/baseLocation" % device_topic, base_location)
            self.publish("%s/baseConnection" % device_topic, ip_connection)
            self.publish("%s/bt_mac" % device_topic, bt_mac)


    def publish_beacon(self, bt_mac, beacon_type, uuid, d_type, proximity, rssi, name, beacon_gateway):
        if self.enable:
            #print('Publish: snomM900/{RFPI}/beacon %s to test.mosquitto.org 1883' % bt_mac)
            print(f'Publish: snomM900/{RFPI}/beacons/{bt_mac}')

            device_topic = f"snomM900/{RFPI}/beacons/{bt_mac}"
            
            if beacon_type != "":
                # publish a complete device sub-tree topic
                self.publish("%s/bt_mac" % device_topic, bt_mac)
                self.publish("%s/beaconType" % device_topic, beacon_type)
                self.publish("%s/uuid" % device_topic, uuid)
                self.publish("%s/dType" % device_topic, d_type)
                self.publish("%s/rssi" % device_topic, rssi)
                self.publish("%s/beaconGateway" % device_topic, beacon_gateway)

            # state moving holding_still update
            self.publish("%s/nameState" % device_topic, name)
            self.publish("%s/proximity" % device_topic, proximity)

    def connect_and_subscribe(self, server='127.0.0.1', port=1883):
        if self.enable:
            self.connect(server, port, 60)
            # wait to connect
            time.sleep(2.0)
            self.loop_start()

            self.subscribe([(f"snomM900/{RFPI}/sms",1), 
                            (f"snomM900/{RFPI}/alarm",1)
                           ])
            self.subscribe("site/+/heartbeat_ind", 0)
            self.message_callback_add(f"snomM900/{RFPI}/sms", self.on_message_sms)
            self.message_callback_add(f"snomM900/{RFPI}/alarm", self.on_message_alarm)
            self.message_callback_add("/+", self.on_message_cloudservice)
            self.message_callback_add("site/+/heartbeat_ind", self.on_message_cloudservice)

        return 0
    # not used in async mode
    def run(self):
        if self.enable:
            rc = 0
            rc = self.loop()
            return rc
        else:
            print('MQTT disabled!')
            return 0


if __name__ == "__main__":

    mqttc = snomM900MqttClient()
    rc = mqttc.connect_and_subscribe()

    rc = 0
    while rc == 0:
        mqttc.publish_login("M85 %s" % time.time(), "myName", "888", "1", "myBaseLocation", "192.168.0.0", "000413xxxxx")
        mqttc.publish_beacon("000413666666", "BTLETAGY", "001122334455", "d_type", "0", "-60", "000413444444", "beacon_gateway")

        rc = mqttc.run()
        time.sleep(2)
    print("rc: "+str(rc))
