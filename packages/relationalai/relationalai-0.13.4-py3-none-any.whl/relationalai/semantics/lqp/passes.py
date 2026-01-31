from relationalai.semantics.metamodel.compiler import Pass
from relationalai.semantics.metamodel.typer import Checker, InferTypes

from ..metamodel.rewrite import (
    DNFUnionSplitter, ExtractNestedLogicals, Flatten, FormatOutputs
)
from .rewrite import (
    AlgorithmPass, AnnotateConstraints, CDC, ConstantsToVars, DeduplicateVars,
    ExtractCommon, EliminateData, ExtractKeys, FunctionAnnotations, PeriodMath,
    QuantifyVars, Splinter, SplitMultiCheckRequires, UnifyDefinitions,
)

def lqp_passes() -> list[Pass]:
    return [
        SplitMultiCheckRequires(),
        FunctionAnnotations(),
        AnnotateConstraints(),
        Checker(),
        CDC(), # specialize to physical relations before extracting nested and typing
        ExtractNestedLogicals(), # before InferTypes to avoid extracting casts
        InferTypes(),
        DNFUnionSplitter(), # Handle unions that require DNF decomposition
        ExtractKeys(), # Create a logical for each valid combinations of keys
        FormatOutputs(),
        ExtractCommon(), # Extracts tasks that will become common after Flatten into their own definition
        Flatten(), # Move nested tasks to the top level, and various related things touched along the way
        Splinter(), # Splits multi-headed rules into multiple rules
        QuantifyVars(), # Adds missing existentials
        EliminateData(),  # Turns Data nodes into ordinary relations.
        DeduplicateVars(),  # Deduplicates vars in Updates and Outputs.
        ConstantsToVars(),  # Turns constants in Updates and Outputs into vars.
        AlgorithmPass(),
        PeriodMath(),  # Rewrite date period uses.
        UnifyDefinitions(), # Unify relations with multiple definitions.
    ]
