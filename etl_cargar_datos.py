import pandas as pd
from sqlalchemy import create_engine
from app.database import DATABASE_URL

# ============================================================
# PASO 1: CARGAR EL CSV
# ============================================================
print("Cargando CSV...")
try:
    df = pd.read_csv("data/delitos_bucaramanga.csv", encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv("data/delitos_bucaramanga.csv", encoding="latin-1")

print(f"Filas cargadas: {len(df)}")

# ============================================================
# PASO 2: LIMPIEZA
# ============================================================

# 2.1 Edad: convertir a número; los valores negativos (ej. -2) son
# errores de captura del dato original, se convierten a NULL (NaN).
df["EDAD"] = pd.to_numeric(df["EDAD"], errors="coerce")
edades_invalidas = (df["EDAD"] < 0).sum()
print(f"Edades inválidas encontradas y limpiadas (convertidas a NULL): {edades_invalidas}")
df.loc[df["EDAD"] < 0, "EDAD"] = None

# 2.2 Fecha y hora: convertir a tipos de fecha/hora reales
df["FECHA_HECHO"] = pd.to_datetime(df["FECHA_HECHO"]).dt.date
df["HORA_HECHO"] = pd.to_datetime(df["HORA_HECHO"], format="%H:%M:%S").dt.time

print("Limpieza completada.\n")

# ============================================================
# PASO 3: CONSTRUIR TABLAS DE DIMENSIÓN (con IDs asignados en Python)
# ============================================================

# --- dim_tipologia ---
tipologias = df["TIPOLOGÍA"].dropna().unique()
dim_tipologia = pd.DataFrame({
    "id": range(1, len(tipologias) + 1),
    "nombre": tipologias
})
print(f"dim_tipologia: {len(dim_tipologia)} filas")

# --- dim_delito (depende de tipologia) ---
delitos_unicos = df[["DELITO_SOLO", "ARTICULO", "DESCRIPCION_CONDUCTA", "TIPOLOGÍA"]].drop_duplicates(subset="DELITO_SOLO")
delitos_unicos = delitos_unicos.merge(dim_tipologia, left_on="TIPOLOGÍA", right_on="nombre", suffixes=("", "_tipologia"))
dim_delito = pd.DataFrame({
    "id": range(1, len(delitos_unicos) + 1),
    "nombre": delitos_unicos["DELITO_SOLO"].values,
    "articulo": delitos_unicos["ARTICULO"].values,
    "descripcion_conducta": delitos_unicos["DESCRIPCION_CONDUCTA"].values,
    "tipologia_id": delitos_unicos["id"].values,
})
print(f"dim_delito: {len(dim_delito)} filas")

# --- dim_clase_sitio ---
sitios = df["CLASE_SITIO"].dropna().unique()
dim_clase_sitio = pd.DataFrame({"id": range(1, len(sitios) + 1), "nombre": sitios})
print(f"dim_clase_sitio: {len(dim_clase_sitio)} filas")

# --- dim_arma_medio ---
armas = df["ARMAS_MEDIOS"].dropna().unique()
dim_arma_medio = pd.DataFrame({"id": range(1, len(armas) + 1), "nombre": armas})
print(f"dim_arma_medio: {len(dim_arma_medio)} filas")

# --- dim_movil (unión de MOVIL_VICTIMA y MOVIL_AGRESOR) ---
moviles = pd.concat([df["MOVIL_VICTIMA"], df["MOVIL_AGRESOR"]]).dropna().unique()
dim_movil = pd.DataFrame({"id": range(1, len(moviles) + 1), "nombre": moviles})
print(f"dim_movil: {len(dim_movil)} filas")

# --- dim_comuna ---
comunas_unicas = df[["NUM_COM", "NOM_COM"]].drop_duplicates()
dim_comuna = pd.DataFrame({
    "id": range(1, len(comunas_unicas) + 1),
    "numero": comunas_unicas["NUM_COM"].values,
    "nombre": comunas_unicas["NOM_COM"].values,
})
print(f"dim_comuna: {len(dim_comuna)} filas")

# --- dim_barrio (depende de comuna) ---
barrios_unicos = df[["BARRIOS_HECHO", "NUM_COM", "NOM_COM"]].drop_duplicates()
barrios_unicos = barrios_unicos.merge(dim_comuna, left_on=["NUM_COM", "NOM_COM"], right_on=["numero", "nombre"])
dim_barrio = pd.DataFrame({
    "id": range(1, len(barrios_unicos) + 1),
    "nombre": barrios_unicos["BARRIOS_HECHO"].values,
    "comuna_id": barrios_unicos["id_y"].values if "id_y" in barrios_unicos.columns else barrios_unicos["id"].values,
})
print(f"dim_barrio: {len(dim_barrio)} filas")

# --- dim_curso_vida ---
curso_vida_unico = df[["CURSO_VIDA", "CURSO_VIDA_ORDEN"]].drop_duplicates()
dim_curso_vida = pd.DataFrame({
    "id": range(1, len(curso_vida_unico) + 1),
    "rango": curso_vida_unico["CURSO_VIDA"].values,
    "orden": curso_vida_unico["CURSO_VIDA_ORDEN"].values,
})
print(f"dim_curso_vida: {len(dim_curso_vida)} filas")

print("\nTodas las tablas de dimensión construidas correctamente.")

# ============================================================
# PASO 4: INSERTAR TABLAS DE DIMENSIÓN EN POSTGRESQL
# ============================================================

engine = create_engine(DATABASE_URL)

print("\nLimpiando tablas existentes (por si el script se corre más de una vez)...")
with engine.begin() as conn:
    conn.exec_driver_sql("""
        TRUNCATE TABLE
            hecho_delictivo,
            dim_delito, dim_tipologia, dim_clase_sitio, dim_arma_medio,
            dim_movil, dim_barrio, dim_comuna, dim_curso_vida
        RESTART IDENTITY CASCADE;
    """)

print("Insertando tablas de dimensión...")
dim_tipologia.to_sql("dim_tipologia", engine, if_exists="append", index=False)
dim_delito.to_sql("dim_delito", engine, if_exists="append", index=False)
dim_clase_sitio.to_sql("dim_clase_sitio", engine, if_exists="append", index=False)
dim_arma_medio.to_sql("dim_arma_medio", engine, if_exists="append", index=False)
dim_movil.to_sql("dim_movil", engine, if_exists="append", index=False)
dim_comuna.to_sql("dim_comuna", engine, if_exists="append", index=False)
dim_barrio.to_sql("dim_barrio", engine, if_exists="append", index=False)
dim_curso_vida.to_sql("dim_curso_vida", engine, if_exists="append", index=False)

print("Tablas de dimensión insertadas correctamente en PostgreSQL.")

# ============================================================
# PASO 5: CONSTRUIR LA TABLA DE HECHOS
# ============================================================
print("\nConstruyendo tabla de hechos...")

# 5.1 Mapear cada delito a su ID
hechos = df.merge(
    dim_delito[["id", "nombre"]].rename(columns={"id": "delito_id", "nombre": "DELITO_SOLO"}),
    on="DELITO_SOLO", how="left"
)

# 5.2 Mapear clase de sitio
hechos = hechos.merge(
    dim_clase_sitio[["id", "nombre"]].rename(columns={"id": "clase_sitio_id", "nombre": "CLASE_SITIO"}),
    on="CLASE_SITIO", how="left"
)

# 5.3 Mapear arma/medio
hechos = hechos.merge(
    dim_arma_medio[["id", "nombre"]].rename(columns={"id": "arma_medio_id", "nombre": "ARMAS_MEDIOS"}),
    on="ARMAS_MEDIOS", how="left"
)

# 5.4 Mapear móvil de la víctima
hechos = hechos.merge(
    dim_movil[["id", "nombre"]].rename(columns={"id": "movil_victima_id", "nombre": "MOVIL_VICTIMA"}),
    on="MOVIL_VICTIMA", how="left"
)

# 5.5 Mapear móvil del agresor
hechos = hechos.merge(
    dim_movil[["id", "nombre"]].rename(columns={"id": "movil_agresor_id", "nombre": "MOVIL_AGRESOR"}),
    on="MOVIL_AGRESOR", how="left"
)

# 5.6 Mapear barrio (a través de comuna, porque un mismo nombre de barrio
# puede repetirse en más de una comuna, como vimos en el conteo de dim_barrio)
hechos = hechos.merge(
    dim_comuna.rename(columns={"id": "comuna_id_temp"}),
    left_on=["NUM_COM", "NOM_COM"], right_on=["numero", "nombre"], how="left"
)
hechos = hechos.merge(
    dim_barrio[["id", "nombre", "comuna_id"]].rename(columns={"id": "barrio_id", "nombre": "BARRIOS_HECHO"}),
    left_on=["BARRIOS_HECHO", "comuna_id_temp"], right_on=["BARRIOS_HECHO", "comuna_id"], how="left"
)

# 5.7 Mapear curso de vida
hechos = hechos.merge(
    dim_curso_vida[["id", "rango"]].rename(columns={"id": "curso_vida_id", "rango": "CURSO_VIDA"}),
    on="CURSO_VIDA", how="left"
)

# 5.8 Armar la tabla final con los nombres de columna que espera la base de datos
hecho_delictivo = pd.DataFrame({
    "fecha_hecho": hechos["FECHA_HECHO"],
    "hora_hecho": hechos["HORA_HECHO"],
    "anio": hechos["AÑO_NUM"],
    "mes": hechos["MES_NUM"],
    "dia": hechos["DIA_NUM"],
    "dia_nombre": hechos["DIA_NOMBRE"],
    "dia_nombre_orden": hechos["DIA_NOMBRE_ORDEN"],
    "rango_horario": hechos["RANGO_HORARIO"],
    "rango_horario_orden": hechos["RANGO_HORARIO_ORDEN"],
    "edad": hechos["EDAD"].astype("Int64"),  # Int64 (con mayúscula) permite NULLs, a diferencia de int normal
    "sexo": hechos["SEXO"],
    "cantidad": hechos["CANTIDAD_UNICA"],
    "delito_id": hechos["delito_id"],
    "clase_sitio_id": hechos["clase_sitio_id"],
    "arma_medio_id": hechos["arma_medio_id"],
    "movil_victima_id": hechos["movil_victima_id"],
    "movil_agresor_id": hechos["movil_agresor_id"],
    "barrio_id": hechos["barrio_id"],
    "curso_vida_id": hechos["curso_vida_id"],
})

# 5.9 Verificación de integridad: ¿algún registro quedó sin poder
# relacionarse con una dimensión? (esto no debería pasar, pero lo
# verificamos explícitamente en vez de asumir que todo salió bien)
columnas_id = ["delito_id", "clase_sitio_id", "arma_medio_id", "barrio_id"]
nulos_criticos = hecho_delictivo[columnas_id].isnull().sum()
print("Valores NULL en IDs obligatorios (debería ser 0 en todas):")
print(nulos_criticos)

print(f"\nTotal de hechos construidos: {len(hecho_delictivo)}")

# ============================================================
# PASO 6: INSERTAR LA TABLA DE HECHOS EN POSTGRESQL
# ============================================================
print("\nInsertando tabla de hechos (puede tardar uno o dos minutos)...")
hecho_delictivo.to_sql(
    "hecho_delictivo", engine, if_exists="append", index=False,
    chunksize=5000, method="multi"
)
print("¡Carga completa! La tabla hecho_delictivo ya tiene los 130.202 registros.")