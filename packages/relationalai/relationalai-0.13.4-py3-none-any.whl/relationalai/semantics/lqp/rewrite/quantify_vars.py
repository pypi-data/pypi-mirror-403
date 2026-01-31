from __future__ import annotations

from relationalai.semantics.metamodel import ir, factory as f, helpers
from relationalai.semantics.metamodel.compiler import Pass
from relationalai.semantics.metamodel.visitor import Visitor, Rewriter
from relationalai.semantics.metamodel.util import OrderedSet, ordered_set
from typing import Optional, Any, Tuple, Iterable
from .functional_dependencies import contains_only_declarable_constraints

class QuantifyVars(Pass):
    """
    Introduce existential quantifiers as closely as possible to the affected sub-tasks.
    """

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        var_info = VarScopeInfo()
        model.root.accept(var_info)
        quant_nodes = FindQuantificationNodes(var_info)
        model.root.accept(quant_nodes)
        return QuantifyVarsRewriter(quant_nodes).walk(model)

def _ignored_vars(node: ir.Logical|ir.Not):
    if isinstance(node, ir.Not):
        return ordered_set()

    vars_to_ignore = ordered_set()
    for task in node.body:
        if isinstance(task, ir.Output):
            # Vars that are output don't need to be quantified.
            vars_to_ignore.update(helpers.output_vars(task.aliases))

        elif isinstance(task, ir.Update):
            # Vars that are in effects don't need to be quantified.
            vars_to_ignore.update(helpers.vars(task.args))

        elif isinstance(task, ir.Aggregate):
            # Variables that are inputs to an aggregate don't need to be quantified.
            for var in helpers.vars(task.args):
                if helpers.is_aggregate_input(var, task):
                    vars_to_ignore.add(var)
            # Variables that are in the projections, and not in the group-by, don't need to be quantified.
            for var in task.projection:
                if var not in task.group:
                    vars_to_ignore.add(var)

        elif isinstance(task, ir.Rank):
            # Variables that are keys, and not in the group-by, don't need to be quantified.
            for var in task.args + task.projection:
                if var not in task.group:
                    vars_to_ignore.add(var)

    return vars_to_ignore

