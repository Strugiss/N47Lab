"""Benchmark FPS per fillet/smoothing"""
import sys, os, numpy as np, time
sys.path.insert(0, r'C:\Users\Utente\OneDrive\Desktop\N47Lab\Codice')
from n47lab import _generate_blender_collare, _generate_blender_box, _generate_blender_cylinder
import trimesh

shapes = [
    ("Cubo", _generate_blender_box(20, 20, 20)),
    ("Collare", _generate_blender_collare(20, 12, 8)),
    ("Cilindro", _generate_blender_cylinder(10, 30, 64)),
]

print("Forma        Subdiv  Verts    Faces    Process  VBO(KB)  FPSest")
print("-" * 65)

for name, mesh in shapes:
    # Senza fillet
    vb_kb = len(mesh.vertices) * 3 * 4 * 2 / 1024
    draw_ms = len(mesh.vertices) / 10000 * 0.03
    fps = 1 / (draw_ms / 1000) if draw_ms > 0 else 1000
    print(f"{name:12s} {'-':>6s} {len(mesh.vertices):>7d} {len(mesh.faces):>7d} {'-':>8s} {vb_kb:>6.0f}  {fps:>6.0f}")
    
    for sd in [1, 2]:
        m = mesh.copy()
        t0 = time.perf_counter()
        for _ in range(sd):
            try:
                m = m.subdivide()
            except:
                break
        trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=sd*5)
        dt = time.perf_counter() - t0
        
        vb_kb = len(m.vertices) * 3 * 4 * 2 / 1024
        draw_ms = len(m.vertices) / 10000 * 0.03
        fps = 1 / (draw_ms / 1000) if draw_ms > 0 else 1000
        print(f"{name:12s} {sd:6d} {len(m.vertices):>7d} {len(m.faces):>7d} {dt*1000:>6.0f}ms {vb_kb:>6.0f}  {fps:>6.0f}")

print()
print("Stima FPS per 10 oggetti in scena (tutti con stesso fillet):")
for sd in [0, 1, 2]:
    verts_total = 0
    for name, mesh in shapes:
        m = mesh.copy()
        for _ in range(sd):
            try:
                m = m.subdivide()
            except:
                break
        verts_total += len(m.vertices)
    draw_ms = verts_total / 10000 * 0.03 * 1.5
    fps = 1 / (draw_ms / 1000) if draw_ms > 0 else 1000
    print(f"  Subdiv={sd}: {verts_total} verts, ~{fps:.0f} FPS")
