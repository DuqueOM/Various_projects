#!/usr/bin/env python3
"""
mega_batch_downloader_patched.py

Script completo y parcheado para descargar videos por lotes.
Estrategia (en orden):
 1) yt-dlp
 2) parseo HTML (video/source, meta, JSON-LD, enlaces directos)
 3) HLS (.m3u8) con ffmpeg
 4) captura de tráfico con selenium-wire (opcional) para páginas que generan URLs con JS

Características añadidas en esta versión:
 - saneamiento automático de URLs (quita backslashes, decodifica percent-encodings)
 - detección de bloqueos por "piracy" u "unknown algorithm" en salida de yt-dlp
 - acepta una sola URL con --url o un archivo con -i/--input
 - opción --use-selenium para fallback (selenium-wire + webdriver-manager)
 - opción --headless para correr Selenium en headless
 - proxy, cookies (archivo o string), rate-limit, download-archive
 - logs de resumen y salida configurable
 - normalización simple de ruta de salida para Windows cuando se ejecuta en Linux/WSL

USO (ejemplos):
  python mega_batch_downloader_patched.py -i lista_urls.txt -o ./mis_descargas --use-selenium --headless -w 4
  python mega_batch_downloader_patched.py --url "https://sitio.com/mi-video" -o "D:\\Videos" --use-selenium

DEPENDENCIAS:
  pip install -U git+https://github.com/yt-dlp/yt-dlp.git requests beautifulsoup4 tqdm selenium-wire webdriver-manager
  ffmpeg instalado y en PATH

LEGAL & ÉTICA:
  Este script es una herramienta general. Úsalo únicamente para contenido que posees o para el que tienes permiso explícito.
  No puedo ayudar a eludir DRM ni a forzar descargas de material protegido sin autorización.

"""

import argparse
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# intentos de importar yt-dlp; si no está, el script seguirá e intentará fallbacks
try:
    from yt_dlp import YoutubeDL
except Exception:
    YoutubeDL = None

# selenium-wire (opcional)
try:
    from seleniumwire import webdriver
    from seleniumwire.utils import decode
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_WIRE_AVAILABLE = True
except Exception:
    SELENIUM_WIRE_AVAILABLE = False

# -------------------
# Helpers
# -------------------
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def run_cmd(cmd, timeout=300):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return proc.returncode, proc.stdout.decode('utf-8', errors='ignore'), proc.stderr.decode('utf-8', errors='ignore')
    except subprocess.TimeoutExpired:
        return 124, '', 'timeout'


def safe_filename(s):
    s = re.sub(r'[\\/*?:"<>|]', '_', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:200]


def ensure_dir(d):
    Path(d).mkdir(parents=True, exist_ok=True)


def normalize_outdir_for_os(outdir):
    """Si estamos en Linux/WSL y el usuario pasó una ruta Windows tipo C:\\..., convertir a /mnt/c/..."""
    if not outdir:
        return outdir
    # quick detect Windows drive notation
    m = re.match(r'^([A-Za-z]):\\(.*)$', outdir)
    if m and sys.platform.startswith('linux'):
        drive = m.group(1).lower()
        rest = m.group(2).replace('\\', '/')
        return f'/mnt/{drive}/{rest}'
    # también aceptar D:/path
    m2 = re.match(r'^([A-Za-z]):/(.*)$', outdir)
    if m2 and sys.platform.startswith('linux'):
        drive = m2.group(1).lower()
        rest = m2.group(2)
        return f'/mnt/{drive}/{rest}'
    return outdir


# -------------------
# Sanitización y detección de errores
# -------------------

def sanitize_url(raw):
    """Quita backslashes, decodifica percent-encoding y trim."""
    if raw is None:
        return raw
    s = raw.replace('\\', '')
    s = s.strip()
    s = s.strip('\'"')
    try:
        s = unquote(s)
    except Exception:
        pass
    return s


