from PIL import Image
import argparse
import os

def _checkerboard(size: tuple[int, int], tile: int = 12) -> Image.Image:
    """
    Create a typical transparency checkerboard background.
    Returns an RGB image of given size.
    """
    w, h = size
    light = (230, 230, 230)
    dark = (200, 200, 200)
    bg = Image.new("RGB", (w, h), light)

    # draw tiles by pasting solid rectangles (fast enough for small images)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            if ((x // tile) + (y // tile)) % 2 == 0:
                continue
            bg.paste(dark, (x, y, min(x + tile, w), min(y + tile, h)))
    return bg

def convertToJPEG(image_path: str) -> str:
    image = Image.open(image_path)

    # JPEG can't store alpha; composite over a checkerboard so transparency is visible.
    if image.mode in ("RGBA", "LA") or ("transparency" in getattr(image, "info", {})):
        rgba = image.convert("RGBA")
        bg = _checkerboard(rgba.size)
        image = Image.alpha_composite(bg.convert("RGBA"), rgba).convert("RGB")
    else:
        image = image.convert("RGB")

    out_path = image_path.replace(".png", ".jpeg")
    image.save(out_path, format="JPEG", quality=95)
    return out_path

def convertToPNG(image_path: str) -> str:
    image = Image.open(image_path)
    image = image.convert("RGBA")
    image.save(image_path.replace(".jpeg", ".png"))
    return image_path.replace(".jpeg", ".png")

def main():
    parser = argparse.ArgumentParser(description="Convert PNGs to JPEG and back again")
    parser.add_argument("input_path", type=str, help="Path to the input image")
    args = parser.parse_args()
    try:
        newPath = convert(args.input_path)
        print(f"Converted {args.input_path} to {newPath}")
    except ValueError as e:
        print(e)

def convert(image_path: str) -> str:
    if image_path.endswith(".png"):
        newPath = convertToJPEG(image_path)
        newPath = convertToPNG(newPath)
        if os.path.exists(newPath.replace(".png", ".jpeg")):
            os.remove(newPath.replace(".png", ".jpeg"))
        return newPath
    elif image_path.endswith(".jpeg"):
        newPath = convertToPNG(image_path)
        newPath = convertToJPEG(newPath)
        newPath = convertToPNG(newPath)
        if os.path.exists(newPath.replace(".png", ".jpg")):
            os.remove(newPath.replace(".png", ".jpeg"))
        return newPath
    else:
        raise ValueError(f"Unsupported file format: {image_path}")
    
if __name__ == "__main__":
    main()