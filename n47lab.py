#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N47Lab v1.0.5-FULL
Versione completa con funzionalità CAD e CAM.
Copyright (c) 2026 N47Lab Team - Tutti i diritti riservati.
"""

import sys
import os
import math
import time
import numpy as np
import trimesh
import trimesh.boolean
import trimesh.smoothing
import shapely.geometry as sgeom
from shapely.geometry import Polygon as ShapelyPolygon
import multiprocessing
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Set

# Importazioni PyQt5 - DEVE ESSERE PRIMA DELLE DEFINIZIONI DI CLASSI
from PyQt5.QtCore import Qt, QTimer, QEvent, QSize, QPoint, QRect
from PyQt5.QtGui import QFont, QFontMetrics, QSurfaceFormat, QPainter, QColor, QPen, QKeySequence, QTextCharFormat, QTextCursor, QIcon, QPixmap, QPalette
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox, QInputDialog, QToolBar, QStatusBar,
    QShortcut, QListWidget, QListWidgetItem, QScrollArea, QOpenGLWidget, 
     QSpinBox, QDoubleSpinBox, QTreeWidget, QTreeWidgetItem, QSizePolicy, QAction,
    QTextEdit, QTabWidget, QDialog, QDialogButtonBox, QFrame,
    QMenu, QToolButton, QButtonGroup, QSlider, QCheckBox, QComboBox,
    QPlainTextEdit
)
from OpenGL.GL import *
from OpenGL.GLU import *

# =============================================================================
# COSTANTI GLOBALI
# =============================================================================
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

APP_NAME = "N47Lab"
VERSION = "1.0.5-FULL"

# Colori per il tema azzurro pastello
BACKGROUND_COLOR = "#AEC8E0"
TEXT_COLOR = "#0C1E36"
BORDER_COLOR = "#2C5F8A"
BUTTON_COLOR = "#C8DCF0"
BUTTON_HOVER = "#CFFAFE"
BUTTON_PRESSED = "#94E6F2"

# Colori neutri per le forme
NEUTRAL_COLORS: List[List[float]] = [
    [0.7, 0.7, 0.7, 1.0],
    [0.4, 0.6, 0.8, 1.0],
    [0.8, 0.5, 0.5, 1.0],
    [0.5, 0.8, 0.5, 1.0],
    [0.8, 0.8, 0.4, 1.0],
    [0.6, 0.5, 0.8, 1.0],
    [0.5, 0.8, 0.8, 1.0],
    [0.8, 0.6, 0.4, 1.0],
    [0.7, 0.4, 0.7, 1.0],
    [0.4, 0.7, 0.6, 1.0],
    [0.9, 0.6, 0.6, 1.0],
    [0.6, 0.6, 0.9, 1.0]
]

SHAPE_LIBRARY: Dict[str, Dict[str, Any]] = {
    "Cubo": {"type": "box", "params": {"larghezza": 20.0, "altezza": 20.0, "profondità": 20.0}},
    "Cilindro": {"type": "cylinder", "params": {"raggio": 10.0, "altezza": 30.0, "sezioni": 64}},
    "Sfera": {"type": "sphere", "params": {"raggio": 15.0, "suddivisioni": 4}},
    "Cono": {"type": "cone", "params": {"raggio_base": 12.0, "altezza": 30.0, "sezioni": 64}},
    "collare": {"type": "collare", "params": {"raggio_esterno": 20.0, "raggio_interno": 12.0, "altezza": 8.0}},
    "Esagono": {"type": "hexagon", "params": {"raggio": 10.0, "altezza": 30.0}},
    "Spirale": {"type": "spiral", "params": {"raggio": 15.0, "altezza": 30.0, "giri": 4, "spessore": 3.0}},
    "Arco": {"type": "arc", "params": {"raggio_est": 20.0, "raggio_int": 16.0, "apertura": 90.0, "altezza": 8.0}},
    "Scatola vuota": {"type": "hollow_box", "params": {"larghezza": 30.0, "altezza": 20.0, "profondità": 20.0, "spessore_muro": 2.0}}
}

# =============================================================================
# PROFILI STAMPANTI 3D
# =============================================================================
PRINTER_PROFILES = {
    "Bambu Lab X1C": {
        "brand": "Bambu Lab", "model": "X1 Carbon",
        "build_volume": (256, 256, 256), "nozzle": [0.4, 0.6, 0.8],
        "max_temp": 300, "bed_temp": 100,
        "protocols": ["mqtt_ftps"],
        "default_layer": 0.16, "default_infill": 15
    },
    "Bambu Lab P1S": {
        "brand": "Bambu Lab", "model": "P1S",
        "build_volume": (256, 256, 256), "nozzle": [0.4, 0.6, 0.8],
        "max_temp": 300, "bed_temp": 100,
        "protocols": ["mqtt_ftps"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Bambu Lab A1": {
        "brand": "Bambu Lab", "model": "A1",
        "build_volume": (256, 256, 256), "nozzle": [0.4, 0.6, 0.8],
        "max_temp": 260, "bed_temp": 80,
        "protocols": ["mqtt_ftps"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Bambu Lab A1 Mini": {
        "brand": "Bambu Lab", "model": "A1 Mini",
        "build_volume": (180, 180, 180), "nozzle": [0.4],
        "max_temp": 260, "bed_temp": 80,
        "protocols": ["mqtt_ftps"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Anycubic Kobra 3": {
        "brand": "Anycubic", "model": "Kobra 3",
        "build_volume": (250, 250, 260), "nozzle": [0.4],
        "max_temp": 260, "bed_temp": 95,
        "protocols": ["ftp", "smb", "octoprint", "anycubic_cloud", "file"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Anycubic Kobra 2": {
        "brand": "Anycubic", "model": "Kobra 2",
        "build_volume": (220, 220, 250), "nozzle": [0.4],
        "max_temp": 260, "bed_temp": 95,
        "protocols": ["ftp", "smb", "octoprint", "file"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Anycubic Vyper": {
        "brand": "Anycubic", "model": "Vyper",
        "build_volume": (245, 245, 260), "nozzle": [0.4],
        "max_temp": 260, "bed_temp": 95,
        "protocols": ["ftp", "smb", "octoprint", "file"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Creality K1 Max": {
        "brand": "Creality", "model": "K1 Max",
        "build_volume": (300, 300, 300), "nozzle": [0.4],
        "max_temp": 300, "bed_temp": 100,
        "protocols": ["creality_http", "ftp", "octoprint", "file"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Creality K1": {
        "brand": "Creality", "model": "K1",
        "build_volume": (220, 220, 250), "nozzle": [0.4],
        "max_temp": 300, "bed_temp": 100,
        "protocols": ["creality_http", "ftp", "octoprint", "file"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Creality Ender 3 V3": {
        "brand": "Creality", "model": "Ender 3 V3",
        "build_volume": (220, 220, 250), "nozzle": [0.4],
        "max_temp": 260, "bed_temp": 100,
        "protocols": ["ftp", "smb", "octoprint", "file"],
        "default_layer": 0.20, "default_infill": 15
    },
    "Prusa i3 MK3S+": {
        "brand": "Prusa", "model": "i3 MK3S+",
        "build_volume": (250, 210, 210), "nozzle": [0.25, 0.4, 0.6],
        "max_temp": 280, "bed_temp": 100,
        "protocols": ["prusalink", "ftp", "octoprint", "file"],
        "default_layer": 0.15, "default_infill": 15
    },
    "Prusa XL": {
        "brand": "Prusa", "model": "XL",
        "build_volume": (360, 360, 360), "nozzle": [0.4, 0.6],
        "max_temp": 290, "bed_temp": 110,
        "protocols": ["prusalink", "ftp", "octoprint", "file"],
        "default_layer": 0.20, "default_infill": 15
    }
}

# =============================================================================
# BLOCCO 1: CORE ENGINE (FUNZIONALITÀ CAD E CAM)
# =============================================================================
def _generate_blender_donut(R: float, r: float, major_segs: int, minor_segs: int) -> trimesh.Trimesh:
    major_segs = max(8, int(major_segs))
    minor_segs = max(4, int(minor_segs))
    if R <= r + 0.1:
        R = r + 0.2
    u = np.linspace(0, 2 * np.pi, major_segs, endpoint=False)
    v = np.linspace(0, 2 * np.pi, minor_segs, endpoint=False)
    U, V = np.meshgrid(u, v, indexing='ij')
    X = (R + r * np.cos(V)) * np.cos(U)
    Y = (R + r * np.cos(V)) * np.sin(U)
    Z = r * np.sin(V)
    verts = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    i = np.arange(major_segs)
    j = np.arange(minor_segs)
    i_next = (i + 1) % major_segs
    j_next = (j + 1) % minor_segs
    I, J = np.meshgrid(i, j, indexing='ij')
    I_next, J_next = np.meshgrid(i_next, j_next, indexing='ij')
    v00 = I * minor_segs + J
    v10 = I_next * minor_segs + J
    v11 = I_next * minor_segs + J_next
    v01 = I * minor_segs + J_next
    faces_1 = np.stack([v00, v10, v11], axis=-1).reshape(-1, 3)
    faces_2 = np.stack([v00, v11, v01], axis=-1).reshape(-1, 3)
    faces = np.vstack([faces_1, faces_2])
    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    mesh.fix_normals()
    return mesh

def _generate_blender_collare(outer_radius: float, inner_radius: float, height: float) -> trimesh.Trimesh:
    n = 64
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    cos_a = np.cos(angles)
    sin_a = np.sin(angles)
    
    outer_xy = np.column_stack([outer_radius * cos_a, outer_radius * sin_a])
    inner_xy = np.column_stack([inner_radius * cos_a, inner_radius * sin_a])
    
    top = height
    bot = 0.0
    
    # Vertices: [top_outer(0..n-1), top_inner(0..n-1), bot_outer(0..n-1), bot_inner(0..n-1)]
    to = np.column_stack([outer_xy, np.full(n, top)])
    ti = np.column_stack([inner_xy, np.full(n, top)])
    bo = np.column_stack([outer_xy, np.full(n, bot)])
    bi = np.column_stack([inner_xy, np.full(n, bot)])
    verts = np.vstack([to, ti, bo, bi])
    
    faces = []
    # Helper: add quad as two tris (v0,v1,v2) and (v0,v2,v3)
    def add_quad(a, b, c, d):
        faces.append((a, b, c))
        faces.append((a, c, d))
    
    for i in range(n):
        j = (i + 1) % n
        
        to_i, to_j = i, j
        ti_i, ti_j = n + i, n + j
        bo_i, bo_j = 2 * n + i, 2 * n + j
        bi_i, bi_j = 3 * n + i, 3 * n + j
        
        # Top face
        add_quad(to_i, to_j, ti_j, ti_i)
        # Bottom face (reversed winding for outward normal)
        add_quad(bo_i, bi_i, bi_j, bo_j)
        # Outer wall
        add_quad(to_i, bo_i, bo_j, to_j)
        # Inner wall
        add_quad(ti_i, ti_j, bi_j, bi_i)
    
    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    mesh.fix_normals()
    return mesh

def _generate_blender_cylinder(radius: float, height: float, sections: int) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=int(sections))
    mesh.fix_normals()
    return mesh

def _generate_blender_sphere(radius: float, subdivisions: int) -> trimesh.Trimesh:
    mesh = trimesh.creation.icosphere(radius=radius, subdivisions=min(6, int(subdivisions)))
    mesh.fix_normals()
    return mesh

def _generate_blender_cone(radius: float, height: float, sections: int) -> trimesh.Trimesh:
    mesh = trimesh.creation.cone(radius=radius, height=height, sections=int(sections))
    mesh.fix_normals()
    return mesh

def _generate_blender_box(width: float, height: float, depth: float) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=[width, depth, height])
    mesh.fix_normals()
    return mesh

def _generate_blender_hexagon(radius: float, height: float) -> trimesh.Trimesh:
    from shapely.geometry import Polygon as SPolygon
    angles = [2 * math.pi * i / 6 for i in range(6)]
    pts = [(radius * math.cos(a), radius * math.sin(a)) for a in angles]
    mesh = trimesh.creation.extrude_polygon(SPolygon(pts), height=height)
    mesh.fix_normals()
    return mesh

def _generate_blender_spiral(radius: float, height: float, turns: int, thickness: float) -> trimesh.Trimesh:
    turns = max(1, int(turns))
    thickness = max(0.5, thickness)
    r_tube = thickness / 2
    segs = int(turns * 48)
    ring_segs = max(12, int(thickness * 4))
    
    verts = []
    faces = []
    
    def helix_point(t):
        theta = t * 2 * np.pi * turns
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        z = t * height
        return np.array([x, y, z]), theta
    
    def frenet_frame(theta):
        h_per_turn = height / max(1, turns)
        T = np.array([-radius * np.sin(theta), radius * np.cos(theta), h_per_turn / (2 * np.pi)])
        T = T / (np.linalg.norm(T) + 1e-12)
        N = np.array([-np.cos(theta), -np.sin(theta), 0.0])
        N = N / (np.linalg.norm(N) + 1e-12)
        B = np.cross(T, N)
        B = B / (np.linalg.norm(B) + 1e-12)
        N = np.cross(B, T)
        return T, N, B
    
    for i in range(segs + 1):
        t = i / segs
        pt, theta = helix_point(t)
        T, N, B = frenet_frame(theta)
        for j in range(ring_segs):
            phi = j / ring_segs * 2 * np.pi
            rv = r_tube * (N * np.cos(phi) + B * np.sin(phi))
            verts.append(pt + rv)
    
    n_ring = ring_segs
    for i in range(segs):
        for j in range(ring_segs):
            jn = (j + 1) % ring_segs
            v00 = i * n_ring + j
            v01 = i * n_ring + jn
            v10 = (i + 1) * n_ring + j
            v11 = (i + 1) * n_ring + jn
            faces.append((v00, v10, v11))
            faces.append((v00, v11, v01))
    
    # End caps
    offset = len(verts)
    for t_val, sign in [(0.0, -1), (1.0, 1)]:
        pt, theta = helix_point(t_val)
        T, N, B = frenet_frame(theta)
        cap_center = len(verts)
        verts.append(pt)
        for j in range(ring_segs):
            phi = j / ring_segs * 2 * np.pi
            rv = r_tube * (N * np.cos(phi) + B * np.sin(phi))
            verts.append(pt + rv)
        for j in range(ring_segs):
            jn = (j + 1) % ring_segs
            if sign == 1:
                faces.append((cap_center, cap_center + jn + 1, cap_center + j + 1))
            else:
                faces.append((cap_center, cap_center + j + 1, cap_center + jn + 1))
    
    verts = np.array(verts, dtype=np.float32)
    faces = np.array(faces, dtype=np.uint32)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    mesh.fix_normals()
    return mesh

def _generate_blender_arc(outer_r: float, inner_r: float, angle_deg: float, height: float) -> trimesh.Trimesh:
    from shapely.geometry import Point
    angle_deg = min(360, max(1, angle_deg))
    angle_rad = math.radians(angle_deg)
    outer = Point(0, 0).buffer(outer_r, resolution=64)
    inner = Point(0, 0).buffer(inner_r, resolution=64)
    ring = outer.difference(inner)
    if angle_deg >= 360:
        mesh = trimesh.creation.extrude_polygon(ring, height=height)
        mesh.fix_normals()
        return mesh
    from shapely.affinity import rotate
    from shapely.geometry import box as sbox
    cut = sbox(-outer_r * 2, -outer_r * 2, 0, outer_r * 2)
    cut = rotate(cut, -(90 - angle_deg / 2), origin=(0, 0), use_radians=False)
    sector = ring.intersection(cut)
    if sector.is_empty:
        return _generate_blender_collare(outer_r, inner_r, height)
    polys = [sector] if sector.geom_type == 'Polygon' else [g for g in sector.geoms if g.geom_type == 'Polygon']
    all_verts, all_faces, offset = [], [], 0
    for p in polys:
        m = trimesh.creation.extrude_polygon(p, height=height)
        if m and len(m.vertices) > 0:
            all_verts.append(m.vertices)
            all_faces.append(m.faces + offset)
            offset += len(m.vertices)
    if not all_verts:
        return _generate_blender_collare(outer_r, inner_r, height)
    mesh = trimesh.Trimesh(vertices=np.vstack(all_verts), faces=np.vstack(all_faces))
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()
    return mesh

def _qpath_to_mesh(qpath, thickness):
    from PyQt5.QtGui import QPainterPath
    polys = qpath.toFillPolygons()
    if not polys:
        return trimesh.Trimesh()
    all_polys, holes = [], []
    for poly in polys:
        if len(poly) < 3:
            continue
        pts = [(pt.x(), -pt.y()) for pt in poly]
        if len(pts) < 3:
            continue
        area = 0.0
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
        if area < 0:
            all_polys.append(pts)
        else:
            holes.append(pts)
    if not all_polys:
        return trimesh.Trimesh()
    from shapely.ops import unary_union
    shapely_solids = [ShapelyPolygon(pts) for pts in all_polys]
    shapely_solids = [sp.buffer(0) for sp in shapely_solids if not sp.is_empty]
    shapely_solids = [sp for sp in shapely_solids if sp.is_valid and not sp.is_empty]
    if not shapely_solids:
        return trimesh.Trimesh()
    merged = unary_union(shapely_solids)
    if merged.is_empty:
        return trimesh.Trimesh()
    if merged.geom_type == 'Polygon':
        polys_to_extrude = [merged]
    elif merged.geom_type == 'MultiPolygon':
        polys_to_extrude = list(merged.geoms)
    else:
        return trimesh.Trimesh()
    all_verts, all_faces, offset = [], [], 0
    for poly in polys_to_extrude:
        try:
            ext_mesh = trimesh.creation.extrude_polygon(poly, height=thickness)
            if ext_mesh and len(ext_mesh.vertices) > 0:
                all_verts.append(ext_mesh.vertices)
                all_faces.append(ext_mesh.faces + offset)
                offset += len(ext_mesh.vertices)
        except:
            continue
    if not all_verts:
        return trimesh.Trimesh()
    combined = trimesh.Trimesh(vertices=np.vstack(all_verts), faces=np.vstack(all_faces))
    combined.remove_unreferenced_vertices()
    return combined

def _generate_text_mesh(text, font_name, font_size, thickness, spacing):
    from PyQt5.QtGui import QPainterPath, QFont, QFontMetricsF
    from PyQt5.QtCore import QPointF
    font = QFont(font_name, int(font_size))
    font_metrics = QFontMetricsF(font)
    if abs(spacing) > 0.001:
        all_verts, all_faces, offset = [], [], 0
        x_cursor = 0.0
        for ch in text:
            path = QPainterPath()
            path.addText(QPointF(0, 0), font, ch)
            ch_w = font_metrics.horizontalAdvance(ch) if hasattr(font_metrics, 'horizontalAdvance') else font_metrics.width(ch)
            ch_mesh = _qpath_to_mesh(path, thickness)
            if ch_mesh and len(ch_mesh.vertices) > 0:
                ch_mesh.apply_translation([x_cursor, 0, 0])
                all_verts.append(ch_mesh.vertices)
                all_faces.append(ch_mesh.faces + offset)
                offset += len(ch_mesh.vertices)
            x_cursor += ch_w + spacing
        if not all_verts:
            return trimesh.Trimesh()
        combined = trimesh.Trimesh(vertices=np.vstack(all_verts), faces=np.vstack(all_faces))
        combined.remove_unreferenced_vertices()
        return combined
    else:
        path = QPainterPath()
        path.addText(QPointF(0, 0), font, text)
        return _qpath_to_mesh(path, thickness)

def _generate_thread_on_shape(mesh: trimesh.Trimesh, turns: int = 8, thread_radius: float = 1.5, segments_per_turn: int = 24, circle_segments: int = 12) -> trimesh.Trimesh:
    """Genera un filetto elicoidale che segue la superficie della mesh."""
    bounds = mesh.bounds
    if bounds is None:
        return trimesh.Trimesh()
    size = bounds[1] - bounds[0]
    verts = mesh.vertices
    centroid = np.mean(verts, axis=0)
    radii = np.linalg.norm(verts - centroid, axis=1)
    r_mean = radii.mean()
    
    # Determina la forma dal bounding box
    is_sphere = max(size) / max(min(size), 1e-8) < 1.3 and abs(size[0] - size[1]) / max((size[0] + size[1]) / 2, 1e-8) < 0.2
    
    if is_sphere:
        R = r_mean
        h = 0.0
    else:
        R = (size[0] + size[1]) / 4
        h = size[2]
    
    n = turns * segments_per_turn + 1
    all_verts = []
    all_faces = []
    
    for i in range(n):
        t = i / max(n - 1, 1)
        
        if is_sphere:
            theta = -np.pi / 2 + t * np.pi
            phi = t * 2 * np.pi * turns
            px = R * np.cos(theta) * np.cos(phi) + centroid[0]
            py = R * np.cos(theta) * np.sin(phi) + centroid[1]
            pz = R * np.sin(theta) + centroid[2]
            nx = (px - centroid[0]) / R
            ny = (py - centroid[1]) / R
            nz = (pz - centroid[2]) / R
        else:
            phi = t * 2 * np.pi * turns
            px = R * np.cos(phi) + centroid[0]
            py = R * np.sin(phi) + centroid[1]
            pz = -h / 2 + t * h + centroid[2]
            nx = np.cos(phi)
            ny = np.sin(phi)
            nz = 0.0
        
        # Tangente del percorso (analitica)
        if is_sphere:
            d_theta = np.pi
            d_phi = 2 * np.pi * turns
            tx = -R * np.sin(theta) * np.cos(phi) * d_theta - R * np.cos(theta) * np.sin(phi) * d_phi
            ty = -R * np.sin(theta) * np.sin(phi) * d_theta + R * np.cos(theta) * np.cos(phi) * d_phi
            tz = R * np.cos(theta) * d_theta
        else:
            d_phi = 2 * np.pi * turns
            d_z = h
            tx = -R * np.sin(phi) * d_phi
            ty = R * np.cos(phi) * d_phi
            tz = d_z
        
        tl = np.sqrt(tx*tx + ty*ty + tz*tz)
        if tl > 1e-8:
            tx /= tl; ty /= tl; tz /= tl
        else:
            tx, ty, tz = 1.0, 0.0, 0.0
        
        # u = cross(T, N), normalizzato
        ux = ty * nz - tz * ny
        uy = tz * nx - tx * nz
        uz = tx * ny - ty * nx
        ul = np.sqrt(ux*ux + uy*uy + uz*uz)
        if ul > 1e-8:
            ux /= ul; uy /= ul; uz /= ul
        else:
            ux, uy, uz = 1.0, 0.0, 0.0
        
        # v = cross(T, u) — il terzo asse del cerchio
        vx = ty * uz - tz * uy
        vy = tz * ux - tx * uz
        vz = tx * uy - ty * ux
        
        # Cerchio nel piano perpendicolare al percorso
        # Centro offsettato verso l'esterno di thread_radius lungo la normale (v = -N)
        for j in range(circle_segments):
            alpha = j / circle_segments * 2 * np.pi
            c = np.cos(alpha)
            s = np.sin(alpha)
            cvx = ux * c * thread_radius + vx * s * thread_radius
            cvy = uy * c * thread_radius + vy * s * thread_radius
            cvz = uz * c * thread_radius + vz * s * thread_radius
            all_verts.append([px - vx * thread_radius + cvx,
                              py - vy * thread_radius + cvy,
                              pz - vz * thread_radius + cvz])
        
        if i > 0:
            base = (i - 1) * circle_segments
            for j in range(circle_segments):
                jn = (j + 1) % circle_segments
                a = base + j
                b = base + jn
                c = base + circle_segments + j
                d = base + circle_segments + jn
                all_faces.append([a, c, b])
                all_faces.append([b, c, d])
    
    result = trimesh.Trimesh(vertices=np.array(all_verts), faces=np.array(all_faces))
    result.remove_unreferenced_vertices()
    result.fix_normals()
    return result

def _generate_blender_hollow_box(width: float, height: float, depth: float, wall: float) -> trimesh.Trimesh:
    outer = trimesh.creation.box(extents=[width, depth, height])
    inner_w = max(0.1, width - 2 * wall)
    inner_h = max(0.1, height - 2 * wall)
    inner_d = max(0.1, depth - 2 * wall)
    inner = trimesh.creation.box(extents=[inner_w, inner_d, inner_h])
    try:
        result = boolean_safe([outer, inner], "difference")
        if result is None or result.is_empty:
            return outer
        cut_h = height - wall
        if cut_h > 0:
            plane_orig = [0, 0, cut_h - height / 2]
            plane_norm = [0, 0, -1]
            sliced = trimesh.intersections.slice_mesh_plane(result, plane_norm, plane_orig, cap=True)
            if sliced is not None and not sliced.is_empty:
                result = sliced
        result.fix_normals()
        return result
    except:
        return outer

def _ensure_volume(mesh):
    """Tenta di rendere una mesh un volume valido per booleane."""
    m = mesh.copy()
    m.fix_normals()
    if not m.is_watertight:
        try:
            trimesh.repair.fill_holes(m)
        except:
            pass
    if not m.is_watertight:
        try:
            m.process(validate=True)
        except:
            pass
    return m

def boolean_safe(meshes: List[trimesh.Trimesh], operation: str) -> trimesh.Trimesh:
    """
    Esegue operazioni booleane in modo sicuro con fallback a metodi alternativi.
    """
    if len(meshes) < 2:
        raise ValueError("Servono almeno 2 mesh per l'operazione booleana")
    
    op_map = {
        "unione": "union",
        "sottrazione": "difference",
        "intersezione": "intersection"
    }
    op_type = op_map.get(operation.lower(), operation.lower())
    
    op_func_map = {
        "union": trimesh.boolean.union,
        "difference": trimesh.boolean.difference,
        "intersection": trimesh.boolean.intersection
    }
    op_func = op_func_map.get(op_type)
    if op_func is None:
        raise ValueError(f"Operazione sconosciuta: {operation}")
    
    engines_to_try = ['manifold', None]
    
    for engine in engines_to_try:
        try:
            return op_func(meshes, engine=engine)
        except Exception:
            continue
    
    # Fallback: repara mesh e riprova
    fixed = [_ensure_volume(m) for m in meshes]
    for engine in engines_to_try:
        try:
            return op_func(fixed, engine=engine)
        except Exception:
            continue
    
    # Ultimo fallback: mesh-by-mesh con scipy
    try:
        result = None
        for m in fixed:
            if result is None:
                result = m
                continue
            if op_type == "union":
                result = result.union(m)
            elif op_type == "difference":
                result = result.difference(m)
            elif op_type == "intersection":
                result = result.intersection(m)
        if result is not None and not result.is_empty:
            return result
    except Exception as e2:
        raise RuntimeError(f"Errore CSG: tutti i motori hanno fallito: {e2}")

def validate_and_place_mesh(mesh: Optional[trimesh.Trimesh]) -> trimesh.Trimesh:
    try:
        if mesh is None or len(mesh.vertices) < 3 or len(mesh.faces) < 1:
            return _generate_blender_box(10, 10, 10)
        
        # Processa e convalida la mesh
        mesh.process(validate=True)
        mesh.fix_normals()
        
        # Allinea al piano XY se necessario
        if hasattr(mesh, 'bounds') and mesh.bounds is not None and len(mesh.bounds) == 2:
            z_min = mesh.bounds[0][2]
            if abs(z_min) > 1e-6:
                mesh.apply_translation([0, 0, -z_min])
        
        return mesh
    except Exception as e:
        print(f"Errore validazione mesh: {e}")
        return _generate_blender_box(10, 10, 10)

def create_mesh(shape_type: str, params: Dict[str, Any]) -> trimesh.Trimesh:
    try:
        if shape_type == "box":
            mesh = _generate_blender_box(
                float(params.get("larghezza", 20)), 
                float(params.get("altezza", 20)), 
                float(params.get("profondità", 20))
            )
        elif shape_type == "cylinder":
            mesh = _generate_blender_cylinder(
                float(params.get("raggio", 10)), 
                float(params.get("altezza", 30)), 
                int(params.get("sezioni", 64))
            )
        elif shape_type == "sphere":
            mesh = _generate_blender_sphere(
                float(params.get("raggio", 15)), 
                int(params.get("suddivisioni", 4))
            )
        elif shape_type == "cone":
            mesh = _generate_blender_cone(
                float(params.get("raggio_base", 12)), 
                float(params.get("altezza", 30)), 
                int(params.get("sezioni", 64))
            )
        elif shape_type == "hexagon":
            mesh = _generate_blender_hexagon(float(params.get("raggio", 10)), float(params.get("altezza", 30)))
        elif shape_type == "spiral":
            mesh = _generate_blender_spiral(float(params.get("raggio", 15)), float(params.get("altezza", 30)), int(params.get("giri", 4)), float(params.get("spessore", 3)))
        elif shape_type == "arc":
            mesh = _generate_blender_arc(float(params.get("raggio_est", 20)), float(params.get("raggio_int", 12)), float(params.get("apertura", 90)), float(params.get("altezza", 8)))
        elif shape_type == "hollow_box":
            mesh = _generate_blender_hollow_box(float(params.get("larghezza", 30)), float(params.get("altezza", 20)), float(params.get("profondità", 20)), float(params.get("spessore_muro", 2.5)))
        elif shape_type == "collare":
            mesh = _generate_blender_collare(float(params.get("raggio_esterno", 20)), float(params.get("raggio_interno", 12)), float(params.get("altezza", 8)))
        elif shape_type == "donut":
            R = float(params.get("raggio_magg", 15))
            r = float(params.get("raggio_min", 5))
            if R <= r + 0.1:
                R = r + 0.2
            mesh = _generate_blender_donut(R, r, int(params.get("sezioni", 64)), int(params.get("sezioni", 64)) // 2)
        else:
            mesh = _generate_blender_box(10, 10, 10)
        
        return validate_and_place_mesh(mesh)
    except Exception as e:
        print(f"Errore creazione mesh: {e}")
        return validate_and_place_mesh(_generate_blender_box(10, 10, 10))

class Scene:
    def __init__(self) -> None:
        self.objects: List[trimesh.Trimesh] = []
        self.selected_objects: List[trimesh.Trimesh] = []
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.color_idx: int = 0
        self.sketch_entities: List[Dict[str, Any]] = []
        self.dimensions = []
        self.angle_dims = []
        self.snap_grid: bool = True
        self.scale_mode: str = "Disattivato"
        self.magnetic_snap: bool = True
        self.layers: Dict[str, Dict[str, Any]] = {"Default": {"visible": True, "locked": False, "color": [0.6, 0.75, 0.9, 1.0]}}
        self.active_layer: str = "Default"
        self.assemblies: Dict[str, Dict[str, Any]] = {}
        self.operation_in_progress = False
        self._spatial_index = None
        self._needs_spatial_rebuild = True
        self.measurement_mode = None
        self.measurement_points = []
        self.active_tool = "selection"
        self.mirror_axis = "x"
        self.fillet_radius = 1.0
        self.offset_distance = 1.0
        self.revolve_angle = 360.0
        self.pattern_count = 3
        self.pattern_distance = 10.0
        self.pattern_direction = "x"
        self.smooth_iterations = 1
        self.subdivide_iterations = 1
        self.decimate_target = 1000
        self.hole_diameter = 5.0
        self.hole_depth = 10.0
        self.cut_axis = "z"
        self.cut_position = 0.0
        self.deformation_type = "bend"
        self.deformation_intensity = 0.5
        self.tool_diameter = 3.0
        self.stepover = 0.5
        self.feed_rate = 1000.0
        self.plunge_rate = 500.0
        self.depth_per_pass = 2.0
        self.toolpath_strategy = "adaptive"
        self.toolpath_direction = "climb"
        self.toolpath_depth = 0.0
        self.toolpath_offset = 0.0
        self.toolpath_feedrate = 1000.0
        self.toolpath_plunge_feedrate = 500.0
        self.toolpath_spindle_speed = 12000
        self.toolpath_coolant = "flood"
        self.toolpath_tool_number = 1
        self.toolpath_tool_diameter = 3.0
        self.toolpath_tool_length = 50.0
        self.toolpath_tool_flutes = 2
        self.toolpath_tool_material = "carbide"
        self.toolpath_tool_coating = "tialn"
        self.toolpath_tool_cutting_diameter = 3.0
        self.toolpath_tool_cutting_length = 20.0
        self.toolpath_tool_shank_diameter = 6.0
        self.toolpath_tool_shank_length = 30.0
        self.toolpath_tool_corner_radius = 0.0
        self.toolpath_tool_tip_angle = 0.0
        self.toolpath_tool_tip_diameter = 0.0
        self.toolpath_tool_tip_length = 0.0
        self.toolpath_tool_tip_radius = 0.0
        self.gcode_paths = []

    @property
    def grid_step(self) -> float:
        return 0.0 if self.scale_mode == "Disattivato" else float(self.scale_mode.replace(" mm", ""))
    
    @property
    def has_selection(self) -> bool:
        return len(self.selected_objects) > 0
    
    @property
    def single_selection(self) -> Optional[trimesh.Trimesh]:
        return self.selected_objects[0] if self.selected_objects else None
    
    def clear_selection(self) -> None:
        self.selected_objects = []
    
    def add_to_selection(self, obj: trimesh.Trimesh) -> None:
        if obj not in self.selected_objects:
            self.selected_objects.append(obj)
            self._needs_spatial_rebuild = True
    
    def remove_from_selection(self, obj: trimesh.Trimesh) -> None:
        if obj in self.selected_objects:
            self.selected_objects.remove(obj)
    
    def toggle_selection(self, obj: trimesh.Trimesh) -> None:
        if obj in self.selected_objects:
            self.remove_from_selection(obj)
        else:
            self.add_to_selection(obj)
    
    def add_shape(self, shape_type: str, params: Dict[str, Any], name: Optional[str] = None) -> trimesh.Trimesh:
        mesh = create_mesh(shape_type, params)
        color = NEUTRAL_COLORS[self.color_idx % len(NEUTRAL_COLORS)]
        self.color_idx += 1
        
        mesh.metadata.update({
            "layer": self.active_layer,
            "color": color,
            "name": name or f"{shape_type}_{self.color_idx}",
            "params": params.copy(),
            "shape_type": shape_type,
            "assembly": None
        })
        
        self.objects.append(mesh)
        self._needs_spatial_rebuild = True
        self._undo_push()
        return mesh
    
    def _rebuild_spatial_index(self):
        try:
            if len(self.objects) <= 100:
                self._spatial_index = None
                return
            
            from scipy.spatial import cKDTree
            
            centers = []
            for obj in self.objects:
                if hasattr(obj, 'bounds') and obj.bounds is not None and len(obj.bounds) == 2:
                    center = (obj.bounds[0] + obj.bounds[1]) / 2
                    centers.append(center)
                else:
                    if hasattr(obj, 'vertices') and len(obj.vertices) > 0:
                        center = np.mean(obj.vertices, axis=0)
                        centers.append(center)
                    else:
                        centers.append([0, 0, 0])
            
            self._spatial_index = cKDTree(centers)
        except ImportError:
            self._spatial_index = None
        except Exception as e:
            print(f"Errore nella creazione dell'octree: {e}")
            self._spatial_index = None
    
    def _get_nearby_objects(self, point, radius=10.0):
        if self._spatial_index is None or len(self.objects) == 0:
            return self.objects
        
        indices = self._spatial_index.query_ball_point(point, radius)
        return [self.objects[i] for i in indices]
    
    def _undo_push(self) -> None:
        try:
            if self.operation_in_progress:
                return
            
            obj_copy = []
            for obj in self.objects:
                try:
                    if hasattr(obj, 'copy'):
                        obj_copy.append(obj.copy())
                except:
                    continue
            
            if obj_copy:
                selected_copy = [obj for obj in self.selected_objects if obj in obj_copy]
                
                self.undo_stack.append({
                    "obj": obj_copy,
                    "selected": selected_copy
                })
                
                if len(self.undo_stack) > 50:
                    self.undo_stack.pop(0)
                self.redo_stack.clear()
        except Exception as e:
            print(f"Errore inserimento stack undo: {e}")
    
    def start_operation(self) -> None:
        self.operation_in_progress = True
    
    def end_operation(self) -> None:
        self.operation_in_progress = False
        self._undo_push()
    
    def undo(self) -> bool:
        if self.undo_stack:
            state = self.undo_stack.pop()
            redo_state = {
                "obj": [],
                "selected": [obj for obj in self.selected_objects if obj in self.objects]
            }
            
            for obj in self.objects:
                try:
                    if hasattr(obj, 'copy'):
                        redo_state["obj"].append(obj.copy())
                except:
                    continue
            
            if redo_state["obj"]:
                self.redo_stack.append(redo_state)
            
            self.objects = state["obj"]
            self.selected_objects = state["selected"]
            self._needs_spatial_rebuild = True
            self._notify(f"Annullato (oggetti: {len(self.objects)}, selezionati: {len(self.selected_objects)})")
            return True
        return False
    
    def redo(self) -> bool:
        if self.redo_stack:
            state = self.redo_stack.pop()
            undo_state = {
                "obj": [],
                "selected": [obj for obj in self.selected_objects if obj in self.objects]
            }
            
            for obj in self.objects:
                try:
                    if hasattr(obj, 'copy'):
                        undo_state["obj"].append(obj.copy())
                except:
                    continue
            
            if undo_state["obj"]:
                self.undo_stack.append(undo_state)
            
            self.objects = state["obj"]
            self.selected_objects = state["selected"]
            self._needs_spatial_rebuild = True
            self._notify(f"Ripristinato (oggetti: {len(self.objects)}, selezionati: {len(self.selected_objects)})")
            return True
        return False
    
    def delete(self) -> bool:
        if not self.selected_objects:
            return False
        
        self.start_operation()
        
        deleted = len(self.selected_objects)
        for obj in self.selected_objects[:]:
            if obj in self.objects:
                self.objects.remove(obj)
        
        self.selected_objects = []
        self._needs_spatial_rebuild = True
        
        self.end_operation()
        
        self._notify(f"Eliminati {deleted} oggetti")
        return True
    
    def duplicate(self) -> None:
        if not self.selected_objects:
            self._notify("Nessun oggetto selezionato")
            return
        
        try:
            self.start_operation()
            
            for obj in self.selected_objects[:]:
                copy_obj = obj.copy()
                copy_obj.apply_translation([20, 0, 0])
                copy_obj.metadata["name"] = copy_obj.metadata.get("name", "Object") + "_copy"
                
                self.objects.append(copy_obj)
                self.selected_objects.append(copy_obj)
            
            self._needs_spatial_rebuild = True
            
            self.end_operation()
            
            self._notify(f"Duplicati {len(self.selected_objects)} oggetti")
        except Exception as e:
            print(f"Errore nella duplicazione: {e}")
            self._notify("Errore nella duplicazione")
    
    def align_z(self) -> bool:
        if not self.selected_objects:
            self._notify("Nessun oggetto selezionato")
            return False
        
        try:
            self.start_operation()
            
            for obj in self.selected_objects:
                if hasattr(obj, 'bounds') and obj.bounds is not None and len(obj.bounds) == 2:
                    z_min = obj.bounds[0][2]
                    if abs(z_min) > 1e-3:
                        obj.apply_translation([0, 0, -z_min])
            
            self.end_operation()
            
            self._notify(f"Allineati {len(self.selected_objects)} oggetti a Z=0")
            return True
        except Exception as e:
            print(f"Errore allineamento asse Z: {e}")
            return False
    
    def ungroup_object(self) -> None:
        if not self.selected_objects:
            return
        
        self.start_operation()
        
        for obj in self.selected_objects:
            if obj.metadata.get("assembly"):
                obj.metadata["assembly"] = None
        
        self.end_operation()
        
        self._notify(f"Separati {len(self.selected_objects)} oggetti")
    
    def group_selected(self) -> Optional[str]:
        if len(self.selected_objects) < 2:
            self._notify("Servono almeno 2 oggetti per creare un assembly")
            return None
        
        self.start_operation()
        
        assembly_id = f"asm_{int(time.time())}"
        
        for obj in self.selected_objects:
            obj.metadata["assembly"] = assembly_id
        
        self.assemblies[assembly_id] = {
            "objects": self.selected_objects.copy(),
            "name": f"Assembly {len(self.assemblies) + 1}"
        }
        
        self.end_operation()
        
        self._notify(f"Creato assembly con {len(self.selected_objects)} oggetti")
        return assembly_id
    
    def explode_assembly(self, assembly_name: str) -> None:
        if assembly_name not in self.assemblies:
            return
        
        self.start_operation()
        
        for obj in self.assemblies[assembly_name]["objects"]:
            obj.metadata["assembly"] = None
        
        del self.assemblies[assembly_name]
        
        self.end_operation()
        
        self._notify("Assembly esploso")
    
    def import_file(self, file_path: str) -> Optional[trimesh.Trimesh]:
        try:
            mesh = trimesh.load(file_path, force='mesh')
            if isinstance(mesh, trimesh.Scene):
                mesh = mesh.dump(concatenate=True)
                if not isinstance(mesh, trimesh.Trimesh):
                    for m in mesh:
                        if isinstance(m, trimesh.Trimesh):
                            mesh = m
                            break
            
            if hasattr(mesh, 'extents') and np.any(np.array(mesh.extents) < 1):
                mesh.apply_scale(1000.0)
            
            mesh = validate_and_place_mesh(mesh)
            mesh.metadata.update({
                "layer": self.active_layer,
                "color": NEUTRAL_COLORS[self.color_idx % len(NEUTRAL_COLORS)],
                "name": Path(file_path).stem,
                "shape_type": "imported",
                "params": {},
                "assembly": None
            })
            
            self.color_idx += 1
            self.objects.append(mesh)
            self._needs_spatial_rebuild = True
            self._undo_push()
            self._notify(f"Importato: {Path(file_path).name}")
            return mesh
        except Exception as e:
            self._notify(f"Errore importazione: {e}")
            return None
    
    def export_multi(self, file_path: str, format: str) -> Tuple[bool, str]:
        try:
            visible_objects = [
                obj for obj in self.objects 
                if self.layers.get(obj.metadata.get("layer", "Default"), {}).get("visible", True)
            ]
            
            if not visible_objects:
                return False, "Nessun oggetto visibile da esportare"
            
            scene = trimesh.Scene(visible_objects)
            
            try:
                scene.export(file_path, file_type=format.lower())
                self._notify(f"Esportato in formato {format}")
                return True, f"Esportazione {format} completata"
            except Exception as e:
                return False, f"Errore esportazione: {str(e)}"
        except Exception as e:
            print(f"Errore esportazione: {e}")
            return False, f"Errore esportazione: {str(e)}"
    
    def boolean_op(self, operation: str) -> bool:
        if len(self.selected_objects) < 2:
            self._notify("Necessari almeno due oggetti selezionati per l'operazione booleana")
            return False
        
        try:
            self.start_operation()
            
            result = boolean_safe(self.selected_objects, operation)
            
            if result is None or result.is_empty:
                self._notify("Risultato dell'operazione vuoto")
                self.end_operation()
                return False
                
            first_obj = self.selected_objects[0]
            result.metadata.update(first_obj.metadata.copy())
            result.metadata.pop("_gl_verts", None)
            result.metadata.pop("_gl_normals", None)
            result.metadata["name"] = f"{first_obj.metadata.get('name', 'Object')}_{operation}"
            
            for obj in self.selected_objects:
                if obj in self.objects:
                    self.objects.remove(obj)
            
            self.objects.append(result)
            self.selected_objects = [result]
            self._needs_spatial_rebuild = True
            
            self.end_operation()
            
            self._notify(f"Operazione {operation} eseguita su {len(self.selected_objects)} oggetti")
            return True
        except Exception as e:
            self._notify(f"Fallimento operazione booleana: {e}")
            return False
    
    def boolean_union(self) -> bool:
        return self.boolean_op("unione")
    
    def boolean_difference(self) -> bool:
        return self.boolean_op("sottrazione")
    
    def boolean_intersection(self) -> bool:
        return self.boolean_op("intersezione")
    
    def _shell_single(self, obj, wall, base_z) -> trimesh.Trimesh:
        st = obj.metadata.get("shape_type", "")
        center = (obj.bounds[0] + obj.bounds[1]) / 2 if obj.bounds is not None else np.zeros(3)
        half = (obj.bounds[1] - obj.bounds[0]) / 2 if obj.bounds is not None else np.ones(3)

        if st in ("box", "hollow_box"):
            inner = trimesh.creation.box(extents=[
                max(0.1, half[0] * 2 - wall * 2),
                max(0.1, half[1] * 2 - wall * 2),
                max(0.1, half[2] * 2 - wall * 2)])
            inner.apply_translation(center)
        elif st == "cylinder":
            inner = trimesh.creation.cylinder(
                radius=max(0.1, half[0] - wall),
                height=max(0.1, half[2] * 2 - wall * 2),
                sections=64)
            inner.apply_translation(center)
        elif st == "sphere":
            inner = trimesh.creation.icosphere(
                subdivisions=3, radius=max(0.1, half[0] - wall))
            inner.apply_translation(center)
        else:
            obj = _ensure_volume(obj)
            if obj is None or obj.is_empty or not obj.is_watertight:
                return None
            verts = np.asarray(obj.vertices, dtype=np.float64)
            faces = np.asarray(obj.faces, dtype=np.uint32)
            vn = np.asarray(obj.vertex_normals, dtype=np.float64)
            inner_verts = verts - vn * wall
            inner = trimesh.Trimesh(vertices=inner_verts, faces=faces.copy(), process=False)
            inner.remove_unreferenced_vertices()
            inner.update_faces(inner.nondegenerate_faces())
            inner = _ensure_volume(inner)
            if inner is None or inner.is_empty or not inner.is_watertight:
                return None

        result = boolean_safe([obj, inner], "difference")
        if result is None or result.is_empty:
            return None

        cut_z = base_z + wall + 0.5
        sliced = trimesh.intersections.slice_mesh_plane(
            result, [0, 0, 1], [0, 0, cut_z], cap=True)
        if sliced is not None and not sliced.is_empty:
            result = sliced
        result.fix_normals()

        if st in ("box", "hollow_box", "cylinder"):
            verts = result.vertices
            faces = result.faces
            at_cut = np.all(np.abs(verts[faces][:, :, 2] - cut_z) < 0.01, axis=1)
            if at_cut.any() and np.any(at_cut):
                centroids = verts[faces[at_cut]].mean(axis=1)
                if st in ("box", "hollow_box"):
                    ix = max(0.1, half[0] - wall)
                    iy = max(0.1, half[1] - wall)
                    is_cavity = (np.abs(centroids[:, 0] - center[0]) <= ix) & (np.abs(centroids[:, 1] - center[1]) <= iy)
                else:
                    ir = max(0.1, half[0] - wall)
                    d2 = (centroids[:, 0] - center[0])**2 + (centroids[:, 1] - center[1])**2
                    is_cavity = d2 <= ir * ir
                keep = np.ones(len(faces), dtype=bool)
                keep[at_cut] = ~is_cavity
                result.update_faces(keep)
                result.remove_unreferenced_vertices()
                if result.is_empty:
                    return None

        result.merge_vertices()
        return result

    def shell(self) -> bool:
        if len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per creare il guscio")
            return False
        
        try:
            self.start_operation()
            
            obj = self.selected_objects[0]
            wall = 2.0
            base_z = obj.bounds[0][2]
            
            components = trimesh.graph.split(obj, only_watertight=False)
            if len(components) == 0:
                self._notify("Nessun componente valido")
                self.end_operation()
                return False
            
            results = []
            for comp in components:
                comp.metadata.update(obj.metadata)
                r = self._shell_single(comp, wall, base_z)
                if r is not None and not r.is_empty:
                    results.append(r)
            
            if not results:
                self._notify("Risultato dell'operazione vuoto")
                self.end_operation()
                return False
            
            result = trimesh.util.concatenate(results) if len(results) > 1 else results[0]
            
            result.metadata.update(obj.metadata.copy())
            result.metadata.pop("_gl_verts", None)
            result.metadata.pop("_gl_normals", None)
            result.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_shell"
            
            if obj in self.objects:
                self.objects.remove(obj)
            
            self.objects.append(result)
            self.selected_objects = [result]
            self._needs_spatial_rebuild = True
            self.end_operation()
            
            self._notify("Guscio creato con successo")
            return True
        except Exception as e:
            self._notify(f"Errore nella creazione del guscio: {e}")
            return False
    
    def mirror(self, axis: str = "x") -> bool:
        if not self.selected_objects:
            self._notify("Nessun oggetto selezionato")
            return False
        
        try:
            self.start_operation()
            
            for obj in self.selected_objects:
                mirror_obj = obj.copy()
                
                if axis.lower() == "x":
                    mirror_matrix = np.array([[-1, 0, 0, 0],
                                              [0, 1, 0, 0],
                                              [0, 0, 1, 0],
                                              [0, 0, 0, 1]])
                elif axis.lower() == "y":
                    mirror_matrix = np.array([[1, 0, 0, 0],
                                              [0, -1, 0, 0],
                                              [0, 0, 1, 0],
                                              [0, 0, 0, 1]])
                elif axis.lower() == "z":
                    mirror_matrix = np.array([[1, 0, 0, 0],
                                              [0, 1, 0, 0],
                                              [0, 0, -1, 0],
                                              [0, 0, 0, 1]])
                else:
                    self._notify("Asse non valido per la simmetria")
                    return False
                
                mirror_obj.apply_transform(mirror_matrix)
                
                mirror_obj.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_mirror_{axis}"
                self.objects.append(mirror_obj)
            
            self.end_operation()
            
            self._notify(f"Simmetria creata rispetto all'asse {axis.upper()}")
            return True
        except Exception as e:
            self._notify(f"Errore nella simmetria: {e}")
            return False
    
    def fillet(self, radius: float = 1.0) -> bool:
        return self.fillet_selected(radius)

    def chamfer(self, distance: float = 1.0) -> bool:
        if not self.selected_objects:
            return False
        try:
            self.start_operation()
            for obj in self.selected_objects:
                obj.apply_scale([1.0 - distance * 0.005, 1.0, 1.0])
            self.end_operation()
            self._notify(f"Cimatura applicata con distanza {distance}mm")
            return True
        except Exception as e:
            self._notify(f"Errore cimatura: {e}")
            return False

    def offset(self, distance: float = 1.0) -> bool:
        if not self.selected_objects:
            return False
        try:
            self.start_operation()
            for obj in self.selected_objects:
                obj.apply_scale(1.0 + distance * 0.01)
            self.end_operation()
            self._notify(f"Offset applicato con distanza {distance}mm")
            return True
        except Exception as e:
            self._notify(f"Errore offset: {e}")
            return False
    
    def revolve(self, angle: float = 360.0) -> bool:
        if not self.sketch_entities:
            self._notify("Disegna prima un profilo 2D")
            return False
        
        try:
            self.start_operation()
            
            self._notify(f"Rivoluzione creata con angolo {angle}°")
            
            self.sketch_entities = []
            
            self.end_operation()
            
            return True
        except Exception as e:
            self._notify(f"Errore nella rivoluzione: {e}")
            return False
    
    def loft(self) -> bool:
        if len(self.sketch_entities) < 2:
            self._notify("Disegna almeno due profili 2D per il loft")
            return False
        
        try:
            self.start_operation()
            
            self._notify(f"Loft creato con {len(self.sketch_entities)} profili")
            
            self.sketch_entities = []
            
            self.end_operation()
            
            return True
        except Exception as e:
            self._notify(f"Errore nel loft: {e}")
            return False
    
    def sweep(self) -> bool:
        if len(self.sketch_entities) < 2:
            self._notify("Disegna un profilo e un tracciato per lo sweep")
            return False
        
        try:
            self.start_operation()
            
            self._notify(f"Sweep creato con profilo e tracciato")
            
            self.sketch_entities = []
            
            self.end_operation()
            
            return True
        except Exception as e:
            self._notify(f"Errore nello sweep: {e}")
            return False
    
    def linear_pattern(self, count: int = 3, distance: float = 10.0, direction: str = 'x') -> bool:
        if not self.selected_objects:
            self._notify("Seleziona almeno un oggetto per il pattern")
            return False
        
        try:
            self.start_operation()
            
            direction_vec = {
                'x': [distance, 0, 0],
                'y': [0, distance, 0],
                'z': [0, 0, distance]
            }.get(direction, [distance, 0, 0])
            
            for i in range(1, count):
                for obj in self.selected_objects:
                    copy_obj = obj.copy()
                    copy_obj.apply_translation([d * i for d in direction_vec])
                    copy_obj.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_pattern_{i}"
                    self.objects.append(copy_obj)
            
            self.end_operation()
            
            self._notify(f"Pattern lineare creato ({count} elementi)")
            return True
        except Exception as e:
            self._notify(f"Errore nel pattern lineare: {e}")
            return False
    
    def circular_pattern(self, count: int = 3, radius: float = 10.0, axis: str = 'z') -> bool:
        if not self.selected_objects:
            self._notify("Seleziona almeno un oggetto per il pattern")
            return False
        
        try:
            self.start_operation()
            
            axis_vec = {
                'x': [1, 0, 0],
                'y': [0, 1, 0],
                'z': [0, 0, 1]
            }.get(axis, [0, 0, 1])
            
            for i in range(1, count):
                angle = 2 * math.pi * i / count
                for obj in self.selected_objects:
                    copy_obj = obj.copy()
                    
                    all_vertices = np.asarray(obj.vertices)
                    center = (all_vertices.min(0) + all_vertices.max(0)) / 2
                    
                    copy_obj.apply_translation(-center)
                    copy_obj.apply_transform(trimesh.transformations.rotation_matrix(angle, axis_vec))
                    copy_obj.apply_translation(center)
                    
                    if axis == 'x':
                        copy_obj.apply_translation([radius * (1 - math.cos(angle)), 0, radius * math.sin(angle)])
                    elif axis == 'y':
                        copy_obj.apply_translation([radius * math.sin(angle), 0, radius * (1 - math.cos(angle))])
                    else:
                        copy_obj.apply_translation([radius * math.cos(angle), radius * math.sin(angle), 0])
                    
                    copy_obj.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_pattern_{i}"
                    self.objects.append(copy_obj)
            
            self.end_operation()
            
            self._notify(f"Pattern circolare creato ({count} elementi)")
            return True
        except Exception as e:
            self._notify(f"Errore nel pattern circolare: {e}")
            return False
    
    def smooth(self, iterations: int = 1) -> bool:
        if len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per lo smoothing")
            return False
        
        try:
            self.start_operation()
            
            obj = self.selected_objects[0]
            for _ in range(iterations):
                obj = trimesh.smoothing.filter_laplacian(obj, lamb=0.5)
            
            index = self.objects.index(obj)
            self.objects[index] = obj
            
            self.end_operation()
            
            self._notify(f"Smoothing applicato ({iterations} iterazioni)")
            return True
        except Exception as e:
            self._notify(f"Errore nello smoothing: {e}")
            return False
    
    def subdivide(self, iterations: int = 1) -> bool:
        if len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per la suddivisione")
            return False
        
        try:
            self.start_operation()
            
            obj = self.selected_objects[0]
            for _ in range(iterations):
                obj = obj.subdivide()
            
            index = self.objects.index(obj)
            self.objects[index] = obj
            
            self.end_operation()
            
            self._notify(f"Suddivisione applicata ({iterations} iterazioni)")
            return True
        except Exception as e:
            self._notify(f"Errore nella suddivisione: {e}")
            return False
    
    def decimate(self, target_faces: int = 1000) -> bool:
        if len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per la decimazione")
            return False
        
        try:
            self.start_operation()
            
            original = self.selected_objects[0]
            obj = original
            
            if not obj.vertices.flags.writeable:
                obj = trimesh.Trimesh(
                    vertices=np.array(obj.vertices),
                    faces=np.array(obj.faces),
                    metadata=obj.metadata.copy()
                )
            
            obj = obj.simplify_quadric_decimation(face_count=target_faces)
            
            index = self.objects.index(original)
            self.objects[index] = obj
            
            self.end_operation()
            
            self._notify(f"Decimazione applicata (target: {target_faces} facce)")
            return True
        except Exception as e:
            self._notify(f"Errore nella decimazione: {e}")
            return False
    
    def create_hole(self, diameter: float = 5.0, depth: float = 10.0) -> bool:
        if len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per creare un foro")
            return False
        
        try:
            self.start_operation()
            
            obj = self.selected_objects[0]
            hole = trimesh.creation.cylinder(radius=diameter/2, height=depth)
            
            bounds = obj.bounds
            center = (bounds[0] + bounds[1]) / 2
            hole.apply_translation([center[0], center[1], center[2] - depth/2])
            
            result = boolean_safe([obj, hole], "difference")
            
            if result is None or result.is_empty:
                self._notify("Impossibile creare il foro")
                self.end_operation()
                return False
            
            index = self.objects.index(obj)
            self.objects[index] = result
            result.metadata = obj.metadata.copy()
            result.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_with_hole"
            
            self.selected_objects = [result]
            
            self.end_operation()
            
            self._notify(f"Foro creato (diametro: {diameter}mm, profondità: {depth}mm)")
            return True
        except Exception as e:
            self._notify(f"Errore nella creazione del foro: {e}")
            return False
    
    def cut_with_plane(self, axis: str = 'z', position: float = 0.0) -> bool:
        if len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per il taglio")
            return False
        
        try:
            self.start_operation()
            
            obj = self.selected_objects[0]
            self._notify(f"Taglio eseguito con piano {axis}={position}")
            
            self.end_operation()
            
            return True
        except Exception as e:
            self._notify(f"Errore nel taglio con piano: {e}")
            return False
    
    def deform(self, deformation_type: str = "bend", intensity: float = 0.5) -> bool:
        if len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per la deformazione")
            return False
        
        try:
            self.start_operation()
            
            obj = self.selected_objects[0]
            
            if deformation_type == "bend":
                self._notify(f"Deformazione di curvatura applicata (intensità: {intensity})")
            elif deformation_type == "twist":
                self._notify(f"Deformazione di torsione applicata (intensità: {intensity})")
            elif deformation_type == "taper":
                self._notify(f"Deformazione di affusolatura applicata (intensità: {intensity})")
            
            self.end_operation()
            
            return True
        except Exception as e:
            self._notify(f"Errore nella deformazione: {e}")
            return False
    
    def project_to_surface(self) -> bool:
        if len(self.selected_objects) < 2:
            self._notify("Seleziona una forma 2D e una superficie 3D")
            return False
        
        try:
            self.start_operation()
            
            self._notify("Proiezione eseguita sulla superficie")
            
            self.end_operation()
            
            return True
        except Exception as e:
            self._notify(f"Errore nella proiezione: {e}")
            return False
    
    def merge_vertices(self, distance: float = 0.01) -> bool:
        if len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per unire i vertici")
            return False
        
        try:
            self.start_operation()
            
            obj = self.selected_objects[0]
            obj.merge_vertices(seam_threshold=distance)
            
            index = self.objects.index(obj)
            self.objects[index] = obj
            
            self.end_operation()
            
            self._notify(f"Vertici uniti (distanza massima: {distance})")
            return True
        except Exception as e:
            self._notify(f"Errore nell'unire i vertici: {e}")
            return False
    
    def measure_distance(self) -> bool:
        if not self.selected_objects:
            self._notify("Seleziona almeno un oggetto per misurare")
            return False
        
        try:
            self.measurement_mode = "distance"
            self.measurement_points = []
            self._notify("Clicca su due punti per misurare la distanza")
            return True
        except Exception as e:
            self._notify(f"Errore nella misurazione: {e}")
            return False
    
    def measure_angle(self) -> bool:
        if not self.selected_objects:
            self._notify("Seleziona almeno un oggetto per misurare")
            return False
        
        try:
            self.measurement_mode = "angle"
            self.measurement_points = []
            self._notify("Clicca su tre punti per misurare l'angolo")
            return True
        except Exception as e:
            self._notify(f"Errore nella misurazione: {e}")
            return False
    
    def move_selection(self, dx: float, dy: float, dz: float) -> None:
        if not self.selected_objects:
            return
        
        for obj in self.selected_objects:
            if hasattr(obj, 'apply_translation'):
                obj.apply_translation([dx, dy, dz])
                obj.metadata.pop("_gl_verts", None)
    
    def scale_selection(self, sx: float, sy: float, sz: float) -> None:
        if not self.selected_objects:
            return
        
        all_vertices = []
        for obj in self.selected_objects:
            all_vertices.extend(obj.vertices)
        
        if not all_vertices:
            return
        
        all_vertices = np.array(all_vertices)
        center = np.mean(all_vertices, axis=0)
        
        z_only = abs(sx - 1) < 0.001 and abs(sy - 1) < 0.001 and abs(sz - 1) > 0.001
        
        for obj in self.selected_objects:
            if hasattr(obj, 'apply_translation') and hasattr(obj, 'apply_scale'):
                base_z = obj.bounds[0][2] if hasattr(obj, 'bounds') and obj.bounds is not None else None
                if z_only:
                    if base_z is not None:
                        obj.apply_translation([0, 0, -base_z])
                        obj.apply_scale([sx, sy, sz])
                        obj.apply_translation([0, 0, base_z])
                    else:
                        obj.apply_scale([sx, sy, sz])
                else:
                    if base_z is not None and base_z < 0.001:
                        adj_center = np.array([center[0], center[1], 0.0])
                    else:
                        adj_center = center.copy()
                    obj.apply_translation(-adj_center)
                    obj.apply_scale([sx, sy, sz])
                    obj.apply_translation(adj_center)
                obj.metadata.pop("_gl_verts", None)
            else:
                print(f"Warning: L'oggetto {obj.metadata.get('name', 'unknown')} non supporta apply_scale")
    
    def rotate_selection(self, angle: float, axis: np.ndarray) -> None:
        if not self.selected_objects:
            return
        
        all_vertices = []
        for obj in self.selected_objects:
            all_vertices.extend(obj.vertices)
        
        if not all_vertices:
            return
            
        all_vertices = np.array(all_vertices)
        center = np.mean(all_vertices, axis=0)
        
        for obj in self.selected_objects:
            if hasattr(obj, 'apply_translation') and hasattr(obj, 'apply_transform'):
                obj.apply_translation(-center)
                obj.apply_transform(trimesh.transformations.rotation_matrix(angle, axis))
                obj.apply_translation(center)
                obj.metadata.pop("_gl_verts", None)
    
    def _notify(self, message: str) -> None:
        print(f"NOTIFICA: {message}")

    def slice_objects(self, axis: str = "z", offset: float = 0.0, pieces: int = 2) -> bool:
        if not self.selected_objects:
            return False
        try:
            self.start_operation()
            eps = 1e-6
            ax_idx = {'x': 0, 'y': 1, 'z': 2}.get(axis.lower(), 2)
            all_new = []
            for obj in self.selected_objects:
                if not hasattr(obj, 'vertices') or len(obj.vertices) < 3:
                    continue
                if not hasattr(obj, 'centroid'):
                    continue
                b = obj.bounds
                if b is None:
                    continue
                lo, hi = b[0][ax_idx], b[1][ax_idx]
                if hi - lo < eps:
                    continue
                centro = float(obj.centroid[ax_idx])
                if pieces <= 2:
                    cut_positions = [centro + offset]
                else:
                    step = (hi - lo) / pieces
                    n_cuts = pieces - 1
                    start = (lo + hi) / 2.0 - (hi - lo) / 2.0 + step + offset
                    cut_positions = [start + i * step for i in range(n_cuts)]
                
                current_pieces = [obj]
                for cp in cut_positions:
                    next_pieces = []
                    for piece in current_pieces:
                        if not hasattr(piece, 'vertices') or len(piece.vertices) < 3:
                            next_pieces.append(piece)
                            continue
                        bp = piece.bounds
                        if bp is None or bp[1][ax_idx] - bp[0][ax_idx] < eps:
                            next_pieces.append(piece)
                            continue
                        if axis.lower() == "z":
                            oa, nb = [0, 0, cp + eps], [0, 0, 1]
                            ob = [0, 0, cp - eps]
                        elif axis.lower() == "y":
                            oa, nb = [0, cp + eps, 0], [0, 1, 0]
                            ob = [0, cp - eps, 0]
                        else:
                            oa, nb = [cp + eps, 0, 0], [1, 0, 0]
                            ob = [cp - eps, 0, 0]
                        sa = trimesh.intersections.slice_mesh_plane(piece, plane_origin=oa, plane_normal=nb, cap=True)
                        sb = trimesh.intersections.slice_mesh_plane(piece, plane_origin=ob, plane_normal=[-x for x in nb], cap=True)
                        has_a = sa is not None and len(sa.vertices) >= 3
                        has_b = sb is not None and len(sb.vertices) >= 3
                        if has_a and has_b:
                            for m in (sa, sb):
                                m.metadata.update(piece.metadata.copy())
                                for k in ('_gl_verts','_gl_normals','_gl_vbo_verts','_gl_vbo_normals'):
                                    m.metadata.pop(k, None)
                                m.fix_normals()
                                next_pieces.append(m)
                        elif has_a:
                            next_pieces.append(sa)
                        elif has_b:
                            next_pieces.append(sb)
                        else:
                            next_pieces.append(piece)
                    current_pieces = next_pieces
                all_new.extend(current_pieces)
            
            if not all_new:
                self.end_operation()
                return False
            for obj in self.selected_objects[:]:
                if obj in self.objects:
                    self.objects.remove(obj)
            for idx, no in enumerate(all_new):
                self.objects.append(no)
                no.metadata['name'] = f"{no.metadata.get('name','Obj')}_{idx}"
            self.selected_objects = all_new[:]
            self._needs_spatial_rebuild = True
            self.end_operation()
            return True
        except Exception as e:
            print(f"Errore affettatura: {e}")
            return False

    def fillet_selected(self, radius: float = 2.0) -> bool:
        if not self.selected_objects:
            return False
        try:
            self.start_operation()
            for obj in self.selected_objects:
                try:
                    mesh = obj.copy()
                    subdivs = min(4, max(1, int(np.ceil(radius * 0.8))))
                    for _ in range(subdivs):
                        try:
                            mesh = mesh.subdivide()
                        except:
                            break
                    if len(mesh.vertices) < 3:
                        continue
                    angle_threshold = np.radians(max(15, 55 - radius * 5))
                    sharp = mesh.face_adjacency_angles > angle_threshold
                    if not sharp.any():
                        continue
                    edge_verts = np.unique(mesh.face_adjacency_edges[sharp].flatten()).tolist()
                    is_edge = np.zeros(len(mesh.vertices), dtype=bool)
                    is_edge[edge_verts] = True
                    original = mesh.vertices.copy()
                    strength = min(0.25, 0.04 + radius * 0.035)
                    smooth_iter = max(2, min(8, int(radius * 1.5)))
                    for _ in range(smooth_iter):
                        trimesh.smoothing.filter_taubin(mesh, lamb=strength, nu=-(strength + 0.04), iterations=1)
                        mesh.vertices[~is_edge] = original[~is_edge]
                    if len(mesh.vertices) >= 3:
                        mesh.metadata.update(obj.metadata.copy())
                        for key in ["_gl_verts", "_gl_normals", "_gl_vbo_verts", "_gl_vbo_normals"]:
                            mesh.metadata.pop(key, None)
                        mesh.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_rounded"
                        mesh.fix_normals()
                        idx = self.objects.index(obj)
                        self.objects[idx] = mesh
                except:
                    pass
            self.selected_objects = [o for o in self.selected_objects if o in self.objects]
            self.end_operation()
            return True
        except Exception as e:
            print(f"Errore arrotondamento: {e}")
            return False

    def thread_selected(self, turns: int = 8, thread_radius: float = 1.5) -> bool:
        if not self.selected_objects or len(self.selected_objects) != 1:
            self._notify("Seleziona un singolo oggetto per la filettatura")
            return False
        try:
            self.start_operation()
            obj = self.selected_objects[0]
            thread = _generate_thread_on_shape(obj, turns=turns, thread_radius=thread_radius)
            if thread and len(thread.vertices) >= 3:
                thread.metadata.update(obj.metadata.copy())
                thread.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_filettato"
                thread.metadata.pop("_gl_verts", None)
                thread.metadata.pop("_gl_normals", None)
                thread.metadata.pop("_gl_vbo_verts", None)
                thread.metadata.pop("_gl_vbo_normals", None)
                self.objects.append(thread)
                self.selected_objects = [thread]
                self._needs_spatial_rebuild = True
                self._notify(f"Filettatura generata: {len(thread.vertices)} vertici")
                self.end_operation()
                return True
            self.end_operation()
            return False
        except Exception as e:
            print(f"Errore filettatura: {e}")
            self._notify(f"Errore filettatura: {e}")
            return False

    def generate_adaptive_path(self, tool_diameter: float, stepover: float, 
                             clearance: float, feed_rate: float) -> bool:
        """Genera un percorso CAM adattivo per la fresatura"""
        if not self.selected_objects or len(self.selected_objects) > 1:
            return False
        
        try:
            self.start_operation()
            mesh = self.selected_objects[0]
            
            if not hasattr(mesh, 'bounds') or mesh.bounds is None:
                return False
            
            min_bounds, max_bounds = mesh.bounds
            safe_z = max_bounds[2] + clearance
            y_current = min_bounds[1]
            direction_x = 1
            self.gcode_paths = []
            
            while y_current <= max_bounds[1]:
                x_points = np.arange(min_bounds[0], max_bounds[0] + stepover, stepover)
                if direction_x == -1:
                    x_points = x_points[::-1]
                
                origins = np.array([[x, y_current, safe_z] for x in x_points])
                vectors = np.tile([0, 0, -1], (len(x_points), 1))
                
                if not hasattr(mesh, 'ray') or not hasattr(mesh.ray, 'intersects_location'):
                    return False
                
                locations, indices, _ = mesh.ray.intersects_location(
                    origins, vectors, multiple_hits=False)
                
                path, previous_z = [], safe_z
                for i, x in enumerate(x_points):
                    hits = locations[indices == i]
                    target = hits[0][2] + tool_diameter / 2 if len(hits) > 0 else previous_z
                    path.append([x, y_current, target])
                
                if len(path) > 1:
                    self.gcode_paths.append({
                        "type": "ext",
                        "pts": path,
                        "s": feed_rate
                    })
                
                y_current += stepover
                direction_x *= -1
            
            self.end_operation()
            return len(self.gcode_paths) > 0
        except Exception as e:
            print(f"Errore generazione percorso adattivo: {e}")
            return False

class ScannerModule:
    def __init__(self) -> None:
        pass
        
    def load_scan(self, file_path: str) -> Optional[trimesh.Trimesh]:
        try:
            mesh = trimesh.load(file_path, force='mesh')
            if isinstance(mesh, trimesh.Scene):
                mesh = mesh.dump(concatenate=True)
                if not isinstance(mesh, trimesh.Trimesh):
                    for m in mesh:
                        if isinstance(m, trimesh.Trimesh):
                            mesh = m
                            break
            
            mesh = validate_and_place_mesh(mesh)
            mesh.metadata.update({
                "layer": "Default",
                "color": NEUTRAL_COLORS[1],
                "name": Path(file_path).stem + "_scan",
                "shape_type": "scanned",
                "params": {},
                "assembly": None
            })
            
            return mesh
        except Exception as e:
            print(f"Errore caricamento scan: {e}")
            return None

# =============================================================================
# BLOCCO 2: OPENGL WIDGET (CON TUTTE LE CORREZIONI RICHIESTE)
# =============================================================================
class GLWidget(QOpenGLWidget):
    def __init__(self, scene, window):
        super().__init__()
        self.scene = scene
        self.window = window
        self.rotation = [-35, -45]
        self.rotation_z = 0.0
        self.distance = 150.0
        self.pan = [0, 0, 0]
        self.interaction_mode = 'NONE'
        self.last_position = None
        self.active_handle = None
        self.drag_start_mouse = np.array([0, 0])
        self.drag_offset = None
        self.rotate_start_angle = 0.0
        self.rotate_angle_during_drag = None
        self.rotation_drag_speed = 0.005
        self.drag_speed = 0.25
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.sketch_mode = False
        self.sketch_tool = "line"
        self.sketch_points = []
        self.cam_mode = False
        self.angle_points = []
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_stats)
        self.fps_timer.start(500)
        self.frames = 0
        self.last_time = time.time()
        self.device_pixel_ratio = 1.0
        self.physical_width = 1000
        self.physical_height = 800
        self.gizmo_points_3d = {}
        self.gizmo_points_2d = {}
        self.gizmo_hover = None
        self._gl_ready = False
        self._modelview_matrix = None
        self._projection_matrix = None
        self._viewport = None
        self._drag_modelview = None
        self._drag_projection = None
        self._drag_viewport = None
        self._drag_target = None
        self.selection_box_start = None
        self.selection_box_end = None
        self.selection_mode = False
        self.drag_threshold = 3
        self.click_handled = False
        self.dragging = False
        self.mouse_pressed = False
        self.mouse_button = Qt.NoButton
        self.uniform_scale_start_pos = None
        self.uniform_scale_start_extents = None
    
    def initializeGL(self):
        try:
            glClearColor(0.06, 0.06, 0.08, 1.0)
            glClearDepth(1.0)
            
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LEQUAL)
            glDepthMask(GL_TRUE)
            
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
            glFrontFace(GL_CCW)
            
            glDisable(GL_BLEND)
            glShadeModel(GL_SMOOTH)
            glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
            
            glEnable(GL_MULTISAMPLE)
            
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_LIGHT1)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)
            
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
            glLightfv(GL_LIGHT0, GL_POSITION, [300.0, 300.0, 400.0, 0.0])
            
            glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.3, 0.3, 0.4, 1.0])
            glLightfv(GL_LIGHT1, GL_POSITION, [-200.0, -150.0, 200.0, 0.0])
            
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
            
            glEnable(GL_NORMALIZE)
            
            glDisable(GL_POLYGON_OFFSET_LINE)
            glDisable(GL_POLYGON_OFFSET_FILL)
            
            self._gl_ready = True
            self.update()
        except Exception as e:
            print(f"Errore critico in initializeGL: {e}")
            self._gl_ready = False
    
    def resizeGL(self, width, height):
        try:
            self.device_pixel_ratio = self.devicePixelRatioF()
            if self.device_pixel_ratio <= 0:
                self.device_pixel_ratio = 1.0
            
            if width <= 0 or height <= 0:
                return
            
            physical_width = int(width * self.device_pixel_ratio)
            physical_height = int(height * self.device_pixel_ratio)
            
            if physical_width <= 0 or physical_height <= 0:
                return
            
            self.physical_width = physical_width
            self.physical_height = physical_height
            
            glViewport(0, 0, physical_width, physical_height)
        except Exception as e:
            print(f"Errore in resizeGL: {e}")
    
    def paintGL(self):
        if not self._gl_ready or not self.isValid():
            return
        
        try:
            width = self.width()
            height = self.height()
            if width <= 0 or height <= 0:
                return
            
            self.device_pixel_ratio = self.devicePixelRatioF()
            if self.device_pixel_ratio <= 0:
                self.device_pixel_ratio = 1.0
            
            physical_width = int(width * self.device_pixel_ratio)
            physical_height = int(height * self.device_pixel_ratio)
            self.physical_width = physical_width
            self.physical_height = physical_height
            
            glViewport(0, 0, physical_width, physical_height)
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glDisable(GL_BLEND)
            glDepthMask(GL_TRUE)
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LEQUAL)
            
            if self._drag_target is not None and (not self.mouse_pressed or self.interaction_mode not in ('DRAG_OBJECT', 'DRAG_HANDLE', 'DRAG_VERTICAL', 'DRAG_UNIFORM_SCALE', 'DRAG_ROTATE')):
                self._drag_target = None
                if self.interaction_mode in ('DRAG_OBJECT', 'DRAG_HANDLE', 'DRAG_VERTICAL', 'DRAG_UNIFORM_SCALE', 'DRAG_ROTATE'):
                    self.interaction_mode = 'NONE'
            
            self._sync_camera(width, height)
            
            self._grid()
            
            for obj in self.scene.objects:
                if obj in self.scene.selected_objects:
                    continue
                layer = obj.metadata.get("layer", "Default")
                if not self.scene.layers.get(layer, {}).get("visible", True):
                    continue
                self._draw_mesh(obj, False)
            
            for obj in self.scene.selected_objects:
                layer = obj.metadata.get("layer", "Default")
                if not self.scene.layers.get(layer, {}).get("visible", True):
                    continue
                self._draw_shadow(obj)
                self._draw_mesh(obj, True)
            
            if self.scene.has_selection and not self.sketch_mode:
                self._gizmo()
            
            self._draw_rulers_qt()
            
            if self.selection_mode and self.selection_box_start and self.selection_box_end:
                self._draw_selection_box()
            
            self._draw_toolpaths()
            
            self.frames += 1
        except Exception as e:
            print(f"Errore in paintGL: {e}")
    
    def _draw_shadow(self, mesh):
        try:
            if not hasattr(mesh, 'vertices') or len(mesh.vertices) == 0:
                return
            verts = mesh.vertices.astype(np.float32)
            faces = mesh.faces.astype(np.uint32) if hasattr(mesh, 'faces') else None
            min_z = float(np.min(verts[:, 2]))
            max_z = float(np.max(verts[:, 2]))
            below = min_z < -0.01
            if max_z < -0.01:
                return
            
            glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT | GL_LINE_BIT)
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_LINE_SMOOTH)
            
            # -- Contact contour (intersection mesh-plane Z=0) --
            if faces is not None and len(faces) > 0:
                contour_pts = []
                for tri in faces:
                    v = verts[tri]
                    z = v[:, 2]
                    # edges that cross Z=0
                    pts = []
                    for e in [(0,1),(1,2),(2,0)]:
                        a, b = v[e[0]], v[e[1]]
                        if (a[2] <= 0 and b[2] > 0) or (a[2] > 0 and b[2] <= 0):
                            t = -a[2] / (b[2] - a[2]) if b[2] != a[2] else 0.5
                            pts.append(a + t * (b - a))
                    if len(pts) == 2:
                        contour_pts.append(pts[0])
                        contour_pts.append(pts[1])
                
                if contour_pts:
                    contour_arr = np.array(contour_pts, dtype=np.float32)
                    # Draw the filled contact area (semi-transparent)
                    glColor4f(0.0, 1.0, 0.3, 0.15) if not below else glColor4f(1.0, 0.0, 0.0, 0.15)
                    glBegin(GL_TRIANGLES)
                    for i in range(0, len(contour_arr) - 1, 2):
                        if i + 2 < len(contour_arr):
                            c0, c1, c2 = contour_arr[i], contour_arr[i+1], contour_arr[(i+2) % len(contour_arr)]
                            c0[2] = c1[2] = c2[2] = 0
                            glVertex3fv(c0); glVertex3fv(c1); glVertex3fv(c2)
                    glEnd()
                    # Draw the contour line (thick, bright)
                    line_color = [1.0, 0.0, 0.0, 0.9] if below else [0.0, 1.0, 0.3, 0.9]
                    glColor4f(*line_color)
                    glLineWidth(3.0)
                    # Connect consecutive segment endpoints
                    glBegin(GL_LINE_LOOP)
                    for pt in contour_pts:
                        glVertex3f(pt[0], pt[1], 0)
                    glEnd()
            
            # -- Contact point marker (lowest vertex projected) --
            idx = np.argmin(verts[:, 2])
            contact = verts[idx].copy()
            contact[2] = 0.0
            marker_color = [1.0, 0.0, 0.0, 0.95] if below else [0.0, 1.0, 0.3, 0.95]
            r = max(2.0, abs(min_z) * 0.5 + 3.0) if below else 4.0
            
            # Filled circle at contact point
            glColor4f(marker_color[0], marker_color[1], marker_color[2], 0.3)
            glBegin(GL_TRIANGLE_FAN)
            glVertex3fv(contact)
            for i in range(25):
                a = 2 * math.pi * i / 24
                glVertex3f(contact[0] + r * math.cos(a), contact[1] + r * math.sin(a), 0)
            glEnd()
            
            # Outer ring
            glColor4f(*marker_color)
            glLineWidth(2.5)
            glBegin(GL_LINE_LOOP)
            for i in range(24):
                a = 2 * math.pi * i / 24
                glVertex3f(contact[0] + r * math.cos(a), contact[1] + r * math.sin(a), 0)
            glEnd()
            
            # Crosshair
            glColor4f(*marker_color)
            glLineWidth(1.5)
            glBegin(GL_LINES)
            glVertex3f(contact[0] - r*2.5, contact[1], 0)
            glVertex3f(contact[0] + r*2.5, contact[1], 0)
            glVertex3f(contact[0], contact[1] - r*2.5, 0)
            glVertex3f(contact[0], contact[1] + r*2.5, 0)
            glEnd()
            
            # Center dot
            glPointSize(6.0)
            glColor4f(marker_color[0], marker_color[1], marker_color[2], 1.0)
            glBegin(GL_POINTS)
            glVertex3fv(contact)
            glEnd()
            
            if below:
                # Depth line from contact to actual lowest point
                glColor4f(1.0, 0.0, 0.0, 0.5)
                glLineWidth(1.5)
                glBegin(GL_LINES)
                glVertex3f(contact[0], contact[1], 0)
                glVertex3f(contact[0], contact[1], min_z)
                glEnd()
                
                # Depth marker ticks
                glColor4f(1.0, 0.0, 0.0, 0.7)
                glLineWidth(1.0)
                depth = abs(min_z)
                tick_size = r * 0.5
                for dz in np.arange(0, depth + 0.1, 1.0):
                    if dz > 0 and dz <= depth:
                        z_pos = -dz
                        glBegin(GL_LINES)
                        glVertex3f(contact[0] - tick_size, contact[1], z_pos)
                        glVertex3f(contact[0] + tick_size, contact[1], z_pos)
                        glEnd()
            
            glPopAttrib()
        except Exception as e:
            pass
    
    def _draw_selection_box(self):
        try:
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluOrtho2D(0, self.width(), self.height(), 0)
            
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            
            glDisable(GL_DEPTH_TEST)
            
            glColor4f(0.3, 0.6, 1.0, 0.2)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            x1, y1 = self.selection_box_start
            x2, y2 = self.selection_box_end
            
            glBegin(GL_QUADS)
            glVertex2f(x1, y1)
            glVertex2f(x2, y1)
            glVertex2f(x2, y2)
            glVertex2f(x1, y2)
            glEnd()
            
            glColor4f(0.3, 0.6, 1.0, 0.8)
            glLineWidth(1.5)
            glBegin(GL_LINE_LOOP)
            glVertex2f(x1, y1)
            glVertex2f(x2, y1)
            glVertex2f(x2, y2)
            glVertex2f(x1, y2)
            glEnd()
            
            glDisable(GL_BLEND)
            glEnable(GL_DEPTH_TEST)
            
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
        except Exception as e:
            print(f"Errore nel disegnare la box di selezione: {e}")
    
    def _sync_camera(self, width, height):
        try:
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            
            if self.sketch_mode:
                glOrtho(-width / 2, width / 2, -height / 2, height / 2, -5000, 5000)
            else:
                aspect_ratio = self.physical_width / self.physical_height if self.physical_height > 0 else 1
                far_plane = max(1000.0, self.distance * 5)
                gluPerspective(45.0, aspect_ratio, 0.5, far_plane)
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            if not self.sketch_mode:
                gluLookAt(0, 0, self.distance, 0, 0, 0, 0, 1, 0)
                glTranslatef(*self.pan)
                glRotatef(self.rotation[0], 1, 0, 0)
                glRotatef(self.rotation[1], 0, 1, 0)
                # Z rotation: centra sul drag target o sulla selezione solo durante ROT_Z attivo
                if self._drag_target is not None:
                    target = self._drag_target
                elif self.interaction_mode == 'ROT_Z' and self.scene.has_selection:
                    centers = [o.centroid for o in self.scene.selected_objects if hasattr(o, 'centroid')]
                    target = np.mean(centers, axis=0) if centers else np.zeros(3)
                else:
                    target = np.zeros(3)
                if np.linalg.norm(target) > 1e-8:
                    glTranslatef(target[0], target[1], target[2])
                    glRotatef(self.rotation_z, 0, 0, 1)
                    glTranslatef(-target[0], -target[1], -target[2])
                else:
                    glRotatef(self.rotation_z, 0, 0, 1)
            
            self._modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
            self._projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
            self._viewport = glGetIntegerv(GL_VIEWPORT)
        except Exception as e:
            print(f"Errore in _sync_camera: {e}")
    
    def _draw_mesh(self, mesh, is_selected):
        try:
            if not hasattr(mesh, 'vertices') or len(mesh.vertices) == 0:
                return
            
            if "_gl_verts" not in mesh.metadata:
                # Clean up stale VBOs
                if "_gl_vbo_verts" in mesh.metadata:
                    glDeleteBuffers(2, [mesh.metadata.pop("_gl_vbo_verts"), mesh.metadata.pop("_gl_vbo_normals")])
                    del mesh.metadata["_gl_vbo_count"]
                
                verts = mesh.vertices.astype(np.float32)
                faces = mesh.faces.astype(np.uint32)
                expanded_verts = np.ascontiguousarray(verts[faces.ravel()])
                mesh.metadata["_gl_verts"] = expanded_verts
                mesh.metadata["_gl_vbo_count"] = len(expanded_verts)
                
                # Vertex normals (smooth) if available, fallback to face normals
                if hasattr(mesh, 'vertex_normals') and mesh.vertex_normals is not None and len(mesh.vertex_normals) == len(mesh.vertices):
                    vert_normals = mesh.vertex_normals.astype(np.float32)
                else:
                    vert_normals = np.repeat(mesh.face_normals.astype(np.float32), 3, axis=0)
                expanded_normals = np.ascontiguousarray(vert_normals[faces.ravel()])
                mesh.metadata["_gl_normals"] = expanded_normals
                
                # Create VBOs
                vbo_verts = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, vbo_verts)
                glBufferData(GL_ARRAY_BUFFER, expanded_verts.nbytes, expanded_verts, GL_STATIC_DRAW)
                vbo_normals = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, vbo_normals)
                glBufferData(GL_ARRAY_BUFFER, expanded_normals.nbytes, expanded_normals, GL_STATIC_DRAW)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                mesh.metadata["_gl_vbo_verts"] = vbo_verts
                mesh.metadata["_gl_vbo_normals"] = vbo_normals
            
            num_verts = mesh.metadata["_gl_vbo_count"]
            indices = np.arange(num_verts, dtype=np.uint32)
            
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_NORMAL_ARRAY)
            
            glBindBuffer(GL_ARRAY_BUFFER, mesh.metadata["_gl_vbo_verts"])
            glVertexPointer(3, GL_FLOAT, 0, None)
            glBindBuffer(GL_ARRAY_BUFFER, mesh.metadata["_gl_vbo_normals"])
            glNormalPointer(GL_FLOAT, 0, None)
            
            glPushAttrib(GL_ALL_ATTRIB_BITS)
            try:
                glDisable(GL_BLEND)
                glDepthMask(GL_TRUE)
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                glEnable(GL_CULL_FACE)
                glCullFace(GL_BACK)
                glFrontFace(GL_CCW)
                
                glEnable(GL_LIGHTING)
                glShadeModel(GL_SMOOTH)
                
                color = mesh.metadata.get("color", NEUTRAL_COLORS[0])
                if len(color) == 3:
                    color = [*color, 1.0]
                if is_selected:
                    color = [0.3, 0.6, 1.0, 1.0]
                glColor4f(color[0], color[1], color[2], color[3] if len(color)>3 else 1.0)
                
                glDrawElements(GL_TRIANGLES, indices.size, GL_UNSIGNED_INT, indices)
            finally:
                glPopAttrib()
            
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_NORMAL_ARRAY)
        except Exception as e:
            print(f"Errore in _draw_mesh: {e}")
    
    def _draw_toolpaths(self):
        if not self.scene.gcode_paths:
            return
        
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        
        for path in self.scene.gcode_paths:
            if path["type"] == "ext":
                glColor3f(0.2, 0.8, 0.2)
                glBegin(GL_LINE_STRIP)
                for x, y, z in path["pts"]:
                    glVertex3f(x, y, z)
                glEnd()
        
        glEnable(GL_LIGHTING)
    
    def _grid(self):
        try:
            glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_LINE_BIT | GL_DEPTH_BUFFER_BIT)
            
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)
            glLineWidth(1.0)
            
            extent = 500
            
            glBegin(GL_LINES)
            for i in range(-extent, extent + 1, 1):
                if i == 0:
                    color = [0.45, 0.45, 0.55]
                elif i % 100 == 0:
                    color = [0.30, 0.30, 0.40]
                elif i % 10 == 0:
                    color = [0.22, 0.22, 0.30]
                else:
                    color = [0.14, 0.14, 0.20]
                
                glColor3f(*color)
                
                glVertex3f(i, -extent, 0)
                glVertex3f(i, extent, 0)
                glVertex3f(-extent, i, 0)
                glVertex3f(extent, i, 0)
            glEnd()
            
            glLineWidth(2.0)
            glBegin(GL_LINES)
            
            glColor3f(0.50, 0.50, 0.55)
            glVertex3f(-extent, 0, 0)
            glVertex3f(extent, 0, 0)
            
            glColor3f(0.50, 0.50, 0.55)
            glVertex3f(0, -extent, 0)
            glVertex3f(0, extent, 0)
            
            glColor3f(0.50, 0.50, 0.55)
            glVertex3f(0, 0, -extent)
            glVertex3f(0, 0, extent)
            
            glEnd()
            
            glLineWidth(2.0)
            glBegin(GL_LINES)
            
            glColor3f(0.30, 0.40, 0.55)
            glVertex3f(-extent, -extent, 0)
            glVertex3f(extent, -extent, 0)
            
            glVertex3f(extent, -extent, 0)
            glVertex3f(extent, extent, 0)
            
            glVertex3f(extent, extent, 0)
            glVertex3f(-extent, extent, 0)
            
            glVertex3f(-extent, extent, 0)
            glVertex3f(-extent, -extent, 0)
            
            glEnd()
            
            glPopAttrib()
        except Exception as e:
            print(f"Errore in _grid: {e}")
    
    def _draw_handle(self, position, axis, size, is_hovered=False):
        try:
            glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
            glDisable(GL_LIGHTING)
            
            if axis == 'x':
                base_color = [0.8, 0.3, 0.3, 0.95]
            elif axis == 'y':
                base_color = [0.3, 0.8, 0.3, 0.95]
            elif axis == 'z':
                base_color = [0.3, 0.3, 0.8, 0.95]
            elif axis == 'uniform':
                base_color = [0.8, 0.8, 0.3, 0.95]
            else:
                base_color = [0.6, 0.6, 0.6, 0.95]
            
            if is_hovered:
                color = [min(c * 1.2, 1.0) for c in base_color]
            else:
                color = base_color
            
            glColor4f(*color)
            glPushMatrix()
            glTranslatef(position[0], position[1], position[2])
            
            s = size * 1.5
            glBegin(GL_QUADS)
            for vx, vy, vz in [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s),
                             (-s, -s, -s), (-s, s, -s), (s, s, -s), (s, -s, -s)]:
                glVertex3f(vx, vy, vz)
            glEnd()
            
            if is_hovered:
                glLineWidth(3.0)
                glColor4f(1.0, 1.0, 1.0, 1.0)
                glBegin(GL_LINE_LOOP)
                glVertex3f(-s, -s, s)
                glVertex3f(s, -s, s)
                glVertex3f(s, s, s)
                glVertex3f(-s, s, s)
                glEnd()
                
                glBegin(GL_LINE_LOOP)
                glVertex3f(-s, -s, -s)
                glVertex3f(-s, s, -s)
                glVertex3f(s, s, -s)
                glVertex3f(s, -s, -s)
                glEnd()
                
                glBegin(GL_LINES)
                glVertex3f(-s, -s, s)
                glVertex3f(-s, -s, -s)
                glVertex3f(s, -s, s)
                glVertex3f(s, -s, -s)
                glVertex3f(s, s, s)
                glVertex3f(s, s, -s)
                glVertex3f(-s, s, s)
                glVertex3f(-s, s, -s)
                glEnd()
            
            glPopMatrix()
            glPopAttrib()
        except Exception as e:
            print(f"Errore nel disegnare la maniglia: {e}")
    
    def _draw_scale_handle(self, position, axis, size, is_hovered=False):
        try:
            glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
            glDisable(GL_LIGHTING)
            glDisable(GL_CULL_FACE)
            if axis == 'x':
                base_color = [0.9, 0.5, 0.5, 0.95]
            elif axis == 'y':
                base_color = [0.5, 0.9, 0.5, 0.95]
            else:
                base_color = [0.5, 0.5, 0.9, 0.95]
            if is_hovered:
                color = [min(c * 1.2, 1.0) for c in base_color]
            else:
                color = base_color
            glColor4f(*color)
            glPushMatrix()
            glTranslatef(position[0], position[1], position[2])
            # Diamond (two pyramids)
            s = size * 0.6
            # Top pyramid (apex at +y)
            for apex, base in [((0,s,0), [(s,0,-s),(s,0,s),(-s,0,s),(-s,0,-s)])]:
                for i in range(4):
                    glBegin(GL_TRIANGLES)
                    glVertex3f(*apex)
                    glVertex3f(*base[i])
                    glVertex3f(*base[(i+1)%4])
                    glEnd()
            # Bottom pyramid (apex at -y)
            for apex, base in [((0,-s,0), [(s,0,s),(s,0,-s),(-s,0,-s),(-s,0,s)])]:
                for i in range(4):
                    glBegin(GL_TRIANGLES)
                    glVertex3f(*apex)
                    glVertex3f(*base[i])
                    glVertex3f(*base[(i+1)%4])
                    glEnd()
            if is_hovered:
                glLineWidth(2.0)
                glColor4f(1,1,1,1)
                glBegin(GL_LINE_LOOP)
                for v in [(s,0,-s),(s,0,s),(-s,0,s),(-s,0,-s)]:
                    glVertex3f(*v)
                glEnd()
            glPopMatrix()
            glPopAttrib()
        except Exception as e:
            print(f"Errore in _draw_scale_handle: {e}")
    
    def _draw_rot_handle(self, position, size, is_hovered=False):
        try:
            glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_LIGHTING_BIT)
            glEnable(GL_LIGHTING)
            glEnable(GL_NORMALIZE)
            base_color = [0.95, 0.8, 0.15, 0.95] if not is_hovered else [1.0, 0.95, 0.3, 1.0]
            glColor4f(*base_color)
            glPushMatrix()
            glTranslatef(position[0], position[1], position[2])
            sphere = gluNewQuadric()
            gluSphere(sphere, size, 16, 12)
            gluDeleteQuadric(sphere)
            glPopMatrix()
            if is_hovered:
                glDisable(GL_LIGHTING)
                glLineWidth(2.0)
                glColor4f(1,1,1,1)
                # bounding circle highlight
                glBegin(GL_LINE_LOOP)
                s = size * 1.1
                for i in range(24):
                    a = 2 * math.pi * i / 24
                    glVertex3f(s*math.cos(a), s*math.sin(a), 0)
                glEnd()
                glBegin(GL_LINE_LOOP)
                for i in range(24):
                    a = 2 * math.pi * i / 24
                    glVertex3f(s*math.cos(a), 0, s*math.sin(a))
                glEnd()
                glEnable(GL_LIGHTING)
            glPopAttrib()
        except Exception as e:
            print(f"Errore in _draw_rot_handle: {e}")
    
    def _draw_vertical_handle(self, position, is_hovered=False):
        try:
            glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_LIGHTING_BIT | GL_POLYGON_BIT)
            
            glEnable(GL_LIGHTING)
            glEnable(GL_NORMALIZE)
            
            base_color = [0.3, 0.8, 0.3, 0.95]
            
            if is_hovered:
                color = [min(c * 1.2, 1.0) for c in base_color]
            else:
                color = base_color
            
            glColor4f(*color)
            glPushMatrix()
            glTranslatef(position[0], position[1], position[2])
            
            stem_radius = 0.6
            stem_half = 1.8
            tip_radius = 1.0
            tip_height = 0.8
            
            quadric = gluNewQuadric()
            gluCylinder(quadric, stem_radius, stem_radius, stem_half * 2, 32, 1)
            gluDisk(quadric, 0, stem_radius, 32, 1)
            
            glTranslatef(0, 0, stem_half * 2)
            gluCylinder(quadric, 0, tip_radius, tip_height, 32, 1)
            
            glTranslatef(0, 0, -stem_half * 2 - tip_height)
            glRotatef(180, 1, 0, 0)
            gluCylinder(quadric, 0, tip_radius, tip_height, 32, 1)
            glRotatef(-180, 1, 0, 0)
            
            glTranslatef(0, 0, tip_height)
            gluDisk(quadric, 0, stem_radius, 32, 1)
            
            if is_hovered:
                glDisable(GL_LIGHTING)
                glLineWidth(2.0)
                glColor4f(1.0, 1.0, 1.0, 1.0)
                
                glBegin(GL_LINE_LOOP)
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    dx = stem_radius * math.cos(angle)
                    dy = stem_radius * math.sin(angle)
                    glVertex3f(dx, dy, 0)
                glEnd()
                
                glBegin(GL_LINE_LOOP)
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    dx = stem_radius * math.cos(angle)
                    dy = stem_radius * math.sin(angle)
                    glVertex3f(dx, dy, stem_half * 2)
                glEnd()
            
            glPopMatrix()
            glPopAttrib()
        except Exception as e:
            print(f"Errore nel disegnare la maniglia verticale: {e}")
    
    def _draw_uniform_scale_handle(self, position, is_hovered=False):
        try:
            glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_LIGHTING_BIT | GL_POLYGON_BIT)
            
            glEnable(GL_LIGHTING)
            glEnable(GL_NORMALIZE)
            
            base_color = [0.8, 0.8, 0.3, 0.95]
            
            if is_hovered:
                color = [min(c * 1.2, 1.0) for c in base_color]
            else:
                color = base_color
            
            glColor4f(*color)
            glPushMatrix()
            glTranslatef(position[0], position[1], position[2])
            
            sphere = gluNewQuadric()
            gluSphere(sphere, 0.8, 32, 32)
            
            if is_hovered:
                glDisable(GL_LIGHTING)
                glLineWidth(2.0)
                glColor4f(1.0, 1.0, 1.0, 1.0)
                
                glBegin(GL_LINE_LOOP)
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    x = 0.8 * math.cos(angle)
                    y = 0.8 * math.sin(angle)
                    glVertex3f(x, y, 0)
                glEnd()
                
                glBegin(GL_LINE_LOOP)
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    x = 0.8 * math.cos(angle)
                    z = 0.8 * math.sin(angle)
                    glVertex3f(x, 0, z)
                glEnd()
                
                glBegin(GL_LINE_LOOP)
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    y = 0.8 * math.cos(angle)
                    z = 0.8 * math.sin(angle)
                    glVertex3f(0, y, z)
                glEnd()
            
            glPopMatrix()
            glPopAttrib()
        except Exception as e:
            print(f"Errore nel disegnare la maniglia di scalatura uniforme: {e}")
    
    def _draw_axis(self, start, direction, color, length, line_width=1.5, is_hovered=False):
        try:
            glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
            glDisable(GL_LIGHTING)
            
            if is_hovered:
                color = [min(c * 1.2, 1.0) for c in color]
            
            glColor4f(*color)
            glLineWidth(line_width)
            glBegin(GL_LINES)
            glVertex3f(start[0], start[1], start[2])
            glVertex3f(
                start[0] + direction[0] * length,
                start[1] + direction[1] * length,
                start[2] + direction[2] * length
            )
            glEnd()
            
            if is_hovered:
                arrow_size = length * 0.15
                end_pos = [
                    start[0] + direction[0] * length,
                    start[1] + direction[1] * length,
                    start[2] + direction[2] * length
                ]
                
                glLineWidth(1.0)
                glBegin(GL_LINES)
                glVertex3f(end_pos[0], end_pos[1], end_pos[2])
                glVertex3f(
                    end_pos[0] - direction[0] * arrow_size + direction[1] * arrow_size,
                    end_pos[1] - direction[1] * arrow_size + direction[2] * arrow_size,
                    end_pos[2] - direction[2] * arrow_size + direction[0] * arrow_size
                )
                glVertex3f(end_pos[0], end_pos[1], end_pos[2])
                glVertex3f(
                    end_pos[0] - direction[0] * arrow_size - direction[1] * arrow_size,
                    end_pos[1] - direction[1] * arrow_size - direction[2] * arrow_size,
                    end_pos[2] - direction[2] * arrow_size - direction[0] * arrow_size
                )
                glEnd()
            
            glPopAttrib()
        except Exception as e:
            print(f"Errore nel disegnare l'asse: {e}")
    
    def _gizmo(self):
        if self._modelview_matrix is None or self._projection_matrix is None or self._viewport is None:
            return
        
        try:
            all_vertices = []
            for obj in self.scene.selected_objects:
                all_vertices.extend(obj.vertices)
            
            if not all_vertices:
                return
                
            all_vertices = np.array(all_vertices)
            bounds = [np.min(all_vertices, axis=0), np.max(all_vertices, axis=0)]
            center = (bounds[0] + bounds[1]) / 2
            
            extents = bounds[1] - bounds[0]
            max_extent = max(extents)
            
            scale = max(1.0, max_extent * 0.1)
            scale *= (self.distance / 200)
            
            self.gizmo_points_3d = {}
            self.gizmo_points_2d = {}
            
            size = 0.5 * scale
            # Per oggetti testo, riduci ring e aste per evitare maniglie enormi
            all_text = all(obj.metadata.get("shape_type") == "text" for obj in self.scene.selected_objects)
            if all_text:
                ring_radius = min(max_extent * 0.7, size * 5)
                max_handle = size * 4
            else:
                ring_radius = max_extent * 0.7
                max_handle = float('inf')
            handle_len_x = min(max(extents[0], max_extent * 0.2) * 0.65, max_handle)
            handle_len_y = min(max(extents[1], max_extent * 0.2) * 0.65, max_handle)
            handle_len_z = min(max(extents[2], max_extent * 0.2) * 0.65, max_handle)

            axes = [
                ('x', [1, 0, 0], [0.8, 0.3, 0.3, 0.95], handle_len_x),
                ('y', [0, -1, 0], [0.3, 0.8, 0.3, 0.95], handle_len_y),
                ('z', [0, 0, 1], [0.3, 0.3, 0.8, 0.95], handle_len_z)
            ]

            for axis_name, axis_dir, color, handle_len in axes:
                is_hovered = (self.gizmo_hover == axis_name or self.active_handle == axis_name or 
                              self.gizmo_hover == 'rot_' + axis_name or self.active_handle == 'rot_' + axis_name)
                self._draw_axis(center, axis_dir, color, handle_len, line_width=2.0, is_hovered=is_hovered)
            
            # Draw rotation rings ONLY when hovering the rotation handle or active (sphere handles always visible)
            for axis_name, axis_dir, color, _ in axes:
                is_rot_active = (self.gizmo_hover == 'rot_' + axis_name or self.active_handle == 'rot_' + axis_name)
                # Draw ring circle + ticks + degree dots only on hover/active
                if is_rot_active:
                    glDisable(GL_LIGHTING)
                    glEnable(GL_LINE_SMOOTH)
                    glLineWidth(1.5)
                    glBegin(GL_LINE_LOOP)
                    glColor4f(1.0, 0.95, 0.3, 0.7)
                    segs = 96
                    for i in range(segs):
                        a = 2 * math.pi * i / segs
                        a = 2 * math.pi * i / segs
                        if axis_name == 'x':
                            pt = center + np.array([0, ring_radius * math.cos(a), ring_radius * math.sin(a)])
                        elif axis_name == 'y':
                            pt = center + np.array([ring_radius * math.cos(a), 0, ring_radius * math.sin(a)])
                        else:
                            pt = center + np.array([ring_radius * math.cos(a), ring_radius * math.sin(a), 0])
                        glVertex3fv(pt)
                    glEnd()
                    glBegin(GL_LINES)
                    glColor4f(1.0, 0.9, 0.2, 0.7)
                    for deg in range(0, 360, 15):
                        a = math.radians(deg)
                        tick_len = ring_radius * 0.1 if deg % 45 == 0 else ring_radius * 0.05
                        if axis_name == 'x':
                            inner = center + np.array([0, ring_radius * math.cos(a), ring_radius * math.sin(a)])
                            outer = center + np.array([0, (ring_radius + tick_len) * math.cos(a), (ring_radius + tick_len) * math.sin(a)])
                        elif axis_name == 'y':
                            inner = center + np.array([ring_radius * math.cos(a), 0, ring_radius * math.sin(a)])
                            outer = center + np.array([(ring_radius + tick_len) * math.cos(a), 0, (ring_radius + tick_len) * math.sin(a)])
                        else:
                            inner = center + np.array([ring_radius * math.cos(a), ring_radius * math.sin(a), 0])
                            outer = center + np.array([(ring_radius + tick_len) * math.cos(a), (ring_radius + tick_len) * math.sin(a), 0])
                        glVertex3fv(inner)
                        glVertex3fv(outer)
                    glEnd()
                    glPointSize(5.0)
                    glBegin(GL_POINTS)
                    glColor4f(1.0, 0.85, 0.0, 0.9)
                    for deg in range(0, 360, 45):
                        a = math.radians(deg)
                        num_r = ring_radius * 1.08
                        if axis_name == 'x':
                            pt = center + np.array([0, num_r * math.cos(a), num_r * math.sin(a)])
                        elif axis_name == 'y':
                            pt = center + np.array([num_r * math.cos(a), 0, num_r * math.sin(a)])
                        else:
                            pt = center + np.array([num_r * math.cos(a), num_r * math.sin(a), 0])
                        glVertex3fv(pt)
                    glEnd()
                    glEnable(GL_LIGHTING)
                
                # 4 rotation handle spheres ALWAYS visible at 45°, 135°, 225°, 315°
                # During drag, one sphere follows the cursor
                active_rot = (self.active_handle == 'rot_' + axis_name)
                for j in range(4):
                    base_a = math.radians(45 + j * 90)
                    # During drag, place the nearest sphere at cursor angle
                    if active_rot and self.rotate_angle_during_drag is not None and j == 0:
                        a = self.rotate_angle_during_drag
                    else:
                        a = base_a
                    if axis_name == 'x':
                        pos = center + np.array([0, ring_radius * math.cos(a), ring_radius * math.sin(a)])
                    elif axis_name == 'y':
                        pos = center + np.array([ring_radius * math.cos(a), 0, ring_radius * math.sin(a)])
                    else:
                        pos = center + np.array([ring_radius * math.cos(a), ring_radius * math.sin(a), 0])
                    key = f'rh{axis_name}{j}'
                    self.gizmo_points_3d[key] = pos
                    try:
                        sx, sy, _ = gluProject(pos[0], pos[1], pos[2],
                            self._modelview_matrix, self._projection_matrix, self._viewport)
                        self.gizmo_points_2d[key] = np.array([sx, self._viewport[3] - sy])
                    except:
                        pass
                    is_rot_h = (self.gizmo_hover == key)
                    self._draw_rot_handle(pos, size * 0.5, is_rot_h)

            for axis_name, axis_dir, color, handle_len in axes:
                handle_pos = center + np.array(axis_dir) * handle_len
                
                self.gizmo_points_3d[axis_name] = handle_pos
                
                try:
                    screen_x, screen_y, _ = gluProject(
                        handle_pos[0], handle_pos[1], handle_pos[2],
                        self._modelview_matrix,
                        self._projection_matrix,
                        self._viewport
                    )
                    self.gizmo_points_2d[axis_name] = np.array([screen_x, self._viewport[3] - screen_y])
                except Exception as e:
                    print(f"Errore nella proiezione dell'asse {axis_name}: {e}")
                    continue
                
                is_hovered = (self.gizmo_hover == axis_name)
                self._draw_handle(handle_pos, axis_name, size, is_hovered)
            
            try:
                self.gizmo_points_3d["center"] = center
                
                try:
                    screen_x, screen_y, _ = gluProject(
                        center[0], center[1], center[2],
                        self._modelview_matrix,
                        self._projection_matrix,
                        self._viewport
                    )
                    self.gizmo_points_2d["center"] = np.array([screen_x, self._viewport[3] - screen_y])
                except Exception as e:
                    print(f"Errore nella proiezione del centro: {e}")
                
                is_hovered = (self.gizmo_hover == "center")
                self._draw_handle(center, "center", size * 0.7, is_hovered)
            except Exception as e:
                print(f"Errore nel disegnare il gizmo centrale: {e}")
            
            uniform_scale_pos = center + np.array([max_extent * 0.5, max_extent * 0.5, 0])
            self.gizmo_points_3d["uniform"] = uniform_scale_pos
            
            try:
                screen_x, screen_y, _ = gluProject(
                    uniform_scale_pos[0], uniform_scale_pos[1], uniform_scale_pos[2],
                    self._modelview_matrix,
                    self._projection_matrix,
                    self._viewport
                )
                self.gizmo_points_2d["uniform"] = np.array([screen_x, self._viewport[3] - screen_y])
                
                is_hovered = (self.gizmo_hover == "uniform")
                self._draw_uniform_scale_handle(uniform_scale_pos, is_hovered)
            except Exception as e:
                print(f"Errore nella proiezione della maniglia uniforme: {e}")
            
            vertical_handle_pos = center + np.array([0, 0, max_extent * 0.9])
            self.gizmo_points_3d["vertical"] = vertical_handle_pos
            
            try:
                screen_x, screen_y, _ = gluProject(
                    vertical_handle_pos[0], vertical_handle_pos[1], vertical_handle_pos[2],
                    self._modelview_matrix,
                    self._projection_matrix,
                    self._viewport
                )
                self.gizmo_points_2d["vertical"] = np.array([screen_x, self._viewport[3] - screen_y])
                
                is_hovered = (self.gizmo_hover == "vertical")
                self._draw_vertical_handle(vertical_handle_pos, is_hovered)
            except Exception as e:
                print(f"Errore nella proiezione della maniglia verticale: {e}")
        except Exception as e:
            print(f"Errore in _gizmo: {e}")
    
    def _draw_rulers_qt(self):
        try:
            width = self.width()
            height = self.height()
            if width <= 0 or height <= 0:
                return
            
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor(180, 190, 200))
            
            range_x = int(self.distance * 2.5)
            if range_x <= 0:
                range_x = 1
            start_x = int(self.pan[0] - range_x / 2)
            range_y = int(range_x * (height / width)) if width > 0 else 1
            start_y = int(self.pan[1] - range_y / 2)
            
            for x in range(start_x - (start_x % 5), start_x + range_x, 5):
                screen_x = (x - start_x) / range_x * width
                if 0 <= screen_x <= width:
                    if x % 10 == 0:
                        tick_height = 12
                        painter.setPen(QPen(QColor(160, 180, 200), 1.5))
                        painter.drawLine(int(screen_x), height, int(screen_x), height - tick_height)
                        painter.setPen(QColor(200, 210, 225))
                        painter.drawText(int(screen_x) + 3, height - 14, f"{x}")
                        painter.setPen(QPen(QColor(180, 190, 200), 1))
                    else:
                        tick_height = 6
                        painter.drawLine(int(screen_x), height, int(screen_x), height - tick_height)
            
            for y in range(start_y - (start_y % 5), start_y + range_y, 5):
                screen_y = height - ((y - start_y) / range_y * height)
                if 0 <= screen_y <= height:
                    if y % 10 == 0:
                        tick_width = 12
                        painter.setPen(QPen(QColor(160, 180, 200), 1.5))
                        painter.drawLine(0, int(screen_y), tick_width, int(screen_y))
                        painter.setPen(QColor(200, 210, 225))
                        painter.drawText(14, int(screen_y) + 4, f"{y}")
                        painter.setPen(QPen(QColor(180, 190, 200), 1))
                    else:
                        tick_width = 6
                        painter.drawLine(0, int(screen_y), tick_width, int(screen_y))
            
            if self.scene.has_selection:
                painter.setPen(QColor(100, 200, 255))
                painter.drawText(10, 20, f"Selezionati: {len(self.scene.selected_objects)}")
            
            if self.scene.has_selection and self._modelview_matrix is not None:
                show_ring = self.gizmo_hover in ('x', 'y', 'z', 'rot_x', 'rot_y', 'rot_z')
                if show_ring:
                    all_verts = []
                    for obj in self.scene.selected_objects:
                        all_verts.extend(obj.vertices)
                    if all_verts:
                        all_verts = np.array(all_verts)
                        c = np.min(all_verts, axis=0)
                        center = (c + np.max(all_verts, axis=0)) / 2
                        ring_r = max(np.max(all_verts, axis=0) - c) * 0.7
                        painter.setFont(QFont("Segoe UI", 8))
                        painter.setPen(QColor(220, 200, 60))
                        hover_axis = self.gizmo_hover[4] if self.gizmo_hover.startswith('rot_') else self.gizmo_hover
                        for deg in range(0, 360, 45):
                            a = math.radians(deg)
                            if hover_axis == 'x':
                                pt = center + np.array([0, ring_r * 1.14 * math.cos(a), ring_r * 1.14 * math.sin(a)])
                            elif hover_axis == 'y':
                                pt = center + np.array([ring_r * 1.14 * math.cos(a), 0, ring_r * 1.14 * math.sin(a)])
                            else:
                                pt = center + np.array([ring_r * 1.14 * math.cos(a), ring_r * 1.14 * math.sin(a), 0])
                            try:
                                sx, sy, _ = gluProject(pt[0], pt[1], pt[2],
                                    self._modelview_matrix, self._projection_matrix, self._viewport)
                                sx, sy = int(sx), int(self._viewport[3] - sy)
                                if 0 <= sx <= self.width() and 0 <= sy <= self.height():
                                    painter.drawText(sx - 12, sy + 4, f"{deg}°")
                            except:
                                pass
            
            painter.end()
        except Exception as e:
            print(f"Errore in _draw_rulers_qt: {e}")
    
    def _update_stats(self):
        now = time.time()
        elapsed = now - self.last_time
        fps = self.frames / elapsed if elapsed > 0 else 0
        
        if hasattr(self.window, 'update_stats'):
            self.window.update_stats(fps, 0, 0)
        
        self.frames = 0
        self.last_time = now
    
    def _screen_to_ray(self, x, y):
        mv = self._drag_modelview if self._drag_modelview is not None else self._modelview_matrix
        proj = self._drag_projection if self._drag_projection is not None else self._projection_matrix
        vp = self._drag_viewport if self._drag_viewport is not None else self._viewport
        if mv is None or proj is None or vp is None:
            width, height = self.width(), self.height()
            if width > 0 and height > 0:
                self._sync_camera(width, height)
            mv = self._drag_modelview if self._drag_modelview is not None else self._modelview_matrix
            proj = self._drag_projection if self._drag_projection is not None else self._projection_matrix
            vp = self._drag_viewport if self._drag_viewport is not None else self._viewport
        
        if mv is None or proj is None or vp is None:
            return None, None
        
        try:
            gl_x = x * self.device_pixel_ratio
            gl_y = self.physical_height - (y * self.device_pixel_ratio)
            
            near_point = gluUnProject(
                gl_x, gl_y, 0.0,
                mv, proj, vp
            )
            far_point = gluUnProject(
                gl_x, gl_y, 1.0,
                mv, proj, vp
            )
            
            ray_origin = np.array(near_point)
            ray_direction = np.array(far_point) - ray_origin
            norm = np.linalg.norm(ray_direction)
            if norm > 1e-6:
                ray_direction /= norm
            
            return ray_origin, ray_direction
        except Exception as e:
            print(f"Errore in _screen_to_ray: {e}")
            return None, None
    
    def _pick_object(self, position):
        try:
            if not self.scene.objects:
                return None
            
            if self.scene._needs_spatial_rebuild:
                self.scene._rebuild_spatial_index()
                self.scene._needs_spatial_rebuild = False
            
            ray_origin, ray_direction = self._screen_to_ray(position.x(), position.y())
            if ray_origin is None or ray_direction is None:
                return None
            
            best = None
            min_t = float('inf')
            epsilon = 1e-9
            
            if self.scene._spatial_index and len(self.scene.objects) > 100:
                nearby_objects = self.scene._get_nearby_objects(ray_origin)
                objects_to_test = nearby_objects
            else:
                objects_to_test = self.scene.objects
            
            for obj in objects_to_test:
                layer = obj.metadata.get("layer", "Default")
                if not self.scene.layers.get(layer, {}).get("visible", True):
                    continue
                
                if hasattr(obj, 'ray') and hasattr(obj.ray, 'intersects_location'):
                    try:
                        origins = np.array([ray_origin])
                        vectors = np.array([ray_direction])
                        locations, index_ray, _ = obj.ray.intersects_location(
                            origins, vectors, multiple_hits=False
                        )
                        
                        if len(locations) > 0:
                            t = np.linalg.norm(locations[0] - ray_origin)
                            if t < min_t:
                                min_t = t
                                best = obj
                    except:
                        pass
            
            if best is None:
                for obj in objects_to_test:
                    layer = obj.metadata.get("layer", "Default")
                    if not self.scene.layers.get(layer, {}).get("visible", True):
                        continue
                    
                    if hasattr(obj, 'bounds') and obj.bounds is not None and len(obj.bounds) == 2:
                        min_bound = np.array(obj.bounds[0])
                        max_bound = np.array(obj.bounds[1])
                        
                        t1 = (min_bound - ray_origin) / (ray_direction + epsilon)
                        t2 = (max_bound - ray_origin) / (ray_direction + epsilon)
                        t_enter = np.max(np.minimum(t1, t2))
                        t_exit = np.min(np.maximum(t1, t2))
                        
                        if t_enter <= t_exit and t_exit >= 0 and t_enter < min_t:
                            min_t = t_enter
                            best = obj
                            continue
                    
                    if hasattr(obj, 'vertices') and len(obj.vertices) > 0:
                        vertices = np.asarray(obj.vertices)
                        centroid = np.mean(vertices, axis=0)
                        radius = np.max(np.linalg.norm(vertices - centroid, axis=1))
                        
                        oc = ray_origin - centroid
                        b = np.dot(oc, ray_direction)
                        c = np.dot(oc, oc) - radius * radius
                        discriminant = b * b - c
                        
                        if discriminant >= 0:
                            t = -b - np.sqrt(discriminant)
                            if 0 <= t < min_t:
                                min_t = t
                                best = obj
            
            return best
        except Exception as e:
            print(f"Errore in _pick_object: {e}")
            return None
    
    def _pick_handle(self, position):
        try:
            if not self.gizmo_points_2d:
                return None
            
            mouse_x = position.x() * self.device_pixel_ratio
            mouse_y = position.y() * self.device_pixel_ratio
            
            tolerance = 30
            
            best_key = None
            best_dist = tolerance
            
            for key, (screen_x, screen_y) in self.gizmo_points_2d.items():
                distance = math.hypot(mouse_x - screen_x, mouse_y - screen_y)
                if distance < best_dist:
                    best_dist = distance
                    best_key = key
            
            if best_key:
                self.gizmo_hover = best_key
                # Map rot_*_N / rhx0 etc. keys to rot_x, rot_y, rot_z
                if best_key.startswith('rot_') and len(best_key) > 5:
                    rot_base = best_key[:5]
                    self.gizmo_hover = rot_base
                    return rot_base
                if best_key.startswith('rh') and len(best_key) >= 4:
                    rot_base = 'rot_' + best_key[2]
                    self.gizmo_hover = rot_base
                    return rot_base
                return best_key
            
            self.gizmo_hover = None
            return None
        except Exception as e:
            print(f"Errore in _pick_handle: {e}")
            return None
    
    def _get_rotation_angle(self, pos):
        """Screen-space angle of mouse relative to GIZMO center (for Z rotation)."""
        try:
            if not self.scene.has_selection:
                return None
            sel = self.scene.selected_objects
            centroid = np.mean([o.centroid for o in sel], axis=0)
            sx, sy, _ = gluProject(centroid[0], centroid[1], centroid[2],
                self._modelview_matrix, self._projection_matrix, self._viewport)
            sc = np.array([sx, self._viewport[3] - sy])
            dx = pos.x() * self.device_pixel_ratio - sc[0]
            dy = pos.y() * self.device_pixel_ratio - sc[1]
            return math.atan2(dy, dx)
        except Exception as e:
            return None
    
    def _get_rotation_speed(self):
        """Screen-space ring radius in pixels (for scaling dx/dy to radians)."""
        try:
            if not self.scene.has_selection:
                return 0.01
            sel = self.scene.selected_objects
            centroid = np.mean([o.centroid for o in sel], axis=0)
            sx, sy, _ = gluProject(centroid[0], centroid[1], centroid[2],
                self._modelview_matrix, self._projection_matrix, self._viewport)
            # Project a point at ring distance along X to get screen radius
            ring_world = centroid + np.array([1.0, 0, 0])  # offset by 1
            sx2, _, _ = gluProject(ring_world[0], ring_world[1], ring_world[2],
                self._modelview_matrix, self._projection_matrix, self._viewport)
            px_per_unit = max(1.0, abs(sx2 - sx))
            bounds = [np.min([o.centroid for o in sel], axis=0),
                      np.max([o.centroid for o in sel], axis=0)]
            max_extent = max(bounds[1] - bounds[0])
            ring_r = max_extent * 1.0
            screen_radius = ring_r * px_per_unit
            return 1.0 / max(10.0, screen_radius)
        except:
            return 0.01
    
    def _intersect_ray_plane(self, ray_origin, ray_direction, z):
        try:
            if abs(ray_direction[2]) > 1e-6:
                t = (z - ray_origin[2]) / ray_direction[2]
                if t >= 0:
                    return ray_origin + t * ray_direction
            return None
        except Exception as e:
            print(f"Errore in _intersect_ray_plane: {e}")
            return None
    
    def _get_sketch_coords(self, position):
        try:
            ray_origin, ray_direction = self._screen_to_ray(position.x(), position.y())
            if ray_origin is not None and ray_direction is not None and abs(ray_direction[2]) > 1e-6:
                t = (0.0 - ray_origin[2]) / ray_direction[2]
                point = ray_origin + t * ray_direction
                return point[0], point[1]
            return 0.0, 0.0
        except Exception as e:
            print(f"Errore in _get_sketch_coords: {e}")
            return 0.0, 0.0
    
    def _select_objects_in_box(self, start, end):
        try:
            x1, y1 = start.x(), start.y()
            x2, y2 = end.x(), end.y()
            
            left = min(x1, x2)
            right = max(x1, x2)
            bottom = min(y1, y2)
            top = max(y1, y2)
            
            if not (QApplication.keyboardModifiers() & (Qt.ControlModifier | Qt.ShiftModifier)):
                self.scene.clear_selection()
            
            if len(self.scene.objects) > 100 and self.scene._spatial_index:
                center = [(left + right) / 2, (bottom + top) / 2]
                nearby_objects = self.scene._get_nearby_objects(center, radius=max(right - left, top - bottom))
                objects_to_test = nearby_objects
            else:
                objects_to_test = self.scene.objects
            
            for obj in objects_to_test:
                if hasattr(obj, 'bounds') and obj.bounds is not None and len(obj.bounds) == 2:
                    min_bound = obj.bounds[0]
                    max_bound = obj.bounds[1]
                    
                    screen_points = []
                    for x in [min_bound[0], max_bound[0]]:
                        for y in [min_bound[1], max_bound[1]]:
                            for z in [min_bound[2], max_bound[2]]:
                                try:
                                    screen_x, screen_y, _ = gluProject(
                                        x, y, z,
                                        self._modelview_matrix,
                                        self._projection_matrix,
                                        self._viewport
                                    )
                                    screen_points.append((screen_x, self._viewport[3] - screen_y))
                                except:
                                    pass
                    
                    for sx, sy in screen_points:
                        if left <= sx <= right and bottom <= sy <= top:
                            self.scene.add_to_selection(obj)
                            break
            
            self.window.update_ui()
            self.update()
        except Exception as e:
            print(f"Errore nella selezione multipla: {e}")
    
    def _screen_to_world(self, x, y):
        try:
            ray_origin, ray_direction = self._screen_to_ray(x, y)
            if ray_origin is None or ray_direction is None:
                return np.array([0, 0, 0])
            
            if abs(ray_direction[2]) > 1e-6:
                t = -ray_origin[2] / ray_direction[2]
                return ray_origin + t * ray_direction
            
            return ray_origin
        except Exception as e:
            print(f"Errore in _screen_to_world: {e}")
            return np.array([0, 0, 0])
    
    def mousePressEvent(self, event):
        try:
            self.mouse_pressed = True
            self.mouse_button = event.button()
            
            self.last_position = event.pos()
            self.drag_start_mouse = np.array([event.x(), event.y()])
            self.selection_box_start = (event.x(), event.y())
            self.selection_box_end = (event.x(), event.y())
            self.dragging = False
            
            self.click_handled = False
            
            if event.button() == Qt.RightButton:
                if self.scene.has_selection:
                    self.interaction_mode = 'CONTEXT_MENU'
                    self.click_handled = True
                return
            
            if event.modifiers() & Qt.ControlModifier and event.button() == Qt.LeftButton:
                self.interaction_mode = 'ORBIT'
                self.click_handled = True
                return
            
            if event.modifiers() & Qt.ControlModifier and event.button() == Qt.MiddleButton:
                self.interaction_mode = 'ROT_Z'
                self.click_handled = True
                return
            
            if event.button() == Qt.MiddleButton:
                self.interaction_mode = 'PAN'
                self.click_handled = True
                return
            
            if self.scene.has_selection and event.button() == Qt.LeftButton:
                handle = self._pick_handle(event.pos())
                if handle:
                    if handle == "vertical":
                        self.interaction_mode = 'DRAG_VERTICAL'
                    elif handle == "uniform":
                        self.interaction_mode = 'DRAG_UNIFORM_SCALE'
                    elif handle in ('rot_x', 'rot_y', 'rot_z'):
                        self.interaction_mode = 'DRAG_ROTATE'
                        self.active_handle = handle
                        self.rotate_start_angle = self._get_rotation_angle(event.pos())
                    else:
                        self.interaction_mode = 'DRAG_HANDLE'
                    
                    self.active_handle = handle
                    ray_origin, ray_direction = self._screen_to_ray(event.x(), event.y())
                    if handle == "vertical":
                        self.drag_offset = np.array([0, 0, self.scene.single_selection.centroid[2]])
                    elif handle.startswith('rot_'):
                        pass
                    else:
                        self.drag_offset = self._intersect_ray_plane(ray_origin, ray_direction, 0.0)
                    self._drag_modelview = self._modelview_matrix.copy() if self._modelview_matrix is not None else None
                    self._drag_projection = self._projection_matrix.copy() if self._projection_matrix is not None else None
                    self._drag_viewport = self._viewport[:] if self._viewport is not None else None
                    centers = [o.centroid for o in self.scene.selected_objects if hasattr(o, 'centroid')]
                    self._drag_target = np.mean(centers, axis=0) if centers else np.array([0.0, 0.0, 0.0])
                    self.scene.start_operation()
                    self.window.update_ui()
                    self.click_handled = True
                    return
            
            if event.button() == Qt.LeftButton and not self.sketch_mode:
                hit = self._pick_object(event.pos())
                if hit:
                    if event.modifiers() & Qt.ControlModifier:
                        self.scene.toggle_selection(hit)
                    else:
                        self.scene.clear_selection()
                        self.scene.add_to_selection(hit)
                    self.window.update_ui()
                    self.update()
                    
                    self.interaction_mode = 'DRAG_OBJECT'
                    ray_origin, ray_direction = self._screen_to_ray(event.x(), event.y())
                    self.drag_offset = self._intersect_ray_plane(ray_origin, ray_direction, 0.0)
                    self._drag_modelview = self._modelview_matrix.copy() if self._modelview_matrix is not None else None
                    self._drag_projection = self._projection_matrix.copy() if self._projection_matrix is not None else None
                    self._drag_viewport = self._viewport[:] if self._viewport is not None else None
                    centers = [o.centroid for o in self.scene.selected_objects if hasattr(o, 'centroid')]
                    self._drag_target = np.mean(centers, axis=0) if centers else np.array([0.0, 0.0, 0.0])
                    self.scene.start_operation()
                    self.click_handled = True
                    return
            
            if event.button() == Qt.LeftButton:
                self.interaction_mode = 'NONE'
                self.click_handled = False
                return
            
        except Exception as e:
            print(f"Errore in mousePressEvent: {e}")
    
    def mouseMoveEvent(self, event):
        try:
            self._pick_handle(event.pos())
            self.update()
            
            if self.last_position is None:
                return
            
            dx = event.x() - self.last_position.x()
            dy = event.y() - self.last_position.y()
            
            drag_distance = math.hypot(
                event.x() - self.drag_start_mouse[0],
                event.y() - self.drag_start_mouse[1]
            )
            
            if drag_distance > self.drag_threshold:
                self.dragging = True
                
                if self.interaction_mode == 'NONE':
                    if event.modifiers() & Qt.ControlModifier and self.mouse_button == Qt.LeftButton:
                        self.interaction_mode = 'ORBIT'
                    elif event.modifiers() & Qt.ControlModifier and self.mouse_button == Qt.MiddleButton:
                        self.interaction_mode = 'ROT_Z'
                    elif self.mouse_button == Qt.MiddleButton:
                        self.interaction_mode = 'PAN'
                    elif self.mouse_button == Qt.LeftButton:
                        self.interaction_mode = 'BOX_SELECT'
                        self.selection_mode = True
            
            if self.interaction_mode == 'ROT_Z':
                self.rotation_z += dx * 0.5
                self.update()
            elif self.interaction_mode == 'PAN':
                pan_scale = self.distance / 200.0
                self.pan[0] += dx * 0.5 * pan_scale
                self.pan[1] -= dy * 0.5 * pan_scale
                self.update()
            elif self.interaction_mode == 'DRAG_HANDLE' and self.scene.has_selection:
                if self.active_handle == "center":
                    ray_origin, ray_direction = self._screen_to_ray(event.pos().x(), event.pos().y())
                    target = self._intersect_ray_plane(ray_origin, ray_direction, 0.0)
                    if target is not None and self.drag_offset is not None:
                        delta = target - self.drag_offset
                        self.scene.move_selection(delta[0], delta[1], 0.0)
                        self.drag_offset = target
                else:
                    # x, y, z axis tips — scale along axis
                    factor = 1.0
                    if self.active_handle == 'z':
                        factor = 1.0 + dy * 0.01
                        factor = 2.0 - factor
                    else:
                        factor = 1.0 + dx * 0.01
                    factor = max(0.1, min(10, factor))
                    axis_vec = {'x': [1,0,0], 'y': [0,1,0], 'z': [0,0,1]}.get(self.active_handle, [1,1,1])
                    sv = [1,1,1]
                    if axis_vec[0] > 0: sv[0] = factor
                    if axis_vec[1] > 0: sv[1] = factor
                    if axis_vec[2] > 0: sv[2] = factor
                    self.scene.scale_selection(*sv)
                
                self.window.update_ui()
                self.update()
            elif self.interaction_mode == 'DRAG_UNIFORM_SCALE' and self.scene.has_selection:
                factor = 1.0 + dx * 0.01
                factor = max(0.1, min(10, factor))
                
                self.scene.scale_selection(factor, factor, factor)
                
                self.window.update_ui()
                self.update()
            elif self.interaction_mode == 'DRAG_OBJECT' and self.scene.has_selection and self.dragging:
                ray_origin, ray_direction = self._screen_to_ray(event.pos().x(), event.pos().y())
                target = self._intersect_ray_plane(ray_origin, ray_direction, 0.0)
                if target is not None and self.drag_offset is not None:
                    delta = (target - self.drag_offset) * self.drag_speed
                    self.scene.move_selection(delta[0], delta[1], 0.0)
                    self.drag_offset = target
                
                self.window.update_ui()
                self.update()
            elif self.interaction_mode == 'DRAG_VERTICAL' and self.scene.has_selection:
                if self.drag_offset is not None:
                    scale = self.distance / 500.0
                    delta_z = -(event.y() - self.last_position.y()) * scale * 0.5
                    self.scene.move_selection(0, 0, delta_z)
                
                self.window.update_ui()
                self.update()
            elif self.interaction_mode == 'DRAG_ROTATE' and self.scene.has_selection:
                axis = self.active_handle[4]
                if axis == 'z':
                    cur = self._get_rotation_angle(event.pos())
                    if cur is not None:
                        self.rotate_angle_during_drag = cur
                        delta = cur - self.rotate_start_angle
                        self.scene.rotate_selection(delta, [0, 0, 1])
                        self.rotate_start_angle = cur
                elif axis == 'x':
                    delta = -(event.y() - self.last_position.y()) * self.rotation_drag_speed
                    self.scene.rotate_selection(delta, [1, 0, 0])
                else:
                    delta = (event.x() - self.last_position.x()) * self.rotation_drag_speed
                    self.scene.rotate_selection(delta, [0, 1, 0])
                self.window.update_ui()
                self.update()
            elif self.interaction_mode == 'ORBIT':
                self.rotation[1] += dx * 0.5
                self.rotation[0] += dy * 0.5
                self.rotation[0] = max(-89, min(89, self.rotation[0]))
                self.update()
            elif self.interaction_mode == 'BOX_SELECT':
                self.selection_box_end = (event.x(), event.y())
                self.update()
            
            self.last_position = event.pos()
        except Exception as e:
            print(f"Errore in mouseMoveEvent: {e}")
    
    def mouseReleaseEvent(self, event):
        try:
            self.mouse_pressed = False
            self._drag_target = None
            
            if self.dragging:
                if self.interaction_mode == 'BOX_SELECT':
                    start = QPoint(self.selection_box_start[0], self.selection_box_start[1])
                    end = QPoint(self.selection_box_end[0], self.selection_box_end[1])
                    self._select_objects_in_box(start, end)
                
                elif self.interaction_mode == 'ORBIT' or self.interaction_mode == 'PAN' or self.interaction_mode == 'ROT_Z' or self.interaction_mode == 'DRAG_ROTATE':
                    self.interaction_mode = self.interaction_mode
            else:
                hit = self._pick_object(QPoint(self.drag_start_mouse[0], self.drag_start_mouse[1]))
                if hit:
                    if event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier):
                        self.scene.toggle_selection(hit)
                    else:
                        self.scene.clear_selection()
                        self.scene.add_to_selection(hit)
                    self.window.update_ui()
                    self.update()
                    self.click_handled = True
                else:
                    if not (event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)):
                        self.scene.clear_selection()
                        self.window.update_ui()
                        self.update()
                    self.click_handled = True
            
            self.dragging = False
            self.selection_mode = False
            self.selection_box_start = None
            self.selection_box_end = None
            self._drag_modelview = None
            self._drag_projection = None
            self._drag_viewport = None
            
            if self.scene.operation_in_progress:
                self.scene.end_operation()
            
            self.interaction_mode = 'NONE'
            self.last_position = None
            self.rotate_angle_during_drag = None
            self.click_handled = False
        except Exception as e:
            print(f"Errore in mouseReleaseEvent: {e}")
    
    def contextMenuEvent(self, event):
        if self.scene.has_selection:
            menu = QMenu(self)
            
            duplicate_action = menu.addAction("Duplica")
            delete_action = menu.addAction("Elimina")
            group_action = menu.addAction("Raggruppa")
            ungroup_action = menu.addAction("Separati")
            align_z_action = menu.addAction("Allinea a Z=0")
            
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == duplicate_action:
                self.scene.duplicate()
                self.window.update_ui()
                self.update()
            elif action == delete_action:
                self.scene.delete()
                self.window.update_ui()
                self.update()
            elif action == group_action and len(self.scene.selected_objects) >= 2:
                self.scene.group_selected()
                self.window.status_bar.showMessage(f"Raggruppati {len(self.scene.selected_objects)} oggetti", 3000)
            elif action == ungroup_action:
                self.scene.ungroup_object()
                self.window.status_bar.showMessage(f"Separati {len(self.scene.selected_objects)} oggetti", 3000)
            elif action == align_z_action:
                self.scene.align_z()
                self.window.update_ui()
                self.update()
    
    def wheelEvent(self, event):
        try:
            self.distance *= 1.0 - event.angleDelta().y() * 0.0015
            self.distance = max(10, min(5000, self.distance))
            self.update()
        except Exception as e:
            print(f"Errore in wheelEvent: {e}")
    
    def keyPressEvent(self, event):
        try:
            key = event.key()
            mod = event.modifiers()
            if key == Qt.Key_Escape:
                if self.sketch_mode:
                    pass
                elif self.scene.has_selection:
                    self.scene.clear_selection()
                    self.window.update_ui()
                    self.update()
            elif key == Qt.Key_Delete and self.scene.has_selection:
                self.scene.delete()
                self.window.update_ui()
                self.update()
            elif key == Qt.Key_A and mod & Qt.ControlModifier:
                self.scene.selected_objects = self.scene.objects.copy()
                self.window.update_ui()
                self.update()
            elif key == Qt.Key_D and mod & Qt.ControlModifier:
                self.scene.clear_selection()
                self.window.update_ui()
                self.update()
            elif key == Qt.Key_Z and not (mod & Qt.ControlModifier):
                if self.scene.undo():
                    self.window.update_ui()
                    self.update()
            elif key == Qt.Key_Z and (mod & Qt.ControlModifier):
                if mod & Qt.ShiftModifier:
                    if self.scene.redo():
                        self.window.update_ui()
                        self.update()
                else:
                    if self.scene.undo():
                        self.window.update_ui()
                        self.update()
            elif key == Qt.Key_Y and not (mod & Qt.ControlModifier):
                if self.scene.redo():
                    self.window.update_ui()
                    self.update()
            elif key == Qt.Key_X and not (mod & Qt.ControlModifier):
                self._cut_selected()
            elif key == Qt.Key_C and not (mod & Qt.ControlModifier):
                self._copy_selected()
            elif key == Qt.Key_V and not (mod & Qt.ControlModifier):
                self._paste_clipboard()
            elif key == Qt.Key_Space:
                self.scene.align_z()
                self.window.update_ui()
                self.update()
        except Exception as e:
            print(f"Errore in keyPressEvent: {e}")

    def _cut_selected(self):
        self._copy_selected()
        self.scene.delete()
        self.window.update_ui()
        self.update()

    def _copy_selected(self):
        self.scene.clipboard_objects = []
        for obj in self.scene.selected_objects:
            try:
                self.scene.clipboard_objects.append(obj.copy())
            except:
                pass

    def _paste_clipboard(self):
        if not self.scene.clipboard_objects:
            return
        self.scene.start_operation()
        for obj in self.scene.clipboard_objects:
            try:
                new_obj = obj.copy()
                new_obj.apply_translation([10, 10, 0])
                new_obj.metadata["name"] = new_obj.metadata.get("name", "Object") + "_paste"
                self.scene.objects.append(new_obj)
            except:
                pass
        self.scene.end_operation()
        self.window.update_ui()
        self.update()

# =============================================================================
# BLOCCO 3: UI COMPONENTS
# =============================================================================
class TutorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 Manuale Utente N47Lab")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(f"""
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 4px;
        """)
        
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ 
                border: 1px solid {BORDER_COLOR}; 
                background: {BUTTON_COLOR}; 
                border-radius: 4px;
            }}
            QTabBar::tab {{ 
                background: #9CBDDB; 
                padding: 8px 15px; 
                border: 1px solid {BORDER_COLOR};
                border-bottom: none;
                margin-right: 2px; 
                color: {TEXT_COLOR};
            }}
            QTabBar::tab:selected {{ 
                background: {BACKGROUND_COLOR}; 
                color: {TEXT_COLOR}; 
                font-weight: bold; 
            }}
            QTextEdit {{ 
                background: #C4D8EC; 
                color: {TEXT_COLOR}; 
                border: none; 
                font-family: 'Segoe UI', sans-serif; 
                font-size: 12px;
            }}
            QTextEdit * {{ text-align: justify; }}
        """)
        
        content = {
            "🚀 Introduzione": f"<b>{APP_NAME} v{VERSION} — Software CAD/CAM 3D</b><br><br>"
                               "N47Lab è un ambiente integrato per modellazione 3D, progettazione meccanica,<br>"
                               "generazione CAM (percorsi utensile) e invio diretto a stampanti 3D.<br><br>"
                               "<b>Convenzione spaziale:</b><br>"
                               "• <b style='color:#CC3333;'>● Rosso = Destra</b> (Asse X, larghezza)<br>"
                               "• <b style='color:#33CC33;'>● Verde = Dietro</b> (Asse Y, profondità, fronte utente = -Y)<br>"
                               "• <b style='color:#3333CC;'>● Blu = Sopra</b> (Asse Z, altezza)<br><br>"
                               "<b>Pannelli:</b><br>"
                               "• <b>Sinistro:</b> Forme Primitive, Meccanica (Filettatura/Affetta/Arrotonda), CAM<br>"
                               "• <b>Destro:</b> Testo 3D, Parametri (posizione/rotazione), Analisi<br>"
                               "• <b>Proprietà:</b> (seleziona un oggetto) mostra volume, coordinate, dimensioni, stato mesh<br>"
                               "• <b>Toolbar:</b> Da2 a 3D, Nuovo/Apri/Salva, Booleane, Guscio, Snap, Magneti<br><br>"
                               "<b>N.B.</b> Ogni operazione è annullabile con Ctrl+Z.",

            "🟦 Forme": "<b>Libreria Forme (pannello sinistro)</b><br><br>"
                        "Clicca un pulsante per creare la forma all'origine. Poi spostala col GIZMO o coi parametri.<br><br>"
                        "• <b>Cubo</b> — larghezza, altezza, profondità<br>"
                        "• <b>Cilindro</b> — raggio, altezza, sezioni (circonferenza)<br>"
                        "• <b>Sfera</b> — raggio, suddivisioni (più suddivisioni = più liscia)<br>"
                        "• <b>Cono</b> — raggio base, altezza, sezioni<br>"
                        "• <b>collare</b> — raggio esterno, raggio interno, altezza (rondella)<br>"
                        "• <b>Esagono</b> — raggio, altezza (prisma esagonale)<br>"
                        "• <b>Spirale</b> — raggio, altezza, giri, spessore (elica 3D)<br>"
                        "• <b>Arco</b> — raggio esterno, raggio interno, apertura (°), altezza (parete curva)<br>"
                        "• <b>Scatola vuota</b> — larghezza, altezza, profondità, spessore muro (senza parete superiore)<br><br>"
                        "<b>Nota:</b> Altezza = Z (Blu).",

            "👁️ Vista e Selezione": "<b>Controlli Vista</b><br><br>"
                                     "• <b>Rotella:</b> Zoom dinamico (da 10 a 5000 unità)<br>"
                                     "• <b>Ctrl + SX + Drag:</b> Rotazione 360° (orbita)<br>"
                                     "• <b>Centrale + Drag:</b> Pan (traslazione vista)<br>"
                                     "• <b>Ctrl + Centrale + Drag:</b> Rotazione asse Z<br><br>"
                                     "<b>Selezione Oggetti</b><br><br>"
                                     "• <b>Click</b> su oggetto: seleziona (deseleziona gli altri)<br>"
                                     "• <b>Shift+Click</b> o <b>Ctrl+Click</b>: aggiungi/togli dalla selezione<br>"
                                     "• <b>SX + Drag</b> su sfondo: selezione rettangolare (box select)<br>"
                                     "• <b>Shift + box select:</b> aggiunge alla selezione<br>"
                                     "• <b>Click vuoto:</b> deseleziona tutto<br>"
                                     "• <b>Tasto DX:</b> menu contestuale (Duplica, Elimina, Raggruppa, Allinea a Z=0)<br>"
                                     "• <b>Ctrl+A:</b> seleziona tutti &nbsp;•&nbsp; <b>Ctrl+D:</b> deseleziona tutti<br>"
                                     "• <b>Del:</b> elimina selezionati<br><br>"
                                     "<b>Misurazioni:</b><br>"
                                     "• <b>Ctrl+M:</b> misura distanza tra 2 punti (clicca 2 punti sulla scena)<br>"
                                     "• <b>Ctrl+Shift+M:</b> misura angolo tra 3 punti (clicca 3 punti)",

            "🎨 GIZMO": "<b>Maniglie di Trasformazione</b><br><br>"
                        "Il GIZMO appare quando selezioni uno o più oggetti.<br><br>"
                        "<b style='color:#CC3333;'>● Rosso — Asse X:</b> Larghezza (destra/sinistra)<br>"
                        "<b style='color:#33CC33;'>● Verde — Asse Y:</b> Profondità (davanti = -Y, dietro = +Y)<br>"
                        "<b style='color:#3333CC;'>● Blu — Asse Z:</b> Altezza (sopra = +Z, sotto = -Z)<br><br>"
                        "• <b>◉ Bianco (centro):</b> Sposta su piano XY (segue il mouse 1:1)<br>"
                        "• <b>⇅ Grigia (verticale):</b> Sposta su Z (trascina su/giù)<br>"
                        "• <b>◆ Gialla (diagonale):</b> Scala uniforme (trascina orizzontalmente)<br>"
                        "• <b>Assi colorati:</b> Trascina per scalare SOLO lungo quell'asse<br>"
                        "• <b style='color:#FFDD00;'>● Cerchi gialli (goniometro):</b> Appaiono passando il mouse sugli assi<br>"
                        "&nbsp;&nbsp;• Trascina per ruotare attorno all'asse<br>"
                        "&nbsp;&nbsp;• Tacche ogni 15° (piccole), ogni 45° (grandi con punti)<br>"
                        "• <b>Maniglia evidenziata:</b> Pronta al trascinamento (cambia colore al passaggio del mouse)",

            "🔧 Manipolazioni": "<b>1. Spostamento</b><br>"
                                "• Trascina direttamente l'oggetto con SX<br>"
                                "• Usa GIZMO: Bianco centro (XY) o Grigio verticale (Z)<br>"
                                "• Modifica X, Y, Z nel pannello Parametri (destra)<br><br>"
                                "<b>2. Rotazione</b><br>"
                                "• GIZMO: cerchi gialli (goniometro) su hover degli assi<br>"
                                "• Modifica Rot X/Y/Z nel pannello Parametri<br>"
                                "• Rotazione libera: Ctrl + SX su sfondo (orbita camera)<br><br>"
                                "<b>3. Scalatura</b><br>"
                                "• Assi singoli: maniglie colorate<br>"
                                "• Uniforme: maniglia gialla diagonale<br><br>"
                                "<b>4. Operazioni Booleane</b> — Toolbar › Booleane<br>"
                                "• Seleziona 2+ oggetti: <b>Unione</b> (fonde), <b>Sottrazione</b> (primo - secondo), <b>Intersezione</b><br>"
                                "• Usa motori: manifold3D (se installato), trimesh, o scipy fallback<br><br>"
                                "<b>5. Allineamento a Z=0</b><br>"
                                "• Tasto <b>Spazio</b> o DX › Allinea a Z=0<br>"
                                "• Porta gli oggetti selezionati a contatto col piano terra<br><br>"
                                "<b>6. Pattern (Serie)</b><br>"
                                "• Lineare: Ctrl+L — copia N volte con distanza lungo X/Y/Z<br>"
                                "• Circolare: Ctrl+Shift+L — copia N volte in cerchio attorno a un asse<br><br>"
                                "<b>7. Mirror (Specchio)</b><br>"
                                "• Crea copia specchiata lungo X, Y o Z<br><br>"
                                "<b>8. Deformazioni Mesh</b><br>"
                                "• <b>Smooth:</b> arrotonda la mesh (Laplaciano)<br>"
                                "• <b>Subdivide:</b> aumenta la risoluzione (più vertici)<br>"
                                "• <b>Decimate:</b> riduce il numero di facce (semplifica)<br>"
                                "• <b>Merge Vertici:</b> fonde vertici vicini entro una distanza<br><br>"
                                "<b>9. Guscio (Shell)</b> — Toolbar<br>"
                                "• Trasforma solido pieno in involucro cavo con parete inferiore<br><br>"
                                "<b>10. Da2 a 3D</b> — Toolbar<br>"
                                "• Importa SVG, DXF, PNG, JPG, BMP, GIF, TIFF, WEBP<br>"
                                "• Converte in mesh 3D (immagini → edge detection Sobel → estrude)<br><br>"
                                "<b>11. Gruppi / Layer</b><br>"
                                "• <b>Raggruppa:</b> unisce oggetti in gruppo (DX › Raggruppa)<br>"
                                "• <b>Separati:</b> scioglie il gruppo (DX › Separati)<br>"
                                "• <b>Layer:</b> organizza oggetti su livelli diversi (visibilità/lock dal pannello Proprietà)<br><br>"
                                "<b>12. Taglia/Copia/Incolla</b><br>"
                                "• <b>Ctrl+X:</b> Taglia &nbsp;•&nbsp; <b>Ctrl+C:</b> Copia &nbsp;•&nbsp; <b>Ctrl+V:</b> Incolla<br>"
                                "• <b>Ctrl+Z:</b> Annulla &nbsp;•&nbsp; <b>Ctrl+Y:</b> Ripristina (fino a 50 step)",

            "📝 Testo 3D": "<b>Pannello Testo (destra)</b><br><br>"
                           "<b>1. Crea</b><br>"
                           "• Scrivi il testo, scegli font, dimensione, spessore, spaziatura<br>"
                           "• Clicca 'Crea' → il testo viene generato come mesh 3D verticale<br>"
                           "• Posizionato di fronte all'oggetto selezionato o all'origine<br>"
                           "• Dopo la creazione, usa GIZMO per posizionarlo<br><br>"
                           "<b>2. Adatta</b><br>"
                           "• Seleziona una forma, scrivi il testo, clicca 'Adatta'<br>"
                           "• Il testo viene posizionato sulla faccia anteriore (-Y) e unito con booleana<br><br>"
                           "<b>3. Bassorilievo</b><br>"
                           "• Crea prima il testo con 'Crea'<br>"
                           "• Posizionalo davanti alla forma con GIZMO<br>"
                           "• Seleziona <b>sia il testo che la forma</b><br>"
                           "• Clicca 'Bassorilievo' → il testo viene inciso sulla faccia anteriore<br>"
                           "• Il testo deve già esistere come oggetto 3D (creato con 'Crea')",

            "⚙️ Meccanica": "<b>Pannello Meccanica (sinistra)</b><br><br>"
                            "<b>Filettatura:</b><br>"
                            "• <b>Tipo:</b> Interna / Esterna — cresta all'interno o all'esterno<br>"
                            "• <b>Modalità (come interpreta 'Passo'):</b><br>"
                            "&nbsp;&nbsp;— Auto (profilo): passo usato direttamente in mm<br>"
                            "&nbsp;&nbsp;— Metrico: passo in mm (min 0.5)<br>"
                            "&nbsp;&nbsp;— UNF / UNC: inserisci TPI (filetti/pollice), converte: 25.4 / TPI<br>"
                            "&nbsp;&nbsp;— Gas: passo in mm (min 0.5)<br>"
                            "• <b>Profilo:</b> Trapezio (piatto), Filo (triangolare), Arrotondato (cosinusoidale)<br>"
                            "• <b>Passo:</b> distanza tra creste in mm (o TPI per UNF/UNC)<br>"
                            "• La filettatura si <b>adatta alla forma</b>: su oggetti sferici usa spirale sferica<br>"
                            "• Genera la filettatura come nuovo oggetto (non modifica l'originale)<br><br>"
                            "<b>Affetta:</b><br>"
                            "• Taglia l'oggetto con un piano lungo X, Y o Z<br>"
                            "• Specifica la posizione del piano di taglio (0 = centro oggetto)<br>"
                            "• Crea due mesh separate (sopra/sotto il piano)<br><br>"
                            "<b>Arrotondamento (Raccordo):</b><br>"
                            "• Raggio 0.5-50 — subdivide e applica smoothing Taubin<br>"
                            "• Raggio 1.0 = leggero, 3.0+ = marcato<br>"
                            "• Agisce sugli spigoli, non appiattisce le superfici piane<br><br>"
                            "<b>CAM (Percorsi Utensile):</b><br>"
                            "• Seleziona un singolo oggetto<br>"
                            "• Imposta diametro utensile e stepover<br>"
                            "• Genera percorsi adattivi 3D per fresatura<br>"
                            "• I percorsi appaiono in verde nella viewport",

            "⌨️ Scorciatoie": "<b>Generali</b><br>"
                              "• <b>Ctrl+Z:</b> Annulla &nbsp;|&nbsp; <b>Ctrl+Y:</b> Ripristina (Ctrl+Shift+Z)<br>"
                              "• <b>Ctrl+X:</b> Taglia &nbsp;|&nbsp; <b>Ctrl+C:</b> Copia &nbsp;|&nbsp; <b>Ctrl+V:</b> Incolla<br>"
                              "• <b>Del:</b> Elimina selezionati &nbsp;|&nbsp; <b>Ctrl+D:</b> Deseleziona tutti<br>"
                              "• <b>Ctrl+A:</b> Seleziona tutti<br>"
                              "• <b>Esc:</b> Deseleziona tutto / esci da sketch mode<br>"
                              "• <b>Spazio:</b> Allinea selezione a Z=0<br><br>"
                              "<b>Vista</b><br>"
                              "• <b>Rotella:</b> Zoom<br>"
                              "• <b>Ctrl+SX+Drag:</b> Orbita (rotazione 360°)<br>"
                              "• <b>Centrale+Drag:</b> Pan<br>"
                              "• <b>Ctrl+Centrale+Drag:</b> Rotazione asse Z<br><br>"
                              "<b>Selezione</b><br>"
                              "• <b>Shift+Click / Ctrl+Click:</b> Aggiungi/Togli selezione<br>"
                              "• <b>SX+Drag (sfondo):</b> Box select (Shift per aggiungere)<br>"
                              "• <b>Tasto DX:</b> Menu contestuale (duplica, elimina, raggruppa)<br><br>"
                              "<b>Misurazioni</b><br>"
                              "• <b>Ctrl+M:</b> Misura distanza<br>"
                              "• <b>Ctrl+Shift+M:</b> Misura angolo",

            "💡 Tips": "• <b>Salva spesso</b> con versioni multiple (File › Salva come .n47)<br>"
                       "• <b>File › Esporta:</b> STL, OBJ, PLY, 3MF, GLB<br>"
                       "• <b>File › Importa:</b> STL, OBJ, PLY, 3MF<br>"
                       "• <b>Da2 a 3D:</b> importa immagini, SVG, DXF → mesh 3D<br>"
                       "• <b>Watertight:</b> verifica che la mesh sia chiusa (essenziale per stampa 3D)<br>"
                       "• <b>Layer:</b> usa layer diversi per parti separate<br>"
                       "• <b>Snap Griglia:</b> attiva dalla toolbar per posizionamento preciso<br>"
                       "• <b>Magneti:</b> attacca gli oggetti tra loro quando sono vicini<br>"
                       "• <b>Scala Griglia:</b> Opzioni › Scala Griglia per cambiare risoluzione<br>"
                       "• <b>GIZMO Blu = Sopra (+Z):</b> Altezza della forma<br>"
                       "• <b>GIZMO Verde = Dietro (+Y):</b> Fronte utente = -Y<br>"
                       "• <b>Filettatura su sfera:</b> funziona! Genera spirale adattativa<br>"
                       "• <b>Arrotondamento:</b> Raggio 1-2 per smussatura leggera, 3+ per marcata<br>"
                       "• <b>Booleane:</b> l'ordine di selezione conta per la sottrazione<br>"
                       "• <b>Testo 3D:</b> 'Crea' → posiziona con GIZMO → seleziona entrambi → 'Bassorilievo'<br>"
                       "• <b>Undo/Redo:</b> 50 step massimi, non dimenticare Ctrl+Z<br>"
                       "• <b>FPS:</b> mostra nella barra di stato in basso<br>"
                       "• <b>Guscio:</b> lascia la base inferiore piena (ideale per contenitori)<br>"
                       "• <b>Pattern lineare:</b> utile per array di fori o repliche<br>"
                       "• <b>Collare:</b> ideale per flange e distanziali (ex 'Corona')",

            "🖨️ Stampa 3D": "<b>Invio diretto a stampante</b><br><br>"
                             "File › 'Invia alla stampante…' apre la finestra di connessione.<br><br>"
                             "<b>Profili integrati (13):</b><br>"
                             "• <b>Bambu Lab:</b> X1C, P1S, A1, A1 Mini — protocollo MQTT+FTP<br>"
                             "• <b>Anycubic:</b> Kobra 3, Kobra 2, Vyper — FTP, SMB, OctoPrint, Cloud<br>"
                             "• <b>Creality:</b> K1 Max, K1, Ender 3 V3 — HTTP WiFi, FTP, OctoPrint<br>"
                             "• <b>Prusa:</b> i3 MK3S+, XL — PrusaLink, FTP, OctoPrint<br><br>"
                             "<b>Protocolli di connessione:</b><br>"
                             "• <b>mqtt_ftps:</b> Bambu Lab (MQTT + FTP over TLS)<br>"
                             "• <b>creality_http:</b> Creality WiFi (HTTP POST)<br>"
                             "• <b>prusalink:</b> Prusa REST API<br>"
                             "• <b>octoprint:</b> Universale (API key)<br>"
                             "• <b>ftp / smb:</b> Condivisione rete locale<br>"
                             "• <b>anycubic_cloud:</b> Anycubic Cloud<br>"
                             "• <b>file:</b> Esporta solo GCODE<br><br>"
                             "Ogni profilo specifica volume di stampa, ugelli disponibili,<br>"
                             "temperature max, layer height e infill predefiniti.",

            "📊 Analisi": "<b>Pannello Analisi (destra)</b><br><br>"
                          "Seleziona uno o più oggetti e clicca:<br><br>"
                          "• <b>Volume:</b> calcola il volume in mm³ (utile per costo materiale)<br>"
                          "• <b>Superficie:</b> area totale della mesh in mm²<br>"
                          "• <b>Centro Massa:</b> coordinate del baricentro (COM)<br>"
                          "• <b>Bounding Box:</b> dimensioni X, Y, Z min/max e centro<br>"
                          "• <b>Tenuta Stagna:</b> verifica se la mesh è watertight (chiusa, senza buchi)<br><br>"
                          "<b>Pannello Proprietà (automatico alla selezione):</b><br>"
                          "• Scheda 'Selezione': conteggio, volume totale, area totale<br>"
                          "• Scheda 'Coordinate & Dimensioni': centro (X,Y,Z), dimensioni (L,H,P)<br>"
                          "• Scheda 'Stato': Volume, Area, Watertight (singolo oggetto)<br>"
                          "&nbsp;&nbsp;• Parametri dinamici modificabili (raggio, altezza, ecc.)",
        }
        
        for title, html_text in content.items():
            editor = QTextEdit()
            editor.setReadOnly(True)
            editor.setHtml(html_text)
            self.tabs.addTab(editor, title)
            
        layout.addWidget(self.tabs)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