def yt_dlp_detects_block(text):
    """Analiza un texto (stderr/stdout) de yt-dlp para detectar bloqueos conocidos."""
    if not text:
        return None
    low = text.lower()
    if 'this website is no longer supported' in low or '[piracy]' in low:
        return 'PIRACY_BLOCK'
    if 'unknown algorithm id' in low or 'unknown algorithm' in low:
        return 'UNKNOWN_ALG'
    if 'extractor error' in low or 'http error' in low:
        return 'EXTRACTOR_ERROR'
    return None


# -------------------
# yt-dlp downloader
# -------------------

def download_with_ytdlp(url, outdir, opts):
    if YoutubeDL is None:
        return False, "yt-dlp no instalado. Instala con: pip install -U git+https://github.com/yt-dlp/yt-dlp.git"
    outtmpl = os.path.join(outdir, opts.get('rename_template') or '%(title)s [%(id)s].%(ext)s')
    ydl_opts = {
        'format': opts.get('format', 'bestvideo+bestaudio/best'),
        'outtmpl': outtmpl,
        'merge_output_format': opts.get('merge_output_format', 'mp4'),
        'noplaylist': opts.get('noplaylist', False),
        'quiet': True,
        'no_warnings': True,
    }
    if opts.get('cookiefile'):
        ydl_opts['cookiefile'] = opts.get('cookiefile')
    if opts.get('download_archive'):
        ydl_opts['download_archive'] = opts.get('download_archive')
    if opts.get('ratelimit'):
        ydl_opts['ratelimit'] = opts.get('ratelimit')
    if opts.get('proxy'):
        ydl_opts['proxy'] = opts.get('proxy')
    if opts.get('username') and opts.get('password'):
        ydl_opts['username'] = opts.get('username')
        ydl_opts['password'] = opts.get('password')
    if opts.get('only_audio'):
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': opts.get('audio_format','mp3'),
            'preferredquality': '192'
        }]
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title') or url
            return True, f"yt-dlp OK: {title}"
    except Exception as e:
        # intentar extraer mensajes de la excepción
        return False, f"yt-dlp fallo: {e}"


# -------------------
# HTML parsing
# -------------------

def get_page_text(url, headers, timeout=20, cookies=None, proxy=None):
    try:
        sess = requests.Session()
        if cookies:
            cdict = {}
            for part in cookies.split(';'):
                if '=' in part:
                    k,v = part.strip().split('=',1)
                    cdict[k.strip()] = v.strip()
            sess.cookies.update(cdict)
        if proxy:
            sess.proxies.update({'http': proxy, 'https': proxy})
        r = sess.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return True, r.text
    except Exception as e:
        return False, str(e)


def find_media_urls_from_html(url, headers, cookies=None, proxy=None):
    ok, content_or_err = get_page_text(url, headers, cookies=cookies, proxy=proxy)
    if not ok:
        return [], f"error al obtener HTML: {content_or_err}"
    text = content_or_err
    soup = BeautifulSoup(text, 'html.parser')
    found = set()

    for video in soup.find_all('video'):
        if video.get('src'):
            found.add(video.get('src'))
        for src in video.find_all('source'):
            if src.get('src'):
                found.add(src.get('src'))

    for meta in soup.find_all('meta'):
        prop = (meta.get('property') or meta.get('name') or '').lower()
        if prop in ('og:video', 'og:video:url', 'og:video_secure_url', 'twitter:player:stream'):
            if meta.get('content'):
                found.add(meta.get('content'))

    for script in soup.find_all('script'):
        txt = script.string or ''
        for m in re.findall(r'https?://[^\s"\'"<>]+(?:m3u8|mp4|webm|mkv|mov|ogg)', txt, flags=re.IGNORECASE):
            found.add(m)

    for a in soup.find_all('a', href=True):
        href = a['href']
        if re.search(r'\.(mp4|mkv|webm|mov|ogg)(\?|$)', href, re.IGNORECASE) or re.search(r'\.m3u8(\?|$)', href, re.IGNORECASE):
            found.add(href)

    full = [urljoin(url, u) for u in found]
    return list(dict.fromkeys(full)), "OK" if full else "no encontrado"


