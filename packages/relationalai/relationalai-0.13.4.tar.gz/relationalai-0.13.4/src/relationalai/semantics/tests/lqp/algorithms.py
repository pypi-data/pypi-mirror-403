"""
Constructing Metamodel IR with Algorithms

We introduce a set of programmatic constructs that provide a convenient syntax for
constructing PyRel's metamodel IR representations for Loopy algorithms. Importantly, these
macros construct a new model using PyRel declarations constructed with a _base model_. The
base model needs to be also used to declare all concepts and relationships.

Below we illustrate the use of these macros by constructing a simple reachability
algorithm, whose Rel-like pseudo-code is as follows:

```
algorithm
    setup
        def edge = { (1,2); (2,3); (3,4) }
        def source = { 1 }
    end setup
    @global empty reachable = {}
    loop
        def frontier = source
        def reachable = frontier
        while (true)
            def next_frontier = frontier . edge
            def frontier = next_frontier
            monus frontier = reachable    # frontier = frontier - reachable
            upsert reachable = frontier   # reachable = reachable ∪ frontier
            break break_reachable = empty(frontier)
        end while
    end loop
end algorithm
```

The PyRel's metamodel IR for the above algorithm is constructed with the utilities as
follows.

```
base_model = Model("algorithm_builder", dry_run=True)

# Input (context) data

edge = base_model.Relationship("Edge from {source:int} to {target:int}")
source = base_model.Relationship("Source node {node:int}")

with algorithm(base_model):
    setup(
        define(edge(1,2), edge(2,3), edge(3,4), edge(4,1))),
        define(source(1))
    )

    # "local" variables and relations
    n = Integer.ref()
    m = Integer.ref()
    reachable = base_model.Relationship("Reachable node {node:int}")
    frontier = base_model.Relationship("Frontier node {node:int}")
    next_frontier = base_model.Relationship("Next frontier node {node:int}")

    global_(empty(define(reachable(n))))
    assign(define(frontier(n)).where(source(n)))
    assign(define(reachable(n)).where(frontier(n)))
    with while_():
        assign(define(next_frontier(m)).where(frontier(n), edge(n, m)))
        assign(define(frontier(m)).where(next_frontier(m)))
        monus(define(frontier(n)).where(reachable(n)))
        upsert(0)(define(reachable(n)).where(frontier(n)))
        break_(where(not_(frontier(n))))

# Prints the PyRel Metamodel (IR)
print(get_metamodel())

# Prints the LQP transaction
print(get_lqp_str())
```
"""
from relationalai.semantics import Model
from relationalai.semantics.metamodel import factory, ir, types
from relationalai.semantics.internal.internal import Fragment
from relationalai.semantics.lqp.algorithms import (
    mk_empty, mk_assign, mk_upsert, mk_global, mk_monus
)
from relationalai.semantics.lqp.constructors import mk_transaction
from relationalai.semantics.lqp.compiler import Compiler
from relationalai.semantics.lqp import ir as lqp, builtins
from typing import cast, TypeGuard, Optional, Sequence
from lqp import print as lqp_print
import threading
from contextlib import contextmanager


# While the constructors are very light-weight they enforce
# the following grammar for algorithms:
#
# <Algorithm> := with algorithm(base_model): <Script>
# <Script> := <Instruction>*
# <Instruction> := <BaseInstruction> | <Loop>
# <BaseInstruction> := [global_(] empty(Fragment) [)]
#                    | [global_(] assign(<Fragment>) [)]
#                    | break(<Fragment>)
#                    | upsert(<Int>)(<Fragment>)
#                    | monus(<Fragment>)
# <Loop> := with while_(): <Script>
#
# Note: global_ annotation can only be used on top-level empty and assign instructions at the
# top-level of the algorithm script.

_storage = threading.local()

def get_builder() -> 'AlgorithmBuilder':
    """ Retrieves the thread-local AlgorithmBuilder instance."""
    global _storage
    if not(hasattr(_storage, "algorithm_builder")):
        _storage.algorithm_builder = AlgorithmBuilder()
    return _storage.algorithm_builder

def get_metamodel() -> ir.Model:
    """ Retrieves the compiled metamodel IR for the previous algorithm. Can only be used
    after an algorithm has been defined."""
    return get_builder().get_metamodel()

