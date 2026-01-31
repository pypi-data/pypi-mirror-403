from __future__ import annotations

from dataclasses import dataclass, field

from lark import Lark, Tree, Token


_PYI_GRAMMAR = r"""
%import common.WS_INLINE
%import common.NEWLINE
%ignore WS_INLINE

start: header imports consts enums structs unions exceptions services

header: "# coding:utf-8" NEWLINE

imports: from_import*
from_import: "from" pkg "import" modules NEWLINE
pkg: /[A-Za-z_.][\w._]*/
modules: module ("," module)*
module: IDENT module_alias?
module_alias: "as" IDENT

consts: const*
const: IDENT "=" value? NEWLINE

enums: enum*
enum: class_enum
class_enum: class_prefix IDENT "(Enum):" NEWLINE kvs
kvs: kv*
kv: IDENT "=" value? NEWLINE

structs: struct*
struct: class_struct
class_struct: class_prefix IDENT "(object):" NEWLINE annotations init NEWLINE
annotations: annotation*
annotation: IDENT ":" type

unions: union*
union: class_union
class_union: class_prefix IDENT "(object):" NEWLINE annotations init NEWLINE

exceptions: exception*
exception: class_exception
class_exception: class_prefix IDENT "(TException):" NEWLINE annotations init NEWLINE

services: service*
service: class_service
class_service: class_prefix IDENT "(object):" NEWLINE methods NEWLINE
methods: method*
method: "def" IDENT "(self," params ")" "->" type ":" NEWLINE "  ..." NEWLINE

params: (param ("," param)*)?
param: annotation "=" value?

init: "def __init__(self," params ")" "-> None:" NEWLINE "  ..." NEWLINE

class_prefix: "# noinspection PyPep8Naming, PyShadowingNames" NEWLINE "class"

type: /[\w.\[\]]+/
IDENT: /[A-Za-z_][\w._]*/
value: VALUE
VALUE: /[\w\-'.\"\{\}]+/
"""

_PARSER = Lark(_PYI_GRAMMAR, parser="lalr", start="start", maybe_placeholders=False)


@dataclass
class Annotation:
    name: str = ""
    type: str = ""


@dataclass
class Annotations(dict):
    pass


@dataclass
class Parameter:
    annotation: Annotation | None = None
    default: str = ""

    @property
    def __name__(self) -> str:
        if self.annotation:
            return self.annotation.name
        return ""

    @__name__.setter
    def __name__(self, value: str) -> None:
        if self.annotation is None:
            self.annotation = Annotation(name=value)
        else:
            self.annotation.name = value


@dataclass
class Parameters(list):
    pass


@dataclass
class Init:
    params: Parameters = field(default_factory=Parameters)


@dataclass
class Struct:
    name: str = ""
    annotations: Annotations = field(default_factory=Annotations)
    init: Init = field(default_factory=Init)


@dataclass
class Structs(list):
    pass


@dataclass
class Union:
    name: str = ""
    annotations: Annotations = field(default_factory=Annotations)
    init: Init = field(default_factory=Init)


@dataclass
class Unions(list):
    pass


@dataclass
class Exc:
    name: str = ""
    annotations: Annotations = field(default_factory=Annotations)
    init: Init = field(default_factory=Init)


@dataclass
class Exceptions(list):
    pass


@dataclass
class Method:
    name: str = ""
    params: Parameters = field(default_factory=Parameters)
    response: str = ""


@dataclass
class Methods(dict):
    pass


@dataclass
class Service:
    name: str = ""
    methods: Methods = field(default_factory=Methods)


@dataclass
class Services(list):
    pass


@dataclass
class ModuleAlias:
    alias: str = ""


@dataclass
class Module:
    name: str = ""
    module_alias: ModuleAlias = field(default_factory=ModuleAlias)


@dataclass
class Modules(list):
    pass


@dataclass
class FromImport:
    name: str = ""
    modules: Modules = field(default_factory=Modules)


@dataclass
class Imports(dict):
    pass


@dataclass
class KeyValue:
    name: str = ""
    value: str = ""


@dataclass
class KeyValues(list):
    pass


@dataclass
class Const:
    name: str = ""
    value: str = ""


@dataclass
class Consts(list):
    pass


@dataclass
class Enum:
    name: str = ""
    kvs: KeyValues = field(default_factory=KeyValues)


@dataclass
class Enums(list):
    pass


@dataclass
class PYI:
    imports: Imports = field(default_factory=Imports)
    consts: Consts = field(default_factory=Consts)
    enums: Enums = field(default_factory=Enums)
    structs: Structs = field(default_factory=Structs)
    unions: Unions = field(default_factory=Unions)
    exceptions: Exceptions = field(default_factory=Exceptions)
    services: Services = field(default_factory=Services)


def _token_value(node: Token | Tree | str) -> str:
    if isinstance(node, Token):
        return str(node)
    if isinstance(node, str):
        return node
    return ""


