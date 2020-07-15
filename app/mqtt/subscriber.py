import paho.mqtt.client as mqtt
import time

class snomM900MqttClient(mqtt.Client):

    def on_connect(self, mqttc, obj, flags, rc):
        print("rc: "+str(rc))

    def on_message(self, mqttc, obj, msg):
        print('Message:', msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    def on_publish(self, mqttc, obj, mid):
        print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def connect_and_subscribe(self):
        self.connect("test.mosquitto.org", 1883, 60)
        #self.subscribe("$SYS/#", 0)
        self.subscribe("snomM900/13466A8A/devices/#")
        self.subscribe("snomM900/13466A8A/beacons/#")

    def run(self):
       
        rc = 0
        rc = self.loop()
        return rc


if __name__ == "__main__":

    mqttc = snomM900MqttClient()
    rc = mqttc.connect_and_subscribe()

    rc = 0
    while rc == 0:
        rc = mqttc.run()
        time.sleep(2)
    print("rc: "+str(rc))
