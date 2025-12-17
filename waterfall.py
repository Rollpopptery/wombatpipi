import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import numpy as np
import serial_reader

# Initialize serial reader
serial_reader.init()
serial_reader.start_reading()

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Metal Detector - Waterfall Display", style={'textAlign': 'center', 'marginTop': '20px'}),
    
    html.Div([
        # Waterfall Display
        html.Div([
            html.H3("Discharge Curve - Normalized Signal"),
            dcc.Graph(id='waterfall-plot', style={'height': '500px'}),
            dcc.Interval(id='waterfall-interval', interval=100, n_intervals=0),  # Update at 10Hz
            html.Div(id='waterfall-status', style={'margin': '10px', 'fontSize': '14px', 'textAlign': 'center'})
        ], style={'marginBottom': '20px', 'padding': '20px', 'backgroundColor': '#e8f4f8', 'borderRadius': '10px'}),
        
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'})
])

# Callback for waterfall plot
@app.callback(
    [Output('waterfall-plot', 'figure'),
     Output('waterfall-status', 'children')],
    Input('waterfall-interval', 'n_intervals')
)
def update_waterfall(n):
    latest = serial_reader.get_latest()
    avg = serial_reader.get_average()
    
    if latest and avg and latest['values'] is not None:
        # Calculate deviation from running average (normalize)
        latest_values = np.array(latest['values'])
        avg_values = np.array(avg['values'])
        normalized = latest_values - avg_values
        
        fig = go.Figure()
        
        # Plot the normalized curve (sample - running average)
        fig.add_trace(go.Scatter(
            x=latest['times_us'],
            y=normalized,
            mode='lines+markers',
            name='Normalized Signal',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        # Add zero reference line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title='Discharge Curve - Normalized (Current - Running Average)',
            xaxis_title='Time (µs)',
            yaxis_title='Deviation from Average',
            template='plotly_white',
            margin=dict(l=50, r=20, t=60, b=40),
            hovermode='x unified',
            showlegend=True
        )
        
        buffer_size = len(serial_reader.get_buffer())
        status = f'Buffer: {buffer_size}/100 curves | Rate: ~10Hz | Normalized signal active'
        
        return fig, status
    else:
        # No data yet
        fig = go.Figure()
        fig.update_layout(
            title='Waiting for serial data from /dev/ttyACM0...',
            xaxis_title='Time (µs)',
            yaxis_title='Deviation from Average',
            template='plotly_white'
        )
        return fig, 'No data received yet - check serial connection'

if __name__ == '__main__':
    print("Starting Metal Detector Waterfall Display...")
    print("Connect to http://localhost:8050")
    app.run(host='0.0.0.0', port=8050, debug=True)