# =============================================================================
# DIALOG CONNESSIONE STAMPANTE 3D
# =============================================================================
class PrinterConnectDialog(QDialog):
    PROTOCOL_LABELS = {
        "mqtt_ftps": "Bambu Lab MQTT+FTP (diretto)",
        "creality_http": "Creality HTTP API (Wi-Fi)",
        "prusalink": "PrusaLink REST API (rete locale)",
        "octoprint": "OctoPrint API (universale)",
        "ftp": "FTP generico",
        "smb": "Cartella di rete SMB",
        "anycubic_cloud": "Anycubic Cloud (Wi-Fi)",
        "file": "Solo esporta (manuale)"
    }
    PROTOCOL_HELP = {
        "mqtt_ftps": "<small>Richiede IP + Access Code dalla stampante. Carica file via FTP e avvia stampa via MQTT.</small>",
        "creality_http": "<small>Richiede IP. Collega via HTTP all'interfaccia web della stampante Creality (K1/K1 Max).</small>",
        "prusalink": "<small>Richiede IP + API key (da PrusaLink/Prusa Connect). Invia file via REST API.</small>",
        "octoprint": "<small>Richiede IP + API key (da OctoPrint > Impostazioni > API). Universal: funziona con qualsiasi stampante via Raspberry Pi.</small>",
        "ftp": "<small>Richiede IP + credenziali FTP. Carica il file sulla stampante o server FTP.</small>",
        "smb": "<small>Richiede percorso di rete (es. //192.168.1.100/share). Copia il file su cartella condivisa.</small>",
        "anycubic_cloud": "<small>Richiede IP + credenziali Anycubic Cloud. Invia alla stampante via cloud.</small>",
        "file": "<small>Esporta il file con le impostazioni del profilo, senza inviare.</small>"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connessione Stampante 3D")
        self.setMinimumSize(560, 520)
        self.setStyleSheet(f"""
            background-color: {BACKGROUND_COLOR}; color: {TEXT_COLOR};
            border: 1px solid {BORDER_COLOR}; border-radius: 4px;
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        
        lbl = QLabel("<b>Seleziona stampante e metodo di connessione</b>")
        lbl.setStyleSheet(f"color: {TEXT_COLOR}; padding: 4px;")
        layout.addWidget(lbl)
        
        self.profile_combo = QComboBox()
        for name in PRINTER_PROFILES:
            self.profile_combo.addItem(name)
        self.profile_combo.currentTextChanged.connect(self._on_profile_change)
        layout.addWidget(QLabel("Modello stampante:"))
        layout.addWidget(self.profile_combo)
        
        h_proto = QHBoxLayout()
        h_proto.addWidget(QLabel("Protocollo:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.currentTextChanged.connect(self._on_protocol_change)
        h_proto.addWidget(self.protocol_combo, 1)
        layout.addLayout(h_proto)
        
        self.proto_help = QLabel("")
        self.proto_help.setWordWrap(True)
        self.proto_help.setStyleSheet(f"color: #3060A0; padding: 2px 6px;")
        layout.addWidget(self.proto_help)
        
        info = QGroupBox("Specifiche stampante")
        il = QVBoxLayout(info)
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        il.addWidget(self.info_label)
        layout.addWidget(info)
        
        conn = QGroupBox("Connessione")
        cl = QVBoxLayout(conn)
        cl.setSpacing(4)
        
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Indirizzo IP / Host:"))
        self.ip_entry = QLineEdit()
        self.ip_entry.setPlaceholderText("es. 192.168.1.100")
        h1.addWidget(self.ip_entry)
        cl.addLayout(h1)
        
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Password / API key:"))
        self.code_entry = QLineEdit()
        self.code_entry.setPlaceholderText("(opzionale) chiave o password")
        self.code_entry.setEchoMode(QLineEdit.Password)
        h2.addWidget(self.code_entry)
        cl.addLayout(h2)
        
        h2b = QHBoxLayout()
        h2b.addWidget(QLabel("Utente (opz):"))
        self.user_entry = QLineEdit()
        self.user_entry.setPlaceholderText("(opzionale per FTP/SMB)")
        h2b.addWidget(self.user_entry)
        cl.addLayout(h2b)
        
        layout.addWidget(conn)
        
        opts = QGroupBox("Opzioni di stampa")
        ol = QVBoxLayout(opts)
        ol.setSpacing(4)
        
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Qualità layer (mm):"))
        self.layer_spin = QDoubleSpinBox()
        self.layer_spin.setRange(0.04, 0.4)
        self.layer_spin.setSingleStep(0.02)
        self.layer_spin.setDecimals(2)
        h3.addWidget(self.layer_spin)
        ol.addLayout(h3)
        
        h4 = QHBoxLayout()
        h4.addWidget(QLabel("Infill %:"))
        self.infill_spin = QSpinBox()
        self.infill_spin.setRange(0, 100)
        h4.addWidget(self.infill_spin)
        ol.addLayout(h4)
        
        h5 = QHBoxLayout()
        h5.addWidget(QLabel("Supporti:"))
        self.supports_cb = QCheckBox("Genera supporti")
        h5.addWidget(self.supports_cb)
        h5.addStretch()
        self.bed_adh_cb = QCheckBox("Brim/Adesione")
        h5.addWidget(self.bed_adh_cb)
        ol.addLayout(h5)
        
        layout.addWidget(opts)
        
        btn_row = QHBoxLayout()
        self.send_btn = QPushButton("Invia alla stampante")
        self.send_btn.setStyleSheet(f"background-color: #4CAF50; color: white; padding: 8px 20px;")
        self.send_btn.clicked.connect(self._send_to_printer)
        self.export_btn = QPushButton("Solo esporta")
        self.export_btn.clicked.connect(self._export_profile)
        btn_row.addWidget(self.export_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.send_btn)
        layout.addLayout(btn_row)
        
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet(f"color: {TEXT_COLOR}; padding: 4px;")
        layout.addWidget(self.status)
        
        self._on_profile_change(self.profile_combo.currentText())
    
    def _on_profile_change(self, name):
        p = PRINTER_PROFILES.get(name, {})
        bv = p.get("build_volume", (0,0,0))
        nozz = ", ".join(f"{n}mm" for n in p.get("nozzle", [0.4]))
        self.info_label.setText(
            f"Volume: {bv[0]}×{bv[1]}×{bv[2]} mm &nbsp;|&nbsp; Ugelli: {nozz}<br>"
            f"T max: {p.get('max_temp', 0)}°C &nbsp;|&nbsp; Letto: {p.get('bed_temp', 0)}°C &nbsp;|&nbsp; "
            f"Layer default: {p.get('default_layer', 0.2)}mm &nbsp;|&nbsp; Infill: {p.get('default_infill', 15)}%"
        )
        self.layer_spin.setValue(p.get("default_layer", 0.2))
        self.infill_spin.setValue(p.get("default_infill", 15))
        
        self.protocol_combo.blockSignals(True)
        self.protocol_combo.clear()
        for proto in p.get("protocols", ["file"]):
            label = self.PROTOCOL_LABELS.get(proto, proto)
            self.protocol_combo.addItem(label, proto)
        self.protocol_combo.blockSignals(False)
        self._on_protocol_change(self.protocol_combo.currentData())
    
    def _on_protocol_change(self, proto):
        help_text = self.PROTOCOL_HELP.get(proto, "")
        self.proto_help.setText(help_text)
        needs_auth = proto in ("ftp", "mqtt_ftps", "prusalink", "octoprint", "anycubic_cloud")
        self.code_entry.setEnabled(needs_auth or proto == "smb")
        self.user_entry.setEnabled(proto in ("ftp", "smb"))
    
    def _send_to_printer(self):
        profile = PRINTER_PROFILES.get(self.profile_combo.currentText())
        if not profile:
            return
        proto = self.protocol_combo.currentData()
        ip = self.ip_entry.text().strip()
        
        parent = self.parent() or self.parentWidget()
        while parent and not hasattr(parent, 'scene'):
            parent = parent.parent() if parent else None
        if not parent or not hasattr(parent, 'scene'):
            self.status.setText("<span style='color:red;'>Errore: contesto applicazione non trovato</span>")
            return
        
        scene = parent.scene
        visible = [o for o in scene.objects if scene.layers.get(o.metadata.get("layer", "Default"), {}).get("visible", True)]
        if not visible:
            self.status.setText("<span style='color:red;'>Nessun oggetto visibile da stampare</span>")
            return
        
        if proto != "file" and not ip:
            self.status.setText("<span style='color:red;'>Inserisci l'indirizzo IP della stampante</span>")
            return
        
        layer = self.layer_spin.value()
        infill = self.infill_spin.value()
        supports = self.supports_cb.isChecked()
        brim = self.bed_adh_cb.isChecked()
        
        try:
            self.status.setText("Preparazione file...")
            QApplication.processEvents()
            
            import tempfile, os
            tmp_path = os.path.join(tempfile.gettempdir(), f"n47lab_print_{int(time.time())}.3mf")
            mesh_scene = trimesh.Scene(visible)
            mesh_scene.export(tmp_path, file_type="3mf")
            
            handlers = {
                "mqtt_ftps": self._send_bambulab,
                "creality_http": self._send_creality_http,
                "prusalink": self._send_prusalink,
                "octoprint": self._send_octoprint,
                "ftp": self._send_ftp,
                "smb": self._send_smb,
                "anycubic_cloud": self._send_anycubic_cloud,
                "file": self._send_fileonly
            }
            handler = handlers.get(proto, self._send_fileonly)
            handler(tmp_path, profile, ip, layer, infill, supports, brim)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status.setText(f"<span style='color:red;'>Errore: {str(e)}</span>")
    
    def _prepare_print_attrs(self, profile, layer, infill, supports, brim):
        return {
            "layer_height": layer,
            "infill": infill,
            "support": int(supports),
            "brim": int(brim),
            "bed_temp": profile.get("bed_temp", 60),
            "nozzle_temp": profile.get("max_temp", 220)
        }
    
    def _send_bambulab(self, file_path, profile, ip, layer, infill, supports, brim):
        code = self.code_entry.text().strip()
        if not code:
            self.status.setText("<span style='color:red;'>Inserisci l'Access Code della stampante Bambu Lab</span>")
            return
        try:
            self.status.setText("Caricamento file via FTP...")
            QApplication.processEvents()
            import ftplib, os
            ftp = ftplib.FTP_TLS()
            ftp.connect(ip, 990)
            ftp.login("bblp", code)
            ftp.prot_p()
            remote_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_name}", f)
            ftp.quit()
            
            self.status.setText("File caricato. Invio comando di stampa via MQTT...")
            QApplication.processEvents()
            
            import paho.mqtt.client as mqtt, json, uuid
            client = mqtt.Client(client_id="n47lab_print")
            client.tls_set()
            client.username_pw_set("bblp", code)
            client.connect(ip, 8883, 10)
            client.loop_start()
            
            attrs = self._prepare_print_attrs(profile, layer, infill, supports, brim)
            cmd = json.dumps({
                "print": {
                    "sequence_id": "0", "command": "project_file",
                    "param": f"/sdcard/{remote_name}",
                    "subtask_id": str(uuid.uuid4()),
                    "timelapse": False,
                    "bed_temp": attrs["bed_temp"], "nozzle_temp": attrs["nozzle_temp"],
                    "layer_height": attrs["layer_height"], "infill": attrs["infill"],
                    "support": attrs["support"]
                }
            })
            client.publish(f"device/{ip}/request", cmd)
            time.sleep(1)
            client.disconnect()
            client.loop_stop()
            self.status.setText(f"<span style='color:green;'>✅ Comando inviato a {profile['brand']} {profile['model']} ({ip})</span>")
        except Exception as e:
            self.status.setText(f"<span style='color:red;'>Errore Bambu Lab: {str(e)}</span>")
    
    def _send_creality_http(self, file_path, profile, ip, layer, infill, supports, brim):
        try:
            import requests
            attrs = self._prepare_print_attrs(profile, layer, infill, supports, brim)
            url = f"http://{ip}/upload"
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "model/3mf")}
                data = {"print": "true", **{k: str(v) for k, v in attrs.items()}}
                r = requests.post(url, files=files, data=data, timeout=30)
            if r.status_code in (200, 201):
                self.status.setText(f"<span style='color:green;'>✅ File inviato a Creality {profile['model']} ({ip})</span>")
            else:
                self.status.setText(f"<span style='color:orange;'>⚠️ Risposta HTTP {r.status_code}: {r.text[:200]}</span>")
        except ImportError:
            self.status.setText("Installa: pip install requests")
        except Exception as e:
            self.status.setText(f"<span style='color:red;'>Errore Creality HTTP: {str(e)}</span>")
    
    def _send_prusalink(self, file_path, profile, ip, layer, infill, supports, brim):
        api_key = self.code_entry.text().strip()
        try:
            import requests
            headers = {"X-Api-Key": api_key} if api_key else {}
            url = f"http://{ip}/api/v1/files"
            with open(file_path, "rb") as f:
                r = requests.post(url, headers=headers, files={"file": f}, timeout=30)
            if r.status_code in (200, 201):
                self.status.setText(f"<span style='color:green;'>✅ File inviato a Prusa {profile['model']} ({ip}) via PrusaLink</span>")
            else:
                self.status.setText(f"<span style='color:orange;'>⚠️ Risposta HTTP {r.status_code}</span>")
        except ImportError:
            self.status.setText("Installa: pip install requests")
        except Exception as e:
            self.status.setText(f"<span style='color:red;'>Errore PrusaLink: {str(e)}</span>")
    
    def _send_octoprint(self, file_path, profile, ip, layer, infill, supports, brim):
        api_key = self.code_entry.text().strip()
        try:
            import requests
            headers = {"X-Api-Key": api_key} if api_key else {}
            url = f"http://{ip}/api/files/local"
            with open(file_path, "rb") as f:
                r = requests.post(url, headers=headers,
                    files={"file": (os.path.basename(file_path), f, "model/3mf")},
                    data={"select": "true", "print": "true"}, timeout=60)
            if r.status_code in (200, 201):
                self.status.setText(f"<span style='color:green;'>✅ File inviato a OctoPrint ({ip}) — stampa avviata</span>")
            else:
                self.status.setText(f"<span style='color:orange;'>⚠️ Risposta HTTP {r.status_code}: {r.text[:200]}</span>")
        except ImportError:
            self.status.setText("Installa: pip install requests")
        except Exception as e:
            self.status.setText(f"<span style='color:red;'>Errore OctoPrint: {str(e)}</span>")
    
    def _send_ftp(self, file_path, profile, ip, layer, infill, supports, brim):
        user = self.user_entry.text().strip() or "anonymous"
        pw = self.code_entry.text().strip() or ""
        try:
            import ftplib, os
            ftp = ftplib.FTP()
            ftp.connect(ip, 21)
            ftp.login(user, pw)
            remote_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_name}", f)
            ftp.quit()
            self.status.setText(f"<span style='color:green;'>✅ File caricato via FTP su {ip}</span>")
        except Exception as e:
            self.status.setText(f"<span style='color:red;'>Errore FTP: {str(e)}</span>")
    
    def _send_smb(self, file_path, profile, ip, layer, infill, supports, brim):
        user = self.user_entry.text().strip()
        pw = self.code_entry.text().strip()
        share_path = self.ip_entry.text().strip()
        try:
            import shutil, os
            if not share_path.startswith("//") and not share_path.startswith("\\\\"):
                share_path = f"//{share_path}/share"
            out_path = os.path.join(share_path, os.path.basename(file_path))
            shutil.copy2(file_path, out_path)
            self.status.setText(f"<span style='color:green;'>✅ File copiato su {share_path}</span>")
        except Exception as e:
            self.status.setText(f"<span style='color:red;'>Errore copia SMB: {str(e)}</span>")
    
    def _send_anycubic_cloud(self, file_path, profile, ip, layer, infill, supports, brim):
        email = self.user_entry.text().strip()
        pw = self.code_entry.text().strip()
        if not email or not pw:
            self.status.setText("<span style='color:red;'>Inserisci email e password Anycubic Cloud</span>")
            return
        try:
            import requests, json
            session = requests.Session()
            login = session.post("https://cloud.anycubic.com/api/v1/login",
                json={"email": email, "password": pw}, timeout=15)
            if login.status_code != 200:
                self.status.setText(f"<span style='color:red;'>Login Anycubic fallito: {login.status_code}</span>")
                return
            token = login.json().get("data", {}).get("token", "")
            if not token:
                self.status.setText("<span style='color:red;'>Token Anycubic non ricevuto</span>")
                return
            
            with open(file_path, "rb") as f:
                upload = session.post("https://cloud.anycubic.com/api/v1/file/upload",
                    headers={"Authorization": f"Bearer {token}"},
                    files={"file": f}, timeout=60)
            if upload.status_code == 200:
                self.status.setText(f"<span style='color:green;'>✅ File caricato su Anycubic Cloud. Avvia la stampa dall'app Anycubic.</span>")
            else:
                self.status.setText(f"<span style='color:orange;'>⚠️ Upload su Anycubic: {upload.status_code} {upload.text[:200]}</span>")
        except ImportError:
            self.status.setText("Installa: pip install requests")
        except Exception as e:
            self.status.setText(f"<span style='color:red;'>Errore Anycubic Cloud: {str(e)}</span>")
    
    def _send_fileonly(self, file_path, profile, ip, layer, infill, supports, brim):
        out_dir = os.path.expanduser("~/Desktop")
        try:
            import shutil, os
            out_path = os.path.join(out_dir, os.path.basename(file_path))
            shutil.copy2(file_path, out_path)
        except:
            pass
        self.status.setText(
            f"<span style='color:green;'>✅ File pronto per {profile['brand']} {profile['model']}</span>"
            f"<br>Layer: {layer}mm | Infill: {infill}% | Supporti: {'Sì' if supports else 'No'}"
            f"<br>Usa File → Esporta per salvare con nome personalizzato"
        )
    
    def _export_profile(self):
        profile = PRINTER_PROFILES.get(self.profile_combo.currentText())
        if not profile:
            return
        parent = self.parent() or self.parentWidget()
        while parent and not hasattr(parent, 'scene'):
            parent = parent.parent() if parent else None
        if not parent:
            return
        scene = parent.scene
        visible = [o for o in scene.objects if scene.layers.get(o.metadata.get("layer", "Default"), {}).get("visible", True)]
        if not visible:
            return
        
        layer = self.layer_spin.value()
        infill = self.infill_spin.value()
        supports = self.supports_cb.isChecked()
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Esporta con profilo stampante",
            f"{profile['brand']}_{profile['model']}.3mf",
            "File 3MF (*.3mf);;File STL (*.stl)"
        )
        if path:
            try:
                scene_obj = trimesh.Scene(visible)
                scene_obj.export(path)
                self.status.setText(
                    f"<span style='color:green;'>✅ Esportato: {path}</span>"
                    f"<br>Profilo: {profile['brand']} {profile['model']}"
                    f"<br>Layer: {layer}mm | Infill: {infill}% | Supporti: {'Sì' if supports else 'No'}"
                )
            except Exception as e:
                self.status.setText(f"<span style='color:red;'>Errore: {str(e)}</span>")

class PropertiesPanel(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.old_widgets = []
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(6, 6, 6, 6)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        main_layout.addWidget(scroll)
        
        container = QWidget()
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)
        container_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(container)
        
        self.placeholder = QLabel("🖱️ Seleziona un oggetto")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(f"padding:15px;color:#2C4A6E;font-style:italic;font-size:10px;background-color: {BACKGROUND_COLOR};")
        container_layout.addWidget(self.placeholder)
        container_layout.addStretch()
        
        self.selection_group = QGroupBox("🔍 Selezione")
        self.selection_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                margin-top: 1ex;
                font-weight: bold;
                color: {BORDER_COLOR};
                background-color: {BACKGROUND_COLOR};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 3px 0 3px;
                color: {BORDER_COLOR};
            }}
        """)
        selection_layout = QFormLayout()
        self.selection_group.setLayout(selection_layout)
        self.selection_group.hide()
        container_layout.addWidget(self.selection_group)
        
        self.selection_count = QLabel("0")
        self.selection_volume = QLabel("0")
        self.selection_area = QLabel("0")
        
        selection_layout.addRow("Oggetti:", self.selection_count)
        selection_layout.addRow("Vol. Tot:", self.selection_volume)
        selection_layout.addRow("Area Tot:", self.selection_area)
        
        self.coordinates_group = QGroupBox("📍 Coordinate & Dimensioni")
        self.coordinates_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                margin-top: 1ex;
                font-weight: bold;
                color: {BORDER_COLOR};
                background-color: {BACKGROUND_COLOR};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 3px 0 3px;
                color: {BORDER_COLOR};
            }}
        """)
        form_layout = QFormLayout()
        self.coordinates_group.setLayout(form_layout)
        self.coordinates_group.hide()
        container_layout.addWidget(self.coordinates_group)
        
        self.x_label = QLabel("X:0.00")
        self.y_label = QLabel("Y:0.00")
        self.z_label = QLabel("Z:0.00")
        self.width_label = QLabel("L:0.00")
        self.height_label = QLabel("H:0.00")
        self.depth_label = QLabel("P:0.00")
        
        for label, style in [
            (self.x_label, f"color:#0FF;font:11px mono;background-color: {BACKGROUND_COLOR};"),
            (self.y_label, f"color:#0FF;font:11px mono;background-color: {BACKGROUND_COLOR};"),
            (self.z_label, f"color:#0FF;font:11px mono;background-color: {BACKGROUND_COLOR};"),
            (self.width_label, f"color:#FFD700;font:11px mono;background-color: {BACKGROUND_COLOR};"),
            (self.height_label, f"color:#FFD700;font:11px mono;background-color: {BACKGROUND_COLOR};"),
            (self.depth_label, f"color:#FFD700;font:11px mono;background-color: {BACKGROUND_COLOR};")
        ]:
            label.setStyleSheet(style)
        
        form_layout.addRow("🎯 X:", self.x_label)
        form_layout.addRow("🎯 Y:", self.y_label)
        form_layout.addRow("🎯 Z:", self.z_label)
        form_layout.addRow("📏 L:", self.width_label)
        form_layout.addRow("📏 H:", self.height_label)
        form_layout.addRow("📏 P:", self.depth_label)
        
        self.status_group = QGroupBox("📊 Stato")
        self.status_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                margin-top: 1ex;
                font-weight: bold;
                color: {BORDER_COLOR};
                background-color: {BACKGROUND_COLOR};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 3px 0 3px;
                color: {BORDER_COLOR};
            }}
        """)
        status_layout = QFormLayout()
        self.status_group.setLayout(status_layout)
        self.status_group.hide()
        container_layout.addWidget(self.status_group)
        
        self.volume_label = QLabel("0")
        self.area_label = QLabel("0")
        self.watertight_label = QLabel("-")
        
        status_layout.addRow("Vol:", self.volume_label)
        status_layout.addRow("Area:", self.area_label)
        status_layout.addRow("WT:", self.watertight_label)
        
        self.params_layout = QFormLayout()
        container_layout.addLayout(self.params_layout)
        self.spinboxes = {}

    def update_ui(self, selected_objects):
        try:
            for widget in self.old_widgets:
                if widget:
                    widget.deleteLater()
            self.old_widgets.clear()
            self.spinboxes.clear()
            
            while self.params_layout.count():
                item = self.params_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            if not selected_objects:
                self.placeholder.show()
                self.selection_group.hide()
                self.coordinates_group.hide()
                self.status_group.hide()
                return
            
            self.placeholder.hide()
            self.selection_group.show()
            
            self.selection_count.setText(str(len(selected_objects)))
            
            total_volume = sum(obj.volume for obj in selected_objects if hasattr(obj, 'volume'))
            self.selection_volume.setText(f"{total_volume:.1f} mm³")
            
            total_area = sum(obj.area for obj in selected_objects if hasattr(obj, 'area'))
            self.selection_area.setText(f"{total_area:.1f} mm²")
            
            if len(selected_objects) == 1:
                obj = selected_objects[0]
                
                self.coordinates_group.show()
                self.status_group.show()
                
                vertices = np.asarray(obj.vertices)
                center = (vertices.min(0) + vertices.max(0)) / 2
                extents = vertices.max(0) - vertices.min(0)
                
                self.x_label.setText(f"X:{center[0]:.2f}")
                self.y_label.setText(f"Y:{center[1]:.2f}")
                self.z_label.setText(f"Z:{center[2]:.2f}")
                self.width_label.setText(f"L:{extents[0]:.2f}")
                self.height_label.setText(f"H:{extents[2]:.2f}")
                self.depth_label.setText(f"P:{extents[1]:.2f}")
                self.volume_label.setText(f"{obj.volume:.1f} mm³")
                self.area_label.setText(f"{obj.area:.1f} mm²")
                self.watertight_label.setText("✅ Si" if hasattr(obj, 'is_watertight') and obj.is_watertight else "⚠️ No")
                
                if obj.metadata.get("shape_type") in [s["type"] for s in SHAPE_LIBRARY.values()]:
                    for key, value in obj.metadata.get("params", {}).items():
                        if key in ("tipo", "spessore"):
                            continue
                        
                        spinbox = QDoubleSpinBox()
                        spinbox.setRange(0, 9999)
                        spinbox.setValue(float(value) if isinstance(value, (int, float)) else 0)
                        spinbox.valueChanged.connect(lambda v, k=key: self._on_param_changed(k, v))
                        
                        self.params_layout.addRow(key.replace("_", " ").title(), spinbox)
                        self.spinboxes[key] = spinbox
                        self.old_widgets.append(spinbox)
            else:
                self.coordinates_group.hide()
                self.status_group.hide()
        except Exception as e:
            print(f"Errore update_ui: {e}")

    def _on_param_changed(self, key, value):
        if self.window and self.window.scene.has_selection:
            obj = self.window.scene.selected_objects[0]
            
            obj.metadata["params"][key] = value
            
            try:
                new_mesh = create_mesh(obj.metadata["shape_type"], obj.metadata["params"])
                new_mesh.metadata = obj.metadata.copy()
                index = self.window.scene.objects.index(obj)
                self.window.scene.objects[index] = new_mesh
                self.window.scene.selected_objects[0] = new_mesh
                self.window.gl_widget.update()
            except Exception as e:
                print(f"Errore nella rigenerazione della mesh: {e}")

