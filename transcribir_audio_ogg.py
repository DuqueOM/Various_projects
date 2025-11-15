#!/usr/bin/env python3
# transcribir_ogg_vosk_mejorado.py
import os
import json
import wave
import shutil
import datetime
import traceback
import re
from pathlib import Path
from pydub import AudioSegment
from pydub.effects import normalize
from pydub.silence import detect_nonsilent, split_on_silence
from vosk import Model, KaldiRecognizer

# --------------------------
# CONFIG
# --------------------------
CARPETA_AUDIOS = Path("/home/duque_om/proyects/audios")  # <- ajusta si hace falta
ARCHIVO_SALIDA = CARPETA_AUDIOS / "transcripcion_total.txt"
NOTAS_PATH = CARPETA_AUDIOS / "procesamiento_notas.txt"

# Ruta donde buscar/instalar modelos (recomendado)
VOSK_MODEL_DIR = Path.home() / ".vosk" / "models" / "es"

# Parámetros de audio para Vosk (Vosk funciona muy bien con 16000 Hz mono PCM16)
TARGET_SAMPLE_RATE = 16000
MIN_AUDIO_MS = 400  # si menos de esto se considera muy corto
MIN_SILENCE_LEN = 500  # longitud mínima del silencio para dividir
SILENCE_THRESH = -40  # umbral de silencio en dB
MAX_CHUNK_LENGTH_MS = 10000  # longitud máxima de cada chunk (10s)
CONFIDENCE_THRESHOLD = 0.3  # umbral de confianza para aceptar palabras

# --------------------------
# UTILIDADES AUDIO
# --------------------------

def asegurar_modelo():
    """Devuelve la ruta del modelo Vosk si existe; si no, devuelve None y escribe nota."""
    if VOSK_MODEL_DIR.exists() and any(VOSK_MODEL_DIR.iterdir()):
        return str(VOSK_MODEL_DIR)
    # Busca modelos en carpetas comunes (por si el usuario colocó otro nombre)
    possible = [
        Path.cwd() / "vosk-model-small-es-0.42",
        Path.cwd() / "vosk-model-es-0.22",
        Path.home() / ".vosk" / "models" / "vosk-model-small-es-0.42"
    ]
    for p in possible:
        if p.exists():
            return str(p)
    return None

def convertir_ogg_a_wav_normalizado(ogg_path: Path, wav_path: Path):
    """Convierte .ogg a .wav, resamplea a 16k mono PCM16, normaliza y recorta silencios extremos."""
    audio = AudioSegment.from_file(str(ogg_path))
    # Normalizar volumen
    audio = normalize(audio)
    # Reducir ruido de fondo (suavizado)
    audio = apply_noise_reduction(audio)
    # Convertir a mono y 16kHz y 16-bit
    audio = audio.set_frame_rate(TARGET_SAMPLE_RATE).set_channels(1).set_sample_width(2)
    # Detectar zonas con sonido (para eliminar silencios largos al inicio/fin)
    nonsilent = detect_nonsilent(audio, min_silence_len=200, silence_thresh=SILENCE_THRESH)
    if nonsilent:
        # mantén desde el primer segmento hasta el último
        start = max(0, nonsilent[0][0] - 100)  # 100ms margen
        end = min(len(audio), nonsilent[-1][1] + 100)
        audio = audio[start:end]
    # Exportar como WAV PCM16
    audio.export(str(wav_path), format="wav")

def apply_noise_reduction(audio):
    """Aplica reducción básica de ruido usando high-pass filter."""
    # Filtro high-pass para eliminar ruido de baja frecuencia
    from pydub.effects import high_pass_filter
    audio = high_pass_filter(audio, 80)
    # Suavizado ligero para reducir artefactos
    return audio

# --------------------------
# TRANSCRIPCIÓN VOSK
# --------------------------

