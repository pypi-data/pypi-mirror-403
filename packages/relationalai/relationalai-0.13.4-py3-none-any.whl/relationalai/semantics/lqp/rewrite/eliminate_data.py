from relationalai.semantics.metamodel.compiler import Pass
from relationalai.semantics.metamodel import ir, builtins as rel_builtins, factory as f, visitor

from typing import cast
import pandas as pd
import hashlib

# Creates intermediary relations for all Data nodes and replaces said Data nodes
# with a Lookup into these created relations. Reuse duplicate created relations.
class EliminateData(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        r = self.DataRewriter()
        return r.walk(model)

    # Does the actual work.
    class DataRewriter(visitor.Rewriter):
        new_relations: list[ir.Relation]
        new_updates: list[ir.Logical]
        # Counter for naming new relations.
        # It must be that new_count == len new_updates == len new_relations.
        new_count: int
        # Cache for Data nodes to avoid creating duplicate intermediary relations
        data_cache: dict[str, ir.Relation]

        def __init__(self):
            self.new_relations = []
            self.new_updates = []
            self.new_count = 0
            self.data_cache = {}
            super().__init__()

        # Create a cache key for a Data node based on its structure and content
        def _data_cache_key(self, node: ir.Data) -> str:
            values = pd.util.hash_pandas_object(node.data).values
            return hashlib.sha256(bytes(values)).hexdigest()

        def _intermediary_relation(self, node: ir.Data) -> ir.Relation:
            cache_key = self._data_cache_key(node)
            if cache_key in self.data_cache:
                return self.data_cache[cache_key]
            self.new_count += 1
            intermediary_name = f"formerly_Data_{self.new_count}"

            intermediary_relation = f.relation(
                intermediary_name,
                [f.field(v.name, v.type) for v in node.vars]
            )
            self.new_relations.append(intermediary_relation)

            intermediary_update = f.logical([
                # For each row (union), equate values and their variable (logical).
                f.union(
                    [
                        f.logical(
                            [
                                f.lookup(rel_builtins.eq, [f.literal(val, var.type), var])
                                for (val, var) in zip(row, node.vars)
                            ],
                        )
                        for row in node
                    ],
                    hoisted = node.vars,
                ),
                # And pop it back into the relation.
                f.update(intermediary_relation, node.vars, ir.Effect.derive),
            ])
            self.new_updates.append(intermediary_update)

            # Cache the result for reuse
            self.data_cache[cache_key] = intermediary_relation

            return intermediary_relation

        # Create a new intermediary relation representing the Data (and pop it in
        # new_updates/new_relations) and replace this Data with a Lookup of said
        # intermediary.
        def handle_data(self, node: ir.Data, parent: ir.Node) -> ir.Lookup:
            intermediary_relation = self._intermediary_relation(node)
            replacement_lookup = f.lookup(intermediary_relation, node.vars)

            return replacement_lookup

        # Walks the model for the handle_data work then updates the model with
        # the new state.
        def handle_model(self, model: ir.Model, parent: None):
            walked_model = super().handle_model(model, parent)
            assert len(self.new_relations) == len(self.new_updates) and self.new_count == len(self.new_relations)

            # This is okay because its LQP.
            assert isinstance(walked_model.root, ir.Logical)
            root_logical = cast(ir.Logical, walked_model.root)

            # We may need to add the new intermediaries from handle_data to the model.
            if self.new_count  == 0:
                return model
            else:
                return ir.Model(
                    walked_model.engines,
                    walked_model.relations | self.new_relations,
                    walked_model.types,
                    ir.Logical(
                        root_logical.engine,
                        root_logical.hoisted,
                        root_logical.body + tuple(self.new_updates),
                        root_logical.annotations,
                    ),
                    walked_model.annotations,
                )
