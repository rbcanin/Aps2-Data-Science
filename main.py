import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc

# Carregar e preparar os dados
file_path = 'MiBolsillo.csv'
df = pd.read_csv(file_path, encoding='ISO-8859-1', sep=';')
df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
df['valor'] = df['valor'].astype(str).str.strip().replace({'-': None, '': None, ' - ': None})
df['valor'] = df['valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
df['limite_total'] = pd.to_numeric(df['limite_total'], errors='coerce')
df['limite_disp'] = pd.to_numeric(df['limite_disp'], errors='coerce')
df['data'] = pd.to_datetime(df['data'], format='%d.%m.%Y', errors='coerce')
df['grupo_estabelecimento'] = df['grupo_estabelecimento'].str.encode('latin1', errors='ignore').str.decode('latin1')
df['faixa_etaria'] = pd.cut(df['idade'], bins=[0, 18, 30, 45, 60, 100], labels=['0-18', '19-30', '31-45', '46-60', '60+'])
df['mes'] = df['data'].dt.to_period('M').dt.to_timestamp()

# Cálculo para análise extra 1: limite médio por faixa etária e mês
limite_etaria_mes = df.groupby(['mes', 'faixa_etaria'])['limite_total'].mean().reset_index()

# Cálculo para análise extra 2: percentual de gasto por limite total por estado
df['percentual_gasto'] = (df['valor'] / df['limite_total']) * 100
gasto_estado = df.groupby('estado')['percentual_gasto'].mean().reset_index()

# App
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([

    html.H1("Análise de Comportamento de Consumo com Cartão de Crédito", className="text-center my-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(
            figure=px.bar(
                df.groupby('grupo_estabelecimento')['valor'].sum().sort_values().tail(10).reset_index(),
                x='valor', y='grupo_estabelecimento', orientation='h',
                title='Gasto Total por Tipo de Estabelecimento'
            )
        ), md=6),

        dbc.Col(dcc.Graph(
            figure=px.line(
                df.groupby('mes')['valor'].sum().reset_index(),
                x='mes', y='valor', title='Evolução dos Gastos Mensais'
            )
        ), md=6),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(
            figure=px.box(
                df, x='estado', y='limite_total', title='Distribuição de Limite de Crédito por Estado'
            )
        ), md=6),

        dbc.Col(dcc.Graph(
            figure=px.violin(
                df, x='sexo', y='valor', color='faixa_etaria', box=True, points='all',
                title='Comparativo de Gastos por Sexo e Faixa Etária'
            )
        ), md=6),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(
            figure=px.bar(
                df.groupby('cidade')['valor'].sum().sort_values(ascending=False).head(10).reset_index(),
                x='cidade', y='valor', title='Top 10 Cidades com Maior Volume de Compras'
            )
        ), width=12),
    ]),

    # NOVOS GRÁFICOS
    dbc.Row([
        dbc.Col(dcc.Graph(
            figure=px.line(
                limite_etaria_mes, x='mes', y='limite_total', color='faixa_etaria',
                title='Evolução do Limite de Crédito Médio por Faixa Etária',
                labels={'limite_total': 'Limite Médio (R$)', 'mes': 'Mês'}
            )
        ), md=6),

        dbc.Col(dcc.Graph(
            figure=px.bar(
                gasto_estado.sort_values(by='percentual_gasto', ascending=False),
                x='estado', y='percentual_gasto',
                title='Média de Gasto em Relação ao Limite Total por Estado',
                labels={'percentual_gasto': '% do Limite Gasto', 'estado': 'Estado'}
            )
        ), md=6),
    ])

], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)
