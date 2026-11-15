# Video Corruptor

[中文](#中文) | [English](#english) | [Español](#español)

---

## 中文

一个使用 Python、Tkinter 和 FFmpeg 制作的视频损坏效果工具。可以降低视频清晰度、增加压缩失真、对音频进行硬削波，并将处理后的音视频合并导出为 MP4。

### 功能

- 0–100% 可调损坏程度
- 视频降采样、盒式模糊和高压缩失真
- 音频增益与 PCM 硬削波
- 自动合并为 H.264 + AAC MP4
- 图形界面和命令行两种使用方式
- 显示处理进度，支持取消
- 保持原视频分辨率，不修改原文件
- 无音轨的视频仅处理画面

### 环境要求

- Python 3.10 或更高版本
- 新版 FFmpeg（推荐使用项目依赖附带的版本）

### 安装

在项目目录运行：

```bash
python -m pip install -r requirements.txt
```

程序会优先使用 `imageio-ffmpeg` 附带的新版 FFmpeg。如果没有安装该依赖，也可以自行安装较新版本的 FFmpeg 并加入系统 `PATH`。

### 图形界面

```bash
python video_corruptor.py
```

选择输入视频和输出位置，调整损坏程度，然后点击“开始损坏并导出”。

### 命令行

```bash
python video_corruptor.py input.mp4 -o output.mp4 --damage 60
```

`--damage` 的范围为 0–100：

- `0`：不添加额外损坏效果
- `60`：明显损坏
- `100`：极严重损坏

不指定 `-o` 时，默认生成 `input_损坏.mp4`。

### 注意

输出的是正常可播放的 MP4 文件，不会真正破坏视频封装，也不会修改原视频。处理所需时间取决于视频时长、分辨率和电脑性能。

### 许可证

本项目采用 [MIT License](LICENSE)。

---

## English

A video degradation tool built with Python, Tkinter, and FFmpeg. It reduces visual clarity, adds compression artifacts, applies hard clipping to audio, and merges the processed audio and video into an MP4 file.

### Features

- Adjustable damage level from 0 to 100
- Video downsampling, box blur, and heavy compression artifacts
- Audio gain and PCM hard clipping
- Automatic muxing into an H.264 + AAC MP4
- Both graphical and command-line interfaces
- Real-time progress and cancellation support
- Preserves the source resolution and leaves the original file unchanged
- Processes video only when the source has no audio track

### Requirements

- Python 3.10 or newer
- A recent version of FFmpeg (the bundled version installed with the project dependency is recommended)

### Installation

Run the following command in the project directory:

```bash
python -m pip install -r requirements.txt
```

The application prefers the recent FFmpeg binary bundled with `imageio-ffmpeg`. If that dependency is unavailable, you can install a recent standalone version of FFmpeg and add it to your system `PATH`.

### Graphical interface

```bash
python video_corruptor.py
```

Select an input video and an output location, adjust the damage level, and click the export button.

### Command line

```bash
python video_corruptor.py input.mp4 -o output.mp4 --damage 60
```

The `--damage` value ranges from 0 to 100:

- `0`: No additional damage effects
- `60`: Noticeable damage
- `100`: Extreme damage

If `-o` is omitted, the output defaults to `input_损坏.mp4`.

### Notes

The output is a valid, playable MP4 file. The process does not damage the container or modify the source video. Processing time depends on the video duration, resolution, and computer performance.

### License

This project is licensed under the [MIT License](LICENSE).

---

## Español

Una herramienta de degradación de vídeo creada con Python, Tkinter y FFmpeg. Reduce la nitidez, añade artefactos de compresión, aplica recorte duro al audio y combina el audio y el vídeo procesados en un archivo MP4.

### Características

- Nivel de deterioro ajustable de 0 a 100
- Remuestreo descendente, desenfoque de caja y compresión intensa del vídeo
- Ganancia de audio y recorte duro mediante PCM
- Exportación automática como MP4 con H.264 + AAC
- Interfaz gráfica e interfaz de línea de comandos
- Progreso en tiempo real y opción de cancelación
- Conserva la resolución original y no modifica el archivo de origen
- Si el vídeo no tiene pista de audio, solo procesa la imagen

### Requisitos

- Python 3.10 o una versión posterior
- Una versión reciente de FFmpeg (se recomienda la incluida con la dependencia del proyecto)

### Instalación

Ejecuta este comando en el directorio del proyecto:

```bash
python -m pip install -r requirements.txt
```

La aplicación utiliza preferentemente la versión reciente de FFmpeg incluida con `imageio-ffmpeg`. Si esta dependencia no está disponible, puedes instalar una versión reciente de FFmpeg y añadirla a la variable `PATH` del sistema.

### Interfaz gráfica

```bash
python video_corruptor.py
```

Selecciona un vídeo de entrada y una ubicación de salida, ajusta el nivel de deterioro y pulsa el botón de exportación.

### Línea de comandos

```bash
python video_corruptor.py input.mp4 -o output.mp4 --damage 60
```

El valor de `--damage` puede estar entre 0 y 100:

- `0`: No añade efectos de deterioro
- `60`: Deterioro notable
- `100`: Deterioro extremo

Si no se especifica `-o`, el archivo de salida será `input_损坏.mp4` de forma predeterminada.

### Notas

El resultado es un archivo MP4 válido y reproducible. El proceso no daña el contenedor ni modifica el vídeo original. El tiempo de procesamiento depende de la duración, la resolución y el rendimiento del equipo.

### Licencia

Este proyecto se distribuye bajo la [licencia MIT](LICENSE).
