import pandas as pd

# Intentamos leer el archivo (probamos utf-8 primero, si falla usamos latin-1)
try:
    df = pd.read_csv("data/delitos_bucaramanga.csv", encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv("data/delitos_bucaramanga.csv", encoding="latin-1")

print("=" * 60)
print("DIMENSIONES DEL DATASET (filas, columnas)")
print("=" * 60)
print(df.shape)

print("\n" + "=" * 60)
print("NOMBRES DE LAS COLUMNAS")
print("=" * 60)
print(df.columns.tolist())

print("\n" + "=" * 60)
print("TIPOS DE DATOS POR COLUMNA")
print("=" * 60)
print(df.dtypes)

print("\n" + "=" * 60)
print("PRIMERAS 5 FILAS")
print("=" * 60)
print(df.head())

print("\n" + "=" * 60)
print("VALORES NULOS POR COLUMNA")
print("=" * 60)
print(df.isnull().sum())

print("\n" + "=" * 60)
print("RANGO DE AÑOS")
print("=" * 60)
print(df["AÑO_NUM"].min(), "-", df["AÑO_NUM"].max())

print("\n" + "=" * 60)
print("VALORES ÚNICOS EN COLUMNAS CLAVE")
print("=" * 60)
print("DELITO_SOLO:", df["DELITO_SOLO"].nunique(), "categorías")
print(df["DELITO_SOLO"].unique()[:15])

print("\nTIPOLOGÍA:", df["TIPOLOGÍA"].nunique(), "categorías")
print(df["TIPOLOGÍA"].unique())

print("\nCLASE_SITIO:", df["CLASE_SITIO"].nunique(), "categorías")
print(df["CLASE_SITIO"].unique())

print("\nLOCALIDAD:", df["LOCALIDAD"].nunique(), "categorías")
print(df["LOCALIDAD"].unique())

print("\nNOM_COM (comunas):", df["NOM_COM"].nunique(), "categorías")

print("\nBARRIOS_HECHO:", df["BARRIOS_HECHO"].nunique(), "barrios distintos")

print("\nEjemplo de FECHA_HECHO:", df["FECHA_HECHO"].iloc[0])
print("Ejemplo de HORA_HECHO:", df["HORA_HECHO"].iloc[0])

print("\n" + "=" * 60)
print("EDAD - muestra de valores únicos")
print("=" * 60)
print(sorted(df["EDAD"].unique())[:20])
print("Total valores únicos de EDAD:", df["EDAD"].nunique())

print("\n" + "=" * 60)
print("SEXO")
print("=" * 60)
print(df["SEXO"].unique())

print("\n" + "=" * 60)
print("MOVIL_VICTIMA")
print("=" * 60)
print(df["MOVIL_VICTIMA"].unique())

print("\n" + "=" * 60)
print("MOVIL_AGRESOR")
print("=" * 60)
print(df["MOVIL_AGRESOR"].unique())

print("\n" + "=" * 60)
print("CURSO_VIDA")
print("=" * 60)
print(df["CURSO_VIDA"].unique())

print("\n" + "=" * 60)
print("ARMAS_MEDIOS - cantidad de categorías")
print("=" * 60)
print(df["ARMAS_MEDIOS"].nunique())

print("\n" + "=" * 60)
print("CANTIDAD_UNICA - distribución de valores")
print("=" * 60)
print(df["CANTIDAD_UNICA"].value_counts())

print("\n" + "=" * 60)
print("Relación LOCALIDAD vs NUM_COM vs NOM_COM (primeras 10 combinaciones)")
print("=" * 60)
print(df[["LOCALIDAD", "NUM_COM", "NOM_COM"]].drop_duplicates().head(10))

print("\n" + "=" * 60)
print("¿Cuántos casos de delitos sexuales contra menores hay?")
print("=" * 60)
sensibles = df[df["DELITO_SOLO"].str.contains("MENOR", case=False, na=False)]
print("Total de registros:", len(sensibles))
print(sensibles["DELITO_SOLO"].value_counts())