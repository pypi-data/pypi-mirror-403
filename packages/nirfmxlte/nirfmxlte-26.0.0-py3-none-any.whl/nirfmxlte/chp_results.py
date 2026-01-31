"""Provides methods to fetch and read the Chp measurement results."""

import functools

import nirfmxlte.attributes as attributes
import nirfmxlte.chp_component_carrier_results as component_carrier
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


class ChpResults(object):
    """Provides methods to fetch and read the Chp measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the Chp measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter
        self.component_carrier = component_carrier.ChpComponentCarrierResults(signal_obj)  # type: ignore

    @_raise_if_disposed
    def get_total_aggregated_power(self, selector_string):
        r"""Gets the total power of all the subblocks. This value is expressed in dBm. The power in each subblock is the sum of
        powers of all the frequency bins over the integration bandwidth of the subblocks. This value includes the power in the
        inter-carrier gaps within a subblock, but it does not include the power within the subblock gaps.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the total power of all the subblocks. This value is expressed in dBm. The power in each subblock is the sum of
                powers of all the frequency bins over the integration bandwidth of the subblocks. This value includes the power in the
                inter-carrier gaps within a subblock, but it does not include the power within the subblock gaps.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.CHP_RESULTS_TOTAL_AGGREGATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_frequency(self, selector_string):
        r"""Gets the absolute center frequency of the subblock. This value is the center of the subblock integration bandwidth.
        Integration bandwidth is the span from left edge of the leftmost carrier to the right edge of the rightmost carrier
        within the subblock. This value is expressed in Hz.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the absolute center frequency of the subblock. This value is the center of the subblock integration bandwidth.
                Integration bandwidth is the span from left edge of the leftmost carrier to the right edge of the rightmost carrier
                within the subblock. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.CHP_RESULTS_SUBBLOCK_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth used in calculating the power of the subblock. Integration bandwidth is the span from
        left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock. This value is
        expressed in Hz.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the integration bandwidth used in calculating the power of the subblock. Integration bandwidth is the span from
                left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock. This value is
                expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.CHP_RESULTS_SUBBLOCK_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_power(self, selector_string):
        r"""Gets the sum of total power of all the frequency bins over the integration bandwidth of the subblock. This value
        includes the power in inter-carrier gaps within a subblock. This value is expressed in dBm.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the sum of total power of all the frequency bins over the integration bandwidth of the subblock. This value
                includes the power in inter-carrier gaps within a subblock. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.CHP_RESULTS_SUBBLOCK_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_spectrum(self, selector_string, timeout, spectrum):
        r"""Fetches the spectrum used for CHP measurements.

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

            spectrum (numpy.float32):
                This parameter returns the array of averaged power measured at each frequency bin. This value is expressed in dBm.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency of the channel. This value is expressed in Hz.

            dx (float):
                This parameter returns the frequency bin spacing. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.chp_fetch_spectrum(
                updated_selector_string, timeout, spectrum
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_subblock_measurement(self, selector_string, timeout):
        r"""Returns the power, integration bandwidth and center frequency of the subblock.

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
            Tuple (subblock_power, integration_bandwidth, frequency, error_code):

            subblock_power (float):
                This parameter returns the sum of powers of all the frequency bins over the integration bandwidth of the subblock. When
                you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, the parameter returns
                the total subblock power in dBm of all the active carriers measured over the subblock. When you set the ACP Pwr Units
                attribute to **dBm/Hz**, the parameter returns the power spectral density in dBm/Hz based on the power in all the
                active carriers measured over the subblock.

            integration_bandwidth (float):
                This parameter returns the integration bandwidth used in calculating the power of the subblock. Integration bandwidth
                is the span from left edge of the leftmost carrier to the right edge of the rightmost carrier within a subblock. This
                value is expressed in Hz.

            frequency (float):
                This parameter returns the absolute center frequency of the subblock. This value is the center of the subblock
                integration bandwidth. Integration bandwidth is the span from left edge of the integration bandwidth of the leftmost
                carrier to the right edge of the integration bandwidth of the rightmost carrier within a subblock. This value is
                expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            subblock_power, integration_bandwidth, frequency, error_code = (
                self._interpreter.chp_fetch_subblock_measurement(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return subblock_power, integration_bandwidth, frequency, error_code

    @_raise_if_disposed
    def fetch_total_aggregated_power(self, selector_string, timeout):
        r"""Fetches the sum of powers in all the subblocks.

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
            Tuple (total_aggregated_power, error_code):

            total_aggregated_power (float):
                This parameter returns the sum of powers of all the frequency bins over the integration bandwidth of subblock. This
                value includes the power in the inter-carrier gaps within a subblock, but it does not include the power in the subblock
                gaps.

                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, the
                parameter returns the total integrated power in dBm of all the active carriers measured. When you set the ACP Pwr Units
                attribute to **dBm/Hz**, the parameter returns the power spectral density in dBm/Hz based on the power in all the
                active carriers measured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            total_aggregated_power, error_code = self._interpreter.chp_fetch_total_aggregated_power(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return total_aggregated_power, error_code
