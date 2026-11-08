"""Procedurally generate wrinkled black peppercorn vector assets (SVG).

Pure vector (paths + linear/radial gradients + opacity, no SVG filters) so the
files open cleanly and stay editable in Adobe Illustrator.

Usage: python3 make_peppercorns.py <out_dir>
"""
import math, random, sys, os

LIGHT = (-0.45, -0.6, 0.66)            # light from upper-left, toward viewer
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)

def clip_halfplane(poly, a, b, c):
    """Keep the part of poly where a*x + b*y <= c."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0: out.append(p)
        if (fp < 0) != (fq < 0) and fp != fq:
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out

def voronoi_cells(sites, bound=1.3):
    cells = []
    for i, s in enumerate(sites):
        poly = [(-bound, -bound), (bound, -bound), (bound, bound), (-bound, bound)]
        for j, t in enumerate(sites):
            if i == j: continue
            a, b = t[0] - s[0], t[1] - s[1]
            c = (t[0] ** 2 + t[1] ** 2 - s[0] ** 2 - s[1] ** 2) / 2
            poly = clip_halfplane(poly, a, b, c)
            if not poly: break
        cells.append(poly)
    return cells

def chaikin(poly, it=3):
    for _ in range(it):
        new = []
        n = len(poly)
        for i in range(n):
            p, q = poly[i], poly[(i + 1) % n]
            new += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]),
                    (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        poly = new
    return poly

def centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))

def inset(poly, k):
    cx, cy = centroid(poly)
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in poly]

def path_d(poly, S, ox, oy):
    pts = [f"{ox + x * S:.2f},{oy + y * S:.2f}" for x, y in poly]
    return "M" + " L".join(pts) + " Z"

def outline(rng, n=72):
    """Slightly lumpy circle (unit radius ~0.97-1.0)."""
    k1, k2, k3 = rng.uniform(0, 6.28), rng.uniform(0, 6.28), rng.uniform(0, 6.28)
    a1, a2, a3 = rng.uniform(.006, .016), rng.uniform(.004, .01), rng.uniform(.002, .005)
    sx = rng.uniform(0.95, 1.0)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        r = 0.985 + a1 * math.sin(2 * t + k1) + a2 * math.sin(3 * t + k2) + a3 * math.sin(7 * t + k3)
        pts.append((r * math.cos(t) * sx, r * math.sin(t)))
    return pts

def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return "#%02x%02x%02x" % tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))

def shade(nx, ny):
    nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
    return max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])

DARK = (10, 8, 7)
MID = (48, 41, 36)
LITE = (112, 98, 88)

def peppercorn(seed, size=400, n_cells=95):
    rng = random.Random(seed)
    S = size * 0.46
    ox = oy = size / 2
    uid = f"p{seed}"

    # sites: uniform on visible hemisphere, orthographic projection
    sites = []
    while len(sites) < n_cells:
        z = rng.uniform(0.0, 1.0); th = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(1 - z * z)
        x, y = r * math.cos(th), r * math.sin(th)
        if all((x - a) ** 2 + (y - b) ** 2 > 0.012 for a, b in sites):
            sites.append((x, y))
    # ring of sites just outside so rim cells close
    for i in range(28):
        t = 2 * math.pi * i / 28
        sites.append((1.12 * math.cos(t), 1.12 * math.sin(t)))
    cells = voronoi_cells(sites)[:n_cells]

    o = outline(rng)
    defs, body = [], []
    defs.append(f'<clipPath id="{uid}-clip"><path d="{path_d(o, S, ox, oy)}"/></clipPath>')
    # base: deep groove colour with slight radial lift
    defs.append(f'''<radialGradient id="{uid}-base" cx="{ox - .3*S:.1f}" cy="{oy - .35*S:.1f}" r="{1.5*S:.1f}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#5e534b"/><stop offset=".35" stop-color="#2e2722"/><stop offset=".75" stop-color="#15110f"/><stop offset="1" stop-color="#070605"/></radialGradient>''')
    # rim darkening overlay
    defs.append(f'''<radialGradient id="{uid}-rim" cx="{ox:.1f}" cy="{oy:.1f}" r="{S:.1f}" gradientUnits="userSpaceOnUse">
  <stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset=".9" stop-color="#000" stop-opacity=".45"/><stop offset="1" stop-color="#000" stop-opacity=".8"/></radialGradient>''')
    # soft specular bloom
    hx, hy = ox - 0.36 * S, oy - 0.42 * S
    defs.append(f'''<radialGradient id="{uid}-spec" cx="{hx:.1f}" cy="{hy:.1f}" r="{0.55*S:.1f}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#fff" stop-opacity=".38"/><stop offset=".35" stop-color="#fff" stop-opacity=".12"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>''')
    # bounce light lower-right (warm, from the bag's kraft tones)
    defs.append(f'''<radialGradient id="{uid}-bounce" cx="{ox + .55*S:.1f}" cy="{oy + .6*S:.1f}" r="{0.6*S:.1f}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#b07a4a" stop-opacity=".22"/><stop offset="1" stop-color="#b07a4a" stop-opacity="0"/></radialGradient>''')

    # ridges = the sphere surface itself; cells become sunken pits between ridges
    body.append(f'<path d="{path_d(o, S, ox, oy)}" fill="url(#{uid}-base)"/>')
    body.append(f'<g clip-path="url(#{uid}-clip)">')
    lx, ly = LIGHT[0], LIGHT[1]
    ll = math.hypot(lx, ly); ux, uy = lx / ll, ly / ll
    for idx, cell in enumerate(cells):
        if len(cell) < 3: continue
        cx, cy = centroid(cell)
        rr = math.hypot(cx, cy)
        if rr > 1.08: continue
        k = rng.uniform(0.60, 0.78) - 0.09 * rr
        pit = chaikin(inset(cell, k), 3)
        xs = [q[0] for q in pit]; ys = [q[1] for q in pit]
        half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
        s_ = shade(max(-.99, min(cx, .99)), max(-.99, min(cy, .99)))
        # lit far wall of the pit
        wall = mix((20, 17, 15), (104, 90, 80), s_ ** 1.4)
        body.append(f'<path d="{path_d(pit, S, ox, oy)}" fill="{wall}"/>')
        # shadowed floor, pushed toward the light so a crescent of wall shows
        sh = inset(pit, 0.86)
        off = half * rng.uniform(0.14, 0.24)
        sh = [(x + ux * off, y + uy * off) for x, y in sh]
        body.append(f'<path d="{path_d(sh, S, ox, oy)}" fill="{mix((8, 7, 6), (34, 29, 26), s_ * .8)}"/>')
        # glints on ridge crests near the hotspot
        d_spec = math.hypot(cx + 0.36, cy + 0.42)
        if d_spec < 0.5 and rng.random() < 0.8:
            gx, gy = cx + ux * half * 0.62, cy + uy * half * 0.62
            a = (1 - d_spec / 0.5) * 0.8
            w, h = half * rng.uniform(.30, .45), half * rng.uniform(.07, .12)
            ang = math.degrees(math.atan2(uy, ux)) + 90
            body.append(f'<ellipse cx="{ox+gx*S:.1f}" cy="{oy+gy*S:.1f}" rx="{w*S:.1f}" ry="{h*S:.1f}" transform="rotate({ang:.0f} {ox+gx*S:.1f} {oy+gy*S:.1f})" fill="#fff" fill-opacity="{a:.2f}"/>')
    body.append(f'<path d="{path_d(o, S, ox, oy)}" fill="url(#{uid}-bounce)"/>')
    body.append(f'<path d="{path_d(o, S, ox, oy)}" fill="url(#{uid}-rim)"/>')
    body.append(f'<path d="{path_d(o, S, ox, oy)}" fill="url(#{uid}-spec)"/>')
    body.append('</g>')
    # tiny stem scar on some corns
    if rng.random() < 0.6:
        t = rng.uniform(0, 2 * math.pi); r = rng.uniform(.25, .55)
        sx_, sy_ = ox + r * math.cos(t) * S, oy + r * math.sin(t) * S
        body.append(f'<circle cx="{sx_:.1f}" cy="{sy_:.1f}" r="{.05*S:.1f}" fill="#070606"/>'
                    f'<circle cx="{sx_ - .015*S:.1f}" cy="{sy_ - .02*S:.1f}" r="{.022*S:.1f}" fill="#2a231f"/>')
    inner = "\n".join(body)
    group = f'<g id="peppercorn-{seed}">\n{inner}\n</g>'
    return defs, group

def write_svg(path, size, defs, groups):
    with open(path, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" viewBox="0 0 {size[0]} {size[1]}">\n')
        f.write("<defs>\n" + "\n".join(defs) + "\n</defs>\n")
        f.write("\n".join(groups) + "\n</svg>\n")

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    seeds = [3, 11, 27, 42, 58, 77]
    sheet_defs, sheet_groups = [], []
    for i, sd in enumerate(seeds):
        d, g = peppercorn(sd)
        write_svg(os.path.join(out, f"black-peppercorn-{i+1:02d}.svg"), (400, 400), d, [g])
        sheet_defs += d
        col, row = i % 3, i // 3
        sheet_groups.append(f'<g transform="translate({col*400} {row*400})">{g}</g>')
    write_svg(os.path.join(out, "black-peppercorns-all.svg"), (1200, 800), sheet_defs, sheet_groups)
    print("done")
