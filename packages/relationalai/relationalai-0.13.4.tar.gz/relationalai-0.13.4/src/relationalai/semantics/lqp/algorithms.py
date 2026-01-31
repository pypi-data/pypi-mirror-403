from typing import TypeGuard
from relationalai.semantics.metamodel import ir, factory, types
from relationalai.semantics.metamodel.visitor import Rewriter, collect_by_type
from relationalai.semantics.lqp import ir as lqp
from relationalai.semantics.lqp.types import meta_type_to_lqp
from relationalai.semantics.lqp.builtins import (
    has_empty_annotation, has_assign_annotation, has_upsert_annotation,
    has_monoid_annotation, has_monus_annotation, has_script_annotation,
    has_algorithm_annotation, has_while_annotation, global_annotation,
    empty_annotation, assign_annotation, upsert_annotation, monoid_annotation,
    monus_annotation
)

# Complex tests for Loopy constructs in the metamodel
def is_script(task: ir.Task) -> TypeGuard[ir.Sequence]:
    """ Check if it is a script i.e., a Sequence with @script annotation. """
    if not isinstance(task, ir.Sequence):
        return False
    return has_script_annotation(task)

def is_algorithm_logical(task: ir.Task) -> TypeGuard[ir.Logical]:
    """ Check if it is an algorithm logical i.e., a Logical task with all subtasks being
    algorithm scripts. """
    if not isinstance(task, ir.Logical):
        return False
    return all(is_algorithm_script(subtask) for subtask in task.body)

def is_algorithm_script(task: ir.Task) -> TypeGuard[ir.Sequence]:
    """ Check if it is an algorithm script i.e., a Sequence with @script and @algorithm annotations. """
    if not isinstance(task, ir.Sequence):
        return False
    return is_script(task) and has_algorithm_annotation(task)

def is_while_loop(task: ir.Task) -> TypeGuard[ir.Loop]:
    """ Check if input is is a while loop i.e., a Loop with @while annotation. """
    if not isinstance(task, ir.Loop):
        return False
    return has_while_annotation(task)

def is_while_script(task: ir.Task) -> TypeGuard[ir.Sequence]:
    """ Check if input is a while script i.e., a Sequence with @script and @while annotations. """
    if not isinstance(task, ir.Sequence):
        return False
    return is_script(task) and has_while_annotation(task)

# Tools for annotating Loopy constructs
class LoopyAnnoAdder(Rewriter):
    """ Rewrites a node by adding the given annotation to all Update nodes. """
    def __init__(self, anno: ir.Annotation):
        self.anno = anno
        super().__init__()

    def handle_update(self, node: ir.Update, parent: ir.Node) -> ir.Update:
        new_annos = list(node.annotations) + [self.anno]
        return factory.update(node.relation, node.args, node.effect, new_annos, node.engine)

def mk_global(i: ir.Node):
    return LoopyAnnoAdder(global_annotation()).walk(i)

def mk_empty(i: ir.Node):
    return LoopyAnnoAdder(empty_annotation()).walk(i)

def mk_assign(i: ir.Node):
    return LoopyAnnoAdder(assign_annotation()).walk(i)

def mk_upsert(i: ir.Node, arity: int):
    return LoopyAnnoAdder(upsert_annotation(arity)).walk(i)

def mk_monoid(i: ir.Node, monoid_type: ir.ScalarType, monoid_op: str, arity: int):
    return LoopyAnnoAdder(monoid_annotation(monoid_type, monoid_op, arity)).walk(i)

def mk_monus(i: ir.Node, monoid_type: ir.ScalarType, monoid_op: str, arity: int):
    return LoopyAnnoAdder(monus_annotation(monoid_type, monoid_op, arity)).walk(i)

def construct_monoid(i: ir.Annotation):
    base_type = None
    op = None
    for arg in i.args:
        if isinstance(arg, ir.ScalarType):
            base_type = meta_type_to_lqp(arg)
        elif isinstance(arg, ir.Literal) and arg.type == types.String:
            op = arg.value
    assert isinstance(base_type, lqp.Type) and isinstance(op, str), "Failed to get monoid"
    if op.lower() == "or":
        return lqp.OrMonoid(meta=None)
    elif op.lower() == "sum":
        return lqp.SumMonoid(type=base_type, meta=None)
    elif op.lower() == "min":
        return lqp.MinMonoid(type=base_type, meta=None)
    elif op.lower() == "max":
        return lqp.MaxMonoid(type=base_type, meta=None)
    else:
        assert False, "Failed to get monoid"

# Tools for analyzing Loopy constructs
def is_logical_instruction(node: ir.Node) -> TypeGuard[ir.Logical]:
    if not isinstance(node, ir.Logical):
        return False
    return any(collect_by_type(ir.Update, node)) and not any(collect_by_type(ir.Sequence, node))

def get_instruction_body_rels(node: ir.Logical) -> set[ir.Relation]:
    assert is_logical_instruction(node)
    body: set[ir.Relation] = set()
    for update in collect_by_type(ir.Lookup, node):
        body.add(update.relation)
    return body

def get_instruction_head_rels(node: ir.Logical) -> set[ir.Relation]:
    assert is_logical_instruction(node)
    heads: set[ir.Relation] = set()
    for update in collect_by_type(ir.Update, node):
        heads.add(update.relation)
    return heads

# base Loopy instruction: @empty, @assign, @upsert, @monoid, @monus
def is_instruction(update: ir.Task) -> TypeGuard[ir.Logical]:
    if not is_logical_instruction(update):
        return False
    for u in collect_by_type(ir.Update, update):
        if (has_empty_annotation(u) or
            has_assign_annotation(u) or
            has_upsert_annotation(u) or
            has_monoid_annotation(u) or
            has_monus_annotation(u)):
            return True
    return False

# update Loopy instruction @upsert, @monoid, @monus
def is_update_instruction(task: ir.Task) -> TypeGuard[ir.Logical]:
    if not is_logical_instruction(task):
        return False
    for u in collect_by_type(ir.Update, task):
        if (has_upsert_annotation(u) or
            has_monoid_annotation(u) or
            has_monus_annotation(u)):
            return True
    return False

def is_empty_instruction(node: ir.Node) -> TypeGuard[ir.Logical]:
    """ Check if input is an empty Loopy instruction `empty rel = ∅`"""
    if not is_logical_instruction(node):
        return False
    updates = collect_by_type(ir.Update, node)
    if not any(has_empty_annotation(update) for update in updates):
        return False

    # At this point, we have the prerequisites for an empty instruction. We check it is
    # well-formed:
    # 1. It has only a single @empty Update operation
    # 2. Has no other operations
    assert len(updates) == 1, "[Loopy] Empty instruction must have single Update operation"
    assert len(node.body) == 1, "[Loopy] Empty instruction must have only a single Update operation"

    return True

# Splits a Loopy instruction into its head updates, body lookups, and other body tasks
def split_instruction(update_logical: ir.Logical) -> tuple[ir.Update,list[ir.Lookup],list[ir.Task]]:
    assert is_instruction(update_logical)
    lookups = []
    update = None
    others = []
    for task in update_logical.body:
        if isinstance(task, ir.Lookup):
            lookups.append(task)
        elif isinstance(task, ir.Update):
            if update is not None:
                raise AssertionError("[Loopy] Update instruction must have exactly one Update operation")
            update = task
        else:
            others.append(task)
    assert update is not None, "[Loopy] Update instruction must have exactly one Update operation"

    return update, lookups, others
