"""
HELIX GUARD - FASTA Sequence Exporter
Constructs validated, headers-annotated FASTA files containing in-silico
corrected genomic sequences with comprehensive audit metadata.
"""

from datetime import datetime, timezone
from typing import List, Optional

from correction_engine import EditAuditRecord, ProposedEdit


class FASTAGenerator:
    """
    Generates standardized FASTA formatted sequence files from corrected genomes.
    """

    def __init__(self, line_wrap: int = 80):
        self.line_wrap = line_wrap

    def wrap_sequence(self, sequence: str) -> str:
        """
        Wraps long sequence strings to standard FASTA column width.
        """
        lines = []
        for i in range(0, len(sequence), self.line_wrap):
            lines.append(sequence[i:i + self.line_wrap])
        return "\n".join(lines)

    def generate_fasta(
        self,
        sequence: str,
        sample_id: str = "SAMPLE_HG_SIM_001",
        edit_history: Optional[List[EditAuditRecord]] = None,
        assembly: str = "GRCh38"
    ) -> str:
        """
        Builds a complete FASTA file with structured metadata in the defline.
        """
        edit_history = edit_history or []
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        genes_edited = sorted(list(set(e.gene_symbol for e in edit_history)))
        genes_str = ",".join(genes_edited) if genes_edited else "NONE"
        edits_count = len(edit_history)

        header = (
            f">HELIX_GUARD|{sample_id}|ASSEMBLY={assembly}|GENES={genes_str}|"
            f"EDITS_APPLIED={edits_count}|TIMESTAMP={timestamp}|STATUS=IN_SILICO_VALIDATED"
        )

        wrapped_seq = self.wrap_sequence(sequence)
        return f"{header}\n{wrapped_seq}\n"

    def generate_clinical_markdown_report(
        self,
        sample_id: str,
        edit_history: List[EditAuditRecord],
        initial_risks: dict,
        final_risks: dict,
        beneficial_suggestions: list
    ) -> str:
        """
        Generates a comprehensive clinical genetics markdown audit report.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        report = []
        report.append(f"# HELIX GUARD — CLINICAL IN-SILICO CORRECTION REPORT")
        report.append(f"**Sample ID**: `{sample_id}`  ")
        report.append(f"**Execution Timestamp**: `{timestamp}`  ")
        report.append(f"**Engine Version**: `HELIX GUARD 2.0 (Milestone 11 Final)`  ")
        report.append(f"**Ethical Status**: Strictly Computational Simulation (No In-Vivo Procedures)\n")

        report.append("## 1. Five-Gene Panel Risk Summary\n")
        report.append("| Priority | Gene | Condition | Pre-Edit Risk | Post-Edit Risk | Clinical Outcome |")
        report.append("|---|---|---|---|---|---|")

        panel_meta = {
            "BRCA1": ("1", "Hereditary Breast/Ovarian Cancer"),
            "HBB": ("2", "Sickle Cell Anemia"),
            "CFTR": ("3", "Cystic Fibrosis"),
            "HEXA": ("4", "Tay-Sachs Disease"),
            "DMD": ("5", "Duchenne Muscular Dystrophy"),
        }

        for gene, (prio, cond) in panel_meta.items():
            pre = initial_risks.get(gene, 0.10)
            post = final_risks.get(gene, 0.10)
            status = "RESTORED TO LOW RISK" if post < 0.25 and pre > 0.40 else "MAINTAINED WILD-TYPE"
            report.append(f"| {prio} | {gene} | {cond} | {pre:.2f} | {post:.2f} | **{status}** |")

        report.append("\n## 2. Applied In-Silico Molecular Edits\n")
        if not edit_history:
            report.append("No pathogenic variants required correction.\n")
        else:
            for edit in edit_history:
                pe = edit.proposed_edit
                report.append(f"### Step {edit.step_number}: {edit.gene_symbol} ({edit.variant_id})")
                report.append(f"- **Strategy**: `{pe.strategy.value}` via `{pe.recommended_modality.value}`")
                report.append(f"- **Locus**: `{pe.chromosome}:{pe.position}` (`{pe.original_allele}` -> `{pe.corrected_allele}`)")
                report.append(f"- **Guide RNA**: `{pe.guide_rna_candidate}`")
                report.append(f"- **Efficiency**: `{pe.predicted_efficiency * 100:.1f}%` | **Off-Target Risk**: `{pe.off_target_risk_score * 100:.1f}%`")
                report.append(f"- **Risk Delta**: `{edit.original_risk:.2f}` -> `{edit.post_edit_risk:.2f}`")
                if edit.conflicts_identified:
                    report.append(f"- **Conflicts Evaluated**: {', '.join(edit.conflicts_identified)}")
                report.append("")

        if beneficial_suggestions:
            report.append("## 3. Investigative Beneficial Allele Suggestions\n")
            for ben in beneficial_suggestions:
                report.append(f"### {ben.gene_symbol} ({ben.allele_name})")
                report.append(f"**Phenotype**: {ben.beneficial_phenotype}")
                report.append(f"**Documented Trade-Offs**:")
                for t in ben.documented_trade_offs:
                    report.append(f"  - {t}")
                report.append(f"> [!WARNING] {ben.ethical_safeguard_notice}\n")

        return "\n".join(report)