class VarScopeInfo(Visitor):
    """
    Compute which variables are still in scope for a given node.
    Those variables will be potentially quantified in this node.
    """

    # Keep track of variables that are still in scope for a given node.
    # Variables are introduced into scope in Var nodes and then propagated upwards.
    # The propagation stops when:
    # 1. They are explicitly quantified, or
    # 2. A node that needs to quantify them is identified.
    #    That node will be the top-most node that still has them in scope.
    _vars_in_scope: dict[int, OrderedSet[ir.Var]]

    IGNORED_NODES = (ir.Type,
                    ir.Var, ir.Literal, ir.Relation, ir.Field,
                    ir.Default, ir.Output, ir.Update, ir.Aggregate,
                    ir.Check, ir.Require,
                    ir.Annotation, ir.Rank, ir.Break)

    def __init__(self):
        super().__init__()
        self._vars_in_scope = {}

    def leave(self, node: ir.Node, parent: Optional[ir.Node]=None):
        if contains_only_declarable_constraints(node):
            return node

        if isinstance(node, ir.Lookup):
            self._record(node, helpers.vars(node.args))

        elif isinstance(node, ir.Data):
            self._record(node, helpers.vars(node.vars))

        elif isinstance(node, ir.Construct):
            self._record(node, helpers.vars(node.values))
            self._record(node, [node.id_var])

        elif isinstance(node, ir.Exists) or isinstance(node, ir.ForAll):
            # Exists and ForAll inherit the vars in scope from their sub-task,
            # but then remove the vars they quantify over.
            scope_vars = self._vars_in_scope.get(node.task.id, None)
            if scope_vars:
                scope_vars.difference_update(node.vars)
                self._record(node, scope_vars)

        elif isinstance(node, ir.Not):
            # Not inherits the vars in scope from its sub-task.
            scope_vars = self._vars_in_scope.get(node.task.id, None)
            self._record(node, scope_vars)

        elif isinstance(node, (ir.Match, ir.Union)):
            # Match/Union only inherits vars if they are in scope for all sub-tasks.
            scope_vars = ordered_set()
            # Prime the search with the first sub-task's vars.
            if node.tasks:
                scope_vars.update(self._vars_in_scope.get(node.tasks[0].id, None))

            for task in node.tasks:
                sub_scope_vars = self._vars_in_scope.get(task.id, None)
                if not scope_vars or not sub_scope_vars:
                    scope_vars = ordered_set()
                    break
                scope_vars = (scope_vars & sub_scope_vars)

            # Hoisted vars are not considered for quantification at this level.
            scope_vars.difference_update(helpers.hoisted_vars(node.hoisted))
            self._record(node, scope_vars)

        elif isinstance(node, (ir.Loop, ir.Sequence)):
            # Variables in Loops and Sequences are scoped exclusively within the body and
            # not propagated outside. No need to record any variables, as they shouldn't be
            # in scope for the node itself
            pass

        elif isinstance(node, ir.Logical):
            self._do_logical(node)

        else:
            assert isinstance(node, self.IGNORED_NODES), f"Unexpected node kind ({node.kind}) -> {node}"

        return node

    def _do_logical(self, node: ir.Logical):
        ignored_vars = _ignored_vars(node)

        scope_vars = ordered_set()
        all_nested_vars = ordered_set()
        output_vars = ordered_set()

        # Collect variables nested in child Logical and Not nodes
        nested_vars_in_task: dict[ir.Var, int] = dict()

        # Collect all variables from logical sub-tasks
        for task in node.body:
            if isinstance(task, ir.Output):
                output_vars.update(helpers.output_vars(task.aliases))

            if isinstance(task, (ir.Aggregate, ir.Rank)):
                # Variables that are in the group-by, and not in the projections, can come into scope.
                for var in task.group:
                    if var not in task.args:
                        scope_vars.add(var)
                continue

            # Hoisted variables from sub-tasks are brought again into scope.
            if isinstance(task, (ir.Logical, ir.Union, ir.Match)):
                scope_vars.update(helpers.hoisted_vars(task.hoisted))

            # Get variables in sub-task scope
            sub_scope_vars = self._vars_in_scope.get(task.id, ordered_set())

            if isinstance(task, ir.Logical):
                # Logical child nodes should have their nested variables quantified
                # only if they are needed in more than one child task.
                for var in sub_scope_vars:
                    if var not in nested_vars_in_task:
                        nested_vars_in_task[var] = 0
                    nested_vars_in_task[var] += 1
            elif not isinstance(task, ir.Not):
                # Other nodes with nested variables need to be quantified at this level
                scope_vars.update(sub_scope_vars)

        for v, c in nested_vars_in_task.items():
            # If the variable appears in more than one nested child, then it needs to be
            # quantified here. Otherwise, it will be handled in the child node
            if c > 1:
                all_nested_vars.add(v)

        # Nested variables also need to be introduced, provided they are not output variables.
        for var in all_nested_vars:
            if var not in output_vars:
                scope_vars.add(var)

        if scope_vars:
            scope_vars.difference_update(ignored_vars)
            # Hoisted vars are not considered for quantification at this level.
            scope_vars.difference_update(helpers.hoisted_vars(node.hoisted))
            self._record(node, scope_vars)

    def _record(self, node: ir.Node, vars: Iterable[ir.Var]|None):
        if not vars:
            return
        if node.id not in self._vars_in_scope:
            self._vars_in_scope[node.id] = ordered_set()
        self._vars_in_scope[node.id].update(vars)

