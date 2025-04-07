import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Chargement des données enrichies
df = pd.read_csv("consommation_enrichie.csv")
df["Date de début"] = pd.to_datetime(df["Date de début"])
df["Date de fin"] = pd.to_datetime(df["Date de fin"])
df["Période"] = df["Date de début"].dt.strftime('%Y-%m-%d') + " au " + df["Date de fin"].dt.strftime('%Y-%m-%d')
df["Date_str"] = df["Date de début"].dt.strftime('%Y-%m-%d')
df["Température moyenne (°C)"] = pd.to_numeric(df["Température moyenne (°C)"], errors="coerce")

# Statistiques clés
correlation = df["kWh"].corr(df["Température moyenne (°C)"])
stats = {
    "Corrélation température ↔ kWh": correlation,
    "Consommation totale (kWh)": df["kWh"].sum(),
    "Montant total facturé ($)": df["Montant ($)"].sum(),
    "Montant total simulé ($)": df["Montant_simulé"].sum(),
    "Économie estimée ($)": (df["Montant ($)"] - df["Montant_simulé"]).sum()
}

# Graphique 1 : Température vs kWh
fig1 = px.scatter(df, x="Température moyenne (°C)", y="kWh",
                  hover_name="Période", trendline="ols",
                  title="Corrélation entre température moyenne et consommation (kWh)")
graph_temp_vs_kwh = fig1.to_html(full_html=False, include_plotlyjs='cdn')

# Graphique 2 : Conso dans le temps + ligne de seuil variable
fig2 = px.line(df.sort_values("Date de début"), x="Date de début", y="kWh",
               title="Évolution de la consommation dans le temps", markers=True)
fig2.add_scatter(
    x=df["Date de début"],
    y=df["Jour"] * 40,
    mode="lines+markers",
    name="Seuil (40 kWh/jour * jours)",
    line=dict(dash="dash", color="black")
)
fig2.update_layout(xaxis_title="Date", yaxis_title="Consommation (kWh)")
graph_kwh_temps = fig2.to_html(full_html=False, include_plotlyjs=False)

# Graphique 3 : Écart $ réel vs simulé
fig3 = px.line(df.sort_values("Date de début"), x="Date de début", y="Écart_facture_vs_simulé",
               title="Écart entre montant facturé et simulé", markers=True)
fig3.update_layout(xaxis_title="Date", yaxis_title="Écart ($)")
graph_ecart = fig3.to_html(full_html=False, include_plotlyjs=False)

# Graphique 4 : conso + température avec dégradé inversé
def get_conso_color(val, min_val, max_val):
    ratio = (val - min_val) / (max_val - min_val)
    if ratio < 0.33:
        return "darkgreen"
    elif ratio < 0.66:
        return "gold"
    else:
        return "darkred"

def get_temp_color(val, min_val, max_val):
    ratio = (val - min_val) / (max_val - min_val)
    r = int(255 * ratio)
    b = int(255 * (1 - ratio))
    return f"rgb({r},0,{b})"

min_kwh, max_kwh = df["kWh"].min(), df["kWh"].max()
min_temp, max_temp = df["Température moyenne (°C)"].min(), df["Température moyenne (°C)"].max()
df["couleur_kWh"] = df["kWh"].apply(lambda x: get_conso_color(x, min_kwh, max_kwh))
df["couleur_temp"] = df["Température moyenne (°C)"].apply(lambda x: get_temp_color(x, min_temp, max_temp))

fig4 = go.Figure()
fig4.add_trace(go.Bar(
    x=df["Date de début"], y=df["kWh"], name="Consommation (kWh)",
    marker_color=df["couleur_kWh"], yaxis="y1"
))
fig4.add_trace(go.Scatter(
    x=df["Date de début"], y=df["Température moyenne (°C)"],
    name="Température moyenne (°C)", mode="lines+markers",
    marker=dict(color=df["couleur_temp"]),
    line=dict(width=2), yaxis="y2"
))
fig4.update_layout(
    title="Consommation et température moyenne",
    xaxis=dict(title="Date"),
    yaxis=dict(title="kWh", side="left"),
    yaxis2=dict(title="Température (°C)", overlaying="y", side="right"),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=-0.3,
        xanchor="center", x=0.5
    ),
    template="plotly_white",
    height=500
)
graph_conso_temp_colore = fig4.to_html(full_html=False, include_plotlyjs=False)

# Rapport HTML complet
html_content = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport de consommation électrique</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body style="font-family:Arial, sans-serif; padding:20px; max-width:1000px; margin:auto;">
    <h1>Rapport de consommation électrique</h1>

    <h2>Résumé statistique</h2>
    <ul>
        {''.join(f'<li><b>{k}</b> : {round(v, 2)}</li>' for k, v in stats.items())}
    </ul>

    <h2>Analyse température ↔ consommation</h2>
    <p>La corrélation entre température moyenne et consommation électrique est de <b>{round(correlation, 2)}</b>. 
    Cela suggère une {"forte" if abs(correlation) > 0.6 else "modérée" if abs(correlation) > 0.3 else "faible"} dépendance entre température et consommation. 
    On observe que les températures plus froides sont généralement associées à une consommation plus élevée.</p>
    {graph_temp_vs_kwh}

    <h2>Consommation dans le temps</h2>
    <p>Ce graphique présente la consommation d’électricité sur l’ensemble des périodes couvertes par les données. Une ligne pointillée montre le seuil de base (40 kWh/jour multiplié par la durée).</p>
    {graph_kwh_temps}

    <h2>Écart entre facturation réelle et simulation tarifaire</h2>
    <p>Un écart positif indique une facture supérieure au tarif D simulé. Un écart négatif indique une économie par rapport au tarif de base simulé.</p>
    {graph_ecart}

    <h2>Consommation et température</h2>
    <p>Barres colorées selon l’intensité de consommation (vert = faible, rouge = élevé) et ligne de température en dégradé (bleu = froid, rouge = chaud).</p>
    {graph_conso_temp_colore}

    <footer style="margin-top:40px; font-size:small; color:gray;">
        Rapport généré automatiquement avec Python (Pandas + Plotly).
    </footer>
</body>
</html>
"""

# Sauvegarde du rapport HTML
with open("rapport_dynamique.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ Rapport standalone généré avec succès : rapport_dynamique.html")
