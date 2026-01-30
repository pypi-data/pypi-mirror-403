"""Batch client for RuneLite API operations."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .api import RuneLiteAPI


class BatchOperation:
    """Single operation in a batch request."""

    __slots__ = ("args", "declaring_class", "method", "ref", "signature", "target")

    def __init__(
        self,
        ref: str,
        method: str,
        signature: str,
        declaring_class: str,
        target: str | None = None,
        args: list[Any] | None = None,
    ):
        self.ref = ref
        self.target = target
        self.method = method
        self.signature = signature
        self.declaring_class = declaring_class
        self.args = args or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref": self.ref,
            "target": self.target,
            "method": self.method,
            "signature": self.signature,
            "declaring_class": self.declaring_class,
            "args": self.args,
        }


class BatchRef:
    """Reference to a batch result, supports method chaining."""

    __slots__ = ("_batch", "_ref_id", "_return_type")

    def __init__(self, batch: "Batch", ref_id: str, return_type: str | None = None):
        self._batch = batch
        self._ref_id = ref_id
        self._return_type = return_type

    @property
    def ref_id(self) -> str:
        return self._ref_id

    @property
    def return_type(self) -> str | None:
        return self._return_type

    def __getattr__(self, method_name: str):
        if method_name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{method_name}'")

        def method_call(*args) -> "BatchRef":
            return self._batch._add_method_call(
                target_ref=self._ref_id,
                target_type=self._return_type,
                method_name=method_name,
                args=list(args),
            )

        return method_call


class Batch:
    """
    Batch builder for RuneLite API operations.

    Usage:
        batch = api.batch()
        varps = batch.client.getServerVarps()
        result = batch.execute({"varps": varps})
    """

    def __init__(self, api: "RuneLiteAPI"):
        self._api = api
        self._operations: list[BatchOperation] = []
        self._ref_counter = 1

    @property
    def client(self) -> BatchRef:
        return BatchRef(self, "client", "net/runelite/api/Client")

    def _next_ref(self) -> str:
        ref_id = f"r{self._ref_counter}"
        self._ref_counter += 1
        return ref_id

    def _add_method_call(
        self,
        target_ref: str,
        target_type: str | None,
        method_name: str,
        args: list[Any],
    ) -> BatchRef:
        method_info = self._api.get_method_info(method_name, args, target_class=target_type)

        if not method_info:
            raise ValueError(f"Method '{method_name}' not found for type '{target_type}'")

        ref_id = self._next_ref()

        op = BatchOperation(
            ref=ref_id,
            target=target_ref if target_ref != "client" else None,
            method=method_name,
            signature=method_info["signature"],
            declaring_class=method_info["declaring_class"],
            args=self._convert_args(args),
        )
        self._operations.append(op)

        return_type = self._extract_return_type(method_info["signature"])
        return BatchRef(self, ref_id, return_type)

    def _convert_args(self, args: list[Any]) -> list[Any]:
        converted = []
        for arg in args:
            if isinstance(arg, BatchRef):
                converted.append({"$ref": arg.ref_id})
            elif hasattr(arg, "_enum_name") and hasattr(arg, "_ordinal"):
                converted.append({"$enum": {"class": arg._enum_name, "ordinal": arg._ordinal}})
            elif isinstance(arg, set):
                converted.append(list(arg))
            else:
                converted.append(arg)
        return converted

    def _extract_return_type(self, signature: str) -> str | None:
        paren_end = signature.rfind(")")
        if paren_end >= 0:
            ret_sig = signature[paren_end + 1 :]
            if ret_sig.startswith("L") and ret_sig.endswith(";"):
                return ret_sig[1:-1]
            elif ret_sig.startswith("["):
                return ret_sig
        return None

    def execute(self, selections: dict[str, "BatchRef"]) -> dict[str, Any]:
        if not self._operations:
            return {"success": True, "results": {}}

        wire_ops = [op.to_dict() for op in self._operations]
        response = self._api.execute_batch_query(wire_ops)

        if not response.get("success"):
            return {
                "success": False,
                "error": response.get("error", "Unknown error"),
                "results": None,
            }

        ref_to_index = {op.ref: i for i, op in enumerate(self._operations)}
        results = response.get("results", [])

        filtered = {}
        for name, ref in selections.items():
            if ref.ref_id in ref_to_index:
                index = ref_to_index[ref.ref_id]
                filtered[name] = results[index] if index < len(results) else None
            else:
                filtered[name] = None

        return {"success": True, "results": filtered}
