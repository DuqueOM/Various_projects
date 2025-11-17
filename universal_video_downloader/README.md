# Universal Video Downloader (mega_batch_downloader_patched)

Script en Python para descargar vídeos por lotes desde múltiples sitios web.

Combina varias estrategias de descarga:

- **yt-dlp** (primera opción, muy completa para YouTube y muchos sitios populares).
- **Parseo HTML** para detectar URLs de media en:
  - Etiquetas `<video>` y `<source>`.
  - Metadatos `og:video`, `twitter:player:stream`, etc.
  - Scripts JSON-LD (`application/ld+json`) con campos como `contentUrl`, `embedUrl`, `videoUrl`.
  - Enlaces directos a ficheros `.mp4`, `.webm`, `.mkv`, `.m3u8`, `.mpd`, etc.
- **Descarga de manifests HLS / DASH** (`.m3u8`, `.mpd`, `/manifest`, `/playlist`) usando `ffmpeg`.
- **Fallback opcional con Selenium + selenium-wire** para páginas que generan las URLs de vídeo por JavaScript.

> **Nota importante:** No existe garantía de que pueda descargar "cualquier" vídeo de "cualquier" sitio; algunos sitios usan DRM u otras protecciones técnicas que este script **no** intenta eludir.

---

## 1. Requisitos

### 1.1. Python y librerías

Asegúrate de tener Python 3 y luego instala las dependencias:

```bash
pip install -U \
  git+https://github.com/yt-dlp/yt-dlp.git \
  requests \
  beautifulsoup4 \
  tqdm \
  selenium-wire \
  webdriver-manager
```

> `selenium-wire` y `webdriver-manager` sólo son necesarios si deseas usar el fallback con Selenium (`--use-selenium`).

### 1.2. ffmpeg

El script usa `ffmpeg` para descargar y unir streams HLS/DASH:

- Debe estar instalado y disponible en el `PATH`.
- En distribuciones Linux, suele bastar con:

```bash
sudo apt install ffmpeg
```

---

## 2. Archivo principal

Dentro de esta carpeta encontrarás:

- `Download_videos.py`  
  Script principal con toda la lógica de descarga.

Puedes ejecutarlo con Python:

```bash
python Download_videos.py [opciones]
```

---

## 3. Opciones principales de la CLI

El script acepta **una sola URL** o un **archivo con muchas URLs**.

### 3.1. Entrada de URLs

- `--url URL`  
  Descarga una sola URL.

- `-i, --input RUTA`  
  Archivo de texto con una URL por línea.  
  Las líneas en blanco o que empiezan por `#` se ignoran.

Si no se proporciona ni `-i` ni `--url`, el script intentará usar automáticamente
un archivo `links_video.txt` ubicado en la misma carpeta que `Download_videos.py`.
Si dicho archivo no existe, mostrará un mensaje de error indicando qué opciones
puedes usar.

### 3.2. Carpeta de salida y organización

- `-o, --outdir CARPETA`  
  Carpeta de salida base. Por defecto: `./Descargas` (subcarpeta dentro del
  propio proyecto `universal_video_downloader`).

- `--by-site`  
  Organiza las descargas en **subcarpetas por dominio** dentro de la carpeta base.  
  Ejemplo: `./downloads/www.youtube.com/`, `./downloads/ejemplo.com/`, etc.

> En Linux/WSL: si pasas una ruta tipo `D:\Videos`, el script la normaliza a `/mnt/d/Videos` para que funcione correctamente.

### 3.3. Concurrencia

- `-w, --workers N`  
  Número de hilos concurrentes para procesar varias URLs a la vez.  
  Por defecto: `3`.

### 3.4. yt-dlp

- `--no-yt`  
  Desactiva el uso de `yt-dlp` (no recomendado salvo que quieras probar sólo el parser HTML).

- `--rename-template`  
  Plantilla de nombre de fichero para `yt-dlp`. Ejemplo: `"%(title)s.%(ext)s"`.

- `--download-archive ARCHIVO`  
  Archivo de registro que evita descargas duplicadas para `yt-dlp`.

- `--ratelimit LIMITE`  
  Límite de velocidad para `yt-dlp` (por ejemplo `500K`).

- `--only-audio`  
  Extrae sólo audio (usa `yt-dlp` + ffmpeg).

- `--audio-format FORMATO`  
  Formato de audio cuando `--only-audio` está activo (por defecto: `mp3`).

### 3.5. Cookies, proxy y User-Agent

- `--cookies-file RUTA`  
  Archivo de cookies (formato Netscape) para `yt-dlp` y ffmpeg.

