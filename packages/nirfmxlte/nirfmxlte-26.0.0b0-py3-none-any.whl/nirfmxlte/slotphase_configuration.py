"""Provides methods to configure the SlotPhase measurement."""

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


class SlotPhaseConfiguration(object):
    """Provides methods to configure the SlotPhase measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the SlotPhase measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the SlotPhase measurement.

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
                Specifies whether to enable the SlotPhase measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPHASE_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the SlotPhase measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the SlotPhase measurement.

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
                attributes.AttributeID.SLOTPHASE_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_synchronization_mode(self, selector_string):
        r"""Gets whether the measurement is performed from the frame or the slot boundary.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Slot**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Frame (0)    | The frame boundary in the acquired signal is detected, and the measurement is performed over the number of slots         |
        |              | specified by the SlotPhase Meas Length attribute, starting at the offset from the boundary specified by the SlotPhase    |
        |              | Meas Offset attribute. When the Trigger Type attribute is set to Digital, the measurement expects a trigger at the       |
        |              | frame boundary.                                                                                                          |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Slot (1)     | The slot boundary in the acquired signal is detected, and the measurement is performed over the number of slots          |
        |              | specified by the SlotPhase Meas Length attribute, starting at the offset from the boundary specified by the SlotPhase    |
        |              | Meas Offset attribute. When the Trigger Type attribute is set to Digital, the measurement expects a trigger at any slot  |
        |              | boundary.                                                                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SlotPhaseSynchronizationMode):
                Specifies whether the measurement is performed from the frame or the slot boundary.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPHASE_SYNCHRONIZATION_MODE.value
            )
            attr_val = enums.SlotPhaseSynchronizationMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_synchronization_mode(self, selector_string, value):
        r"""Sets whether the measurement is performed from the frame or the slot boundary.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Slot**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Frame (0)    | The frame boundary in the acquired signal is detected, and the measurement is performed over the number of slots         |
        |              | specified by the SlotPhase Meas Length attribute, starting at the offset from the boundary specified by the SlotPhase    |
        |              | Meas Offset attribute. When the Trigger Type attribute is set to Digital, the measurement expects a trigger at the       |
        |              | frame boundary.                                                                                                          |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Slot (1)     | The slot boundary in the acquired signal is detected, and the measurement is performed over the number of slots          |
        |              | specified by the SlotPhase Meas Length attribute, starting at the offset from the boundary specified by the SlotPhase    |
        |              | Meas Offset attribute. When the Trigger Type attribute is set to Digital, the measurement expects a trigger at any slot  |
        |              | boundary.                                                                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SlotPhaseSynchronizationMode, int):
                Specifies whether the measurement is performed from the frame or the slot boundary.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SlotPhaseSynchronizationMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPHASE_SYNCHRONIZATION_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_offset(self, selector_string):
        r"""Gets the measurement offset to skip from the synchronization boundary. This value is expressed in slots. The
        synchronization boundary is specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_SYNCHRONIZATION_MODE` attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. Valid values are 0 to 19, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the measurement offset to skip from the synchronization boundary. This value is expressed in slots. The
                synchronization boundary is specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_SYNCHRONIZATION_MODE` attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPHASE_MEASUREMENT_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_offset(self, selector_string, value):
        r"""Sets the measurement offset to skip from the synchronization boundary. This value is expressed in slots. The
        synchronization boundary is specified by the
        :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_SYNCHRONIZATION_MODE` attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. Valid values are 0 to 19, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the measurement offset to skip from the synchronization boundary. This value is expressed in slots. The
                synchronization boundary is specified by the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_SYNCHRONIZATION_MODE` attribute.

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
                attributes.AttributeID.SLOTPHASE_MEASUREMENT_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_length(self, selector_string):
        r"""Gets the number of slots to be measured. This value is expressed in slots.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 20.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of slots to be measured. This value is expressed in slots.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_length(self, selector_string, value):
        r"""Sets the number of slots to be measured. This value is expressed in slots.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 20.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of slots to be measured. This value is expressed in slots.

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
                attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_exclusion_period_enabled(self, selector_string):
        r"""Gets whether to exclude some portions of the slots when calculating the phase. This attribute is valid only when
        there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP 36.521-1* specification for more
        information about the exclusion.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Phase is calculated on complete slots.                                                                                   |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Phase is calculated on truncated slots. The power changes at the slot boundaries are detected by the measurement, and    |
        |              | the defined 3GPP specification period is excluded from the slots being measured.                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SlotPhaseExclusionPeriodEnabled):
                Specifies whether to exclude some portions of the slots when calculating the phase. This attribute is valid only when
                there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP 36.521-1* specification for more
                information about the exclusion.

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
                attributes.AttributeID.SLOTPHASE_EXCLUSION_PERIOD_ENABLED.value,
            )
            attr_val = enums.SlotPhaseExclusionPeriodEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_exclusion_period_enabled(self, selector_string, value):
        r"""Sets whether to exclude some portions of the slots when calculating the phase. This attribute is valid only when
        there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP 36.521-1* specification for more
        information about the exclusion.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Phase is calculated on complete slots.                                                                                   |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Phase is calculated on truncated slots. The power changes at the slot boundaries are detected by the measurement, and    |
        |              | the defined 3GPP specification period is excluded from the slots being measured.                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SlotPhaseExclusionPeriodEnabled, int):
                Specifies whether to exclude some portions of the slots when calculating the phase. This attribute is valid only when
                there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP 36.521-1* specification for more
                information about the exclusion.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SlotPhaseExclusionPeriodEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPHASE_EXCLUSION_PERIOD_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_common_clock_source_enabled(self, selector_string):
        r"""Gets whether the same Reference Clock is used for local oscillator and the digital-to-analog converter. When the
        same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

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

            attr_val (enums.SlotPhaseCommonClockSourceEnabled):
                Specifies whether the same Reference Clock is used for local oscillator and the digital-to-analog converter. When the
                same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

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
                attributes.AttributeID.SLOTPHASE_COMMON_CLOCK_SOURCE_ENABLED.value,
            )
            attr_val = enums.SlotPhaseCommonClockSourceEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_common_clock_source_enabled(self, selector_string, value):
        r"""Sets whether the same Reference Clock is used for local oscillator and the digital-to-analog converter. When the
        same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

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

            value (enums.SlotPhaseCommonClockSourceEnabled, int):
                Specifies whether the same Reference Clock is used for local oscillator and the digital-to-analog converter. When the
                same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SlotPhaseCommonClockSourceEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPHASE_COMMON_CLOCK_SOURCE_ENABLED.value,
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

            attr_val (enums.SlotPhaseSpectrumInverted):
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
                updated_selector_string, attributes.AttributeID.SLOTPHASE_SPECTRUM_INVERTED.value
            )
            attr_val = enums.SlotPhaseSpectrumInverted(attr_val)
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

            value (enums.SlotPhaseSpectrumInverted, int):
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
            value = value.value if type(value) is enums.SlotPhaseSpectrumInverted else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SLOTPHASE_SPECTRUM_INVERTED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the SlotPhase measurement.

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
                Specifies whether to enable the traces to be stored and retrieved after performing the SlotPhase measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SLOTPHASE_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the SlotPhase measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the SlotPhase measurement.

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
                attributes.AttributeID.SLOTPHASE_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_synchronization_mode_and_interval(
        self, selector_string, synchronization_mode, measurement_offset, measurement_length
    ):
        r"""Configures the **Synchronization Mode**, **Measurement Offset**, and **Measurement Length** parameters of SlotPhase
        measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            synchronization_mode (enums.SlotPhaseSynchronizationMode, int):
                This parameter specifies whether the measurement is performed from the frame or the slot boundary. The default value is
                **Slot**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | Frame  (0)   | The frame boundary in the acquired signal is detected, and the measurement is performed over the number of slots         |
                |              | specified by the Measurement Length parameter, starting at the offset from the boundary specified by the Measurement     |
                |              | Offset parameter. When you set the Trigger Type attribute to Digital Edge, the measurement expects a trigger at the      |
                |              | frame boundary.                                                                                                          |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Slot (1)     | The slot boundary the acquired signal is detected, and the measurement is performed over the number of slots specified   |
                |              | by the Measurement Length parameter, starting at the offset from the boundary specified by the Measurement Offset        |
                |              | parameter. When you set the Trigger Type attribute to Digital Edge, the measurement expects a trigger at any slot        |
                |              | boundary.                                                                                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            measurement_offset (int):
                This parameter specifies the measurement offset to skip from the synchronization boundary. The synchronization boundary
                is specified by the Synchronization Mode parameter. This value is expressed in slots. The default value is 0. Valid
                values are 0 to 19, inclusive.

            measurement_length (int):
                This parameter specifies the number of slots to be measured. This value is expressed in slots. The default value is 20.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            synchronization_mode = (
                synchronization_mode.value
                if type(synchronization_mode) is enums.SlotPhaseSynchronizationMode
                else synchronization_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.slotphase_configure_synchronization_mode_and_interval(
                updated_selector_string,
                synchronization_mode,
                measurement_offset,
                measurement_length,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
