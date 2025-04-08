import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import io
import base64
import plotly.graph_objs as go
import plotly.io as pio


fichier = "historique-production-consommation-ec-horaire.csv"
df = pd.read_csv(fichier, encoding="latin1", sep=",")

df.columns = df.columns.str.encode('latin1').str.decode('utf-8').str.strip()

rapport_html = "<html><head><meta charset='utf-8'><title>Analyse Hydro-Québec</title></head><body>"
rapport_html += "<h1>Rapport d'analyse des données de production et consommation (Hydro-Québec)</h1>"

colonnes_numeriques = df.select_dtypes(include=[np.number]).columns.tolist()

for col in df.columns:
    rapport_html += f"<h2>{col}</h2>"
    if col in colonnes_numeriques:
        minimum = df[col].min()
        maximum = df[col].max()
        quantiles = df[col].quantile([0.25, 0.5, 0.75]).to_dict()
        rapport_html += f"<p>Min: {minimum}, Max: {maximum}</p>"
        rapport_html += "<ul>" + "".join([f"<li>{int(k*100)}%: {v}</li>" for k, v in quantiles.items()]) + "</ul>"
        plt.figure()
        couleur = 'blue'
        if col.strip().startswith('-'):
            couleur = 'red'
        elif col.strip().startswith('+'):
            couleur = 'green'
        elif col.strip().startswith('='):
            couleur = 'purple'
        sns.histplot(df[col].dropna(), kde=True, bins=50, color=couleur)
        titre_graph = col
        if len(col) > 40:
            mots = col.split()
            milieu = len(mots) // 2
            titre_graph = ' '.join(mots[:milieu]) + '\n' + ' '.join(mots[milieu:])
        plt.title(f"Distribution de {titre_graph}")
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        rapport_html += f'<img src="data:image/png;base64,{image_base64}" width="800"/>'

df["mois"] = pd.to_numeric(df["mois"], errors="coerce")
df["jour"] = pd.to_numeric(df["jour"], errors="coerce")
df["Heure"] = pd.to_numeric(df["Heure"], errors="coerce")
df["Année"] = pd.to_datetime(df["Filename"], errors="coerce", dayfirst=True).dt.year

df["Datetime"] = pd.to_datetime(dict(
    year=df["Année"],
    month=df["mois"],
    day=df["jour"],
    hour=df["Heure"]
), errors='coerce')

df = df.dropna(subset=["Datetime"])
df = df.sort_values("Datetime")
df["diff"] = df["Datetime"].diff().dt.total_seconds().div(3600)

trous = df[df["diff"] > 1].copy()
trous["Début"] = trous["Datetime"] - pd.to_timedelta(trous["diff"], unit="h")

rapport_html += "<h2>Analyse des trous temporels</h2>"
rapport_html += f"<p>Nombre de trous (>1h): {len(trous)}</p>"
rapport_html += "<ul>" + "".join([
    f"<li>{row['Début']} → {row['Datetime']}</li>"
    for _, row in trous.iterrows()
]) + "</ul>"

plt.figure()
plt.plot(df["Datetime"], df["diff"].fillna(0), color='black')
plt.title("Intervalle entre les mesures\n(en heures)")
plt.xlabel("Date")
plt.ylabel("Différence en heures")
plt.tight_layout()
buffer = io.BytesIO()
plt.savefig(buffer, format='png')
plt.close()
buffer.seek(0)
image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
rapport_html += f'<img src="data:image/png;base64,{image_base64}" width="800"/>'

col_prod = "= Production brute des centrales d'HQP (MWh)"
rapport_html += f"<h2>Analyse temporelle de la {col_prod}</h2>"

df["Saison"] = df["mois"].map({
    12: "Hiver", 1: "Hiver", 2: "Hiver",
    3: "Printemps", 4: "Printemps", 5: "Printemps",
    6: "Été", 7: "Été", 8: "Été",
    9: "Automne", 10: "Automne", 11: "Automne"
})

