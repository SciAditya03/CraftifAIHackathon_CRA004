"""Unit tests for geometric zone membership rules."""

import unittest
from safety_events.models import BoundingBox, Point, RawDetection, RestrictedZone, ZoneRuleType
from safety_events.zone_rules import (
    box_polygon_overlap_ratio,
    create_rectangular_zone,
    evaluate_detection,
    is_bbox_in_zone,
    normalize_bbox,
    point_in_polygon,
)


class TestZoneRules(unittest.TestCase):

    def setUp(self):
        # Unit square [0, 0] to [10, 10]
        self.square_polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        # Non-convex L-shaped polygon
        self.l_polygon = [
            (0.0, 0.0),
            (6.0, 0.0),
            (6.0, 3.0),
            (3.0, 3.0),
            (3.0, 6.0),
            (0.0, 6.0),
        ]

    def test_point_in_polygon_convex(self):
        self.assertTrue(point_in_polygon(Point(5.0, 5.0), self.square_polygon))
        self.assertTrue(point_in_polygon(Point(1.0, 1.0), self.square_polygon))
        self.assertFalse(point_in_polygon(Point(15.0, 5.0), self.square_polygon))
        self.assertFalse(point_in_polygon(Point(-1.0, 5.0), self.square_polygon))
        self.assertFalse(point_in_polygon(Point(5.0, 11.0), self.square_polygon))

    def test_point_in_polygon_concave(self):
        # Inside the L shape
        self.assertTrue(point_in_polygon(Point(1.0, 1.0), self.l_polygon))
        self.assertTrue(point_in_polygon(Point(5.0, 1.0), self.l_polygon))
        self.assertTrue(point_in_polygon(Point(1.0, 5.0), self.l_polygon))
        # In the cut-out corner of the L (should be outside)
        self.assertFalse(point_in_polygon(Point(5.0, 5.0), self.l_polygon))
        self.assertFalse(point_in_polygon(Point(4.0, 4.0), self.l_polygon))

    def test_polygon_too_few_vertices(self):
        self.assertFalse(point_in_polygon(Point(1.0, 1.0), [(0.0, 0.0), (1.0, 1.0)]))

    def test_box_polygon_overlap_ratio(self):
        # Bbox entirely inside square
        bbox_inside = BoundingBox(2.0, 2.0, 4.0, 4.0)
        ratio_in = box_polygon_overlap_ratio(bbox_inside, self.square_polygon)
        self.assertAlmostEqual(ratio_in, 1.0, delta=0.05)

        # Bbox entirely outside square
        bbox_outside = BoundingBox(20.0, 20.0, 25.0, 25.0)
        ratio_out = box_polygon_overlap_ratio(bbox_outside, self.square_polygon)
        self.assertEqual(ratio_out, 0.0)

        # Bbox half overlapping right boundary
        bbox_half = BoundingBox(8.0, 2.0, 12.0, 8.0)
        ratio_half = box_polygon_overlap_ratio(bbox_half, self.square_polygon)
        self.assertGreater(ratio_half, 0.3)
        self.assertLess(ratio_half, 0.7)

    def test_normalize_bbox(self):
        bbox_pixels = BoundingBox(192.0, 108.0, 384.0, 324.0)
        norm = normalize_bbox(bbox_pixels, frame_width=1920.0, frame_height=1080.0)
        self.assertAlmostEqual(norm.left, 0.1)
        self.assertAlmostEqual(norm.top, 0.1)
        self.assertAlmostEqual(norm.right, 0.2)
        self.assertAlmostEqual(norm.bottom, 0.3)

    def test_feet_point_vs_center_rule(self):
        # Zone on ground plane [0.3, 0.7] to [0.7, 1.0]
        ground_zone_feet = create_rectangular_zone(
            zone_id="danger-pit",
            x1=0.3,
            y1=0.7,
            x2=0.7,
            y2=1.0,
            rule_type=ZoneRuleType.FEET_POINT,
        )
        ground_zone_center = create_rectangular_zone(
            zone_id="danger-pit",
            x1=0.3,
            y1=0.7,
            x2=0.7,
            y2=1.0,
            rule_type=ZoneRuleType.BOX_CENTER,
        )

        # Person standing: head at y=0.5, center at y=0.6, feet at y=0.75
        standing_person = BoundingBox(left=0.45, top=0.5, right=0.55, bottom=0.75)

        # Center is at (0.5, 0.625) -> outside zone (top is 0.7)
        self.assertFalse(is_bbox_in_zone(standing_person, ground_zone_center))

        # Feet are at (0.5, 0.75) -> inside zone
        self.assertTrue(is_bbox_in_zone(standing_person, ground_zone_feet))

    def test_auto_normalization_for_pixel_coords(self):
        norm_zone = create_rectangular_zone(
            zone_id="gate-1",
            x1=0.5,
            y1=0.5,
            x2=1.0,
            y2=1.0,
            is_normalized=True,
        )
        pixel_bbox = BoundingBox(left=1200.0, top=600.0, right=1400.0, bottom=900.0)
        # Should auto-normalize with provided frame dimensions
        is_in = is_bbox_in_zone(pixel_bbox, norm_zone, frame_width=1920.0, frame_height=1080.0)
        self.assertTrue(is_in)


if __name__ == "__main__":
    unittest.main()
