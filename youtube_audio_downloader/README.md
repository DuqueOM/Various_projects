# YouTube / YouTube Music Audio Downloader

Script sencillo en Python para descargar **audio** desde YouTube y YouTube Music, usando `yt-dlp` y `ffmpeg`.

- Acepta **URLs individuales**, **playlists** y **listas de URLs**.
- Descarga siempre el **mejor audio disponible**.
- Convierte a audio (MP3 por defecto, configurable) en **alta calidad**.
- Pide a `ffmpeg` que escriba metadatos (título, artista, álbum) y que **incruste la portada** cuando sea posible.
- Guarda un fichero `.info.json` por vídeo con metadatos extendidos (incluyendo letras si el extractor las expone).

> ⚠️ **Uso responsable:** Usa este script sólo para contenido propio o con permiso. Respeta los derechos de autor y los Términos de Servicio de cada plataforma.

---

## 1. Requisitos

### 1.1. Python y yt-dlp

Instala `yt-dlp` (recomendado desde pip):

```bash
pip install -U yt-dlp
```

### 1.2. ffmpeg

El script usa `ffmpeg` para convertir el audio y escribir metadatos:

- Debe estar instalado y accesible en el `PATH`.
- En muchas distribuciones Linux basta con:

```bash
sudo apt install ffmpeg
```

En Windows puedes instalarlo desde la página oficial de FFmpeg y añadir la carpeta `bin` al PATH.

---

## 2. Archivos del proyecto

En esta carpeta tienes:

- `Download_youtube.py`  
  Script principal que descarga y convierte audio desde YouTube / YouTube Music.
- `README.md` (este archivo)  
  Documentación de uso y advertencias.

Puedes ejecutar el script así:

```bash
python Download_youtube.py
```

> Recomendación: crea y usa un entorno virtual (virtualenv, venv, conda, etc.) para gestionar dependencias.

---

## 3. Configuración básica del script

Abre `Download_youtube.py` en tu editor y localiza el bloque marcado como **CONFIGURACIÓN**.

### 3.1. Lista de URLs en el propio script

```python
urls = [
    "https://www.youtube.com/watch?v=Z1c3SXLmAUg&list=RDZ1c3SXLmAUg&start_radio=1",
    # Ejemplos:
    # "https://www.youtube.com/watch?v=VIDEO_ID",
    # "https://music.youtube.com/watch?v=VIDEO_ID",
    # "https://www.youtube.com/playlist?list=PLAYLIST_ID",
]
```

Puedes añadir tantas URLs como quieras:

- Vídeos de YouTube.
- Vídeos de YouTube Music.
- Playlists completas.

### 3.2. Archivo de texto con URLs (opcional)

El script está pensado para trabajar, por defecto, con un archivo llamado
`links_audio.txt` dentro de la carpeta `youtube_audio_downloader`:

```python
urls_from_file = os.path.join(BASE_DIR, "links_audio.txt")
```

Si quieres usar otro archivo diferente, puedes cambiar esta ruta. En todos los
casos, el script leerá ese archivo, tomará **una URL por línea** y las añadirá
a la lista `urls`.

- Las líneas vacías o que empiezan por `#` se ignoran.

### 3.3. Carpeta de salida

Por defecto, el script usa una subcarpeta llamada `Descargas` dentro del propio
proyecto `youtube_audio_downloader`:

```python
output_folder = os.path.join(BASE_DIR, "Descargas")
```

Puedes cambiarla por la carpeta donde quieras guardar tu música si lo deseas.

### 3.4. Formato de salida y calidad

```python
audio_format = "mp3"
mp3_quality = "320"  # "192", "256" o "320" para MP3
```

- `audio_format`:
  - `"mp3"` (por defecto) → buena compatibilidad con casi todos los reproductores.
  - `"m4a"` → recomendable si quieres menos pérdida (se aprovecha mejor el stream original de YouTube).
- `mp3_quality` (kbps) se usa sólo cuando `audio_format == "mp3"`.

**Máxima calidad recomendada:**

- Para máxima fidelidad, pon `audio_format = "m4a"`.  
  En ese caso, `yt-dlp` extraerá el audio en un contenedor muy cercano al original de YouTube/YouTube Music.

