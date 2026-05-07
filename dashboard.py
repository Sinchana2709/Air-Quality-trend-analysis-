import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# -------------------------------------------------------------
# Color Theme & Styling (SaaS Redesign)
# -------------------------------------------------------------
THEME = {
    'main_bg': '#0B132B',
    'card_bg': '#1C2541',
    'border': '#3A506B',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B0B3C6',
    'cyan': '#00D4FF',
    'purple': '#7B61FF',
    'red': '#FF4C4C',
    'green': '#2ECC71',
    'gray_muted': 'rgba(176, 179, 198, 0.3)'
}

# -------------------------------------------------------------
# Data Loading & Preprocessing
# -------------------------------------------------------------
print("Loading and aggregating data for SaaS Dashboard...")
cols_to_use = [
    'City', 'Datetime', 'US_AQI', 'PM2_5_ugm3', 'Rain_mm', 
    'Wind_Speed_10m_kmh', 'Temp_2m_C', 'Festival_Period', 'Crop_Burning_Season', 'Season'
]
metro_cities = ['Delhi', 'Mumbai', 'Bengaluru', 'Chennai', 'Kolkata', 'Hyderabad', 'Ahmedabad']

try:
    df = pd.read_csv('INDIA_AQI_COMPLETE_20251126.csv', usecols=cols_to_use)
    df_metro = df[df['City'].isin(metro_cities)].copy()
    
    df_metro['Datetime'] = pd.to_datetime(df_metro['Datetime'])
    df_metro['Date'] = df_metro['Datetime'].dt.date
    df_metro['Month'] = df_metro['Datetime'].dt.to_period('M').dt.to_timestamp()
    df_metro['Year'] = df_metro['Datetime'].dt.year
    
    # Aggregation
    df_daily = df_metro.groupby(['City', 'Date', 'Month', 'Year', 'Season']).agg({
        'US_AQI': 'mean',
        'PM2_5_ugm3': 'mean',
        'Rain_mm': 'sum',
        'Wind_Speed_10m_kmh': 'mean',
        'Temp_2m_C': 'mean',
        'Festival_Period': 'max',
        'Crop_Burning_Season': 'max'
    }).reset_index()
    
    def get_aqi_category(aqi):
        if aqi <= 50: return 'Good'
        elif aqi <= 100: return 'Moderate'
        elif aqi <= 200: return 'Poor'
        else: return 'Severe'
        
    df_daily['AQI_Category'] = df_daily['US_AQI'].apply(get_aqi_category)
    print("Data loaded successfully.")
except Exception as e:
    print(f"Error loading data: {e}")
    df_daily = pd.DataFrame()

# -------------------------------------------------------------
# Dash App Initialization
# -------------------------------------------------------------
app = dash.Dash(__name__, title="AQI Analytics SaaS", suppress_callback_exceptions=True)

# -------------------------------------------------------------
# Reusable Components
# -------------------------------------------------------------
def get_base_layout(title=""):
    return go.Layout(
        title=dict(text=title, font=dict(color=THEME['text_primary'], size=16)),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=THEME['text_secondary']),
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis=dict(showgrid=False, zeroline=False, color=THEME['text_secondary']),
        yaxis=dict(showgrid=True, gridcolor=THEME['border'], zeroline=False, color=THEME['text_secondary']),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=THEME['card_bg'], font_color=THEME['text_primary'], bordercolor=THEME['border'])
    )

def create_kpi_card(title, value, color_accent):
    return html.Div(style={
        'backgroundColor': THEME['card_bg'],
        'borderRadius': '12px',
        'padding': '20px',
        'borderLeft': f'4px solid {color_accent}',
        'boxShadow': '0 8px 16px rgba(0,0,0,0.4)',
        'flex': '1',
        'minWidth': '180px',
        'margin': '10px'
    }, children=[
        html.H4(title, style={'margin': '0 0 10px 0', 'fontSize': '13px', 'color': THEME['text_secondary'], 'fontWeight': '500', 'textTransform': 'uppercase', 'letterSpacing': '1px'}),
        html.H2(value, style={'margin': '0', 'fontSize': '32px', 'fontWeight': 'bold', 'color': THEME['text_primary']})
    ])

