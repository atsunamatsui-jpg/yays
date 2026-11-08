import math, random, os, sys
OUT = sys.argv[1]
random.seed(7)

# Palette (matched to the mockup's amber honey)
HL   = "#FFF4CC"   # specular
LT   = "#FFD45A"   # light honey
MID  = "#F2A516"   # honey amber
DK   = "#C9700A"   # deep amber
DDK  = "#8E4705"   # shadow amber
WAX_L = "#FFE08A"; WAX_M = "#F5BE45"; WAX_D = "#C98316"

def f(x): return f"{x:.2f}".rstrip('0').rstrip('.')

def smooth_closed(pts, t=0.5):
    """Catmull-Rom -> cubic Bezier closed path."""
    n = len(pts); d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    for i in range(n):
        p0, p1, p2, p3 = pts[i-1], pts[i], pts[(i+1)%n], pts[(i+2)%n]
        c1 = (p1[0]+(p2[0]-p0[0])*t/3, p1[1]+(p2[1]-p0[1])*t/3)
        c2 = (p2[0]-(p3[0]-p1[0])*t/3, p2[1]-(p3[1]-p1[1])*t/3)
        d += f" C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d + " Z"

def smooth_open(pts, t=0.5):
    n = len(pts); d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    for i in range(n-1):
        p0 = pts[max(i-1,0)]; p1=pts[i]; p2=pts[i+1]; p3=pts[min(i+2,n-1)]
        c1 = (p1[0]+(p2[0]-p0[0])*t/3, p1[1]+(p2[1]-p0[1])*t/3)
        c2 = (p2[0]-(p3[0]-p1[0])*t/3, p2[1]-(p3[1]-p1[1])*t/3)
        d += f" C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d

def blob(cx, cy, rx, ry, n=10, jitter=0.12, rot=0):
    pts=[]
    for i in range(n):
        a = rot + 2*math.pi*i/n
        r = 1 + random.uniform(-jitter, jitter)
        pts.append((cx+rx*r*math.cos(a), cy+ry*r*math.sin(a)))
    return pts

def svg(w, h, body, defs, title):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- yay's Honey Butter — {title}. Vector, editable in Adobe Illustrator. -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<title>{title}</title>
<defs>
{defs}
</defs>
{body}
</svg>
'''

# ---------- shared gradients ----------
def grad_defs(p):
    return f'''
<radialGradient id="{p}-drop" cx="0.42" cy="0.62" r="0.62" fx="0.5" fy="0.72">
  <stop offset="0" stop-color="{LT}"/>
  <stop offset="0.45" stop-color="{MID}"/>
  <stop offset="0.85" stop-color="{DK}"/>
  <stop offset="1" stop-color="{DDK}"/>
</radialGradient>
<linearGradient id="{p}-hl" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.95"/>
  <stop offset="1" stop-color="{HL}" stop-opacity="0"/>
</linearGradient>
<radialGradient id="{p}-glow" cx="0.5" cy="1" r="0.6">
  <stop offset="0" stop-color="{LT}" stop-opacity="0.9"/>
  <stop offset="1" stop-color="{LT}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="{p}-stream" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{DK}"/>
  <stop offset="0.3" stop-color="{MID}"/>
  <stop offset="0.55" stop-color="{LT}"/>
  <stop offset="0.8" stop-color="{MID}"/>
  <stop offset="1" stop-color="{DK}"/>
</linearGradient>
<radialGradient id="{p}-shadow" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="#7A3D00" stop-opacity="0.35"/>
  <stop offset="1" stop-color="#7A3D00" stop-opacity="0"/>
