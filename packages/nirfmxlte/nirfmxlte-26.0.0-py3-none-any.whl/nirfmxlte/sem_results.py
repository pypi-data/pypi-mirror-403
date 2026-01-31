"""Provides methods to fetch and read the Sem measurement results."""

import functools

import nirfmxlte.attributes as attributes
import nirfmxlte.enums as enums
import nirfmxlte.errors as errors
import nirfmxlte.internal._helper as _helper
import nirfmxlte.sem_component_carrier_results as component_carrier


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        meas_obj = xs[0]  # parameter 0 is 'self' which is the measurement object
        if meas_obj._signal_obj.is_disposed:
            raise Exception("Cannot access a disposed Lte signal configuration")
        return f(*xs, **kws)

    return aux


class SemResults(object):
    """Provides methods to fetch and read the Sem measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the Sem measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter
        self.component_carrier = component_carrier.SemComponentCarrierResults(signal_obj)  # type: ignore

    @_raise_if_disposed
    def get_total_aggregated_power(self, selector_string):
        r"""Gets the sum of powers of all the subblocks. This value includes the power in the inter-carrier gap within a
        subblock, but it excludes power in the  inter-subblock gaps. This value is expressed in dBm.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the sum of powers of all the subblocks. This value includes the power in the inter-carrier gap within a
                subblock, but it excludes power in the  inter-subblock gaps. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_measurement_status(self, selector_string):
        r"""Gets the overall measurement status based on the standard mask type that you configure in the
        :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

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

            attr_val (enums.SemMeasurementStatus):
                Returns the overall measurement status based on the standard mask type that you configure in the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_RESULTS_MEASUREMENT_STATUS.value
            )
            attr_val = enums.SemMeasurementStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_center_frequency(self, selector_string):
        r"""Gets the absolute center frequency of the subblock. This value is the center of the subblock integration bandwidth.
        Integration bandwidth is the span from the left edge of the leftmost carrier to the right edge of the rightmost carrier
        within the subblock. This value is expressed in Hz.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the absolute center frequency of the subblock. This value is the center of the subblock integration bandwidth.
                Integration bandwidth is the span from the left edge of the leftmost carrier to the right edge of the rightmost carrier
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
                updated_selector_string,
                attributes.AttributeID.SEM_RESULTS_SUBBLOCK_CENTER_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of the subblock. Integration bandwidth is the span from left edge of the leftmost
        carrier to the right edge of the rightmost carrier within the subblock. This value is expressed in Hz.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the integration bandwidth of the subblock. Integration bandwidth is the span from left edge of the leftmost
                carrier to the right edge of the rightmost carrier within the subblock. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_SUBBLOCK_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_power(self, selector_string):
        r"""Gets the power measured over the integration bandwidth of the subblock. This value is expressed in dBm.

        Use "subblock<*n*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power measured over the integration bandwidth of the subblock. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SEM_RESULTS_SUBBLOCK_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_measurement_status(self, selector_string):
        r"""Indicates the measurement status based on the spectrum emission limits defined by the standard mask type that you
        configure in the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM mask.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

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

            attr_val (enums.SemLowerOffsetMeasurementStatus):
                Indicates the measurement status based on the spectrum emission limits defined by the standard mask type that you
                configure in the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MEASUREMENT_STATUS.value,
            )
            attr_val = enums.SemLowerOffsetMeasurementStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_absolute_integrated_power(self, selector_string):
        r"""Gets the lower (negative) offset segment power. For the intra-band non-contiguous type of carrier aggregation, the
        offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
        specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
        offset segment is discarded, a NaN is returned. This value is expressed in dBm.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the lower (negative) offset segment power. For the intra-band non-contiguous type of carrier aggregation, the
                offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
                specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
                offset segment is discarded, a NaN is returned. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_relative_integrated_power(self, selector_string):
        r"""Gets the power in the lower (negative) offset segment relative to the total aggregated power.  For the intra-band
        non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
        overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
        performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
        in dB.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power in the lower (negative) offset segment relative to the total aggregated power.  For the intra-band
                non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
                overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
                performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
                in dB.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_RELATIVE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_absolute_peak_power(self, selector_string):
        r"""Gets the peak power in the lower (negative) offset segment.  For the intra-band non-contiguous type of carrier
        aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
        *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
        segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power in the lower (negative) offset segment.  For the intra-band non-contiguous type of carrier
                aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
                *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
                segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_relative_peak_power(self, selector_string):
        r"""Gets the peak power in the lower (negative) offset segment relative to the total aggregated power.  For the
        intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the
        offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the
        measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This
        value is expressed in dB.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power in the lower (negative) offset segment relative to the total aggregated power.  For the
                intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the
                offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the
                measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This
                value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_RELATIVE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_peak_frequency(self, selector_string):
        r"""Gets the frequency at which the peak power occurs in the lower (negative) offset segment. For the intra-band
        non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
        overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
        performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
        in Hz.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency at which the peak power occurs in the lower (negative) offset segment. For the intra-band
                non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
                overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
                performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
                in Hz.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_PEAK_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin(self, selector_string):
        r"""Gets the margin from the standard-defined absolute limit mask for the lower (negative) offset. Margin is defined as
        the minimum difference between the limit mask and the spectrum. For the intra-band non-contiguous type of carrier
        aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
        *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
        segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dB.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the margin from the standard-defined absolute limit mask for the lower (negative) offset. Margin is defined as
                the minimum difference between the limit mask and the spectrum. For the intra-band non-contiguous type of carrier
                aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
                *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
                segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin_absolute_power(self, selector_string):
        r"""Gets the power at which the margin occurs in the lower (negative) offset segment. For the intra-band non-contiguous
        type of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as
        defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the
        updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power at which the margin occurs in the lower (negative) offset segment. For the intra-band non-contiguous
                type of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as
                defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the
                updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN_ABSOLUTE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin_relative_power(self, selector_string):
        r"""Gets the power at which the margin occurs in the lower (negative) offset segment relative to the total aggregated
        power. For the intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded
        based on the offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is
        truncated, the measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is
        returned. This value is expressed in dB.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power at which the margin occurs in the lower (negative) offset segment relative to the total aggregated
                power. For the intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded
                based on the offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is
                truncated, the measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is
                returned. This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN_RELATIVE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin_frequency(self, selector_string):
        r"""Gets the frequency at which the margin occurs in the lower (negative) offset. For the intra-band non-contiguous type
        of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined
        in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated
        offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in Hz.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency at which the margin occurs in the lower (negative) offset. For the intra-band non-contiguous type
                of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined
                in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated
                offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_measurement_status(self, selector_string):
        r"""Gets the measurement status based on the user-configured standard measurement limits and the failure criteria
        specified by Limit Fail Mask for the upper (positive) offset. For intra-band non-contiguous case, the offset segment
        may be truncated or discarded based on offset overlap rules defined in the *3GPP TS 36.521* specification. If the
        offset segment is truncated, the measurement is performed on the updated offset segment. If the offset segment is
        discarded, a NaN is returned.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

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

            attr_val (enums.SemUpperOffsetMeasurementStatus):
                Returns the measurement status based on the user-configured standard measurement limits and the failure criteria
                specified by Limit Fail Mask for the upper (positive) offset. For intra-band non-contiguous case, the offset segment
                may be truncated or discarded based on offset overlap rules defined in the *3GPP TS 36.521* specification. If the
                offset segment is truncated, the measurement is performed on the updated offset segment. If the offset segment is
                discarded, a NaN is returned.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MEASUREMENT_STATUS.value,
            )
            attr_val = enums.SemUpperOffsetMeasurementStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_absolute_integrated_power(self, selector_string):
        r"""Gets the upper (positive) offset segment power. For the intra-band non-contiguous type of carrier aggregation, the
        offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
        specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
        offset segment is discarded, a NaN is returned. This value is expressed in dBm.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the upper (positive) offset segment power. For the intra-band non-contiguous type of carrier aggregation, the
                offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
                specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
                offset segment is discarded, a NaN is returned. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_relative_integrated_power(self, selector_string):
        r"""Gets the power in the upper (positive) offset segment relative to the total aggregated power.

        For the intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded
        based on the offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is
        truncated, the measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is
        returned. This value is expressed in dB.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power in the upper (positive) offset segment relative to the total aggregated power.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_RELATIVE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_absolute_peak_power(self, selector_string):
        r"""Gets the power in the upper (positive) offset segment. For the intra-band non-contiguous type of carrier
        aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
        *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
        segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power in the upper (positive) offset segment. For the intra-band non-contiguous type of carrier
                aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
                *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
                segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_relative_peak_power(self, selector_string):
        r"""Gets the peak power in the upper (positive) offset segment relative to the total aggregated power. For the
        intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the
        offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the
        measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This
        value is expressed in dB.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power in the upper (positive) offset segment relative to the total aggregated power. For the
                intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the
                offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the
                measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This
                value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_RELATIVE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_peak_frequency(self, selector_string):
        r"""Gets the frequency at which the peak power occurs in the upper (positive) offset segment.  For the intra-band
        non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
        overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
        performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
        in Hz.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency at which the peak power occurs in the upper (positive) offset segment.  For the intra-band
                non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
                overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
                performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
                in Hz.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_PEAK_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin(self, selector_string):
        r"""Gets the margin from the absolute limit mask for the upper (positive) offset. The Margin is defined as the minimum
        difference between the limit mask and the spectrum. For the intra-band non-contiguous type of carrier aggregation, the
        offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
        specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
        offset segment is discarded, a NaN is returned. This value is expressed in Hz.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the margin from the absolute limit mask for the upper (positive) offset. The Margin is defined as the minimum
                difference between the limit mask and the spectrum. For the intra-band non-contiguous type of carrier aggregation, the
                offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
                specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
                offset segment is discarded, a NaN is returned. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin_absolute_power(self, selector_string):
        r"""Gets the power at which the margin occurs in the upper (positive) offset segment. For the intra-band non-contiguous
        type of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as
        defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the
        updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power at which the margin occurs in the upper (positive) offset segment. For the intra-band non-contiguous
                type of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as
                defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the
                updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN_ABSOLUTE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin_relative_power(self, selector_string):
        r"""Gets the power at which the margin occurs in the upper (positive) offset segment relative to the total aggregated
        power. For the intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded
        based on the offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is
        truncated, the measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is
        returned. This value is expressed in dB.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power at which the margin occurs in the upper (positive) offset segment relative to the total aggregated
                power. For the intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded
                based on the offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is
                truncated, the measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is
                returned. This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN_RELATIVE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin_frequency(self, selector_string):
        r"""Gets the frequency at which the margin occurs in the upper (positive) offset. For the intra-band non-contiguous type
        of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined
        in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated
        offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in Hz.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information about SEM offsets.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency at which the margin occurs in the upper (positive) offset. For the intra-band non-contiguous type
                of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined
                in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated
                offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_lower_offset_margin_array(self, selector_string, timeout):
        r"""Returns an array of measurement statuses, margins, frequencies at margins, and absolute and relative powers at margins
        for lower offset segments. The relative power is relative to the total aggregated power.

        Use "subblock<*n*>" as the selector string to read results from this method.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information.

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
            Tuple (measurement_status, margin, margin_frequency, margin_absolute_power, margin_relative_power, error_code):

            measurement_status (enums.SemLowerOffsetMeasurementStatus):
                This parameter returns the array of the measurement status indicating whether the power before and after the burst is
                within the standard defined limit.

                +--------------+--------------------------------------------+
                | Name (Value) | Description                                |
                +==============+============================================+
                | Fail (0)     | Indicates that the measurement has failed. |
                +--------------+--------------------------------------------+
                | Pass (1)     | Indicates that the measurement has passed. |
                +--------------+--------------------------------------------+

            margin (float):
                This parameter returns the array of margins from the standard-defined absolute limit mask for the lower (negative)
                offset. Margin is defined as the minimum difference between the spectrum and the limit mask. For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the SEM results lower
                offset start frequency and SEM results lower offset stop frequency are updated, and the measurement is performed on the
                updated offset segment. If the offset segment is discarded, a NaN is returned.

            margin_frequency (float):
                This parameter returns the array of frequency at which the margin occurs in the lower (negative) offset. For the
                intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset
                overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the SEM results
                lower offset start frequency and SEM results lower offset stop frequency are updated, and the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            margin_absolute_power (float):
                This parameter returns the array of power at which the margin occurs in the upper (positive) offset segment. For the
                intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset
                overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the SEM results
                lower offset start frequency and SEM results lower offset stop frequency are updated, and the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            margin_relative_power (float):
                This parameter returns the array of powers at which the margin occurs in the upper (positive) offset segment relative
                to the value returned by the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute.
                For the intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on
                offset overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the
                measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned.

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
                margin,
                margin_frequency,
                margin_absolute_power,
                margin_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_lower_offset_margin_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_lower_offset_margin(self, selector_string, timeout):
        r"""Returns the measurement status, margin, frequency at margin, and the absolute and relative powers at the margin for
        lower offset segments. The relative power is relative to the total aggregated power.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to read results from this method.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and offset number.

                Example:

                "subblock0/offset0"

                "result::r1/subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (measurement_status, margin, margin_frequency, margin_absolute_power, margin_relative_power, error_code):

            measurement_status (enums.SemLowerOffsetMeasurementStatus):
                This parameter returns the measurement status indicating whether the power before and after the burst is within the
                standard defined limit.

                +--------------+--------------------------------------------+
                | Name (Value) | Description                                |
                +==============+============================================+
                | Fail (0)     | Indicates that the measurement has failed. |
                +--------------+--------------------------------------------+
                | Pass (1)     | Indicates that the measurement has passed. |
                +--------------+--------------------------------------------+

            margin (float):
                This parameter returns the margin from the standard-defined absolute limit mask for the lower (negative) offset. Margin
                is defined as the minimum difference between the spectrum and the limit mask. For the intra-band noncontiguous type of
                carrier aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the
                *3GPP TS 36.521* specification. If the offset segment is truncated, the SEM results lower offset start frequency and
                SEM results lower offset stop frequency are updated, and the measurement is performed on the updated offset segment. If
                the offset segment is discarded, a NaN is returned.

            margin_frequency (float):
                This parameter returns the frequency at which the margin occurs in the lower (negative) offset. For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the SEM results lower
                offset start frequency and SEM results lower offset stop frequency are updated, and the measurement is performed on the
                updated offset segment. If the offset segment is discarded, a NaN is returned.

            margin_absolute_power (float):
                This parameter returns the power at which the margin occurs in the upper (positive) offset segment. For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the SEM results lower
                offset start frequency and SEM results lower offset stop frequency are updated, and the measurement is performed on the
                updated offset segment. If the offset segment is discarded, a NaN is returned.

            margin_relative_power (float):
                This parameter returns the power at which the margin occurs in the upper (positive) offset segment relative to the
                value returned by the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute. For
                the intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on
                offset overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the
                measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned.

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
                margin,
                margin_frequency,
                margin_absolute_power,
                margin_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_lower_offset_margin(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_lower_offset_power_array(self, selector_string, timeout):
        r"""Returns an array of total absolute and relative powers, peak, absolute, and relative powers, and frequencies at peak
        absolute powers of lower offset segments. The relative power is relative to total aggregated power.

        Use "subblock<*n*>" as the selector string to read results from this method.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information.

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
            Tuple (absolute_integrated_power, relative_integrated_power, absolute_peak_power, peak_frequency, relative_peak_power, error_code):

            absolute_integrated_power (float):
                This parameter returns the array of lower (negative) offset segment powers. For the intra-band noncontiguous type of
                carrier aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the
                *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed on the updated offset
                segment. If the offset segment is discarded, a NaN is returned.

            relative_integrated_power (float):
                This parameter returns the array of powers in the lower (negative) offset segment relative to the value returned by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute.  For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            absolute_peak_power (float):
                This parameter returns the array of peak powers in the lower (negative) offset segment.  For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            peak_frequency (float):
                This parameter returns the array of frequency at which the peak power occurs in the upper (positive) offset segment.
                For the intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on
                offset overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the
                measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            relative_peak_power (float):
                This parameter returns the array of peak power in the upper (positive) offset segment relative to the value returned by
                the SEM Results Total Aggregated Pwr attribute. For the intra-band noncontiguous type of carrier aggregation, the
                offset segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS 36.521*
                specification. If the offset segment is truncated the measurement is performed on the updated offset segment. If the
                offset segment is discarded, a NaN is returned.

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
                absolute_integrated_power,
                relative_integrated_power,
                absolute_peak_power,
                peak_frequency,
                relative_peak_power,
                error_code,
            ) = self._interpreter.sem_fetch_lower_offset_power_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            absolute_integrated_power,
            relative_integrated_power,
            absolute_peak_power,
            peak_frequency,
            relative_peak_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_lower_offset_power(self, selector_string, timeout):
        r"""Returns the total absolute and relative powers, peak, absolute, and relative powers, and the frequency at the peak
        absolute power of the lower offset segment. The relative power is relative to the total aggregated power.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to read results from this method.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and offset number.

                Example:

                "subblock0/offset0"

                "result::r1/subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (absolute_integrated_power, relative_integrated_power, absolute_peak_power, peak_frequency, relative_peak_power, error_code):

            absolute_integrated_power (float):
                This parameter returns the lower (negative) offset segment power. For the intra-band noncontiguous type of carrier
                aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS
                36.521* specification. If the offset segment is truncated the measurement is performed on the updated offset segment.
                If the offset segment is discarded, a NaN is returned.

            relative_integrated_power (float):
                This parameter returns the power in the lower (negative) offset segment relative to the value returned by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute.  For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            absolute_peak_power (float):
                This parameter returns the peak power in the lower (negative) offset segment.  For the intra-band noncontiguous type of
                carrier aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the
                *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed on the updated offset
                segment. If the offset segment is discarded, a NaN is returned.

            peak_frequency (float):
                This parameter returns the frequency at which the peak power occurs in the upper (positive) offset segment. For the
                intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset
                overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is
                performed on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            relative_peak_power (float):
                This parameter returns the peak power in the upper (positive) offset segment relative to the value returned by the SEM
                Results Total Aggregated Pwr attribute. For the intra-band noncontiguous type of carrier aggregation, the offset
                segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS 36.521* specification.
                If the offset segment is truncated the measurement is performed on the updated offset segment. If the offset segment is
                discarded, a NaN is returned.

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
                absolute_integrated_power,
                relative_integrated_power,
                absolute_peak_power,
                peak_frequency,
                relative_peak_power,
                error_code,
            ) = self._interpreter.sem_fetch_lower_offset_power(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            absolute_integrated_power,
            relative_integrated_power,
            absolute_peak_power,
            peak_frequency,
            relative_peak_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_measurement_status(self, selector_string, timeout):
        r"""Returns the overall measurement status based on the standard mask type that you configure.

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
            Tuple (measurement_status, error_code):

            measurement_status (enums.SemMeasurementStatus):
                This parameter returns the measurement status indicating whether the power before and after the burst is within the
                standard defined limit.

                +--------------+--------------------------------------------+
                | Name (Value) | Description                                |
                +==============+============================================+
                | Fail (0)     | Indicates that the measurement has failed. |
                +--------------+--------------------------------------------+
                | Pass (1)     | Indicates that the measurement has passed. |
                +--------------+--------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            measurement_status, error_code = self._interpreter.sem_fetch_measurement_status(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return measurement_status, error_code

    @_raise_if_disposed
    def fetch_spectrum(self, selector_string, timeout, spectrum, composite_mask):
        r"""Fetches the spectrum used for the SEM measurement.

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

            composite_mask (numpy.float32):
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
            x0, dx, error_code = self._interpreter.sem_fetch_spectrum(
                updated_selector_string, timeout, spectrum, composite_mask
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
                This parameter returns the integration bandwidth of the subblock. Integration bandwidth is the span from left edge of
                the leftmost carrier to the right edge of the rightmost carrier within a subblock. This value is expressed in Hz.

            frequency (float):
                This parameter returns the absolute center frequency of the subblock. This value is the center of the subblock
                integration bandwidth. This value is expressed in Hz.

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
                self._interpreter.sem_fetch_subblock_measurement(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return subblock_power, integration_bandwidth, frequency, error_code

    @_raise_if_disposed
    def fetch_total_aggregated_power(self, selector_string, timeout):
        r"""Returns the sum of powers of all subblocks.

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
            total_aggregated_power, error_code = self._interpreter.sem_fetch_total_aggregated_power(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return total_aggregated_power, error_code

    @_raise_if_disposed
    def fetch_upper_offset_margin_array(self, selector_string, timeout):
        r"""Returns an array of measurement statuses, margins, frequencies at margins, and absolute and relative powers at margins
        for upper offset segments. The relative power is relative to total aggregated power.

        Use "subblock<*n*>" as the selector string to read results from this method.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information.

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
            Tuple (measurement_status, margin, margin_frequency, margin_absolute_power, margin_relative_power, error_code):

            measurement_status (enums.SemUpperOffsetMeasurementStatus):
                This parameter returns the array of the measurement status indicating whether the power before and after the burst is
                within the standard defined limit.

                +--------------+--------------------------------------------+
                | Name (Value) | Description                                |
                +==============+============================================+
                | Fail (0)     | Indicates that the measurement has failed. |
                +--------------+--------------------------------------------+
                | Pass (1)     | Indicates that the measurement has passed. |
                +--------------+--------------------------------------------+

            margin (float):
                This parameter returns the array of margins from the standard defined absolute limit mask for upper offset. The margin
                is defined as the minimum difference between the spectrum and the limit mask. For the intra-band noncontiguous type of
                carrier aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the
                *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed on the updated offset
                segment. If the offset segment is discarded, a NaN is returned.

            margin_frequency (float):
                This parameter returns the array of frequency at which the margin occurs in the upper offset. For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            margin_absolute_power (float):
                This parameter returns the array of power at which the margin occurs in the upper (positive) offset segment. For the
                intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset
                overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the SEM results
                lower offset start frequency and SEM results lower offset stop frequency are updated, and the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            margin_relative_power (float):
                This parameter returns the array of powers at which the margin occurs in the upper (positive) offset segment relative
                to the value returned by the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute.
                For the intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on
                offset overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the
                measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned.

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
                margin,
                margin_frequency,
                margin_absolute_power,
                margin_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_upper_offset_margin_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_upper_offset_margin(self, selector_string, timeout):
        r"""Returns the measurement status, margin,  frequency at margin, and absolute and relative powers at margin for upper
        offset segments. The relative power is relative to total aggregated power.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to read results from this method.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and offset number.

                Example:

                "subblock0/offset0"

                "result::r1/subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (measurement_status, margin, margin_frequency, margin_absolute_power, margin_relative_power, error_code):

            measurement_status (enums.SemUpperOffsetMeasurementStatus):
                This parameter returns the measurement status indicating whether the power before and after the burst is within the
                standard defined limit.

                +--------------+--------------------------------------------+
                | Name (Value) | Description                                |
                +==============+============================================+
                | Fail (0)     | Indicates that the measurement has failed. |
                +--------------+--------------------------------------------+
                | Pass (1)     | Indicates that the measurement has passed. |
                +--------------+--------------------------------------------+

            margin (float):
                This parameter returns the margin from the standard defined absolute limit mask for upper offset. Margin is defined as
                the minimum difference between the spectrum and the limit mask. For the intra-band noncontiguous type of carrier
                aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS
                36.521* specification. If the offset segment is truncated the measurement is performed on the updated offset segment.
                If the offset segment is discarded, a NaN is returned.

            margin_frequency (float):
                This parameter returns the frequency at which the margin occurs in the upper offset. For the intra-band noncontiguous
                type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined
                in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed on the updated
                offset segment. If the offset segment is discarded, a NaN is returned.

            margin_absolute_power (float):
                This parameter returns the power at which the margin occurs in the upper (positive) offset segment. For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the SEM results lower
                offset start frequency and SEM results lower offset stop frequency are updated, and the measurement is performed on the
                updated offset segment. If the offset segment is discarded, a NaN is returned.

            margin_relative_power (float):
                This parameter returns the power at which the margin occurs in the upper (positive) offset segment relative to the
                value returned by the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute. For
                the intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on
                offset overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the
                measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned.

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
                margin,
                margin_frequency,
                margin_absolute_power,
                margin_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_upper_offset_margin(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_upper_offset_power_array(self, selector_string, timeout):
        r"""Returns an array of total absolute and relative powers, peak, absolute, and relative powers, and frequencies at peak
        absolute powers of upper offset segments. The relative power is relative to total aggregated power.

        Use "subblock<*n*>" as the selector string to read results from this method.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information.

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
            Tuple (absolute_integrated_power, relative_integrated_power, absolute_peak_power, peak_frequency, relative_peak_power, error_code):

            absolute_integrated_power (float):
                This parameter returns the array of upper offset segment powers. For the intra-band noncontiguous type of carrier
                aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS
                36.521* specification. If the offset segment is truncated the measurement is performed on the updated offset segment.
                If the offset segment is discarded, a NaN is returned.

            relative_integrated_power (float):
                This parameter returns the array of powers in the upper offset segment relative to the value returned by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute.  For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            absolute_peak_power (float):
                This parameter returns the array of peak powers in the upper offset segment.  For the intra-band noncontiguous type of
                carrier aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the
                *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed on the updated offset
                segment. If the offset segment is discarded, a NaN is returned.

            peak_frequency (float):
                This parameter returns the array of frequency at which the peak power occurs in the upper (positive) offset segment.
                For the intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on
                offset overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the
                measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            relative_peak_power (float):
                This parameter returns the array of peak power in the upper (positive) offset segment relative to the value returned by
                the SEM Results Total Aggregated Pwr attribute. For the intra-band noncontiguous type of carrier aggregation, the
                offset segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS 36.521*
                specification. If the offset segment is truncated the measurement is performed on the updated offset segment. If the
                offset segment is discarded, a NaN is returned.

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
                absolute_integrated_power,
                relative_integrated_power,
                absolute_peak_power,
                peak_frequency,
                relative_peak_power,
                error_code,
            ) = self._interpreter.sem_fetch_upper_offset_power_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            absolute_integrated_power,
            relative_integrated_power,
            absolute_peak_power,
            peak_frequency,
            relative_peak_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_upper_offset_power(self, selector_string, timeout):
        r"""Returns the total absolute and relative powers, peak, absolute, and relative powers, and frequency at peak absolute
        power of upper offset segment. The relative power is relative to total aggregated power.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to read results from this method.

        Refer to the `LTE Uplink Spectral Emission Mask
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
        Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
        topics for more information.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and offset number.

                Example:

                "subblock0/offset0"

                "result::r1/subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (absolute_integrated_power, relative_integrated_power, absolute_peak_power, peak_frequency, relative_peak_power, error_code):

            absolute_integrated_power (float):
                This parameter returns the upper offset segment power. For the intra-band noncontiguous type of carrier aggregation,
                the offset segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS 36.521*
                specification. If the offset segment is truncated the measurement is performed on the updated offset segment. If the
                offset segment is discarded, a NaN is returned.

            relative_integrated_power (float):
                This parameter returns the power in the upper offset segment relative to the value returned by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute.  For the intra-band
                noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset overlap
                rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is performed
                on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            absolute_peak_power (float):
                This parameter returns the peak power in the upper offset segment.  For the intra-band noncontiguous type of carrier
                aggregation, the offset segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS
                36.521* specification. If the offset segment is truncated the measurement is performed on the updated offset segment.
                If the offset segment is discarded, a NaN is returned.

            peak_frequency (float):
                This parameter returns the frequency at which the peak power occurs in the upper (positive) offset segment. For the
                intra-band noncontiguous type of carrier aggregation, the offset segment may be truncated or discarded based on offset
                overlap rules as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated the measurement is
                performed on the updated offset segment. If the offset segment is discarded, a NaN is returned.

            relative_peak_power (float):
                This parameter returns the peak power in the upper (positive) offset segment relative to the value returned by the SEM
                Results Total Aggregated Pwr attribute. For the intra-band noncontiguous type of carrier aggregation, the offset
                segment may be truncated or discarded based on offset overlap rules as defined in the *3GPP TS 36.521* specification.
                If the offset segment is truncated the measurement is performed on the updated offset segment. If the offset segment is
                discarded, a NaN is returned.

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
                absolute_integrated_power,
                relative_integrated_power,
                absolute_peak_power,
                peak_frequency,
                relative_peak_power,
                error_code,
            ) = self._interpreter.sem_fetch_upper_offset_power(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            absolute_integrated_power,
            relative_integrated_power,
            absolute_peak_power,
            peak_frequency,
            relative_peak_power,
            error_code,
        )
