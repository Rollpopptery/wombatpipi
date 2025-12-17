import dash
from dash import dcc, html, Input, Output, State
import sound

# Initialize audio
sound.init()

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Audio Synthesizer", style={'textAlign': 'center', 'marginTop': '20px'}),
    
    html.Div([
        # Beep button
        html.Div([
            html.H3("Simple Beep Test"),
            html.Button('BEEP!', id='beep-button', n_clicks=0, 
                       style={
                           'fontSize': '24px',
                           'padding': '20px 40px',
                           'margin': '10px',
                           'cursor': 'pointer',
                           'backgroundColor': '#4CAF50',
                           'color': 'white',
                           'border': 'none',
                           'borderRadius': '5px'
                       }),
            html.Div(id='beep-output', style={'margin': '10px', 'fontSize': '16px'})
        ], style={'textAlign': 'center', 'marginBottom': '40px', 'padding': '20px', 'backgroundColor': '#f0f0f0', 'borderRadius': '10px'}),
        
        # Continuous tone controls
        html.Div([
            html.H3("Continuous Tone Generator"),
            
            # Start/Stop button
            html.Button('Start Tone', id='tone-button', n_clicks=0,
                       style={
                           'fontSize': '20px',
                           'padding': '15px 30px',
                           'margin': '20px',
                           'cursor': 'pointer',
                           'backgroundColor': '#2196F3',
                           'color': 'white',
                           'border': 'none',
                           'borderRadius': '5px'
                       }),
            
            # Frequency slider
            html.Div([
                html.Label('Frequency (Hz):', style={'fontSize': '18px', 'fontWeight': 'bold'}),
                dcc.Slider(
                    id='freq-slider',
                    min=100,
                    max=2000,
                    step=10,
                    value=440,
                    marks={100: '100', 440: '440', 880: '880', 1500: '1500', 2000: '2000'},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'
                ),
            ], style={'margin': '20px', 'padding': '20px'}),
            
            # Volume slider
            html.Div([
                html.Label('Volume (%):', style={'fontSize': '18px', 'fontWeight': 'bold'}),
                dcc.Slider(
                    id='vol-slider',
                    min=0,
                    max=100,
                    step=1,
                    value=30,
                    marks={0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%'},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'
                ),
            ], style={'margin': '20px', 'padding': '20px'}),
            
            html.Div(id='tone-output', style={'margin': '20px', 'fontSize': '16px', 'textAlign': 'center'})
            
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f9f9f9', 'borderRadius': '10px'}),
        
    ], style={'maxWidth': '800px', 'margin': '0 auto', 'padding': '20px'})
])

# Callback for simple beep
@app.callback(
    Output('beep-output', 'children'),
    Input('beep-button', 'n_clicks'),
    prevent_initial_call=True
)
def play_beep(n_clicks):
    if n_clicks > 0:
        try:
            sound.beep(440, 1.0, 0.3)
            return f'Beep played! (Click #{n_clicks})'
        except Exception as e:
            return f'Error: {str(e)}'
    return ''

# Callback for tone start/stop
@app.callback(
    [Output('tone-button', 'children'),
     Output('tone-button', 'style'),
     Output('tone-output', 'children')],
    Input('tone-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_tone(n_clicks):
    if n_clicks % 2 == 1:  # Odd clicks = start
        sound.start_tone()
        style = {
            'fontSize': '20px',
            'padding': '15px 30px',
            'margin': '20px',
            'cursor': 'pointer',
            'backgroundColor': '#f44336',
            'color': 'white',
            'border': 'none',
            'borderRadius': '5px'
        }
        return 'Stop Tone', style, 'Tone is playing... adjust sliders to change sound'
    else:  # Even clicks = stop
        sound.stop_tone()
        style = {
            'fontSize': '20px',
            'padding': '15px 30px',
            'margin': '20px',
            'cursor': 'pointer',
            'backgroundColor': '#2196F3',
            'color': 'white',
            'border': 'none',
            'borderRadius': '5px'
        }
        return 'Start Tone', style, ''

# Callback for frequency changes
@app.callback(
    Output('freq-slider', 'value'),
    Input('freq-slider', 'value')
)
def update_frequency(freq):
    sound.set_frequency(freq)
    return freq

# Callback for volume changes
@app.callback(
    Output('vol-slider', 'value'),
    Input('vol-slider', 'value')
)
def update_volume(vol):
    sound.set_volume(vol / 100.0)  # Convert percentage to 0-1 range
    return vol

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