def create_chart_wrapper(chart_id, height='400px', width='100%'):
    return html.Div(style={
        'backgroundColor': THEME['card_bg'],
        'borderRadius': '12px',
        'padding': '20px',
        'margin': '10px',
        'width': f'calc({width} - 20px)',
        'boxSizing': 'border-box',
        'boxShadow': '0 8px 16px rgba(0,0,0,0.4)'
    }, children=[
        dcc.Graph(id=chart_id, style={'height': height}, config={'displayModeBar': False})
    ])

# -------------------------------------------------------------
# Layout Definition
# -------------------------------------------------------------
if not df_daily.empty:
    years = sorted(df_daily['Year'].unique().tolist())
    seasons = sorted(df_daily['Season'].unique().tolist())

    sidebar = html.Div(style={
        'position': 'fixed', 'top': '0', 'left': '0', 'bottom': '0', 'width': '80px',
        'backgroundColor': THEME['main_bg'], 'borderRight': f'1px solid {THEME["border"]}',
        'padding': '30px 0', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'zIndex': '1000'
    }, children=[
        html.Div("AQI", style={'color': THEME['cyan'], 'fontWeight': 'bold', 'fontSize': '24px', 'marginBottom': '40px'}),
        html.A("📊", href="#trends", title="Trends", style={'color': THEME['text_secondary'], 'textDecoration': 'none', 'fontSize': '24px', 'marginBottom': '30px'}),
        html.A("🏙️", href="#city-analysis", title="City Analysis", style={'color': THEME['text_secondary'], 'textDecoration': 'none', 'fontSize': '24px', 'marginBottom': '30px'}),
        html.A("⚙️", href="#drivers", title="Drivers", style={'color': THEME['text_secondary'], 'textDecoration': 'none', 'fontSize': '24px'})
    ])

    header_filters = html.Div(style={
        'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
        'marginBottom': '20px', 'backgroundColor': THEME['card_bg'], 'padding': '15px 30px',
        'borderRadius': '12px', 'boxShadow': '0 8px 16px rgba(0,0,0,0.4)'
    }, children=[
        html.Div(style={'flex': '2', 'marginRight': '20px'}, children=[
            html.Label("Cities", style={'color': THEME['text_secondary'], 'fontSize': '12px', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='city-filter',
                options=[{'label': c, 'value': c} for c in metro_cities],
                value=['Delhi', 'Mumbai', 'Bengaluru'], # Default 3
                multi=True,
                style={'backgroundColor': THEME['main_bg'], 'color': '#000', 'border': 'none', 'borderRadius': '6px'}
            )
        ]),
        html.Div(style={'flex': '1', 'marginRight': '20px'}, children=[
            html.Label("Year", style={'color': THEME['text_secondary'], 'fontSize': '12px', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='year-filter',
                options=[{'label': 'All Years', 'value': 'All'}] + [{'label': str(y), 'value': y} for y in years],
                value='All',
                clearable=False,
                style={'backgroundColor': THEME['main_bg'], 'color': '#000', 'border': 'none', 'borderRadius': '6px'}
            )
        ]),
        html.Div(style={'flex': '1'}, children=[
            html.Label("Season", style={'color': THEME['text_secondary'], 'fontSize': '12px', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='season-filter',
                options=[{'label': 'All Seasons', 'value': 'All'}] + [{'label': s, 'value': s} for s in seasons],
                value='All',
                clearable=False,
                style={'backgroundColor': THEME['main_bg'], 'color': '#000', 'border': 'none', 'borderRadius': '6px'}
            )
        ])
    ])

    insight_box = html.Div(id='insight-box', style={
        'backgroundColor': 'rgba(0, 212, 255, 0.1)', 'border': f'1px solid {THEME["cyan"]}',
        'color': THEME['cyan'], 'padding': '15px 20px', 'borderRadius': '8px',
        'marginBottom': '20px', 'fontSize': '15px', 'fontWeight': '500', 'display': 'flex', 'alignItems': 'center'
    })

    main_content = html.Div(style={
        'marginLeft': '80px',
        'padding': '30px 40px',
        'backgroundColor': THEME['main_bg'],
        'minHeight': '100vh',
        'fontFamily': '"Inter", "Segoe UI", sans-serif'
    }, children=[
        header_filters,
        insight_box,
        
        # KPIs
        html.Div(id='kpi-cards-container', style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '10px'}),
        
        # Trend
        html.Div(id='trends', style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '10px'}, children=[
            create_chart_wrapper("main-trend-chart", width='100%', height='450px')
        ]),
        
        # City Analysis
        html.Div(id='city-analysis', style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '10px'}, children=[
            create_chart_wrapper("comparison-bar-chart", width='65%', height='350px'),
            create_chart_wrapper("mini-boxplot", width='35%', height='350px')
        ]),
        
        # Events & Drivers
        html.Div(id='drivers', style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '10px'}, children=[
            create_chart_wrapper("distribution-donut", width='33.33%', height='350px'),
            create_chart_wrapper("event-bar-chart", width='33.33%', height='350px'),
            create_chart_wrapper("driver-scatter", width='33.33%', height='350px')
        ])
    ])

    app.layout = html.Div([sidebar, main_content])

