"""Shared test fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "data"


@pytest.fixture
def test_fai(test_data_dir):
    return test_data_dir / "test.fa.fai"


@pytest.fixture
def test_bed(test_data_dir):
    return test_data_dir / "test.bed"


@pytest.fixture
def test_haplotypes(test_data_dir):
    return test_data_dir / "test_haplotypes.bed"


@pytest.fixture
def test_gff(test_data_dir):
    return test_data_dir / "test.gff3"


@pytest.fixture
def test_paf(test_data_dir):
    return test_data_dir / "test.paf"


@pytest.fixture
def test_vcf(test_data_dir):
    return test_data_dir / "test.vcf"


@pytest.fixture
def test_bedgraph(test_data_dir):
    return test_data_dir / "test.bedGraph"


@pytest.fixture
def test_synteny(test_data_dir):
    return test_data_dir / "test_synteny.bed"


@pytest.fixture
def test_annotations(test_data_dir):
    return test_data_dir / "test_annotations.tsv"
