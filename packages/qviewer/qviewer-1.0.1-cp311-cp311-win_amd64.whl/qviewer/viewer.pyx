# cython: language_level=3
"""
QViewer Image Viewer - Cython optimized version with navigation and animated GIF support
"""
import sys
import os
from pathlib import Path
# from ctraceback import CTraceback
# sys.excepthook = CTraceback
import requests
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QPixmap, QKeyEvent, QMovie
from PyQt5.QtCore import Qt, QRect, QBuffer, QByteArray, QIODevice
from PyQt5.Qt import QScreen
from io import BytesIO

# Supported image extensions
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.webp', '.ico', '.svg', '.heic', '.heif', '.avif',
    '.jfif', '.pjpeg', '.pjp', '.apng'
}

# Animated format extensions
ANIMATED_EXTENSIONS = {'.gif', '.apng', '.webp'}

class ImageViewer(QMainWindow):
    """Fast image viewer window with Cython optimization, navigation, and animated GIF support."""
    
    def __init__(self, image_paths, start_index=0):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.image_label)
        
        self.image_list = image_paths
        self.current_index = start_index
        self.current_movie = None
        
        self.load_current_image()
        self.center_window()
        self.update_title()
    
    def update_title(self):
        """Update window title with current image info."""
        if self.image_list:
            filename = os.path.basename(self.image_list[self.current_index])
            title = f"{filename} ({self.current_index + 1}/{len(self.image_list)})"
            self.setWindowTitle(title)
    
    def load_current_image(self):
        """Load current image from the list."""
        if 0 <= self.current_index < len(self.image_list):
            self.load_image(self.image_list[self.current_index])
    
    def next_image(self):
        """Go to next image (cycle to first if at end)."""
        if len(self.image_list) > 0:
            self.current_index = (self.current_index + 1) % len(self.image_list)
            self.load_current_image()
            self.update_title()
    
    def prev_image(self):
        """Go to previous image (cycle to last if at start)."""
        if len(self.image_list) > 0:
            self.current_index = (self.current_index - 1) % len(self.image_list)
            self.load_current_image()
            self.update_title()
    
    def is_animated_format(self, image_path):
        """Check if the image format supports animation."""
        return Path(image_path).suffix.lower() in ANIMATED_EXTENSIONS
    
    def load_image(self, image_path):
        """Load and scale image to fit screen, with animation support."""
        # Stop any current animation
        if self.current_movie:
            self.current_movie.stop()
            self.current_movie = None
        
        # Check if it's an animated format
        if self.is_animated_format(image_path):
            self.load_animated_image(image_path)
        else:
            self.load_static_image(image_path)
    
    def load_animated_image(self, image_path):
        """Load animated image (GIF, APNG, WebP)."""
        screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen())
        
        # Handle URL or local file
        if image_path.startswith("http://") or image_path.startswith("https://"):
            response = requests.get(image_path)
            if response.status_code == 200:
                # Create QByteArray from response content
                byte_array = QByteArray(response.content)
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.ReadOnly)
                
                movie = QMovie()
                movie.setDevice(buffer)
                
                if movie.isValid():
                    self.current_movie = movie
                    self.image_label.setMovie(movie)
                    movie.start()
                    
                    # Scale if needed
                    first_frame = movie.currentPixmap()
                    if first_frame.width() > screen_geometry.width() or first_frame.height() > screen_geometry.height():
                        scaled_width = int(screen_geometry.width() * 0.8)
                        scaled_height = int(screen_geometry.height() * 0.8)
                        movie.setScaledSize(first_frame.size().scaled(scaled_width, scaled_height, Qt.KeepAspectRatio))
                    
                    self.resize(movie.currentPixmap().size())
                else:
                    print(f"Error: Invalid animated image from URL")
                    sys.exit(1)
            else:
                print(f"Error loading image from URL: {response.status_code}")
                sys.exit(1)
        else:
            # Local file
            movie = QMovie(image_path)
            if movie.isValid():
                self.current_movie = movie
                self.image_label.setMovie(movie)
                movie.start()
                
                # Scale if needed
                first_frame = movie.currentPixmap()
                if first_frame.width() > screen_geometry.width() or first_frame.height() > screen_geometry.height():
                    scaled_width = int(screen_geometry.width() * 0.8)
                    scaled_height = int(screen_geometry.height() * 0.8)
                    movie.setScaledSize(first_frame.size().scaled(scaled_width, scaled_height, Qt.KeepAspectRatio))
                
                self.resize(movie.currentPixmap().size())
            else:
                print(f"Error: Invalid animated image file: {image_path}")
                # Fallback to static image
                self.load_static_image(image_path)
        
        self.center_window()
    
    def load_static_image(self, image_path):
        """Load static image."""
        pixmap = self.get_pixmap(image_path)
        screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen())
        
        if pixmap.width() > screen_geometry.width() or pixmap.height() > screen_geometry.height():
            scaled_width = int(screen_geometry.width() * 0.8)
            scaled_height = int(screen_geometry.height() * 0.8)
            pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.image_label.setPixmap(pixmap)
        self.resize(pixmap.size())
        self.center_window()
    
    def get_pixmap(self, image_path):
        """Get pixmap from file path or URL."""
        if image_path.startswith("http://") or image_path.startswith("https://"):
            response = requests.get(image_path)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data.read())
                return pixmap
            else:
                print(f"Error loading image from URL: {response.status_code}")
                sys.exit(1)
        else:
            return QPixmap(image_path)
    
    def center_window(self):
        """Center window on screen."""
        screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen())
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry.center())
        self.move(frame_geometry.topLeft())
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        key = event.key()
        
        if key == Qt.Key_Q or key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_Right or key == Qt.Key_Down or key == Qt.Key_Space:
            self.next_image()
        elif key == Qt.Key_Left or key == Qt.Key_Up:
            self.prev_image()
    
    def closeEvent(self, event):
        """Clean up when closing."""
        if self.current_movie:
            self.current_movie.stop()
        event.accept()

