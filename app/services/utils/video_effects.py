from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import fadein, fadeout
from moviepy.video.tools.drawing import color_gradient


# FadeIn
def fadein_transition(clip: VideoFileClip, t: float) -> VideoFileClip:
    return fadein(clip, duration=t)


# FadeOut
def fadeout_transition(clip: VideoFileClip, t: float) -> VideoFileClip:
    return fadeout(clip, duration=t)


# SlideIn
def slidein_transition(clip: VideoFileClip, t: float, side: str) -> VideoFileClip:
    w, h = clip.size
    if side in ["left", "right"]:
        grad = color_gradient(w, h, p1=(0, h/2), p2=(w, h/2))
    else:  # top or bottom
        grad = color_gradient(w, h, p1=(w/2, 0), p2=(w/2, h))
        
    mask = VideoFileClip(grad).with_duration(t)
    
    if side == "left":
        position = lambda t: ('center', 'center', -w + w*t/t)
    elif side == "right":
        position = lambda t: ('center', 'center', w - w*t/t)
    elif side == "top":
        position = lambda t: ('center', 'center', 0, -h + h*t/t)
    else:  # bottom
        position = lambda t: ('center', 'center', 0, h - h*t/t)
        
    return clip.with_mask(mask).with_position(position)


# SlideOut
def slideout_transition(clip: VideoFileClip, t: float, side: str) -> VideoFileClip:
    w, h = clip.size
    if side in ["left", "right"]:
        grad = color_gradient(w, h, p1=(0, h/2), p2=(w, h/2))
    else:  # top or bottom
        grad = color_gradient(w, h, p1=(w/2, 0), p2=(w/2, h))
        
    mask = VideoFileClip(grad).with_duration(t)
    
    if side == "left":
        position = lambda t: ('center', 'center', -w*t/t)
    elif side == "right":
        position = lambda t: ('center', 'center', w*t/t)
    elif side == "top":
        position = lambda t: ('center', 'center', 0, -h*t/t)
    else:  # bottom
        position = lambda t: ('center', 'center', 0, h*t/t)
        
    return clip.with_mask(mask).with_position(position)
