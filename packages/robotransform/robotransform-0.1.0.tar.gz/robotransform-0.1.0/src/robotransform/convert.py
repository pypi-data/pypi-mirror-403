from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Optional, Union

from robotransform.aadl import (
    AADLPackage,
    ComponentType,
    Connection as AADLConnection,
    Port,
    Mode,
    BehaviorSpecification,
    BehaviorTransition,
    BehaviorGuard,
    Subcomponent,
    ProcessImplementation,
    ThreadImplementation,
    SystemImplementation,
)
from robotransform.filters import type_to_aadl_type
from robotransform.main import get_template, write_output
from robotransform.concepts import Package, StateMachineDef, ControllerDef, RoboticPlatformDef, Variable, Event, Module

_IDENTIFIER_RE = re.compile(r"[^0-9A-Za-z_]")


def _aadl_id(value: object) -> str:
    if value is None:
        return "unnamed"
    text = str(value)
    text = text.replace("::", "_")
    text = _IDENTIFIER_RE.sub("_", text)
    if text and text[0].isdigit():
        text = f"n_{text}"
    return text or "unnamed"


def _local_name(value: object) -> str:
    if value is None:
        return "unnamed"
    if hasattr(value, "parts"):
        parts = getattr(value, "parts")
        if parts:
            return str(parts[-1])
    text = str(value)
    return text.split("::")[-1]


def _aadl_name(value: object) -> str:
    return _aadl_id(_local_name(value))


def _aadl_qualified_name(value: object) -> str:
    if hasattr(value, "parts"):
        parts = getattr(value, "parts")
        return "::".join(_aadl_id(part) for part in parts)
    return str(value)


def _unique_name(base: str, existing: set[str]) -> str:
    name = base
    index = 1
    while name in existing:
        name = f"{base}_{index}"
        index += 1
    return name


def _message_type_name(type_ref: Optional[str]) -> Optional[str]:
    if not type_ref or "::" not in type_ref:
        return None
    package, name = type_ref.split("::", 1)
    if package != "messages":
        return None
    return name


def _collect_message_types(packages: list[AADLPackage]) -> set[str]:
    names: set[str] = set()
    for pkg in packages:
        for comp in pkg.public_types.values():
            for feature in comp.features.values():
                if isinstance(feature, Port):
                    msg_name = _message_type_name(feature.data_type)
                    if msg_name:
                        names.add(msg_name)
        for impl in pkg.public_implementations.values():
            for sub in impl.subcomponents.values():
                if sub.category != "data":
                    continue
                msg_name = _message_type_name(sub.component_type)
                if msg_name:
                    names.add(msg_name)
    return names


def _collect_defined_message_types(robo_packages: list[Package]) -> set[str]:
    names: set[str] = set()
    for pkg in robo_packages:
        for record in getattr(pkg, "types", []):
            names.add(str(getattr(record, "name", "")))
    return names


def _render_messages(robo_packages: list[Package], aadl_packages: list[AADLPackage],
                     output: Optional[Union[io.TextIOBase, Path, str]]) -> str:
    used_types = _collect_message_types(aadl_packages)
    defined_types = _collect_defined_message_types(robo_packages)
    extra_types = sorted(used_types - defined_types)
    template = get_template("messages")
    data = template.render(packages=robo_packages, extra_types=extra_types)
    return write_output(data, output)


