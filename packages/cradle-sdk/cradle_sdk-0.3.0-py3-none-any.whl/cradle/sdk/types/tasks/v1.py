from __future__ import annotations

from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, Field

from .common import (
    ArtifactParam,
    ParametersBase,
    ResultBase,
    TableResult,
    TableSourceQuery,
    TableSourceTable,
    TableSourceTaskResult,
)


class FeatureAnnotation(StrEnum):
    """Annotation to be configured per residue in a domain:

    UNRELIABLE: The evolutionary context is not reliable, eg in CDRs of antibodies.
    IGNORE: A part of the sequence that should not be used for evolutionary search and won't be mutated, this can be tags, linkers or other artificial subsequences.
    """

    UNRELIABLE = "UNRELIABLE"
    IGNORE = "IGNORE"


class OptimizationDirection(StrEnum):
    MAXIMIZE = "MAXIMIZE"
    MINIMIZE = "MINIMIZE"


class ProteinDatabase(StrEnum):
    UNIREF_30 = "UNIREF_30"
    OAS_90 = "OAS_90"


class ProteinModelType(StrEnum):
    DEFAULT = "DEFAULT"
    ANTIBODY = "ANTIBODY"


class ScaleType(StrEnum):
    MULTIPLICATIVE = "MULTIPLICATIVE"
    ADDITIVE = "ADDITIVE"
    RANK = "RANK"


class AbsoluteConstraint(BaseModel):
    type_: Literal["ABSOLUTE_CONSTRAINT"] = Field(default="ABSOLUTE_CONSTRAINT", alias="type")
    assay_id: str = Field(description="The ID of the constrained assay.")
    direction: OptimizationDirection = Field(
        description="Whether the assay value should be above (MAXIMIZE) or below (MINIMIZE) the threshold."
    )
    threshold: float = Field(description="The threshold assay value.")


class AnalyzeDataParameters(ParametersBase):
    task_type: ClassVar[str] = "analyze.data/v1"

    reference_sequence: str = Field(description="The sequence to consider as a reference for computing mutations.")
    dataset: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The assay data to be used for model training.")
    assays: list[Assay] = Field(default_factory=list, description="List of assay metadata entries")


class AnalyzeDiversifyParameters(ParametersBase):
    task_type: ClassVar[str] = "analyze.diversify/v1"

    selected_sequences: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The name of the input table with the selected sequences.")
    generated_sequences: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The name of the input view/table with the generated sequences.")
    template_metadata: TemplateMetadata = Field(description="Metadata about templates.")


class AnalyzeEngineerParameters(ParametersBase):
    task_type: ClassVar[str] = "analyze.engineer/v1"

    selected_sequences: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The name of the input table with the selected sequences.")
    engineered_sequences: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The name of the input view/table with the generated sequences.")
    assays: list[Assay] = Field(
        default_factory=list, description="The list of objectives that were optimized during training."
    )
    primary_objective: PrimaryObjective = Field(description="The primary objective to be optimized.")
    constraints: list[Annotated[AbsoluteConstraint | RelativeConstraint, Field(discriminator="type_")]] = Field(
        default_factory=list, description="The constraints applied to engineering."
    )
    template_metadata: list[TemplateMetadata] = Field(description="Metadata about templates.")
    new_mutation_ratio: float = Field(description="Ratio of new mutations in the generated sequences.")
    scorer: ArtifactParam = Field(description="Scoring model used to predict assay values for candidate sequences.")


class AnalyzeResult(ResultBase):
    report: ArtifactParam = Field(description="The report data")


class AnalyzeTrainParameters(ParametersBase):
    task_type: ClassVar[str] = "analyze.train/v1"

    prediction_data: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="Table of predicted assay values for the input dataset under the scorer.")
    generator_prediction_data: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="Pseudo log-likelihoods of the sequences in the dataset under the sampler.")
    assays: list[Assay] = Field(default_factory=list, description="List of assay metadata entries")
    primary_objective: PrimaryObjective = Field(
        description="The primary objective on which the sampler model is conditioned."
    )
    constraints: list[Annotated[AbsoluteConstraint | RelativeConstraint, Field(discriminator="type_")]] = Field(
        default_factory=list, description="The constraints applied to training."
    )


