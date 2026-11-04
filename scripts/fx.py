#!/usr/bin/env python3
"""42 video effects adapted for Swarag Video Director. Original effects copyright Vibha Ramprakash (MIT).

One effect:    python fx.py orbit in.mp4 out.mp4 --start 3.2 --end 6
Many effects:  python fx.py --plan plan.json in.mp4 out.mp4
Quick check:   python fx.py --plan plan.json in.mp4 check.png --still 4.5
List them:     python fx.py --list
"""
import argparse, json, math, os, random, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = {k: os.path.join(ROOT, 'fonts', v) for k, v in {
    'bold': 'ArchivoBlack-Regular.ttf', 'serif': 'InstrumentSerif-Italic.ttf', 'mono': 'SpaceMono-Bold.ttf',
    'hand': 'PermanentMarker-Regular.ttf', 'ui': 'Inter.ttf', 'uim': 'Inter.ttf', 'uib': 'Inter.ttf',
    'anton': 'Anton-Regular.ttf', 'mont': 'Montserrat.ttf', 'monts': 'Montserrat.ttf', 'montb': 'Montserrat.ttf',
    'didone': 'PlayfairDisplay.ttf', 'didoneb': 'PlayfairDisplay.ttf', 'didonei': 'PlayfairDisplay-Italic.ttf'}.items()}
WGHT = {'ui': (24, 640), 'uim': (24, 540), 'uib': (32, 860), 'mont': (700,), 'monts': (600,), 'montb': (800,), 'didone': (500,), 'didoneb': (800,), 'didonei': (500,)}  # Inter variable: (optical size, weight)
CREAM, INK, PEACH, YELLOW = (245, 242, 236), (16, 25, 35), (197, 164, 109), (44, 154, 144)
NAMES = ['The Noise', 'The Lineup', 'Locked On', 'Orbit', 'Lean-In', 'Backdrop Word', 'Spotlight', 'The Bill',
         'Moody', 'Swipe', 'The To-Do', 'Comment Box', 'The Tap', 'Pause & Point', 'Uninstall', 'Reel Frame',
         'Shortcut Rain', 'Reject Stamp', 'Countdown Flip', 'Rabbit Hole', 'Cover Star', 'Scribble']
EFFECTS = {}
# Production UI must never disappear while the output MP4 remains technically
# decodable. These original functions now use place_safe_panel.
_REQUIRED_PANEL_VISIBLE = frozenset({
    'swipe','todo','tap','pause-point','the-bill','noise','lineup',
    'orbit','reject-stamp','cover-star','scribble','red-collage',
    'check-pills','headline-box','profile-wall','tier-list',
    'phone-fan','headline-wall','checklist','glass-widgets',
    'timeline','comment-box','liquid-glass-graph','carousel-spin',
    'apple-toggles','shortcut-rain','backdrop-word'
})
ALIASES = {'the-noise': 'noise', 'the-lineup': 'lineup', 'bill': 'the-bill', 'to-do': 'todo', 'the-todo': 'todo', 'the-to-do': 'todo',
           'the-tap': 'tap', 'follow': 'tap', 'comment': 'comment-box', 'pause': 'pause-point', 'pause-and-point': 'pause-point',
           'backdrop': 'backdrop-word', 'stamp': 'reject-stamp', 'countdown': 'countdown-flip', 'cover': 'cover-star', 'rain': 'shortcut-rain',
           'glass': 'glass-widgets', 'widgets': 'glass-widgets', 'collage': 'red-collage', 'split': 'split-headline', 'pastel': 'pastel-word',
           'pills': 'check-pills', 'auto-edit': 'timeline', 'headline': 'headline-box', 'wall': 'profile-wall', 'tiers': 'tier-list',
           'tier': 'tier-list', 'broll': 'broll-split', 'b-roll': 'broll-split', 'fan': 'phone-fan', 'dots': 'dot-reveal',
           'headlines': 'headline-wall', 'tasks': 'checklist',
           'liquid-glass': 'liquid-glass-graph', 'glass-graph': 'liquid-glass-graph', 'carousel': 'carousel-spin', 'match': 'match-cut',
           'toggles': 'apple-toggles', 'led': 'led-sign', 'push': 'slow-push', 'push-in': 'slow-push'}
LOOK_NAMES = {'glitter-spotlight': ('spotlight', 'sparkle'), 'glitter': ('spotlight', 'sparkle')}  # a named look of another effect
CARD_FX = ('noise', 'orbit', 'carousel-spin', 'check-pills', 'profile-wall', 'phone-fan', 'broll-split', 'timeline')


def effect(name, desc):
    def deco(fn):
        EFFECTS[name] = (fn, desc)
        return fn
    return deco


# ---------- small helpers ----------
_grid={}
def grid(c):
    """Cached coordinate mesh used by the untouched cinematic effects."""
    key=(int(c.W),int(c.H))
    if key not in _grid:
        yy,xx=np.mgrid[0:c.H,0:c.W].astype(np.float32)
        _grid[key]=(xx,yy)
    return _grid[key]


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_inout(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def ease_back(x): x = clamp(x); s = 1.7; x -= 1; return x * x * ((s + 1) * x + s) + 1
def ramp(c, e, t_in=0.25, t_out=0.2): return clamp(c.lt / t_in) * clamp((e.d - c.lt) / t_out) if t_out else clamp(c.lt / t_in)
def rgb(v, default):
    if v is None: return default
    if isinstance(v, (list, tuple)): return tuple(int(x) for x in v[:3])
    v = str(v).lstrip('#'); return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


_fc = {}
def font(kind, size):
    k = (kind, int(size))
    if k not in _fc:
        f = ImageFont.truetype(FONT[kind], max(6, int(size)))
        if kind in WGHT:
            try: f.set_variation_by_axes(list(WGHT[kind]))
            except Exception: pass
        _fc[k] = f
    return _fc[k]


def text_img(s, size, kind='bold', fill=(255, 255, 255), stroke=0, stroke_fill=INK, shadow=0, glow=None):
    f = font(kind, size)
    bb = f.getbbox(s, stroke_width=stroke)
    pad = int(size * 0.2 + shadow * 2.5 + (glow[1] * 2.5 if glow else 0)) + 4
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    pos = (pad - bb[0], pad - bb[1])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pos[0], pos[1] + shadow * 0.5), s, font=f, fill=(0, 0, 0, 160), stroke_width=stroke)
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(shadow)))
    if glow:
        g = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text(pos, s, font=f, fill=tuple(glow[0]) + (255,), stroke_width=int(size * 0.04))
        g = g.filter(ImageFilter.GaussianBlur(glow[1]))
        im = Image.alpha_composite(Image.alpha_composite(im, g), g)
    ImageDraw.Draw(im).text(pos, s, font=f, fill=tuple(fill) + (255,), stroke_width=stroke, stroke_fill=tuple(stroke_fill) + (255,))
    return im


def fit_text(s, max_w, kind='bold', start=400, **kw):
    size = start
    while size > 10 and font(kind, size).getlength(s) > max_w: size = int(size * 0.92)
    return text_img(s, size, kind, **kw)


def rrect(w, h, r, fill, outline=None, width=0):
    im = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, int(w) - 1, int(h) - 1], int(r), fill=fill, outline=outline, width=width)
    return im


def shadowed(im, blur=18, dy=10, alpha=120):
    pad = blur * 2 + abs(dy)
    out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 255)); sh.putalpha(a)
    out.paste(sh, (pad, pad + dy), sh)
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def to_np(im): return np.asarray(im.convert('RGBA'), dtype=np.float32) / 255.0



# Deliberate editorial layout: move a complete graphic rather than cutting
# an oval hole in its letters or glass panel. The face box follows the original
# tracked speaker; these are geometric bounds, not identity recognition.
_FACE_TOUCH_EFFECTS = frozenset(("locked-on", "scribble", "swipe",
                                 "pause-point", "dot-reveal", "rabbit-hole",
                                 "uninstall"))

def face_protection_rect(c):
    fw = max(float(c.fw), float(c.W) * 0.045, 1.0)
    margin = max(c.W * 0.035, 3.0)
    # YuNet's face centre and width already represent the detected
    # facial area. Protect the hairline generously while keeping the
    # chest available for genuinely lower-third graphics. Extending
    # 1.48 face-widths below the centre had reserved the entire torso,
    # collapsing informational panels into unreadable postage stamps.
    return (c.fx - fw * 1.08 - margin, c.fy - fw * 1.42 - margin,
            c.fx + fw * 1.08 + margin, c.fy + fw * 1.12 + margin)


def overlaps_face(c, x, y, w, h):
    a, b, d, e = face_protection_rect(c)
    return (x < d and x + w > a and y < e and y + h > b)


def safe_graphic_xy(c, x, y, w, h, preferred=None):
    """Return full-unit, face-clear top-left or None when it cannot fit.

    Unlike the legacy pixel-mask guard, the text and its background move
    TOGETHER; no chopped text, transparent forehead or floating UI toggle.
    """
    margin = max(c.W * 0.035, 4.0)
    # Respect entrance/exit motion and large graphics that are already clear.
    if not overlaps_face(c, x, y, w, h):
        return (x, y)
    if w > c.W - margin * 2 or h > c.H - margin * 2:
        return None
    def bounded(u, a, b): return max(a, min(b, u))
    x0 = bounded(x, margin, c.W - w - margin)
    y0 = bounded(y, margin, c.H - h - margin)
    if not overlaps_face(c, x0, y0, w, h):
        return (x0, y0)
    face_left, face_top, face_right, face_bottom = face_protection_rect(c)
    top = (c.W / 2 - w / 2, margin)
    bottom = (c.W / 2 - w / 2, c.H - h - margin)
    left = (margin, bounded(y, margin, c.H - h - margin))
    right = (c.W - w - margin, bounded(y, margin, c.H - h - margin))
    if preferred == 'above': candidates = [top, left, right, bottom]
    elif preferred == 'below': candidates = [bottom, left, right, top]
    else: candidates = [top, bottom, left, right]
    valid = [(cx, cy) for cx, cy in candidates
             if not overlaps_face(c, cx, cy, w, h)]
    if not valid: return None
    if preferred in ('above', 'below'): return valid[0]
    return min(valid, key=lambda pt: abs(pt[0]-x)+abs(pt[1]-y))

def editorial_headline_anchor(c, image, margin=.042):
    """Place a complete editorial word only where real negative space exists.

    When the upper strip is too shallow, use lower negative space. If neither
    zone can hold legible type, omit the unsafe word rather than carve it
    through the eyes or overlay a synthetic face-shaped black hole.
    """
    _, face_top, _, face_bottom = face_protection_rect(c)
    page_top, page_bottom = c.H*margin, c.H*(1-margin)
    air=c.H*.018
    upper=max(0.,face_top-page_top-air)
    lower=max(0.,page_bottom-face_bottom-air)
    required=max(c.H*.10,image.height*.55)
    if upper>=required:
        scale=min(1.,upper/max(1,image.height))
        cy=page_top+min(upper,image.height*scale)/2
        return cy,scale
    if lower>=required:
        scale=min(1.,lower/max(1,image.height))
        cy=page_bottom-image.height*scale/2
        return cy,scale
    return 0.,0.


def safe_panel_layout(c, width, height, region="above", min_scale=0.45,
                      max_scale=1.0):
    """Fit one complete information panel into a strict face-clear region.

    Unlike safe_graphic_xy, this never swaps an explicitly requested 'below'
    panel to the top. A non-fitting layout fails explicitly instead of
    silently deleting a graph, checklist or phone fan from a valid MP4.
    """
    W, H = c.W, c.H
    margin = max(float(W)*0.03, 4.0)
    face_left, face_top, face_right, face_bottom = face_protection_rect(c)
    zones = {
        "above": (margin, min(H*0.48, face_top-margin)),
        "below": (max(H*0.52, face_bottom+margin), H-margin),
    }
    if region not in zones:
        raise ValueError("Expected strict above/below panel region")
    top, bottom = zones[region]
    space_h = max(0.0, bottom-top)
    space_w = W-2*margin
    if space_h <= 0 or space_w <= 0:
        raise ValueError("NO_SAFE_REGION: "+region)
    if width <= 0 or height <= 0:
        raise ValueError("EMPTY_PANEL")
    fit = min(float(max_scale), space_w/float(width), space_h/float(height))
    if fit < min_scale:
        raise ValueError("PANEL_DOES_NOT_FIT_"+region.upper())
    return W/2.0, (top+bottom)/2.0, fit


def place_safe_panel(c, im, region="above", alpha=1.0, min_scale=0.42,
                     max_scale=1.0):
    """Render a complete information unit at a guaranteed strict position."""
    if alpha <= 0: return False
    cx, cy, scale = safe_panel_layout(c, im.width, im.height, region,
                                      min_scale=min_scale,max_scale=max_scale)
    # A proposed safe coordinate is not evidence that a pixel was drawn.
    # The compositor may still reject it because tracking changed the face
    # exclusion box. Count ONLY successfully composited nontransparent pixels.
    painted = place(c, im, cx, cy, scale=scale, alpha=alpha)
    if not painted:
        raise ValueError("SAFE_PANEL_NOT_COMPOSITED_"+region.upper())
    c.visible_safe_panels = getattr(c, "visible_safe_panels", 0)+1
    return True


