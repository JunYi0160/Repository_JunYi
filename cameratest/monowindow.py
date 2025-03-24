import tkinter as tk
import raspberrypi as RP
from imagetxt_to_csv import generate_csv


class MonoWindow:
    def __init__(self, reading_imagetime, adjuster, mqtt_Datagetter):
        self.reading_imagetime = reading_imagetime
        self.adjuster = adjuster
        self.mqtt_Datagetter = mqtt_Datagetter

        self.root = tk.Tk()
        self.root.title("Monitor")
        self.root.geometry("600x600")  # windon size
        # Showing labels for Timestamp
        self.timestamp_label = tk.Label(self.root, text="image Time: ", font=("Arial", 11))
        self.timestamp_label.grid(row=0, column=1, columnspan=3, padx=10, pady=10)

        # Showing labels for remainder
        self.remainder_label = tk.Label(self.root, text="image tiem Remainder for 17:    ", font=("Arial", 11))
        self.remainder_label.grid(row=1, column=1, columnspan=3, padx=10, pady=10)

        # Labels for MQTTDatagetter data
        self.machine_timestamp_label = tk.Label(self.root, text="Machine Time: ", font=("Arial", 10))
        self.machine_timestamp_label.grid(row=6, column=1, columnspan=3, padx=10, pady=10)

        self.no_offset_machine_time_label = tk.Label(self.root, text="No Offset Machine Time: ", font=("Arial", 11))
        self.no_offset_machine_time_label.grid(row=5, column=1, columnspan=3, padx=10, pady=10)

        self.no_offset_machine_remainder_label = tk.Label(self.root, text="No Offset Machine Remainder: ", font=("Arial", 11))
        self.no_offset_machine_remainder_label.grid(row=4, column=1, columnspan=3, padx=10, pady=10)        

        # Machine Running State Label
        self.machine_running_label = tk.Label(self.root, text="Machine Running State: ", font=("Arial", 11))
        self.machine_running_label.grid(row=7, column=1, padx=10, pady=10)

        # Create the circular indicator light (initially red, assuming machine is not running)
        self.machine_running_light = tk.Canvas(self.root, width=30, height=30, bg="white", highlightthickness=0)
        self.machine_running_light.grid(row=7, column=2, padx=10, pady=10)
        self.machine_light_circle = self.machine_running_light.create_oval(5, 5, 25, 25, fill="red")


        # Camera Running State Label and Indicator
        self.camera_running_label = tk.Label(self.root, text="Camera Running State: ", font=("Arial", 11))
        self.camera_running_label.grid(row=8, column=1, padx=10, pady=10)

        self.camera_running_light = tk.Canvas(self.root, width=30, height=30, bg="white", highlightthickness=0)
        self.camera_running_light.grid(row=8, column=2, padx=10, pady=10)
        self.camera_light_circle = self.camera_running_light.create_oval(5, 5, 25, 25, fill="red")

        # Create Button
        self._create_big_button("17", 0, 0, "green")
        self._create_big_button("0", 0, 4, "red")

        # Create generate csv file butten
        self._create_csv_button()

        # Create the input field and send button
        self._create_input_field()

        # Create the input field and button for setting target value
        self._create_target_input()

        self._alignment_button()

        # Add Start and Stop Adjustment buttons
        self._create_control_buttons()

        self._create_reset_calibration_button()

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._update_timestamp()


    def _create_reset_calibration_button(self):
        # Create a 'Reset Calibration' button
        reset_button = tk.Button(self.root, text="Reset Calibration", font=("Arial", 10), width=15, height=2,
                                 command=self.mqtt_Datagetter.reset_calibration)
        reset_button.grid(row=3, column=3, padx=10, pady=10)  # Adjust row and column as needed for layout



    def _create_input_field(self):
        # Create an Entry widget (input field)
        self.number_entry = tk.Entry(self.root, font=("Arial", 14), width=10)
        self.number_entry.grid(row=2, column=0, padx=10, pady=10)

        # Create a 'Send to Pi' button
        send_button = tk.Button(self.root, text="Send to Pi", font=("Arial", 10), width=10, height=2,
                                command=self._send_inputnumber_to_pi)
        send_button.grid(row=2, column=1, padx=10, pady=10)

    def _send_inputnumber_to_pi(self):
        # Get the number from the input field
        number = self.number_entry.get()
        try:
            # Convert the number to integer
            number = int(number)
            RP.send_number_to_pi(number)
            print(f"Sent {number} to Pi")
        except ValueError:
            print("Invalid input! Please enter a valid number.")



    def _create_target_input(self):
        # Create an Entry widget for setting target
        self.target_entry = tk.Entry(self.root, font=("Arial", 14), width=10)
        self.target_entry.grid(row=3, column=0, padx=10, pady=10)

        # Create a 'Set Target' button
        set_target_button = tk.Button(self.root, text="Set Target", font=("Arial", 10), width=10, height=2,
                                      command=self._set_target_value)
        set_target_button.grid(row=3, column=1, padx=10, pady=10)


    def _alignment_button(self):

        # Create a 'Set Target' button
        set_alignment_button = tk.Button(self.root, text="Alignment", font=("Arial", 10), width=10, height=2,
                                      command=self.adjuster.updatetarget_to_machine)
        set_alignment_button.grid(row=3, column=2, padx=10, pady=10)

    def _set_target_value(self):
        # Get the target value from the input field
        target = self.target_entry.get()
        try:
            # Convert the target to integer
            target = int(target)
            self.adjuster.set_target(target)
            print(f"Target set to {target}")
        except ValueError:
            print("Invalid input! Please enter a valid target number.")


    def _create_big_button(self, text, row, col, color):
        button = tk.Button(self.root, text=str(text), font=("Arial", 10), width=8, height=2, 
                           bg=color, command=lambda: RP.send_number_to_pi(text))
        button.grid(row=row, column=col, padx=10, pady=10)

    def _create_small_button(self, text, row, col):
        button = tk.Button(self.root, text=str(text), font=("Arial", 14), width=5, height=2, 
                           command=lambda: RP.send_number_to_pi(text))
        button.grid(row=row, column=col, padx=5, pady=5)

    def _create_csv_button(self):
        # Create a 'Generate CSV' button
        button = tk.Button(self.root, text="Generate CSV", font=("Arial", 8), width=12, height=2,
                           command=lambda: generate_csv())  # Call generate_csv function when clicked
        button.grid(row=2, column=4, padx=10, pady=10)  # Place it in the bottom right corner

    def _create_control_buttons(self):
        # Create "Start Adjustment" button
        start_button = tk.Button(self.root, text="Start Adjustment", font=("Arial", 10), width=12, height=2,
                                 command=lambda: self.adjuster.start_adjustment())
        start_button.grid(row=2, column=2, padx=10, pady=10)  # Adjust row and column as needed

        # Create "Stop Adjustment" button
        stop_button = tk.Button(self.root, text="Stop Adjustment", font=("Arial", 10), width=12, height=2,
                                command=lambda: self.adjuster.stop_adjustment())
        stop_button.grid(row=2, column=3, padx=10, pady=10)  # Adjust row and column as needed

    def _on_closing(self):
        self.root.destroy()
        RP.close_connection()


    def _update_timestamp(self):
        new_image_timestamp = self.reading_imagetime.get_newimage_time()[0]
        if new_image_timestamp:
            # update stamps
            self.timestamp_label.config(text=f"Timestamp: {new_image_timestamp}")
            
            # calcultate reminder for 34
            remainder = self.reading_imagetime.get_newimage_time()[1]
            self.remainder_label.config(text=f"Remainder for 17:     {remainder}")
        
        # refresh
        self._update_mqtt_data()
        self.root.after(30, self._update_timestamp)

    def _update_mqtt_data(self):
        # Update the MQTT data from mqtt_Datagetter
        machine_timestamp = self.mqtt_Datagetter.get_machine_timestamp()
        no_offset_machine_time, no_offset_machine_remainder = self.mqtt_Datagetter.get_no_offset_machine_time()

        # Update labels with MQTT data
        self.machine_timestamp_label.config(text=f"Machine Timestamp: {machine_timestamp}")
        self.no_offset_machine_time_label.config(text=f"No Offset Machine Time: {no_offset_machine_time}")
        self.no_offset_machine_remainder_label.config(text=f"No Offset Machine Remainder: {no_offset_machine_remainder}")


        camera_running = self.mqtt_Datagetter.get_camera_running()
        machine_running = self.mqtt_Datagetter.get_machine_running()

        # Update the color of the circular light based on the machine state
        if machine_running:
            self.machine_running_light.itemconfig(self.machine_light_circle, fill="green")
        else:
            self.machine_running_light.itemconfig(self.machine_light_circle, fill="red")
        camera_running = self.mqtt_Datagetter.get_camera_running()
        machine_running = self.mqtt_Datagetter.get_machine_running()

        # Update the color of the circular light based on the machine state
        if machine_running:
            self.machine_running_light.itemconfig(self.machine_light_circle, fill="green")
        else:
            self.machine_running_light.itemconfig(self.machine_light_circle, fill="red")

        # Update the color of the circular light based on the camera state
        if camera_running:
            self.camera_running_light.itemconfig(self.camera_light_circle, fill="green")
        else:
            self.camera_running_light.itemconfig(self.camera_light_circle, fill="red")

    def run(self):
        self.root.mainloop()