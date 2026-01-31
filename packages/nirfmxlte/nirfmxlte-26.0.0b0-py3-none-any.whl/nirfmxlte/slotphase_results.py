"""Provides methods to fetch and read the SlotPhase measurement results."""

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


class SlotPhaseResults(object):
    """Provides methods to fetch and read the SlotPhase measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the SlotPhase measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_maximum_phase_discontinuity(self, selector_string):
        r"""Gets the maximum value of phase difference at the slot boundaries within the
        :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH`. This values is expressed in degrees.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of phase difference at the slot boundaries within the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH`. This values is expressed in degrees.

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
                attributes.AttributeID.SLOTPHASE_RESULTS_MAXIMUM_PHASE_DISCONTINUITY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_maximum_phase_discontinuity_array(self, selector_string, timeout):
        r"""Fetches the array of maximum values of phase differences at slot boundaries within the measurement interval.

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
            Tuple (maximum_phase_discontinuity, error_code):

            maximum_phase_discontinuity (float):
                This parameter returns the array of maximum values of phase difference at the slot boundaries within the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH`.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            maximum_phase_discontinuity, error_code = (
                self._interpreter.slotphase_fetch_maximum_phase_discontinuity_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return maximum_phase_discontinuity, error_code

    @_raise_if_disposed
    def fetch_maximum_phase_discontinuity(self, selector_string, timeout):
        r"""Fetches the maximum value of phase differences at slot boundaries within the measurement interval.

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
            Tuple (maximum_phase_discontinuity, error_code):

            maximum_phase_discontinuity (float):
                This parameter returns the maximum value of phase difference at the slot boundaries within the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH`.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            maximum_phase_discontinuity, error_code = (
                self._interpreter.slotphase_fetch_maximum_phase_discontinuity(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return maximum_phase_discontinuity, error_code

    @_raise_if_disposed
    def fetch_phase_discontinuities(self, selector_string, timeout):
        r"""Fetches the array of phase differences at slot boundaries within measurement interval.

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
            Tuple (slot_phase_discontinuity, error_code):

            slot_phase_discontinuity (float):
                This parameter returns the array of phase differences at the slot boundaries within the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH`. This value is expressed in degrees.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            slot_phase_discontinuity, error_code = (
                self._interpreter.slotphase_fetch_phase_discontinuities(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return slot_phase_discontinuity, error_code

    @_raise_if_disposed
    def fetch_sample_phase_error_linear_fit_trace(
        self, selector_string, timeout, sample_phase_error_linear_fit
    ):
        r"""Fetches the sample phase error linear fit trace for the SlotPhase measurement. The linear fit is over the array of
        phase differences at each sample between the received signal and the locally generated reference signal.

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

            sample_phase_error_linear_fit (numpy.float32):
                This parameter returns the array of sample phase error linear fit traces.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start sample phase error linear fit trace value. This value is expressed in degrees.

            dx (float):
                This parameter returns the spacing between the sample phase error linear fit trace values.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.slotphase_fetch_sample_phase_error_linear_fit_trace(
                    updated_selector_string, timeout, sample_phase_error_linear_fit
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_sample_phase_error(self, selector_string, timeout, sample_phase_error):
        r"""Fetches the sample phase error trace for the SlotPhase measurement. At each sample, this is the phase difference
        between received signal and locally generated reference signal.

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

            sample_phase_error (numpy.float32):
                This parameter returns the array of sample phase error traces.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start sample phase error linear fit trace value.

            dx (float):
                This parameter returns the spacing between the sample phase error linear fit trace values.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.slotphase_fetch_sample_phase_error(
                updated_selector_string, timeout, sample_phase_error
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
