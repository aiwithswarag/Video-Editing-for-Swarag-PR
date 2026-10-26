"""No-dependency validation for effect plans."""
import math
AVAILABLE_EFFECTS=frozenset("""noise lineup locked-on orbit lean-in backdrop-word spotlight the-bill moody swipe todo comment-box tap pause-point uninstall reel-frame shortcut-rain reject-stamp countdown-flip rabbit-hole cover-star scribble glass-widgets red-collage split-headline pastel-word check-pills timeline headline-box profile-wall tier-list broll-split phone-fan dot-reveal headline-wall checklist liquid-glass-graph carousel-spin match-cut apple-toggles led-sign slow-push""".split())
ALIASES={"bill":"the-bill","to-do":"todo","follow":"tap","stamp":"reject-stamp","countdown":"countdown-flip","cover":"cover-star","rain":"shortcut-rain","pause":"pause-point","push":"slow-push","glass":"glass-widgets","liquid-glass":"liquid-glass-graph","carousel":"carousel-spin"}
LOOKS={"glitter-spotlight":("spotlight","sparkle")}

def validate_plan(plan,duration=None):
    if isinstance(plan,dict): plan=plan.get("effects")
    if not isinstance(plan,list) or not 1<=len(plan)<=150: raise ValueError("Plan requires 1..150 effects")
    if duration is not None and (isinstance(duration,bool) or not isinstance(duration,(int,float)) or not math.isfinite(duration) or duration<=0): raise ValueError("Invalid duration")
    clean=[]
    for i,item in enumerate(plan):
        if not isinstance(item,dict): raise ValueError(f"Effect {i}: expected object")
        d=dict(item)
        name=d.get("fx")
        if not isinstance(name,str): raise ValueError(f"Effect {i}: fx must be string")
        name=name.lower().lstrip("/")
        if name in LOOKS:
            name,look=LOOKS[name];d.setdefault("look",look)
        name=ALIASES.get(name,name)
        if name not in AVAILABLE_EFFECTS: raise ValueError(f"Effect {i}: unknown effect {name}")
        s,e=d.get("start"),d.get("end")
        for n,v in (("start",s),("end",e)):
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v): raise ValueError(f"Effect {i}: {n} not finite numeric")
        if s<0 or e<=s or (duration is not None and e>duration+1e-6): raise ValueError(f"Effect {i}: invalid time window")
        for key,value in d.items():
            if not isinstance(key,str) or len(key)>80 or isinstance(value,(list,dict)) or (isinstance(value,str) and len(value)>3000):raise ValueError(f"Effect {i}: invalid option")
        d["fx"]=name;clean.append(d)
    return clean
