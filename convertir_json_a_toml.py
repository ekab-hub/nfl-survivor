# convertir_json_a_toml.py
import json

# Cambia esto por la ruta real de tu archivo descargado
JSON_PATH = "linear-elf-506318-m3-02353f315789.json"
OUTPUT_PATH = ".streamlit/secrets.toml"

with open(JSON_PATH, "r") as f:
    creds = json.load(f)

lines = ["[gcp_service_account]"]
for key, value in creds.items():
    if key == "private_key":
        # Comillas triples para que los saltos de línea reales no rompan el TOML
        lines.append(f'{key} = """{value}"""')
    else:
        # Escapamos comillas dobles por si acaso
        safe_value = str(value).replace('"', '\\"')
        lines.append(f'{key} = "{safe_value}"')

import os
os.makedirs(".streamlit", exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    f.write("\n".join(lines))

print(f"Listo. Archivo generado en {OUTPUT_PATH}")