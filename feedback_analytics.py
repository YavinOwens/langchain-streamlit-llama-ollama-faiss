"""
Feedback Analytics Dashboard
View and analyze user feedback for the LLM chat application
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

def load_feedback_data():
    """Load feedback data from file."""
    try:
        feedback_data = []
        with open("feedback_log.json", "r") as f:
            for line in f:
                if line.strip():
                    feedback_data.append(json.loads(line))
        return feedback_data
    except:
        return []

def main():
    st.title("📊 Feedback Analytics Dashboard")
    st.markdown("Analyze user feedback and response quality")
    
    # Load data
    feedback_data = load_feedback_data()
    
    if not feedback_data:
        st.warning("No feedback data available yet. Start chatting and rating responses to see analytics!")
        return
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(feedback_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # Overview Metrics
    st.header("📈 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Responses", len(df))
    with col2:
        thumbs_up = len(df[df['feedback'] == 'up'])
        st.metric("👍 Thumbs Up", thumbs_up)
    with col3:
        thumbs_down = len(df[df['feedback'] == 'down'])
        st.metric("👎 Thumbs Down", thumbs_down)
    with col4:
        satisfaction_rate = (thumbs_up / len(df)) * 100 if df else 0
        st.metric("Satisfaction Rate", f"{satisfaction_rate:.1f}%")
    
    # Charts
    st.header("📊 Analytics Charts")
    
    # Feedback over time
    daily_feedback = df.groupby(['date', 'feedback']).size().unstack(fill_value=0).reset_index()
    
    fig1 = px.line(
        daily_feedback, 
        x='date', 
        y=['up', 'down'],
        title="Feedback Trend Over Time",
        labels={'value': 'Count', 'date': 'Date'},
        color_discrete_map={'up': '#00cc96', 'down': '#ff6692'}
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Response time analysis
    st.subheader("⏱️ Response Time Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        avg_time_up = df[df['feedback'] == 'up']['response_time'].mean()
        avg_time_down = df[df['feedback'] == 'down']['response_time'].mean()
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name='👍 Thumbs Up',
            x=['Avg Response Time'],
            y=[avg_time_up],
            marker_color='#00cc96'
        ))
        fig2.add_trace(go.Bar(
            name='👎 Thumbs Down',
            x=['Avg Response Time'],
            y=[avg_time_down],
            marker_color='#ff6692'
        ))
        fig2.update_layout(title='Response Time by Feedback', yaxis_title='Seconds')
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        st.metric("Avg Time (Thumbs Up)", f"{avg_time_up:.2f}s")
        st.metric("Avg Time (Thumbs Down)", f"{avg_time_down:.2f}s")
        
        if avg_time_up < avg_time_down:
            st.success("✅ Faster responses get more thumbs up!")
        else:
            st.warning("⚠️ Consider optimizing response times")
    
    # Tool usage analysis
    st.subheader("🔧 Tool Usage Analysis")
    
    tool_feedback = df.groupby('tools_used')['feedback'].value_counts().unstack(fill_value=0)
    
    if not tool_feedback.empty:
        fig3 = px.bar(
            tool_feedback.reset_index(),
            x='tools_used',
            y=['up', 'down'],
            title="Feedback by Tool Usage",
            labels={'value': 'Count', 'tools_used': 'Tools Used'},
            barmode='group',
            color_discrete_map={'up': '#00cc96', 'down': '#ff6692'}
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    # Recent feedback
    st.header("🕐 Recent Feedback")
    
    recent_feedback = df.sort_values('timestamp', ascending=False).head(10)
    
    for _, row in recent_feedback.iterrows():
        with st.expander(f"{row['timestamp'].strftime('%Y-%m-%d %H:%M')} - {row['feedback'].upper()}"):
            st.write(f"**Response:** {row['response_text']}...")
            st.write(f"**Response Time:** {row['response_time']}s")
            st.write(f"**Tools Used:** {'Yes' if row['tools_used'] else 'No'}")
    
    # Improvement suggestions
    st.header("🔧 Improvement Suggestions")
    
    suggestions = []
    
    if satisfaction_rate < 70:
        suggestions.append("📊 Low satisfaction rate - review response quality")
    
    if avg_time_up > avg_time_down:
        suggestions.append("⚡ Optimize response times - faster responses get better feedback")
    
    thumbs_up_with_tools = len(df[(df['feedback'] == 'up') & (df['tools_used'] == True)])
    thumbs_up_without_tools = len(df[(df['feedback'] == 'up') & (df['tools_used'] == False)])
    
    if thumbs_up_with_tools > thumbs_up_without_tools:
        suggestions.append("🔧 Tool usage correlates with positive feedback - expand tool capabilities")
    
    if len(df) < 50:
        suggestions.append("📈 Collect more feedback for better insights")
    
    if suggestions:
        for suggestion in suggestions:
            st.warning(suggestion)
    else:
        st.success("🎉 Performance looks good! Keep up the great work!")

if __name__ == "__main__":
    main()
