"""Provides methods to configure the SlotPower measurement."""

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


class SlotPowerConfiguration(object):
    """Provides methods to configure the SlotPower measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the SlotPower measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the SlotPower measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable the SlotPower measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPOWER_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the SlotPower measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the SlotPower measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPOWER_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_offset(self, selector_string):
        r"""Gets the measurement offset to skip from the frame boundary or the marker (external trigger) location. This value
        is expressed in subframe.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the measurement offset to skip from the frame boundary or the marker (external trigger) location. This value
                is expressed in subframe.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPOWER_MEASUREMENT_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_offset(self, selector_string, value):
        r"""Sets the measurement offset to skip from the frame boundary or the marker (external trigger) location. This value
        is expressed in subframe.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the measurement offset to skip from the frame boundary or the marker (external trigger) location. This value
                is expressed in subframe.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPOWER_MEASUREMENT_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_length(self, selector_string):
        r"""Gets the number of subframes to be measured. This value is expressed in subframe.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of subframes to be measured. This value is expressed in subframe.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPOWER_MEASUREMENT_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_length(self, selector_string, value):
        r"""Sets the number of subframes to be measured. This value is expressed in subframe.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of subframes to be measured. This value is expressed in subframe.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPOWER_MEASUREMENT_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_common_clock_source_enabled(self, selector_string):
        r"""Gets whether the same Reference Clock is used for the local oscillator and the digital-to-analog converter in the
        transmitter. When the same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------+
        | Name (Value) | Description                                                        |
        +==============+====================================================================+
        | False (0)    | The Sample Clock error is estimated independently.                 |
        +--------------+--------------------------------------------------------------------+
        | True (1)     | The Sample Clock error is estimated from carrier frequency offset. |
        +--------------+--------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SlotPowerCommonClockSourceEnabled):
                Specifies whether the same Reference Clock is used for the local oscillator and the digital-to-analog converter in the
                transmitter. When the same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

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
                attributes.AttributeID.SLOTPOWER_COMMON_CLOCK_SOURCE_ENABLED.value,
            )
            attr_val = enums.SlotPowerCommonClockSourceEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_common_clock_source_enabled(self, selector_string, value):
        r"""Sets whether the same Reference Clock is used for the local oscillator and the digital-to-analog converter in the
        transmitter. When the same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------+
        | Name (Value) | Description                                                        |
        +==============+====================================================================+
        | False (0)    | The Sample Clock error is estimated independently.                 |
        +--------------+--------------------------------------------------------------------+
        | True (1)     | The Sample Clock error is estimated from carrier frequency offset. |
        +--------------+--------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SlotPowerCommonClockSourceEnabled, int):
                Specifies whether the same Reference Clock is used for the local oscillator and the digital-to-analog converter in the
                transmitter. When the same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SlotPowerCommonClockSourceEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPOWER_COMMON_CLOCK_SOURCE_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_spectrum_inverted(self, selector_string):
        r"""Gets whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
        components of the baseband complex signal are swapped.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                     |
        +==============+=================================================================================================================+
        | False (0)    | The spectrum of the measured signal is not inverted.                                                            |
        +--------------+-----------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components. |
        +--------------+-----------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SlotPowerSpectrumInverted):
                Specifies whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
                components of the baseband complex signal are swapped.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPOWER_SPECTRUM_INVERTED.value
            )
            attr_val = enums.SlotPowerSpectrumInverted(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_spectrum_inverted(self, selector_string, value):
        r"""Sets whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
        components of the baseband complex signal are swapped.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                     |
        +==============+=================================================================================================================+
        | False (0)    | The spectrum of the measured signal is not inverted.                                                            |
        +--------------+-----------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components. |
        +--------------+-----------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SlotPowerSpectrumInverted, int):
                Specifies whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
                components of the baseband complex signal are swapped.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SlotPowerSpectrumInverted else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPOWER_SPECTRUM_INVERTED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the SlotPower measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the SlotPower measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPOWER_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the SlotPower measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the SlotPower measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPOWER_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_measurement_interval(
        self, selector_string, measurement_offset, measurement_length
    ):
        r"""Configures the **Measurement Offset** and **Measurement Length** parameters of SlotPower measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_offset (int):
                This parameter specifies the measurement offset to skip from the frame boundary or the marker (external trigger)
                location. This value is expressed in subframes. The default value is 0.

            measurement_length (int):
                This parameter specifies the number of subframes to be measured. This value is expressed in subframes. The default
                value is 10.

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
            error_code = self._interpreter.slotpower_configure_measurement_interval(
                updated_selector_string, measurement_offset, measurement_length
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
