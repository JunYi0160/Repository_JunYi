import os
import threading
import time
import set_path
from MQTTDatagetter import mqtt_Datagetter

class Image_Timestamp_Manager:
    def __init__(self, mqtt_Datagetter):
        self.mqtt_Datagetter = mqtt_Datagetter
        self.image_timestamp = None
        self.image_timestamp_remainder = None
        self.last_timestamp_str = "unixtime"
        self.meta_file_path = set_path.get_meta_file_path()
        self.thread = None

    def _extract_timestamp_from_txt(self):
        latest_line = None
        try:
            with open(self.meta_file_path, 'rb') as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
                latest_line = f.readline().decode()
        except:
            return None
        if latest_line:
            parts = latest_line.split('|')
            if len(parts) >= 4:
                return parts[2].strip()
        return None

    def _update_image_timestamp(self):
        while True:
            try:
                image_timestamp_str = self._extract_timestamp_from_txt()
                if image_timestamp_str and image_timestamp_str != self.last_timestamp_str:
                    self.last_timestamp_str = image_timestamp_str
                    self.image_timestamp = int(image_timestamp_str)
                    self.image_timestamp_remainder = self.image_timestamp % 17
                    if self.on_timestamp_update:
                        self.on_timestamp_update()

                    if not self.mqtt_Datagetter.camera_running:
                        self.mqtt_Datagetter.camera_running = True
                if self.mqtt_Datagetter.camera_running and int(time.time()*1000) - self.image_timestamp >  300:
                    self.mqtt_Datagetter.camera_running = False
            except:
                pass
            time.sleep(0.01)

    def set_on_timestamp_update_callback(self, callback):
        """
        Allows the user to set a custom callback function
        """
        self.on_timestamp_update = callback

    def start_read_image_time(self):
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._update_image_timestamp)
            self.thread.start()
            time.sleep(0.1)

    def get_newimage_time(self):
        return self.image_timestamp, self.image_timestamp_remainder

reading_imagetime = Image_Timestamp_Manager(mqtt_Datagetter)