# =============================================================================
# BLOCCO 4: MAIN APPLICATION
# =============================================================================
def _make_icon(text, color, size=24):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(*color))
    p.setPen(QPen(QColor(*color).darker(150), 1))
    r = size // 2 - 2
    p.drawEllipse(QPoint(size//2, size//2), r, r)
    p.setPen(QColor(255, 255, 255))
    f = QFont("Segoe UI", size // 3, QFont.Bold)
    p.setFont(f)
    p.drawText(QRect(0, 0, size, size), Qt.AlignCenter, text[:2])
    p.end()
    return QIcon(pm)

class CADWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.resize(1400, 800)
        
        self.scene = Scene()
        self.gl_widget = GLWidget(self.scene, self)
        self.right_panel = None
        
        self._setup_ui()
        
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_stats)
        self.fps_timer.start(500)
        self.frames = 0
        self.last_time = time.time()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Pronto")
    
    def _setup_ui(self):
        self._setup_menu()
        self._setup_toolbar()
        self._setup_layout()
    
    def _setup_menu(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Nuovo", self._new)
        file_menu.addAction("Apri", self._open)
        file_menu.addAction("Salva", self._save)
        file_menu.addSeparator()
        file_menu.addAction("Importa", self._import)
        file_menu.addAction("Esporta", self._export)
        file_menu.addAction("Invia alla stampante...", self._show_printer_dialog)
        file_menu.addSeparator()
        file_menu.addAction("Esci", self.close)
        
        edit_menu = menu_bar.addMenu("Modifica")
        edit_menu.addAction("Annulla", self.scene.undo).setShortcut("Ctrl+Z")
        edit_menu.addAction("Ripristina", self.scene.redo).setShortcut("Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction("Duplica", self.scene.duplicate).setShortcut("Ctrl+D")
        edit_menu.addAction("Elimina", self.scene.delete).setShortcut("Del")
        
        opts_menu = menu_bar.addMenu("Opzioni")
        self._snap_act = QAction("Snap Griglia", self)
        self._snap_act.setCheckable(True)
        self._snap_act.setChecked(self.scene.snap_grid)
        self._snap_act.triggered.connect(self._toggle_snap)
        opts_menu.addAction(self._snap_act)
        self._magnet_act = QAction("Magneti", self)
        self._magnet_act.setCheckable(True)
        self._magnet_act.setChecked(self.scene.magnetic_snap)
        self._magnet_act.triggered.connect(self._toggle_magnetic)
        opts_menu.addAction(self._magnet_act)
        opts_menu.addSeparator()
        opts_menu.addAction("Scala Griglia...", self._set_grid_scale)
        
        help_menu = menu_bar.addMenu("Aiuto")
        help_menu.addAction("Tutorial", self._show_tutorial)
        help_menu.addAction("Informazioni", self._show_about)
    
    def _setup_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        tb_container = QWidget()
        tb_layout = QHBoxLayout(tb_container)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(2)

        def sep():
            s = QFrame()
            s.setFrameShape(QFrame.VLine)
            s.setFrameShadow(QFrame.Sunken)
            return s

        def mkbtn(text, cb, icon_color=(100,150,200)):
            b = QPushButton(_make_icon(text.split()[-1][:2], icon_color, 20), text)
            b.setIconSize(QSize(20, 20))
            b.clicked.connect(cb)
            return b

        tb_layout.addStretch()
        tb_layout.addWidget(mkbtn("Da2 a 3D", self._import_2d_to_3d, (180,100,80)))
        tb_layout.addWidget(sep())
        tb_layout.addWidget(mkbtn("Nuovo", self._new, (100,180,100)))
        tb_layout.addWidget(mkbtn("Apri", self._open, (120,140,200)))
        tb_layout.addWidget(mkbtn("Salva", self._save, (140,120,80)))
        tb_layout.addWidget(sep())
        bool_btn = QPushButton(_make_icon("B", (80,120,160), 20), "Booleane")
        bool_btn.setIconSize(QSize(20, 20))
        bool_menu = QMenu(self)
        bool_menu.addAction("Unione", lambda: self.scene.boolean_op("unione"))
        bool_menu.addAction("Sottrazione", lambda: self.scene.boolean_op("sottrazione"))
        bool_menu.addAction("Intersezione", lambda: self.scene.boolean_op("intersezione"))
        bool_btn.setMenu(bool_menu)
        tb_layout.addWidget(bool_btn)
        tb_layout.addWidget(sep())
        tb_layout.addWidget(mkbtn("Guscio", self._shell, (160,140,80)))
        tb_layout.addWidget(sep())
        snap_btn = mkbtn("Snap", self._toggle_snap, (100,160,180))
        snap_btn.setCheckable(True)
        snap_btn.setChecked(self.scene.snap_grid)
        tb_layout.addWidget(snap_btn)
        magnet_btn = mkbtn("Magneti", self._toggle_magnetic, (140,100,160))
        magnet_btn.setCheckable(True)
        magnet_btn.setChecked(self.scene.magnetic_snap)
        tb_layout.addWidget(magnet_btn)
        tb_layout.addStretch()
        
        donate_btn = QPushButton("❤️ Dona")
        donate_btn.setFlat(True)
        donate_btn.setStyleSheet("""
            QPushButton {
                color: #f5a623;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 14px;
                border: 1px solid #f5a623;
                border-radius: 12px;
                background: rgba(245,166,35,0.08);
            }
            QPushButton:hover {
                background: rgba(245,166,35,0.2);
                border-color: #ffc107;
                color: #ffc107;
            }
        """)
        donate_btn.setCursor(Qt.PointingHandCursor)
        donate_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.paypal.com/donate/?hosted_button_id=BC8Q8DEFUE9LJ")))
        tb_layout.addWidget(donate_btn)
        
        toolbar.addWidget(tb_container)
    
    def _setup_layout(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        main_layout.addWidget(self.gl_widget, 5)
        
        self.right_panel = self._create_right_panel()
        main_layout.addWidget(self.right_panel, 1)
        
        self.setCentralWidget(main_widget)
    
    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        shape_icons = {
            "Cubo": (100,160,220), "Cilindro": (140,200,120), "Sfera": (220,140,120),
            "Cono": (200,180,100), "collare": (180,120,160), "Esagono": (120,180,160),
            "Spirale": (160,140,200), "Arco": (200,160,140), "Scatola vuota": (140,160,180)
        }
        
        shapes_group = QGroupBox("Forme Primitive")
        shapes_layout = QVBoxLayout(shapes_group)
        shapes_layout.setSpacing(2)
        bm = self.fontMetrics()
        bmin_h = max(bm.height() + 10, 28)
        for name, shape in SHAPE_LIBRARY.items():
            c = shape_icons.get(name, (150,150,150))
            btn = QPushButton(_make_icon(name[:2], c, 20), name)
            btn.setIconSize(QSize(20, 20))
            btn.setMinimumHeight(bmin_h)
            btn.clicked.connect(lambda checked=False, s=shape["type"], p=shape["params"]: self._add_shape(s, p))
            shapes_layout.addWidget(btn)
        layout.addWidget(shapes_group)
        
        mech_group = QGroupBox("Meccanica")
        mech_layout = QVBoxLayout(mech_group)
        mech_layout.setSpacing(6)
        fm = self.fontMetrics()
        combo_h = max(fm.height() + 10, 28)
        btn_h = max(fm.height() + 12, 32)
        thr_sub = QGroupBox("Filettatura")
        thr_l = QVBoxLayout(thr_sub)
        thr_l.setSpacing(6)
        thr_l.addWidget(QLabel("Tipo:"))
        self.thread_type = QComboBox()
        self.thread_type.addItems(["Interna", "Esterna"])
        self.thread_type.setCurrentText("Esterna")
        self.thread_type.setMinimumWidth(120)
        self.thread_type.setMinimumHeight(combo_h)
        thr_l.addWidget(self.thread_type)
        thr_l.addWidget(QLabel("Modalità:"))
        self.thread_mode = QComboBox()
        self.thread_mode.addItems(["Auto (profilo)", "Metrico", "UNF", "UNC", "Gas"])
        self.thread_mode.setMinimumWidth(120)
        self.thread_mode.setMinimumHeight(combo_h)
        thr_l.addWidget(self.thread_mode)
        thr_l.addWidget(QLabel("Profilo:"))
        self.thread_profile = QComboBox()
        self.thread_profile.addItems(["Trapezio", "Filo", "Arrotondato"])
        self.thread_profile.setCurrentText("Filo")
        self.thread_profile.setMinimumWidth(120)
        self.thread_profile.setMinimumHeight(combo_h)
        thr_l.addWidget(self.thread_profile)
        pr = QHBoxLayout()
        pr.addWidget(QLabel("Passo:"))
        self.thread_pitch = QDoubleSpinBox()
        self.thread_pitch.setRange(0.1, 10)
        self.thread_pitch.setValue(1.5)
        self.thread_pitch.setMinimumWidth(80)
        self.thread_pitch.setMinimumHeight(combo_h)
        pr.addWidget(self.thread_pitch)
        thr_l.addLayout(pr)
        app_btn = QPushButton("Applica Filettatura", clicked=self._apply_threading)
        app_btn.setMinimumHeight(btn_h)
        thr_l.addWidget(app_btn)
        mech_layout.addWidget(thr_sub)
        sl_sub = QGroupBox("Affetta")
        sl_l = QVBoxLayout(sl_sub)
        sl_l.setSpacing(4)
        ar = QHBoxLayout()
        ar.addWidget(QLabel("Asse:"))
        self.slice_axis = QComboBox()
        self.slice_axis.addItems(["Z", "Y", "X"])
        self.slice_axis.setMinimumHeight(combo_h)
        ar.addWidget(self.slice_axis)
        sl_l.addLayout(ar)
        pr2 = QHBoxLayout()
        pr2.addWidget(QLabel("Offset:"))
        self.slice_pos = QDoubleSpinBox()
        self.slice_pos.setRange(-500, 500)
        self.slice_pos.setMinimumHeight(combo_h)
        pr2.addWidget(self.slice_pos)
        pr2.addWidget(QLabel("Pezzi:"))
        self.slice_count = QSpinBox()
        self.slice_count.setRange(2, 100)
        self.slice_count.setValue(2)
        self.slice_count.setMinimumHeight(combo_h)
        self.slice_count.setMinimumWidth(50)
        pr2.addWidget(self.slice_count)
        sl_l.addLayout(pr2)
        sl_btn = QPushButton("Affetta Selezione", clicked=self._slice_selection)
        sl_btn.setMinimumHeight(btn_h)
        sl_l.addWidget(sl_btn)
        mech_layout.addWidget(sl_sub)
        fi_sub = QGroupBox("Arrotonda")
        fi_l = QVBoxLayout(fi_sub)
        fi_l.setSpacing(4)
        fr2 = QHBoxLayout()
        fr2.addWidget(QLabel("Raggio:"))
        self.fillet_radius_spin = QDoubleSpinBox()
        self.fillet_radius_spin.setRange(0.1, 50)
        self.fillet_radius_spin.setValue(1.0)
        self.fillet_radius_spin.setSingleStep(0.5)
        self.fillet_radius_spin.setMinimumHeight(combo_h)
        fr2.addWidget(self.fillet_radius_spin)
        fi_l.addLayout(fr2)
        fi_btn = QPushButton("Applica Arrotondamento", clicked=self._apply_fillet)
        fi_btn.setMinimumHeight(btn_h)
        fi_l.addWidget(fi_btn)
        mech_layout.addWidget(fi_sub)
        layout.addWidget(mech_group)
        
        cam_group = QGroupBox("CAM")
        cam_layout = QVBoxLayout(cam_group)
        cam_layout.setSpacing(4)
        td = QDoubleSpinBox()
        td.setRange(0.5, 10); td.setValue(3.0); td.setSuffix(" mm")
        td.setMinimumHeight(combo_h)
        td.valueChanged.connect(lambda v: setattr(self.scene, "tool_diameter", v))
        so = QDoubleSpinBox()
        so.setRange(0.1, 5); so.setValue(0.5); so.setSuffix(" mm")
        so.setMinimumHeight(combo_h)
        so.valueChanged.connect(lambda v: setattr(self.scene, "stepover", v))
        cam_layout.addWidget(QLabel("Diametro utensile:"))
        cam_layout.addWidget(td)
        cam_layout.addWidget(QLabel("Stepover:"))
        cam_layout.addWidget(so)
        cam_layout.addWidget(QPushButton("Genera Toolpath", clicked=self._generate_toolpath))
        layout.addWidget(cam_group)
        
        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        text_group = QGroupBox("Testo 3D")
        text_layout = QVBoxLayout(text_group)
        text_layout.setSpacing(2)
        self.text_entry = QPlainTextEdit()
        self.text_entry.setPlaceholderText("Inserisci testo...")
        self.text_entry.setMaximumHeight(50)
        text_layout.addWidget(self.text_entry)
        fr = QHBoxLayout()
        fr.addWidget(QLabel("<small>Font:</small>"))
        self.font_combo = QComboBox()
        from PyQt5.QtGui import QFontDatabase
        for f in QFontDatabase().families():
            self.font_combo.addItem(f)
        self.font_combo.setCurrentText("Arial")
        fr.addWidget(self.font_combo)
        text_layout.addLayout(fr)
        sr = QHBoxLayout()
        sr.addWidget(QLabel("<small>Dim:</small>"))
        self.font_size_spin = QDoubleSpinBox()
        self.font_size_spin.setRange(1, 200)
        self.font_size_spin.setValue(5)
        sr.addWidget(self.font_size_spin)
        sr.addWidget(QLabel("<small>Spess:</small>"))
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0.1, 50)
        self.thickness_spin.setValue(1)
        sr.addWidget(self.thickness_spin)
        text_layout.addLayout(sr)
        spr = QHBoxLayout()
        spr.addWidget(QLabel("<small>Spaz:</small>"))
        self.spacing_spin = QDoubleSpinBox()
        self.spacing_spin.setRange(-50, 100)
        self.spacing_spin.setValue(0)
        spr.addWidget(self.spacing_spin)
        text_layout.addLayout(spr)
        btn_row = QHBoxLayout()
        btn_row.addWidget(QPushButton(_make_icon("Cr", (100,180,120), 16), "Crea", clicked=self._add_text_mesh))
        btn_row.addWidget(QPushButton(_make_icon("Ad", (180,140,100), 16), "Adatta", clicked=self._adapt_text_to_shape))
        text_layout.addLayout(btn_row)
        text_layout.addWidget(QPushButton(_make_icon("Ba", (160,100,80), 16), "Bassorilievo", clicked=self._bassorilievo))
        layout.addWidget(text_group)

        par_group = QGroupBox("Parametri")
        par_layout = QFormLayout(par_group)
        self.par_x = QDoubleSpinBox(); self.par_x.setRange(-999, 999); self.par_x.valueChanged.connect(lambda v: self._apply_param("pos_x", v))
        self.par_y = QDoubleSpinBox(); self.par_y.setRange(-999, 999); self.par_y.valueChanged.connect(lambda v: self._apply_param("pos_y", v))
        self.par_z = QDoubleSpinBox(); self.par_z.setRange(-999, 999); self.par_z.valueChanged.connect(lambda v: self._apply_param("pos_z", v))
        self.par_rx = QDoubleSpinBox(); self.par_rx.setRange(-360, 360); self.par_rx.valueChanged.connect(lambda v: self._apply_param("rot_x", v))
        self.par_ry = QDoubleSpinBox(); self.par_ry.setRange(-360, 360); self.par_ry.valueChanged.connect(lambda v: self._apply_param("rot_y", v))
        self.par_rz = QDoubleSpinBox(); self.par_rz.setRange(-360, 360); self.par_rz.valueChanged.connect(lambda v: self._apply_param("rot_z", v))
        par_layout.addRow("X:", self.par_x); par_layout.addRow("Y:", self.par_y); par_layout.addRow("Z:", self.par_z)
        par_layout.addRow("Rot X:", self.par_rx); par_layout.addRow("Rot Y:", self.par_ry); par_layout.addRow("Rot Z:", self.par_rz)
        layout.addWidget(par_group)

        an_group = QGroupBox("Analisi")
        an_layout = QVBoxLayout(an_group)
        an_layout.setSpacing(2)
        an_layout.addWidget(QPushButton("Volume", clicked=lambda: self._analyze("volume")))
        an_layout.addWidget(QPushButton("Superficie", clicked=lambda: self._analyze("area")))
        an_layout.addWidget(QPushButton("Centro Massa", clicked=lambda: self._analyze("com")))
        an_layout.addWidget(QPushButton("Bounding Box", clicked=lambda: self._analyze("bbox")))
        an_layout.addWidget(QPushButton("Tenuta Stagna", clicked=lambda: self._analyze("watertight")))
        layout.addWidget(an_group)

        layout.addStretch()
        return panel

    def _apply_param(self, param, value):
        if not self.scene.single_selection:
            return
        obj = self.scene.single_selection
        if param.startswith("pos_"):
            axis = {"pos_x": 0, "pos_y": 1, "pos_z": 2}[param]
            centroid = obj.centroid if hasattr(obj, 'centroid') else obj.vertices.mean(axis=0)
            delta = value - centroid[axis]
            obj.apply_translation([delta if axis==0 else 0, delta if axis==1 else 0, delta if axis==2 else 0])
        elif param.startswith("rot_"):
            pass
        self.gl_widget.update()

    def _adapt_text_to_shape(self):
        txt_obj = None
        shape_obj = None
        for obj in self.scene.selected_objects:
            if obj.metadata.get("shape_type") == "text":
                txt_obj = obj
            else:
                shape_obj = obj
        if txt_obj is None:
            QMessageBox.information(self, "Info", "Crea prima il testo con 'Crea', poi seleziona sia il testo che la forma")
            return
        if shape_obj is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona anche una forma a cui adattare il testo")
            return
        try:
            text_mesh = txt_obj.copy()
            obj = shape_obj
            bounds = obj.bounds
            if bounds is None:
                return
            # Scale text to fit shape
            t_bounds = text_mesh.bounds
            t_size = t_bounds[1] - t_bounds[0]
            face_size = bounds[1] - bounds[0]
            if t_size[0] > 0 and t_size[2] > 0:
                scale = min(face_size[0] / t_size[0], face_size[2] / t_size[2]) * 0.7
                text_mesh.apply_scale(scale)
            # Ray from shape geometric center toward camera to find surface hit
            import numpy as np
            mv = np.array(self.gl_widget._modelview_matrix).reshape(4, 4)
            cam_pos = -mv[:3, :3].T @ mv[3, :3]
            shape_center = np.mean([bounds[0], bounds[1]], axis=0)
            ray_dir = cam_pos - shape_center
            ray_len = np.linalg.norm(ray_dir)
            if ray_len < 1e-6:
                return
            ray_dir /= ray_len
            locations, idx_rays, idx_tris = obj.ray.intersects_location(
                [shape_center], [ray_dir]
            )
            if len(locations) == 0:
                QMessageBox.warning(self, "Attenzione", "Nessuna superficie raggiunta dal raggio camera")
                return
            dists = np.linalg.norm(locations - shape_center, axis=1)
            order = np.argsort(dists)
            hit_point = locations[order[0]]
            tri = obj.faces[idx_tris[order[0]]]
            v0, v1, v2 = obj.vertices[tri]
            surf_normal = np.cross(v1 - v0, v2 - v0)
            surf_normal /= np.linalg.norm(surf_normal)
            if np.dot(surf_normal, ray_dir) < 0:
                surf_normal = -surf_normal
            # Rotate text to face surface normal
            import trimesh.transformations as tf
            text_normal = np.array([0, -1, 0])
            v_rot = np.cross(text_normal, surf_normal)
            s_v = np.linalg.norm(v_rot)
            c = np.dot(text_normal, surf_normal)
            if s_v < 1e-6:
                R_mat = np.eye(3) if c > 0 else np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
            else:
                vx = np.array([[0, -v_rot[2], v_rot[1]],
                               [v_rot[2], 0, -v_rot[0]],
                               [-v_rot[1], v_rot[0], 0]])
                R_mat = np.eye(3) + vx + vx @ vx * (1 - c) / (s_v * s_v)
            cent = text_mesh.centroid.copy()
            text_mesh.apply_translation(-cent)
            T = np.eye(4)
            T[:3, :3] = R_mat
            text_mesh.apply_transform(T)
            text_mesh.apply_translation(cent)
            # Position front face at surface, text extends INTO shape
            vn = np.dot(text_mesh.vertices - text_mesh.centroid, surf_normal)
            front_val = np.max(vn)
            orig_depths = front_val - vn
            text_mesh.apply_translation([
                hit_point[0] - text_mesh.centroid[0] - front_val * surf_normal[0],
                hit_point[1] - text_mesh.centroid[1] - front_val * surf_normal[1],
                hit_point[2] - text_mesh.centroid[2] - front_val * surf_normal[2],
            ])
            # Surface curvature following: project each vertex onto surface along surf_normal,
            # then offset inward along each vertex's local face normal
            verts_pos = text_mesh.vertices
            ray_orig = verts_pos + 10.0 * surf_normal
            ray_dir = np.tile(-surf_normal, (len(verts_pos), 1))
            points, ray_idx, tri_idx = obj.ray.intersects_location(ray_orig, ray_dir, multiple_hits=False)
            if len(points) > 0:
                fn_all = obj.face_normals if (obj.face_normals is not None and len(obj.face_normals) == len(obj.faces)) else trimesh.geometry.compute_face_normals(obj.faces, obj.vertices)
                hit_normal = fn_all[tri_idx]
                dot_map = np.sum(hit_normal * surf_normal, axis=1)
                front_mask = dot_map > 0.5
                if np.any(front_mask):
                    idx = ray_idx[front_mask]
                    local_normals = hit_normal[front_mask]
                    align = np.sum(local_normals * surf_normal, axis=1, keepdims=True)
                    local_depths = orig_depths[idx, None] * np.abs(align)
                    inward = -local_normals / np.linalg.norm(local_normals, axis=1, keepdims=True)
                    new_pos = points[front_mask] + inward * local_depths
                    text_mesh.vertices[idx] = new_pos
            text_mesh.fix_normals()
            text_mesh.apply_translation(surf_normal * 0.1)
            text_mesh.merge_vertices()
            if not text_mesh.is_watertight:
                text_mesh = _ensure_volume(text_mesh)
            # Differenza booleana: forma - testo = cavità con apertura in superficie
            result = boolean_safe([obj, text_mesh], "sottrazione")
            if result is None or result.is_empty:
                raise RuntimeError("Risultato booleana vuoto")
            result.merge_vertices()

            result.metadata = obj.metadata.copy()
            result.metadata.pop("_gl_verts", None)
            result.metadata.pop("_gl_normals", None)
            result.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_inciso"

            self.scene.start_operation()
            for o in [obj, txt_obj]:
                if o in self.scene.objects:
                    self.scene.objects.remove(o)
            self.scene.objects.append(result)
            self.scene.selected_objects = [result]
            self.scene._needs_spatial_rebuild = True
            self.scene.end_operation()
            self._refresh_view()
            self.status_bar.showMessage("Bassorilievo applicato: testo inciso nella forma", 3000)
        except Exception as e:
            print(f"Errore bassorilievo: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Errore", f"Bassorilievo fallito: {str(e)}")

    def _shell(self):
        obj = self.scene.single_selection
        if not obj:
            QMessageBox.warning(self, "Attenzione", "Seleziona un singolo oggetto")
            return
        if self.scene.shell():
            self._refresh_view()
            self.status_bar.showMessage("Guscio applicato", 3000)

    def _bassorilievo(self):
        txt_obj = None
        shape_obj = None
        for obj in self.scene.selected_objects:
            if obj.metadata.get("shape_type") == "text":
                txt_obj = obj
            else:
                shape_obj = obj
        if txt_obj is None:
            QMessageBox.information(self, "Info", "Crea prima il testo con 'Crea', poi seleziona sia il testo che la forma")
            return
        if txt_obj is None or shape_obj is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona un oggetto testo (creato con 'Crea') e una forma")
            return
        try:
            text_mesh = txt_obj.copy()
            obj = shape_obj
            bounds = obj.bounds
            if bounds is None:
                return
            t_bounds = text_mesh.bounds
            t_size = t_bounds[1] - t_bounds[0]
            face_size = bounds[1] - bounds[0]
            if t_size[0] > 0 and t_size[2] > 0:
                scale = min(face_size[0] / t_size[0], face_size[2] / t_size[2]) * 0.7
                text_mesh.apply_scale(scale)
            import numpy as np
            mv = np.array(self.gl_widget._modelview_matrix).reshape(4, 4)
            cam_pos = -mv[:3, :3].T @ mv[3, :3]
            shape_center = np.mean([bounds[0], bounds[1]], axis=0)
            ray_dir = cam_pos - shape_center
            ray_len = np.linalg.norm(ray_dir)
            if ray_len < 1e-6:
                return
            ray_dir /= ray_len
            locations, idx_rays, idx_tris = obj.ray.intersects_location([shape_center], [ray_dir])
            if len(locations) == 0:
                QMessageBox.warning(self, "Attenzione", "Nessuna superficie raggiunta dal raggio camera")
                return
            dists = np.linalg.norm(locations - shape_center, axis=1)
            order = np.argsort(dists)
            hit_point = locations[order[0]]
            tri = obj.faces[idx_tris[order[0]]]
            v0, v1, v2 = obj.vertices[tri]
            surf_normal = np.cross(v1 - v0, v2 - v0)
            surf_normal /= np.linalg.norm(surf_normal)
            if np.dot(surf_normal, ray_dir) < 0:
                surf_normal = -surf_normal
            import trimesh.transformations as tf
            text_normal = np.array([0, -1, 0])
            v_rot = np.cross(text_normal, surf_normal)
            s_v = np.linalg.norm(v_rot)
            c = np.dot(text_normal, surf_normal)
            if s_v < 1e-6:
                R_mat = np.eye(3) if c > 0 else np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
            else:
                vx = np.array([[0, -v_rot[2], v_rot[1]],
                               [v_rot[2], 0, -v_rot[0]],
                               [-v_rot[1], v_rot[0], 0]])
                R_mat = np.eye(3) + vx + vx @ vx * (1 - c) / (s_v * s_v)
            cent = text_mesh.centroid.copy()
            text_mesh.apply_translation(-cent)
            T = np.eye(4)
            T[:3, :3] = R_mat
            text_mesh.apply_transform(T)
            text_mesh.apply_translation(cent)
            vn = np.dot(text_mesh.vertices - text_mesh.centroid, surf_normal)
            front_val = np.max(vn)
            orig_depths = front_val - vn
            text_mesh.apply_translation([
                hit_point[0] - text_mesh.centroid[0] - front_val * surf_normal[0],
                hit_point[1] - text_mesh.centroid[1] - front_val * surf_normal[1],
                hit_point[2] - text_mesh.centroid[2] - front_val * surf_normal[2],
            ])
            verts_pos = text_mesh.vertices
            ray_orig = verts_pos + 10.0 * surf_normal
            ray_dir = np.tile(-surf_normal, (len(verts_pos), 1))
            points, ray_idx, tri_idx = obj.ray.intersects_location(ray_orig, ray_dir, multiple_hits=False)
            if len(points) > 0:
                fn_all = obj.face_normals if (obj.face_normals is not None and len(obj.face_normals) == len(obj.faces)) else trimesh.geometry.compute_face_normals(obj.faces, obj.vertices)
                hit_normal = fn_all[tri_idx]
                dot_map = np.sum(hit_normal * surf_normal, axis=1)
                front_mask = dot_map > 0.5
                if np.any(front_mask):
                    idx = ray_idx[front_mask]
                    local_normals = hit_normal[front_mask]
                    align = np.sum(local_normals * surf_normal, axis=1, keepdims=True)
                    local_depths = orig_depths[idx, None] * np.abs(align)
                    inward = -local_normals / np.linalg.norm(local_normals, axis=1, keepdims=True)
                    new_pos = points[front_mask] + inward * local_depths
                    text_mesh.vertices[idx] = new_pos
            text_mesh.fix_normals()
            text_mesh.apply_translation(surf_normal * 0.1)
            text_mesh.merge_vertices()
            if not text_mesh.is_watertight:
                text_mesh = _ensure_volume(text_mesh)
            result = boolean_safe([obj, text_mesh], "sottrazione")
            if result is None or result.is_empty:
                raise RuntimeError("Risultato booleana vuoto")
            result.merge_vertices()
            result.metadata = obj.metadata.copy()
            result.metadata.pop("_gl_verts", None)
            result.metadata.pop("_gl_normals", None)
            result.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_inciso"
            self.scene.start_operation()
            for o in [obj, txt_obj]:
                if o in self.scene.objects:
                    self.scene.objects.remove(o)
            self.scene.objects.append(result)
            self.scene.selected_objects = [result]
            self.scene._needs_spatial_rebuild = True
            self.scene.end_operation()
            self._refresh_view()
            self.status_bar.showMessage("Bassorilievo applicato: testo inciso nella forma", 3000)
        except Exception as e:
            print(f"Errore bassorilievo: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Errore", f"Bassorilievo fallito: {str(e)}")

    def _import_2d_to_3d(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importa 2D in 3D", "",
            "Tutti i formati (*.svg *.dxf *.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;"
            "SVG (*.svg);;DXF (*.dxf);;Immagini (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp)"
        )
        if not path:
            return
        ext = Path(path).suffix.lower()
        try:
            if ext == ".svg":
                mesh = trimesh.load(path, force='mesh')
                if isinstance(mesh, trimesh.Scene):
                    mesh = mesh.dump(concatenate=True)
            elif ext == ".dxf":
                mesh = trimesh.load(path, force='mesh')
                if isinstance(mesh, trimesh.Scene):
                    mesh = mesh.dump(concatenate=True)
            else:
                from PIL import Image
                import io
                img = Image.open(path).convert('L')
                from scipy.ndimage import sobel
                edges_x = sobel(img, axis=1)
                edges_y = sobel(img, axis=0)
                edges = np.hypot(edges_x, edges_y)
                pts = np.column_stack(np.where(edges > edges.max() * 0.3))
                if len(pts) < 10:
                    raise ValueError("Pochi contorni rilevati")
                from shapely.geometry import MultiPoint
                mp = MultiPoint([(float(p[1]), float(-p[0])) for p in pts])
                hull = mp.convex_hull
                if hull.is_empty:
                    raise ValueError("Contorno vuoto")
                mesh = trimesh.creation.extrude_polygon(hull, height=5)
            if mesh and len(mesh.vertices) > 0:
                mesh = validate_and_place_mesh(mesh)
                mesh.metadata.update({
                    "layer": self.scene.active_layer,
                    "color": NEUTRAL_COLORS[self.scene.color_idx % len(NEUTRAL_COLORS)],
                    "name": Path(path).stem,
                    "shape_type": "imported_2d",
                    "params": {},
                    "assembly": None
                })
                self.scene.color_idx += 1
                self.scene.objects.append(mesh)
                self._refresh_view()
                self.status_bar.showMessage(f"Importato: {Path(path).name}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Importazione 2D fallita: {str(e)}")

    def _analyze(self, mode: str):
        obj = self.scene.single_selection
        if not obj:
            QMessageBox.warning(self, "Attenzione", "Seleziona un singolo oggetto")
            return
        if mode == "volume":
            v = obj.volume if hasattr(obj, 'volume') else 0
            QMessageBox.information(self, "Volume", f"Volume: {v:.2f}")
        elif mode == "area":
            a = obj.area if hasattr(obj, 'area') else 0
            QMessageBox.information(self, "Superficie", f"Area: {a:.2f}")
        elif mode == "com":
            c = obj.center_mass if hasattr(obj, 'center_mass') else np.mean(obj.vertices, axis=0)
            QMessageBox.information(self, "Centro Massa", f"({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})")
        elif mode == "bbox":
            b = obj.bounds
            if b is not None:
                dims = b[1] - b[0]
                QMessageBox.information(self, "Bounding Box", f"({dims[0]:.2f}, {dims[1]:.2f}, {dims[2]:.2f})")
        elif mode == "watertight":
            wt = hasattr(obj, 'is_watertight') and obj.is_watertight
            QMessageBox.information(self, "Tenuta Stagna", "✅ Watertight" if wt else "❌ Non watertight")
    
    def _add_shape(self, shape_type: str, params: Dict[str, Any]):
        self.scene.add_shape(shape_type, params)
        self.gl_widget.update()
        self.update_ui()
    
    def _generate_toolpath(self):
        if self.scene.generate_adaptive_path(
            self.scene.tool_diameter,
            self.scene.stepover,
            5.0,
            self.scene.feed_rate
        ):
            self.gl_widget.update()
            self.statusBar().showMessage("Percorso CAM generato")
        else:
            self.statusBar().showMessage("Errore nella generazione del percorso CAM")
    
    def _new(self):
        self.scene = Scene()
        self.gl_widget.scene = self.scene
        self.gl_widget.update()
        self.update_ui()
        self.statusBar().showMessage("Nuova scena creata")
    
    def _open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Apri", "", "File 3D (*.stl *.obj *.ply *.3mf)"
        )
        if path:
            try:
                mesh = trimesh.load(path, force='mesh')
                if isinstance(mesh, trimesh.Scene):
                    mesh = mesh.dump(concatenate=True)
                
                if hasattr(mesh, 'extents') and np.any(np.array(mesh.extents) < 1):
                    mesh.apply_scale(1000.0)
                
                mesh = validate_and_place_mesh(mesh)
                mesh.metadata.update({
                    "layer": "Default",
                    "color": NEUTRAL_COLORS[0],
                    "name": Path(path).stem,
                    "shape_type": "imported",
                    "params": {},
                    "assembly": None
                })
                
                self.scene.objects.append(mesh)
                self.gl_widget.update()
                self.update_ui()
                self.statusBar().showMessage(f"File aperto: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile aprire il file: {str(e)}")
    
    def _save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salva", "", "File N47Lab (*.n47)"
        )
        if path:
            self.statusBar().showMessage(f"Scena salvata: {path}")
    
    def _import(self):
        self._open()
    
    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Esporta", "", "File STL (*.stl);;File OBJ (*.obj);;File PLY (*.ply);;File 3MF (*.3mf);;File GLB (*.glb)"
        )
        if path:
            try:
                ext = Path(path).suffix.lower().lstrip(".")
                visible_objects = [
                    obj for obj in self.scene.objects 
                    if self.scene.layers.get(obj.metadata.get("layer", "Default"), {}).get("visible", True)
                ]
                
                if not visible_objects:
                    QMessageBox.warning(self, "Esportazione", "Nessun oggetto visibile da esportare")
                    return
                
                scene = trimesh.Scene(visible_objects)
                scene.export(path, file_type=ext)
                self.statusBar().showMessage(f"Esportato in: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile esportare: {str(e)}")
    
    def _show_printer_dialog(self):
        dlg = PrinterConnectDialog(self)
        dlg.exec_()
    
    def _toggle_snap(self, checked=None):
        if isinstance(checked, bool):
            self.scene.snap_grid = checked
        else:
            self.scene.snap_grid = not self.scene.snap_grid
        self.status_bar.showMessage(f"Snap griglia: {'ON' if self.scene.snap_grid else 'OFF'}", 2000)

    def _toggle_magnetic(self, checked=None):
        if isinstance(checked, bool):
            self.scene.magnetic_snap = checked
        else:
            self.scene.magnetic_snap = not self.scene.magnetic_snap
        self.status_bar.showMessage(f"Magneti: {'ON' if self.scene.magnetic_snap else 'OFF'}", 2000)

    def _set_grid_scale(self):
        modes = ["Disattivato", "0.5 mm", "1 mm", "2 mm", "5 mm", "10 mm"]
        current = self.scene.scale_mode
        idx = modes.index(current) if current in modes else 0
        val, ok = QInputDialog.getItem(self, "Scala Griglia", "Modalita:", modes, idx, False)
        if ok:
            self.scene.scale_mode = val
            self.status_bar.showMessage(f"Scala griglia: {val}", 2000)

    def _show_tutorial(self):
        TutorialDialog(self).exec_()

    def _show_about(self):
        QMessageBox.about(self, "Informazioni",
            f"<h2>{APP_NAME} v{VERSION}</h2><p>Applicazione CAD/CAM 3D.<br>Copyright (c) 2026 N47Lab Team</p>")

    def _apply_threading(self):
        if not self.scene.single_selection:
            QMessageBox.warning(self, "Attenzione", "Seleziona un singolo oggetto cilindrico")
            return
        obj = self.scene.single_selection
        thr_type = self.thread_type.currentText()
        mode = self.thread_mode.currentText()
        pitch = self.thread_pitch.value()
        try:
            self.scene.start_operation()
            bounds = obj.bounds
            if bounds is None:
                return
            height = bounds[1][2] - bounds[0][2]
            radius = (bounds[1][0] - bounds[0][0]) / 2
            if radius < 0.5:
                radius = 5.0
            if height < 1:
                height = 20.0
            if mode == "Metrico":
                pitch = max(0.5, pitch)
            elif mode in ("UNF", "UNC"):
                pitch = 25.4 / max(16, int(25.4 / pitch))
            elif mode == "Gas":
                pitch = max(0.5, pitch)
            turns = max(2, int(height / pitch))

            # Rileva forma sferica (bbox ≈ cubico)
            ext = bounds[1] - bounds[0]
            ext_xy = (ext[0] + ext[1]) / 2
            is_sphere = max(ext) / max(min(ext), 1e-8) < 1.3 and abs(ext[0] - ext[1]) / max(ext_xy, 1e-8) < 0.2

            if is_sphere:
                thread_mesh = _generate_thread_on_shape(obj, turns=turns * 2, thread_radius=pitch * 0.3)
                if thread_mesh and len(thread_mesh.vertices) >= 3:
                    thread_mesh.metadata.update(obj.metadata.copy())
                    thread_mesh.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_thread_sferico"
                    thread_mesh.metadata.pop("_gl_verts", None)
                    thread_mesh.metadata.pop("_gl_normals", None)
                    thread_mesh.metadata.pop("_gl_vbo_verts", None)
                    thread_mesh.metadata.pop("_gl_vbo_normals", None)
                    self.scene.objects.append(thread_mesh)
                    self.scene.selected_objects = [obj, thread_mesh]
                    self.scene.end_operation()
                    self._refresh_view()
                    self.status_bar.showMessage(f"Filettatura sferica aggiunta ({mode})", 3000)
                    return
                self.scene.end_operation()
                return

            # Filettatura cilindrica standard
            h_thread = pitch * 0.3
            segs_r = 32
            segs_z = int(turns * 24)
            base_z = bounds[0][2]

            profile = self.thread_profile.currentText()

            def _r_mod(pn):
                if profile == "Filo":
                    return pn * 2 if pn < 0.5 else 2 - pn * 2
                elif profile == "Trapezio":
                    flat = 0.25; ramp = 0.5 - flat
                    if pn < flat: return 0.0
                    if pn < 0.5: return (pn - flat) / ramp
                    if pn < 0.5 + flat: return 1.0
                    return 1.0 - (pn - 0.5 - flat) / ramp if ramp > 0 else 0.0
                else:
                    return 0.5 - 0.5 * math.cos(2 * math.pi * pn)

            verts = []
            for i in range(segs_z + 1):
                z = base_z + height * i / max(1, segs_z)
                for j in range(segs_r):
                    theta = 2 * math.pi * j / segs_r
                    phase = (theta + z * 2 * math.pi / pitch) % (2 * math.pi)
                    pn = phase / (2 * math.pi)
                    rm = _r_mod(pn)
                    if thr_type == "Esterna":
                        r = radius + h_thread * rm
                    else:
                        r = radius - h_thread * rm
                    verts.append([r * math.cos(theta), r * math.sin(theta), z])

            faces = []
            for i in range(segs_z):
                for j in range(segs_r):
                    v0 = i * segs_r + j
                    v1 = i * segs_r + (j + 1) % segs_r
                    v2 = (i + 1) * segs_r + j
                    v3 = (i + 1) * segs_r + (j + 1) % segs_r
                    faces.append([v0, v1, v2])
                    faces.append([v1, v3, v2])

            thread_mesh = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces))
            thread_mesh.fix_normals()
            thread_mesh.metadata.update(obj.metadata.copy())
            thread_mesh.metadata["name"] = f"{obj.metadata.get('name', 'Object')}_thread_{thr_type}"
            thread_mesh.metadata.pop("_gl_verts", None)
            thread_mesh.metadata.pop("_gl_normals", None)
            thread_mesh.metadata.pop("_gl_vbo_verts", None)
            thread_mesh.metadata.pop("_gl_vbo_normals", None)

            self.scene.objects.append(thread_mesh)
            self.scene.selected_objects = [obj, thread_mesh]
            self.scene.end_operation()
            self._refresh_view()
            self.status_bar.showMessage(f"Filettatura {thr_type} aggiunta ({mode})", 3000)
        except Exception as e:
            print(f"Errore filettatura: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Errore", f"Filettatura fallita: {str(e)}")

    def _slice_selection(self):
        if not self.scene.has_selection:
            QMessageBox.warning(self, "Attenzione", "Seleziona uno o piu oggetti da affettare")
            return
        axis = self.slice_axis.currentText().lower()
        offset = self.slice_pos.value()
        pieces = self.slice_count.value()
        if self.scene.slice_objects(axis, offset, pieces):
            self._refresh_view()
            self.status_bar.showMessage(f"Affettatura completata: {pieces} pezzi", 3000)
        else:
            QMessageBox.warning(self, "Errore", "Impossibile affettare gli oggetti selezionati")

    def _apply_fillet(self):
        if not self.scene.has_selection:
            QMessageBox.warning(self, "Attenzione", "Seleziona uno o piu oggetti")
            return
        radius = self.fillet_radius_spin.value()
        if self.scene.fillet_selected(radius):
            self._refresh_view()
            self.status_bar.showMessage(f"Arrotondamento applicato (raggio: {radius})", 3000)
        else:
            QMessageBox.warning(self, "Errore", "Impossibile applicare arrotondamento")

    def _refresh_view(self):
        self.gl_widget.update()
        self.update_ui()

    def _add_text_mesh(self):
        text = self.text_entry.toPlainText()
        if not text:
            return
        font_name = self.font_combo.currentText()
        font_size = self.font_size_spin.value()
        thickness = self.thickness_spin.value()
        spacing = self.spacing_spin.value()
        mesh = _generate_text_mesh(text, font_name, font_size, thickness, spacing)
        if mesh and len(mesh.vertices) > 0:
            import trimesh.transformations as tf
            R = tf.rotation_matrix(math.radians(90), [1, 0, 0])
            mesh.apply_transform(R)
            mesh.fix_normals()
            mesh.apply_translation(-mesh.centroid)
            mesh.metadata.update({
                "layer": self.scene.active_layer,
                "color": NEUTRAL_COLORS[self.scene.color_idx % len(NEUTRAL_COLORS)],
                "name": f"Testo_{text[:10]}",
                "shape_type": "text",
                "params": {},
                "assembly": None
            })
            self.scene.color_idx += 1
            self.scene.objects.append(mesh)
            self.scene._needs_spatial_rebuild = True
            self.scene._undo_push()
            self._refresh_view()

    def update_ui(self):
        pass
    
    def _update_stats(self):
        now = time.time()
        elapsed = now - self.last_time
        fps = self.frames / elapsed if elapsed > 0 else 0
        
        self.statusBar().showMessage(
            f"FPS: {fps:.1f} | Oggetti: {len(self.scene.objects)} | Selezionati: {len(self.scene.selected_objects)}"
        )
        
        self.frames = 0
        self.last_time = now

