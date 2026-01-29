#!/usr/bin/env python3
"""
RuneLite API Wrapper - Data-Driven Universal Bridge Interface.

Uses perfect type conversion data from the scraper for zero-maintenance operation.
Now with type-safe enum support to prevent int/enum confusion.
"""

import json
import mmap
import os
import struct
import time
from typing import Any, cast

from escape._internal.logger import logger

from .batch import Batch

# Import enum support
try:
    from .enums import EnumValue, generate_all_enum_classes
except ImportError:
    logger.warning("runelite_enums module not found - enum support disabled")
    EnumValue = None
    generate_all_enum_classes = None


class RuneLiteAPI:
    """Smart API wrapper that uses scraped data to provide exact signatures."""

    _instance = None

    def __new__(cls, api_data_file: str | None = None, auto_update: bool = True):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __del__(self):
        """Cleanup when API object is destroyed."""
        # Disabled auto-cleanup to prevent issues
        pass

    def __init__(self, api_data_file: str | None = None, auto_update: bool = True):
        """Load API data and connect to bridge."""
        # Skip if already initialized
        if self._initialized:
            return
        self._initialized = True

        self.api_channel = None
        self.result_buffer = None
        self.cached_objects = {}
        self.enum_classes = {}  # Store generated enum classes
        self.plugin_data = None  # Plugin API data (loaded separately)

        # Always use the JSON file with perfect type conversion data
        if api_data_file is None:
            # Look for data file in cache directory
            from .cache_manager import get_cache_manager

            cache_manager = get_cache_manager()
            api_data_file = str(cache_manager.get_data_path("api") / "runelite_api_data.json")

        # Check for updates if enabled
        if auto_update:
            self._check_and_update()

        # Load scraped API data with perfect type conversion
        try:
            # Convert Path to string if needed
            api_data_file = str(api_data_file)

            # Get the full path to the data file
            if not os.path.isabs(api_data_file):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                api_data_file = os.path.join(script_dir, api_data_file)

            if not os.path.exists(api_data_file):
                raise FileNotFoundError(f"API data file not found: {api_data_file}")

            with open(api_data_file) as f:
                self.api_data = json.load(f)

            # Check if we have the perfect type conversion data
            if "type_conversion" in self.api_data:
                type_count = self.api_data["type_conversion"]["conversion_lookup"]["type_count"]
                logger.success(
                    f"Loaded perfect API data: {len(self.api_data['methods'])} methods, {len(self.api_data['enums'])} enums, {type_count} types"
                )
            else:
                logger.success(
                    f"Loaded API data: {len(self.api_data['methods'])} methods, {len(self.api_data['enums'])} enums"
                )
                logger.warning("No type conversion data found - regenerate with latest scraper")

            # Generate enum classes from API data
            if generate_all_enum_classes:
                self.enum_classes = generate_all_enum_classes(self.api_data)
                logger.success(f"Generated {len(self.enum_classes)} enum classes")

                # Make enums accessible as attributes for convenience
                for enum_name, enum_class in self.enum_classes.items():
                    setattr(self, enum_name, enum_class)
            else:
                logger.warning("Enum generation not available")

        except Exception as e:
            logger.error(f"Failed to load API data: {e}")
            logger.info(f"Current directory: {os.getcwd()}")
            logger.info(f"Looking for: {api_data_file}")
            self.api_data = {
                "methods": {},
                "enums": {},
                "classes": [],
                "constants": {},
                "type_conversion": {},
            }

        # Load plugin API data (shortest-path plugin, etc.)
        self._load_plugin_data()

    def _load_plugin_data(self):
        """Load plugin API data from scraped plugin files."""
        try:
            from .cache_manager import get_cache_manager

            cache_manager = get_cache_manager()
            plugin_data_file = cache_manager.get_data_path("api") / "shortestpath_api_data.json"

            if plugin_data_file.exists():
                with open(plugin_data_file) as f:
                    self.plugin_data = json.load(f)
                logger.success(
                    f"Loaded plugin data: {len(self.plugin_data.get('methods', {}))} methods from {len(self.plugin_data.get('classes', []))} classes"
                )
            else:
                logger.warning("Plugin data not found - plugin queries will not be available")
                self.plugin_data = None

        except Exception as e:
            logger.warning(f"Failed to load plugin data: {e}")
            self.plugin_data = None

    def _check_and_update(self):
        """Check for RuneLite API updates and regenerate if needed."""
        try:
            # Import auto_updater (absolute import to avoid issues)
            from escape._internal.updater.api import RuneLiteAPIUpdater

            updater = RuneLiteAPIUpdater()

            # Check if update is needed
            needs_update, reason = updater.should_update(force=False, max_age_days=7)

            if needs_update:
                logger.info("RuneLite API Update")
                logger.info(f"{reason}")

                # Run the update
                success = updater.update(force=False, max_age_days=7)

                if success:
                    logger.success("API data generated successfully")
                else:
                    logger.error("API update failed")
                    raise FileNotFoundError("API update failed - cannot continue")

        except ImportError as e:
            # auto_updater not available, skip update check
            logger.warning(f"API updater not available: {e}")
        except FileNotFoundError:
            # Re-raise file not found errors
            raise
        except Exception as e:
            logger.warning(f"Auto-update check failed: {e}")
            import traceback

            traceback.print_exc()

    def __enter__(self):
        """Context manager entry - connect to bridge."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Don't suppress exceptions
        return False

    def connect(self) -> bool:
        """Connect to the universal bridge"""
        try:
            # File handles kept open intentionally - mmap requires fd to stay open
            self.api_fd = open("/dev/shm/runelite_api_universal", "r+b")  # noqa: SIM115
            self.api_channel = mmap.mmap(
                self.api_fd.fileno(), 16 * 1024 * 1024
            )  # 16MB to match C side

            self.result_fd = open("/dev/shm/runelite_results_universal", "r+b")  # noqa: SIM115
            self.result_buffer = mmap.mmap(
                self.result_fd.fileno(), 16 * 1024 * 1024
            )  # 16MB to match C side

            logger.success("Connected to bridge")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def _parse_signature_params(self, signature: str) -> list[str]:
        """Parse JNI signature and extract all parameter types."""
        params_str = signature[signature.index("(") + 1 : signature.index(")")]
        if not params_str:
            return []

        param_types = []
        i = 0
        while i < len(params_str):
            if params_str[i] == "L":
                # Object type - find semicolon
                end = params_str.index(";", i)
                param_types.append(params_str[i : end + 1])
                i = end + 1
            elif params_str[i] == "[":
                # Array type - consume all array dimensions
                j = i
                while j < len(params_str) and params_str[j] == "[":
                    j += 1
                if j < len(params_str) and params_str[j] == "L":
                    end = params_str.index(";", j)
                    param_types.append(params_str[i : end + 1])
                    i = end + 1
                else:
                    param_types.append(params_str[i : j + 1])
                    i = j + 1
            else:
                # Primitive type - single character
                param_types.append(params_str[i])
                i += 1

        return param_types

    def _fix_widget_path(self, signature: str) -> str:
        """Fix Widget class path in signature (should be in widgets package)."""
        if "Widget" not in signature:
            return signature
        return (
            signature.replace("Lnet/runelite/api/Widget;", "Lnet/runelite/api/widgets/Widget;")
            .replace("[Lnet/runelite/api/Widget;", "[Lnet/runelite/api/widgets/Widget;")
            .replace("[[Lnet/runelite/api/Widget;", "[[Lnet/runelite/api/widgets/Widget;")
        )

    def _normalize_class_name(self, class_name: str) -> str:
        """Normalize class name to full JNI path format."""
        # Convert dots to slashes
        normalized = class_name.replace(".", "/")

        # If already a full path, return it
        if "/" in normalized:
            return normalized

        # Look up full path from class_packages
        if "class_packages" in self.api_data:
            package_path = self.api_data["class_packages"].get(normalized)
            if package_path:
                return f"{package_path}/{normalized}"

        # Try common packages as fallback
        if normalized in ["WorldPoint", "LocalPoint", "WorldArea"]:
            return f"net/runelite/api/coords/{normalized}"

        return f"net/runelite/api/{normalized}"

    def _find_method_in_hierarchy(
        self, method_name: str, target_class: str, signatures: list
    ) -> list:
        """Find method signatures by walking up the inheritance tree."""
        # Extract simple class name for inheritance lookup
        simple_target = target_class.split("/")[-1]

        # Try exact match first
        filtered = [
            (item[0], item[1], item[2] if len(item) > 2 else None)
            for item in signatures
            if item[0] == target_class
        ]

        if filtered or "inheritance" not in self.api_data:
            return filtered

        # Walk up inheritance tree
        inheritance = self.api_data["inheritance"]
        current = simple_target
        seen = set()

        while current and current not in seen:
            seen.add(current)
            if current in inheritance and "extends" in inheritance[current]:
                parent = inheritance[current]["extends"]
                # Handle multiple inheritance - take first parent
                if "," in parent:
                    parent = parent.split(",")[0].strip()

                # Try to find method in parent class
                filtered = [
                    (item[0], item[1], item[2] if len(item) > 2 else None)
                    for item in signatures
                    if item[0].endswith("/" + parent)
                ]

                if filtered:
                    return filtered

                current = parent
            else:
                break

        return []

    def get_method_signature(
        self, method_name: str, args: list | None = None, target_class: str = "Client"
    ) -> str | None:
        """Get the correct JNI signature for a method based on arguments."""
        info = self.get_method_info(method_name, args, target_class)
        return info["signature"] if info else None

    def get_method_info(
        self, method_name: str, args: list | None = None, target_class: str | None = "Client"
    ) -> dict | None:
        """Get signature, declaring_class, and return_type for a method."""
        # Default to "Client" if None
        if target_class is None:
            target_class = "Client"

        # Check if target_class is a plugin class (contains "shortestpath")
        is_plugin_class = target_class and "shortestpath" in target_class

        # Choose which data source to use
        methods_data = (
            self.plugin_data.get("methods", {})
            if is_plugin_class and self.plugin_data
            else self.api_data["methods"]
        )

        if method_name not in methods_data:
            return None

        signatures = methods_data[method_name]

        # Filter by class if specified and not None/empty
        if target_class:
            normalized_target = self._normalize_class_name(target_class)
            filtered = self._find_method_in_hierarchy(method_name, normalized_target, signatures)

            if filtered:
                signatures = filtered
            elif target_class:  # Explicitly filtered but found nothing
                return None

        # Find best matching signature based on arguments
        if args is not None:
            best_match = None
            best_score = -1

            for item in signatures:
                cls, sig = item[0], item[1]
                ret_type = item[2] if len(item) > 2 else None
                score = self._score_signature_match(sig, args)

                if score > best_score:
                    best_score = score
                    best_match = {
                        "signature": self._fix_widget_path(sig),
                        "declaring_class": cls,
                        "return_type": ret_type,
                    }

            return best_match if best_match and best_score >= 0 else None

        # Fallback to first signature (no args provided)
        if signatures:
            first = signatures[0]
            return {
                "signature": self._fix_widget_path(first[1]),
                "declaring_class": first[0],
                "return_type": first[2] if len(first) > 2 else None,
            }

        return None

    def _score_signature_match(self, signature: str, args: list) -> int:
        """Score how well arguments match a signature (-1 = no match)."""
        # Extract parameter types from signature (using consolidated parser)
        param_types = self._parse_signature_params(signature)

        # Check argument count
        if len(args) != len(param_types):
            return -1

        score = 0
        for arg, param_type in zip(args, param_types, strict=False):
            arg_score = self._score_arg_match(arg, param_type)
            if arg_score < 0:
                return -1  # Invalid match
            score += arg_score

        return score

    def _score_arg_match(self, arg: Any, param_type: str) -> int:
        """Score how well a single argument matches a parameter type."""
        # Special 'client' proxy
        if hasattr(arg, "ref_id") and arg.ref_id == "client":
            if param_type == "Lnet/runelite/api/Client;":
                return 100  # Perfect match
            elif param_type == "Ljava/lang/Object;":
                return 50  # Compatible
            return -1  # Not compatible

        # QueryRef or proxy object with return_type
        if hasattr(arg, "return_type") and arg.return_type:
            if param_type.startswith("L") and param_type.endswith(";"):
                expected_jni = f"L{arg.return_type.replace('.', '/')};".replace("//", "/")
                if expected_jni == param_type:
                    return 100  # Perfect match
                elif param_type == "Ljava/lang/Object;":
                    return 50  # Object is compatible
                return 20  # Possible subclass/interface match
            return -1  # QueryRef but expecting primitive

        # EnumValue for enum parameter
        if EnumValue and isinstance(arg, EnumValue):
            if param_type.startswith("L") and param_type.endswith(";"):
                expected_enum = param_type[1:-1].split("/")[-1]
                return 100 if arg._enum_name == expected_enum else -1
            return -1  # Not an object type

        # Primitive types
        if isinstance(arg, int):
            if param_type == "I":
                return 100  # Perfect int match
            # Check if int could be enum ordinal (discouraged but allowed)
            if param_type.startswith("Lnet/runelite/api/") and param_type.endswith(";"):
                enum_name = param_type[1:-1].split("/")[-1]
                if enum_name in self.api_data.get("enums", {}):
                    enum_values = self.api_data["enums"][enum_name].get("values", [])
                    return 10 if 0 <= arg < len(enum_values) else -1
                return 5  # Unknown enum, might work
            return -1

        if isinstance(arg, str):
            if param_type == "Ljava/lang/String;":
                return 100  # Perfect string match
            return -1  # String not allowed for other types

        # No match
        return -1

    def convert_argument(
        self, arg_value: Any, signature: str, arg_index: int = 0
    ) -> tuple[str, str]:
        """Convert argument to (type, value) tuple using scraped type data."""
        # FIRST: Check if it's an EnumValue object - this takes priority!
        if EnumValue and isinstance(arg_value, EnumValue):
            return (arg_value._enum_name, str(arg_value._ordinal))

        # Extract the JNI type for this parameter from the signature (using consolidated parser)
        param_types = self._parse_signature_params(signature)
        if arg_index >= len(param_types):
            return ("int", str(arg_value))

        jni_type = param_types[arg_index]

        # Use the perfect type conversion database if available
        if "type_conversion" in self.api_data and "all_types" in self.api_data["type_conversion"]:
            type_info = self.api_data["type_conversion"]["all_types"].get(jni_type)

            if type_info:
                return self._convert_by_category(arg_value, jni_type, type_info)

        # Fallback for when perfect data isn't available
        return self._convert_fallback(arg_value, jni_type)

    def _convert_by_category(
        self, arg_value: Any, jni_type: str, type_info: dict
    ) -> tuple[str, str]:
        """Convert argument based on type category from API data."""
        category = type_info["category"]

        if category == "primitive":
            if isinstance(arg_value, int) and jni_type == "I":
                return ("int", str(arg_value))
            return (type_info["bridge_type"], str(arg_value))

        elif category == "enum":
            enum_name = type_info["bridge_type"]
            if isinstance(arg_value, str):
                raise TypeError(
                    f"Expected {enum_name} enum object, got string '{arg_value}'.\n"
                    f"Use: api.{enum_name}.{arg_value.upper()} or api.{enum_name}.from_name('{arg_value}')"
                )
            elif isinstance(arg_value, int):
                raise TypeError(
                    f"Expected {enum_name} enum object, got integer {arg_value}.\n"
                    f"Use: api.{enum_name}.from_ordinal({arg_value}) or api.{enum_name}[{arg_value}]"
                )
            return (type_info["bridge_type"], str(arg_value))

        elif category == "java":
            bridge_type = type_info["bridge_type"]
            if bridge_type == "String":
                return ("String", str(arg_value))
            elif bridge_type == "Boolean":
                return ("Boolean", "true" if arg_value else "false")
            return (bridge_type, str(arg_value))

        elif category == "object":
            if isinstance(arg_value, str) and arg_value.startswith("obj_"):
                return ("object", arg_value)
            return ("object", str(arg_value))

        elif category == "array":
            return ("array", str(arg_value))

        return ("object", str(arg_value))

    def _convert_fallback(self, arg_value: Any, jni_type: str) -> tuple[str, str]:
        """Fallback conversion when type_conversion data isn't available."""
        if isinstance(arg_value, int):
            if jni_type == "I":
                return ("int", str(arg_value))
            elif jni_type == "J":
                return ("long", str(arg_value))
            return ("int", str(arg_value))

        # Map JNI types to bridge types
        type_map = {
            "I": "int",
            "B": "int",
            "S": "int",
            "C": "int",
            "J": "long",
            "Z": "boolean",
            "F": "float",
            "D": "float",
            "Ljava/lang/String;": "String",
        }

        bridge_type = type_map.get(jni_type, "object")

        if bridge_type == "boolean":
            return (bridge_type, "true" if arg_value else "false")

        return (bridge_type, str(arg_value))

    def get_static_method_signature(
        self, class_name: str, method_name: str, args: tuple[Any, ...]
    ) -> str | None:
        """Get static method signature."""
        return self.get_method_signature(
            method_name, list(args), target_class=class_name.split(".")[-1]
        )

    def get_enum_value(self, enum_name: str, ordinal: int) -> str | None:
        """Get enum constant name from ordinal using perfect data"""
        if "type_conversion" in self.api_data:
            # Search for enum in all packages
            for jni_sig, enum_info in self.api_data["type_conversion"]["enums"].items():
                # Check if this is the enum we're looking for (by simple name)
                if jni_sig.endswith(f"/{enum_name};"):
                    return enum_info.get("ordinal_to_name", {}).get(ordinal)
        return None

    def get_enum_ordinal(self, enum_name: str, value_name: str) -> int | None:
        """Get enum ordinal from constant name using perfect data"""
        if "type_conversion" in self.api_data:
            # Search for enum in all packages
            for jni_sig, enum_info in self.api_data["type_conversion"]["enums"].items():
                # Check if this is the enum we're looking for (by simple name)
                if jni_sig.endswith(f"/{enum_name};"):
                    return enum_info.get("name_to_ordinal", {}).get(value_name.upper())
        return None

    def get_enum(self, enum_name: str) -> type | None:
        """Get an enum class by name"""
        return self.enum_classes.get(enum_name)

    def list_enums(self) -> list[str]:
        """List all available enum names"""
        return sorted(self.enum_classes.keys())

    def query(self) -> Batch:
        """Create a query for API operations."""
        return Batch(self)

    def _send_request(self, encoded_data: bytes) -> None:
        """Send encoded request to bridge via shared memory."""
        if self.api_channel is None or self.result_buffer is None:
            raise RuntimeError("Not connected to bridge - call connect() first")
        api_channel = self.api_channel
        result_buffer = self.result_buffer

        # Wait for bridge to clear pending from previous request (max 10ms)
        wait_start = time.perf_counter()
        while (time.perf_counter() - wait_start) * 1000 < 10:
            api_channel.seek(0)
            old_pending = struct.unpack("<I", api_channel.read(4))[0]
            if old_pending == 0:
                break
            time.sleep(0.0001)  # 100μs

        # Clear result buffer header
        result_buffer.seek(0)
        result_buffer.write(struct.pack("<IIII", 0, 0, 0, 0))

        # Write request data
        api_channel.seek(8)
        api_channel.write(struct.pack("<I", len(encoded_data)))
        api_channel.seek(16)
        api_channel.write(encoded_data)

        # Set request ready
        api_channel.seek(0)
        api_channel.write(struct.pack("<II", 1, 0))  # pending=1, ready=0

    def _wait_for_response(self, timeout_ms: int = 10000) -> bytes | None:
        """Wait for response from bridge with exponential backoff polling."""
        if self.api_channel is None or self.result_buffer is None:
            raise RuntimeError("Not connected to bridge - call connect() first")
        api_channel = self.api_channel
        result_buffer = self.result_buffer

        start_time = time.perf_counter()
        poll_count = 0

        while (time.perf_counter() - start_time) * 1000 < timeout_ms:
            result_buffer.seek(4)
            ready = struct.unpack("<I", result_buffer.read(4))[0]

            if ready == 1:
                elapsed = (time.perf_counter() - start_time) * 1000
                if elapsed > 100:
                    logger.debug(f"Response ready after {elapsed:.2f}ms (polls={poll_count})")

                # Read response
                result_buffer.seek(0)
                size = struct.unpack("<I", result_buffer.read(4))[0]

                if size == 0:
                    logger.error(
                        f"DEBUG: ready=1 but size=0 after {elapsed:.2f}ms (polls={poll_count})"
                    )
                    logger.info("This means C set ready flag but didn't write response data")
                    # Clear ready flag anyway
                    result_buffer.seek(4)
                    result_buffer.write(struct.pack("<I", 0))
                    return None

                if size > 0:
                    result_buffer.seek(16)
                    # Read the full buffer size to check for magic header
                    data = result_buffer.read(size)

                    # Check if there's a magic header and adjust data if needed
                    if len(data) >= 8:
                        magic = struct.unpack("<I", data[:4])[0]
                        if magic == 0xDEADBEEF:
                            # Only return the actual message data (header + message)
                            msg_size = struct.unpack("<I", data[4:8])[0]
                            data = data[: 8 + msg_size]

                    # Clear ready flag
                    result_buffer.seek(4)
                    result_buffer.write(struct.pack("<I", 0))

                    return data

                return None

            # Exponential backoff polling
            poll_count += 1
            if poll_count < 5000:
                pass  # Busy wait for ~1.5ms
            elif poll_count < 10000:
                time.sleep(0.00001)  # 10μs sleep
            elif poll_count < 20000:
                time.sleep(0.0001)  # 100μs sleep
            else:
                time.sleep(0.001)  # 1ms sleep

        # Timeout
        elapsed = (time.perf_counter() - start_time) * 1000
        api_channel.seek(0)
        query_pending = struct.unpack("i", api_channel.read(4))[0]
        logger.warning(
            f"TIMEOUT after {elapsed:.2f}ms (polls={poll_count}, pending={query_pending})"
        )
        return None

    def _decode_msgpack_response(self, data: bytes) -> Any:
        """Decode MessagePack response, handling magic header if present."""
        import msgpack

        if len(data) >= 8:
            magic = struct.unpack("<I", data[:4])[0]
            if magic == 0xDEADBEEF:
                msg_size = struct.unpack("<I", data[4:8])[0]
                # Data was already trimmed in _wait_for_response, so just decode
                return msgpack.unpackb(data[8 : 8 + msg_size], raw=False, strict_map_key=False)

        # No magic header - decode directly
        # Data was already trimmed in _wait_for_response if it had a magic header
        return msgpack.unpackb(data, raw=False, strict_map_key=False)

    def execute_batch_query(self, operations: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute a batch query using MessagePack v2 protocol."""
        if not self.api_channel or not self.result_buffer:
            raise RuntimeError("Not connected to bridge - call connect() first")

        import msgpack

        # Encode and send request
        encoded = msgpack.packb(operations)
        if encoded is None:
            raise RuntimeError("Failed to encode operations with msgpack")
        self._send_request(cast("bytes", encoded))

        # Wait for and decode response
        data = self._wait_for_response(timeout_ms=2500)
        if not data:
            return {"error": "Timeout waiting for batch response", "success": False}

        try:
            results = self._decode_msgpack_response(data)

            # Handle error responses from bridge
            if isinstance(results, dict) and "error" in results:
                return {"error": results.get("error"), "success": False, "results": None}

            # Normal response - ensure it's a list
            response = {
                "results": results if isinstance(results, list) else [results],
                "success": True,
            }

            # Cache object references
            if response.get("results"):
                for result in response["results"]:
                    if isinstance(result, dict) and "_ref" in result:
                        self.cached_objects[result["_ref"]] = result

            return response

        except Exception as e:
            return {"error": f"Failed to decode response: {e}", "success": False, "results": None}

    def invoke_custom_method(
        self,
        target: str,
        method: str,
        signature: str,
        args: list[Any] | None = None,
        async_exec: bool = False,
        declaring_class: str | None = None,
    ) -> Any:
        """Invoke a custom Java method directly."""
        operation = {
            "async": async_exec,
            "target": target,
            "method": method,
            "signature": signature,
            "args": args if args is not None else [],
        }
        if declaring_class:
            operation["declaring_class"] = declaring_class

        response = self.execute_batch_query([operation])

        if not response.get("success"):
            error = response.get("error", "Unknown error")
            raise RuntimeError(f"Custom method invocation failed: {error}")

        results = response.get("results", [])
        if not results:
            return None

        return results[0]
