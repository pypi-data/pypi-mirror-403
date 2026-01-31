# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
GridSeal: Verification and compliance-grade audit logging for LLM applications.

GridSeal sits between your AI systems and their outputs, providing:
- Hallucination detection via verification checks
- Immutable audit trails with hash chain integrity
- Compliance-grade logging for FedRAMP, NIST AI RMF, EU AI Act
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, ParamSpec, TypeVar

from gridseal._version import __version__
from gridseal.audit import AuditStore
from gridseal.core import (
    AdapterError,
    AuditConfig,
    AuditError,
    AuditRecord,
    CheckResult,
    ConfigurationError,
    GridSealConfig,
    GridSealError,
    IntegrityError,
    RequestContext,
    VerificationConfig,
    VerificationError,
    VerificationResult,
    clear_context,
    get_context,
    parse_config,
    set_context,
)
from gridseal.verification import VerificationEngine

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

__all__ = [
    "__version__",
    "GridSeal",
    "CheckResult",
    "VerificationResult",
    "AuditRecord",
    "GridSealConfig",
    "VerificationConfig",
    "AuditConfig",
    "GridSealError",
    "ConfigurationError",
    "VerificationError",
    "AuditError",
    "AdapterError",
    "IntegrityError",
    "VerificationEngine",
    "AuditStore",
]


class GridSeal:
    """
    Main entry point for GridSeal verification and audit logging.

    GridSeal can operate in two modes:

    1. Standalone Mode (default):
       Full verification and audit logging.

    2. Adapter Mode:
       Adds compliance layer on top of existing observability tools.
    """

    def __init__(
        self,
        mode: str | None = None,
        verification: dict[str, Any] | VerificationConfig | None = None,
        audit: dict[str, Any] | AuditConfig | None = None,
        adapter: Any = None,
    ) -> None:
        """
        Initialize GridSeal.

        Args:
            mode: Operating mode ("standalone" or "adapter")
            verification: Verification configuration
            audit: Audit configuration
            adapter: Adapter instance for adapter mode
        """
        self.config = parse_config(mode=mode, verification=verification, audit=audit)
        self.engine = VerificationEngine(self.config.verification)
        self.store = AuditStore(self.config.audit)
        self._adapter = adapter

        if adapter is not None:
            adapter.attach_store(self.store)

    def verify(
        self,
        func: Callable[P, T] | None = None,
        *,
        checks: list[str] | None = None,
        threshold: float | None = None,
    ) -> Callable[[Callable[P, T]], Callable[P, VerificationResult[T]]] | Callable[
        P, VerificationResult[T]
    ]:
        """
        Decorator to verify LLM function outputs.

        Can be used with or without arguments:
            @gs.verify
            def my_func(...): ...

            @gs.verify(threshold=0.8)
            def my_func(...): ...

        Args:
            func: The function to decorate
            checks: Override which checks to run
            threshold: Override default threshold
        """
        def decorator(
            fn: Callable[P, T],
        ) -> Callable[P, VerificationResult[T]]:
            @functools.wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> VerificationResult[T]:
                existing_ctx = get_context()
                owns_context = existing_ctx is None
                if owns_context:
                    ctx = RequestContext()
                    set_context(ctx)
                else:
                    ctx = existing_ctx

                try:
                    response = fn(*args, **kwargs)

                    query = ""
                    context: list[str] = []

                    if args:
                        query = str(args[0]) if args else ""
                        if len(args) > 1 and isinstance(args[1], list):
                            context = [str(c) for c in args[1]]

                    if "query" in kwargs:
                        query = str(kwargs["query"])
                    if "context" in kwargs:
                        kwctx = kwargs["context"]
                        if isinstance(kwctx, list):
                            context = [str(c) for c in kwctx]

                    response_str = str(response) if response is not None else ""

                    result = self.engine.verify(
                        query=query,
                        context=context,
                        response=response_str,
                    )

                    ctx.query = query
                    ctx.context = context
                    ctx.response = response_str
                    ctx.verification_passed = result.passed
                    ctx.verification_results = {
                        k: v.to_dict() for k, v in result.checks.items()
                    }

                    if not result.passed:
                        if self.config.verification.on_fail == "block":
                            raise VerificationError(
                                "Verification failed",
                                results=result.checks,
                            )

                    return VerificationResult(
                        response=response,  # type: ignore[arg-type]
                        passed=result.passed,
                        checks=result.checks,
                        flags=result.flags,
                        audit_id=ctx.audit_id,
                        duration_ms=result.duration_ms,
                    )
                finally:
                    if owns_context:
                        clear_context()

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def audit(
        self,
        func: Callable[P, T] | None = None,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> Callable[[Callable[P, T]], Callable[P, T]] | Callable[P, T]:
        """
        Decorator to audit LLM function calls.

        Can be used with or without arguments:
            @gs.audit
            def my_func(...): ...

            @gs.audit(metadata={"user": "test"})
            def my_func(...): ...

        Args:
            func: The function to decorate
            metadata: Additional metadata to include in audit record
        """
        def decorator(fn: Callable[P, T]) -> Callable[P, T]:
            @functools.wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                existing_ctx = get_context()
                owns_context = existing_ctx is None
                if owns_context:
                    ctx = RequestContext()
                    set_context(ctx)
                else:
                    ctx = existing_ctx

                try:
                    result = fn(*args, **kwargs)

                    if isinstance(result, VerificationResult):
                        response_str = str(result.response)
                        passed = result.passed
                        verification_results = {
                            k: v.to_dict() for k, v in result.checks.items()
                        }
                    else:
                        response_str = str(result) if result is not None else ""
                        passed = ctx.verification_passed
                        verification_results = ctx.verification_results

                    query = ctx.query
                    context = ctx.context

                    if not query and args:
                        query = str(args[0])
                    if not context and len(args) > 1 and isinstance(args[1], list):
                        context = [str(c) for c in args[1]]

                    combined_metadata = metadata.copy() if metadata else {}
                    combined_metadata.update(ctx.metadata)

                    record = self.store.log(
                        query=query,
                        context=context,
                        response=response_str,
                        verification_passed=passed,
                        verification_results=verification_results,
                        metadata=combined_metadata,
                    )

                    ctx.audit_id = record.id

                    if isinstance(result, VerificationResult):
                        result.audit_id = record.id

                    return result

                finally:
                    if owns_context:
                        clear_context()

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def start_sync(self) -> None:
        """Start adapter sync (adapter mode only)."""
        if self._adapter is None:
            raise ConfigurationError("No adapter configured")
        self._adapter.start_sync()

    def stop_sync(self) -> None:
        """Stop adapter sync (adapter mode only)."""
        if self._adapter is not None:
            self._adapter.stop_sync()

    def close(self) -> None:
        """Close GridSeal and release resources."""
        self.stop_sync()
        self.store.close()
