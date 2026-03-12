from paddleocr import PaddleOCR
import os
import traceback

class OCREngine:

    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            use_gpu=False
        )

    def extract_text(self, image_path):

        try:
            if not os.path.exists(image_path):
                return ""

            result = self.ocr.ocr(image_path)

            # ---------------- SAFE GUARD ----------------
            if result is None:
                return ""

            if len(result) == 0:
                return ""

            text = []

            for line in result:

                if line is None:
                    continue

                for word in line:

                    if word is None:
                        continue

                    if len(word) < 2:
                        continue

                    text.append(word[1][0])

            return " ".join(text)

        except Exception:
            traceback.print_exc()
            return ""