def _text_of(tree: Tree, rule: str) -> str:
    for child in tree.children:
        if isinstance(child, Tree) and child.data == rule:
            return _token_value(child.children[0]) if child.children else ""
    return ""


def _find_children(tree: Tree, rule: str) -> list[Tree]:
    return [child for child in tree.children if isinstance(child, Tree) and child.data == rule]


def compose(pyi: PYI) -> str:
    parts = ["# coding:utf-8\n"]

    if pyi.imports:
        for pkg, from_import in pyi.imports.items():
            modules = []
            for module in from_import.modules:
                if module.module_alias and module.module_alias.alias:
                    modules.append(f"{module.name} as {module.module_alias.alias}")
                else:
                    modules.append(module.name)
            parts.append(f"from {pkg} import {', '.join(modules)}\n")
        parts.append("\n")

    if pyi.consts:
        for const in pyi.consts:
            parts.append(f"{const.name} = {const.value}\n")
        parts.append("\n")

    if pyi.enums:
        for enum in pyi.enums:
            parts.append("# noinspection PyPep8Naming, PyShadowingNames\n")
            parts.append(f"class {enum.name}(Enum):\n")
            for kv in enum.kvs:
                parts.append(f"    {kv.name} = {kv.value}\n")
            parts.append("\n")

    if pyi.structs:
        for struct in pyi.structs:
            parts.append("# noinspection PyPep8Naming, PyShadowingNames\n")
            parts.append(f"class {struct.name}(object):\n")
            for name, annotation in struct.annotations.items():
                parts.append(f"    {name}: {annotation.type}\n")
            parts.append("\n    def __init__(self,\n")
            if struct.init.params:
                params = []
                for param in struct.init.params:
                    params.append(f"                 {param.__name__}: {param.annotation.type} = {param.default}")
                parts.append(",\n".join(params))
                parts.append(") -> None:\n")
            else:
                parts.append("                 ) -> None:\n")
            parts.append("        ...\n\n")

    if pyi.unions:
        for union in pyi.unions:
            parts.append("# noinspection PyPep8Naming, PyShadowingNames\n")
            parts.append(f"class {union.name}(object):\n")
            for name, annotation in union.annotations.items():
                parts.append(f"    {name}: {annotation.type}\n")
            parts.append("\n    def __init__(self,\n")
            if union.init.params:
                params = []
                for param in union.init.params:
                    params.append(f"                 {param.__name__}: {param.annotation.type} = {param.default}")
                parts.append(",\n".join(params))
                parts.append(") -> None:\n")
            else:
                parts.append("                 ) -> None:\n")
            parts.append("        ...\n\n")

    if pyi.exceptions:
        for exc in pyi.exceptions:
            parts.append("# noinspection PyPep8Naming, PyShadowingNames\n")
            parts.append(f"class {exc.name}(TException):\n")
            for name, annotation in exc.annotations.items():
                parts.append(f"    {name}: {annotation.type}\n")
            parts.append("\n    def __init__(self,\n")
            if exc.init.params:
                params = []
                for param in exc.init.params:
                    params.append(f"                 {param.__name__}: {param.annotation.type} = {param.default}")
                parts.append(",\n".join(params))
                parts.append(") -> None:\n")
            else:
                parts.append("                 ) -> None:\n")
            parts.append("        ...\n\n")

    if pyi.services:
        for service in pyi.services:
            parts.append("# noinspection PyPep8Naming, PyShadowingNames\n")
            parts.append(f"class {service.name}(object):\n")
            for method_name, method in service.methods.items():
                parts.append(f"    def {method_name}(self, ")
                if method.params:
                    params = []
                    for param in method.params:
                        params.append(f"{param.__name__}: {param.annotation.type} = {param.default}")
                    parts.append(", ".join(params))
                parts.append(f") -> {method.response}:\n")
                parts.append("        ...\n\n")
            parts.append("\n")

    return "".join(parts).rstrip() + "\n"


def _parse_annotation(tree: Tree) -> Annotation:
    name = _token_value(tree.children[0])
    type_ = _token_value(tree.children[1])
    return Annotation(name=name, type=type_)


def _parse_param(tree: Tree) -> Parameter:
    annotation_tree = tree.children[0]
    value = _token_value(tree.children[1])
    annotation = _parse_annotation(annotation_tree)
    return Parameter(annotation=annotation, default=value)


def _parse_params(tree: Tree) -> Parameters:
    params = Parameters()
    if not tree.children:
        return params
    for child in tree.children:
        if isinstance(child, Tree) and child.data == "param":
            params.append(_parse_param(child))
    return params


def _parse_annotations(tree: Tree) -> Annotations:
    annotations = Annotations()
    for child in tree.children:
        if isinstance(child, Tree) and child.data == "annotation":
            ann = _parse_annotation(child)
            annotations[ann.name] = ann
    return annotations


