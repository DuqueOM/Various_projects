# clean_bank_statements

Script para **limpiar y etiquetar extractos bancarios** a partir de un archivo
CSV (`BANJIO.csv`) usando reglas basadas en expresiones regulares.

Este proyecto está pensado para trabajar todo dentro de **una sola carpeta**:

- `clean_bank_statements.py`  → script principal
- `BANJIO.csv`                → archivo de entrada esperado
- `extractos_limpios.csv`     → archivo de salida generado
- `README.md`                 → este archivo

---

## 1. Estructura y archivos

Coloca todos estos archivos en la carpeta `clean_bank_statements/`:

- `clean_bank_statements.py`
- `BANJIO.csv`
- `README.md`

Al ejecutar el script:

- Leerá `BANJIO.csv` desde **la misma carpeta**.
- Generará `extractos_limpios.csv` en **la misma carpeta**.

El código usa rutas relativas basadas en la ubicación del propio script:

```python
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "BANJIO.csv"
OUTPUT_FILE = BASE_DIR / "extractos_limpios.csv"
```

---

## 2. Requisitos

- Python 3
- Librería `pandas`:

```bash
pip install pandas
```

---

## 3. Uso

1. Asegúrate de que `BANJIO.csv` esté en la carpeta `clean_bank_statements/`.
2. Desde esa carpeta, ejecuta:

```bash
cd clean_bank_statements
python clean_bank_statements.py
```

El script:

1. Carga `BANJIO.csv` con encoding `latin1`.
2. Aplica reglas de limpieza y etiquetado sobre la columna `"Descripción"`.
3. Elimina columnas temporales internas.
4. Guarda el resultado en `extractos_limpios.csv` usando encoding `utf-8-sig`.

Verás un mensaje tipo:

```text
✅ Limpieza completada. Archivo guardado en: extractos_limpios.csv
```

---

## 4. Notas sobre las reglas

Las reglas se definen en la lista `raw_rules` del script y se compilan a
expresiones regulares. Algunas características:

- Detección de operaciones SPEI (Enviado, Recibido, Devolución) con
  extracción de beneficiario/ordenante.
- Identificación de comisiones, IVA, depósitos, entregas y retiros de recursos.
- Una regla RAW específica para patrones del tipo:
  `"(1,234.56) mxn Nro.Ref/Docto. # 1234567"`.
- Reglas especiales para ciertos textos como "TRASPASO DE SALDOS",
  "CUOTA OBRERO PATRONAL", "Nómina", etc.

El resultado final se refleja en la columna `label` del CSV.

---

## 5. Consideraciones

- Asegúrate de que la columna `"Descripción"` exista en `BANJIO.csv`. Si no,
  el script mostrará un error.
- Este script está adaptado a un formato específico de extracto (por ejemplo
  BANJIO); si cambian los formatos o textos, puede requerir ajustar o añadir
  reglas en `raw_rules`.

---

## 6. Privacidad

El CSV puede contener información financiera sensible. Asegúrate de:

- Guardar estos archivos en un lugar seguro.
- No compartir los resultados con terceros no autorizados.
- Cumplir siempre la normativa de protección de datos aplicable.