# -------------------
# Download helpers
# -------------------

def download_direct_file(url, outpath, headers, cookies=None, proxy=None, max_retries=3, timeout=30):
    ensure_dir(os.path.dirname(outpath) or '.')
    session = requests.Session()
    if cookies:
        cdict = {}
        for part in cookies.split(';'):
            if '=' in part:
                k,v = part.strip().split('=',1)
                cdict[k.strip()] = v.strip()
        session.cookies.update(cdict)
    if proxy:
        session.proxies.update({'http': proxy, 'https': proxy})
    headers = headers or {}
    last_err = None
    for attempt in range(1, max_retries+1):
        try:
            with session.get(url, headers=headers, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0) or 0)
                with open(outpath, 'wb') as f, tqdm(total=total, unit='B', unit_scale=True, desc=os.path.basename(outpath)) as pbar:
                    for chunk in r.iter_content(chunk_size=1024*32):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            return True, f"descargado directo: {outpath}"
        except Exception as e:
            last_err = str(e)
            time.sleep(1 + attempt)
    return False, f"error descarga directa tras {max_retries} intentos: {last_err}"


def download_hls_with_ffmpeg(m3u8_url, outpath, proxy=None, cookies=None, timeout=300):
    ensure_dir(os.path.dirname(outpath) or '.')
    cmd = ['ffmpeg', '-y', '-i', m3u8_url, '-c', 'copy', outpath]
    env = os.environ.copy()
    if proxy:
        env['http_proxy'] = proxy
        env['https_proxy'] = proxy
    code, out, err = run_cmd(cmd, timeout=timeout)
    if code == 0:
        return True, f"ffmpeg OK: {outpath}"
    else:
        return False, f"ffmpeg fallo: {err.splitlines()[-1] if err else out}"


# -------------------
# Selenium capture fallback
# -------------------

def capture_with_selenium(url, wait_seconds=8, headless=True, headers=None, proxy=None):
    if not SELENIUM_WIRE_AVAILABLE:
        return [], "selenium-wire no instalado"
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    selenium_opts = {}
    if proxy:
        selenium_opts['proxy'] = {'http': proxy, 'https': proxy, 'no_proxy': 'localhost,127.0.0.1'}
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options, seleniumwire_options=selenium_opts)
    found = set()
    try:
        driver.scopes = ['.*']
        driver.get(url)
        time.sleep(wait_seconds)
        for req in driver.requests:
            if req.response:
                u = req.url
                if re.search(r'\.m3u8(\?|$)|\.mp4(\?|$)|/playlist/|/manifest', u, re.IGNORECASE):
                    found.add(u)
                ct = req.response.headers.get('Content-Type','') if req.response else ''
                if 'application/vnd.apple.mpegurl' in ct or 'video' in ct:
                    found.add(u)
        srcs, _ = find_media_urls_from_html(url, headers or {'User-Agent': DEFAULT_UA})
        for s in srcs:
            found.add(s)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return list(found), "OK" if found else "no encontrado"


# -------------------
# High-level parse+download
# -------------------