def executive_motion_cards(c,e,mode="noise"):
    """Distinct face-clear cards: scatter, orbit or carousel (not one template)."""
    W=c.W
    sources=list(getattr(e,'cards',[]) or [])
    if not sources: raise ValueError("MOTION_CARDS_NEED_APPROVED_ASSETS")
    labels=[v.strip() for v in str(e.o.get('labels','')).split('|') if v.strip()]
    if not labels:
        labels=['ILLUSTRATIVE CONCEPT']*len(sources)
    n=max(2,min(4,int(e.o.get('count',3))))
    p=clamp(c.lt/max(.3,e.d))
    w,h=int(W*.86),int(W*.35)
    body=Image.new('RGBA',(w,h),(0,0,0,0))
    background=rrect(w,h,max(5,int(W*.024)),(15,29,41,234))
    body.alpha_composite(background,(0,0))
    d=ImageDraw.Draw(body)
    pad=int(W*.032)
    name={'noise':'IDEA COLLAGE','orbit':'IDEAS IN ORBIT',
          'carousel':'CONTENT CAROUSEL'}.get(mode,'CONCEPT CARDS')
    d.text((pad,W*.039),name,font=font('uim',W*.029),
           fill=(188,215,214,255),anchor='lm')
    def tile(index,tw,th,focus=False):
        src=sources[index%len(sources)].convert('RGB')
        sw,sh=src.size
        thumbw=int(tw*.32);thumbh=int(th*.74)
        ratio=thumbw/max(1,thumbh)
        if sw/sh>ratio:
            crop=int(sh*ratio);src=src.crop(((sw-crop)//2,0,
                                           (sw+crop)//2,sh))
        else:
            crop=int(sw/ratio);src=src.crop((0,(sh-crop)//2,
                                           sw,(sh+crop)//2))
        image=src.resize((max(1,thumbw),max(1,thumbh)),
                         Image.LANCZOS).convert('RGBA')
        pane=rrect(tw,th,max(4,int(W*.013)),
                   (29,49,61,252) if focus else (35,52,65,239))
        pane.alpha_composite(image,(int(W*.014),(th-thumbh)//2))
        dd=ImageDraw.Draw(pane)
        x=int(W*.022)+thumbw
        label=str(labels[index%len(labels)]).upper()
        fsz=lines_fit([label],tw-x-W*.014,'uib',
                      int(W*(.043 if focus else .034)))
        dd.text((x,th*.50),label,font=font('uib',fsz),
                fill=(247,245,239,255),anchor='lm')
        return pane
    if mode=='noise':
        # Independently staggered cards create a genuine layered collage.
        layout=((.035,.29,.44,.58),(.49,.19,.34,.39),(.50,.64,.33,.29))
        for i,(x,y,rw,rh) in enumerate(layout[:n]):
            if c.lt<.09+.12*i: continue
            tw,th=int(w*rw),int(h*rh)
            im=tile(i,tw,th,i==0)
            q=ease_out((c.lt-.09-.12*i)/.35)
            left=int(w*x+(1-q)*W*.022*(1 if i%2 else -1))
            top=int(h*y)
            if top+im.height>h: top=h-im.height
            body.alpha_composite(im,(max(0,left),max(0,top)))
    elif mode=='orbit':
        # Three visible depth-ordered ideas travel along a shallow orbital arc.
        rx=w*.305
        count=3
        for i in range(count):
            angle=2*math.pi*i/count+.40*math.sin(2*math.pi*p)
            depth=math.sin(angle)
            tw=int(W*(.255+.025*(depth+1)))
            th=int(W*.190)
            im=tile(i,tw,th,i==int(p*count)%count)
            cx=w*.50+rx*math.cos(angle)
            cy=h*.55+h*.10*math.sin(angle)
            left=max(0,min(w-im.width,int(cx-im.width/2)))
            top=max(0,min(h-im.height,int(cy-im.height/2)))
            body.alpha_composite(im,(left,top))
    elif mode=='carousel':
        # Horizontal adjacent-card peeks and a clear active central card.
        active=int(p*n)%n
        ww=[int(W*.21),int(W*.38),int(W*.21)]
        hh=int(W*.215)
        positions=[int(w*.035),int(w*.31),int(w*.735)]
        order=[(active-1)%n,active,(active+1)%n]
        for slot,i in enumerate(order):
            im=tile(i,ww[slot],hh,focus=slot==1)
            y=int(h*.23)+int(abs(1-slot)*W*.018)
            body.alpha_composite(im,(positions[slot],y))
        y0=h-W*.026
        d.rounded_rectangle((w*.26,y0,w*.74,y0+W*.007),
                            radius=max(1,W*.004),fill=(69,98,109,255))
        d.rounded_rectangle((w*.26,y0,w*(.26+.48*p),y0+W*.007),
                            radius=max(1,W*.004),fill=(44,154,144,255))
    return place_adaptive_panel(c,body,'above',
                alpha=fade(c,e)*clamp((c.lt-.05)/.18),min_scale=.32)


def adaptive_panel_location(c, width, height, preferred="below", min_scale=.34):
    """Use the speaker's actual negative space; do not erase a panel.

    'below' is a preference for ordinary informational effects, NOT the
    strict named apple-toggles-below variant. Return an explicit region
    before building glass, so the blur samples the true background.
    """
    # A technically valid 0.3x card is often unreadable. Select the
    # LARGER safe region when the preferred one would shrink the content
    # substantially; this choice is made before frosted blur sampling.
    # Explicit named positional variants continue using safe_panel_layout.
    candidates=[]
    for region in (preferred, "above" if preferred=="below" else "below"):
        try:
            cx,cy,scale=safe_panel_layout(c,width,height,region,
                                           min_scale=min_scale)
            candidates.append((region,cx,cy,scale))
        except ValueError:
            continue
    if not candidates:
        raise ValueError("NO_FACE_CLEAR_EDITORIAL_PANEL_FOR_"+preferred.upper())
    chosen=candidates[0]
    for option in candidates[1:]:
        if option[3]>=chosen[3]+.14:
            chosen=option
    if getattr(c,"face_priority",False) and chosen[3]<.55:
        raise ValueError("PANEL_UNREADABLY_SMALL_"+preferred.upper())
    c.last_safe_panel_region=chosen[0]
    c.last_safe_panel_scale=chosen[3]
    return chosen


def place_adaptive_panel(c, image, preferred="below", alpha=1.0,
                         min_scale=.34):
    if alpha<=0: return False
    region,_,_,_=adaptive_panel_location(
        c,image.width,image.height,preferred,min_scale)
    return place_safe_panel(c,image,region,alpha=alpha,
                            min_scale=min_scale)


def comp(c, layer, x, y, alpha=1.0, behind=False, guard=False):
    """Alpha-composite an RGBA layer with its top-left at (x, y).
    behind=True hides it wherever the person is (so it sits behind you).
    guard=True only hides it where it would cover your face."""
    L = to_np(layer) if isinstance(layer, Image.Image) else layer
    h, w = L.shape[:2]; x, y = int(round(x)), int(round(y))
    if alpha <= 0: return False
    executive = bool(getattr(c, "face_priority", False))
    intentional_face_art = getattr(c, "current_fx", None) in _FACE_TOUCH_EFFECTS
    if executive and not behind and (guard or not intentional_face_art):
        preferred = getattr(c, "graphic_region", None)
        pos = safe_graphic_xy(c, x, y, w, h, preferred)
        if pos is None:
            # Do not cover the real eyes/mouth or manufacture an oval gap.
            c.layout_conflicts = getattr(c, "layout_conflicts", 0) + 1
            return False
        x, y = [int(round(v)) for v in pos]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(c.W, x + w), min(c.H, y + h)
    if x1 <= x0 or y1 <= y0: return False
    L = L[y0 - y:y1 - y, x0 - x:x1 - x]
    a = L[..., 3:4] * alpha
    m = np.clip(c.m[y0:y1, x0:x1, None], 0, 1)
    if behind:
        # Actual person segmentation is authoritative where available.
        # Previous max(mask, face_ellipse) caused an obvious oval halo around
        # the hair even when the segmentation correctly followed the person.
        if float(c.m.max()) > 0.08:
            a = a * (1 - m)
        else:
            yy, xx = np.ogrid[y0:y1, x0:x1]
            fw = max(float(c.fw), float(c.W) * 0.045, 1.0)
            e = ((xx - c.fx)/(fw*1.08))**2 + ((yy-c.fy)/(fw*1.44))**2
            fallback = np.clip((1.20-e)/0.30,0,1)[...,None]
            a = a * (1 - fallback)
    elif guard and not executive:
        # Unbranded showcase keeps the historical guarded style.
        yy, xx = np.ogrid[y0:y1, x0:x1]
        fw = max(float(c.fw), float(c.W)*0.045, 1.)
        e = ((xx-c.fx)/(fw*1.07))**2 + ((yy-c.fy)/(fw*1.43))**2
        a = a * (1 - np.clip((1.25-e)/0.3,0,1)[...,None])
    if a.size == 0 or float(a.max()) < (1.0/255):
        return False
    dst = c.img[y0:y1, x0:x1]
    dst[:] = dst * (1 - a) + L[..., :3] * a
    c.last_composited_bounds = (x0,y0,x1,y1)
    return True


def place(c, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0, behind=False, guard=False):
    """Draw a PIL image centred on (cx, cy), scaled and rotated (degrees, counter-clockwise)."""
    if scale <= 0.01 or alpha <= 0: return False
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05: im = im.rotate(rot, Image.BICUBIC, expand=True)
    return comp(c, im, cx - im.width / 2, cy - im.height / 2, alpha, behind, guard)


def camera(c, zoom, cx, cy):
    """Zoom the whole frame (and the person mask) towards (cx, cy). Capped at 2x so it stays sharp."""
    zoom = min(zoom, 2.0)
    if zoom <= 1.002: return
    cw, ch = c.W / zoom, c.H / zoom
    x0 = clamp(cx - cw / 2, 0, c.W - cw); y0 = clamp(cy - ch / 2, 0, c.H - ch)
    M = np.float32([[zoom, 0, -x0 * zoom], [0, zoom, -y0 * zoom]])
    c.img = cv2.warpAffine(c.img, M, (c.W, c.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    c.m = cv2.warpAffine(c.m, M, (c.W, c.H), flags=cv2.INTER_LINEAR)
    c.fx, c.fy, c.fw = (c.fx - x0) * zoom, (c.fy - y0) * zoom, c.fw * zoom


def face_cam(c, zoom, head_at=0.40):
    """Zoom on the face, keeping it at `head_at` of the frame height."""
    z = min(zoom, 2.0)
    camera(c, z, c.fx, c.fy + (c.H / z) * (0.5 - head_at))


def grade(img, kind='moody'):
    lum = (img @ np.float32([0.299, 0.587, 0.114]))[..., None]
    if kind == 'bw':
        g = np.clip((lum - 0.5) * 1.25 + 0.5, 0, 1); return np.repeat(g, 3, axis=2)
    if kind == 'warm': return np.clip(img * np.float32([1.08, 1.0, 0.86]) + 0.02, 0, 1)
    if kind == 'cool': return np.clip(img * np.float32([0.9, 1.0, 1.1]), 0, 1)
    if kind == 'pop':
        o = lum + (img - lum) * 1.35; return np.clip((o - 0.5) * 1.12 + 0.5, 0, 1)
    # moody: a little darker, softer colour, teal shadows, warm highlights, gentle contrast
    o = lum + (img - lum) * 0.6
    o = np.power(np.clip(o, 0, 1), 1.3) * 0.88
    o = o + (1 - lum) * np.float32([-0.03, 0.035, 0.065]) + lum * np.float32([0.05, 0.015, -0.04])
    o = np.clip((o - 0.42) * 1.12 + 0.42, 0, 1)
    return o


_vig = {}
def vignette(c, strength=0.35):
    k = (c.W, c.H)
    if k not in _vig:
        yy, xx = np.ogrid[0:c.H, 0:c.W]
        d = ((xx - c.W / 2) / (c.W * 0.75)) ** 2 + ((yy - c.H / 2) / (c.H * 0.7)) ** 2
        _vig[k] = np.clip(d, 0, 1).astype(np.float32)
    c.img *= (1 - strength * _vig[k])[..., None]


def card(im, w, radius=0.07):
    """A reel-shaped (9:16) rounded card with a soft shadow."""
    h = int(w * 16 / 9)
    src = im.convert('RGB'); sw, sh = src.size
    s = max(w / sw, h / sh)
    src = src.resize((max(w, int(sw * s)), max(h, int(sh * s))), Image.LANCZOS)
    l, t = (src.width - w) // 2, (src.height - h) // 2
    src = src.crop((l, t, l + w, t + h)).convert('RGBA')
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], int(w * radius), fill=255)
    src.putalpha(m)
    ImageDraw.Draw(src).rounded_rectangle([0, 0, w - 1, h - 1], int(w * radius), outline=(0, 0, 0, 70), width=2)
    return shadowed(src, blur=max(6, w // 16), dy=w // 22, alpha=150)


def vary(im, i):
    """Give each card its own look, so a pile of frames reads as different reels."""
    kind = ('pop', 'bw', 'warm', 'cool', 'moody')[i % 5]
    a = np.asarray(im.convert('RGB'), np.float32) / 255
    return Image.fromarray((grade(a, kind) * 255).astype(np.uint8))


def cached(e, key, fn):
    if key not in e.state: e.state[key] = fn()
    return e.state[key]


# ---------- original effect library (all 42 effects) ----------
@effect('noise', 'reels pile up behind your head, one every quarter second')
def fx_noise(c, e):
    if getattr(c,'face_priority',False):
        return executive_motion_cards(c,e,'noise')
    cw = int(c.W * float(e.o.get('size', 0.34)))
    def setup():
        rnd = random.Random(7)
        n = min(16,max(2,int(e.o['count']))) if 'count' in e.o else min(16,max(4,int(e.d/0.22)))
        return [(rnd.uniform(0.14, 0.86), rnd.uniform(0.12, 0.52), rnd.uniform(-7, 7)) for _ in range(n)]
    pos = cached(e, 'pos', setup)
    cards = cached(e, 'cards', lambda: [card(im if e.o.get('brand_cards') or e.o.get('images') is not None else vary(im, i), cw) for i, im in enumerate(e.cards)])
    out = clamp((e.d - c.lt) / 0.2)
    for i, (x, y, r) in enumerate(pos):
        t0 = i * 0.22
        if c.lt < t0: break
        k = ease_back((c.lt - t0) / 0.25)
        place(c, cards[i % len(cards)], x * c.W, y * c.H, 0.6 + 0.4 * k, r, clamp((c.lt - t0) / 0.08) * out, behind=True)


@effect('lineup', 'numbered tiles fan out in an arc above your head')
def fx_lineup(c, e):
    if getattr(c,'face_priority',False):
        W=c.W
        names=[x.strip() for x in str(e.o.get(
            'text','STRATEGY|EXECUTION|OUTCOMES')).split('|') if x.strip()]
        names=names[:4]
        if not names: raise ValueError('lineup requires approved step names')
        w=int(W*.82)
        rh=int(W*.115)
        h=int(W*.055)+rh*len(names)
        im=rrect(w,h,W*.027,(18,31,43,239))
        d=ImageDraw.Draw(im)
        progress=clamp(c.lt/max(.4,e.d*.7))
        shown=max(1,min(len(names),1+int(progress*len(names))))
        for i,name in enumerate(names[:shown]):
            cy=int(W*.055)+(i+.50)*rh
            d.text((W*.055,cy),f'{i+1:02d}',
                   font=font('uib',W*.046),
                   fill=(197,164,109,255),anchor='lm')
            fs=lines_fit([name],w-W*.20,'uib',int(W*.049))
            d.text((W*.19,cy),name.upper(),font=font('uib',fs),
                   fill=(242,244,245,255),anchor='lm')
        return place_safe_panel(c,im,'above',
                                alpha=fade(c,e)*clamp(c.lt/.15),
                                min_scale=.43)
    names = e.o.get('text', '|'.join(NAMES)).split('|')
    tw = int(c.W * 0.105)
    def tile(i, name):
        im = rrect(tw, int(tw * 1.25), tw * 0.16, (24, 24, 28, 225), (255, 255, 255, 60), 2)
        d = ImageDraw.Draw(im)
        num = text_img(f'{i + 1:02d}', tw * 0.42, 'serif', CREAM)
        im.alpha_composite(num, ((tw - num.width) // 2, int(tw * 0.04)))
        words = name.split(' ')
        lines = [' '.join(words[:len(words) // 2 or 1]), ' '.join(words[len(words) // 2 or 1:])] if len(name) > 10 else [name]
        f = font('ui', tw * 0.15)
        for j, ln in enumerate([l for l in lines if l]):
            d.text((tw / 2, tw * (0.78 + 0.19 * j)), ln, font=f, fill=(255, 255, 255, 235), anchor='mm')
        return shadowed(im, 8, 5, 90)
    tiles = cached(e, 'tiles', lambda: [tile(i, n) for i, n in enumerate(names)])
    n = len(tiles); outer = math.ceil(n / 2 + 0.5); inner = n - outer
    cx, cy = c.W / 2 * 0.6 + c.fx * 0.4, c.fy + c.fw * 0.3
    slots = []
    for row, cnt, R in ((0, outer, c.W * 0.47), (1, inner, c.W * 0.33)):
        for k in range(cnt):
            a = math.pi * (0.94 - 0.88 * k / max(1, cnt - 1))
            slots.append((cx + R * math.cos(a), cy - R * math.sin(a) * 1.05, math.degrees(a - math.pi / 2) * 0.3))
    out = clamp((e.d - c.lt) / 0.2)
    for i, (x, y, r) in enumerate(slots[:n]):
        t0 = 0.035 * i
        if c.lt < t0: continue
        k = ease_back((c.lt - t0) / 0.3)
        place(c, tiles[i], x, y + (1 - k) * 40, 0.5 + 0.5 * k, r, clamp((c.lt - t0) / 0.1) * out, behind=True)


@effect('locked-on', 'corner brackets snap onto your face and the camera follows you')
def fx_locked_on(c, e):
    face_cam(c, 1 + (float(e.o.get('zoom', 1.35)) - 1) * ease_out(c.lt / 0.6))
    snap = ease_out(c.lt / 0.22); s = c.fw * 0.85 * (1 + 0.6 * (1 - snap))
    al = clamp(c.lt / 0.12) * clamp((e.d - c.lt) / 0.2)
    size = int(2 * s + 40); im = Image.new('RGBA', (size, int(size * 1.25)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 20, 20, size - 20, im.height - 20; L = int(s * 0.32); wd = max(4, int(c.W / 200))
    for (px, py, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(px, py + dy * L), (px, py), (px + dx * L, py)], fill=(255, 255, 255, 255), width=wd, joint='curve')
    place(c, shadowed(im, 6, 2, 120), c.fx, c.fy, alpha=al)
    tag = text_img(e.o.get('text', 'LOCKED ON').upper(), c.W * 0.022, 'mono', INK)
    pill = rrect(tag.width + 10, tag.height, tag.height / 2, (255, 255, 255, 235)); pill.alpha_composite(tag, (5, 0))
    place(c, pill, c.fx, c.fy + s * 1.25 + pill.height, alpha=clamp((c.lt - 0.15) / 0.15) * al, guard=True)


@effect('orbit', 'your reels circle your head: in front at the bottom, behind you at the top')
def fx_orbit(c, e):
    if getattr(c,'face_priority',False):
        return executive_motion_cards(c,e,'orbit')
    K = int(e.o.get('count', 6)); cw = int(c.W * float(e.o.get('size', 0.2)))
    cards = cached(e, 'cards', lambda: [card(vary(im, i) if e.o.get('images') is None else im, cw) for i, im in enumerate(e.cards)])
    intro, out = ease_out(c.lt / 0.4), clamp((e.d - c.lt) / 0.25)
    rx, ry = c.W * 0.38 * intro, max(c.fw * 1.5, c.H * 0.1)
    oy = c.fy + c.fw * 0.9
    items = []
    for i in range(K):
        th = i * 2 * math.pi / K + c.lt * float(e.o.get('speed', 1.9))
        items.append((math.sin(th), th, i))
    for depth, th, i in sorted(items):
        place(c, cards[i % len(cards)], c.fx + rx * math.cos(th), oy + ry * math.sin(th), (0.78 + 0.24 * (depth + 1) / 2) * (0.5 + 0.5 * intro),
              -6 * math.cos(th), out * clamp(c.lt / 0.15), behind=depth < 0, guard=depth >= 0)


@effect('lean-in', 'a fast punch-in on one word')
def fx_lean_in(c, e):
    z = float(e.o.get('zoom', 1.45))
    face_cam(c, 1 + (z - 1) * ease_out(c.lt / float(e.o.get('speed', 0.18))), 0.42)


@effect('backdrop-word', 'a giant word drops in behind you')
def fx_backdrop_word(c, e):
    word=str(e.o.get('text','STRATEGY')).upper()[:32]
    k=ease_out(c.lt/.42)
    al=fade(c,e)*clamp(c.lt/.12)
    if getattr(c,'face_priority',False):
        W=c.W
        bw,bh=int(W*.86),int(W*.21)
        panel=rrect(bw,bh,int(W*.022),(17,29,40,218))
        d=ImageDraw.Draw(panel)
        font_size=lines_fit([word],bw*.90,'didoneb',int(W*.10))
        d.text((bw/2,bh/2),word,font=font('didoneb',font_size),
               fill=rgb(e.o.get('color'),(207,177,124))+(255,),
               anchor='mm')
        place_safe_panel(c,panel,'above',alpha=al*k,min_scale=.52)
    else:
        im=cached(e,'w',lambda:fit_text(word,c.W*.94,
             e.o.get('font','bold'),fill=rgb(e.o.get('color'),CREAM),
             shadow=10))
        y,scale=c.fy-c.fw*1.05,1.
        place(c,im,c.W/2,y-(1-k)*im.height,scale=scale,
              alpha=al,behind=True)

@effect('spotlight', 'kill the lights, keep you lit')
def fx_spotlight(c, e):
    if e.o.get('look') == 'sparkle': return spotlight_sparkle(c, e)
    face_cam(c, 1 + (float(e.o.get('push', 1.1)) - 1) * ease_inout(c.lt / e.d))
    k = ramp(c, e, 0.3, 0.25)
    xx, yy = grid(c)
    d = ((xx - c.fx) / (c.W * 0.5)) ** 2 + ((yy - (c.fy + c.H * 0.2)) / (c.H * 0.46)) ** 2
    pool = np.clip(1 - d, 0, 1) ** 1.6
    bright = 1 - k * float(e.o.get('dim',1.0)) * (1 - (0.2 + 0.45 * pool))
    f = bright * (1 - c.m) + c.m * (1 + 0.04 * k)
    if e.o.get('text'):
        word = e.o['text']; col = rgb(e.o.get('color'), PEACH)
        im = cached(e, 'w', lambda: fit_text(word, c.W * 0.9, e.o.get('font', 'serif'), fill=col, glow=(col, 26)))
        c.img *= f[..., None]
        place(c, im, c.W / 2, c.fy - c.fw * 1.1, alpha=k, behind=True)
    else:
        c.img *= f[..., None]


@effect('the-bill', 'prints every instruction like a ticket, into the wall above your head')
def fx_bill(c, e):
    lines = e.o.get('text', 'DEMO EDIT NOTES|STRATEGY|EXECUTION|EXAMPLE ONLY').split('|')
    def build():
        pw = int(c.W * 0.72); lh = max(10,int(pw * 0.105)); pad = int(pw * 0.055)
        h = pad * 2 + lh * (len(lines) + 1)
        im = Image.new('RGBA', (pw, h), CREAM + (255,)); d = ImageDraw.Draw(im)
        fontsize = lh * 0.69
        while fontsize > 11 and max(font('mono',fontsize).getlength(ln) for ln in lines) > pw - pad*2:
            fontsize *= 0.94
        f = font('mono', fontsize)
        for i, ln in enumerate(lines):
            y = pad + lh * i + (lh if i == len(lines) - 1 else 0)
            if i == len(lines) - 1:
                for x in range(pad, pw - pad, 14): d.line([(x, y - lh * 0.45), (x + 7, y - lh * 0.45)], fill=INK + (140,), width=2)
            d.text((pad, y), ln, font=f, fill=INK + (255,))
        return im
    rec = cached(e, 'r', build)
    if getattr(c,'face_priority',False):
        # The original print animation clipped the lower lines or moved the
        # paper through the hair when the camera framing changed.
        place_safe_panel(c,rec,'above',
                         alpha=fade(c,e)*clamp(c.lt/.16),
                         min_scale=.30)
        return
    slot_y, sw = c.H * 0.028, c.W * 0.77
    max_h = max(80, c.fy - c.fw * 1.3 - slot_y)
    s = min(1.0, max_h / rec.height)
    pr = ease_inout(c.lt / (e.d * 0.75)); L = int(rec.height * pr)
    al = clamp((e.d - c.lt) / 0.25)
    cx = c.W / 2
    if L > 2:
        paper = rec.crop((0, 0, rec.width, L))
        z = 14; jag = Image.new('RGBA', (rec.width, L + z), (0, 0, 0, 0)); jag.paste(paper, (0, 0))
        ImageDraw.Draw(jag).polygon([(x, L) for x in range(0, rec.width + 1, 2 * z)] + [(rec.width, L)] +
                                    [(x + z, L + z) for x in range(rec.width - 2 * z, -1, -2 * z)], fill=CREAM + (255,))
        paper = shadowed(jag, 10, 6, 90)
        if s < 1: paper = paper.resize((int(paper.width * s), int(paper.height * s)), Image.BILINEAR)
        comp(c, paper, cx - paper.width / 2, slot_y - 10 * s, al, behind=True)
    slot = rrect(sw, c.H * 0.03, c.H * 0.015, (30, 30, 34, 255), (90, 90, 96, 255), 3)
    place(c, shadowed(slot, 10, 6, 140), cx, slot_y, alpha=al * clamp(c.lt / 0.15), behind=True)


@effect('moody', 'a moody colour grade: darker, softer, teal shadows')
def fx_moody(c, e):
    k = ramp(c, e, 0.35, 0)
    # Retain natural skin; the executive preset is a restrained grade,
    # not a full grey/cyan replacement of the recorded camera color.
    mix = min(.30, float(e.o.get('strength',.28))) if getattr(c,'face_priority',False) else 1.0
    c.img = c.img*(1-k*mix)+grade(c.img,e.o.get('grade','warm'))*k*mix
    vignette(c, float(e.o.get('vignette_strength',0.4)) * k)


@effect('swipe', 'a before and after slider that sweeps across you')
def fx_swipe(c, e):
    """Source-authentic A/B grade comparison, no divider through the face."""
    W=c.W
    phase=ease_inout(c.lt/max(.30,e.d*.77))
    source=c.img.copy()
    target=grade(source,e.o.get('grade','warm'))
    c.img=source*(1-phase)+target*phase
    if not getattr(c,'face_priority',False):
        return
    # The two images depict exactly the same original camera frame before
    # and after the requested grade; no invented business/visual result.
    cw,ch=int(W*.84),int(W*.35)
    deck=rrect(cw,ch,max(5,int(W*.027)),(17,32,43,246))
    d=ImageDraw.Draw(deck)
    tile_w=int(W*.32);tile_h=int(W*.245)
    for index,imarray in enumerate((source,target)):
        arr=(np.clip(imarray,0,1)*255).astype(np.uint8)
        ih,iw=arr.shape[:2]
        aspect=tile_w/tile_h
        crop_w=min(iw,int(ih*aspect))
        crop_h=min(ih,int(iw/aspect))
        ax=(iw-crop_w)//2;ay=max(0,int(ih*.23-crop_h*.5))
        ay=min(ay,ih-crop_h)
        tile=Image.fromarray(arr[ay:ay+crop_h,ax:ax+crop_w]).resize(
            (tile_w,tile_h),Image.Resampling.LANCZOS).convert('RGBA')
        x=int(W*(.075 if index==0 else .44))
        y=int(W*.045)
        deck.alpha_composite(tile,(x,y))
        label=('ORIGINAL' if index==0 else 'GRADED')
        d.text((x+tile_w/2,W*.315),label,
               font=font('uib',int(W*.040)),
               fill=(244,242,236,255),anchor='mm')
    # The divider is INSIDE the comparison only, never across eyes/mouth.
    dx=cw*.50
    d.line((dx,W*.065,dx,W*.264),
           fill=(197,164,109,255),width=max(2,W//115))
    place_adaptive_panel(c,deck,'above',
              alpha=fade(c,e)*clamp(c.lt/.14),min_scale=.48)


@effect('todo', 'a checklist card beside your head that ticks off as you talk')
def fx_todo(c, e):
    items = e.o.get('text', 'Strategy|Execution|Measurable value').split('|')
    # ticks = video seconds when each item gets ticked (e.g. when you say it); default is evenly spaced
    ticks = [float(t) - e.start for t in str(e.o['ticks']).split('|')] if e.o.get('ticks') else [e.d * (i + 1) / (len(items) + 1) for i in range(len(items))]
    if not 1 <= len(items) <= 4:
        raise ValueError('todo requires 1-4 verified short items for readable phone video')
    cw = int(c.W * 0.72); lh = max(16,int(cw * 0.142)); pad = int(cw * 0.065)
    im = rrect(cw, pad * 2 + lh * (len(items) + 1), cw * 0.07, (250, 248, 242, 235)); d = ImageDraw.Draw(im)
    done = sum(c.lt >= t for t in ticks)
    d.text((pad, pad), e.o.get('title', 'TO DO').upper(), font=font('ui', lh * 0.42), fill=(200, 140, 20, 255))
    d.text((cw - pad, pad), f'{done} of {len(items)}', font=font('ui', lh * 0.36), fill=(120, 120, 120, 255), anchor='ra')
    f = font('uim', lh * 0.48)
    for it in items:
        if f.getlength(it) > cw-pad*2-lh*.80:
            raise ValueError('todo label is too long for phone-sized display')
    for i, it in enumerate(items):
        y = pad + lh * (i + 1); bx = lh * 0.42
        d.rounded_rectangle([pad, y + lh * 0.12, pad + bx, y + lh * 0.12 + bx], 6, outline=(160, 160, 160, 255), width=3)
        d.text((pad + bx * 1.5, y + lh * 0.1), it, font=f, fill=INK + (255,))
        if c.lt >= ticks[i]:
            k = ease_out((c.lt - ticks[i]) / 0.25)
            d.rounded_rectangle([pad, y + lh * 0.12, pad + bx, y + lh * 0.12 + bx], 6, fill=(52, 199, 89, 255))
            d.line([(pad + bx * .22, y + lh * .12 + bx * .52), (pad + bx * .42, y + lh * .12 + bx * .74), (pad + bx * .8, y + lh * .12 + bx * .28)], fill=(255, 255, 255, 255), width=4)
            tw = f.getlength(it) * k
            d.line([(pad + bx * 1.5, y + lh * 0.36), (pad + bx * 1.5 + tw, y + lh * 0.36)], fill=INK + (255,), width=3)
    left = c.fx > c.W / 2
    x = c.W * 0.05 + cw / 2 if left else c.W * 0.95 - cw / 2
    pop = ease_back(c.lt / 0.3)
    if getattr(c,'face_priority',False):
        # Prefer an upper checklist; when the upper strip is too short
        # explicitly choose a readable lower composition. Never silently
        # delete the entire card or punch an oval through its rows.
        try:
            safe_panel_layout(c, im.width, im.height,'above',
                              min_scale=.42)
            region='above'
        except ValueError:
            safe_panel_layout(c,im.width,im.height,'below',
                              min_scale=.42)
            region='below'
        place_safe_panel(c,im,region,
                         alpha=clamp(c.lt/.12)*fade(c,e),
                         min_scale=.42)
    else:
        place(c,shadowed(im,14,8,90),x,
              max(im.height/2+c.H*.06,c.fy-c.fw*1.4),
              .8+.2*pop,0,clamp(c.lt/.12)*fade(c,e),behind=True)


def heart(size, color=(255, 48, 64)):
    s = int(size); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(s / 2 + s * 0.48 * (16 * math.sin(t) ** 3) / 16, s * 0.46 - s * 0.46 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
           for t in np.linspace(0, 2 * math.pi, 60)]
    d.polygon(pts, fill=color + (255,)); return im


def comment_bar(c, e):
    """Readable intentional quote; no simulated posting/replies as facts."""
    W=c.W
    quote=str(e.o.get('text') or 'ILLUSTRATIVE COMMENT')[:70]
    w,h=int(W*.82),int(W*.30)
    panel=rrect(w,h,int(W*.028),(19,34,46,239))
    d=ImageDraw.Draw(panel)
    pad=int(W*.046)
    d.text((pad,h*.20),'COMMENT / QUOTE',
           font=font('uib',W*.034),fill=(196,215,221,255),
           anchor='lm')
    fs=lines_fit([quote],w-2*pad,'uib',int(W*.053))
    d.text((pad,h*.57),quote,font=font('uib',fs),
           fill=(244,246,247,255),anchor='lm')
    d.line((pad,h*.82,w-pad,h*.82),fill=(44,154,144,220),
           width=max(2,W//110))
    place_safe_panel(c,panel,'above',alpha=fade(c,e)*clamp(c.lt/.15),
                     min_scale=.45)

@effect('tap', 'a Follow button pops up and flips to Following')
def fx_tap(c, e):
    """One coherent button/ripple unit; both always share the same anchor."""
    W=c.W
    bw,bh=int(W*.42),int(W*.135)
    at=float(e.o['at'])-e.start if e.o.get('at') else e.d*.45
    on=c.lt>=at
    col=rgb(e.o.get('color'),(44,154,144)) if on else (44,116,165)
    gw,gh=int(W*.65),int(W*.24)
    layer=Image.new('RGBA',(gw,gh),(0,0,0,0))
    button=rrect(bw,bh,int(W*.025),col+(255,))
    d=ImageDraw.Draw(button)
    d.text((bw/2,bh/2),'Following' if on else '+ Follow',
           font=font('uib',W*.052),fill=(255,255,255,255),anchor='mm')
    layer.alpha_composite(button,((gw-bw)//2,(gh-bh)//2))
    if on and c.lt-at<.45:
        q=clamp((c.lt-at)/.45)
        r=int(bh*(.68+.32*q))
        ring=Image.new('RGBA',(gw,gh))
        ImageDraw.Draw(ring).ellipse(
            (gw/2-r,gh/2-r,gw/2+r,gh/2+r),
            outline=(230,248,244,int(200*(1-q))),width=max(2,W//120))
        layer.alpha_composite(ring)
    place_safe_panel(c,layer,'below',alpha=fade(c,e)*clamp(c.lt/.12),
                     min_scale=.40)

def hand_path(d, pts, color, width, frac):
    n = max(2, int(len(pts) * clamp(frac)))
    if frac > 0: d.line(pts[:n], fill=color, width=width, joint='curve')
    return pts[n - 1]


def arrow_pts(x0, y0, x1, y1, bend=0.25, n=40):
    mx, my = (x0 + x1) / 2 - (y1 - y0) * bend, (y0 + y1) / 2 + (x1 - x0) * bend
    return [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1) for t in np.linspace(0, 1, n)]


def arrow_head(d, pts, color, width, size):
    (xa, ya), (xb, yb) = pts[-4], pts[-1]; a = math.atan2(yb - ya, xb - xa)
    for s in (2.6, -2.6):
        d.line([(xb, yb), (xb + size * math.cos(a + s), yb + size * math.sin(a + s))], fill=color, width=width)


@effect('pause-point', 'freeze the frame and point at something with a hand-drawn arrow')
def fx_pause_point(c, e):
    if 'f' not in e.state:
        e.state['f']=(c.img.copy(),c.m.copy(),c.fx,c.fy,c.fw)
    img,m,c.fx,c.fy,c.fw=e.state['f']
    c.img,c.m=img.copy(),m.copy()
    # Freeze the camera, draw toward a verified on-screen idea. A missing
    # target defaults to background shelf space, never the real eyes.
    W,H=c.W,c.H
    target_x=W*float(e.o.get('target_x',.78))
    target_y=H*float(e.o.get('target_y',.16))
    if overlaps_face(c,target_x-W*.02,target_y-W*.02,W*.04,W*.04):
        # Put the target within actual negative space, not on the face.
        try:
            target_x,target_y,_=safe_panel_layout(c,W*.10,W*.10,'above',
                                                  min_scale=.35)
        except ValueError:
            target_x,target_y,_=safe_panel_layout(c,W*.10,W*.10,'below',
                                                  min_scale=.35)
    label=str(e.o.get('text','KEY DETAIL'))[:32].upper()
    panel=rrect(int(W*.76),int(W*.18),int(W*.026),
                (18,31,42,236))
    d=ImageDraw.Draw(panel)
    f=lines_fit([label],panel.width*.88,'uib',int(W*.065))
    d.text((panel.width/2,panel.height/2),label,
           font=font('uib',f),fill=(247,243,232,255),anchor='mm')
    place_safe_panel(c,panel,'above',alpha=clamp(c.lt/.18)*fade(c,e),
                     min_scale=.45)
    # Mark the factual target with a compact, unobtrusive ring.
    radius=max(5,int(W*.020))
    im=Image.new('RGBA',(radius*3,radius*3),(0,0,0,0))
    col=rgb(e.o.get('color'),(197,164,109))+(255,)
    ImageDraw.Draw(im).ellipse((radius*.5,radius*.5,
         radius*2.5,radius*2.5),outline=col,width=max(2,W//130))
    place(c,im,target_x,target_y,alpha=fade(c,e)*clamp(c.lt/.2))

@effect('uninstall', 'a glitchy uninstall bar that breaks the frame apart')
def fx_uninstall(c, e):
    p = clamp(c.lt / e.d); g = p ** 1.6
    rnd = np.random.default_rng(int(c.t * 30))
    sh = int(g * c.W * 0.025)
    if sh: c.img = np.stack([np.roll(c.img[..., 0], sh, 1), c.img[..., 1], np.roll(c.img[..., 2], -sh, 1)], -1)
    for _ in range(int(2 + g * 10)):
        y0 = int(rnd.uniform(0, c.H)); hh = int(rnd.uniform(8, 60)); off = int(rnd.uniform(-1, 1) * g * c.W * 0.08)
        c.img[y0:y0 + hh] = np.roll(c.img[y0:y0 + hh], off, 1)
    if p > 0.82:
        q = (p - 0.82) / 0.18; f = 1 + int(q * 40)
        small = cv2.resize(c.img, (max(1, c.W // f), max(1, c.H // f)), interpolation=cv2.INTER_AREA)
        c.img = cv2.resize(small, (c.W, c.H), interpolation=cv2.INTER_NEAREST) * (1 - 0.6 * q)
    bw, bh = int(c.W * 0.7), int(c.W * 0.2)
    im = rrect(bw, bh, 22, (245, 245, 247, 240)); d = ImageDraw.Draw(im)
    d.text((bw * 0.06, bh * 0.28), e.o.get('text', 'Uninstalling...'), font=font('ui', bh * 0.18), fill=INK + (255,), anchor='lm')
    d.rounded_rectangle([bw * 0.06, bh * 0.56, bw * 0.94, bh * 0.7], 8, fill=(215, 215, 220, 255))
    d.rounded_rectangle([bw * 0.06, bh * 0.56, bw * 0.06 + bw * 0.88 * max(0.03, ease_inout(p)), bh * 0.7], 8, fill=(0, 122, 255, 255))
    d.text((bw * 0.94, bh * 0.85), f'{int(ease_inout(p) * 100)}%', font=font('ui', bh * 0.13), fill=(110, 110, 110, 255), anchor='rm')
    place(c, shadowed(im, 16, 8, 120), c.W / 2, c.H * 0.16, 0.8 + 0.2 * ease_back(c.lt / 0.3), 0, clamp(c.lt / 0.1))


def reel_icons(size, likes=None, comments=None):
    """Social-frame icons are decorative; counts need explicit provenance."""
    s = int(size); im = Image.new('RGBA', (s, int(s * 3.6)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w = max(3, s // 12)
    h = heart(s * 0.8, (255, 255, 255)); im.alpha_composite(h, (int(s * 0.1), 0))
    if likes is not None:
        d.text((s / 2, s * 0.95), str(likes), font=font('ui', s * 0.24), fill=(255, 255, 255, 255), anchor='mm')
    d.ellipse([s * 0.15, s * 1.25, s * 0.85, s * 1.95], outline=(255, 255, 255, 255), width=w)
    if comments is not None:
        d.text((s / 2, s * 2.15), str(comments), font=font('ui', s * 0.24), fill=(255, 255, 255, 255), anchor='mm')
    d.polygon([(s * 0.12, s * 2.75), (s * 0.9, s * 2.45), (s * 0.55, s * 3.25), (s * 0.45, s * 2.88)], outline=(255, 255, 255, 255), width=w)
    return im


@effect('reel-frame', 'your video shrinks into an Instagram reel card')
def fx_reel_frame(c, e):
    k = ease_out(c.lt / 0.35) * clamp((e.d - c.lt) / 0.3)
    if k <= 0: return
    s = 1 - 0.2 * k
    small = cv2.resize(c.img, (c.W // 16, c.H // 16), interpolation=cv2.INTER_AREA)
    bg = cv2.GaussianBlur(cv2.resize(small, (c.W, c.H), interpolation=cv2.INTER_LINEAR), (0, 0), 12) * (1 - 0.45 * k)
    iw, ih = int(c.W * s), int(c.H * s)
    inset = cv2.resize(c.img, (iw, ih), interpolation=cv2.INTER_AREA)
    m = to_np(rrect(iw, ih, c.W * 0.05 * k + 1, (255, 255, 255, 255)))[..., 3:4]
    x0, y0 = (c.W - iw) // 2, int((c.H - ih) * 0.42)
    out = bg.copy(); reg = out[y0:y0 + ih, x0:x0 + iw]; reg[:] = reg * (1 - m) + inset * m
    c.img = out
    mm = np.zeros_like(c.m); mm[y0:y0 + ih, x0:x0 + iw] = cv2.resize(c.m, (iw, ih)); c.m = mm
    c.fx, c.fy, c.fw = x0 + c.fx * s, y0 + c.fy * s, c.fw * s
    verified=e.o.get('metrics_verified') is True
    likes=e.o.get('likes') if verified else None
    comments=e.o.get('comments') if verified else None
    ic = cached(e, 'ic', lambda: shadowed(reel_icons(c.W * 0.075,likes,comments), 6, 2, 120))
    comp(c, ic, x0 + iw - ic.width - c.W * 0.01, y0 + ih * 0.52, k)
    hdl=fit_text(e.o.get('text','@aiwithswarag'),
                 iw*.70,'uib',int(c.W*.050),
                 fill=(255,255,255),shadow=5)
    # One coherent, readable inset credit strip.
    hbg=rrect(int(min(iw*.83,hdl.width+c.W*.11)),
               int(hdl.height+c.W*.055),max(4,int(c.W*.013)),
               (14,26,35,222))
    hbg.alpha_composite(hdl,(int(c.W*.035),
           max(0,(hbg.height-hdl.height)//2)))
    comp(c,hbg,x0+c.W*.035,y0+ih-hbg.height-c.W*.055,k)


@effect('shortcut-rain', 'keyboard keys rain down behind you')
def fx_shortcut_rain(c, e):
    if getattr(c,'face_priority',False):
        W=c.W
        keys=[x.strip() for x in str(e.o.get(
            'text','CMD|TAB|SHIFT|ENTER')).split('|') if x.strip()][:4]
        w,h=int(W*.82),int(W*.27)
        layer=rrect(w,h,int(W*.026),(16,29,41,238))
        d=ImageDraw.Draw(layer)
        d.text((W*.04,h*.22),'KEYBOARD SHORTCUTS',
               font=font('uib',W*.038),fill=(217,230,231,255),
               anchor='lm')
        row_y=h*.56
        key_gap=W*.02
        available=w-W*.07-key_gap*(len(keys)-1)
        key_w=available/max(1,len(keys))
        for i,key in enumerate(keys):
            x=W*.035+i*(key_w+key_gap)
            enter=clamp((c.lt-.09-i*.10)/.18)
            y=row_y+(1-enter)*W*.02
            d.rounded_rectangle((x,y-key_w*.25,x+key_w,y+key_w*.36),
                                radius=max(3,int(W*.01)),
                                fill=(238,239,234,int(255*enter)))
            fs=lines_fit([key.upper()],key_w*.84,'uim',int(W*.043))
            d.text((x+key_w/2,y+key_w*.07),key.upper(),
                   font=font('uim',fs),fill=(23,37,49,int(255*enter)),
                   anchor='mm')
        return place_safe_panel(c,layer,'above',alpha=fade(c,e)*clamp(c.lt/.10),
                                min_scale=.45)
    keys=e.o.get('text','cmd|/|C|V|Z|esc|tab|shift|enter|opt').split('|')
    ks=int(c.W*.1)
    def cap(k):
        w=max(ks,int(font('mono',ks*.36).getlength(k)+ks*.5))
        im=rrect(w,ks,ks*.18,(190,190,198,255))
        top=rrect(w-8,ks-14,ks*.16,(246,246,248,255))
        im.alpha_composite(top,(4,3))
        ImageDraw.Draw(im).text((w/2,ks*.44),k,
                font=font('mono',ks*.36),fill=INK+(255,),anchor='mm')
        return shadowed(im,8,6,100)
    caps=cached(e,'caps',lambda:[cap(k) for k in keys])
    parts=cached(e,'p',lambda:[
        (random.Random(i).random(),
         random.Random(i+99).random()*max(.1,e.d-.8),
         .45+.4*random.Random(i+7).random(),
         random.Random(i+3).uniform(-25,25),
         random.Random(i+5).uniform(-60,60))
         for i in range(int(e.o.get('count',26)))])
    for i,(x,t0,v,r0,w) in enumerate(parts):
        if c.lt<t0: continue
        y=-ks+(c.lt-t0)*v*c.H
        place(c,caps[i%len(caps)],c.W*(.04+.92*x),y,
              .75+.35*v,r0+w*(c.lt-t0),fade(c,e),behind=True)

@effect('reject-stamp', 'a big red stamp slams onto the screen')
def fx_reject_stamp(c, e):
    """Legible judgment stamp with contrast plate, never over facial details."""
    W=c.W
    txt=str(e.o.get('text','REJECTED')).upper()[:26]
    w,h=int(W*.74),int(W*.215)
    im=rrect(w,h,int(W*.022),(20,32,43,242))
    d=ImageDraw.Draw(im)
    edge=(197,164,109,255)
    pad=int(W*.016)
    d.rounded_rectangle((pad,pad,w-pad,h-pad),
                        radius=int(W*.014),outline=edge,
                        width=max(2,int(W*.008)))
    fs=lines_fit([txt],w-pad*5,'uib',int(W*.090))
    d.text((w/2,h/2),txt,font=font('uib',fs),
           fill=(242,235,218,255),anchor='mm')
    place_safe_panel(c,im,'below',
                     alpha=fade(c,e)*ease_out(c.lt/.21),
                     min_scale=.40)

@effect('countdown-flip', 'a 3, 2, 1 flip clock above your head')
def fx_countdown(c, e):
    n0 = int(e.o.get('from', 3)); seg = e.d / n0
    i = min(n0 - 1, int(c.lt / seg)); cur, prev = n0 - i, n0 - i + 1
    f = clamp((c.lt - i * seg) / 0.3) if i > 0 else 1.0
    tw, th = int(c.W * 0.3), int(c.W * 0.38)
    def half(num, top):
        im = rrect(tw, th, tw * 0.1, (30, 30, 34, 255)); d = ImageDraw.Draw(im)
        d.text((tw / 2, th / 2), str(num), font=font('bold', th * 0.62), fill=CREAM + (255,), anchor='mm')
        return im.crop((0, 0, tw, th // 2)) if top else im.crop((0, th // 2, tw, th))
    hv = cached(e, 'h', lambda: {(n, t): half(n, t) for n in range(0, n0 + 2) for t in (True, False)})
    im = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    im.paste(hv[(cur, True)], (0, 0)); im.paste(hv[(prev if f < 1 else cur, False)], (0, th // 2))
    if f < 0.5:
        h = max(1, int(th / 2 * (1 - 2 * f))); fl = hv[(prev, True)].resize((tw, h)); im.paste(fl, (0, th // 2 - h))
    elif f < 1:
        h = max(1, int(th / 2 * (2 * f - 1))); fl = hv[(cur, False)].resize((tw, h)); im.paste(fl, (0, th // 2))
    ImageDraw.Draw(im).line([(0, th // 2), (tw, th // 2)], fill=(0, 0, 0, 255), width=4)
    y = max(th / 2 + c.H * 0.05, c.fy - c.fw * 2.3)
    place(c, shadowed(im, 16, 10, 120), c.W / 2 * 0.6 + c.fx * 0.4, y, 0.7 + 0.3 * ease_back(c.lt / 0.3), 0, clamp((e.d - c.lt) / 0.2), behind=True)


_rect = {}
@effect('rabbit-hole', 'the frame tunnels into itself, spinning')
def fx_rabbit_hole(c, e):
    k = ease_out(c.lt / 0.4) * clamp((e.d - c.lt) / 0.3)
    if k <= 0: return
    if (c.W, c.H) not in _rect:
        a = np.ones((c.H, c.W), np.float32); b = np.zeros((c.H, c.W), np.float32); t = max(4, c.W // 120)
        b[:t] = b[-t:] = 1; b[:, :t] = b[:, -t:] = 1; _rect[(c.W, c.H)] = (a, b)
    ones, border = _rect[(c.W, c.H)]
    r = float(e.o.get('ratio', 0.62)); z = (c.lt * float(e.o.get('speed', 0.8))) % 1.0
    src = c.img; cx, cy = c.fx, c.fy
    out = None
    for lev in range(0, 7):
        s = r ** (lev - z * k) if lev else 1.0
        ang = (lev - z) * float(e.o.get('spin', 10)) * k if lev else 0
        if lev and s < 0.03: break
        M = cv2.getRotationMatrix2D((cx, cy), ang, s)
        if lev == 0:
            out = src.copy(); continue
        L = cv2.warpAffine(src, M, (c.W, c.H), flags=cv2.INTER_LINEAR)
        a = cv2.warpAffine(ones, M, (c.W, c.H))[..., None] * k
        bd = cv2.warpAffine(border, M, (c.W, c.H))[..., None] * k
        out = out * (1 - a) + L * a
        out = out * (1 - bd) + bd
    m = c.m[..., None] * k  # you stay in front while the room tunnels behind you
    c.img = out * (1 - m) + src * m


@effect('cover-star', 'you become a magazine cover, with the title behind your head')
def fx_cover_star(c, e):
    if e.o.get('look')=='editorial':
        return cover_editorial(c,e)
    """A composed magazine masthead, not independent overlapping words."""
    W,H=c.W,c.H
    al=fade(c,e)*clamp(c.lt/.15)
    title=str(e.o.get('text','EXECUTION')).upper()[:28]
    issue=str(e.o.get('issue','SWARAG / EXECUTIVE')).upper()[:34]
    lines=[x.strip() for x in str(e.o.get(
        'lines','DIRECTION|DELIVERY')).split('|') if x.strip()][:2]
    pw=int(W*.87);ph=int(W*.37)
    lay=Image.new('RGBA',(pw,ph),(0,0,0,0))
    d=ImageDraw.Draw(lay)
    d.rounded_rectangle((0,0,pw,ph),radius=int(W*.025),
                        fill=(14,24,35,212))
    pad=int(W*.045)
    d.text((pad,int(W*.052)),issue,font=font('uim',W*.030),
           fill=(224,234,236,255))
    mastsize=lines_fit([title],pw-2*pad,'didoneb',int(W*.108))
    d.text((pad,int(W*.104)),title,font=font('didoneb',mastsize),
           fill=rgb(e.o.get('color'),(197,164,109))+(255,))
    rule=int(W*.22)
    d.line((pad,rule,pw-pad,rule),fill=(197,164,109,220),
           width=max(1,int(W*.006)))
    for j,line in enumerate(lines):
        fs=lines_fit([line],pw-2*pad,'uib',int(W*.042))
        d.text((pad,rule+int(W*(.028+.062*j))),line.upper(),
               font=font('uib',fs),fill=(241,244,245,255))
    place_safe_panel(c,lay,'above',alpha=al,min_scale=.47)

@effect('scribble', 'marker doodles draw themselves around you')
def fx_scribble(c, e):
    if getattr(c,'face_priority',False):
        # Marker on a genuine, source-approved target instead of a halo
        # drawn through the speaker's hair and expressions.
        W,H=c.W,c.H
        px=W*float(e.o.get('target_x',.72))
        py=H*float(e.o.get('target_y',.16))
        if overlaps_face(c,px-W*.09,py-W*.09,W*.18,W*.18):
            # Choose a face-clear target automatically; never annotate eyes.
            try:
                px,py,_=safe_panel_layout(c,W*.18,W*.18,'above',
                                          min_scale=.35)
            except ValueError:
                px,py,_=safe_panel_layout(c,W*.18,W*.18,'below',
                                          min_scale=.35)
        col=rgb(e.o.get('color'),(44,154,144))+(255,)
        r=max(7,int(W*.057))
        deco=Image.new('RGBA',(r*3,r*3))
        d=ImageDraw.Draw(deco)
        q=clamp(c.lt/.48)
        if q>0:
            start=-90
            d.arc((r*.4,r*.4,r*2.6,r*2.6),start,
                  start+int(330*q),fill=col,width=max(2,W//110))
        place(c,deco,px,py,alpha=fade(c,e))
        label=str(e.o.get('text','KEY DETAIL'))[:30].upper()
        im=rrect(int(W*.70),int(W*.16),int(W*.02),(18,34,46,231))
        d=ImageDraw.Draw(im)
        fs=lines_fit([label],im.width*.90,'uib',int(W*.055))
        d.text((im.width/2,im.height/2),label,
               font=font('uib',fs),fill=(238,247,247,255),anchor='mm')
        place_safe_panel(c,im,'above',
                         alpha=fade(c,e)*clamp((c.lt-.25)/.18),
                         min_scale=.45)
        return
    col = rgb(e.o.get('color'), YELLOW) + (255,); wd = max(6, c.W // 130)
    lay = Image.new('RGBA', (c.W, c.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rx, ry = c.fw * 1.0, c.fw * 1.3
    angs = np.linspace(-1.9, -1.9 + 2 * math.pi * 1.08, 70)
    ring = [(c.fx + rx * (1 + 0.04 * math.sin(3 * a)) * math.cos(a), c.fy + ry * (1 + 0.04 * math.cos(2 * a)) * math.sin(a)) for a in angs]
    hand_path(d, ring, col, wd, ease_inout(c.lt / 0.5))
    lx, ly = clamp(c.fx + c.fw * 2.3, c.W * 0.2, c.W * 0.8), max(c.H * 0.08, c.fy - c.fw * 2.4)
    pts = arrow_pts(lx - c.fw * 0.3, ly + c.fw * 0.5, c.fx + rx * 0.85, c.fy - ry * 0.75, -0.3)
    k2 = ease_out((c.lt - 0.45) / 0.35)
    if k2 > 0: hand_path(d, pts, col, wd, k2)
    if k2 >= 0.99: arrow_head(d, pts, col, wd, c.W * 0.035)
    for j, (sx, sy) in enumerate(((c.fx - c.fw * 1.9, c.fy - c.fw * 1.2), (c.fx - c.fw * 1.5, c.fy + c.fw * 0.6), (c.fx + c.fw * 1.6, c.fy + c.fw * 0.3))):
        ks = ease_back((c.lt - 0.8 - 0.1 * j) / 0.25) * c.fw * 0.28
        if ks > 0:
            d.line([(sx - ks, sy), (sx + ks, sy)], fill=col, width=wd); d.line([(sx, sy - ks), (sx, sy + ks)], fill=col, width=wd)
    al = clamp((e.d - c.lt) / 0.2)
    comp(c, to_np(lay), 0, 0, al)
    if c.lt > 0.7:
        lab = text_img(e.o.get('text', 'me!'), c.W * 0.075, 'hand', col[:3], shadow=6)
        place(c, lab, lx, ly - lab.height * 0.15, 0.7 + 0.3 * ease_back((c.lt - 0.7) / 0.3), 8, al)


# ---------- pack 2: app-style effects (added 21 Oct 2026) ----------
def pop(c, t0, dur=0.3): return ease_back((c.lt - t0) / dur) if c.lt > t0 else 0.0
def fade(c, e, t=0.2): return clamp((e.d - c.lt) / t)
GREEN, BLUE, PURPLE, ORANGE, RED = (44, 154, 144), (69, 124, 165), (130, 147, 165), (197, 164, 109), (171, 75, 73)


def glass(c, w, h, r, cx, cy, amt=0.22, tint=(255, 255, 255), blur=None, alpha=240, dark=0.0):
    """A frosted glass panel: a blurred, tinted copy of whatever sits behind it."""
    w, h = int(w), int(h); blur = blur or max(8, c.W // 40); pad = blur * 2
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xs = np.clip(np.arange(x0 - pad, x0 + w + pad), 0, c.W - 1); ys = np.clip(np.arange(y0 - pad, y0 + h + pad), 0, c.H - 1)
    reg = cv2.GaussianBlur(np.ascontiguousarray(c.img[np.ix_(ys, xs)]), (0, 0), blur)[pad:pad + h, pad:pad + w]
    reg = reg * (1 - dark) * (1 - amt) + np.float32(tint) / 255 * amt
    im = Image.fromarray((np.clip(reg, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], int(r), fill=alpha); im.putalpha(m)
    ImageDraw.Draw(im).rounded_rectangle([1, 1, w - 2, h - 2], int(r), outline=(255, 255, 255, 120), width=max(2, c.W // 540))
    return im


def face_chip(c, e, size):
    """A round avatar cut from your own face (grabbed once, at the start of the effect)."""
    def grab():
        r = c.fw * 0.9; x0, y0 = int(max(0, c.fx - r)), int(max(0, c.fy - r * 1.05))
        crop = c.img[y0:int(y0 + 2 * r), x0:int(x0 + 2 * r)]
        im = Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
        return im
    src = cached(e, 'face', grab).resize((int(size), int(size)), Image.LANCZOS)
    m = Image.new('L', src.size, 0); ImageDraw.Draw(m).ellipse([0, 0, src.width - 1, src.height - 1], fill=255); src.putalpha(m)
    return src


def cursor(size):
    s = float(size); im = Image.new('RGBA', (int(s * 0.95), int(s * 1.45)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(3, 3), (3, s * 1.12), (s * 0.3, s * 0.87), (s * 0.5, s * 1.33), (s * 0.66, s * 1.26), (s * 0.46, s * 0.8), (s * 0.82, s * 0.8)]
    d.polygon(pts, fill=(255, 255, 255, 255)); d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=max(2, int(s / 14)), joint='curve')
    return shadowed(im, 6, 3, 110)


def tick(d, x, y, s, color=(255, 255, 255, 255), w=None):
    d.line([(x, y + s * 0.5), (x + s * 0.36, y + s * 0.85), (x + s, y + s * 0.1)], fill=color, width=w or max(3, int(s / 5)), joint='curve')


def lines_fit(lines, max_w, kind, start):
    size = start
    while size > 10 and max(font(kind, size).getlength(l) for l in lines) > max_w: size = int(size * 0.94)
    return size


def shift(c, dy):
    """Slide the whole picture (and you) down by dy pixels."""
    if abs(dy) < 0.5: return
    M = np.float32([[1, 0, 0], [0, 1, dy]])
    c.img = cv2.warpAffine(c.img, M, (c.W, c.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    c.m = cv2.warpAffine(c.m, M, (c.W, c.H), flags=cv2.INTER_LINEAR); c.fy += dy


def thumb_grid(cards, cols, rows, cell, gap, i0=0, look=True):
    im = Image.new('RGBA', (cols * cell + (cols - 1) * gap, rows * int(cell * 1.25) + (rows - 1) * gap), (0, 0, 0, 0))
    ch = int(cell * 1.25)
    for k in range(cols * rows):
        src = cards[(i0 + k) % len(cards)]; src = vary(src, i0 + k) if look else src.convert('RGB')
        sw, sh = src.size; s = max(cell / sw, ch / sh); t = src.resize((max(cell, int(sw * s)), max(ch, int(sh * s))), Image.LANCZOS)
        l, tp = (t.width - cell) // 2, int((t.height - ch) * 0.3); t = t.crop((l, tp, l + cell, tp + ch)).convert('RGBA')
        m = Image.new('L', t.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cell - 1, ch - 1], max(4, cell // 12), fill=255); t.putalpha(m)
        im.alpha_composite(t, ((k % cols) * (cell + gap), (k // cols) * (ch + gap)))
    return im


def glass_widgets_v1(c, e):
    k0 = ramp(c, e, 0.3, 0)
    if e.o.get('grade', 'warm') != 'none': c.img = c.img * (1 - 0.6 * k0) + grade(c.img, e.o.get('grade', 'warm')) * 0.6 * k0
    al = fade(c, e); W = c.W; mg = W * 0.055
    S = W * 0.31; y_top = c.H * 0.07
    gd = float(e.o.get('dark', 0.2))
    a = glass(c, S, S, S * 0.2, mg + S / 2, y_top + S / 2, amt=0.14, dark=gd); d = ImageDraw.Draw(a)
    d.ellipse([S * 0.1, S * 0.115, S * 0.1 + S * 0.06, S * 0.115 + S * 0.06], fill=ORANGE + (255,))
    d.text((S * 0.2, S * 0.145), e.o.get('title', 'Swarag'), font=font('uim', S * 0.085), fill=(255, 255, 255, 235), anchor='lm')
    stat=str(e.o.get('text') or 'DEMO')
    stat_size=lines_fit([stat], S*.78,'uib', S*.33)
    d.text((S*.08,S*.25), stat,font=font('uib',stat_size),fill=(255,255,255,255))
    for j, ln in enumerate(e.o.get('sub', 'effects|one clip').split('|')):
        d.text((S * 0.1, S * (0.7 + 0.11 * j)), ln, font=font('uim', S * 0.085), fill=(255, 255, 255, 235))
    place(c, a, mg + S / 2, y_top + S / 2, 0.6 + 0.4 * pop(c, 0.0), 0, al * clamp(c.lt / 0.1), behind=True)
    bw, bh = W * 0.37, W * 0.15; bx = W - mg - bw / 2
    b = glass(c, bw, bh, bh * 0.28, bx, y_top + bh / 2, amt=0.14, dark=gd); d = ImageDraw.Draw(b)
    d.ellipse([bh * 0.17, bh * 0.2, bh * 0.17 + bh * 0.11, bh * 0.31], fill=(255, 69, 58, 255))
    d.text((bh * 0.36, bh * 0.255), e.o.get('bar_title', 'Execution plan'), font=font('uim', bh * 0.19), fill=(255, 255, 255, 240), anchor='lm')
    p = ease_inout(c.lt / max(0.3, e.d * 0.85))
    d.rounded_rectangle([bh * 0.17, bh * 0.5, bw - bh * 0.17, bh * 0.6], bh * 0.05, fill=(255, 255, 255, 70))
    d.rounded_rectangle([bh * 0.17, bh * 0.5, bh * 0.17 + (bw - bh * 0.34) * max(0.04, p), bh * 0.6], bh * 0.05, fill=(255, 255, 255, 245))
    d.text((bh * 0.17, bh * 0.78), e.o.get('label', 'Strategy roadmap'), font=font('uim', bh * 0.14), fill=(255, 255, 255, 210), anchor='lm')
    place(c, b, bx, y_top + bh / 2, 0.6 + 0.4 * pop(c, 0.12), 0, al * clamp((c.lt - 0.12) / 0.1), behind=True)
    cy2 = y_top + bh + mg * 0.45 + bh / 2
    g = glass(c, bw, bh, bh * 0.28, bx, cy2, amt=0.14, dark=gd); d = ImageDraw.Draw(g)
    av = face_chip(c, e, bh * 0.62); g.alpha_composite(av, (int(bw - bh * 0.19 - av.width), int((bh - av.height) / 2)))
    d.text((bh * 0.2, bh * 0.36), e.o.get('name', 'Swarag'), font=font('uib', bh * 0.22), fill=(255, 255, 255, 255), anchor='lm')
    d.text((bh * 0.2, bh * 0.66), e.o.get('handle', '@aiwithswarag'), font=font('uim', bh * 0.14), fill=(255, 255, 255, 215), anchor='lm')
    place(c, g, bx, cy2, 0.6 + 0.4 * pop(c, 0.24), 0, al * clamp((c.lt - 0.24) / 0.1), behind=True)
    f1, f2 = font('uim', W * 0.045), font('uib', W * 0.045)
    pre, hi = e.o.get('pill', 'Strategy |Execution').split('|') if '|' in e.o.get('pill', 'Strategy |Execution') else (e.o['pill'], '')
    tw = f1.getlength(pre) + f2.getlength(hi); ph = W * 0.105; pw = tw + ph * 0.9; py = c.H * 0.865
    q = glass(c, pw, ph, ph / 2, W / 2, py, amt=0.16, tint=(70, 70, 76)); d = ImageDraw.Draw(q)
    d.text(((pw - tw) / 2, ph / 2), pre, font=f1, fill=(255, 255, 255, 255), anchor='lm')
    d.text(((pw - tw) / 2 + f1.getlength(pre), ph / 2), hi, font=f2, fill=(255, 176, 146, 255), anchor='lm')
    place(c, shadowed(q, 14, 6, 70), W / 2, py, 0.7 + 0.3 * pop(c, 0.4), 0, al * clamp((c.lt - 0.4) / 0.1), guard=True)


@effect('red-collage', 'black and white you, a giant red word behind, kinetic type stacked beside you')
def fx_red_collage(c, e):
    if getattr(c,'face_priority',False):
        W=c.W
        headline=str(e.o.get('text','STRATEGY'))[:28].upper()
        lines=[x.strip() for x in str(e.o.get(
            'lines','CLEAR DIRECTION|SMART EXECUTION')).split('|')
            if x.strip()][:2]
        w=int(W*.84);h=int(W*.36)
        card=rrect(w,h,W*.026,(25,33,39,239))
        d=ImageDraw.Draw(card)
        pad=int(W*.043)
        d.text((pad,W*.049),'EDITORIAL / STRATEGY',
               font=font('uim',W*.028),
               fill=(208,203,190,255))
        fs=lines_fit([headline],w-2*pad,'didoneb',int(W*.097))
        d.text((pad,W*.133),headline,font=font('didoneb',fs),
               fill=rgb(e.o.get('color'),(197,164,109))+(255,))
        d.line((pad,W*.238,w-pad,W*.238),
               fill=(197,164,109,215),width=max(2,W//110))
        if lines:
            second=' · '.join(lines)
            fs=lines_fit([second],w-2*pad,'uib',int(W*.037))
            d.text((pad,W*.285),second,font=font('uib',fs),
                   fill=(237,239,239,255))
        place_safe_panel(c,card,'above',
                         alpha=fade(c,e)*clamp(c.lt/.14),
                         min_scale=.45)
        return
    k = ramp(c, e, 0.15, 0); m = c.m[..., None]
    bw = grade(c.img, 'bw'); out = bw * m + bw * 0.62 * (1 - m)
    c.img = c.img * (1 - k) + out * k
    vignette(c, 0.45 * k)
    red = rgb(e.o.get('color'), RED); al = fade(c, e)
    w = cached(e, 'w', lambda: fit_text(e.o.get('text', 'EDIT').upper(), c.W * 0.98, 'uib', 700, fill=red, glow=(red, 34)))
    s = 1.12 - 0.12 * ease_out(c.lt / 0.4)
    if getattr(c,'face_priority',False):
        upper,sc = editorial_headline_anchor(c, w)
        place(c, w, c.W / 2, upper, s*sc, 0, clamp(c.lt / 0.12) * al, behind=True)
    else:
        place(c, w, c.W / 2, max(w.height * 0.42, c.fy - c.fw * 1.05),
              s, 0, clamp(c.lt / 0.12) * al, behind=True)
    lines = e.o.get('lines', 'CLEAR STRATEGY.|SMART EXECUTION.|REAL IMPACT.').split('|')
    size = cached(e, 'sz', lambda: lines_fit(lines, c.W * 0.8, 'uib', int(c.W * 0.14)))
    if getattr(c,'face_priority',False):
        y=min(c.H*.88-len(lines)*size*1.15,
              max(c.H*.67,c.fy+c.fw*1.55))
        y=max(c.H*.60,y)
    else:
        y=max(c.H*.5,c.fy+c.fw*1.55)
    for j, ln in enumerate(lines):
        im = cached(e, ('l', j), lambda: text_img(ln, size, 'uib', red if j == 1 else (255, 255, 255), shadow=8))
        kk = clamp((c.lt - 0.18 - 0.13 * j) / 0.16)
        if kk > 0: place(c, im, c.W * 0.05 + im.width / 2, y + im.height / 2, 1.4 - 0.4 * ease_out(kk), 0, kk * al, guard=True)
        y += size * 1.0
    tag = cached(e, 'tag', lambda: text_img(e.o.get('tag', 'REC  ·  RED COLLAGE'), c.W * 0.027, 'mono', red))
    dot = Image.new('RGBA', (int(tag.height * 0.4),) * 2, (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse([0, 0, dot.width - 1, dot.width - 1], fill=red + (255,))
    blink = 1.0 if int(c.lt * 2.5) % 2 == 0 else 0.35
    place(c, dot, c.W * 0.07, c.H * 0.93, alpha=al * k * blink, guard=True)
    place(c, tag, c.W * 0.07 + dot.width + tag.width / 2, c.H * 0.93, alpha=al * k, guard=True)


@effect('split-headline', 'a clean headline card slides down and pushes you into the bottom of the frame')
def fx_split_headline(c, e):
    k = ease_out(c.lt / 0.38) * clamp((e.d - c.lt) / 0.25)
    ch = c.H * float(e.o.get('height', 0.36))
    shift(c, ch * float(e.o.get('push', 0.72)) * k)
    top = ch * k; W = c.W; col = rgb(e.o.get('color'), GREEN)
    lay = Image.new('RGBA', (W, int(ch)), (244, 242, 236, 255)); d = ImageDraw.Draw(lay)
    lines = e.o.get('text', 'Strategy|meets|execution.').split('|'); hl = e.o.get('hl', 'edits')
    S = cached(e, 'sz', lambda: lines_fit(lines, W * 0.84, 'uib', int(W * 0.135))); f = font('uib', S)
    x0, y0 = W * 0.07, ch * 0.13
    for j, ln in enumerate(lines):
        kj = clamp((c.lt - 0.12 - 0.08 * j) / 0.18)
        if kj <= 0: continue
        y = y0 + j * S * 1.04 + (1 - ease_out(kj)) * S * 0.35; a = int(255 * kj)
        x = x0
        for wi, word in enumerate(ln.split(' ')):
            tail = '.' if word.endswith('.') else ''; core = word[:-1] if tail else word
            wl = f.getlength(core)
            if core == hl:
                hk = ease_out((c.lt - 0.42) / 0.22); pad = S * 0.12
                if hk > 0: d.rounded_rectangle([x - pad, y + S * 0.02, x - pad + (wl + 2 * pad) * hk, y + S * 1.1], S * 0.16, fill=col + (a,))
                d.text((x, y), core, font=f, fill=((255, 255, 255, a) if hk > 0.55 else (20, 20, 22, a)))
            else: d.text((x, y), core, font=f, fill=(20, 20, 22, a))
            x += wl
            if tail: d.text((x, y), tail, font=f, fill=col + (a,)); x += f.getlength(tail)
            x += f.getlength(' ') + (S * 0.12 if core == hl else 0)
    d.rectangle([0, ch - max(5, W // 180), W, ch], fill=col + (255,))
    comp(c, lay, 0, top - ch)
    pt = text_img(e.o.get('pill', 'KEY POINT'), W * 0.050, 'uib', (255, 255, 255))
    pill = rrect(pt.width + W * 0.02, pt.height * 0.95, pt.height * 0.47, col + (255,)); pill.alpha_composite(pt, (int(W * 0.01), int(-pt.height * 0.025)))
    place(c, shadowed(pill, 10, 4, 80), W * 0.93 - pill.width / 2, top + pill.height * 0.95, 0.6 + 0.4 * pop(c, 0.62), 0, clamp((c.lt - 0.62) / 0.1) * k, guard=True)


_grad = {}
@effect('pastel-word', 'a soft lavender backdrop, a giant word behind you and a profile card that gets followed')
def fx_pastel_word(c, e):
    W, H = c.W, c.H; k = ramp(c, e, 0.2, 0); m = c.m[..., None]; al = fade(c, e)
    if (W, H) not in _grad:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); t = np.clip((yy / H) * 0.8 + (xx / W) * 0.2, 0, 1)[..., None]
        _grad[(W, H)] = np.float32([0.70, 0.67, 0.97]) * (1 - t) + np.float32([0.93, 0.90, 1.0]) * t
    lum = (c.img @ np.float32([0.299, 0.587, 0.114]))[..., None]
    bg = _grad[(W, H)] * (0.86 + 0.22 * lum)
    you = np.clip(c.img * 0.93 + 0.05, 0, 1)
    c.img = c.img * (1 - k) + (you * m + bg * (1 - m)) * k
    word = cached(e, 'w', lambda: fit_text(e.o.get('text', 'INSIGHTS').upper(), W * 0.96, 'uib', 700, fill=(255, 255, 255)))
    dk = ease_out(c.lt / 0.45)
    if getattr(c,'face_priority',False):
        top_y, top_scale = editorial_headline_anchor(c, word)
    else:
        top_y, top_scale = max(word.height * 0.45, c.fy - c.fw * 1.2), 1.0
    place(c, shadowed(word, 24, 12, 60), W / 2,
          top_y - (1 - dk) * H * 0.06,
          top_scale, 0, al * clamp(c.lt / 0.15), behind=True)
    cw, chh = W * 0.86, W * 0.15; cy = H * 0.865 + (1 - ease_out((c.lt - 0.15) / 0.35)) * H * 0.2
    card_ = rrect(cw, chh, chh * 0.3, (255, 255, 255, 248)); d = ImageDraw.Draw(card_)
    av = face_chip(c, e, chh * 0.64); card_.alpha_composite(av, (int(chh * 0.18), int((chh - av.height) / 2)))
    d.text((chh * 0.98, chh * 0.38), e.o.get('name', 'Swarag'), font=font('uib', chh * 0.22), fill=(20, 20, 22, 255), anchor='lm')
    h1 = e.o.get('handle', '@aiwithswarag  ·  '); f = font('uim', chh * 0.15)
    d.text((chh * 0.98, chh * 0.66), h1, font=f, fill=(140, 140, 150, 255), anchor='lm')
    d.text((chh * 0.98 + f.getlength(h1), chh * 0.66), e.o.get('role', 'creator'), font=f, fill=PURPLE + (255,), anchor='lm')
    at = e.d * 0.6; on = c.lt >= at
    bx = cw - chh * 0.22
    d.text((bx, chh / 2), 'Following' if on else 'Follow', font=font('uib', chh * 0.2), fill=((140, 140, 150, 255) if on else PURPLE + (255,)), anchor='rm')
    sq = 1 - 0.06 * math.sin(math.pi * clamp((c.lt - at) / 0.25)) if on else 1
    place(c, shadowed(card_, 18, 8, 90), W / 2, cy, sq, 0, al * clamp((c.lt - 0.15) / 0.12), guard=True)
    cu = cached(e, 'cur', lambda: cursor(W * 0.06))
    ck = ease_inout((c.lt - 0.25) / max(0.2, at - 0.3))
    tx, ty = W / 2 + cw / 2 - chh * 0.55, cy + chh * 0.12
    sx, sy = W * 1.02, H * 1.02
    place(c, cu, sx + (tx - sx) * ck + cu.width / 2, sy + (ty - sy) * ck + cu.height / 2, 0.85 if on and c.lt - at < 0.15 else 1, 0, al * clamp((c.lt - 0.25) / 0.1))


_gp = {}
@effect('check-pills', 'grid-paper room, your reels pinned behind you and blue pills that get clicked')
def fx_check_pills(c, e):
    """Two clearly readable decision pills instead of fake mini reports."""
    W=c.W
    names=[x.strip() for x in str(e.o.get(
        'text','DIRECTION|DELIVERY')).split('|') if x.strip()]
    if not 1<=len(names)<=3:
        raise ValueError('check-pills needs 1–3 approved concepts')
    w=int(W*.80)
    row=int(W*.135)
    h=int(W*.105)+len(names)*row
    lay=rrect(w,h,W*.028,(16,31,42,232))
    d=ImageDraw.Draw(lay)
    pad=int(W*.047)
    d.text((pad,W*.056),'EXECUTIVE CHECKS',
           font=font('uib',W*.043),fill=(230,242,244,255),
           anchor='lm')
    for i,name in enumerate(names):
        y=int(W*.105)+(i+.5)*row
        on=c.lt>=(.22+i*.25)
        color=(44,154,144,255) if on else (100,121,138,255)
        rr=max(5,int(row*.27))
        d.ellipse((pad,y-rr,pad+2*rr,y+rr),fill=color)
        if on:
            tick(d,pad+rr*.55,y-rr*.15,rr*.68,
                 w=max(2,W//100))
        fs=lines_fit([name],w-pad*2-rr*3,'uib',int(W*.052))
        d.text((pad+rr*2.8,y),name.upper(),
               font=font('uib',fs),fill=(244,246,247,255),anchor='lm')
    place_safe_panel(c,lay,'above',alpha=fade(c,e)*clamp(c.lt/.14),
                     min_scale=.40)

def red_timeline(c, e):
    W, H = c.W, c.H; k = ramp(c, e, 0.2, 0); m = c.m[..., None]; al = fade(c, e)
    lum = (c.img @ np.float32([0.299, 0.587, 0.114]))[..., None]
    bg = np.clip(lum * np.float32([1.05, 0.3, 0.27]) * 0.85, 0, 1)
    you = np.clip(c.img * np.float32([1.04, 0.86, 0.82]), 0, 1)
    c.img = c.img * (1 - k) + (you * m + bg * (1 - m)) * k; vignette(c, 0.5 * k)
    red = rgb(e.o.get('color'), (255, 52, 44))
    sl = (1 - ease_out(c.lt / 0.35)) * W * 0.08; tb = clamp(c.lt / 0.15) * al
    secs = 21 + int(c.lt * 3)
    rec = text_img(f"{e.o.get('tc', 'REC')} 00:{secs:02d}", W * 0.032, 'mono', red)
    dot = Image.new('RGBA', (int(rec.height * 0.36),) * 2, (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse([0, 0, dot.width - 1, dot.width - 1], fill=red + (255,))
    comp(c, dot, W * 0.065 - sl, H * 0.075 + (rec.height - dot.height) / 2, tb * (1.0 if int(c.lt * 2.5) % 2 == 0 else 0.35), guard=True)
    comp(c, rec, W * 0.065 + dot.width * 1.4 - sl, H * 0.075, tb, guard=True)
    ti = cached(e, 'ti', lambda: text_img(e.o.get('text', 'AUTO-EDIT'), W * 0.13, 'uib', (255, 255, 255), shadow=10))
    comp(c, ti, W * 0.055 - sl, H * 0.075 + rec.height * 0.85, tb, guard=True)
    su = cached(e, 'su', lambda: text_img(e.o.get('sub', 'Swarag Video Director'), W * 0.037, 'uim', red))
    comp(c, su, W * 0.065 - sl, H * 0.075 + rec.height * 0.85 + ti.height * 0.88, tb, guard=True)
    pw, phh = int(W * 0.9), int(H * 0.19); py = H * 0.755 + (1 - ease_out((c.lt - 0.1) / 0.35)) * H * 0.3
    lay = rrect(pw, phh, W * 0.03, (14, 10, 10, 215), (255, 70, 60, 90), 2); d = ImageDraw.Draw(lay)
    for j in range(4): d.text((pw * (0.05 + 0.3 * j), phh * 0.12), f'00:0{j}', font=font('mono', W * 0.022), fill=(170, 170, 175, 255), anchor='lm')
    clips = cached(e, 'cl', lambda: [(r, a, b) for r, segs in enumerate([[(0.04, 0.24), (0.26, 0.5), (0.53, 0.76), (0.79, 0.96)],
                                                                            [(0.04, 0.3), (0.33, 0.45), (0.48, 0.7)], [(0.04, 0.55), (0.6, 0.96)]]) for a, b in segs])
    p = 0.04 + 0.92 * clamp(c.lt / (e.d * 0.95)); ph_x = pw * p
    glow = Image.new('RGBA', (pw, phh), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for r, a, b in clips:
        y0 = phh * (0.27 + 0.235 * r); x0, x1 = pw * a, pw * b; on = pw * a < ph_x
        fill = red + (255,) if on else (120, 30, 28, 255)
        d.rounded_rectangle([x0, y0, x1, y0 + phh * 0.17], phh * 0.04, fill=fill)
        if on: gd.rounded_rectangle([x0, y0, x1, y0 + phh * 0.17], phh * 0.04, fill=red + (200,))
    d.line([(ph_x, phh * 0.2), (ph_x, phh * 0.97)], fill=(255, 255, 255, 255), width=max(3, W // 300))
    gd.line([(ph_x, phh * 0.2), (ph_x, phh * 0.97)], fill=(255, 255, 255, 255), width=max(8, W // 100))
    lay = Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W // 90)), lay)
    comp(c, lay, (W - pw) / 2, py, al, guard=True)


@effect('headline-box', 'a punch-in with a clean two-line headline, the second line in a white box')
def fx_headline_box(c, e):
    W=c.W
    lines=[x.strip() for x in str(e.o.get(
        'text','Strategy into|measurable impact.')).split('|') if x.strip()][:2]
    if len(lines)!=2:
        raise ValueError('headline-box requires two approved text lines')
    w,h=int(W*.83),int(W*.32)
    panel=rrect(w,h,int(W*.027),(18,32,44,224))
    d=ImageDraw.Draw(panel)
    pad=int(W*.042)
    f1=lines_fit([lines[0]],w-2*pad,'uib',int(W*.072))
    f2=lines_fit([lines[1]],w-2*pad,'uib',int(W*.070))
    d.text((pad,h*.32),lines[0],font=font('uib',f1),
           fill=(238,244,246,255),anchor='lm')
    d.rounded_rectangle((pad,h*.52,w-pad,h*.91),
                        radius=int(W*.012),fill=(245,242,233,255))
    d.text((pad+W*.025,h*.715),lines[1],font=font('uib',f2),
           fill=(22,33,42,255),anchor='lm')
    place_safe_panel(c,panel,'above',
                     alpha=fade(c,e)*clamp((c.lt-.08)/.22),
                     min_scale=.46)

@effect('profile-wall', 'your profile grid fills the wall behind you while a counter ticks up')
def fx_profile_wall(c, e):
    """Readable real/approved portfolio cards without a forehead cutout."""
    W=c.W
    cards=e.cards
    if not cards:
        raise ValueError('profile-wall requires approved original media')
    pw=int(W*.80)
    cell=int(W*.30)
    gap=int(W*.025)
    header=int(W*.12)
    ph=header+2*cell+3*gap
    im=rrect(pw,ph,W*.03,(14,28,41,239))
    d=ImageDraw.Draw(im)
    d.text((pw*.06,header*.53),
           str(e.o.get('title','PORTFOLIO EXAMPLES')).upper()[:27],
           font=font('uib',W*.043),fill=(237,246,247,255),anchor='lm')
    sx=(pw-(2*cell+gap))//2
    for i in range(4):
        src=cards[i%len(cards)].convert('RGB')
        sw,sh=src.size
        take=min(sw,sh)
        src=src.crop(((sw-take)//2,(sh-take)//2,
                      (sw+take)//2,(sh+take)//2))
        tile=src.resize((cell,cell),Image.LANCZOS).convert('RGBA')
        x=sx+(i%2)*(cell+gap)
        y=header+gap+(i//2)*(cell+gap)
        im.alpha_composite(tile,(x,y))
    # The portfolio itself is the effect. Keep its approved media grouped
    # in the upper negative space, not a second badge across the shirt.
    place_adaptive_panel(c,im,'above',alpha=fade(c,e)*clamp(c.lt/.18),
                         min_scale=.55)
    if e.o.get('count') is not None:
        if not str(e.o.get('metric_source','')).strip():
            raise ValueError('PROFILE_COUNT_WITHOUT_VERIFIED_SOURCE')
        metric=str(e.o['count'])
        metric_label=str(e.o.get('label','VERIFIED METRIC'))
    else:
        metric='ILLUSTRATIVE'
        metric_label='PORTFOLIO LAYOUT'
    bw,bh=int(W*.72),int(W*.16)
    bar=rrect(bw,bh,W*.024,(18,34,45,235))
    bd=ImageDraw.Draw(bar)
    bd.text((bw*.06,bh*.38),metric,font=font('uib',W*.052),
            fill=(247,247,245,255),anchor='lm')
    bd.text((bw*.06,bh*.76),metric_label[:24],
            font=font('uim',W*.029),fill=(191,214,218,255),anchor='lm')
    # Do not add a second unreadable floating badge on the chest.
    # A verified metric remains available to the higher-level director,
    # but must be paired with an explicit well-framed scene to be displayed.
    if e.o.get('show_metric_badge') is True:
        place_adaptive_panel(c,bar,'above',
                       alpha=fade(c,e)*clamp((c.lt-.3)/.20),
                       min_scale=.58)

@effect('tier-list', 'an executive tier list with a highlighted item')
def fx_tier_list(c,e):
    """Full priority tier board in two compact rows, never a lone badge."""
    W=c.W
    rows=[v.strip() for v in str(e.o.get('rows',
         'Strategy|Execution|Delivery|Outcomes')).split('|') if v.strip()]
    rows=rows[:6] if e.o.get('all_tiers') else rows[:4]
    if not rows: raise ValueError("TIER_LIST_NEEDS_APPROVED_ROWS")
    labels="SABCDF"
    colors=((44,154,144),(69,124,165),(197,164,109),
            (130,147,165),(170,151,121),(171,75,73))
    w,h=int(W*.86),int(W*(.17+.16*math.ceil(len(rows)/2)))
    lay=rrect(w,h,max(5,int(W*.029)),(17,31,43,248))
    d=ImageDraw.Draw(lay)
    pad=W*.037
    title=str(e.o.get('title','EXECUTIVE PRIORITIES')).upper()
    title_size=lines_fit([title],w-2*pad,'uib',int(W*.047))
    d.text((pad,W*.065),title,font=font('uib',title_size),
           fill=(243,245,243,255),anchor='lm')
    d.line((pad,W*.129,w-pad,W*.129),fill=(197,164,109,200),
           width=max(1,W//160))
    half=(w-pad*3)/2
    visible=max(1,min(len(rows),int(clamp(c.lt/max(.4,e.d*.7))*len(rows))+1))
    for i,txt in enumerate(rows):
        x=pad+(i%2)*(half+pad)
        y=W*(.15+.16*(i//2))
        # Keep the board geometry fixed so rows cannot jump during animation.
        fill=(34,49,61,255)
        d.rounded_rectangle((x,y,x+half,y+W*.135),
                            radius=max(3,int(W*.013)),fill=fill)
        c0=colors[i]
        d.rounded_rectangle((x+W*.009,y+W*.012,
                             x+W*.115,y+W*.123),
                            radius=max(3,int(W*.012)),fill=c0+(255,))
        d.text((x+W*.062,y+W*.067),labels[i],
               font=font('uib',W*.057),fill=(15,29,37,255),
               anchor='mm')
        fsz=lines_fit([txt],half-W*.145,'uib',int(W*.042))
        if fsz<int(W*.029):
            raise ValueError("TIER_LIST_LABEL_OVERFLOW")
        d.text((x+W*.127,y+W*.068),txt,
               font=font('uib',fsz),
               fill=(239,244,245,255) if i<visible else (132,149,159,255),
               anchor='lm')
    place_adaptive_panel(c,lay,'below',
                         alpha=fade(c,e)*clamp(c.lt/.12),min_scale=.35)

@effect('broll-split', 'split screen: b-roll on top with a price-tag sticker, you on the bottom')
def fx_broll_split(c, e):
    W, H = c.W, c.H; k = ease_out(c.lt / 0.3) * clamp((e.d - c.lt) / 0.2); al = fade(c, e)
    shift(c, (H * 0.72 - c.fy) * k)
    sh = int(H * 0.5 * k)
    if sh > 2:
        src = e.cards[int(e.o.get('pick', 0)) % len(e.cards)].convert('RGB')
        z = 1.0 + 0.06 * clamp(c.lt / e.d); tw, th = int(W * z), int(H * 0.5 * z)
        s = max(tw / src.width, th / src.height); im = src.resize((int(src.width * s) + 1, int(src.height * s) + 1), Image.BILINEAR)
        l, t = (im.width - W) // 2, int((im.height - H * 0.5) * 0.35); im = im.crop((l, t, l + W, t + int(H * 0.5)))
        top = np.asarray(im, np.float32) / 255
        c.img[:sh] = top[int(H * 0.5) - sh:]; c.m[:sh] = 0
        c.img[max(0, sh - 3):sh + 3] = 1.0
    tag = cached(e, 'tag', lambda: fit_text(e.o.get('text', 'EXAMPLE ONLY'), W * 0.76, 'uib', W * 0.06, fill=(16,16,18)))
    tw, th = int(tag.width + W * 0.11), int(tag.height * 1.25)
    st = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(st); n = th * 0.5
    d.polygon([(0, th / 2), (n, 0), (tw, 0), (tw, th), (n, th)], fill=(255, 255, 255, 255))
    d.ellipse([n * 0.55, th / 2 - n * 0.16, n * 0.87, th / 2 + n * 0.16], fill=(200, 200, 205, 255))
    st.alpha_composite(tag, (int(n * 1.05), (th - tag.height) // 2))
    # The sticker belongs to the upper B-roll pane, NEVER to the speaker's
    # face. Previous 0.39*H placement cut across the eyes in the camera test.
    scale = 0.74 + 0.26 * pop(c, 0.3)
    card_height = shadowed(st, 12, 6, 110).height * scale
    safe_bottom = sh - H * 0.045
    if safe_bottom > card_height * 1.12:
        cy = min(H * 0.24, safe_bottom - card_height * 0.57)
        cy = max(card_height * 0.6, cy)
        place(c, shadowed(st, 12, 6, 110), W * 0.55, cy,
              scale, 2, al * clamp((c.lt - 0.3) / 0.08), guard=True)


@effect('phone-fan', 'your reels fan out like a hand of phones in front of you, under a two-line headline')
def fx_phone_fan(c,e):
    """Four genuinely visible phone cards, not a missing mini-carousel."""
    W=c.W
    approved=list(getattr(e,'cards',[]) or [])
    if not approved: raise ValueError("PHONE_FAN_REQUIRES_APPROVED_ASSETS")
    lines=[s.strip() for s in str(e.o.get('text','Strategy|Execution')
          ).split('|') if s.strip()][:2]
    heading='  •  '.join(lines).upper()
    w,h=int(W*.89),int(W*.52)
    lay=rrect(w,h,max(5,int(W*.026)),(15,29,42,232))
    d=ImageDraw.Draw(lay)
    f=lines_fit([heading],w*.91,'uib',int(W*.048))
    d.text((w/2,W*.065),heading,font=font('uib',f),
           fill=(245,244,239,255),anchor='mm')
    count=4
    pw,ph=int(W*.178),int(W*.325)
    gap=int(W*.022)
    left=(w-(count*pw+(count-1)*gap))/2
    t=clamp((c.lt-.05)/.45)
    for i in range(count):
        item=approved[i%len(approved)].convert('RGB')
        sw,sh=item.size
        ratio=(pw-6)/(ph-6)
        if sw/sh>ratio:
            cw=max(1,int(sh*ratio))
            item=item.crop(((sw-cw)//2,0,(sw+cw)//2,sh))
        else:
            ch=max(1,int(sw/ratio))
            item=item.crop((0,(sh-ch)//2,sw,(sh+ch)//2))
        item=item.resize((pw-6,ph-6),Image.LANCZOS).convert('RGBA')
        phone=rrect(pw,ph,max(3,int(W*.012)),(10,23,37,255))
        phone.alpha_composite(item,(3,3))
        a=(i-1.5)*5*t
        rotated=phone.rotate(a,Image.BICUBIC,expand=True)
        x=left+i*(pw+gap)+(pw-rotated.width)/2
        y=W*.135+abs(i-1.5)*W*.028+(1-t)*W*.06
        x=max(0,min(w-rotated.width,int(x)))
        y=max(0,min(h-rotated.height,int(y)))
        lay.alpha_composite(rotated,(x,y))
    place_adaptive_panel(c,lay,'below',
                         alpha=fade(c,e)*clamp((c.lt-.1)/.12),
                         min_scale=.31)

@effect('dot-reveal', 'your shot builds itself out of glowing dots, then snaps into the full picture')
def fx_dot_reveal(c, e):
    p = clamp(c.lt / e.d); W, H = c.W, c.H
    cell = max(6, int(W * float(e.o.get('cell', 0.017)))); gh, gw = H // cell + 1, W // cell + 1
    def geo():
        yy, xx = np.mgrid[0:gh * cell, 0:gw * cell].astype(np.float32)
        dist = np.sqrt((xx % cell - cell / 2 + 0.5) ** 2 + (yy % cell - cell / 2 + 0.5) ** 2)[:H, :W]
        return dist, np.random.default_rng(5).random((gh, gw)).astype(np.float32)
    dist, thr = cached(e, 'geo', geo)
    pad = np.pad(c.img, ((0, gh * cell - H), (0, gw * cell - W), (0, 0)), mode='edge')
    small = cv2.resize(pad, (gw, gh), interpolation=cv2.INTER_AREA)
    lum = small @ np.float32([0.299, 0.587, 0.114])
    on = np.clip((p * 1.7 - thr * 0.95) / 0.3, 0, 1)
    sparkle = 0.75 + 0.25 * np.sin(thr * 40 + c.lt * 18)
    r = (0.18 + 0.32 * np.sqrt(np.clip(lum, 0, 1))) * cell * on
    col = rgb(e.o.get('color'), (255, 128, 80))
    q2 = clamp((p - 0.3) / 0.35)
    dc = np.float32(col) / 255 * (0.55 + 0.6 * lum[..., None]) * sparkle[..., None] * (1 - q2) + np.clip(small * 1.15, 0, 1) * q2
    R = np.repeat(np.repeat(r, cell, 0), cell, 1)[:H, :W]
    DC = np.repeat(np.repeat(dc, cell, 0), cell, 1)[:H, :W]
    dm = np.clip(R - dist + 0.5, 0, 1)[..., None]
    bgc = np.float32(rgb(e.o.get('bg'), (20, 20, 22))) / 255
    dots = bgc * (1 - dm) + DC * dm
    q = ease_inout((p - 0.6) / 0.4)
    c.img = dots * (1 - q) + c.img * q


def tracked(s, size, kind, fill, spacing, colors=None):
    """Letter-spaced text. colors: optional per-character fill list."""
    f = font(kind, size); w = sum(f.getlength(ch) for ch in s) + spacing * max(0, len(s) - 1)
    bb = f.getbbox('Ag'); im = Image.new('RGBA', (int(w) + 8, int(bb[3] - bb[1] + size * 0.4)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4
    for i, ch in enumerate(s):
        d.text((x, -bb[1] + size * 0.2), ch, font=f, fill=(colors[i] if colors else fill) + (255,)); x += f.getlength(ch) + spacing
    return im


def rich(parts, size, kind, base, accent, accent_kind=None, shadow=0):
    """One line of text where *starred* words take the accent colour (and optionally another font)."""
    segs = []
    for j, p in enumerate(parts.split('*')):
        if p: segs.append(text_img(p, size, accent_kind if (j % 2 and accent_kind) else kind, accent if j % 2 else base, shadow=shadow))
    pad = int(size * 0.2 + shadow * 2.5) + 4
    w = sum(s.width - 2 * pad for s in segs) + 2 * pad; h = max(s.height for s in segs)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); x = 0
    for s in segs: im.alpha_composite(s, (x, (h - s.height) // 2)); x += s.width - 2 * pad
    return im


@effect('headline-wall', 'a wall of your own reel headlines piles up behind your head, then your total views pop in front')
def fx_headline_wall(c, e):
    """Two source-backed editorial items, not fabricated tiny publications."""
    W=c.W
    rows=[(x.split('::')+[''])[:2] for x in str(e.o.get(
        'text','AI DELIVERY::ILLUSTRATIVE|GOVERNANCE::EXAMPLE')).split('|')
        if x.strip()][:2]
    if not rows: raise ValueError('No verified headline provided')
    w=int(W*.84)
    rh=int(W*.22)
    h=int(W*.10)+len(rows)*rh
    lay=rrect(w,h,W*.024,(21,36,49,237))
    d=ImageDraw.Draw(lay)
    pad=int(W*.05)
    d.text((pad,int(W*.060)),'EDITORIAL BRIEF',
           font=font('uib',int(W*.037)),
           fill=(210,227,229,255),anchor='lm')
    for j,(headline,meta) in enumerate(rows):
        if j>0 and c.lt<(.25+j*.3): continue
        y=int(W*.10)+j*rh
        fsize=lines_fit([headline],w-pad*2,'uib',int(W*.062))
        d.text((pad,y+rh*.35),headline[:62],
               font=font('uib',fsize),fill=(243,244,241,255),
               anchor='lm')
        d.text((pad,y+rh*.76),meta[:30].upper(),
               font=font('uim',int(W*.030)),
               fill=(197,164,109,255),anchor='lm')
    place_safe_panel(c,lay,'above',
                     alpha=fade(c,e)*clamp(c.lt/.12),min_scale=.38)

@effect('checklist', 'an executive task list builds with animated check marks')
def fx_checklist(c,e):
    """Compact four-check editorial panel with real visible checkboxes."""
    W=c.W
    rows=[(s.split('::')+[''])[:2] for s in str(
         e.o.get('text','Direction::sample|Delivery::sample|'
                 'Outcomes::sample')).split('|') if s.strip()]
    if not 1<=len(rows)<=4:
        raise ValueError("CHECKLIST_REQUIRES_1_TO_4_APPROVED_ROWS")
    n=len(rows);w=int(W*.87)
    h=int(W*(.14+.18*math.ceil(n/2)))
    region,cx,cy,_=adaptive_panel_location(c,w,h,'below',min_scale=.36)
    lay=glass(c,w,h,W*.030,cx,cy,amt=.13,
              tint=(16,32,43),dark=.50,blur=max(5,W//36))
    d=ImageDraw.Draw(lay)
    pad=W*.038
    name=str(e.o.get('title','EXECUTION CHECKS'))[:28].upper()
    fs=lines_fit([name],w-pad*2,'uib',int(W*.049))
    d.text((pad,W*.061),name,font=font('uib',fs),
           fill=(241,246,246,255),anchor='lm')
    done_times=[.27+max(.3,e.d-.55)*(j+1)/n for j in range(n)]
    for i,(label,meta) in enumerate(rows):
        col=i%2;rr=i//2
        x=pad+col*(w*.5-pad*.5);y=W*(.125+.18*rr)
        box_w=w*.48-pad*.6;box_h=W*.156
        d.rounded_rectangle((x,y,x+box_w,y+box_h),
                            radius=max(3,int(W*.015)),
                            fill=(24,42,52,235))
        on=c.lt>=done_times[i]
        r=max(4,int(W*.026));mk_x=x+W*.044;mk_y=y+W*.062
        color=(44,154,144,255) if on else (140,163,172,255)
        d.ellipse((mk_x-r,mk_y-r,mk_x+r,mk_y+r),
                  outline=color,width=max(2,W//120),
                  fill=color if on else (0,0,0,0))
        if on:tick(d,mk_x-r*.45,mk_y-r*.23,r*.8,
                   w=max(2,W//110))
        txt=str(label).strip()
        fsz=lines_fit([txt],box_w-W*.10,'uib',int(W*.043))
        if fsz<int(W*.030):raise ValueError("CHECKLIST_LABEL_TOO_LONG")
        d.text((x+W*.085,y+W*.068),txt,font=font('uib',fsz),
               fill=(242,245,244,255),anchor='lm')
        if meta:
            sub=str(meta)[:16]
            sf=lines_fit([sub],box_w-W*.08,'uim',int(W*.025))
            d.text((x+W*.085,y+W*.119),sub,font=font('uim',sf),
                   fill=(183,205,211,255),anchor='lm')
    place_safe_panel(c,lay,region,alpha=fade(c,e)*clamp(c.lt/.12),
                     min_scale=.36)

def np_thumb(c, w, h):
    """The current frame as a small PIL thumbnail (cropped to w:h around your face)."""
    ar = w / h; ch = c.H * 0.62; cw = ch * ar
    x0 = int(clamp(c.fx - cw / 2, 0, c.W - cw)); y0 = int(clamp(c.fy - ch * 0.4, 0, c.H - ch))
    crop = c.img[y0:int(y0 + ch), x0:int(x0 + cw)]
    return Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).resize((int(w), int(h)), Image.LANCZOS)


def glow_panel(w, h, r, top, bot, line, glow, gblur):
    """A rounded panel with a vertical gradient fill, a thin border and an outer glow."""
    w, h = int(w), int(h); pad = int(gblur * 2.2)
    out = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    g = Image.new('RGBA', out.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle([pad, pad, pad + w, pad + h], r, fill=glow)
    out.alpha_composite(g.filter(ImageFilter.GaussianBlur(gblur)))
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    fill = (np.float32(top) * (1 - t) + np.float32(bot) * t) * np.ones((1, w, 1), np.float32)
    body = Image.fromarray(np.concatenate([fill, np.full((h, w, 1), 255, np.float32)], 2).astype(np.uint8), 'RGBA')
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); body.putalpha(m)
    ImageDraw.Draw(body).rounded_rectangle([1, 1, w - 2, h - 2], r, outline=line, width=max(2, int(w / 400)))
    out.alpha_composite(body, (pad, pad))
    return out, pad


def np_thumb_pil(im, w, h):
    src = im.convert('RGB'); s = max(w / src.width, h / src.height)
    t = src.resize((max(w, int(src.width * s) + 1), max(h, int(src.height * s) + 1)), Image.LANCZOS)
    l, tp = (t.width - w) // 2, int((t.height - h) * 0.3); t = t.crop((l, tp, l + w, tp + h)).convert('RGBA')
    m = Image.new('L', t.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], max(3, w // 10), fill=255); t.putalpha(m)
    return t


def glass_widgets_v2(c, e):
    """More widgets, artifact-style: stat tile, render bar, profile, a mini views artifact, now-playing, calendar, a 4K ring and the editorial label."""
    W, H = c.W, c.H; u = W / 1080
    k0 = ramp(c, e, 0.3, 0)
    if e.o.get('grade', 'warm') != 'none': c.img = c.img * (1 - 0.6 * k0) + grade(c.img, e.o.get('grade', 'warm')) * 0.6 * k0
    al = fade(c, e); gd = float(e.o.get('dark', 0.22)); white = (255, 255, 255)
    def bob(i): return 6 * u * math.sin(2 * math.pi * (c.lt * 0.55 + i * 0.17))
    def show(im, x, y, i, front=False):
        t0 = 0.07 * i
        if c.lt < t0: return
        place(c, im, x, y + bob(i), 0.6 + 0.4 * pop(c, t0, 0.32), 0, al * clamp((c.lt - t0) / 0.08), behind=not front, guard=front)
    G = lambda w, h, cx, cy, r=None: glass(c, w, h, r or min(w, h) * 0.2, cx, cy, amt=0.14, dark=gd)
    # 1 · stat tile
    S = 300 * u; ax, ay = 50 * u + S / 2, 118 * u + S / 2
    a = G(S, S, ax, ay); d = ImageDraw.Draw(a)
    d.ellipse([S * 0.1, S * 0.115, S * 0.16, S * 0.175], fill=ORANGE + (255,))
    d.text((S * 0.2, S * 0.145), e.o.get('title', 'Swarag'), font=font('uim', S * 0.085), fill=white + (235,), anchor='lm')
    stat=str(e.o.get('text') or 'DEMO')
    stat_size=lines_fit([stat], S*.80,'uib',S*.34)
    d.text((S*.08,S*.25),stat,font=font('uib',stat_size),fill=white+(255,))
    for j, ln in enumerate(e.o.get('sub', 'effects|one clip').split('|')): d.text((S * 0.1, S * (0.7 + 0.11 * j)), ln, font=font('uim', S * 0.085), fill=white + (235,))
    show(a, ax, ay, 0)
    # 2 · render bar
    bw, bh = 400 * u, 150 * u; bx, by = W - 50 * u - bw / 2, 118 * u + bh / 2
    b = G(bw, bh, bx, by, bh * 0.28); d = ImageDraw.Draw(b); p = ease_inout(c.lt / max(0.3, e.d * 0.85))
    d.ellipse([bh * 0.17, bh * 0.2, bh * 0.28, bh * 0.31], fill=(255, 69, 58, 255))
    d.text((bh * 0.36, bh * 0.255), e.o.get('bar_title','Illustrative progress'), font=font('uim', bh * 0.17), fill=white + (240,), anchor='lm')
    d.rounded_rectangle([bh * 0.17, bh * 0.5, bw - bh * 0.17, bh * 0.6], bh * 0.05, fill=white + (70,))
    d.rounded_rectangle([bh * 0.17, bh * 0.5, bh * 0.17 + (bw - bh * 0.34) * max(0.04, p), bh * 0.6], bh * 0.05, fill=white + (245,))
    d.text((bh*.17,bh*.78), 'DEMO WORKFLOW — NOT MEASURED',
           font=font('uim',bh*.125),fill=white+(210,),anchor='lm')
    show(b, bx, by, 1)
    # 3 · profile
    cy3 = by + bh / 2 + 22 * u + bh / 2
    g = G(bw, bh, bx, cy3, bh * 0.28); d = ImageDraw.Draw(g)
    av = face_chip(c, e, bh * 0.62); g.alpha_composite(av, (int(bw - bh * 0.19 - av.width), int((bh - av.height) / 2)))
    d.text((bh * 0.2, bh * 0.36), e.o.get('name', 'Swarag'), font=font('uib', bh * 0.22), fill=white + (255,), anchor='lm')
    d.text((bh * 0.2, bh * 0.66), e.o.get('handle', '@aiwithswarag'), font=font('uim', bh * 0.14), fill=white + (215,), anchor='lm')
    show(g, bx, cy3, 2)
    # 4 · views artifact (a mini page inside the glass)
    aw, ah = 330 * u, 330 * u; dx, dy = 50 * u + aw / 2, ay + S / 2 + 26 * u + ah / 2
    art = G(aw, ah, dx, dy, 44 * u); d = ImageDraw.Draw(art)
    d.text((24 * u, 30 * u), 'artifact · views.html', font=font('mono', 15 * u), fill=white + (220,), anchor='lm')
    inn = rrect(aw - 36 * u, ah - 74 * u, 20 * u, (250, 248, 244, 255)); di = ImageDraw.Draw(inn); iw, ih = inn.size
    for j in range(3): di.ellipse([14 * u + j * 16 * u, 14 * u, 24 * u + j * 16 * u, 24 * u], fill=((255, 95, 87), (255, 189, 46), (40, 200, 64))[j] + (255,))
    di.text((16 * u, 40 * u), 'Example chart', font=font('uib', 26 * u), fill=(24, 22, 26, 255))
    di.text((16 * u, 72 * u), 'DEMO', font=font('anton', 44 * u), fill=(200, 85, 61, 255))
    vals = [197, 140, 124, 83, 50, 40, 38]; gx0, gx1, gy1 = 16 * u, iw - 16 * u, ih - 18 * u; bwid = (gx1 - gx0) / 7 * 0.66
    for j, v in enumerate(vals):
        q = ease_out((c.lt - 0.35 - 0.05 * j) / 0.4); hh = (ih * 0.42) * v / 197 * q; x0 = gx0 + (gx1 - gx0) * j / 7
        if hh > 1: di.rounded_rectangle([x0, gy1 - hh, x0 + bwid, gy1], 5 * u, fill=((242, 196, 109) if j == 0 else (200, 85, 61)) + (255,))
    art.alpha_composite(inn, (int(18 * u), int(56 * u)))
    show(art, dx, dy, 3)
    # 5 · now playing
    mw, mh = 360 * u, 220 * u; mx, my = W - 50 * u - mw / 2, cy3 + bh / 2 + 22 * u + mh / 2
    mu = G(mw, mh, mx, my, 40 * u); d = ImageDraw.Draw(mu); A = 96 * u
    t = np.linspace(0, 1, int(A), dtype=np.float32)[:, None, None]
    art2 = Image.fromarray(np.concatenate([(np.float32([255, 150, 110]) * (1 - t) + np.float32([217, 90, 70]) * t) * np.ones((1, int(A), 1), np.float32), np.full((int(A), int(A), 1), 255, np.float32)], 2).astype(np.uint8), 'RGBA')
    am = Image.new('L', art2.size, 0); ImageDraw.Draw(am).rounded_rectangle([0, 0, art2.width - 1, art2.height - 1], 16 * u, fill=255); art2.putalpha(am)
    ad = ImageDraw.Draw(art2)
    for k_ in range(6):
        ang = k_ * math.pi / 3; ad.line([(A / 2 - 26 * u * math.cos(ang), A / 2 - 26 * u * math.sin(ang)), (A / 2 + 26 * u * math.cos(ang), A / 2 + 26 * u * math.sin(ang))], fill=(255, 255, 255, 255), width=int(7 * u))
    mu.alpha_composite(art2, (int(22 * u), int(22 * u)))
    d.text((134 * u, 44 * u), 'NOW EDITING', font=font('mono', 15 * u), fill=white + (200,), anchor='lm')
    d.text((134 * u, 78 * u), e.o.get('song', 'soft UI pops'), font=font('uib', 28 * u), fill=white + (255,), anchor='lm')
    d.text((134 * u, 108 * u), 'timing · example', font=font('uim', 20 * u), fill=white + (200,), anchor='lm')
    pp = clamp(c.lt / max(0.5, e.d)); d.rounded_rectangle([22 * u, 140 * u, mw - 22 * u, 146 * u], 3 * u, fill=white + (70,))
    d.rounded_rectangle([22 * u, 140 * u, 22 * u + (mw - 44 * u) * pp, 146 * u], 3 * u, fill=white + (240,))
    cxm, cym = mw / 2, 184 * u
    d.polygon([(cxm - 12 * u, cym - 16 * u), (cxm - 12 * u, cym + 16 * u), (cxm + 16 * u, cym)], fill=white + (255,))
    for sgn in (-1, 1):
        x = cxm + sgn * 80 * u
        d.polygon([(x - sgn * 10 * u, cym - 11 * u), (x - sgn * 10 * u, cym + 11 * u), (x + sgn * 6 * u, cym)], fill=white + (220,))
        d.polygon([(x + sgn * 4 * u, cym - 11 * u), (x + sgn * 4 * u, cym + 11 * u), (x + sgn * 20 * u, cym)], fill=white + (220,))
    show(mu, mx, my, 4)
    # 6 · calendar
    kw, kh = 330 * u, 190 * u; kx, ky = 50 * u + kw / 2, dy + ah / 2 + 26 * u + kh / 2
    ca = G(kw, kh, kx, ky, 40 * u); d = ImageDraw.Draw(ca)
    d.text((26 * u, 36 * u), e.o.get('day', 'SAMPLE'), font=font('uib', 22 * u), fill=(255, 92, 82, 255), anchor='lm')
    d.text((26 * u, 82 * u), e.o.get('date', '—'), font=font('uib', 56 * u), fill=white + (255,), anchor='lm')
    d.rounded_rectangle([22 * u, 120 * u, kw - 22 * u, 168 * u], 12 * u, fill=(255, 92, 82, 210))
    d.text((36 * u, 144 * u), e.o.get('event', 'Illustrative example'), font=font('uib', 22 * u), fill=white + (255,), anchor='lm')
    show(ca, kx, ky, 5)
    # 7 · 4K ring
    R = 250 * u; rx, ry = W - 50 * u - R / 2, my + mh / 2 + 26 * u + R / 2
    rg = G(R, R, rx, ry, 56 * u); d = ImageDraw.Draw(rg); rp = ease_inout((c.lt - 0.4) / 1.0); rr = R * 0.34
    d.ellipse([R / 2 - rr, R / 2 - rr - 8 * u, R / 2 + rr, R / 2 + rr - 8 * u], outline=white + (60,), width=int(16 * u))
    if rp > 0: d.arc([R / 2 - rr, R / 2 - rr - 8 * u, R / 2 + rr, R / 2 + rr - 8 * u], -90, -90 + 360 * rp, fill=(52, 199, 89, 255), width=int(16 * u))
    d.text((R / 2, R / 2 - 8 * u), 'DEMO', font=font('uib', 44 * u), fill=white + (255,), anchor='mm')
    d.text((R / 2, R - 26 * u), 'render', font=font('uim', 20 * u), fill=white + (210,), anchor='mm')
    show(rg, rx, ry, 6)
    # 8 · editorial label (in front)
    f1, f2 = font('uim', W * 0.045), font('uib', W * 0.045); pre, hi = 'Swarag ', 'Studio'
    tw = f1.getlength(pre) + f2.getlength(hi); ph = W * 0.105; pw = tw + ph * 0.9; py = H * 0.875
    q = glass(c, pw, ph, ph / 2, W / 2, py, amt=0.16, tint=(70, 70, 76)); d = ImageDraw.Draw(q)
    d.text(((pw - tw) / 2, ph / 2), pre, font=f1, fill=white + (255,), anchor='lm')
    d.text(((pw - tw) / 2 + f1.getlength(pre), ph / 2), hi, font=f2, fill=(255, 176, 146, 255), anchor='lm')
    show(shadowed(q, 14, 6, 70), W / 2, py, 7, front=True)


def rag_evidence_glass_widgets(c, e):
    """REPOSITORY glass-widgets: factual RAG proof cards BEHIND the real person.

    No demo views, social profile clones, fabricated rendering percentages or
    chart values. Reuses the ORIGINAL glass() blur, original place(...behind)
    person-depth segmentation, fonts and modest reveal animation. The backdrop
    and subject remain the ACTUAL source camera footage, full-screen.
    """
    kind = e.o.get('stage')
    approved = ('hook','policies','outdated-answer','rag-flow',
                'check-1','check-2','check-3','closing')
    if kind not in approved:
        raise ValueError('RAG glass-widgets requires a verified eight-stage storyboard')
    W, H = c.W, c.H
    u = W / 1080.0
    white, subdued, gold = (242,239,233,255), (205,213,213,255), (183,150,96,255)
    teal, coral = (44,154,144,255), (208,144,119,255)
    alpha = ramp(c,e,0.30,0.24)
    if alpha <= 0:return
    progress=ease_out(c.lt/0.40)
    # Executive Editorial V2 copy zone; automatic person segmentation ensures
    # all glass pixels, including blurred panel interiors, stay BEHIND Swarag.
    # Crucially, cards are never painted on top of eyes, hair or expressions.
    card_top = H * 0.083
    def f(which, pt):
        return font(which, max(8,pt*u))
    def position(panel,cx,top,index=0):
        y=top+panel.height/2.0 - (1-progress)*12*u
        # No artificial face ellipse: the actual hair/shoulder segmentation
        # provides behind-subject depth. The old injected oval caused visible
        # hard-edged gaps through readable glass labels.
        place(c,panel,cx,y,0.965+0.035*progress,0,
              alpha*clamp((c.lt-index*.065)/0.18),behind=True)
    def pane(width,height,accent):
        panel=glass(c,width,height,min(width,height)*0.105,
                    W/2,card_top+height/2,
                    amt=0.10,tint=(18,27,38),blur=max(5,int(W/90)),
                    alpha=246,dark=0.70)
        d=ImageDraw.Draw(panel)
        d.rounded_rectangle((14*u,15*u,width-14*u,24*u),
                            radius=4*u,fill=accent)
        return panel,d
    def tx(d,xy,value,kind='uim',pt=42,color=white,maxw=None):
        # This copy is intentionally concise, already verified against the
        # uploaded six-part fictional-policy script.
        if maxw:
            sz=pt*u
            while sz>12*u and font(kind,sz).getlength(value)>maxw:sz*=.94
        else:sz=pt*u
        d.text(xy,value,font=font(kind,sz),fill=color)
    if kind=='policies':
        w=437*u; h=287*u
        labels=(('2024','OLD POLICY','$100',coral),
                ('2026','CURRENT POLICY','$150',teal))
        for i,(year,meta,amount,accent) in enumerate(labels):
            panel,d=pane(w,h,accent)
            tx(d,(34*u,43*u),'FICTIONAL / PER NIGHT',pt=36,color=subdued,maxw=w-55*u)
            tx(d,(34*u,103*u),year,pt=47,color=white)
            tx(d,(218*u,109*u),meta,pt=34,color=accent,maxw=w-234*u)
            tx(d,(34*u,163*u),amount,'serif',106,white)
            cx=W*(0.267 if i==0 else 0.733)
            position(panel,cx,card_top,i)
    elif kind=='rag-flow':
        terms=('SEARCH','RETRIEVE','GENERATE')
        w=304*u;h=221*u
        for i,term in enumerate(terms):
            panel,d=pane(w,h,gold if i==1 else teal)
            tx(d,(29*u,43*u),f'STEP {i+1:02d}',pt=36,color=subdued)
            tx(d,(29*u,92*u),term,'uim',52,white,maxw=w-48*u)
            tx(d,(29*u,157*u),('DOCUMENTS','RELEVANT TEXT','ANSWER')[i],
               'uim',34,subdued,maxw=w-48*u)
            position(panel,W*(.18+.32*i),card_top,i)
        # The old freestanding gold sentence was illegible over the
        # real bookshelf at phone scale. Put the exact source-backed
        # takeaway inside its own dark frosted glass ribbon.
        rw,rh=916*u,132*u
        ry=H*.296
        ribbon=glass(c,rw,rh,37*u,W/2,ry,
                     amt=.08,tint=(18,27,38),blur=max(5,int(W/90)),
                     alpha=248,dark=.78)
        dr=ImageDraw.Draw(ribbon)
        reminder='RELEVANT DOES NOT ALWAYS MEAN CURRENT'
        fs=54*u
        while font('uib',fs).getlength(reminder)>rw-72*u:
            fs*=.96
        dr.text((rw/2,rh/2),reminder,font=font('uib',fs),
                fill=(242,239,233,255),anchor='mm')
        position(ribbon,W/2,ry-rh/2,3)
    elif kind in ('check-1','check-2','check-3'):
        idx=int(kind[-1])
        statement=('RIGHT VERSION?','ANSWER MATCHES SOURCE?','AUTHORIZED ACCESS?')[idx-1]
        w=905*u;h=267*u
        panel,d=pane(w,h,teal)
        tx(d,(36*u,54*u),f'VERIFICATION CHECK  {idx:02d} / 03',
           pt=34,color=subdued)
        tx(d,(36*u,124*u),statement,'uib',72,white,maxw=w-72*u)
        position(panel,W/2,card_top)
    elif kind=='hook':
        w=922*u;h=259*u
        panel,d=pane(w,h,gold)
        tx(d,(42*u,54*u),'YOUR AI CITED A SOURCE',pt=41,color=subdued)
        tx(d,(42*u,122*u),'CAN IT STILL BE WRONG?', 'serif',83,white,maxw=w-85*u)
        position(panel,W/2,card_top)
    elif kind=='outdated-answer':
        w=913*u;h=297*u
        panel,d=pane(w,h,coral)
        tx(d,(37*u,49*u),'FICTIONAL AI ANSWER',pt=34,color=subdued)
        tx(d,(37*u,111*u),'$100 / NIGHT', 'serif',92,white)
        tx(d,(37*u,213*u),'CITED: 2024 POLICY  ·  OUTDATED',
           pt=37,color=coral,maxw=w-65*u)
        position(panel,W/2,card_top)
    elif kind=='closing':
        w=916*u;h=275*u
        panel,d=pane(w,h,gold)
        tx(d,(38*u,48*u),'A CITATION IS WHERE',pt=46,color=subdued)
        tx(d,(38*u,106*u),'VERIFICATION STARTS', 'serif',94,white,
           maxw=w-75*u)
        tx(d,(38*u,212*u),'NOT WHERE IT ENDS',pt=36,color=gold)
        position(panel,W/2,card_top)


@effect('glass-widgets', 'minimalist floating data widgets and mini artifacts')
def executive_glass_widgets(c,e):
    """Native frosted executive glass, not a duplicated dark template."""
    W=c.W
    simple=e.o.get('look')=='simple'
    headline=str(e.o.get('text') or 'ILLUSTRATIVE CONCEPT').upper()[:38]
    detail=str(e.o.get('sub') or 'STRATEGY  •  DELIVERY')[:54]
    if not e.o.get('metric_source') and not e.o.get('hypothetical_example'):
        if any(ch.isdigit() for ch in headline):
            raise ValueError('GLASS_WIDGET_NUMERIC_CLAIM_REQUIRES_SOURCE')
    w=int(W*.88)
    h=int(W*(.275 if simple else .385))
    cx,cy,scale=safe_panel_layout(c,w,h,'above',min_scale=.56)
    lay=glass(c,w,h,max(5,int(W*.026)),cx,cy,
              amt=.18,tint=(24,41,51),dark=.33,
              blur=max(7,W//27))
    d=ImageDraw.Draw(lay)
    pad=int(W*.047)
    # Strong enough ivory type for actual phone-sized playback.
    fs=lines_fit([headline],w-2*pad,'uib',int(W*.061))
    if fs<int(W*.041):raise ValueError('GLASS_WIDGET_HEADLINE_TOO_LONG')
    d.text((pad,W*.069),headline,font=font('uib',fs),
           fill=(249,249,244,255),anchor='lm')
    d.line((pad,W*.128,w-pad,W*.128),
           fill=(44,154,144,230),width=max(2,W//118))
    subsize=lines_fit([detail],w-2*pad,'uim',int(W*.042))
    d.text((pad,W*.195),detail,font=font('uim',subsize),
           fill=(231,243,240,255),anchor='lm')
    if not simple:
        # The standard look has a distinct second glass compartment,
        # grouped with the primary content. The SIMPLE look has none.
        pill=str(e.o.get('pill') or 'REVIEW → EXECUTION').upper()[:36]
        bottom_y=int(W*.252)
        d.rounded_rectangle((pad,bottom_y,w-pad,h-W*.027),
                            radius=max(4,int(W*.018)),
                            fill=(14,37,46,196),
                            outline=(108,175,175,142),
                            width=max(1,W//180))
        pf=lines_fit([pill],w-3*pad,'uib',int(W*.044))
        d.text((w/2,(bottom_y+h-W*.027)/2),pill,
               font=font('uib',pf),
               fill=(237,247,245,255),anchor='mm')
    d.rounded_rectangle((1,1,w-2,h-2),
                        radius=max(5,int(W*.026)),
                        outline=(228,239,238,94),
                        width=max(1,W//220))
    place_safe_panel(c,lay,'above',alpha=fade(c,e)*clamp(c.lt/.16),
                     min_scale=.56)


def fx_glass_widgets(c, e):
    if e.o.get('look') == 'rag-evidence':
        return rag_evidence_glass_widgets(c,e)
    if getattr(c,'face_priority',False):
        return executive_glass_widgets(c,e)
    (glass_widgets_v1 if e.o.get('look') == 'simple' else glass_widgets_v2)(c, e)


@effect('timeline', 'a dark red cinematic grade with an editing timeline, a REC timecode and a glowing playhead')
def studio_timeline(c,e):
    """Production timeline with legible tracks, no invented recording timecode."""
    W=c.W
    w,h=int(W*.87),int(W*.34)
    lay=rrect(w,h,max(5,int(W*.025)),(16,31,43,244))
    d=ImageDraw.Draw(lay)
    pad=W*.045
    title=str(e.o.get('text','EDIT TIMELINE')).upper()[:25]
    f=lines_fit([title],w*.73,'uib',int(W*.049))
    d.text((pad,W*.061),title,font=font('uib',f),
           fill=(244,246,245,255),anchor='lm')
    d.text((w-pad,W*.061),'SOURCE',
           font=font('uim',int(W*.029)),fill=(188,213,215,255),
           anchor='rm')
    d.line((pad,W*.111,w-pad,W*.111),
           fill=(191,208,212,100),width=max(1,W//180))
    progress=clamp(c.lt/max(e.d,.25))
    for track in range(2):
        yy=W*(.14+.085*track)
        d.rounded_rectangle((pad,yy,w-pad,yy+W*.058),
                            radius=W*.008,fill=(49,67,82,255))
        for seg in range(3):
            x=pad+(w-pad*2)*(.035+.32*seg)
            end=x+(w-pad*2)*(.25 if track==0 else .19)
            col=(44,154,144,255) if (track+seg)%2==0 else (130,149,166,255)
            d.rounded_rectangle((x,yy+W*.007,end,yy+W*.051),
                                radius=W*.006,fill=col)
    play=pad+(w-2*pad)*(.03+.94*progress)
    d.line((play,W*.126,play,W*.312),
           fill=(249,240,216,255),width=max(2,W//115))
    place_adaptive_panel(c,lay,'below',
                         alpha=fade(c,e)*clamp(c.lt/.12),min_scale=.35)

def fx_timeline(c, e):
    studio = globals().get('studio_timeline')
    (studio if studio and e.o.get('look') != 'red' else red_timeline)(c, e)


_emoji = {}
def emoji(ch, size):
    """A colour emoji as an RGBA image (Apple Color Emoji on a Mac). Returns None where the font is missing."""
    k = (ch, int(size))
    if k not in _emoji:
        try:
            f = ImageFont.truetype('/System/Library/Fonts/Apple Color Emoji.ttc', 160)
            im = Image.new('RGBA', (200, 200), (0, 0, 0, 0)); ImageDraw.Draw(im).text((20, 10), ch, font=f, embedded_color=True)
            im = im.crop(im.getbbox()); _emoji[k] = im.resize((int(size), int(size * im.height / im.width)), Image.LANCZOS)
        except Exception:
            _emoji[k] = None
    return _emoji[k]


def comment_sheet(c, e):
    """Reels 1021 + VOX look: an Instagram Comments sheet above your head (your hair in front). The word types in, posts,
    gets a heart, then your reply drops in with a link chip."""
    W, H = c.W, c.H; u = W / 1080; al = fade(c, e)
    word = e.o.get('text', 'EFFECTS'); handle = e.o.get('handle', 'aiwithswarag')
    reply = e.o.get('reply', 'Sent you the pack'); chip = e.o.get('chip', '42 effects')
    sw, sh = 740 * u, 450 * u
    t_post = 0.3 + 0.06 * len(word) + 0.1; t_heart, t_rep = t_post + 0.25, t_post + 0.4
    sheet = rrect(sw, sh, 30 * u, (38, 38, 40, 248)); d = ImageDraw.Draw(sheet)
    white, grey, blue = (245, 245, 245, 255), (160, 160, 166, 255), (0, 149, 246, 255)
    d.rounded_rectangle([sw / 2 - 32 * u, 14 * u, sw / 2 + 32 * u, 20 * u], 3 * u, fill=(110, 110, 116, 255))
    d.text((sw / 2, 50 * u), 'Comments', font=font('uib', 26 * u), fill=white, anchor='mm')
    d.line([(0, 80 * u), (sw, 80 * u)], fill=(60, 60, 64, 255), width=max(1, int(2 * u)))
    def avatar(sz):
        a = Image.new('RGBA', (int(sz), int(sz)), (0, 0, 0, 0)); ad = ImageDraw.Draw(a)
        ad.ellipse([0, 0, sz - 1, sz - 1], fill=(233, 90, 140, 255)); ad.text((sz / 2, sz / 2), 'V', font=font('uib', sz * 0.5), fill=(255, 255, 255, 255), anchor='mm')
        return a
    if c.lt < t_post:
        d.text((sw / 2, 190 * u), 'Start the conversation.', font=font('uim', 21 * u), fill=grey, anchor='mm')
    else:
        q = ease_out((c.lt - t_post) / 0.25); oy = (1 - q) * -20 * u; a8 = int(255 * clamp(q * 1.5))
        av = avatar(46 * u); av.putalpha(av.split()[3].point(lambda v: v * a8 // 255)); sheet.alpha_composite(av, (int(26 * u), int(100 * u + oy)))
        d.text((88 * u, 108 * u + oy), 'you', font=font('uib', 19 * u), fill=white[:3] + (a8,), anchor='lm')
        d.text((88 * u + font('uib', 19 * u).getlength('you ') + 4 * u, 108 * u + oy), 'now', font=font('uim', 18 * u), fill=grey[:3] + (a8,), anchor='lm')
        d.text((86 * u, 128 * u + oy), word, font=font('uib', 50 * u), fill=white[:3] + (a8,))
        d.text((88 * u, 196 * u + oy), 'Reply', font=font('uim', 17 * u), fill=grey[:3] + (a8,), anchor='lm')
        hk = ease_back((c.lt - t_heart) / 0.3)
        if hk > 0:
            hh = heart(30 * u * hk, (255, 48, 64)); sheet.alpha_composite(hh, (int(sw - 46 * u - hh.width / 2), int(130 * u - hh.height / 2)))
        rk = ease_out((c.lt - t_rep) / 0.25)
        if rk > 0:
            ra = int(255 * clamp(rk * 1.5)); ry = 226 * u + (1 - rk) * 16 * u; rx = 88 * u
            fc = face_chip(c, e, 34 * u); fc.putalpha(fc.split()[3].point(lambda v: v * ra // 255)); sheet.alpha_composite(fc, (int(rx), int(ry)))
            d.text((rx + 46 * u, ry + 8 * u), handle, font=font('uib', 18 * u), fill=white[:3] + (ra,), anchor='lm')
            d.text((rx + 46 * u + font('uib', 18 * u).getlength(handle) + 10 * u, ry + 8 * u), 'Author', font=font('uim', 16 * u), fill=grey[:3] + (ra,), anchor='lm')
            d.text((rx + 46 * u, ry + 36 * u), reply, font=font('uim', 22 * u), fill=white[:3] + (ra,), anchor='lm')
            gift = emoji('🎁', 24 * u)
            if gift is not None:
                g2 = gift.copy(); g2.putalpha(g2.split()[3].point(lambda v: v * ra // 255))
                sheet.alpha_composite(g2, (int(rx + 52 * u + font('uim', 22 * u).getlength(reply)), int(ry + 36 * u - g2.height / 2)))
            ck = ease_back((c.lt - t_rep - 0.12) / 0.3)
            if ck > 0:
                ct = text_img(chip, 19 * u, 'uib', (20, 20, 22)); lk = emoji('🔗', 20 * u)
                cw_ = ct.width + (lk.width + 4 * u if lk is not None else 0) + 10 * u
                cp = rrect(cw_, ct.height * 0.9, ct.height * 0.45, (255, 214, 10, 255))
                x0 = 6 * u
                if lk is not None: cp.alpha_composite(lk, (int(x0 + 4 * u), int((cp.height - lk.height) / 2))); x0 += lk.width + 4 * u
                cp.alpha_composite(ct, (int(x0), int((cp.height - ct.height) / 2)))
                cp = cp.resize((max(1, int(cp.width * (0.6 + 0.4 * ck))), max(1, int(cp.height * (0.6 + 0.4 * ck)))))
                sheet.alpha_composite(cp, (int(rx + 46 * u), int(ry + 56 * u)))
    ey = sh - 140 * u
    chars = ['❤️', '🙌', '🔥', '👏', '😢', '😍', '😮', '😂']
    for j, ch in enumerate(chars):
        im = emoji(ch, 36 * u)
        if im is not None: sheet.alpha_composite(im, (int(36 * u + j * (sw - 72 * u - 36 * u) / 7), int(ey)))
    iy = sh - 78 * u
    sheet.alpha_composite(avatar(48 * u), (int(22 * u), int(iy)))
    d.rounded_rectangle([82 * u, iy, sw - 22 * u, iy + 48 * u], 24 * u, fill=(54, 54, 58, 255))
    typed = word[:int(clamp((c.lt - 0.3) / (0.06 * len(word))) * len(word) + 1e-3)] if c.lt < t_post else ''
    if typed:
        d.text((104 * u, iy + 24 * u), typed, font=font('uib', 26 * u), fill=white, anchor='lm')
        if int(c.lt * 4) % 2: d.rectangle([104 * u + font('uib', 26 * u).getlength(typed) + 3 * u, iy + 10 * u, 106 * u + font('uib', 26 * u).getlength(typed) + 3 * u, iy + 38 * u], fill=(0, 149, 246, 255))
    else:
        d.text((104 * u, iy + 24 * u), f'Add a comment for {handle}', font=font('uim', 20 * u), fill=grey, anchor='lm')
    pressed = t_post - 0.08 <= c.lt < t_post
    d.text((sw - 44 * u, iy + 24 * u), 'Post', font=font('uib', 23 * u), fill=(blue if typed else (70, 110, 160, 255)) if not pressed else (140, 200, 255, 255), anchor='rm')
    sheet = shadowed(sheet, 22, 10, 120)
    bottom = c.fy - c.fw * 0.5; top = bottom - sheet.height
    s = 1.0
    if top < H * 0.02: s = max(0.6, (bottom - H * 0.02) / sheet.height)
    cy = bottom - sheet.height * s / 2 + 3 * u * math.sin(c.lt * 3.2)
    place(c, sheet, W / 2 * 0.5 + c.fx * 0.5, cy, s * (0.85 + 0.15 * ease_back(c.lt / 0.3)), 1.2, al * clamp(c.lt / 0.1), behind=True)


@effect('comment-box', 'an Instagram comments sheet above your head types your word, posts it, gets a heart and your reply')
def fx_comment_box(c, e):
    (comment_bar if e.o.get('look') == 'bar' else comment_sheet)(c, e)


# ---------- pack 3: showcase effects (added 23 Oct 2026) ----------
def num_parts(s):
    """'197K' -> (197.0, 'K', 0 decimals); '59%' -> (59.0, '%', 0); '4.8' -> (4.8, '', 1)."""
    s = str(s).strip(); i = len(s)
    while i and not (s[i - 1].isdigit()): i -= 1
    n = s[:i].replace(',', '') or '0'
    return float(n), s[i:], (len(n.split('.')[1]) if '.' in n else 0)


@effect('liquid-glass-graph', 'a liquid glass card floats under your chin while a graph climbs and the number counts up')
def fx_liquid_glass_graph(c,e):
    """Sourced or clearly illustrative legible graph, with a distinct bento look."""
    W=c.W
    bento=e.o.get('look')=='bento'
    # The bento layout has a separate real section, not a note covering
    # the plot. Reserve vertical space for the source key before the chart.
    w,h=int(W*.85),int(W*(.51 if bento else .38))
    region,cx,cy,_=adaptive_panel_location(c,w,h,'below',min_scale=.34)
    im=glass(c,w,h,W*.030,cx,cy,amt=.09,
             tint=(16,35,43),dark=.55,blur=max(5,W//40))
    d=ImageDraw.Draw(im)
    pad=W*.041
    source=str(e.o.get('metric_source','')).strip()
    illustrative=bool(e.o.get('hypothetical_example'))
    if getattr(c,'face_priority',False) and not illustrative and not source:
        raise ValueError('GLASS_GRAPH_REQUIRES_SOURCE_OR_EXPLICIT_ILLUSTRATION')
    label=str(e.o.get('text','ILLUSTRATIVE TREND')).upper()[:28]
    label_fs=lines_fit([label],w*.61,'uib',int(W*.044))
    d.text((pad,W*.068),label,font=font('uib',label_fs),
           fill=(244,248,246,255),anchor='lm')
    tag='ILLUSTRATIVE · NOT MEASURED' if illustrative else source[:35].upper()
    tag_fs=lines_fit([tag],w-pad*2,'uim',int(W*.027))
    d.text((pad,W*.129),tag,font=font('uim',tag_fs),
           fill=(242,212,161,255),anchor='lm')
    a,_,_=num_parts(e.o.get('from','0'))
    b,suffix,dp=num_parts(e.o.get('to','0'))
    g=ease_inout((c.lt-.16)/max(.3,e.d*.72))
    v=a+(b-a)*g
    number=f'{v:.{dp}f}{suffix}'
    vf=lines_fit([number],w*.28,'uib',int(W*.084))
    d.text((w-pad,W*.067),number,font=font('uib',vf),
           fill=(242,249,245,255),anchor='rm')
    x0,x1=pad,w-pad
    y0,y1=h-W*.040,h*.53
    for i in range(1,3):
        y=y0-(y0-y1)*i/3
        d.line((x0,y,x1,y),fill=(238,248,248,36),width=max(1,W//180))
    count=max(1,int(44*g))
    pts=[(x0+(x1-x0)*j/44,y0-(y0-y1)*(j/44)**1.5)
          for j in range(count+1)]
    accent=rgb(e.o.get('color'),(44,154,144))
    if len(pts)>1:
        under=Image.new('RGBA',(w,h),(0,0,0,0))
        dd=ImageDraw.Draw(under)
        dd.polygon(pts+[(pts[-1][0],y0),(x0,y0)],
                   fill=accent+(42,))
        im.alpha_composite(under)
        d=ImageDraw.Draw(im)
        d.line(pts,fill=accent+(255,),
               width=max(2,W//95),joint='curve')
        ox,oy=pts[-1];rad=max(2,W*.011)
        d.ellipse((ox-rad,oy-rad,ox+rad,oy+rad),
                  fill=(240,249,247,255))
    if bento:
        # One atomic two-part bento unit. The old second independent strip
        # was placed across the first chart when both sought the top zone.
        note=str(e.o.get('bento_label',
            'ILLUSTRATIVE VIEW' if illustrative else 'SOURCE CHECK'))[:33]
        ix,iy=int(W*.033),int(W*.167)
        iw,ih=int(w-W*.066),int(W*.077)
        bd=ImageDraw.Draw(im)
        bd.rounded_rectangle((ix,iy,ix+iw,iy+ih),
                             radius=max(3,int(W*.014)),
                             fill=(21,45,57,240),
                             outline=(44,154,144,190),
                             width=max(1,W//180))
        ff=lines_fit([note],iw*.91,'uib',int(W*.041))
        bd.text((ix+iw*.50,iy+ih*.50),note.upper(),
                font=font('uib',ff),
                fill=(241,249,247,255),anchor='mm')
    place_safe_panel(c,im,region,
                     alpha=fade(c,e)*clamp(c.lt/.12),min_scale=.34)

@effect('carousel-spin', 'your reels spin around you in a 3D carousel, then slow to a stop')
def fx_carousel_spin(c, e):
    if getattr(c,'face_priority',False):
        return executive_motion_cards(c,e,'carousel')
    K = int(e.o.get('count', max(6, min(12, len(e.cards))))); cw = int(c.W * float(e.o.get('size', 0.3)))
    def mk():
        out = []
        for i, im in enumerate(e.cards):
            f = card(vary(im, i) if e.o.get('images') is None else im, cw)
            dk = f.copy(); a = np.asarray(dk).copy(); a[..., :3] = (a[..., :3] * 0.55).astype(np.uint8); out.append((f, Image.fromarray(a, 'RGBA')))
        return out
    cards = cached(e, 'cards', mk)
    k = ramp(c, e, 0.3, 0.25); xx, yy = grid(c)
    d = ((xx - c.fx) / (c.W * 0.55)) ** 2 + ((yy - (c.fy + c.H * 0.15)) / (c.H * 0.5)) ** 2
    dim = 1 - k * 0.5 * np.clip(d, 0, 1) - k * 0.12
    c.img *= (dim * (1 - c.m) + c.m)[..., None]
    p = clamp(c.lt / e.d); spin = float(e.o.get('turns', 1.1)) * 2 * math.pi * (1 - (1 - p) ** 2.4)
    intro, out = ease_out(c.lt / 0.45), fade(c, e, 0.25)
    R, ry = c.W * 0.56 * intro, c.H * 0.07
    cy = c.fy + c.fw * 1.8
    items = sorted((math.cos(i * 2 * math.pi / K + spin), i * 2 * math.pi / K + spin, i) for i in range(K))
    for depth, th, i in items:
        n = len(cards); f, dk = cards[(i * (3 if n % 3 else 2)) % n]; src = f if depth >= 0 else dk  # spread similar covers apart
        sx = max(0.06, abs(math.cos(th)) ** 0.6)
        s = (0.72 + 0.34 * (depth + 1) / 2) * (0.5 + 0.5 * intro)
        w2, h2 = max(2, int(src.width * s * sx)), max(2, int(src.height * s))
        place(c, src.resize((w2, h2), Image.BILINEAR), c.fx + R * math.sin(th), cy + ry * depth, 1.0, 0,
              out * clamp(c.lt / 0.12) * (0.85 + 0.15 * depth), behind=depth < 0, guard=depth >= 0)


MATCH_TXT = ('one clip went in and every cut came back before lunch while editors once spent whole weeks rebuilding the same '
             'timeline by hand early users called it unsettling then impossible to ignore the dead air was gone the captions '
             'matched and the colour finally looked like the room it was shot in nobody opened an editing app all week').split()


def match_page_editorial(c, e, page_no):
    """Source-backed news-card match cut, without a wall of repeated prose.

    The original full-page word-matching effect remains available when the
    user explicitly selects the unbranded original look. Executive mode uses
    an actual short excerpt over authentic moving source camera footage.
    """
    import textwrap
    W,H=c.W,c.H
    bg=Image.fromarray(np.uint8(np.clip(c.img,0,1)*255)).convert('RGBA')
    face_top=face_protection_rect(c)[1]
    top=int(H*.045)
    max_height=max(int(H*.14),min(int(H*.25),int(face_top-top-H*.018)))
    pw=int(W*.90)
    ph=max_height
    if ph<int(W*.26):
        ph=int(W*.26)
    panel=rrect(pw,ph,max(6,int(W*.022)),(242,239,233,246))
    d=ImageDraw.Draw(panel)
    accent=rgb(e.o.get('color'),(44,154,144))
    margin=int(W*.047)
    band=max(2,int(W*.012))
    d.rectangle((margin,margin,margin+int(W*.15),margin+band),fill=accent+(255,))
    source_ok=e.o.get('source_verified') is True
    heading='VERIFIED SOURCE EXCERPT' if source_ok else 'ILLUSTRATIVE / DEMO'
    d.text((margin,margin+int(W*.022)),heading,font=font('uib',W*.032),fill=(35,52,62,255))
    word=str(e.o.get('text') or 'EXAMPLE').upper().strip()
    word=word[:42]
    title_size=lines_fit([word],pw-margin*2,'uib',int(W*.079))
    d.text((margin,margin+int(W*.095)),word,font=font('uib',title_size),fill=accent+(255,))
    supplied=str(e.o.get('article_text') or '').strip()
    if not supplied: supplied='Demonstration typography only. No article is asserted.'
    body_size=max(11,int(W*.051))
    # two lines only, using the actual provided excerpt; long source text
    # must be shortened by the editor, not tiled into fake article pages.
    max_chars=max(12,int((pw-margin*2)/(body_size*.62)))
    wrapped=textwrap.wrap(supplied,width=max_chars,break_long_words=False)
    for i,line in enumerate(wrapped[:2]):
        d.text((margin,margin+int(W*.165)+i*body_size*1.22),line,
               font=font('uim',body_size),fill=(40,48,55,255))
    if len(wrapped)>2:
        d.text((pw-margin,ph-int(W*.037)),'EXCERPT',font=font('uim',max(7,int(W*.027))),
               fill=(90,96,102,255),anchor='rm')
    # Gentle variation between news cards; no fabricated pages/metrics.
    if page_no % 2:
        rule_y=ph-int(W*.03)
        d.line((margin,rule_y,pw-margin,rule_y),fill=accent+(160,),width=band)
    bg.alpha_composite(panel,(int((W-pw)/2),top))
    return np.asarray(bg.convert('RGB'),np.uint8)


def match_page(c, e, j, wx, wy):
    """One article page, with the key word in a red box locked at (wx, wy)."""
    W, H = c.W, c.H; rnd = random.Random(31 + j)
    paper = [(246, 243, 236), (236, 229, 212), (251, 251, 250), (241, 236, 228), (232, 232, 230), (248, 240, 228)][j % 6]
    kind = ['serif', 'mont', 'ui', 'serif', 'anton', 'monts'][j % 6]
    size = W * [0.085, 0.07, 0.072, 0.095, 0.08, 0.068][j % 6]; f = font(kind, size); lh = size * 1.22
    word = e.o.get('text', 'Strategy'); red = rgb(e.o.get('color'), (214, 40, 40))
    im = Image.new('RGB', (W, H), paper); d = ImageDraw.Draw(im); ink = (40, 38, 36)
    base = f.getbbox('Ag'); asc = -base[1]
    ww = f.getlength(word); bx0 = wx - ww / 2
    # Real business edits may supply their own verified words. Never publish
    # an apparently cited article assembled from hard-coded synthetic claims.
    supplied = str(e.o.get('article_text') or '').strip().split()
    vocabulary = supplied if supplied else MATCH_TXT
    counter = j * 23
    def run(x, y, direction):
        nonlocal counter
        while (x < W + size if direction > 0 else x > -size * 6):
            w_ = vocabulary[counter % len(vocabulary)] + ' '
            counter += 1
            if direction < 0: x -= f.getlength(w_)
            d.text((x, y), w_, font=f, fill=ink)
            if direction > 0: x += f.getlength(w_)
    off = rnd.uniform(0, size * 3)
    ys = wy - asc - lh * math.ceil((wy - asc) / lh + 1)
    y = ys
    while y < H + lh:
        if abs(y - (wy - asc)) < 1: pass
        else: run(-off - rnd.uniform(0, size * 4), y, 1)
        y += lh
    ky = wy - asc
    d.rectangle([0, ky - lh * 0.1, W, ky + lh * 0.95], fill=paper)
    run(bx0 - size * 0.45, ky, -1); run(bx0 + ww + size * 0.45, ky, 1)
    a = np.asarray(im, np.float32) / 255
    bl = cv2.GaussianBlur(a, (0, 0), W * 0.006)
    yy, xx = np.ogrid[0:H, 0:W]
    dd = np.clip((((xx - wx) / (W * 0.62)) ** 2 + ((yy - wy) / (H * 0.32)) ** 2) - 0.15, 0, 1)[..., None]
    a = a * (1 - dd) + bl * dd
    a *= (1 - 0.18 * np.clip(dd * 1.4, 0, 1))
    pg = Image.fromarray((a * 255).astype(np.uint8)).convert('RGBA')
    bf = font(kind, size); bb = bf.getbbox(word); padx, pady = size * 0.22, size * 0.12
    box = rrect(ww + 2 * padx, (bb[3] - bb[1]) + 2 * pady + size * 0.08, size * 0.08, red + (255,))
    ImageDraw.Draw(box).text((padx, pady - bb[1]), word, font=bf, fill=(255, 255, 255, 255))
    pg.alpha_composite(box, (int(bx0 - padx), int(wy - asc + bb[1] - pady)))
    if not supplied:
        # The matrix is a technical demo, not a real article or endorsement.
        stamp = ImageDraw.Draw(pg)
        stamp.text((W * 0.07, H * 0.94), 'SAMPLE TEXT / DEMO',
                   font=font('uib', W * 0.037), fill=(120, 46, 46, 255))
    return np.asarray(pg.convert('RGB'), np.uint8)


@effect('match-cut', 'news pages cut on one word, locked in place behind your head')
def fx_match_cut(c, e):
    k = clamp(c.lt / 0.06) * fade(c, e, 0.12)
    face_cam(c, 1 + 0.06 * ease_out(c.lt / e.d), 0.44)
    wx, wy = cached(e, 'anchor', lambda: (c.W / 2, max(c.H * 0.1, c.fy - c.fw * 1.55)))
    durs = [0.15, 0.15, 0.17, 0.19, 0.22, 0.26, 0.3, 0.45]; t, j = c.lt, 0
    while j < len(durs) - 1 and t > durs[j]: t -= durs[j]; j += 1
    if e.o.get('look')=='executive':
        pg = match_page_editorial(c,e,j).astype(np.float32)/255.
    else:
        pg = cached(e, ('pg', j), lambda: match_page(c, e, j, wx, wy)).astype(np.float32)/255.
    m=c.m[...,None]
    c.img = c.img*(1-k)+(pg*(1-m)+c.img*m)*k


@effect('apple-toggles', 'an iPhone settings card under your chin flips its switches on, one line at a time')
def fx_apple_toggles(c, e):
    rows = e.o.get('text', 'CLARITY|GOVERNANCE|OUTCOMES').split('|')
    if e.o.get('pos')=='below' and getattr(c,'face_priority',False):
        # The named BELOW variant is a fully independent compact component:
        # no shared shadow padding, no top fallback, and no hidden third row.
        if not 1<=len(rows)<=4:raise ValueError('TOGGLE_ROW_COUNT')
        W=c.W
        w=int(W*.78);rh=int(W*.115);h=rh*len(rows)
        im=rrect(w,h,max(5,int(W*.026)),(249,249,246,252))
        d=ImageDraw.Draw(im)
        pad=W*.045;tw=W*.115;th=W*.064
        for i,label in enumerate(rows):
            y=(i+.5)*rh
            ff=lines_fit([label],w-pad*2-tw,'uim',int(W*.046))
            if ff<int(W*.028):raise ValueError('TOGGLE_LABEL_TOO_LONG')
            d.text((pad,y),label,font=font('uim',ff),
                   fill=(22,33,41,255),anchor='lm')
            if i:d.line((pad,i*rh,w-pad,i*rh),
                        fill=(213,219,221,255),width=max(1,W//200))
            t0=.34+.28*i
            on=ease_out((c.lt-t0)/.21)
            sx=w-pad-tw
            col=tuple(int(a*(1-on)+b*on) for a,b in
                      zip((205,209,212),(44,154,144)))+(255,)
            d.rounded_rectangle((sx,y-th/2,sx+tw,y+th/2),
                                radius=th*.50,fill=col)
            kr=th*.41
            mid=sx+th/2+(tw-th)*on
            d.ellipse((mid-kr,y-kr,mid+kr,y+kr),
                      fill=(255,255,255,255))
        place_safe_panel(c,im,'below',
                         alpha=fade(c,e)*clamp(c.lt/.12),
                         min_scale=.27,max_scale=.92)
        return
    if e.o.get('pos', 'above') != 'below': face_cam(c, 1 + (float(e.o.get('zoom', 1.12)) - 1) * ease_out(c.lt / 0.5), 0.56)
    if not 1 <= len(rows) <= 4:
        raise ValueError('apple-toggles requires 1–4 short rows')
    W = c.W; cw = int(W * 0.78); rh = int(W * 0.145)
    ch = rh * len(rows); r = int(W * 0.045)
    tw, th = int(W * 0.135), int(W * 0.08); tx = cw - int(W * 0.05) - tw
    def base():
        im = rrect(cw, ch, r, (255, 255, 255, 250)); d = ImageDraw.Draw(im)
        f = font('uim', W * 0.050)
        allowed = tx - W * 0.075
        for i, s in enumerate(rows):
            if f.getlength(s) > allowed:
                raise ValueError('apple-toggles row is too long for readable phone typography')
            d.text((W * 0.05, i * rh + rh / 2), s, font=f, fill=(18, 18, 20, 255), anchor='lm')
            if i: d.line([(W * 0.05, i * rh), (cw, i * rh)], fill=(222, 222, 226, 255), width=max(2, W // 900))
        blur = max(4, W // 55)
        pad = blur * 2 + max(2, W // 120)
        return shadowed(im, blur, max(2, W // 120), 75), pad
    sh, pad = cached(e, 'base', base)
    ts = [float(x) for x in e.o['ticks'].split('|')] if e.o.get('ticks') else [0.45 + 0.34 * i for i in range(len(rows))]
    im = sh.copy(); d = ImageDraw.Draw(im)
    off, on = np.float32((233, 233, 235)), np.float32(rgb(e.o.get('color'), (52, 199, 89)))
    for i in range(len(rows)):
        u = ease_out((c.lt - ts[i]) / 0.2) if i < len(ts) else 0.0
        col = tuple(int(v) for v in off * (1 - u) + on * u) + (255,)
        x0, y0 = pad + tx, pad + i * rh + (rh - th) / 2
        d.rounded_rectangle([x0, y0, x0 + tw, y0 + th], th // 2, fill=col)
        kr = th / 2 - W * 0.006; kx = x0 + th / 2 + (tw - th) * u; ky = y0 + th / 2
        d.ellipse([kx - kr, ky - kr + W * 0.002, kx + kr, ky + kr + W * 0.004], fill=(0, 0, 0, 40))
        d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=(255, 255, 255, 255))
    q = pop(c, 0.0, 0.38); al = fade(c, e) * clamp(c.lt / 0.1)
    region='below' if e.o.get('pos','above')=='below' else 'above'
    if getattr(c,'face_priority',False):
        # Strict region: a below-face variant must never silently show above.
        place_safe_panel(c,im,region,alpha=al,min_scale=.36,
                         max_scale=.88)
    else:
        cy=(c.H*.84 if region=='below' else c.H*.14)
        place(c,im,c.W/2,cy,.68+.25*q,0,al,guard=True)


@effect('led-sign', 'the lights drop and a glowing LED sign types itself out behind you')
def fx_led_sign(c, e):
    k = ramp(c, e, 0.2, 0.2)
    face_cam(c, 1 + (float(e.o.get('push', 1.08)) - 1) * ease_inout(c.lt / e.d), 0.42)
    lines = e.o.get('text', 'STRATEGY').upper().split('|'); col = np.float32(rgb(e.o.get('color'), (255, 146, 48))) / 255
    def setup():
        mats = []
        for s in lines:
            f = font('uib', 40); w = int(f.getlength(s)) + 8
            im = Image.new('L', (w, 56), 0); ImageDraw.Draw(im).text((4, 2), s, font=f, fill=255)
            bb = im.getbbox() or (0, 0, w, 56); im = im.crop(bb)
            rows = 11; cols = max(1, round(im.width / im.height * rows))
            mats.append(np.asarray(im.resize((cols, rows), Image.BOX), np.float32) / 255 > 0.42)
        cols = max(m.shape[1] for m in mats) + 2
        cell = int(min(c.W * 0.96 / cols, c.H * 0.3 / (len(mats) * 12)))
        L = np.zeros((len(mats) * 12 - 1, cols), np.float32)
        for i, m in enumerate(mats): o = (cols - m.shape[1]) // 2; L[i * 12:i * 12 + 11, o:o + m.shape[1]] = m
        yy, xx = np.mgrid[0:cell, 0:cell].astype(np.float32); rr = np.hypot(xx - cell / 2 + 0.5, yy - cell / 2 + 0.5)
        dot = np.clip(cell * 0.36 - rr + 0.5, 0, 1)
        return L, cell, dot, np.random.default_rng(3).random(L.shape).astype(np.float32)
    L, cell, dot, rnd = cached(e, 'm', setup)
    rows, cols = L.shape
    sweep = clamp((c.lt - 0.15) / 0.75) * (cols + 4)
    lit = L * np.clip((sweep - np.arange(cols)[None, :]) / 3, 0, 1)
    flick = 0.82 + 0.18 * np.sin(rnd * 50 + c.lt * 30)
    b = np.maximum(lit * flick, 0.09)
    pan = np.kron(b, dot)[..., None] * col
    glow = cv2.GaussianBlur(pan, (0, 0), cell * 0.9)
    pan = np.clip(pan + glow * 1.6, 0, 1)
    ph, pw = pan.shape[:2]; x0 = int(c.W / 2 - pw / 2)
    y0 = int(max(c.H*.03, min(c.H*.11,
              face_protection_rect(c)[1]-ph-c.H*.018))
              if getattr(c,'face_priority',False)
              else max(c.H*.03,c.fy-c.fw*.75-ph))
    xx, yy = grid(c)
    d = ((xx - c.fx) / (c.W * 0.6)) ** 2 + ((yy - (c.fy + c.H * 0.25)) / (c.H * 0.55)) ** 2
    dim=float(e.o.get('dim',.36 if getattr(c,'face_priority',False) else .84))
    bright=1-k*(dim-.3*dim*np.clip(1-d,0,1))
    c.img *= (bright * (1 - c.m) + c.m * (1 - 0.18 * k))[..., None]
    xa, xb = max(0, x0), min(c.W, x0 + pw); ya, yb = max(0, y0), min(c.H, y0 + ph)
    if xb > xa and yb > ya:
        sub = pan[ya - y0:yb - y0, xa - x0:xb - x0] * k * (1 - c.m[ya:yb, xa:xb, None])
        c.img[ya:yb, xa:xb] = np.clip(c.img[ya:yb, xa:xb] + sub, 0, 1)


@effect('slow-push', 'a slow cinematic push-in from the wide shot to your face, the room melting out of focus')
def fx_slow_push(c, e):
    p = ease_inout(c.lt / e.d)
    face_cam(c, 1 + (float(e.o.get('zoom', 1.6)) - 1) * p, 0.4)
    s = c.W * float(e.o.get('blur', 0.006)) * p
    if s > 0.6:
        bl = cv2.GaussianBlur(c.img, (0, 0), s); m = c.m[..., None]
        c.img = c.img * m + bl * (1 - m)
    vignette(c, 0.25 * p)


# ---------- pack 3 looks: sparkle spotlight, editorial cover, glass bento (added 23 Oct 2026) ----------
def star(size, color=(255, 244, 222)):
    """A 4-point sparkle with a soft glow."""
    s = max(8, int(size)); h = s / 2; t = s * 0.075
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).polygon([(h, s * 0.02), (h + t, h - t), (s * 0.98, h), (h + t, h + t), (h, s * 0.98), (h - t, h + t), (s * 0.02, h), (h - t, h - t)], fill=tuple(color) + (255,))
    g = im.filter(ImageFilter.GaussianBlur(s * 0.07)); out = Image.alpha_composite(g, g); out.alpha_composite(im)
    r = s * 0.07; ImageDraw.Draw(out).ellipse([h - r, h - r, h + r, h + r], fill=(255, 255, 255, 255))
    return out


def gradient_text(s, size, kind, top, bot, glow=None):
    """Text filled with a vertical colour gradient (gold, chrome...), with an optional glow."""
    f = font(kind, size); bb = f.getbbox(s); pad = int(size * 0.25 + (glow[1] * 2.5 if glow else 0))
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), s, font=f, fill=255)
    g = np.linspace(0, 1, h)[:, None, None]; col = np.float32(top) * (1 - g) + np.float32(bot) * g
    im = Image.fromarray(np.dstack([np.broadcast_to(col, (h, w, 3)).astype(np.uint8), np.asarray(m)]), 'RGBA')
    if glow:
        gl = Image.new('RGBA', (w, h), tuple(glow[0]) + (0,)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(glow[1])))
        im = Image.alpha_composite(Image.alpha_composite(gl, gl), im)
    return im


def spotlight_sparkle(c, e):
    k = ramp(c, e, 0.25, 0.2); W, H = c.W, c.H
    face_cam(c, 1 + (float(e.o.get('push', 1.12)) - 1) * ease_inout(c.lt / e.d), 0.46)
    gold = np.float32(rgb(e.o.get('color'), (255, 190, 128))) / 255
    xx, yy = grid(c)
    d = ((xx - c.fx) / (W * 0.55)) ** 2 + ((yy - (c.fy + H * 0.15)) / (H * 0.5)) ** 2
    pool = np.clip(1 - d, 0, 1) ** 1.5
    strength=.40 if getattr(c,'face_priority',False) else .92
    c.img *= ((1-k*(strength-.20*pool))*(1-c.m)+c.m*(1+.018*k))[...,None]
    ox, oy = c.fx, c.fy - c.fw * 1.1
    q = 4; sy, sx = np.mgrid[0:H // q, 0:W // q].astype(np.float32) * q
    ang = np.arctan2(sy - oy, sx - ox); rad = np.hypot(sx - ox, sy - oy)
    rays = (0.5 + 0.5 * np.cos(16 * ang + c.lt * 0.9)) ** 5 * np.exp(-rad / (H * 0.42)) + 0.9 * np.exp(-(rad / (H * 0.2)) ** 2)
    rays = cv2.resize(rays.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    halo = np.clip(cv2.GaussianBlur(c.m, (0, 0), W * 0.012) * 1.6 - c.m, 0, 1)
    rays_int=.10 if getattr(c,'face_priority',False) else .32
    halo_int=.16 if getattr(c,'face_priority',False) else .70
    c.img+=(rays*rays_int+halo*halo_int)[...,None]*gold*k*(1-c.m[...,None])
    word = e.o.get('text', 'STRATEGY')
    def wimg():
        size = int(H * 0.2)
        while size > 20 and font('didonei', size).getlength(word) > W * 0.86: size = int(size * 0.94)
        im = gradient_text(word, size, 'didonei', (255, 255, 250), (255, 200, 130), glow=(tuple(int(v * 255) for v in gold), size * 0.06))
        im = shadowed(im, int(size * 0.05), 0, 200)
        return np.asarray(im, np.float32) / 255
    wa = cached(e, 'w', wimg); wh, ww = wa.shape[:2]
    band = np.exp(-(((np.arange(ww)[None, :] + np.arange(wh)[:, None] * 0.5) - (-0.3 + 1.6 * clamp((c.lt - 0.25) / 0.9)) * ww * 1.3) / (ww * 0.07)) ** 2)
    w2 = wa.copy(); w2[..., :3] = np.clip(w2[..., :3] + band[..., None] * 0.9, 0, 1)
    s = 1.08 - 0.08 * ease_out(c.lt / 0.5)
    im = Image.fromarray((w2 * 255).astype(np.uint8), 'RGBA')
    place(c, im, W / 2, max(wh * 0.5 + H * 0.06, c.fy - c.fw * 1.05 - wh * 0.28), s, 0, k, behind=True)
    def spots():
        rnd = random.Random(9)
        count=10 if getattr(c,'face_priority',False) else 48
        return [(rnd.uniform(.04,.96),rnd.uniform(.05,.32),
                 rnd.uniform(.025,.06),rnd.uniform(0,6.3),
                 rnd.uniform(5,8),rnd.random()<.12) for _ in range(count)]
    spr = cached(e, 'star', lambda: star(W * 0.07))
    for x, y, sz, ph, sp, front in cached(e, 'sp', spots):
        a = max(0.0, math.sin(ph + c.lt * sp)) ** 2 * k
        if a < 0.03: continue
        sc = sz / 0.07 * (0.45 + 0.75 * a)
        place(c, spr, x * W, y * H, sc, c.lt * 40 + ph * 30, a, behind=not front, guard=front)


def cover_editorial(c, e):
    """High-end magazine hierarchy with complete text blocks off the face."""
    W,H=c.W,c.H
    al=fade(c,e)*clamp(c.lt/.15)
    title=str(e.o.get('text','EXECUTION')).upper()[:28]
    issue=str(e.o.get('issue','SWARAG / EXECUTIVE EDITION'))[:44]
    lines=[x.strip() for x in str(e.o.get(
        'lines','Direction|Delivery')).split('|') if x.strip()][:2]
    pw=int(W*.87);ph=int(W*.35)
    im=Image.new('RGBA',(pw,ph),(0,0,0,0))
    d=ImageDraw.Draw(im)
    cream=(249,242,231,247)
    d.rounded_rectangle((0,0,pw,ph),radius=int(W*.019),
                        fill=(26,25,30,232))
    pad=int(W*.04)
    d.text((pad,int(W*.055)),issue.upper(),
           font=font('uim',int(W*.030)),
           fill=cream)
    fsize=lines_fit([title],pw-2*pad,'didoneb',int(W*.111))
    d.text((pad,int(W*.116)),title,font=font('didoneb',fsize),
           fill=(248,234,214,255))
    d.line((pad,int(W*.235),pw-pad,int(W*.235)),
           fill=(195,163,121,220),width=max(2,int(W*.004)))
    for i,line in enumerate(lines):
        f=font('didonei',max(11,int(W*.041)))
        if f.getlength(line)>pw-2*pad:
            raise ValueError('COVER_EDITORIAL_COPY_TOO_LONG')
        d.text((pad,int(W*(.257+.050*i))),line,
               font=f,fill=(241,226,205,255))
    place_safe_panel(c,im,'above',alpha=al,min_scale=.46)

def donut(size, pct, col, label, value):
    S = int(size) * 2; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w = int(S * 0.1); pad = int(S * 0.08)
    d.arc([pad, pad, S - pad, S - pad], 0, 360, fill=(255, 255, 255, 46), width=w)
    if pct > 0.002: d.arc([pad, pad, S - pad, S - pad], -90, -90 + 360 * pct, fill=tuple(col) + (255,), width=w)
    f = font('uib', S * 0.2); d.text((S / 2, S / 2 - S * 0.02), value, font=f, fill=(255, 255, 255, 255), anchor='mm')
    f2 = font('mono', S * 0.065); d.text((S / 2, S / 2 + S * 0.15), label.upper(), font=f2, fill=(255, 255, 255, 170), anchor='mm')
    return im.resize((int(size), int(size)), Image.LANCZOS)


def glass_bento(c, e):
    W, H = c.W, c.H; al = fade(c, e) * clamp(c.lt / 0.12)
    if al <= 0: return
    green = rgb(e.o.get('color'), (52, 211, 110)); peach = (255, 160, 122)
    # 1. the big graph, on a smoked glass screen behind you
    q = ease_out(c.lt / 0.4); pw, ph = int(W * 0.9), int(H * 0.3); pcx, pcy = W / 2, H * 0.08 + ph / 2 + (1 - q) * H * 0.02
    pan = glass(c, pw, ph, W * 0.04, pcx, pcy, amt=0.06, dark=0.62, blur=max(10, W // 30))
    lay = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); pad = pw * 0.05
    g = ease_inout((c.lt - 0.2) / max(0.3, e.d * 0.75))
    d.text((pad, pad * 0.8), e.o.get('text', 'VIEWS').upper(), font=font('mono', pw * 0.026), fill=(255, 255, 255, 180))
    a, _, _ = num_parts(e.o.get('from', '0')); b, suf, dp = num_parts(e.o.get('to', '0')); s = f'{a + (b - a) * g:.{dp}f}{suf}'
    f = font('uib', pw * 0.085); d.text((pw - pad - f.getlength(s), pad * 0.45), s, font=f, fill=(255, 255, 255, 255))
    x0, x1, y0, y1 = pad, pw - pad, ph - pad * 0.8, ph * 0.3
    for j in range(1, 4): yy = y0 - (y0 - y1) * j / 3.3; d.line([(x0, yy), (x1, yy)], fill=(255, 255, 255, 34), width=max(1, W // 1000))
    n = 80; pts = [(x0 + (x1 - x0) * j / n, y0 - (y0 - y1) * ((j / n) ** 1.7) + math.sin(j / n * 17) * ph * 0.02 * (1 - j / n)) for j in range(int(n * g) + 1)]
    if len(pts) > 1:
        area = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); ImageDraw.Draw(area).polygon(pts + [(pts[-1][0], y0), (x0, y0)], fill=green + (60,)); lay.alpha_composite(area)
        lw = max(4, int(pw * 0.006)); gl = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); ImageDraw.Draw(gl).line(pts, fill=green + (255,), width=lw * 3, joint='curve')
        lay.alpha_composite(gl.filter(ImageFilter.GaussianBlur(lw * 2))); ImageDraw.Draw(lay).line(pts, fill=green + (255,), width=lw, joint='curve')
        hx, hy = pts[-1]; r = lw * 2; ImageDraw.Draw(lay).ellipse([hx - r, hy - r, hx + r, hy + r], fill=(255, 255, 255, 255), outline=green + (255,), width=lw // 2)
    pan.alpha_composite(lay)
    place(c, pan, pcx, pcy, alpha=al * q, behind=True)
    # 2. the bento tiles in front of you
    def tile(i, cx, cy, tw, th, draw):
        k = pop(c, 0.15 + 0.12 * i, 0.4)
        if k <= 0: return
        t = glass(c, tw, th, W * 0.035, cx, cy, amt=0.08, dark=0.5, blur=max(10, W // 34))
        draw(t, ImageDraw.Draw(t), tw, th); place(c, shadowed(t, max(8, W // 80), W // 120, 90), cx, cy, 0.7 + 0.3 * k, 0, al * clamp(k * 2))
    dv, dl = (e.o.get('donut', '29%::ERASE share').split('::') + [''])[:2]; pct = num_parts(dv)[0] / 100
    def dr_donut(t, d, tw, th):
        p = ease_out((c.lt - 0.35) / 0.8) * pct
        dn = donut(tw * 0.86, p, peach, dl, f'{round(p * 100)}%'); t.alpha_composite(dn, (int((tw - dn.width) / 2), int((th - dn.height) / 2)))
    kv, kl = (e.o.get('kpi', '0::example only').split('::') + [''])[:2]
    def dr_kpi(t, d, tw, th):
        b, suf, dp = num_parts(kv); v = b * ease_out((c.lt - 0.45) / 0.8)
        d.text((tw * 0.1, th * 0.18), f'{v:.{dp}f}{suf}', font=font('uib', th * 0.36), fill=(255, 255, 255, 255))
        d.text((tw * 0.1, th * 0.7), kl.upper(), font=font('mono', th * 0.1), fill=(255, 255, 255, 170))
    bv, bl = (e.o.get('bars', '4|3|2|1|1::example values').split('::') + [''])[:2]; vals = [num_parts(v)[0] for v in bv.split('|')]
    def dr_bars(t, d, tw, th):
        d.text((tw * 0.1, th * 0.06), bl.upper(), font=font('mono', tw * 0.055), fill=(255, 255, 255, 170))
        n = len(vals); bw = tw * 0.8 / n; top, base = th * 0.2, th * 0.88; mx = max(vals)
        for j, v in enumerate(vals):
            kk = ease_out((c.lt - 0.4 - 0.08 * j) / 0.5); hgt = (base - top) * v / mx * kk; x = tw * 0.1 + j * bw
            d.rounded_rectangle([x + bw * 0.14, base - hgt, x + bw * 0.86, base], int(bw * 0.18), fill=(green if j == 0 else (255, 255, 255)) + (255 if j == 0 else 150,))
            if kk > 0.6: d.text((x + bw / 2, base - hgt - tw * 0.02), f'{v:g}', font=font('uib', tw * 0.06), fill=(255, 255, 255, 230), anchor='md')
    tw = W * 0.25; gap = W * 0.02; ty = max(H * 0.5, c.fy + c.fw * 1.1)
    tile(0, W * 0.15, ty + tw * 0.5, tw, tw, dr_donut)
    tile(1, W * 0.15, ty + tw + gap + tw * 0.28, tw, tw * 0.56, dr_kpi)
    tile(2, W * 0.85, ty + tw * 0.65, tw, tw * 1.3, dr_bars)


# Private, auto-executed effect modules intentionally disabled for predictable and secure execution.


def probe(path):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate:format=duration',
                                   '-of', 'json', path], capture_output=True, text=True, check=True).stdout)
    fr = j['streams'][0]['r_frame_rate']; num, den = fr.split('/'); fps = float(num) / float(den or 1)
    png = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True).stdout
    h, w = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR).shape[:2]
    return (fr if fps <= 30.5 else '30'), min(fps, 30.0), float(j['format']['duration']), w, h


def read_frames(path, W, H, fr):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'fps={fr},scale={W}:{H}:flags=bicubic,format=rgb24', '-f', 'rawvideo', '-'],
                         stdout=subprocess.PIPE, bufsize=10 ** 8)
    n = W * H * 3
    try:
        while True:
            b = p.stdout.read(n)
            if len(b) < n: break
            yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    finally:
        if p.poll() is None: p.kill()
        p.stdout.close(); p.wait()


def guided(I, p, r=8, eps=2e-3):
    box = lambda x: cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1))
    mI, mp_ = box(I), box(p); a = (box(I * p) - mI * mp_) / (box(I * I) - mI * mI + eps); b = mp_ - a * mI
    return np.clip(box(a) * I + box(b), 0, 1)


class Tracker:
    def __init__(self, aw, ah):
        import mediapipe as mp
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.core.base_options import BaseOptions
        self.mp = mp
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=os.path.join(ROOT, 'models', 'selfie_segmenter.tflite')),
            running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True, output_category_mask=False))
        self.fd = cv2.FaceDetectorYN.create(os.path.join(ROOT, 'models', 'yunet.onnx'), '', (aw, ah), 0.6, 0.3, 20)
        self.prev = None

    def __call__(self, rgb, ms):
        img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        ms_ = self.seg.segment_for_video(img, ms).confidence_masks
        m = ms_[-1].numpy_view().astype(np.float32); m = m.reshape(m.shape[0], m.shape[1])
        if m.shape[:2] != rgb.shape[:2]: m = cv2.resize(m, (rgb.shape[1], rgb.shape[0]))
        m = guided(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255, m)
        m = np.clip((m - 0.5) * 1.6 + 0.5, 0, 1)
        if self.prev is not None: m = 0.65 * m + 0.35 * self.prev
        self.prev = m
        _, f = self.fd.detect(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        face = None
        if f is not None and len(f):
            r = max(f, key=lambda r: r[2] * r[3] * r[-1]); face = (r[0] + r[2] / 2, r[1] + r[3] / 2, r[2])
        else:
            rows = np.where((m > 0.5).sum(1) > m.shape[1] * 0.01)[0]
            if len(rows):
                top = rows[0]; band = m[top:top + max(4, int(m.shape[0] * 0.06))] > 0.5; xs = np.where(band.any(0))[0]
                fw = max(8.0, (xs.max() - xs.min()) * 0.8); face = (float(xs.mean()), top + fw * 0.7, fw)
        return (m * 255).astype(np.uint8), face


def smooth(vals, fps, tau=0.18):
    idx = [i for i, v in enumerate(vals) if v is not None]
    if not idx: return None
    arr = np.array([vals[i] if vals[i] is not None else (np.nan,) * 3 for i in range(len(vals))], np.float64)
    for k in range(3):
        col = arr[:, k]; good = ~np.isnan(col); col[~good] = np.interp(np.where(~good)[0], np.where(good)[0], col[good]); arr[:, k] = col
    a = 1 - math.exp(-1 / (fps * tau))  # forward then backward pass, so the smoothing has no lag
    for i in range(1, len(arr)): arr[i] = arr[i - 1] + a * (arr[i] - arr[i - 1])
    for i in range(len(arr) - 2, -1, -1): arr[i] = arr[i + 1] + a * (arr[i] - arr[i + 1])
    return arr


class Ctx: pass


class Fx:
    def __init__(self, d, fps):
        self.name = d['fx']; self.start = float(d['start']); self.end = float(d['end']); self.d = max(0.05, self.end - self.start)
        self.o = {k: v for k, v in d.items() if k not in ('fx', 'start', 'end')}; self.state = {}; self.cards = []



def executive_cards(labels=None):
    """Generate original, content-neutral Orbit visuals when no user assets are supplied."""
    names = [v.strip().upper() for v in str(labels or 'STRATEGY|EXECUTION|GOVERNANCE|AI ADOPTION|OUTCOMES|DELIVERY').split('|') if v.strip()]
    if not names:
        names = ['STRATEGY']
    out = []
    palettes = [((16, 25, 35), (44, 154, 144)), ((23, 40, 62), (197, 164, 109)),
                ((24, 36, 46), (130, 147, 165)), ((18, 38, 42), (44, 154, 144)),
                ((38, 36, 42), (197, 164, 109)), ((16, 25, 35), (197, 164, 109))]
    for i, title in enumerate(names[:20]):
        W, H = 486, 864
        bg, accent = palettes[i % len(palettes)]
        im = Image.new('RGB', (W, H), bg)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([24, 24, W - 25, H - 25], radius=35, outline=accent, width=3)
        d.rectangle((42, 53, 112, 61), fill=accent)
        tiny = ImageFont.truetype(FONT['uim'], 21)
        d.text((W - 42, 50), f'{i+1:02d} / {len(names):02d}', font=tiny, fill=(220, 227, 228), anchor='ra')
        x0, y0 = 43, H * 0.44
        for j, chunk in enumerate(title.split(' ')):
            sz = 64
            ft = ImageFont.truetype(FONT['uib'], sz)
            while ft.getlength(chunk) > W - 80 and sz > 24:
                sz -= 2
                ft = ImageFont.truetype(FONT['uib'], sz)
            d.text((x0, y0 + j * 72), chunk, font=ft, fill=(245, 242, 236))
        d.line([(42, H - 130), (W - 42, H - 130)], fill=accent, width=3)
        d.text((43, H - 106), 'SWARAG  /  EXECUTIVE', font=tiny, fill=(203, 213, 218))
        out.append(im)
    return out


def load_cards(folder, thumbs):
    """No silent substitution of real user-approved assets with duplicate selfies."""
    out = []
    if folder:
        if not os.path.isdir(folder):
            raise ValueError("Approved card media directory does not exist")
        for n in sorted(os.listdir(folder)):
            p = os.path.join(folder, n); ext = n.lower().rsplit('.', 1)[-1]
            if ext in ('jpg', 'jpeg', 'png', 'webp'):
                with Image.open(p) as source: out.append(source.convert('RGB'))
            elif ext in ('mp4', 'mov', 'm4v', 'webm'):
                cap = cv2.VideoCapture(p); cap.set(cv2.CAP_PROP_POS_MSEC, 1000); ok, fr = cap.read(); cap.release()
                if ok: out.append(Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)))
            if len(out) >= 40: break
        if not out:
            raise ValueError("Approved card media directory contains no decodable images or videos")
        return out
    return thumbs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('args', nargs='*', help='[effect] input.mp4 output.mp4')
    ap.add_argument('--plan'); ap.add_argument('--start', type=float); ap.add_argument('--end', type=float)
    ap.add_argument('--text'); ap.add_argument('--images'); ap.add_argument('--opt', action='append', default=[], help='key=value')
    ap.add_argument('--still', help='comma-separated seconds: save PNG check frames instead of a video')
    ap.add_argument('--width', type=int, default=1080, help='short side of the output (1080 default, 2160 for 4K)')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    if a.list:
        for i, (k, (_, d)) in enumerate(EFFECTS.items()): print(f'{i + 1:2d}. {k:15s} {d}')
        return
    if a.plan:
        src, dst = a.args[0], a.args[1]; plan = json.load(open(a.plan))
        plan = plan.get('effects', plan) if isinstance(plan, dict) else plan
    else:
        name, src, dst = a.args[0], a.args[1], a.args[2]
        d = {'fx': name, 'start': a.start or 0.0, 'end': a.end if a.end is not None else 1e9}
        if a.text: d['text'] = a.text
        if a.images: d['images'] = a.images
        for kv in a.opt: k, v = kv.split('=', 1); d[k] = v
        plan = [d]
    for d in plan:
        d['fx'] = ALIASES.get(d['fx'].lower().lstrip('/'), d['fx'].lower().lstrip('/'))
        if d['fx'] in LOOK_NAMES: d['fx'], look = LOOK_NAMES[d['fx']]; d.setdefault('look', look)
        if d['fx'] not in EFFECTS: sys.exit(f"Unknown effect '{d['fx']}'. Run --list to see all {len(EFFECTS)}.")
    fr, fps, dur, sw, sh = probe(src)
    for d in plan: d['end'] = min(float(d['end']), dur)
    if sw <= sh: W = a.width; H = int(round(a.width * sh / sw / 2)) * 2
    else: H = a.width; W = int(round(a.width * sw / sh / 2)) * 2
    aw = 540 if sw <= sh else int(round(540 * sw / sh / 2)) * 2; ah = int(round(aw * sh / sw / 2)) * 2
    fxs = [Fx(d, fps) for d in plan]
    inwin = lambda t: any(f.start - 0.5 <= t < f.end + 0.5 for f in fxs)
    print(f'Pass 1: tracking you ({len(fxs)} effect{"s" * (len(fxs) > 1)})...', flush=True)
    trk = Tracker(aw, ah); masks, faces, thumbs = {}, [], []
    n_thumb = 10; thumb_at = {int(dur * fps * (j + 0.5) / n_thumb) for j in range(n_thumb)}
    for i, fr_ in enumerate(read_frames(src, aw, ah, fr)):
        t = i / fps
        if i in thumb_at: thumbs.append(Image.fromarray(fr_.copy()))
        if inwin(t):
            m, f = trk(fr_, int(t * 1000)); masks[i] = m; faces.append(f)
        else:
            faces.append(None); trk.prev = None
    trk.seg.close()  # release native MediaPipe resources before interpreter shutdown
    sm = smooth(faces, fps)
    if sm is None: sm = np.tile([aw / 2, ah * 0.33, aw * 0.15], (len(faces), 1))
    for f in fxs:
        if f.name in CARD_FX:
            # Explicit original Swarag editorial cards are a credible choice
            # for abstract concepts. In their absence, raw source thumbnails
            # remain SHOWCASE fixtures only; premium lint blocks their use.
            f.cards = (executive_cards(f.o.get('labels'))
                if f.o.get('brand_cards') and not f.o.get('images')
                else load_cards(f.o.get('images'), thumbs))
    stills = sorted({int(round(float(s) * fps)) for s in a.still.split(',')}) if a.still else None
    enc = None
    if not stills:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fr), '-i', '-',
                                '-i', src, '-map', '0:v', '-map', '1:a:0?', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                                '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', dst], stdin=subprocess.PIPE)
    print('Pass 2: adding the effects...', flush=True)
    sc = W / aw; total = int(dur * fps)
    for i, frame in enumerate(read_frames(src, W, H, fr)):
        t = i / fps
        act = [f for f in fxs if f.start <= t < f.end]
        if stills is not None and i not in stills:
            if i > stills[-1]: break
            continue
        if act:
            c = Ctx(); c.W, c.H, c.t, c.fps = W, H, t, fps
            c.img = frame.astype(np.float32) / 255.0
            m = masks.get(i)
            c.m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0 if m is not None else np.zeros((H, W), np.float32)
            fx_, fy_, fw_ = sm[min(i, len(sm) - 1)]; c.fx, c.fy, c.fw = fx_ * sc, fy_ * sc, max(fw_ * sc, W * 0.05)
            for f in act:
                c.lt = t - f.start
                # Swarag premium rendering prioritizes the real eyes and mouth
                # even if individual original effects place an unguarded card.
                # Unbranded original showcase preserves its original behavior.
                c.face_priority = f.o.get("face_priority") is True
                c.current_fx = f.name
                c.graphic_region = f.o.get("graphic_region")
                visible_before=getattr(c,'visible_safe_panels',0)
                EFFECTS[f.name][0](c, f)
                if (c.face_priority and f.name in _REQUIRED_PANEL_VISIBLE
                    and not (f.name=='glass-widgets' and
                             f.o.get('look')=='rag-evidence')
                    and c.lt>.35 and
                    getattr(c,'visible_safe_panels',0)==visible_before):
                    raise RuntimeError(
                        'VISIBLE_PANEL_MISSING: '+f.name+
                        ' at source time %.3fs' % t)
            frame = (np.clip(c.img, 0, 1) * 255 + 0.5).astype(np.uint8)
        if stills is not None:
            out = dst if len(stills) == 1 else dst.replace('.png', f'_{t:.2f}.png')
            cv2.imwrite(out, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)); print('saved', out)
        else:
            enc.stdin.write(frame.tobytes())
            if i % int(fps * 5) == 0: print(f'  {t:5.1f}s / {dur:.1f}s', flush=True)
    if enc: enc.stdin.close(); enc.wait(); print('Done:', dst)


if __name__ == '__main__':
    main()
