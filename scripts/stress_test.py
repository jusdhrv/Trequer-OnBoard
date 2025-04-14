import requests
import time
import random
import math
import threading
from datetime import datetime, timezone
import argparse
import psutil

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

class SensorSimulator:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/sensors"
        
        # Sensor configurations
        self.sensors = {
            "temperature": {
                "id": "temperature",
                "base_value": 22.0,      # Celsius
                "noise_amplitude": 0.5,
                "periodic_amplitude": 5.0
            },
            "humidity": {
                "id": "humidity",
                "base_value": 45.0,      # Percentage
                "noise_amplitude": 2.0,
                "periodic_amplitude": 15.0
            },
            "methane": {
                "id": "methane",
                "base_value": 2.0,       # PPM
                "noise_amplitude": 0.2,
                "periodic_amplitude": 1.0
            },
            "light": {
                "id": "light",
                "base_value": 800.0,     # Lux
                "noise_amplitude": 50.0,
                "periodic_amplitude": 500.0
            },
            "atmosphericPressure": {
                "id": "atmosphericPressure",
                "base_value": 1013.25,   # hPa
                "noise_amplitude": 1.0,
                "periodic_amplitude": 5.0
            }
        }
        
        self.start_time = time.time()

    def generate_reading(self, sensor_id, config):
        """Generate a realistic sensor reading with noise and periodic variations"""
        current_time = time.time() - self.start_time
        
        # Add periodic variation (24-hour cycle)
        periodic = math.sin(2 * math.pi * current_time / (24 * 3600))
        periodic_component = config["periodic_amplitude"] * periodic
        
        # Add random noise
        noise = random.gauss(0, config["noise_amplitude"] * 0.1)
        
        # Combine components
        value = config["base_value"] + periodic_component + noise
        
        # Ensure values stay within realistic ranges
        if sensor_id == "humidity":
            value = max(0, min(100, value))
        elif sensor_id in ["methane", "light"]:
            value = max(0, value)
        
        return round(value, 2)

    def send_readings(self):
        """Send readings for all sensors to the API"""
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        readings = []
        
        for sensor_id, config in self.sensors.items():
            value = self.generate_reading(sensor_id, config)
            readings.append({
                "sensor_id": sensor_id,
                "value": value,
                "timestamp": timestamp
            })
        
        try:
            response = requests.post(self.api_endpoint, json={"readings": readings})
            if response.status_code != 200:
                print(f"Error sending data: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Exception while sending data: {e}")
            return False

def run_diagnostics_thread(stop_event):
    """Run diagnostics collection in a separate thread"""
    diagnostics = DiagnosticsCollector()
    while not stop_event.is_set():
        diagnostics.send_diagnostics()
        time.sleep(60)  # Send diagnostics every minute

def run_stress_test(duration, delay=1.0, infinite=False):
    """Run the stress test for a specified duration or indefinitely"""
    simulator = SensorSimulator()
    stop_event = threading.Event()
    
    # Start diagnostics collection in a separate thread
    diagnostics_thread = threading.Thread(target=run_diagnostics_thread, args=(stop_event,))
    diagnostics_thread.start()
    
    start_time = time.time()
    successful_requests = 0
    failed_requests = 0
    
    print(f"Starting stress test{' indefinitely' if infinite else f' for {duration} seconds'} with {delay}s delay between requests")
    print("Press Ctrl+C to stop the test")
    
    try:
        while infinite or time.time() - start_time < duration:
            if simulator.send_readings():
                successful_requests += 1
            else:
                failed_requests += 1
            
            # Calculate and display statistics
            elapsed_time = time.time() - start_time
            requests_per_second = (successful_requests + failed_requests) / elapsed_time
            success_rate = (successful_requests / (successful_requests + failed_requests)) * 100
            
            print(f"\rElapsed: {elapsed_time:.1f}s | "
                  f"Successful: {successful_requests} | "
                  f"Failed: {failed_requests} | "
                  f"Req/s: {requests_per_second:.1f} | "
                  f"Success Rate: {success_rate:.1f}%", end="")
            
            time.sleep(delay)
    
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    finally:
        # Stop the diagnostics thread
        stop_event.set()
        diagnostics_thread.join()
    
    # Final statistics
    total_time = time.time() - start_time
    print("\n\nFinal Statistics:")
    print(f"Total Time: {total_time:.1f} seconds")
    print(f"Successful Requests: {successful_requests}")
    print(f"Failed Requests: {failed_requests}")
    print(f"Average Requests/Second: {(successful_requests + failed_requests) / total_time:.1f}")
    print(f"Overall Success Rate: {(successful_requests / (successful_requests + failed_requests)) * 100:.1f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='API Stress Test Tool for Sensor Data')
    parser.add_argument('--duration', type=int, default=3600,
                      help='Duration of the test in seconds (default: 3600, ignored if --infinite is set)')
    parser.add_argument('--delay', type=float, default=1.0,
                      help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--infinite', action='store_true',
                      help='Run the test indefinitely until Ctrl+C is pressed')
    
    args = parser.parse_args()
    
    run_stress_test(args.duration, args.delay, args.infinite) 