plt.figure()
sns.boxplot(x="Heure", y=col_prod, data=df, color="purple")
plt.title("Distribution horaire de la production brute")
plt.tight_layout()
buffer = io.BytesIO()
plt.savefig(buffer, format='png')
plt.close()
buffer.seek(0)
image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
rapport_html += f'<img src="data:image/png;base64,{image_base64}" width="800"/>'

df_mois = df[df["mois"].isin(range(1, 13))]
plt.figure()
sns.boxplot(x="mois", y=col_prod, data=df_mois, color="purple")
plt.title("Distribution mensuelle de la production brute")
plt.tight_layout()
buffer = io.BytesIO()
plt.savefig(buffer, format='png')
plt.close()
buffer.seek(0)
image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
rapport_html += f'<img src="data:image/png;base64,{image_base64}" width="800"/>'

plt.figure()
sns.boxplot(x="Année", y=col_prod, data=df, color="purple")
plt.title("Distribution annuelle de la production brute")
plt.xticks(rotation=45)
plt.tight_layout()
buffer = io.BytesIO()
plt.savefig(buffer, format='png')
plt.close()
buffer.seek(0)
image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
rapport_html += f'<img src="data:image/png;base64,{image_base64}" width="800"/>'

rapport_html += "<h2>Répartition saisonnière annuelle</h2>"

for annee in sorted(df["Année"].dropna().unique()):
    data_annee = df[df["Année"] == annee]
    total_par_saison = data_annee.groupby("Saison")[col_prod].sum().reindex(["Hiver", "Printemps", "Été", "Automne"])
    if total_par_saison.notna().sum() == 4:
        plt.figure()
        plt.pie(total_par_saison, labels=total_par_saison.index, autopct='%1.1f%%')
        plt.title(f"Répartition par saison - {annee}")
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        rapport_html += f'<img src="data:image/png;base64,{image_base64}" width="500"/>'

rapport_html += "<h2>Répartition saisonnière globale</h2>"

total_global_saisons = df.groupby("Saison")[col_prod].sum().reindex(["Hiver", "Printemps", "Été", "Automne"])
if total_global_saisons.notna().sum() == 4:
    plt.figure()
    plt.pie(total_global_saisons, labels=total_global_saisons.index, autopct='%1.1f%%')
    plt.title("Répartition par saison - Toutes années")
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    rapport_html += f'<img src="data:image/png;base64,{image_base64}" width="500"/>'

rapport_html += "<h2>Évolution horaire de la consommation et production</h2>"

colonnes_mwh = [
    "= Production brute des centrales d'HQP (MWh)",
    "- Consommation des centrales d'HQP (MWh)",
    "+ Électricité reçue par HQP aux points de raccordement des centrales et des interconnexions (MWh)",
    "+ Consommation attribuable à la puissance interruptible mise à la disposition d'HQP majorée des pertes de transport (MWh)",
    "= Volume d'électricité fournie par les ressources du Producteur (MWh)",
    "- Volume des engagements du Producteur envers des tiers (MWh)",
    "= Volume d'électricité fournie par le Producteur au Distributeur (MWh)",
    "- Volume des approvisionnements hors patrimoniaux provenant d'HQP (MWh)",
    "= Volume d'électricité mobilisée par le Distributeur au titre de l'électricité patrimoniale (MWh)",
    "Volume d'électricité patrimoniale (bâtonnets affectés) (MWh)",
    "Volume d'électricité mobilisée par le Distributeur en dépassement de l'électricité patrimoniale (MWh)"
]

traces = []
for col in colonnes_mwh:
    if col in df.columns:
        traces.append(go.Scatter(x=df["Datetime"], y=df[col], mode='lines', name=col))

layout = go.Layout(
    title="Comparaison interactive des volumes d'électricité (MWh)",
    xaxis=dict(title="Date"),
    yaxis=dict(title="Énergie (MWh)"),
    height=600
)

fig = go.Figure(data=traces, layout=layout)
graph_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False)

rapport_html += "<h2>Graphique interactif des données horaires (Plotly)</h2>"
rapport_html += graph_html

rapport_html += "</body></html>"

with open("rapport_analyse_HQ01.html", "w", encoding="utf-8") as f:
    f.write(rapport_html)
