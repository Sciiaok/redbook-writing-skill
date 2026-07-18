from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "redbook-writing" / "scripts" / "render_text_card_cover.py"


class TextCardRendererTests(unittest.TestCase):
    def run_renderer(self, payload: dict) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                ["python3", str(SCRIPT), "--input", str(input_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            receipt = json.loads(result.stdout)
            if result.returncode == 0:
                with Image.open(payload["output_path"]) as image:
                    image.load()
                    receipt["_decoded_size"] = image.size
                    receipt["_decoded_mode"] = image.mode
            return result, receipt

    def test_renderer_outputs_decodable_xhs_portrait_png(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = str(Path(directory) / "cover.png")
            result, receipt = self.run_renderer({
                "variant": "black_accent_card",
                "headline": "说一个暴论：\n真正好用的封面，\n先让人看懂",
                "accent_terms": ["暴论", "看懂"],
                "meta": "NATIVE COVER · 07/18",
                "output_path": output,
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(receipt["status"], "rendered_prototype")
            self.assertEqual(receipt["_decoded_size"], (1080, 1440))
            self.assertEqual(receipt["_decoded_mode"], "RGB")
            self.assertEqual(receipt["output_state"], "prototype_only")

    def test_all_three_native_variants_render(self) -> None:
        for variant in ("black_accent_card", "paper_meme_card", "highlight_note_card"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                result, receipt = self.run_renderer({
                    "variant": variant,
                    "headline": "最近发现：\n封面不是越精致\n越容易被点开",
                    "accent_terms": ["不是越精致"],
                    "meta": "DAILY NOTE",
                    "output_path": str(Path(directory) / f"{variant}.png"),
                })
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(receipt["_decoded_size"], (1080, 1440))

    def test_more_than_two_accent_terms_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, receipt = self.run_renderer({
                "variant": "black_accent_card",
                "headline": "一个两个三个",
                "accent_terms": ["一个", "两个", "三个"],
                "output_path": str(Path(directory) / "cover.png"),
            })
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipt["status"], "invalid_input")

    def test_text_overflow_fails_instead_of_shrinking_to_ppt_density(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, receipt = self.run_renderer({
                "variant": "black_accent_card",
                "headline": "这是一段故意写得特别特别长而且没有任何信息层级的封面文字" * 8,
                "accent_terms": [],
                "output_path": str(Path(directory) / "cover.png"),
            })
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipt["status"], "text_overflow")


if __name__ == "__main__":
    unittest.main()
