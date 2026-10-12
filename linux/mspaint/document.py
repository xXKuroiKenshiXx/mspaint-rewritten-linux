"""Transactional raster document and bounded history; no platform APIs."""
from pathlib import Path
from io import BytesIO
from PySide6.QtCore import QIODevice, QSaveFile, QPoint, QRect
from PySide6.QtGui import QColor, QImage, QImageReader, QImageWriter, QPainter

MAX_PIXELS = 64 * 1024 * 1024
MAX_HISTORY_BYTES = 256 * 1024 * 1024


def valid_size(width, height):
    if not (0 < width <= 32767 and 0 < height <= 32767 and width * height <= MAX_PIXELS):
        raise ValueError("Canvas must be positive, at most 32767 per side and 64 megapixels.")


def blank(width, height, color="white"):
    valid_size(width, height)
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    if image.isNull():
        raise MemoryError("Unable to allocate canvas")
    image.fill(QColor(color))
    return image


class Document:
    def __init__(self):
        self.new()

    def new(self, width=1030, height=552):
        image = blank(width, height)
        self.image, self.path = image, None
        self.history, self.position = [image.copy()], 0
        self.saved_key = image.cacheKey()

    @property
    def dirty(self):
        return self.image.cacheKey() != self.saved_key

    def commit(self, image):
        valid_size(image.width(), image.height())
        if image == self.image:
            return
        self.history = self.history[:self.position + 1]
        self.image = image.copy()
        self.history.append(self.image)
        while len(self.history) > 1 and (len(self.history) > 50 or
                sum(i.sizeInBytes() for i in self.history) > MAX_HISTORY_BYTES):
            self.history.pop(0)
        self.position = len(self.history) - 1

    def undo(self):
        if self.position:
            self.position -= 1
            self.image = self.history[self.position]

    def redo(self):
        if self.position + 1 < len(self.history):
            self.position += 1
            self.image = self.history[self.position]

    def load(self, path):
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        size = reader.size()
        if size.isValid():
            valid_size(size.width(), size.height())
        image = reader.read()
        if image.isNull():
            raise ValueError(reader.errorString())
        valid_size(image.width(), image.height())
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self.image, self.path = image, Path(path)
        self.history, self.position = [image], 0
        self.saved_key = image.cacheKey()

    def save(self, path):
        path = Path(path)
        fmt = path.suffix.lower().lstrip(".")
        if fmt == "jpg":
            fmt = "jpeg"
        if fmt != "gif" and fmt.encode() not in [bytes(f) for f in QImageWriter.supportedImageFormats()]:
            raise ValueError(f"Unsupported output format: {fmt}")
        target = QSaveFile(str(path))
        if not target.open(QIODevice.OpenModeFlag.WriteOnly):
            raise OSError(target.errorString())
        image = self.image
        if fmt in ("jpeg", "bmp"):
            image = blank(image.width(), image.height())
            painter = QPainter(image)
            painter.drawImage(0, 0, self.image)
            painter.end()
        if fmt == "gif":
            from PIL import Image
            rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
            encoded = BytesIO()
            try:
                Image.frombytes("RGBA", (rgba.width(), rgba.height()), bytes(rgba.constBits())).save(encoded, format="GIF")
                payload = encoded.getvalue()
                if target.write(payload) != len(payload):
                    raise OSError(target.errorString())
            except Exception:
                target.cancelWriting()
                raise
        else:
            writer = QImageWriter(target, fmt.encode())
            writer.setQuality(95)
            if not writer.write(image):
                target.cancelWriting()
                raise OSError(writer.errorString())
        if not target.commit():
            raise OSError(target.errorString())
        self.path, self.saved_key = path, self.image.cacheKey()

    def resize(self, width, height, scale=False, background="white"):
        valid_size(width, height)
        if scale:
            image = self.image.scaled(width, height)
        else:
            image = blank(width, height, background)
            painter = QPainter(image)
            painter.drawImage(0, 0, self.image)
            painter.end()
        self.commit(image)

    def paste(self, image, point=QPoint()):
        if image.isNull():
            raise ValueError("Clipboard contains no image")
        width = max(self.image.width(), point.x() + image.width())
        height = max(self.image.height(), point.y() + image.height())
        result = blank(width, height)
        painter = QPainter(result)
        painter.drawImage(0, 0, self.image)
        painter.drawImage(point, image)
        painter.end()
        self.commit(result)

    def fill(self, point, color):
        """Scanline flood fill, bounded by canvas size, with no recursion."""
        if not self.image.rect().contains(point):
            return
        image = self.image.copy()
        old, new = image.pixel(point), QColor(color).rgba()
        if old == new:
            return
        todo = [(point.x(), point.y())]
        width, height = image.width(), image.height()
        while todo:
            x, y = todo.pop()
            if image.pixel(x, y) != old:
                continue
            left = x
            while left > 0 and image.pixel(left - 1, y) == old:
                left -= 1
            right = x
            while right + 1 < width and image.pixel(right + 1, y) == old:
                right += 1
            for xx in range(left, right + 1):
                image.setPixel(xx, y, new)
            for yy in (y - 1, y + 1):
                if 0 <= yy < height:
                    run = False
                    for xx in range(left, right + 1):
                        matches = image.pixel(xx, yy) == old
                        if matches and not run:
                            todo.append((xx, yy))
                        run = matches
        self.commit(image)
