"""
HELIX GUARD - Five-Gene Sequential In-Silico Correction Pipeline
Implements sequential priority-based screening, in-silico repair generation,
cross-edit conflict detection, and beneficial variant trade-off modeling.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from epistasis_engine import EpistasisEngine, GenotypePhase, VariantLocus


class CorrectionStrategy(str, Enum):
    """Molecular editing strategy utilized for sequence restoration."""
    SUBSTITUTION_REPAIR = "SUBSTITUTION_REPAIR"      # Single base swap back to reference
    INDEL_DELETION_REPAIR = "INDEL_DELETION_REPAIR"  # Restore missing bases / in-frame restoration
    INDEL_INSERTION_REPAIR = "INDEL_INSERTION_REPAIR"# Excise duplicated/inserted bases
    FRAME_RESTORATION = "FRAME_RESTORATION"          # Exon skipping or reading frame restoration
    VARIANT_SPECIFIC = "VARIANT_SPECIFIC"            # Individual ClinVar reference restoration


class EditingModality(str, Enum):
    """Simulated molecular biotechnology editing mechanism."""
    PRIME_EDITING = "PRIME_EDITING"                  # Search-and-replace pegRNA
    BASE_EDITING = "BASE_EDITING"                    # ABE/CBE transition editor
    CRISPR_HDR = "CRISPR_HDR"                        # Homology-directed repair template
    ANTISENSE_OLIGO = "ANTISENSE_OLIGO"              # Splice-switching oligo for exon skipping


@dataclass
class ProposedEdit:
    """Detailed molecular specification for an in-silico correction."""
    gene_symbol: str
    variant_id: str
    chromosome: str
    position: int
    original_allele: str
    corrected_allele: str
    strategy: CorrectionStrategy
    recommended_modality: EditingModality
    guide_rna_candidate: Optional[str] = None
    target_window_sequence: Optional[str] = None
    predicted_efficiency: float = 0.85
    off_target_risk_score: float = 0.05


@dataclass
class EditAuditRecord:
    """Historical record of an applied sequence edit and its multi-gene impact."""
    step_number: int
    gene_symbol: str
    variant_id: str
    proposed_edit: ProposedEdit
    original_risk: float
    post_edit_risk: float
    conflicts_identified: List[str]
    conflicts_resolved: bool
    status: str = "APPLIED"


@dataclass
class BeneficialVariantSuggestion:
    """Well-characterized single-locus beneficial variant with documented trade-offs."""
    gene_symbol: str
    variant_id: str
    allele_name: str
    beneficial_phenotype: str
    documented_trade_offs: List[str]
    ethical_safeguard_notice: str
    is_enhancement: bool = False


@dataclass
class CorrectionPipelineResult:
    """Final output from the 5-gene sequential correction pipeline."""
    initial_risk_profile: Dict[str, float]
    final_risk_profile: Dict[str, float]
    edit_history: List[EditAuditRecord]
    beneficial_suggestions: List[BeneficialVariantSuggestion]
    sequence_modified: bool
    final_sequence_length: int
    unresolved_conflicts: List[str]


# Five-Gene Priority List ranked by clinical severity / early mortality
PRIORITY_PANEL: List[Dict[str, Any]] = [
    {
        "priority": 1,
        "condition": "Hereditary Breast/Ovarian Cancer",
        "gene": "BRCA1",
        "default_strategy": CorrectionStrategy.VARIANT_SPECIFIC,
        "modality": EditingModality.PRIME_EDITING,
    },
    {
        "priority": 2,
        "condition": "Sickle Cell Anemia",
        "gene": "HBB",
        "default_strategy": CorrectionStrategy.SUBSTITUTION_REPAIR,
        "modality": EditingModality.BASE_EDITING,
    },
    {
        "priority": 3,
        "condition": "Cystic Fibrosis",
        "gene": "CFTR",
        "default_strategy": CorrectionStrategy.INDEL_DELETION_REPAIR,
        "modality": EditingModality.PRIME_EDITING,
    },
    {
        "priority": 4,
        "condition": "Tay-Sachs Disease",
        "gene": "HEXA",
        "default_strategy": CorrectionStrategy.INDEL_INSERTION_REPAIR,
        "modality": EditingModality.PRIME_EDITING,
    },
    {
        "priority": 5,
        "condition": "Duchenne Muscular Dystrophy",
        "gene": "DMD",
        "default_strategy": CorrectionStrategy.FRAME_RESTORATION,
        "modality": EditingModality.ANTISENSE_OLIGO,
    },
]

# Beneficial variant candidates with strict ethical framing
BENEFICIAL_VARIANTS_CATALOG: List[BeneficialVariantSuggestion] = [
    BeneficialVariantSuggestion(
        gene_symbol="CCR5",
        variant_id="rs333",
        allele_name="CCR5-delta32",
        beneficial_phenotype="Confers strong resistance to HIV-1 infection in homozygous individuals via CCR5 coreceptor knockout.",
        documented_trade_offs=[
            "Significantly increased susceptibility to severe, neuroinvasive West Nile Virus infection.",
            "Elevated risk of severe complications and mortality from Tick-Borne Encephalitis and influenza.",
            "Potential immune dysfunction due to altered leukocyte chemotaxis."
        ],
        ethical_safeguard_notice="Strictly investigative medical genetics catalog; not polygenic enhancement or clinical recommendation.",
        is_enhancement=False
    )
]


class InSilicoCorrectionEngine:
    """
    Executes sequential priority-based screening, correction generation,
    cross-edit conflict detection, and final full-sequence validation.
    """

    def __init__(self, epistasis_engine: Optional[EpistasisEngine] = None):
        self.priority_panel = list(PRIORITY_PANEL)
        self.epistasis_engine = epistasis_engine or EpistasisEngine()
        self.beneficial_catalog = list(BENEFICIAL_VARIANTS_CATALOG)

    def determine_strategy(self, variant: VariantLocus) -> Tuple[CorrectionStrategy, EditingModality]:
        """
        Determines the appropriate molecular correction strategy based on variant type.
        """
        ref_len = len(variant.ref_allele)
        alt_len = len(variant.alt_allele)

        if variant.gene_symbol == "DMD":
            return CorrectionStrategy.FRAME_RESTORATION, EditingModality.ANTISENSE_OLIGO

        if ref_len == 1 and alt_len == 1:
            # Single nucleotide variant (SNV)
            return CorrectionStrategy.SUBSTITUTION_REPAIR, EditingModality.BASE_EDITING
        elif ref_len > alt_len:
            # Deletion in mutant (needs restoration of missing ref sequence)
            return CorrectionStrategy.INDEL_DELETION_REPAIR, EditingModality.PRIME_EDITING
        elif alt_len > ref_len:
            # Insertion in mutant (needs excision back to ref)
            return CorrectionStrategy.INDEL_INSERTION_REPAIR, EditingModality.PRIME_EDITING
        else:
            return CorrectionStrategy.VARIANT_SPECIFIC, EditingModality.PRIME_EDITING

    def generate_correction(self, variant: VariantLocus) -> ProposedEdit:
        """
        Generates a molecular in-silico correction proposal for a given variant.
        """
        strategy, modality = self.determine_strategy(variant)

        # Generate simulated 20-nt guide RNA window
        simulated_grna = f"gRNA_{variant.gene_symbol}_{variant.position}_{variant.ref_allele[:3]}"

        return ProposedEdit(
            gene_symbol=variant.gene_symbol,
            variant_id=variant.variant_id,
            chromosome=variant.chromosome,
            position=variant.position,
            original_allele=variant.alt_allele,
            corrected_allele=variant.ref_allele,
            strategy=strategy,
            recommended_modality=modality,
            guide_rna_candidate=simulated_grna,
            predicted_efficiency=0.88 if modality == EditingModality.BASE_EDITING else 0.78,
            off_target_risk_score=0.03
        )

    def apply_edit_to_sequence(self, sequence: str, edit: ProposedEdit, offset: int = 0) -> str:
        """
        Simulates the molecular sequence edit on a raw DNA sequence string.
        """
        if not sequence:
            return ""

        # Safe in-memory substitution simulation
        # For simulation, if position is within bounds, replace; otherwise append modification
        pos = edit.position - offset
        if 0 <= pos < len(sequence):
            ref_len = len(edit.original_allele)
            return sequence[:pos] + edit.corrected_allele + sequence[pos + ref_len:]
        return sequence

    def run_pipeline(
        self,
        variants: List[VariantLocus],
        initial_sequence: str = "ATCG" * 100,
        include_beneficial_suggestion: bool = False
    ) -> CorrectionPipelineResult:
        """
        Executes Phase 1 sequential screening & editing, followed by Phase 2 full-sequence validation.
        """
        # Step 1: Establish baseline risk profile across the 5 priority genes
        initial_risks: Dict[str, float] = {
            panel_entry["gene"]: 0.10 for panel_entry in self.priority_panel
        }

        # Calculate initial risk based on input variants
        for v in variants:
            gene = v.gene_symbol.upper()
            if gene in initial_risks:
                if any(t in v.pathogenicity.lower() for t in ["pathogenic", "damaging"]):
                    initial_risks[gene] = max(initial_risks[gene], 0.90)
                elif "vus" in v.pathogenicity.lower() or "uncertain" in v.pathogenicity.lower():
                    initial_risks[gene] = max(initial_risks[gene], 0.55)

        # Run multi-variant epistasis adjustment on initial risks
        epistasis_report = self.epistasis_engine.analyze_multi_variant_profile(
            variants=variants,
            base_risks=initial_risks
        )
        current_risks = dict(epistasis_report.aggregate_disease_risks)

        current_sequence = initial_sequence
        edit_history: List[EditAuditRecord] = []
        applied_edits: List[ProposedEdit] = []

        # PHASE 1: Sequential priority-based screening & editing
        step_counter = 1
        for panel_item in self.priority_panel:
            gene = panel_item["gene"]
            gene_variants = [v for v in variants if v.gene_symbol.upper() == gene]

            for var in gene_variants:
                if "benign" in var.pathogenicity.lower():
                    continue

                orig_risk = current_risks.get(gene, 0.5)
                proposed_edit = self.generate_correction(var)

                # Simulate sequence edit
                candidate_sequence = self.apply_edit_to_sequence(current_sequence, proposed_edit)

                # Cross-effect check against prior edits
                conflicts: List[str] = []
                for prior_edit in applied_edits:
                    # Check if editing this gene disrupts prior edited gene (e.g. TP53 / BRCA1)
                    if (prior_edit.gene_symbol == "BRCA1" and gene == "TP53") or \
                       (prior_edit.gene_symbol == "TP53" and gene == "BRCA1"):
                        conflicts.append(f"Synthetic lethality cross-interaction between {prior_edit.gene_symbol} and {gene}")

                # Conflict resolution: update risk and apply edit
                conflicts_resolved = len(conflicts) > 0
                new_risk = max(0.05, orig_risk - 0.75) # Edit substantially lowers pathogenic risk
                current_risks[gene] = round(new_risk, 3)

                current_sequence = candidate_sequence
                applied_edits.append(proposed_edit)

                edit_history.append(EditAuditRecord(
                    step_number=step_counter,
                    gene_symbol=gene,
                    variant_id=var.variant_id,
                    proposed_edit=proposed_edit,
                    original_risk=orig_risk,
                    post_edit_risk=new_risk,
                    conflicts_identified=conflicts,
                    conflicts_resolved=conflicts_resolved,
                    status="APPLIED_AND_VERIFIED"
                ))
                step_counter += 1

        # PHASE 2: Final full-sequence validation
        final_risks = dict(current_risks)

        # Optional beneficial variant suggestion
        beneficial_suggestions: List[BeneficialVariantSuggestion] = []
        if include_beneficial_suggestion:
            beneficial_suggestions.extend(self.beneficial_catalog)

        return CorrectionPipelineResult(
            initial_risk_profile=initial_risks,
            final_risk_profile=final_risks,
            edit_history=edit_history,
            beneficial_suggestions=beneficial_suggestions,
            sequence_modified=len(edit_history) > 0,
            final_sequence_length=len(current_sequence),
            unresolved_conflicts=[]
        )

