# Athena Python PPTX - Extended API Reference

> **Version:** 0.1.8
> **Generated:** 2026-01-28 07:56:47 UTC

This document covers **Athena-specific extensions** to the python-pptx API.
These functions are NOT available in the standard python-pptx library.

## Table of Contents

- [Slide.render](#sliderender)
- [Slide.clone](#slideclone)
- [Slides.delete_slides](#slidesdelete_slides)
- [Slides.keep_only](#slideskeep_only)

## Slide

### Slide.render

*Added in v0.1.5*

Render the slide to an image.

```python
def render(format: str = 'png', scale: int = 2, as_pil: bool = False) -> bytes | Any
```

**Parameters:**

- **format** (`str`): Image format (currently only "png" is supported) (default: `'png'`)
- **scale** (`int`): Render scale factor (default 2x for high resolution) (default: `2`)
- **as_pil** (`bool`): If True, return a PIL.Image.Image object instead of bytes. Requires the Pillow library to be installed. (default: `False`)

**Returns:**

bytes: PNG image data (if as_pil=False) PIL.Image.Image: PIL Image object (if as_pil=True) (`bytes | Any`)

**Raises:**

- `ValueError`: If an unsupported format is specified
- `ImportError`: If as_pil=True but Pillow is not installed

**Example:**

```python
# Get raw PNG bytes
png_bytes = slide.render()
with open("slide.png", "wb") as f:
    f.write(png_bytes)

# Get PIL Image (requires Pillow)
img = slide.render(as_pil=True)
img.save("slide.png")
img.show()  # Display the image

# High resolution render
img = slide.render(scale=4, as_pil=True)
```

**Note:**

> This method is Athena-specific and not available in python-pptx.

---

### Slide.clone

*Added in v0.1.6*

Clone this slide with all its content.

```python
def clone(target_index: Optional[int] = None) -> Slide
```

**Parameters:**

- **target_index** (`Optional[int]`): Zero-based index where the clone should be inserted. If None, the clone is inserted immediately after this slide. (default: `None`)

**Returns:**

Slide: The newly created slide object. (`Slide`)

**Example:**

```python
# Clone slide and insert after it
new_slide = slide.clone()

# Clone slide and insert at beginning
new_slide = slide.clone(target_index=0)

# Clone slide and insert at end
new_slide = slide.clone(target_index=len(prs.slides))
```

**Note:**

> This method is Athena-specific and not available in python-pptx.

---

## Slides

### Slides.delete_slides

*Added in v0.1.2*

Delete multiple slides from the presentation by their indices.

```python
def delete_slides(indices: list[int]) -> None
```

**Parameters:**

- **indices** (`list[int]`): List of zero-based slide indices to delete

**Raises:**

- `ValueError`: If any index is out of range
- `ValueError`: If duplicate indices are provided

**Example:**

```python
# Delete slides at indices 1, 3, and 5
prs.slides.delete_slides([1, 3, 5])

# Delete the last two slides
prs.slides.delete_slides([len(prs.slides) - 1, len(prs.slides) - 2])
```

**Note:**

> This method is Athena-specific and not available in python-pptx.

---

### Slides.keep_only

*Added in v0.1.2*

Keep only the slides at the specified indices, deleting all others.

```python
def keep_only(indices: list[int]) -> None
```

**Parameters:**

- **indices** (`list[int]`): List of zero-based slide indices to keep

**Raises:**

- `ValueError`: If any index is out of range
- `ValueError`: If duplicate indices are provided
- `ValueError`: If indices list is empty

**Example:**

```python
# Keep only the first and last slides
prs.slides.keep_only([0, len(prs.slides) - 1])

# Keep only slide at index 2
prs.slides.keep_only([2])
```

**Note:**

> This method is Athena-specific and not available in python-pptx. The order of indices does not affect the final slide order - slides maintain their relative positions.

---

## See Also

- [python-pptx Documentation](https://python-pptx.readthedocs.io/) - Standard API reference
- [Athena Python PPTX on PyPI](https://pypi.org/project/athena-python-pptx/) - Package page
