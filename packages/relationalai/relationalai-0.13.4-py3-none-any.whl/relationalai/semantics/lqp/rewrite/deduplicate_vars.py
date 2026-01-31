from relationalai.semantics.metamodel.compiler import Pass
from relationalai.semantics.metamodel import ir, builtins as rel_builtins, factory as f, visitor
from relationalai.semantics.metamodel import helpers
from relationalai.semantics.metamodel.util import FrozenOrderedSet

from relationalai.semantics.lqp.utils import output_names

from typing import List, Sequence, Tuple, Union

# Deduplicate Vars in Updates and Outputs.
class DeduplicateVars(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        r = self.VarDeduplicator()
        return r.walk(model)

    # Return 1) a new list of Values with no duplicates (at the object level) and
    # 2) equalities between any original Value and a deduplicated Value.
    @staticmethod
    def dedup_values(vals: Sequence[ir.Value]) -> Tuple[List[ir.Value], List[ir.Lookup]]:
        # If a var is seen more than once, it is a duplicate and we will create
        # a new Var and equate it with the seen one.
        seen_vars = set()

        new_vals = []
        eqs = []

        for i, val in enumerate(vals):
            # Duplicates can only occur within Vars.
            # TODO: we don't know for sure if these are the only relevant cases.
            if isinstance(val, ir.Default) or isinstance(val, ir.Var):
                var = val if isinstance(val, ir.Var) else val.var
                if var in seen_vars:
                    new_var = ir.Var(var.type, var.name + "_dup_" + str(i))
                    new_val = new_var if isinstance(val, ir.Var) else ir.Default(new_var, val.value)
                    new_vals.append(new_val)
                    eqs.append(f.lookup(rel_builtins.eq, [new_var, var]))
                else:
                    seen_vars.add(var)
                    new_vals.append(val)
            else:
                # No possibility of problematic duplication.
                new_vals.append(val)

        return new_vals, eqs

    # Returns a reconstructed output with no duplicate variable objects
    # (dedup_values) and now necessary equalities between any two previously
    # duplicate variables.
    @staticmethod
    def dedup_output(output: ir.Output) -> List[Union[ir.Output, ir.Lookup]]:
        vals = helpers.output_values(output.aliases)
        deduped_vals, req_lookups = DeduplicateVars.dedup_values(vals)
        # Need the names so we can recombine.
        alias_names = output_names(output.aliases)
        new_output = ir.Output(
            output.engine,
            FrozenOrderedSet(list(zip(alias_names, deduped_vals))),
            output.keys,
            output.annotations,
        )
        return req_lookups + [new_output]

    # Returns a replacement update with no duplicate variable objects
    # (dedup_values) and now necessary equalities between any two previously
    # duplicate variables.
    @staticmethod
    def dedup_update(update: ir.Update) -> List[Union[ir.Update, ir.Lookup]]:
        deduped_vals, req_lookups = DeduplicateVars.dedup_values(update.args)
        new_update = ir.Update(
            update.engine,
            update.relation,
            tuple(deduped_vals),
            update.effect,
            update.annotations,
        )
        return req_lookups + [new_update]

    # Does the actual work.
    class VarDeduplicator(visitor.Rewriter):
        def __init__(self):
            super().__init__()

        # We implement handle_logical instead of handle_update/handle_output
        # because in addition to modifying said update/output we require new
        # lookups (equality between original and deduplicated variables).
        def handle_logical(self, node: ir.Logical, parent: ir.Node):
            # In order to recurse over subtasks.
            node = super().handle_logical(node, parent)

            new_body = []
            for subtask in node.body:
                if isinstance(subtask, ir.Output):
                    new_body.extend(DeduplicateVars.dedup_output(subtask))
                elif isinstance(subtask, ir.Update):
                    new_body.extend(DeduplicateVars.dedup_update(subtask))
                else:
                    new_body.append(subtask)

            return ir.Logical(
                node.engine,
                node.hoisted,
                tuple(new_body),
                node.annotations
            )
