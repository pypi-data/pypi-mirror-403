from relationalai.semantics.metamodel import ir
from typing import Union

CompilableType = Union[
    # Subgrouping
    ir.Logical,
    ir.Union,

    # Loops
    ir.Loop,
    ir.Sequence,
    ir.Break,

    # Formulas
    ir.Lookup,
    ir.Exists,
    ir.Construct,
    ir.Not,

    # Aggregations
    ir.Aggregate,

    # Rank
    ir.Rank,

    # Effects
    ir.Output,
    ir.Update,

    # Constraints
    ir.Require,
]

# Preconditions
def assert_valid_input(model: ir.Model) -> None:
    task = model.root

    assert isinstance(task, ir.Logical), f"expected root to be logical task, got {type(task)}"
    for subtask in task.body:
        _assert_valid_subtask(subtask)

def _assert_valid_subtask(task: ir.Task) -> None:
    # TODO: assert what subtasks should look like
    assert isinstance(task, (ir.Logical, ir.Sequence)), f"expected logical task, got {type(task)}"
    _assert_task_compilable(task)

def _assert_task_compilable(task: ir.Task) -> None:
    assert isinstance(task, CompilableType), f"expected task to be compilable, got {type(task)}"
    if isinstance(task, ir.Logical):
        for subtask in task.body:
            _assert_task_compilable(subtask)
    elif isinstance(task, ir.Union):
        for subtask in task.tasks:
            _assert_task_compilable(subtask)
    elif isinstance(task, ir.Update):
        assert_valid_update(task)
        effect = task.effect
        assert effect == ir.Effect.derive, "only derive supported at the moment"
    elif isinstance(task, ir.Sequence):
        assert any(anno.relation.name == "script" for anno in task.annotations), "only @script sequences supported at the moment"
        for subtask in task.tasks:
            _assert_task_compilable(subtask)
    elif isinstance(task, ir.Loop):
        assert isinstance(task.body, ir.Sequence), f"expected loop body to be a sequence, got {type(task.body)}"
        for subtask in task.body.tasks:
            _assert_task_compilable(subtask)

def assert_valid_update(update: ir.Update) -> None:
    effect = update.effect
    assert effect == ir.Effect.derive, "only derive supported at the moment"
