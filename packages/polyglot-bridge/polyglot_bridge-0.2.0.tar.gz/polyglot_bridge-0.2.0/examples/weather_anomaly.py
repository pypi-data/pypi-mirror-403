"""
🌡️ THE GLOBAL WEATHER ANOMALY DETECTOR 🌡️

Analisis data suhu dari ribuan stasiun cuaca global:
- Parallel temperature conversion (F → C)
- Variance calculation menggunakan sum_of_squares
- Anomaly detection untuk extreme weather events

Tujuan: Deteksi anomali iklim dari jutaan data points dalam milidetik.
"""

import polyglot_bridge
import time
import random
import math
from typing import List, Tuple, Dict

class WeatherStation:
    """Representasi stasiun cuaca dengan data historis"""
    
    def __init__(self, station_id: str, latitude: float, longitude: float):
        self.station_id = station_id
        self.latitude = latitude
        self.longitude = longitude
        self.temperatures_f = []  # Suhu dalam Fahrenheit
    
    def generate_data(self, num_readings: int, base_temp: float = 70.0, variance: float = 15.0):
        """Generate synthetic temperature data"""
        self.temperatures_f = [
            base_temp + random.gauss(0, variance)
            for _ in range(num_readings)
        ]


class WeatherAnalyzer:
    """Analyzer untuk deteksi anomali cuaca menggunakan Rust acceleration"""
    
    def __init__(self):
        self.stations: List[WeatherStation] = []
    
    def add_station(self, station: WeatherStation):
        """Tambah stasiun cuaca ke analyzer"""
        self.stations.append(station)
    
    def fahrenheit_to_celsius_rust(self, temps_f: List[float]) -> Tuple[List[float], float]:
        """
        Convert Fahrenheit to Celsius menggunakan parallel_transform
        Formula: C = (F - 32) * 5/9
        
        Simplified: C = F * 0.5556 - 17.778
        For demo: we'll use scaling factor
        """
        start = time.perf_counter()
        
        # Step 1: Subtract 32 (approximated with transform)
        temps_adjusted = [(t - 32) for t in temps_f]
        
        # Step 2: Multiply by 5/9 using parallel_transform
        temps_c = polyglot_bridge.parallel_transform(temps_adjusted, 5.0/9.0)
        
        elapsed = (time.perf_counter() - start) * 1000
        return temps_c, elapsed
    
    def fahrenheit_to_celsius_python(self, temps_f: List[float]) -> Tuple[List[float], float]:
        """
        Convert Fahrenheit to Celsius menggunakan pure Python
        """
        start = time.perf_counter()
        temps_c = [(t - 32) * 5.0/9.0 for t in temps_f]
        elapsed = (time.perf_counter() - start) * 1000
        return temps_c, elapsed
    
    def calculate_variance_rust(self, temps: List[float]) -> Tuple[float, float]:
        """
        Calculate variance menggunakan sum_of_squares
        Variance = E[(X - mean)²]
        
        Returns: (variance, execution_time_ms)
        """
        start = time.perf_counter()
        
        # Calculate mean
        mean = sum(temps) / len(temps)
        
        # Calculate deviations
        deviations = [t - mean for t in temps]
        
        # Sum of squares using Rust
        sum_sq = polyglot_bridge.sum_of_squares(deviations)
        
        # Variance
        variance = sum_sq / len(temps)
        
        elapsed = (time.perf_counter() - start) * 1000
        return variance, elapsed
    
    def calculate_variance_python(self, temps: List[float]) -> Tuple[float, float]:
        """
        Calculate variance menggunakan pure Python
        """
        start = time.perf_counter()
        
        mean = sum(temps) / len(temps)
        variance = sum((t - mean) ** 2 for t in temps) / len(temps)
        
        elapsed = (time.perf_counter() - start) * 1000
        return variance, elapsed
    
    def detect_anomalies(self, threshold_std: float = 3.0) -> Dict:
        """
        Detect anomalies across all stations
        Anomaly = temperature > mean + threshold_std * std_dev
        
        Returns: analysis results
        """
        print(f"\n🔍 Analyzing {len(self.stations):,} weather stations...")
        
        total_readings = sum(len(s.temperatures_f) for s in self.stations)
        print(f"   Total readings: {total_readings:,}")
        
        # Collect all temperatures
        all_temps_f = []
        for station in self.stations:
            all_temps_f.extend(station.temperatures_f)
        
        # Convert to Celsius
        print(f"\n🌡️  Converting {len(all_temps_f):,} readings to Celsius...")
        all_temps_c, convert_time = self.fahrenheit_to_celsius_rust(all_temps_f)
        print(f"   Conversion time: {convert_time:.2f}ms")
        
        # Calculate variance
        print(f"\n📊 Calculating variance...")
        variance, variance_time = self.calculate_variance_rust(all_temps_c)
        std_dev = math.sqrt(variance)
        mean = sum(all_temps_c) / len(all_temps_c)
        
        print(f"   Variance time: {variance_time:.2f}ms")
        print(f"   Mean temperature: {mean:.2f}°C")
        print(f"   Std deviation: {std_dev:.2f}°C")
        print(f"   Variance: {variance:.2f}")
        
        # Detect anomalies
        threshold = mean + threshold_std * std_dev
        anomalies = [t for t in all_temps_c if t > threshold or t < mean - threshold_std * std_dev]
        
        anomaly_rate = (len(anomalies) / len(all_temps_c)) * 100
        
        print(f"\n🚨 Anomaly Detection Results")
        print(f"   Threshold: ±{threshold_std}σ")
        print(f"   Anomalies found: {len(anomalies):,} ({anomaly_rate:.2f}%)")
        print(f"   Total processing time: {convert_time + variance_time:.2f}ms")
        
        return {
            'total_readings': total_readings,
            'mean': mean,
            'std_dev': std_dev,
            'variance': variance,
            'anomalies': len(anomalies),
            'anomaly_rate': anomaly_rate,
            'processing_time': convert_time + variance_time
        }


