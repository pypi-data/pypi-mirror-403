import os
from pathlib        import Path
from PIL            import Image
from src.ilovejpngs import convertToJPEG, convertToPNG, convert


def _createTempImage(tmp_path: Path, name: str, mode: str, fmt: str) -> str:
    imgPath = tmp_path / name
    image   = Image.new(mode, (10, 10), color=(255, 0, 0, 255) if "A" in mode else (255, 0, 0))
    image.save(imgPath, format = fmt)
    return str(imgPath)


class TestIlovejpngs:
    def setup_method(self) -> None:
        self._paths: list[str] = []

    def teardown_method(self, method) -> None:  # runs after each test method
        for p in self._paths:
            if os.path.exists(p):
                os.remove(p)
        self._paths.clear()

    def _track(self, path: str) -> str:
        self._paths.append(path)
        return path

    def test_convert_to_jpeg_creates_jpeg(self, tmp_path: Path):
        png_path   = self._track(_createTempImage(tmp_path, "input.png", "RGBA", "PNG"))
        resultPath = self._track(convertToJPEG(png_path))

        assert resultPath.endswith(".jpeg")
        assert os.path.exists(resultPath)

        img = Image.open(resultPath)
        assert img.mode == "RGB"

    def test_convert_to_jpeg_uses_checkerboard_for_transparency(self, tmp_path: Path):
        # Create a fully transparent PNG and ensure JPEG isn't flattened to black.
        transparent_png = tmp_path / "transparent.png"
        Image.new("RGBA", (24, 24), color=(0, 0, 0, 0)).save(transparent_png, format="PNG")
        self._track(str(transparent_png))

        jpeg_path = self._track(convertToJPEG(str(transparent_png)))
        img = Image.open(jpeg_path).convert("RGB")
        px = img.getpixel((0, 0))

        # With our checkerboard background this should be a light/dark gray, not black.
        assert px != (0, 0, 0)

    def test_convert_to_png_creates_png(self, tmp_path: Path):
        jpegPath   = self._track(_createTempImage(tmp_path, "input.jpeg", "RGB", "JPEG"))
        resultPath = self._track(convertToPNG(jpegPath))

        assert resultPath.endswith(".png")
        assert os.path.exists(resultPath)

        img = Image.open(resultPath)
        assert img.mode == "RGBA"

    def test_convert_roundtrip_from_png(self, tmp_path: Path):
        pngPath    = self._track(_createTempImage(tmp_path, "input.png", "RGBA", "PNG"))
        resultPath = self._track(convert(pngPath))

        assert resultPath.endswith(".png")
        assert os.path.exists(resultPath)

    def test_convert_roundtrip_from_jpeg(self, tmp_path: Path):
        jpegPath   = self._track(_createTempImage(tmp_path, "input.jpeg", "RGB", "JPEG"))
        resultPath = self._track(convert(jpegPath))

        assert resultPath.endswith(".png")
        assert os.path.exists(resultPath)

