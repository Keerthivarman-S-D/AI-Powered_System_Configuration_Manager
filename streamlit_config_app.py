import streamlit as st
import psutil
import platform
from datetime import datetime
import time
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os
import json

# Page configuration
st.set_page_config(
    page_title="AI Configuration Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for black background and clean design
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    .main {
        background-color: #000000;
    }
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        color: #ffffff;
    }
    div[data-testid="stMetricLabel"] {
        color: #cccccc;
    }
    .stProgress > div > div > div > div {
        background-color: #00ff00;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .css-1d391kg {
        background-color: #1a1a1a;
    }
    div[data-baseweb="select"] {
        background-color: #1a1a1a;
    }
    .stSelectbox {
        color: #ffffff;
    }
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
    }
    .metric-card {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333333;
    }
    </style>
""", unsafe_allow_html=True)

class ConfigManager:
    def __init__(self):
        self.metrics_file = "streamlit_metrics.json"
        self.model_file = "streamlit_model.pkl"
        self.metrics_history = []
        self.model = None
        self.scaler = StandardScaler()
        
    def collect_metrics(self):
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
    
    def analyze_state(self, metrics):
        """Analyze system state"""
        cpu = metrics['cpu_percent']
        mem = metrics['memory_percent']
        
        if cpu > 80 or mem > 85:
            return "CRITICAL", "#ff0000"
        elif cpu > 60 or mem > 70:
            return "HIGH LOAD", "#ff9900"
        elif cpu > 30 or mem > 50:
            return "MODERATE", "#3399ff"
        else:
            return "OPTIMAL", "#00ff00"
    
    def get_recommendations(self, state, metrics):
        """Get recommendations based on state"""
        recommendations = []
        
        if state == "CRITICAL":
            recommendations = [
                "CRITICAL: System under heavy load",
                "Close unnecessary applications immediately",
                "Disable startup programs",
                "Clear temporary files",
                "Restart high-memory processes"
            ]
        elif state == "HIGH LOAD":
            recommendations = [
                "System experiencing high load",
                "Consider closing browser tabs",
                "Disable background applications",
                "Check for Windows updates running"
            ]
        elif state == "MODERATE":
            recommendations = [
                "System running normally",
                "Performance optimizations available",
                "Consider disk cleanup if needed"
            ]
        else:
            recommendations = [
                "System running optimally",
                "No immediate actions needed",
                "Good time for maintenance tasks"
            ]
        
        return recommendations
    
    def get_top_processes(self, n=5):
        """Get top resource-consuming processes"""
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] is not None and info['memory_percent'] is not None:
                    if info['cpu_percent'] > 0 or info['memory_percent'] > 0:
                        processes.append({
                            'Process': info['name'],
                            'CPU (%)': round(info['cpu_percent'], 2),
                            'Memory (%)': round(info['memory_percent'], 2)
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes.sort(key=lambda x: x['CPU (%)'] + x['Memory (%)'], reverse=True)
        return processes[:n]
    
    def save_metrics(self, metrics):
        """Save metrics to history"""
        self.metrics_history.append(metrics)
        
        # Keep only last 100 records
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics_history, f)
        except Exception as e:
            st.error(f"Error saving metrics: {e}")
    
    def load_metrics(self):
        """Load metrics history"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.metrics_history = json.loads(content)
            except Exception:
                self.metrics_history = []
    
    def train_model(self):
        """Train ML model"""
        if len(self.metrics_history) < 10:
            return False, "Need at least 10 samples to train"
        
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
            
            state, _ = self.analyze_state(entry)
            state_map = {'OPTIMAL': 0, 'MODERATE': 1, 'HIGH LOAD': 2, 'CRITICAL': 3}
            y.append(state_map[state])
        
        X = np.array(X)
        y = np.array(y)
        
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        self.model = DecisionTreeClassifier(max_depth=4, random_state=42)
        self.model.fit(X_scaled, y)
        
        try:
            with open(self.model_file, 'wb') as f:
                pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
        except Exception as e:
            return False, f"Error saving model: {e}"
        
        return True, "Model trained successfully"

