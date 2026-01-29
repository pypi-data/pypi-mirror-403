import argparse
from pathlib import Path

from .render import RenderConfig, render_call_video


def main() -> None:
    p = argparse.ArgumentParser(prog="sosi-call", description="Generate a pixel-art call-style avatar video reacting to audio.")
    p.add_argument("--avatar", required=True, help="Path to avatar image (png/jpg/etc).")
    p.add_argument("--audio", required=True, help="Path to audio (wav/mp3/ogg/etc).")
    p.add_argument("--out", default="sosi_call.mp4", help="Output mp4 path.")
    p.add_argument("--size", type=int, default=1080, help="Output resolution (square).")
    p.add_argument("--low", type=int, default=240, help="Internal render resolution (pixel-art).")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--gain", type=float, default=3.2)
    p.add_argument("--gamma", type=float, default=0.45)
    args = p.parse_args()

    cfg = RenderConfig(size=args.size, low=args.low, fps=args.fps, gain=args.gain, gamma=args.gamma)
    out = render_call_video(Path(args.avatar), Path(args.audio), Path(args.out), cfg=cfg)
    print(f"Done: {out}")

