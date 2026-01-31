from relationalai.semantics.metamodel.compiler import Pass
from relationalai.semantics.metamodel import ir, builtins as rel_builtins, factory as f, visitor
from relationalai.semantics.metamodel.typer import typer

from typing import List, Sequence, Tuple, Union

# Rewrite constants to vars in Updates. This results in a more normalized format where
# updates contain only variables. This allows for easier rewrites in later passes.
class ConstantsToVars(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        r = self.ConstantToVarRewriter()
        return r.walk(model)

    # Return 1) a new list of Values with no duplicates (at the object level) and
    # 2) equalities between any original Value and a deduplicated Value.
    @staticmethod
    def replace_constants_with_vars(vals: Sequence[ir.Value]) -> Tuple[List[ir.Value], List[ir.Lookup]]:
        new_vals = []
        eqs = []

        for i, val in enumerate(vals):
            if isinstance(val, ir.PyValue) or isinstance(val, ir.Literal):
                # Replace constant with a new Var.
                typ = typer.to_type(val)
                assert isinstance(typ, ir.ScalarType), "can only replace scalar constants with vars"
                new_var = ir.Var(typ, f"{typ.name.lower()}_{i}")
                new_vals.append(new_var)
                eqs.append(f.lookup(rel_builtins.eq, [new_var, val]))
            else:
                new_vals.append(val)

        return new_vals, eqs

    @staticmethod
    def dedup_update(update: ir.Update) -> List[Union[ir.Update, ir.Lookup]]:
        deduped_vals, req_lookups = ConstantsToVars.replace_constants_with_vars(update.args)
        new_update = ir.Update(
            update.engine,
            update.relation,
            tuple(deduped_vals),
            update.effect,
            update.annotations,
        )
        return req_lookups + [new_update]

    # Does the actual work.
    class ConstantToVarRewriter(visitor.Rewriter):
        def __init__(self):
            super().__init__()

        # We implement handle_logical instead of handle_update because in
        # addition to modifying said update we require new lookups (equality
        # between original and deduplicated variables).
        def handle_logical(self, node: ir.Logical, parent: ir.Node):
            # In order to recurse over subtasks.
            node = super().handle_logical(node, parent)

            new_body = []
            for subtask in node.body:
                if isinstance(subtask, ir.Update):
                    new_body.extend(ConstantsToVars.dedup_update(subtask))
                else:
                    new_body.append(subtask)

            return ir.Logical(
                node.engine,
                node.hoisted,
                tuple(new_body),
                node.annotations
            )