def parse_and_download(url, outdir, opts):
    headers = {'User-Agent': opts.get('user_agent') or DEFAULT_UA}
    if opts.get('headers'):
        headers.update(opts.get('headers'))
    media_urls, msg = find_media_urls_from_html(url, headers, cookies=opts.get('cookie_string'), proxy=opts.get('proxy'))
    if not media_urls and opts.get('use_selenium'):
        cap_urls, msg2 = capture_with_selenium(url, wait_seconds=opts.get('selenium_wait',8), headless=opts.get('selenium_headless',True), headers=headers, proxy=opts.get('proxy'))
        media_urls = cap_urls or []
        msg = msg2
    if not media_urls:
        return False, f"No se encontraron recursos directos: {msg}"

    for m in media_urls:
        if re.search(r'\.m3u8(\?|$)', m, re.IGNORECASE):
            outname = safe_filename(Path(urlparse(m).path).name or 'stream')
            outpath = os.path.join(outdir, outname)
            if not outpath.lower().endswith('.mp4'):
                outpath = outpath + '.mp4'
            ok, info = download_hls_with_ffmpeg(m, outpath, proxy=opts.get('proxy'), cookies=opts.get('cookie_string'))
            if ok:
                return True, info

    for m in media_urls:
        full = m if bool(urlparse(m).netloc) else urljoin(url, m)
        basename = Path(urlparse(full).path).name or 'video'
        if not re.search(r'\.(mp4|mkv|webm|mov|ogg)', basename, re.IGNORECASE):
            basename = basename + '.mp4'
        outpath = os.path.join(outdir, safe_filename(basename))
        ok, info = download_direct_file(full, outpath, headers=headers, cookies=opts.get('cookie_string'), proxy=opts.get('proxy'), max_retries=opts.get('retries',3))
        if ok:
            return True, info

    return False, "No se pudo descargar ninguno de los recursos detectados."


# -------------------
# Worker orchestration (parche con sanitización y detección)
# -------------------

def worker(url, outdir, opts):
    url = sanitize_url(url or '')
    if not url:
        return (url, False, "URL vacía after sanitize")
    ensure_dir(outdir)
    # 1) Try yt-dlp (a menos que lo desactives)
    if not opts.get('no_yt'):
        try:
            ok, msg = download_with_ytdlp(url, outdir, opts)
            if ok:
                return (url, True, msg)
            err = str(msg or '')
            block = yt_dlp_detects_block(err)
            if block == 'PIRACY_BLOCK':
                return (url, False, "yt-dlp bloquea este sitio por política (Piracy). No se puede forzar.")
        except Exception as e:
            print(f"[WARN] yt-dlp excepción para {url}: {e}")

    # 2) parse HTML + direct download + ffmpeg HLS + selenium fallback
    ok, msg = parse_and_download(url, outdir, opts)
    if ok:
        return (url, True, msg)

    # 3) intentar yt-dlp via subprocess para capturar stderr completo y decidir estrategia
    if not opts.get('no_yt'):
        try:
            cmd = ['yt-dlp', '--no-warnings', '-f', opts.get('format','bestvideo+bestaudio/best'), url]
            if opts.get('cookiefile'):
                cmd += ['--cookies', opts.get('cookiefile')]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
            stderr = proc.stderr or proc.stdout
            block = yt_dlp_detects_block(stderr)
            if block == 'PIRACY_BLOCK':
                return (url, False, "yt-dlp bloquea este sitio por política (Piracy). No se puede forzar.")
            if block == 'UNKNOWN_ALG':
                if opts.get('use_selenium'):
                    cap_urls, capmsg = capture_with_selenium(url, wait_seconds=opts.get('selenium_wait',8), headless=opts.get('selenium_headless',True), headers={'User-Agent': opts.get('user_agent')}, proxy=opts.get('proxy'))
                    if cap_urls:
                        for m in cap_urls:
                            if re.search(r'\.m3u8(\?|$)', m, re.IGNORECASE):
                                outname = safe_filename(Path(urlparse(m).path).name or 'stream')
                                outpath = os.path.join(outdir, outname + '.mp4')
                                ok2, info2 = download_hls_with_ffmpeg(m, outpath, proxy=opts.get('proxy'), cookies=opts.get('cookie_string'))
                            else:
                                ok2, info2 = parse_and_download(m, outdir, opts)
                            if ok2:
                                return (url, True, f"Selenium fallback OK: {info2}")
                return (url, False, "yt-dlp error de algoritmo desconocido; se intentó fallback sin éxito.")
        except Exception:
            pass

    return (url, False, f"Todas las estrategias fallaron: {msg}")


# -------------------
# CLI
# -------------------