- `--cookie-string "k=v; k2=v2"`  
  Cadena de cookies para las peticiones HTTP (requests) y cabecera `Cookie` de ffmpeg.

- `--proxy URL_PROXY`  
  Proxy HTTP/HTTPS para las descargas (requests y ffmpeg).  
  Ejemplo: `http://127.0.0.1:8080`.

- `--user-agent CADENA`  
  User-Agent a usar en las peticiones HTTP. Por defecto el script usa un **UA de navegador moderno**.

### 3.6. Selenium (opcional)

- `--use-selenium`  
  Activa el fallback con Selenium + selenium-wire, recomendable en páginas que generan las URLs de vídeo con JavaScript.

- `--selenium-wait SEGUNDOS`  
  Segundos a esperar tras cargar la página antes de inspeccionar las peticiones de red. Por defecto: `8`.

- `--headless`  
  Ejecuta el navegador en modo headless (sin abrir ventana gráfica).

### 3.7. Otros

- `--retries N`  
  Número de reintentos en descargas directas HTTP (no yt-dlp). Por defecto: `3`.

- `--log ARCHIVO_CSV`  
  Guarda un CSV con el resultado por cada URL: `url, ok/fail, mensaje`.

---

## 4. Ejemplos de uso

### 4.1. Descargar un único vídeo (YouTube u otra página)

```bash
python Download_videos.py \
  --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" \
  -o ./Descargas \
  --by-site
```

### 4.2. Descargar una lista de vídeos de distintas páginas

Archivo `lista_urls.txt`:

```text
# Cada línea es una URL
https://www.youtube.com/watch?v=AAA
https://www.ejemplo.com/video/xyz
https://otro-sitio.com/player?id=999
```

Comando:

```bash
python Download_videos.py \
  -i lista_urls.txt \
  -o ./Descargas \
  -w 4 \
  --use-selenium \
  --selenium-wait 10 \
  --headless \
  --by-site
```

### 4.3. Descargar sólo audio

```bash
python Download_videos.py \
  --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" \
  -o ./Descargas \
  --only-audio \
  --audio-format mp3
```

---

## 5. Alcance y limitaciones

- El script **no garantiza** poder descargar todos los vídeos de todos los sitios.
- Algunos servicios utilizan **DRM** (por ejemplo Widevine, FairPlay u otros sistemas de cifrado) u otras medidas técnicas específicas:
  - Este script **no** intenta ni debe usarse para eludir dichas protecciones.
- También puede haber sitios que cambien con frecuencia su código interno o añadan mecanismos anti-automatización, por lo que la tasa de éxito puede variar con el tiempo.

---

## 6. Advertencia legal y responsabilidad (derechos de autor)

1. **Uso legítimo únicamente**  
   Este programa está pensado **exclusivamente** para:
   - Descargar contenido propio o sobre el cual tengas derechos suficientes.
   - Contenido en dominio público o bajo licencias que permitan la descarga y copia (por ejemplo algunas licencias Creative Commons).

2. **Respeto a los términos de servicio**  
   Muchos sitios (incluyendo plataformas de vídeo populares) tienen Términos de Servicio que restringen o prohíben la descarga de contenidos mediante herramientas no oficiales.  
   Es tu responsabilidad revisar y respetar esos términos antes de usar este script.

3. **DRM y medidas técnicas de protección**  
   Este script **no está diseñado** para, ni debe usarse con el propósito de:
   - Eludir sistemas de gestión de derechos digitales (DRM).
   - Romper cifrados u otras medidas técnicas de protección.

4. **Responsabilidad del usuario**  
   Los autores del script **no asumen ninguna responsabilidad** por el uso que se haga de esta herramienta.  
   El usuario final es el único responsable de:
   - Verificar que tiene permisos para descargar un contenido concreto.
   - Cumplir la legislación aplicable en materia de propiedad intelectual y derechos de autor.
   - Cumplir los términos de servicio de cada plataforma.

5. **Sin garantías**  
   Este software se proporciona "tal cual" (*as is*), sin garantías de ningún tipo, expresas o implícitas.  
   El uso es bajo tu propia responsabilidad.

---

## 7. Recomendaciones de uso responsable

- Antes de descargar, pregúntate siempre si:
  - ¿Soy titular de los derechos del contenido?  
  - ¿Tengo una licencia o permiso explícito?  
  - ¿La plataforma permite la descarga según sus Términos de Servicio?
- Prefiere descargar sólo contenido:
  - De tu propia cuenta.
  - Publicado bajo licencias abiertas.
  - Claramente autorizado por el titular de los derechos.

Si tienes dudas sobre la legalidad de descargar cierto contenido, consulta con un profesional legal o el propio titular de los derechos.
