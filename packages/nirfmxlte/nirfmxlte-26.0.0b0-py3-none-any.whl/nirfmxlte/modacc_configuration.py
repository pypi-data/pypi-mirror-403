"""Provides methods to configure the ModAcc measurement."""

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


class ModAccConfiguration(object):
    """Provides methods to configure the ModAcc measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the ModAcc measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the ModAcc measurement.

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
                Specifies whether to enable the ModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the ModAcc measurement.

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
                attributes.AttributeID.MODACC_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_multicarrier_filter_enabled(self, selector_string):
        r"""Gets whether to use a filter to suppress the interference from out of band emissions into the carriers being
        measured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                           |
        +==============+=======================================================================================================+
        | False (0)    | The measurement does not use the multicarrier filter.                                                 |
        +--------------+-------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement filters out interference from out of band emissions into the carriers being measured. |
        +--------------+-------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccMulticarrierFilterEnabled):
                Specifies whether to use a filter to suppress the interference from out of band emissions into the carriers being
                measured.

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
                attributes.AttributeID.MODACC_MULTICARRIER_FILTER_ENABLED.value,
            )
            attr_val = enums.ModAccMulticarrierFilterEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_multicarrier_filter_enabled(self, selector_string, value):
        r"""Sets whether to use a filter to suppress the interference from out of band emissions into the carriers being
        measured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                           |
        +==============+=======================================================================================================+
        | False (0)    | The measurement does not use the multicarrier filter.                                                 |
        +--------------+-------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement filters out interference from out of band emissions into the carriers being measured. |
        +--------------+-------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccMulticarrierFilterEnabled, int):
                Specifies whether to use a filter to suppress the interference from out of band emissions into the carriers being
                measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccMulticarrierFilterEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_MULTICARRIER_FILTER_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_multicarrier_time_synchronization_mode(self, selector_string):
        r"""Gets the time synchronization mode used in uplink in the case of carrier aggregation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Common**.

        +-----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)    | Description                                                                                                              |
        +=================+==========================================================================================================================+
        | Common (0)      | Specifies that a common time synchronization value is used for synchronization of all the component carriers and time    |
        |                 | synchronization value is obtained from the synchronization of the first active component carrier of the first subblock.  |
        +-----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Per Carrier (1) | Specifies that time synchronization is performed on each component carrier.                                              |
        +-----------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccMulticarrierTimeSynchronizationMode):
                Specifies the time synchronization mode used in uplink in the case of carrier aggregation.

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
                attributes.AttributeID.MODACC_MULTICARRIER_TIME_SYNCHRONIZATION_MODE.value,
            )
            attr_val = enums.ModAccMulticarrierTimeSynchronizationMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_multicarrier_time_synchronization_mode(self, selector_string, value):
        r"""Sets the time synchronization mode used in uplink in the case of carrier aggregation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Common**.

        +-----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)    | Description                                                                                                              |
        +=================+==========================================================================================================================+
        | Common (0)      | Specifies that a common time synchronization value is used for synchronization of all the component carriers and time    |
        |                 | synchronization value is obtained from the synchronization of the first active component carrier of the first subblock.  |
        +-----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Per Carrier (1) | Specifies that time synchronization is performed on each component carrier.                                              |
        +-----------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccMulticarrierTimeSynchronizationMode, int):
                Specifies the time synchronization mode used in uplink in the case of carrier aggregation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccMulticarrierTimeSynchronizationMode
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_MULTICARRIER_TIME_SYNCHRONIZATION_MODE.value,
                value,
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

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about
        synchronization mode.

        The default value is **Slot**.

        .. note::
           When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, the measurement
           supports only **Frame** synchronization mode.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Frame (0)    | The frame boundary is detected, and the measurement is performed over the ModAcc Meas Length attribute, starting at the  |
        |              | ModAcc Meas Offset attribute from the frame boundary. When you set the Trigger Type attribute to Digital Edge, the       |
        |              | measurement expects a trigger at the frame boundary.                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Slot (1)     | The slot boundary is detected, and the measurement is performed over the ModAcc Meas Length attribute starting at the    |
        |              | ModAcc Meas Offset attribute from the slot boundary. When you set the Trigger Type attribute to Digital Edge, the        |
        |              | measurement expects a trigger at any slot boundary.                                                                      |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Marker (2)   | The measurement expects a marker (trigger) at the frame boundary from the user. The measurement takes advantage of       |
        |              | triggered acquisitions to reduce processing resulting in faster measurement time. Measurement is performed over the      |
        |              | ModAcc Meas Length attribute starting at ModAcc Meas Offset attribute from the frame boundary.                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccSynchronizationMode):
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
                updated_selector_string, attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE.value
            )
            attr_val = enums.ModAccSynchronizationMode(attr_val)
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

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about
        synchronization mode.

        The default value is **Slot**.

        .. note::
           When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, the measurement
           supports only **Frame** synchronization mode.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Frame (0)    | The frame boundary is detected, and the measurement is performed over the ModAcc Meas Length attribute, starting at the  |
        |              | ModAcc Meas Offset attribute from the frame boundary. When you set the Trigger Type attribute to Digital Edge, the       |
        |              | measurement expects a trigger at the frame boundary.                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Slot (1)     | The slot boundary is detected, and the measurement is performed over the ModAcc Meas Length attribute starting at the    |
        |              | ModAcc Meas Offset attribute from the slot boundary. When you set the Trigger Type attribute to Digital Edge, the        |
        |              | measurement expects a trigger at any slot boundary.                                                                      |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Marker (2)   | The measurement expects a marker (trigger) at the frame boundary from the user. The measurement takes advantage of       |
        |              | triggered acquisitions to reduce processing resulting in faster measurement time. Measurement is performed over the      |
        |              | ModAcc Meas Length attribute starting at ModAcc Meas Offset attribute from the frame boundary.                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccSynchronizationMode, int):
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
            value = value.value if type(value) is enums.ModAccSynchronizationMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_offset(self, selector_string):
        r"""Gets the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
        by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. This value is expressed in
        slots.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. For uplink, the upper limit is 19. For downlink, the upper limit is
        (2*:py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_NUMBER_OF_SUBFRAMES` - 1).

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
                by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. This value is expressed in
                slots.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_offset(self, selector_string, value):
        r"""Sets the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
        by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. This value is expressed in
        slots.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. For uplink, the upper limit is 19. For downlink, the upper limit is
        (2*:py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_NUMBER_OF_SUBFRAMES` - 1).

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
                by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. This value is expressed in
                slots.

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
                attributes.AttributeID.MODACC_MEASUREMENT_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_length(self, selector_string):
        r"""Gets the number of slots to be measured. This value is expressed in slots. For NB-IoT a measurement length of 20
        slots is recommended.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of slots to be measured. This value is expressed in slots. For NB-IoT a measurement length of 20
                slots is recommended.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_length(self, selector_string, value):
        r"""Sets the number of slots to be measured. This value is expressed in slots. For NB-IoT a measurement length of 20
        slots is recommended.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of slots to be measured. This value is expressed in slots. For NB-IoT a measurement length of 20
                slots is recommended.

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
                attributes.AttributeID.MODACC_MEASUREMENT_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_frequency_error_estimation(self, selector_string):
        r"""Gets the operation mode of frequency error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Normal (1)   | Estimate and correct frequency error of range +/- half subcarrier spacing.                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Wide (2)     | Estimate and correct frequency error of range +/- half resource block when Auto RB Detection Enabled is True, or range   |
        |              | +/- number of guard subcarrier when Auto RB Detection Enabled is False.                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccFrequencyErrorEstimation):
                Specifies the operation mode of frequency error estimation.

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
                attributes.AttributeID.MODACC_FREQUENCY_ERROR_ESTIMATION.value,
            )
            attr_val = enums.ModAccFrequencyErrorEstimation(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_frequency_error_estimation(self, selector_string, value):
        r"""Sets the operation mode of frequency error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Normal (1)   | Estimate and correct frequency error of range +/- half subcarrier spacing.                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Wide (2)     | Estimate and correct frequency error of range +/- half resource block when Auto RB Detection Enabled is True, or range   |
        |              | +/- number of guard subcarrier when Auto RB Detection Enabled is False.                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccFrequencyErrorEstimation, int):
                Specifies the operation mode of frequency error estimation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccFrequencyErrorEstimation else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_FREQUENCY_ERROR_ESTIMATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_origin_offset_estimation_enabled(self, selector_string):
        r"""Gets whether to estimate IQ origin offset.

        .. note::
           IQ origin offset estimation is supported only when you set the
           :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Uplink** or **Sidelink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | False (0)    | IQ origin offset estimation and correction is disabled. |
        +--------------+---------------------------------------------------------+
        | True (1)     | IQ origin offset estimation and correction is enabled.  |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQOriginOffsetEstimationEnabled):
                Specifies whether to estimate IQ origin offset.

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
                attributes.AttributeID.MODACC_IQ_ORIGIN_OFFSET_ESTIMATION_ENABLED.value,
            )
            attr_val = enums.ModAccIQOriginOffsetEstimationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_origin_offset_estimation_enabled(self, selector_string, value):
        r"""Sets whether to estimate IQ origin offset.

        .. note::
           IQ origin offset estimation is supported only when you set the
           :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Uplink** or **Sidelink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | False (0)    | IQ origin offset estimation and correction is disabled. |
        +--------------+---------------------------------------------------------+
        | True (1)     | IQ origin offset estimation and correction is enabled.  |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQOriginOffsetEstimationEnabled, int):
                Specifies whether to estimate IQ origin offset.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccIQOriginOffsetEstimationEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_ORIGIN_OFFSET_ESTIMATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_mismatch_estimation_enabled(self, selector_string):
        r"""Gets whether to estimate IQ mismatch such as gain imbalance, quadrature skew, and timing skew.

        .. note::
           Timing skew value is estimated only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
           attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------+
        | Name (Value) | Description                         |
        +==============+=====================================+
        | False (0)    | IQ mismatch estimation is disabled. |
        +--------------+-------------------------------------+
        | True (1)     | IQ mismatch estimation is enabled.  |
        +--------------+-------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQMismatchEstimationsEnabled):
                Specifies whether to estimate IQ mismatch such as gain imbalance, quadrature skew, and timing skew.

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
                attributes.AttributeID.MODACC_IQ_MISMATCH_ESTIMATION_ENABLED.value,
            )
            attr_val = enums.ModAccIQMismatchEstimationsEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_mismatch_estimation_enabled(self, selector_string, value):
        r"""Sets whether to estimate IQ mismatch such as gain imbalance, quadrature skew, and timing skew.

        .. note::
           Timing skew value is estimated only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
           attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------+
        | Name (Value) | Description                         |
        +==============+=====================================+
        | False (0)    | IQ mismatch estimation is disabled. |
        +--------------+-------------------------------------+
        | True (1)     | IQ mismatch estimation is enabled.  |
        +--------------+-------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQMismatchEstimationsEnabled, int):
                Specifies whether to estimate IQ mismatch such as gain imbalance, quadrature skew, and timing skew.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccIQMismatchEstimationsEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_MISMATCH_ESTIMATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_gain_imbalance_correction_enabled(self, selector_string):
        r"""Gets whether to enable IQ gain imbalance correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------+
        | Name (Value) | Description                               |
        +==============+===========================================+
        | False (0)    | IQ gain imbalance correction is disabled. |
        +--------------+-------------------------------------------+
        | True (1)     | IQ gain imbalance correction is enabled.  |
        +--------------+-------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQGainImbalanceCorrectionEnabled):
                Specifies whether to enable IQ gain imbalance correction.

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
                attributes.AttributeID.MODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED.value,
            )
            attr_val = enums.ModAccIQGainImbalanceCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_gain_imbalance_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable IQ gain imbalance correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------+
        | Name (Value) | Description                               |
        +==============+===========================================+
        | False (0)    | IQ gain imbalance correction is disabled. |
        +--------------+-------------------------------------------+
        | True (1)     | IQ gain imbalance correction is enabled.  |
        +--------------+-------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQGainImbalanceCorrectionEnabled, int):
                Specifies whether to enable IQ gain imbalance correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccIQGainImbalanceCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_quadrature_error_correction_enabled(self, selector_string):
        r"""Gets whether to enable IQ quadrature error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | False (0)    | IQ quadrature error correction is disabled. |
        +--------------+---------------------------------------------+
        | True (1)     | IQ quadrature error correction is enabled.  |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQQuadratureErrorCorrectionEnabled):
                Specifies whether to enable IQ quadrature error correction.

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
                attributes.AttributeID.MODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED.value,
            )
            attr_val = enums.ModAccIQQuadratureErrorCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_quadrature_error_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable IQ quadrature error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | False (0)    | IQ quadrature error correction is disabled. |
        +--------------+---------------------------------------------+
        | True (1)     | IQ quadrature error correction is enabled.  |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQQuadratureErrorCorrectionEnabled, int):
                Specifies whether to enable IQ quadrature error correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccIQQuadratureErrorCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_timing_skew_correction_enabled(self, selector_string):
        r"""Gets whether to enable IQ timing skew correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------+
        | Name (Value) | Description                            |
        +==============+========================================+
        | False (0)    | IQ timing skew correction is disabled. |
        +--------------+----------------------------------------+
        | True (1)     | IQ timing skew correction is enabled.  |
        +--------------+----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQTimingSkewCorrectionEnabled):
                Specifies whether to enable IQ timing skew correction.

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
                attributes.AttributeID.MODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED.value,
            )
            attr_val = enums.ModAccIQTimingSkewCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_timing_skew_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable IQ timing skew correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------+
        | Name (Value) | Description                            |
        +==============+========================================+
        | False (0)    | IQ timing skew correction is disabled. |
        +--------------+----------------------------------------+
        | True (1)     | IQ timing skew correction is enabled.  |
        +--------------+----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQTimingSkewCorrectionEnabled, int):
                Specifies whether to enable IQ timing skew correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccIQTimingSkewCorrectionEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED.value,
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

            attr_val (enums.ModAccSpectrumInverted):
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
                updated_selector_string, attributes.AttributeID.MODACC_SPECTRUM_INVERTED.value
            )
            attr_val = enums.ModAccSpectrumInverted(attr_val)
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

            value (enums.ModAccSpectrumInverted, int):
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
            value = value.value if type(value) is enums.ModAccSpectrumInverted else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SPECTRUM_INVERTED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_estimation_type(self, selector_string):
        r"""Gets the method used for the channel estimation for the ModAcc measurement. The measurement ignores this
        attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference+Data**.

        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)       | Description                                                                                                              |
        +====================+==========================================================================================================================+
        | Reference (0)      | Only the demodulation reference signal (DMRS) symbol is used to calculate the channel coefficients.                      |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference+Data (1) | Both the DMRS symbol and the data symbol are used to calculate the channel coefficients, as specified by the 3GPP        |
        |                    | 36.521 specification, Annexe E.                                                                                          |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccChannelEstimationType):
                Specifies the method used for the channel estimation for the ModAcc measurement. The measurement ignores this
                attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_CHANNEL_ESTIMATION_TYPE.value
            )
            attr_val = enums.ModAccChannelEstimationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_estimation_type(self, selector_string, value):
        r"""Sets the method used for the channel estimation for the ModAcc measurement. The measurement ignores this
        attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference+Data**.

        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)       | Description                                                                                                              |
        +====================+==========================================================================================================================+
        | Reference (0)      | Only the demodulation reference signal (DMRS) symbol is used to calculate the channel coefficients.                      |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference+Data (1) | Both the DMRS symbol and the data symbol are used to calculate the channel coefficients, as specified by the 3GPP        |
        |                    | 36.521 specification, Annexe E.                                                                                          |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccChannelEstimationType, int):
                Specifies the method used for the channel estimation for the ModAcc measurement. The measurement ignores this
                attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccChannelEstimationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_CHANNEL_ESTIMATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_evm_unit(self, selector_string):
        r"""Gets the units of the EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Percentage**.

        +----------------+--------------------------------------+
        | Name (Value)   | Description                          |
        +================+======================================+
        | Percentage (0) | The EVM is reported as a percentage. |
        +----------------+--------------------------------------+
        | dB (1)         | The EVM is reported in dB.           |
        +----------------+--------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccEvmUnit):
                Specifies the units of the EVM results.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_EVM_UNIT.value
            )
            attr_val = enums.ModAccEvmUnit(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_evm_unit(self, selector_string, value):
        r"""Sets the units of the EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Percentage**.

        +----------------+--------------------------------------+
        | Name (Value)   | Description                          |
        +================+======================================+
        | Percentage (0) | The EVM is reported as a percentage. |
        +----------------+--------------------------------------+
        | dB (1)         | The EVM is reported in dB.           |
        +----------------+--------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccEvmUnit, int):
                Specifies the units of the EVM results.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccEvmUnit else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_EVM_UNIT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_window_type(self, selector_string):
        r"""Gets the FFT window type used for the EVM calculation for the ModAcc measurement.

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about FFT window
        type.

        The default value is **Custom**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | 3GPP (0)     | The maximum EVM between the start window position and the end window position is returned according to the 3GPP          |
        |              | specification. The FFT window positions are specified by the                                                             |
        |              | attribute. Refer to the Annexe E.3.2 of 3GPP TS 36.521 specification for more information on the FFT window.             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (1)   | Only one FFT window position is used for the EVM calculation. FFT window position is specified by ModAcc FFT Window      |
        |              | Offset attribute.                                                                                                        |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccFftWindowType):
                Specifies the FFT window type used for the EVM calculation for the ModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_FFT_WINDOW_TYPE.value
            )
            attr_val = enums.ModAccFftWindowType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_window_type(self, selector_string, value):
        r"""Sets the FFT window type used for the EVM calculation for the ModAcc measurement.

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about FFT window
        type.

        The default value is **Custom**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | 3GPP (0)     | The maximum EVM between the start window position and the end window position is returned according to the 3GPP          |
        |              | specification. The FFT window positions are specified by the                                                             |
        |              | attribute. Refer to the Annexe E.3.2 of 3GPP TS 36.521 specification for more information on the FFT window.             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (1)   | Only one FFT window position is used for the EVM calculation. FFT window position is specified by ModAcc FFT Window      |
        |              | Offset attribute.                                                                                                        |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccFftWindowType, int):
                Specifies the FFT window type used for the EVM calculation for the ModAcc measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccFftWindowType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_FFT_WINDOW_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_window_offset(self, selector_string):
        r"""Gets the position of the FFT window used to calculate the EVM. The offset is expressed as a percentage of the
        cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end of cyclic prefix. If you set
        this attribute to 100, the EVM window starts at the beginning of cyclic prefix.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 50. Valid values are 0 to 100, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the position of the FFT window used to calculate the EVM. The offset is expressed as a percentage of the
                cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end of cyclic prefix. If you set
                this attribute to 100, the EVM window starts at the beginning of cyclic prefix.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_FFT_WINDOW_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_window_offset(self, selector_string, value):
        r"""Sets the position of the FFT window used to calculate the EVM. The offset is expressed as a percentage of the
        cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end of cyclic prefix. If you set
        this attribute to 100, the EVM window starts at the beginning of cyclic prefix.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 50. Valid values are 0 to 100, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the position of the FFT window used to calculate the EVM. The offset is expressed as a percentage of the
                cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end of cyclic prefix. If you set
                this attribute to 100, the EVM window starts at the beginning of cyclic prefix.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.MODACC_FFT_WINDOW_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_window_length(self, selector_string):
        r"""Gets the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
        attribute is used when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
        **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
        Delta_C+W/2. Refer to the Annexe E.3.2 of *3GPP 36.521* specification for more information.

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about FFT Window
        Length.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is as given in the 3GPP specification. The default value is 91.7 %CP for 10M bandwidth. Valid
        values range from -1 to 100, inclusive.

        When this attribute is set to -1, RFmx populates the FFT Window Length based on carrier bandwidth
        automatically, as given in the Annexe E.5.1 of *3GPP 36.104* specification.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
                attribute is used when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
                **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
                Delta_C+W/2. Refer to the Annexe E.3.2 of *3GPP 36.521* specification for more information.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_FFT_WINDOW_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_window_length(self, selector_string, value):
        r"""Sets the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
        attribute is used when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
        **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
        Delta_C+W/2. Refer to the Annexe E.3.2 of *3GPP 36.521* specification for more information.

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about FFT Window
        Length.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is as given in the 3GPP specification. The default value is 91.7 %CP for 10M bandwidth. Valid
        values range from -1 to 100, inclusive.

        When this attribute is set to -1, RFmx populates the FFT Window Length based on carrier bandwidth
        automatically, as given in the Annexe E.5.1 of *3GPP 36.104* specification.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
                attribute is used when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
                **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
                Delta_C+W/2. Refer to the Annexe E.3.2 of *3GPP 36.521* specification for more information.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.MODACC_FFT_WINDOW_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_common_clock_source_enabled(self, selector_string):
        r"""Gets whether the same Reference Clock is used for the local oscillator and the digital-to-analog converter in the
        transmitter. When the same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

        The ModAcc measurement ignores this attribute, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

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

            attr_val (enums.ModAccCommonClockSourceEnabled):
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
                attributes.AttributeID.MODACC_COMMON_CLOCK_SOURCE_ENABLED.value,
            )
            attr_val = enums.ModAccCommonClockSourceEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_common_clock_source_enabled(self, selector_string, value):
        r"""Sets whether the same Reference Clock is used for the local oscillator and the digital-to-analog converter in the
        transmitter. When the same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.

        The ModAcc measurement ignores this attribute, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

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

            value (enums.ModAccCommonClockSourceEnabled, int):
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
            value = value.value if type(value) is enums.ModAccCommonClockSourceEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_COMMON_CLOCK_SOURCE_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_evm_with_exclusion_period_enabled(self, selector_string):
        r"""Gets whether to exclude some portion of the slots when calculating the EVM. This attribute is valid only when
        there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP TS 36.521-1* specification for
        more information about exclusion.

        The measurement ignores this attribute, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | EVM is calculated on complete slots.                                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | EVM is calculated on truncated slots. The power changes at the slot boundaries are detected by the measurement, and the  |
        |              | defined 3GPP specification period is excluded from the slots being measured.                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccEvmWithExclusionPeriodEnabled):
                Specifies whether to exclude some portion of the slots when calculating the EVM. This attribute is valid only when
                there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP TS 36.521-1* specification for
                more information about exclusion.

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
                attributes.AttributeID.MODACC_EVM_WITH_EXCLUSION_PERIOD_ENABLED.value,
            )
            attr_val = enums.ModAccEvmWithExclusionPeriodEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_evm_with_exclusion_period_enabled(self, selector_string, value):
        r"""Sets whether to exclude some portion of the slots when calculating the EVM. This attribute is valid only when
        there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP TS 36.521-1* specification for
        more information about exclusion.

        The measurement ignores this attribute, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | EVM is calculated on complete slots.                                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | EVM is calculated on truncated slots. The power changes at the slot boundaries are detected by the measurement, and the  |
        |              | defined 3GPP specification period is excluded from the slots being measured.                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccEvmWithExclusionPeriodEnabled, int):
                Specifies whether to exclude some portion of the slots when calculating the EVM. This attribute is valid only when
                there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP TS 36.521-1* specification for
                more information about exclusion.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccEvmWithExclusionPeriodEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_EVM_WITH_EXCLUSION_PERIOD_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_spectral_flatness_condition(self, selector_string):
        r"""Gets the frequency ranges at which to measure spectral flatness. The measurement ignores this attribute, when you
        set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+----------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                    |
        +==============+================================================================================================================+
        | Normal (0)   | Uses the frequency range defined in the section 6.5.2.4.5, and table 6.5.2.4.3-1 of 3GPP 36.521 specification. |
        +--------------+----------------------------------------------------------------------------------------------------------------+
        | Extreme (1)  | Uses the frequency range defined in the section 6.5.2.4.5, and table 6.5.2.4.3-2 of 3GPP 36.521 specification. |
        +--------------+----------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccSpectralFlatnessCondition):
                Specifies the frequency ranges at which to measure spectral flatness. The measurement ignores this attribute, when you
                set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

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
                attributes.AttributeID.MODACC_SPECTRAL_FLATNESS_CONDITION.value,
            )
            attr_val = enums.ModAccSpectralFlatnessCondition(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_spectral_flatness_condition(self, selector_string, value):
        r"""Sets the frequency ranges at which to measure spectral flatness. The measurement ignores this attribute, when you
        set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+----------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                    |
        +==============+================================================================================================================+
        | Normal (0)   | Uses the frequency range defined in the section 6.5.2.4.5, and table 6.5.2.4.3-1 of 3GPP 36.521 specification. |
        +--------------+----------------------------------------------------------------------------------------------------------------+
        | Extreme (1)  | Uses the frequency range defined in the section 6.5.2.4.5, and table 6.5.2.4.3-2 of 3GPP 36.521 specification. |
        +--------------+----------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccSpectralFlatnessCondition, int):
                Specifies the frequency ranges at which to measure spectral flatness. The measurement ignores this attribute, when you
                set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccSpectralFlatnessCondition else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SPECTRAL_FLATNESS_CONDITION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_in_band_emission_mask_type(self, selector_string):
        r"""Gets the in-band emissions mask type to be used for measuring in-band emission margin (dB) and subblock in-Band
        emission margin (dB) results.

        Refer to section 6.5.2.3.5 of the *3GPP 36.521-1* specification for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Release 8-10** for bandwidths other than 200 KHz and
        :py:attr:`~nirfmxlte.attributes.AttributeID.EMTC_ANALYSIS_ENABLED` is **False**. It is **Release 11 Onwards**,
        otherwise.

        +------------------------+--------------------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                            |
        +========================+========================================================================================================+
        | Release 8-10 (0)       | Specifies the mask type to be used for UE, supporting 3GPP Release 8 to 3GPP Release 10 specification. |
        +------------------------+--------------------------------------------------------------------------------------------------------+
        | Release 11 Onwards (1) | Specifies the mask type to be used for UE, supporting 3GPP Release 11 and higher specification.        |
        +------------------------+--------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccInBandEmissionMaskType):
                Specifies the in-band emissions mask type to be used for measuring in-band emission margin (dB) and subblock in-Band
                emission margin (dB) results.

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
                attributes.AttributeID.MODACC_IN_BAND_EMISSION_MASK_TYPE.value,
            )
            attr_val = enums.ModAccInBandEmissionMaskType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_in_band_emission_mask_type(self, selector_string, value):
        r"""Sets the in-band emissions mask type to be used for measuring in-band emission margin (dB) and subblock in-Band
        emission margin (dB) results.

        Refer to section 6.5.2.3.5 of the *3GPP 36.521-1* specification for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Release 8-10** for bandwidths other than 200 KHz and
        :py:attr:`~nirfmxlte.attributes.AttributeID.EMTC_ANALYSIS_ENABLED` is **False**. It is **Release 11 Onwards**,
        otherwise.

        +------------------------+--------------------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                            |
        +========================+========================================================================================================+
        | Release 8-10 (0)       | Specifies the mask type to be used for UE, supporting 3GPP Release 8 to 3GPP Release 10 specification. |
        +------------------------+--------------------------------------------------------------------------------------------------------+
        | Release 11 Onwards (1) | Specifies the mask type to be used for UE, supporting 3GPP Release 11 and higher specification.        |
        +------------------------+--------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccInBandEmissionMaskType, int):
                Specifies the in-band emissions mask type to be used for measuring in-band emission margin (dB) and subblock in-Band
                emission margin (dB) results.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccInBandEmissionMaskType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IN_BAND_EMISSION_MASK_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the ModAcc Averaging   |
        |              | Count attribute.                                                                                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccAveragingEnabled):
                Specifies whether to enable averaging for the ModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_ENABLED.value
            )
            attr_val = enums.ModAccAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the ModAcc Averaging   |
        |              | Count attribute.                                                                                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccAveragingEnabled, int):
                Specifies whether to enable averaging for the ModAcc measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_AVERAGING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

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
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.

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
                Specifies whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.

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
                attributes.AttributeID.MODACC_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
        range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
        number of threads used depends on the problem size, system resources, data availability, and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
                range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
                number of threads used depends on the problem size, system resources, data availability, and other considerations.

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
                attributes.AttributeID.MODACC_NUMBER_OF_ANALYSIS_THREADS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
        range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
        number of threads used depends on the problem size, system resources, data availability, and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
                range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
                number of threads used depends on the problem size, system resources, data availability, and other considerations.

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
                attributes.AttributeID.MODACC_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pre_fft_error_estimation_interval(self, selector_string):
        r"""Gets the interval used for Pre-FFT Error Estimation.

        Pre-FFT Error Estimation Interval set to **Slot** is valid only when the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Uplink**.
        Pre-FFT Error Estimation Interval set to **Subframe** is valid only when the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measurement Length**.

        +------------------------+----------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                  |
        +========================+==============================================================================================+
        | Slot (0)               | Frequency and Timing Error is estimated per slot in the pre-fft domain.                      |
        +------------------------+----------------------------------------------------------------------------------------------+
        | Subframe (1)           | Frequency and Timing Error is estimated per subframe in the pre-fft domain.                  |
        +------------------------+----------------------------------------------------------------------------------------------+
        | Measurement Length (2) | Frequency and Timing Error is estimated over the measurement interval in the pre-fft domain. |
        +------------------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccPreFftErrorEstimationInterval):
                Specifies the interval used for Pre-FFT Error Estimation.

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
                attributes.AttributeID.MODACC_PRE_FFT_ERROR_ESTIMATION_INTERVAL.value,
            )
            attr_val = enums.ModAccPreFftErrorEstimationInterval(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pre_fft_error_estimation_interval(self, selector_string, value):
        r"""Sets the interval used for Pre-FFT Error Estimation.

        Pre-FFT Error Estimation Interval set to **Slot** is valid only when the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Uplink**.
        Pre-FFT Error Estimation Interval set to **Subframe** is valid only when the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measurement Length**.

        +------------------------+----------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                  |
        +========================+==============================================================================================+
        | Slot (0)               | Frequency and Timing Error is estimated per slot in the pre-fft domain.                      |
        +------------------------+----------------------------------------------------------------------------------------------+
        | Subframe (1)           | Frequency and Timing Error is estimated per subframe in the pre-fft domain.                  |
        +------------------------+----------------------------------------------------------------------------------------------+
        | Measurement Length (2) | Frequency and Timing Error is estimated over the measurement interval in the pre-fft domain. |
        +------------------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccPreFftErrorEstimationInterval, int):
                Specifies the interval used for Pre-FFT Error Estimation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccPreFftErrorEstimationInterval else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_PRE_FFT_ERROR_ESTIMATION_INTERVAL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_symbol_clock_error_estimation_enabled(self, selector_string):
        r"""Gets whether to estimate symbol clock error.

        If symbol clock error is not present in the signal to be analyzed, symbol clock error estimation may be
        disabled to reduce measurement time or to avoid measurement inaccuracy due to error in symbol clock error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-----------------------------------------------------------+
        | Name (Value) | Description                                               |
        +==============+===========================================================+
        | False (0)    | Symbol Clock Error estimation and correction is disabled. |
        +--------------+-----------------------------------------------------------+
        | True (1)     | Symbol Clock Error estimation and correction is enabled.  |
        +--------------+-----------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccSymbolClockErrorEstimationEnabled):
                Specifies whether to estimate symbol clock error.

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
                attributes.AttributeID.MODACC_SYMBOL_CLOCK_ERROR_ESTIMATION_ENABLED.value,
            )
            attr_val = enums.ModAccSymbolClockErrorEstimationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_symbol_clock_error_estimation_enabled(self, selector_string, value):
        r"""Sets whether to estimate symbol clock error.

        If symbol clock error is not present in the signal to be analyzed, symbol clock error estimation may be
        disabled to reduce measurement time or to avoid measurement inaccuracy due to error in symbol clock error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-----------------------------------------------------------+
        | Name (Value) | Description                                               |
        +==============+===========================================================+
        | False (0)    | Symbol Clock Error estimation and correction is disabled. |
        +--------------+-----------------------------------------------------------+
        | True (1)     | Symbol Clock Error estimation and correction is enabled.  |
        +--------------+-----------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccSymbolClockErrorEstimationEnabled, int):
                Specifies whether to estimate symbol clock error.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccSymbolClockErrorEstimationEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SYMBOL_CLOCK_ERROR_ESTIMATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_timing_tracking_enabled(self, selector_string):
        r"""Gets whether timing tracking is enabled.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------------------+
        | Name (Value) | Description                                                      |
        +==============+==================================================================+
        | False (0)    | Disables the Timing Tracking.                                    |
        +--------------+------------------------------------------------------------------+
        | True (1)     | All the reference and data symbols are used for Timing Tracking. |
        +--------------+------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccTimingTrackingEnabled):
                Specifies whether timing tracking is enabled.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_TIMING_TRACKING_ENABLED.value
            )
            attr_val = enums.ModAccTimingTrackingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_timing_tracking_enabled(self, selector_string, value):
        r"""Sets whether timing tracking is enabled.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------------------+
        | Name (Value) | Description                                                      |
        +==============+==================================================================+
        | False (0)    | Disables the Timing Tracking.                                    |
        +--------------+------------------------------------------------------------------+
        | True (1)     | All the reference and data symbols are used for Timing Tracking. |
        +--------------+------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccTimingTrackingEnabled, int):
                Specifies whether timing tracking is enabled.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccTimingTrackingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_TIMING_TRACKING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_phase_tracking_enabled(self, selector_string):
        r"""Gets whether phase tracking is enabled.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------+
        | Name (Value) | Description                                                     |
        +==============+=================================================================+
        | False (0)    | Disables the Phase Tracking.                                    |
        +--------------+-----------------------------------------------------------------+
        | True (1)     | All the reference and data symbols are used for Phase Tracking. |
        +--------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccPhaseTrackingEnabled):
                Specifies whether phase tracking is enabled.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_PHASE_TRACKING_ENABLED.value
            )
            attr_val = enums.ModAccPhaseTrackingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_phase_tracking_enabled(self, selector_string, value):
        r"""Sets whether phase tracking is enabled.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------+
        | Name (Value) | Description                                                     |
        +==============+=================================================================+
        | False (0)    | Disables the Phase Tracking.                                    |
        +--------------+-----------------------------------------------------------------+
        | True (1)     | All the reference and data symbols are used for Phase Tracking. |
        +--------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccPhaseTrackingEnabled, int):
                Specifies whether phase tracking is enabled.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccPhaseTrackingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_PHASE_TRACKING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        r"""Configures averaging for the ModAcc measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.ModAccAveragingEnabled, int):
                This parameter specifies whether to enable averaging for the measurement. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The measurement is performed on a single acquisition.                                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the Averaging Count    |
                |              | parameter.                                                                                                               |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            averaging_count (int):
                This parameter specifies the number of acquisitions used for averaging when you set the **Averaging Enabled** parameter
                to **True**. The default value is 10.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            averaging_enabled = (
                averaging_enabled.value
                if type(averaging_enabled) is enums.ModAccAveragingEnabled
                else averaging_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_common_clock_source_enabled(self, selector_string, common_clock_source_enabled):
        r"""Configures the Reference Clock and specifies whether same Reference Clock is used for local oscillator and D/A
        converter.

        The modacc measurement ignores this method, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            common_clock_source_enabled (enums.ModAccCommonClockSourceEnabled, int):
                This parameter specifies whether the same Reference Clock is used for the local oscillator and the D/A converter. When
                the same Reference Clock is used, the carrier frequency offset is proportional to the Sample Clock error. The default
                value is **True**.

                +--------------+--------------------------------------------------------------------+
                | Name (Value) | Description                                                        |
                +==============+====================================================================+
                | False (0)    | The Sample Clock error is estimated independently.                 |
                +--------------+--------------------------------------------------------------------+
                | True (1)     | The Sample Clock error is estimated from carrier frequency offset. |
                +--------------+--------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            common_clock_source_enabled = (
                common_clock_source_enabled.value
                if type(common_clock_source_enabled) is enums.ModAccCommonClockSourceEnabled
                else common_clock_source_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_common_clock_source_enabled(
                updated_selector_string, common_clock_source_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_evm_unit(self, selector_string, evm_unit):
        r"""Configures the units of the EVM results.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            evm_unit (enums.ModAccEvmUnit, int):
                This parameter specifies the units of the EVM results. The default value is **Percentage**.

                +----------------+------------------------------------+
                | Name (Value)   | Description                        |
                +================+====================================+
                | Percentage (0) | The EVM is reported in percentage. |
                +----------------+------------------------------------+
                | dB (1)         | The EVM is reported in dB.         |
                +----------------+------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            evm_unit = evm_unit.value if type(evm_unit) is enums.ModAccEvmUnit else evm_unit
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_evm_unit(
                updated_selector_string, evm_unit
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_fft_window_offset(self, selector_string, fft_window_offset):
        r"""Configures the position of the FFT window that is used to calculate the EVM.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            fft_window_offset (float):
                This parameter specifies the position of the FFT window that is used to calculate the EVM. The offset is expressed as a
                percentage of the cyclic prefix length. If you set this parameter to 0, the EVM window starts from the end of cyclic
                prefix. If you set this parameter to 100, the EVM window starts from the beginning of cyclic prefix. The default value
                is 50. Valid values are 0 to 100, inclusive.

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
            error_code = self._interpreter.modacc_configure_fft_window_offset(
                updated_selector_string, fft_window_offset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_fft_window_position(
        self, selector_string, fft_window_type, fft_window_offset, fft_window_length
    ):
        r"""Configures the FFT window position used for an EVM calculation.

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about FFT window
        position.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            fft_window_type (enums.ModAccFftWindowType, int):
                This parameter specifies the FFT window type used for an EVM calculation. The default value is **Custom**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | 3GPP (0)     | The maximum EVM between the start window position and the end window position is returned according to the 3GPP          |
                |              | specification. The window positions are specified by the ModAcc FFT Window Length parameter. For more information about  |
                |              | the FFT window specification, refer to the 3GPP TS 36.521 specification, Annexe E.3.2.                                   |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Custom (1)   | Only one FFT window position is used for the EVM calculation. The FFT window position is specified by the ModAcc FFT     |
                |              | Window Offset parameter.                                                                                                 |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            fft_window_offset (float):
                This parameter specifies the position of the FFT window used to calculate the EVM. The offset is expressed as a
                percentage of the cyclic prefix length. If you set this parameter to 0, the EVM window starts from the end of cyclic
                prefix. If you set this parameter to 100, the EVM window starts from the beginning of cyclic prefix.

                The default value is 50. Valid values are 0 to 100, inclusive.

            fft_window_length (float):
                This parameter specifies the FFT window length. This value is expressed in a percentage of the cyclic prefix length.
                This parameter is used when you set the **ModAcc FFT Window Type** parameter to **3GPP**, where you need to calculate
                the EVM using two different FFT window positions, Delta_C-W/2, and Delta_C+W/2.

                The default value is -1. Valid values are -1 to 100, inclusive. When this attribute is set to -1, the RFmx
                populates the FFT Window Length based on carrier bandwidth automatically, as given in the*3GPP 36.104* specification,
                Annexe E.5.1.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            fft_window_type = (
                fft_window_type.value
                if type(fft_window_type) is enums.ModAccFftWindowType
                else fft_window_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_fft_window_position(
                updated_selector_string, fft_window_type, fft_window_offset, fft_window_length
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_in_band_emission_mask_type(self, selector_string, in_band_emission_mask_type):
        r"""Configures the **In-Band Emission Mask Type** parameter to be used.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            in_band_emission_mask_type (enums.ModAccInBandEmissionMaskType, int):
                This parameter specifies the in-band emissions mask type to be used for measuring in-band emission margin (dB) and
                subblock in-Band emission margin (dB) results.

                Refer to section 6.5.2.3.5 of the *3GPP 36.521-1* specification for more information.

                The default value is **Release 8-10** for bandwidths other than 200 KHz and
                :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` is **False**. It is **Release 11 Onwards**, otherwise.

                +------------------------+--------------------------------------------------------------------------------------------------------+
                | Name (Value)           | Description                                                                                            |
                +========================+========================================================================================================+
                | Release 8-10 (0)       | Specifies the mask type to be used for UE, supporting 3GPP Release 8 to 3GPP Release 10 specification. |
                +------------------------+--------------------------------------------------------------------------------------------------------+
                | Release 11 Onwards (1) | Specifies the mask type to be used for UE, supporting 3GPP Release 11 and higher specification.        |
                +------------------------+--------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            in_band_emission_mask_type = (
                in_band_emission_mask_type.value
                if type(in_band_emission_mask_type) is enums.ModAccInBandEmissionMaskType
                else in_band_emission_mask_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_in_band_emission_mask_type(
                updated_selector_string, in_band_emission_mask_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_synchronization_mode_and_interval(
        self, selector_string, synchronization_mode, measurement_offset, measurement_length
    ):
        r"""Configures the **Synchronization Mode**, the **Measurement Offset**, and the **Measurement Length** parameters of the
        ModAcc measurement.

        Refer to the `LTE Modulation Accuracy
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about ModAcc
        measurements.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            synchronization_mode (enums.ModAccSynchronizationMode, int):
                This parameter specifies whether the measurement is performed from the frame or the slot boundary. The default value is
                **Slot**.

                When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, the
                measurement supports only **Frame** synchronization mode.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | Frame  (0)   | The frame boundary is detected, and the measurement is performed over the Measurement Length parameter, starting at the  |
                |              | Measurement Offset parameter from the frame boundary. When you set the Trigger Type attribute to Digital Edge, the       |
                |              | measurement expects a trigger at the frame boundary.                                                                     |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Slot (1)     | The slot boundary is detected, and the measurement is performed over the Measurement Length parameter starting at the    |
                |              | Measurement Offset parameter from the slot boundary. When you set the Trigger Type attribute to Digital Edge, the        |
                |              | measurement expects a trigger at any slot boundary.                                                                      |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Marker (2)   | The measurement expects a marker (trigger) at the frame boundary from the user. The measurement takes advantage of       |
                |              | triggered acquisitions to reduce processing resulting in faster measurement time. Measurement is performed over the      |
                |              | Measurement Length parameter                                                                                             |
                |              | starting at the Measurement Offset parameter from the frame boundary.                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            measurement_offset (int):
                This parameter specifies the measurement offset, in slots, to skip from the synchronization boundary. The
                synchronization boundary is specified by the **Synchronization Mode** parameter. The default value is 0. Valid values
                are 0 to 19, inclusive.

            measurement_length (int):
                This parameter specifies the number of slots to be measured. The default value is 1.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            synchronization_mode = (
                synchronization_mode.value
                if type(synchronization_mode) is enums.ModAccSynchronizationMode
                else synchronization_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_synchronization_mode_and_interval(
                updated_selector_string,
                synchronization_mode,
                measurement_offset,
                measurement_length,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
