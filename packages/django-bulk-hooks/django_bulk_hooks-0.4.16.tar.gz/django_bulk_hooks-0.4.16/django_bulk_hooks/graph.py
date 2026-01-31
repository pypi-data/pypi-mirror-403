"""
Dependency graph for computing interdependent fields.

Steps are registered with dependencies, then executed in
topologically-sorted order. Used with before_create/before_update
to run only affected steps and only for records whose changed fields
intersect step dependencies.
"""

from __future__ import annotations

import networkx as nx
from dataclasses import dataclass
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Protocol
from typing import Set
from typing import TypeVar

CtxT = TypeVar("CtxT", bound="Context")


class Context(Protocol):
    """Protocol for context objects passed to step apply functions."""

    pass


ApplyFn = Callable[[list, list | None, Context], None]


@dataclass(frozen=True)
class Step:
    """A single step in a dependency graph (immutable)."""

    name: str
    provides: str
    depends_on: Set[str]
    apply: ApplyFn


class DependencyGraph:
    """
    Dependency graph for computing interdependent fields.

    Steps are registered with dependencies, then executed in
    topologically-sorted order automatically.

    Design note: 'provides' means "may write this field", not "always mutates it".
    """

    def __init__(self, external_inputs: Iterable[str] = ()):
        self._steps: Dict[str, Step] = {}
        self._graph: nx.DiGraph | None = None
        self._dirty = True
        self._external_inputs = set(external_inputs)

    @property
    def steps(self) -> Dict[str, Step]:
        return self._steps.copy()

    def register(
        self,
        name: str,
        provides: str,
        depends_on: Set[str] | Iterable[str] | None,
        apply: ApplyFn,
    ) -> None:
        if name in self._steps:
            raise ValueError(f"Step '{name}' is already registered")

        existing_providers = {s.provides: s.name for s in self._steps.values()}
        if provides in existing_providers:
            raise ValueError(
                f"Field '{provides}' is already provided by step '{existing_providers[provides]}'"
            )

        depends_on_set = set(depends_on or ())
        self._steps[name] = Step(name=name, provides=provides, depends_on=depends_on_set, apply=apply)
        self._dirty = True

    def extend(
        self,
        other: DependencyGraph,
        override: Dict[str, ApplyFn] | None = None,
    ) -> None:
        """
        Copy all steps from another graph into this one.

        Args:
            other: Graph to copy steps from.
            override: Optional dict of {step_name: new_apply_function}
                to override specific steps during extension.

        Steps already present in this graph are skipped (not overwritten).
        """
        override_map = override or {}

        for step in other.ordered_steps():
            if step.name in self._steps:
                continue

            existing_providers = {s.provides: s.name for s in self._steps.values()}
            if step.provides in existing_providers:
                raise ValueError(
                    f"Cannot extend: field '{step.provides}' is already provided by step "
                    f"'{existing_providers[step.provides]}'"
                )

            apply_fn = override_map.get(step.name, step.apply)
            self._steps[step.name] = Step(
                name=step.name,
                provides=step.provides,
                depends_on=step.depends_on,
                apply=apply_fn,
            )

        self._dirty = True

    def _build_graph(self) -> None:
        if not self._dirty:
            return

        self._graph = nx.DiGraph()
        providers = {s.provides: s for s in self._steps.values()}

        for step in self._steps.values():
            self._graph.add_node(step.name, step=step)
            for dep_field in step.depends_on:
                if dep_field in providers:
                    self._graph.add_edge(providers[dep_field].name, step.name)

        self._dirty = False

    def ordered_steps(self) -> List[Step]:
        self._build_graph()
        assert self._graph is not None

        if not nx.is_directed_acyclic_graph(self._graph):
            cycles = list(nx.simple_cycles(self._graph))
            raise ValueError(f"Circular dependencies detected: {cycles}")

        order = list(nx.topological_sort(self._graph))
        return [self._graph.nodes[name]["step"] for name in order]

    def steps_affected_by(self, changed_fields: Set[str]) -> List[Step]:
        self._build_graph()
        assert self._graph is not None

        affected = {step.name for step in self._steps.values() if (step.depends_on & changed_fields)}

        all_affected = set(affected)
        for step_name in affected:
            all_affected.update(nx.descendants(self._graph, step_name))

        ordered = self.ordered_steps()
        return [s for s in ordered if s.name in all_affected]

    def run(self, records: list, old_records: list | None, ctx: Context) -> None:
        for step in self.ordered_steps():
            step.apply(records, old_records, ctx)

    def run_for_changes(
        self,
        records: list,
        old_records: list,
        changed_fields: Dict[int, Set[str]],
        ctx: Context,
        external_changed: Set[str] | None = None,
    ) -> None:
        """
        Run only the steps affected by changes, and pass only the records that
        are relevant for each step.

        Behavior:
          - Steps that depend on any external input receive all records.
          - Steps that depend only on graph-provided fields receive only records
            whose changed fields intersect their dependencies.

        Requirements:
          - records and old_records must be aligned by index.
          - records must have a non-null pk (used as the key into changed_fields).
        """
        if not changed_fields:
            return

        all_changed: Set[str] = set()
        for s in changed_fields.values():
            all_changed.update(s)

        external_changed_set = set(external_changed or ())
        all_changed_with_external = all_changed | external_changed_set

        for step in self.steps_affected_by(all_changed_with_external):
            # If a step depends on external inputs, run it for all records.
            if step.depends_on & self._external_inputs:
                step.apply(records, old_records, ctx)
                continue

            # Otherwise, filter to records that changed fields relevant to this step.
            step_indices: List[int] = []
            for i, rec in enumerate(records):
                pk = getattr(rec, "pk", None)
                if pk is None:
                    continue
                rec_changes = changed_fields.get(pk)
                if rec_changes and (rec_changes & step.depends_on):
                    step_indices.append(i)

            if not step_indices:
                continue

            step_records = [records[i] for i in step_indices]
            step_old_records = [old_records[i] for i in step_indices]
            step.apply(step_records, step_old_records, ctx)

    def to_dot(self) -> str:
        self._build_graph()
        assert self._graph is not None

        def _escape(s: str) -> str:
            return s.replace("\\", "\\\\").replace('"', '\\"')

        lines = [
            "digraph DependencyGraph {",
            "  rankdir=LR;",
            "  node [shape=box, style=rounded];",
        ]

        step_to_id = {step.name: f"n{i}" for i, step in enumerate(self._steps.values())}

        for step in self._steps.values():
            node_id = step_to_id[step.name]
            deps = "\\n".join(sorted(step.depends_on)) if step.depends_on else "(no deps)"
            label = _escape(f"{step.name}\n\nProvides: {step.provides}\n\nDepends on:\n{deps}")
            lines.append(f'  {node_id} [label="{label}"];')

        for frm, to in self._graph.edges():
            lines.append(f"  {step_to_id[frm]} -> {step_to_id[to]};")

        lines.append("}")
        return "\n".join(lines)

    def validate(self, strict_missing_dependencies: bool = False) -> None:
        self.ordered_steps()

        if strict_missing_dependencies:
            providers = {s.provides for s in self._steps.values()}
            all_inputs = providers | self._external_inputs

            for step in self._steps.values():
                missing = step.depends_on - all_inputs
                if missing:
                    raise ValueError(
                        f"Step '{step.name}' depends on fields not provided by any step "
                        f"or declared as external inputs: {missing}"
                    )


# Backwards compatibility alias
Workflow = DependencyGraph
