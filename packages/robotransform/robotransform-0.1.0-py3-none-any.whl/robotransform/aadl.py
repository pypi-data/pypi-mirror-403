from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal

ComponentCategory = Literal[
    "system", "process", "thread", "data", "processor", "bus", "device",
    "memory", "virtual_processor", "virtual_bus"
]

FeatureDirection = Literal["in", "out", "in out"]
PortCategory = Literal["event", "event_data", "data"]


@dataclass
class Mode:
    name: str
    initial: bool = False

    def to_aadl(self, indent: str = "") -> str:
        initial = "initial " if self.initial else ""
        lines = [f"{indent}{self.name}: {initial}mode;"]
        return "\n".join(lines)


@dataclass
class Port:
    name: str
    direction: FeatureDirection
    port_category: PortCategory = "data"
    data_type: Optional[str] = None

    def to_aadl(self, indent: str = "") -> str:
        port_type = "data port"
        if self.port_category == "event":
            port_type = "event port"
        elif self.port_category == "event_data":
            port_type = "event data port"
        dt = f" {self.data_type}" if self.data_type else ""
        return f"{indent}{self.name}: {self.direction} {port_type}{dt};"


@dataclass
class Subcomponent:
    name: str
    category: ComponentCategory
    component_type: str
    component_implementation: Optional[str] = None

    def to_aadl(self, indent: str = "") -> str:
        impl_part = f".{self.component_implementation}" if self.component_implementation else ""
        return f"{indent}{self.name}: {self.category} {self.component_type}{impl_part};"


@dataclass
class Connection:
    name: str
    source: str
    destination: str
    bidirectional: bool = False

    def to_aadl(self, indent: str = "") -> str:
        arrow = "<->" if self.bidirectional else "->"
        return f"{indent}{self.name}: {self.source} {arrow} {self.destination};"


@dataclass
class ComponentType:
    name: str
    category: ComponentCategory
    features: Dict[str, Port] = field(default_factory=dict)
    modes: List[Mode] = field(default_factory=list)

    def to_aadl(self, indent: str = "") -> str:
        lines = [f"{indent}{self.category} {self.name}"]
        if self.features:
            lines.append(f"{indent}  features")
            for f in self.features.values():
                lines.append(f.to_aadl(indent + "    "))
        if self.modes:
            lines.append(f"{indent}  modes")
            for m in self.modes:
                lines.append(m.to_aadl(indent + "    "))
        lines.append(f"{indent}end {self.name};")
        return "\n".join(lines)


@dataclass
class BehaviorGuard:
    expression: str

    def to_aadl(self) -> str:
        return f"-[{self.expression}]-" if self.expression else ""


@dataclass
class BehaviorTransition:
    source: str
    destination: str
    guard: Optional[BehaviorGuard] = None

    def to_aadl(self) -> str:
        if self.guard and self.guard.expression:
            return f"{self.source} -[{self.guard.expression}]-> {self.destination};"
        return f"{self.source} -> {self.destination};"


@dataclass
class BehaviorSpecification:
    transitions: List[BehaviorTransition] = field(default_factory=list)

    def add_transition(self, source: str, destination: str, guard_expression: Optional[str] = None) -> None:
        self.transitions.append(
            BehaviorTransition(
                source=source,
                destination=destination,
                guard=BehaviorGuard(guard_expression) if guard_expression else None,
            )
        )

    def to_aadl(self, indent: str = "") -> str:
        lines = [f"{indent}annex behaviour_specification {{**", f"{indent}  mode transitions"]
        for t in self.transitions:
            lines.append(f"{indent}    {t.to_aadl()}")
        lines.append(f"{indent}**}};")
        return "\n".join(lines)


@dataclass
class ComponentImplementation:
    name: str
    category: str
    type_name: str
    subcomponents: Dict[str, Subcomponent] = field(default_factory=dict)
    connections: List['Connection'] = field(default_factory=list)
    modes: List['Mode'] = field(default_factory=list)
    behavior: Optional['BehaviorSpecification'] = None

    def to_aadl_header(self, indent: str = "") -> str:
        return f"{indent}{self.category} implementation {self.name} for {self.type_name}"

    def to_aadl(self, indent: str = "") -> str:
        lines = [self.to_aadl_header(indent)]
        if self.subcomponents:
            lines.append(f"{indent}  subcomponents")
            for s in self.subcomponents.values():
                lines.append(s.to_aadl(indent + "    "))
        if self.connections:
            lines.append(f"{indent}  connections")
            for c in self.connections:
                lines.append(c.to_aadl(indent + "    "))
        if self.modes:
            lines.append(f"{indent}  modes")
            for m in self.modes:
                lines.append(m.to_aadl(indent + "    "))
        if self.behavior:
            lines.append(self.behavior.to_aadl(indent + "  "))
        lines.append(f"{indent}end {self.name};")
        return "\n".join(lines)


@dataclass
class ThreadImplementation(ComponentImplementation):
    category: str = field(init=False, default="thread")

@dataclass
class ProcessImplementation(ComponentImplementation):
    category: str = field(init=False, default="process")

@dataclass
class SystemImplementation(ComponentImplementation):
    category: str = field(init=False, default="system")


@dataclass
class AADLPackage:
    name: str
    with_packages: List[str] = field(default_factory=list)
    public_types: Dict[str, ComponentType] = field(default_factory=dict)
    public_implementations: Dict[str, ComponentImplementation] = field(default_factory=dict)
    private_types: Dict[str, ComponentType] = field(default_factory=dict)
    private_implementations: Dict[str, ComponentImplementation] = field(default_factory=dict)

    def to_aadl(self) -> str:
        lines = [f"package {self.name}", "public"]
        if self.with_packages:
            lines.append(f"  with {', '.join(self.with_packages)};")
        for t in self.public_types.values():
            lines.append(t.to_aadl("  "))
        for i in self.public_implementations.values():
            lines.append(i.to_aadl("  "))
        if self.private_types or self.private_implementations:
            lines.append("private")
            for t in self.private_types.values():
                lines.append(t.to_aadl("  "))
            for i in self.private_implementations.values():
                lines.append(i.to_aadl("  "))
        lines.append(f"end {self.name};")
        return "\n".join(lines)
