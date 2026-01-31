# OpenFrame

OpenFrame is a pure Python video editing toolkit that lets you blend text, images, video, and audio without ever leaving the language. It is designed for fast exports while keeping the API expressive and minimal so you can make videos very easily.

## Installation

```bash
pip install openframe
```

## Quick start

```python
from openframe import *


width, height, fps = 1980, 1080, 30

scene = Scene(start_at=0)

scene.add(
    ImageClip(
        path="bg.jpg",
        start_time=0,
        duration=5,
        position=(0, 0),
        size=(width, height),
        content_mode=ContentMode.FILL,
        fade_in_duration=1,
        fade_out_duration=1,
    )
)

scene.add(
    TextClip(
        text="OpenFrame Demo",
        start_time=0,
        duration=5,
        position=(width//2, height//2),
        anchor_point=AnchorPoint.CENTER,
        font_size=48,
        text_align=TextAlign.CENTER,
        fade_in_duration=1,
        fade_out_duration=1,
    )
)

scene.render(output_path="output.mp4", width=width, height=height, fps=fps)
```
