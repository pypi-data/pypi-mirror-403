from typing import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExporter,
    SpanExportResult,
)


class LazyBatchSpanProcessor(BatchSpanProcessor):
    """
    Fork of BatchSpanProcessor

    Nothing need to change because everything works well on this sdk version
    """

    ...


class NoOpSpanExporter(SpanExporter):
    """不执行任何操作的 Span Exporter，用于禁用数据上报时使用"""

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass
