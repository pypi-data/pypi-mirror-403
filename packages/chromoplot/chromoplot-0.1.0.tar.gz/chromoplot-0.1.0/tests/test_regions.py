"""Tests for region handling."""

import pytest
from chromoplot.core.regions import Region, parse_regions
from chromoplot.core.coordinates import GenomeCoordinates


class TestRegion:

    def test_parse_full(self):
        region = Region.parse("chr1:1000000-2000000")
        assert region.chrom == "chr1"
        assert region.start == 1000000
        assert region.end == 2000000

    def test_parse_with_commas(self):
        region = Region.parse("chr1:1,000,000-2,000,000")
        assert region.start == 1000000
        assert region.end == 2000000

    def test_parse_whole_chromosome(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region.parse("chr1", coordinates=coords)
        assert region.chrom == "chr1"
        assert region.start == 0
        assert region.end == 10000000

    def test_parse_whole_chromosome_requires_coords(self):
        with pytest.raises(ValueError):
            Region.parse("chr1")

    def test_len(self):
        region = Region("chr1", 1000, 2000)
        assert len(region) == 1000

    def test_str(self):
        region = Region("chr1", 1000, 2000)
        assert str(region) == "chr1:1000-2000"

    def test_contains_int(self):
        region = Region("chr1", 1000, 2000)
        assert 1500 in region
        assert 999 not in region
        assert 2000 not in region

    def test_contains_tuple(self):
        region = Region("chr1", 1000, 2000)
        assert ("chr1", 1500) in region
        assert ("chr2", 1500) not in region

    def test_overlaps(self):
        r1 = Region("chr1", 1000, 2000)
        r2 = Region("chr1", 1500, 2500)
        r3 = Region("chr1", 3000, 4000)
        r4 = Region("chr2", 1000, 2000)

        assert r1.overlaps(r2)
        assert r2.overlaps(r1)
        assert not r1.overlaps(r3)
        assert not r1.overlaps(r4)  # Different chromosomes

    def test_intersect(self):
        r1 = Region("chr1", 1000, 2000)
        r2 = Region("chr1", 1500, 2500)

        intersection = r1.intersect(r2)
        assert intersection.start == 1500
        assert intersection.end == 2000

    def test_intersect_no_overlap(self):
        r1 = Region("chr1", 1000, 2000)
        r2 = Region("chr1", 3000, 4000)

        assert r1.intersect(r2) is None

    def test_union(self):
        r1 = Region("chr1", 1000, 2000)
        r2 = Region("chr1", 1500, 2500)

        union = r1.union(r2)
        assert union.start == 1000
        assert union.end == 2500

    def test_union_adjacent(self):
        r1 = Region("chr1", 1000, 2000)
        r2 = Region("chr1", 2000, 3000)

        union = r1.union(r2)
        assert union.start == 1000
        assert union.end == 3000

    def test_union_different_chromosomes(self):
        r1 = Region("chr1", 1000, 2000)
        r2 = Region("chr2", 1000, 2000)

        with pytest.raises(ValueError):
            r1.union(r2)

    def test_expand(self):
        region = Region("chr1", 1000, 2000)
        expanded = region.expand(500)
        assert expanded.start == 500
        assert expanded.end == 2500

    def test_expand_no_negative(self):
        region = Region("chr1", 100, 2000)
        expanded = region.expand(500)
        assert expanded.start == 0  # Clamped at 0

    def test_to_bed(self):
        region = Region("chr1", 1000, 2000)
        assert region.to_bed() == "chr1\t1000\t2000"

    def test_split(self):
        region = Region("chr1", 0, 1000)
        parts = region.split(4)
        assert len(parts) == 4
        assert parts[0] == Region("chr1", 0, 250)
        assert parts[3] == Region("chr1", 750, 1000)

    def test_windows(self):
        region = Region("chr1", 0, 1000)
        windows = list(region.windows(300))
        assert len(windows) == 4
        assert windows[0] == Region("chr1", 0, 300)
        assert windows[3] == Region("chr1", 900, 1000)

    def test_windows_overlapping(self):
        region = Region("chr1", 0, 500)
        windows = list(region.windows(200, step=100))
        assert len(windows) == 5
        assert windows[0] == Region("chr1", 0, 200)
        assert windows[1] == Region("chr1", 100, 300)

    def test_invalid_region(self):
        with pytest.raises(ValueError):
            Region("chr1", -1, 1000)

        with pytest.raises(ValueError):
            Region("chr1", 2000, 1000)


class TestParseRegions:

    def test_parse_single(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        regions = parse_regions("chr1:0-1000000", coords)
        assert len(regions) == 1
        assert regions[0].chrom == "chr1"

    def test_parse_list(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        regions = parse_regions(["chr1:0-1000000", "chr2:0-500000"], coords)
        assert len(regions) == 2

    def test_parse_none_returns_all(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        regions = parse_regions(None, coords)
        assert len(regions) == 3
        assert regions[0].chrom == "chr1"
        assert len(regions[0]) == 10000000