# -------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------
@app.callback(
    [Output('insight-box', 'children'),
     Output('kpi-cards-container', 'children'),
     Output('main-trend-chart', 'figure'),
     Output('comparison-bar-chart', 'figure'),
     Output('mini-boxplot', 'figure'),
     Output('distribution-donut', 'figure'),
     Output('event-bar-chart', 'figure'),
     Output('driver-scatter', 'figure')],
    [Input('city-filter', 'value'),
     Input('year-filter', 'value'),
     Input('season-filter', 'value')]
)
def update_dashboard(selected_cities, selected_year, selected_season):
    if not selected_cities or df_daily.empty:
        empty = go.Figure(layout=get_base_layout("No Data Available"))
        return "Please select at least one city.", html.Div(), empty, empty, empty, empty, empty, empty
    
    dff = df_daily[df_daily['City'].isin(selected_cities)]
    if selected_year != 'All': dff = dff[dff['Year'] == selected_year]
    if selected_season != 'All': dff = dff[dff['Season'] == selected_season]
    
    if dff.empty:
        empty = go.Figure(layout=get_base_layout("No Data in Range"))
        return "No data for this filter.", html.Div(), empty, empty, empty, empty, empty, empty

    # Global Stats
    city_avg = dff.groupby('City')['PM2_5_ugm3'].mean()
    most_polluted_city = city_avg.idxmax()
    max_pm25 = city_avg.max()
    
    severe_days = len(dff[dff['US_AQI'] > 200])
    pct_severe = (severe_days / len(dff)) * 100
    
    # 1. Insight Text
    insight_text = [
        html.Span("💡 Insight: ", style={'marginRight': '8px', 'fontSize': '18px'}),
        html.Span(f"{most_polluted_city} represents the critical focus area with an average PM2.5 of {max_pm25:.1f} µg/m³. {pct_severe:.1f}% of recorded days were classified as severe.")
    ]
    
    # 2. KPIs
    kpis = [
        create_kpi_card("Avg PM2.5", f"{dff['PM2_5_ugm3'].mean():.1f}", THEME['purple']),
        create_kpi_card("Avg AQI", f"{dff['US_AQI'].mean():.0f}", THEME['cyan']),
        create_kpi_card("Severe Days", f"{pct_severe:.1f}%", THEME['red'] if pct_severe > 10 else THEME['green']),
        create_kpi_card("Most Polluted", f"{most_polluted_city}", THEME['red']),
    ]
    
    # 3. Main Trend Chart
    trend_df = dff.groupby(['Month', 'City'])['PM2_5_ugm3'].mean().reset_index()
    fig_main = go.Figure(layout=get_base_layout("PM2.5 Long-Term Trend"))
    
    for city in selected_cities:
        city_data = trend_df[trend_df['City'] == city]
        if city_data.empty: continue
            
        is_highlight = (city == most_polluted_city)
        color = THEME['cyan'] if is_highlight else THEME['text_secondary']
        width = 3 if is_highlight else 1.5
        opacity = 1.0 if is_highlight else 0.4
        
        fig_main.add_trace(go.Scatter(
            x=city_data['Month'], y=city_data['PM2_5_ugm3'],
            mode='lines', name=city,
            line=dict(color=color, width=width, shape='spline', smoothing=0.3),
            opacity=opacity,
            hovertemplate=f"<b>{city}</b><br>Date: %{{x|%b %Y}}<br>PM2.5: %{{y:.1f}}<extra></extra>"
        ))
    fig_main.update_layout(showlegend=False) # Keep it clean
    
    # 4. Center Comparison Bar
    comp_df = city_avg.reset_index().sort_values('PM2_5_ugm3', ascending=True) # Ascending for horizontal or descending for vertical
    colors = [THEME['red'] if c == most_polluted_city else THEME['border'] for c in comp_df['City']]
    
    fig_comp = go.Figure(data=[go.Bar(
        x=comp_df['City'], y=comp_df['PM2_5_ugm3'],
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Avg PM2.5: %{y:.1f}<extra></extra>"
    )], layout=get_base_layout("City Comparison (Avg PM2.5)"))
    
    # 5. Mini Boxplot
    fig_box = go.Figure(layout=get_base_layout("PM2.5 Spread"))
    for city in selected_cities:
        c_data = dff[dff['City'] == city]['PM2_5_ugm3']
        fig_box.add_trace(go.Box(
            y=c_data, name=city, 
            marker_color=THEME['cyan'] if city == most_polluted_city else THEME['border'],
            boxpoints=False, line_width=1.5
        ))
    fig_box.update_layout(showlegend=False)
    
    # 6. Distribution Donut
    cat_counts = dff['AQI_Category'].value_counts()
    color_map = {'Good': THEME['green'], 'Moderate': THEME['cyan'], 'Poor': '#FFA500', 'Severe': THEME['red']}
    pie_colors = [color_map.get(c, THEME['border']) for c in cat_counts.index]
    
    fig_donut = go.Figure(data=[go.Pie(
        labels=cat_counts.index, values=cat_counts.values,
        hole=0.6, marker_colors=pie_colors,
        textinfo='percent', hoverinfo='label+value'
    )], layout=get_base_layout("AQI Distribution"))
    fig_donut.update_layout(margin=dict(t=50, b=10, l=10, r=10), showlegend=True, legend=dict(orientation="h", y=-0.2))
    
    # 7. Event Analysis (Bar)
    event_df = dff.groupby('Festival_Period')['PM2_5_ugm3'].mean().reset_index()
    event_df['Period'] = event_df['Festival_Period'].map({0: 'Normal Days', 1: 'Festival Days'})
    fig_event = go.Figure(data=[go.Bar(
        x=event_df['Period'], y=event_df['PM2_5_ugm3'],
        marker_color=[THEME['border'], THEME['purple']],
        width=0.4
    )], layout=get_base_layout("Event Impact"))
    
    # 8. Driver Scatter
    median_pm25 = dff['PM2_5_ugm3'].median()
    fig_scatter = go.Figure(layout=get_base_layout("Wind vs PM2.5 Drivers"))
    fig_scatter.add_trace(go.Scatter(
        x=dff['Wind_Speed_10m_kmh'], y=dff['PM2_5_ugm3'],
        mode='markers', marker=dict(color=THEME['cyan'], opacity=0.3, size=6),
        hovertemplate="Wind: %{x:.1f} km/h<br>PM2.5: %{y:.1f}<extra></extra>"
    ))
    fig_scatter.add_hline(y=median_pm25, line_dash="dash", line_color=THEME['red'], annotation_text="Median PM2.5", annotation_font_color=THEME['red'])
    fig_scatter.update_layout(xaxis_title="Wind Speed (km/h)")
    
    return insight_text, kpis, fig_main, fig_comp, fig_box, fig_donut, fig_event, fig_scatter

if __name__ == '__main__':
    app.run(debug=False, port=8050)