def cargar_modelo_vosk(model_path=None):
    """Carga el modelo Vosk desde model_path o desde Model(lang='es') como fallback.
       Devuelve (model_obj, nota)"""
    try:
        if model_path:
            model = Model(model_path)
            return model, f"Modelo Vosk cargado desde: {model_path}"
        else:
            # Intento con acceso por idioma (algunas versiones permiten Model(lang='es'))
            model = Model(lang="es")
            return model, "Modelo Vosk cargado con Model(lang='es')"
    except Exception as e:
        return None, f"No se pudo cargar modelo Vosk: {e}"

def transcribir_con_vosk(wav_path: Path, model):
    """Transcribe un WAV (16k mono) con Vosk y devuelve texto mejorado."""
    # Dividir audio en chunks para mejor precisión
    audio = AudioSegment.from_wav(wav_path)
    chunks = dividir_audio_en_chunks(audio)
    
    textos_chunk = []
    for i, chunk in enumerate(chunks):
        chunk_path = wav_path.parent / f"chunk_{i}.wav"
        chunk.export(str(chunk_path), format="wav")
        
        texto_chunk = transcribir_chunk(chunk_path, model)
        if texto_chunk:
            textos_chunk.append(texto_chunk)
        
        # Limpiar chunk temporal
        if chunk_path.exists():
            chunk_path.unlink()
    
    # Unir y post-procesar texto
    texto_completo = " ".join(textos_chunk)
    texto_mejorado = post_procesar_texto(texto_completo)
    
    return texto_mejorado.strip()

def dividir_audio_en_chunks(audio):
    """Divide el audio en chunks basados en silencios para mejor transcripción."""
    chunks = split_on_silence(
        audio,
        min_silence_len=MIN_SILENCE_LEN,
        silence_thresh=SILENCE_THRESH,
        keep_silence=100  # mantener 100ms de silencio
    )
    
    # Filtrar chunks muy cortos y combinar chunks muy largos
    chunks_filtrados = []
    for chunk in chunks:
        if len(chunk) >= MIN_AUDIO_MS:
            if len(chunk) > MAX_CHUNK_LENGTH_MS:
                # Dividir chunk largo en partes más pequeñas
                sub_chunks = [chunk[i:i+MAX_CHUNK_LENGTH_MS] 
                             for i in range(0, len(chunk), MAX_CHUNK_LENGTH_MS)]
                chunks_filtrados.extend(sub_chunks)
            else:
                chunks_filtrados.append(chunk)
    
    return chunks_filtrados

def transcribir_chunk(chunk_path, model):
    """Transcribe un chunk individual de audio."""
    wf = wave.open(str(chunk_path), "rb")
    sr = wf.getframerate()
    rec = KaldiRecognizer(model, sr)
    rec.SetWords(True)
    rec.SetPartialWords(True)

    resultado_total = []
    try:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                j = json.loads(rec.Result())
                if "text" in j and j["text"].strip():
                    resultado_total.append(j["text"].strip())
        final = json.loads(rec.FinalResult())
        if "text" in final and final["text"].strip():
            resultado_total.append(final["text"].strip())
    finally:
        wf.close()

    return " ".join(filter(None, resultado_total)).strip()

def post_procesar_texto(texto):
    """Aplica correcciones comunes al texto transcrito."""
    if not texto:
        return texto
    
    # Corregir problemas comunes de transcripción
    correcciones = {
        # Números y palabras comunes
        r'\buno\b': 'uno',
        r'\bdos\b': 'dos', 
        r'\btres\b': 'tres',
        r'\bcuatro\b': 'cuatro',
        r'\bcinco\b': 'cinco',
        # Palabras confundidas comúnmente
        r'\bha\b': 'a',
        r'\bhecho\b': 'hecho',
        r'\bvan\b': 'van',
        r'\bpara\b': 'para',
        r'\bpor\b': 'por',
        r'\bque\b': 'que',
        r'\bcon\b': 'con',
        r'\bcomo\b': 'como',
        r'\bpero\b': 'pero',
        r'\bsus\b': 'sus',
        r'\bles\b': 'les',
        # Quitar espacios múltiples
        r'\s+': ' ',
        # Corregir puntuación
        r'\s+([.,!?;:])': r'\1',
        r'([.,!?;:])(?!\s)': r'\1 ',
    }
    
    texto_corregido = texto
    for patron, reemplazo in correcciones.items():
        texto_corregido = re.sub(patron, reemplazo, texto_corregido, flags=re.IGNORECASE)
    
    # Capitalizar primera letra y asegurar puntuación final
    texto_corregido = texto_corregido.strip()
    if texto_corregido:
        texto_corregido = texto_corregido[0].upper() + texto_corregido[1:]
        if texto_corregido[-1] not in '.!?':
            texto_corregido += '.'
    
    return texto_corregido

