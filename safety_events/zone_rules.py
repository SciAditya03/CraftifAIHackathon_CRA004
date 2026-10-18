"""Geometric zone membership rules for Workplace Safety Sentinel.

Implements point-in-polygon ray casting and bounding-box evaluation.
Supports feet-contact (recommended for ground-plane cameras), centroid, and box overlap.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from safety_events.models import BoundingBox, Point, RawDetection, RestrictedZone, ZoneRuleType


def point_in_polygon(point: Point, polygon: List[Tuple[float, float]]) -> bool:
    """Determine if a 2D point is inside a polygon using the Ray Casting Algorithm.
    
    A ray is cast from the point horizontally to +infinity.
    If the number of intersections with polygon edges is odd, the point is inside.
    
    Args:
        point: 2D Point (x, y)
        polygon: List of (x, y) vertices in order
        
    Returns:
        True if inside the polygon or on the boundary, False otherwise.
    """
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    x, y = point.x, point.y

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]

        # Check if point is on horizontal vertex level
        if min(p1y, p2y) < y <= max(p1y, p2y):
            # Check if point is to the left of the edge
            if x <= max(p1x, p2x):
                # Calculate x-coordinate of intersection with edge
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                else:
                    xinters = p1x

                if p1x == p2x or x <= xinters:
                    inside = not inside

        p1x, p1y = p2x, p2y

    return inside


def box_polygon_overlap_ratio(
    bbox: BoundingBox,
    polygon: List[Tuple[float, float]],
    grid_size: int = 5,
) -> float:
    """Approximate the fraction of bounding box area inside the polygon.
    
    Uses deterministic uniform grid sampling over the bounding box.
    Avoids external C-dependency geometric libraries (like shapely/geos).
    
    Args:
        bbox: Bounding box to test
        polygon: List of (x, y) vertices
        grid_size: Number of sample steps along each axis (grid_size^2 total points)
        
    Returns:
        Float in [0.0, 1.0] representing ratio of bbox inside polygon.
    """
    if bbox.area <= 0:
        return 0.0

    step_x = bbox.width / (grid_size + 1)
    step_y = bbox.height / (grid_size + 1)

    inside_count = 0
    total_points = grid_size * grid_size

    for i in range(1, grid_size + 1):
        sample_x = bbox.left + i * step_x
        for j in range(1, grid_size + 1):
            sample_y = bbox.top + j * step_y
            if point_in_polygon(Point(sample_x, sample_y), polygon):
                inside_count += 1

    return inside_count / float(total_points)


def normalize_bbox(
    bbox: BoundingBox,
    frame_width: float,
    frame_height: float,
) -> BoundingBox:
    """Normalize pixel bounding box coordinates to [0.0, 1.0]."""
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("Frame dimensions must be strictly positive.")
    return BoundingBox(
        left=bbox.left / frame_width,
        top=bbox.top / frame_height,
        right=bbox.right / frame_width,
        bottom=bbox.bottom / frame_height,
    )


def is_bbox_in_zone(
    bbox: BoundingBox,
    zone: RestrictedZone,
    frame_width: Optional[float] = None,
    frame_height: Optional[float] = None,
) -> bool:
    """Check if a bounding box satisfies the membership rule for a restricted zone.
    
    Coordinates are automatically converted if bbox is in pixels and zone is normalized.
    """
    eval_bbox = bbox
    # If zone is normalized [0, 1] and bbox appears to be in absolute pixels (> 1.0)
    if zone.is_normalized and (bbox.right > 1.0 or bbox.bottom > 1.0):
        fw = frame_width if (frame_width and frame_width > 0) else 1920.0
        fh = frame_height if (frame_height and frame_height > 0) else 1080.0
        eval_bbox = normalize_bbox(bbox, fw, fh)

    if zone.rule_type == ZoneRuleType.FEET_POINT:
        return point_in_polygon(eval_bbox.feet_point, zone.polygon)
    elif zone.rule_type == ZoneRuleType.BOX_CENTER:
        return point_in_polygon(eval_bbox.center, zone.polygon)
    elif zone.rule_type == ZoneRuleType.BOX_OVERLAP:
        ratio = box_polygon_overlap_ratio(eval_bbox, zone.polygon)
        return ratio >= zone.min_overlap_ratio
    else:
        raise ValueError(f"Unsupported zone rule type: {zone.rule_type}")


def evaluate_detection(
    detection: RawDetection,
    zone: RestrictedZone,
    frame_width: Optional[float] = None,
    frame_height: Optional[float] = None,
) -> bool:
    """Evaluate whether a raw detection intrudes into the given zone."""
    return is_bbox_in_zone(
        bbox=detection.bbox,
        zone=zone,
        frame_width=frame_width,
        frame_height=frame_height,
    )


def create_rectangular_zone(
    zone_id: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    name: str = "Restricted Box",
    rule_type: ZoneRuleType = ZoneRuleType.FEET_POINT,
    is_normalized: bool = True,
) -> RestrictedZone:
    """Convenience helper to create an axis-aligned rectangular zone."""
    polygon = [
        (min(x1, x2), min(y1, y2)),
        (max(x1, x2), min(y1, y2)),
        (max(x1, x2), max(y1, y2)),
        (min(x1, x2), max(y1, y2)),
    ]
    return RestrictedZone(
        zone_id=zone_id,
        polygon=polygon,
        name=name,
        rule_type=rule_type,
        is_normalized=is_normalized,
    )
