from flask import Flask, render_template, jsonify
import psutil
import platform
from datetime import datetime
import json
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Windows AI Config Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 30px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255,255,255,0.15);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s;
        }
        .card:hover { transform: translateY(-5px); }
        
        .card h3 {
            font-size: 1.3em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .metric {
            font-size: 2.5em;
            font-weight: bold;
            margin: 15px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 25px;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 12px;
            transition: width 0.5s ease, background-color 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .state-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
            margin: 10px 0;
        }
        
        .state-idle { background: #10b981; }
        .state-moderate { background: #3b82f6; }
        .state-high { background: #f59e0b; }
        .state-critical { background: #ef4444; }
        
        .recommendations {
            background: rgba(255,255,255,0.15);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .recommendations h3 {
            font-size: 1.5em;
            margin-bottom: 20px;
        }
        
        .recommendation-item {
            background: rgba(0,0,0,0.2);
            padding: 12px 18px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #fff;
        }
        
        .process-list {
            margin-top: 15px;
        }
        
        .process-item {
            background: rgba(0,0,0,0.2);
            padding: 10px;
            border-radius: 6px;
            margin: 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .refresh-btn {
            background: #fff;
            color: #667eea;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            margin: 20px auto;
            display: block;
        }
        
        .refresh-btn:hover {
            background: #667eea;
            color: #fff;
            transform: scale(1.05);
        }
        
        .timestamp {
            text-align: center;
            opacity: 0.8;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI-Powered Windows Configuration Manager</h1>
            <p>Real-time System Monitoring & Intelligent Recommendations</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>💻 CPU Usage</h3>
                <div class="metric" id="cpu-metric">--</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpu-bar">0%</div>
                </div>
            </div>
            
            <div class="card">
                <h3>🧠 Memory Usage</h3>
                <div class="metric" id="memory-metric">--</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memory-bar">0%</div>
                </div>
            </div>
            
            <div class="card">
                <h3>💾 Disk Usage</h3>
                <div class="metric" id="disk-metric">--</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="disk-bar">0%</div>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ System State</h3>
                <div id="system-state">
                    <span class="state-badge state-idle">ANALYZING...</span>
                </div>
                <div style="margin-top: 15px; font-size: 0.9em;">
                    <div>Processes: <strong id="process-count">--</strong></div>
                    <div>CPU Freq: <strong id="cpu-freq">--</strong> MHz</div>
                </div>
            </div>
        </div>
        
        <div class="recommendations">
            <h3>🎯 AI Recommendations</h3>
            <div id="recommendations-list">
                <div class="recommendation-item">Loading recommendations...</div>
            </div>
            
            <div class="process-list">
                <h4 style="margin-top: 25px; margin-bottom: 15px;">🔝 Top Resource Consumers</h4>
                <div id="top-processes"></div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="updateData()">🔄 Refresh Data</button>
        <div class="timestamp" id="timestamp"></div>
    </div>
    
    <script>
        function getProgressColor(value) {
            if (value >= 80) return '#ef4444';
            if (value >= 60) return '#f59e0b';
            if (value >= 40) return '#3b82f6';
            return '#10b981';
        }
        
        function updateProgressBar(barId, value) {
            const bar = document.getElementById(barId);
            bar.style.width = value + '%';
            bar.style.backgroundColor = getProgressColor(value);
            bar.textContent = value.toFixed(1) + '%';
        }
        
        function getStateClass(state) {
            const map = {
                'IDLE': 'state-idle',
                'MODERATE': 'state-moderate',
                'HIGH_LOAD': 'state-high',
                'CRITICAL': 'state-critical'
            };
            return map[state] || 'state-idle';
        }
        
        function updateData() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    // Update metrics
                    document.getElementById('cpu-metric').textContent = 
                        data.metrics.cpu_percent.toFixed(1) + '%';
                    document.getElementById('memory-metric').textContent = 
                        data.metrics.memory_percent.toFixed(1) + '%';
                    document.getElementById('disk-metric').textContent = 
                        data.metrics.disk_percent.toFixed(1) + '%';
                    
                    // Update progress bars
                    updateProgressBar('cpu-bar', data.metrics.cpu_percent);
                    updateProgressBar('memory-bar', data.metrics.memory_percent);
                    updateProgressBar('disk-bar', data.metrics.disk_percent);
                    
                    // Update system state
                    const stateDiv = document.getElementById('system-state');
                    stateDiv.innerHTML = `
                        <span class="state-badge ${getStateClass(data.state)}">${data.state}</span>
                    `;
                    
                    document.getElementById('process-count').textContent = 
                        data.metrics.process_count;
                    document.getElementById('cpu-freq').textContent = 
                        data.metrics.cpu_freq.toFixed(0);
                    
                    // Update recommendations
                    const recList = document.getElementById('recommendations-list');
                    recList.innerHTML = data.recommendations.actions
                        .map(action => `<div class="recommendation-item">${action}</div>`)
                        .join('');
                    
                    // Update top processes
                    const procList = document.getElementById('top-processes');
                    procList.innerHTML = data.top_processes
                        .map(proc => `
                            <div class="process-item">
                                <span><strong>${proc.name}</strong></span>
                                <span>CPU: ${proc.cpu.toFixed(1)}% | RAM: ${proc.memory.toFixed(1)}%</span>
                            </div>
                        `).join('');
                    
                    // Update timestamp
                    document.getElementById('timestamp').textContent = 
                        'Last updated: ' + new Date().toLocaleTimeString();
                })
                .catch(error => console.error('Error:', error));
        }
        
        // Update immediately and then every 5 seconds
        updateData();
        setInterval(updateData, 5000);
    </script>
</body>
</html>
"""

def analyze_system_state(metrics):
    cpu = metrics['cpu_percent']
    mem = metrics['memory_percent']
    
    if cpu > 80 or mem > 85:
        return "CRITICAL"
    elif cpu > 60 or mem > 70:
        return "HIGH_LOAD"
    elif cpu > 30 or mem > 50:
        return "MODERATE"
    else:
        return "IDLE"

def get_recommendations(metrics, state):
    recommendations = {'state': state, 'actions': []}
    
    if state == "CRITICAL":
        recommendations['actions'] = [
            "⚠️ CRITICAL: System under heavy load",
            "🔴 Close unnecessary applications immediately",
            "🔴 Disable startup programs",
            "🔴 Clear temporary files",
            f"📊 Memory Usage: {metrics['memory_percent']:.1f}%",
            f"📊 CPU Usage: {metrics['cpu_percent']:.1f}%"
        ]
    elif state == "HIGH_LOAD":
        recommendations['actions'] = [
            "⚡ System experiencing high load",
            "🟡 Consider closing browser tabs",
            "🟡 Disable background apps",
            "🟡 Check for Windows updates running",
            f"📊 Memory Usage: {metrics['memory_percent']:.1f}%"
        ]
    elif state == "MODERATE":
        recommendations['actions'] = [
            "✅ System running normally",
            "🟢 Performance optimizations available",
            "🟢 Consider disk cleanup if needed",
            f"📊 Memory Usage: {metrics['memory_percent']:.1f}%"
        ]
    else:
        recommendations['actions'] = [
            "✅ System running optimally",
            "🟢 No immediate actions needed",
            "🟢 Good time for maintenance tasks"
        ]
    
    return recommendations

def get_top_processes(n=5):
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
    
    processes.sort(key=lambda x: x['cpu'] + x['memory'], reverse=True)
    return processes[:n]

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/metrics')
def get_metrics():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'disk_percent': disk.percent,
        'process_count': len(psutil.pids()),
        'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0
    }
    
    state = analyze_system_state(metrics)
    recommendations = get_recommendations(metrics, state)
    top_processes = get_top_processes(5)
    
    return jsonify({
        'metrics': metrics,
        'state': state,
        'recommendations': recommendations,
        'top_processes': top_processes,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Windows AI Config Manager Dashboard")
    print("="*60)
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Total RAM: {psutil.virtual_memory().total / (1024**3):.2f} GB")
    print("\n📱 Open your browser and go to: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)