# Phase 4 — PCB preprocessing and registration

## Coordinate convention

The test PCB is transformed into the reference PCB coordinate system. `align_to_reference(reference, test)` estimates a homography from test-image keypoints to reference-image keypoints and returns an aligned image with the reference dimensions.

## Pipeline

1. Validate array shape, size, numeric values, channels, and dtype.
2. Convert 8/16-bit or floating-point images to 8-bit grayscale.
3. Apply a small Gaussian blur and CLAHE for local contrast normalization.
4. Detect ORB keypoints and binary descriptors.
5. Match test descriptors to reference descriptors using Hamming distance.
6. Apply Lowe-style nearest-neighbour ratio filtering.
7. Estimate a homography using RANSAC.
8. Warp the test image and a coverage mask into reference coordinates.
9. Score registration using match count, inlier ratio, median inlier reprojection error, and overlap.
10. Compute a masked absolute difference and connected difference regions only when registration passes.

## Failure behavior

Registration returns a structured failure instead of silently producing a misleading comparison. Reasons include `insufficient_features`, `insufficient_matches`, `homography_estimation_failed`, `low_inlier_ratio`, `high_reprojection_error`, and `low_overlap`.

Thresholds are configurable because board texture, image scale, optics, and capture geometry differ. Defaults are research starting points, not certified industrial tolerances.

## CLI

```bash
python -m src.cv.cli \
  --reference samples/reference.png \
  --test samples/test.png \
  --output reports/alignment
```

Outputs include the aligned image, valid-overlap mask, grayscale difference, binary difference mask, annotated difference regions, and `registration.json` quality report.

## Limitations

- A single planar homography assumes a mostly planar PCB and limited lens distortion.
- Repetitive traces can create ambiguous ORB matches.
- Large lighting changes may remain after CLAHE and appear as differences.
- Difference regions are visual candidates, not classified defects.
- Component-level matching remains Phase 5.