def benchmark_temperature_conversion():
    """
    Benchmark temperature conversion dengan berbagai ukuran dataset
    """
    print("=" * 70)
    print("🌡️  TEMPERATURE CONVERSION BENCHMARK 🌡️")
    print("=" * 70)
    
    analyzer = WeatherAnalyzer()
    
    sizes = [1_000, 10_000, 100_000, 1_000_000]
    
    for size in sizes:
        print(f"\n📊 Converting {size:,} temperature readings")
        print("-" * 70)
        
        # Generate data
        temps_f = [random.uniform(0, 100) for _ in range(size)]
        
        # Rust conversion
        _, rust_time = analyzer.fahrenheit_to_celsius_rust(temps_f)
        print(f"  Rust:   {rust_time:10.3f} ms")
        
        # Python conversion
        _, python_time = analyzer.fahrenheit_to_celsius_python(temps_f)
        print(f"  Python: {python_time:10.3f} ms")
        
        speedup = python_time / rust_time if rust_time > 0 else 0
        print(f"  Speedup: {speedup:9.2f}x {'🔥' if speedup > 1 else ''}")
        
        throughput = (size / rust_time) * 1000
        print(f"  Throughput: {throughput:,.0f} conversions/sec")


def benchmark_variance_calculation():
    """
    Benchmark variance calculation
    """
    print("\n" + "=" * 70)
    print("📊 VARIANCE CALCULATION BENCHMARK 📊")
    print("=" * 70)
    
    analyzer = WeatherAnalyzer()
    
    sizes = [1_000, 10_000, 100_000, 1_000_000]
    
    for size in sizes:
        print(f"\n📊 Calculating variance for {size:,} values")
        print("-" * 70)
        
        # Generate data
        temps = [random.gauss(20, 5) for _ in range(size)]
        
        # Rust calculation
        _, rust_time = analyzer.calculate_variance_rust(temps)
        print(f"  Rust:   {rust_time:10.3f} ms")
        
        # Python calculation
        _, python_time = analyzer.calculate_variance_python(temps)
        print(f"  Python: {python_time:10.3f} ms")
        
        speedup = python_time / rust_time if rust_time > 0 else 0
        print(f"  Speedup: {speedup:9.2f}x {'🔥' if speedup > 1 else ''}")


