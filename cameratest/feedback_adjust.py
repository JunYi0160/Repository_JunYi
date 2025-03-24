import time
from image_timestamp import reading_imagetime
import raspberrypi as RP
from threading import Thread
from MQTTDatagetter import mqtt_Datagetter

class ImageAdjuster:
    def __init__(self, reanding_imagetime, mqtt_Datagetter, target=8, k_min=0.03, k_max=0.3, error_threshold=4):
        # Initialize the parameters of the adjuster
        self.reading_imagetime = reanding_imagetime
        self.mqtt_Datagetter = mqtt_Datagetter
        self.target = target
        self.k_min = k_min
        self.k_max = k_max
        self.error_threshold = error_threshold
        self.adjusting = False
        self.recent_errors = []  # To store recent errors
        self.adjustment_thread = None  # To store the adjustment thread

        self.reading_imagetime.set_on_timestamp_update_callback(self.updatetarget_to_machine)

    def _adjustment_loop(self):
        """
        Internal method: A loop that continuously adjusts the output of the Raspberry Pi 
        based on the target and current value.
        """
        while self.adjusting:
            current_value = self.reading_imagetime.get_newimage_time()[1]
            if current_value is not None:
                error = self.target - current_value
                if error <= -8:
                    error = error + 17
                if error >= 8 :
                    error = error -17

                # Record the recent errors, keeping only the last 2
                if len(self.recent_errors) >= 2:
                    self.recent_errors.pop(0)
                self.recent_errors.append(error)

                # Calculate the average of recent errors
                average_error = sum(self.recent_errors) / len(self.recent_errors)

                # Adjust the coefficient k based on the error
                k = self.k_min + (self.k_max - self.k_min) * (abs(average_error) / self.error_threshold)
                k = max(self.k_min, min(k, self.k_max))

                # Calculate the adjustment value
                adjustment = average_error * k
                if adjustment < 0:
                    adjustment += 17

                # Send the adjustment value to Raspberry Pi
                if 0.01 < adjustment < 15.9:
                    RP.send_number_to_pi(adjustment)

            time.sleep(0.04)

    def start_adjustment(self):
        """
        Start the adjustment. If a new target is provided, update the target.
        """
        if not self.adjusting:
            self.adjusting = True
            adjust_target = self.mqtt_Datagetter.get_no_offset_machine_time()[1]
            if adjust_target is not None:
                self.target = adjust_target
            self.recent_errors = []  # Clear the recent errors record

            # Start the adjustment loop thread
            self.adjustment_thread = Thread(target=self._adjustment_loop)
            self.adjustment_thread.start()
            print(f"Adjustment started with target={self.target}")

    def stop_adjustment(self):
        """
        Stop the adjustment loop.
        """
        if self.adjusting:
            self.adjusting = False
            if self.adjustment_thread:
                self.adjustment_thread.join()  # Wait for the thread to finish
            print("Adjustment stopped")

    def set_target(self, target):
        """
        Set a new adjustment target.
        """
        self.target = target
        print(f"Target updated to {self.target}")

    def is_adjusting(self):
        """
        Check if the adjustment is currently running.
        """
        return self.adjusting
    
    def updatetarget_to_machine(self):
        adjust_target = self.mqtt_Datagetter.get_no_offset_machine_time()[1]
        if adjust_target:
            self.target =  adjust_target


adjuster = ImageAdjuster(reading_imagetime, mqtt_Datagetter)  # Create an instance of ImageAdjuster with a default target of 10