</radialGradient>'''

# ---------- 1. Teardrop droplet ----------
def droplet(x, y, s, p, shadow=True):
    # teardrop 100 x 140 units, origin top tip
    d = "M50,0 C55,22 92,62 92,96 C92,121 73,140 50,140 C27,140 8,121 8,96 C8,62 45,22 50,0 Z"
    g = f'<g transform="translate({f(x)},{f(y)}) scale({f(s)})">'
    if shadow:
        g += f'<ellipse cx="54" cy="141" rx="40" ry="7" fill="url(#{p}-shadow)"/>'
    g += f'<path d="{d}" fill="url(#{p}-drop)"/>'
    g += f'<path d="M28,118 C40,131 62,132 76,120 C68,128 34,130 28,118 Z" fill="{LT}" opacity="0.8"/>'  # bottom caustic
    g += f'<path d="M30,78 C30,64 40,48 47,38 C44,52 40,66 40,82 C40,92 30,92 30,78 Z" fill="url(#{p}-hl)"/>'  # long highlight
    g += f'<ellipse cx="34" cy="98" rx="5" ry="7" fill="#FFFFFF" opacity="0.9"/>'
    g += '</g>'
    return g

# ---------- 2. Round bead ----------
def bead(x, y, r, p):
    g = f'<g transform="translate({f(x)},{f(y)})">'
    g += f'<ellipse cx="{f(r*0.1)}" cy="{f(r*0.95)}" rx="{f(r*0.9)}" ry="{f(r*0.18)}" fill="url(#{p}-shadow)"/>'
    g += f'<circle r="{f(r)}" fill="url(#{p}-drop)"/>'
    g += f'<path d="M{f(-r*0.6)},{f(r*0.45)} A{f(r*0.8)},{f(r*0.8)} 0 0 0 {f(r*0.6)},{f(r*0.45)} A{f(r*0.9)},{f(r*0.7)} 0 0 1 {f(-r*0.6)},{f(r*0.45)} Z" fill="{LT}" opacity="0.75"/>'
    g += f'<ellipse cx="{f(-r*0.35)}" cy="{f(-r*0.38)}" rx="{f(r*0.32)}" ry="{f(r*0.2)}" transform="rotate(-35 {f(-r*0.35)} {f(-r*0.38)})" fill="url(#{p}-hl)"/>'
    g += f'<circle cx="{f(-r*0.15)}" cy="{f(-r*0.5)}" r="{f(r*0.08)}" fill="#fff"/>'
    g += '</g>'
    return g

# ---------- 3. Drizzle ribbon (variable width) ----------
def ribbon(center, wfun, p, hl=True):
    n = len(center); L=[]; R=[]; H=[]
    for i,(x,y) in enumerate(center):
        a = center[min(i+1,n-1)]; b = center[max(i-1,0)]
        tx, ty = a[0]-b[0], a[1]-b[1]; ln = math.hypot(tx,ty) or 1
        nx, ny = -ty/ln, tx/ln
        w = wfun(i/(n-1))
        L.append((x+nx*w, y+ny*w)); R.append((x-nx*w, y-ny*w))
        H.append((x+nx*w*0.35, y+ny*w*0.35))
    outline = smooth_open(L) + " L" + smooth_open(R[::-1])[1:] + " Z"
    out = f'<path d="{outline}" fill="{MID}"/>'
    # darker edge on one side
    sideL=[]; 
    for i,(x,y) in enumerate(center):
        a = center[min(i+1,n-1)]; b = center[max(i-1,0)]
        tx, ty = a[0]-b[0], a[1]-b[1]; ln = math.hypot(tx,ty) or 1
        nx, ny = -ty/ln, tx/ln; w = wfun(i/(n-1))
        sideL.append((x-nx*w*0.35, y-ny*w*0.35))
    shade = smooth_open(R) + " L" + smooth_open(sideL[::-1])[1:] + " Z"
    out += f'<path d="{shade}" fill="{DK}" opacity="0.85"/>'
    if hl:
        hpts=[]
        for i,(x,y) in enumerate(center):
            a = center[min(i+1,n-1)]; b = center[max(i-1,0)]
            tx, ty = a[0]-b[0], a[1]-b[1]; ln = math.hypot(tx,ty) or 1
            nx, ny = -ty/ln, tx/ln; w = wfun(i/(n-1))
            hpts.append((x+nx*w*0.45, y+ny*w*0.45))
        out += f'<path d="{smooth_open(hpts[2:-3])}" fill="none" stroke="#FFFFFF" stroke-opacity="0.85" stroke-linecap="round" stroke-width="{f(max(2,wfun(0.5)*0.28))}"/>'
        out += f'<path d="{smooth_open(H[1:-1])}" fill="none" stroke="{LT}" stroke-opacity="0.6" stroke-linecap="round" stroke-width="{f(max(2,wfun(0.5)*0.4))}"/>'
    return out

def bez(p0,p1,p2,p3,n=60):
    pts=[]
    for i in range(n):
        t=i/(n-1); u=1-t
        pts.append((u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0],
                    u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]))
    return pts

# ---------- 4. Puddle ----------
def puddle(cx, cy, rx, ry, p, seed=3):
    random.seed(seed)
    pts = blob(cx, cy, rx, ry, n=12, jitter=0.14)
    g = f'<ellipse cx="{f(cx+6)}" cy="{f(cy+ry*0.25)}" rx="{f(rx*1.05)}" ry="{f(ry*1.0)}" fill="url(#{p}-shadow)"/>'
    g += f'<path d="{smooth_closed(pts)}" fill="url(#{p}-drop)"/>'
    random.seed(seed+1)
    inner = blob(cx-rx*0.05, cy+ry*0.12, rx*0.7, ry*0.55, n=10, jitter=0.12)
    g += f'<path d="{smooth_closed(inner)}" fill="{LT}" opacity="0.55"/>'
    # rim highlights
    g += f'<path d="M{f(cx-rx*0.75)},{f(cy-ry*0.15)} Q{f(cx-rx*0.4)},{f(cy-ry*0.75)} {f(cx+rx*0.2)},{f(cy-ry*0.7)}" fill="none" stroke="#fff" stroke-opacity="0.9" stroke-width="{f(ry*0.09)}" stroke-linecap="round"/>'
    g += f'<ellipse cx="{f(cx+rx*0.45)}" cy="{f(cy+ry*0.35)}" rx="{f(rx*0.12)}" ry="{f(ry*0.08)}" fill="#fff" opacity="0.8"/>'
    return g

# ---------- 5. Honeycomb chunk ----------
def honeycomb(cx, cy, size, p, seed=11, rot=-8, depth=None, drip=True):
    random.seed(seed)
    r = size/9.5  # hex radius
    depth = depth if depth is not None else r*0.75
    outline_pts = blob(cx, cy, size*0.5, size*0.42, n=9, jitter=0.10, rot=0.3)
    outline = smooth_closed(outline_pts, t=0.35)
    cid = f"{p}-clip-{seed}"
    defs = f'''
