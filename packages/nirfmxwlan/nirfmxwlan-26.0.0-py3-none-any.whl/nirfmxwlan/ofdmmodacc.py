"""Represents the OfdmModAcc measurement."""

import functools

import nirfmxwlan.ofdmmodacc_configuration as configuration
import nirfmxwlan.ofdmmodacc_results as results


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        meas_obj = xs[0]  # parameter 0 is 'self' which is the measurement object
        if meas_obj._signal_obj.is_disposed:
            raise Exception("Cannot access a disposed Wlan signal configuration")
        return f(*xs, **kws)

    return aux


class OfdmModAcc(object):
    """Represents the OfdmModAcc measurement."""

    def __init__(self, signal_obj):
        """Represents the OfdmModAcc measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter
        self.configuration = configuration.OfdmModAccConfiguration(signal_obj)  # type: ignore
        self.results = results.OfdmModAccResults(signal_obj)  # type: ignore