class FindQuantificationNodes(Visitor):
    """
    Find the top-most nodes that need to quantify a variable.
    The same variable may be quantified at different points assuming they are not parent/child.
    E.g.,
    Logical
        Exists(x)
            ...
    Logical
        Exists(x, y)
            ...
    """

    node_quantifies_vars: dict[int, OrderedSet[ir.Var]]

    def __init__(self, var_info: VarScopeInfo):
        super().__init__()
        self._vars_in_scope = var_info._vars_in_scope
        self.handled_vars: dict[int, OrderedSet[ir.Var]] = {}
        self.node_quantifies_vars = {}

    def enter(self, node: ir.Node, parent: Optional[ir.Node]=None) -> "Visitor":
        if contains_only_declarable_constraints(node):
            return self

        handled_vars = self.handled_vars.get(parent.id, ordered_set()) if parent else ordered_set()
        # Clone the set to avoid modifying parent's handled vars
        handled_vars = OrderedSet.from_iterable(handled_vars)

        if isinstance(node, (ir.Logical, ir.Not)):
            ignored_vars = _ignored_vars(node)
            handled_vars.update(ignored_vars)

            scope_vars = self._vars_in_scope.get(node.id, None)
            if scope_vars:
                scope_vars.difference_update(handled_vars)
                if scope_vars:
                    handled_vars.update(scope_vars)
                    self.node_quantifies_vars[node.id] = scope_vars

        self.handled_vars[node.id] = handled_vars
        return self

class QuantifyVarsRewriter(Rewriter):
    """
    Rewrite the model to quantify variables as closely as possible to the affected sub-tasks.
    """

    def __init__(self, quant: FindQuantificationNodes):
        super().__init__()
        self.node_quantifies_vars = quant.node_quantifies_vars

    def handle_logical(self, node: ir.Logical, parent: ir.Node, ctx:Optional[Any]=None) -> ir.Logical:
        if contains_only_declarable_constraints(node):
            return node

        new_body = self.walk_list(node.body, node)

        if node.id in self.node_quantifies_vars:
            vars = self.node_quantifies_vars[node.id]
            effect_tasks = []
            inner_tasks = []
            agg_or_rank_tasks = []
            for task in new_body:
                if isinstance(task, ir.Output):
                    effect_tasks.append(task)

                elif isinstance(task, ir.Update):
                    effect_tasks.append(task)

                elif isinstance(task, (ir.Aggregate, ir.Rank)):
                    # TODO: QB shouldn't generate multiple aggregate tasks, but unit tests written
                    # in IR directly may do so and the flatten pass doesn't split them yet.
                    if len(agg_or_rank_tasks) > 0:
                        print(f"Multiple aggregate/rank tasks found: {agg_or_rank_tasks} and {task}")
                    # If the agg/rank depends on any of the vars being quantified here,
                    # then it needs to be inside the quantification
                    if any(var in helpers.vars(task.projection) for var in vars):
                        inner_tasks.append(task)
                    else:
                        agg_or_rank_tasks.append(task)

                else:
                    inner_tasks.append(task)

            if vars:
                var_list = list(vars)
                var_list.sort(key=lambda var: var.name)
                if len(inner_tasks) == 1 and isinstance(inner_tasks[0], ir.Logical):
                    body = f.exists(var_list, inner_tasks[0])
                else:
                    body = f.exists(var_list, f.logical(inner_tasks))
                # If the logical is describing an aggregate/rank, confine the existential to
                # the aggregate/rank's body, by wrapping it in another logical.
                if agg_or_rank_tasks:
                    body = f.logical([body, *agg_or_rank_tasks])
                return f.logical([body, *effect_tasks], node.hoisted)

        return node if self._eq_tasks(node.body, new_body) else f.logical(new_body, node.hoisted)

    def handle_not(self, node: ir.Not, parent: ir.Node, ctx:Optional[Any]=None) -> ir.Not:
        new_task = self.walk(node.task)

        if node.id in self.node_quantifies_vars:
            vars = self.node_quantifies_vars[node.id]
            return f.not_(f.exists(list(vars), new_task))

        return node if node.task is new_task else f.not_(new_task)

    def handle_union(self, node: ir.Union, parent: ir.Node, ctx:Optional[Any]=None) -> ir.Union:
        if not node.tasks:
            return node

        new_tasks = self.walk_list(node.tasks, node)
        return node if node.tasks is new_tasks else f.union(
            tasks = new_tasks,
            hoisted = node.hoisted,
        )

    # To avoid unnecessary cloning of vars in the visitor.
    def handle_var(self, node: ir.Var, parent: ir.Node, ctx:Optional[Any]=None) -> ir.Var:
        return node

    def _eq_tasks(self, xs: Tuple[ir.Task, ...], ys: Tuple[ir.Task, ...]) -> bool:
        if len(xs) != len(ys):
            return False
        for x, y in zip(xs, ys):
            if x is not y:
                return False
        return True
