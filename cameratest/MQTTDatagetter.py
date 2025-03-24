import bisect
import time
import csv
import threading
import paho.mqtt.client as mqtt
import set_path
import raspberrypi as RP

class MQTTDatagetter:
    def __init__(self):
        # get mqtt configuration
        self.broker, self.port, self.keep_alive = set_path.get_MQTTconfiguration()

        # define mqtt client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # define topics
        self.set_beamshape_lcos0 = "eos/rpi-lcos-0/lcos/image/set"
        self.set_beamshape_lcos1 = "eos/rpi-lcos-1/lcos/image/set"
        self.set_zernikes_lcos0 = "eos/rpi-lcos-0/lcos/zernike/set"
        self.set_zernikes_lcos1 = "eos/rpi-lcos-1/lcos/zernike/set"
        self.post_beamshape_lcos0 = "eos/rpi-lcos-0/lcos/image"
        self.post_beamshape_lcos1 = "eos/rpi-lcos-1/lcos/image"
        self.post_zernikes_lcos0 = "eos/rpi-lcos-0/lcos/zernike"
        self.post_zernikes_lcos1 = "eos/rpi-lcos-1/lcos/zernike"
        self.get_monitoring_images = "eos/optics/save_monitoring_image"
        self.get_camera_image = "eos/optics/save_current_image"
        self.get_exposure_data = "eos/atlasmetadata"
        self.get_exposure_data_feedback = "eos/atlasmetadata/$data"

        # data_array update every 10 ms, is a list with element format and a length 32
        self.data_array = []
        self.machine_timestamp = 0
        self.no_offset_machine_time = 0
        self.no_offset_machine_remainder = 0
        # Create unique_data list to store unique elements from data_array
        self.unique_data = []

        # Track machine status
        self.machine_running = False
        self.camera_running = False
        self.new_data_count = 0  # Count of new data in the last 153ms
        self.last_check_time = time.time()  # Time of last check

        # For time calibration
        self.pc_machine_offset = None
        self.calibration_active = True  # Used to enable/disable time calibration
        self.time_differences = []  # List to store time differences for calibration

        self.last_machine_running_time = time.time()

        # Open CSV file once and store the file handler
        self.csv_file = open("Machine_data_logging.csv", mode="a", newline='')
        self.csv_writer = csv.writer(self.csv_file)


        # Start calibration reset timer
        #self.start_calibration_reset_timer()


    def on_connect(self, client, userdata, flags, rc):
        print("MQTT Connected")
        #client.subscribe(self.get_exposure_data)
        client.subscribe(self.get_exposure_data_feedback)

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            if topic == self.get_exposure_data_feedback:
                payload = message.payload.decode('utf-8')
                if not payload:
                    return
                buffer_data_array = payload.split("/")

                if buffer_data_array and len(buffer_data_array) > 10:
                    self.data_array = buffer_data_array
                    self.update_unique_data()  # Update unique data with the new data_array
                    self.check_machine_status()  # Check if the machine is running
        except Exception as e:
            print(f"Error processing message: {str(e)}")


    def connect(self):
        # connect to broker
        self.mqtt_client.connect(self.broker, self.port, self.keep_alive)
        self.mqtt_client.loop_start()

    def disconnect(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.csv_file.close()  # Close the CSV file when disconnecting

    # keep publishing request to Broker and receive data
    def beginn_watch_machine_data(self):
        try:
            while True:

                # send data request
                self.sent_data_request()
                time.sleep(0.8)

        finally:
            self.disconnect()

    def sent_data_request(self):
        self.mqtt_client.publish(self.get_exposure_data, "192")

    def update_unique_data(self):
        """
        Update the unique_data list by adding only new elements based on their timestamp.
        unique_data is sorted with the latest timestamps first and keeps only the latest 8 elements.
        """
        for item in self.data_array:
            item_elements = item.split(";")  # Split item into list
            timestamp = int(item_elements[0])  # Extract timestamp

            # Check if the timestamp is not already in unique_data
            if all(int(unique_item[0]) != timestamp for unique_item in self.unique_data):
                # Find the correct position to insert the new item
                pos = bisect.bisect_left([int(x[0]) for x in self.unique_data], timestamp, hi=len(self.unique_data))
                self.unique_data.insert(pos, item_elements)  # Insert new item at the correct position


                # Update machine timestamp
                if not self.machine_timestamp or timestamp > self.machine_timestamp:
                    self.machine_timestamp = timestamp
                    self.no_offset_machine_time = self.machine_timestamp + self.pc_machine_offset
                    self.no_offset_machine_remainder = self.no_offset_machine_time % 17
                    item_elements.append(self.get_no_offset_machine_time()[0])
                    self.log_machine_data(item_elements)         # Log new data


                # Increment new data count
                self.new_data_count += 1

        # Perform time calibration on new data
        if self.calibration_active:
            self.calibrate_time()  # Pass the new data to calibrate_time()

        # Ensure unique_data only contains the latest 80 elements
        if len(self.unique_data) > 192:
            self.unique_data = self.unique_data[:192]  # Keep only the latest 80 elements

    def log_machine_data(self, row):
        # log_current data_array to CSV
        self.csv_writer.writerow(row)
        self.csv_file.flush()

    def check_machine_status(self):
        """
        Check if the machine is running based on new data received in the last 102ms.
        If at least 4 new data points were received, set machine_running to True, else False.
        """
        current_time = time.time()
        if current_time - self.last_check_time >= 1.5:
            # If time passed, check if 4 or more new data points were received
            if self.new_data_count >= 40:
                self.last_machine_running_time = time.time()  # Update the timestamp
                if not self.machine_running:
                    self.machine_running = True             
                    self.on_machine_status_change(self.machine_running)
            else:
                if self.machine_running:
                    self.machine_running = False
                    self.on_machine_status_change(self.machine_running)

            # Reset counters for the next 102ms period
            self.new_data_count = 0
            self.last_check_time = current_time


    def on_machine_status_change(self, machine_running):
        if machine_running:
            # If the machine is running and the camera is off, turn it on
            if not self.camera_running:
                self.camera_turn_on()
                self.camera_running = True

        else:
            # If machine_running has been False for more than 4 second, turn off the camera
            if time.time() - self.last_machine_running_time > 4:
                if self.camera_running:
                    self.camera_turn_off()
                    self.camera_running = False


    def camera_turn_on(self):
        """Simulate turning the camera on."""
        RP.send_number_to_pi(17)
        print("Camera turned ON.")


    def camera_turn_off(self):
        """Simulate turning the camera off."""
        RP.send_number_to_pi(0)
        print("Camera turned OFF.")


    def calibrate_time(self, timestamp):
        """
        Calibrate time by calculating the difference between the current PC time
        and the machine timestamp for the first 25 new data entries.
        """
        pc_time = int(time.time() * 1000)  # Get current PC time in milliseconds

        # Calculate the difference and store it
        time_diff = pc_time - self.machine_timestamp
        self.time_differences.append(time_diff)

        # Stop calibration after 25 new data points
        if len(self.time_differences) >= 25:
            self.pc_machine_offset = min(self.time_differences)  # Use the smallest difference
            self.calibration_active = False  # Stop calibration
            print(f"Calibration complete. Offset: {self.pc_machine_offset} ms")

    def start_calibration_reset_timer(self):
        """
        Start a timer that resets the calibration process every 30 seconds.
        """
        self.reset_calibration()  # Set calibration active immediately
        timer = threading.Timer(300, self.start_calibration_reset_timer)  # Reset every 60 seconds
        timer.start()

    def reset_calibration(self):
        """
        Reset the calibration process by setting calibration_active to True and clearing differences.
        """
        print("Resetting calibration...")
        self.calibration_active = True
        self.time_differences.clear()  # Clear previous differences

    def get_machine_timestamp(self):
        """
        Returns the machine_time with offset.
        """
        return self.machine_timestamp
    
    def get_no_offset_machine_time(self):
        """
        Returns the no_offset_machine_time and its remainder.
        """
        return self.no_offset_machine_time , self.no_offset_machine_remainder

    def get_machine_running(self):
        return self.machine_running
    
    def set_camera_running(self, camera_running : bool):
        self.camera_running = camera_running

    def get_camera_running(self):
        return self.camera_running

mqtt_Datagetter = MQTTDatagetter()





