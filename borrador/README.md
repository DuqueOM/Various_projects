# borrador

Versión **borrador/experimental** del limpiador de extractos bancarios.

Funciona de forma muy similar a `clean_bank_statements.py`, pero mantiene
información adicional sobre cómo se etiquetó cada fila:

- `label`  → etiqueta asignada mediante las reglas.
- `method` → regla que disparó la coincidencia.
- `score`  → puntuación (ej. 100 si hubo match directo, 0 si no hubo).

Este proyecto también está pensado para trabajar todo dentro de **una sola
carpeta**:

- `borrador.py`            → script principal
- `BANJIO.csv`             → archivo de entrada esperado
- `extractos_limpios.csv`  → archivo de salida generado
- `README.md`              → este archivo

---

## 1. Estructura y archivos

Coloca todos estos archivos en la carpeta `borrador/`:

- `borrador.py`
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

1. Asegúrate de que `BANJIO.csv` esté en la carpeta `borrador/`.
2. Desde esa carpeta, ejecuta:

```bash
cd borrador
python borrador.py
```

El script:

1. Carga `BANJIO.csv` con encoding `latin1`.
2. Aplica reglas de limpieza y etiquetado sobre la columna `"Descripción"`.
3. Mantiene columnas auxiliares:
   - `<Descripción>_norm` y `<Descripción>_raw` mientras se aplican las reglas.
   - `label`, `method`, `score` para inspeccionar cómo se realizó el match.
4. Guarda el resultado en `extractos_limpios.csv` usando encoding `utf-8-sig`.

Verás un mensaje tipo:

```text
✅ Limpieza completada. Archivo guardado en: extractos_limpios.csv
```

---

## 4. Notas sobre las reglas

Las reglas en `borrador.py` son muy similares a las de `clean_bank_statements`,
con énfasis en:

- Detección de patrones SPEI, devoluciones, entregas y retiros de recursos.
- Detección de comisiones, IVA, depósitos y servicios (ej. TELMEX, Nómina).
- Reglas RAW para casos donde se desea conservar el texto original de
  la descripción como etiqueta.

La información en `method` y `score` resulta útil para depurar o ajustar las
reglas en el futuro.

---

## 5. Consideraciones

- Asegúrate de que la columna `"Descripción"` exista en `BANJIO.csv`; si no,
  el script mostrará un error.
- Esta versión es útil cuando quieres analizar **cómo** se están aplicando las
  reglas y no sólo el resultado final.

---

## 6. Privacidad

El CSV puede contener información financiera sensible. Asegúrate de:

- Guardar estos archivos en un lugar seguro.
- No compartir los resultados con terceros no autorizados.
- Cumplir siempre la normativa de protección de datos aplicable.
