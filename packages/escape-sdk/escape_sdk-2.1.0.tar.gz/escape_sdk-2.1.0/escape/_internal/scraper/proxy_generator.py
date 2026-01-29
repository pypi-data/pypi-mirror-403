#!/usr/bin/env python3
"""Auto-generates proxy classes for the Query Builder from scraped API data."""

import json
from pathlib import Path

from escape._internal.logger import logger

# Python keywords that can't be used as method names
PYTHON_KEYWORDS = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}


class ProxyGenerator:
    """Generates proxy classes from scraped RuneLite API data."""

    def __init__(self, api_data_path: str):
        """Initialize the proxy generator with API data from the given path."""
        with open(api_data_path) as f:
            self.api_data = json.load(f)

        self.methods = self.api_data.get("methods", {})
        self.classes = self.api_data.get("classes", [])
        self.enums = self.api_data.get("enums", {})
        self.inheritance = self.api_data.get("inheritance", {})  # Load inheritance data

        # Build class to methods mapping
        self.class_methods = self._build_class_methods_mapping()

        # Add AWT classes that RuneLite uses
        self._add_awt_classes()

    def _add_awt_classes(self):
        """Add AWT and geometry classes to class_methods mapping with empty method lists."""
        geometry_classes = [
            "java.awt.Point",
            "java.awt.Rectangle",
            "java.awt.Dimension",
            "java.awt.Color",
            "java.awt.image.BufferedImage",
            "java.awt.Shape",
            "net.runelite.api.Polygon",
        ]

        for class_name in geometry_classes:
            if class_name not in self.class_methods:
                self.class_methods[class_name] = []

    def _build_class_methods_mapping(self) -> dict[str, list[tuple[str, str, str, str, str, str]]]:
        """Build mapping of class names to their method tuples."""
        class_methods = {}

        for method_name, signatures in self.methods.items():
            for sig_info in signatures:
                if isinstance(sig_info, list) and len(sig_info) >= 2:
                    class_name = sig_info[0].replace("/", ".")
                    signature = sig_info[1]
                    generic_type = sig_info[2] if len(sig_info) >= 3 else None

                    # Keep declaring_class in JNI format (with slashes) for C bridge
                    declaring_class_jni = sig_info[0]

                    # Extract return type from signature (JNI type)
                    jni_return_type = self._extract_return_type(signature)

                    # Extract full Java class path from signature for bridge communication
                    full_java_class = self._extract_full_class_from_signature(signature)

                    # Use generic type if available, otherwise use JNI-derived type
                    python_return_type = (
                        self._convert_generic_to_python_type(generic_type)
                        if generic_type
                        else jni_return_type
                    )

                    if class_name not in class_methods:
                        class_methods[class_name] = []

                    class_methods[class_name].append(
                        (
                            method_name,
                            signature,
                            python_return_type,
                            generic_type,
                            full_java_class,
                            declaring_class_jni,
                        )
                    )

        return class_methods

    def _convert_generic_to_python_type(self, generic_type: str) -> str:
        """Convert Java generic type to Python type hint."""
        if not generic_type:
            return "Any"

        # Handle void return type
        if generic_type == "void":
            return "None"

        # Filter out invalid types (scraper errors)
        if generic_type in PYTHON_KEYWORDS or generic_type in (
            "return",
            "other",
            "extends",
            "implements",
        ):
            return "Any"

        # Handle arrays: Tile[][] -> List[List[Tile]]
        if "[]" in generic_type:
            # Count array dimensions
            dims = generic_type.count("[]")
            base_type = generic_type.replace("[]", "").strip()

            # Convert base type
            if base_type in ("int", "boolean", "long", "float", "double", "byte", "short", "char"):
                python_base = base_type
            else:
                # It's an object type - just use the simple name
                python_base = base_type.split(".")[-1] if "." in base_type else base_type
                # Filter out invalid names
                if python_base in PYTHON_KEYWORDS or python_base in (
                    "return",
                    "other",
                    "extends",
                    "implements",
                ):
                    return "Any"

            # Wrap in List[] for each dimension
            result = python_base
            for _ in range(dims):
                result = f"List[{result}]"
            return result

        # Handle generics: List<Player> -> List[Player]
        if "<" in generic_type and ">" in generic_type:
            # Extract base and generic part
            base = generic_type[: generic_type.index("<")]
            generic_part = generic_type[generic_type.index("<") + 1 : generic_type.rindex(">")]

            # Convert base type
            if base in ["List", "ArrayList", "LinkedList"]:
                base = "List"
            elif base in ["Set", "HashSet", "TreeSet"]:
                base = "Set"
            elif base in ["Map", "HashMap", "TreeMap"]:
                base = "Map"

            # Convert generic part (handle simple cases)
            element_type = generic_part.split(".")[-1] if "." in generic_part else generic_part
            # Filter out invalid names
            if element_type in PYTHON_KEYWORDS or element_type in (
                "return",
                "other",
                "extends",
                "implements",
            ):
                return "Any"

            return f"{base}[{element_type}]"

        # Check if it's a valid simple type
        simple_type = generic_type.split(".")[-1] if "." in generic_type else generic_type
        if simple_type in PYTHON_KEYWORDS or simple_type in (
            "return",
            "other",
            "extends",
            "implements",
        ):
            return "Any"

        # No generics or arrays - return as-is
        return generic_type

    def _extract_return_type(self, signature: str) -> str:
        """Extract return type from a JNI signature."""
        if ")" in signature:
            return_part = signature.split(")")[1]
            return self._jni_to_python_type(return_part)
        return "Any"

    def _extract_full_class_from_signature(self, signature: str) -> str | None:
        """Extract full Java class path from JNI signature return type."""
        if ")" not in signature:
            return None

        return_part = signature.split(")")[1]

        # Check if it's an object type
        if return_part.startswith("L") and return_part.endswith(";"):
            # Extract class path and convert / to .
            class_path = return_part[1:-1].replace("/", ".")
            return class_path

        # Primitive or void - no class
        return None

    def _jni_to_python_type(self, jni_type: str) -> str:
        """Convert JNI type descriptor to Python type hint."""
        if jni_type == "V":
            return "None"
        elif jni_type == "Z":
            return "bool"
        elif jni_type in ("B", "S", "I", "J"):
            return "int"
        elif jni_type in ("F", "D"):
            return "float"
        elif jni_type.startswith("L") and jni_type.endswith(";"):
            class_name = jni_type[1:-1].replace("/", ".")
            if class_name == "java.lang.String":
                return "str"
            simple_name = class_name.split(".")[-1]
            if simple_name in self.enums:
                return "QueryRef"
            if simple_name in self.classes:
                return f"'{simple_name}Proxy'"
            return "Any"
        elif jni_type.startswith("["):
            element_type = self._jni_to_python_type(jni_type[1:])
            return f"List[{element_type}]"
        return "Any"

    def _extract_parameters(self, signature: str) -> list[tuple[str, str]]:
        """Extract parameter types from a JNI signature."""
        if "(" not in signature or ")" not in signature:
            return []

        params_part = signature[signature.index("(") + 1 : signature.index(")")]
        if not params_part:
            return []

        params = []
        i = 0
        param_count = 0

        while i < len(params_part):
            param_count += 1
            if params_part[i] == "L":
                # Object type - find the semicolon
                end = params_part.index(";", i)
                param_type = self._jni_to_python_type(params_part[i : end + 1])
                param_name = f"arg{param_count}"

                # Special handling for enums
                class_name = params_part[i + 1 : end].replace("/", ".")
                simple_name = class_name.split(".")[-1]
                if simple_name in self.enums:
                    param_type = f"Union[int, '{simple_name}Enum']"
                    param_name = simple_name.lower().replace("id", "_id")

                params.append((param_name, param_type))
                i = end + 1
            elif params_part[i] == "[":
                # Array type - find the end
                j = i + 1
                if params_part[j] == "L":
                    end = params_part.index(";", j)
                    param_type = self._jni_to_python_type(params_part[i : end + 1])
                    i = end + 1
                else:
                    param_type = self._jni_to_python_type(params_part[i : j + 1])
                    i = j + 1
                params.append((f"arg{param_count}", param_type))
            else:
                # Primitive type
                param_type = self._jni_to_python_type(params_part[i])
                params.append((f"arg{param_count}", param_type))
                i += 1

        return params

    def _get_all_methods_including_inherited(
        self, class_name: str
    ) -> list[tuple[str, str, str, str, str, str]]:
        """Get all methods for a class including inherited methods from parents."""
        all_methods = []
        seen_methods = set()

        if class_name in self.class_methods:
            for method_tuple in self.class_methods[class_name]:
                method_name = method_tuple[0]
                signature = method_tuple[1]
                key = (method_name, signature)
                if key not in seen_methods:
                    all_methods.append(method_tuple)
                    seen_methods.add(key)

        simple_name = class_name.split(".")[-1]
        if simple_name in self.inheritance:
            inheritance_info = self.inheritance[simple_name]
            if "extends" in inheritance_info:
                parent_simple_name = inheritance_info["extends"]
                if "," in parent_simple_name:
                    parent_simple_name = parent_simple_name.split(",")[0].strip()

                parent_full_name = None
                for full_name in self.class_methods:
                    if (
                        full_name.endswith("." + parent_simple_name)
                        or full_name == parent_simple_name
                    ):
                        parent_full_name = full_name
                        break

                if parent_full_name:
                    parent_methods = self._get_all_methods_including_inherited(parent_full_name)
                    for method_tuple in parent_methods:
                        method_name = method_tuple[0]
                        signature = method_tuple[1]
                        key = (method_name, signature)
                        if key not in seen_methods:
                            all_methods.append(method_tuple)
                            seen_methods.add(key)

        return all_methods

    def _generate_proxy_class(
        self, class_name: str, methods: list[tuple[str, str, str, str, str, str]]
    ) -> str:
        """Generate a proxy class for a RuneLite API class."""
        simple_name = class_name.split(".")[-1]

        code = f"class {simple_name}Proxy:\n"
        code += '    """Auto-generated proxy for ' + simple_name + '"""\n\n'

        code += "    def __init__(self, query_ref):\n"
        code += "        self._ref = query_ref\n\n"

        code += "    def __getattr__(self, name):\n"
        code += '        """Fallback for field access."""\n'
        code += "        ref = object.__getattribute__(self, '_ref')\n"
        code += "        if name in ('query', 'ref_id', 'source_ref', 'return_type'):\n"
        code += "            return getattr(ref, name)\n"
        code += "        return ref._field(name)\n\n"

        method_groups: dict[str, list[tuple[str, str, str, str, str]]] = {}
        for (
            method_name,
            signature,
            return_type,
            generic_type,
            full_java_class,
            declaring_class,
        ) in methods:
            if method_name not in method_groups:
                method_groups[method_name] = []
            method_groups[method_name].append(
                (signature, return_type, generic_type, full_java_class, declaring_class)
            )

        for method_name, signatures in sorted(method_groups.items()):
            if method_name in (
                "toString",
                "equals",
                "hashCode",
                "getClass",
                "notify",
                "notifyAll",
                "wait",
            ):
                continue

            if method_name in PYTHON_KEYWORDS:
                continue

            if len(signatures) == 1:
                signature, return_type, generic_type, full_java_class, declaring_class = signatures[
                    0
                ]
                params = self._extract_parameters(signature)
                code += self._generate_method(
                    method_name,
                    signature,
                    return_type,
                    generic_type,
                    full_java_class,
                    declaring_class,
                    params,
                )
            else:
                int_sig = None
                enum_sig = None
                enum_type = None

                for sig, ret_type, gen_type, full_cls, decl_cls in signatures:
                    if sig == "(I)" + sig.split(")")[1]:
                        int_sig = (sig, ret_type, gen_type, full_cls, decl_cls)
                    elif "InventoryID" in sig or "Skill" in sig or "Prayer" in sig:
                        enum_sig = (sig, ret_type, gen_type, full_cls, decl_cls)
                        if "InventoryID" in sig:
                            enum_type = "InventoryID"
                        elif "Skill" in sig:
                            enum_type = "Skill"
                        elif "Prayer" in sig:
                            enum_type = "Prayer"

                if int_sig and enum_sig and enum_type:
                    code += self._generate_int_enum_method(
                        method_name, int_sig, enum_sig, enum_type
                    )
                else:
                    code += self._generate_overloaded_method(method_name, signatures, class_name)

        return code

    def _generate_overloaded_method(
        self, method_name: str, signatures: list[tuple[str, str, str, str, str]], class_name: str
    ) -> str:
        """Generate a method that handles multiple overloads with runtime dispatch."""
        signatures.sort(key=lambda x: x[0].count(";") + x[0].count("I"))
        _, return_type, _, full_java_class, _ = signatures[0]
        display_return_type = (
            full_java_class
            if full_java_class
            else (return_type if return_type != "Any" else "QueryRef")
        )

        if display_return_type and "." in display_return_type:
            parts = display_return_type.split(".")
            if parts[-1] in PYTHON_KEYWORDS:
                display_return_type = "int"

        needs_wrapping = False
        wrapped_class = None
        if (
            return_type
            and return_type
            not in (
                "int",
                "long",
                "bool",
                "boolean",
                "float",
                "double",
                "str",
                "String",
                "java.lang.String",
                "None",
                "Any",
                "QueryRef",
            )
            and "[" not in return_type
            and "]" not in return_type
            and return_type not in self.enums
        ):
            wrapped_class = return_type
            needs_wrapping = True

        return_annotation = f"'{wrapped_class}Proxy'" if needs_wrapping else display_return_type
        code = f'''

    def {method_name}(self, *args) -> {return_annotation}:
        """Auto-generated method (overloaded)."""
        arg_count = len(args)
'''

        by_param_count = {}
        for sig, ret_type, gen_type, full_cls, decl_cls in signatures:
            params = self._extract_parameters(sig)
            param_count = len(params)
            if param_count not in by_param_count:
                by_param_count[param_count] = []
            by_param_count[param_count].append(
                (sig, ret_type, gen_type, full_cls, decl_cls, params)
            )

        for idx, (param_count, sigs) in enumerate(sorted(by_param_count.items())):
            if_keyword = "if" if idx == 0 else "elif"
            sig, ret_type, gen_type, full_cls, decl_cls, params = sigs[0]
            code += f"""        {if_keyword} arg_count == {param_count}:
            signature = "{sig}"
            declaring_class = "{decl_cls}"
            return_type = "{full_cls if full_cls else ret_type}"
"""

        simple_name = class_name.split("/")[-1]
        code += f"""        else:
            raise TypeError(f"{simple_name}.{method_name}() doesn't support {{arg_count}} arguments")

        ref = self._ref._createRef(
            "{method_name}",
            signature,
            *args,
            return_type=return_type,
            declaring_class=declaring_class
        )
"""

        if needs_wrapping:
            code += f"""        return {wrapped_class}Proxy(ref)
"""
        else:
            code += """        return ref
"""

        return code

    def _generate_int_enum_method(
        self,
        method_name: str,
        int_sig: tuple[str, str, str, str, str],
        enum_sig: tuple[str, str, str, str, str],
        enum_type: str,
    ) -> str:
        """Generate a method that handles both integer and enum arguments."""
        int_signature, int_return_type, _int_generic, int_full_java_class, int_declaring_class = (
            int_sig
        )
        (
            enum_signature,
            _enum_return_type,
            _enum_generic,
            _enum_full_java_class,
            enum_declaring_class,
        ) = enum_sig

        return_type = int_return_type
        display_return_type = return_type if return_type != "Any" else "QueryRef"
        actual_return_type = int_full_java_class if int_full_java_class else return_type

        needs_wrapping = False
        wrapped_class = None

        primitive_types = (
            "int",
            "long",
            "bool",
            "boolean",
            "float",
            "double",
            "str",
            "String",
            "java.lang.String",
            "None",
            "Any",
            "QueryRef",
        )
        if (
            return_type
            and return_type not in primitive_types
            and "[" not in return_type
            and "]" not in return_type
            and return_type not in self.enums
        ):
            wrapped_class = return_type
            needs_wrapping = True

        if needs_wrapping:
            code = f'''

    def {method_name}(self, arg1) -> '{wrapped_class}Proxy':
        """Auto-generated method (overloaded)."""
        if isinstance(arg1, int):
            signature = "{int_signature}"
            declaring_class = "{int_declaring_class}"
        else:
            signature = "{enum_signature}"
            declaring_class = "{enum_declaring_class}"

        ref = self._ref._createRef(
            "{method_name}",
            signature,
            arg1,
            return_type="{actual_return_type}",
            declaring_class=declaring_class
        )
        return {wrapped_class}Proxy(ref)'''
        else:
            code = f'''

    def {method_name}(self, arg1) -> {display_return_type}:
        """Auto-generated method (overloaded)."""
        if isinstance(arg1, int):
            signature = "{int_signature}"
            declaring_class = "{int_declaring_class}"
        else:
            signature = "{enum_signature}"
            declaring_class = "{enum_declaring_class}"

        return self._ref._createRef(
            "{method_name}",
            signature,
            arg1,
            return_type="{actual_return_type}",
            declaring_class=declaring_class
        )'''

        return code

    def _generate_method(
        self,
        method_name: str,
        signature: str,
        return_type: str,
        generic_type: str,
        full_java_class: str,
        declaring_class: str,
        params: list[tuple[str, str]],
        is_overloaded: bool = False,
    ) -> str:
        """Generate a single method for a proxy class."""
        if params:
            param_str = ", ".join(f"{name}: {ptype}" for name, ptype in params)
            param_names = ", ".join(name for name, _ in params)
        else:
            param_str = ""
            param_names = ""

        needs_wrapping = False
        wrapped_class = None

        primitive_types = (
            "int",
            "long",
            "bool",
            "boolean",
            "float",
            "double",
            "str",
            "String",
            "java.lang.String",
            "None",
            "Any",
            "QueryRef",
        )
        if (
            return_type
            and return_type not in primitive_types
            and "[" not in return_type
            and "]" not in return_type
            and return_type not in self.enums
        ):
            wrapped_class = return_type
            needs_wrapping = True

        display_return_type = return_type if return_type != "Any" else "QueryRef"
        actual_return_type = full_java_class if full_java_class else return_type

        if not full_java_class and signature and ")" in signature:
            jni_return = signature.split(")")[1]
            if jni_return.startswith("["):
                actual_return_type = jni_return

        if needs_wrapping:
            code = f'''

    def {method_name}(self{", " + param_str if param_str else ""}) -> '{wrapped_class}Proxy':
        """Auto-generated method{" (overloaded)" if is_overloaded else ""}."""
        ref = self._ref._createRef(
            "{method_name}",
            "{signature}",
            {param_names + "," if param_names else ""}
            return_type="{actual_return_type}",
            declaring_class="{declaring_class}"
        )
        return {wrapped_class}Proxy(ref)'''
        else:
            code = f'''

    def {method_name}(self{", " + param_str if param_str else ""}) -> {display_return_type}:
        """Auto-generated method{" (overloaded)" if is_overloaded else ""}."""
        return self._ref._createRef(
            "{method_name}",
            "{signature}",
            {param_names + "," if param_names else ""}
            return_type="{actual_return_type}",
            declaring_class="{declaring_class}"
        )'''

        return code

    def generate_all_proxies(self) -> str:
        """Generate all proxy classes and return the complete Python code."""
        code = '''"""
Auto-generated proxy classes for RuneLite API Query Builder.
Generated from scraped API data - DO NOT EDIT MANUALLY.

This file is stored in ~/.cache/escape/generated/ and uses absolute imports.
"""

from __future__ import annotations
from typing import Any, List, Union, Optional, TYPE_CHECKING
from escape._internal.query_builder import QueryRef

if TYPE_CHECKING:
    from escape._internal.query_builder import Query


class ProxyBase(QueryRef):
    """Base class for all proxies with helper methods."""

    def _wrap_as_proxy(self, ref: QueryRef, proxy_class: type) -> Any:
        """Wrap a QueryRef as a specific proxy class for chaining."""
        proxy = proxy_class.__new__(proxy_class)
        proxy.query = ref.query
        proxy.ref_id = ref.ref_id
        proxy.source_ref = ref.source_ref
        proxy.return_type = ref.return_type
        return proxy


class StaticMethodProxy:
    """Proxy for calling static methods on a class."""

    def __init__(self, query, class_name: str):
        self._query = query
        self._class_name = class_name

    def __getattr__(self, method_name: str):
        """Return a callable that creates a static method call."""
        def static_method_caller(*args, **kwargs):
            signature = kwargs.pop('_signature', None)
            return_type = kwargs.pop('_return_type', None)
            return self._query.callStatic(
                self._class_name,
                method_name,
                *args,
                _signature=signature,
                _return_type=return_type
            )
        return static_method_caller


class ConstructorProxy:
    """Proxy for calling constructors."""

    def __init__(self, query, class_name: str, signature: str = None):
        self._query = query
        self._class_name = class_name
        self._signature = signature

    def __call__(self, *args, **kwargs):
        """Create an instance using the constructor."""
        signature = kwargs.pop('_signature', self._signature)
        return self._query.construct(self._class_name, *args, _signature=signature)

'''

        def get_dependencies(class_name: str) -> list[str]:
            """Get parent classes that need to be generated first."""
            deps = []
            simple_name = class_name.split(".")[-1]
            if simple_name in self.inheritance:
                inheritance_info = self.inheritance[simple_name]
                if "extends" in inheritance_info:
                    parent_class = inheritance_info["extends"]
                    if "," in parent_class:
                        parent_class = parent_class.split(",")[0].strip()
                    if parent_class in self.classes:
                        deps.append(parent_class)
            return deps

        sorted_classes = []
        remaining_classes = list(self.class_methods.keys())
        generated_set = set()

        while remaining_classes:
            made_progress = False
            for class_name in remaining_classes[:]:
                simple_name = class_name.split(".")[-1]
                deps = get_dependencies(class_name)

                if all(dep in generated_set for dep in deps):
                    sorted_classes.append(class_name)
                    generated_set.add(simple_name)
                    remaining_classes.remove(class_name)
                    made_progress = True

            if not made_progress and remaining_classes:
                sorted_classes.extend(remaining_classes)
                break

        generated_classes = set()

        for class_name in sorted_classes:
            methods = self._get_all_methods_including_inherited(class_name)
            simple_name = class_name.split(".")[-1]

            if simple_name in generated_classes:
                continue

            generated_classes.add(simple_name)
            class_code = self._generate_proxy_class(class_name, methods)
            code += class_code + "\n\n"

        code += '''

class QueryClassAccessor:
    """Provides dot-notation access to constructors and static methods."""

    def __init__(self, query):
        self._query = query

    def __getattr__(self, class_name: str):
        """Access a class for constructors or static methods."""
        return ClassAccessor(self._query, class_name)


class ClassAccessor:
    """Allows both constructor calls and static method access."""

    def __init__(self, query, class_name: str):
        self._query = query
        self._class_name = class_name

    def __call__(self, *args, **kwargs):
        """Call as constructor."""
        return self._query.construct(self._class_name, *args, **kwargs)

    def __getattr__(self, method_name: str):
        """Access static method."""
        def static_caller(*args, **kwargs):
            return self._query.callStatic(self._class_name, method_name, *args, **kwargs)
        return static_caller

'''

        code += """
PROXY_CLASSES = {"""

        for class_name in sorted(generated_classes):
            code += f"""
    "{class_name}": {class_name}Proxy,"""

        code += '''
}


def get_proxy_class(class_name: str) -> type:
    """Get a proxy class by name."""
    return PROXY_CLASSES.get(class_name, QueryRef)
'''

        return code

    def save_proxies(self, output_path: str):
        """Generate and save proxy classes to the specified file."""
        code = self.generate_all_proxies()

        with open(output_path, "w") as f:
            f.write(code)

        logger.success(f"Generated {len(self.class_methods)} proxy classes")
        logger.info(f"Saved to: {output_path}")

    def generate_constants(self) -> str:
        """Generate constant classes for ItemID, AnimationID, ObjectID, etc."""
        constants = self.api_data.get("constants", {})

        code = []
        code.append('"""')
        code.append("Auto-generated RuneLite API Constants")
        code.append("Generated from runelite_api_data.json")
        code.append("")
        code.append("Provides constants for ItemID, AnimationID, ObjectID, NpcID, etc.")
        code.append("Use these for type-safe, autocomplete-friendly constant access.")
        code.append("")
        code.append("Example:")
        code.append("    from src.generated.constants import ItemID")
        code.append("    inventory.contains(ItemID.CANNONBALL)")
        code.append('"""')
        code.append("")

        important_constants = {
            "net.runelite.api.ItemID": "ItemID",
            "net.runelite.api.ObjectID": "ObjectID",
            "net.runelite.api.AnimationID": "AnimationID",
            "net.runelite.api.NpcID": "NpcID",
            "NullItemID": "NullItemID",
            "NullObjectID": "NullObjectID",
            "NullNpcID": "NullNpcID",
            "Varbits": "Varbits",
            "VarPlayer": "VarPlayer",
            "VarClientInt": "VarClientInt",
            "VarClientStr": "VarClientStr",
            "net.runelite.api.SpriteID": "SpriteID",
            "HitsplatID": "HitsplatID",
            "GraphicID": "GraphicID",
            "ParamID": "ParamID",
            "StructID": "StructID",
        }

        for full_class_name, simple_name in important_constants.items():
            if full_class_name not in constants:
                continue

            class_constants = constants[full_class_name]

            code.append(f"class {simple_name}:")
            code.append('    """')
            code.append(f"    {simple_name} constants from RuneLite API.")
            code.append(f"    Total: {len(class_constants)} constants")
            code.append('    """')

            sorted_constants = sorted(class_constants.items(), key=lambda x: x[0])

            if not sorted_constants:
                code.append("    pass")
            else:
                for const_name, const_value in sorted_constants:
                    if isinstance(const_value, str):
                        escaped_value = const_value.replace("\\", "\\\\").replace('"', '\\"')
                        code.append(f'    {const_name} = "{escaped_value}"')
                    elif isinstance(const_value, int | float):
                        code.append(f"    {const_name} = {const_value}")
                    else:
                        code.append(f"    {const_name} = {const_value!r}")

            code.append("")
            code.append("")

        interface_ids = self.api_data.get("interface_ids", {})
        if interface_ids:
            code.append("class InterfaceID:")
            code.append('    """Widget interface IDs from RuneLite API."""')
            code.append("")

            groups = interface_ids.get("groups", {})
            if groups:
                sorted_groups = sorted(groups.items(), key=lambda x: x[1])
                for group_name, group_id in sorted_groups:
                    code.append(f"    {group_name} = {group_id}")
                code.append("")

            nested = interface_ids.get("nested", {})
            if nested:
                for class_name, widgets in sorted(nested.items()):
                    code.append(f"    class {class_name}:")
                    code.append(f'        """Widget constants for {class_name}."""')
                    sorted_widgets = sorted(widgets.items(), key=lambda x: x[1])
                    for widget_name, widget_id in sorted_widgets:
                        code.append(f"        {widget_name} = 0x{widget_id:08x}")
                    code.append("")

            code.append("")

        return "\n".join(code)

    def _generate_and_save_constant_file(
        self, full_class_name: str, simple_name: str, output_path: Path
    ) -> bool:
        """Generate and save a single constant class file."""
        constants = self.api_data.get("constants", {})
        if full_class_name not in constants:
            return False

        class_constants = constants[full_class_name]
        code = []
        code.append('"""')
        code.append(f"Auto-generated {simple_name} constants from RuneLite API")
        code.append("DO NOT EDIT MANUALLY")
        code.append('"""')
        code.append("")
        code.append(f"class {simple_name}:")
        code.append('    """')
        code.append(f"    {simple_name} constants from RuneLite API.")
        code.append(f"    Total: {len(class_constants):,} constants")
        code.append('    """')

        sorted_constants = sorted(class_constants.items(), key=lambda x: x[0])

        if not sorted_constants:
            code.append("    pass")
        else:
            for const_name, const_value in sorted_constants:
                if isinstance(const_value, str):
                    escaped_value = const_value.replace("\\", "\\\\").replace('"', '\\"')
                    code.append(f'    {const_name} = "{escaped_value}"')
                elif isinstance(const_value, int | float):
                    code.append(f"    {const_name} = {const_value}")
                else:
                    code.append(f"    {const_name} = {const_value!r}")

        with open(output_path, "w") as f:
            f.write("\n".join(code))

        return True

    def _generate_varbit_constants(self) -> str | None:
        """Generate VarClientInt and VarClientStr constants."""
        constants = self.api_data.get("constants", {})
        code = []
        code.append('"""Auto-generated VarClient constants from RuneLite API."""')
        code.append("")

        varbit_classes = ["VarClientInt", "VarClientStr"]

        found_any = False
        for class_name in varbit_classes:
            if class_name not in constants:
                continue

            found_any = True
            class_constants = constants[class_name]
            code.append(f"class {class_name}:")
            code.append(f'    """{class_name} constants from RuneLite API."""')

            sorted_constants = sorted(class_constants.items(), key=lambda x: x[0])
            if not sorted_constants:
                code.append("    pass")
            else:
                for const_name, const_value in sorted_constants:
                    if isinstance(const_value, int | float):
                        code.append(f"    {const_name} = {const_value}")
                    else:
                        code.append(f"    {const_name} = {const_value!r}")

            code.append("")
            code.append("")

        return "\n".join(code) if found_any else None

    def _generate_other_constants(self) -> str | None:
        """Generate NullItemID, NullObjectID, and NullNpcID constants."""
        constants = self.api_data.get("constants", {})
        code = []
        code.append('"""Auto-generated miscellaneous constants from RuneLite API."""')
        code.append("")

        other_classes = {
            "NullItemID": "NullItemID",
            "NullObjectID": "NullObjectID",
            "NullNpcID": "NullNpcID",
        }

        found_any = False
        for class_key, class_name in other_classes.items():
            if class_key not in constants:
                continue

            found_any = True
            class_constants = constants[class_key]
            code.append(f"class {class_name}:")
            code.append(f'    """{class_name} constants from RuneLite API."""')

            sorted_constants = sorted(class_constants.items(), key=lambda x: x[0])
            if not sorted_constants:
                code.append("    pass")
            else:
                for const_name, const_value in sorted_constants:
                    if isinstance(const_value, int | float):
                        code.append(f"    {const_name} = {const_value}")
                    else:
                        code.append(f"    {const_name} = {const_value!r}")

            code.append("")
            code.append("")

        return "\n".join(code) if found_any else None

    def _generate_item_id_constants(self) -> str | None:
        """Generate ItemID constants with nested Noted and Placeholder classes."""
        item_ids = self.api_data.get("constants", {}).get("net.runelite.api.gameval.ItemID")

        if not item_ids:
            return None

        code = []
        code.append('"""Auto-generated ItemID constants from RuneLite API (gameval)."""')
        code.append("")
        code.append("class ItemID:")
        code.append('    """Item IDs from RuneLite API."""')
        code.append("")

        main_items = item_ids.get("main", {})
        if main_items:
            sorted_items = sorted(main_items.items(), key=lambda x: x[0])
            for item_name, item_id in sorted_items:
                code.append(f"    {item_name} = {item_id}")
            code.append("")

        noted_items = item_ids.get("Noted", {})
        if noted_items:
            code.append("    class Noted:")
            code.append('        """Noted item IDs."""')
            sorted_noted = sorted(noted_items.items(), key=lambda x: x[0])
            for item_name, item_id in sorted_noted:
                code.append(f"        {item_name} = {item_id}")
            code.append("")

        placeholder_items = item_ids.get("Placeholder", {})
        if placeholder_items:
            code.append("    class Placeholder:")
            code.append('        """Placeholder item IDs."""')
            sorted_placeholder = sorted(placeholder_items.items(), key=lambda x: x[0])
            for item_name, item_id in sorted_placeholder:
                code.append(f"        {item_name} = {item_id}")
            code.append("")

        return "\n".join(code)

    def _generate_interface_id_constants(self) -> str | None:
        """Generate InterfaceID constants with nested widget classes."""
        interface_ids = self.api_data.get("interface_ids", {})
        if not interface_ids:
            return None

        code = []
        code.append('"""Auto-generated InterfaceID constants from RuneLite API."""')
        code.append("")
        code.append("class InterfaceID:")
        code.append('    """Widget interface IDs from RuneLite API."""')
        code.append("")

        groups = interface_ids.get("groups", {})
        if groups:
            sorted_groups = sorted(groups.items(), key=lambda x: x[1])
            for group_name, group_id in sorted_groups:
                code.append(f"    {group_name} = {group_id}")
            code.append("")

        nested = interface_ids.get("nested", {})
        if nested:
            for class_name, widgets in sorted(nested.items()):
                code.append(f"    class {class_name}:")
                code.append(f'        """Widget constants for {class_name}."""')
                sorted_widgets = sorted(widgets.items(), key=lambda x: x[1])
                for widget_name, widget_id in sorted_widgets:
                    code.append(f"        {widget_name} = 0x{widget_id:08x}")
                code.append("")

        return "\n".join(code)

    def _generate_sprite_id_constants(self) -> str | None:
        """Generate SpriteID constants with indexed and named sprites."""
        sprite_ids = self.api_data.get("sprite_ids", {})
        if not sprite_ids:
            return None

        code = []
        code.append('"""Auto-generated SpriteID constants from RuneLite API."""')
        code.append("")
        code.append("class SpriteID:")
        code.append('    """Sprite IDs from RuneLite API."""')
        code.append("")

        constants = sprite_ids.get("constants", {})
        if constants:
            sorted_constants = sorted(constants.items(), key=lambda x: x[1])
            for const_name, const_value in sorted_constants:
                code.append(f"    {const_name} = {const_value}")
            code.append("")

        nested = sprite_ids.get("nested", {})
        if nested:
            for class_name, sprites in sorted(nested.items()):
                code.append(f"    class {class_name}:")
                code.append(f'        """Sprite constants for {class_name}."""')

                indexed = {
                    k: v for k, v in sprites.items() if k.startswith("_") and k[1:].isdigit()
                }
                named = {
                    k: v for k, v in sprites.items() if not (k.startswith("_") and k[1:].isdigit())
                }

                if indexed:
                    sorted_indexed = sorted(indexed.items(), key=lambda x: int(x[0][1:]))
                    for sprite_name, sprite_id in sorted_indexed:
                        code.append(f"        {sprite_name} = {sprite_id}")

                if named:
                    if indexed:
                        code.append("")
                    sorted_named = sorted(named.items(), key=lambda x: x[1])
                    for sprite_name, sprite_id in sorted_named:
                        code.append(f"        {sprite_name} = {sprite_id}")

                code.append("")

        return "\n".join(code)

    def _generate_constants_init(self, files_created: list) -> str:
        """Generate __init__.py that imports all constant classes."""
        code = []
        code.append('"""RuneLite API Constants Package."""')
        code.append("")

        if "ItemID" in files_created:
            code.append("from .item_id import ItemID")
        if "ObjectID" in files_created:
            code.append("from .object_id import ObjectID")
        if "NpcID" in files_created:
            code.append("from .npc_id import NpcID")
        if "AnimationID" in files_created:
            code.append("from .animation_id import AnimationID")
        if "VarClient" in files_created:
            code.append("from .varclient import VarClientInt, VarClientStr")
        if "VarClientID" in files_created:
            code.append("from .varclient_id import VarClientID")
        if "InterfaceID" in files_created:
            code.append("from .interface_id import InterfaceID")
        if "SpriteID" in files_created:
            code.append("from .sprite_id import SpriteID")

        code.append("")
        code.append("__all__ = [")
        for module in files_created:
            if module not in ("VarClient",):
                code.append(f'    "{module}",')
        if "VarClient" in files_created:
            code.append('    "VarClientInt",')
            code.append('    "VarClientStr",')
        code.append("]")

        return "\n".join(code)

    def _generate_constants_wrapper(self) -> str:
        """Generate wrapper file that re-exports all constants."""
        code = []
        code.append('"""RuneLite API Constants Wrapper."""')
        code.append("")
        code.append("from .constants import *")
        code.append("")
        code.append("__all__ = [")
        code.append('    "ItemID",')
        code.append('    "ObjectID",')
        code.append('    "NpcID",')
        code.append('    "AnimationID",')
        code.append('    "InterfaceID",')
        code.append('    "VarClientInt",')
        code.append('    "VarClientStr",')
        code.append('    "VarClientID",')
        code.append("]")

        return "\n".join(code)

    def save_constants(self, output_path: str):
        """Generate and save constants to separate files in a constants/ subdirectory."""
        logger.info("\n Generating constants files")

        output_dir = Path(output_path).parent / "constants"
        output_dir.mkdir(parents=True, exist_ok=True)

        files_created = []

        item_id_code = self._generate_item_id_constants()
        if item_id_code:
            with open(output_dir / "item_id.py", "w") as f:
                f.write(item_id_code)
            files_created.append("ItemID")
        elif self._generate_and_save_constant_file(
            "net.runelite.api.ItemID", "ItemID", output_dir / "item_id.py"
        ):
            files_created.append("ItemID")

        if self._generate_and_save_constant_file(
            "net.runelite.api.ObjectID", "ObjectID", output_dir / "object_id.py"
        ):
            files_created.append("ObjectID")

        if self._generate_and_save_constant_file(
            "net.runelite.api.NpcID", "NpcID", output_dir / "npc_id.py"
        ):
            files_created.append("NpcID")

        if self._generate_and_save_constant_file(
            "net.runelite.api.AnimationID", "AnimationID", output_dir / "animation_id.py"
        ):
            files_created.append("AnimationID")

        varclient_code = self._generate_varbit_constants()
        if varclient_code:
            with open(output_dir / "varclient.py", "w") as f:
                f.write(varclient_code)
            files_created.append("VarClient")

        if self._generate_and_save_constant_file(
            "VarClientID", "VarClientID", output_dir / "varclient_id.py"
        ):
            files_created.append("VarClientID")

        interface_code = self._generate_interface_id_constants()
        if interface_code:
            with open(output_dir / "interface_id.py", "w") as f:
                f.write(interface_code)
            files_created.append("InterfaceID")

        sprite_code = self._generate_sprite_id_constants()
        if sprite_code:
            with open(output_dir / "sprite_id.py", "w") as f:
                f.write(sprite_code)
            files_created.append("SpriteID")

        init_code = self._generate_constants_init(files_created)
        with open(output_dir / "__init__.py", "w") as f:
            f.write(init_code)

        wrapper_code = self._generate_constants_wrapper()
        with open(output_path, "w") as f:
            f.write(wrapper_code)

        total_size = sum(f.stat().st_size for f in output_dir.glob("*.py")) / 1024
        logger.success(
            f"Generated {len(files_created)} constant modules ({total_size:.1f} KB total)"
        )
        logger.info(f"Files: {', '.join(files_created)}")
        logger.success(f"Created wrapper at {output_path}")


def main():
    """Generate constants from API data."""
    from ..cache_manager import get_cache_manager

    cache_manager = get_cache_manager()
    api_data_path = cache_manager.get_data_path("api") / "runelite_api_data.json"

    generated_dir = cache_manager.generated_dir
    constants_output_path = generated_dir / "constants.py"

    generated_dir.mkdir(parents=True, exist_ok=True)

    generator = ProxyGenerator(str(api_data_path))
    generator.save_constants(str(constants_output_path))

    constants = generator.api_data.get("constants", {})
    total_constants = sum(len(v) for v in constants.values())
    logger.info("\n Constants Statistics")
    logger.info(f"Total constant values: {total_constants}")
    logger.info("Constant classes generated: ItemID, ObjectID, AnimationID, NpcID, and more")


if __name__ == "__main__":
    main()
