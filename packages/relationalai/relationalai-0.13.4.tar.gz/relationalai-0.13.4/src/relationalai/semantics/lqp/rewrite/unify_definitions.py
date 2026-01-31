from relationalai.semantics.metamodel.compiler import Pass
from relationalai.semantics.metamodel import ir, builtins as rel_builtins, factory as f, visitor
from relationalai.semantics.metamodel.typer import typer
from relationalai.semantics.metamodel import helpers
from relationalai.semantics.metamodel.util import FrozenOrderedSet, OrderedSet


from typing import cast, Union, Optional, Iterable
from collections import defaultdict

# LQP does not support multiple definitions for the same relation. This pass unifies all
# definitions for each relation into a single definition using a union.
class UnifyDefinitions(Pass):
    def __init__(self):
        super().__init__()

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        # Maintain a cache of renamings for each relation. These need to be consistent
        # across all definitions of the same relation.
        self.renamed_relation_args: dict[Union[ir.Value, ir.Relation], list[ir.Var]] = {}

        root = cast(ir.Logical, model.root)
        new_tasks = self.get_combined_multidefs(root)
        return ir.Model(
            model.engines,
            model.relations,
            model.types,
            f.logical(
                tuple(new_tasks),
                root.hoisted,
                root.engine,
            ),
            model.annotations,
        )

    def _get_heads(self, logical: ir.Logical) -> list[Union[ir.Update, ir.Output]]:
        derives = []
        for task in logical.body:
            if isinstance(task, ir.Update) and task.effect == ir.Effect.derive:
                derives.append(task)
            elif isinstance(task, ir.Output):
                derives.append(task)
        return derives

    def _get_non_heads(self, logical: ir.Logical) -> list[ir.Task]:
        non_derives = []
        for task in logical.body:
            if not(isinstance(task, ir.Update) and task.effect == ir.Effect.derive) and not isinstance(task, ir.Output):
                non_derives.append(task)
        return non_derives

    def _get_head_identifier(self, head: Union[ir.Update, ir.Output]) -> Optional[ir.Value]:
        if isinstance(head, ir.Update):
            return head.relation
        else:
            assert isinstance(head, ir.Output)
            if len(head.aliases) <= 2:
                # For processing here, we need output to have at least the column markers
                # `cols` and `col`, and also a key
                return None

            output_alias_names = helpers.output_alias_names(head.aliases)
            output_vals = helpers.output_values(head.aliases)

            # For normal outputs, the pattern is output[keys](cols, "col000" as 'col', ...)
            if output_alias_names[0] == "cols" and output_alias_names[1] == "col":
                return output_vals[1]

            # For exports, the pattern is output[keys]("col000" as 'col', ...)
            if helpers.is_export(head):
                if output_alias_names[0] == "col":
                    return output_vals[0]

        return None

    def get_combined_multidefs(self, root: ir.Logical) -> list[ir.Logical]:
        # Step 1: Group tasks by the relation they define.
        relation_to_tasks: dict[Union[None, ir.Value, ir.Relation], list[ir.Logical]] = defaultdict(list)

        for task in root.body:
            task = cast(ir.Logical, task)
            task_heads = self._get_heads(task)

            # Some relations do not need to be grouped, e.g., if they don't contain a
            # derive. Use `None` as a placeholder key for these cases.
            if len(task_heads) != 1:
                relation_to_tasks[None].append(task)
                continue

            head_id = self._get_head_identifier(task_heads[0])
            relation_to_tasks[head_id].append(task)

        # Step 2: For each relation, combine all of the body definitions into a union.
        result_tasks = []
        for relation, tasks in relation_to_tasks.items():
            # If there's only one task for the relation, or if grouping is not needed, then
            # just keep the original tasks.
            if len(tasks) == 1 or relation is None:
                result_tasks.extend(tasks)
                continue

            result_tasks.append(self._combine_tasks_into_union(tasks))
        return result_tasks

    def _get_variable_mapping(self, logical: ir.Logical) -> dict[ir.Value, ir.Var]:
        heads = self._get_heads(logical)
        assert len(heads) == 1, "should only have one head in a logical at this stage"
        head = heads[0]

        var_mapping = {}
        head_id = self._get_head_identifier(head)

        if isinstance(head, ir.Update):
            args_for_renaming = head.args
        else:
            assert isinstance(head, ir.Output)
            output_alias_names = helpers.output_alias_names(head.aliases)
            if output_alias_names[0] == "cols" and output_alias_names[1] == "col":
                assert len(head.aliases) > 2

                # For outputs, we do not need to rename the `cols` and `col` markers or the
                # keys.
                output_values = helpers.output_values(head.aliases)[2:]

            else:
                assert helpers.is_export(head) and output_alias_names[0] == "col"
                assert len(head.aliases) > 1

                # For exports, we do not need to rename the `col` marker or the keys.
                output_values = helpers.output_values(head.aliases)[1:]

            args_for_renaming = []
            for v in output_values:
                if head.keys and isinstance(v, ir.Var) and v in head.keys:
                    continue
                args_for_renaming.append(v)

        if head_id not in self.renamed_relation_args:
            renamed_vars = []
            for (i, arg) in enumerate(args_for_renaming):
                typ = typer.to_type(arg)
                assert arg not in var_mapping, "args of update should be unique"
                if isinstance(arg, ir.Var):
                    var_mapping[arg] = ir.Var(typ, arg.name)
                else:
                    var_mapping[arg] = ir.Var(typ, f"arg_{i}")

                renamed_vars.append(var_mapping[arg])
            self.renamed_relation_args[head_id] = renamed_vars
        else:
            for (arg, var) in zip(args_for_renaming, self.renamed_relation_args[head_id]):
                var_mapping[arg] = var

        return var_mapping

    def _rename_variables(self, logical: ir.Logical) -> ir.Logical:
        class RenameVisitor(visitor.Rewriter):
            def __init__(self, var_mapping: dict[ir.Value, ir.Var]):
                super().__init__()
                self.var_mapping = var_mapping

            def _get_mapped_value(self, val: ir.Value) -> ir.Value:
                if isinstance(val, tuple):
                    return tuple(self._get_mapped_value(t) for t in val)
                return self.var_mapping.get(val, val)

            def _get_mapped_values(self, vals: Iterable[ir.Value]) -> list[ir.Value]:
                return [self._get_mapped_value(v) for v in vals]

            def handle_var(self, node: ir.Var, parent: ir.Node) -> ir.Var:
                return self.var_mapping.get(node, node)

            # TODO: ideally, extend the rewriter class to allow rewriting PyValue to Var so
            # we don't need to separately handle all cases containing them.
            def handle_update(self, node: ir.Update, parent: ir.Node) -> ir.Update:
                return ir.Update(
                    node.engine,
                    node.relation,
                    tuple(self._get_mapped_values(node.args)),
                    node.effect,
                    node.annotations,
                )

            def handle_lookup(self, node: ir.Lookup, parent: ir.Node) -> ir.Lookup:
                return ir.Lookup(
                    node.engine,
                    node.relation,
                    tuple(self._get_mapped_values(node.args)),
                    node.annotations,
                )

            def handle_output(self, node: ir.Output, parent: ir.Node) -> ir.Output:
                new_aliases = FrozenOrderedSet(
                    [(name, self._get_mapped_value(value)) for name, value in node.aliases]
                )
                if node.keys:
                    new_keys = FrozenOrderedSet(
                        [self.var_mapping.get(key, key) for key in node.keys]
                    )
                else:
                    new_keys = node.keys

                return ir.Output(
                    node.engine,
                    new_aliases,
                    new_keys,
                    node.annotations,
                )

            def handle_construct(self, node: ir.Construct, parent: ir.Node) -> ir.Construct:
                new_values = tuple(self._get_mapped_values(node.values))
                new_id_var = self.var_mapping.get(node.id_var, node.id_var)
                return ir.Construct(
                    node.engine,
                    new_values,
                    new_id_var,
                    node.annotations,
                )

            def handle_aggregate(self, node: ir.Aggregate, parent: ir.Node) -> ir.Aggregate:
                new_projection = tuple(self.var_mapping.get(arg, arg) for arg in node.projection)
                new_group = tuple(self.var_mapping.get(arg, arg) for arg in node.group)
                new_args = tuple(self._get_mapped_values(node.args))
                return ir.Aggregate(
                    node.engine,
                    node.aggregation,
                    new_projection,
                    new_group,
                    new_args,
                    node.annotations,
                )

            def handle_rank(self, node: ir.Rank, parent: ir.Node) -> ir.Rank:
                new_projection = tuple(self.var_mapping.get(arg, arg) for arg in node.projection)
                new_group = tuple(self.var_mapping.get(arg, arg) for arg in node.group)
                new_args = tuple(self.var_mapping.get(arg, arg) for arg in node.args)
                new_result = self.var_mapping.get(node.result, node.result)

                return ir.Rank(
                    node.engine,
                    new_projection,
                    new_group,
                    new_args,
                    node.arg_is_ascending,
                    new_result,
                    node.limit,
                    node.annotations,
                )

        var_mapping = self._get_variable_mapping(logical)

        renamer = RenameVisitor(var_mapping)
        result = renamer.walk(logical)

        # Also need to append the equality for each renamed constant. E.g., if the mapping
        # contains (50.0::FLOAT -> arg_2::FLOAT), we need to add
        # `eq(arg_2::FLOAT, 50.0::FLOAT)` to the result.
        value_eqs = []
        for (old_var, new_var) in var_mapping.items():
            if not isinstance(old_var, ir.Var):
                value_eqs.append(f.lookup(rel_builtins.eq, [new_var, old_var]))

        return ir.Logical(
            result.engine,
            result.hoisted,
            tuple(value_eqs) + tuple(result.body),
            result.annotations,
        )

    # This function is the main workhorse for this rewrite pass. It takes a list of tasks
    # that define the same relation, and combines them into a single task that defines
    # the relation using a union of all of the bodies.
    def _combine_tasks_into_union(self, tasks: list[ir.Logical]) -> ir.Logical:
        # Step 1: Rename the variables in all tasks so that they will match the final derive
        # after reconstructing into a union
        renamed_tasks = [self._rename_variables(task) for task in tasks]

        # Step 2: Get the final derive
        derives = self._get_heads(renamed_tasks[0])
        assert len(derives) == 1, "should only have one derive in a logical at this stage"
        # Also make sure that all the derives are the same. This should be the case because
        # we renamed all the variables to be the same in step 1.
        for task in renamed_tasks[1:]:
            assert self._get_heads(task) == derives, "all derives should be the same"

        derive = derives[0]

        # Step 3: Remove the final `derive` from each task
        renamed_task_bodies = [
            f.logical(
                tuple(self._get_non_heads(t)),  # Only keep non-head tasks
                t.hoisted,
                t.engine,
            )
            for t in renamed_tasks
        ]

        # Deduplicate bodies
        renamed_task_bodies = OrderedSet.from_iterable(renamed_task_bodies).get_list()

        # Step 4: Construct a union of all the task bodies
        if len(renamed_task_bodies) == 1:
            # If there's only one body after deduplication, no need to create a union
            new_body = renamed_task_bodies[0]
        else:
            new_body = f.union(
                tuple(renamed_task_bodies),
                [],
                renamed_tasks[0].engine,
            )

        # Step 5: Add the final derive back
        return f.logical(
            (new_body, derive),
            [],
            renamed_tasks[0].engine,
        )