def get_lqp_str() -> str:
    """ Retrieves the LQP string representation for the previous algorithm. Can only be used
    after an algorithm has been defined."""
    return get_builder().get_lqp_str()

@contextmanager
def algorithm(model:Model):
    """ Context manager for defining an algorithm on the given base model."""
    get_builder().begin_algorithm(model)
    yield
    get_builder().end_algorithm()

@contextmanager
def while_():
    """ Context manager for defining a while loop within an algorithm."""
    get_builder().begin_while_loop()
    yield
    get_builder().end_while_loop()

def setup(*stmts:Fragment):
    """ Defines the setup section of an algorithm: a collection of PyRel statement that
    prepare input data for the algorithm."""
    builder = get_builder()
    assert len(builder.script_stacks) == 1, "setup can only be called at the top-level of an algorithm"
    assert builder.setup_fragments is None, "setup can only be called once per algorithm"
    builder.set_setup_fragments(stmts)

def global_(pos:int):
    """ Marks a top-level `empty` or `assign` instruction as defining a global relation."""
    assert type(pos) is int, "global_ can only be applied to empty and assign"
    builder = get_builder()
    assert len(builder.script_stacks) == 1, "global_ can only be applied to top-level instructions"
    assert len(builder.script_stacks[0].instructions) == pos + 1
    task = cast(ir.Task, mk_global(builder.script_stacks[0].instructions[pos]))
    builder.script_stacks[0].instructions[pos] = task
    builder.add_global_relation(task)

def empty(stmt) -> int:
    """ Marks a PyRel statement as an assignment of empty relation. The statement must not
    have a body (no where clause)."""
    assert has_empty_body(stmt), "Empty instruction must have an empty body"
    task = get_builder().compile_statement(stmt)
    task = cast(ir.Task, mk_empty(task))
    return get_builder().append_task(task)

def assign(stmt) -> int:
    """ Marks a PyRel statement as an assignment instruction."""
    task = get_builder().compile_statement(stmt)
    task = cast(ir.Task, mk_assign(task))
    return get_builder().append_task(task)

def upsert_with_arity(arity:int, stmt:Fragment):
    task = get_builder().compile_statement(stmt)
    task = cast(ir.Task, mk_upsert(task, arity))
    get_builder().append_task(task)

def upsert(arity:int):
    """ Marks a PyRel statement as an upsert instruction with the given arity."""
    assert type(arity) is int and arity >= 0, "arity must be a non-negative integer"
    return lambda stmt: upsert_with_arity(arity, stmt)

def monus(stmt: Fragment) -> int:
    """ Marks a PyRel statement as a Boolean monus (set difference) instruction."""
    task = get_builder().compile_statement(stmt)
    task = cast(ir.Task, mk_monus(task, types.Bool, "or", 0))
    return get_builder().append_task(task)

def break_(stmt):
    """ Marks a PyRel statement as a break instruction. The statement must be headless (no define clause)."""
    assert has_no_head(stmt), "Break instruction must have a headless fragment"
    task = get_builder().compile_statement(stmt)
    assert isinstance(task, ir.Logical)
    break_condition = [cond for cond in task.body if not isinstance(cond, ir.Update)]
    break_node = factory.break_(factory.logical(break_condition))
    get_builder().append_task(break_node)

def has_empty_body(stmt) -> TypeGuard[Fragment]:
    if not isinstance(stmt, Fragment):
        return False
    return len(stmt._where) == 0

def has_no_head(frag):
    return len(frag._define) == 0


class ScriptBuilder:
    """
    Builder for Loopy scripts.
    """
    def __init__(self):
        self.instructions:list[ir.Task] = []

    def add_task(self, instr:ir.Task) -> int:
        self.instructions.append(instr)
        return len(self.instructions) - 1

    def build_script(self, annos:list[ir.Annotation]) -> ir.Sequence:
        return factory.sequence(
            tasks=self.instructions,
            annos=[builtins.script_annotation()] + annos
        )