def is_image_file(filepath):
    """Check if file has a valid image extension."""
    return Path(filepath).suffix.lower() in IMAGE_EXTENSIONS

cpdef list collect_images_from_path(str path, int max_depth=-1, int current_depth=0):
    """
    Collect image files from a path (file or directory).
    
    Args:
        path: File or directory path
        max_depth: Maximum recursion depth (-1 for infinite)
        current_depth: Current recursion level
    
    Returns:
        List of image file paths
    """
    cdef list images = []
    cdef object path_obj = Path(path)
    
    if path_obj.is_file():
        if is_image_file(str(path_obj)):
            images.append(str(path_obj.absolute()))
    elif path_obj.is_dir():
        if max_depth == -1 or current_depth < max_depth:
            try:
                for item in sorted(path_obj.iterdir()):
                    if item.is_file() and is_image_file(str(item)):
                        images.append(str(item.absolute()))
                    elif item.is_dir():
                        images.extend(collect_images_from_path(
                            str(item), max_depth, current_depth + 1
                        ))
            except PermissionError:
                print(f"Warning: Permission denied for {path}")
        else:
            # At max depth, only process files in current directory
            try:
                for item in sorted(path_obj.iterdir()):
                    if item.is_file() and is_image_file(str(item)):
                        images.append(str(item.absolute()))
            except PermissionError:
                print(f"Warning: Permission denied for {path}")
    
    return images

cpdef list collect_all_images(list paths, int max_depth=-1):
    """
    Collect all images from multiple paths.
    
    Args:
        paths: List of file/directory paths
        max_depth: Maximum directory recursion depth (-1 for infinite)
    
    Returns:
        List of unique image paths
    """
    cdef list all_images = []
    cdef set seen = set()
    
    for path in paths:
        images = collect_images_from_path(path, max_depth)
        for img in images:
            if img not in seen:
                seen.add(img)
                all_images.append(img)
    
    return all_images

def show(image_paths, start_index=0):
    """Show image viewer window."""
    if not image_paths:
        print("No images found!")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    viewer = ImageViewer(image_paths, start_index)
    viewer.show()
    viewer.activateWindow()
    app.exec_()