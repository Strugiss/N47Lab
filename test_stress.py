"""Stress test per il backend di n47lab"""
import sys, os, gc, time
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Importa solo le funzioni che non richiedono GUI
from n47lab import boolean_safe, _ensure_volume

def test_booleane_massive():
    """Test booleane con mesh sempre piu complesse"""
    for n in [10, 50, 100, 500, 1000, 5000]:
        # Crea una mesh densa
        sphere = trimesh.creation.icosphere(subdivisions=3)
        t0 = time.perf_counter()
        try:
            result = boolean_safe([sphere, sphere.copy().apply_translation([2, 0, 0])], "unione")
            dt = time.perf_counter() - t0
            wc = result.is_watertight if hasattr(result, 'is_watertight') else '?'
            print(f"  Unione 2 sfere ({len(sphere.vertices)} verts): {dt*1000:.0f}ms, watertight={wc}, vertici={len(result.vertices)}")
        except Exception as e:
            print(f"  Unione 2 sfere ({len(sphere.vertices)} verts): FALLITA - {e}")

def test_booleane_molte_mesh():
    """Test booleane con molte mesh piccole"""
    for count in [2, 5, 10, 20]:
        cubes = [trimesh.creation.box(extents=[1, 1, 1]).apply_translation([i*1.5, 0, 0]) for i in range(count)]
        t0 = time.perf_counter()
        try:
            result = boolean_safe(cubes, "unione")
            dt = time.perf_counter() - t0
            print(f"  Unione {count} cubi: {dt*1000:.0f}ms, watertight={result.is_watertight}, vertici={len(result.vertices)}")
        except Exception as e:
            print(f"  Unione {count} cubi: FALLITA - {e}")

def test_ensure_volume():
    """Test _ensure_volume su mesh problematiche"""
    # Mesh watertight
    cube = trimesh.creation.box()
    r = _ensure_volume(cube)
    print(f"  Cubo watertight: input_ok={cube.is_watertight}, output_ok={r.is_watertight}")
    
    # Mesh non-manifold
    verts = [[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,0,0.5]]
    faces = [[0,1,2],[0,2,3],[1,4,3]]  # non manifold
    bad = trimesh.Trimesh(vertices=verts, faces=faces)
    r = _ensure_volume(bad)
    print(f"  Mesh non-manifold: input_ok={bad.is_watertight}, output_ok={r.is_watertight}")

def test_batch_creazione():
    """Test creazione e gestione tante mesh"""
    meshes = []
    t0 = time.perf_counter()
    for i in range(100):
        m = trimesh.creation.box(extents=[1,1,1]).apply_translation([i*2, 0, 0])
        meshes.append(m)
    dt = time.perf_counter() - t0
    print(f"  Create 100 mesh in {dt*1000:.0f}ms")
    
    t0 = time.perf_counter()
    combined = trimesh.util.concatenate(meshes)
    dt = time.perf_counter() - t0
    print(f"  Concatenate 100 mesh in {dt*1000:.0f}ms, vertici={len(combined.vertices)}")

def test_memoria():
    """Test leak memoria con operazioni ripetute"""
    gc.collect()
    before = len(gc.get_objects())
    
    for _ in range(50):
        a = trimesh.creation.box()
        b = trimesh.creation.box().apply_translation([2, 0, 0])
        try:
            r = boolean_safe([a, b], "unione")
        except:
            pass
    
    gc.collect()
    after = len(gc.get_objects())
    leaked = after - before
    print(f"  Oggetti GC prima={before}, dopo={after}, differenza={leaked}")
    if leaked > 1000:
        print("  WARNING: possibile memory leak!")

if __name__ == "__main__":
    print("=" * 60)
    print("STRESS TEST BACKEND")
    print("=" * 60)
    
    print("\n[1/5] Booleane con mesh dense...")
    test_booleane_massive()
    
    print("\n[2/5] Booleane con molte mesh...")
    test_booleane_molte_mesh()
    
    print("\n[3/5] _ensure_volume...")
    test_ensure_volume()
    
    print("\n[4/5] Batch creazione...")
    test_batch_creazione()
    
    print("\n[5/5] Test memoria...")
    test_memoria()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETATI")
    print("=" * 60)
