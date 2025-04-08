import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
import io, base64


df = pd.read_csv("consommation_enrichie01.csv")
df["Date de début"] = pd.to_datetime(df["Date de début"])
df["Date de fin"] = pd.to_datetime(df["Date de fin"])
df["Intervalle"] = df["Date de début"].dt.strftime("%Y-%m-%d") + " → " + df["Date de fin"].dt.strftime("%Y-%m-%d")
df["Température moyenne (°C)"] = pd.to_numeric(df["Température moyenne (°C)"], errors="coerce")
df["Montant ($)"] = pd.to_numeric(df["Montant ($)"].astype(str).str.replace(",", "."), errors="coerce")
df["kWh"] = pd.to_numeric(df["kWh"].astype(str).str.replace(",", "."), errors="coerce")

jours = []
for _, row in df.iterrows():
    for i in range(int(row["Jour"])):
        date = row["Date de début"] + timedelta(days=i)
        jours.append({
            "date": date,
            "Intervalle": row["Intervalle"],
            "kWh": row["kWh"] / row["Jour"],
            "Montant ($)": row["Montant ($)"] / row["Jour"],
            "Température moyenne (°C)": row["Température moyenne (°C)"]
        })

dfj = pd.DataFrame(jours)
dfj["mois"] = dfj["date"].dt.to_period("M").astype(str)
dfj["année"] = dfj["date"].dt.year
dfj["jour"] = dfj["date"].dt.dayofyear

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

fig1 = px.scatter(dfj, x="kWh", y="Montant ($)", color="Intervalle", title="Coût vs Consommation (journalier)", trendline="ols")
g1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')

dfm = dfj.groupby("mois")[["kWh", "Montant ($)"]].sum().reset_index()
fig2 = px.scatter(dfm, x="kWh", y="Montant ($)", title="Coût vs Consommation (mensuel)", trendline="ols")
g2 = fig2.to_html(full_html=False, include_plotlyjs=False)

fig3 = px.violin(
    dfj,
    y="Montant ($)",
    box=True,
    points="all",
    title="Distribution du coût journalier (densité + boîte à moustache)"
)
fig3.update_layout(yaxis_title="Montant ($)", xaxis_visible=False)
g3 = fig3.to_html(full_html=False, include_plotlyjs=False)

corrs = dfj[["kWh", "Montant ($)", "Température moyenne (°C)"]].corr().round(2)
fig4 = go.Figure(data=go.Heatmap(z=corrs.values, x=corrs.columns, y=corrs.columns, colorscale='RdBu', zmin=-1, zmax=1))
fig4.update_layout(title="Matrice de corrélation")
g4 = fig4.to_html(full_html=False, include_plotlyjs=False)

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

df_proj_mensuel = dfp.groupby("mois")[["kWh", "Montant ($)"]].sum().reset_index()
fig6 = px.line(df_proj_mensuel, x="mois", y="Montant ($)", title="Projection des coûts mensuels simulés")
g6 = fig6.to_html(full_html=False, include_plotlyjs=False)

fig7 = px.scatter(dfp, x="Température moyenne (°C)", y="kWh", title="Simulation : Température vs Consommation", trendline="ols")
g7 = fig7.to_html(full_html=False, include_plotlyjs=False)

# Ajout des saisons
def attribuer_saison(date):
    mois = date.month
    jour = date.day
    if (mois == 12 and jour >= 21) or (mois <= 3 and (mois != 3 or jour < 20)):
        return "Hiver"
    elif (mois == 3 and jour >= 20) or (4 <= mois <= 5) or (mois == 6 and jour < 21):
        return "Printemps"
    elif (mois == 6 and jour >= 21) or (7 <= mois <= 8) or (mois == 9 and jour < 22):
        return "Été"
    else:
        return "Automne"

dfj["Saison"] = dfj["date"].apply(attribuer_saison)

# Répartition saisonnière dans le HTML
rapport_saisons = "<h2>Répartition saisonnière annuelle</h2>"
col_prod = "kWh"

for annee in sorted(dfj["année"].dropna().unique()):
    data_annee = dfj[dfj["année"] == annee]
    total_par_saison = data_annee.groupby("Saison")[col_prod].sum().reindex(["Hiver", "Printemps", "Été", "Automne"])
    if total_par_saison.notna().sum() == 4:
        plt.figure()
        plt.pie(total_par_saison, labels=total_par_saison.index, autopct='%1.1f%%', startangle=90)
        plt.title(f"Répartition par saison - {annee}")
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        rapport_saisons += f'<img src="data:image/png;base64,{image_base64}" width="400" style="margin:10px;"/>'

rapport_saisons += "<h2>Répartition saisonnière globale</h2>"

total_global_saisons = dfj.groupby("Saison")[col_prod].sum().reindex(["Hiver", "Printemps", "Été", "Automne"])
if total_global_saisons.notna().sum() == 4:
    plt.figure()
    plt.pie(total_global_saisons, labels=total_global_saisons.index, autopct='%1.1f%%', startangle=90)
    plt.title("Répartition par saison - Toutes années")
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    rapport_saisons += f'<img src="data:image/png;base64,{image_base64}" width="400" style="margin:10px;"/>'



total_kwh = dfp["kWh"].sum()
total_cout = dfp["Montant ($)"].sum()
moy_annuelle = dfp.groupby("année")["Montant ($)"].sum().mean()
std_annuelle = dfp.groupby("année")["Montant ($)"].sum().std()

html = f"""
<html><head><meta charset="utf-8"><title>Rapport économique</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head>
<body style="font-family:Arial;padding:20px;max-width:1000px;margin:auto;">
<h1>Rapport économique – Analyse et Simulation</h1>

<h2>Résumé des projections</h2>
<ul>
<li><b>Coût total simulé sur 10 ans</b> : {total_cout:,.2f} $</li>
<li><b>Consommation totale simulée</b> : {total_kwh:,.2f} kWh</li>
<li><b>Coût annuel moyen</b> : {moy_annuelle:,.2f} $</li>
<li><b>Écart-type annuel</b> : {std_annuelle:,.2f} $</li>
</ul>

<h2>Analyse : Coût vs Consommation (journalier)</h2>
<p>Chaque point correspond à une journée. Légende colorée selon les périodes historiques.</p>
{g1}

<h2>Analyse mensuelle : Coût vs Consommation</h2>{g2}

<h2>Distribution des coûts journaliers</h2>
<p>Visualisation de la dispersion des montants quotidiens avec densité et boîtes à moustaches.</p>
{g3}

<h2>Corrélations entre les variables</h2>
<p>La température moyenne semble fortement liée à la consommation et donc aux coûts.</p>
{g4}

<h2>Historique vs Simulation : Évolution mensuelle</h2>
<p>Confrontation des données observées à une projection de 10 ans à climat constant + bruit aléatoire.</p>
{g5}

<h2>Projection des coûts mensuels</h2>{g6}

<h2>Corrélation température vs consommation simulée</h2>
<p>Vérifie si le lien température-consommation se maintient sur 10 ans simulés.</p>
{g7}

{rapport_saisons}

<footer style="margin-top:40px;font-size:small;color:gray;">
Rapport généré automatiquement avec Python (Pandas, NumPy, Plotly).
</footer></body></html>
"""

with open("rapport_economique.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Rapport économique standalone généré avec succès : rapport_economique.html")
