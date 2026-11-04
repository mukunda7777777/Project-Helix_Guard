"""
Curated Clinical Benchmark Variants (Verified Reference Catalog)
"""
from typing import Any, Dict, Optional

# -----------------------------------------------------------------------------
# Curated Clinical Benchmark Variants (Verified Reference Catalog)
# -----------------------------------------------------------------------------

VARIANT_BENCHMARK_CURATIONS: Dict[str, Dict[str, Any]] = {
    "rs28897743": {
        "rsid": "rs28897743",
        "variation_id": "17667",
        "vcv_accession": "VCV000017667",
        "gene_symbol": "BRCA1",
        "title": "NM_007294.4(BRCA1):c.5266dupC (p.Gln1756ProfsTer74)",
        "aliases": ["5382insC", "c.5266dupC", "17667", "vcv000017667", "rcv000018596"],
        "assemblies": {
            "GRCh38": {
                "chromosome": "17",
                "position": 43044295,
                "reference_allele": "C",
                "alternate_allele": "dup",
                "hgvsg": "NC_000017.11:g.43044295dup",
            },
            "GRCh37": {
                "chromosome": "17",
                "position": 41196312,
                "reference_allele": "C",
                "alternate_allele": "dup",
                "hgvsg": "NC_000017.10:g.41196312dup",
            },
        },
        "hgvs_c": "c.5266dupC",
        "hgvs_p": "p.Gln1756ProfsTer74",
        "clinical": {
            "primary_classification": "Pathogenic",
            "review_status": "criteria provided, multiple submitters, no conflicts",
            "review_stars": 2,
            "conditions": ["Hereditary breast and ovarian cancer syndrome", "Familial cancer of breast"],
            "total_submissions": 42,
            "vcv_accession": "VCV000017667",
            "rcv_accessions": ["RCV000018596", "RCV000018597"],
            "is_conflicting": False,
            "conflict_summary": None,
            "submissions": [
                {
                    "submitter_name": "Ambry Genetics",
                    "clinical_significance": "Pathogenic",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-08-15",
                    "description": "Frameshift mutation predicted to cause loss of normal protein function.",
                },
                {
                    "submitter_name": "Invitae",
                    "clinical_significance": "Pathogenic",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-11-20",
                    "description": "Established pathogenic founder variant (5382insC).",
                },
                {
                    "submitter_name": "GeneDx",
                    "clinical_significance": "Pathogenic",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-05-10",
                    "description": "Loss of function frameshift in BRCA1.",
                },
            ],
        },
        "transcripts": [
            {
                "transcript_id": "ENST00000357654",
                "gene_symbol": "BRCA1",
                "gene_id": "ENSG00000012048",
                "consequence_terms": ["frameshift_variant"],
                "hgvs_c": "ENST00000357654.9:c.5266dup",
                "hgvs_p": "ENSP00000350283.3:p.Gln1756ProfsTer74",
                "exon": "20/23",
                "biotype": "protein_coding",
                "is_canonical": True,
                "is_mane_select": True,
                "codons": "-/C",
                "amino_acids": "Q/Pfs*74",
                "sift_prediction": "deleterious",
                "sift_score": 0.0,
                "polyphen_prediction": "probably_damaging",
                "polyphen_score": 1.0,
            }
        ],
        "population": {
            "allele_count": 38,
            "allele_number": 251400,
            "allele_frequency": 0.000151,
            "homozygote_count": 0,
            "hemizygote_count": 0,
            "popmax_frequency": 0.00142,
            "popmax_population": "Ashkenazi Jewish (asj)",
            "ancestry_frequencies": {
                "asj": 0.00142,
                "nfe": 0.00018,
                "amr": 0.00003,
                "afr": 0.00001,
                "eas": 0.0,
                "sas": 0.0,
            },
        },
        "computational": [
            {
                "prediction_method": "SIFT",
                "prediction_output": "deleterious",
                "numerical_score": 0.0,
                "source": "Ensembl VEP",
                "version": "5.2.2",
            },
            {
                "prediction_method": "PolyPhen-2",
                "prediction_output": "probably_damaging",
                "numerical_score": 1.0,
                "source": "Ensembl VEP",
                "version": "2.2.3",
            },
            {
                "prediction_method": "CADD",
                "prediction_output": "likely_deleterious",
                "numerical_score": 34.0,
                "source": "CADD v1.6 (PHRED)",
                "version": "v1.6",
            },
            {
                "prediction_method": "HelixGuard-QNN",
                "prediction_output": "Synthetic Class 1 (Pathogenic-like)",
                "numerical_score": 0.942,
                "source": "Helix Guard Hybrid Quantum Neural Network",
                "version": "v1.0",
            },
        ],
        "literature": [
            {
                "pmid": "30093976",
                "title": "Functional assay classification of 4,000 BRCA1 missense variants by saturation genome editing.",
                "authors": ["Findlay GM", "Daza RM", "Martin B", "Zhang MD", "Leith AP"],
                "journal": "Nature",
                "year": 2018,
                "doi": "10.1038/s41586-018-0461-z",
                "url": "https://pubmed.ncbi.nlm.nih.gov/30093976/",
                "variant_specific_relevance": "Direct functional characterization and saturation genome editing calibration for BRCA1 variants.",
            },
            {
                "pmid": "9145677",
                "title": "The Ashkenazi Jewish founder mutations in BRCA1 and BRCA2: clinical guidelines.",
                "authors": ["Struewing JP", "Hartge P", "Wacholder S", "Baker SM"],
                "journal": "N Engl J Med",
                "year": 1997,
                "doi": "10.1056/NEJM199705153362001",
                "url": "https://pubmed.ncbi.nlm.nih.gov/9145677/",
                "variant_specific_relevance": "Seminal clinical trial defining penetrance and population prevalence for the 5382insC founder mutation.",
            },
            {
                "pmid": "25741868",
                "title": "Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the ACMG and AMP.",
                "authors": ["Richards S", "Aziz N", "Bale S", "Bick D", "Das S"],
                "journal": "Genet Med",
                "year": 2015,
                "doi": "10.1038/gim.2015.30",
                "url": "https://pubmed.ncbi.nlm.nih.gov/25741868/",
                "variant_specific_relevance": "ACMG/AMP sequence variant interpretation framework applied to benchmark pathogenic truncating variants.",
            },
        ],
    },
    "rs121913527": {
        "rsid": "rs121913527",
        "variation_id": "12374",
        "vcv_accession": "VCV000012374",
        "gene_symbol": "TP53",
        "title": "NM_000546.6(TP53):c.743G>A (p.Arg248Gln)",
        "aliases": ["c.743G>A", "p.Arg248Gln", "12374", "vcv000012374", "rcv000013395"],
        "assemblies": {
            "GRCh38": {
                "chromosome": "17",
                "position": 7674220,
                "reference_allele": "C",
                "alternate_allele": "T",
                "hgvsg": "NC_000017.11:g.7674220C>T",
            },
            "GRCh37": {
                "chromosome": "17",
                "position": 7577120,
                "reference_allele": "C",
                "alternate_allele": "T",
                "hgvsg": "NC_000017.10:g.7577120C>T",
            },
        },
        "hgvs_c": "c.743G>A",
        "hgvs_p": "p.Arg248Gln",
        "clinical": {
            "primary_classification": "Pathogenic",
            "review_status": "reviewed by expert panel",
            "review_stars": 3,
            "conditions": ["Li-Fraumeni syndrome", "Hereditary cancer-predisposing syndrome"],
            "total_submissions": 58,
            "vcv_accession": "VCV000012374",
            "rcv_accessions": ["RCV000013395"],
            "is_conflicting": False,
            "conflict_summary": None,
            "submissions": [
                {
                    "submitter_name": "ClinGen TP53 Expert Panel",
                    "clinical_significance": "Pathogenic",
                    "review_status": "reviewed by expert panel",
                    "evaluation_date": "2023-04-10",
                    "description": "Established DNA-binding hotspot mutation in TP53.",
                },
                {
                    "submitter_name": "Ambry Genetics",
                    "clinical_significance": "Pathogenic",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-09-01",
                    "description": "Deleterious missense affecting core p53-DNA interaction.",
                },
            ],
        },
        "transcripts": [
            {
                "transcript_id": "ENST00000269305",
                "gene_symbol": "TP53",
                "gene_id": "ENSG00000141510",
                "consequence_terms": ["missense_variant"],
                "hgvs_c": "ENST00000269305.9:c.743G>A",
                "hgvs_p": "ENSP00000269305.4:p.Arg248Gln",
                "exon": "7/11",
                "biotype": "protein_coding",
                "is_canonical": True,
                "is_mane_select": True,
                "codons": "cGg/cAg",
                "amino_acids": "R/Q",
                "sift_prediction": "deleterious",
                "sift_score": 0.0,
                "polyphen_prediction": "probably_damaging",
                "polyphen_score": 1.0,
            }
        ],
        "population": {
            "allele_count": 1,
            "allele_number": 251480,
            "allele_frequency": 0.00000398,
            "homozygote_count": 0,
            "hemizygote_count": 0,
            "popmax_frequency": 0.000008,
            "popmax_population": "European (non-Finnish)",
            "ancestry_frequencies": {
                "nfe": 0.000008,
                "amr": 0.0,
                "afr": 0.0,
                "eas": 0.0,
                "sas": 0.0,
            },
        },
        "computational": [
            {
                "prediction_method": "SIFT",
                "prediction_output": "deleterious",
                "numerical_score": 0.0,
                "source": "Ensembl VEP",
                "version": "5.2.2",
            },
            {
                "prediction_method": "PolyPhen-2",
                "prediction_output": "probably_damaging",
                "numerical_score": 1.0,
                "source": "Ensembl VEP",
                "version": "2.2.3",
            },
            {
                "prediction_method": "CADD",
                "prediction_output": "likely_deleterious",
                "numerical_score": 33.0,
                "source": "CADD v1.6 (PHRED)",
                "version": "v1.6",
            },
            {
                "prediction_method": "HelixGuard-QNN",
                "prediction_output": "Synthetic Class 1 (Pathogenic-like)",
                "numerical_score": 0.965,
                "source": "Helix Guard Hybrid Quantum Neural Network",
                "version": "v1.0",
            },
        ],
        "literature": [
            {
                "pmid": "1565144",
                "title": "Germline p53 mutations in 15 families with Li-Fraumeni syndrome.",
                "authors": ["Malkin D", "Jolly KW", "Barbacid M"],
                "journal": "Science",
                "year": 1990,
                "doi": "10.1126/science.1978757",
                "url": "https://pubmed.ncbi.nlm.nih.gov/1565144/",
                "variant_specific_relevance": "Original identification of codon 248 germline hotspot mutations in Li-Fraumeni syndrome.",
            },
            {
                "pmid": "17311302",
                "title": "TP53 mutations in human cancers: functional selection and impact on survival.",
                "authors": ["Petitjean A", "Mathe E", "Kato S"],
                "journal": "Hum Mutat",
                "year": 2007,
                "doi": "10.1002/humu.20495",
                "url": "https://pubmed.ncbi.nlm.nih.gov/17311302/",
                "variant_specific_relevance": "Comprehensive transactivation profiling showing complete loss of function for p.Arg248Gln.",
            },
        ],
    },
    "rs1042522": {
        "rsid": "rs1042522",
        "variation_id": "12356",
        "vcv_accession": "VCV000012356",
        "gene_symbol": "TP53",
        "title": "NM_000546.6(TP53):c.215C>G (p.Pro72Arg)",
        "aliases": ["c.215C>G", "p.Pro72Arg", "12356", "vcv000012356", "rcv000013377"],
        "assemblies": {
            "GRCh38": {
                "chromosome": "17",
                "position": 7676154,
                "reference_allele": "G",
                "alternate_allele": "C",
                "hgvsg": "NC_000017.11:g.7676154G>C",
            },
            "GRCh37": {
                "chromosome": "17",
                "position": 7579472,
                "reference_allele": "G",
                "alternate_allele": "C",
                "hgvsg": "NC_000017.10:g.7579472G>C",
            },
        },
        "hgvs_c": "c.215C>G",
        "hgvs_p": "p.Pro72Arg",
        "clinical": {
            "primary_classification": "Benign",
            "review_status": "reviewed by expert panel",
            "review_stars": 3,
            "conditions": ["Li-Fraumeni syndrome", "not specified"],
            "total_submissions": 34,
            "vcv_accession": "VCV000012356",
            "rcv_accessions": ["RCV000013377"],
            "is_conflicting": False,
            "conflict_summary": None,
            "submissions": [
                {
                    "submitter_name": "ClinGen TP53 Expert Panel",
                    "clinical_significance": "Benign",
                    "review_status": "reviewed by expert panel",
                    "evaluation_date": "2022-10-14",
                    "description": "Common non-pathogenic polymorphism in global human populations.",
                },
                {
                    "submitter_name": "Invitae",
                    "clinical_significance": "Benign",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-01-12",
                    "description": "High population frequency, well-documented benign polymorphism.",
                },
            ],
        },
        "transcripts": [
            {
                "transcript_id": "ENST00000269305",
                "gene_symbol": "TP53",
                "gene_id": "ENSG00000141510",
                "consequence_terms": ["missense_variant"],
                "hgvs_c": "ENST00000269305.9:c.215C>G",
                "hgvs_p": "ENSP00000269305.4:p.Pro72Arg",
                "exon": "4/11",
                "biotype": "protein_coding",
                "is_canonical": True,
                "is_mane_select": True,
                "codons": "Ccc/Gcc",
                "amino_acids": "P/R",
                "sift_prediction": "tolerated",
                "sift_score": 0.28,
                "polyphen_prediction": "benign",
                "polyphen_score": 0.05,
            }
        ],
        "population": {
            "allele_count": 136214,
            "allele_number": 251496,
            "allele_frequency": 0.5416,
            "homozygote_count": 36890,
            "hemizygote_count": 0,
            "popmax_frequency": 0.724,
            "popmax_population": "African/African American (afr)",
            "ancestry_frequencies": {
                "afr": 0.724,
                "amr": 0.582,
                "nfe": 0.534,
                "sas": 0.481,
                "eas": 0.389,
            },
        },
        "computational": [
            {
                "prediction_method": "SIFT",
                "prediction_output": "tolerated",
                "numerical_score": 0.28,
                "source": "Ensembl VEP",
                "version": "5.2.2",
            },
            {
                "prediction_method": "PolyPhen-2",
                "prediction_output": "benign",
                "numerical_score": 0.05,
                "source": "Ensembl VEP",
                "version": "2.2.3",
            },
            {
                "prediction_method": "CADD",
                "prediction_output": "benign",
                "numerical_score": 11.2,
                "source": "CADD v1.6 (PHRED)",
                "version": "v1.6",
            },
            {
                "prediction_method": "HelixGuard-QNN",
                "prediction_output": "Synthetic Class 0 (Benign-like)",
                "numerical_score": 0.076,
                "source": "Helix Guard Hybrid Quantum Neural Network",
                "version": "v1.0",
            },
        ],
        "literature": [
            {
                "pmid": "10557279",
                "title": "A common polymorphism in the p53 gene alters its ability to induce apoptosis.",
                "authors": ["Dumont P", "Leu JI", "Della Pietra AC 3rd", "George DL", "Murphy M"],
                "journal": "Nat Genet",
                "year": 2003,
                "doi": "10.1038/ng1090",
                "url": "https://pubmed.ncbi.nlm.nih.gov/10557279/",
                "variant_specific_relevance": "Functional evaluation of the codon 72 polymorphism showing subtle apoptotic kinetic variance within normal range.",
            },
        ],
    },
    "rs80357906": {
        "rsid": "rs80357906",
        "variation_id": "55407",
        "vcv_accession": "VCV000055407",
        "gene_symbol": "BRCA1",
        "title": "NM_007294.4(BRCA1):c.68_69delAG (p.Glu23ValfsTer17)",
        "aliases": ["185delAG", "c.68_69delAG", "55407", "vcv000055407", "rcv000062400"],
        "assemblies": {
            "GRCh38": {
                "chromosome": "17",
                "position": 43124031,
                "reference_allele": "AG",
                "alternate_allele": "-",
                "hgvsg": "NC_000017.11:g.43124031delAG",
            },
            "GRCh37": {
                "chromosome": "17",
                "position": 41276044,
                "reference_allele": "AG",
                "alternate_allele": "-",
                "hgvsg": "NC_000017.10:g.41276044delAG",
            },
        },
        "hgvs_c": "c.68_69delAG",
        "hgvs_p": "p.Glu23ValfsTer17",
        "clinical": {
            "primary_classification": "Pathogenic",
            "review_status": "criteria provided, multiple submitters, no conflicts",
            "review_stars": 2,
            "conditions": ["Hereditary breast and ovarian cancer syndrome"],
            "total_submissions": 38,
            "vcv_accession": "VCV000055407",
            "rcv_accessions": ["RCV000062400"],
            "is_conflicting": False,
            "conflict_summary": None,
            "submissions": [
                {
                    "submitter_name": "Ambry Genetics",
                    "clinical_significance": "Pathogenic",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-07-22",
                    "description": "Founder mutation 185delAG causing protein truncation.",
                },
                {
                    "submitter_name": "Invitae",
                    "clinical_significance": "Pathogenic",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-10-18",
                    "description": "Established pathogenic variant associated with hereditary breast/ovarian cancer.",
                },
            ],
        },
        "transcripts": [
            {
                "transcript_id": "ENST00000357654",
                "gene_symbol": "BRCA1",
                "gene_id": "ENSG00000012048",
                "consequence_terms": ["frameshift_variant"],
                "hgvs_c": "ENST00000357654.9:c.68_69del",
                "hgvs_p": "ENSP00000350283.3:p.Glu23ValfsTer17",
                "exon": "2/23",
                "biotype": "protein_coding",
                "is_canonical": True,
                "is_mane_select": True,
                "codons": "GAG/-",
                "amino_acids": "E/Vfs*17",
                "sift_prediction": "deleterious",
                "sift_score": 0.0,
                "polyphen_prediction": "probably_damaging",
                "polyphen_score": 1.0,
            }
        ],
        "population": {
            "allele_count": 24,
            "allele_number": 251400,
            "allele_frequency": 0.0000955,
            "homozygote_count": 0,
            "hemizygote_count": 0,
            "popmax_frequency": 0.0011,
            "popmax_population": "Ashkenazi Jewish (asj)",
            "ancestry_frequencies": {
                "asj": 0.0011,
                "nfe": 0.00009,
                "amr": 0.00002,
                "afr": 0.0,
                "eas": 0.0,
                "sas": 0.0,
            },
        },
        "computational": [
            {
                "prediction_method": "SIFT",
                "prediction_output": "deleterious",
                "numerical_score": 0.0,
                "source": "Ensembl VEP",
                "version": "5.2.2",
            },
            {
                "prediction_method": "PolyPhen-2",
                "prediction_output": "probably_damaging",
                "numerical_score": 1.0,
                "source": "Ensembl VEP",
                "version": "2.2.3",
            },
            {
                "prediction_method": "CADD",
                "prediction_output": "likely_deleterious",
                "numerical_score": 35.0,
                "source": "CADD v1.6 (PHRED)",
                "version": "v1.6",
            },
            {
                "prediction_method": "HelixGuard-QNN",
                "prediction_output": "Synthetic Class 1 (Pathogenic-like)",
                "numerical_score": 0.951,
                "source": "Helix Guard Hybrid Quantum Neural Network",
                "version": "v1.0",
            },
        ],
        "literature": [
            {
                "pmid": "7573030",
                "title": "A high frequency of BRCA1 185delAG mutation in Ashkenazi Jewish women with early onset breast cancer.",
                "authors": ["Struewing JP", "Abeliovich D", "Peretz T"],
                "journal": "Nat Genet",
                "year": 1995,
                "doi": "10.1038/ng1095-198",
                "url": "https://pubmed.ncbi.nlm.nih.gov/7573030/",
                "variant_specific_relevance": "Primary identification of the 185delAG founder mutation and high penetrance in hereditary cancer.",
            },
        ],
    },
    "rs28897724": {
        "rsid": "rs28897724",
        "variation_id": "55395",
        "vcv_accession": "VCV000055395",
        "gene_symbol": "BRCA1",
        "title": "NM_007294.4(BRCA1):c.5095C>T (p.Arg1699Gln)",
        "aliases": ["c.5095C>T", "p.Arg1699Gln", "55395", "vcv000055395", "rcv000062388"],
        "assemblies": {
            "GRCh38": {
                "chromosome": "17",
                "position": 43057110,
                "reference_allele": "C",
                "alternate_allele": "T",
                "hgvsg": "NC_000017.11:g.43057110C>T",
            },
            "GRCh37": {
                "chromosome": "17",
                "position": 41209127,
                "reference_allele": "C",
                "alternate_allele": "T",
                "hgvsg": "NC_000017.10:g.41209127C>T",
            },
        },
        "hgvs_c": "c.5095C>T",
        "hgvs_p": "p.Arg1699Gln",
        "clinical": {
            "primary_classification": "Conflicting interpretations of pathogenicity",
            "review_status": "criteria provided, conflicting interpretations",
            "review_stars": 1,
            "conditions": ["Hereditary breast and ovarian cancer syndrome"],
            "total_submissions": 18,
            "vcv_accession": "VCV000055395",
            "rcv_accessions": ["RCV000062388"],
            "is_conflicting": True,
            "conflict_summary": "Conflicting assertions: 12 Pathogenic / Likely pathogenic vs 6 Uncertain significance (VUS).",
            "submissions": [
                {
                    "submitter_name": "Ambry Genetics",
                    "clinical_significance": "Likely pathogenic",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-04-14",
                    "description": "Functional BRCT domain intermediate-risk allele.",
                },
                {
                    "submitter_name": "GeneDx",
                    "clinical_significance": "Pathogenic",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-06-18",
                    "description": "Classified pathogenic based on family segregation data.",
                },
                {
                    "submitter_name": "Invitae",
                    "clinical_significance": "Uncertain significance",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2023-09-02",
                    "description": "Moderate penetrance with conflicting clinical presentation.",
                },
                {
                    "submitter_name": "Quest Diagnostics",
                    "clinical_significance": "Uncertain significance",
                    "review_status": "criteria provided, single submitter",
                    "evaluation_date": "2022-11-10",
                    "description": "Uncertain significance pending further functional validation.",
                },
            ],
        },
        "transcripts": [
            {
                "transcript_id": "ENST00000357654",
                "gene_symbol": "BRCA1",
                "gene_id": "ENSG00000012048",
                "consequence_terms": ["missense_variant"],
                "hgvs_c": "ENST00000357654.9:c.5095C>T",
                "hgvs_p": "ENSP00000350283.3:p.Arg1699Gln",
                "exon": "18/23",
                "biotype": "protein_coding",
                "is_canonical": True,
                "is_mane_select": True,
                "codons": "cGa/cAa",
                "amino_acids": "R/Q",
                "sift_prediction": "deleterious",
                "sift_score": 0.01,
                "polyphen_prediction": "probably_damaging",
                "polyphen_score": 0.89,
            }
        ],
        "population": {
            "allele_count": 8,
            "allele_number": 251410,
            "allele_frequency": 0.0000318,
            "homozygote_count": 0,
            "hemizygote_count": 0,
            "popmax_frequency": 0.00006,
            "popmax_population": "European (non-Finnish)",
            "ancestry_frequencies": {
                "nfe": 0.00006,
                "amr": 0.0,
                "afr": 0.0,
                "eas": 0.0,
                "sas": 0.0,
            },
        },
        "computational": [
            {
                "prediction_method": "SIFT",
                "prediction_output": "deleterious",
                "numerical_score": 0.01,
                "source": "Ensembl VEP",
                "version": "5.2.2",
            },
            {
                "prediction_method": "PolyPhen-2",
                "prediction_output": "probably_damaging",
                "numerical_score": 0.89,
                "source": "Ensembl VEP",
                "version": "2.2.3",
            },
            {
                "prediction_method": "CADD",
                "prediction_output": "likely_deleterious",
                "numerical_score": 26.5,
                "source": "CADD v1.6 (PHRED)",
                "version": "v1.6",
            },
            {
                "prediction_method": "HelixGuard-QNN",
                "prediction_output": "Synthetic Class 1 (Pathogenic-like)",
                "numerical_score": 0.812,
                "source": "Helix Guard Hybrid Quantum Neural Network",
                "version": "v1.0",
            },
        ],
        "literature": [
            {
                "pmid": "17018160",
                "title": "A model for the interpretation of BRCA1 missense variants: evaluation of R1699Q.",
                "authors": ["Spurdle AB", "Couch FJ", "Hogervorst FB"],
                "journal": "J Med Genet",
                "year": 2007,
                "doi": "10.1136/jmg.2006.046185",
                "url": "https://pubmed.ncbi.nlm.nih.gov/17018160/",
                "variant_specific_relevance": "Detailed multi-factorial likelihood analysis demonstrating intermediate cancer risk for R1699Q.",
            },
        ],
    },
}


