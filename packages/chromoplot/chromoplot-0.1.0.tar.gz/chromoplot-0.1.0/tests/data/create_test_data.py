#!/usr/bin/env python3
"""Create test data for chromoplot."""

from pathlib import Path

def main():
    data_dir = Path(__file__).parent
    
    # test.fa.fai
    with open(data_dir / "test.fa.fai", "w") as f:
        f.write("chr1\t10000000\t5\t80\t81\n")
        f.write("chr2\t8000000\t10125005\t80\t81\n")
        f.write("chr3\t6000000\t18250010\t80\t81\n")
    
    # test.bed
    with open(data_dir / "test.bed", "w") as f:
        f.write("chr1\t100000\t200000\tfeature1\t100\t+\n")
        f.write("chr1\t500000\t600000\tfeature2\t200\t-\n")
        f.write("chr1\t1000000\t1500000\tfeature3\t150\t+\n")
    
    # test_haplotypes.bed
    with open(data_dir / "test_haplotypes.bed", "w") as f:
        f.write("chr1\t0\t3000000\tB73\t1000\t.\n")
        f.write("chr1\t3000000\t7000000\tMo17\t1000\t.\n")
        f.write("chr1\t7000000\t10000000\tB73\t1000\t.\n")
    
    print("Test data created!")

if __name__ == "__main__":
    main()
