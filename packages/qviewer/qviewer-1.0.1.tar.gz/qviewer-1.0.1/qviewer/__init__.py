#!/usr/bin/env python3

# File: qviewer/__init__.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-01-25
# Description: QViewer - Fast PyQt5-based image viewer with navigation
# License: MIT

"""QViewer - Fast PyQt5-based image viewer with navigation"""
__version__ = '0.2.0'
__author__ = 'Your Name'

from qviewer.viewer import show, ImageViewer, collect_all_images

__all__ = ['show', 'ImageViewer', 'collect_all_images']