<clipPath id="{cid}"><path d="{outline}"/></clipPath>
<linearGradient id="{p}-wax-{seed}" x1="0" y1="0" x2="0.4" y2="1">
  <stop offset="0" stop-color="{WAX_L}"/><stop offset="0.55" stop-color="{WAX_M}"/><stop offset="1" stop-color="{WAX_D}"/>
</linearGradient>
<radialGradient id="{p}-cell-{seed}" cx="0.55" cy="0.65" r="0.65">
  <stop offset="0" stop-color="{LT}"/><stop offset="0.5" stop-color="{MID}"/><stop offset="1" stop-color="{DK}"/>
</radialGradient>
<linearGradient id="{p}-side-{seed}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{DK}"/><stop offset="1" stop-color="{DDK}"/>
</linearGradient>'''
    g = f'<g transform="rotate({rot} {f(cx)} {f(cy)})">'
    g += f'<ellipse cx="{f(cx+size*0.04)}" cy="{f(cy+size*0.42+depth)}" rx="{f(size*0.52)}" ry="{f(size*0.08)}" fill="url(#{p}-shadow)"/>'
    # extruded side
    steps = 8
    g += '<g>' + ''.join(f'<path d="{outline}" transform="translate(0 {f(depth*(k+1)/steps)})" fill="url(#{p}-side-{seed})"/>' for k in range(steps)) + '</g>'
    # side cell openings hint (vertical lines)
    g += f'<path d="{outline}" fill="url(#{p}-wax-{seed})"/>'
    cells = '<g clip-path="url(#%s)">' % cid
    dx = math.sqrt(3)*r; dy = 1.5*r
    cols = int(size/dx)+3; rows = int(size/dy)+3
    x0 = cx - cols*dx/2; y0 = cy - rows*dy/2
    ir = r*0.80
    for j in range(rows):
        for i in range(cols):
            hx = x0 + i*dx + (dx/2 if j%2 else 0); hy = y0 + j*dy
            pts = [(hx+ir*math.cos(math.radians(60*k-90)), hy+ir*math.sin(math.radians(60*k-90))) for k in range(6)]
            d = "M" + " L".join(f"{f(a)},{f(b)}" for a,b in pts) + " Z"
            cells += f'<path d="{d}" fill="url(#{p}-cell-{seed})" stroke="{DK}" stroke-width="{f(r*0.06)}" stroke-linejoin="round"/>'
            # glossy highlight in cell (upper-left)
            hpts = [pts[4], pts[5], pts[0]]
            cells += f'<path d="M{f(pts[4][0]+ir*0.12)},{f(pts[4][1]+ir*0.12)} L{f(pts[5][0]+ir*0.08)},{f(pts[5][1]+ir*0.16)} L{f(pts[0][0])},{f(pts[0][1]+ir*0.2)}" fill="none" stroke="#FFFFFF" stroke-opacity="0.75" stroke-width="{f(r*0.1)}" stroke-linecap="round" stroke-linejoin="round"/>'
            cells += f'<circle cx="{f(hx+ir*0.2)}" cy="{f(hy+ir*0.3)}" r="{f(ir*0.12)}" fill="#FFF8DD" opacity="0.7"/>'
    cells += '</g>'
    g += cells
    # wax rim light
    g += f'<path d="{outline}" fill="none" stroke="{WAX_L}" stroke-width="{f(r*0.22)}" opacity="0.9"/>'
    g += '</g>'
    if drip:
        # honey oozing from the lower right edge
        bx = cx + size*0.18; by = cy + size*0.36 + depth*0.6
        g += droplet(bx-size*0.06, by-size*0.06, size/420, p, shadow=False)
    return g, defs

# ---------- 6. Dripping border ----------
def drip_border(w, h_band, p, seed=5):
    random.seed(seed)
    d = f"M0,0 L{w},0 L{w},{h_band}"
    x = w
    while x > 0:
        seg = random.uniform(w*0.06, w*0.12)
        nx = max(0, x-seg)
        if random.random() < 0.6 and x-nx > w*0.05:
            L = random.uniform(h_band*0.6, h_band*2.2); bw = (x-nx)*0.22
            mx = (x+nx)/2
            d += f" C{f(x-seg*0.2)},{f(h_band)} {f(mx+bw*1.4)},{f(h_band)} {f(mx+bw*0.6)},{f(h_band+L*0.55)}"
            d += f" C{f(mx+bw*0.45)},{f(h_band+L*0.8)} {f(mx+bw*1.3)},{f(h_band+L)} {f(mx)},{f(h_band+L+bw*0.9)}"
            d += f" C{f(mx-bw*1.3)},{f(h_band+L)} {f(mx-bw*0.45)},{f(h_band+L*0.8)} {f(mx-bw*0.6)},{f(h_band+L*0.55)}"
            d += f" C{f(mx-bw*1.4)},{f(h_band)} {f(nx+seg*0.2)},{f(h_band)} {f(nx)},{f(h_band)}"
        else:
            d += f" Q{f((x+nx)/2)},{f(h_band+random.uniform(4,14))} {f(nx)},{f(h_band)}"
        x = nx
    d += " Z"
    defs = f'''<linearGradient id="{p}-band" x1="0" y1="0" x2="0" y2="1" gradientUnits="userSpaceOnUse" y2_="0">
  <stop offset="0" stop-color="{DK}"/><stop offset="0.25" stop-color="{MID}"/><stop offset="0.7" stop-color="{MID}"/><stop offset="1" stop-color="{DK}"/>
