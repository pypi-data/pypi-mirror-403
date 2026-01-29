"""Tests for I/O functions."""

import pytest
import tempfile
from pathlib import Path

from chromoplot.io.bed import read_bed, read_bed_to_dataframe, write_bed, BEDRecord
from chromoplot.io.fasta import read_fai, read_chrom_sizes
from chromoplot.io.gff import read_gff, read_genes
from chromoplot.core.regions import Region


class TestFAI:

    def test_read_fai(self, test_fai):
        chroms = read_fai(test_fai)
        assert 'chr1' in chroms
        assert chroms['chr1'] == 10000000
        assert chroms['chr2'] == 8000000
        assert chroms['chr3'] == 6000000

    def test_read_chrom_sizes(self, test_data_dir):
        # Create a temp chrom.sizes file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sizes', delete=False) as f:
            f.write("chr1\t1000000\n")
            f.write("chr2\t2000000\n")
            temp_path = f.name

        try:
            chroms = read_chrom_sizes(temp_path)
            assert chroms['chr1'] == 1000000
            assert chroms['chr2'] == 2000000
        finally:
            Path(temp_path).unlink()


class TestBED:

    def test_read_bed(self, test_bed):
        records = list(read_bed(test_bed))
        assert len(records) == 3
        assert records[0].chrom == 'chr1'
        assert records[0].name == "feature1"
        assert records[0].start == 100000
        assert records[0].end == 200000

    def test_read_bed_with_region(self, test_bed):
        region = Region("chr1", 0, 300000)
        records = list(read_bed(test_bed, region=region))
        assert len(records) == 1
        assert records[0].name == "feature1"

    def test_read_bed_to_dataframe(self, test_bed):
        df = read_bed_to_dataframe(test_bed)
        assert len(df) == 3
        assert 'chrom' in df.columns
        assert 'start' in df.columns
        assert 'end' in df.columns
        assert 'name' in df.columns

    def test_bed_record_len(self):
        record = BEDRecord('chr1', 100, 200)
        assert len(record) == 100

    def test_bed_record_to_region(self):
        record = BEDRecord('chr1', 100, 200)
        region = record.to_region()
        assert region.chrom == 'chr1'
        assert region.start == 100
        assert region.end == 200

    def test_write_bed_records(self):
        records = [
            BEDRecord('chr1', 100, 200, 'gene1', 100, '+'),
            BEDRecord('chr1', 300, 400, 'gene2', 200, '-'),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            temp_path = f.name

        try:
            write_bed(records, temp_path)
            read_back = list(read_bed(temp_path))
            assert len(read_back) == 2
            assert read_back[0].name == 'gene1'
        finally:
            Path(temp_path).unlink()

    def test_read_bed_empty_region(self, test_bed):
        region = Region("chr1", 9000000, 10000000)  # No features here
        df = read_bed_to_dataframe(test_bed, region=region)
        assert len(df) == 0


class TestGFF:

    def test_read_gff(self, test_gff):
        records = list(read_gff(test_gff))
        assert len(records) > 0

        genes = [r for r in records if r.feature_type == 'gene']
        assert len(genes) == 2

    def test_read_gff_with_region(self, test_gff):
        region = Region("chr1", 0, 300000)
        records = list(read_gff(test_gff, region=region))

        genes = [r for r in records if r.feature_type == 'gene']
        assert len(genes) == 1

    def test_read_gff_with_feature_types(self, test_gff):
        records = list(read_gff(test_gff, feature_types=['gene', 'exon']))

        for r in records:
            assert r.feature_type in ['gene', 'exon']

    def test_gff_record_properties(self, test_gff):
        records = list(read_gff(test_gff))
        gene = next(r for r in records if r.feature_type == 'gene')

        assert gene.id == 'gene1'
        assert gene.name == 'TestGene1'

    def test_read_genes(self, test_gff):
        genes = read_genes(test_gff)
        assert len(genes) == 2

        gene1 = next(g for g in genes if g.id == 'gene1')
        assert gene1.name == 'TestGene1'
        assert len(gene1.transcripts) == 1
        assert len(gene1.transcripts[0].exons) == 3


from chromoplot.io.paf import read_paf, read_paf_to_dataframe, PAFRecord


class TestPAF:

    def test_read_paf(self, test_paf):
        records = list(read_paf(test_paf))
        assert len(records) == 3

        assert records[0].query_name == 'contig1'
        assert records[0].target_name == 'chr1'
        assert records[0].strand == '+'

    def test_paf_record_identity(self, test_paf):
        records = list(read_paf(test_paf))
        assert records[0].identity == pytest.approx(0.98, rel=0.01)

    def test_paf_record_query_coverage(self, test_paf):
        records = list(read_paf(test_paf))
        assert records[0].query_coverage == pytest.approx(1.0, rel=0.01)

    def test_paf_record_target_span(self, test_paf):
        records = list(read_paf(test_paf))
        assert records[0].target_span == 50000

    def test_read_paf_with_region(self, test_paf):
        region = Region("chr1", 0, 2000000)
        records = list(read_paf(test_paf, target_region=region))
        assert len(records) == 1
        assert records[0].query_name == 'contig1'

    def test_read_paf_min_length(self, test_paf):
        records = list(read_paf(test_paf, min_length=60000))
        assert len(records) == 1
        assert records[0].query_name == 'contig3'

    def test_read_paf_min_mapq(self, test_paf):
        records = list(read_paf(test_paf, min_mapq=60))
        assert len(records) == 2

    def test_paf_tags_parsed(self, test_paf):
        records = list(read_paf(test_paf))
        assert 'tp' in records[0].tags
        assert records[0].tags['tp'] == 'P'

    def test_read_paf_to_dataframe(self, test_paf):
        df = read_paf_to_dataframe(test_paf)
        assert len(df) == 3
        assert 'query_name' in df.columns
        assert 'identity' in df.columns
