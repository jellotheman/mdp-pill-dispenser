"""Optional MQTT transport for the reference API, for synthetic demonstrations.

The REST API remains the source of truth. MQTT topics provide delivery, not
authorization; use an authenticated private broker for anything beyond demos.
"""
import argparse
import json
import logging
import os
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import paho.mqtt.client as mqtt

LOG = logging.getLogger("mdp.mqtt")
IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
MAX_MESSAGE = 6143


class Api:
    def __init__(self, url, device, token):
        self.base = f"{url.rstrip('/')}/api/v1/devices/{device}"
        self.token = token

    def request(self, route, data=None):
        body = None if data is None else json.dumps(data).encode()
        request = Request(self.base + route, data=body, headers={
            "Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        with urlopen(request, timeout=3) as response:
            return json.load(response)


class Bridge:
    def __init__(self, api, client, namespace, device):
        if not IDENTIFIER.fullmatch(namespace) or not IDENTIFIER.fullmatch(device):
            raise ValueError("Namespace and device ID must each contain 1-32 letters, digits, _ or -")
        self.api, self.client = api, client
        self.prefix = f"mdp-demo/{namespace}/{device}"
        self.needs_config = threading.Event()
        self.last_config = None

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            LOG.error("Broker connection rejected: %s", reason_code)
            return
        client.subscribe([(self.prefix + "/config-ack", 1), (self.prefix + "/events", 1)])
        self.needs_config.set()
        LOG.info("Connected to broker; subscribed for device acknowledgements and events")

    def on_message(self, client, userdata, message):
        if message.retain or len(message.payload) > MAX_MESSAGE:
            LOG.warning("Ignoring retained or oversized device message")
            return
        try:
            data = json.loads(message.payload)
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object")
            if message.topic == self.prefix + "/config-ack":
                self.api.request("/config-acks", data)
            elif message.topic == self.prefix + "/events":
                if data.get("simulated") is not True:
                    raise ValueError("MQTT demo accepts simulated events only")
                result = self.api.request("/events", data)
                if result.get("accepted") is True and result.get("event_id") == data.get("event_id"):
                    client.publish(self.prefix + "/event-ack", json.dumps(result), qos=1, retain=False)
        except (ValueError, UnicodeError, HTTPError, URLError, OSError) as exc:
            # No event acknowledgement on failure: firmware keeps its durable outbox.
            LOG.warning("Device message rejected or service unavailable: %s", exc)

    def sync_config(self):
        if not self.client.is_connected():
            return
        try:
            config = json.dumps(self.api.request("/config"), separators=(",", ":"))
            if self.needs_config.is_set() or config != self.last_config:
                result = self.client.publish(self.prefix + "/config", config, qos=1, retain=True)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    raise OSError(f"MQTT publish failed: {result.rc}")
                self.last_config = config
                self.needs_config.clear()
                LOG.info("Published desired device configuration")
        except (ValueError, HTTPError, URLError, OSError) as exc:
            LOG.warning("Configuration sync unavailable: %s", exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default=os.getenv("MDP_BACKEND_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--device", default=os.getenv("MDP_DEVICE_ID", "mdp-demo"))
    parser.add_argument("--namespace", default=os.getenv("MDP_MQTT_NAMESPACE"), required=not os.getenv("MDP_MQTT_NAMESPACE"))
    parser.add_argument("--broker", default=os.getenv("MDP_MQTT_HOST", "broker.hivemq.com"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MDP_MQTT_PORT", "1883")))
    parser.add_argument("--tls", action="store_true", help="Verify TLS using the system trust store")
    args = parser.parse_args()
    token = os.getenv("MDP_DEVICE_TOKEN")
    if not token:
        parser.error("Set MDP_DEVICE_TOKEN to the reference API token")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    username = os.getenv("MDP_MQTT_USERNAME")
    if username:
        client.username_pw_set(username, os.getenv("MDP_MQTT_PASSWORD"))
    if args.tls:
        client.tls_set()
    bridge = Bridge(Api(args.api, args.device, token), client, args.namespace, args.device)
    client.on_connect, client.on_message = bridge.on_connect, bridge.on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    LOG.warning("Demo transport: public broker messages are untrusted; use synthetic data only")
    client.connect_async(args.broker, args.port, 30)
    client.loop_start()
    try:
        while True:
            bridge.sync_config()
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
