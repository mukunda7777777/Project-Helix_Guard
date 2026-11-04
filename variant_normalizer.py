"""
Variant Normalizer and Assembly Isolation Engine
"""

import re
from typing import Any, Dict, Optional, Tuple

from evidence_engine import GenomeAssembly, VariantIdentity
from variant_benchmarks import VARIANT_BENCHMARK_CURATIONS, _lookup_benchmark_entry

class VariantNormalizer:
    """
    Normalizes variant identifiers across dbSNP rsID, ClinVar Variation ID,
    HGVS genomic notation, and chromosome:position:ref:alt coordinates.
    Enforces strict assembly discipline (GRCh38 vs GRCh37) and rejects silent conversion.
    """

    REFSEQ_GRCH38 = {
        f"NC_0000{i:02d}.11": str(i) for i in range(1, 23)
    }
    REFSEQ_GRCH38["NC_000023.11"] = "X"
    REFSEQ_GRCH38["NC_000024.10"] = "Y"

    REFSEQ_GRCH37 = {
        f"NC_0000{i:02d}.10": str(i) for i in range(1, 23)
    }
    REFSEQ_GRCH37["NC_000023.10"] = "X"
    REFSEQ_GRCH37["NC_000024.9"] = "Y"

    @classmethod
    def clean_chromosome(cls, chrom: str) -> str:
        c = chrom.strip().upper()
        if c.startswith("CHR"):
            c = c[3:]
        if c == "M":
            c = "MT"
        return c

    @classmethod
    def normalize(
        cls,
        identifier: str,
        assembly: GenomeAssembly = GenomeAssembly.GRCh38,
        gene_symbol: Optional[str] = None,
        reference_allele: Optional[str] = None,
        alternate_allele: Optional[str] = None,
    ) -> VariantIdentity:
        """
        Normalizes variant input into a strongly-typed VariantIdentity contract.
        Validates assembly bounds, detects ambiguities, and forbids silent conversion.
        """
        if not identifier or not identifier.strip():
            return VariantIdentity(
                variant_id="EMPTY",
                chromosome="Unknown",
                position=0,
                reference_allele="N",
                alternate_allele="N",
                assembly=assembly,
                input_identifier=identifier or "",
                is_valid=False,
                validation_error="Variant identifier cannot be empty",
            )

        clean_id = identifier.strip()
        lower_id = clean_id.lower()

        # 1. HGVS Genomic Notation with explicit RefSeq accession (e.g. NC_000017.11:g.43044295dup or NC_000017.10:g.41196312dup)
        hgvs_match = re.search(r"^(NC_\d+\.\d+):g\.(\d+)([A-Za-z0-9_>deldupins]+)$", clean_id, re.I)
        if hgvs_match:
            accession, pos_str, mut_str = hgvs_match.group(1), hgvs_match.group(2), hgvs_match.group(3)
            pos = int(pos_str)
            acc_upper = accession.upper()

            acc_assembly = None
            acc_chrom = None
            if acc_upper in cls.REFSEQ_GRCH38:
                acc_assembly = GenomeAssembly.GRCh38
                acc_chrom = cls.REFSEQ_GRCH38[acc_upper]
            elif acc_upper in cls.REFSEQ_GRCH37:
                acc_assembly = GenomeAssembly.GRCh37
                acc_chrom = cls.REFSEQ_GRCH37[acc_upper]

            if acc_assembly and acc_assembly != assembly:
                err_msg = (
                    f"RefSeq accession assembly mismatch: accession '{accession}' corresponds to {acc_assembly.value}, "
                    f"but requested target assembly is {assembly.value}. Silent coordinate conversion is strictly prohibited."
                )
                return VariantIdentity(
                    variant_id=clean_id,
                    chromosome=acc_chrom or "Unknown",
                    position=pos,
                    reference_allele="N",
                    alternate_allele="N",
                    assembly=assembly,
                    gene_symbol=gene_symbol,
                    input_identifier=clean_id,
                    normalized_identifier=clean_id,
                    associated_gene=gene_symbol,
                    normalization_source="HGVS Genomic Parser",
                    is_ambiguous=True,
                    ambiguity_reason=err_msg,
                    is_valid=False,
                    validation_error=err_msg,
                )

            # Check SNV pattern
            snv_match = re.match(r"^([A-Za-z])>([A-Za-z])$", mut_str)
            if snv_match:
                ref_a = snv_match.group(1).upper()
                alt_a = snv_match.group(2).upper()
                if ref_a == alt_a:
                    return VariantIdentity(
                        variant_id=clean_id,
                        chromosome=acc_chrom or "Unknown",
                        position=pos,
                        reference_allele=ref_a,
                        alternate_allele=alt_a,
                        assembly=assembly,
                        input_identifier=clean_id,
                        is_valid=False,
                        validation_error="Reference allele cannot be identical to alternate allele",
                    )
                norm_id = f"{acc_chrom}-{pos}-{ref_a}-{alt_a}"
                return VariantIdentity(
                    variant_id=clean_id,
                    chromosome=acc_chrom or "Unknown",
                    position=pos,
                    reference_allele=ref_a,
                    alternate_allele=alt_a,
                    assembly=assembly,
                    gene_symbol=gene_symbol,
                    input_identifier=clean_id,
                    normalized_identifier=norm_id,
                    associated_gene=gene_symbol,
                    normalization_source="HGVS Genomic Parser",
                    is_ambiguous=False,
                    is_valid=True,
                )
            else:
                ref_a = "REF"
                alt_a = mut_str.upper()
                norm_id = f"{acc_chrom}-{pos}-{ref_a}-{alt_a}"
                return VariantIdentity(
                    variant_id=clean_id,
                    chromosome=acc_chrom or "Unknown",
                    position=pos,
                    reference_allele=ref_a,
                    alternate_allele=alt_a,
                    assembly=assembly,
                    gene_symbol=gene_symbol,
                    input_identifier=clean_id,
                    normalized_identifier=norm_id,
                    associated_gene=gene_symbol,
                    normalization_source="HGVS Genomic Parser",
                    is_ambiguous=False,
                    is_valid=True,
                )

        # 2. Curated benchmark reference lookup
        benchmark = _lookup_benchmark_entry(clean_id)
        if benchmark:
            asm_key = assembly.value
            coords = benchmark["assemblies"].get(asm_key)
            if coords:
                norm_id = f"{coords['chromosome']}-{coords['position']}-{coords['reference_allele']}-{coords['alternate_allele']}"
                prov = EvidenceProvenance(
                    source_name="Curated Reference Snapshot",
                    source_endpoint="Local Benchmark Variant Catalog",
                    retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                    source_url=f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{benchmark.get('variation_id', '')}/",
                    is_cached=False,
                    is_local_reference=True,
                    assembly=assembly,
                    license_notice="Helix Guard Verified Benchmark Catalog (Local Reference Snapshot)",
                )
                return VariantIdentity(
                    variant_id=benchmark["rsid"],
                    chromosome=coords["chromosome"],
                    position=coords["position"],
                    reference_allele=coords["reference_allele"],
                    alternate_allele=coords["alternate_allele"],
                    assembly=assembly,
                    gene_symbol=benchmark.get("gene_symbol"),
                    input_identifier=clean_id,
                    normalized_identifier=norm_id,
                    associated_gene=benchmark.get("gene_symbol"),
                    normalization_source="Curated Benchmark Reference Snapshot",
                    is_ambiguous=False,
                    is_valid=True,
                    is_local_reference=True,
                    provenance=prov,
                )

        # 3. Coordinate Patterns (e.g. chr17:43044295:C:T, 17-43044295-C-T, chr17:43044295 C>T, chr17:43044295)
        coord_pattern = r"^(?:chr)?([0-9]{1,2}|[XYxy]|MT|mt)[:\-_ ](-?[0-9]+)(?:[:\-_ ]([A-Za-z\-]+)[:\-_ >/]([A-Za-z\-]+))?$"
        coord_match = re.match(coord_pattern, clean_id)
        if coord_match:
            raw_chrom = coord_match.group(1)
            raw_pos = coord_match.group(2)
            raw_ref = coord_match.group(3) or reference_allele
            raw_alt = coord_match.group(4) or alternate_allele

            chrom = cls.clean_chromosome(raw_chrom)
            pos = int(raw_pos)

            if pos <= 0:
                return VariantIdentity(
                    variant_id=clean_id,
                    chromosome=chrom,
                    position=pos,
                    reference_allele="N",
                    alternate_allele="N",
                    assembly=assembly,
                    input_identifier=clean_id,
                    is_valid=False,
                    validation_error="Genomic position must be a positive integer",
                )

            if raw_ref and raw_alt:
                ref_clean = raw_ref.strip().upper()
                alt_clean = raw_alt.strip().upper()
                if ref_clean == alt_clean:
                    return VariantIdentity(
                        variant_id=clean_id,
                        chromosome=chrom,
                        position=pos,
                        reference_allele=ref_clean,
                        alternate_allele=alt_clean,
                        assembly=assembly,
                        input_identifier=clean_id,
                        is_valid=False,
                        validation_error="Reference allele cannot be identical to alternate allele",
                    )
                norm_id = f"{chrom}-{pos}-{ref_clean}-{alt_clean}"
                return VariantIdentity(
                    variant_id=norm_id,
                    chromosome=chrom,
                    position=pos,
                    reference_allele=ref_clean,
                    alternate_allele=alt_clean,
                    assembly=assembly,
                    gene_symbol=gene_symbol,
                    input_identifier=clean_id,
                    normalized_identifier=norm_id,
                    associated_gene=gene_symbol,
                    normalization_source="Genomic Coordinate Parser",
                    is_ambiguous=False,
                    is_valid=True,
                )
            else:
                norm_id = f"{chrom}-{pos}-N-N"
                return VariantIdentity(
                    variant_id=norm_id,
                    chromosome=chrom,
                    position=pos,
                    reference_allele="N",
                    alternate_allele="N",
                    assembly=assembly,
                    gene_symbol=gene_symbol,
                    input_identifier=clean_id,
                    normalized_identifier=norm_id,
                    associated_gene=gene_symbol,
                    normalization_source="Genomic Coordinate Parser",
                    is_ambiguous=True,
                    ambiguity_reason="Missing reference or alternate allele for precise variant definition",
                    is_valid=True,
                )

        # 4. dbSNP rsID (unresolved externally)
        if re.match(r"^rs\d+$", lower_id):
            return VariantIdentity(
                variant_id=lower_id,
                chromosome="Unknown",
                position=0,
                reference_allele="N",
                alternate_allele="N",
                assembly=assembly,
                gene_symbol=gene_symbol,
                input_identifier=clean_id,
                normalized_identifier=lower_id,
                associated_gene=gene_symbol,
                normalization_source="dbSNP rsID Resolver",
                is_ambiguous=True,
                ambiguity_reason="Unresolved rsID requires external lookup for genomic coordinates",
                is_valid=True,
            )

        # 5. ClinVar Variation ID (unresolved externally)
        if re.match(r"^(?:VCV|RCV)?\d+$", clean_id, re.I) or lower_id.startswith("clinvar:"):
            return VariantIdentity(
                variant_id=clean_id,
                chromosome="Unknown",
                position=0,
                reference_allele="N",
                alternate_allele="N",
                assembly=assembly,
                gene_symbol=gene_symbol,
                input_identifier=clean_id,
                normalized_identifier=clean_id,
                associated_gene=gene_symbol,
                normalization_source="ClinVar Variation ID Parser",
                is_ambiguous=True,
                ambiguity_reason="ClinVar ID requires external query to resolve genomic coordinates",
                is_valid=True,
            )

        # 6. Fallback for unrecognized format
        return VariantIdentity(
            variant_id=clean_id,
            chromosome="Unknown",
            position=0,
            reference_allele="N",
            alternate_allele="N",
            assembly=assembly,
            input_identifier=clean_id,
            normalized_identifier=clean_id,
            is_valid=False,
            validation_error=f"Unrecognized variant identifier format: '{clean_id}'",
        )
