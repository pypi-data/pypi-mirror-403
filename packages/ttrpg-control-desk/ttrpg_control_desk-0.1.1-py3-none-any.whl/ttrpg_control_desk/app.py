#!/usr/bin/env python3
import sys
import os
from collections import OrderedDict
from typing import NamedTuple
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QListWidgetItem, QPushButton, QFileDialog,
                             QCheckBox, QSlider, QSizePolicy, QMainWindow, QDockWidget,
                             QToolBar, QAction)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QBrush, QIcon, QImageReader, QCursor, QPen
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize, QThread, QObject, QTimer, QEvent


# Viewport state
class Viewport(NamedTuple):
    zoom: float = 1.0
    center_x: float = 0.5
    center_y: float = 0.5


# Configuration
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
EXTERNAL_WINDOW_SIZE = (800, 600)
CONTROL_WINDOW_SIZE = (1200, 700)
THUMBNAIL_SIZE = 80

# Character overlay configuration
PORTRAIT_WIDTH = 300
PORTRAIT_HEIGHT = 300
PORTRAIT_MARGIN = 5

# Pointer configuration
POINTER_RADIUS = 18
POINTER_COLOR = QColor(255, 50, 50, 180)
POINTER_BORDER_COLOR = QColor(255, 255, 255)
POINTER_BORDER_WIDTH = 3

# Cache configuration
IMAGE_CACHE_SIZE = 10  # Number of full images to keep in memory
THUMBNAIL_CACHE_DIR = ".thumbnails"


class LRUCache:
    """Simple LRU cache for loaded images."""

    def __init__(self, max_size):
        self.max_size = max_size
        self.cache = OrderedDict()

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
        self.cache[key] = value

    def clear(self):
        self.cache.clear()


class ImageLoader(QObject):
    """Worker for loading images in background thread."""
    finished = pyqtSignal(str, object, float)  # path, pixmap, zoom_level

    def __init__(self, path, max_width, max_height, zoom_level):
        super().__init__()
        self.path = path
        self.max_width = max_width
        self.max_height = max_height
        self.zoom_level = zoom_level

    def run(self):
        pixmap = load_scaled_image(self.path, self.max_width, self.max_height)
        self.finished.emit(self.path, pixmap, self.zoom_level)


def get_thumbnail_cache_path(folder_path):
    """Get path to thumbnail cache directory for a folder."""
    cache_dir = os.path.join(folder_path, THUMBNAIL_CACHE_DIR)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir


def get_cached_thumbnail(folder_path, filename, size):
    """Load thumbnail from disk cache if available and valid."""
    cache_dir = get_thumbnail_cache_path(folder_path)
    cache_name = f"{filename}_{size}.png"
    cache_path = os.path.join(cache_dir, cache_name)
    original_path = os.path.join(folder_path, filename)

    # Check if cache exists and is newer than original
    if os.path.exists(cache_path):
        if os.path.getmtime(cache_path) >= os.path.getmtime(original_path):
            pixmap = QPixmap(cache_path)
            if not pixmap.isNull():
                return pixmap
    return None


def save_cached_thumbnail(folder_path, filename, size, pixmap):
    """Save thumbnail to disk cache."""
    cache_dir = get_thumbnail_cache_path(folder_path)
    cache_name = f"{filename}_{size}.png"
    cache_path = os.path.join(cache_dir, cache_name)
    pixmap.save(cache_path, "PNG")


def load_thumbnail(path, size):
    """Load image as thumbnail efficiently without decoding full resolution."""
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    original_size = reader.size()
    if original_size.isValid():
        # Calculate scaled size maintaining aspect ratio
        scaled = original_size.scaled(size, size, Qt.KeepAspectRatio)
        reader.setScaledSize(scaled)
    image = reader.read()
    return QPixmap.fromImage(image)


def load_thumbnail_cached(folder_path, filename, size):
    """Load thumbnail with disk caching."""
    # Try disk cache first
    cached = get_cached_thumbnail(folder_path, filename, size)
    if cached:
        return cached

    # Load and cache
    path = os.path.join(folder_path, filename)
    pixmap = load_thumbnail(path, size)
    if not pixmap.isNull():
        save_cached_thumbnail(folder_path, filename, size, pixmap)
    return pixmap


def load_scaled_image(path, max_width, max_height):
    """Load image scaled to fit within max dimensions (only downscales if needed)."""
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    original_size = reader.size()
    if original_size.isValid():
        # Only scale down if image is larger than max dimensions
        if original_size.width() > max_width or original_size.height() > max_height:
            scaled = original_size.scaled(max_width, max_height, Qt.KeepAspectRatio)
            reader.setScaledSize(scaled)
    image = reader.read()
    return QPixmap.fromImage(image)


# Fog of war configuration
FOG_COLOR = (0, 0, 0)  # Black fog
FOG_ALPHA = 255        # Fully opaque
PREVIEW_FOG_ALPHA = 150  # Semi-transparent for preview (see through while painting)
DEFAULT_BRUSH_SIZE = 30
MIN_BRUSH_SIZE = 10
MAX_BRUSH_SIZE = 100


def calculate_visible_region(width, height, viewport):
    """Calculate visible region for viewport cropping.

    Returns (x, y, w, h) as integers for the visible region.
    """
    view_w = width / viewport.zoom
    view_h = height / viewport.zoom
    view_x = viewport.center_x * width - view_w / 2
    view_y = viewport.center_y * height - view_h / 2
    return int(view_x), int(view_y), int(view_w), int(view_h)


