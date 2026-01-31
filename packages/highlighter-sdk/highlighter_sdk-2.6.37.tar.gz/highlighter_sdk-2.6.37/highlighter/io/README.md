# IO Package Overview

This package groups the low-level I/O primitives used across the SDK (readers, writers,
codecs, and backend-specific adapters). It is intended to be the shared home for
backend implementations (PyAV, GStreamer, OpenCV, etc.) so that capabilities can
swap implementations without pulling in backend-specific logic directly.

## Current files

- `sdk/python/src/highlighter/io/base.py`: Protocols and shared types for writers.
- `sdk/python/src/highlighter/io/registry.py`: Registry that maps content types to writers.
- `sdk/python/src/highlighter/io/url.py`: URL utilities.
- `sdk/python/src/highlighter/io/writers.py`: Built-in payload writers.

## Proposed directory layout

This layout keeps each media domain separate while allowing multiple backends
per domain. It also leaves room for non-media I/O (tabular, documents, etc.).

```
io/
  base.py
  registry.py
  url.py
  writers.py
  backends/
    video/
      pyav.py
      gstreamer.py
      opencv.py
    audio/
      ffmpeg.py
      gstreamer.py
      soundfile.py
    image/
      pillow.py
      opencv.py
      vips.py
    pdf/
      pymupdf.py
      pdfminer.py
      poppler.py
    tabular/
      pandas.py
      polars.py
      pyarrow.py
    text/
      markdown.py
      docx.py
      html.py
    pointcloud/
      open3d.py
      laspy.py
```

## How to add a new backend

1. Create a backend module under `io/backends/<domain>/`.
2. Keep backend-specific parsing, error translation, and logging in that module.
3. Expose a small, stable interface (e.g., `open_stream`, `read_frame`, `close`)
   that callers can wrap in a domain-specific adapter or capability.
4. If the backend produces output compatible with existing writers, register the
   writer via `io/registry.py`. Otherwise, add a new writer in `io/writers.py` and
   register it.

## Suggested next moves

- Keep `io/writers.py` as a thin facade that imports and registers default writers.
- Move implementations into backend modules, for example:
  - `io/backends/video/pyav.py` (VideoWriter)
  - `io/backends/image/pillow.py` (ImageWriter)
  - `io/backends/entities/avro.py` (EntityWriter)
- Update `io/registry.py` to import writers from the new backend modules.
- Re-export writer classes from `io/writers.py` to keep current import paths stable.