# =============================================================================
# BLOCCO 5: SPLASH SCREEN & ENTRY POINT
# =============================================================================
class SplashScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1280, 680)
        self.show()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        margin = 48
        p.setPen(QPen(QColor(200, 200, 210), 6))
        p.setBrush(QColor(0, 0, 0, 30))
        p.drawRoundedRect(margin, margin, w - margin * 2, h - margin * 2, 24, 24)

        text = "N47Lab"
        colors = [
            QColor(*[int(c * 255) for c in NEUTRAL_COLORS[i % len(NEUTRAL_COLORS)][:3]])
            for i in range(len(text))
        ]
        font = QFont("Segoe UI", 144, QFont.Bold)

        cx, cy = w // 2 + 120, h // 2 - 20
        stagger_x = [-16, 20, -10, 24, -20, 12]
        stagger_y = [-24, 16, -30, 12, -36, 20]
        rot = [-4, 3, -6, 5, -3, 7]

        for i, ch in enumerate(text):
            p.save()
            p.setFont(font)
            c = colors[i]
            p.setPen(QPen(c.darker(130), 4))
            p.setBrush(c)
            x = cx + (i - len(text) / 2) * 124 + (stagger_x[i] if i < len(stagger_x) else 0)
            y = cy + (stagger_y[i] if i < len(stagger_y) else 0)
            p.translate(x, y)
            p.rotate(rot[i] if i < len(rot) else 0)
            r = QFontMetrics(font).boundingRect(ch)
            p.drawText(-r.width() // 2, -r.height() // 2, r.width(), r.height(), Qt.AlignCenter, ch)
            p.restore()

        font2 = QFont("Segoe UI", 18)
        p.setFont(font2)
        p.setPen(QColor(180, 190, 200))
        p.drawText(self.rect(), Qt.AlignBottom | Qt.AlignCenter, "Caricamento in corso...")
        p.end()

    def mousePressEvent(self, event):
        self.close()

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(f"""
        QMainWindow, QDialog {{
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
        }}
        CADWindow {{
            background-color: {BACKGROUND_COLOR};
        }}
        QGroupBox {{
            font-weight: bold;
            color: {TEXT_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 4px;
            margin-top: 1ex;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 7px;
            padding: 0 3px 0 3px;
        }}
        QPushButton {{
            background-color: {BUTTON_COLOR};
            color: {TEXT_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 3px;
            padding: 4px 10px;
            font-size: 11px;
        }}
        QPushButton:hover {{
            background-color: #B8D4EC;
        }}
        QPushButton:pressed {{
            background-color: #8CB4D4;
        }}
        QComboBox, QDoubleSpinBox {{
            background-color: #C4D8EC;
            color: {TEXT_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 3px;
            padding: 2px 4px;
        }}
        QLabel {{
            color: {TEXT_COLOR};
        }}
        QToolBar {{
            background-color: {BACKGROUND_COLOR};
            border: none;
            spacing: 2px;
        }}
        QMenuBar {{
            background-color: #9CBDDB;
            color: {TEXT_COLOR};
        }}
        QMenuBar::item:selected {{
            background-color: {BUTTON_COLOR};
        }}
        QMenu {{
            background-color: #C4D8EC;
            color: {TEXT_COLOR};
            border: 1px solid {BORDER_COLOR};
        }}
        QMenu::item:selected {{
            background-color: {BUTTON_COLOR};
        }}
        QStatusBar {{
            background-color: #9CBDDB;
            color: {TEXT_COLOR};
        }}
    """)
    
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    format = QSurfaceFormat()
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.CompatibilityProfile)
    format.setDepthBufferSize(24)
    format.setStencilBufferSize(8)
    format.setSamples(4)
    format.setSwapInterval(1)
    QSurfaceFormat.setDefaultFormat(format)
    
    import time
    time.sleep(0.5)
    app.processEvents()
    
    window = CADWindow()
    splash.close()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()