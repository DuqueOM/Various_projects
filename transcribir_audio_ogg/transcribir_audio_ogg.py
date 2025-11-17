"""transcribir_audio_ogg.py

Script para convertir cualquier audio a MP3 (máxima calidad posible vía ffmpeg)
 y luego transcribirlo usando Whisper.

- Carpeta de entrada de audios: ./audios
- Carpeta de salida de resultados: ./Descargas
  - <nombre>.mp3  : audio convertido
  - <nombre>.txt  : transcripción en texto plano

Usa este script SOLO con audios tuyos o con permiso.
"""

import os
import subprocess
from pathlib import Path

import whisper

# Directorios base
BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audios"
OUTPUT_DIR = BASE_DIR / "Descargas"

# Extensiones de audio aceptadas
AUDIO_EXTS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".aac",
    ".wma",
    ".opus",
    ".webm",
}


def ensure_directories() -> None:
    """Crea las carpetas audios y Descargas si no existen."""

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_ffmpeg_convert(input_path: Path, output_path: Path) -> bool:
    """Convierte un audio cualquiera a MP3 usando ffmpeg.

    Usa libmp3lame con calidad VBR máxima (-qscale:a 0).
    Devuelve True si la conversión fue exitosa.
    """

    cmd = [
        "ffmpeg",
        "-y",  # sobreescribir sin preguntar
        "-i",
        str(input_path),
        "-vn",  # sin vídeo
        "-acodec",
        "libmp3lame",
        "-qscale:a",
        "0",
        str(output_path),
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        print(
            "[ERROR] ffmpeg no encontrado. Asegúrate de tenerlo instalado y en el PATH."
        )
        return False

    if proc.returncode != 0:
        print(
            f"[ERROR] ffmpeg fallo para {input_path.name}: {proc.stderr.splitlines()[-1] if proc.stderr else ''}"
        )
        return False

    return True


def convert_all_to_mp3() -> list[Path]:
    """Convierte todos los audios de AUDIO_DIR a MP3 en OUTPUT_DIR.

    Devuelve la lista de rutas MP3 generadas.
    """

    mp3_paths: list[Path] = []

    for audio_file in sorted(AUDIO_DIR.iterdir()):
        if not audio_file.is_file():
            continue
        if audio_file.suffix.lower() not in AUDIO_EXTS:
            continue

        base_name = audio_file.stem
        out_mp3 = OUTPUT_DIR / f"{base_name}.mp3"

        print(f"[INFO] Convirtiendo a MP3: {audio_file.name} -> {out_mp3.name}")
        ok = run_ffmpeg_convert(audio_file, out_mp3)
        if ok:
            mp3_paths.append(out_mp3)
        else:
            print(
                f"[WARN] Se omitió la transcripción de {audio_file.name} por error en la conversión."
            )

    return mp3_paths


def load_whisper_model() -> whisper.Whisper:
    """Carga el modelo Whisper.

    Usa la variable de entorno WHISPER_MODEL si está definida, si no usa 'medium'.
    """

    model_name = os.environ.get("WHISPER_MODEL", "medium")
    print(f"[INFO] Cargando modelo Whisper: {model_name}")
    return whisper.load_model(model_name)


def transcribe_mp3_files(
    mp3_files: list[Path], model: whisper.Whisper, language: str | None = None
) -> None:
    """Transcribe cada MP3 y guarda un .txt con el mismo nombre en OUTPUT_DIR."""

    if not mp3_files:
        print("[INFO] No hay archivos MP3 para transcribir.")
        return

    for mp3_path in mp3_files:
        txt_path = OUTPUT_DIR / f"{mp3_path.stem}.txt"
        print(f"[INFO] Transcribiendo: {mp3_path.name} -> {txt_path.name}")

        try:
            result = model.transcribe(str(mp3_path), language=language)
            text = (result.get("text") or "").strip()
        except Exception as e:
            print(f"[ERROR] Fallo al transcribir {mp3_path.name}: {e}")
            continue

        try:
            with txt_path.open("w", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"[ERROR] No se pudo escribir el archivo {txt_path}: {e}")


def main() -> None:
    """Punto de entrada principal.

    1) Crea carpetas audios y Descargas.
    2) Convierte todos los audios de audios/ a MP3 en Descargas/.
    3) Transcribe cada MP3 y guarda el texto en Descargas/.
    """

    ensure_directories()

    # Buscar audios a procesar
    audio_files = [
        p for p in AUDIO_DIR.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    ]
    if not audio_files:
        print(
            "[INFO] No se encontraron audios en la carpeta 'audios'. Coloca ahí tus archivos y vuelve a ejecutar."
        )
        return

    # 1) Convertir a MP3
    mp3_files = convert_all_to_mp3()
    if not mp3_files:
        print(
            "[WARN] No se generó ningún MP3. Revisa ffmpeg y los formatos de entrada."
        )
        return

    # 2) Cargar modelo Whisper y transcribir
    try:
        model = load_whisper_model()
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el modelo Whisper: {e}")
        return

    # Puedes forzar un idioma, por ejemplo 'es' para español, si lo deseas.
    language = None  # o 'es', 'en', etc.
    transcribe_mp3_files(mp3_files, model, language=language)

    print("\n[OK] Proceso completado. Revisa la carpeta 'Descargas'.")


if __name__ == "__main__":
    main()
