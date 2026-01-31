from __future__ import annotations
from dataclasses import dataclass, field
from relationalai.clients.config import Config
from relationalai.semantics.metamodel import builtins
from relationalai.semantics.metamodel.ir import Node, Model, Require
from relationalai.semantics.metamodel.compiler import Pass
from relationalai.semantics.metamodel.rewrite.discharge_constraints import (
    DischargeConstraintsVisitor
)
from relationalai.semantics.lqp.rewrite.functional_dependencies import (
    is_valid_unique_constraint, normalized_fd
)

class AnnotateConstraints(Pass):
    """
    Extends `DischargeConstraints` pass by discharging only those Require nodes that cannot
    be declared as constraints in LQP.

    More precisely, the pass annotates Require nodes depending on how they should be
    treated when generating code:
     * `@declare_constraint` if the Require represents a constraint that can be declared in LQP.
     * `@discharge` if the Require represents a constraint that should be dismissed during
       code generation. Namely, when it cannot be declared in LQP and uses one of the
       `unique`, `exclusive`, `anyof` builtins. These nodes are removed from the IR model
       in the Flatten pass.
    """

    def rewrite(self, model: Model, options: dict = {}) -> Model:
        return AnnotateConstraintsRewriter().walk(model)

@dataclass
class AnnotateConstraintsRewriter(DischargeConstraintsVisitor):
    emit_constraints: bool = field(default=False)
    """
    Visitor marks Require nodes with
    - `discharge` if they should be discharged from the metamodel
    - `declare_constraint` if they should be kept and emitted as LQP constraint declarations

    By default, all constraints are discharged. To enable emitting constraints, set the
    `reasoner.rule.emit_constraints` flag to True in the config file.
    ```toml
    [reasoner.rule]
    emit_constraints = true
    ```
    """

    def __post_init__(self):
        from relationalai.semantics.internal.internal import overridable_flag
        self.emit_constraints = overridable_flag('reasoner.rule.emit_constraints', Config(), None, False)

    def _should_declare_constraint(self, node: Require) -> bool:
        if not self.emit_constraints:
            return False
        if not is_valid_unique_constraint(node):
            return False
        # Currently, we only declare non-structural functional dependencies.
        fd = normalized_fd(node)
        return fd is not None and not fd.is_structural

    def handle_require(self, node: Require, parent: Node):
        if self._should_declare_constraint(node):
            return node.reconstruct(
                node.engine,
                node.domain,
                node.checks,
                node.annotations | [builtins.declare_constraint_annotation]
            )

        return super().handle_require(node, parent)