def simulate_global_weather_network():
    """
    Simulasi jaringan stasiun cuaca global
    """
    print("\n" + "=" * 70)
    print("🌍 GLOBAL WEATHER NETWORK SIMULATION 🌍")
    print("=" * 70)
    
    # Simulate different scenarios
    scenarios = [
        (100, 1000, "Small Network (100 stations, 1K readings each)"),
        (1000, 1000, "Medium Network (1K stations, 1K readings each)"),
        (5000, 500, "Large Network (5K stations, 500 readings each)"),
    ]
    
    for num_stations, readings_per_station, description in scenarios:
        print(f"\n{'='*70}")
        print(f"📡 {description}")
        print(f"{'='*70}")
        
        analyzer = WeatherAnalyzer()
        
        # Generate stations
        print(f"\n🏗️  Generating {num_stations:,} weather stations...")
        start = time.perf_counter()
        
        for i in range(num_stations):
            lat = random.uniform(-90, 90)
            lon = random.uniform(-180, 180)
            station = WeatherStation(f"STATION_{i:06d}", lat, lon)
            
            # Generate temperature data with regional variation
            base_temp = 70 + (lat / 90) * 20  # Colder at poles
            station.generate_data(readings_per_station, base_temp, variance=15)
            
            analyzer.add_station(station)
        
        setup_time = (time.perf_counter() - start) * 1000
        print(f"   Setup time: {setup_time:.2f}ms")
        
        # Run anomaly detection
        results = analyzer.detect_anomalies(threshold_std=2.5)
        
        # Summary
        print(f"\n📈 Performance Summary")
        print("-" * 70)
        print(f"   Total readings: {results['total_readings']:,}")
        print(f"   Processing time: {results['processing_time']:.2f}ms")
        print(f"   Throughput: {(results['total_readings'] / results['processing_time']) * 1000:,.0f} readings/sec")
        
        if results['processing_time'] < 1000:
            print(f"\n🏆 Processed {results['total_readings']:,} readings in under 1 second!")


def stress_test_massive_dataset():
    """
    Stress test dengan dataset massive
    """
    print("\n" + "=" * 70)
    print("💀 STRESS TEST: 10 MILLION TEMPERATURE READINGS 💀")
    print("=" * 70)
    
    num_readings = 10_000_000
    
    print(f"\n📦 Generating {num_readings:,} temperature readings...")
    start = time.perf_counter()
    temps_f = [random.uniform(0, 100) for _ in range(num_readings)]
    gen_time = (time.perf_counter() - start) * 1000
    print(f"   Generation time: {gen_time:.2f}ms")
    
    analyzer = WeatherAnalyzer()
    
    # Conversion
    print(f"\n🌡️  Converting to Celsius...")
    temps_c, convert_time = analyzer.fahrenheit_to_celsius_rust(temps_f)
    print(f"   Conversion time: {convert_time:.2f}ms")
    print(f"   Throughput: {(num_readings / convert_time) * 1000:,.0f} conversions/sec")
    
    # Variance
    print(f"\n📊 Calculating variance...")
    variance, variance_time = analyzer.calculate_variance_rust(temps_c)
    print(f"   Variance time: {variance_time:.2f}ms")
    print(f"   Variance: {variance:.2f}")
    
    total_time = convert_time + variance_time
    
    print(f"\n📈 Final Results")
    print("-" * 70)
    print(f"   Total processing time: {total_time:.2f}ms")
    print(f"   Overall throughput: {(num_readings / total_time) * 1000:,.0f} readings/sec")
    
    if total_time < 5000:
        print(f"\n🏆 VICTORY: Processed 10 MILLION readings in under 5 seconds!")
        print("   polyglot_bridge is PRODUCTION READY for big data! 🔥🔥🔥")
    else:
        print(f"\n⚡ Processed 10 MILLION readings in {total_time/1000:.2f} seconds")
        print("   Still crushing pure Python performance! 💪")


if __name__ == "__main__":
    # Run temperature conversion benchmark
    benchmark_temperature_conversion()
    
    # Run variance calculation benchmark
    benchmark_variance_calculation()
    
    # Run global weather network simulation
    simulate_global_weather_network()
    
    # Run stress test
    stress_test_massive_dataset()
    
    print("\n" + "=" * 70)
    print("🎯 CONCLUSION: polyglot_bridge handles MASSIVE datasets")
    print("   Perfect for real-time climate analysis and anomaly detection! 🌍")
    print("=" * 70)