class Assay(BaseModel):
    assay_id: str = Field(description="ID of the assay")
    name: str = Field(description="Human readable name of the assay")
    scale_type: ScaleType = Field(
        description="The scale type defines how the assay behaves.\n\n* **Additive**: Assay values are comparable in magnitude over batches, a delta of eg 5 in one batch is equivalent to 5 in another batch.\n* **Multiplicative**: Assay values are comparable over batches by applying a multiplication factor, eg fold improvement: `score_variantB_batch1 = factor(typically starting sequence score) * score_variantB_batch`.\n* **Rank**: Assay values are not comparable over batches, we can only assume the ranking within a batch is correct."
    )
    unit: str | None = Field(default=None, description="Unit of the assay - used for display purposes only")


class BlockedAAItem(BaseModel):
    blocked_aas: str = Field(
        description="One or more amino acid letter code to be blocked from being mutated to. Use '*' to indicate that a position is fully blocked from being mutated."
    )
    ranges: list[tuple[int, int]] = Field(
        description="List of ranges where the mutations are blocked. Each range is a tuple of (start, end). Indices are 0-based and inclusive for the start and exclusive for the end. For example, (0, 5) blocks positions 0 to 4."
    )


class BlockedMotifItem(BaseModel):
    blocked_motif: str = Field(description="Amino acid motif to be blocked from appearing in the final sequence.")
    ranges: list[tuple[int, int]] = Field(
        description="List of ranges where the motif is blocked. Each range is a tuple of (start, end). Indices are 0-based and inclusive for the start and exclusive for the end. For example, (0, 5) blocks positions 0 to 4. The entire motif must fit into the specified positions to be blocked."
    )


class ClusterParameters(BaseModel):
    e_value_threshold: float = Field(
        default=float("inf"),
        description="Maximum e-value allowed between linked sequences in clustering algorithm. A lower number will result in tighter clusters.",
    )
    coverage_threshold: float = Field(
        default=0.8,
        description="Minimum coverage allowed between linked sequences in clustering algorithm. A higher number will result in tighter clusters.",
    )
    sequence_identity_threshold: float = Field(
        default=0.0,
        description="Minimum sequence identity allowed between linked sequences in clustering algorithm. A higher number will result in tighter clusters.",
    )


class ClusteredBatches(BaseModel):
    assayed_sequences: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="Table containing assayed sequences. Everything outside of this set will not be selected.")
    sort_parameters: SortParameters
    filter_parameters: FilterParameters | None = Field(default=None, description="If `None`, no filtering is applied.")
    cluster_ids_or_parameters: (
        list
        | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
        | ClusterParameters
    ) = Field(
        default_factory=ClusterParameters,
        description="Either a table mapping sequences to cluster ids or parameters for running clustering.",
    )


class DatabaseSearch(BaseModel):
    type_: Literal["DATABASE_SEARCH"] = Field(default="DATABASE_SEARCH", alias="type")
    seed_domains: list[str] = Field(description="A list of domain sequences to search for.")
    database: ProteinDatabase = Field(
        default=ProteinDatabase.UNIREF_30, description="Type of the protein database to use."
    )


class DiversifyParameters(ParametersBase):
    task_type: ClassVar[str] = "diversify/v1"

    template_sequence: DiversifyTemplateInputs = Field(description="The template amino acid sequence to diversify.")
    homologs: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(
        description="Table of homologs to use for generator training. In the simplest case, this is just the result of a multiple sequence alignment (MSA) against the sequence to optimize."
    )
    domain_features: dict[
        str,
        Annotated[
            list[DomainFeatureItem],
            Field(
                description="List of domain annotations. A residue may be assigned zero or one annotations. Ranges which are not annotated are considered reliable, i.e. the MSA in those ranges is used to infer conservation-based features."
            ),
        ],
    ] = Field(
        default_factory=dict,
        description="Properties for each domain. A domain is one or more subsequences of the protein sequence, for example the active site of an enzyme, CDRs of an antibody, heavy and light chains of an scFv, etc. ",
    )
    protein_model_type: ProteinModelType = Field(
        default=ProteinModelType.DEFAULT,
        description="Specifies the type of base model to use for training: use `DEFAULT` for single-chain proteins and `ANTIBODY` for multi-chain antibodies.",
    )


