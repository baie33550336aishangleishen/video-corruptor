# Video Corruptor 音频损坏效果器

[简体中文](#简体中文) | [繁體中文](#繁體中文) | [English](#english) | [Español](#español)

---

## 简体中文

一个使用 Python、Tkinter 和 FFmpeg 制作的视频损坏效果工具。可以降低视频清晰度、增加压缩失真、模拟安卓绿色偏色、调整十段音频均衡器并进行硬削波，最后导出可播放的 MP4。

### 功能

- 0–200% 可调整体损坏程度，100% 以上为极限档
- 视频降采样、盒式模糊和高压缩失真
- 0–100% 独立绿色故障强度
- 原视频与损坏效果左右对比，支持 3 秒无声循环预览
- 20 Hz–20 kHz 十段音频均衡器，垂直滑块范围为 -10 至 +10 dB
- 音频增益、PCM 硬削波和可调 AAC 码率
- 自动合并为 H.264 + AAC MP4
- 简体中文、繁体中文、英语和西班牙语界面
- 图形界面和命令行两种使用方式
- 显示处理进度，支持取消
- 保持原视频分辨率，不修改原文件；无音轨时仅处理画面

### 环境要求

- Python 3.10 或更高版本
- 新版 FFmpeg（推荐使用项目依赖附带的版本）

### 安装

在项目目录运行：

```bash
python -m pip install -r requirements.txt
```

程序会优先使用 `imageio-ffmpeg` 附带的新版 FFmpeg。如果没有安装该依赖，也可以自行安装较新版本的 FFmpeg 并加入系统 `PATH`。

### 图形界面与语言设置

```bash
python video_corruptor.py
```

选择输入视频和输出位置，调整整体损坏、绿色故障及各频段增益。点击“视频预览”可左右对比原视频与损坏效果，并播放或暂停 3 秒无声循环预览；点击“开始损坏并导出”生成完整视频。右上角的“语言”下拉菜单可即时切换简体中文、繁体中文、English 或 Español，并保留当前路径和滑块设置。

也可以指定启动语言：

```bash
python video_corruptor.py --language zh-TW
```

可选值为 `zh-CN`（简体中文）、`zh-TW`（繁体中文）、`en`（英语）和 `es`（西班牙语），默认为 `zh-CN`。

### 命令行

```bash
python video_corruptor.py input.mp4 -o output.mp4 --damage 60 --green 35
python video_corruptor.py input.mp4 -o output.mp4 --eq "6,3,0,-2,-4,0,2,4,-3,5" --language zh-CN
```

- `--damage`：整体损坏程度，范围 0–200，默认 60；100 以上为极限档
- `--green`：绿色故障强度，范围 0–100，默认 0
- `--eq`：依次为 20、50、100、200、500、1000、2000、5000、10000、20000 Hz 设置增益；必须提供十个逗号分隔的数值，每项范围为 -10 至 +10 dB
- `--language`：界面、处理消息和默认输出文件名使用的语言

不指定 `-o` 时，默认生成 `input_损坏.mp4`。语言切换后，自动输出文件名也会使用对应语言。

### 注意

输出的是正常可播放的 MP4 文件，不会真正破坏视频封装，也不会修改原视频。处理所需时间取决于视频时长、分辨率和电脑性能。

### 许可证

本项目采用 [MIT License](LICENSE)。

---

## 繁體中文

一個使用 Python、Tkinter 和 FFmpeg 製作的影片損壞效果工具。可以降低影片清晰度、增加壓縮失真、模擬 Android 綠色偏色、調整十段音訊等化器並進行硬削波，最後匯出可播放的 MP4。

### 功能

- 0–200% 可調整體損壞程度，100% 以上為極限檔
- 影片降採樣、盒式模糊和高壓縮失真
- 0–100% 獨立綠色故障強度
- 原影片與損壞效果左右對比，支援 3 秒無聲循環預覽
- 20 Hz–20 kHz 十段音訊等化器，垂直滑桿範圍為 -10 至 +10 dB
- 音訊增益、PCM 硬削波和可調 AAC 位元率
- 自動合併為 H.264 + AAC MP4
- 簡體中文、繁體中文、英語和西班牙語介面
- 圖形介面和命令列兩種使用方式
- 顯示處理進度，支援取消
- 保持原影片解析度，不修改原檔案；無音軌時僅處理畫面

### 環境需求

- Python 3.10 或更高版本
- 新版 FFmpeg（建議使用專案相依套件附帶的版本）

### 安裝

在專案目錄執行：

```bash
python -m pip install -r requirements.txt
```

程式會優先使用 `imageio-ffmpeg` 附帶的新版 FFmpeg。如果沒有安裝該相依套件，也可以自行安裝較新版本的 FFmpeg 並加入系統 `PATH`。

### 圖形介面與語言設定

```bash
python video_corruptor.py
```

選擇輸入影片和輸出位置，調整整體損壞、綠色故障及各頻段增益。點擊「影片預覽」可左右對比原影片與損壞效果，並播放或暫停 3 秒無聲循環預覽；點擊「開始損壞並匯出」產生完整影片。右上角的「語言」下拉選單可即時切換简体中文、繁體中文、English 或 Español，並保留目前路徑和滑桿設定。

也可以指定啟動語言：

```bash
python video_corruptor.py --language zh-TW
```

可選值為 `zh-CN`（簡體中文）、`zh-TW`（繁體中文）、`en`（英語）和 `es`（西班牙語），預設為 `zh-CN`。

### 命令列

```bash
python video_corruptor.py input.mp4 -o output.mp4 --damage 60 --green 35
python video_corruptor.py input.mp4 -o output.mp4 --eq "6,3,0,-2,-4,0,2,4,-3,5" --language zh-TW
```

- `--damage`：整體損壞程度，範圍 0–200，預設 60；100 以上為極限檔
- `--green`：綠色故障強度，範圍 0–100，預設 0
- `--eq`：依序為 20、50、100、200、500、1000、2000、5000、10000、20000 Hz 設定增益；必須提供十個以逗號分隔的數值，每項範圍為 -10 至 +10 dB
- `--language`：介面、處理訊息和預設輸出檔名使用的語言

未指定 `-o` 時，預設產生 `input_損壞.mp4`。語言切換後，自動輸出檔名也會使用對應語言。

### 注意

輸出的是正常可播放的 MP4 檔案，不會真正破壞影片封裝，也不會修改原影片。處理所需時間取決於影片長度、解析度和電腦效能。

### 授權

本專案採用 [MIT License](LICENSE)。

---

## English

A video degradation tool built with Python, Tkinter, and FFmpeg. It reduces visual clarity, adds compression artifacts, simulates the Android green tint, provides ten-band audio equalization and hard clipping, and exports a playable MP4.

### Features

- Adjustable overall damage from 0 to 200, with a maximum-intensity range above 100
- Video downsampling, box blur, and heavy compression artifacts
- Independent green glitch intensity from 0 to 100
- Side-by-side original and damaged video comparison with a three-second silent looping preview
- Ten-band audio EQ from 20 Hz to 20 kHz, with vertical sliders from -10 to +10 dB
- Audio gain, PCM hard clipping, and adjustable AAC bitrate
- Automatic muxing into an H.264 + AAC MP4
- Simplified Chinese, Traditional Chinese, English, and Spanish interfaces
- Both graphical and command-line interfaces
- Real-time progress and cancellation support
- Preserves the source resolution and leaves the original file unchanged; processes video only when no audio track is present

### Requirements

- Python 3.10 or newer
- A recent version of FFmpeg (the bundled version installed with the project dependency is recommended)

### Installation

Run the following command in the project directory:

```bash
python -m pip install -r requirements.txt
```

The application prefers the recent FFmpeg binary bundled with `imageio-ffmpeg`. If that dependency is unavailable, you can install a recent standalone version of FFmpeg and add it to your system `PATH`.

### Graphical interface and language settings

```bash
python video_corruptor.py
```

Select an input video and an output location, adjust the overall damage, green glitch, and frequency gains. Click Video preview to compare the original and damaged video side by side and play or pause the three-second silent loop; use the export button to create the full video. The Language drop-down in the upper-right corner instantly switches between 简体中文, 繁體中文, English, and Español while preserving the current paths and slider settings.

You can also select the startup language:

```bash
python video_corruptor.py --language en
```

Available values are `zh-CN` (Simplified Chinese), `zh-TW` (Traditional Chinese), `en` (English), and `es` (Spanish). The default is `zh-CN`.

### Command line

```bash
python video_corruptor.py input.mp4 -o output.mp4 --damage 60 --green 35
python video_corruptor.py input.mp4 -o output.mp4 --eq "6,3,0,-2,-4,0,2,4,-3,5" --language en
```

- `--damage`: Overall damage from 0 to 200; default is 60, with maximum intensity above 100
- `--green`: Green glitch intensity from 0 to 100; default is 0
- `--eq`: Gains for 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, and 20000 Hz respectively; provide exactly ten comma-separated values, each from -10 to +10 dB
- `--language`: Language used for the interface, processing messages, and automatic output filename

If `-o` is omitted with the English language selected, the output defaults to `input_damaged.mp4`. The automatic filename suffix follows the selected language.

### Notes

The output is a valid, playable MP4 file. The process does not damage the container or modify the source video. Processing time depends on the video duration, resolution, and computer performance.

### License

This project is licensed under the [MIT License](LICENSE).

---

## Español

Una herramienta de degradación de vídeo creada con Python, Tkinter y FFmpeg. Reduce la nitidez, añade artefactos de compresión, simula el tinte verde de Android, ofrece ecualización de audio de diez bandas y recorte duro, y exporta un MP4 reproducible.

### Características

- Deterioro general ajustable de 0 a 200, con intensidad máxima por encima de 100
- Remuestreo descendente, desenfoque de caja y compresión intensa del vídeo
- Intensidad independiente del fallo verde de 0 a 100
- Comparación del vídeo original y el efecto con una vista previa silenciosa en bucle de tres segundos
- Ecualizador de audio de diez bandas de 20 Hz a 20 kHz, con controles verticales de -10 a +10 dB
- Ganancia de audio, recorte duro mediante PCM y tasa de bits AAC ajustable
- Exportación automática como MP4 con H.264 + AAC
- Interfaces en chino simplificado, chino tradicional, inglés y español
- Interfaz gráfica e interfaz de línea de comandos
- Progreso en tiempo real y opción de cancelación
- Conserva la resolución original y no modifica el archivo de origen; si no hay audio, solo procesa la imagen

### Requisitos

- Python 3.10 o una versión posterior
- Una versión reciente de FFmpeg (se recomienda la incluida con la dependencia del proyecto)

### Instalación

Ejecuta este comando en el directorio del proyecto:

```bash
python -m pip install -r requirements.txt
```

La aplicación utiliza preferentemente la versión reciente de FFmpeg incluida con `imageio-ffmpeg`. Si esta dependencia no está disponible, puedes instalar una versión reciente de FFmpeg y añadirla a la variable `PATH` del sistema.

### Interfaz gráfica e idioma

```bash
python video_corruptor.py
```

Selecciona un vídeo de entrada y una ubicación de salida, ajusta el deterioro general, el fallo verde y las ganancias de frecuencia. Pulsa Vista previa para comparar el original y el efecto, y reproducir o pausar el bucle silencioso de tres segundos; usa el botón de exportación para crear el vídeo completo. El menú desplegable Idioma de la esquina superior derecha cambia al instante entre 简体中文, 繁體中文, English y Español, conservando las rutas y los controles actuales.

También puedes elegir el idioma de inicio:

```bash
python video_corruptor.py --language es
```

Los valores disponibles son `zh-CN` (chino simplificado), `zh-TW` (chino tradicional), `en` (inglés) y `es` (español). El valor predeterminado es `zh-CN`.

### Línea de comandos

```bash
python video_corruptor.py input.mp4 -o output.mp4 --damage 60 --green 35
python video_corruptor.py input.mp4 -o output.mp4 --eq "6,3,0,-2,-4,0,2,4,-3,5" --language es
```

- `--damage`: Deterioro general de 0 a 200; el valor predeterminado es 60 y la intensidad máxima supera 100
- `--green`: Intensidad del fallo verde de 0 a 100; el valor predeterminado es 0
- `--eq`: Ganancias para 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000 y 20000 Hz respectivamente; debes indicar exactamente diez valores separados por comas, cada uno de -10 a +10 dB
- `--language`: Idioma de la interfaz, los mensajes de procesamiento y el nombre automático del archivo de salida

Si se omite `-o` con el idioma español, la salida predeterminada será `input_dañado.mp4`. El sufijo automático del nombre sigue el idioma seleccionado.

### Notas

El resultado es un archivo MP4 válido y reproducible. El proceso no daña el contenedor ni modifica el vídeo original. El tiempo de procesamiento depende de la duración, la resolución y el rendimiento del equipo.

### Licencia

Este proyecto se distribuye bajo la [licencia MIT](LICENSE).
