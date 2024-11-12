import requests
import pdfplumber
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import io
import os

# Base URL para los archivos PDF
url_base = "https://smn.conagua.gob.mx/tools/DATA/Climatolog%C3%ADa/Pron%C3%B3stico%20clim%C3%A1tico/Temperatura%20y%20Lluvia/PREC/"

# Lista de estados con nombres compuestos
composite_states = [
    "Baja California", "Ciudad de México", "Estado de México", "San Luis Potosí",
    "Baja California Sur", "Nuevo León", "Quintana Roo"
]

# Cargar y procesar PDFs directamente en un DataFrame
def obtener_datos_pronostico():
    all_data = []
    
    for year in range(2000, 2025):
        # Generar URL y realizar la solicitud GET
        url = f"{url_base}{year}.pdf"
        response = requests.get(url)
        
        if response.status_code == 200:
            # Abrir el PDF desde el contenido descargado
            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                page = pdf.pages[0]
                text = page.extract_text()
                
                # Procesar el texto para extraer datos
                lines = text.split('\n')
                for line in lines:
                    if any(char.isdigit() for char in line):
                        row = line.split()
                        if len(row) == 14:
                            row.append(year)
                            all_data.append(row)
                        elif len(row) > 14:
                            estado = " ".join(row[:2])
                            if estado in composite_states:
                                row = [estado] + row[2:]
                            else:
                                estado = " ".join(row[:3])
                                row = [estado] + row[3:]
                            row.append(year)
                            if len(row) == 15:
                                all_data.append(row)

    # Crear el DataFrame final
    columns = ["Estado", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic", "Anual", "Año"]
    df = pd.DataFrame(all_data, columns=columns)
    for col in columns[1:-1]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Manejar valores faltantes para 2024 en Nov y Dic
    df.loc[df['Año'] == 2024, ['Nov', 'Dic']] = None
    return df

# Obtener los datos
df = obtener_datos_pronostico()

# Filtrar datos para Ciudad de México y organizar para graficación
df_CDMX = df[df['Estado'] == 'Ciudad de México']
df_CDMX = df_CDMX.drop(columns=['Anual', 'Estado'], errors='ignore')
df_CDMX_long = df_CDMX.melt(id_vars=['Año'], var_name='Mes', value_name='Cantidad de Lluvia')

# Agregar datos de noviembre y diciembre en 2024 como promedio histórico
nov_avg = df_CDMX_long[(df_CDMX_long['Mes'] == 'Nov') & (df_CDMX_long['Año'] < 2024)]['Cantidad de Lluvia'].mean()
dic_avg = df_CDMX_long[(df_CDMX_long['Mes'] == 'Dic') & (df_CDMX_long['Año'] < 2024)]['Cantidad de Lluvia'].mean()
df_CDMX_long = pd.concat([df_CDMX_long, pd.DataFrame({'Año': [2024, 2024], 'Mes': ['Nov', 'Dic'], 'Cantidad de Lluvia': [nov_avg, dic_avg]})], ignore_index=True)

df_2024_new = pd.DataFrame({
    'Año': [2024] * 10, 
    'Mes': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct'], 
    'Cantidad de Lluvia': [0.5, 13.2, 0.1, 9.1, 34.6, 104.4, 145.8, 234.6, 159.6, 45.5]
})
df_CDMX_long = pd.concat([df_CDMX_long, df_2024_new], ignore_index=True)


# Asignar valores numéricos a los meses para ordenarlos
meses_numericos = {'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12}
df_CDMX_long['Mes_Num'] = df_CDMX_long['Mes'].map(meses_numericos)
df_CDMX_long = df_CDMX_long.sort_values(['Año', 'Mes_Num'])


# Crear la aplicación Dash
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Dashboard de Lluvias Mensuales en Ciudad de México"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in sorted(df_CDMX_long['Año'].unique())],
        value=sorted(df_CDMX_long['Año'].unique()),
        multi=True,
        placeholder="Seleccione los años a visualizar"
    ),
    dcc.Graph(id='rainfall-graph')
])

# Callback para actualizar el gráfico según los años seleccionados
@app.callback(
    Output('rainfall-graph', 'figure'),
    Input('year-dropdown', 'value')
)
def update_graph(selected_years):
    df_filtered = df_CDMX_long[df_CDMX_long['Año'].isin(selected_years)]
    fig = px.line(
        df_filtered, 
        x='Mes_Num', 
        y='Cantidad de Lluvia', 
        color='Año', 
        line_group='Año',
        labels={'Mes_Num': 'Mes', 'Cantidad de Lluvia': 'Cantidad de Lluvia (mm)'},
        title="Registro de Lluvias Mensuales"
    )
    fig.update_xaxes(tickvals=list(meses_numericos.values()), ticktext=list(meses_numericos.keys()))
    fig.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de Lluvia (mm)")
    return fig

# Lee el puerto desde la variable de entorno
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))  # Heroku proporciona el puerto en $PORT
    app.run_server(host="0.0.0.0", port=port, debug=False)