# --------------------------
# PROCESO PRINCIPAL
# --------------------------

def procesar_carpeta(carpeta: Path, salida: Path):
    notas = []
    if not carpeta.exists():
        raise FileNotFoundError(f"La carpeta {carpeta} no existe.")

    # Determinar modelo
    modelo_path = asegurar_modelo()
    model, model_note = cargar_modelo_vosk(modelo_path)
    notas.append(model_note)
    if model is None:
        notas.append("ATENCIÓN: No se encontró un modelo Vosk local. Descarga uno (ver notas) y colócalo en:")
        notas.append(str(VOSK_MODEL_DIR))
        # aun así intentamos con Model(lang='es') en cargar_modelo_vosk (si falla, model será None)
    ogg_files = [f for f in carpeta.iterdir() if f.is_file() and f.suffix.lower() == ".ogg"]
    ogg_files.sort(key=lambda f: f.stat().st_ctime)

    with open(salida, "w", encoding="utf-8") as out_f:
        for ogg in ogg_files:
            try:
                created_ts = ogg.stat().st_ctime
                created_dt = datetime.datetime.fromtimestamp(created_ts)
                header = f"\n=== Archivo: {ogg.name} | Creado: {created_dt.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                out_f.write(header)

                wav_path = carpeta / (ogg.stem + ".wav")
                # Convertir y preparar WAV
                convertir_ogg_a_wav_normalizado(ogg, wav_path)
                notas.append(f"Convertido: {ogg.name} → {wav_path.name}")

                # Comprobar duración
                audio = AudioSegment.from_wav(wav_path)
                dur_ms = len(audio)
                notas.append(f"Duración (ms): {dur_ms} - {ogg.name}")
                if dur_ms < MIN_AUDIO_MS:
                    out_f.write("[Archivo demasiado corto o vacío]\n")
                    notas.append(f"Archivo muy corto: {ogg.name}")
                else:
                    if model is None:
                        out_f.write("[Error: modelo Vosk no cargado]\n")
                        notas.append(f"No se pudo transcribir (modelo ausente): {ogg.name}")
                    else:
                        texto = transcribir_con_vosk(wav_path, model)
                        if texto:
                            out_f.write(texto + "\n")
                            notas.append(f"Transcripción exitosa: {ogg.name}")
                        else:
                            out_f.write("[Sin voz o inaudible]\n")
                            notas.append(f"No se detectó voz / transcripción vacía: {ogg.name}")

                # eliminar WAV temporal sólo si existe
                try:
                    if wav_path.exists():
                        wav_path.unlink()
                except Exception as e_rm:
                    notas.append(f"No se pudo borrar WAV {wav_path.name}: {e_rm}")

            except Exception as e:
                tb = traceback.format_exc()
                notas.append(f"Error procesando {ogg.name}: {e}\n{tb}")
                out_f.write("[Error procesando este archivo]\n")

    # Guardar notas
    with open(NOTAS_PATH, "w", encoding="utf-8") as nf:
        nf.write("\n".join(notas))

    print(f"✅ Proceso completado.\n→ Transcripciones: {salida}\n→ Notas: {NOTAS_PATH}")
    print("Resumen rápido (últimas notas):")
    for n in notas[-6:]:
        print(" -", n)

# --------------------------
# EJECUCIÓN
# --------------------------
if __name__ == "__main__":
    procesar_carpeta(CARPETA_AUDIOS, ARCHIVO_SALIDA)
