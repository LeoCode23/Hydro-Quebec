import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta

# Chargement
df = pd.read_csv("consommation_enrichie.csv")
df["Date de début"] = pd.to_datetime(df["Date de début"])
df["Date de fin"] = pd.to_datetime(df["Date de fin"])
df["Température moyenne (°C)"] = pd.to_numeric(df["Température moyenne (°C)"], errors="coerce")

# Données journalières historiques
jours = []
for _, row in df.iterrows():
    for i in range(int(row["Jour"])):
        date = row["Date de début"] + timedelta(days=i)
        jours.append({
            "date": date,
            "kWh": row["kWh"] / row["Jour"],
            "Montant ($)": row["Montant ($)"] / row["Jour"],
            "Température moyenne (°C)": row["Température moyenne (°C)"]
        })
dfj = pd.DataFrame(jours)
dfj["mois"] = dfj["date"].dt.to_period("M").astype(str)
dfj["année"] = dfj["date"].dt.year
dfj["jour"] = dfj["date"].dt.dayofyear

# Simulation réaliste 10 ans
jours_proj = pd.date_range("2025-04-06", periods=3650, freq="D")
moy_par_jour = dfj.groupby("jour").agg({
    "kWh": "mean",
    "Montant ($)": "mean",
    "Température moyenne (°C)": "mean"
}).reindex(range(1, 367)).fillna(method="ffill")

proj = []
for i, date in enumerate(jours_proj):
    jour = date.timetuple().tm_yday
    base = moy_par_jour.loc[jour]
    bruit = np.random.normal(0, 0.05)
    proj.append({
        "date": date,
        "kWh": base["kWh"] * (1 + bruit),
        "Montant ($)": base["Montant ($)"] * (1 + bruit),
        "Température moyenne (°C)": base["Température moyenne (°C)"] + np.random.normal(0, 1)
    })
dfp = pd.DataFrame(proj)
dfp["mois"] = dfp["date"].dt.to_period("M").astype(str)
dfp["année"] = dfp["date"].dt.year
dfp["jour"] = dfp["date"].dt.dayofyear

# Graphique 1 : Coût vs consommation (journalier)
fig1 = px.scatter(dfj, x="kWh", y="Montant ($)", title="Coût vs Consommation (journalier)", trendline="ols")
g1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')

# Graphique 2 : Coût vs consommation (mensuel)
dfm = dfj.groupby("mois")[["kWh", "Montant ($)"]].sum().reset_index()
fig2 = px.scatter(dfm, x="kWh", y="Montant ($)", title="Coût vs Consommation (mensuel)", trendline="ols")
g2 = fig2.to_html(full_html=False, include_plotlyjs=False)

# Graphique 3 : Histogramme du coût journalier
fig3 = px.violin(
    dfj,
    y="Montant ($)",
    box=True,
    points="all",
    title="Distribution du coût journalier (densité + boîte à moustache)"
)
fig3.update_layout(yaxis_title="Montant ($)", xaxis_visible=False)
g3 = fig3.to_html(full_html=False, include_plotlyjs=False)


# Graphique 4 : Matrice de corrélation
corrs = dfj[["kWh", "Montant ($)", "Température moyenne (°C)"]].corr().round(2)
fig4 = go.Figure(data=go.Heatmap(z=corrs.values, x=corrs.columns, y=corrs.columns, colorscale='RdBu', zmin=-1, zmax=1))
fig4.update_layout(title="Matrice de corrélation")
g4 = fig4.to_html(full_html=False, include_plotlyjs=False)

# Graphique 5 : Conso + Température mensuelle (historique vs simulation)
dfj["source"] = "Historique"
dfp["source"] = "Projection"
df_all = pd.concat([dfj, dfp])
df_all_mensuel = df_all.groupby(["mois", "source"])[["kWh", "Montant ($)", "Température moyenne (°C)"]].mean().reset_index()

fig5 = go.Figure()
for src, couleur in [("Historique", "green"), ("Projection", "red")]:
    df_src = df_all_mensuel[df_all_mensuel["source"] == src]
    fig5.add_trace(go.Bar(x=df_src["mois"], y=df_src["kWh"], name=f"Conso {src}", marker_color=couleur))
    fig5.add_trace(go.Scatter(x=df_src["mois"], y=df_src["Température moyenne (°C)"],
                              name=f"Temp {src}", yaxis="y2", mode="lines+markers"))
fig5.update_layout(
    title="Consommation et température (mensuelle, réel vs simulé)",
    xaxis_title="Mois", yaxis=dict(title="kWh"), yaxis2=dict(title="Température (°C)", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
    template="plotly_white", barmode="group"
)
g5 = fig5.to_html(full_html=False, include_plotlyjs=False)

# Graphique 6 : Projection seule (variation réaliste mensuelle)
df_proj_mensuel = dfp.groupby("mois")[["kWh", "Montant ($)"]].sum().reset_index()
fig6 = px.line(df_proj_mensuel, x="mois", y="Montant ($)", title="Projection des coûts mensuels simulés")
g6 = fig6.to_html(full_html=False, include_plotlyjs=False)

# Graphique 7 : Consommation vs température projetée
fig7 = px.scatter(dfp, x="Température moyenne (°C)", y="kWh", title="Simulation : Température vs Consommation", trendline="ols")
g7 = fig7.to_html(full_html=False, include_plotlyjs=False)

# Résumés
total_kwh = dfp["kWh"].sum()
total_cout = dfp["Montant ($)"].sum()
moy_annuelle = dfp.groupby("année")["Montant ($)"].sum().mean()
std_annuelle = dfp.groupby("année")["Montant ($)"].sum().std()

# Rapport HTML
html = f"""
<html><head><meta charset="utf-8"><title>Rapport économique</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head>
<body style="font-family:Arial;padding:20px;max-width:1000px;margin:auto;">
<h1>Rapport économique – Analyse et Simulation</h1>
<h2>Résumé des projections</h2>
<ul>
<li>Coût total simulé sur 10 ans : <b>{total_cout:.2f} $</b></li>
<li>Consommation totale simulée : <b>{total_kwh:.2f} kWh</b></li>
<li>Coût annuel moyen : <b>{moy_annuelle:.2f} $</b></li>
<li>Écart-type annuel : <b>{std_annuelle:.2f} $</b></li>
</ul>
<h2>Coût vs consommation (journalier)</h2>{g1}
<h2>Coût vs consommation (mensuel)</h2>{g2}
<h2>Distribution du coût journalier</h2>{g3}
<h2>Corrélations entre variables</h2>{g4}
<h2>Consommation et température (réel vs simulé)</h2>{g5}
<h2>Projection des coûts mensuels</h2>{g6}
<h2>Température vs consommation (simulation)</h2>{g7}
<footer style="margin-top:40px;font-size:small;color:gray;">
Rapport généré automatiquement avec Python, Pandas et Plotly.
</footer></body></html>
"""

with open("rapport_economique.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Rapport économique standalone généré avec succès : rapport_economique.html")