# Initialize session state
if 'manager' not in st.session_state:
    st.session_state.manager = ConfigManager()
    st.session_state.manager.load_metrics()

manager = st.session_state.manager

# Header
st.title("AI-Powered System Configuration Manager")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("System Information")
    st.text(f"OS: {platform.system()} {platform.release()}")
    st.text(f"Processor: {platform.processor()[:40]}")
    st.text(f"RAM: {psutil.virtual_memory().total / (1024**3):.2f} GB")
    st.text(f"CPU Cores: {psutil.cpu_count(logical=False)} Physical")
    st.text(f"Logical Cores: {psutil.cpu_count(logical=True)}")
    
    st.markdown("---")
    st.header("Data Collection")
    
    if st.button("Collect Data Sample", use_container_width=True):
        metrics = manager.collect_metrics()
        manager.save_metrics(metrics)
        st.success("Sample collected")
        st.rerun()
    
    st.text(f"Total Samples: {len(manager.metrics_history)}")
    
    st.markdown("---")
    st.header("AI Model")
    
    if st.button("Train Model", use_container_width=True):
        success, message = manager.train_model()
        if success:
            st.success(message)
        else:
            st.warning(message)
    
    st.markdown("---")
    auto_refresh = st.checkbox("Auto Refresh (5s)", value=False)

# Main content
metrics = manager.collect_metrics()
state, color = manager.analyze_state(metrics)

# System State
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="System State",
        value=state,
        delta=None
    )
    st.markdown(f'<div style="width:100%; height:5px; background-color:{color}; border-radius:3px;"></div>', unsafe_allow_html=True)

with col2:
    st.metric(
        label="CPU Usage",
        value=f"{metrics['cpu_percent']:.1f}%"
    )

with col3:
    st.metric(
        label="Memory Usage",
        value=f"{metrics['memory_percent']:.1f}%"
    )

with col4:
    st.metric(
        label="Disk Usage",
        value=f"{metrics['disk_percent']:.1f}%"
    )

st.markdown("---")

# Progress bars
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("CPU")
    st.progress(metrics['cpu_percent'] / 100)

with col2:
    st.subheader("Memory")
    st.progress(metrics['memory_percent'] / 100)

with col3:
    st.subheader("Disk")
    st.progress(metrics['disk_percent'] / 100)

st.markdown("---")

# Two column layout for recommendations and processes
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("System Recommendations")
    recommendations = manager.get_recommendations(state, metrics)
    
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"**{i}.** {rec}")

with col2:
    st.subheader("Top Resource Consumers")
    top_processes = manager.get_top_processes(5)
    
    if top_processes:
        df = pd.DataFrame(top_processes)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

# Historical data chart
if len(manager.metrics_history) > 1:
    st.markdown("---")
    st.subheader("Historical Performance")
    
    # Prepare data for chart
    timestamps = [entry['timestamp'][-8:] for entry in manager.metrics_history[-20:]]
    cpu_data = [entry['cpu_percent'] for entry in manager.metrics_history[-20:]]
    mem_data = [entry['memory_percent'] for entry in manager.metrics_history[-20:]]
    
    # Create plotly chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=cpu_data,
        mode='lines+markers',
        name='CPU',
        line=dict(color='#3399ff', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=mem_data,
        mode='lines+markers',
        name='Memory',
        line=dict(color='#ff9900', width=2)
    ))
    
    fig.update_layout(
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#0a0a0a',
        font=dict(color='#ffffff'),
        xaxis=dict(
            title='Time',
            gridcolor='#333333'
        ),
        yaxis=dict(
            title='Usage (%)',
            gridcolor='#333333',
            range=[0, 100]
        ),
        legend=dict(
            bgcolor='#1a1a1a',
            bordercolor='#333333',
            borderwidth=1
        ),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Auto refresh
if auto_refresh:
    time.sleep(5)
    st.rerun()