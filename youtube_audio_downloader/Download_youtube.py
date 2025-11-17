# download_youtube_audio.py
# Descargador de audio (YouTube / YouTube Music) basado en yt-dlp.
# Usa este script SOLO para tus propios vídeos o material con permiso.
#
# Características principales:
# - Acepta URLs individuales, playlists y listas de URLs.
# - Descarga siempre el mejor audio disponible.
# - Convierte a audio (MP3 por defecto) en la mejor calidad posible.
# - Intenta escribir metadatos (título, artista, álbum) y portada.
# - Guarda un .info.json por archivo con metadatos extendidos
#   (incluyendo letras si el extractor las expone).
#
# Requisitos:
#   pip install yt-dlp
#   ffmpeg disponible en PATH

import os

from yt_dlp import YoutubeDL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------- CONFIGURACIÓN -----------------
# 1) URLs a descargar (videos o playlists de YouTube / YouTube Music)
#    Si no quieres hardcodear URLs aquí, puedes dejar esta lista vacía
#    y usar el archivo links_audio.txt.
urls = [
    # "https://www.youtube.com/watch?v=VIDEO_ID",
    # "https://music.youtube.com/watch?v=VIDEO_ID",
    # "https://www.youtube.com/playlist?list=PLAYLIST_ID",
]

# 2) Archivo de texto con URLs (una por línea).
#    Por defecto, se usa links_audio.txt en la misma carpeta que este script.
urls_from_file = os.path.join(BASE_DIR, "links_audio.txt")

# 3) Carpeta de destino (cambia la ruta a la que prefieras).
#    Por defecto, una subcarpeta ./Descargas junto al script.
output_folder = os.path.join(BASE_DIR, "Descargas")

# 4) Formato de salida y calidad
#    - audio_format: "mp3" por defecto. Para máxima calidad es recomendable
#      usar "m4a" (suele implicar menos pérdida a partir del stream original).
#    - mp3_quality: sólo aplica cuando audio_format es "mp3".
audio_format = "mp3"
mp3_quality = "320"  # "192", "256" o "320" para MP3
# -------------------------------------------------

os.makedirs(output_folder, exist_ok=True)

# Plantilla de nombre de archivo: título del video.mp3
outtmpl = os.path.join(output_folder, "%(title)s.%(ext)s")

ydl_opts = {
    # Mejor audio disponible (YouTube / YouTube Music)
    "format": "bestaudio/best",
    # Postprocesado: extraer audio + metadatos + portada
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": mp3_quality,
        },
        {
            "key": "FFmpegMetadata",
        },
        {
            "key": "EmbedThumbnail",
        },
    ],
    # Plantilla salida: título.ext dentro de output_folder
    "outtmpl": outtmpl,
    # Guardar thumbnail y JSON de info para metadatos extendidos (incl. letras)
    "writethumbnail": True,
    "writeinfojson": True,
    # No descargar subtítulos (puedes cambiar a True si los necesitas)
    "writesubtitles": False,
    # Mostrar progreso en consola
    "progress_hooks": [],
    # Continúa si un video falla
    "ignoreerrors": True,
    # Si la URL es una playlist, descarga toda la lista
    "yes_playlist": True,
    "noplaylist": False,
    # No conservar el archivo de vídeo original tras extraer el audio
    "keepvideo": False,
}

# Hook para ver progreso en consola


def progreso(info):
    status = info.get("status")
    if status == "downloading":
        print(
            f"Descargando: {info.get('filename', '')} -> {info.get('_percent_str','')} {info.get('_eta_str','')}"
        )
    elif status == "finished":
        print(f"Descargado, convirtiendo: {info.get('filename','')}")
    elif status == "error":
        print(f"Error en: {info.get('filename','')}")


ydl_opts["progress_hooks"].append(progreso)


def descargar_a_mp3(lista_urls):
    if not lista_urls:
        print("No hay URLs en la lista. Agrega URLs en la variable 'urls'.")
        return

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download(lista_urls)
            print("\n¡Terminado! Revisa la carpeta:", output_folder)
        except Exception as e:
            print("Ocurrió un error al descargar:", str(e))


if __name__ == "__main__":
    # Construir la lista final de URLs combinando las configuradas en el
    # script y, opcionalmente, las leídas desde un archivo de texto.
    all_urls = list(urls)
    if urls_from_file:
        if os.path.isfile(urls_from_file):
            with open(urls_from_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        all_urls.append(line)
        else:
            print(f"Aviso: el archivo '{urls_from_file}' no existe; se ignorará.")

    descargar_a_mp3(all_urls)
