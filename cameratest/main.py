import monowindow
from image_timestamp import reading_imagetime
from feedback_adjust import adjuster
import raspberrypi as RP
from MQTTDatagetter import mqtt_Datagetter

# Start reading image time stamp
reading_imagetime.start_read_image_time()

# Connect to Pi
RP.connect_to_pi()

# Connect to MQTT
mqtt_Datagetter.connect()
mqtt_Datagetter.beginn_watch_machine_data()
#mqtt_Datagetter.reset_calibration()


#generate a window
window = monowindow.MonoWindow(reading_imagetime, adjuster, mqtt_Datagetter)
window.run()
