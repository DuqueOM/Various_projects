# descarga_mp3_ytdlp.py
# Usa este script SOLO para tus propios videos o material con permiso.
# Requisitos: pip install yt-dlp ; ffmpeg en PATH

import os
from yt_dlp import YoutubeDL

# ----------------- CONFIGURACIÓN -----------------
# Cambia aquí las URLs (pueden ser videos individuales o URLs de playlists)
urls = ['https://www.youtube.com/watch?v=Z1c3SXLmAUg&list=RDZ1c3SXLmAUg&start_radio=1',
        # Ejemplo:
        # "https://www.youtube.com/watch?v=VIDEO_ID",
        # "https://www.youtube.com/playlist?list=PLAYLIST_ID",
        ]

# Carpeta de destino (cambia la ruta a la que prefieras)
# o "/home/tuusuario/Music/DescargasYT"
output_folder = r"/mnt/c/Users/User/Desktop/music"

# Formato de calidad MP3 (kbps): "192", "256", "320"
mp3_quality = "320"
# -------------------------------------------------

os.makedirs(output_folder, exist_ok=True)

# Plantilla de nombre de archivo: título del video.mp3
outtmpl = os.path.join(output_folder, "%(title)s.%(ext)s")

ydl_opts = {
    # Mejor audio disponible
    "format": "bestaudio/best",
    # Escribir metadatos ID3 y usar ffmpeg para extraer audio a mp3
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": mp3_quality,
    }],
    # Plantilla salida
    "outtmpl": outtmpl,
    # Evita descargar thumbnails o subtítulos innecesarios (puedes cambiar)
    "writethumbnail": False,
    "writesubtitles": False,
    # Mostrar progreso en consola
    "progress_hooks": [],
    # Continúa si un video falla
    "ignoreerrors": True,
    # Si la URL es una playlist, descarga toda la lista
    "yes_playlist": True,
    # Evita archivos temporales al final si algo falla
    "noplaylist": False,
    # No borrar los archivos si falla la conversión (útil para debugging)
    "keepvideo": False,
}

# Hook para ver progreso en consola


def progreso(info):
    status = info.get("status")
    if status == "downloading":
        print(
            f"Descargando: {info.get('filename', '')} -> {info.get('_percent_str','')} {info.get('_eta_str','')}")
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
    descargar_a_mp3(urls)
