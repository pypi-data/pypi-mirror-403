from collections import defaultdict
from typing import Optional, TypeGuard, Union, cast
from relationalai.semantics.metamodel import ir, helpers, factory
from relationalai.semantics.metamodel.compiler import Pass
from relationalai.semantics.metamodel.visitor import Visitor, Rewriter, collect_by_type
from relationalai.semantics.lqp.algorithms import (
    is_script, is_algorithm_script,is_logical_instruction, is_update_instruction,
    get_instruction_head_rels, get_instruction_body_rels, mk_assign, split_instruction
)

class AlgorithmPass(Pass):
    """
    Transforms algorithm scripts by normalizing Loopy constructs (iterative algorithm).

    This pass applies three main rewriting transformations to Metamodel IR that prepare
    algorithm scripts for execution, in the order listed below:

    1. *Intermediate Rescoping*: Moves nested logical intermediate relations from their
       original logical scope into algorithm scripts, placing them immediately before each
       instruction that uses them (which can include Break instructions). Removes
       intermediates from the logical scope if they're only used within algorithms.
       TODO: Monitor https://github.com/RelationalAI/relationalai-python/pull/3187

       Example (Metamodel IR):
           BEFORE:
               Logical
                   Logical
                       R(x::Int128, y::Int128)
                       → derive _nested_logical_1(x::Int128, y::Int128) @assign
                   Sequence @script @algorithm
                       Logical
                           _nested_logical_1(a::Int128, b::Int128)
                           → derive S(a::Int128, b::Int128) @assign

           AFTER:
               Logical
                   Sequence @script @algorithm
                       Logical
                           R(x::Int128, y::Int128)
                           → derive _nested_logical_1(x::Int128, y::Int128) @assign
                       Logical
                           _nested_logical_1(a::Int128, b::Int128)
                           → derive S(a::Int128, b::Int128) @assign

    2. **Update Normalization**: Transforms Loopy update operations (@upsert, @monoid, @monus)
       to use a single body atom. Complex bodies with multiple lookups or additional
       operations are normalized by introducing intermediate relations.

       Example (Metamodel IR):
           BEFORE:
               Logical
                   R(x::Int128, y::Int128)
                   S(y::Int128, z::Int128)
                   → derive T(x::Int128, z::Int128) @upsert

           AFTER:
               Logical
                   R(x::Int128, y::Int128)
                   S(y::Int128, z::Int128)
                   → derive _loopy_update_intermediate_1(x::Int128, z::Int128) @assign

               Logical
                   _loopy_update_intermediate_1(x::Int128, z::Int128)
                   → derive T(x::Int128, z::Int128) @upsert

    3. **Recursive Assignment Decoupling**: Decouples self-referential assignments where the
       head relation appears in the body by introducing a copy relation. This transformation
       is required for BackIR analysis compatibility.

       Example (Metamodel IR):
           BEFORE:
               Logical
                   iter(i::Int128)
                   rel_primitive_int128_add(i::Int128, 1::Int128, i_plus_1::Int128)
                   → derive iter(i_plus_1::Int128) @assign

           AFTER:
               Logical
                   iter(i::Int128)
                   → derive _loopy_iter_copy_1(i::Int128) @assign

               Logical
                   _loopy_iter_copy_1(i::Int128)
                   rel_primitive_int128_add(i::Int128, 1::Int128, i_plus_1::Int128)
                   → derive iter(i_plus_1::Int128) @assign
    """
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        # Find all nested logical intermediates
        intermediate_finder = FindIntermediates()
        model.accept(intermediate_finder)

        intermediate_analyzer = AnalyzeIntermediateUse(set(intermediate_finder.intermediates.keys()))
        model.accept(intermediate_analyzer)

        # Determine which intermediates to move and which to remove
        uses_intermediates: dict[Union[ir.Logical, ir.Break], set[ir.Logical]] = defaultdict(set)
        remove_declarations: set[ir.Logical] = set()
        for rel, decl in intermediate_finder.intermediates.items():
            if rel not in intermediate_analyzer.used_outside_algorithm:
                remove_declarations.add(decl)
            for instr in intermediate_analyzer.used_in_alg_instruction[rel]:
                uses_intermediates[instr].add(decl)

        # Rescope intermediates
        rescoper = IntermediateRescoper(uses_intermediates, remove_declarations)
        model = rescoper.walk(model)

        # Normalize Loopy updates
        normalizer = UpdateNormalizer()
        model = normalizer.walk(model)

        # Decompose recursive assignments
        decomposer = RecursiveAssignmentDecoupling()
        model = decomposer.walk(model)

        return model

class FindIntermediates(Visitor):
    """
    Gathers all `_nested_logical.*` intermediates defined in a Logical scope (where order
    doesn't matter); in particular DOES NOT gather any intermediates declared in the scope
    of a Sequence.
    """
    def __init__(self):
        self.intermediates: dict[ir.Relation, ir.Logical] = dict()
        self._inside_algorithm: bool = False

    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]):
        if is_logical_instruction(node):
            heads = get_instruction_head_rels(node)
            for rel in heads:
                if rel.name.startswith("_nested_logical"):
                    self.intermediates[rel] = node
        else:
            super().visit_logical(node, parent)

    def visit_sequence(self, node: ir.Sequence, parent: Optional[ir.Node]):
        if is_algorithm_script(node):
            self._inside_algorithm = True
        super().visit_sequence(node, parent)
        if is_algorithm_script(node):
            self._inside_algorithm = False