class DiversifyResult(ResultBase):
    selected_sequences: TableResult = Field(description="Table containing the selected sequences.")
    generated_sequences: TableResult = Field(description="Table containing the generated sequences.")
    template_metadata: TemplateMetadata = Field(description="Metadata about templates.")
    report: ArtifactParam = Field(description="A report on the result of the task.")


class DiversifyTemplateInputs(BaseModel):
    template_id: str = Field(
        description="Identifier for the template used to identify the source of generated sequences in the output."
    )
    sequence: str = Field(description="The template amino acid sequence")
    num_results: int = Field(
        description="Number of sequences to generate for the final plate from the template sequence."
    )
    min_mutations: int = Field(default=1, description="Minimum number of mutations per sequence")
    max_mutations: int = Field(default=4, description="Maximum number of mutations per sequence")
    blocked_aas: list[BlockedAAItem] = Field(
        default_factory=list,
        description="List of blocked amino acids which may not be mutated to, with their respective ranges.",
    )
    blocked_motifs: list[BlockedMotifItem] = Field(
        default_factory=list, description="List of blocked amino acid motifs with their respective ranges."
    )


class DomainFeatureItem(BaseModel):
    annotation: FeatureAnnotation = Field(
        description="Annotation for the residues. `UNRELIABLE`: do not look at the MSA to infer conservation-based features (e.g. CDRs) for the protein `IGNORE`: do not change this position at all (e.g. for linkers) and do not use to infer any conservation-based features."
    )
    ranges: list[tuple[int, int]] = Field(
        description="List of ranges where the annotation applies. Each range is a tuple of (start, end). Indices are 0-based and inclusive for the start and exclusive for the end. For example, (0, 5) blocks positions 0 to 4."
    )


class EngineerParameters(ParametersBase):
    task_type: ClassVar[str] = "engineer/v1"

    dataset: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The table of assayed data, to be used for exploitation.")
    assays: list[Assay] = Field(default_factory=list, description="List of assay metadata entries")
    primary_objective: PrimaryObjective = Field(description="The primary objective the samplers are trained for.")
    constraints: list[Annotated[AbsoluteConstraint | RelativeConstraint, Field(discriminator="type_")]] = Field(
        default_factory=list, description="List of assay constraints"
    )
    samplers: list[ArtifactParam] = Field(description="The sampling models used to generate candidate sequences.")
    scorer: ArtifactParam = Field(description="Scoring model used to predict assay values for candidate sequences.")
    template_sequences: list[TemplateInputs] = Field(description="Initial sequences used as templates for generation")


class EngineerResult(ResultBase):
    selected_sequences: TableResult = Field(description="Table containing the selected sequences.")
    engineered_sequences: TableResult = Field(description="Table containing the generated sequences.")
    num_evaluated_seqs: int = Field(
        description="Number of sequences evaluated in silico (only the ones sent to the predictor)."
    )
    num_generated_seqs: int = Field(
        description="Number of sequences generated in silico (this is > num_evaluated_seqs, as it includes generated sequences that were not sent to the predictor, due to lower likelihood)."
    )
    new_mutation_ratio: float = Field(
        description="Number of mutations in `selected_candidates` that do not appear in train/test datasets."
    )
    template_metadata: list[TemplateMetadata] = Field(description="Metadata about templates.")
    report: ArtifactParam = Field(description="A report on the result of the task.")


class FilterParameters(BaseModel):
    objective: PrimaryObjective = Field(
        description="The objective used for filtering clusters. Assay id must match one of the assay ids in the input dataset."
    )
    hit_redundancy: int = Field(
        default=5,
        description='The maximum number of similar variants within the proposed set.\n\nWe say two variants are "similar" when their predicted performances are highly correlated.\nAt lower values this will mean on average fewer hits, but greater diversity within the set,\nwhile at maximum value (hit_redundancy=num_selected) the selection is purely greedy, with\nno requirement on diversity within the set.',
    )


