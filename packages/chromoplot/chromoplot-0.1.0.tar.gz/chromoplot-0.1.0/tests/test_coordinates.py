"""Tests for coordinate system."""

import pytest
from chromoplot.core.coordinates import GenomeCoordinates


class TestGenomeCoordinates:

    def test_from_fai(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        assert coords.n_chromosomes == 3
        assert coords.get_size('chr1') == 10000000

    def test_from_dict(self):
        coords = GenomeCoordinates.from_dict({'chr1': 1000, 'chr2': 2000})
        assert coords.n_chromosomes == 2
        assert coords.get_size('chr1') == 1000

    def test_total_size(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        assert coords.total_size == 24000000

    def test_chromosome_names(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        assert coords.chromosome_names == ['chr1', 'chr2', 'chr3']

    def test_linearize(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        assert coords.linearize('chr1', 0) == 0
        assert coords.linearize('chr2', 0) == 10000000
        assert coords.linearize('chr2', 1000000) == 11000000
        assert coords.linearize('chr3', 0) == 18000000

    def test_delinearize(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        assert coords.delinearize(0) == ('chr1', 0)
        assert coords.delinearize(10000000) == ('chr2', 0)
        assert coords.delinearize(11000000) == ('chr2', 1000000)

    def test_validate_region(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        assert coords.validate_region('chr1', 0, 1000) is True
        assert coords.validate_region('chr1', 0, 10000001) is False
        assert coords.validate_region('chrX', 0, 1000) is False
        assert coords.validate_region('chr1', -1, 1000) is False
        assert coords.validate_region('chr1', 1000, 500) is False

    def test_filter_chromosomes(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)

        # Filter by include
        filtered = coords.filter_chromosomes(include=['chr1', 'chr2'])
        assert filtered.n_chromosomes == 2
        assert 'chr3' not in filtered.chromosome_names

        # Filter by exclude
        filtered = coords.filter_chromosomes(exclude=['chr3'])
        assert filtered.n_chromosomes == 2

        # Filter by min_size
        filtered = coords.filter_chromosomes(min_size=7000000)
        assert filtered.n_chromosomes == 2
        assert 'chr3' not in filtered.chromosome_names

    def test_iter_chromosomes(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        chroms = list(coords.iter_chromosomes())
        assert len(chroms) == 3
        assert chroms[0] == ('chr1', 10000000)

    def test_get_size_missing(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        with pytest.raises(KeyError):
            coords.get_size('chrX')
