from typing import TypeGuard
from relationalai.semantics.metamodel import factory as f, ir, types
from relationalai.semantics.metamodel.util import FrozenOrderedSet
from relationalai.semantics.metamodel import builtins

# Indicates a relation is short-lived, thus, backends should not optimize for incremental
# maintenance.
adhoc = f.relation("adhoc", [])
adhoc_annotation = f.annotation(adhoc, [])

# We only want to emit attributes for a known set of annotations.
supported_lqp_annotations = FrozenOrderedSet([
    adhoc.name,
    builtins.function.name,
    builtins.track.name,
    builtins.recursion_config.name,
])

# [LoopyIR] Annotations used to mark metamodel IR elements as Loopy constructs.
# 1. Programming structures:
#   * @script marks Sequence blocks `begin ... end`
#   * @algorithm additionally marks the top-level script
#   * @while marks Loop as a `while(true) {...}`; its sole Task is a @script @while Sequence
# 2. Base instructions (Update's with derive Effects)
#   * @global marks instructions that write to a global relation (only used in top-level script)
#   * @empty marks instructions that initialize relations to an empty relation
#   * @assign marks instructions that are standard assignments
#   * @upsert marks instructions that perform in-place upserts
#   * @monoid marks instructions that perform in-place monoid updates
#   * @monus marks instructions that perform in-place monus updates

# These tasks require dedicated handling and currently are only supported in LQP.

# Here we only provide basic inspection functions. Functions for creating these annotations
# and more complex analysis are in the module relationalai.semantics.lqp.algorithms

# Algorithm: for top-level script of an algorithm
_algorithm_anno_name = "algorithm"
algorithm = f.relation(_algorithm_anno_name, [])

def algorithm_annotation():
    return f.annotation(algorithm, [])

def has_algorithm_annotation(node: ir.Node) -> bool:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _algorithm_anno_name:
            return True
    return False

# Script: for Sequence blocks (algorithm or while loop)
_script_anno_name = "script"
script = f.relation(_script_anno_name, [])

def script_annotation():
    return f.annotation(script, [])

def has_script_annotation(node: ir.Node) -> bool:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _script_anno_name:
            return True
    return False

# While: for a while Loop or its script body (Sequence)
_while_anno_name = "while"
while_ = f.relation(_while_anno_name, [])

def while_annotation():
    return f.annotation(while_, [])

def has_while_annotation(node: ir.Node) -> bool:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _while_anno_name:
            return True
    return False

# Global: marks instructions that write to relation that is the result of an algorithm
_global_anno_name = "global"
global_ = f.relation(_global_anno_name, [])

def global_annotation():
    return f.annotation(global_, [])

def has_global_annotation(node: ir.Node) -> TypeGuard[ir.Update]:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _global_anno_name:
            return True
    return False

# Empty: Initializes a relation to an empty relation
_empty_anno_name = "empty"
empty = f.relation(_empty_anno_name, [])

def empty_annotation():
    return f.annotation(empty, [])

def has_empty_annotation(node: ir.Node) -> TypeGuard[ir.Update]:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _empty_anno_name:
            return True
    return False

# Assign: overwrites the target relation
_assign_anno_name = "assign"
assign = f.relation(_assign_anno_name, [])

def assign_annotation():
    return f.annotation(assign, [])

def has_assign_annotation(node: ir.Node) -> TypeGuard[ir.Update]:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _assign_anno_name:
            return True
    return False

# Upsert: In-place update of relation
_upsert_anno_name = "upsert"
upsert = f.relation(_upsert_anno_name, [])

def upsert_annotation(arity: int):
    return f.annotation(upsert, [f.literal(arity, type=types.Int64)])

def has_upsert_annotation(node: ir.Node) -> TypeGuard[ir.Update]:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _upsert_anno_name:
            return True
    return False

def get_upsert_annotation(i: ir.Update):
    for anno in i.annotations:
        if anno.relation.name == _upsert_anno_name:
            return anno
    return None

# Monoid: In-place update of relation by another by a monoid operation (e.g. Integer addition)
_monoid_anno_name = "monoid"
monoid = f.relation(_monoid_anno_name, [])

def monoid_annotation(monoid_type: ir.ScalarType, monoid_op: str, arity: int):
    return f.annotation(monoid, [f.literal(arity, type=types.Int64), monoid_type, f.literal(monoid_op, type=types.String)])

def has_monoid_annotation(node: ir.Node) -> TypeGuard[ir.Update]:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _monoid_anno_name:
            return True
    return False

def get_monoid_annotation(i: ir.Update):
    for anno in i.annotations:
        if anno.relation.name == _monoid_anno_name:
            return anno
    return None

# Monus: In-place update of relation by another by "subtraction" operation, if it exists (e.g. Integer subtraction)
_monus_anno_name = "monus"
monus = f.relation(_monus_anno_name, [])

def monus_annotation(monoid_type: ir.ScalarType, monoid_op: str, arity: int):
    return f.annotation(monus, [f.literal(arity, type=types.Int64), monoid_type, f.literal(monoid_op, type=types.String)])

def has_monus_annotation(node: ir.Node) -> TypeGuard[ir.Update]:
    if not hasattr(node, "annotations"):
        return False
    annotations = getattr(node, "annotations", [])
    for anno in annotations:
        if anno.relation.name == _monus_anno_name:
            return True
    return False

def get_monus_annotation(i: ir.Update):
    for anno in i.annotations:
        if anno.relation.name == _monus_anno_name:
            return anno
    return None

# Get arity from annotation (for @upsert, @monoid, and @monus)
def get_arity(i: ir.Annotation):
    for arg in i.args:
        if isinstance(arg, ir.Literal) and (arg.type == types.Int64 or arg.type == types.Int128 or arg.type == types.Number):
            return arg.value
    assert False, "Failed to get arity"

# All Loopy instructions
loopy_instructions = [
    empty,
    assign,
    upsert,
    monoid,
    monus
]
