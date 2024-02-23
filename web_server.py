import network
import socket
from time import sleep
from picozero import pico_temp_sensor
import machine

sensorPin = machine.ADC(28)
buzzerPin = 13  # You can adjust this pin based on your Pico board
threshold_warning = 5000
threshold_alarm = 10000

ssid = 'TELUS2165'
password = 'Alexisthebest'
def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print('Waiting for connection...')
        sleep(1)
    print(wlan.ifconfig())
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection

def serve(connection):
    # Start a web server
    temperature = 0
    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass

        # Read temperature and gas sensor values
        temperature = pico_temp_sensor.temp
        gas_value = sensorPin.read_u16()

        # Check gas sensor thresholds and play corresponding buzzer
        if gas_value > threshold_alarm:
            play_alarm_buzzer()
        elif gas_value > threshold_warning:
            play_warning_buzzer()

        # Serve HTML page with temperature and gas sensor values
        html = webpage(temperature, gas_value)
        client.send(html)
        client.close()

def print_sensor_readings():
    while True:
        # Read temperature and gas sensor values
        temperature = pico_temp_sensor.temp
        gas_value = sensorPin.read_u16()

        print("Temperature:", temperature)
        print("Gas Sensor Value:", gas_value)
        
        sleep(1)
        if gas_value > threshold_alarm:
            play_alarm_buzzer()
        elif gas_value > threshold_warning:
            play_warning_buzzer()

def webpage(temperature, gas_value):
    # Template HTML
    html = f"""
            <!DOCTYPE html>
            <html>
            <p>Temperature is {temperature}</p>
            <p>Gas Sensor Value is {gas_value}</p>
            </body>
            </html>
            """
    return str(html)

def play_tone(frequency, duration):
    buzzer = machine.PWM(machine.Pin(buzzerPin))
    buzzer.freq(int(frequency))
    buzzer.duty_u16(1000)
    sleep(duration / 1000)  # sleep in seconds
    buzzer.duty_u16(0)
    buzzer.deinit()

def play_warning_buzzer():
    play_tone(500, 500)
    sleep(0.5)
    play_tone(600, 500)
    sleep(0.5)

def play_alarm_buzzer():
    play_tone(700, 100)
    sleep(0.1)
    play_tone(800, 100)
    sleep(0.1)

try:
    ip = connect()
    connection = open_socket(ip)

    # Run a separate thread for continuously printing sensor readings
    import _thread
    _thread.start_new_thread(print_sensor_readings, ())

    # Serve the web page
    serve(connection)

except KeyboardInterrupt:
    machine.reset()