def main():
    ap = argparse.ArgumentParser(description="Mega batch downloader - intenta varias estrategias.")
    ap.add_argument('-i','--input', required=False, help='Archivo con URLs (una por línea).')
    ap.add_argument('--url', help='Una sola URL (alternativa a -i).')
    ap.add_argument('-o','--outdir', default='./downloads', help='Carpeta de salida.')
    ap.add_argument('-w','--workers', type=int, default=3, help='Hilos concurrentes.')
    ap.add_argument('--no-yt', action='store_true', help='No usar yt-dlp.')
    ap.add_argument('--use-selenium', action='store_true', help='Usar selenium-wire como fallback (instalación requerida).')
    ap.add_argument('--selenium-wait', type=int, default=8, help='Segundos a esperar en Selenium para carga.')
    ap.add_argument('--cookies-file', help='Archivo cookies (Netscape) para yt-dlp (y ffmpeg si aplica).')
    ap.add_argument('--cookie-string', help='Cookies en formato "k=v; k2=v2" para requests.')
    ap.add_argument('--proxy', help='Proxy (ej: http://127.0.0.1:8080).')
    ap.add_argument('--rename-template', help='Plantilla de yt-dlp para nombres (ej: %(title)s.%(ext)s)')
    ap.add_argument('--download-archive', help='Archivo para evitar descargas duplicadas (yt-dlp).')
    ap.add_argument('--ratelimit', help='Límite de bytes/s para yt-dlp (ej: 500K).')
    ap.add_argument('--only-audio', action='store_true', help='Extraer solo audio con yt-dlp.')
    ap.add_argument('--audio-format', default='mp3', help='Formato de audio si --only-audio.')
    ap.add_argument('--retries', type=int, default=3, help='Reintentos para descargas directas.')
    ap.add_argument('--user-agent', default=DEFAULT_UA, help='User-Agent para requests.')
    ap.add_argument('--headless', action='store_true', help='Selenium en headless (si se usa).')
    ap.add_argument('--log', help='Archivo CSV para log de resultados (opcional).')
    args = ap.parse_args()

    if not args.input and not args.url:
        ap.error('Necesitas pasar -i/--input o --url')

    outdir = normalize_outdir_for_os(args.outdir)
    ensure_dir(outdir)

    opts = {
        'no_yt': args.no_yt,
        'use_selenium': args.use_selenium,
        'selenium_wait': args.selenium_wait,
        'selenium_headless': args.headless,
        'cookiefile': args.cookies_file,
        'cookie_string': args.cookie_string,
        'proxy': args.proxy,
        'rename_template': args.rename_template,
        'download_archive': args.download_archive,
        'ratelimit': args.ratelimit,
        'only_audio': args.only_audio,
        'audio_format': args.audio_format,
        'retries': args.retries,
        'user_agent': args.user_agent,
        'headers': None,
    }

    if args.url:
        urls = [args.url.strip()]
    else:
        with open(args.input, 'r', encoding='utf-8') as f:
            urls = [sanitize_url(line.strip()) for line in f if line.strip() and not line.strip().startswith('#')]

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(worker, url, outdir, opts): url for url in urls}
        for fut in as_completed(futures):
            url = futures[fut]
            try:
                u, ok, msg = fut.result()
                results.append((u, ok, msg))
                status = "OK" if ok else "FAIL"
                print(f"[{status}] {u} -> {msg}")
            except Exception as e:
                results.append((url, False, f"Excepción: {e}"))
                print(f"[ERROR] {url} -> {e}")

    ok_count = sum(1 for r in results if r[1])
    print(f"\nResumen: {ok_count}/{len(results)} descargados. Carpeta: {outdir}")

    if args.log:
        try:
            import csv
            with open(args.log, 'w', newline='', encoding='utf-8') as csvf:
                w = csv.writer(csvf)
                w.writerow(['url','ok','message'])
                for r in results:
                    w.writerow([r[0], 'OK' if r[1] else 'FAIL', r[2]])
            print(f"Log guardado en {args.log}")
        except Exception as e:
            print(f"No se pudo guardar log: {e}")


if __name__ == '__main__':
    main()
