import pandas as pd
import numpy as np
import sqlite3

# 1. CARGAR LOS DATOS CRUDOS (RAW)
df_cows = pd.read_csv("data/cows_raw.csv")
df_milk = pd.read_csv("data/milk_records_raw.csv")
df_health = pd.read_csv("data/health_events_raw.csv")

print("--- AUDITORÍA INICIAL DE DATOS CRUDOS ---")
print("Valores nulos por columna en df_milk:")
print(df_milk.isnull().sum())
print("\nRegistros con SCC negativo (error de sensor):", (df_milk["scc"] < 0).sum())

# 2. LIMPIEZA DE ERRORES DE SENSOR EN SCC (-999)
# Primero convertimos los valores negativos (-999) en valores nulos reales (NaN)
df_milk["scc"] = df_milk["scc"].replace(-999, np.nan)

# Reemplazamos esos SCC faltantes con la MEDIANA de SCC de cada vaca individual
# (Usamos mediana y no promedio porque el SCC es asimétrico / skewed)
df_milk["scc"] = df_milk["scc"].fillna(
    df_milk.groupby("cow_id")["scc"].transform("median")
)

# 3. LIMPIEZA DE LITROS DIARIOS FALTANTES (daily_liters = NaN)
# Imputamos los litros faltantes usando el PROMEDIO histórico de esa misma vaca
df_milk["daily_liters"] = (
    df_milk["daily_liters"]
    .fillna(df_milk.groupby("cow_id")["daily_liters"].transform("mean"))
    .round(2)
)

# 4. INGENIERÍA DE CARACTERÍSTICAS (FEATURE ENGINEERING - CREAR COLUMNAS ÚTILES)
# Creamos una columna clínica que clasifica el estado de la ubre según estándares NZ
df_milk["udder_status"] = np.where(
    df_milk["scc"] > 200000, "Subclinical Risk", "Healthy"
)

# Calculamos los kilogramos totales de sólidos lácteos (Grasa + Proteína), que es como pagan en NZ
# Fórmula estándar: Litros * (%Grasa + %Proteína) / 100
df_milk["milk_solids_kg"] = (
    df_milk["daily_liters"] * (df_milk["fat_pct"] + df_milk["protein_pct"]) / 100
).round(2)

print("\n--- AUDITORÍA DESPUÉS DE LA LIMPIEZA ---")
print("Valores nulos restantes en df_milk:")
print(df_milk.isnull().sum())
print("\nPrimeras 5 filas de la tabla limpia:")
print(df_milk.head())

# 5. GUARDAR DATOS LIMPIOS EN CSV Y ACTUALIZAR BASE DE DATOS SQLITE
df_milk.to_csv("data/milk_records_clean.csv", index=False)

conn = sqlite3.connect("data/nz_dairy_herd.db")
df_milk.to_sql("milk_records_clean", conn, if_exists="replace", index=False)
conn.close()

print(
    "\n¡Limpieza completada! Archivo 'milk_records_clean.csv' y tabla SQL 'milk_records_clean' creados."
)
