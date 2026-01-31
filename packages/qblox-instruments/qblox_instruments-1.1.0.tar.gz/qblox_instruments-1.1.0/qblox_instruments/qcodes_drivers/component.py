from qcodes import InstrumentChannel


class Component(InstrumentChannel):
    # ------------------------------------------------------------------------
    def _invalidate_qcodes_parameter_cache(self) -> None:
        """
        Marks the cache of all QCoDeS parameters on this component as invalid.
        """
        for param in self.parameters.values():
            param.cache.invalidate()

    # ------------------------------------------------------------------------
    def print_readable_snapshot(self, update: bool = False, max_chars: int = 80) -> None:
        """
        Introduce additional spacing in the readable version of the snapshot.
        """
        print()
        super().print_readable_snapshot(update=update, max_chars=max_chars)
