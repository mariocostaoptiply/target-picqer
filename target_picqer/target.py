"""Picqer target class."""

from __future__ import annotations

from hotglue_singer_sdk import typing as th
from hotglue_singer_sdk.sinks import Sink
from hotglue_singer_sdk.target_sdk.target import TargetHotglue

from target_picqer.sinks import (
    PurchaseOrders,
)


class TargetPicqer(TargetHotglue):
    """Sample target for Picqer."""

    SINK_TYPES = [PurchaseOrders]
    MAX_PARALLELISM = 10
    name = "target-picqer"
    config_jsonschema = th.PropertiesList(
        th.Property("api_key", th.StringType, required=True),
        th.Property("org", th.StringType, required=True),
    ).to_dict()

    def get_sink_class(self, stream_name: str) -> type[Sink] | None:
        """Get sink for a stream."""
        return next(
            (
                sink_class
                for sink_class in self.SINK_TYPES
                if stream_name.lower() in sink_class.names_available
            ),
            None,
        )


if __name__ == "__main__":
    TargetPicqer.cli()
