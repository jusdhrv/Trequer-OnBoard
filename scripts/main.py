import serial, time, math, random, requests, psutil
from datetime import datetime, timezone

class DiagnosticsCollector:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/diagnostics"
        self.start_time = time.time()

    def collect_diagnostics(self):
        """Collect system diagnostic information"""
        try:
            # CPU Usage (percentage)
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # CPU Temperature (absolute in Celsius)
            # Note: This might not work on all systems, fallback to simulation if needed
            try:
                cpu_temp = psutil.sensors_temperatures()
                if 'coretemp' in cpu_temp:
                    cpu_temperature = cpu_temp['coretemp'][0].current
                else:
                    # Simulate temperature between 35-85°C based on CPU usage
                    cpu_temperature = 35 + (cpu_usage * 0.5)
            except:
                cpu_temperature = 35 + (cpu_usage * 0.5)
            
            # Memory Usage (percentage)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk Usage (percentage)
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network Usage (absolute in bytes/sec)
            net = psutil.net_io_counters()
            time.sleep(1)  # Wait 1 second to calculate rate
            net_new = psutil.net_io_counters()
            network_usage = (net_new.bytes_sent + net_new.bytes_recv - net.bytes_sent - net.bytes_recv)
            
            # System Uptime (seconds)
            system_uptime = time.time() - psutil.boot_time()
            
            return {
                "cpu_usage": round(cpu_usage, 2),
                "cpu_temperature": round(cpu_temperature, 2),
                "memory_usage": round(memory_usage, 2),
                "disk_usage": round(disk_usage, 2),
                "network_usage": round(network_usage, 2),
                "system_uptime": round(system_uptime, 2),
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        except Exception as e:
            print(f"Error collecting diagnostics: {e}")
            return None

    def send_diagnostics(self):
        """Send diagnostic readings to the API"""
        diagnostics = self.collect_diagnostics()
        if not diagnostics:
            return False
            
        try:
            response = requests.post(self.api_endpoint, json=diagnostics)
            if response.status_code != 200:
                print(f"Error sending diagnostics: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Exception while sending diagnostics: {e}")
            return False

# Data Output Format:
# 0 - ultrasonic distance
# 1 - ir distance
# 2 - light intensity
# 3 - humidity
# 4 - temperature
# 5 - gas

def modulate_value(base, start_time):
    current_time = time.time() - start_time
    periodic = math.sin(2 * math.pi * current_time / (24 * 3600))
    periodic_component = 5 * periodic
    
    # Add random noise
    noise = random.gauss(0, 0.5)
    
    # Combine components
    value = base + periodic_component + noise
    
    return round(value, 2)

def send_reading(values):
        reading = values
        try:
            response = requests.post('http://localhost:3000/api/sensors', json=reading)
            if response.status_code != 200:
                print(f"Error sending data: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Exception while sending data: {e}")
            return False

def readserial(comport, baudrate, start_time):
    ser = serial.Serial(comport, baudrate, timeout=0.1)         # 1/timeout is the frequency at which the port is read
    diagnostics = DiagnosticsCollector()
    last_diagnostics_time = 0

    while True:
        # Send sensor data
        data = ser.readline().decode().strip()
        if data:
            values = {}
            data_out_list = data.split('|')
            values['temperature'] = float(data_out_list[4])
            values['humidity'] = float(data_out_list[3])
            values['methane'] = float(data_out_list[5])
            values['light'] = int(data_out_list[2])
            values['atmosphericPressure'] = modulate_value(1013, start_time)
            print("Sent sensor data: ", values)
            send_reading(values)

        # Send diagnostic data every 60 seconds
        current_time = time.time()
        if current_time - last_diagnostics_time >= 60:
            if diagnostics.send_diagnostics():
                print("Sent diagnostic data")
            last_diagnostics_time = current_time

if __name__ == '__main__':
    start_time = time.time()
    readserial('/dev/ttyACM0', 9600, start_time)