class FogMask:
    """Store and manipulate the fog mask for a background image."""

    def __init__(self, width, height):
        # QImage with alpha channel, starts fully opaque (fogged)
        self.mask = QImage(width, height, QImage.Format_ARGB32)
        self.mask.fill(QColor(FOG_COLOR[0], FOG_COLOR[1], FOG_COLOR[2], FOG_ALPHA))

    def width(self):
        return self.mask.width()

    def height(self):
        return self.mask.height()

    def reveal(self, x, y, radius):
        """Paint transparent circle at (x, y) to reveal the area."""
        painter = QPainter(self.mask)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.setBrush(QBrush(Qt.transparent))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(int(x), int(y)), radius, radius)
        painter.end()

    def clear_all(self):
        """Reveal everything (remove all fog)."""
        self.mask.fill(Qt.transparent)

    def fog_all(self):
        """Hide everything (full fog)."""
        self.mask.fill(QColor(FOG_COLOR[0], FOG_COLOR[1], FOG_COLOR[2], FOG_ALPHA))

    def get_cropped(self, viewport):
        """Return cropped portion of fog mask for the given viewport."""
        x, y, w, h = calculate_visible_region(self.width(), self.height(), viewport)
        return self.mask.copy(x, y, w, h)

    def apply_to(self, pixmap):
        """Return pixmap with fog overlay applied."""
        result = QPixmap(pixmap.size())
        result.fill(Qt.black)
        painter = QPainter(result)
        painter.drawPixmap(0, 0, pixmap)
        # Scale mask to pixmap size and draw
        scaled_mask = self.mask.scaled(pixmap.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        painter.drawImage(0, 0, scaled_mask)
        painter.end()
        return result


class FogPreview(QLabel):
    """Interactive preview widget that captures mouse events for fog painting."""

    fog_changed = pyqtSignal()  # Emitted when fog mask is modified
    viewport_changed = pyqtSignal()  # Emitted when pan changes viewport
    pointer_moved = pyqtSignal(float, float)  # Emitted with normalized coords (0-1)

    def __init__(self):
        super().__init__()
        self.fog_enabled = False
        self.brush_size = DEFAULT_BRUSH_SIZE
        self.fog_mask = None
        self.background_pixmap = None
        self.character_pixmaps = []
        self.portrait_height = PORTRAIT_HEIGHT
        self.painting = False
        self.setMouseTracking(True)

        # Viewport state
        self.zoom_level = 1.0  # 1.0 = 100%, 2.0 = 200%, etc.
        self.view_center_x = 0.5  # Normalized 0-1 coordinates of center point
        self.view_center_y = 0.5
        self.dragging = False
        self.last_drag_pos = None
        self.pointer_active = False

    def _create_brush_cursor(self, size):
        """Create a circular cursor for the brush."""
        cursor_size = max(size, 8)
        pixmap = QPixmap(cursor_size, cursor_size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 255, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(1, 1, cursor_size - 2, cursor_size - 2)
        # Inner dark circle for visibility on light backgrounds
        pen.setColor(QColor(0, 0, 0, 150))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(2, 2, cursor_size - 4, cursor_size - 4)
        painter.end()

        return QCursor(pixmap, cursor_size // 2, cursor_size // 2)

    def update_cursor(self):
        """Update cursor based on fog enabled state."""
        if self.fog_enabled:
            # Calculate visual brush size on preview
            visual_size = self.brush_size
            pixmap = self.pixmap()
            if pixmap and self.fog_mask:
                # Brush is applied in mask space, convert to preview space
                scale = pixmap.width() / self.fog_mask.width()
                visual_size = int(self.brush_size * scale * 2)  # diameter
            self.setCursor(self._create_brush_cursor(visual_size))
        else:
            self.unsetCursor()

    def set_characters(self, pixmaps, portrait_height=PORTRAIT_HEIGHT):
        """Set character portraits to display."""
        self.character_pixmaps = pixmaps
        self.portrait_height = portrait_height
        self._update_preview()

    def set_background(self, pixmap):
        """Set the background pixmap for preview."""
        self.background_pixmap = pixmap
        self._update_preview()

    def set_fog_mask(self, fog_mask):
        """Set the fog mask to use."""
        self.fog_mask = fog_mask
        self._update_preview()

    def set_fog_enabled(self, enabled):
        """Enable or disable fog display."""
        self.fog_enabled = enabled
        self.update_cursor()
        self._update_preview()

    def set_zoom(self, zoom_level):
        """Set zoom level and update preview."""
        self.zoom_level = max(1.0, min(4.0, zoom_level))
        self._clamp_view_center()
        self._update_preview()

    def set_viewport(self, zoom_level, center_x, center_y):
        """Set the complete viewport state."""
        self.zoom_level = zoom_level
        self.view_center_x = center_x
        self.view_center_y = center_y
        self._clamp_view_center()
        self._update_preview()

    def get_viewport(self):
        """Return the current viewport state."""
        return (self.zoom_level, self.view_center_x, self.view_center_y)

    def _clamp_view_center(self):
        """Clamp view center to keep viewport within image bounds."""
        if self.zoom_level <= 1.0:
            self.view_center_x = 0.5
            self.view_center_y = 0.5
            return

        # Calculate the half-size of viewport in normalized coordinates
        half_view_w = 0.5 / self.zoom_level
        half_view_h = 0.5 / self.zoom_level

        # Clamp center so viewport stays within [0, 1]
        self.view_center_x = max(half_view_w, min(1.0 - half_view_w, self.view_center_x))
        self.view_center_y = max(half_view_h, min(1.0 - half_view_h, self.view_center_y))

    def _update_preview(self):
        """Update the preview display with viewport-based rendering."""
        if self.background_pixmap is None:
            self.clear()
            return

        viewport = Viewport(self.zoom_level, self.view_center_x, self.view_center_y)
        bg_w = self.background_pixmap.width()
        bg_h = self.background_pixmap.height()

        if viewport.zoom <= 1.0:
            # No zoom: scale entire background to preview size
            scaled_bg = self.background_pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            # Crop visible region and scale to fill preview
            x, y, w, h = calculate_visible_region(bg_w, bg_h, viewport)
            cropped = self.background_pixmap.copy(x, y, w, h)
            scaled_bg = cropped.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        if self.fog_enabled and self.fog_mask:
            # Apply fog to preview with reduced opacity (so GM can see what's underneath)
            if viewport.zoom <= 1.0:
                display_pixmap = self._apply_preview_fog(scaled_bg, self.fog_mask.mask)
            else:
                cropped_mask = self.fog_mask.get_cropped(viewport)
                display_pixmap = self._apply_preview_fog(scaled_bg, cropped_mask)
        else:
            display_pixmap = scaled_bg

        # Draw characters on top
        if self.character_pixmaps:
            display_pixmap = self._draw_characters(display_pixmap)

        self.setPixmap(display_pixmap)

    def _draw_characters(self, pixmap):
        """Draw character portraits on the pixmap."""
        result = QPixmap(pixmap)
        painter = QPainter(result)

        # Scale portrait size relative to preview size
        scale = min(pixmap.width(), pixmap.height()) / 600.0
        portrait_w = int(self.portrait_height * scale * 0.5)
        portrait_h = int(self.portrait_height * scale * 0.5)
        margin = int(PORTRAIT_MARGIN * scale)

        y = pixmap.height() - portrait_h - margin

        for i, char_pixmap in enumerate(self.character_pixmaps):
            slot = i // 2
            if i % 2 == 0:
                # Left side
                x = margin + slot * (portrait_w + margin)
            else:
                # Right side
                x = pixmap.width() - portrait_w - margin - slot * (portrait_w + margin)

            # Scale and draw character
            scaled_char = char_pixmap.scaled(portrait_w, portrait_h,
                                              Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Center in the slot
            char_x = x + (portrait_w - scaled_char.width()) // 2
            char_y = y + (portrait_h - scaled_char.height()) // 2
            painter.drawPixmap(char_x, char_y, scaled_char)

        painter.end()
        return result

    def _apply_preview_fog(self, pixmap, mask):
        """Apply fog with reduced opacity for preview visibility."""
        result = QPixmap(pixmap.size())
        result.fill(Qt.black)
        painter = QPainter(result)
        painter.drawPixmap(0, 0, pixmap)

        # Scale mask to pixmap size
        scaled_mask = mask.scaled(pixmap.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        # Draw fog with reduced opacity
        painter.setOpacity(PREVIEW_FOG_ALPHA / 255.0)
        painter.drawImage(0, 0, scaled_mask)
        painter.end()
        return result

    def mousePressEvent(self, event):
        """Handle mouse press to start painting or panning."""
        if event.button() == Qt.LeftButton:
            if self.fog_enabled and self.fog_mask:
                self.painting = True
                self._paint_at(event.pos())
        elif event.button() in (Qt.MiddleButton, Qt.RightButton):
            # Start dragging for pan
            self.dragging = True
            self.last_drag_pos = event.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for continuous painting or panning."""
        if self.pointer_active:
            # Emit normalized pointer position
            norm_x = event.pos().x() / self.width()
            norm_y = event.pos().y() / self.height()
            self.pointer_moved.emit(norm_x, norm_y)
        elif self.painting and self.fog_enabled and self.fog_mask:
            self._paint_at(event.pos())
        elif self.dragging and self.last_drag_pos and self.zoom_level > 1.0:
            # Calculate delta in widget coordinates
            delta = event.pos() - self.last_drag_pos
            self.last_drag_pos = event.pos()

            # Convert delta to normalized coordinates (inverted for natural drag)
            # Movement in widget space should move the view center in opposite direction
            pixmap = self.pixmap()
            if pixmap:
                # Scale factor: how much of the image is visible
                delta_x = -delta.x() / pixmap.width() / self.zoom_level
                delta_y = -delta.y() / pixmap.height() / self.zoom_level

                self.view_center_x += delta_x
                self.view_center_y += delta_y
                self._clamp_view_center()
                self._update_preview()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop painting or panning."""
        if event.button() == Qt.LeftButton:
            self.painting = False
        elif event.button() in (Qt.MiddleButton, Qt.RightButton):
            if self.dragging:
                self.dragging = False
                self.last_drag_pos = None
                self.viewport_changed.emit()

    def _paint_at(self, pos):
        """Paint (reveal) at the given preview position."""
        if not self.fog_mask or not self.background_pixmap:
            return

        # Get the actual displayed pixmap dimensions
        pixmap = self.pixmap()
        if not pixmap:
            return

        # Calculate offset (preview is centered in label)
        offset_x = (self.width() - pixmap.width()) // 2
        offset_y = (self.height() - pixmap.height()) // 2

        # Adjust position for centering
        adjusted_x = pos.x() - offset_x
        adjusted_y = pos.y() - offset_y

        # Check if click is within the image area
        if adjusted_x < 0 or adjusted_y < 0:
            return
        if adjusted_x >= pixmap.width() or adjusted_y >= pixmap.height():
            return

        # Convert preview coords to mask coords, accounting for viewport
        mask_w = self.fog_mask.width()
        mask_h = self.fog_mask.height()

        if self.zoom_level <= 1.0:
            # No zoom: simple scaling
            scale_x = mask_w / pixmap.width()
            scale_y = mask_h / pixmap.height()
            mask_x = adjusted_x * scale_x
            mask_y = adjusted_y * scale_y
        else:
            # Zoomed: need to account for visible region
            viewport = Viewport(self.zoom_level, self.view_center_x, self.view_center_y)
            view_x, view_y, view_w, view_h = calculate_visible_region(mask_w, mask_h, viewport)

            # Convert widget position to position within visible region
            rel_x = adjusted_x / pixmap.width()
            rel_y = adjusted_y / pixmap.height()
            mask_x = view_x + rel_x * view_w
            mask_y = view_y + rel_y * view_h

        # Scale brush size to mask coordinates (account for zoom)
        base_scale = mask_w / pixmap.width()
        brush_radius = int(self.brush_size * base_scale / self.zoom_level)

        # Reveal at position
        self.fog_mask.reveal(mask_x, mask_y, brush_radius)

        # Update preview and emit signal
        self._update_preview()
        self.fog_changed.emit()

    def resizeEvent(self, event):
        """Handle resize to update preview."""
        super().resizeEvent(event)
        self._update_preview()


class BackgroundWidget(QWidget):
    """Custom widget that draws background pixmap and pointer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.pointer_visible = False
        self.pointer_x = 0.5
        self.pointer_y = 0.5

    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def clear(self):
        self.pixmap = None
        self.update()

    def show_pointer(self, x, y):
        self.pointer_x = x
        self.pointer_y = y
        self.pointer_visible = True
        self.repaint()

    def hide_pointer(self):
        self.pointer_visible = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Fill with black background
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        # Draw pixmap centered
        if self.pixmap:
            x = (self.width() - self.pixmap.width()) // 2
            y = (self.height() - self.pixmap.height()) // 2
            painter.drawPixmap(x, y, self.pixmap)

        # Draw pointer on top
        if self.pointer_visible:
            painter.setRenderHint(QPainter.Antialiasing)
            px = int(self.pointer_x * self.width())
            py = int(self.pointer_y * self.height())
            painter.setPen(QPen(POINTER_BORDER_COLOR, POINTER_BORDER_WIDTH))
            painter.setBrush(QBrush(POINTER_COLOR))
            diameter = POINTER_RADIUS * 2
            painter.drawEllipse(px - POINTER_RADIUS, py - POINTER_RADIUS, diameter, diameter)

        painter.end()


class ExternalDisplay(QWidget):
    """External display widget with background and character overlays."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")

        # Background widget (custom widget that draws pixmap + pointer)
        self.background_widget = BackgroundWidget(self)
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        self.background_widget.show()

        # Store current pixmaps
        self.background_pixmap = None
        self.character_pixmaps = []
        self.portrait_labels = []
        self.portrait_width = PORTRAIT_WIDTH
        self.portrait_height = PORTRAIT_HEIGHT

        # Fog of war
        self.fog_mask = None
        self.fog_enabled = False

        # Viewport state
        self.zoom_level = 1.0
        self.view_center_x = 0.5
        self.view_center_y = 0.5

    def show_pointer(self, x, y):
        """Show pointer at normalized position (0-1, 0-1)."""
        self.background_widget.show_pointer(x, y)

    def hide_pointer(self):
        """Hide the pointer."""
        self.background_widget.hide_pointer()

    def showEvent(self, event):
        """Handle show to ensure proper sizing."""
        super().showEvent(event)
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        self._update_background()

    def resizeEvent(self, event):
        """Handle resize to rescale images."""
        super().resizeEvent(event)
        # Resize background widget to fill the display
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        self._update_background()
        self._position_portraits()

    def set_fog_mask(self, fog_mask):
        """Set the fog mask to use."""
        self.fog_mask = fog_mask
        self._update_background()

    def set_fog_enabled(self, enabled):
        """Enable or disable fog overlay."""
        self.fog_enabled = enabled
        self._update_background()

    def set_viewport(self, zoom_level, center_x, center_y):
        """Set the viewport state (synced from preview)."""
        self.zoom_level = zoom_level
        self.view_center_x = center_x
        self.view_center_y = center_y
        self._update_background()

    def set_background(self, pixmap):
        """Set the background image."""
        self.background_pixmap = pixmap
        self._update_background()

    def _update_background(self):
        """Rescale and display background with optional fog overlay and viewport."""
        if self.background_pixmap:
            viewport = Viewport(self.zoom_level, self.view_center_x, self.view_center_y)
            bg_w = self.background_pixmap.width()
            bg_h = self.background_pixmap.height()

            if viewport.zoom <= 1.0:
                # No zoom: scale entire background to widget size
                scaled = self.background_pixmap.scaled(
                    self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                # Crop visible region and scale to fill widget
                x, y, w, h = calculate_visible_region(bg_w, bg_h, viewport)
                cropped = self.background_pixmap.copy(x, y, w, h)
                scaled = cropped.scaled(
                    self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Apply fog of war if enabled
            if self.fog_enabled and self.fog_mask:
                if viewport.zoom <= 1.0:
                    display_pixmap = self.fog_mask.apply_to(scaled)
                else:
                    cropped_mask = self.fog_mask.get_cropped(viewport)
                    # Apply cropped fog to scaled background
                    result = QPixmap(scaled.size())
                    result.fill(Qt.black)
                    painter = QPainter(result)
                    painter.drawPixmap(0, 0, scaled)
                    scaled_mask = cropped_mask.scaled(
                        scaled.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                    painter.drawImage(0, 0, scaled_mask)
                    painter.end()
                    display_pixmap = result
            else:
                display_pixmap = scaled

            self.background_widget.setPixmap(display_pixmap)
        else:
            self.background_widget.clear()

    def set_characters(self, pixmaps, portrait_height=PORTRAIT_HEIGHT):
        """Set the character portraits as overlays."""
        self.character_pixmaps = pixmaps
        self.portrait_height = portrait_height
        self.portrait_width = portrait_height  # Keep square

        # Remove existing portrait labels
        for label in self.portrait_labels:
            label.deleteLater()
        self.portrait_labels = []

        # Create new portrait labels
        for pixmap in pixmaps:
            label = QLabel(self)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background-color: transparent;")
            label.setFixedSize(self.portrait_width, self.portrait_height)
            scaled = pixmap.scaled(
                self.portrait_width,
                self.portrait_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled)
            label.show()
            label.raise_()  # Ensure above background widget
            self.portrait_labels.append(label)

        self._position_portraits()

    def _position_portraits(self):
        """Position portrait labels at the bottom, alternating left and right."""
        y = self.height() - self.portrait_height - PORTRAIT_MARGIN

        for i, label in enumerate(self.portrait_labels):
            slot = i // 2  # Which position from the edge (0, 0, 1, 1, 2, 2, ...)
            if i % 2 == 0:
                # Even indices: left side
                x = PORTRAIT_MARGIN + slot * (self.portrait_width + PORTRAIT_MARGIN)
            else:
                # Odd indices: right side
                x = self.width() - self.portrait_width - PORTRAIT_MARGIN - slot * (self.portrait_width + PORTRAIT_MARGIN)
            label.move(x, y)

class ImageRegie(QMainWindow):
    def __init__(self, root_folder):
        super().__init__()

        self.root_folder = root_folder
        self.backgrounds_folder = None
        self.characters_folder = None
        self.background_images = []
        self.character_images = []
        self.index = 0

        # Fog of war state
        self.fog_enabled = False
        self.fog_masks = {}  # Maps image filename to FogMask

        # Viewport state per image
        self.viewports = {}  # Maps filename to (zoom, center_x, center_y)
        self.current_bg_filename = None
        self.current_bg_path = None
        self.current_loaded_zoom = 1.0  # Track what zoom level the image was loaded for

        # Image cache for fast navigation
        self.image_cache = LRUCache(IMAGE_CACHE_SIZE)

        # Async loading
        self.loader_thread = None
        self.pending_load = None  # Track pending async load

        self._setup_ui()
        self._setup_docks()
        self._setup_toolbar()
        self._setup_external_display()

        # Install event filter to capture key events globally
        QApplication.instance().installEventFilter(self)

        self.show()
        self.auto_detect_folders()

    def _setup_ui(self):
        """Setup central widget with preview."""
        self.preview = FogPreview()
        self.preview.setMinimumSize(400, 300)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background-color: #1a1a1a;")
        self.preview.fog_changed.connect(self.on_fog_changed)
        self.preview.viewport_changed.connect(self.on_viewport_changed)

        self.setCentralWidget(self.preview)
        self.setWindowTitle("GM Control")
        self.resize(*CONTROL_WINDOW_SIZE)

    def _setup_docks(self):
        """Setup dock widgets for backgrounds, characters, and fog."""
        # Backgrounds dock (left)
        self.bg_list = QListWidget()
        self.bg_list.setViewMode(QListWidget.ListMode)
        self.bg_list.setIconSize(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        self.bg_list.setSpacing(3)
        self.bg_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bg_list.currentRowChanged.connect(self.change_background)

        self.bg_folder_btn = QPushButton("Folder...")
        self.bg_folder_btn.clicked.connect(self.select_backgrounds_folder)

        bg_widget = QWidget()
        bg_layout = QVBoxLayout(bg_widget)
        bg_layout.addWidget(self.bg_list, stretch=1)
        bg_layout.addWidget(self.bg_folder_btn)
        bg_layout.setContentsMargins(5, 5, 5, 5)

        self.bg_dock = QDockWidget("Backgrounds", self)
        self.bg_dock.setWidget(bg_widget)
        self.bg_dock.setMinimumWidth(THUMBNAIL_SIZE + 40)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.bg_dock)

        # Characters dock (right)
        self.character_list = QListWidget()
        self.character_list.setViewMode(QListWidget.ListMode)
        self.character_list.setIconSize(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        self.character_list.setSpacing(3)
        self.character_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.character_list.setSelectionMode(QListWidget.MultiSelection)
        self.character_list.itemSelectionChanged.connect(self.update_display)

        self.char_folder_btn = QPushButton("Folder...")
        self.char_folder_btn.clicked.connect(self.select_characters_folder)

        # Character height control
        self.portrait_height = PORTRAIT_HEIGHT
        self.char_height_label = QLabel(f"Size: {PORTRAIT_HEIGHT}")
        self.char_height_slider = QSlider(Qt.Horizontal)
        self.char_height_slider.setMinimum(100)
        self.char_height_slider.setMaximum(600)
        self.char_height_slider.setValue(PORTRAIT_HEIGHT)
        self.char_height_slider.valueChanged.connect(self.change_portrait_height)

        char_widget = QWidget()
        char_layout = QVBoxLayout(char_widget)
        char_layout.addWidget(self.character_list, stretch=1)
        char_layout.addWidget(self.char_height_label)
        char_layout.addWidget(self.char_height_slider)
        char_layout.addWidget(self.char_folder_btn)
        char_layout.setContentsMargins(5, 5, 5, 5)

        self.char_dock = QDockWidget("Characters", self)
        self.char_dock.setWidget(char_widget)
        self.char_dock.setMinimumWidth(THUMBNAIL_SIZE + 40)
        self.addDockWidget(Qt.RightDockWidgetArea, self.char_dock)

        # Fog dock (bottom, hidden by default)
        self.fog_checkbox = QCheckBox("Enable Fog")
        self.fog_checkbox.stateChanged.connect(self.toggle_fog)

        self.brush_label = QLabel(f"Brush: {DEFAULT_BRUSH_SIZE}")
        self.brush_slider = QSlider(Qt.Horizontal)
        self.brush_slider.setMinimum(MIN_BRUSH_SIZE)
        self.brush_slider.setMaximum(MAX_BRUSH_SIZE)
        self.brush_slider.setValue(DEFAULT_BRUSH_SIZE)
        self.brush_slider.setMaximumWidth(150)
        self.brush_slider.valueChanged.connect(self.change_brush_size)

        self.fog_clear_btn = QPushButton("Clear")
        self.fog_clear_btn.clicked.connect(self.clear_fog)
        self.fog_fill_btn = QPushButton("Fill")
        self.fog_fill_btn.clicked.connect(self.fill_fog)

        fog_widget = QWidget()
        fog_layout = QHBoxLayout(fog_widget)
        fog_layout.addWidget(self.fog_checkbox)
        fog_layout.addWidget(self.brush_label)
        fog_layout.addWidget(self.brush_slider)
        fog_layout.addWidget(self.fog_clear_btn)
        fog_layout.addWidget(self.fog_fill_btn)
        fog_layout.addStretch()
        fog_layout.setContentsMargins(5, 5, 5, 5)

        self.fog_dock = QDockWidget("Fog of War", self)
        self.fog_dock.setWidget(fog_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.fog_dock)
        self.fog_dock.hide()  # Hidden by default

    def _setup_toolbar(self):
        """Setup toolbar with common actions."""
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Zoom controls
        self.zoom_label = QLabel(" Zoom: 100% ")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(100)
        self.zoom_slider.setMaximum(400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setMaximumWidth(120)
        self.zoom_slider.valueChanged.connect(self.change_zoom)

        toolbar.addWidget(self.zoom_label)
        toolbar.addWidget(self.zoom_slider)
        toolbar.addSeparator()

        # Fullscreen action
        self.fullscreen_action = QAction("Fullscreen (F)", self)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        toolbar.addAction(self.fullscreen_action)

        toolbar.addSeparator()

        # View menu actions for docks
        toolbar.addAction(self.bg_dock.toggleViewAction())
        toolbar.addAction(self.char_dock.toggleViewAction())
        toolbar.addAction(self.fog_dock.toggleViewAction())

    def _setup_external_display(self):
        """Setup external display window."""
        self.external_display = ExternalDisplay()
        self.external_display.setWindowFlags(Qt.Window)
        self.external_display.setWindowTitle("Player Display")
        self.is_fullscreen = False

        # Choose external screen (second screen if available)
        screens = QApplication.screens()
        if len(screens) > 1:
            self.external_screen = screens[1]
        else:
            self.external_screen = screens[0]

        # Start as a normal window on external screen
        geo = self.external_screen.geometry()
        self.external_display.setGeometry(geo.x() + 50, geo.y() + 50, *EXTERNAL_WINDOW_SIZE)
        self.external_display.show()

        # Connect pointer signal
        self.preview.pointer_moved.connect(self.external_display.show_pointer)

    def auto_detect_folders(self):
        """Auto-detect Backgrounds/ and Characters/ subfolders in root."""
        if not self.root_folder:
            return

        bg_names = ['Backgrounds', 'backgrounds', 'Fonds', 'fonds']
        char_names = ['Characters', 'characters', 'Personnages', 'personnages']

        for name in bg_names:
            path = os.path.join(self.root_folder, name)
            if os.path.isdir(path):
                self.load_backgrounds_folder(path)
                break

        for name in char_names:
            path = os.path.join(self.root_folder, name)
            if os.path.isdir(path):
                self.load_characters_folder(path)
                break

    def select_backgrounds_folder(self):
        """Open folder dialog to select backgrounds folder."""
        start_dir = self.root_folder or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self, "Select backgrounds folder", start_dir)
        if folder:
            self.load_backgrounds_folder(folder)

    def select_characters_folder(self):
        """Open folder dialog to select characters folder."""
        start_dir = self.root_folder or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self, "Select characters folder", start_dir)
        if folder:
            self.load_characters_folder(folder)

    def load_backgrounds_folder(self, folder_path):
        """Load background images from the specified folder."""
        self.backgrounds_folder = folder_path
        self.background_images = [f for f in os.listdir(folder_path)
                                   if f.lower().endswith(IMAGE_EXTENSIONS)]
        self.background_images.sort()
        self.index = 0

        # Update list widget with thumbnails (using disk cache)
        self.bg_list.clear()
        for filename in self.background_images:
            thumb = load_thumbnail_cached(folder_path, filename, THUMBNAIL_SIZE)
            item = QListWidgetItem(QIcon(thumb), filename)
            self.bg_list.addItem(item)

        # Update button tooltip
        self.bg_folder_btn.setToolTip(folder_path)

    def load_characters_folder(self, folder_path):
        """Load character images from the specified folder."""
        self.characters_folder = folder_path
        self.character_images = [f for f in os.listdir(folder_path)
                                  if f.lower().endswith(IMAGE_EXTENSIONS)]
        self.character_images.sort()

        # Update character list widget with thumbnails (using disk cache)
        self.character_list.clear()
        for filename in self.character_images:
            thumb = load_thumbnail_cached(folder_path, filename, THUMBNAIL_SIZE)
            item = QListWidgetItem(QIcon(thumb), filename)
            self.character_list.addItem(item)

        # Update button tooltip
        self.char_folder_btn.setToolTip(folder_path)

    def change_background(self, row):
        """Handle background selection from list."""
        if row >= 0:
            self.index = row
            self.update_display()

    def toggle_fullscreen(self):
        """Toggle external window between windowed and fullscreen."""
        if self.is_fullscreen:
            self.external_display.showNormal()
            geo = self.external_screen.geometry()
            self.external_display.setGeometry(geo.x() + 50, geo.y() + 50, *EXTERNAL_WINDOW_SIZE)
            self.fullscreen_action.setText("Fullscreen (F)")
        else:
            self.external_display.showFullScreen()
            self.fullscreen_action.setText("Windowed (F)")
        self.is_fullscreen = not self.is_fullscreen
        # Refresh display to fit new window size
        QApplication.processEvents()
        self.update_display()

    def toggle_fog(self, state):
        """Enable or disable fog of war."""
        self.fog_enabled = state == Qt.Checked
        self.preview.set_fog_enabled(self.fog_enabled)
        self.external_display.set_fog_enabled(self.fog_enabled)

    def change_brush_size(self, value):
        """Update the brush size for fog painting."""
        self.preview.brush_size = value
        self.preview.update_cursor()
        self.brush_label.setText(f"Brush: {value}")

    def change_portrait_height(self, value):
        """Update character portrait height."""
        self.portrait_height = value
        self.char_height_label.setText(f"Size: {value}")
        # Refresh character display
        self.update_display()

    def clear_fog(self):
        """Reveal all (remove all fog)."""
        if self.preview.fog_mask:
            self.preview.fog_mask.clear_all()
            self.preview._update_preview()
            self.external_display._update_background()

    def fill_fog(self):
        """Fill all (full fog)."""
        if self.preview.fog_mask:
            self.preview.fog_mask.fog_all()
            self.preview._update_preview()
            self.external_display._update_background()

    def on_fog_changed(self):
        """Handle fog mask changes from the preview."""
        self.external_display._update_background()

    def change_zoom(self, value):
        """Update zoom level for preview and external display."""
        zoom = value / 100.0
        self.zoom_label.setText(f"Zoom: {value}%")

        # Reload at higher resolution if zooming beyond what's loaded
        if zoom > self.current_loaded_zoom and self.current_bg_path:
            self._reload_background_for_zoom(zoom)

        self.preview.set_zoom(zoom)
        # Sync viewport to external display
        z, cx, cy = self.preview.get_viewport()
        self.external_display.set_viewport(z, cx, cy)
        # Save viewport state for current image
        if self.current_bg_filename:
            self.viewports[self.current_bg_filename] = (z, cx, cy)

    def _reload_background_for_zoom(self, zoom):
        """Reload current background at resolution appropriate for zoom level."""
        if not self.current_bg_path:
            return

        screen_geo = self.external_screen.geometry()
        max_w = int(screen_geo.width() * zoom)
        max_h = int(screen_geo.height() * zoom)

        # Check cache first
        cache_key = self._get_cache_key(self.current_bg_path, zoom)
        cached = self.image_cache.get(cache_key)

        if cached:
            self.current_loaded_zoom = zoom
            self.preview.set_background(cached)
            self.external_display.set_background(cached)
        else:
            # Load async
            self._load_image_async(self.current_bg_path, max_w, max_h, zoom)

    def on_viewport_changed(self):
        """Handle viewport changes from the preview (pan)."""
        z, cx, cy = self.preview.get_viewport()
        self.external_display.set_viewport(z, cx, cy)
        # Save viewport state for current image
        if self.current_bg_filename:
            self.viewports[self.current_bg_filename] = (z, cx, cy)

    def get_or_create_fog_mask(self, filename, pixmap):
        """Get existing fog mask for image or create a new one."""
        if filename not in self.fog_masks:
            self.fog_masks[filename] = FogMask(pixmap.width(), pixmap.height())
        return self.fog_masks[filename]

    def _get_cache_key(self, path, zoom):
        """Generate cache key for an image at a specific zoom level."""
        return f"{path}@{zoom:.1f}"

    def _load_image_async(self, path, max_w, max_h, zoom):
        """Load image in background thread."""
        # Cancel any pending load
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.quit()
            self.loader_thread.wait()

        self.pending_load = path
        self.loader_thread = QThread()
        self.loader = ImageLoader(path, max_w, max_h, zoom)
        self.loader.moveToThread(self.loader_thread)
        self.loader_thread.started.connect(self.loader.run)
        self.loader.finished.connect(self._on_image_loaded)
        self.loader.finished.connect(self.loader_thread.quit)
        self.loader_thread.start()

    def _on_image_loaded(self, path, pixmap, zoom):
        """Handle async image load completion."""
        # Ignore if this isn't the image we're waiting for
        if path != self.pending_load:
            return

        self.pending_load = None

        # Cache the loaded image
        cache_key = self._get_cache_key(path, zoom)
        self.image_cache.put(cache_key, pixmap)

        # Only update display if this is still the current image
        if path == self.current_bg_path:
            self.current_loaded_zoom = zoom
            self._apply_background(pixmap)
            # Preload adjacent images after main image is displayed
            self._schedule_preload()

    def _apply_background(self, pixmap):
        """Apply a loaded background pixmap to preview and external display."""
        if not self.current_bg_filename:
            return

        # Restore viewport state
        if self.current_bg_filename in self.viewports:
            z, cx, cy = self.viewports[self.current_bg_filename]
        else:
            z, cx, cy = 1.0, 0.5, 0.5

        # Get or create fog mask
        fog_mask = self.get_or_create_fog_mask(self.current_bg_filename, pixmap)

        # Update preview
        self.preview.set_background(pixmap)
        self.preview.set_fog_mask(fog_mask)
        self.preview.set_fog_enabled(self.fog_enabled)
        self.preview.set_viewport(z, cx, cy)

        # Update zoom slider
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(z * 100))
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText(f"Zoom: {int(z * 100)}%")

        # Update external display
        self.external_display.set_fog_mask(fog_mask)
        self.external_display.set_fog_enabled(self.fog_enabled)
        self.external_display.set_viewport(z, cx, cy)
        self.external_display.set_background(pixmap)

    def update_display(self):
        """Update both background and character overlays on external display."""
        # Save current viewport state before switching
        if self.current_bg_filename:
            self.viewports[self.current_bg_filename] = self.preview.get_viewport()

        # Update background
        if self.backgrounds_folder and self.background_images and self.index < len(self.background_images):
            filename = self.background_images[self.index]
            self.current_bg_filename = filename
            self.current_bg_path = os.path.join(self.backgrounds_folder, filename)

            # Restore viewport state for this image (or use defaults)
            if filename in self.viewports:
                z, cx, cy = self.viewports[filename]
            else:
                z, cx, cy = 1.0, 0.5, 0.5

            # Calculate required resolution
            screen_geo = self.external_screen.geometry()
            max_w = int(screen_geo.width() * z)
            max_h = int(screen_geo.height() * z)

            # Check cache first
            cache_key = self._get_cache_key(self.current_bg_path, z)
            cached = self.image_cache.get(cache_key)

            if cached:
                # Use cached image immediately
                self.current_loaded_zoom = z
                self._apply_background(cached)
                # Preload adjacent images
                self._schedule_preload()
            else:
                # Load async (preload will happen after load completes)
                self._load_image_async(self.current_bg_path, max_w, max_h, z)

            # Update list selection
            self.bg_list.setCurrentRow(self.index)
        else:
            self.current_bg_filename = None
            self.current_bg_path = None
            self.current_loaded_zoom = 1.0
            self.external_display.set_fog_mask(None)
            self.external_display.set_background(None)
            self.preview.set_fog_mask(None)
            self.preview.set_background(None)

        # Update character overlays
        selected_characters = []
        if self.characters_folder:
            for item in self.character_list.selectedItems():
                row = self.character_list.row(item)
                if row < len(self.character_images):
                    img_path = os.path.join(self.characters_folder, self.character_images[row])
                    # Load at portrait size (no need for larger)
                    pixmap = load_scaled_image(img_path, self.portrait_height, self.portrait_height)
                    selected_characters.append(pixmap)

        self.external_display.set_characters(selected_characters, self.portrait_height)
        self.preview.set_characters(selected_characters, self.portrait_height)

    def eventFilter(self, obj, event):
        """Global event filter to capture key events regardless of focus."""
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_P and not event.isAutoRepeat():
                self.preview.pointer_active = True
                self.external_display.show_pointer(0.5, 0.5)
                return True
            elif event.key() == Qt.Key_Escape:
                QApplication.quit()
                return True
            elif event.key() == Qt.Key_F:
                self.toggle_fullscreen()
                return True
            elif event.key() in (Qt.Key_Left, Qt.Key_Right) and self.background_images:
                if event.key() == Qt.Key_Right:
                    self.index = (self.index + 1) % len(self.background_images)
                else:
                    self.index = (self.index - 1) % len(self.background_images)
                self.update_display()
                return True
        elif event.type() == QEvent.KeyRelease:
            if event.key() == Qt.Key_P and not event.isAutoRepeat():
                self.preview.pointer_active = False
                self.external_display.hide_pointer()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        # Clean up loader thread
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.quit()
            self.loader_thread.wait()
        QApplication.quit()

    def _schedule_preload(self):
        """Schedule preloading of adjacent images after a short delay."""
        QTimer.singleShot(100, self._preload_adjacent)

    def _preload_adjacent(self):
        """Preload next and previous images in background."""
        if not self.backgrounds_folder or not self.background_images:
            return
        if len(self.background_images) < 2:
            return

        screen_geo = self.external_screen.geometry()
        max_w = screen_geo.width()
        max_h = screen_geo.height()

        # Preload next image at 100% zoom
        next_index = (self.index + 1) % len(self.background_images)
        next_filename = self.background_images[next_index]
        next_path = os.path.join(self.backgrounds_folder, next_filename)
        cache_key = self._get_cache_key(next_path, 1.0)

        if not self.image_cache.get(cache_key):
            pixmap = load_scaled_image(next_path, max_w, max_h)
            self.image_cache.put(cache_key, pixmap)


def main():
    app = QApplication(sys.argv)
    folder = sys.argv[1] if len(sys.argv) > 1 else None
    window = ImageRegie(folder)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