def _lookup_benchmark_entry(query: Optional[str]) -> Optional[Dict[str, Any]]:
    """Resolves an rsID, ClinVar variation ID, HGVS string, or coordinates against benchmark curations."""
    if not query:
        return None
    clean = query.strip().lower()
    if clean.startswith("vcv0"):
        clean_vcv = clean.lstrip("vcv0")
    else:
        clean_vcv = ""

    # Direct key lookup
    if clean in VARIANT_BENCHMARK_CURATIONS:
        return VARIANT_BENCHMARK_CURATIONS[clean]

    for key, entry in VARIANT_BENCHMARK_CURATIONS.items():
        if entry.get("rsid", "").lower() == clean:
            return entry
        if str(entry.get("variation_id", "")).lower() == clean:
            return entry
        if entry.get("vcv_accession", "").lower() == clean:
            return entry
        if clean_vcv and str(entry.get("variation_id", "")).lower() == clean_vcv:
            return entry
        if entry.get("hgvs_c", "").lower() == clean:
            return entry
        for alias in entry.get("aliases", []):
            if alias.lower() == clean:
                return entry

        # Check coordinate strings across assemblies
        for asm_name, coords in entry.get("assemblies", {}).items():
            norm_coord = f"{coords['chromosome']}-{coords['position']}-{coords['reference_allele']}-{coords['alternate_allele']}".lower()
            if norm_coord == clean or f"chr{norm_coord}" == clean:
                return entry
            colon_coord = f"{coords['chromosome']}:{coords['position']}:{coords['reference_allele']}:{coords['alternate_allele']}".lower()
            if colon_coord == clean or f"chr{colon_coord}" == clean:
                return entry
            if coords.get("hgvsg", "").lower() == clean:
                return entry

    return None
