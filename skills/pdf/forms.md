# PDF Form Filling Process

## Initial Assessment

Begin by determining form type:

```bash
python scripts/check_fillable_fields.py <file.pdf>
```

## For Fillable Form Fields

1. Extract field metadata:
   ```bash
   python scripts/extract_form_field_info.py input.pdf fields.json
   ```
2. Convert PDF pages to PNG images for visual analysis:
   ```bash
   python scripts/convert_pdf_to_images.py input.pdf output_dir/
   ```
3. Create a `field_values.json` mapping field IDs to values
4. Fill the form:
   ```bash
   python scripts/fill_fillable_fields.py input.pdf field_values.json output.pdf
   ```

## For Non-Fillable Forms

### Approach A - Structure-Based (Preferred)

Use `extract_form_structure.py` to detect text labels and checkboxes with exact PDF coordinates:

```bash
python scripts/extract_form_structure.py input.pdf structure.json
```

### Approach B - Visual Estimation (Fallback)

For scanned/image-based PDFs, convert to images, then use zoom refinement with ImageMagick cropping to precisely locate field boundaries before calculating coordinates.

### Hybrid Method

Combine both approaches: use structure extraction where available and visual refinement for missed elements.

## Validation

Before filling any form, validate bounding boxes:

```bash
python scripts/check_bounding_boxes.py fields.json
```

Address all reported errors before proceeding.

## Coordinate Systems

- Structure-based work uses `pdf_width`/`pdf_height` with PDF coordinates.
- Visual estimation uses `image_width`/`image_height` with pixel coordinates.
- The hybrid approach requires converting image pixels to PDF coordinates using proportional scaling.