def robocart_package_to_aadl_full(rc_pkg: "Package") -> AADLPackage:
    aadl_pkg = AADLPackage(
        name=_aadl_name(rc_pkg.name),
        with_packages=["Base_Types", "messages"],
    )

    # ---- registries ----
    def register_type(comp_type: ComponentType) -> ComponentType:
        return aadl_pkg.public_types.setdefault(comp_type.name, comp_type)

    def register_impl(comp_impl):
        return aadl_pkg.public_implementations.setdefault(comp_impl.name, comp_impl)

    local_type_names = {str(getattr(t, "name", "")) for t in getattr(rc_pkg, "types", [])}

    # ---- helpers ----
    def resolve_type(robo_type: object) -> str:
        typename = str(robo_type)
        short_name = typename.split("::")[-1]
        if short_name in local_type_names:
            return _aadl_id(short_name)
        return type_to_aadl_type(robo_type)

    def convert_event(ev: "Event") -> Port:
        data_type = resolve_type(ev.type) if getattr(ev, "type", None) else None
        port_category = "event_data" if data_type else "event"
        return Port(
            name=_aadl_id(ev.name),
            direction="in out",
            port_category=port_category,
            data_type=data_type,
        )

    def convert_variable(var: "Variable") -> Subcomponent:
        return Subcomponent(
            name=_aadl_id(var.name),
            category="data",
            component_type=resolve_type(var.type),
        )

    def transition_guard(transition) -> Optional[str]:
        trigger = getattr(transition, "trigger", None)
        if not trigger:
            return None
        communication = getattr(trigger, "trigger", None)
        if communication:
            return _aadl_name(getattr(communication, "event", ""))
        return None

    def ensure_process(sm: "StateMachineDef") -> ProcessImplementation:
        type_name = _aadl_name(sm.name)
        impl_name = f"{type_name}.impl"
        if impl_name in aadl_pkg.public_implementations:
            return aadl_pkg.public_implementations[impl_name]

        proc_type = ComponentType(name=type_name, category="process")
        for ev in getattr(sm, "events", []):
            port = convert_event(ev)
            proc_type.features.setdefault(port.name, port)
        register_type(proc_type)

        proc_impl = ProcessImplementation(name=impl_name, type_name=type_name)

        nodes = list(getattr(sm, "nodes", []) or [])
        state_names: list[str] = []
        initial_names: set[str] = set()
        for idx, node in enumerate(nodes):
            node_type = node.__class__.__name__
            if node_type == "State":
                raw_name = getattr(node, "name", f"state_{idx}")
                state_names.append(_aadl_name(raw_name))
            elif node_type == "Initial":
                initial_names.add(_aadl_name(getattr(node, "name", "")))

        state_name_set = set(state_names)
        initial_targets: set[str] = set()
        transitions: list[BehaviorTransition] = []
        for t in getattr(sm, "transitions", []):
            src = _aadl_name(getattr(t, "source", ""))
            dst = _aadl_name(getattr(t, "target", ""))
            if src in initial_names and dst in state_name_set:
                initial_targets.add(dst)
            if src in state_name_set and dst in state_name_set:
                guard_expr = transition_guard(t)
                guard = BehaviorGuard(guard_expr) if guard_expr else None
                transitions.append(BehaviorTransition(source=src, destination=dst, guard=guard))

        for state_name in state_names:
            proc_impl.modes.append(Mode(name=state_name, initial=state_name in initial_targets))

        if proc_impl.modes and not any(m.initial for m in proc_impl.modes):
            proc_impl.modes[0].initial = True

        subcomponent_names = set()
        for state_name in state_names:
            thread_type_name = _aadl_id(f"{type_name}_{state_name}_Thread")
            thread_impl_name = f"{thread_type_name}.impl"
            register_type(ComponentType(name=thread_type_name, category="thread"))
            register_impl(ThreadImplementation(name=thread_impl_name, type_name=thread_type_name))
            sub_name = _unique_name(f"{state_name}_thread", subcomponent_names)
            subcomponent_names.add(sub_name)
            proc_impl.subcomponents[sub_name] = Subcomponent(
                name=sub_name,
                category="thread",
                component_type=thread_type_name,
                component_implementation="impl",
            )

        for var in getattr(sm, "variables", []):
            data_sub = convert_variable(var)
            data_sub.name = _unique_name(data_sub.name, subcomponent_names)
            subcomponent_names.add(data_sub.name)
            proc_impl.subcomponents[data_sub.name] = data_sub

        if transitions:
            behavior = BehaviorSpecification(transitions=transitions)
            proc_impl.behavior = behavior

        register_impl(proc_impl)
        return proc_impl

    def connection_endpoint(component, event, subcomponents: set[str]) -> str:
        component_name = _aadl_name(component)
        event_name = _aadl_name(event)
        if component_name in subcomponents:
            return f"{component_name}.{event_name}"
        return event_name

    def convert_connection(conn, subcomponents: set[str]) -> AADLConnection:
        src = _aadl_name(getattr(conn, "source", ""))
        dst = _aadl_name(getattr(conn, "target", ""))
        src_evt = _aadl_name(getattr(conn, "event_source", ""))
        dst_evt = _aadl_name(getattr(conn, "event_target", ""))
        name = _aadl_id(f"{src}_{src_evt}_to_{dst}_{dst_evt}")
        return AADLConnection(
            name=name,
            source=connection_endpoint(conn.source, conn.event_source, subcomponents),
            destination=connection_endpoint(conn.target, conn.event_target, subcomponents),
            bidirectional=getattr(conn, "bidirectional", False),
        )

    def ensure_controller(controller: "ControllerDef") -> SystemImplementation:
        type_name = _aadl_name(controller.name)
        impl_name = f"{type_name}.impl"
        if impl_name in aadl_pkg.public_implementations:
            return aadl_pkg.public_implementations[impl_name]

        sys_type = ComponentType(name=type_name, category="system")
        for ev in getattr(controller, "events", []):
            port = convert_event(ev)
            sys_type.features.setdefault(port.name, port)
        register_type(sys_type)

        sys_impl = SystemImplementation(name=impl_name, type_name=type_name)
        subcomponent_names = set()
        port_subcomponents = set()

        for sm in getattr(controller, "machines", []):
            if isinstance(sm, StateMachineDef) or sm.__class__.__name__ == "StateMachineDef":
                proc_impl = ensure_process(sm)
                sub_name = _aadl_name(getattr(sm, "name", "process"))
                sub_name = _unique_name(sub_name, subcomponent_names)
                subcomponent_names.add(sub_name)
                port_subcomponents.add(sub_name)
                sys_impl.subcomponents[sub_name] = Subcomponent(
                    name=sub_name,
                    category="process",
                    component_type=proc_impl.type_name,
                    component_implementation="impl",
                )
            elif sm.__class__.__name__ == "StateMachineRef":
                sub_name = _aadl_name(getattr(sm, "name", "process_ref"))
                sub_name = _unique_name(sub_name, subcomponent_names)
                subcomponent_names.add(sub_name)
                port_subcomponents.add(sub_name)
                sys_impl.subcomponents[sub_name] = Subcomponent(
                    name=sub_name,
                    category="process",
                    component_type=_aadl_qualified_name(getattr(sm, "ref", "")),
                )

        for var in getattr(controller, "variables", []):
            data_sub = convert_variable(var)
            data_sub.name = _unique_name(data_sub.name, subcomponent_names)
            subcomponent_names.add(data_sub.name)
            sys_impl.subcomponents[data_sub.name] = data_sub

        for conn in getattr(controller, "connections", []):
            sys_impl.connections.append(convert_connection(conn, port_subcomponents))

        register_impl(sys_impl)
        return sys_impl

    def ensure_robotic_platform(platform: "RoboticPlatformDef") -> SystemImplementation:
        type_name = _aadl_name(platform.name)
        impl_name = f"{type_name}.impl"
        if impl_name in aadl_pkg.public_implementations:
            return aadl_pkg.public_implementations[impl_name]

        sys_type = ComponentType(name=type_name, category="system")
        for ev in getattr(platform, "events", []):
            port = convert_event(ev)
            sys_type.features.setdefault(port.name, port)
        register_type(sys_type)

        sys_impl = SystemImplementation(name=impl_name, type_name=type_name)
        subcomponent_names = set()

        for var in getattr(platform, "variables", []):
            data_sub = convert_variable(var)
            data_sub.name = _unique_name(data_sub.name, subcomponent_names)
            subcomponent_names.add(data_sub.name)
            sys_impl.subcomponents[data_sub.name] = data_sub

        register_impl(sys_impl)
        return sys_impl

    def ensure_module(module: "Module") -> SystemImplementation:
        type_name = _aadl_name(module.name)
        impl_name = f"{type_name}.impl"
        if impl_name in aadl_pkg.public_implementations:
            return aadl_pkg.public_implementations[impl_name]

        module_type = ComponentType(name=type_name, category="system")
        register_type(module_type)

        module_impl = SystemImplementation(name=impl_name, type_name=type_name)
        subcomponent_names = set()
        port_subcomponents = set()

        for node in getattr(module, "nodes", []):
            node_type = node.__class__.__name__
            if node_type == "ControllerDef":
                controller_impl = ensure_controller(node)
                sub_name = _aadl_name(getattr(node, "name", "controller"))
                sub_name = _unique_name(sub_name, subcomponent_names)
                subcomponent_names.add(sub_name)
                port_subcomponents.add(sub_name)
                module_impl.subcomponents[sub_name] = Subcomponent(
                    name=sub_name,
                    category="system",
                    component_type=controller_impl.type_name,
                    component_implementation="impl",
                )
            elif node_type == "ControllerRef":
                sub_name = _aadl_name(getattr(node, "name", "controller_ref"))
                sub_name = _unique_name(sub_name, subcomponent_names)
                subcomponent_names.add(sub_name)
                port_subcomponents.add(sub_name)
                module_impl.subcomponents[sub_name] = Subcomponent(
                    name=sub_name,
                    category="system",
                    component_type=_aadl_qualified_name(getattr(node, "ref", "")),
                )
            elif node_type == "StateMachineDef":
                proc_impl = ensure_process(node)
                sub_name = _aadl_name(getattr(node, "name", "process"))
                sub_name = _unique_name(sub_name, subcomponent_names)
                subcomponent_names.add(sub_name)
                port_subcomponents.add(sub_name)
                module_impl.subcomponents[sub_name] = Subcomponent(
                    name=sub_name,
                    category="process",
                    component_type=proc_impl.type_name,
                    component_implementation="impl",
                )
            elif node_type == "StateMachineRef":
                sub_name = _aadl_name(getattr(node, "name", "process_ref"))
                sub_name = _unique_name(sub_name, subcomponent_names)
                subcomponent_names.add(sub_name)
                port_subcomponents.add(sub_name)
                module_impl.subcomponents[sub_name] = Subcomponent(
                    name=sub_name,
                    category="process",
                    component_type=_aadl_qualified_name(getattr(node, "ref", "")),
                )
            elif node_type == "RoboticPlatformDef":
                platform_impl = ensure_robotic_platform(node)
                sub_name = _aadl_name(getattr(node, "name", "platform"))
                sub_name = _unique_name(sub_name, subcomponent_names)
                subcomponent_names.add(sub_name)
                port_subcomponents.add(sub_name)
                module_impl.subcomponents[sub_name] = Subcomponent(
                    name=sub_name,
                    category="system",
                    component_type=platform_impl.type_name,
                    component_implementation="impl",
                )
            elif node_type == "RoboticPlatformRef":
                sub_name = _aadl_name(getattr(node, "name", "platform_ref"))
                sub_name = _unique_name(sub_name, subcomponent_names)
                subcomponent_names.add(sub_name)
                port_subcomponents.add(sub_name)
                module_impl.subcomponents[sub_name] = Subcomponent(
                    name=sub_name,
                    category="system",
                    component_type=_aadl_qualified_name(getattr(node, "ref", "")),
                )

        for conn in getattr(module, "connections", []):
            module_impl.connections.append(convert_connection(conn, port_subcomponents))

        register_impl(module_impl)
        return module_impl

    # ---- top-level package conversion ----
    for record in getattr(rc_pkg, "types", []):
        data_name = _aadl_name(getattr(record, "name", "data"))
        register_type(ComponentType(name=data_name, category="data"))

    for ctl in getattr(rc_pkg, "controllers", []):
        ensure_controller(ctl)

    for sm in getattr(rc_pkg, "machines", []):
        if isinstance(sm, StateMachineDef) or sm.__class__.__name__ == "StateMachineDef":
            ensure_process(sm)

    for robot in getattr(rc_pkg, "robots", []):
        ensure_robotic_platform(robot)

    for mod in getattr(rc_pkg, "modules", []):
        ensure_module(mod)

    return aadl_pkg


def dump_aadl(rc_input: Union["Package", "Store"], output: Optional[Union[io.TextIOBase, Path, str]] = None,
              template_name: str = "aadl",
              messages_output: Optional[Union[io.TextIOBase, Path, str]] = None) -> str:
    # If a Store, render all packages inside it
    if hasattr(rc_input, "__iter__") and not isinstance(rc_input, Package):
        robo_packages = list(rc_input.load().values())
        packages = [robocart_package_to_aadl_full(pkg) for pkg in robo_packages]
    else:
        robo_packages = [rc_input]
        packages = [robocart_package_to_aadl_full(rc_input)]

    template = get_template(template_name)
    data = template.render(packages=packages)
    write_output(data, output)

    if messages_output is None and isinstance(output, (str, Path)):
        messages_output = Path(output).parent / "messages.aadl"

    if messages_output is not None:
        _render_messages(robo_packages, packages, messages_output)

    return data
