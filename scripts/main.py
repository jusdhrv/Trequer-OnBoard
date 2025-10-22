import serial, time, math, random, requests, psutil, logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    filename='diagnostics.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DiagnosticsCollector:
    def __init__(self, base_url="https://trequer.vercel.app"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/diagnostics"
        self.start_time = time.time()

    def collect_diagnostics(self):
        """Collect system diagnostic information"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            try:
                cpu_temp = psutil.sensors_temperatures()
                if 'coretemp' in cpu_temp:
                    cpu_temperature = cpu_temp['coretemp'][0].current
                else:
                    cpu_temperature = 35 + (cpu_usage * 0.5)
            except:
                cpu_temperature = 35 + (cpu_usage * 0.5)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            net = psutil.net_io_counters()
            time.sleep(1)
            net_new = psutil.net_io_counters()
            network_usage = (net_new.bytes_sent + net_new.bytes_recv - net.bytes_sent - net.bytes_recv)
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
            error_msg = f"Error collecting diagnostics: {e}"
            print(error_msg)
            logging.error(error_msg)
            return None

    def send_diagnostics(self):
        diagnostics = self.collect_diagnostics()
        if not diagnostics:
            logging.error("No diagnostics data to send")
            return False
        required_fields = {
            'cpu_usage': float, 'cpu_temperature': float, 'memory_usage': float,
            'disk_usage': float, 'network_usage': float, 'system_uptime': float,
            'timestamp': str
        }
        if not all(k in diagnostics and isinstance(diagnostics[k], v) for k, v in required_fields.items()):
            error_msg = f"Invalid diagnostics data format: {diagnostics}"
            print(error_msg)
            logging.error(error_msg)
            return False
        retries = 3
        for attempt in range(retries):
            try:
                headers = {'Authorization': 'Bearer YOUR_API_KEY'}  # Replace with actual API key if required
                response = requests.post(self.api_endpoint, json=[diagnostics], headers=headers, timeout=5)
                if response.status_code == 200:
                    logging.info("Successfully sent diagnostics data")
                    return True
                else:
                    error_msg = f"Error sending diagnostics: {response.status_code} - {response.text}"
                    print(error_msg)
                    logging.error(error_msg)
            except requests.exceptions.Timeout:
                error_msg = f"Request timed out while sending diagnostics (attempt {attempt + 1}/{retries})"
                print(error_msg)
                logging.error(error_msg)
            except requests.exceptions.ConnectionError:
                error_msg = f"Connection error while sending diagnostics (attempt {attempt + 1}/{retries})"
                print(error_msg)
                logging.error(error_msg)
            except Exception as e:
                error_msg = f"Exception while sending diagnostics (attempt {attempt + 1}/{retries}): {e}"
                print(error_msg)
                logging.error(error_msg)
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
        logging.error("Failed to send diagnostics after all retries")
        return False

def modulate_value(base, start_time):
    current_time = time.time() - start_time
    periodic = math.sin(2 * math.pi * current_time / (24 * 3600))
    periodic_component = 5 * periodic
    noise = random.gauss(0, 0.5)
    value = base + periodic_component + noise
    return round(value, 2)

def send_reading(values):
    required_fields = {'temperature': float, 'humidity': float, 'methane': float, 'light': int}
    if not all(k in values and isinstance(values[k], v) for k, v in required_fields.items()):
        error_msg = f"Invalid sensor data format: {values}"
        print(error_msg)
        logging.error(error_msg)
        return False
    
    # Create readings array in the required format
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    readings = [
        {"sensor_id": key, "value": value, "timestamp": timestamp}
        for key, value in values.items()
    ]
    payload = {"readings": readings}
    
    retries = 3
    for attempt in range(retries):
        try:
            headers = {'Authorization': 'Bearer YOUR_API_KEY'}  # Replace with actual API key if required
            response = requests.post('https://trequer.vercel.app/api/sensors', json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                logging.info(f"Successfully sent sensor data: {payload}")
                return True
            else:
                error_msg = f"Error sending data: {response.status_code} - {response.text}"
                print(error_msg)
                logging.error(error_msg)
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out while sending sensor data (attempt {attempt + 1}/{retries})"
            print(error_msg)
            logging.error(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection error while sending sensor data (attempt {attempt + 1}/{retries})"
            print(error_msg)
            logging.error(error_msg)
        except Exception as e:
            error_msg = f"Exception while sending sensor data (attempt {attempt + 1}/{retries}): {e}"
            print(error_msg)
            logging.error(error_msg)
        if attempt < retries - 1:
            time.sleep(2 ** attempt)
    logging.error("Failed to send sensor data after all retries")
    return False

def readserial(comport, baudrate, start_time):
    ser = serial.Serial(comport, baudrate, timeout=0.1)
    diagnostics = DiagnosticsCollector()
    last_diagnostics_time = 0
    last_sensor_time = 0

    while True:
        data = ser.readline().decode().strip()
        current_time = time.time()
        if data and current_time - last_sensor_time >= 1:
            values = {}
            try:
                data_out_list = data.split('|')
                values['temperature'] = float(data_out_list[4])
                values['humidity'] = float(data_out_list[3])
                values['methane'] = float(data_out_list[5])
                values['light'] = int(data_out_list[2])
                print("Prepared sensor data: ", values)
                if send_reading(values):
                    last_sensor_time = current_time
                    print("Successfully sent sensor data")
            except (IndexError, ValueError) as e:
                error_msg = f"Error parsing sensor data: {e}"
                print(error_msg)
                logging.error(error_msg)
                continue
        if current_time - last_diagnostics_time >= 60:
            if diagnostics.send_diagnostics():
                print("Successfully sent diagnostic data")
            else:
                print("Failed to send diagnostic data")
            last_diagnostics_time = current_time

if __name__ == '__main__':
    start_time = time.time()
    readserial('/dev/ttyACM0', 9600, start_time)
