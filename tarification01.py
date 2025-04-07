import pandas as pd

# 🔧 Paramètres de tarification Hydro-Québec
TARIF_BASE = 0.06905  # 6,905 ¢/kWh
TARIF_HAUT = 0.10652  # 10,652 ¢/kWh
KWH_PAR_JOUR_TARIF_BASE = 40

# 🔃 Fonction robuste de conversion de chaîne vers float
def nettoyer_virgule_vers_float(serie):
    return pd.to_numeric(serie.astype(str).str.replace(",", "."), errors="coerce")

# 📥 Chargement du fichier CSV (encodage Windows et séparateur ;)
fichier = "0314397469_p_riode_2023-02-16_au_2025-04-05.csv"
df = pd.read_csv(fichier, encoding="latin1", sep=";")

# 🧼 Nettoyage et conversion des colonnes
df["kWh"] = nettoyer_virgule_vers_float(df["kWh"])
df["Montant ($)"] = nettoyer_virgule_vers_float(df["Montant ($)"])
df["Jour"] = pd.to_numeric(df["Jour"], errors="coerce")
df["Date de début"] = pd.to_datetime(df["Date de début"], errors="coerce")
df["Date de fin"] = pd.to_datetime(df["Date de fin"], errors="coerce")

# ➗ Calcul du seuil de base en kWh (40 kWh/jour)
df["Seuil_kWh"] = df["Jour"] * KWH_PAR_JOUR_TARIF_BASE

# ➕ Séparation conso base vs excédent
df["kWh_base"] = df[["kWh", "Seuil_kWh"]].min(axis=1)
df["kWh_haut"] = (df["kWh"] - df["Seuil_kWh"]).clip(lower=0)

# 💸 Montant simulé avec les deux paliers
df["Montant_simulé"] = df["kWh_base"] * TARIF_BASE + df["kWh_haut"] * TARIF_HAUT

# 🔍 Écart entre la facture réelle et le calcul simulé
df["Écart_facture_vs_simulé"] = df["Montant ($)"] - df["Montant_simulé"]

# 💾 Export optionnel en CSV (si tu veux)
df.to_csv("consommation_enrichie.csv", index=False)

# ✅ Aperçu terminal
print(df[[
    "Date de début", "Date de fin", "Jour", "kWh", "Montant ($)",
    "kWh_base", "kWh_haut", "Montant_simulé", "Écart_facture_vs_simulé"
]].to_string(index=False))
