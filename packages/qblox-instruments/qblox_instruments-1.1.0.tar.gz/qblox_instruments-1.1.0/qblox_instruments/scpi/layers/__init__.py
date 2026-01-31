# ----------------------------------------------------------------------------
# Description    : SCPI interface
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2020)
# ----------------------------------------------------------------------------

from __future__ import annotations
from typing import TYPE_CHECKING

from qblox_instruments.build import BuildInfo

if TYPE_CHECKING:
    from qblox_instruments.scpi.scpi import Scpi


LAYERS: dict[tuple[str, int], dict[int, type[Scpi]]] = {}


def register_layer(product: str, version: tuple[int, int], layer: type[Scpi]) -> None:
    major, minor = version
    LAYERS.setdefault((product, major), {})[minor] = layer


def lookup_layer(product: str, version: tuple[int, int]) -> type[Scpi] | None:
    major, minor = version
    if (product, major) not in LAYERS:
        return None
    product_layers = LAYERS[product, major]
    if not product_layers:
        return None

    # Try to find specific minor first
    if minor in product_layers:
        return product_layers[minor]
    # Specific minor not found, find closest minor to it
    closest_minor = max(m for m in product_layers if m <= minor)
    return product_layers[closest_minor]


from . import cluster_mm_legacy  # noqa: E402

register_layer("cluster_mm", (0, 1), cluster_mm_legacy.Cluster)

from . import cluster_mm_1_0  # noqa: E402

register_layer("cluster_mm", (1, 0), cluster_mm_1_0.Cluster)

from . import cfg_man  # noqa: E402

register_layer("cfg_man", (0, 1), cfg_man.CfgMan)
register_layer("cfg_man", (1, 0), cfg_man.CfgMan)
