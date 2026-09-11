from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from .preprocessing import PreprocessConfig, preprocess_for_features, validate_image


@dataclass(frozen=True)
class AlignmentConfig:
    max_features: int = 5000
    ratio_test: float = 0.78
    min_matches: int = 12
    ransac_reprojection_threshold: float = 3.0
    min_inlier_ratio: float = 0.25
    max_median_reprojection_error: float = 5.0
    min_overlap_ratio: float = 0.55
    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)

    def validate(self) -> None:
        if self.max_features < 100 or self.min_matches < 4:
            raise ValueError("max_features must be >=100 and min_matches >=4")
        if not 0 < self.ratio_test < 1 or not 0 <= self.min_inlier_ratio <= 1:
            raise ValueError("ratio_test and min_inlier_ratio must be within valid ranges")
        if self.ransac_reprojection_threshold <= 0 or self.max_median_reprojection_error <= 0:
            raise ValueError("reprojection thresholds must be positive")
        if not 0 <= self.min_overlap_ratio <= 1:
            raise ValueError("min_overlap_ratio must be between 0 and 1")
        self.preprocess.validate()


@dataclass(frozen=True)
class AlignmentResult:
    success: bool
    aligned_image: np.ndarray | None
    homography: np.ndarray | None
    valid_mask: np.ndarray | None
    keypoints_test: int
    keypoints_reference: int
    candidate_matches: int
    good_matches: int
    inlier_count: int
    inlier_ratio: float
    median_reprojection_error: float | None
    overlap_ratio: float
    reason: str | None = None

    def quality_dict(self) -> dict[str, int | float | bool | str | None]:
        return {
            "success": self.success,
            "keypoints_test": self.keypoints_test,
            "keypoints_reference": self.keypoints_reference,
            "candidate_matches": self.candidate_matches,
            "good_matches": self.good_matches,
            "inlier_count": self.inlier_count,
            "inlier_ratio": self.inlier_ratio,
            "median_reprojection_error": self.median_reprojection_error,
            "overlap_ratio": self.overlap_ratio,
            "reason": self.reason,
        }


def _failure(reason: str, kp_test: int = 0, kp_ref: int = 0, candidates: int = 0,
             good: int = 0) -> AlignmentResult:
    return AlignmentResult(False, None, None, None, kp_test, kp_ref, candidates, good, 0, 0.0, None, 0.0, reason)


def align_to_reference(reference: np.ndarray, test: np.ndarray,
                       config: AlignmentConfig | None = None) -> AlignmentResult:
    config = config or AlignmentConfig()
    config.validate()
    validate_image(reference, "reference")
    validate_image(test, "test")
    reference_gray = preprocess_for_features(reference, config.preprocess)
    test_gray = preprocess_for_features(test, config.preprocess)

    orb = cv2.ORB_create(nfeatures=config.max_features, scoreType=cv2.ORB_HARRIS_SCORE)
    kp_test, desc_test = orb.detectAndCompute(test_gray, None)
    kp_ref, desc_ref = orb.detectAndCompute(reference_gray, None)
    count_test, count_ref = len(kp_test), len(kp_ref)
    if desc_test is None or desc_ref is None:
        return _failure("insufficient_features", count_test, count_ref)

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    pairs = matcher.knnMatch(desc_test, desc_ref, k=2)
    good = [first for pair in pairs if len(pair) == 2 for first, second in [pair]
            if first.distance < config.ratio_test * second.distance]
    if len(good) < config.min_matches:
        return _failure("insufficient_matches", count_test, count_ref, len(pairs), len(good))

    source_points = np.float32([kp_test[match.queryIdx].pt for match in good]).reshape(-1, 1, 2)
    target_points = np.float32([kp_ref[match.trainIdx].pt for match in good]).reshape(-1, 1, 2)
    homography, inlier_mask = cv2.findHomography(
        source_points, target_points, cv2.RANSAC, config.ransac_reprojection_threshold,
    )
    if homography is None or inlier_mask is None or not np.isfinite(homography).all():
        return _failure("homography_estimation_failed", count_test, count_ref, len(pairs), len(good))

    inliers = inlier_mask.ravel().astype(bool)
    inlier_count = int(inliers.sum())
    inlier_ratio = inlier_count / len(good)
    projected = cv2.perspectiveTransform(source_points[inliers], homography)
    errors = np.linalg.norm(projected.reshape(-1, 2) - target_points[inliers].reshape(-1, 2), axis=1)
    median_error = float(np.median(errors)) if errors.size else None

    ref_height, ref_width = reference.shape[:2]
    aligned = cv2.warpPerspective(test, homography, (ref_width, ref_height), flags=cv2.INTER_LINEAR)
    source_mask = np.full(test.shape[:2], 255, dtype=np.uint8)
    valid_mask = cv2.warpPerspective(source_mask, homography, (ref_width, ref_height), flags=cv2.INTER_NEAREST)
    overlap_ratio = float(np.count_nonzero(valid_mask)) / float(ref_width * ref_height)

    reason = None
    if inlier_ratio < config.min_inlier_ratio:
        reason = "low_inlier_ratio"
    elif median_error is None or median_error > config.max_median_reprojection_error:
        reason = "high_reprojection_error"
    elif overlap_ratio < config.min_overlap_ratio:
        reason = "low_overlap"
    success = reason is None
    return AlignmentResult(success, aligned, homography, valid_mask, count_test, count_ref,
                           len(pairs), len(good), inlier_count, inlier_ratio,
                           median_error, overlap_ratio, reason)
