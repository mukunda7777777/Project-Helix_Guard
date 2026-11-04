"""
HELIX GUARD - Epistasis & Multi-Variant Conflict Engine
Models compound heterozygosity, cis/trans phasing, and non-additive
epistatic interactions across multi-variant clinical genotypes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class GenotypePhase(str, Enum):
    """Genotype phase configuration between two variant loci."""
    CIS = "CIS"              # Both variants on the same chromosome allele (monoallelic)
    TRANS = "TRANS"          # Variants on opposite homologous chromosomes (biallelic)
    UNKNOWN = "UNKNOWN"      # Phase unphased / unconfirmed


class InheritanceMode(str, Enum):
    """Mendelian and complex inheritance patterns."""
    AUTOSOMAL_RECESSIVE = "AUTOSOMAL_RECESSIVE"
    AUTOSOMAL_DOMINANT = "AUTOSOMAL_DOMINANT"
    X_LINKED_RECESSIVE = "X_LINKED_RECESSIVE"
    COMPLEX_MODIFIER = "COMPLEX_MODIFIER"


@dataclass
class VariantLocus:
    """Genomic locus and clinical annotation for a single variant."""
    variant_id: str                      # rsID or HGVS (e.g. 'rs121908752')
    gene_symbol: str                     # Gene symbol (e.g. 'CFTR')
    chromosome: str                      # Chromosome ('chr7')
    position: int                        # 1-based genomic position
    ref_allele: str                      # Reference allele
    alt_allele: str                      # Alternate allele
    pathogenicity: str                   # 'Pathogenic', 'Likely Pathogenic', 'VUS', 'Benign'
    allele_frequency: Optional[float] = None
    zygosity: str = "HETEROZYGOUS"       # 'HETEROZYGOUS' or 'HOMOZYGOUS'


@dataclass
class CompoundHeterozygoteResult:
    """Clinical evaluation of compound heterozygosity at a single gene locus."""
    gene_symbol: str
    is_compound_heterozygous: bool
    phase: GenotypePhase
    variants_involved: List[str]
    inheritance_mode: InheritanceMode
    clinical_risk: str                   # 'HIGH_RECESSIVE_RISK', 'CARRIER_ONLY', 'BENIGN_EFFECT'
    explanation: str


@dataclass
class EpistaticInteraction:
    """Epistatic or modifier relationship between variants in separate loci."""
    variant_a: str
    gene_a: str
    variant_b: str
    gene_b: str
    interaction_type: str               # 'SYNTHETIC_LETHALITY', 'MODIFIER_SEVERITY', 'PROTECTIVE_BUFFER'
    severity_delta: float               # Pathogenicity delta (-1.0 to +1.0)
    biological_rationale: str


@dataclass
class MultiVariantConflictReport:
    """Comprehensive conflict and interaction analysis across a variant set."""
    evaluated_variants: List[VariantLocus]
    compound_heterozygotes: List[CompoundHeterozygoteResult]
    epistatic_interactions: List[EpistaticInteraction]
    conflicts_identified: List[str]
    aggregate_disease_risks: Dict[str, float]
    clinical_warnings: List[str]


# Curated inheritance models for canonical gene panel
GENE_INHERITANCE_MODELS: Dict[str, InheritanceMode] = {
    "CFTR": InheritanceMode.AUTOSOMAL_RECESSIVE,
    "HEXA": InheritanceMode.AUTOSOMAL_RECESSIVE,
    "HBB": InheritanceMode.AUTOSOMAL_RECESSIVE,
    "BRCA1": InheritanceMode.AUTOSOMAL_DOMINANT,
    "TP53": InheritanceMode.AUTOSOMAL_DOMINANT,
    "DMD": InheritanceMode.X_LINKED_RECESSIVE,
}

# Known biochemical pathway interactions and modifiers
KNOWN_EPISTATIC_RULES: List[Dict] = [
    {
        "genes": ("TP53", "BRCA1"),
        "interaction_type": "SYNTHETIC_LETHALITY",
        "severity_delta": 0.35,
        "rationale": "Concurrent loss of TP53 checkpoint and BRCA1 homologous recombination repair dramatically accelerates genomic instability."
    },
    {
        "genes": ("HBB", "BCL11A"),
        "interaction_type": "PROTECTIVE_BUFFER",
        "severity_delta": -0.40,
        "rationale": "BCL11A downregulation or modifier variants sustain fetal hemoglobin (HbF) expression, significantly alleviating sickle cell severity."
    },
    {
        "genes": ("CFTR", "SLC26A9"),
        "interaction_type": "MODIFIER_SEVERITY",
        "severity_delta": 0.20,
        "rationale": "SLC26A9 chloride/bicarbonate transporter polymorphisms modulate meconium ileus and pulmonary function decline in CFTR F508del carriers."
    }
]


class EpistasisEngine:
    """
    Evaluates multi-variant interactions, phasing relationships, and
    phenotypic modifications across human genomic loci.
    """

    def __init__(self):
        self.gene_inheritance = dict(GENE_INHERITANCE_MODELS)
        self.epistatic_rules = list(KNOWN_EPISTATIC_RULES)

    def evaluate_phasing(
        self,
        variant_a: VariantLocus,
        variant_b: VariantLocus,
        explicit_phase: Optional[GenotypePhase] = None
    ) -> GenotypePhase:
        """
        Determines the phasing relationship between two variants on the same chromosome.
        If explicit phase is provided, validates and returns it.
        Otherwise, infers based on proximity and homozygosity.
        """
        if variant_a.chromosome != variant_b.chromosome:
            return GenotypePhase.UNKNOWN

        if explicit_phase in [GenotypePhase.CIS, GenotypePhase.TRANS]:
            return explicit_phase

        # If either variant is homozygous, both alleles are affected (effective TRANS coverage)
        if variant_a.zygosity == "HOMOZYGOUS" or variant_b.zygosity == "HOMOZYGOUS":
            return GenotypePhase.TRANS

        # Unphased short-read data without parental trio or read overlap cannot definitively phase
        # Distance heuristic: variants within ~300bp might be phased by single paired-end read,
        # but without BAM reads we must conservatively flag as UNKNOWN
        return GenotypePhase.UNKNOWN

    def detect_compound_heterozygosity(
        self,
        variants: List[VariantLocus],
        phase_map: Optional[Dict[Tuple[str, str], GenotypePhase]] = None
    ) -> List[CompoundHeterozygoteResult]:
        """
        Scans a list of variants to detect compound heterozygosity in recessive genes.
        """
        phase_map = phase_map or {}
        results: List[CompoundHeterozygoteResult] = []

        # Group variants by gene
        gene_groups: Dict[str, List[VariantLocus]] = {}
        for var in variants:
            gene_groups.setdefault(var.gene_symbol.upper(), []).append(var)

        for gene, var_list in gene_groups.items():
            inheritance = self.gene_inheritance.get(gene, InheritanceMode.AUTOSOMAL_DOMINANT)

            # Filter for damaging/uncertain variants
            pathogenic_vars = [
                v for v in var_list
                if any(term in v.pathogenicity.lower() for term in ["pathogenic", "vus", "uncertain"])
            ]

            # Compound heterozygosity requires at least 2 distinct variant loci in the same gene
            if len(pathogenic_vars) < 2:
                continue

            # Evaluate pairwise phasing
            for i in range(len(pathogenic_vars)):
                for j in range(i + 1, len(pathogenic_vars)):
                    v1 = pathogenic_vars[i]
                    v2 = pathogenic_vars[j]

                    key = (v1.variant_id, v2.variant_id)
                    rev_key = (v2.variant_id, v1.variant_id)
                    phase = phase_map.get(key) or phase_map.get(rev_key) or self.evaluate_phasing(v1, v2)

                    if inheritance == InheritanceMode.AUTOSOMAL_RECESSIVE:
                        if phase == GenotypePhase.TRANS:
                            results.append(CompoundHeterozygoteResult(
                                gene_symbol=gene,
                                is_compound_heterozygous=True,
                                phase=phase,
                                variants_involved=[v1.variant_id, v2.variant_id],
                                inheritance_mode=inheritance,
                                clinical_risk="HIGH_RECESSIVE_RISK",
                                explanation=(
                                    f"Biallelic disruption confirmed in trans ({v1.variant_id} on paternal allele, "
                                    f"{v2.variant_id} on maternal allele). Recessive phenotype expected to manifest."
                                )
                            ))
                        elif phase == GenotypePhase.CIS:
                            results.append(CompoundHeterozygoteResult(
                                gene_symbol=gene,
                                is_compound_heterozygous=False,
                                phase=phase,
                                variants_involved=[v1.variant_id, v2.variant_id],
                                inheritance_mode=inheritance,
                                clinical_risk="CARRIER_ONLY",
                                explanation=(
                                    f"Variants in cis ({v1.variant_id} and {v2.variant_id} on same chromosome allele). "
                                    f"One functional wild-type allele remains; carrier status without full recessive manifestation."
                                )
                            ))
                        else:
                            results.append(CompoundHeterozygoteResult(
                                gene_symbol=gene,
                                is_compound_heterozygous=False,
                                phase=GenotypePhase.UNKNOWN,
                                variants_involved=[v1.variant_id, v2.variant_id],
                                inheritance_mode=inheritance,
                                clinical_risk="UNCONFIRMED_PHASE_RISK",
                                explanation=(
                                    f"Two pathogenic/VUS variants detected in {gene} ({v1.variant_id}, {v2.variant_id}), "
                                    f"but phase is unconfirmed. Parental trio sequencing or long-read phasing required to rule out compound heterozygosity."
                                )
                            ))

        return results

    def detect_epistatic_interactions(
        self,
        variants: List[VariantLocus]
    ) -> List[EpistaticInteraction]:
        """
        Detects inter-genic modifier and synthetic lethality relationships.
        """
        interactions: List[EpistaticInteraction] = []
        genes_present = {v.gene_symbol.upper(): v for v in variants}

        for rule in self.epistatic_rules:
            g1, g2 = rule["genes"]
            if g1 in genes_present and g2 in genes_present:
                v1 = genes_present[g1]
                v2 = genes_present[g2]

                # Only trigger if both variants are potentially functional (not benign)
                if "benign" not in v1.pathogenicity.lower() and "benign" not in v2.pathogenicity.lower():
                    interactions.append(EpistaticInteraction(
                        variant_a=v1.variant_id,
                        gene_a=g1,
                        variant_b=v2.variant_id,
                        gene_b=g2,
                        interaction_type=rule["interaction_type"],
                        severity_delta=rule["severity_delta"],
                        biological_rationale=rule["rationale"]
                    ))

        return interactions

    def analyze_multi_variant_profile(
        self,
        variants: List[VariantLocus],
        phase_map: Optional[Dict[Tuple[str, str], GenotypePhase]] = None,
        base_risks: Optional[Dict[str, float]] = None
    ) -> MultiVariantConflictReport:
        """
        Performs holistic analysis: compound heterozygosity, epistasis,
        and adjusted multi-variant risk calculation.
        """
        base_risks = base_risks or {}
        compound_results = self.detect_compound_heterozygosity(variants, phase_map)
        epistatic_results = self.detect_epistatic_interactions(variants)

        conflicts: List[str] = []
        warnings: List[str] = []
        adjusted_risks: Dict[str, float] = dict(base_risks)

        # Apply compound heterozygote adjustments
        for comp in compound_results:
            gene = comp.gene_symbol
            current_risk = adjusted_risks.get(gene, 0.5)

            if comp.clinical_risk == "HIGH_RECESSIVE_RISK":
                # Both copies defective -> high disease risk
                adjusted_risks[gene] = min(1.0, max(current_risk, 0.95))
                conflicts.append(f"Compound heterozygosity in {gene}: Biallelic damage elevates risk to {adjusted_risks[gene]:.2f}")
            elif comp.clinical_risk == "CARRIER_ONLY":
                # Single allele defective -> carrier risk remains low for recessive condition
                adjusted_risks[gene] = min(0.35, current_risk)
            else:
                warnings.append(f"Unphased variants in recessive gene {gene}. Risk estimation has high epistemic uncertainty.")

        # Apply epistatic interaction adjustments
        for epi in epistatic_results:
            g1 = epi.gene_a
            g2 = epi.gene_b

            r1 = adjusted_risks.get(g1, 0.5)
            r2 = adjusted_risks.get(g2, 0.5)

            new_r1 = min(1.0, max(0.0, r1 + epi.severity_delta))
            new_r2 = min(1.0, max(0.0, r2 + epi.severity_delta))

            adjusted_risks[g1] = round(new_r1, 3)
            adjusted_risks[g2] = round(new_r2, 3)

            conflicts.append(
                f"Epistasis ({epi.interaction_type}) between {g1} ({epi.variant_a}) and {g2} ({epi.variant_b}): "
                f"severity delta {epi.severity_delta:+.2f} applied."
            )

        return MultiVariantConflictReport(
            evaluated_variants=variants,
            compound_heterozygotes=compound_results,
            epistatic_interactions=epistatic_results,
            conflicts_identified=conflicts,
            aggregate_disease_risks=adjusted_risks,
            clinical_warnings=warnings
        )

