import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta

# Fijar semilla para que los datos sean reproducibles
np.random.seed(42)

# 1. TABLA MAESTRA DE VACAS (cows)
n_cows = 150
cow_ids = [f"NZ-{str(i).zfill(4)}" for i in range(1, n_cows + 1)]
breeds = np.random.choice(["KiwiCross", "Holstein-Friesian", "Jersey"], size=n_cows, p=[0.50, 0.35, 0.15])
lactation_numbers = np.random.choice([1, 2, 3, 4, 5, 6], size=n_cows, p=[0.25, 0.25, 0.20, 0.15, 0.10, 0.05])
birth_dates = [datetime(2026, 6, 1) - timedelta(days=int(365 * (lac + 1.8) + np.random.randint(-60, 60))) for lac in lactation_numbers]

df_cows = pd.DataFrame({
    "cow_id": cow_ids,
    "breed": breeds,
    "lactation_number": lactation_numbers,
    "birth_date": [d.strftime("%Y-%m-%d") for d in birth_dates]
})

# 2. TABLA DE REGISTROS DE ORDEÑO QUINCENALES (milk_records) - 6 meses (12 controles)
dates = pd.date_range(start="2026-01-01", periods=12, freq="15D")
milk_rows = []

for cow_id, breed, lac in zip(df_cows["cow_id"], df_cows["breed"], df_cows["lactation_number"]):
    base_yield = 26.0 if breed == "Holstein-Friesian" else (23.0 if breed == "KiwiCross" else 19.5)
    base_fat = 4.1 if breed == "Holstein-Friesian" else (4.8 if breed == "KiwiCross" else 5.6)
    base_protein = 3.5 if breed == "Holstein-Friesian" else (3.9 if breed == "KiwiCross" else 4.3)
    
    chronic_risk = np.random.rand() < (0.08 * lac)
    
    for d in dates:
        daily_liters = round(np.random.normal(base_yield, 2.8), 2)
        fat_pct = round(np.random.normal(base_fat, 0.25), 2)
        protein_pct = round(np.random.normal(base_protein, 0.18), 2)
        
        if chronic_risk and np.random.rand() < 0.65:
            scc = int(np.random.lognormal(mean=5.8, sigma=0.55) * 1000)
            daily_liters = round(daily_liters * 0.82, 2)
        else:
            scc = int(np.random.lognormal(mean=4.3, sigma=0.45) * 1000)
            
        milk_rows.append([cow_id, d.strftime("%Y-%m-%d"), daily_liters, fat_pct, protein_pct, scc])

df_milk = pd.DataFrame(milk_rows, columns=["cow_id", "record_date", "daily_liters", "fat_pct", "protein_pct", "scc"])

# Introducir "datos sucios" realistas para practicar limpieza mañana
dirty_indices_null = np.random.choice(df_milk.index, size=25, replace=False)
df_milk.loc[dirty_indices_null, "daily_liters"] = np.nan

dirty_indices_neg = np.random.choice(df_milk.index, size=8, replace=False)
df_milk.loc[dirty_indices_neg, "scc"] = -999

# 3. TABLA DE EVENTOS CLÍNICOS DE MASTITIS (health_events)
high_scc = df_milk[df_milk["scc"] > 350000].sample(frac=0.70, random_state=42)
health_rows = []

treatments = [
    ("Intramammary Cloxacillin", 4, 48.50),
    ("Tylosin Injectable", 5, 65.00),
    ("Cefquinome Intramammary", 3, 55.00)
]

for idx, row in enumerate(high_scc.itertuples(), start=1):
    tx_name, withholding_days, tx_cost = treatments[np.random.randint(0, len(treatments))]
    quarter = np.random.choice(["FL", "FR", "RL", "RR"])
    health_rows.append([
        f"EVT-{str(idx).zfill(4)}",
        row.cow_id,
        row.record_date,
        "Clinical Mastitis",
        quarter,
        tx_name,
        withholding_days,
        tx_cost
    ])

df_health = pd.DataFrame(health_rows, columns=[
    "event_id", "cow_id", "diagnosis_date", "diagnosis", "affected_quarter",
    "treatment", "milk_withholding_days", "treatment_cost_nzd"
])

# Guardar archivos CSV crudos en carpeta data/
df_cows.to_csv("data/cows_raw.csv", index=False)
df_milk.to_csv("data/milk_records_raw.csv", index=False)
df_health.to_csv("data/health_events_raw.csv", index=False)

# Crear base de datos SQLite lista para consultas SQL
conn = sqlite3.connect("data/nz_dairy_herd.db")
df_cows.to_sql("cows", conn, if_exists="replace", index=False)
df_milk.to_sql("milk_records", conn, if_exists="replace", index=False)
df_health.to_sql("health_events", conn, if_exists="replace", index=False)
conn.close()

print("¡Base de datos SQLite y archivos CSV generados exitosamente en la carpeta data/!")