---

## 4. Qué metadatos se guardan

El script está configurado con estos postprocesadores de `yt-dlp`:

- `FFmpegExtractAudio`  
  Extrae el mejor audio disponible y lo convierte al formato elegido (`mp3` o `m4a`).

- `FFmpegMetadata`  
  Pide a `ffmpeg` que escriba metadatos en el archivo final (título, artista, álbum, etc.) basándose en la información que proporciona `yt-dlp`.

- `EmbedThumbnail`  
  Intenta incrustar la miniatura del vídeo como **portada** en el archivo de audio.

Además, se activa:

- `writethumbnail = True`  → guarda la miniatura en un fichero aparte.
- `writeinfojson = True`   → guarda un archivo `.info.json` con todos los metadatos que conoce `yt-dlp` sobre ese vídeo.

### Letras (lyrics)

- Algunos extractores de `yt-dlp` pueden incluir campos relacionados con letras o descripciones largas dentro del `.info.json`.
- **YouTube / YouTube Music normalmente no ofrecen letras completas** de forma estructurada como un campo específico, así que:
  - No se puede garantizar que haya letras.
  - Si el extractor proporciona letras o información similar, aparecerá en el `.info.json`, **no** como una etiqueta ID3 estándar.

Si necesitas letras dentro de las etiquetas del archivo (ID3, Vorbis, etc.), puedes usar herramientas adicionales (por ejemplo, editores de tags o scripts basados en `mutagen`) apoyándote en el `.info.json` como fuente de datos.

---

## 5. Ejemplos de uso

### 5.1. Ejecutar con las URLs definidas en el script

Simplemente:

```bash
python Download_youtube.py
```

El script:

1. Construye la lista de URLs: `urls` + (opcional) `urls_from_file`.
2. Usa `yt-dlp` para descargar el mejor audio.
3. Convierte al formato configurado y escribe metadatos/portada.
4. Muestra el progreso de cada descarga en la consola.

### 5.2. Archivo de lista de reproducción personalizado

Crea un archivo `lista_urls.txt` junto al script:

```text
# Comentarios permitidos
https://www.youtube.com/watch?v=AAA
https://music.youtube.com/watch?v=BBBB
https://www.youtube.com/playlist?list=CCCC
```

Modifica en `Download_youtube.py`:

```python
urls = []  # si quieres que la lista principal esté vacía
urls_from_file = "lista_urls.txt"
```

Ejecuta:

```bash
python Download_youtube.py
```

Todos los audios se guardarán en la carpeta `output_folder`.

---

## 6. Advertencia legal y responsabilidad

1. **Uso legítimo solamente**  
   Este script está pensado **exclusivamente** para:
   - Descargar tus propios vídeos o música.
   - Contenido en dominio público.
   - Contenido con licencia que **permita explícitamente** la descarga y copia.

2. **Respeta los Términos de Servicio**  
   YouTube, YouTube Music y otras plataformas suelen prohibir descargas con herramientas no oficiales.  
   Es tu responsabilidad leer y respetar esos términos antes de usar este script.

3. **No eludir DRM ni protecciones técnicas**  
   El script **no está diseñado** para, ni debe usarse para:
   - Romper cifrados.
   - Eludir DRM u otras medidas técnicas de protección.

4. **Responsabilidad del usuario**  
   Los autores de este script **no asumen ninguna responsabilidad** por su uso.  
   El usuario es el único responsable de:
   - Verificar que tiene derecho a descargar determinado contenido.
   - Cumplir la legislación vigente sobre propiedad intelectual y derechos de autor.
   - Cumplir los Términos de Servicio de cada plataforma.

5. **Software sin garantía**  
   Este software se proporciona "tal cual" (*as is*), sin garantías de ningún tipo.  
   Lo usas bajo tu propia responsabilidad.

---

## 7. Buenas prácticas

- Descarga sólo contenido que tengas derecho a conservar.
- Si tienes dudas sobre la legalidad, consulta con un profesional o con el titular de los derechos.
- Considera apoyar a los creadores de contenido comprando su música o usando las plataformas oficiales.
