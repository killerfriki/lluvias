import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

# Cargar los datos
file_path = 'datos_coches.csv'  # Cambia esta ruta según donde tengas el archivo
df = pd.read_csv(file_path)

# Agregar la columna 'Total' que suma todas las categorías de vehículos
df['Total'] = df[['Automóviles', 'Camiones para pasajeros', 
                  'Camiones y camionetas para carga', 'Motocicletas']].sum(axis=1)

# Crear la aplicación Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Dashboard de Vehículos Registrados por Año"),
    dcc.Dropdown(
        id='tipo-dropdown',
        options=[{'label': col, 'value': col} for col in df.columns[1:]],  # Columnas de datos y 'Total'
        value='Total',  # Valor inicial
        clearable=False,
        placeholder="Seleccione el tipo de vehículo"
    ),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in sorted(df['Año'].unique())],
        value=sorted(df['Año'].unique()),  # Muestra todos los años por defecto
        multi=True,
        placeholder="Seleccione los años a visualizar"
    ),
    dcc.Graph(id='vehicle-graph')
])

# Callback para actualizar el gráfico según el tipo de vehículo y los años seleccionados
@app.callback(
    Output('vehicle-graph', 'figure'),
    [Input('tipo-dropdown', 'value'), Input('year-dropdown', 'value')]
)
def update_graph(tipo, selected_years):
    # Filtrar los datos según los años seleccionados
    df_filtered = df[df['Año'].isin(selected_years)]
    fig = px.line(
        df_filtered,
        x='Año',
        y=tipo,
        labels={'Año': 'Año', tipo: f'Registro de {tipo}'},
        title=f"Registro Anual de {tipo} por Año"
    )
    fig.update_layout(xaxis_title="Año", yaxis_title=f"Cantidad de {tipo}")
    return fig

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
