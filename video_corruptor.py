"""视频损坏器：降低画质、硬削波音频，并输出可播放的 MP4。

图形界面：python video_corruptor.py
命令行：python video_corruptor.py input.mp4 -o output.mp4 --damage 60
依赖：FFmpeg（加入 PATH，或安装 imageio-ffmpeg）。
"""

import argparse
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


BG = "#F3F5F7"
PANEL = "#FFFFFF"
TEXT = "#17202A"
MUTED = "#667085"
ACCENT = "#2563EB"
GRID = "#DDE2E8"

LANGUAGE_NAMES = {
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
    "en": "English",
    "es": "Español",
}
DEFAULT_LANGUAGE = "zh-CN"
_current_language = DEFAULT_LANGUAGE

# 顺序与 LANGUAGE_NAMES 一致：简体中文、繁体中文、英语、西班牙语。
TRANSLATIONS = {
    "app_title": ("视频损坏器", "影片損壞器", "Video Corruptor", "Corruptor de vídeo"),
    "subtitle": (
        "画质损坏 · 10 段音频调频 · 音频硬削波 · 安卓绿色故障",
        "畫質損壞 · 10 段音訊等化 · 音訊硬削波 · Android 綠色故障",
        "Video damage · 10-band audio EQ · hard clipping · Android green glitch",
        "Daño de vídeo · ecualizador de 10 bandas · recorte duro · fallo verde de Android",
    ),
    "language": ("语言", "語言", "Language", "Idioma"),
    "files": ("输入与输出", "輸入與輸出", "Input and output", "Entrada y salida"),
    "choose_input": ("选择视频", "選擇影片", "Choose video", "Elegir vídeo"),
    "choose_output": ("输出位置", "輸出位置", "Output location", "Ubicación de salida"),
    "media_empty": ("尚未选择视频", "尚未選擇影片", "No video selected", "Ningún vídeo seleccionado"),
    "media_reading": (
        "正在读取视频信息……",
        "正在讀取影片資訊……",
        "Reading video information…",
        "Leyendo la información del vídeo…",
    ),
    "media_error": (
        "无法读取视频信息",
        "無法讀取影片資訊",
        "Could not read video information",
        "No se pudo leer la información del vídeo",
    ),
    "status_initial": (
        "请选择输入视频，调整效果后开始处理",
        "請選擇輸入影片，調整效果後開始處理",
        "Select an input video, adjust the effects, and start processing",
        "Selecciona un vídeo, ajusta los efectos e inicia el procesamiento",
    ),
    "damage": ("整体损坏程度", "整體損壞程度", "Overall damage", "Deterioro general"),
    "scale_none": ("0  不损坏", "0  不損壞", "0  None", "0  Ninguno"),
    "scale_noticeable": ("100  极严重", "100  極嚴重", "100  Extreme", "100  Extremo"),
    "scale_extreme": ("200  极限", "200  極限", "200  Maximum", "200  Máximo"),
    "green": ("绿色故障强度", "綠色故障強度", "Green glitch intensity", "Intensidad del fallo verde"),
    "green_normal": ("0  正常", "0  正常", "0  Normal", "0  Normal"),
    "green_full": ("100  全绿", "100  全綠", "100  Full green", "100  Todo verde"),
    "green_description": (
        "模拟安卓传视频时的经典绿色偏色，可独立调节。",
        "模擬 Android 傳輸影片時的經典綠色偏色，可獨立調整。",
        "Simulates the classic green tint from Android video transfers; adjustable independently.",
        "Simula el clásico tinte verde de las transferencias de vídeo en Android; se ajusta por separado.",
    ),
    "eq": ("音频损坏调频", "音訊損壞等化", "Audio damage EQ", "Ecualización de daño de audio"),
    "reset_eq": ("全部归零", "全部歸零", "Reset all", "Restablecer todo"),
    "eq_description": (
        "10 段均衡器 · 每段 +10 至 -10 dB（上方增强，下方衰减）",
        "10 段等化器 · 每段 +10 至 -10 dB（上方增強，下方衰減）",
        "10-band EQ · +10 to -10 dB per band (boost above, cut below)",
        "Ecualizador de 10 bandas · de +10 a -10 dB por banda (arriba refuerza, abajo atenúa)",
    ),
    "output_note": (
        "输出仍为正常可播放的 MP4；原视频不会被修改。无音轨时仅处理画面，调频设置不生效。",
        "輸出仍為正常可播放的 MP4；原影片不會被修改。無音軌時僅處理畫面，等化設定不會生效。",
        "The output remains a playable MP4 and the source is unchanged. Without audio, only video is processed and EQ has no effect.",
        "La salida sigue siendo un MP4 reproducible y el original no cambia. Sin audio, solo se procesa la imagen y el ecualizador no tiene efecto.",
    ),
    "start": ("开始损坏并导出", "開始損壞並匯出", "Damage and export", "Deteriorar y exportar"),
    "cancel": ("取消", "取消", "Cancel", "Cancelar"),
    "preview": ("视频预览", "影片預覽", "Video preview", "Vista previa"),
    "preview_original": ("原视频", "原影片", "Original", "Original"),
    "preview_effect": ("损坏效果", "損壞效果", "Damaged effect", "Efecto de deterioro"),
    "preview_generate": ("生成预览", "產生預覽", "Generate preview", "Generar vista previa"),
    "preview_play": ("播放", "播放", "Play", "Reproducir"),
    "preview_pause": ("暂停", "暫停", "Pause", "Pausar"),
    "preview_note": (
        "3 秒无声循环预览，仅用于查看画面；音频效果请导出后试听。",
        "3 秒無聲循環預覽，僅用於查看畫面；音訊效果請匯出後試聽。",
        "A three-second silent loop for comparing video effects; export the video to hear the audio.",
        "Un bucle silencioso de tres segundos para comparar la imagen; exporta el vídeo para escuchar el audio.",
    ),
    "preview_generating": (
        "正在生成预览……",
        "正在產生預覽……",
        "Generating preview…",
        "Generando la vista previa…",
    ),
    "preview_ready": (
        "预览已就绪，可播放或暂停",
        "預覽已就緒，可播放或暫停",
        "Preview ready; play or pause the comparison",
        "Vista previa lista; reproduce o pausa la comparación",
    ),
    "preview_failed": ("预览生成失败", "預覽產生失敗", "Preview failed", "Error al generar la vista previa"),
    "preview_no_frames": (
        "无法从视频中读取预览帧",
        "無法從影片讀取預覽影格",
        "No preview frames could be read from the video",
        "No se pudieron leer fotogramas del vídeo",
    ),
    "preview_incomplete": (
        "预览帧数据不完整",
        "預覽影格資料不完整",
        "Incomplete preview frame data",
        "Datos incompletos de fotogramas",
    ),
    "video_files": ("视频文件", "影片檔案", "Video files", "Archivos de vídeo"),
    "all_files": ("所有文件", "所有檔案", "All files", "Todos los archivos"),
    "choose_input_title": ("选择输入视频", "選擇輸入影片", "Select input video", "Seleccionar vídeo de entrada"),
    "default_output_name": ("损坏视频.mp4", "損壞影片.mp4", "damaged_video.mp4", "video_dañado.mp4"),
    "mp4_video": ("MP4 视频", "MP4 影片", "MP4 video", "Vídeo MP4"),
    "read_failed": ("读取失败", "讀取失敗", "Read failed", "Error de lectura"),
    "has_audio": ("有音轨", "有音軌", "Audio track", "Con audio"),
    "no_audio": ("无音轨", "無音軌", "No audio", "Sin audio"),
    "duration_unknown": ("时长未知", "時長未知", "Unknown duration", "Duración desconocida"),
    "video_ready": ("视频已就绪", "影片已就緒", "Video ready", "Vídeo listo"),
    "damage_none": ("不损坏", "不損壞", "None", "Ninguno"),
    "damage_very_light": ("轻微", "輕微", "Very light", "Muy leve"),
    "damage_light": ("较轻", "較輕", "Light", "Leve"),
    "damage_noticeable": ("明显", "明顯", "Noticeable", "Notable"),
    "damage_severe": ("严重", "嚴重", "Severe", "Severo"),
    "damage_extreme": ("极严重", "極嚴重", "Extreme", "Extremo"),
    "damage_maximum": ("极限", "極限", "Maximum", "Máximo"),
    "blur_pixels": ("{radius} 像素盒式模糊", "{radius} 像素盒式模糊", "{radius}-pixel box blur", "desenfoque de caja de {radius} px"),
    "blur_none": ("不额外模糊", "不額外模糊", "no extra blur", "sin desenfoque adicional"),
    "detail_video": (
        "画面：{factor:.1f} 倍降采样 + {blur}，压缩 CRF {crf}",
        "畫面：{factor:.1f} 倍降採樣 + {blur}，壓縮 CRF {crf}",
        "Video: {factor:.1f}× downsampling + {blur}, compression CRF {crf}",
        "Vídeo: reducción de resolución {factor:.1f}× + {blur}, compresión CRF {crf}",
    ),
    "detail_audio": (
        "音频：增益 +{gain:.1f} dB 后硬削波，AAC {bitrate} kbps",
        "音訊：增益 +{gain:.1f} dB 後硬削波，AAC {bitrate} kbps",
        "Audio: hard clipping after +{gain:.1f} dB gain, AAC {bitrate} kbps",
        "Audio: recorte duro tras una ganancia de +{gain:.1f} dB, AAC {bitrate} kbps",
    ),
    "missing_input_title": ("缺少输入", "缺少輸入", "Missing input", "Falta la entrada"),
    "missing_input": (
        "请先选择输入视频",
        "請先選擇輸入影片",
        "Select an input video first",
        "Selecciona primero un vídeo de entrada",
    ),
    "output_format": ("输出格式", "輸出格式", "Output format", "Formato de salida"),
    "input_error": ("输入错误", "輸入錯誤", "Input error", "Error de entrada"),
    "overwrite_title": ("确认覆盖", "確認覆蓋", "Confirm overwrite", "Confirmar sobrescritura"),
    "overwrite_prompt": (
        "输出文件已存在，是否覆盖？",
        "輸出檔案已存在，是否覆蓋？",
        "The output file already exists. Overwrite it?",
        "El archivo de salida ya existe. ¿Quieres sobrescribirlo?",
    ),
    "status_initializing": (
        "正在初始化 FFmpeg……",
        "正在初始化 FFmpeg……",
        "Initializing FFmpeg…",
        "Iniciando FFmpeg…",
    ),
    "status_cancelling": ("正在取消处理……", "正在取消處理……", "Cancelling…", "Cancelando…"),
    "status_processing": (
        "正在处理并合并音视频…… {value:.1f}%",
        "正在處理並合併影音…… {value:.1f}%",
        "Processing and muxing audio/video… {value:.1f}%",
        "Procesando y combinando audio y vídeo… {value:.1f}%",
    ),
    "status_success": ("处理完成：{path}", "處理完成：{path}", "Completed: {path}", "Completado: {path}"),
    "export_complete_title": ("导出完成", "匯出完成", "Export complete", "Exportación completada"),
    "export_complete_message": (
        "损坏视频已保存到：\n{path}",
        "損壞影片已儲存至：\n{path}",
        "The damaged video was saved to:\n{path}",
        "El vídeo deteriorado se guardó en:\n{path}",
    ),
    "status_cancelled": (
        "处理已取消，未保留未完成文件",
        "處理已取消，未保留未完成檔案",
        "Processing cancelled; no incomplete file was kept",
        "Procesamiento cancelado; no se conservó ningún archivo incompleto",
    ),
    "status_failed": ("处理失败", "處理失敗", "Processing failed", "Error de procesamiento"),
    "confirm_exit_title": ("确认退出", "確認結束", "Confirm exit", "Confirmar salida"),
    "confirm_exit": (
        "正在处理视频，确定取消并退出吗？",
        "正在處理影片，確定取消並結束嗎？",
        "A video is being processed. Cancel and exit?",
        "Se está procesando un vídeo. ¿Cancelar y salir?",
    ),
    "ffmpeg_not_found": (
        "未找到 FFmpeg。请安装 FFmpeg 并加入 PATH，或执行：python -m pip install imageio-ffmpeg",
        "找不到 FFmpeg。請安裝 FFmpeg 並加入 PATH，或執行：python -m pip install imageio-ffmpeg",
        "FFmpeg was not found. Install FFmpeg and add it to PATH, or run: python -m pip install imageio-ffmpeg",
        "No se encontró FFmpeg. Instálalo y añádelo a PATH, o ejecuta: python -m pip install imageio-ffmpeg",
    ),
    "no_video_stream": (
        "未检测到可处理的视频流，请确认文件未损坏且格式受支持",
        "未偵測到可處理的視訊串流，請確認檔案未損壞且格式受支援",
        "No processable video stream was detected. Check that the file is intact and the format is supported",
        "No se detectó una secuencia de vídeo procesable. Comprueba que el archivo esté intacto y que el formato sea compatible",
    ),
    "eq_numeric": (
        "均衡器增益必须是数字",
        "等化器增益必須是數字",
        "Equalizer gains must be numbers",
        "Las ganancias del ecualizador deben ser números",
    ),
    "eq_count": (
        "均衡器需要 {count} 个增益值",
        "等化器需要 {count} 個增益值",
        "The equalizer requires {count} gain values",
        "El ecualizador necesita {count} valores de ganancia",
    ),
    "eq_range": (
        "每段均衡器增益必须在 -10 到 +10 dB 之间",
        "每段等化器增益必須介於 -10 到 +10 dB 之間",
        "Each equalizer band gain must be between -10 and +10 dB",
        "La ganancia de cada banda debe estar entre -10 y +10 dB",
    ),
    "output_suffix": ("损坏", "損壞", "damaged", "dañado"),
    "input_not_found": (
        "输入视频不存在：{path}",
        "輸入影片不存在：{path}",
        "Input video does not exist: {path}",
        "El vídeo de entrada no existe: {path}",
    ),
    "output_over_source": (
        "输出文件不能覆盖原视频，请选择另一个文件名",
        "輸出檔案不能覆蓋原影片，請選擇另一個檔名",
        "The output cannot overwrite the source video; choose another filename",
        "La salida no puede sobrescribir el vídeo original; elige otro nombre",
    ),
    "output_mp4": (
        "输出文件必须使用 .mp4 扩展名",
        "輸出檔案必須使用 .mp4 副檔名",
        "The output file must use the .mp4 extension",
        "El archivo de salida debe usar la extensión .mp4",
    ),
    "damage_range": (
        "损坏程度必须在 0 到 200 之间",
        "損壞程度必須介於 0 到 200 之間",
        "Damage must be between 0 and 200",
        "El deterioro debe estar entre 0 y 200",
    ),
    "green_range": (
        "绿色故障强度必须在 0 到 100 之间",
        "綠色故障強度必須介於 0 到 100 之間",
        "Green glitch intensity must be between 0 and 100",
        "La intensidad del fallo verde debe estar entre 0 y 100",
    ),
    "no_ffmpeg_details": (
        "未返回详细错误信息",
        "未回傳詳細錯誤資訊",
        "No detailed error information was returned",
        "No se recibió información detallada del error",
    ),
    "ffmpeg_failed": (
        "FFmpeg 处理失败（退出代码 {code}）：\n{details}",
        "FFmpeg 處理失敗（結束代碼 {code}）：\n{details}",
        "FFmpeg processing failed (exit code {code}):\n{details}",
        "FFmpeg falló (código de salida {code}):\n{details}",
    ),
    "invalid_output": (
        "处理结束，但 FFmpeg 没有生成有效输出文件",
        "處理結束，但 FFmpeg 未產生有效輸出檔案",
        "Processing finished, but FFmpeg did not create a valid output file",
        "El procesamiento terminó, pero FFmpeg no creó un archivo de salida válido",
    ),
    "cli_description": (
        "视频模糊与绿色故障、10 段音频调频和硬削波，合并导出 MP4",
        "影片模糊與綠色故障、10 段音訊等化和硬削波，合併匯出 MP4",
        "Apply video blur and green glitch, 10-band audio EQ and hard clipping, then export MP4",
        "Aplica desenfoque y fallo verde, ecualizador de 10 bandas y recorte duro, y exporta a MP4",
    ),
    "input_help": (
        "输入视频路径；不提供时打开图形界面",
        "輸入影片路徑；未提供時開啟圖形介面",
        "Input video path; opens the graphical interface if omitted",
        "Ruta del vídeo de entrada; si se omite, se abre la interfaz gráfica",
    ),
    "output_help": ("输出 MP4 路径", "輸出 MP4 路徑", "Output MP4 path", "Ruta del MP4 de salida"),
    "damage_help": (
        "整体损坏程度 0-200，默认 60",
        "整體損壞程度 0-200，預設 60",
        "Overall damage from 0 to 200 (default: 60)",
        "Deterioro general de 0 a 200 (predeterminado: 60)",
    ),
    "green_help": (
        "绿色故障强度 0-100，默认 0",
        "綠色故障強度 0-100，預設 0",
        "Green glitch intensity from 0 to 100 (default: 0)",
        "Intensidad del fallo verde de 0 a 100 (predeterminado: 0)",
    ),
    "eq_help": (
        "20、50、100、200、500、1k、2k、5k、10k、20k Hz 的增益，每项 -10 至 +10 dB",
        "20、50、100、200、500、1k、2k、5k、10k、20k Hz 的增益，每項 -10 至 +10 dB",
        "Gains for 20, 50, 100, 200, 500, 1k, 2k, 5k, 10k, and 20k Hz; each from -10 to +10 dB",
        "Ganancias para 20, 50, 100, 200, 500, 1k, 2k, 5k, 10k y 20k Hz; cada una de -10 a +10 dB",
    ),
    "language_help": (
        "界面与消息语言：zh-CN、zh-TW、en、es",
        "介面與訊息語言：zh-CN、zh-TW、en、es",
        "Interface and message language: zh-CN, zh-TW, en, es",
        "Idioma de la interfaz y los mensajes: zh-CN, zh-TW, en, es",
    ),
    "cli_progress": ("处理进度：{value:5.1f}%", "處理進度：{value:5.1f}%", "Progress: {value:5.1f}%", "Progreso: {value:5.1f}%"),
    "cli_cancelled": ("已取消", "已取消", "Cancelled", "Cancelado"),
    "cli_error": ("错误：{error}", "錯誤：{error}", "Error: {error}", "Error: {error}"),
    "cli_complete": ("处理完成：{result}", "處理完成：{result}", "Completed: {result}", "Completado: {result}"),
}
_language_codes = tuple(LANGUAGE_NAMES)
VIDEO_PATTERN = "*.mp4 *.mov *.mkv *.avi *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.ts"
EQ_FREQUENCIES = (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000)
PREVIEW_WIDTH = 320
PREVIEW_HEIGHT = 180
PREVIEW_FPS = 10
PREVIEW_SECONDS = 3
PREVIEW_FRAME_SIZE = PREVIEW_WIDTH * PREVIEW_HEIGHT * 3


