"""Provides methods to fetch and read the ModAcc measurement results."""

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


class ModAccResults(object):
    """Provides methods to fetch and read the ModAcc measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the ModAcc measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_mean_rms_composite_evm(self, selector_string):
        r"""Gets the mean value of the RMS EVMs calculated on all the configured channels, over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the RMS EVMs calculated on all the configured channels, over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_COMPOSITE_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_maximum_peak_composite_evm(self, selector_string):
        r"""Gets the maximum value of the peak EVMs calculated on all the configured channels over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of the peak EVMs calculated on all the configured channels over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_composite_magnitude_error(self, selector_string):
        r"""Gets the RMS mean value of the composite magnitude error calculated over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS mean value of the composite magnitude error calculated over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_COMPOSITE_MAGNITUDE_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_maximum_peak_composite_magnitude_error(self, selector_string):
        r"""Gets the peak value of the composite magnitude error calculated over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak value of the composite magnitude error calculated over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels.

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
                attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_MAGNITUDE_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_composite_phase_error(self, selector_string):
        r"""Gets the RMS mean value of the composite phase error calculated over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels. This
        value is expressed in degrees.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS mean value of the composite phase error calculated over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels. This
                value is expressed in degrees.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_COMPOSITE_PHASE_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_maximum_peak_composite_phase_error(self, selector_string):
        r"""Gets the peak value of phase error calculated over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all thee configured channels. This
        value is expressed in degrees.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak value of phase error calculated over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all thee configured channels. This
                value is expressed in degrees.

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
                attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_PHASE_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_composite_evm_slot_index(self, selector_string):
        r"""Gets the slot index where the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM`
        occurs.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the slot index where the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM`
                occurs.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_RESULTS_PEAK_COMPOSITE_EVM_SLOT_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_composite_evm_symbol_index(self, selector_string):
        r"""Gets the symbol index of the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM`
        attribute.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the symbol index of the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM`
                attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_RESULTS_PEAK_COMPOSITE_EVM_SYMBOL_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_composite_evm_subcarrier_index(self, selector_string):
        r"""Gets the subcarrier index where the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM` for ModAcc occurs.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the subcarrier index where the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM` for ModAcc occurs.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_RESULTS_PEAK_COMPOSITE_EVM_SUBCARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_mean_rms_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on PDSCH data symbols over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on PDSCH data symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_MEAN_RMS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_mean_rms_qpsk_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on all QPSK modulated PDSCH resource blocks over the slots specified by
        the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on all QPSK modulated PDSCH resource blocks over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_MEAN_RMS_QPSK_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_mean_rms_16_qam_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on all 16QAM modulated PDSCH resource blocks over the slots specified by
        the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on all 16QAM modulated PDSCH resource blocks over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_MEAN_RMS_16QAM_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_mean_rms_64_qam_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on all 64 QAM modulated PDSCH resource blocks over the slots specified by
        the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on all 64 QAM modulated PDSCH resource blocks over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_MEAN_RMS_64QAM_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_mean_rms_256_qam_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on all 256 QAM modulated PDSCH resource blocks over the slots specified
        by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on all 256 QAM modulated PDSCH resource blocks over the slots specified
                by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_MEAN_RMS_256QAM_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_mean_rms_1024_qam_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on all 1024 QAM modulated PDSCH resource blocks over the slots specified
        by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on all 1024 QAM modulated PDSCH resource blocks over the slots specified
                by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_MEAN_RMS_1024QAM_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_csrs_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on RS resource elements over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on RS resource elements over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_CSRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_pss_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on primary synchronization signal (PSS) channel over the slots specified
        by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on primary synchronization signal (PSS) channel over the slots specified
                by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_PSS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_sss_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on secondary synchronization signal (SSS) channel over the slots
        specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on secondary synchronization signal (SSS) channel over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_SSS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_pbch_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on PBCH channel over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on PBCH channel over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_PBCH_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_pcfich_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on PCFICH channel over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on PCFICH channel over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_PCFICH_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_pdcch_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on PDCCH channel over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on PDCCH channel over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_PDCCH_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_phich_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on PHICH channel over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on PHICH channel over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_PHICH_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_downlink_rs_transmit_power(self, selector_string):
        r"""Gets the mean value of power calculated on cell-specific reference signal (CSRS) resource elements over the slots
        specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
        expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of power calculated on cell-specific reference signal (CSRS) resource elements over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
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
                attributes.AttributeID.MODACC_RESULTS_DOWNLINK_RS_TRANSMIT_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_downlink_ofdm_symbol_transmit_power(self, selector_string):
        r"""Gets the mean value of power calculated in one OFDM symbol over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of power calculated in one OFDM symbol over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.

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
                attributes.AttributeID.MODACC_RESULTS_DOWNLINK_OFDM_SYMBOL_TRANSMIT_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_downlink_detected_cell_id(self, selector_string):
        r"""Gets the detected cell ID value.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the detected cell ID value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_RESULTS_DOWNLINK_DETECTED_CELL_ID.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_npss_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on NB-IoT primary synchronization signal (NPSS) channel over the slots
        specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on NB-IoT primary synchronization signal (NPSS) channel over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_NPSS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_nsss_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on NB-IoT secondary synchronization signal (NSSS) channel over the slots
        specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on NB-IoT secondary synchronization signal (NSSS) channel over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_NSSS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_npdsch_mean_rms_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on the NB-IoT downlink shared channel (NPDSCH) data symbols over the
        slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on the NB-IoT downlink shared channel (NPDSCH) data symbols over the
                slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_NPDSCH_MEAN_RMS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_npdsch_mean_rms_qpsk_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on all QPSK modulated NPDSCH subframes/slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on all QPSK modulated NPDSCH subframes/slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_NPDSCH_MEAN_RMS_QPSK_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_nrs_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on NRS resource elements over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on NRS resource elements over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_NRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_downlink_nrs_transmit_power(self, selector_string):
        r"""Gets the mean value of power calculated on NB-IoT downlink reference signal (NRS) resource elements over the slots
        specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
        expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of power calculated on NB-IoT downlink reference signal (NRS) resource elements over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
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
                attributes.AttributeID.MODACC_RESULTS_DOWNLINK_NRS_TRANSMIT_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_in_band_emission_margin(self, selector_string):
        r"""Gets the in-band emission margin. This value is expressed in dB.

        The margin is the lowest difference between the in-band emission measurement trace and the limit trace. The
        limit is defined in section 6.5.2.3.5 of the *3GPP TS 36.521* specification.

        The in-band emissions are a measure of the interference falling into the non-allocated resources blocks.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the in-band emission margin. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_IN_BAND_EMISSION_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range_1_maximum_to_range_1_minimum(self, selector_string):
        r"""Gets the peak-to-peak ripple of the EVM equalizer coefficients within the frequency *Range1*. This value is
        expressed in dB.

        The frequency *Range1* is defined in section 6.5.2.4.5 of the *3GPP TS 36.521* specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak-to-peak ripple of the EVM equalizer coefficients within the frequency *Range1*. This value is
                expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_TO_RANGE1_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range_2_maximum_to_range_2_minimum(self, selector_string):
        r"""Gets the peak-to-peak ripple of the EVM equalizer coefficients within the frequency *Measurement Offset* parameter.
        This value is expressed in dB.

        The frequency *Measurement Offset* parameter is defined in section 6.5.2.4.5 of the *3GPP TS 36.521*
        specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak-to-peak ripple of the EVM equalizer coefficients within the frequency *Measurement Offset* parameter.
                This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_TO_RANGE2_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range_1_maximum_to_range_2_minimum(self, selector_string):
        r"""Gets the peak-to-peak ripple of the EVM equalizer coefficients from the frequency *Range1* to the frequency
        *Measurement Offset* parameter. The frequency *Range1* and frequency *Measurement Offset* parameter are defined in the
        section 6.5.2.4.5 of the *3GPP TS 36.521* specification. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak-to-peak ripple of the EVM equalizer coefficients from the frequency *Range1* to the frequency
                *Measurement Offset* parameter. The frequency *Range1* and frequency *Measurement Offset* parameter are defined in the
                section 6.5.2.4.5 of the *3GPP TS 36.521* specification. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_TO_RANGE2_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_mean_rms_data_evm(self, selector_string):
        r"""Gets the mean value of the RMS EVMs calculated on the physical uplink shared channel (PUSCH) data symbols over the
        slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the RMS EVMs calculated on the physical uplink shared channel (PUSCH) data symbols over the
                slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_MEAN_RMS_DATA_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_maximum_peak_data_evm(self, selector_string):
        r"""Gets the maximum value of the peak EVMs calculated on the physical uplink shared channel (PUSCH) data symbols over
        the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of the peak EVMs calculated on the physical uplink shared channel (PUSCH) data symbols over
                the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_MAXIMUM_PEAK_DATA_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_mean_rms_dmrs_evm(self, selector_string):
        r"""Gets the mean value of the RMS EVMs calculated on the PUSCH DMRS over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the RMS EVMs calculated on the PUSCH DMRS over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_MEAN_RMS_DMRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_maximum_peak_dmrs_evm(self, selector_string):
        r"""Gets the maximum value of the peak EVMs calculated on PUSCH DMRS over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of the peak EVMs calculated on PUSCH DMRS over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_MAXIMUM_PEAK_DMRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_mean_data_power(self, selector_string):
        r"""Gets the mean value of the power calculated on the physical uplink shared channel (PUSCH) data symbols over the
        slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
        expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the power calculated on the physical uplink shared channel (PUSCH) data symbols over the
                slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_MEAN_DATA_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_mean_dmrs_power(self, selector_string):
        r"""Gets the mean value of the power calculated on the PUSCH DMRS over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the power calculated on the PUSCH DMRS over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_MEAN_DMRS_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_rms_srs_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on the SRS symbols over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on the SRS symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_RMS_SRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_srs_power(self, selector_string):
        r"""Gets the mean value of power calculated on SRS over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This values is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of power calculated on SRS over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This values is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_MEAN_SRS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_npusch_mean_rms_data_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) data symbols
        over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **percentage**, the
        result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
        dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) data symbols
                over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_NPUSCH_MEAN_RMS_DATA_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_npusch_maximum_peak_data_evm(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) data
        symbols over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
        attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **percentage**, the
        result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
        dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) data
                symbols over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
                attribute.

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
                attributes.AttributeID.MODACC_RESULTS_NPUSCH_MAXIMUM_PEAK_DATA_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_npusch_mean_rms_dmrs_evm(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) DMRS over the
        slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
        dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) DMRS over the
                slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_NPUSCH_MEAN_RMS_DMRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_npusch_maximum_peak_dmrs_evm(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated on NPUSCH DMRS over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
        dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated on NPUSCH DMRS over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_NPUSCH_MAXIMUM_PEAK_DMRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_npusch_mean_data_power(self, selector_string):
        r"""Gets the mean value of the power calculated on the narrowband physical uplink shared channel (NPUSCH) data symbols
        over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This
        value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the power calculated on the narrowband physical uplink shared channel (NPUSCH) data symbols
                over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This
                value is expressed in dBm.

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
                attributes.AttributeID.MODACC_RESULTS_NPUSCH_MEAN_DATA_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_npusch_mean_dmrs_power(self, selector_string):
        r"""Gets the mean value of the power calculated on the narrowband physical uplink shared channel (NPUSCH) DMRS over the
        slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the power calculated on the narrowband physical uplink shared channel (NPUSCH) DMRS over the
                slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_NPUSCH_MEAN_DMRS_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range_2_maximum_to_range_1_minimum(self, selector_string):
        r"""Gets the peak-to-peak ripple of the EVM equalizer coefficients from frequency *Measurement Offset* parameter to
        frequency *Range1*. This value is expressed in dB.

        The frequency *Range1* and frequency *Measurement Offset* parameter are defined in section 6.5.2.4.5 of the
        *3GPP TS 36.521* specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak-to-peak ripple of the EVM equalizer coefficients from frequency *Measurement Offset* parameter to
                frequency *Range1*. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_TO_RANGE1_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_in_band_emission_margin(self, selector_string):
        r"""Gets the in-band emission margin of a subblock aggregated bandwidth. This value is expressed in dB.

        The margin is the lowest difference between the in-band emission measurement trace and the limit trace. The
        limit is defined in section 6.5.2A.3 of the *3GPP TS 36.521* specification.

        The in-band emissions are a measure of the interference falling into the non-allocated resources blocks. The
        result of this attribute is valid only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per Subblock**.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the in-band emission margin of a subblock aggregated bandwidth. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_IN_BAND_EMISSION_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pssch_mean_rms_data_evm(self, selector_string):
        r"""Gets the mean value of the RMS EVMs calculated on the physical sidelink shared channel (PSSCH) data symbols over the
        slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the RMS EVMs calculated on the physical sidelink shared channel (PSSCH) data symbols over the
                slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PSSCH_MEAN_RMS_DATA_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pssch_maximum_peak_data_evm(self, selector_string):
        r"""Gets the maximum value of the peak EVMs calculated on the physical sidelink shared channel (PSSCH) data symbols over
        the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of the peak EVMs calculated on the physical sidelink shared channel (PSSCH) data symbols over
                the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PSSCH_MAXIMUM_PEAK_DATA_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pssch_mean_rms_dmrs_evm(self, selector_string):
        r"""Gets the mean value of the RMS EVMs calculated on the PSSCH DMRS symbols over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the RMS EVMs calculated on the PSSCH DMRS symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PSSCH_MEAN_RMS_DMRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pssch_maximum_peak_dmrs_evm(self, selector_string):
        r"""Gets the maximum value of the peak EVMs calculated on PSSCH DMRS symbols over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of the peak EVMs calculated on PSSCH DMRS symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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
                attributes.AttributeID.MODACC_RESULTS_PSSCH_MAXIMUM_PEAK_DMRS_EVM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pssch_mean_data_power(self, selector_string):
        r"""Gets the mean value of the power calculated on the physical sidelink shared channel (PSSCH) data symbols over the
        slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
        expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the power calculated on the physical sidelink shared channel (PSSCH) data symbols over the
                slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
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
                attributes.AttributeID.MODACC_RESULTS_PSSCH_MEAN_DATA_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pssch_mean_dmrs_power(self, selector_string):
        r"""Gets the mean value of the power calculated on the PSSCH DMRS symbols over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of the power calculated on the PSSCH DMRS symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.

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
                attributes.AttributeID.MODACC_RESULTS_PSSCH_MEAN_DMRS_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_frequency_error(self, selector_string):
        r"""Gets the estimated carrier frequency offset averaged over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated carrier frequency offset averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_FREQUENCY_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_maximum_peak_frequency_error(self, selector_string):
        r"""Gets the estimated maximum carrier frequency offset per slot in case of **Uplink** and per subframe in case of
        **Downlink** over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
        attribute. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated maximum carrier frequency offset per slot in case of **Uplink** and per subframe in case of
                **Downlink** over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
                attribute. This value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_FREQUENCY_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_iq_origin_offset(self, selector_string):
        r"""Gets the estimated I/Q origin offset averaged over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBc.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**. This result will not be measured in case of downlink.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated I/Q origin offset averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBc.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_IQ_ORIGIN_OFFSET.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_maximum_peak_iq_origin_offset(self, selector_string):
        r"""Gets the estimated maximum IQ origin offset over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBc.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**. This result will not be measured in case of **Downlink**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated maximum IQ origin offset over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBc.

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
                attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_IQ_ORIGIN_OFFSET.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_iq_gain_imbalance(self, selector_string):
        r"""Gets the estimated I/Q gain imbalance averaged over the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`. The I/Q gain imbalance is the ratio of the
        amplitude of the I component to the Q component of the I/Q signal being measured. This value is expressed in dB.

        .. note::
           When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` attribute to **200.0 k** and
           the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 12, this result is available. For
           other values of NPUSCH Num Tones, this result will be reported as NaN.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated I/Q gain imbalance averaged over the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`. The I/Q gain imbalance is the ratio of the
                amplitude of the I component to the Q component of the I/Q signal being measured. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_IQ_GAIN_IMBALANCE.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_quadrature_error(self, selector_string):
        r"""Gets the estimated quadrature error averaged over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.  This value is expressed in degrees.

        Quadrature error is a measure of the skewness of the I component with respect to the Q component of the I/Q
        signal being measured.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` attribute to **200.0
        k** and the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 12, this result is
        available. For other values of NPUSCH Num Tones, this result will be reported as NaN.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated quadrature error averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.  This value is expressed in degrees.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_QUADRATURE_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_iq_timing_skew(self, selector_string):
        r"""Gets the estimated IQ timing skew averaged over measured length. IQ timing skew is the difference between the group
        delay of the in-phase (I) and quadrature (Q) components of the signal. This value is expressed in seconds.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated IQ timing skew averaged over measured length. IQ timing skew is the difference between the group
                delay of the in-phase (I) and quadrature (Q) components of the signal. This value is expressed in seconds.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_IQ_TIMING_SKEW.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_time_offset(self, selector_string):
        r"""Gets the time difference between the detected slot or frame boundary and the reference trigger location depending on
        the value of :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. This value is
        expressed in seconds.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the time difference between the detected slot or frame boundary and the reference trigger location depending on
                the value of :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. This value is
                expressed in seconds.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_TIME_OFFSET.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mean_symbol_clock_error(self, selector_string):
        r"""Gets the estimated symbol clock error averaged over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in ppm.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated symbol clock error averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in ppm.

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
                attributes.AttributeID.MODACC_RESULTS_MEAN_SYMBOL_CLOCK_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_mean_iq_origin_offset(self, selector_string):
        r"""Gets the estimated I/Q origin offset averaged over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute in the subblock. This value is
        expressed in dBc.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
        per Subblock**.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated I/Q origin offset averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute in the subblock. This value is
                expressed in dBc.

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
                attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_MEAN_IQ_ORIGIN_OFFSET.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_mean_iq_gain_imbalance(self, selector_string):
        r"""Gets the estimated I/Q gain imbalance averaged over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dB. The
        I/Q gain imbalance is the ratio of the amplitude of the I component to the Q component of the I/Q signal being measured
        in the subblock.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
        per Subblock**. Otherwise, this parameter returns NaN, as measurement of this result is currently not supported.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated I/Q gain imbalance averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dB. The
                I/Q gain imbalance is the ratio of the amplitude of the I component to the Q component of the I/Q signal being measured
                in the subblock.

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
                attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_MEAN_IQ_GAIN_IMBALANCE.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_mean_quadrature_error(self, selector_string):
        r"""Gets the estimated quadrature error averaged over the slots specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in degrees.
        Quadrature error is a measure of the skewness of the I component with respect to the Q component of the I/Q signal
        being measured in the subblock.

        This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
        per Subblock**. Otherwise, this parameter returns NaN, as measurement of this result is currently not supported.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated quadrature error averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in degrees.
                Quadrature error is a measure of the skewness of the I component with respect to the Q component of the I/Q signal
                being measured in the subblock.

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
                attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_MEAN_QUADRATURE_ERROR.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_composite_evm_array(self, selector_string, timeout):
        r"""Returns an array of the composite EVM for ModAcc measurements.

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
            Tuple (mean_rms_composite_evm, maximum_peak_composite_evm, mean_frequency_error, peak_composite_evm_symbol_index, peak_composite_evm_subcarrier_index, peak_composite_evm_slot_index, error_code):

            mean_rms_composite_evm (float):
                This parameter returns the array of the mean value of the RMS EVMs calculated on all configured channels over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            maximum_peak_composite_evm (float):
                This parameter returns the array of the maximum value of peak EVMs calculated on all configured channels over the slots
                specified by the ModAcc Meas Length attribute.

            mean_frequency_error (float):
                This parameter returns the array of the estimated carrier frequency offset averaged over the slots specified by the
                ModAcc Meas Length attribute.

            peak_composite_evm_symbol_index (int):
                This parameter returns the array of the symbol index where the ModAcc maximum peak composite EVM occurs.

            peak_composite_evm_subcarrier_index (int):
                This parameter returns the array of the subcarrier index of the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM` attribute.

            peak_composite_evm_slot_index (int):
                This parameter returns the array of the slot index where the ModAcc maximum peak composite EVM occurs.

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
                mean_rms_composite_evm,
                maximum_peak_composite_evm,
                mean_frequency_error,
                peak_composite_evm_symbol_index,
                peak_composite_evm_subcarrier_index,
                peak_composite_evm_slot_index,
                error_code,
            ) = self._interpreter.modacc_fetch_composite_evm_array(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            mean_rms_composite_evm,
            maximum_peak_composite_evm,
            mean_frequency_error,
            peak_composite_evm_symbol_index,
            peak_composite_evm_subcarrier_index,
            peak_composite_evm_slot_index,
            error_code,
        )

    @_raise_if_disposed
    def fetch_composite_evm(self, selector_string, timeout):
        r"""Fetches the composite EVM for ModAcc measurements.

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
            Tuple (mean_rms_composite_evm, maximum_peak_composite_evm, mean_frequency_error, peak_composite_evm_symbol_index, peak_composite_evm_subcarrier_index, peak_composite_evm_slot_index, error_code):

            mean_rms_composite_evm (float):
                This parameter returns the mean value of the RMS EVMs calculated on all configured channels over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            maximum_peak_composite_evm (float):
                This parameter returns the symbol index where the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM` occurs.

            mean_frequency_error (float):
                This parameter returns the estimated carrier frequency offset averaged over the slots specified by the ModAcc Meas
                Length attribute.

            peak_composite_evm_symbol_index (int):
                This parameter returns the symbol index where the ModAcc maximum peak composite EVM occurs.

            peak_composite_evm_subcarrier_index (int):
                This parameter returns the subcarrier index where the ModAcc maximum peak composite EVM occurs.

            peak_composite_evm_slot_index (int):
                This parameter returns the slot index where the ModAcc maximum peak composite EVM occurs.

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
                mean_rms_composite_evm,
                maximum_peak_composite_evm,
                mean_frequency_error,
                peak_composite_evm_symbol_index,
                peak_composite_evm_subcarrier_index,
                peak_composite_evm_slot_index,
                error_code,
            ) = self._interpreter.modacc_fetch_composite_evm(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            mean_rms_composite_evm,
            maximum_peak_composite_evm,
            mean_frequency_error,
            peak_composite_evm_symbol_index,
            peak_composite_evm_subcarrier_index,
            peak_composite_evm_slot_index,
            error_code,
        )

    @_raise_if_disposed
    def fetch_composite_magnitude_and_phase_error_array(self, selector_string, timeout):
        r"""Returns the arrays of the mean RMS composite magnitude error and phase error, and the max peak composite magnitude
        error and phase error.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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
            Tuple (mean_rms_composite_magnitude_error, maximum_peak_composite_magnitude_error, mean_rms_composite_phase_error, maximum_peak_composite_phase_error, error_code):

            mean_rms_composite_magnitude_error (float):
                This parameter returns the array of the RMS mean value of the magnitude error calculated over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels.

            maximum_peak_composite_magnitude_error (float):
                This parameter returns the array of the peak value of magnitude error calculated over the slots specified by the ModAcc
                Meas Length attribute on all the configured channels.

            mean_rms_composite_phase_error (float):
                This parameter returns the array of the RMS mean value of the phase error calculated over the slots specified by the
                ModAcc Meas Length attribute on all the configured channels. This value is expressed in degrees.

            maximum_peak_composite_phase_error (float):
                This parameter returns the array of the peak value of phase error calculated over the slots specified by the ModAcc
                Meas Length attribute on all thee configured channels. This value is expressed in degrees.

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
                mean_rms_composite_magnitude_error,
                maximum_peak_composite_magnitude_error,
                mean_rms_composite_phase_error,
                maximum_peak_composite_phase_error,
                error_code,
            ) = self._interpreter.modacc_fetch_composite_magnitude_and_phase_error_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            mean_rms_composite_magnitude_error,
            maximum_peak_composite_magnitude_error,
            mean_rms_composite_phase_error,
            maximum_peak_composite_phase_error,
            error_code,
        )

    @_raise_if_disposed
    def fetch_composite_magnitude_and_phase_error(self, selector_string, timeout):
        r"""Returns the mean RMS composite magnitude error, phase error, the maximum peak composite magnitude error, and the phase
        error.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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
            Tuple (mean_rms_composite_magnitude_error, maximum_peak_composite_magnitude_error, mean_rms_composite_phase_error, maximum_peak_composite_phase_error, error_code):

            mean_rms_composite_magnitude_error (float):
                This parameter returns the RMS mean value of the magnitude error calculated over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels.

            maximum_peak_composite_magnitude_error (float):
                This parameter returns the peak value of magnitude error calculated over the slots specified by the ModAcc Meas Length
                attribute on all the configured channels.

            mean_rms_composite_phase_error (float):
                This parameter returns the RMS mean value of the phase error calculated over the slots specified by the ModAcc Meas
                Length attribute on all the configured channels. This value is expressed in degrees.

            maximum_peak_composite_phase_error (float):
                This parameter returns the peak value of phase error calculated over the slots specified by the ModAcc Meas Length
                attribute on all thee configured channels. This value is expressed in degrees.

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
                mean_rms_composite_magnitude_error,
                maximum_peak_composite_magnitude_error,
                mean_rms_composite_phase_error,
                maximum_peak_composite_phase_error,
                error_code,
            ) = self._interpreter.modacc_fetch_composite_magnitude_and_phase_error(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            mean_rms_composite_magnitude_error,
            maximum_peak_composite_magnitude_error,
            mean_rms_composite_phase_error,
            maximum_peak_composite_phase_error,
            error_code,
        )

    @_raise_if_disposed
    def fetch_csrs_constellation(self, selector_string, timeout, csrs_constellation):
        r"""Fetches the constellation trace for a cell-specific reference signal.

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

            csrs_constellation (numpy.complex64):
                This parameter returns CSRS constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_csrs_constellation(
                updated_selector_string, timeout, csrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_csrs_evm_array(self, selector_string, timeout):
        r"""Fetches the array of CSRS EVMs for all the component carriers within the subblock.

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
            Tuple (mean_rms_csrs_evm, error_code):

            mean_rms_csrs_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on Reference Signal (RS) resource elements over
                the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you
                set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement is
                returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_csrs_evm, error_code = self._interpreter.modacc_fetch_csrs_evm_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_csrs_evm, error_code

    @_raise_if_disposed
    def fetch_csrs_evm(self, selector_string, timeout):
        r"""Fetches the cell-specific reference signal EVM.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read results from this method.

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
            Tuple (mean_rms_csrs_evm, error_code):

            mean_rms_csrs_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on Reference Signal (RS) resource elements over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement is returned
                in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_csrs_evm, error_code = self._interpreter.modacc_fetch_csrs_evm(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_csrs_evm, error_code

    @_raise_if_disposed
    def fetch_downlink_detected_cell_id_array(self, selector_string, timeout):
        r"""Fetches the array of detected cell IDs for all the component carriers within the subblock.

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
            Tuple (detected_cell_id, error_code):

            detected_cell_id (int):
                This parameter returns the array of the detected cell ID values.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            detected_cell_id, error_code = (
                self._interpreter.modacc_fetch_downlink_detected_cell_id_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return detected_cell_id, error_code

    @_raise_if_disposed
    def fetch_downlink_detected_cell_id(self, selector_string, timeout):
        r"""Fetches the detected cell ID. This method is valid only when the measured signal contains primary synchronization
        signal (PSS) and secondary synchronization signal (SSS).

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
            Tuple (detected_cell_id, error_code):

            detected_cell_id (int):
                This parameter returns the detected cell ID value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            detected_cell_id, error_code = self._interpreter.modacc_fetch_downlink_detected_cell_id(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return detected_cell_id, error_code

    @_raise_if_disposed
    def fetch_downlink_pbch_constellation(self, selector_string, timeout, pbch_constellation):
        r"""Fetches the PBCH constellation trace for the control channels.

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

            pbch_constellation (numpy.complex64):
                This parameter returns the PBCH constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_downlink_pbch_constellation(
                updated_selector_string, timeout, pbch_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_downlink_pcfich_constellation(self, selector_string, timeout, pcfich_constellation):
        r"""Fetches the PCFICH constellation trace for the control channels.

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

            pcfich_constellation (numpy.complex64):
                This parameter returns the PCFICH constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_downlink_pcfich_constellation(
                updated_selector_string, timeout, pcfich_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_downlink_pdcch_constellation(self, selector_string, timeout, pdcch_constellation):
        r"""Fetches the PDCCH constellation trace for the control channels.

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

            pdcch_constellation (numpy.complex64):
                This parameter returns the PDCCH constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_downlink_pdcch_constellation(
                updated_selector_string, timeout, pdcch_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_downlink_phich_constellation(self, selector_string, timeout, phich_constellation):
        r"""Fetches the PHICH constellation trace for the control channels.

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

            phich_constellation (numpy.complex64):
                This parameter returns the PHICH constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_downlink_phich_constellation(
                updated_selector_string, timeout, phich_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_downlink_transmit_power_array(self, selector_string, timeout):
        r"""Fetches the array of reference signal powers and the OFDM symbol transmit powers for all the component carriers within
        the subblock.

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
            Tuple (rs_transmit_power, ofdm_symbol_transmit_power, reserved_1, reserved_2, error_code):

            rs_transmit_power (float):
                This parameter returns the array of mean values of power calculated on cell-specific reference signal (CSRS) resource
                elements over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
                attribute. This value is expressed in dBm.

            ofdm_symbol_transmit_power (float):
                This parameter returns the array the mean value of power calculated in one OFDM symbol over the slots specified by the
                ModAcc Meas Length attribute. This value is expressed in dBm.

            reserved_1 (float):
                This parameter this result is not supported in this release and it is reserved for future enhancements.

            reserved_2 (float):
                This parameter this result is not supported in this release and it is reserved for future enhancements.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            rs_transmit_power, ofdm_symbol_transmit_power, reserved_1, reserved_2, error_code = (
                self._interpreter.modacc_fetch_downlink_transmit_power_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return rs_transmit_power, ofdm_symbol_transmit_power, reserved_1, reserved_2, error_code

    @_raise_if_disposed
    def fetch_downlink_transmit_power(self, selector_string, timeout):
        r"""Fetches the reference signal power and the OFDM symbol transmit power.

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
            Tuple (rs_transmit_power, ofdm_symbol_transmit_power, reserved_1, reserved_2, error_code):

            rs_transmit_power (float):
                This parameter returns the mean value of power calculated on cell-specific reference signal (CSRS) resource elements
                over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This
                value is expressed in dBm.

            ofdm_symbol_transmit_power (float):
                This parameter returns the mean power value calculated in one OFDM symbol over the slots specified by the ModAcc Meas
                Length attribute. This value is expressed in dBm.

            reserved_1 (float):
                This parameter this result is not supported in this release and it is reserved for future enhancements.

            reserved_2 (float):
                This parameter this result is not supported in this release and it is reserved for future enhancements.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            rs_transmit_power, ofdm_symbol_transmit_power, reserved_1, reserved_2, error_code = (
                self._interpreter.modacc_fetch_downlink_transmit_power(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return rs_transmit_power, ofdm_symbol_transmit_power, reserved_1, reserved_2, error_code

    @_raise_if_disposed
    def fetch_evm_per_slot_trace(self, selector_string, timeout, rms_evm_per_slot):
        r"""Returns the EVM of each slot averaged across all the symbols within the slots and all the allocated subcarriers.

        Use "carrier<*k*>" or "subblock<*k*>/carrier<*k*>" as the selector string to read results from this method.

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

            rms_evm_per_slot (numpy.float32):
                This parameter returns the EVM of each slot averaged across all the symbols within the slots and all the allocated
                subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM slot position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_evm_per_slot_trace(
                updated_selector_string, timeout, rms_evm_per_slot
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_evm_per_subcarrier_trace(self, selector_string, timeout, mean_rms_evm_per_subcarrier):
        r"""Returns the EVM of each allocated subcarrier averaged across all the symbols within the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

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

            mean_rms_evm_per_subcarrier (numpy.float32):
                This parameter returns the EVM of each allocated subcarrier averaged across all the symbols within the measurement
                length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier position corresponding to the RB offset of the signal being measured.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_evm_per_subcarrier_trace(
                updated_selector_string, timeout, mean_rms_evm_per_subcarrier
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_evm_per_symbol_trace(self, selector_string, timeout, rms_evm_per_symbol):
        r"""Returns the EVM on each symbol within the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
        attribute averaged across all the allocated subcarriers.

        Use "carrier<*k*>" or "subblock<*k*>/carrier<*k*>" as the selector string to read results from this method.

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

            rms_evm_per_symbol (numpy.float32):
                This parameter returns the EVM of each symbol within the measurement length averaged across all the allocated
                subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the value of the ModAcc Meas Length
                attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_evm_per_symbol_trace(
                updated_selector_string, timeout, rms_evm_per_symbol
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_evm_high_per_symbol_trace(self, selector_string, timeout, evm_high_per_symbol):
        r"""Returns the EVM per symbol trace for all the configured slots. The EVM is obtained by using the FFT window position,
        Delta_C+W/2.

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

            evm_high_per_symbol (numpy.float32):
                This parameter returns the array of the EVM per symbol trace for all the configured slots. The EVM is obtained by using
                FFT window position, Delta_C+W/2.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_evm_high_per_symbol_trace(
                updated_selector_string, timeout, evm_high_per_symbol
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_maximum_evm_high_per_symbol_trace(
        self, selector_string, timeout, maximum_evm_high_per_symbol
    ):
        r"""Returns the maximum EVM per symbol trace for all the configured slots. The EVM is obtained by using the FFT window
        position, Delta_C+W/2.

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

            maximum_evm_high_per_symbol (numpy.float32):
                This parameter returns the array of the maximum EVM per symbol trace for all the configured slots. The EVM is obtained
                by using FFT window position, Delta_C+W/2.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_maximum_evm_high_per_symbol_trace(
                updated_selector_string, timeout, maximum_evm_high_per_symbol
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_evm_low_per_symbol_trace(self, selector_string, timeout, evm_low_per_symbol):
        r"""Returns the EVM per symbol trace for all the configured slots. The EVM is obtained by using FFT window position,
        Delta_C-W/2.

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information.

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

            evm_low_per_symbol (numpy.float32):
                This parameter returns the array of the EVM per symbol trace for all the configured slots. The EVM is obtained by using
                FFT window position, Delta_C-W/2.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_evm_low_per_symbol_trace(
                updated_selector_string, timeout, evm_low_per_symbol
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_maximum_evm_low_per_symbol_trace(
        self, selector_string, timeout, maximum_evm_low_per_symbol
    ):
        r"""Returns the maximum EVM per symbol trace for all the configured slots. The EVM is obtained by using FFT window
        position, Delta_C-W/2.

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information.

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

            maximum_evm_low_per_symbol (numpy.float32):
                This parameter returns the array of the maximum EVM per symbol trace for all the configured slots. The EVM is obtained
                by using FFT window position, Delta_C-W/2.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_maximum_evm_low_per_symbol_trace(
                updated_selector_string, timeout, maximum_evm_low_per_symbol
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_in_band_emission_margin_array(self, selector_string, timeout):
        r"""Returns an array of margins on non allocated resource blocks (RBs) in the uplink signal for all component carriers
        within the subblock.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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
            Tuple (in_band_emission_margin, error_code):

            in_band_emission_margin (float):
                This parameter returns the array of the in-band emission margins. The margin is the least difference between the
                in-band emission measurement trace and limit trace. The limit is defined in section 6.5.2.3.5 of the *3GPP TS 36.521 *
                specification. The in-band emissions are a measure of the interference falling into the non-allocated resources blocks.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            in_band_emission_margin, error_code = (
                self._interpreter.modacc_fetch_in_band_emission_margin_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return in_band_emission_margin, error_code

    @_raise_if_disposed
    def fetch_in_band_emission_margin(self, selector_string, timeout):
        r"""Returns the in-band emission margin on non allocated resource blocks (RBs) in the uplink signal. This value is
        expressed in dB.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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
            Tuple (in_band_emission_margin, error_code):

            in_band_emission_margin (float):
                This parameter returns the in-band emission margin. The margin is the least difference between the in-band emission
                measurement trace and limit trace. The limit is defined in section 6.5.2.3.5 of the *3GPP TS 36.521 * specification.
                The in-band emissions are a measure of the interference falling into the non-allocated resources blocks.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            in_band_emission_margin, error_code = (
                self._interpreter.modacc_fetch_in_band_emission_margin(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return in_band_emission_margin, error_code

    @_raise_if_disposed
    def fetch_in_band_emission_trace(
        self, selector_string, timeout, in_band_emission, in_band_emission_mask
    ):
        r"""Returns the in-band emission (IBE) and limit traces. In-band emission is the interference falling into non allocated
        resource blocks. The IBE for various spectral regions (general, carrier leakage, and I/Q image) are evaluated according
        to section 6.5.2.3.5 of the *3GPP 36.521 * specification and concatenated to form a composite trace. The limit trace is
        derived from the limits in the section 6.5.2.3.5 of the *3GPP 36.521 * specification.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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

            in_band_emission (numpy.float32):
                This parameter returns the in-band emission value as an array for each of the resource blocks. In-band emission is the
                interference falling into non-allocated resource blocks.  This value is expressed in dB.

            in_band_emission_mask (numpy.float32):
                This parameter returns the in-band emission value as an array for each of the resource blocks. In-band emission is the
                interference falling into non-allocated resource blocks.  This value is expressed in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource block.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_in_band_emission_trace(
                updated_selector_string, timeout, in_band_emission, in_band_emission_mask
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_iq_impairments_array(self, selector_string, timeout):
        r"""Returns an array of the mean I/Q origin offset, mean I/Q gain imbalance, and mean I/Q quadrature error.

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
            Tuple (mean_iq_origin_offset, mean_iq_gain_imbalance, mean_iq_quadrature_error, error_code):

            mean_iq_origin_offset (float):
                This parameter returns the array of the estimated I/Q origin offset averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. The modacc measurement ignores this
                parameter, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

            mean_iq_gain_imbalance (float):
                This parameter returns the array of the estimated I/Q gain imbalance averaged over the slots specified by the ModAcc
                Meas Length attribute. The I/Q gain imbalance is the ratio of the amplitude of the I component to the Q component of
                the I/Q signal being measured.

                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` attribute to **200.0
                k** and the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 12, this result is
                available. For other values of NPUSCH Num Tones, this result will be reported as NaN.

            mean_iq_quadrature_error (float):
                This parameter returns the array of the estimated quadrature error averaged over the slots specified by the ModAcc Meas
                Length attribute. Quadrature error is a measure of the skewness of the I component with respect to the Q component of
                the I/Q signal being measured. This value is expressed in degrees.

                When you set the CC Bandwidth attribute to **200.0 k** and the NPUSCH Num Tones attribute to 12, this result is
                available. For other values of NPUSCH Num Tones, this result will be reported as NaN.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_iq_origin_offset, mean_iq_gain_imbalance, mean_iq_quadrature_error, error_code = (
                self._interpreter.modacc_fetch_iq_impairments_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_iq_origin_offset, mean_iq_gain_imbalance, mean_iq_quadrature_error, error_code

    @_raise_if_disposed
    def fetch_iq_impairments(self, selector_string, timeout):
        r"""Returns the mean I/Q origin offset, mean I/Q gain imbalance, and mean I/Q quadrature error.

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
            Tuple (mean_iq_origin_offset, mean_iq_gain_imbalance, mean_iq_quadrature_error, error_code):

            mean_iq_origin_offset (float):
                This parameter returns the estimated I/Q origin offset averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. The modacc measurement ignores this
                parameter, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

            mean_iq_gain_imbalance (float):
                This parameter returns the estimated I/Q gain imbalance averaged over the slots specified by the ModAcc Meas Length
                attribute. The I/Q gain imbalance is the ratio of the amplitude of the I component to the Q component of the I/Q signal
                being measured.

                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` attribute to **200.0
                k** and the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 12, this result is
                available. For other values of NPUSCH Num Tones, this result will be reported as NaN.

            mean_iq_quadrature_error (float):
                This parameter returns the estimated quadrature error averaged over the slots specified by the ModAcc Meas Length
                attribute. Quadrature error is a measure of the skewness of the I component with respect to the Q component of the I/Q
                signal being measured. This value is expressed in degrees.

                When you set the CC Bandwidth attribute to **200.0 k** and the NPUSCH Num Tones attribute to 12, this result is
                available. For other values of NPUSCH Num Tones, this result will be reported as NaN.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_iq_origin_offset, mean_iq_gain_imbalance, mean_iq_quadrature_error, error_code = (
                self._interpreter.modacc_fetch_iq_impairments(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_iq_origin_offset, mean_iq_gain_imbalance, mean_iq_quadrature_error, error_code

    @_raise_if_disposed
    def fetch_maximum_evm_per_slot_trace(self, selector_string, timeout, maximum_evm_per_slot):
        r"""Returns the peak value of an EVM for each slot computed across all the symbols and all the allocated subcarriers.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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

            maximum_evm_per_slot (numpy.float32):
                This parameter returns the peak value of an EVM for each slot computed across all the symbols and all the allocated
                subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM slot position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_maximum_evm_per_slot_trace(
                updated_selector_string, timeout, maximum_evm_per_slot
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_maximum_evm_per_subcarrier_trace(
        self, selector_string, timeout, maximum_evm_per_subcarrier
    ):
        r"""Returns the peak value of an EVM for each allocated subcarrier computed across all the symbols within the value of the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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

            maximum_evm_per_subcarrier (numpy.float32):
                This parameter returns the peak value of an EVM for each allocated subcarrier computed across all the symbols within
                the ModAcc Meas Length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier position corresponding to the RB offset of the signal being measured.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_maximum_evm_per_subcarrier_trace(
                updated_selector_string, timeout, maximum_evm_per_subcarrier
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_maximum_evm_per_symbol_trace(self, selector_string, timeout, maximum_evm_per_symbol):
        r"""Returns the peak value of an EVM for each symbol computed across all the allocated subcarriers.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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

            maximum_evm_per_symbol (numpy.float32):
                This parameter returns the peak value of an EVM for each symbol computed across all the allocated subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_maximum_evm_per_symbol_trace(
                updated_selector_string, timeout, maximum_evm_per_symbol
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_maximum_magnitude_error_per_symbol_trace(
        self, selector_string, timeout, maximum_magnitude_error_per_symbol
    ):
        r"""Returns the peak value of the magnitude error for each symbol computed across all the allocated subcarriers.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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

            maximum_magnitude_error_per_symbol (numpy.float32):
                This parameter returns the array of the peak value of the magnitude error for each symbol computed across all the
                allocated subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

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
                self._interpreter.modacc_fetch_maximum_magnitude_error_per_symbol_trace(
                    updated_selector_string, timeout, maximum_magnitude_error_per_symbol
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_maximum_phase_error_per_symbol_trace(
        self, selector_string, timeout, maximum_phase_error_per_symbol
    ):
        r"""Returns the peak value of the phase error for each symbol computed across all the allocated subcarriers.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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

            maximum_phase_error_per_symbol (numpy.float32):
                This parameter returns the peak value of the phase error for each symbol computed across all the allocated subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

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
                self._interpreter.modacc_fetch_maximum_phase_error_per_symbol_trace(
                    updated_selector_string, timeout, maximum_phase_error_per_symbol
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_npusch_data_evm(self, selector_string, timeout):
        r"""Fetches the narrowband physical uplink shared channel (NPUSCH) data EVM for ModAcc measurements.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

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
            Tuple (npusch_mean_rms_data_evm, npusch_maximum_peak_data_evm, error_code):

            npusch_mean_rms_data_evm (float):
                This parameter returns the mean value of the RMS EVMs calculated on the NPUSCH data symbols over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
                result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to  **dB**, the result is returned
                in dB.

            npusch_maximum_peak_data_evm (float):
                This parameter returns the maximum value of the peak EVMs calculated on the NPUSCH data symbols over the slots
                specified by the ModAcc Meas Length attribute.
                When you set the ModAcc EVM Unit attribute to **Percentage**, the result is returned as a percentage. When you set
                the ModAcc EVM Unit attribute to **dB**, the result is returned in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            npusch_mean_rms_data_evm, npusch_maximum_peak_data_evm, error_code = (
                self._interpreter.modacc_fetch_npusch_data_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return npusch_mean_rms_data_evm, npusch_maximum_peak_data_evm, error_code

    @_raise_if_disposed
    def fetch_npusch_dmrs_evm(self, selector_string, timeout):
        r"""Fetches the EVM values calculated on NPUSCH DMRS over the length of the measurement.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

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
            Tuple (npusch_mean_rms_dmrs_evm, npusch_maximum_peak_dmrs_evm, error_code):

            npusch_mean_rms_dmrs_evm (float):
                This parameter returns the mean value of the RMS EVMs calculated on the NPUSCH DMRS over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
                result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
                dB.

            npusch_maximum_peak_dmrs_evm (float):
                This parameter returns the maximum value of the peak EVMs calculated on **NPUSCH DMRS** over the slots specified by the
                ModAcc Meas Length attribute.

                When you set the ModAcc EVM Unit attribute to **Percentage**, the result is returned as a percentage, and when
                you set the ModAcc EVM Unit attribute to **dB**, the result is returned in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            npusch_mean_rms_dmrs_evm, npusch_maximum_peak_dmrs_evm, error_code = (
                self._interpreter.modacc_fetch_npusch_dmrs_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return npusch_mean_rms_dmrs_evm, npusch_maximum_peak_dmrs_evm, error_code

    @_raise_if_disposed
    def fetch_npusch_symbol_power(self, selector_string, timeout):
        r"""Fetches the narrowband physical uplink shared channel (NPUSCH) symbol powers.

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
            Tuple (npusch_mean_data_power, npusch_mean_dmrs_power, error_code):

            npusch_mean_data_power (float):
                This parameter returns the mean value of the power calculated on the narrowband physical uplink shared channel (NPUSCH)
                data symbols over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
                attribute.

                This value is expressed in dBm.

            npusch_mean_dmrs_power (float):
                This parameter returns the mean value of the power calculated on the NPUSCH DMRS over the slots specified by the ModAcc
                Meas Length attribute.

                This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            npusch_mean_data_power, npusch_mean_dmrs_power, error_code = (
                self._interpreter.modacc_fetch_npusch_symbol_power(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return npusch_mean_data_power, npusch_mean_dmrs_power, error_code

    @_raise_if_disposed
    def fetch_pdsch_1024_qam_constellation(self, selector_string, timeout, qam1024_constellation):
        r"""Fetches the physical downlink shared channel (PDSCH) 1024 QAM trace.

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

            qam1024_constellation (numpy.complex64):
                This parameter returns the 1024 QAM constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_pdsch_1024_qam_constellation(
                updated_selector_string, timeout, qam1024_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_1024_qam_evm_array(self, selector_string, timeout):
        r"""Fetches an array of physical downlink shared channel (PDSCH) 1024QAM EVMs for all the component carriers within the
        subblock.

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
            Tuple (mean_rms_1024qam_evm, error_code):

            mean_rms_1024qam_evm (float):
                This parameter returns an array of mean values of the calculated RMS EVMs on all 1024QAM modulated PDSCH resource
                blocks over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
                attribute.
                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
                result is returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in
                dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_1024qam_evm, error_code = (
                self._interpreter.modacc_fetch_pdsch_1024_qam_evm_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_1024qam_evm, error_code

    @_raise_if_disposed
    def fetch_pdsc_1024_qam_evm(self, selector_string, timeout):
        r"""Fetches the physical downlink shared channel (PDSCH) 1024QAM EVMs.

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
            Tuple (mean_rms_1024qam_evm, error_code):

            mean_rms_1024qam_evm (float):
                This parameter returns a mean value of the calculated RMS EVMs on all 1024QAM modulated PDSCH resource blocks over the
                slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
                measurement is returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is
                returned in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_1024qam_evm, error_code = self._interpreter.modacc_fetch_pdsc_1024_qam_evm(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_1024qam_evm, error_code

    @_raise_if_disposed
    def fetch_pdsch_16_qam_constellation(self, selector_string, timeout, qam16_constellation):
        r"""Fetches the physical downlink shared channel (PDSCH) 16 QAM trace.

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

            qam16_constellation (numpy.complex64):
                This parameter returns the 16 QAM constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_pdsch_16_qam_constellation(
                updated_selector_string, timeout, qam16_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_256_qam_constellation(self, selector_string, timeout, qam256_constellation):
        r"""Fetches the physical downlink shared channel (PDSCH) 256 QAM trace.

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

            qam256_constellation (numpy.complex64):
                This parameter returns the 256 QAM constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_pdsch_256_qam_constellation(
                updated_selector_string, timeout, qam256_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_64_qam_constellation(self, selector_string, timeout, qam64_constellation):
        r"""Fetches the physical downlink shared channel (PDSCH) 64 QAM trace.

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

            qam64_constellation (numpy.complex64):
                This parameter returns the 64 QAM constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_pdsch_64_qam_constellation(
                updated_selector_string, timeout, qam64_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_evm_array(self, selector_string, timeout):
        r"""Fetches the array of physical downlink shared channel (PDSCH) EVM for all the component carriers within the subblock.

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
            Tuple (mean_rms_evm, mean_rms_qpsk_evm, mean_rms_16qam_evm, mean_rms_64qam_evm, mean_rms_256qam_evm, error_code):

            mean_rms_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on the PDSCH data symbols over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
                measurement is returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is
                returned in dB.

            mean_rms_qpsk_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on all QPSK modulated PDSCH resource blocks over
                the slots specified by the ModAcc Meas Length attribute. When you set the ModAcc EVM Unit attribute to **Percentage**,
                the measurement is returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is
                returned in dB.

            mean_rms_16qam_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on all 16 QAM modulated PDSCH resource blocks
                over the slots specified by the ModAcc Meas Length attribute. When you set the ModAcc EVM Unit attribute to
                **Percentage**, the measurement is returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the
                measurement is returned in dB.

            mean_rms_64qam_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on all 64 QAM modulated PDSCH resource blocks
                over the slots specified by the ModAcc Meas Length attribute. When you set the ModAcc EVM Unit attribute to
                **Percentage**, the measurement is returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the
                measurement is returned in dB.

            mean_rms_256qam_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on all 256 QAM modulated PDSCH resource blocks
                over the slots specified by the ModAcc Meas Length attribute. When you set the ModAcc EVM Unit attribute to
                **Percentage**, the measurement is returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the
                measurement is returned in dB.

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
                mean_rms_evm,
                mean_rms_qpsk_evm,
                mean_rms_16qam_evm,
                mean_rms_64qam_evm,
                mean_rms_256qam_evm,
                error_code,
            ) = self._interpreter.modacc_fetch_pdsch_evm_array(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            mean_rms_evm,
            mean_rms_qpsk_evm,
            mean_rms_16qam_evm,
            mean_rms_64qam_evm,
            mean_rms_256qam_evm,
            error_code,
        )

    @_raise_if_disposed
    def fetch_pdsch_evm(self, selector_string, timeout):
        r"""Fetches the physical downlink shared channel (PDSCH) EVMs.

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
            Tuple (mean_rms_evm, mean_rms_qpsk_evm, mean_rms_16qam_evm, mean_rms_64qam_evm, mean_rms_256qam_evm, error_code):

            mean_rms_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on PDSCH data symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement is returned
                in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            mean_rms_qpsk_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on all QPSK modulated PDSCH resource blocks over the slots
                specified by the ModAcc Meas Length attribute. When you set the ModAcc EVM Unit attribute to **Percentage**, the
                measurement is returned in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is
                returned in dB.

            mean_rms_16qam_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on all 16QAM modulated PDSCH resource blocks over the
                slots specified by the ModAcc Meas Length attribute.
                When you set the ModAcc EVM Unit attribute to **Percentage**, the measurement is returned in percentage. When you
                set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            mean_rms_64qam_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on all 64QAM modulated PDSCH resource blocks over the
                slots specified by the ModAcc Meas Length attribute.
                When you set the ModAcc EVM Unit attribute to **Percentage**, the measurement is returned in percentage. When you
                set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            mean_rms_256qam_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on all 256QAM modulated PDSCH resource blocks over the
                slots specified by the ModAcc Meas Length attribute.
                When you set the ModAcc EVM Unit attribute to **Percentage**, the measurement is returned in percentage. When you
                set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

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
                mean_rms_evm,
                mean_rms_qpsk_evm,
                mean_rms_16qam_evm,
                mean_rms_64qam_evm,
                mean_rms_256qam_evm,
                error_code,
            ) = self._interpreter.modacc_fetch_pdsch_evm(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            mean_rms_evm,
            mean_rms_qpsk_evm,
            mean_rms_16qam_evm,
            mean_rms_64qam_evm,
            mean_rms_256qam_evm,
            error_code,
        )

    @_raise_if_disposed
    def fetch_pdsch_qpsk_constellation(self, selector_string, timeout, qpsk_constellation):
        r"""Fetches the physical downlink shared channel (PDSCH) QPSK trace.

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

            qpsk_constellation (numpy.complex64):
                This parameter returns the QPSK constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_pdsch_qpsk_constellation(
                updated_selector_string, timeout, qpsk_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pssch_data_evm_array(self, selector_string, timeout):
        r"""Fetches the array of the physical sidelink shared channel (PSSCH) data EVM for ModAcc measurements.

        Use "subblock<*n*>" as the selector string to read results from this method.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        method returns the results as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the method returns
        the results in dB.

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
            Tuple (pssch_mean_rms_data_evm, pssch_maximum_peak_data_evm, error_code):

            pssch_mean_rms_data_evm (float):
                This parameter returns the array of the mean value of the RMS EVMs calculated on the PSSCH data symbols over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            pssch_maximum_peak_data_evm (float):
                This parameter returns the array of the maximum value of the peak EVMs calculated on the PSSCH data symbols over the
                slots specified by the ModAcc Meas Length attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pssch_mean_rms_data_evm, pssch_maximum_peak_data_evm, error_code = (
                self._interpreter.modacc_fetch_pssch_data_evm_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pssch_mean_rms_data_evm, pssch_maximum_peak_data_evm, error_code

    @_raise_if_disposed
    def fetch_pssch_data_evm(self, selector_string, timeout):
        r"""Fetches the physical sidelink shared channel (PSSCH) data EVM for ModAcc measurements.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results from this method.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        method returns the results as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the method returns
        the results in dB.

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
            Tuple (pssch_mean_rms_data_evm, pssch_maximum_peak_data_evm, error_code):

            pssch_mean_rms_data_evm (float):
                This parameter returns the mean value of the RMS EVMs calculated on the PSSCH data symbols over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            pssch_maximum_peak_data_evm (float):
                This parameter returns the maximum value of the peak EVMs calculated on the PSSCH data symbols over the slots specified
                by the ModAcc Meas Length attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pssch_mean_rms_data_evm, pssch_maximum_peak_data_evm, error_code = (
                self._interpreter.modacc_fetch_pssch_data_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pssch_mean_rms_data_evm, pssch_maximum_peak_data_evm, error_code

    @_raise_if_disposed
    def fetch_pssch_dmrs_evm_array(self, selector_string, timeout):
        r"""Fetches the array of the EVM values calculated on PSSCH DMRS over the length of the measurement.

        Use "subblock<*n*>" as the selector string to read results from this method.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        method returns the results as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the method returns
        the results in dB.

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
            Tuple (pssch_mean_rms_dmrs_evm, pssch_maximum_peak_dmrs_evm, error_code):

            pssch_mean_rms_dmrs_evm (float):
                This parameter returns the array of the mean value of the RMS EVMs calculated on the PSSCH DMRS symbols over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            pssch_maximum_peak_dmrs_evm (float):
                This parameter returns the array of the maximum value of the peak EVMs calculated on PSSCH DMRS symbols over the slots
                specified by the ModAcc Meas Length attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pssch_mean_rms_dmrs_evm, pssch_maximum_peak_dmrs_evm, error_code = (
                self._interpreter.modacc_fetch_pssch_dmrs_evm_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pssch_mean_rms_dmrs_evm, pssch_maximum_peak_dmrs_evm, error_code

    @_raise_if_disposed
    def fetch_pssch_dmrs_evm(self, selector_string, timeout):
        r"""Fetches the EVM values calculated on PSSCH DMRS over the length of the measurement.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results from this method.

        When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        method returns the results as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the method returns
        the results in dB.

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
            Tuple (pssch_mean_rms_dmrs_evm, pssch_maximum_peak_dmrs_evm, error_code):

            pssch_mean_rms_dmrs_evm (float):
                This parameter returns the mean value of the RMS EVMs calculated on the PSSCH DMRS symbols over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            pssch_maximum_peak_dmrs_evm (float):
                This parameter returns the maximum value of the peak EVMs calculated on PSSCH DMRS symbols over the slots specified by
                the ModAcc Meas Length attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pssch_mean_rms_dmrs_evm, pssch_maximum_peak_dmrs_evm, error_code = (
                self._interpreter.modacc_fetch_pssch_dmrs_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pssch_mean_rms_dmrs_evm, pssch_maximum_peak_dmrs_evm, error_code

    @_raise_if_disposed
    def fetch_pssch_symbol_power_array(self, selector_string, timeout):
        r"""Fetches the array of the physical sidelink shared channel (PSSCH) data symbols power and DMRS symbols power.

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
            Tuple (pssch_mean_data_power, pssch_mean_dmrs_power, error_code):

            pssch_mean_data_power (float):
                This parameter returns the array of the mean value of the power calculated on the PSSCH data symbols over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
                expressed in dBm.

            pssch_mean_dmrs_power (float):
                This parameter returns the array of the mean value of the power calculated on the PSSCH DMRS symbols over the slots
                specified by the ModAcc Meas Length attribute. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pssch_mean_data_power, pssch_mean_dmrs_power, error_code = (
                self._interpreter.modacc_fetch_pssch_symbol_power_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pssch_mean_data_power, pssch_mean_dmrs_power, error_code

    @_raise_if_disposed
    def fetch_pssch_symbol_power(self, selector_string, timeout):
        r"""Fetches the physical sidelink shared channel (PSSCH) data symbols power and DMRS symbols power.

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
            Tuple (pssch_mean_data_power, pssch_mean_dmrs_power, error_code):

            pssch_mean_data_power (float):
                This parameter returns the mean value of the power calculated on the PSSCH data symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.

            pssch_mean_dmrs_power (float):
                This parameter returns the mean value of the power calculated on the PSSCH DMRS symbols over the slots specified by the
                ModAcc Meas Length attribute. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pssch_mean_data_power, pssch_mean_dmrs_power, error_code = (
                self._interpreter.modacc_fetch_pssch_symbol_power(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pssch_mean_data_power, pssch_mean_dmrs_power, error_code

    @_raise_if_disposed
    def fetch_pusch_data_evm_array(self, selector_string, timeout):
        r"""Returns an array of the Mean RMS PUSCH data EVM and the maximum peak PUSCH data EVM.

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
            Tuple (mean_rms_data_evm, maximum_peak_data_evm, error_code):

            mean_rms_data_evm (float):
                This parameter returns the array of the mean value of the RMS EVMs calculated on PUSCH data symbols over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            maximum_peak_data_evm (float):
                This parameter returns the array of the maximum value of the peak EVMs calculated on PUSCH data symbols over the slots
                specified by the ModAcc Meas Length attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_data_evm, maximum_peak_data_evm, error_code = (
                self._interpreter.modacc_fetch_pusch_data_evm_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_data_evm, maximum_peak_data_evm, error_code

    @_raise_if_disposed
    def fetch_pusch_data_evm(self, selector_string, timeout):
        r"""Fetches the physical uplink shared channel (PUSCH) data EVM for ModAcc measurements.

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
            Tuple (mean_rms_data_evm, maximum_peak_data_evm, error_code):

            mean_rms_data_evm (float):
                This parameter returns the mean value of the RMS EVMs calculated on PUSCH data symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            maximum_peak_data_evm (float):
                This parameter returns the maximum value of the peak EVMs calculated on PUSCH data symbols over the slots specified by
                the ModAcc Meas Length attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_data_evm, maximum_peak_data_evm, error_code = (
                self._interpreter.modacc_fetch_pusch_data_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_data_evm, maximum_peak_data_evm, error_code

    @_raise_if_disposed
    def fetch_pusch_demodulated_bits(self, selector_string, timeout):
        r"""Fetches the recovered bits during EVM calculation. The bits of different slots in the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute are concatenated.

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
            Tuple (bits, error_code):

            bits (int):
                This parameter returns the array of the recovered bits during EVM calculation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            bits, error_code = self._interpreter.modacc_fetch_pusch_demodulated_bits(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return bits, error_code

    @_raise_if_disposed
    def fetch_pusch_dmrs_evm_array(self, selector_string, timeout):
        r"""Returns an array of the PUSCH mean RMS DMRS EVM and the PUSCH maximum peak DMRS EVM of all the component carriers
        within the subblock.

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
            Tuple (mean_rms_dmrs_evm, maximum_peak_dmrs_evm, error_code):

            mean_rms_dmrs_evm (float):
                This parameter returns the array of the mean value of RMS EVMs calculated on PUSCH DMRS over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            maximum_peak_dmrs_evm (float):
                This parameter returns the array of the maximum value of peak EVMs calculated on PUSCH DMRS over the slots specified by
                the ModAcc Meas Length attribute. This value is expressed in dB or in percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_dmrs_evm, maximum_peak_dmrs_evm, error_code = (
                self._interpreter.modacc_fetch_pusch_dmrs_evm_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_dmrs_evm, maximum_peak_dmrs_evm, error_code

    @_raise_if_disposed
    def fetch_pusch_dmrs_evm(self, selector_string, timeout):
        r"""Fetches the EVM values calculated on PUSCH DMRS calculated over the length of the measurement.

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
            Tuple (mean_rms_dmrs_evm, maximum_peak_dmrs_evm, error_code):

            mean_rms_dmrs_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on PUSCH DMRS over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dB or in
                percentage.

            maximum_peak_dmrs_evm (float):
                This parameter returns the maximum value of peak EVMs calculated on PUSCH DMRS over the slots specified by the ModAcc
                Meas Length attribute. This value is expressed in dB or in percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_dmrs_evm, maximum_peak_dmrs_evm, error_code = (
                self._interpreter.modacc_fetch_pusch_dmrs_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_dmrs_evm, maximum_peak_dmrs_evm, error_code

    @_raise_if_disposed
    def fetch_pusch_symbol_power_array(self, selector_string, timeout):
        r"""Returns an array of powers of the physical uplink shared channel (PUSCH) data symbols and DMRS of all the component
        carriers in the subblock.

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
            Tuple (pusch_mean_data_power, pusch_mean_dmrs_power, error_code):

            pusch_mean_data_power (float):
                This parameter returns the array of the mean value of the power calculated on PUSCH data symbols over the slots
                specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            pusch_mean_dmrs_power (float):
                This parameter returns the array of the mean value of the power calculated on PUSCH DMRS over the slots specified by
                the ModAcc Meas Length attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pusch_mean_data_power, pusch_mean_dmrs_power, error_code = (
                self._interpreter.modacc_fetch_pusch_symbol_power_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pusch_mean_data_power, pusch_mean_dmrs_power, error_code

    @_raise_if_disposed
    def fetch_pusch_symbol_power(self, selector_string, timeout):
        r"""Fetches the physical uplink shared channel (PUSCH) symbol power measurement.

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
            Tuple (pusch_mean_data_power, pusch_mean_dmrs_power, error_code):

            pusch_mean_data_power (float):
                This parameter returns the mean value of the power calculated on PUSCH data symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.

            pusch_mean_dmrs_power (float):
                This parameter returns the mean value of the power calculated on PUSCH DMRS over the slots specified by the ModAcc Meas
                Length attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pusch_mean_data_power, pusch_mean_dmrs_power, error_code = (
                self._interpreter.modacc_fetch_pusch_symbol_power(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pusch_mean_data_power, pusch_mean_dmrs_power, error_code

    @_raise_if_disposed
    def fetch_rms_magnitude_error_per_symbol_trace(
        self, selector_string, timeout, rms_magnitude_error_per_symbol
    ):
        r"""Returns the RMS mean value of the magnitude error for each symbol computed over all the allocated subcarriers and
        within the measurement length.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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

            rms_magnitude_error_per_symbol (numpy.float32):
                This parameter returns the RMS mean value of the  magnitude error for each symbol computed over all the allocated
                subcarriers and within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

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
                self._interpreter.modacc_fetch_rms_magnitude_error_per_symbol_trace(
                    updated_selector_string, timeout, rms_magnitude_error_per_symbol
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_rms_phase_error_per_symbol_trace(
        self, selector_string, timeout, rms_phase_error_per_symbol
    ):
        r"""Returns the RMS mean value of the phase error for each symbol computed over all the allocated subcarriers and within
        the measurement length.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

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

            rms_phase_error_per_symbol (numpy.float32):
                This parameter returns the results of the phase error for each symbol computed over all the allocated subcarriers and
                within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_rms_phase_error_per_symbol_trace(
                updated_selector_string, timeout, rms_phase_error_per_symbol
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_spectral_flatness_array(self, selector_string, timeout):
        r"""Returns the arrays of spectral flatness measurements of all component carriers within the subblock.

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
            Tuple (range1_maximum_to_range1_minimum, range2_maximum_to_range2_minimum, range1_maximum_to_range2_minimum, range2_maximum_to_range1_minimum, error_code):

            range1_maximum_to_range1_minimum (float):
                This parameter returns the array of the peak-to-peak ripple of the EVM equalizer coefficients within the frequency
                *Range1*. The frequency *Range1* is as defined in section 6.5.2.4.5 of the *3GPP TS 36.521 * specification.

            range2_maximum_to_range2_minimum (float):
                This parameter returns the array of the peak-to-peak ripple of the EVM equalizer coefficients within the frequency
                *Range2*. The frequency *Range2* is defined in section 6.5.2.4.5 of the *3GPP TS 36.521 * specification.

            range1_maximum_to_range2_minimum (float):
                This parameter returns the array of the peak-to-peak ripple of the EVM equalizer coefficients from the frequency
                *Range1* to the frequency *Range2*. The frequency *Range1* and 2 are defined in the section 6.5.2.4.5 of the *3GPP TS
                36.521 * specification.

            range2_maximum_to_range1_minimum (float):
                This parameter returns the array of the peak-to-peak ripple of the EVM equalizer coefficients from frequency *Range2*
                to frequency *Range1*. The frequency *Range1* and 2 are defined in section 6.5.2.4.5 of the *3GPP TS 36.521 *
                specification.

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
                range1_maximum_to_range1_minimum,
                range2_maximum_to_range2_minimum,
                range1_maximum_to_range2_minimum,
                range2_maximum_to_range1_minimum,
                error_code,
            ) = self._interpreter.modacc_fetch_spectral_flatness_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            range1_maximum_to_range1_minimum,
            range2_maximum_to_range2_minimum,
            range1_maximum_to_range2_minimum,
            range2_maximum_to_range1_minimum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_spectral_flatness(self, selector_string, timeout):
        r"""Returns the spectral flatness measurements of the component carrier.

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
            Tuple (range1_maximum_to_range1_minimum, range2_maximum_to_range2_minimum, range1_maximum_to_range2_minimum, range2_maximum_to_range1_minimum, error_code):

            range1_maximum_to_range1_minimum (float):
                This parameter returns the peak-to-peak ripple of the EVM equalizer coefficients within the frequency *Range1*. The
                frequency *Range1* is as defined in section 6.5.2.4.5 of the *3GPP TS 36.521 * specification.

            range2_maximum_to_range2_minimum (float):
                This parameter returns the peak-to-peak ripple of the EVM equalizer coefficients within the frequency *Range2*. The
                frequency *Range2* is defined in section 6.5.2.4.5 of the *3GPP TS 36.521 * specification.

            range1_maximum_to_range2_minimum (float):
                This parameter returns the peak-to-peak ripple of the EVM equalizer coefficients from the frequency *Range1* to the
                frequency *Range2*. The frequency *Range1* and 2 are defined in the section 6.5.2.4.5 of the *3GPP TS 36.521 *
                specification.

            range2_maximum_to_range1_minimum (float):
                This parameter returns the peak-to-peak ripple of the EVM equalizer coefficients from frequency *Range2* to frequency
                *Range1*. The frequency *Range1* and 2 are defined in section 6.5.2.4.5 of the *3GPP TS 36.521 * specification.

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
                range1_maximum_to_range1_minimum,
                range2_maximum_to_range2_minimum,
                range1_maximum_to_range2_minimum,
                range2_maximum_to_range1_minimum,
                error_code,
            ) = self._interpreter.modacc_fetch_spectral_flatness(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            range1_maximum_to_range1_minimum,
            range2_maximum_to_range2_minimum,
            range1_maximum_to_range2_minimum,
            range2_maximum_to_range1_minimum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_srs_constellation(self, selector_string, timeout, srs_constellation):
        r"""Fetches the constellation trace for the SRS channel.

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

            srs_constellation (numpy.complex64):
                This parameter returns the SRS constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_srs_constellation(
                updated_selector_string, timeout, srs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_srs_evm_array(self, selector_string, timeout):
        r"""Fetches the array of SRS EVMs for all the component carriers within the subblock. This value is expressed in percentage
        or dB.

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
            Tuple (mean_rms_srs_evm, mean_srs_power, error_code):

            mean_rms_srs_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on the SRS symbols over the slots specified by
                the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement is returned
                in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            mean_srs_power (float):
                This parameter returns the array of mean values of power calculated on SRS over the slots specified by the ModAcc Meas
                Length attribute. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_srs_evm, mean_srs_power, error_code = (
                self._interpreter.modacc_fetch_srs_evm_array(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_srs_evm, mean_srs_power, error_code

    @_raise_if_disposed
    def fetch_srs_evm(self, selector_string, timeout):
        r"""Fetches the mean RMS EVM and the mean power for the SRS channel.

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
            Tuple (mean_rms_srs_evm, mean_srs_power, error_code):

            mean_rms_srs_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on the SRS symbols over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement is returned
                in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            mean_srs_power (float):
                This parameter returns the mean value of power calculated on SRS over the slots specified by the ModAcc Meas Length
                attribute. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_srs_evm, mean_srs_power, error_code = self._interpreter.modacc_fetch_srs_evm(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_srs_evm, mean_srs_power, error_code

    @_raise_if_disposed
    def fetch_subblock_in_band_emission_margin(self, selector_string, timeout):
        r"""Returns the margin on non-allocated resource blocks (RBs) within the subblock aggregated bandwidth. This value is
        expressed in dB.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
        per Subblock**.

        Refer to section 6.5.2A.3 of the *3GPP TS 36.521* specification for more information about in-band emission
        margin.

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
            Tuple (subblock_in_band_emission_margin, error_code):

            subblock_in_band_emission_margin (float):
                This parameter returns the in-band emission margin of a subblock aggregated bandwidth. This value is expressed in dB.

                The margin is the lowest difference between the in-band emission measurement trace and the limit trace. The
                limit is defined in section 6.5.2A.3 of the *3GPP TS 36.521* specification.

                The in-band emissions are a measure of the interference in the non-allocated resources blocks. This result is
                valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per
                Subblock**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            subblock_in_band_emission_margin, error_code = (
                self._interpreter.modacc_fetch_subblock_in_band_emission_margin(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return subblock_in_band_emission_margin, error_code

    @_raise_if_disposed
    def fetch_subblock_in_band_emission_trace(self, selector_string, timeout):
        r"""Returns the in-band emission trace and the limit trace within the subblock aggregated bandwidth. The in-band emissions
        are a measure of the interference in the non-allocated resources blocks. The in-band emissions for various regions,
        such as general, carrier leakage, and I/Q image, are evaluated according to the method defined in the *3GPP 36.521*
        specification, and concatenated to form a composite trace.
        Limit trace is derived from the limits defined in section 6.5.2A.3 of the *3GPP TS 36.521* specification.

        The method result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
        per Subblock**.

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
            Tuple (subblock_in_band_emission, subblock_in_band_emission_mask, subblock_in_band_emission_rb_indices, error_code):

            subblock_in_band_emission (float):
                This parameter returns the array of the subblock in-band emission measurement trace.

            subblock_in_band_emission_mask (float):
                This parameter returns the array of the subblock in-band emission mask trace.

            subblock_in_band_emission_rb_indices (float):
                This parameter returns the array of the resource block indices for the subblock in-band emission trace. It can have non
                integer values depending upon the spacing between carriers.

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
                subblock_in_band_emission,
                subblock_in_band_emission_mask,
                subblock_in_band_emission_rb_indices,
                error_code,
            ) = self._interpreter.modacc_fetch_subblock_in_band_emission_trace(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            subblock_in_band_emission,
            subblock_in_band_emission_mask,
            subblock_in_band_emission_rb_indices,
            error_code,
        )

    @_raise_if_disposed
    def fetch_subblock_iq_impairments(self, selector_string, timeout):
        r"""Returns the mean I/Q origin offset, the mean I/Q gain imbalance, and the mean I/Q quadrature error of a subblock.

        This method is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
        per Subblock**. Otherwise, the method returns NaN, as measurements of this result are currently not supported.

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
            Tuple (subblock_mean_iq_origin_offset, subblock_mean_iq_gain_imbalance, subblock_mean_iq_quadrature_error, error_code):

            subblock_mean_iq_origin_offset (float):
                This parameter returns the estimated I/Q origin offset averaged over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute in a subblock. This value is expressed
                in dBc.

            subblock_mean_iq_gain_imbalance (float):
                This parameter returns the estimated I/Q gain imbalance averaged over the slots specified by the ModAcc Meas Length
                attribute. This value is expressed in dB. The I/Q gain imbalance is the ratio of the amplitude of the I component to
                the Q component of the I/Q signal being measured in the subblock.

            subblock_mean_iq_quadrature_error (float):
                This parameter returns the estimated quadrature error averaged over the slots specified by the ModAcc Meas Length
                attribute. This value is expressed in degrees. Quadrature error is a measure of the skewness of the I component with
                respect to the Q component of the I/Q signal being measured in the subblock.

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
                subblock_mean_iq_origin_offset,
                subblock_mean_iq_gain_imbalance,
                subblock_mean_iq_quadrature_error,
                error_code,
            ) = self._interpreter.modacc_fetch_subblock_iq_impairments(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            subblock_mean_iq_origin_offset,
            subblock_mean_iq_gain_imbalance,
            subblock_mean_iq_quadrature_error,
            error_code,
        )

    @_raise_if_disposed
    def fetch_synchronization_signal_constellation(
        self, selector_string, timeout, sss_constellation, pss_constellation
    ):
        r"""Fetches the constellations traces for PSS and SSS.

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

            sss_constellation (numpy.complex64):
                This parameter returns SSS constellation trace.

            pss_constellation (numpy.complex64):
                This parameter returns PSS constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_synchronization_signal_constellation(
                updated_selector_string, timeout, sss_constellation, pss_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_synchronization_signal_evm_array(self, selector_string, timeout):
        r"""Fetches the array of primary synchronization signal (PSS) EVMs and secondary synchronization signal (SSS) EVMS for all
        the component carriers within a subblock.

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
            Tuple (mean_rms_pss_evm, mean_rms_sss_evm, error_code):

            mean_rms_pss_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on PSS channel over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement is returned
                in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            mean_rms_sss_evm (float):
                This parameter returns the array of mean values of RMS EVMs calculated on SSS channel over the slots specified by the
                ModAcc Meas Length attribute. When you set the ModAcc EVM Unit attribute to **Percentage**, the measurement is returned
                in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_pss_evm, mean_rms_sss_evm, error_code = (
                self._interpreter.modacc_fetch_synchronization_signal_evm_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_pss_evm, mean_rms_sss_evm, error_code

    @_raise_if_disposed
    def fetch_synchronization_signal_evm(self, selector_string, timeout):
        r"""Fetches the primary synchronization signal (PSS) EVM and  secondary synchronization signal (SSS) EVM.

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
            Tuple (mean_rms_pss_evm, mean_rms_sss_evm, error_code):

            mean_rms_pss_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on PSS channel over the slots specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement is returned
                in percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            mean_rms_sss_evm (float):
                This parameter returns the mean value of RMS EVMs calculated on SSS channel over the slots specified by the ModAcc Meas
                Length attribute.  When you set the ModAcc EVM Unit attribute to **Percentage**, the measurement is returned in
                percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement is returned in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mean_rms_pss_evm, mean_rms_sss_evm, error_code = (
                self._interpreter.modacc_fetch_synchronization_signal_evm(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mean_rms_pss_evm, mean_rms_sss_evm, error_code

    @_raise_if_disposed
    def fetch_maximum_frequency_error_per_slot_trace(
        self, selector_string, timeout, maximum_frequency_error_per_slot
    ):
        r"""Fetches an array of the maximum value across averaging counts of the frequency error per slot for all slots within the
        measurement length. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*k*>/carrier<*k*>" as the selector string to read results from this method.

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

            maximum_frequency_error_per_slot (numpy.float32):
                This parameter returns an array of the maximum value across averaging counts of the frequency error per slot for all
                slots within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM slot position corresponding to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

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
                self._interpreter.modacc_fetch_maximum_frequency_error_per_slot_trace(
                    updated_selector_string, timeout, maximum_frequency_error_per_slot
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_npdsch_qpsk_constellation(self, selector_string, timeout, qpsk_constellation):
        r"""Fetches the narrow-band physical downlink shared channel (NPDSCH) QPSK trace.

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

            qpsk_constellation (numpy.complex64):
                This parameter returns the QPSK constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_npdsch_qpsk_constellation(
                updated_selector_string, timeout, qpsk_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_nrs_constellation(self, selector_string, timeout, nrs_constellation):
        r"""Fetches the constellation trace for a narrow-band reference signal.

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

            nrs_constellation (numpy.complex64):
                This parameter returns NRS constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_nrs_constellation(
                updated_selector_string, timeout, nrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pusch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        r"""Returns the recovered physical uplink shared channel (PUSCH) constellation points. The constellation points of
        different slots in the :py:attr:`~nirfmxlte.attributes.AttributeID.MEASUREMENT_LENGTH` are concatenated.

        Use \"carrier<*k*>\" or \"subblock<*n*>/carrier<*k*>\" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                \"subblock0/carrier0\"

                \"result::r1/subblock0/carrier0\"

                You can use the `RFmxLTE Build Carrier String <rfmxltevi.chm/RFmxLTE_Build_Carrier_String.html>`_ method to
                build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            data_constellation (numpy.complex64):
                This parameter returns the data constellation trace.

            dmrs_constellation (numpy.complex64):
                This parameter returns the demodulation reference signal (DMRS) constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_pusch_constellation_trace(
                updated_selector_string, timeout, data_constellation, dmrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_npusch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        r"""Returns the recovered narrowband physical uplink shared channel (NPUSCH) constellation points. The constellation points
        of different slots in the measurement length are concatenated.

        Use \"carrier<*k*>\" or \"subblock<*n*>/carrier<*k*>\" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                \"subblock0/carrier0\"

                \"result::r1/subblock0/carrier0\"

                You can use the `RFmxLTE Build Carrier String <rfmxltevi.chm/RFmxLTE_Build_Carrier_String.html>`_ method to
                build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            data_constellation (numpy.complex64):
                This parameter returns the data constellation trace.

            dmrs_constellation (numpy.complex64):
                This parameter returns the demodulation reference signal (DMRS) constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_npusch_constellation_trace(
                updated_selector_string, timeout, data_constellation, dmrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_nb_synchronization_signal_constellation(
        self, selector_string, timeout, nsss_constellation, npss_constellation
    ):
        r"""Fetches the NB synchronization signal constellation for ModAcc measurement.

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

            nsss_constellation (numpy.complex64):
                This parameter returns the NSSS constellation trace.

            npss_constellation (numpy.complex64):
                This parameter returns the NPSS constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_nb_synchronization_signal_constellation(
                updated_selector_string, timeout, nsss_constellation, npss_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_spectral_flatness_trace(
        self,
        selector_string,
        timeout,
        spectral_flatness,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
    ):
        r"""Fetches the spectral flatness trace for ModAcc measurement.

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

            spectral_flatness (numpy.float32):
                This parameter returns the spectral flatness trace.

            spectral_flatness_lower_mask (numpy.float32):
                This parameter returns the spectral flatness lower mask trace.

            spectral_flatness_upper_mask (numpy.float32):
                This parameter returns the spectral flatness upper mask trace.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency. This value is expressed in Hz.

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
            x0, dx, error_code = self._interpreter.modacc_fetch_spectral_flatness_trace(
                updated_selector_string,
                timeout,
                spectral_flatness,
                spectral_flatness_lower_mask,
                spectral_flatness_upper_mask,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pssch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        r"""Fetches the PSSCH constellation trace for ModAcc measurement.

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

            data_constellation (numpy.complex64):
                This parameter returns the data constellation trace.

            dmrs_constellation (numpy.complex64):
                This parameter returns the DMRS constellation trace.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_fetch_pssch_constellation_trace(
                updated_selector_string, timeout, data_constellation, dmrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
