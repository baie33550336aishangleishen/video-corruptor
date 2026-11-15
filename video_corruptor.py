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

VIDEO_FILETYPES = [
    ("视频文件", "*.mp4 *.mov *.mkv *.avi *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.ts"),
    ("所有文件", "*.*"),
]


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
    raise RuntimeError(
        "未找到 FFmpeg。请安装 FFmpeg 并加入 PATH，"
        "或执行：python -m pip install imageio-ffmpeg"
    )


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
        raise ValueError("未检测到可处理的视频流，请确认文件未损坏且格式受支持")

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
    damage = max(0, min(100, int(round(float(damage)))))
    amount = damage / 100.0
    return DamageSettings(
        downscale_factor=1.0 + 19.0 * amount ** 1.5,
        blur_radius=int(round(6 * amount)),
        crf=int(round(18 + 28 * amount)),
        audio_gain_db=30.0 * amount,
        audio_bitrate_kbps=int(round(160 - 96 * amount)),
    )


def _even_dimension(value):
    return max(2, int(round(value)) // 2 * 2)


def build_video_filter(info, settings):
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
    filters.append("format=yuv420p")
    return ",".join(filters)


def build_audio_filter(settings):
    # 转为有符号 16 位 PCM 时，超出 ±1 的采样会被硬性截断。
    gain_linear = 10.0 ** (settings.audio_gain_db / 20.0)
    return f"volume={gain_linear:.8f},aformat=sample_fmts=s16"


def default_output_path(input_path):
    input_path = Path(input_path)
    return input_path.with_name(f"{input_path.stem}_损坏.mp4")


def corrupt_video(
    input_path,
    output_path,
    damage=60,
    progress_callback=None,
    cancel_event=None,
):
    input_path = Path(input_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()
    if not input_path.is_file():
        raise ValueError(f"输入视频不存在：{input_path}")
    if input_path == output_path:
        raise ValueError("输出文件不能覆盖原视频，请选择另一个文件名")
    if output_path.suffix.lower() != ".mp4":
        raise ValueError("输出文件必须使用 .mp4 扩展名")
    if not 0 <= float(damage) <= 100:
        raise ValueError("损坏程度必须在 0 到 100 之间")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = find_ffmpeg()
    info = probe_media(input_path, ffmpeg_path)
    settings = calculate_damage(damage)
    video_filter = build_video_filter(info, settings)

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
                build_audio_filter(settings),
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
            details = "\n".join(list(logs)[-12:]) or "未返回详细错误信息"
            raise RuntimeError(f"FFmpeg 处理失败（退出代码 {return_code}）：\n{details}")
        if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
            raise RuntimeError("处理结束，但 FFmpeg 没有生成有效输出文件")
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
    def __init__(self, initial_damage=60):
        super().__init__()
        self.title("视频损坏器")
        self.geometry("760x570")
        self.minsize(680, 540)
        self.configure(background=BG)

        self.media_info = None
        self.processing = False
        self.cancel_event = threading.Event()
        self.events = queue.Queue()
        self.output_is_automatic = True

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.damage_var = tk.DoubleVar(value=initial_damage)
        self.damage_text = tk.StringVar()
        self.detail_text = tk.StringVar()
        self.media_text = tk.StringVar(value="尚未选择视频")
        self.status_text = tk.StringVar(value="请选择输入视频，调整损坏程度后开始处理")
        self.progress_var = tk.DoubleVar(value=0.0)

        self._configure_styles()
        self._build_ui()
        self._update_damage()
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
        main = ttk.Frame(self, style="App.TFrame", padding=22)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="视频损坏器", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            main,
            text="降采样模糊 · 高压缩失真 · 音频硬削波 · 自动合并 MP4",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 18))

        files = ttk.LabelFrame(main, text="输入与输出", padding=14)
        files.pack(fill=tk.X)
        files.columnconfigure(0, weight=1)
        self.input_entry = ttk.Entry(files, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.input_button = ttk.Button(
            files, text="选择视频", command=self.choose_input
        )
        self.input_button.grid(row=0, column=1)
        self.output_entry = ttk.Entry(files, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(10, 0))
        self.output_button = ttk.Button(
            files, text="输出位置", command=self.choose_output
        )
        self.output_button.grid(row=1, column=1, pady=(10, 0))
        ttk.Label(
            files,
            textvariable=self.media_text,
            style="Subtitle.TLabel",
            wraplength=650,
            justify=tk.LEFT,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

        damage_panel = ttk.Frame(main, style="Card.TFrame", padding=18)
        damage_panel.pack(fill=tk.X, pady=(16, 0))
        damage_header = ttk.Frame(damage_panel, style="Card.TFrame")
        damage_header.pack(fill=tk.X)
        ttk.Label(damage_header, text="损坏程度", style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            damage_header, textvariable=self.damage_text, style="Damage.TLabel"
        ).pack(side=tk.RIGHT)
        self.damage_scale = ttk.Scale(
            damage_panel,
            from_=0,
            to=100,
            variable=self.damage_var,
            command=self._update_damage,
        )
        self.damage_scale.pack(fill=tk.X, pady=(14, 6))
        scale_labels = ttk.Frame(damage_panel, style="Card.TFrame")
        scale_labels.pack(fill=tk.X)
        ttk.Label(scale_labels, text="0  不损坏", style="CardMuted.TLabel").pack(side=tk.LEFT)
        ttk.Label(scale_labels, text="50  明显", style="CardMuted.TLabel").pack(side=tk.LEFT, expand=True)
        ttk.Label(scale_labels, text="100  极严重", style="CardMuted.TLabel").pack(side=tk.RIGHT)
        ttk.Label(
            damage_panel,
            textvariable=self.detail_text,
            style="CardMuted.TLabel",
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(14, 0))

        ttk.Label(
            main,
            text="输出仍为正常可播放的 MP4；原视频不会被修改。无音轨的视频仅处理画面。",
            style="Subtitle.TLabel",
            wraplength=690,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(14, 18))

        actions = ttk.Frame(main, style="App.TFrame")
        actions.pack(fill=tk.X)
        self.start_button = ttk.Button(
            actions,
            text="开始损坏并导出",
            style="Accent.TButton",
            command=self.start_processing,
        )
        self.start_button.pack(side=tk.LEFT)
        self.cancel_button = ttk.Button(
            actions,
            text="取消",
            command=self.cancel_processing,
            state=tk.DISABLED,
        )
        self.cancel_button.pack(side=tk.LEFT, padx=(8, 0))

        self.progress_bar = ttk.Progressbar(
            main,
            style="Accent.Horizontal.TProgressbar",
            maximum=100,
            variable=self.progress_var,
        )
        self.progress_bar.pack(fill=tk.X, pady=(18, 8))
        ttk.Label(main, textvariable=self.status_text, style="Subtitle.TLabel").pack(anchor="w")

    def choose_input(self):
        path = filedialog.askopenfilename(
            parent=self, title="选择输入视频", filetypes=VIDEO_FILETYPES
        )
        if path:
            self.load_input(path)

    def load_input(self, path):
        self.input_var.set(path)
        if self.output_is_automatic or not self.output_var.get().strip():
            self.output_var.set(str(default_output_path(path)))
            self.output_is_automatic = True
        self.media_info = None
        self.media_text.set("正在读取视频信息……")
        self.update_idletasks()
        try:
            self.media_info = probe_media(path)
        except Exception as exc:
            self.media_text.set("无法读取视频信息")
            messagebox.showerror("读取失败", str(exc), parent=self)
            return
        info = self.media_info
        audio_text = "有音轨" if info.has_audio else "无音轨"
        duration_text = format_duration(info.duration) if info.duration else "时长未知"
        self.media_text.set(
            f"{info.width} × {info.height}    {duration_text}    {audio_text}"
        )
        self.status_text.set("视频已就绪")

    def choose_output(self):
        current = self.output_var.get().strip()
        initial_file = Path(current).name if current else "损坏视频.mp4"
        path = filedialog.asksaveasfilename(
            parent=self,
            title="选择输出位置",
            defaultextension=".mp4",
            initialfile=initial_file,
            filetypes=[("MP4 视频", "*.mp4")],
        )
        if path:
            self.output_var.set(path)
            self.output_is_automatic = False

    def _update_damage(self, _value=None):
        damage = int(round(float(self.damage_var.get())))
        settings = calculate_damage(damage)
        if damage == 0:
            level = "不损坏"
        elif damage <= 20:
            level = "轻微"
        elif damage <= 40:
            level = "较轻"
        elif damage <= 60:
            level = "明显"
        elif damage <= 80:
            level = "严重"
        else:
            level = "极严重"
        self.damage_text.set(f"{damage}% · {level}")
        blur_text = (
            f"{settings.blur_radius} 像素盒式模糊"
            if settings.blur_radius
            else "不额外模糊"
        )
        self.detail_text.set(
            f"画面：{settings.downscale_factor:.1f} 倍降采样 + {blur_text}，"
            f"压缩 CRF {settings.crf}\n"
            f"音频：增益 +{settings.audio_gain_db:.1f} dB 后硬削波，"
            f"AAC {settings.audio_bitrate_kbps} kbps"
        )

    def start_processing(self):
        if self.processing:
            return
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()
        if not input_path:
            messagebox.showwarning("缺少输入", "请先选择输入视频", parent=self)
            return
        if not output_path:
            output_path = str(default_output_path(input_path))
            self.output_var.set(output_path)
        if Path(output_path).suffix.lower() != ".mp4":
            messagebox.showwarning("输出格式", "输出文件必须使用 .mp4 扩展名", parent=self)
            return
        if Path(input_path).resolve() == Path(output_path).resolve():
            messagebox.showwarning("输出位置", "输出文件不能覆盖原视频", parent=self)
            return
        if not Path(input_path).is_file():
            messagebox.showerror("输入错误", "输入视频不存在", parent=self)
            return
        if Path(output_path).exists() and not messagebox.askyesno(
            "确认覆盖", "输出文件已存在，是否覆盖？", parent=self
        ):
            return

        self.processing = True
        self.cancel_event.clear()
        self.progress_var.set(0.0)
        self.status_text.set("正在初始化 FFmpeg……")
        self._set_controls_enabled(False)
        damage = int(round(float(self.damage_var.get())))
        threading.Thread(
            target=self._processing_worker,
            args=(input_path, output_path, damage),
            daemon=True,
        ).start()

    def _processing_worker(self, input_path, output_path, damage):
        try:
            result = corrupt_video(
                input_path,
                output_path,
                damage,
                progress_callback=lambda value: self.events.put(("progress", value)),
                cancel_event=self.cancel_event,
            )
        except ProcessingCancelled:
            self.events.put(("cancelled", None))
        except Exception as exc:
            self.events.put(("error", str(exc)))
        else:
            self.events.put(("success", str(result)))

    def _set_controls_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        for widget in (
            self.input_entry,
            self.output_entry,
            self.input_button,
            self.output_button,
            self.damage_scale,
            self.start_button,
        ):
            widget.configure(state=state)
        self.cancel_button.configure(state=tk.DISABLED if enabled else tk.NORMAL)

    def cancel_processing(self):
        if self.processing:
            self.cancel_event.set()
            self.cancel_button.configure(state=tk.DISABLED)
            self.status_text.set("正在取消处理……")

    def _poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "progress":
                    self.progress_var.set(payload)
                    self.status_text.set(f"正在处理并合并音视频…… {payload:.1f}%")
                    continue

                self.processing = False
                self._set_controls_enabled(True)
                if kind == "success":
                    self.progress_var.set(100.0)
                    self.status_text.set(f"处理完成：{payload}")
                    messagebox.showinfo(
                        "导出完成", f"损坏视频已保存到：\n{payload}", parent=self
                    )
                elif kind == "cancelled":
                    self.progress_var.set(0.0)
                    self.status_text.set("处理已取消，未保留未完成文件")
                else:
                    self.progress_var.set(0.0)
                    self.status_text.set("处理失败")
                    messagebox.showerror("处理失败", payload, parent=self)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_events)

    def on_close(self):
        if self.processing:
            if not messagebox.askyesno(
                "确认退出", "正在处理视频，确定取消并退出吗？", parent=self
            ):
                return
            self.cancel_event.set()
        self.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(description="将视频变糊、音频硬削波并合并为 MP4")
    parser.add_argument("input", nargs="?", help="输入视频路径；不提供时打开图形界面")
    parser.add_argument("-o", "--output", help="输出 MP4 路径")
    parser.add_argument(
        "-d", "--damage", type=float, default=60, help="损坏程度 0-100，默认 60"
    )
    args = parser.parse_args(argv)
    if not 0 <= args.damage <= 100:
        parser.error("损坏程度必须在 0 到 100 之间")

    if not args.input:
        app = VideoCorruptorApp(initial_damage=args.damage)
        app.mainloop()
        return 0

    output = args.output or str(default_output_path(args.input))
    cancel_event = threading.Event()

    def show_progress(value):
        sys.stdout.write(f"\r处理进度：{value:5.1f}%")
        sys.stdout.flush()

    try:
        result = corrupt_video(
            args.input,
            output,
            args.damage,
            progress_callback=show_progress,
            cancel_event=cancel_event,
        )
    except KeyboardInterrupt:
        cancel_event.set()
        sys.stdout.write("\n已取消\n")
        return 130
    except ProcessingCancelled:
        sys.stdout.write("\n已取消\n")
        return 130
    except Exception as exc:
        sys.stdout.write("\n")
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    print(f"\n处理完成：{result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
