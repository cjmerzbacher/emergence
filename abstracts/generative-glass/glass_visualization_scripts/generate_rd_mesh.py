"""
generate_rd_mesh.py (v2 - sphere)
Reaction-diffusion on a 2D grid, mapped as displacement onto a sphere.

Run: python generate_rd_mesh.py
Outputs: rd_sphere.obj
"""
import numpy as np
from scipy.ndimage import laplace
import os


def gray_scott(N=256, steps=8000, Du=0.16, Dv=0.08, f=0.035, k=0.065, dt=1.0):
    print(f"Running Gray-Scott: {N}x{N}, {steps} steps...")
    u = np.ones((N, N))
    v = np.zeros((N, N))
    np.random.seed(42)
    for _ in range(12):
        cx, cy = np.random.randint(40, N - 40, size=2)
        size = np.random.randint(4, 10)
        u[cx-size:cx+size, cy-size:cy+size] = 0.50
        v[cx-size:cx+size, cy-size:cy+size] = 0.25
    for step in range(steps):
        Lu = laplace(u, mode='wrap')
        Lv = laplace(v, mode='wrap')
        uvv = u * v * v
        u += dt * (Du * Lu - uvv + f * (1 - u))
        v += dt * (Dv * Lv + uvv - (f + k) * v)
        u = np.clip(u, 0, 1)
        v = np.clip(v, 0, 1)
        if (step + 1) % 2000 == 0:
            print(f"  step {step+1}/{steps}")
    return v


def rd_sphere(heightmap, radius=1.0, displacement=0.25, lat_res=128, lon_res=256):
    """Map a reaction-diffusion heightmap onto a sphere as radial displacement."""
    print(f"Generating sphere mesh: {lat_res}x{lon_res}")
    N = heightmap.shape[0]

    verts = []
    for i in range(lat_res + 1):
        theta = np.pi * i / lat_res  # 0 to pi
        for j in range(lon_res):
            phi = 2.0 * np.pi * j / lon_res  # 0 to 2pi

            # Sample heightmap using spherical coords
            u_coord = j / lon_res
            v_coord = i / lat_res
            hi = int(v_coord * (N - 1))
            hj = int(u_coord * (N - 1))
            h = heightmap[hi, hj]

            r = radius + h * displacement
            x = r * np.sin(theta) * np.cos(phi)
            y = r * np.sin(theta) * np.sin(phi)
            z = r * np.cos(theta)
            verts.append((x, y, z))

    faces = []
    for i in range(lat_res):
        for j in range(lon_res):
            j_next = (j + 1) % lon_res
            idx00 = i * lon_res + j
            idx01 = i * lon_res + j_next
            idx10 = (i + 1) * lon_res + j
            idx11 = (i + 1) * lon_res + j_next
            faces.append((idx00, idx01, idx11, idx10))

    return verts, faces


def write_obj(path, verts, faces):
    with open(path, 'w') as f:
        f.write("# RD sphere\n")
        for v in verts:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")
    print(f"Wrote {len(verts)} verts, {len(faces)} faces to {path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rd_sphere.obj")
    v = gray_scott()
    verts, faces = rd_sphere(v)
    write_obj(out, verts, faces)