import psutil
import platform
import time
import json
from datetime import datetime
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os

class WindowsConfigManager:
    def __init__(self):
        self.metrics_history = []
        self.model = None
        self.scaler = StandardScaler()
        self.config_file = "system_metrics.json"
        self.model_file = "config_model.pkl"
        
    def collect_system_metrics(self):
        """Collect current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'process_count': len(psutil.pids()),
            'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }
        
        return metrics
    
    def analyze_system_state(self, metrics):
        """Analyze and categorize system state"""
        cpu = metrics['cpu_percent']
        mem = metrics['memory_percent']
        
        # Define system states
        if cpu > 80 or mem > 85:
            return "CRITICAL"
        elif cpu > 60 or mem > 70:
            return "HIGH_LOAD"
        elif cpu > 30 or mem > 50:
            return "MODERATE"
        else:
            return "IDLE"
    
    def get_recommendations(self, metrics, state):
        """AI-powered recommendations based on system state"""
        recommendations = {
            'state': state,
            'actions': [],
            'priority': 'LOW'
        }
        
        if state == "CRITICAL":
            recommendations['priority'] = 'CRITICAL'
            recommendations['actions'] = [
                "⚠️ CRITICAL: System under heavy load",
                "🔴 Close unnecessary applications immediately",
                "🔴 Disable startup programs",
                "🔴 Clear temporary files",
                "🔴 Restart high-memory processes",
                f"📊 Memory Usage: {metrics['memory_percent']:.1f}%",
                f"📊 CPU Usage: {metrics['cpu_percent']:.1f}%"
            ]
        elif state == "HIGH_LOAD":
            recommendations['priority'] = 'HIGH'
            recommendations['actions'] = [
                "⚡ System experiencing high load",
                "🟡 Consider closing browser tabs",
                "🟡 Disable background apps",
                "🟡 Check for Windows updates running",
                f"📊 Memory Usage: {metrics['memory_percent']:.1f}%",
                f"📊 CPU Usage: {metrics['cpu_percent']:.1f}%"
            ]
        elif state == "MODERATE":
            recommendations['priority'] = 'MEDIUM'
            recommendations['actions'] = [
                "✅ System running normally",
                "🟢 Performance optimizations available",
                "🟢 Consider disk cleanup if needed",
                f"📊 Memory Usage: {metrics['memory_percent']:.1f}%",
                f"📊 CPU Usage: {metrics['cpu_percent']:.1f}%"
            ]
        else:
            recommendations['priority'] = 'LOW'
            recommendations['actions'] = [
                "✅ System running optimally",
                "🟢 No immediate actions needed",
                "🟢 Good time for maintenance tasks",
                f"📊 Memory Usage: {metrics['memory_percent']:.1f}%",
                f"📊 CPU Usage: {metrics['cpu_percent']:.1f}%"
            ]
        
        # Add process-specific recommendations
        top_processes = self.get_top_processes(5)
        if top_processes:
            recommendations['actions'].append("\n🔍 Top Resource Consumers:")
            for proc in top_processes:
                recommendations['actions'].append(
                    f"   • {proc['name']}: CPU {proc['cpu']:.1f}% | RAM {proc['memory']:.1f}%"
                )
        
        return recommendations
    
    def get_top_processes(self, n=5):
        """Get top N resource-consuming processes"""
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] > 0 or info['memory_percent'] > 0:
                    processes.append({
                        'name': info['name'],
                        'cpu': info['cpu_percent'],
                        'memory': info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU + Memory usage
        processes.sort(key=lambda x: x['cpu'] + x['memory'], reverse=True)
        return processes[:n]
    
    def train_model(self):
        """Train simple ML model for pattern recognition"""
        if len(self.metrics_history) < 10:
            print("⚠️  Not enough data to train model (need at least 10 samples)")
            return False
        
        # Prepare training data
        X = []
        y = []
        
        for entry in self.metrics_history:
            features = [
                entry['cpu_percent'],
                entry['memory_percent'],
                entry['disk_percent'],
                entry['process_count']
            ]
            X.append(features)
            
            # Label based on state
            state = self.analyze_system_state(entry)
            state_map = {'IDLE': 0, 'MODERATE': 1, 'HIGH_LOAD': 2, 'CRITICAL': 3}
            y.append(state_map[state])
        
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        self.model = DecisionTreeClassifier(max_depth=4, random_state=42)
        self.model.fit(X_scaled, y)
        
        # Save model
        with open(self.model_file, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
        
        print("✅ ML Model trained successfully!")
        return True
    
    def predict_state(self, metrics):
        """Predict system state using ML model"""
        if self.model is None:
            return None
        
        features = np.array([[
            metrics['cpu_percent'],
            metrics['memory_percent'],
            metrics['disk_percent'],
            metrics['process_count']
        ]])
        
        X_scaled = self.scaler.transform(features)
        prediction = self.model.predict(X_scaled)[0]
        
        state_map = {0: 'IDLE', 1: 'MODERATE', 2: 'HIGH_LOAD', 3: 'CRITICAL'}
        return state_map[prediction]
    
    def save_metrics(self):
        """Save metrics history to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)
    
    def load_metrics(self):
        """Load metrics history from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.metrics_history = json.loads(content)
                        print(f"✅ Loaded {len(self.metrics_history)} historical records")
                    else:
                        print("⚠️  Empty metrics file, starting fresh")
                        self.metrics_history = []
            except json.JSONDecodeError:
                print("⚠️  Corrupted metrics file, starting fresh")
                self.metrics_history = []
        else:
            print("ℹ️  No previous data found, starting fresh")
    
    def load_model(self):
        """Load trained model"""
        if os.path.exists(self.model_file):
            try:
                # Check if file is not empty
                if os.path.getsize(self.model_file) > 0:
                    with open(self.model_file, 'rb') as f:
                        data = pickle.load(f)
                        self.model = data['model']
                        self.scaler = data['scaler']
                    print("✅ ML Model loaded successfully!")
                    return True
                else:
                    print("⚠️  Empty model file, will need to train")
                    return False
            except Exception as e:
                print(f"⚠️  Could not load model: {e}")
                print("ℹ️  You can train a new model using option 3")
                return False
        else:
            print("ℹ️  No trained model found, you can train one using option 3")
        return False
    
    def display_system_info(self):
        """Display system information"""
        print("\n" + "="*60)
        print("🖥️  WINDOWS AI-POWERED CONFIGURATION MANAGER")
        print("="*60)
        print(f"OS: {platform.system()} {platform.release()}")
        print(f"Processor: {platform.processor()}")
        print(f"Total RAM: {psutil.virtual_memory().total / (1024**3):.2f} GB")
        print(f"CPU Cores: {psutil.cpu_count(logical=False)} Physical | {psutil.cpu_count(logical=True)} Logical")
        print("="*60 + "\n")
    
    def run_monitoring(self, duration=60, interval=5):
        """Run continuous monitoring"""
        print(f"🔄 Starting monitoring for {duration} seconds (interval: {interval}s)")
        print("📊 Collecting data for AI training...\n")
        
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < duration:
            count += 1
            metrics = self.collect_system_metrics()
            state = self.analyze_system_state(metrics)
            
            # Try ML prediction if model exists
            predicted_state = self.predict_state(metrics) if self.model else None
            
            self.metrics_history.append(metrics)
            recommendations = self.get_recommendations(metrics, state)
            
            print(f"\n{'='*60}")
            print(f"📸 Sample #{count} | {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            print(f"State: {state} | Priority: {recommendations['priority']}")
            if predicted_state and predicted_state != state:
                print(f"🤖 AI Prediction: {predicted_state}")
            
            for action in recommendations['actions']:
                print(action)
            
            if count % 3 == 0:
                self.save_metrics()
            
            time.sleep(interval)
        
        self.save_metrics()
        print(f"\n✅ Monitoring complete! Collected {len(self.metrics_history)} samples")


def main():
    manager = WindowsConfigManager()
    manager.display_system_info()
    
    # Load existing data
    manager.load_metrics()
    manager.load_model()
    
    while True:
        print("\n" + "="*60)
        print("🤖 AI CONFIGURATION MANAGER - MAIN MENU")
        print("="*60)
        print("1. 📊 Quick System Analysis (Single Check)")
        print("2. 🔄 Start Monitoring (60 seconds)")
        print("3. 🧠 Train AI Model")
        print("4. 📈 View Historical Data")
        print("5. 🚀 Extended Monitoring (5 minutes)")
        print("6. ❌ Exit")
        print("="*60)
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            print("\n🔍 Analyzing system...")
            metrics = manager.collect_system_metrics()
            state = manager.analyze_system_state(metrics)
            recommendations = manager.get_recommendations(metrics, state)
            
            print(f"\n{'='*60}")
            print("📊 SYSTEM ANALYSIS REPORT")
            print(f"{'='*60}")
            print(f"State: {state}")
            print(f"Priority: {recommendations['priority']}\n")
            for action in recommendations['actions']:
                print(action)
            print(f"{'='*60}")
            
        elif choice == '2':
            manager.run_monitoring(duration=60, interval=5)
            
        elif choice == '3':
            print("\n🧠 Training AI Model...")
            if manager.train_model():
                print("✅ Model ready for predictions!")
            
        elif choice == '4':
            print(f"\n📈 Historical Records: {len(manager.metrics_history)}")
            if manager.metrics_history:
                recent = manager.metrics_history[-5:]
                print("\nLast 5 samples:")
                for i, entry in enumerate(recent, 1):
                    print(f"\n{i}. {entry['timestamp']}")
                    print(f"   CPU: {entry['cpu_percent']:.1f}% | RAM: {entry['memory_percent']:.1f}%")
            else:
                print("⚠️  No historical data available")
        
        elif choice == '5':
            manager.run_monitoring(duration=300, interval=10)
            
        elif choice == '6':
            print("\n👋 Saving data and exiting...")
            manager.save_metrics()
            print("✅ Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please try again.")


if __name__ == "__main__":
    main()