class Homologs(BaseModel):
    type_: Literal["HOMOLOGS"] = Field(default="HOMOLOGS", alias="type")
    homologs: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="Precomputed homologs table.")


class LabeledSelectionParameters(BaseModel):
    assayed_sequences: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(
        description="Table containing sequences with assays to use for down-selection. Everything outside of this set will not be selected."
    )


class PrimaryObjective(BaseModel):
    assay_id: str = Field(description="The ID of the assay to be optimized.")
    direction: OptimizationDirection = Field(description="Whether the maximize or minimize the assay value.")


class RelativeConstraint(BaseModel):
    type_: Literal["RELATIVE_CONSTRAINT"] = Field(default="RELATIVE_CONSTRAINT", alias="type")
    assay_id: str = Field(description="The ID of the constrained assay.")
    direction: OptimizationDirection = Field(
        description="Whether the assay value of new sequences should be above (MAXIMIZE) or below (MINIMIZE) the assay value of the `relative_to` sequence."
    )
    relative_to: str = Field(description="The sequence relative to which new sequences are constrained.")


class ScoredSelectionParameters(BaseModel):
    scorer: ArtifactParam
    hit_redundancy: int = Field(
        default=10,
        description="Number of top candidates for which to optimize the average score. A higher number means less diversity.",
    )
    max_mutation_frequency: float | None = Field(
        default=None,
        description="Maximum mutation frequency in the set of selected sequences. If None, the algorithm will pick sensible defaults.",
    )


class SearchParameters(ParametersBase):
    task_type: ClassVar[str] = "search/v1"

    source: Homologs | DatabaseSearch = Field(
        description="Precomputed homologs table or seed sequences to search for. If a table of precomputed sequence homologs is provided, the entries in the `seed_domain` column of this table may be used for sequence feature computation. For example, if the sequence to be optimized is an scFv, the `seed_domain` column would contain the heavy and light chain scaffold sequences of the scFv. These 2 scaffold sequences will be used to search for homologs and infer features such as the CDRs.",
        discriminator="type_",
    )
    antibody_sequence_features: bool = Field(
        default=False, description="Whether to compute sequence features. Only supported for antibodies."
    )


class SearchResult(ResultBase):
    domain_features: dict[
        str,
        Annotated[
            list[DomainFeatureItem],
            Field(
                description="List of domain annotations. A residue may be assigned zero or one annotations. Ranges which are not annotated are considered reliable, i.e. the MSA in those ranges is used to infer conservation-based features."
            ),
        ],
    ] = Field(
        default_factory=dict,
        description="Mapping of protein sequences to their respective domain features. Each range in the domain features must be a valid index into the corresponding protein sequence.",
    )
    homologs: TableResult


class SelectParameters(ParametersBase):
    task_type: ClassVar[str] = "select/v1"

    sequences: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The sequences to select from.")
    objective: PrimaryObjective = Field(
        description="The primary objective to optimize during selection. This is used for scoring sequences."
    )
    constraints: list[Annotated[AbsoluteConstraint | RelativeConstraint, Field(discriminator="type_")]] = Field(
        default_factory=list, description="Constraints that must be satisfied by the selected sequences."
    )
    selection_method: ScoredSelectionParameters | LabeledSelectionParameters = Field(
        description="Method of selection. Can either be based on a scorer or on hard labels."
    )
    clustered_batches: ClusteredBatches | None = Field(
        default=None,
        description="Determines the clusters and representatives to use for selection. If `None`, all sequences are passed for selection at once.",
    )
    max_num_sequences_to_select: int = Field(description="No more than this many sequences will be selected.")
    min_num_sequences_to_select: int = Field(
        default=0, description="Warning will be raised if fewer than this many sequences are selected."
    )