class AnalyzeIntermediateUse(Visitor):
    """
    Identifies, for each nested logical intermediate, the algorithm instructions that
    use it. Additionally, determines whether the intermediate is used anywhere
    outside of an algorithm.
    """
    def __init__(self, intermediate_relations: set[ir.Relation]):
        self.intermediates = intermediate_relations
        self.used_in_algorithm: set[ir.Relation] = set()
        self.used_in_alg_instruction: dict[ir.Relation, set[Union[ir.Logical, ir.Break]]] = {rel: set() for rel in intermediate_relations}
        self.used_outside_algorithm: set[ir.Relation] = set()

        self._current_algorithm: Optional[ir.Sequence] = None

    def register_use(self, instr: Union[ir.Logical, ir.Break], uses_intermediates: set[ir.Relation]):
        # this instruction uses intermediates
        if self._current_algorithm is not None:
            # instruction is inside an algorithm
            for rel in uses_intermediates:
                self.used_in_algorithm.add(rel)
                self.used_in_alg_instruction[rel].add(instr)
        else:
            self.used_outside_algorithm.update(uses_intermediates)

    def visit_break(self, node: ir.Break, parent: Optional[ir.Node]):
        lookups = collect_by_type(ir.Lookup, node)
        lookup_rels = {lookup.relation for lookup in lookups}
        uses_intermediates = lookup_rels.intersection(self.intermediates)
        self.register_use(node, uses_intermediates)
        super().visit_break(node, parent)

    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]):
        if is_logical_instruction(node):
            body = get_instruction_body_rels(node)
            uses_intermediates = body.intersection(self.intermediates)
            self.register_use(node, uses_intermediates)
        else:
            super().visit_logical(node, parent)

    def visit_sequence(self, node: ir.Sequence, parent: Optional[ir.Node]):
        if is_algorithm_script(node):
            self._current_algorithm = node
        super().visit_sequence(node, parent)
        if is_algorithm_script(node):
            self._current_algorithm = None

class IntermediateRescoper(Rewriter):
    """
    Moves nested logical intermediates used in algorithm instructions from the logical scope
    to any algorithm using the instruction before every instruction that uses them. Removes
    an intermediate from the logical scope if it is not used anywhere else.

    * `uses_intermediates`: a mapping from algorithm instructions to the set of nested logical
      intermediates they use.
    * `remove_declarations`: the set of nested logical intermediates to remove from the
      logical scope because they are not used anywhere else.
    """
    def __init__(self,
                 uses_intermediates: dict[Union[ir.Logical, ir.Break], set[ir.Logical]],
                 remove_declarations: set[ir.Logical]):
        super().__init__()
        self.uses_intermediates = uses_intermediates
        self.remove_declarations = remove_declarations

    def handle_logical(self, node: ir.Logical, parent: ir.Node) -> ir.Logical:
        body = []
        for child in node.body:
            if child in self.remove_declarations:
                continue
            child = self.walk(child, node)
            body.append(child)
        return node.reconstruct(node.engine, node.hoisted, tuple(body), node.annotations)

    def handle_sequence(self, node: ir.Sequence, parent: ir.Node) -> ir.Sequence:
        tasks = []
        for child in node.tasks:
            if child in self.uses_intermediates:
                assert isinstance(child, (ir.Logical, ir.Break))
                for intermediate in self.uses_intermediates[child]:
                    tasks.append(mk_assign(intermediate))
            child = self.walk(child, node)
            tasks.append(child)
        return node.reconstruct(node.engine, node.hoisted, tuple(tasks), node.annotations)

