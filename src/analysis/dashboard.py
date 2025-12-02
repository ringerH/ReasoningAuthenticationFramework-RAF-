import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import glob
import time
import plotly.graph_objects as go
import plotly.express as px
from sklearn.metrics import auc

# --- CONFIGURATION ---
st.set_page_config(
    page_title="RAF Real-Time Monitor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Slick" Dark Mode Look
st.markdown("""
<style>
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    /* Chart Containers */
    .stPlotlyChart {
        background-color: #0E1117;
        border-radius: 10px;
    }
    /* Titles */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "data", "results")

# --- HELPER FUNCTIONS ---

@st.cache_data(ttl=2)  # Cache for 2 seconds to allow live updates without disk thrashing
def load_data(filepath):
    """Loads JSONL and returns raw DF + Aggregated Stats"""
    if not filepath or not os.path.exists(filepath):
        return None, None
    
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except:
                    continue
    except Exception as e:
        return None, None

    if not data:
        return None, None

    df = pd.DataFrame(data)
    
    # Validation
    if 'level' not in df.columns or 'is_correct' not in df.columns:
        return None, None

    # Sort
    df = df.sort_values(by=['level'])
    
    # Aggregation for Curves
    stats = df.groupby('level')['is_correct'].agg(['mean', 'count', 'sum']).reset_index()
    stats.columns = ['level', 'accuracy', 'count', 'correct_count']
    
    return df, stats

def calculate_kpis(stats):
    """Calculates Robust Score (AUC) and Max Cliff"""
    if stats is None or len(stats) < 2:
        return 0, 0, 0

    x = stats['level'].values
    y = stats['accuracy'].values
    
    # Drops
    drops = [y[i] - y[i+1] for i in range(len(y)-1)]
    max_cliff = max([max(0, d) for d in drops]) if drops else 0.0
    
    # AUC Normalization
    if x[-1] - x[0] == 0:
        perf_auc = 0.0
    else:
        perf_auc = auc(x, y) / (x[-1] - x[0])
        
    robust_score = perf_auc * (1.0 - max_cliff)
    
    return robust_score, max_cliff, y[-1] # Score, Cliff, Final Accuracy

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛 Control Panel")
    
    # File Scanner
    result_files = glob.glob(os.path.join(RESULTS_DIR, "run_*.jsonl"))
    result_files.sort(key=os.path.getmtime, reverse=True)
    
    if not result_files:
        st.error("No JSONL files found in `data/results/`")
        st.stop()

    selected_file = st.selectbox(
        "🔴 Live Run (Target)", 
        result_files, 
        index=0,
        format_func=lambda x: "📄 " + os.path.basename(x)
    )
    
    compare_file = st.selectbox(
        "🔵 Baseline (Optional)", 
        [None] + result_files, 
        index=0,
        format_func=lambda x: "📄 " + os.path.basename(x) if x else "None"
    )
    
    st.divider()
    
    auto_refresh = st.toggle("Auto-Refresh (Live Mode)", value=True)
    refresh_rate = st.slider("Refresh Rate (s)", 1, 10, 2)

# --- MAIN DATA LOADING ---
df_live, stats_live = load_data(selected_file)
df_base, stats_base = load_data(compare_file) if compare_file else (None, None)

if stats_live is None:
    st.warning("Waiting for data stream to initialize...")
    time.sleep(2)
    st.rerun()

# --- KPI CALCULATION ---
score_live, cliff_live, final_acc_live = calculate_kpis(stats_live)
score_base, cliff_base, final_acc_base = calculate_kpis(stats_base)

# Delta Calculations
delta_score = score_live - score_base if stats_base is not None else 0
delta_cliff = cliff_live - cliff_base if stats_base is not None else 0

# --- DASHBOARD HEADER ---
st.title("🧩 Reasoning Decay Monitor")
st.markdown(f"Tracking: **{os.path.basename(selected_file)}**")

# --- ROW 1: METRICS ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Robust Score (AUC)", 
        f"{score_live:.3f}", 
        f"{delta_score:.3f}" if stats_base is not None else None
    )

with col2:
    st.metric(
        "Max Drop (Cliff)", 
        f"{cliff_live:.1%}", 
        f"{delta_cliff:.1%}" if stats_base is not None else None,
        delta_color="inverse" # Red is bad for cliffs
    )

with col3:
    current_level = stats_live['level'].iloc[-1]
    st.metric("Current Complexity", f"Lvl {current_level}", f"{stats_live['count'].sum()} samples")

with col4:
    st.metric("Final Accuracy", f"{final_acc_live:.1%}")

st.divider()

# --- ROW 2: PRIMARY CHARTS ---
c1, c2 = st.columns([2, 1])

with c1:
    # 1. ACCURACY DECAY CURVE (Comparison)
    fig_curve = go.Figure()
    
    # Baseline Trace
    if stats_base is not None:
        fig_curve.add_trace(go.Scatter(
            x=stats_base['level'], 
            y=stats_base['accuracy'],
            mode='lines',
            name='Baseline',
            line=dict(color='gray', width=2, dash='dot')
        ))

    # Live Trace
    fig_curve.add_trace(go.Scatter(
        x=stats_live['level'], 
        y=stats_live['accuracy'],
        mode='lines+markers',
        name='Live Run',
        line=dict(color='#00CC96', width=4),
        fill='tozeroy', # Gradient feel
        fillcolor='rgba(0, 204, 150, 0.1)'
    ))

    fig_curve.update_layout(
        title="📉 Reasoning Accuracy vs. Complexity",
        xaxis_title="Complexity Level",
        yaxis_title="Accuracy",
        yaxis_range=[0, 1.05],
        template="plotly_dark",
        height=400,
        hovermode="x unified"
    )
    st.plotly_chart(fig_curve, use_container_width=True)

with c2:
    # 2. WATERFALL CHART (Visualizing the Loss)
    # We construct a waterfall showing how 100% drops to current
    
    levels = stats_live['level'].astype(str).tolist()
    accuracies = stats_live['accuracy'].tolist()
    
    # Calculate step differences
    measures = ["absolute"] + ["relative"] * (len(accuracies)-1) + ["total"]
    x_data = ["Start"] + levels[1:] + ["Final"]
    y_data = [accuracies[0]] + [accuracies[i] - accuracies[i-1] for i in range(1, len(accuracies))] + [None]
    text_data = [f"{y:.0%}" for y in y_data[:-1]] + [f"{accuracies[-1]:.0%}"]

    fig_water = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = measures,
        x = x_data,
        textposition = "outside",
        text = [f"{v*100:.1f}%" if v else "" for v in y_data],
        y = y_data,
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#EF553B"}}, # Red for drops
        increasing = {"marker":{"color":"#00CC96"}},
        totals = {"marker":{"color":"#AB63FA"}}
    ))

    fig_water.update_layout(
        title="🌊 Performance Drop (Waterfall)",
        template="plotly_dark",
        height=400,
        yaxis_title="Accuracy Change"
    )
    st.plotly_chart(fig_water, use_container_width=True)

# --- ROW 3: GRANULAR ANALYSIS ---
st.subheader("🔍 Granular Success Matrix")

if df_live is not None:
    # Create a simulated "Question ID" if not present to make the matrix work
    if 'id' not in df_live.columns:
        df_live['q_idx'] = df_live.groupby('level').cumcount()
    else:
        df_live['q_idx'] = df_live['id']

    # Pivot: Index=Question Index, Columns=Level, Values=Correct(1)/Incorrect(0)
    # We filter to show only the first 50 questions per level to avoid clutter if N is huge
    df_matrix = df_live[df_live['q_idx'] < 50].pivot(index='q_idx', columns='level', values='is_correct')
    
    fig_heat = px.imshow(
        df_matrix,
        labels=dict(x="Complexity Level", y="Sample Index", color="Correct"),
        color_continuous_scale=[[0, '#EF553B'], [1, '#00CC96']], # Red to Green
        title="Success/Fail Pattern (Green=Pass, Red=Fail)"
    )
    fig_heat.update_layout(template="plotly_dark", height=350)
    fig_heat.update_traces(showscale=False) # Hide legend for cleaner look
    st.plotly_chart(fig_heat, use_container_width=True)

# --- AUTO REFRESH LOGIC ---
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()