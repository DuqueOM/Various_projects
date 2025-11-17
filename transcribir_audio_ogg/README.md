# transcribir_audio_ogg

Pequeño proyecto en Python para:

1. Tomar audios en (casi) cualquier formato.
2. Convertirlos a **MP3** con la mejor calidad posible (ffmpeg + libmp3lame).
3. **Transcribir** el contenido de audio a texto usando **Whisper**.

Todo se organiza dentro de una sola carpeta con dos subcarpetas principales:

- `audios/`    → aquí colocas los audios de entrada.
- `Descargas/` → aquí se guardan los resultados:
  - `<nombre>.mp3` : audio convertido a MP3.
  - `<nombre>.txt` : transcripción de ese audio.

> ⚠️ Usa este programa sólo para audios tuyos o para los que tengas permiso. Respeta siempre la privacidad y los derechos de autor.

---

## 1. Estructura del proyecto

Dentro de `transcribir_audio_ogg/` encontrarás:

- `transcribir_audio_ogg.py`  
  Script principal que convierte y transcribe audios.
- `audios/`  
  Carpeta donde debes colocar los archivos de audio originales.
- `Descargas/`  
  Carpeta donde se guardan los MP3 y los `.txt` con las transcripciones.
- `README.md`  
  Este documento.

Si las carpetas `audios` y `Descargas` no existen al ejecutar el script, se crearán automáticamente.

---

## 2. Requisitos

### 2.1. Python y librerías

Asegúrate de tener Python 3 instalado y luego instala las librerías necesarias:

```bash
pip install -U openai-whisper
```

> La librería `openai-whisper` instalará también `torch` como dependencia (puede tardar un poco). Si lo prefieres, puedes instalar `torch` por separado según tu plataforma/CPU/GPU.

### 2.2. ffmpeg

El script usa `ffmpeg` para convertir a MP3.

- Debe estar instalado y accesible en el PATH.
- En muchas distribuciones Linux bastará con:

```bash
sudo apt install ffmpeg
```

En Windows puedes instalar FFmpeg desde la página oficial y añadir la carpeta `bin` a la variable de entorno `PATH`.

---

## 3. Cómo usarlo

1. Copia tus archivos de audio a la carpeta `audios/`.
   - Se aceptan extensiones comunes: `.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`, `.aac`, `.wma`, `.opus`, `.webm`, etc.
2. Ejecuta el script desde la carpeta del proyecto:

```bash
cd transcribir_audio_ogg
python transcribir_audio_ogg.py
```

3. El script hará lo siguiente:
   - Creará (si no existen) las carpetas `audios` y `Descargas`.
   - Buscará todos los archivos de audio en `audios/` con extensiones conocidas.
   - Convertirá cada archivo a MP3 con ffmpeg, guardando el resultado en `Descargas/`.
   - Cargará un modelo Whisper y transcribirá cada MP3.
   - Guardará la transcripción en un archivo `<nombre>.txt` dentro de `Descargas/`.

Al final verás un mensaje indicando que el proceso ha terminado y podrás revisar la carpeta `Descargas`.

---

## 4. Configuración del modelo Whisper

Por defecto, el script carga el modelo Whisper `medium`:

- Este modelo ofrece una buena calidad de transcripción con un coste razonable de memoria.

Si quieres usar otro modelo (por ejemplo, `small`, `base`, `large`), puedes definir la variable de entorno `WHISPER_MODEL` antes de ejecutar el script:

```bash
export WHISPER_MODEL=small
python transcribir_audio_ogg.py
```

En Windows (CMD):

```bat
set WHISPER_MODEL=small
python transcribir_audio_ogg.py
```

Modelos más grandes suelen dar mejor calidad pero requieren más memoria y tardan más.

---

## 5. Notas y recomendaciones

- Si no se encuentran audios en la carpeta `audios/`, el script lo indicará y terminará sin error.
- Si `ffmpeg` no está instalado o no se encuentra en el PATH, la conversión a MP3 fallará y el script lo avisará.
- Puedes forzar un idioma de transcripción editando la variable `language` en `transcribir_audio_ogg.py` (por ejemplo, `'es'` para español, `'en'` para inglés, etc.).

Ejemplo dentro del script:

```python
language = None  # o 'es', 'en', etc.
```

- Si quieres limpiar las transcripciones o procesarlas más adelante (por ejemplo, resumirlas), puedes usar los `.txt` generados como entrada a otros scripts o herramientas.

---

## 6. Consideraciones legales y de privacidad

1. **Propiedad intelectual**  
   Utiliza este script únicamente con audios que te pertenezcan o para los que tengas permiso explícito de uso y procesamiento.

2. **Privacidad**  
   Si los audios contienen información sensible (conversaciones privadas, datos personales, etc.), asegúrate de manejar los archivos y transcripciones de forma segura y conforme a la legislación aplicable.

3. **Sin garantías**  
   Este proyecto se proporciona "tal cual" (*as is*), sin garantías de ningún tipo. El autor no se hace responsable del uso que se haga de esta herramienta.

---

## 7. Resumen rápido

1. Instala dependencias: `openai-whisper` y `ffmpeg`.
2. Copia tus audios a `audios/`.
3. Ejecuta `python transcribir_audio_ogg.py` desde la carpeta del proyecto.
4. Revisa los MP3 convertidos y los `.txt` de transcripción en `Descargas/`.

Con eso tendrás un flujo sencillo para transformar y transcribir tus audios dentro de una sola carpeta organizada.
