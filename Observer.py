import time

import obsws_python as obs

HOST = "localhost"
PORT_A = 4455
PORT_B = 4466

class Observer:
    def __init__(self, host, port, sheet_name):
        self.host = host
        self.port = port
        print(host + " " + str(port))
        self.sheet_name = sheet_name
        self._client = obs.EventClient(host=host, port=port)
        self._client.callback.register(
            [
                self.on_exit_started,
                self.on_input_mute_state_changed
            ]
        )
        print(f"Registered events: {self._client.callback.get()}")
        self.running = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._client.disconnect()

    def on_input_mute_state_changed(self, _):
        print(self.sheet_name + " has its mic mute status changed")


    def on_exit_started(self, _):
        """OBS has begun the shutdown process."""
        print("OBS closing!")
        self.running = False


""" if __name__ == "__main__":
    with Observer(HOST, PORT_A, "Sheet A") as observer:
        while observer.running:
            time.sleep(0.1)
"""
