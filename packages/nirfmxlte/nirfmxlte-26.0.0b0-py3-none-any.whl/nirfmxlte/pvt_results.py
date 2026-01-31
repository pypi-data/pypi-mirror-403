"""Provides methods to fetch and read the Pvt measurement results."""

import functools

import nirfmxlte.attributes as attributes
import nirfmxlte.enums as enums
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


class PvtResults(object):
    """Provides methods to fetch and read the Pvt measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the Pvt measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_status(self, selector_string):
        r"""Gets the measurement status indicating whether the power before and after the burst is within the standard defined
        limit.

        Refer to the `LTE PVT (Power Vs Time) Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about
        measurement status.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | Fail (0)     | Indicates that the measurement has failed. |
        +--------------+--------------------------------------------+
        | Pass (1)     | Indicates that the measurement has passed. |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PvtMeasurementStatus):
                Returns the measurement status indicating whether the power before and after the burst is within the standard defined
                limit.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PVT_RESULTS_MEASUREMENT_STATUS.value
            )
            attr_val = enums.PvtMeasurementStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_absolute_off_power_before(self, selector_string):
        r"""Gets the mean power in the segment before the captured burst. The segment is defined as one subframe prior to the
        burst for the FDD mode and 10 SC-FDMA symbols prior to the burst for the TDD mode. This value is expressed in dBm.

        Refer to the `LTE PVT (Power Vs Time) Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about OFF
        Power.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean power in the segment before the captured burst. The segment is defined as one subframe prior to the
                burst for the FDD mode and 10 SC-FDMA symbols prior to the burst for the TDD mode. This value is expressed in dBm.

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
                attributes.AttributeID.PVT_RESULTS_MEAN_ABSOLUTE_OFF_POWER_BEFORE.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_absolute_off_power_after(self, selector_string):
        r"""Gets the mean power in the segment after the captured burst. This value is expressed in dBm. The segment is defined
        as one subframe long, excluding a transient period of 20 micro seconds at the beginning.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Refer to the `LTE PVT (Power Vs Time) Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about OFF
        Power.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean power in the segment after the captured burst. This value is expressed in dBm. The segment is defined
                as one subframe long, excluding a transient period of 20 micro seconds at the beginning.

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
                attributes.AttributeID.PVT_RESULTS_MEAN_ABSOLUTE_OFF_POWER_AFTER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_absolute_on_power(self, selector_string):
        r"""Gets the average power of the subframes within the captured burst. This value is expressed in dBm. The average power
        excludes the transient period of 20 micro seconds at the beginning.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the subframes within the captured burst. This value is expressed in dBm. The average power
                excludes the transient period of 20 micro seconds at the beginning.

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
                attributes.AttributeID.PVT_RESULTS_MEAN_ABSOLUTE_ON_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_burst_width(self, selector_string):
        r"""Gets the width of the captured burst. This value is expressed in seconds.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the width of the captured burst. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PVT_RESULTS_BURST_WIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_measurement_array(self, selector_string, timeout):
        r"""Returns the measurement array.

        Use "subblock<*n*>" as the selector string to read this result.

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
            Tuple (measurement_status, mean_absolute_off_power_before, mean_absolute_off_power_after, mean_absolute_on_power, burst_width, error_code):

            measurement_status (enums.PvtMeasurementStatus):
                This parameter returns the array of the measurement status indicating whether the power before and after the burst is
                within the standard defined limit.

                +--------------+--------------------------------------------+
                | Name (Value) | Description                                |
                +==============+============================================+
                | Fail (0)     | Indicates that the measurement has failed. |
                +--------------+--------------------------------------------+
                | Pass (1)     | Indicates that the measurement has passed. |
                +--------------+--------------------------------------------+

            mean_absolute_off_power_before (float):
                This parameter returns the array of the mean power in the segment before the captured burst. The segment is defined as
                one subframe prior to the burst for the FDD mode and 10 SCFDMA symbols prior to the burst for the TDD mode. This value
                is expressed in dBm.

            mean_absolute_off_power_after (float):
                This parameter returns the array of the mean power in the segment after the captured burst. This value is expressed in
                dBm.

                The segment is defined as one subframe long excluding a transient period of 20 μs at the beginning.

            mean_absolute_on_power (float):
                This parameter returns the array of the average power of the subframes within the captured burst, excluding a transient
                period of 20 μs at the beginning. This value is expressed in dBm.

            burst_width (float):
                This parameter returns the array of the width of the captured burst.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            (
                measurement_status,
                mean_absolute_off_power_before,
                mean_absolute_off_power_after,
                mean_absolute_on_power,
                burst_width,
                error_code,
            ) = self._interpreter.pvt_fetch_measurement_array(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            mean_absolute_off_power_before,
            mean_absolute_off_power_after,
            mean_absolute_on_power,
            burst_width,
            error_code,
        )

    @_raise_if_disposed
    def fetch_measurement(self, selector_string, timeout):
        r"""Returns the measurement.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

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
            Tuple (measurement_status, mean_absolute_off_power_before, mean_absolute_off_power_after, mean_absolute_on_power, burst_width, error_code):

            measurement_status (enums.PvtMeasurementStatus):
                This parameter returns the measurement status indicating whether the power before and after the burst is within the
                standard defined limit.

                +--------------+--------------------------------------------+
                | Name (Value) | Description                                |
                +==============+============================================+
                | Fail (0)     | Indicates that the measurement has failed. |
                +--------------+--------------------------------------------+
                | Pass (1)     | Indicates that the measurement has passed. |
                +--------------+--------------------------------------------+

            mean_absolute_off_power_before (float):
                This parameter returns the mean power in the segment before the captured burst. The segment is defined as one subframe
                prior to the burst for the FDD mode and 10 SCFDMA symbols prior to the burst for the TDD mode. This value is expressed
                in dBm.

            mean_absolute_off_power_after (float):
                This parameter returns the mean power in the segment after the captured burst. This value is expressed in dBm.

                The segment is defined as one subframe long excluding a transient period of 20 μs at the beginning. This value
                is expressed in dBm.

            mean_absolute_on_power (float):
                This parameter returns the average power of the subframes within the captured burst, excluding a transient period of 20
                μs at the beginning. This value is expressed in dBm.

            burst_width (float):
                This parameter returns the width of the captured burst.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            (
                measurement_status,
                mean_absolute_off_power_before,
                mean_absolute_off_power_after,
                mean_absolute_on_power,
                burst_width,
                error_code,
            ) = self._interpreter.pvt_fetch_measurement(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            mean_absolute_off_power_before,
            mean_absolute_off_power_after,
            mean_absolute_on_power,
            burst_width,
            error_code,
        )

    @_raise_if_disposed
    def fetch_signal_power_trace(self, selector_string, timeout, signal_power, absolute_limit):
        r"""Returns the instantaneous signal power trace along with absolute limit for each segment in the trace as specified by
        section 6.5.2.4.5 of the *3GPP 36.521*. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

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

            signal_power (numpy.float32):
                This parameter returns the instantaneous signal power trace. This value is expressed in dBm.

            absolute_limit (numpy.float32):
                This parameter returns the instantaneous signal power trace. This value is expressed in dBm.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns start time of the signal. This value is expressed in seconds.

            dx (float):
                This parameter returns the time bin spacing. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.pvt_fetch_signal_power_trace(
                updated_selector_string, timeout, signal_power, absolute_limit
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