class AlgorithmBuilder:
    """
    Builder for Loopy algorithms.
    """
    def __init__(self):
        self.script_stacks:list[ScriptBuilder] = []
        self.compiled_model:Optional[ir.Model] = None
        self.global_relations:list[str] = []
        self.base_model:Optional[Model] = None
        self.setup_fragments:Optional[list[Fragment]] = None

    def begin_algorithm(self, base_model:Model):
        self.base_model = base_model
        self.script_stacks = [ScriptBuilder()]
        self.compiled_model = None
        self.global_relations:list[str] = []
        self.setup_fragments:Optional[list[Fragment]] = None

    def add_global_relation(self, task:ir.Task):
        assert isinstance(task, ir.Logical)
        for t in task.body:
            if isinstance(t, ir.Update):
                if t.relation.name not in self.global_relations:
                    self.global_relations.append(t.relation.name)

    def set_setup_fragments(self, fragments:Sequence[Fragment]):
        self.setup_fragments = list(fragments)

    def compile_statement(self, stmt:Fragment) -> ir.Task:
        assert self.base_model is not None
        task = self.base_model._compiler.compile_task(stmt)
        return task

    def append_task(self, task:ir.Task) -> int:
        assert len(self.script_stacks) > 0
        return self.script_stacks[-1].add_task(task)

    def begin_while_loop(self):
        script_builder = ScriptBuilder()
        self.script_stacks.append(script_builder)

    def end_while_loop(self):
        script_builder = self.script_stacks.pop()
        while_script = script_builder.build_script([builtins.while_annotation()])
        loop = factory.loop(while_script, annos=[builtins.while_annotation()])
        self.append_task(loop)

    def end_algorithm(self):
        assert len(self.script_stacks) == 1
        script_builder = self.script_stacks.pop()
        algorithm_script = script_builder.build_script([builtins.algorithm_annotation()])
        setup = self.compile_setup()
        algorithm_logical = factory.logical(setup + [algorithm_script])
        self.compiled_model = factory.compute_model(algorithm_logical)

    def compile_setup(self) -> list[ir.Logical]:
        if self.setup_fragments is None:
            return []
        assert self.setup_fragments is not None
        assert self.base_model is not None
        setup_tasks = []
        for stmt in self.setup_fragments:
            task = self.base_model._compiler.compile_task(stmt)
            setup_tasks.append(task)
        return setup_tasks

    def get_metamodel(self) -> ir.Model:
        """ Retrieves the compiled metamodel IR for the previous algorithm. """
        metamodel = self.compiled_model
        assert metamodel is not None, "No metamodel available. You must first define algorithm."
        return metamodel

    def get_lqp_str(self) -> str:
        lqp = self.get_lqp()
        options = lqp_print.ugly_config.copy()
        options[str(lqp_print.PrettyOptions.PRINT_NAMES)] = True
        options[str(lqp_print.PrettyOptions.PRINT_DEBUG)] = False
        lqp_str = lqp_print.to_string(lqp, options)
        return lqp_str

    def get_lqp(self):
        model = self.get_metamodel()

        compiler = Compiler()
        rewritten_model = compiler.rewrite(model)
        write_epoch = compiler.do_compile(rewritten_model, {'fragment_id': b"f1"})[1]

        define = cast(lqp.Define, write_epoch.writes[0].write_type)
        debug_info = define.fragment.debug_info

        read_epoch = self._build_read_epoch(debug_info)

        transaction = mk_transaction([write_epoch, read_epoch])

        return transaction

    def _build_read_epoch(self, debug_info:lqp.DebugInfo) -> lqp.Epoch:
        reads = []

        relation_id:dict[str,lqp.RelationId] = dict()
        for rel_id, rel_name in debug_info.id_to_orig_name.items():
            if rel_name in self.global_relations:
                relation_id[rel_name] = rel_id

        global_relation_names = [rel for rel in self.global_relations if rel in relation_id]

        for (i, rel_name) in enumerate(global_relation_names):
            read = lqp.Read(
                meta = None,
                read_type = lqp.Output(
                    meta=None,
                    name=f"{rel_name}",
                    relation_id=relation_id[rel_name],
                )
            )
            reads.append(read)

        read_epoch = lqp.Epoch(
            meta = None,
            writes = [],
            reads = reads,
        )

        return read_epoch