class SelectResults(ResultBase):
    selected_sequences: TableResult = Field(description="Table containing the selected sequences.")


class SortParameters(BaseModel):
    objective: PrimaryObjective = Field(
        description="The objective used for sorting clusters. Assay id must match one of the assay ids in the input dataset. Sorting direction is determined by `objective.direction`."
    )


class TemplateInputs(BaseModel):
    template_id: str = Field(
        description="Identifier for the template used to identify the source of generated sequences in the output."
    )
    sequence: str = Field(description="The template amino acid sequence")
    num_results: int = Field(
        description="Number of sequences generated from this template to be added to the final plate."
    )
    min_mutations: int = Field(default=1, description="Minimum number of mutations per sequence.")
    max_mutations: int = Field(default=8, description="Maximum number of mutations per sequence.")
    hit_redundancy: int = Field(
        default=10,
        description="Number of top candidates for which to optimize the average score. A higher number means less diversity.",
    )
    blocked_aas: list[BlockedAAItem] = Field(
        default_factory=list,
        description="List of blocked amino acids which may not be mutated to, with their respective ranges.",
    )
    blocked_motifs: list[BlockedMotifItem] = Field(
        default_factory=list, description="List of blocked amino acid motifs with their respective ranges."
    )
    blocked_regexps: list[str] | None = Field(
        default_factory=list, description="Regular expressions that the sequence cannot match"
    )
    must_match_regexps: list[str] | None = Field(
        default_factory=list,
        description="Generated sequences must match all of the given regular expressions. Can be used to enforce certain motifs.",
    )


class TemplateMetadata(BaseModel):
    template_id: str = Field(
        description="Identifier for the template used to identify the source of generated sequences."
    )
    sequence: str = Field(description="Amino acid template sequence used for generation.")
    blocked_aas: list[BlockedAAItem] = Field(
        default_factory=list,
        description="List of blocked amino acids which may not be mutated to, with their respective ranges.",
    )
    min_mutations: int
    max_mutations: int
    structure: ArtifactParam | None = Field(default=None)


class TrainParameters(ParametersBase):
    task_type: ClassVar[str] = "train/v1"

    homologs: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The table of homologous sequences to be used for training the base model.")
    domain_features: dict[
        str,
        Annotated[
            list[DomainFeatureItem],
            Field(
                description="List of domain annotations. A residue may be assigned zero or one annotations. Ranges which are not annotated are considered reliable, i.e. the MSA in those ranges is used to infer conservation-based features."
            ),
        ],
    ] = Field(
        default_factory=dict,
        description="Mapping of protein sequences to their respective domain features. Each range in the domain features must be a valid index into the corresponding protein sequence.",
    )
    protein_model_type: ProteinModelType = Field(
        default=ProteinModelType.DEFAULT,
        description="Specifies the type of base model to use for training: use `DEFAULT` for single-chain proteins and `ANTIBODY` for multi-chain antibodies.",
    )
    dataset: (
        list | Annotated[TableSourceTable | TableSourceQuery | TableSourceTaskResult, Field(discriminator="kind")]
    ) = Field(description="The name of the input table to be used for model training.")
    assays: list[Assay] = Field(default_factory=list, description="List of assay metadata entries")
    primary_objective: PrimaryObjective = Field(
        description="The primary objective on which the sampler model is conditioned. Should correspond to an assay in `dataset`."
    )


class TrainResult(ResultBase):
    base_sampler: ArtifactParam = Field(
        description="A sampler which attempts to produce plausible sequences as understood relative to the passed `homologs`. "
    )
    conditioned_sampler: ArtifactParam | None = Field(
        description="A sampler which attempts to produce high quality sequences as understood relative to the passed `primary_objective`."
    )
    scorer: ArtifactParam = Field(description="The scoring model, trained on the assay data provided.")
    prediction_data: TableResult = Field(description="Predicted assay values on all folds of the input dataset.")
    generator_prediction_data: TableResult = Field(
        description="Pseudo log-likelihoods of the sequences in the dataset under the generator(s)."
    )
    report: ArtifactParam = Field(description="A report on the result of the task.")