class UpdateNormalizer(Rewriter):
    """
    This pass normalizes Loopy Update operations (upsert, monoid, and monus) to use a single
    atom in their body. For any Update operation with more complex body, it introduces a new
    intermediate relation to hold the body results.
    """
    def __init__(self):
        super().__init__()
        self._inside_algorithm: bool = False
        self._intermediate_counter: int = 0

    # Tests if the given Update operation requires normalization
    # * the body has more than one Lookup operation, or
    # * the body has other tasks than Lookup and Update
    def _requires_update_normalization(self, update: ir.Task) -> bool:
        if not isinstance(update, ir.Logical):
            return False
        if not is_update_instruction(update):
            return False
        _, lookups, others = split_instruction(update)
        return len(lookups) > 1 or len(others) > 0

    def handle_sequence(self, node: ir.Sequence, parent: ir.Node) -> ir.Sequence:
        if is_algorithm_script(node):
            self._inside_algorithm = True

        if self._inside_algorithm:
            new_tasks = []
            for task in node.tasks:
                if self._requires_update_normalization(task):
                    assert isinstance(task, ir.Logical)
                    intermediate, normalized_update = self._normalize_update_instruction(task)
                    new_tasks.extend((intermediate, normalized_update))
                else:
                    new_tasks.append(self.walk(task, node))
            result = node.reconstruct(node.engine, node.hoisted, tuple(new_tasks), node.annotations)
        else:
            result = super().handle_sequence(node, parent)

        if is_algorithm_script(node):
            self._inside_algorithm = False

        return result

    def _normalize_update_instruction(self, update_instr: ir.Logical) -> tuple[ir.Logical, ir.Logical]:
        update, lookups, others = split_instruction(update_instr)
        normalized_update = []

        var_list = helpers.vars(update.args)

        intermediate_rel = factory.relation(
            self._fresh_intermediate_name(), [
                factory.field(f"arg_{i}", var.type) for i, var in enumerate(var_list)
            ]
        )

        intermediate_derive = factory.derive(intermediate_rel, var_list)
        intermediate_logical = mk_assign(factory.logical(
            engine=update_instr.engine,
            hoisted=update_instr.hoisted,
            body=(*lookups, *others, intermediate_derive),
            annos=list(update_instr.annotations)
        ))
        assert isinstance(intermediate_logical, ir.Logical)

        intermediate_lookup = factory.lookup(
            intermediate_rel,
            var_list
        )

        normalized_update = factory.logical(
            engine=update_instr.engine,
            hoisted=update_instr.hoisted,
            body=(intermediate_lookup, update),
            annos=list(update_instr.annotations)
        )

        return (intermediate_logical, normalized_update)

    def _fresh_intermediate_name(self) -> str:
        self._intermediate_counter += 1
        return f"_loopy_update_intermediate_{self._intermediate_counter}"

class RecursiveAssignmentDecoupling(Rewriter):
    """
    Decouples assignments whose definition is "recursive", i.e., the body contain the head
    e.g., `assign iter = iter + 1`. Currently, BackIR analysis cannot handle properly such
    assignments. Such assignments are decoupled by introducing a new intermediate copy
    relation; in the example above, `assign iter_copy = iter; assign iter = iter_copy + 1`.
    The performance is not affected because the backend can identify the new assignment as a
    copy operation and the execution will not lead to materialization of the intermediate
    relation.
    """
    def __init__(self):
        super().__init__()
        self._intermediate_copy_counter: int = 0
        # control of head_rel -> copy_rel substitution in traversal
        self._perform_substitution: bool = False
        self._head_rel: Optional[ir.Relation] = None
        self._copy_rel: Optional[ir.Relation] = None

    def _fresh_copy_rel_name(self, rel_name:str) -> str:
        self._intermediate_copy_counter += 1
        return f"_loopy_{rel_name}_copy_{self._intermediate_copy_counter}"

    def handle_sequence(self, node: ir.Sequence, parent: ir.Node) -> ir.Sequence:
        if is_script(node):
            new_tasks = []
            for task in node.tasks:
                if self._is_recursive_assignment(task):
                    assert isinstance(task, ir.Logical)
                    intermediate_copy, decomposed_assign = self._decouple_recursive_assignment(task, parent)
                    new_tasks.extend((intermediate_copy, decomposed_assign))
                else:
                    new_tasks.append(self.walk(task, node))
            return node.reconstruct(node.engine, node.hoisted, tuple(new_tasks), node.annotations)
        else:
            return super().handle_sequence(node, parent)

    def _is_recursive_assignment(self, task: ir.Task) -> TypeGuard[ir.Logical]:
        if is_logical_instruction(task):
            heads = get_instruction_head_rels(task)
            body = get_instruction_body_rels(task)
            return len(body & heads) > 0
        return False

    def _decouple_recursive_assignment(self, rule: ir.Logical, parent: ir.Node) -> tuple[ir.Logical, ir.Logical]:
        # we have `assign rel(x,...) = ..., rel(y,...), ...`
        update, _, _ = split_instruction(rule)
        self._head_rel = update.relation

        copy_rel_name = self._fresh_copy_rel_name(self._head_rel.name)

        self._copy_rel = factory.relation(copy_rel_name, list(self._head_rel.fields))
        # build `assign copy_rel(x,...) = rel(x,...)`
        copy_rule = cast(ir.Logical, mk_assign(
            factory.logical([
                factory.lookup(self._head_rel,update.args),
                factory.update(self._copy_rel, update.args, update.effect)
            ])
        ))

        # build `assign rel(x,...) = ..., copy_rel(y,...), ...``
        self._perform_substitution = True
        rewritten_rule = self.walk(rule, parent)
        self._perform_substitution = False

        self._head_rel = None
        self._copy_rel = None

        return (copy_rule, rewritten_rule)

    def handle_lookup(self, node: ir.Lookup, parent: ir.Node) -> ir.Lookup:
        if self._perform_substitution and node.relation == self._head_rel:
            assert self._copy_rel is not None
            return factory.lookup(self._copy_rel, node.args)
        return super().handle_lookup(node, parent)
