import pandas as pd

def nettoyer_virgule_vers_float(serie):
    return pd.to_numeric(serie.astype(str).str.replace(",", "."), errors="coerce")

df = pd.read_csv("0314397469_p_riode_2023-02-16_au_2025-04-05.csv", sep=';', encoding='iso-8859-1')

colonnes = [
    "Date de début", "Date de fin", "Jour", "kWh", "Montant ($)",
    "Moyenne $/j", "Moyenne kwh/j", "Température moyenne (°C)"
]

df = df[colonnes].copy()

df["Date de début"] = pd.to_datetime(df["Date de début"], errors="coerce")
df["Date de fin"] = pd.to_datetime(df["Date de fin"], errors="coerce")
df["Jour"] = pd.to_numeric(df["Jour"], errors="coerce")
df["kWh"] = nettoyer_virgule_vers_float(df["kWh"])
df["Montant ($)"] = nettoyer_virgule_vers_float(df["Montant ($)"])
df["Moyenne $/j"] = nettoyer_virgule_vers_float(df["Moyenne $/j"])
df["Moyenne kwh/j"] = nettoyer_virgule_vers_float(df["Moyenne kwh/j"])
df["Température moyenne (°C)"] = pd.to_numeric(df["Température moyenne (°C)"], errors="coerce")

df["Intervalle"] = df["Date de début"].astype(str) + " → " + df["Date de fin"].astype(str)

df.to_csv("consommation_enrichie01.csv", index=False)