def _parse_init(tree: Tree) -> Init:
    init = Init()
    for child in tree.children:
        if isinstance(child, Tree) and child.data == "params":
            init.params = _parse_params(child)
    return init


def _parse_methods(tree: Tree) -> Methods:
    methods = Methods()
    for child in tree.children:
        if isinstance(child, Tree) and child.data == "method":
            name = _token_value(child.children[0])
            params = Parameters()
            response = ""
            for part in child.children[1:]:
                if isinstance(part, Tree) and part.data == "params":
                    params = _parse_params(part)
                elif isinstance(part, Token):
                    response = str(part)
            methods[name] = Method(name=name, params=params, response=response)
    return methods


def _parse_struct_like(tree: Tree) -> tuple[str, Annotations, Init]:
    name = _token_value(tree.children[1])
    annotations = Annotations()
    init = Init()
    for part in tree.children[2:]:
        if isinstance(part, Tree) and part.data == "annotations":
            annotations = _parse_annotations(part)
        elif isinstance(part, Tree) and part.data == "init":
            init = _parse_init(part)
    return name, annotations, init


def _parse_imports(tree: Tree) -> Imports:
    imports = Imports()
    for child in tree.children:
        if not (isinstance(child, Tree) and child.data == "from_import"):
            continue
        pkg_tree = _find_children(child, "pkg")[0]
        pkg = _token_value(pkg_tree.children[0])
        modules = Modules()
        modules_tree = _find_children(child, "modules")[0]
        for module_tree in modules_tree.children:
            if not (isinstance(module_tree, Tree) and module_tree.data == "module"):
                continue
            name = _token_value(module_tree.children[0])
            alias = ""
            if len(module_tree.children) > 1:
                alias_tree = module_tree.children[1]
                if isinstance(alias_tree, Tree) and alias_tree.data == "module_alias":
                    alias = _token_value(alias_tree.children[0])
            module = Module(name=name, module_alias=ModuleAlias(alias=alias))
            modules.append(module)
        from_import = FromImport(name=pkg, modules=modules)
        imports[pkg] = from_import
    return imports


def parse(text: str) -> PYI:
    tree = _PARSER.parse(text)
    pyi = PYI()

    for child in tree.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "imports":
            pyi.imports = _parse_imports(child)
        elif child.data == "consts":
            consts = Consts()
            for const_tree in child.children:
                if isinstance(const_tree, Tree) and const_tree.data == "const":
                    name = _token_value(const_tree.children[0])
                    value = _token_value(const_tree.children[1])
                    consts.append(Const(name=name, value=value))
            pyi.consts = consts
        elif child.data == "enums":
            enums = Enums()
            for enum_tree in child.children:
                if not (isinstance(enum_tree, Tree) and enum_tree.data == "class_enum"):
                    continue
                name = _token_value(enum_tree.children[1])
                kvs = KeyValues()
                for kv_tree in enum_tree.children:
                    if isinstance(kv_tree, Tree) and kv_tree.data == "kv":
                        kv_name = _token_value(kv_tree.children[0])
                        kv_value = _token_value(kv_tree.children[1])
                        kvs.append(KeyValue(name=kv_name, value=kv_value))
                enums.append(Enum(name=name, kvs=kvs))
            pyi.enums = enums
        elif child.data == "structs":
            structs = Structs()
            for struct_tree in child.children:
                if not (isinstance(struct_tree, Tree) and struct_tree.data == "class_struct"):
                    continue
                name, annotations, init = _parse_struct_like(struct_tree)
                structs.append(Struct(name=name, annotations=annotations, init=init))
            pyi.structs = structs
        elif child.data == "unions":
            unions = Unions()
            for union_tree in child.children:
                if not (isinstance(union_tree, Tree) and union_tree.data == "class_union"):
                    continue
                name, annotations, init = _parse_struct_like(union_tree)
                unions.append(Union(name=name, annotations=annotations, init=init))
            pyi.unions = unions
        elif child.data == "exceptions":
            exceptions = Exceptions()
            for exc_tree in child.children:
                if not (isinstance(exc_tree, Tree) and exc_tree.data == "class_exception"):
                    continue
                name, annotations, init = _parse_struct_like(exc_tree)
                exceptions.append(Exc(name=name, annotations=annotations, init=init))
            pyi.exceptions = exceptions
        elif child.data == "services":
            services = Services()
            for service_tree in child.children:
                if not (isinstance(service_tree, Tree) and service_tree.data == "class_service"):
                    continue
                name = _token_value(service_tree.children[1])
                methods = Methods()
                for part in service_tree.children[2:]:
                    if isinstance(part, Tree) and part.data == "methods":
                        methods = _parse_methods(part)
                services.append(Service(name=name, methods=methods))
            pyi.services = services

    return pyi
