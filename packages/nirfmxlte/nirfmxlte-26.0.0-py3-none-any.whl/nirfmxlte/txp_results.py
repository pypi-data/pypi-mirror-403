"""Provides methods to fetch and read the Txp measurement results."""

import functools

import nirfmxlte.attributes as attributes
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


class TxpResults(object):
    """Provides methods to fetch and read the Txp measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the Txp measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_average_power_mean(self, selector_string):
        r"""Gets the average power of the acquired signal.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
        returns the mean of the average power computed for each averaging count.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the acquired signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.TXP_RESULTS_AVERAGE_POWER_MEAN.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the acquired signal.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
        returns the max of the peak power computed for each averaging count.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the acquired signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.TXP_RESULTS_PEAK_POWER_MAXIMUM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_measurement(self, selector_string, timeout):
        r"""Fetches the average power and peak power of the the signal over which power measurments are performed.

        Use "subblock<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and subblock number.

                Example:

                "subblock0"

                "result::r1/subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (average_power_mean, peak_power_maximum, error_code):

            average_power_mean (float):
                This parameter returns the average power of the the signal over which power measurments are performed. This value is
                expressed in dBm.

            peak_power_maximum (float):
                This parameter returns the peak power of the the signal over which power measurments are performed. This value is
                expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            average_power_mean, peak_power_maximum, error_code = (
                self._interpreter.txp_fetch_measurement(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return average_power_mean, peak_power_maximum, error_code

    @_raise_if_disposed
    def fetch_power_trace(self, selector_string, timeout, power):
        r"""Fetches power versus time trace.

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

            power (numpy.float32):
                This parameter returns the measured average power at each time instance, in dBm.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start time, in seconds.

            dx (float):
                This parameter returns the sample duration, in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.txp_fetch_power_trace(
                updated_selector_string, timeout, power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
