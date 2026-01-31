""""""

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


class SemComponentCarrierResults(object):
    """"""

    def __init__(self, signal_obj):
        """"""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_absolute_integrated_power(self, selector_string):
        r"""Gets the sum of powers of all the frequency bins over the integration bandwidth of the carrier. This value is
        expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the sum of powers of all the frequency bins over the integration bandwidth of the carrier. This value is
                expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_COMPONENT_CARRIER_ABSOLUTE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_relative_integrated_power(self, selector_string):
        r"""Gets the sum of powers of all the frequency bins over the integration bandwidth of the component carrier power
        relative to its subblock power. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the sum of powers of all the frequency bins over the integration bandwidth of the component carrier power
                relative to its subblock power. This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_COMPONENT_CARRIER_RELATIVE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_absolute_peak_power(self, selector_string):
        r"""Gets the peak power in the component carrier. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power in the component carrier. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_COMPONENT_CARRIER_ABSOLUTE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_frequency(self, selector_string):
        r"""Gets the frequency at which the peak power occurs in the component carrier. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency at which the peak power occurs in the component carrier. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_COMPONENT_CARRIER_PEAK_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_measurement_array(self, selector_string, timeout):
        r"""Returns an array of the absolute powers and relative powers measured in the component carriers. The relative power is
        relative to subblock power.

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
            Tuple (absolute_integrated_power, relative_integrated_power, error_code):

            absolute_integrated_power (float):
                This parameter returns the array of power measured in the subblock. The carrier power is reported in dBm when you set
                the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the
                ACP Pwr Units attribute to **dBm/Hz**.

            relative_integrated_power (float):
                This parameter returns the array of the sum of powers of all the frequency bins over the integration bandwidth of the
                component carrier power relative to its subblock power.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            absolute_integrated_power, relative_integrated_power, error_code = (
                self._interpreter.sem_fetch_measurement_array(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return absolute_integrated_power, relative_integrated_power, error_code

    @_raise_if_disposed
    def fetch_measurement(self, selector_string, timeout):
        r"""Returns the absolute power and relative power measured in the component carrier. The relative power is relative to
        subblock power.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (absolute_integrated_power, relative_integrated_power, error_code):

            absolute_integrated_power (float):
                This parameter returns the power measured over the integration bandwidth of the carrier. The carrier power is reported
                in dBm when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in
                dBm/Hz when you set the ACP Pwr Units attribute to **dBm/Hz**.

            relative_integrated_power (float):
                This parameter returns the component carrier power relative to its subblock power.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            absolute_integrated_power, relative_integrated_power, error_code = (
                self._interpreter.sem_fetch_measurement(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return absolute_integrated_power, relative_integrated_power, error_code