def set_language(language):
    if language not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported language: {language}")
    global _current_language
    _current_language = language


def tr(key, **values):
    translations = TRANSLATIONS[key]
    text = translations[_language_codes.index(_current_language)]
    return text.format(**values) if values else text


def video_filetypes():
    return [(tr("video_files"), VIDEO_PATTERN), (tr("all_files"), "*.*")]


@dataclass(frozen=True)
class MediaInfo:
    width: int
    height: int
    duration: float
    has_audio: bool


@dataclass(frozen=True)
class DamageSettings:
    downscale_factor: float
    blur_radius: int
    crf: int
    audio_gain_db: float
    audio_bitrate_kbps: int


class ProcessingCancelled(Exception):
    pass


def find_ffmpeg():
    # 优先使用新版内嵌后端，避免旧版 FFmpeg 无法解码新格式视频。
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        pass

    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    raise RuntimeError(tr("ffmpeg_not_found"))


def _creation_flags():
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _parse_clock(value):
    match = re.match(r"(\d+):(\d+):(\d+(?:\.\d+)?)", value)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def probe_media(input_path, ffmpeg_path=None):
    input_path = Path(input_path)
    ffmpeg_path = ffmpeg_path or find_ffmpeg()
    result = subprocess.run(
        [ffmpeg_path, "-i", str(input_path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        creationflags=_creation_flags(),
    )
    text = result.stdout
    video_match = re.search(
        r"Video:[^\r\n]*?\b(\d{2,6})x(\d{2,6})\b", text
    )
    if not video_match:
        raise ValueError(tr("no_video_stream"))

    duration = 0.0
    duration_match = re.search(r"Duration:\s*(\d+:\d+:\d+(?:\.\d+)?)", text)
    if duration_match:
        duration = _parse_clock(duration_match.group(1)) or 0.0

    return MediaInfo(
        width=int(video_match.group(1)),
        height=int(video_match.group(2)),
        duration=duration,
        has_audio=re.search(r"Stream[^\r\n]*Audio:", text) is not None,
    )


def calculate_damage(damage):
    damage = max(0, min(200, int(round(float(damage)))))
    amount = damage / 100.0
    return DamageSettings(
        downscale_factor=1.0 + 19.0 * amount ** 1.5,
        blur_radius=int(round(6 * amount)),
        crf=min(51, int(round(18 + 28 * amount))),
        audio_gain_db=30.0 * amount,
        audio_bitrate_kbps=max(32, int(round(160 - 96 * amount))),
    )


def normalize_eq_gains(eq_gains=None):
    if eq_gains is None:
        return (0.0,) * len(EQ_FREQUENCIES)
    try:
        gains = tuple(float(gain) for gain in eq_gains)
    except (TypeError, ValueError) as exc:
        raise ValueError(tr("eq_numeric")) from exc
    if len(gains) != len(EQ_FREQUENCIES):
        raise ValueError(tr("eq_count", count=len(EQ_FREQUENCIES)))
    if any(not -10 <= gain <= 10 for gain in gains):
        raise ValueError(tr("eq_range"))
    return gains


def _even_dimension(value):
    return max(2, int(round(value)) // 2 * 2)


def build_video_filter(info, settings, green=0):
    output_width = _even_dimension(info.width)
    output_height = _even_dimension(info.height)
    small_width = max(16, _even_dimension(info.width / settings.downscale_factor))
    small_height = max(16, _even_dimension(info.height / settings.downscale_factor))
    filters = [
        f"scale={small_width}:{small_height}:flags=area",
        f"scale={output_width}:{output_height}:flags=bilinear",
    ]
    if settings.blur_radius:
        chroma_radius = max(1, settings.blur_radius // 2)
        filters.append(
            f"boxblur=lr={settings.blur_radius}:lp=1:"
            f"cr={chroma_radius}:cp=1"
        )
    green_amount = float(green) / 100.0
    if green_amount:
        # 按亮度生成绿色通道，模拟安卓视频传输异常时的绿色偏色。
        filters.append(
            "colorchannelmixer="
            f"rr={1 - green_amount:.6f}:"
            f"rg={0.299 * green_amount:.6f}:"
            f"gg={1 - 0.413 * green_amount:.6f}:"
            f"gb={0.114 * green_amount:.6f}:"
            f"bb={1 - green_amount:.6f}"
        )
    filters.append("format=yuv420p")
    return ",".join(filters)


def decode_preview_frames(input_path, ffmpeg_path, video_filter=None, cancel_event=None):
    filters = []
    if video_filter:
        filters.append(video_filter)
    filters.extend(
        [
            f"fps={PREVIEW_FPS}",
            f"scale={PREVIEW_WIDTH}:{PREVIEW_HEIGHT}:"
            "force_original_aspect_ratio=decrease",
            f"pad={PREVIEW_WIDTH}:{PREVIEW_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black",
            "setsar=1",
        ]
    )
    command = [
        ffmpeg_path,
        "-v",
        "error",
        "-ss",
        "0",
        "-i",
        str(input_path),
        "-map",
        "0:v:0",
        "-t",
        str(PREVIEW_SECONDS),
        "-an",
        "-sn",
        "-dn",
        "-vf",
        ",".join(filters),
        "-c:v",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=_creation_flags(),
    )
    frames = []
    try:
        while True:
            if cancel_event and cancel_event.is_set():
                process.terminate()
                raise ProcessingCancelled
            frame = process.stdout.read(PREVIEW_FRAME_SIZE)
            if not frame:
                break
            if len(frame) != PREVIEW_FRAME_SIZE:
                raise RuntimeError(tr("preview_incomplete"))
            frames.append(frame)
        error_details = process.stderr.read().decode("utf-8", errors="replace").strip()
        return_code = process.wait()
        if cancel_event and cancel_event.is_set():
            raise ProcessingCancelled
        if return_code != 0:
            raise RuntimeError(
                tr(
                    "ffmpeg_failed",
                    code=return_code,
                    details=error_details or tr("no_ffmpeg_details"),
                )
            )
        if not frames:
            raise RuntimeError(tr("preview_no_frames"))
        return frames
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()


def build_audio_filter(settings, eq_gains=None):
    gains = normalize_eq_gains(eq_gains)
    filters = []
    if any(gain for gain in gains):
        # 统一采样率，确保 20 kHz 频段不会超出输入的奈奎斯特频率。
        filters.append("aresample=48000")
        for frequency, gain in zip(EQ_FREQUENCIES, gains):
            if gain:
                filters.append(
                    f"equalizer=f={frequency}:t=q:w=1:g={gain:.2f}"
                )
    # 转为有符号 16 位 PCM 时，超出 ±1 的采样会被硬性截断。
    gain_linear = 10.0 ** (settings.audio_gain_db / 20.0)
    filters.extend([f"volume={gain_linear:.8f}", "aformat=sample_fmts=s16"])
    return ",".join(filters)


def default_output_path(input_path):
    input_path = Path(input_path)
    return input_path.with_name(f"{input_path.stem}_{tr('output_suffix')}.mp4")


def corrupt_video(
    input_path,
    output_path,
    damage=60,
    progress_callback=None,
    cancel_event=None,
    green=0,
    eq_gains=None,
):
    input_path = Path(input_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()
    if not input_path.is_file():
        raise ValueError(tr("input_not_found", path=input_path))
    if input_path == output_path:
        raise ValueError(tr("output_over_source"))
    if output_path.suffix.lower() != ".mp4":
        raise ValueError(tr("output_mp4"))
    if not 0 <= float(damage) <= 200:
        raise ValueError(tr("damage_range"))
    if not 0 <= float(green) <= 100:
        raise ValueError(tr("green_range"))
    eq_gains = normalize_eq_gains(eq_gains)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = find_ffmpeg()
    info = probe_media(input_path, ffmpeg_path)
    settings = calculate_damage(damage)
    video_filter = build_video_filter(info, settings, green)

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0:v:0",
    ]
    if info.has_audio:
        command.extend(["-map", "0:a:0"])
    command.extend(
        [
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            str(settings.crf),
            "-pix_fmt",
            "yuv420p",
        ]
    )
    if info.has_audio:
        command.extend(
            [
                "-af",
                build_audio_filter(settings, eq_gains),
                "-c:a",
                "aac",
                "-b:a",
                f"{settings.audio_bitrate_kbps}k",
                "-strict",
                "-2",
            ]
        )
    command.extend(["-movflags", "+faststart"])

    temporary_path = output_path.with_name(
        f".{output_path.stem}.{os.getpid()}.{threading.get_ident()}.partial.mp4"
    )
    command.extend(["-progress", "pipe:1", "-nostats", str(temporary_path)])

    if progress_callback:
        progress_callback(0.0)
    process = None
    logs = deque(maxlen=24)
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=_creation_flags(),
        )
        for raw_line in process.stdout:
            line = raw_line.strip()
            if cancel_event and cancel_event.is_set():
                process.terminate()
                raise ProcessingCancelled
            if line.startswith("out_time=") and info.duration > 0:
                seconds = _parse_clock(line.split("=", 1)[1])
                if seconds is not None and progress_callback:
                    progress_callback(min(99.0, seconds / info.duration * 100.0))
            elif line == "progress=end" and progress_callback:
                progress_callback(99.0)
            elif line and not re.match(r"^[a-z_]+=", line):
                logs.append(line)

        return_code = process.wait()
        if cancel_event and cancel_event.is_set():
            raise ProcessingCancelled
        if return_code != 0:
            details = "\n".join(list(logs)[-12:]) or tr("no_ffmpeg_details")
            raise RuntimeError(
                tr("ffmpeg_failed", code=return_code, details=details)
            )
        if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
            raise RuntimeError(tr("invalid_output"))
        os.replace(temporary_path, output_path)
        if progress_callback:
            progress_callback(100.0)
        return output_path
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()
            if process.stdout:
                process.stdout.close()
        if temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass


def format_duration(seconds):
    seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class VideoCorruptorApp(tk.Tk):
    def __init__(
        self,
        initial_damage=60,
        initial_green=0,
        initial_eq_gains=None,
        initial_language=DEFAULT_LANGUAGE,
    ):
        super().__init__()
        set_language(initial_language)
        self.title(tr("app_title"))
        self.geometry("1100x760")
        self.minsize(980, 700)
        self.configure(background=BG)

        self.media_info = None
        self.media_state = "empty"
        self.processing = False
        self.cancel_event = threading.Event()
        self.events = queue.Queue()
        self.output_is_automatic = True
        self.main = None
        self.preview_window = None
        self.preview_generation = 0
        self.preview_cancel_event = threading.Event()
        self.preview_building = False
        self.preview_playing = False
        self.preview_after_id = None
        self.preview_original_frames = []
        self.preview_effect_frames = []
        self.preview_frame_index = 0
        self.preview_images = [None, None]
        self.preview_status_key = None

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.language_var = tk.StringVar(value=LANGUAGE_NAMES[initial_language])
        self.damage_var = tk.DoubleVar(value=initial_damage)
        self.damage_text = tk.StringVar()
        self.green_var = tk.DoubleVar(value=initial_green)
        self.green_text = tk.StringVar()
        initial_eq_gains = normalize_eq_gains(initial_eq_gains)
        self.eq_vars = [tk.DoubleVar(value=gain) for gain in initial_eq_gains]
        self.eq_value_vars = [tk.StringVar() for _ in EQ_FREQUENCIES]
        self.eq_scales = []
        self.detail_text = tk.StringVar()
        self.media_text = tk.StringVar()
        self.status_key = "status_initial"
        self.status_values = {}
        self.status_text = tk.StringVar()
        self.preview_status_text = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0.0)

        self._configure_styles()
        self._build_ui()
        self._refresh_ui_text()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self._poll_events)

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=BG)
        style.configure("Card.TFrame", background=PANEL)
        style.configure(
            "TLabel",
            background=BG,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=BG,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=BG,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Card.TLabel",
            background=PANEL,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "CardMuted.TLabel",
            background=PANEL,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Damage.TLabel",
            background=PANEL,
            foreground=ACCENT,
            font=("Microsoft YaHei UI", 14, "bold"),
        )
        style.configure(
            "Green.TLabel",
            background=PANEL,
            foreground="#15803D",
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(12, 8))
        style.configure(
            "Accent.TButton",
            font=("Microsoft YaHei UI", 10, "bold"),
            padding=(18, 9),
            background=ACCENT,
            foreground="#FFFFFF",
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#1D4ED8"), ("disabled", "#93C5FD")],
            foreground=[("disabled", "#EFF6FF")],
        )
        style.configure(
            "Accent.Horizontal.TProgressbar",
            background=ACCENT,
            troughcolor=GRID,
            bordercolor=GRID,
        )

    def _build_ui(self):
        if self.main is not None:
            self.main.destroy()
        self.eq_scales = []
        main = ttk.Frame(self, style="App.TFrame", padding=18)
        self.main = main
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main, style="App.TFrame")
        header.pack(fill=tk.X)
        ttk.Label(header, text=tr("app_title"), style="Title.TLabel").pack(side=tk.LEFT)
        language_controls = ttk.Frame(header, style="App.TFrame")
        language_controls.pack(side=tk.RIGHT)
        ttk.Label(language_controls, text=tr("language")).pack(side=tk.LEFT, padx=(0, 8))
        self.language_combobox = ttk.Combobox(
            language_controls,
            textvariable=self.language_var,
            values=tuple(LANGUAGE_NAMES.values()),
            state="readonly",
            width=12,
        )
        self.language_combobox.pack(side=tk.LEFT)
        self.language_combobox.bind("<<ComboboxSelected>>", self.on_language_change)
        ttk.Label(
            main,
            text=tr("subtitle"),
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 14))

        files = ttk.LabelFrame(main, text=tr("files"), padding=12)
        files.pack(fill=tk.X)
        files.columnconfigure(0, weight=1)
        self.input_entry = ttk.Entry(files, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.input_button = ttk.Button(
            files, text=tr("choose_input"), command=self.choose_input
        )
        self.input_button.grid(row=0, column=1)
        self.output_entry = ttk.Entry(files, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(10, 0))
        self.output_button = ttk.Button(
            files, text=tr("choose_output"), command=self.choose_output
        )
        self.output_button.grid(row=1, column=1, pady=(10, 0))
        ttk.Label(
            files,
            textvariable=self.media_text,
            style="Subtitle.TLabel",
            wraplength=980,
            justify=tk.LEFT,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        effects = ttk.Frame(main, style="App.TFrame")
        effects.pack(fill=tk.X, pady=(14, 0))
        effects.columnconfigure(0, weight=1)
        effects.columnconfigure(1, weight=2)

        damage_panel = ttk.Frame(effects, style="Card.TFrame", padding=16)
        damage_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        damage_header = ttk.Frame(damage_panel, style="Card.TFrame")
        damage_header.pack(fill=tk.X)
        ttk.Label(damage_header, text=tr("damage"), style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            damage_header, textvariable=self.damage_text, style="Damage.TLabel"
        ).pack(side=tk.RIGHT)
        self.damage_scale = ttk.Scale(
            damage_panel,
            from_=0,
            to=200,
            variable=self.damage_var,
            command=self._update_damage,
        )
        self.damage_scale.pack(fill=tk.X, pady=(14, 6))
        scale_labels = ttk.Frame(damage_panel, style="Card.TFrame")
        scale_labels.pack(fill=tk.X)
        ttk.Label(scale_labels, text=tr("scale_none"), style="CardMuted.TLabel").pack(side=tk.LEFT)
        ttk.Label(scale_labels, text=tr("scale_noticeable"), style="CardMuted.TLabel").pack(side=tk.LEFT, expand=True)
        ttk.Label(scale_labels, text=tr("scale_extreme"), style="CardMuted.TLabel").pack(side=tk.RIGHT)
        ttk.Label(
            damage_panel,
            textvariable=self.detail_text,
            style="CardMuted.TLabel",
            justify=tk.LEFT,
            wraplength=310,
        ).pack(anchor="w", pady=(12, 0))

        ttk.Separator(damage_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=14)
        green_header = ttk.Frame(damage_panel, style="Card.TFrame")
        green_header.pack(fill=tk.X)
        ttk.Label(green_header, text=tr("green"), style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            green_header, textvariable=self.green_text, style="Green.TLabel"
        ).pack(side=tk.RIGHT)
        self.green_scale = ttk.Scale(
            damage_panel,
            from_=0,
            to=100,
            variable=self.green_var,
            command=self._update_green,
        )
        self.green_scale.pack(fill=tk.X, pady=(12, 6))
        green_labels = ttk.Frame(damage_panel, style="Card.TFrame")
        green_labels.pack(fill=tk.X)
        ttk.Label(green_labels, text=tr("green_normal"), style="CardMuted.TLabel").pack(side=tk.LEFT)
        ttk.Label(green_labels, text=tr("green_full"), style="CardMuted.TLabel").pack(side=tk.RIGHT)
        ttk.Label(
            damage_panel,
            text=tr("green_description"),
            style="CardMuted.TLabel",
            wraplength=310,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(10, 0))

        eq_panel = ttk.Frame(effects, style="Card.TFrame", padding=16)
        eq_panel.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        eq_header = ttk.Frame(eq_panel, style="Card.TFrame")
        eq_header.pack(fill=tk.X)
        ttk.Label(eq_header, text=tr("eq"), style="Card.TLabel").pack(side=tk.LEFT)
        self.reset_eq_button = ttk.Button(
            eq_header, text=tr("reset_eq"), command=self.reset_eq
        )
        self.reset_eq_button.pack(side=tk.RIGHT)
        ttk.Label(
            eq_panel,
            text=tr("eq_description"),
            style="CardMuted.TLabel",
        ).pack(anchor="w", pady=(4, 0))
        sliders = ttk.Frame(eq_panel, style="Card.TFrame")
        sliders.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        for index, frequency in enumerate(EQ_FREQUENCIES):
            sliders.columnconfigure(index, weight=1)
            ttk.Label(
                sliders,
                textvariable=self.eq_value_vars[index],
                style="CardMuted.TLabel",
                anchor=tk.CENTER,
                width=7,
            ).grid(row=0, column=index, pady=(0, 4))
            scale = ttk.Scale(
                sliders,
                orient=tk.VERTICAL,
                from_=10,
                to=-10,
                length=160,
                variable=self.eq_vars[index],
                command=lambda _value, i=index: self._update_eq_label(i),
            )
            scale.grid(row=1, column=index, sticky="ns")
            frequency_text = (
                f"{frequency} Hz" if frequency < 1000 else f"{frequency // 1000} kHz"
            )
            ttk.Label(
                sliders,
                text=frequency_text,
                style="CardMuted.TLabel",
                anchor=tk.CENTER,
                width=7,
            ).grid(row=2, column=index, pady=(5, 0))
            self.eq_scales.append(scale)

        ttk.Label(
            main,
            text=tr("output_note"),
            style="Subtitle.TLabel",
            wraplength=1020,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(12, 12))

        actions = ttk.Frame(main, style="App.TFrame")
        actions.pack(fill=tk.X)
        self.start_button = ttk.Button(
            actions,
            text=tr("start"),
            style="Accent.TButton",
            command=self.start_processing,
        )
        self.start_button.pack(side=tk.LEFT)
        self.cancel_button = ttk.Button(
            actions,
            text=tr("cancel"),
            command=self.cancel_processing,
            state=tk.DISABLED,
        )
        self.cancel_button.pack(side=tk.LEFT, padx=(8, 0))
        self.preview_button = ttk.Button(
            actions,
            text=tr("preview"),
            command=self.open_preview,
        )
        self.preview_button.pack(side=tk.LEFT, padx=(8, 0))

        self.progress_bar = ttk.Progressbar(
            main,
            style="Accent.Horizontal.TProgressbar",
            maximum=100,
            variable=self.progress_var,
        )
        self.progress_bar.pack(fill=tk.X, pady=(14, 7))
        ttk.Label(main, textvariable=self.status_text, style="Subtitle.TLabel").pack(anchor="w")

    def on_language_change(self, _event=None):
        selected_name = self.language_var.get()
        language = next(
            code for code, name in LANGUAGE_NAMES.items() if name == selected_name
        )
        set_language(language)
        if self.output_is_automatic and self.input_var.get().strip():
            self.output_var.set(str(default_output_path(self.input_var.get().strip())))
        self._build_ui()
        self._refresh_ui_text()

    def _refresh_ui_text(self):
        self.title(tr("app_title"))
        self._update_damage()
        self._update_green()
        for index in range(len(EQ_FREQUENCIES)):
            self._update_eq_label(index)
        self._refresh_media_text()
        self._refresh_status()
        self._refresh_preview_language()

    def _set_status(self, key, **values):
        self.status_key = key
        self.status_values = values
        self._refresh_status()

    def _refresh_status(self):
        self.status_text.set(tr(self.status_key, **self.status_values))

    def _refresh_media_text(self):
        if self.media_state != "ready" or self.media_info is None:
            self.media_text.set(tr(f"media_{self.media_state}"))
            return
        info = self.media_info
        audio_text = tr("has_audio" if info.has_audio else "no_audio")
        duration_text = (
            format_duration(info.duration) if info.duration else tr("duration_unknown")
        )
        self.media_text.set(
            f"{info.width} × {info.height}    {duration_text}    {audio_text}"
        )

    def open_preview(self):
        input_path = self.input_var.get().strip()
        if not input_path:
            messagebox.showwarning(
                tr("missing_input_title"), tr("missing_input"), parent=self
            )
            return
        if not Path(input_path).is_file():
            messagebox.showerror(
                tr("input_error"),
                tr("input_not_found", path=input_path),
                parent=self,
            )
            return
        if self.preview_window is not None:
            self.preview_window.lift()
            self.preview_window.focus_set()
            return

        window = tk.Toplevel(self)
        self.preview_window = window
        window.title(tr("preview"))
        window.geometry("720x390")
        window.minsize(700, 360)
        window.configure(background=BG)
        window.transient(self)
        window.protocol("WM_DELETE_WINDOW", self.close_preview)

        container = ttk.Frame(window, style="App.TFrame", padding=16)
        container.pack(fill=tk.BOTH, expand=True)
        comparison = ttk.Frame(container, style="App.TFrame")
        comparison.pack(fill=tk.BOTH, expand=True)

        original_panel = ttk.Frame(comparison, style="App.TFrame")
        original_panel.pack(side=tk.LEFT, expand=True, padx=(0, 6))
        self.preview_original_title = ttk.Label(
            original_panel, text=tr("preview_original"), style="Subtitle.TLabel"
        )
        self.preview_original_title.pack(pady=(0, 6))
        original_frame = tk.Frame(
            original_panel,
            width=PREVIEW_WIDTH,
            height=PREVIEW_HEIGHT,
            background="#111827",
        )
        original_frame.pack()
        original_frame.pack_propagate(False)
        self.preview_original_label = tk.Label(original_frame, background="#111827")
        self.preview_original_label.pack(expand=True)

        effect_panel = ttk.Frame(comparison, style="App.TFrame")
        effect_panel.pack(side=tk.LEFT, expand=True, padx=(6, 0))
        self.preview_effect_title = ttk.Label(
            effect_panel, text=tr("preview_effect"), style="Subtitle.TLabel"
        )
        self.preview_effect_title.pack(pady=(0, 6))
        effect_frame = tk.Frame(
            effect_panel,
            width=PREVIEW_WIDTH,
            height=PREVIEW_HEIGHT,
            background="#111827",
        )
        effect_frame.pack()
        effect_frame.pack_propagate(False)
        self.preview_effect_label = tk.Label(effect_frame, background="#111827")
        self.preview_effect_label.pack(expand=True)

        controls = ttk.Frame(container, style="App.TFrame")
        controls.pack(fill=tk.X, pady=(14, 8))
        self.preview_generate_button = ttk.Button(
            controls, text=tr("preview_generate"), command=self.generate_preview
        )
        self.preview_generate_button.pack(side=tk.LEFT)
        self.preview_play_button = ttk.Button(
            controls,
            text=tr("preview_play"),
            command=self.toggle_preview_playback,
            state=tk.DISABLED,
        )
        self.preview_play_button.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(
            container,
            textvariable=self.preview_status_text,
            style="Subtitle.TLabel",
            wraplength=660,
        ).pack(fill=tk.X)
        self.preview_note_label = ttk.Label(
            container,
            text=tr("preview_note"),
            style="Subtitle.TLabel",
            wraplength=660,
            justify=tk.LEFT,
        )
        self.preview_note_label.pack(fill=tk.X, pady=(6, 0))
        self.generate_preview()

    def close_preview(self):
        self.preview_generation += 1
        self.preview_cancel_event.set()
        self.preview_building = False
        self._stop_preview_playback()
        window = self.preview_window
        self.preview_window = None
        if window is not None and window.winfo_exists():
            window.destroy()
        self.preview_original_frames = []
        self.preview_effect_frames = []
        self.preview_images = [None, None]
        self.preview_status_key = None
        self.preview_status_text.set("")

    def generate_preview(self):
        if self.preview_window is None or self.preview_building:
            return
        input_path = self.input_var.get().strip()
        if not Path(input_path).is_file():
            self._preview_failed(
                self.preview_generation, tr("input_not_found", path=input_path)
            )
            return

        self._stop_preview_playback()
        self.preview_cancel_event.set()
        cancel_event = threading.Event()
        self.preview_cancel_event = cancel_event
        self.preview_generation += 1
        generation = self.preview_generation
        self.preview_building = True
        self.preview_generate_button.configure(state=tk.DISABLED)
        self.preview_play_button.configure(state=tk.DISABLED)
        self._set_preview_status("preview_generating")
        damage = int(round(float(self.damage_var.get())))
        green = float(self.green_var.get())
        threading.Thread(
            target=self._preview_worker,
            args=(generation, input_path, damage, green, cancel_event),
            daemon=True,
        ).start()

    def _preview_worker(self, generation, input_path, damage, green, cancel_event):
        try:
            ffmpeg_path = find_ffmpeg()
            info = probe_media(input_path, ffmpeg_path)
            original_frames = decode_preview_frames(
                input_path, ffmpeg_path, cancel_event=cancel_event
            )
            effect_filter = build_video_filter(
                info, calculate_damage(damage), green
            )
            effect_frames = decode_preview_frames(
                input_path,
                ffmpeg_path,
                video_filter=effect_filter,
                cancel_event=cancel_event,
            )
            if cancel_event.is_set():
                raise ProcessingCancelled
            self.events.put(
                ("preview_ready", (generation, original_frames, effect_frames))
            )
        except ProcessingCancelled:
            pass
        except Exception as exc:
            self.events.put(("preview_error", (generation, str(exc))))

    def _preview_ready(self, generation, original_frames, effect_frames):
        if generation != self.preview_generation or self.preview_window is None:
            return
        frame_count = min(len(original_frames), len(effect_frames))
        if not frame_count:
            self._preview_failed(generation, tr("preview_no_frames"))
            return
        self.preview_original_frames = original_frames[:frame_count]
        self.preview_effect_frames = effect_frames[:frame_count]
        self.preview_frame_index = 0
        self.preview_building = False
        self.preview_generate_button.configure(state=tk.NORMAL)
        self.preview_play_button.configure(state=tk.NORMAL)
        self._show_preview_frame()
        self._set_preview_status("preview_ready")

    def _preview_failed(self, generation, error):
        if generation != self.preview_generation or self.preview_window is None:
            return
        self.preview_building = False
        self.preview_generate_button.configure(state=tk.NORMAL)
        self.preview_play_button.configure(state=tk.DISABLED)
        self._set_preview_status("preview_failed")
        messagebox.showerror(
            tr("preview_failed"), error, parent=self.preview_window
        )

    def _show_preview_frame(self):
        if self.preview_window is None or not self.preview_original_frames:
            return
        index = self.preview_frame_index % len(self.preview_original_frames)
        header = (
            f"P6\n{PREVIEW_WIDTH} {PREVIEW_HEIGHT}\n255\n".encode("ascii")
        )
        self.preview_images = [
            tk.PhotoImage(data=header + self.preview_original_frames[index]),
            tk.PhotoImage(data=header + self.preview_effect_frames[index]),
        ]
        self.preview_original_label.configure(image=self.preview_images[0])
        self.preview_effect_label.configure(image=self.preview_images[1])

    def toggle_preview_playback(self):
        if self.preview_playing:
            self._stop_preview_playback()
            return
        if not self.preview_original_frames or self.preview_window is None:
            return
        self.preview_playing = True
        self.preview_play_button.configure(text=tr("preview_pause"))
        self.preview_after_id = self.after(
            round(1000 / PREVIEW_FPS), self._advance_preview
        )

    def _stop_preview_playback(self):
        self.preview_playing = False
        if self.preview_after_id is not None:
            self.after_cancel(self.preview_after_id)
            self.preview_after_id = None
        if self.preview_window is not None:
            self.preview_play_button.configure(text=tr("preview_play"))

    def _advance_preview(self):
        self.preview_after_id = None
        if not self.preview_playing or self.preview_window is None:
            return
        self.preview_frame_index = (
            self.preview_frame_index + 1
        ) % len(self.preview_original_frames)
        self._show_preview_frame()
        self.preview_after_id = self.after(
            round(1000 / PREVIEW_FPS), self._advance_preview
        )

    def _set_preview_status(self, key):
        self.preview_status_key = key
        self.preview_status_text.set(tr(key))

    def _refresh_preview_language(self):
        if self.preview_window is None:
            return
        self.preview_window.title(tr("preview"))
        self.preview_original_title.configure(text=tr("preview_original"))
        self.preview_effect_title.configure(text=tr("preview_effect"))
        self.preview_generate_button.configure(text=tr("preview_generate"))
        self.preview_play_button.configure(
            text=tr("preview_pause" if self.preview_playing else "preview_play")
        )
        self.preview_note_label.configure(text=tr("preview_note"))
        if self.preview_status_key:
            self.preview_status_text.set(tr(self.preview_status_key))

    def choose_input(self):
        path = filedialog.askopenfilename(
            parent=self, title=tr("choose_input_title"), filetypes=video_filetypes()
        )
        if path:
            self.load_input(path)

    def load_input(self, path):
        self.close_preview()
        self.input_var.set(path)
        if self.output_is_automatic or not self.output_var.get().strip():
            self.output_var.set(str(default_output_path(path)))
            self.output_is_automatic = True
        self.media_info = None
        self.media_state = "reading"
        self._refresh_media_text()
        self.update_idletasks()
        try:
            self.media_info = probe_media(path)
        except Exception as exc:
            self.media_state = "error"
            self._refresh_media_text()
            messagebox.showerror(tr("read_failed"), str(exc), parent=self)
            return
        self.media_state = "ready"
        self._refresh_media_text()
        self._set_status("video_ready")

    def choose_output(self):
        current = self.output_var.get().strip()
        initial_file = Path(current).name if current else tr("default_output_name")
        path = filedialog.asksaveasfilename(
            parent=self,
            title=tr("choose_output"),
            defaultextension=".mp4",
            initialfile=initial_file,
            filetypes=[(tr("mp4_video"), "*.mp4")],
        )
        if path:
            self.output_var.set(path)
            self.output_is_automatic = False

    def _update_damage(self, _value=None):
        damage = int(round(float(self.damage_var.get())))
        settings = calculate_damage(damage)
        if damage == 0:
            level_key = "damage_none"
        elif damage <= 20:
            level_key = "damage_very_light"
        elif damage <= 40:
            level_key = "damage_light"
        elif damage <= 60:
            level_key = "damage_noticeable"
        elif damage <= 80:
            level_key = "damage_severe"
        elif damage <= 100:
            level_key = "damage_extreme"
        else:
            level_key = "damage_maximum"
        self.damage_text.set(f"{damage}% · {tr(level_key)}")
        blur_text = (
            tr("blur_pixels", radius=settings.blur_radius)
            if settings.blur_radius
            else tr("blur_none")
        )
        video_details = tr(
            "detail_video",
            factor=settings.downscale_factor,
            blur=blur_text,
            crf=settings.crf,
        )
        audio_details = tr(
            "detail_audio",
            gain=settings.audio_gain_db,
            bitrate=settings.audio_bitrate_kbps,
        )
        self.detail_text.set(f"{video_details}\n{audio_details}")

    def _update_green(self, _value=None):
        self.green_text.set(f"{int(round(float(self.green_var.get())))}%")

    def _update_eq_label(self, index, _value=None):
        self.eq_value_vars[index].set(f"{float(self.eq_vars[index].get()):+.1f} dB")

    def reset_eq(self):
        for index, variable in enumerate(self.eq_vars):
            variable.set(0.0)
            self._update_eq_label(index)

    def start_processing(self):
        if self.processing:
            return
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()
        if not input_path:
            messagebox.showwarning(
                tr("missing_input_title"), tr("missing_input"), parent=self
            )
            return
        if not output_path:
            output_path = str(default_output_path(input_path))
            self.output_var.set(output_path)
        if Path(output_path).suffix.lower() != ".mp4":
            messagebox.showwarning(
                tr("output_format"), tr("output_mp4"), parent=self
            )
            return
        if Path(input_path).resolve() == Path(output_path).resolve():
            messagebox.showwarning(
                tr("choose_output"), tr("output_over_source"), parent=self
            )
            return
        if not Path(input_path).is_file():
            messagebox.showerror(
                tr("input_error"),
                tr("input_not_found", path=input_path),
                parent=self,
            )
            return
        if Path(output_path).exists() and not messagebox.askyesno(
            tr("overwrite_title"), tr("overwrite_prompt"), parent=self
        ):
            return

        self.close_preview()
        self.processing = True
        self.cancel_event.clear()
        self.progress_var.set(0.0)
        self._set_status("status_initializing")
        self._set_controls_enabled(False)
        damage = int(round(float(self.damage_var.get())))
        green = float(self.green_var.get())
        eq_gains = tuple(float(variable.get()) for variable in self.eq_vars)
        threading.Thread(
            target=self._processing_worker,
            args=(input_path, output_path, damage, green, eq_gains),
            daemon=True,
        ).start()

    def _processing_worker(self, input_path, output_path, damage, green, eq_gains):
        try:
            result = corrupt_video(
                input_path,
                output_path,
                damage,
                progress_callback=lambda value: self.events.put(("progress", value)),
                cancel_event=self.cancel_event,
                green=green,
                eq_gains=eq_gains,
            )
        except ProcessingCancelled:
            self.events.put(("cancelled", None))
        except Exception as exc:
            self.events.put(("error", str(exc)))
        else:
            self.events.put(("success", str(result)))

    def _set_controls_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        controls = [
            self.input_entry,
            self.output_entry,
            self.input_button,
            self.output_button,
            self.damage_scale,
            self.green_scale,
            self.reset_eq_button,
            self.start_button,
            self.preview_button,
        ]
        controls.extend(self.eq_scales)
        for widget in controls:
            widget.configure(state=state)
        self.language_combobox.configure(
            state="readonly" if enabled else tk.DISABLED
        )
        self.cancel_button.configure(state=tk.DISABLED if enabled else tk.NORMAL)

    def cancel_processing(self):
        if self.processing:
            self.cancel_event.set()
            self.cancel_button.configure(state=tk.DISABLED)
            self._set_status("status_cancelling")

    def _poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "preview_ready":
                    self._preview_ready(*payload)
                    continue
                if kind == "preview_error":
                    self._preview_failed(*payload)
                    continue
                if kind == "progress":
                    self.progress_var.set(payload)
                    self._set_status("status_processing", value=payload)
                    continue

                self.processing = False
                self._set_controls_enabled(True)
                if kind == "success":
                    self.progress_var.set(100.0)
                    self._set_status("status_success", path=payload)
                    messagebox.showinfo(
                        tr("export_complete_title"),
                        tr("export_complete_message", path=payload),
                        parent=self,
                    )
                elif kind == "cancelled":
                    self.progress_var.set(0.0)
                    self._set_status("status_cancelled")
                else:
                    self.progress_var.set(0.0)
                    self._set_status("status_failed")
                    messagebox.showerror(tr("status_failed"), payload, parent=self)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_events)

    def on_close(self):
        if self.processing:
            if not messagebox.askyesno(
                tr("confirm_exit_title"), tr("confirm_exit"), parent=self
            ):
                return
            self.cancel_event.set()
        self.close_preview()
        self.destroy()


def parse_eq_argument(value):
    try:
        return normalize_eq_gains(value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    language_parser = argparse.ArgumentParser(add_help=False)
    language_parser.add_argument(
        "--language", choices=tuple(LANGUAGE_NAMES), default=DEFAULT_LANGUAGE
    )
    language_args, _ = language_parser.parse_known_args(argv)
    set_language(language_args.language)

    parser = argparse.ArgumentParser(description=tr("cli_description"))
    parser.add_argument("input", nargs="?", help=tr("input_help"))
    parser.add_argument("-o", "--output", help=tr("output_help"))
    parser.add_argument(
        "-d", "--damage", type=float, default=60, help=tr("damage_help")
    )
    parser.add_argument(
        "--green", type=float, default=0, help=tr("green_help")
    )
    parser.add_argument(
        "--eq",
        type=parse_eq_argument,
        default=None,
        metavar="G1,...,G10",
        help=tr("eq_help"),
    )
    parser.add_argument(
        "--language",
        choices=tuple(LANGUAGE_NAMES),
        default=DEFAULT_LANGUAGE,
        help=tr("language_help"),
    )
    args = parser.parse_args(argv)
    set_language(args.language)
    if not 0 <= args.damage <= 200:
        parser.error(tr("damage_range"))
    if not 0 <= args.green <= 100:
        parser.error(tr("green_range"))

    if not args.input:
        app = VideoCorruptorApp(
            initial_damage=args.damage,
            initial_green=args.green,
            initial_eq_gains=args.eq,
            initial_language=args.language,
        )
        app.mainloop()
        return 0

    output = args.output or str(default_output_path(args.input))
    cancel_event = threading.Event()

    def show_progress(value):
        sys.stdout.write("\r" + tr("cli_progress", value=value))
        sys.stdout.flush()

    try:
        result = corrupt_video(
            args.input,
            output,
            args.damage,
            progress_callback=show_progress,
            cancel_event=cancel_event,
            green=args.green,
            eq_gains=args.eq,
        )
    except KeyboardInterrupt:
        cancel_event.set()
        sys.stdout.write(f"\n{tr('cli_cancelled')}\n")
        return 130
    except ProcessingCancelled:
        sys.stdout.write(f"\n{tr('cli_cancelled')}\n")
        return 130
    except Exception as exc:
        sys.stdout.write("\n")
        print(tr("cli_error", error=exc), file=sys.stderr)
        return 1
    print("\n" + tr("cli_complete", result=result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
