import math
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw
from moviepy import VideoClip, AudioFileClip


@dataclass(frozen=True)
class RenderConfig:
    # Output
    size: int = 1080
    low: int = 240
    fps: int = 30
    audio_sr: int = 22050
    bg_rgb: Tuple[int, int, int] = (0, 0, 0)

    # Sensitivity
    gain: float = 3.2
    gamma: float = 0.45
    smooth_alpha: float = 0.35

    # Ring
    ring_base_ratio: float = 0.26
    ring_amp_ratio: float = 0.14
    ring_w_min: int = 5
    ring_w_amp: int = 6
    inner_accent: bool = True

    # Avatar
    avatar_ratio: float = 0.44
    breath: bool = True
    breath_scales: Tuple[float, float, float] = (0.98, 1.00, 1.02)


def _circle_mask(size: int) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((0, 0, size - 1, size - 1), fill=255)
    return m


def _ema_smooth(x: np.ndarray, alpha: float) -> np.ndarray:
    y = np.empty_like(x, dtype=np.float32)
    y[0] = x[0]
    for i in range(1, len(x)):
        y[i] = alpha * x[i] + (1 - alpha) * y[i - 1]
    return y


def _resize_cover_square(img: Image.Image, size: int) -> Image.Image:
    """Scale keeping aspect ratio and center-crop to size×size (no deformation)."""
    w, h = img.size
    scale = max(size / w, size / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    im = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - size) // 2
    top = (nh - size) // 2
    return im.crop((left, top, left + size, top + size))


def _audio_to_rms_frames(audio_path: str | Path, fps: int, cfg: RenderConfig) -> tuple[np.ndarray, float]:
    sr = getattr(cfg, "audio_sr", 22050)

    aclip = AudioFileClip(str(audio_path))
    duration = float(aclip.duration)

    snd = aclip.to_soundarray(fps=sr)
    aclip.close()

    if snd.ndim == 2:
        snd = snd.mean(axis=1)

    hop = max(1, int(sr / fps))
    frame_count = int(math.ceil(len(snd) / hop))

    rms = np.empty(frame_count, dtype=np.float32)
    for i in range(frame_count):
        chunk = snd[i * hop : (i + 1) * hop]
        rms[i] = float(np.sqrt(np.mean(chunk * chunk) + 1e-12)) if len(chunk) else 0.0

    den = np.percentile(rms, 95)
    if den > 0:
        rms = rms / den
    rms = np.clip(rms, 0, 1)

    rms = _ema_smooth(rms, alpha=cfg.smooth_alpha)
    rms = np.clip((rms * cfg.gain) ** cfg.gamma, 0, 1)

    return rms, duration


def render_call_video(
    avatar_path: str | Path,
    audio_path: str | Path,
    out_path: str | Path = "sosi_call.mp4",
    cfg: Optional[RenderConfig] = None,
) -> Path:
    """
    Create a pixel-art 'call style' video (avatar + reactive ring) in 1080p by default.
    Audio can be .wav/.mp3/.ogg/etc (whatever librosa/ffmpeg can decode).
    """
    cfg = cfg or RenderConfig()

    avatar_src = Image.open(str(avatar_path)).convert("RGBA")
    rms, duration = _audio_to_rms_frames(audio_path, fps=cfg.fps, cfg=cfg)

    LOW = cfg.low
    SIZE = cfg.size

    avatar_px = int(LOW * cfg.avatar_ratio)

    # Precompute avatar (LOW) cache
    avatar_cache: list[Image.Image] = []
    if cfg.breath:
        for s in cfg.breath_scales:
            px = max(2, int(avatar_px * s))
            square = _resize_cover_square(avatar_src, px)
            av = square.resize((px, px), Image.NEAREST)
            av.putalpha(_circle_mask(px))
            avatar_cache.append(av)
    else:
        square = _resize_cover_square(avatar_src, avatar_px)
        av = square.resize((avatar_px, avatar_px), Image.NEAREST)
        av.putalpha(_circle_mask(avatar_px))
        avatar_cache = [av]

    cx, cy = LOW // 2, LOW // 2
    ring_base = int(LOW * cfg.ring_base_ratio)

    def render_pixel_frame(amp: float) -> np.ndarray:
        frame = Image.new("RGB", (LOW, LOW), cfg.bg_rgb)
        d = ImageDraw.Draw(frame)

        radius = ring_base + int((LOW * cfg.ring_amp_ratio) * amp)
        width = max(1, cfg.ring_w_min + int(cfg.ring_w_amp * amp))

        d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                  outline=(255, 255, 255), width=width)

        if cfg.inner_accent and amp > 0.25:
            r2 = max(2, radius - (2 + int(4 * amp)))
            w2 = max(1, width // 2)
            d.ellipse((cx - r2, cy - r2, cx + r2, cy + r2),
                      outline=(180, 180, 180), width=w2)

        # avatar selection
        if cfg.breath and len(avatar_cache) >= 3:
            k = 0 if amp < 0.33 else (1 if amp < 0.66 else 2)
        else:
            k = 0
        av = avatar_cache[k]

        ax = cx - av.size[0] // 2
        ay = cy - av.size[1] // 2

        frame_rgba = frame.convert("RGBA")
        frame_rgba.alpha_composite(av, (ax, ay))
        frame = frame_rgba.convert("RGB")

        # upscale to 1080p
        frame = frame.resize((SIZE, SIZE), Image.NEAREST)
        return np.array(frame)

    def make_frame(t: float) -> np.ndarray:
        idx = int(np.clip(int(t * cfg.fps), 0, len(rms) - 1))
        return render_pixel_frame(float(rms[idx]))

    clip = VideoClip(make_frame=make_frame, duration=duration).set_fps(cfg.fps)
    clip = clip.set_audio(AudioFileClip(str(audio_path)))

    out_path = Path(out_path)
    clip.write_videofile(
        str(out_path),
        codec="libx264",
        audio_codec="aac",
        fps=cfg.fps,
        preset="veryfast",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    return out_path