</linearGradient>'''
    defs = f'''<linearGradient id="{p}-band" x1="0" y1="0" x2="0" y2="{f(h_band*3.3)}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="{DK}"/><stop offset="0.2" stop-color="{MID}"/><stop offset="0.6" stop-color="{LT}"/><stop offset="1" stop-color="{MID}"/>
</linearGradient>'''
    g = f'<path d="{d}" fill="url(#{p}-band)"/>'
    g += f'<path d="M{f(w*0.03)},{f(h_band*0.55)} C{f(w*0.3)},{f(h_band*0.35)} {f(w*0.6)},{f(h_band*0.7)} {f(w*0.95)},{f(h_band*0.45)}" fill="none" stroke="#fff" stroke-opacity="0.7" stroke-width="{f(h_band*0.1)}" stroke-linecap="round"/>'
    return g, defs

files = {}

# 01 droplet
p="d1"; files["honey-01-droplet.svg"] = svg(120,160, droplet(10,6,1,p), grad_defs(p), "Honey droplet")
# 02 beads
p="b2"; files["honey-02-bead-drops.svg"] = svg(260,120,
    bead(50,58,38,p)+bead(130,72,24,p)+bead(190,60,15,p)+bead(232,74,9,p), grad_defs(p), "Honey bead drops")
# 03 drizzle stream (like the mockup's top-left pour)
p="s3"
c = bez((40,30),(260,-20),(330,120),(300,260),80) 
body = ribbon(c, lambda t: 5+ 7*math.sin(math.pi*t)**0.8 + 6*t**3, p)
body += droplet(268,236,0.62,p,shadow=False)
files["honey-03-drizzle.svg"] = svg(380,340, body, grad_defs(p), "Honey drizzle")
# 04 S-swirl drizzle
p="s4"
c = bez((20,90),(150,-40),(230,220),(380,70),90)
body = ribbon(c, lambda t: 6+8*math.sin(math.pi*t), p)
files["honey-04-swirl.svg"] = svg(400,170, body, grad_defs(p), "Honey swirl drizzle")
# 05 puddle
p="p5"; files["honey-05-puddle.svg"] = svg(320,170, puddle(160,85,140,62,p), grad_defs(p), "Honey puddle")
# 06 honeycomb chunk
p="h6"; hc, hd = honeycomb(190,165,300,p, seed=11)
files["honey-06-honeycomb-chunk.svg"] = svg(380,380, hc, grad_defs(p)+hd, "Honeycomb chunk")
# 07 small honeycomb
p="h7"; hc, hd = honeycomb(120,110,190,p, seed=23, rot=14, drip=False)
files["honey-07-honeycomb-small.svg"] = svg(240,240, hc, grad_defs(p)+hd, "Small honeycomb chunk")
# 08 dripping border
p="r8"; bb, bd = drip_border(1200, 60, p)
files["honey-08-drip-border.svg"] = svg(1200,250, bb, bd, "Dripping honey border")

# 09 hero: honeycomb resting in a puddle (like the mockup centre)
p="x9"; hc, hd = honeycomb(200,172,190,p, seed=31, rot=-6, drip=False)
body = puddle(200,232,175,58,p,seed=9) + hc + bead(330,250,10,p) + bead(70,238,7,p)
files["honey-09-honeycomb-in-puddle.svg"] = svg(400,310, body, grad_defs(p)+hd, "Honeycomb in honey puddle")

for name, s in files.items():
    open(os.path.join(OUT, name), "w").write(s)
print("\n".join(files))
