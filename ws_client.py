# ws_client.py
import json
import websocket

class RosbridgeClient:
    def __init__(self, rosbridge_port=9090):
        self.rosbridge_port = rosbridge_port
        self.rosbridge_ip = ""
        self.ws = None

    def connect(self, ip):
        self.rosbridge_ip = ip
        self.ws_url = f"ws://{ip}:{self.rosbridge_port}"
        try:
            self.ws = websocket.create_connection(self.ws_url, timeout=3)
            print(f"Connected to rosbridge via websocket at {self.ws_url}")
            return True
        except Exception as e:
            self.ws = None
            print(f"Failed to connect to rosbridge at {self.ws_url}: {e}")
            return False

    def disconnect(self):
        if self.ws:
            try:
                self.ws.close()
                print("Disconnected from rosbridge.")
            except Exception as e:
                print(f"Error closing websocket: {e}")
        self.ws = None

    def advertise_topic(self, topic, msg_type):
        if not self.ws:
            return
        advertise_msg = {
            "op": "advertise",
            "topic": topic,
            "type": msg_type
        }
        try:
            self.ws.send(json.dumps(advertise_msg))
            # print(f"Advertised topic {topic} with type {msg_type}")
        except Exception as e:
            print(f"Failed to advertise topic {topic}: {e}")

    def publish(self, topic, msg):
        if not self.ws:
            print("Websocket connection not established.")
            return
        publish_msg = {
            "op": "publish",
            "topic": topic,
            "msg": msg
        }
        try:
            self.ws.send(json.dumps(publish_msg))
            # print(f"Published to {topic}")
        except Exception as e:
            print(f"Failed to publish on {topic}: {e}")
