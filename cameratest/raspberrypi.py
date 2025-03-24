import serial
import set_path
import time

ser = None

def connect_to_pi(port=set_path.get_port_name(), baud_rate=9600, timeout=1):
    global ser
    try:
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        print(f"At {time.time()} :Connected to Pi on {port}")
    except serial.SerialException:
        print("Pi not connected")
        ser = None

def send_number_to_pi(number):
    ser.write(f"{number}\n".encode('utf-8'))
    print(f"At {time.time()} : Sent: {number}")

def close_connection():
    """close connect"""
    global ser
    if ser and ser.is_open:
        ser.close()
        print("Connection closed.")
    ser = None
