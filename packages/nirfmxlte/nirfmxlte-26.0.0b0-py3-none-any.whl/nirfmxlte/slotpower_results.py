"""Provides methods to fetch and read the SlotPower measurement results."""

import functools

import nirfmxlte.errors as errors
import nirfmxlte.internal._helper as _helper


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        meas_obj = xs[0]  # parameter 0 is 'self' which is the measurement object
        if meas_obj._signal_obj.is_disposed:
            raise Exception("Cannot access a disposed Lte signal configuration")
        return f(*xs, **kws)

    return aux


class SlotPowerResults(object):
    """Provides methods to fetch and read the SlotPower measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the SlotPower measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def fetch_powers(self, selector_string, timeout):
        r"""Fetches the array of Subframe Power and the Subframe Power Delta parameters over the measurement interval. A NaN is
        returned as subframe power delta, when the preceding slot is not occupied.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name.

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (subframe_power, subframe_power_delta, error_code):

            subframe_power (float):
                This parameter returns the array of subframe power values over the measurement interval. The values are expressed in
                dBm.

            subframe_power_delta (float):
                This parameter returns the array of subframe power delta values over the measurement interval. Subframe power delta
                values are the power difference between the two consecutive subframes. The values are expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            subframe_power, subframe_power_delta, error_code = (
                self._interpreter.slotpower_fetch_powers(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return subframe_power, subframe_power_delta, error_code
