"""
HELIX GUARD - VCF Parsing & Ingestion Pipeline
Parses standard Variant Call Format (VCF v4.2) files and text streams
into canonical VariantLocus entities for downstream risk analysis.
"""

import io
import re
from typing import Dict, List, Optional, Tuple

from epistasis_engine import VariantLocus


class VCFPipeline:
    """
    Ingests and validates VCF (Variant Call Format) files and strings.
    Extracts variants, maps gene annotations, and formats VariantLocus records.
    """

    # Gene coordinate mappings for the 5-gene panel on GRCh38
    GENE_COORDINATE_MAP: Dict[str, Tuple[str, int, int]] = {
        "HBB": ("chr11", 5225000, 5230000),
        "CFTR": ("chr7", 117460000, 117720000),
        "BRCA1": ("chr17", 43040000, 43130000),
        "HEXA": ("chr15", 72340000, 72380000),
        "DMD": ("chrX", 31100000, 33360000),
        "TP53": ("chr17", 7660000, 7690000),
    }

    def infer_gene_from_locus(self, chrom: str, pos: int) -> str:
        """
        Infers gene symbol from genomic coordinates if not present in INFO field.
        """
        chrom_clean = chrom if chrom.startswith("chr") else f"chr{chrom}"
        for gene, (g_chrom, start, end) in self.GENE_COORDINATE_MAP.items():
            if chrom_clean == g_chrom and start <= pos <= end:
                return gene
        return "UNKNOWN_LOCUS"

    def parse_vcf_text(self, vcf_content: str) -> List[VariantLocus]:
        """
        Parses raw VCF text lines into a list of VariantLocus objects.
        """
        variants: List[VariantLocus] = []
        lines = vcf_content.strip().splitlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")
            if len(fields) < 5:
                # Malformed line or space-separated fallback
                fields = re.split(r"\s+", line)
                if len(fields) < 5:
                    continue

            chrom = fields[0]
            try:
                pos = int(fields[1])
            except ValueError:
                continue

            var_id = fields[2] if fields[2] != "." else f"{chrom}_{pos}"
            ref = fields[3]
            alt = fields[4]

            info_str = fields[7] if len(fields) > 7 else ""
            format_str = fields[8] if len(fields) > 8 else ""
            sample_str = fields[9] if len(fields) > 9 else ""

            # Extract gene and clinical significance from INFO
            gene_symbol = "UNKNOWN"
            pathogenicity = "Pathogenic"  # Default assumption for targeted screening
            af: Optional[float] = None

            info_dict = {}
            for item in info_str.split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    info_dict[k.upper()] = v

            if "GENE" in info_dict:
                gene_symbol = info_dict["GENE"]
            elif "SYMBOL" in info_dict:
                gene_symbol = info_dict["SYMBOL"]
            else:
                gene_symbol = self.infer_gene_from_locus(chrom, pos)

            if "CLNSIG" in info_dict:
                pathogenicity = info_dict["CLNSIG"].replace("_", " ")

            if "AF" in info_dict:
                try:
                    af = float(info_dict["AF"])
                except ValueError:
                    pass

            # Infer zygosity from genotype (GT) field
            zygosity = "HETEROZYGOUS"
            if format_str and sample_str:
                format_keys = format_str.split(":")
                sample_vals = sample_str.split(":")
                if "GT" in format_keys:
                    gt_idx = format_keys.index("GT")
                    if gt_idx < len(sample_vals):
                        gt_val = sample_vals[gt_idx]
                        if gt_val in ["1/1", "1|1"]:
                            zygosity = "HOMOZYGOUS"

            variants.append(VariantLocus(
                variant_id=var_id,
                gene_symbol=gene_symbol,
                chromosome=chrom if chrom.startswith("chr") else f"chr{chrom}",
                position=pos,
                ref_allele=ref,
                alt_allele=alt,
                pathogenicity=pathogenicity,
                allele_frequency=af,
                zygosity=zygosity
            ))

        return variants

    def get_sample_preset_vcf(self, preset_name: str) -> str:
        """
        Returns authentic sample VCF text for multi-variant testing scenarios.
        """
        if preset_name == "cftr_compound_het":
            return (
                "##fileformat=VCFv4.2\n"
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
                "chr7\t117559590\trs121908752\tCTT\t.\t99\tPASS\tGENE=CFTR;CLNSIG=Pathogenic;AF=0.012\tGT\t0|1\n"
                "chr7\t117559600\trs75527207\tG\tA\t99\tPASS\tGENE=CFTR;CLNSIG=Pathogenic;AF=0.0001\tGT\t1|0\n"
            )
        elif preset_name == "synthetic_lethality_tp53_brca1":
            return (
                "##fileformat=VCFv4.2\n"
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
                "chr17\t7676154\trs1042522\tC\tG\t99\tPASS\tGENE=TP53;CLNSIG=Pathogenic;AF=0.28\tGT\t0/1\n"
                "chr17\t43044295\trs80357906\tC\tT\t99\tPASS\tGENE=BRCA1;CLNSIG=Pathogenic;AF=0.00005\tGT\t0/1\n"
            )
        else: # complete 5-gene panel
            return (
                "##fileformat=VCFv4.2\n"
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
                "chr17\t43044295\trs80357906\tC\tT\t99\tPASS\tGENE=BRCA1;CLNSIG=Pathogenic\tGT\t0/1\n"
                "chr11\t5227002\trs334\tA\tT\t99\tPASS\tGENE=HBB;CLNSIG=Pathogenic\tGT\t0/1\n"
                "chr7\t117559590\trs121908752\tCTT\t.\t99\tPASS\tGENE=CFTR;CLNSIG=Pathogenic\tGT\t0/1\n"
                "chr15\t72346580\trs387906309\t.\tTATC\t99\tPASS\tGENE=HEXA;CLNSIG=Pathogenic\tGT\t0/1\n"
                "chrX\t31165000\trs121913527\tA\tC\t99\tPASS\tGENE=DMD;CLNSIG=Pathogenic\tGT\t0/1\n"
            )

