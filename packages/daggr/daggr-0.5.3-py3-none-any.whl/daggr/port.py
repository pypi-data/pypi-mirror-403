"""Port module for node input/output definitions.

Ports are named connection points on nodes. Output ports can be connected
to input ports to form edges in the graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from daggr.node import Node


class Port:
    """A named connection point on a node.

    Ports represent inputs or outputs of a node. Access them as attributes
    on a node: `node.port_name`.

    Attributes:
        node: The node this port belongs to.
        name: The name of the port.
    """

    def __init__(self, node: Node, name: str):
        self.node = node
        self.name = name

    def __repr__(self):
        return f"Port({self.node._name}.{self.name})"

    def _as_source(self) -> tuple[Node, str]:
        return (self.node, self.name)

    def _as_target(self) -> tuple[Node, str]:
        return (self.node, self.name)

    def __getattr__(self, attr: str) -> ScatteredPort:
        if attr.startswith("_"):
            raise AttributeError(attr)
        if (
            hasattr(self.node, "_item_list_schemas")
            and self.name in self.node._item_list_schemas
        ):
            schema = self.node._item_list_schemas[self.name]
            if attr in schema:
                return ScatteredPort(self, attr)
        raise AttributeError(f"Port '{self.name}' has no attribute '{attr}'")

    @property
    def each(self) -> ScatteredPort:
        """Scatter this port's output - run the downstream node once per item in the list."""
        return ScatteredPort(self)

    def all(self) -> GatheredPort:
        """Gather outputs from a scattered node back into a list."""
        return GatheredPort(self)


class ScatteredPort:
    """A port that scatters its list output to run downstream nodes per-item.

    Created by accessing `.each` on a port. When connected to a downstream
    node, that node will be executed once for each item in the list.
    """

    def __init__(self, port: Port, item_key: str | None = None):
        self.port = port
        self.item_key = item_key

    @property
    def node(self):
        return self.port.node

    @property
    def name(self):
        return self.port.name

    def __getitem__(self, key: str) -> ScatteredPort:
        """Access a specific field from each scattered item (e.g., dialogue.json.each["text"])."""
        return ScatteredPort(self.port, key)

    def __repr__(self):
        if self.item_key:
            return f"ScatteredPort({self.port}['{self.item_key}'])"
        return f"ScatteredPort({self.port})"


class GatheredPort:
    """A port that gathers scattered results back into a list.

    Created by calling `.all()` on a port. Collects results from all
    scattered executions back into a single list.
    """

    def __init__(self, port: Port):
        self.port = port

    @property
    def node(self):
        return self.port.node

    @property
    def name(self):
        return self.port.name

    def __repr__(self):
        return f"GatheredPort({self.port})"


PortLike = Port | ScatteredPort | GatheredPort


def is_port(obj: Any) -> bool:
    """Check if an object is a Port, ScatteredPort, or GatheredPort."""
    return isinstance(obj, (Port, ScatteredPort, GatheredPort))


class PortNamespace:
    """A namespace for accessing ports that start with underscores.

    Used via `node._inputs` or `node._outputs` to access ports whose names
    start with underscores (which can't be accessed directly as attributes).
    """

    def __init__(self, node: Node, port_names: list[str]):
        self._node = node
        self._names = set(port_names)

    def __getattr__(self, name: str) -> Port:
        if name.startswith("_"):
            raise AttributeError(name)
        return Port(self._node, name)

    def __dir__(self) -> list[str]:
        return list(self._names)

    def __repr__(self):
        return f"PortNamespace({list(self._names)})"


class ItemList:
    """Define an editable list output with per-item schema.

    Example:
        outputs={
            "items": ItemList(
                speaker=gr.Dropdown(choices=["Host", "Guest"]),
                text=gr.Textbox(lines=2),
            ),
        }

    The function should return a list of dicts matching the schema keys.
    """

    def __init__(self, **schema):
        self.schema = schema
