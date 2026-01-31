""""""

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


class ComponentCarrier(object):
    """"""

    def __init__(self, signal_obj):
        """"""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_spacing_type(self, selector_string):
        r"""Gets the spacing between two adjacent component carriers within a subblock. Refer to the `Channel Spacing
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/channel-spacing.html>`_ and `Carrier Frequency Offset Definition and
        Reference Frequency
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_ topics for
        more information about component carrier spacing.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is **Nominal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Nominal (0)  | Calculates the frequency spacing between component carriers, as defined in section 5.4.1A in the 3GPP TS 36.521          |
        |              | specification,                                                                                                           |
        |              | and sets the CC Freq attribute.                                                                                          |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Minimum (1)  | Calculates the frequency spacing between component carriers, as defined in section 5.4.1A of the 3GPP TS 36.521          |
        |              | specification, and sets the CC Freq attribute.                                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | User (2)     | The CC frequency that you configure in the CC Freq attribute is used.                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ComponentCarrierSpacingType):
                Specifies the spacing between two adjacent component carriers within a subblock. Refer to the `Channel Spacing
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/channel-spacing.html>`_ and `Carrier Frequency Offset Definition and
                Reference Frequency
                <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_ topics for
                more information about component carrier spacing.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE.value
            )
            attr_val = enums.ComponentCarrierSpacingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_spacing_type(self, selector_string, value):
        r"""Sets the spacing between two adjacent component carriers within a subblock. Refer to the `Channel Spacing
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/channel-spacing.html>`_ and `Carrier Frequency Offset Definition and
        Reference Frequency
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_ topics for
        more information about component carrier spacing.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is **Nominal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Nominal (0)  | Calculates the frequency spacing between component carriers, as defined in section 5.4.1A in the 3GPP TS 36.521          |
        |              | specification,                                                                                                           |
        |              | and sets the CC Freq attribute.                                                                                          |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Minimum (1)  | Calculates the frequency spacing between component carriers, as defined in section 5.4.1A of the 3GPP TS 36.521          |
        |              | specification, and sets the CC Freq attribute.                                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | User (2)     | The CC frequency that you configure in the CC Freq attribute is used.                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ComponentCarrierSpacingType, int):
                Specifies the spacing between two adjacent component carriers within a subblock. Refer to the `Channel Spacing
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/channel-spacing.html>`_ and `Carrier Frequency Offset Definition and
                Reference Frequency
                <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_ topics for
                more information about component carrier spacing.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ComponentCarrierSpacingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_component_carrier_at_center_frequency(self, selector_string):
        r"""Gets the index of the component carrier having its center at the user-configured center frequency. RFmx LTE uses
        this attribute along with :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
        calculate the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`.

        Refer to the `Carrier Frequency Offset Definition and Reference Frequency
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_  topic for
        more information about component carrier frequency.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        Valid values are -1, 0, 1 ... *n* - 1, inclusive, where *n* is the number of component carriers in the
        subblock.

        The default value is -1. If the value is -1, the component carrier frequency values are calculated such that
        the center of aggregated carriers (subblock) lies at the Center Frequency. This attribute is ignored if you set the CC
        Spacing Type attribute to **User**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the index of the component carrier having its center at the user-configured center frequency. RFmx LTE uses
                this attribute along with :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
                calculate the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`.

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
                attributes.AttributeID.COMPONENT_CARRIER_AT_CENTER_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_component_carrier_at_center_frequency(self, selector_string, value):
        r"""Sets the index of the component carrier having its center at the user-configured center frequency. RFmx LTE uses
        this attribute along with :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
        calculate the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`.

        Refer to the `Carrier Frequency Offset Definition and Reference Frequency
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_  topic for
        more information about component carrier frequency.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        Valid values are -1, 0, 1 ... *n* - 1, inclusive, where *n* is the number of component carriers in the
        subblock.

        The default value is -1. If the value is -1, the component carrier frequency values are calculated such that
        the center of aggregated carriers (subblock) lies at the Center Frequency. This attribute is ignored if you set the CC
        Spacing Type attribute to **User**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the index of the component carrier having its center at the user-configured center frequency. RFmx LTE uses
                this attribute along with :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
                calculate the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`.

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
                attributes.AttributeID.COMPONENT_CARRIER_AT_CENTER_FREQUENCY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_component_carriers(self, selector_string):
        r"""Gets the number of component carriers configured within a subblock.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of component carriers configured within a subblock.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_COMPONENT_CARRIERS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_component_carriers(self, selector_string, value):
        r"""Sets the number of component carriers configured within a subblock.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of component carriers configured within a subblock.

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
                attributes.AttributeID.NUMBER_OF_COMPONENT_CARRIERS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bandwidth(self, selector_string):
        r"""Gets the channel bandwidth of the signal being measured. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **10 MHz**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the channel bandwidth of the signal being measured. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bandwidth(self, selector_string, value):
        r"""Sets the channel bandwidth of the signal being measured. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **10 MHz**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the channel bandwidth of the signal being measured. This value is expressed in Hz.

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
                attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_frequency(self, selector_string):
        r"""Gets the offset of the component carrier from the subblock center frequency that you configure in the
        :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz. This attribute
        is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
        **User**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset of the component carrier from the subblock center frequency that you configure in the
                :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz. This attribute
                is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
                **User**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_frequency(self, selector_string, value):
        r"""Sets the offset of the component carrier from the subblock center frequency that you configure in the
        :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz. This attribute
        is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
        **User**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset of the component carrier from the subblock center frequency that you configure in the
                :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz. This attribute
                is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
                **User**.

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
                attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_cell_id(self, selector_string):
        r"""Gets a physical layer cell identity.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 503, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies a physical layer cell identity.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CELL_ID.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_cell_id(self, selector_string, value):
        r"""Sets a physical layer cell identity.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 503, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies a physical layer cell identity.

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
                updated_selector_string, attributes.AttributeID.CELL_ID.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_cyclic_prefix_mode(self, selector_string):
        r"""Gets the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | Normal (0)   | The CP duration is 4.67 microseconds, and the number of symbols in a slot is 7.  |
        +--------------+----------------------------------------------------------------------------------+
        | Extended (1) | The CP duration is 16.67 microseconds, and the number of symbols in a slot is 6. |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.CyclicPrefixMode):
                Specifies the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CYCLIC_PREFIX_MODE.value
            )
            attr_val = enums.CyclicPrefixMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_cyclic_prefix_mode(self, selector_string, value):
        r"""Sets the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | Normal (0)   | The CP duration is 4.67 microseconds, and the number of symbols in a slot is 7.  |
        +--------------+----------------------------------------------------------------------------------+
        | Extended (1) | The CP duration is 16.67 microseconds, and the number of symbols in a slot is 6. |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.CyclicPrefixMode, int):
                Specifies the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.CyclicPrefixMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.CYCLIC_PREFIX_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_auto_cell_id_detection_enabled(self, selector_string):
        r"""Gets whether to enable autodetection of the cell ID. If the signal being measured does not contain primary and
        secondary sync signal (PSS/SSS), autodetection of cell ID is not possible. Detected cell ID can be fetched using
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_DOWNLINK_DETECTED_CELL_ID` attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------+
        | Name (Value) | Description                                     |
        +==============+=================================================+
        | False (0)    | The measurement uses the cell ID you configure. |
        +--------------+-------------------------------------------------+
        | True (1)     | The measurement auto detects the cell ID.       |
        +--------------+-------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkAutoCellIDDetectionEnabled):
                Specifies whether to enable autodetection of the cell ID. If the signal being measured does not contain primary and
                secondary sync signal (PSS/SSS), autodetection of cell ID is not possible. Detected cell ID can be fetched using
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_DOWNLINK_DETECTED_CELL_ID` attribute.

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
                attributes.AttributeID.DOWNLINK_AUTO_CELL_ID_DETECTION_ENABLED.value,
            )
            attr_val = enums.DownlinkAutoCellIDDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_auto_cell_id_detection_enabled(self, selector_string, value):
        r"""Sets whether to enable autodetection of the cell ID. If the signal being measured does not contain primary and
        secondary sync signal (PSS/SSS), autodetection of cell ID is not possible. Detected cell ID can be fetched using
        :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_DOWNLINK_DETECTED_CELL_ID` attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------+
        | Name (Value) | Description                                     |
        +==============+=================================================+
        | False (0)    | The measurement uses the cell ID you configure. |
        +--------------+-------------------------------------------------+
        | True (1)     | The measurement auto detects the cell ID.       |
        +--------------+-------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkAutoCellIDDetectionEnabled, int):
                Specifies whether to enable autodetection of the cell ID. If the signal being measured does not contain primary and
                secondary sync signal (PSS/SSS), autodetection of cell ID is not possible. Detected cell ID can be fetched using
                :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_DOWNLINK_DETECTED_CELL_ID` attribute.

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
                value.value if type(value) is enums.DownlinkAutoCellIDDetectionEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_AUTO_CELL_ID_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_channel_configuration_mode(self, selector_string):
        r"""Gets the channel configuration mode.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Test Model**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | User Defined (1) | You have to manually set all the signals and channels.                                                                   |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Test Model (2)   | You need to select a test model using the DL Test Model attribute, which will configure all the signals and channels     |
        |                  | automatically according to the 3GPP specification.                                                                       |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkChannelConfigurationMode):
                Specifies the channel configuration mode.

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
                attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE.value,
            )
            attr_val = enums.DownlinkChannelConfigurationMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_channel_configuration_mode(self, selector_string, value):
        r"""Sets the channel configuration mode.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Test Model**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | User Defined (1) | You have to manually set all the signals and channels.                                                                   |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Test Model (2)   | You need to select a test model using the DL Test Model attribute, which will configure all the signals and channels     |
        |                  | automatically according to the 3GPP specification.                                                                       |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkChannelConfigurationMode, int):
                Specifies the channel configuration mode.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DownlinkChannelConfigurationMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_pdsch_channel_detection_enabled(self, selector_string):
        r"""Gets whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_RESOURCE_BLOCK_ALLOCATION`
        attribute, the corresponding :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_CW0_MODULATION_TYPE` attribute, and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_POWER` attribute are auto-detected by the measurement or
        user-specified. This attribute is not valid, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
        measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement uses the values of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation   |
        |              | Type, and the PDSCH Power attribute that you specify.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the values of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation   |
        |              | Type, and the PDSCH Power attribute that are auto-detected.                                                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoPdschChannelDetectionEnabled):
                Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_RESOURCE_BLOCK_ALLOCATION`
                attribute, the corresponding :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_CW0_MODULATION_TYPE` attribute, and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_POWER` attribute are auto-detected by the measurement or
                user-specified. This attribute is not valid, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
                measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
                attribute to **Uplink**.

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
                attributes.AttributeID.AUTO_PDSCH_CHANNEL_DETECTION_ENABLED.value,
            )
            attr_val = enums.AutoPdschChannelDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_pdsch_channel_detection_enabled(self, selector_string, value):
        r"""Sets whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_RESOURCE_BLOCK_ALLOCATION`
        attribute, the corresponding :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_CW0_MODULATION_TYPE` attribute, and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_POWER` attribute are auto-detected by the measurement or
        user-specified. This attribute is not valid, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
        measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement uses the values of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation   |
        |              | Type, and the PDSCH Power attribute that you specify.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the values of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation   |
        |              | Type, and the PDSCH Power attribute that are auto-detected.                                                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoPdschChannelDetectionEnabled, int):
                Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_RESOURCE_BLOCK_ALLOCATION`
                attribute, the corresponding :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_CW0_MODULATION_TYPE` attribute, and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_POWER` attribute are auto-detected by the measurement or
                user-specified. This attribute is not valid, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
                measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
                attribute to **Uplink**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AutoPdschChannelDetectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.AUTO_PDSCH_CHANNEL_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_control_channel_power_detection_enabled(self, selector_string):
        r"""Gets whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PSS_POWER`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.SSS_POWER`, :py:attr:`~nirfmxlte.attributes.AttributeID.PBCH_POWER`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PDCCH_POWER`, and :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_POWER`
        attributes are auto-detected by the measurement or user-specified. Currently, auto-detection of
        :py:attr:`~nirfmxlte.attributes.AttributeID.PHICH_POWER` attribute is not supported. This attribute is not valid, when
        you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test
        Model**. The measurement ignores this attribute, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, PHICH Power, and PCFICH Power attributes that you        |
        |              | specify are used for the measurement.                                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, and PCFICH Power attributes are auto-detected and used   |
        |              | for the measurement.                                                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoControlChannelPowerDetectionEnabled):
                Specifies whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PSS_POWER`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.SSS_POWER`, :py:attr:`~nirfmxlte.attributes.AttributeID.PBCH_POWER`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PDCCH_POWER`, and :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_POWER`
                attributes are auto-detected by the measurement or user-specified. Currently, auto-detection of
                :py:attr:`~nirfmxlte.attributes.AttributeID.PHICH_POWER` attribute is not supported. This attribute is not valid, when
                you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test
                Model**. The measurement ignores this attribute, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
                attribute to **Uplink**.

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
                attributes.AttributeID.AUTO_CONTROL_CHANNEL_POWER_DETECTION_ENABLED.value,
            )
            attr_val = enums.AutoControlChannelPowerDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_control_channel_power_detection_enabled(self, selector_string, value):
        r"""Sets whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PSS_POWER`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.SSS_POWER`, :py:attr:`~nirfmxlte.attributes.AttributeID.PBCH_POWER`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PDCCH_POWER`, and :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_POWER`
        attributes are auto-detected by the measurement or user-specified. Currently, auto-detection of
        :py:attr:`~nirfmxlte.attributes.AttributeID.PHICH_POWER` attribute is not supported. This attribute is not valid, when
        you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test
        Model**. The measurement ignores this attribute, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, PHICH Power, and PCFICH Power attributes that you        |
        |              | specify are used for the measurement.                                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, and PCFICH Power attributes are auto-detected and used   |
        |              | for the measurement.                                                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoControlChannelPowerDetectionEnabled, int):
                Specifies whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PSS_POWER`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.SSS_POWER`, :py:attr:`~nirfmxlte.attributes.AttributeID.PBCH_POWER`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PDCCH_POWER`, and :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_POWER`
                attributes are auto-detected by the measurement or user-specified. Currently, auto-detection of
                :py:attr:`~nirfmxlte.attributes.AttributeID.PHICH_POWER` attribute is not supported. This attribute is not valid, when
                you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test
                Model**. The measurement ignores this attribute, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
                attribute to **Uplink**.

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
                if type(value) is enums.AutoControlChannelPowerDetectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.AUTO_CONTROL_CHANNEL_POWER_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_pcfich_cfi_detection_enabled(self, selector_string):
        r"""Gets whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_CFI` attribute is auto-detected by
        the measurement or user-specified. This attribute is not valid, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
        measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The value of PCFICH CFI attribute used for the measurement is specified by you.                                          |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The value of PCFICH CFI attribute used for the measurement is auto-detected. This value is obtained by decoding the      |
        |              | PCFICH channel.                                                                                                          |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoPcfichCfiDetectionEnabled):
                Specifies whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_CFI` attribute is auto-detected by
                the measurement or user-specified. This attribute is not valid, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
                measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
                attribute to **Uplink**.

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
                attributes.AttributeID.AUTO_PCFICH_CFI_DETECTION_ENABLED.value,
            )
            attr_val = enums.AutoPcfichCfiDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_pcfich_cfi_detection_enabled(self, selector_string, value):
        r"""Sets whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_CFI` attribute is auto-detected by
        the measurement or user-specified. This attribute is not valid, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
        measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The value of PCFICH CFI attribute used for the measurement is specified by you.                                          |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The value of PCFICH CFI attribute used for the measurement is auto-detected. This value is obtained by decoding the      |
        |              | PCFICH channel.                                                                                                          |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoPcfichCfiDetectionEnabled, int):
                Specifies whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_CFI` attribute is auto-detected by
                the measurement or user-specified. This attribute is not valid, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
                measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
                attribute to **Uplink**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AutoPcfichCfiDetectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.AUTO_PCFICH_CFI_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_user_defined_cell_specific_ratio(self, selector_string):
        r"""Gets the ratio Rho\ :sub:`b`\/Rho\ :sub:`a`\ for the cell-specific ratio of one, two,
        or four cell-specific antenna ports as described in Table 5.2-1 in section 5.2 of the *3GPP TS 36.213*
        specification. This attribute determines the power of the channel resource element (RE) in the symbols that do not
        contain the reference symbols.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **P_B=0**.

        +--------------+--------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                          |
        +==============+======================================================================================+
        | P_B=0 (0)    | Specifies a ratio of 1 for one antenna port and 5/4 for two or four antenna ports.   |
        +--------------+--------------------------------------------------------------------------------------+
        | P_B=1 (1)    | Specifies a ratio of 4/5 for one antenna port and 1 for two or four antenna ports.   |
        +--------------+--------------------------------------------------------------------------------------+
        | P_B=2 (2)    | Specifies a ratio of 3/5 for one antenna port and 3/4 for two or four antenna ports. |
        +--------------+--------------------------------------------------------------------------------------+
        | P_B=3 (3)    | Specifies a ratio of 2/5 for one antenna port and 1/2 for two or four antenna ports. |
        +--------------+--------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkUserDefinedRatio):
                Specifies the ratio Rho\ :sub:`b`\/Rho\ :sub:`a`\ for the cell-specific ratio of one, two,
                or four cell-specific antenna ports as described in Table 5.2-1 in section 5.2 of the *3GPP TS 36.213*
                specification. This attribute determines the power of the channel resource element (RE) in the symbols that do not
                contain the reference symbols.

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
                attributes.AttributeID.DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO.value,
            )
            attr_val = enums.DownlinkUserDefinedRatio(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_user_defined_cell_specific_ratio(self, selector_string, value):
        r"""Sets the ratio Rho\ :sub:`b`\/Rho\ :sub:`a`\ for the cell-specific ratio of one, two,
        or four cell-specific antenna ports as described in Table 5.2-1 in section 5.2 of the *3GPP TS 36.213*
        specification. This attribute determines the power of the channel resource element (RE) in the symbols that do not
        contain the reference symbols.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **P_B=0**.

        +--------------+--------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                          |
        +==============+======================================================================================+
        | P_B=0 (0)    | Specifies a ratio of 1 for one antenna port and 5/4 for two or four antenna ports.   |
        +--------------+--------------------------------------------------------------------------------------+
        | P_B=1 (1)    | Specifies a ratio of 4/5 for one antenna port and 1 for two or four antenna ports.   |
        +--------------+--------------------------------------------------------------------------------------+
        | P_B=2 (2)    | Specifies a ratio of 3/5 for one antenna port and 3/4 for two or four antenna ports. |
        +--------------+--------------------------------------------------------------------------------------+
        | P_B=3 (3)    | Specifies a ratio of 2/5 for one antenna port and 1/2 for two or four antenna ports. |
        +--------------+--------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkUserDefinedRatio, int):
                Specifies the ratio Rho\ :sub:`b`\/Rho\ :sub:`a`\ for the cell-specific ratio of one, two,
                or four cell-specific antenna ports as described in Table 5.2-1 in section 5.2 of the *3GPP TS 36.213*
                specification. This attribute determines the power of the channel resource element (RE) in the symbols that do not
                contain the reference symbols.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DownlinkUserDefinedRatio else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pss_power(self, selector_string):
        r"""Gets the power of primary synchronization signal (PSS) relative to the power of cell-specific reference signal.
        This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of primary synchronization signal (PSS) relative to the power of cell-specific reference signal.
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
                updated_selector_string, attributes.AttributeID.PSS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pss_power(self, selector_string, value):
        r"""Sets the power of primary synchronization signal (PSS) relative to the power of cell-specific reference signal.
        This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of primary synchronization signal (PSS) relative to the power of cell-specific reference signal.
                This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PSS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sss_power(self, selector_string):
        r"""Gets the power of secondary synchronization signal (SSS) relative to the power of cell-specific reference signal.
        This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of secondary synchronization signal (SSS) relative to the power of cell-specific reference signal.
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
                updated_selector_string, attributes.AttributeID.SSS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sss_power(self, selector_string, value):
        r"""Sets the power of secondary synchronization signal (SSS) relative to the power of cell-specific reference signal.
        This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of secondary synchronization signal (SSS) relative to the power of cell-specific reference signal.
                This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.SSS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pbch_power(self, selector_string):
        r"""Gets the power of physical broadcast channel (PBCH) relative to the power of cell-specific reference signal. This
        value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of physical broadcast channel (PBCH) relative to the power of cell-specific reference signal. This
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
                updated_selector_string, attributes.AttributeID.PBCH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pbch_power(self, selector_string, value):
        r"""Sets the power of physical broadcast channel (PBCH) relative to the power of cell-specific reference signal. This
        value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of physical broadcast channel (PBCH) relative to the power of cell-specific reference signal. This
                value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PBCH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdcch_power(self, selector_string):
        r"""Gets the power of physical downlink control channel (PDCCH) relative to the power of cell-specific reference
        signal. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of physical downlink control channel (PDCCH) relative to the power of cell-specific reference
                signal. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PDCCH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdcch_power(self, selector_string, value):
        r"""Sets the power of physical downlink control channel (PDCCH) relative to the power of cell-specific reference
        signal. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of physical downlink control channel (PDCCH) relative to the power of cell-specific reference
                signal. This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PDCCH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_number_of_subframes(self, selector_string):
        r"""Gets the number of unique subframes transmitted by the DUT. If you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**, this
        attribute will be set to 10 for FDD and 20 for TDD by default.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 10. Valid values are 10 and 20.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of unique subframes transmitted by the DUT. If you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**, this
                attribute will be set to 10 for FDD and 20 for TDD by default.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DOWNLINK_NUMBER_OF_SUBFRAMES.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_number_of_subframes(self, selector_string, value):
        r"""Sets the number of unique subframes transmitted by the DUT. If you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**, this
        attribute will be set to 10 for FDD and 20 for TDD by default.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 10. Valid values are 10 and 20.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of unique subframes transmitted by the DUT. If you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**, this
                attribute will be set to 10 for FDD and 20 for TDD by default.

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
                attributes.AttributeID.DOWNLINK_NUMBER_OF_SUBFRAMES.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pcfich_cfi(self, selector_string):
        r"""Gets the control format indicator (CFI) carried by physical control format indicator channel (PCFICH). CFI is used
        to compute the number of OFDM symbols which will determine the size of physical downlink control channel (PDCCH) within
        a subframe.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the control format indicator (CFI) carried by physical control format indicator channel (PCFICH). CFI is used
                to compute the number of OFDM symbols which will determine the size of physical downlink control channel (PDCCH) within
                a subframe.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PCFICH_CFI.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pcfich_cfi(self, selector_string, value):
        r"""Sets the control format indicator (CFI) carried by physical control format indicator channel (PCFICH). CFI is used
        to compute the number of OFDM symbols which will determine the size of physical downlink control channel (PDCCH) within
        a subframe.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the control format indicator (CFI) carried by physical control format indicator channel (PCFICH). CFI is used
                to compute the number of OFDM symbols which will determine the size of physical downlink control channel (PDCCH) within
                a subframe.

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
                updated_selector_string, attributes.AttributeID.PCFICH_CFI.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pcfich_power(self, selector_string):
        r"""Gets the power of physical control format indicator channel (PCFICH) relative to the power of cell-specific
        reference signal. This value is expressed in dB.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of physical control format indicator channel (PCFICH) relative to the power of cell-specific
                reference signal. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PCFICH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pcfich_power(self, selector_string, value):
        r"""Sets the power of physical control format indicator channel (PCFICH) relative to the power of cell-specific
        reference signal. This value is expressed in dB.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of physical control format indicator channel (PCFICH) relative to the power of cell-specific
                reference signal. This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PCFICH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_phich_resource(self, selector_string):
        r"""Gets the physical channel hybridARQ indicator channel (PHICH) resource value. This value is expressed in Ng. This
        attribute is used to calculate number of PHICH resource groups. Refer to section 6.9 of the *3GPP 36.211* specification
        for more information about PHICH.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is **1/6**.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | 1/6 (0)      | Specifies the PHICH resource value is 1/6. |
        +--------------+--------------------------------------------+
        | 1/2 (1)      | Specifies the PHICH resource value is 1/2. |
        +--------------+--------------------------------------------+
        | 1 (2)        | Specifies the PHICH resource value is 1.   |
        +--------------+--------------------------------------------+
        | 2 (3)        | Specifies the PHICH resource value is 2.   |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkUserDefinedPhichResource):
                Specifies the physical channel hybridARQ indicator channel (PHICH) resource value. This value is expressed in Ng. This
                attribute is used to calculate number of PHICH resource groups. Refer to section 6.9 of the *3GPP 36.211* specification
                for more information about PHICH.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PHICH_RESOURCE.value
            )
            attr_val = enums.DownlinkUserDefinedPhichResource(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_phich_resource(self, selector_string, value):
        r"""Sets the physical channel hybridARQ indicator channel (PHICH) resource value. This value is expressed in Ng. This
        attribute is used to calculate number of PHICH resource groups. Refer to section 6.9 of the *3GPP 36.211* specification
        for more information about PHICH.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is **1/6**.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | 1/6 (0)      | Specifies the PHICH resource value is 1/6. |
        +--------------+--------------------------------------------+
        | 1/2 (1)      | Specifies the PHICH resource value is 1/2. |
        +--------------+--------------------------------------------+
        | 1 (2)        | Specifies the PHICH resource value is 1.   |
        +--------------+--------------------------------------------+
        | 2 (3)        | Specifies the PHICH resource value is 2.   |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkUserDefinedPhichResource, int):
                Specifies the physical channel hybridARQ indicator channel (PHICH) resource value. This value is expressed in Ng. This
                attribute is used to calculate number of PHICH resource groups. Refer to section 6.9 of the *3GPP 36.211* specification
                for more information about PHICH.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DownlinkUserDefinedPhichResource else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PHICH_RESOURCE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_phich_duration(self, selector_string):
        r"""Gets the physical hybrid-ARQ indicator channel (PHICH) duration.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is **Normal**.

        +--------------+------------------------------------------------------------+
        | Name (Value) | Description                                                |
        +==============+============================================================+
        | Normal (0)   | Orthogonal sequences of length 4 is used to extract PHICH. |
        +--------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkUserDefinedPhichDuration):
                Specifies the physical hybrid-ARQ indicator channel (PHICH) duration.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PHICH_DURATION.value
            )
            attr_val = enums.DownlinkUserDefinedPhichDuration(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_phich_duration(self, selector_string, value):
        r"""Sets the physical hybrid-ARQ indicator channel (PHICH) duration.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is **Normal**.

        +--------------+------------------------------------------------------------+
        | Name (Value) | Description                                                |
        +==============+============================================================+
        | Normal (0)   | Orthogonal sequences of length 4 is used to extract PHICH. |
        +--------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkUserDefinedPhichDuration, int):
                Specifies the physical hybrid-ARQ indicator channel (PHICH) duration.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DownlinkUserDefinedPhichDuration else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PHICH_DURATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_phich_power(self, selector_string):
        r"""Gets the power of all BPSK symbols in a physical hybrid-ARQ indicator channel (PHICH) sequence. This value is
        expressed in dB.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of all BPSK symbols in a physical hybrid-ARQ indicator channel (PHICH) sequence. This value is
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
                updated_selector_string, attributes.AttributeID.PHICH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_phich_power(self, selector_string, value):
        r"""Sets the power of all BPSK symbols in a physical hybrid-ARQ indicator channel (PHICH) sequence. This value is
        expressed in dB.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of all BPSK symbols in a physical hybrid-ARQ indicator channel (PHICH) sequence. This value is
                expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PHICH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_pdsch_channels(self, selector_string):
        r"""Gets the number of physical downlink shared channel (PDSCH) allocations in a subframe.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 1. Valid values are 0 to 100, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of physical downlink shared channel (PDSCH) allocations in a subframe.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_PDSCH_CHANNELS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_pdsch_channels(self, selector_string, value):
        r"""Sets the number of physical downlink shared channel (PDSCH) allocations in a subframe.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 1. Valid values are 0 to 100, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of physical downlink shared channel (PDSCH) allocations in a subframe.

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
                attributes.AttributeID.NUMBER_OF_PDSCH_CHANNELS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_cw_0_modulation_type(self, selector_string):
        r"""Gets the modulation type of codeword0 PDSCH allocation.

        Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>" as the selector string to configure or read this attribute.

        The default value is **QPSK**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | QPSK (0)     | Specifies a QPSK modulation scheme.     |
        +--------------+-----------------------------------------+
        | 16 QAM (1)   | Specifies a 16-QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 64 QAM (2)   | Specifies a 64-QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 256 QAM (3)  | Specifies a 256-QAM modulation scheme.  |
        +--------------+-----------------------------------------+
        | 1024 QAM (4) | Specifies a 1024-QAM modulation scheme. |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.UserDefinedPdschCW0ModulationType):
                Specifies the modulation type of codeword0 PDSCH allocation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_CW0_MODULATION_TYPE.value
            )
            attr_val = enums.UserDefinedPdschCW0ModulationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_cw_0_modulation_type(self, selector_string, value):
        r"""Sets the modulation type of codeword0 PDSCH allocation.

        Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>" as the selector string to configure or read this attribute.

        The default value is **QPSK**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | QPSK (0)     | Specifies a QPSK modulation scheme.     |
        +--------------+-----------------------------------------+
        | 16 QAM (1)   | Specifies a 16-QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 64 QAM (2)   | Specifies a 64-QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 256 QAM (3)  | Specifies a 256-QAM modulation scheme.  |
        +--------------+-----------------------------------------+
        | 1024 QAM (4) | Specifies a 1024-QAM modulation scheme. |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.UserDefinedPdschCW0ModulationType, int):
                Specifies the modulation type of codeword0 PDSCH allocation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.UserDefinedPdschCW0ModulationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PDSCH_CW0_MODULATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_resource_block_allocation(self, selector_string):
        r"""Gets the resource blocks of the physical downlink shared channel (PDSCH) allocation.
        
        The following string formats are supported for this property:
        
        1) *RB*
        \ :sub:`StartValue1`\-*RB*
        \ :sub:`StopValue1`\,*RB*
        \ :sub:`StartValue2`\-*RB*
        \ :sub:`StopValue2`\
        
        2) *RB*
        \ :sub:`1`\,*RB*
        \ :sub:`2`\
        
        3) *RB*
        \ :sub:`StartValue1`\-*RB*
        \ :sub:`StopValue1`\, *RB*
        \ :sub:`1`\,*RB*
        \ :sub:`StartValue2`\-*RB*
        \ :sub:`StopValue2`\,*RB*
        \ :sub:`2`\
        
        For example: If the RB allocation is 0-5,7,8,10-15, the RB allocation string specifies contiguous resource
        blocks from 0 to 5, resource block 7, resource block 8, and contiguous resource blocks from 10 to 15.
        
        Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>"
        as the selector string to configure or read this attribute.
        
        The default value is 0-49.

        Args:
            selector_string (string): 
                Pass an empty string.
        
        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the resource blocks of the physical downlink shared channel (PDSCH) allocation.

            error_code (int): 
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string,
                attributes.AttributeID.PDSCH_RESOURCE_BLOCK_ALLOCATION.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_resource_block_allocation(self, selector_string, value):
        r"""Sets the resource blocks of the physical downlink shared channel (PDSCH) allocation.
        
        The following string formats are supported for this property:
        
        1) *RB*
        \ :sub:`StartValue1`\-*RB*
        \ :sub:`StopValue1`\,*RB*
        \ :sub:`StartValue2`\-*RB*
        \ :sub:`StopValue2`\
        
        2) *RB*
        \ :sub:`1`\,*RB*
        \ :sub:`2`\
        
        3) *RB*
        \ :sub:`StartValue1`\-*RB*
        \ :sub:`StopValue1`\, *RB*
        \ :sub:`1`\,*RB*
        \ :sub:`StartValue2`\-*RB*
        \ :sub:`StopValue2`\,*RB*
        \ :sub:`2`\
        
        For example: If the RB allocation is 0-5,7,8,10-15, the RB allocation string specifies contiguous resource
        blocks from 0 to 5, resource block 7, resource block 8, and contiguous resource blocks from 10 to 15.
        
        Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>"
        as the selector string to configure or read this attribute.
        
        The default value is 0-49.

        Args:
            selector_string (string): 
                Pass an empty string.

            value (string): 
                Specifies the resource blocks of the physical downlink shared channel (PDSCH) allocation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string,
                attributes.AttributeID.PDSCH_RESOURCE_BLOCK_ALLOCATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_power(self, selector_string):
        r"""Gets the physical downlink shared channel (PDSCH) power level (Ra) relative to the power of the cell-specific
        reference signal. This value is expressed in dB. Measurement uses the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO` attribute to calculate the Rb.
        Refer to section 3.3 of the *3GPP 36.521* specification for more information about Ra.

        Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the physical downlink shared channel (PDSCH) power level (Ra) relative to the power of the cell-specific
                reference signal. This value is expressed in dB. Measurement uses the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO` attribute to calculate the Rb.
                Refer to section 3.3 of the *3GPP 36.521* specification for more information about Ra.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PDSCH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_power(self, selector_string, value):
        r"""Sets the physical downlink shared channel (PDSCH) power level (Ra) relative to the power of the cell-specific
        reference signal. This value is expressed in dB. Measurement uses the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO` attribute to calculate the Rb.
        Refer to section 3.3 of the *3GPP 36.521* specification for more information about Ra.

        Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the physical downlink shared channel (PDSCH) power level (Ra) relative to the power of the cell-specific
                reference signal. This value is expressed in dB. Measurement uses the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO` attribute to calculate the Rb.
                Refer to section 3.3 of the *3GPP 36.521* specification for more information about Ra.

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
                updated_selector_string, attributes.AttributeID.PDSCH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_test_model(self, selector_string):
        r"""Gets the E-UTRA test model type when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
        section 6.1.1 of the *3GPP 36.141* specification for more information regarding test model configurations.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **TM1.1**.

        +--------------+--------------------------------------+
        | Name (Value) | Description                          |
        +==============+======================================+
        | TM1.1 (0)    | Specifies an E-UTRA Test Model 1.1.  |
        +--------------+--------------------------------------+
        | TM1.2 (1)    | Specifies an E-UTRA Test Model 1.2.  |
        +--------------+--------------------------------------+
        | TM2 (2)      | Specifies an E-UTRA Test Model 2.    |
        +--------------+--------------------------------------+
        | TM2a (3)     | Specifies an E-UTRA Test Model 2a.   |
        +--------------+--------------------------------------+
        | TM2b (8)     | Specifies an E-UTRA Test Model 2b.   |
        +--------------+--------------------------------------+
        | TM3.1 (4)    | Specifies an E-UTRA Test Model 3.1.  |
        +--------------+--------------------------------------+
        | TM3.1a (7)   | Specifies an E-UTRA Test Model 3.1a. |
        +--------------+--------------------------------------+
        | TM3.1b (9)   | Specifies an E-UTRA Test Model 3.1b. |
        +--------------+--------------------------------------+
        | TM3.2 (5)    | Specifies an E-UTRA Test Model 3.2.  |
        +--------------+--------------------------------------+
        | TM3.3 (6)    | Specifies an E-UTRA Test Model 3.3.  |
        +--------------+--------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkTestModel):
                Specifies the E-UTRA test model type when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
                section 6.1.1 of the *3GPP 36.141* specification for more information regarding test model configurations.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DOWNLINK_TEST_MODEL.value
            )
            attr_val = enums.DownlinkTestModel(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_test_model(self, selector_string, value):
        r"""Sets the E-UTRA test model type when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
        section 6.1.1 of the *3GPP 36.141* specification for more information regarding test model configurations.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **TM1.1**.

        +--------------+--------------------------------------+
        | Name (Value) | Description                          |
        +==============+======================================+
        | TM1.1 (0)    | Specifies an E-UTRA Test Model 1.1.  |
        +--------------+--------------------------------------+
        | TM1.2 (1)    | Specifies an E-UTRA Test Model 1.2.  |
        +--------------+--------------------------------------+
        | TM2 (2)      | Specifies an E-UTRA Test Model 2.    |
        +--------------+--------------------------------------+
        | TM2a (3)     | Specifies an E-UTRA Test Model 2a.   |
        +--------------+--------------------------------------+
        | TM2b (8)     | Specifies an E-UTRA Test Model 2b.   |
        +--------------+--------------------------------------+
        | TM3.1 (4)    | Specifies an E-UTRA Test Model 3.1.  |
        +--------------+--------------------------------------+
        | TM3.1a (7)   | Specifies an E-UTRA Test Model 3.1a. |
        +--------------+--------------------------------------+
        | TM3.1b (9)   | Specifies an E-UTRA Test Model 3.1b. |
        +--------------+--------------------------------------+
        | TM3.2 (5)    | Specifies an E-UTRA Test Model 3.2.  |
        +--------------+--------------------------------------+
        | TM3.3 (6)    | Specifies an E-UTRA Test Model 3.3.  |
        +--------------+--------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkTestModel, int):
                Specifies the E-UTRA test model type when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
                section 6.1.1 of the *3GPP 36.141* specification for more information regarding test model configurations.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DownlinkTestModel else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.DOWNLINK_TEST_MODEL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_resource_block_detection_enabled(self, selector_string):
        r"""Gets whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_MODULATION_TYPE`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET`, and
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attributes are auto-detected by the
        measurement or if you specify the values of these attributes.

        The measurement ignores this attribute, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The values of the PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes that you specify     |
        |              | are used for the measurement.                                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The values of the PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes are detected         |
        |              | automatically and used for the measurement.                                                                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoResourceBlockDetectionEnabled):
                Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_MODULATION_TYPE`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET`, and
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attributes are auto-detected by the
                measurement or if you specify the values of these attributes.

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
                attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED.value,
            )
            attr_val = enums.AutoResourceBlockDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_resource_block_detection_enabled(self, selector_string, value):
        r"""Sets whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_MODULATION_TYPE`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET`, and
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attributes are auto-detected by the
        measurement or if you specify the values of these attributes.

        The measurement ignores this attribute, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The values of the PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes that you specify     |
        |              | are used for the measurement.                                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The values of the PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes are detected         |
        |              | automatically and used for the measurement.                                                                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoResourceBlockDetectionEnabled, int):
                Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_MODULATION_TYPE`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET`, and
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attributes are auto-detected by the
                measurement or if you specify the values of these attributes.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AutoResourceBlockDetectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_uplink_group_hopping_enabled(self, selector_string):
        r"""Gets whether the sequence group number hopping for demodulation reference signal (DMRS) is enabled, as defined in
        section 5.5.1.3 of the *3GPP TS 36.211* specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+---------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                         |
        +==============+=====================================================================================================================+
        | False (0)    | The measurement uses zero as the sequence group number for all the slots.                                           |
        +--------------+---------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Calculates the sequence group number for each slot, as defined in the section 5.5.1.3 of 3GPP 36.211 Specification. |
        +--------------+---------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.UplinkGroupHoppingEnabled):
                Specifies whether the sequence group number hopping for demodulation reference signal (DMRS) is enabled, as defined in
                section 5.5.1.3 of the *3GPP TS 36.211* specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.UPLINK_GROUP_HOPPING_ENABLED.value
            )
            attr_val = enums.UplinkGroupHoppingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_uplink_group_hopping_enabled(self, selector_string, value):
        r"""Sets whether the sequence group number hopping for demodulation reference signal (DMRS) is enabled, as defined in
        section 5.5.1.3 of the *3GPP TS 36.211* specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+---------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                         |
        +==============+=====================================================================================================================+
        | False (0)    | The measurement uses zero as the sequence group number for all the slots.                                           |
        +--------------+---------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Calculates the sequence group number for each slot, as defined in the section 5.5.1.3 of 3GPP 36.211 Specification. |
        +--------------+---------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.UplinkGroupHoppingEnabled, int):
                Specifies whether the sequence group number hopping for demodulation reference signal (DMRS) is enabled, as defined in
                section 5.5.1.3 of the *3GPP TS 36.211* specification.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.UplinkGroupHoppingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.UPLINK_GROUP_HOPPING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_uplink_sequence_hopping_enabled(self, selector_string):
        r"""Gets whether the base sequence number hopping for the demodulation reference signal (DMRS) is enabled, as defined
        in section 5.5.1.3 of the *3GPP TS 36.211* specification.  This attribute is only valid only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attribute to a value greater than 5.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                        |
        +==============+====================================================================================================================+
        | False (0)    | The measurement uses zero as the base sequence number for all the slots.                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Calculates the base sequence number for each slot, as defined in the section 5.5.1.4 of 3GPP 36.211 specification. |
        +--------------+--------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.UplinkSequenceHoppingEnabled):
                Specifies whether the base sequence number hopping for the demodulation reference signal (DMRS) is enabled, as defined
                in section 5.5.1.3 of the *3GPP TS 36.211* specification.  This attribute is only valid only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attribute to a value greater than 5.

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
                attributes.AttributeID.UPLINK_SEQUENCE_HOPPING_ENABLED.value,
            )
            attr_val = enums.UplinkSequenceHoppingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_uplink_sequence_hopping_enabled(self, selector_string, value):
        r"""Sets whether the base sequence number hopping for the demodulation reference signal (DMRS) is enabled, as defined
        in section 5.5.1.3 of the *3GPP TS 36.211* specification.  This attribute is only valid only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attribute to a value greater than 5.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                        |
        +==============+====================================================================================================================+
        | False (0)    | The measurement uses zero as the base sequence number for all the slots.                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Calculates the base sequence number for each slot, as defined in the section 5.5.1.4 of 3GPP 36.211 specification. |
        +--------------+--------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.UplinkSequenceHoppingEnabled, int):
                Specifies whether the base sequence number hopping for the demodulation reference signal (DMRS) is enabled, as defined
                in section 5.5.1.3 of the *3GPP TS 36.211* specification.  This attribute is only valid only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attribute to a value greater than 5.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.UplinkSequenceHoppingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.UPLINK_SEQUENCE_HOPPING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_dmrs_occ_enabled(self, selector_string):
        r"""Gets whether orthogonal cover codes (OCCs) need to be used on the demodulation reference signal (DMRS) signal. The
        measurement internally sets this attribute to **TRUE** for multi antenna cases.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement ignores the Cyclic Shift Field and uses the PUSCH n_DMRS_2 field for DMRS calculations.                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the table 5.5.2.1.1-1 of 3GPP 36.211 specification to decide the value of PUSCH n_DMRS_2 and [w(0)  |
        |              | w(1)] for DMRS signal based on the values you set for the Cyclic Shift Field and Tx Antenna to Analyze.                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DmrsOccEnabled):
                Specifies whether orthogonal cover codes (OCCs) need to be used on the demodulation reference signal (DMRS) signal. The
                measurement internally sets this attribute to **TRUE** for multi antenna cases.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DMRS_OCC_ENABLED.value
            )
            attr_val = enums.DmrsOccEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_dmrs_occ_enabled(self, selector_string, value):
        r"""Sets whether orthogonal cover codes (OCCs) need to be used on the demodulation reference signal (DMRS) signal. The
        measurement internally sets this attribute to **TRUE** for multi antenna cases.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement ignores the Cyclic Shift Field and uses the PUSCH n_DMRS_2 field for DMRS calculations.                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the table 5.5.2.1.1-1 of 3GPP 36.211 specification to decide the value of PUSCH n_DMRS_2 and [w(0)  |
        |              | w(1)] for DMRS signal based on the values you set for the Cyclic Shift Field and Tx Antenna to Analyze.                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DmrsOccEnabled, int):
                Specifies whether orthogonal cover codes (OCCs) need to be used on the demodulation reference signal (DMRS) signal. The
                measurement internally sets this attribute to **TRUE** for multi antenna cases.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DmrsOccEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.DMRS_OCC_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_n_dmrs_1(self, selector_string):
        r"""Gets the n_DMRS_1 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
        in a frame.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0. The valid values for this attribute are defined in table 5.5.2.1.1-2 of the *3GPP TS
        36.211* specification.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the n_DMRS_1 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
                in a frame.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_N_DMRS_1.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_n_dmrs_1(self, selector_string, value):
        r"""Sets the n_DMRS_1 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
        in a frame.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0. The valid values for this attribute are defined in table 5.5.2.1.1-2 of the *3GPP TS
        36.211* specification.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the n_DMRS_1 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
                in a frame.

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
                updated_selector_string, attributes.AttributeID.PUSCH_N_DMRS_1.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_delta_sequence_shift(self, selector_string):
        r"""Gets the physical uplink shared channel (PUSCH) delta sequence shift, which is used to calculate cyclic shift of
        the demodulation reference signal (DMRS). Refer to section 5.5.2.1.1 of the *3GPP TS 36.211* specification for more
        information about the PUSCH delta sequence shift.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the physical uplink shared channel (PUSCH) delta sequence shift, which is used to calculate cyclic shift of
                the demodulation reference signal (DMRS). Refer to section 5.5.2.1.1 of the *3GPP TS 36.211* specification for more
                information about the PUSCH delta sequence shift.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DELTA_SEQUENCE_SHIFT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_delta_sequence_shift(self, selector_string, value):
        r"""Sets the physical uplink shared channel (PUSCH) delta sequence shift, which is used to calculate cyclic shift of
        the demodulation reference signal (DMRS). Refer to section 5.5.2.1.1 of the *3GPP TS 36.211* specification for more
        information about the PUSCH delta sequence shift.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the physical uplink shared channel (PUSCH) delta sequence shift, which is used to calculate cyclic shift of
                the demodulation reference signal (DMRS). Refer to section 5.5.2.1.1 of the *3GPP TS 36.211* specification for more
                information about the PUSCH delta sequence shift.

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
                attributes.AttributeID.PUSCH_DELTA_SEQUENCE_SHIFT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_modulation_type(self, selector_string):
        r"""Gets the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **QPSK**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | QPSK (0)     | Specifies a QPSK modulation scheme.     |
        +--------------+-----------------------------------------+
        | 16 QAM (1)   | Specifies a 16-QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 64 QAM (2)   | Specifies a 64-QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 256 QAM (3)  | Specifies a 256-QAM modulation scheme.  |
        +--------------+-----------------------------------------+
        | 1024 QAM (4) | Specifies a 1024-QAM modulation scheme. |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschModulationType):
                Specifies the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_MODULATION_TYPE.value
            )
            attr_val = enums.PuschModulationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_modulation_type(self, selector_string, value):
        r"""Sets the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **QPSK**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | QPSK (0)     | Specifies a QPSK modulation scheme.     |
        +--------------+-----------------------------------------+
        | 16 QAM (1)   | Specifies a 16-QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 64 QAM (2)   | Specifies a 64-QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 256 QAM (3)  | Specifies a 256-QAM modulation scheme.  |
        +--------------+-----------------------------------------+
        | 1024 QAM (4) | Specifies a 1024-QAM modulation scheme. |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschModulationType, int):
                Specifies the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschModulationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_MODULATION_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_number_of_resource_block_clusters(self, selector_string):
        r"""Gets the number of resource allocation clusters, with each cluster including one or more consecutive resource
        blocks. Refer to 5.5.2.1.1 of the *3GPP TS 36.213* specification for more information about the number of channels in
        the physical uplink shared channel (PUSCH).

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of resource allocation clusters, with each cluster including one or more consecutive resource
                blocks. Refer to 5.5.2.1.1 of the *3GPP TS 36.213* specification for more information about the number of channels in
                the physical uplink shared channel (PUSCH).

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
                attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_number_of_resource_block_clusters(self, selector_string, value):
        r"""Sets the number of resource allocation clusters, with each cluster including one or more consecutive resource
        blocks. Refer to 5.5.2.1.1 of the *3GPP TS 36.213* specification for more information about the number of channels in
        the physical uplink shared channel (PUSCH).

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of resource allocation clusters, with each cluster including one or more consecutive resource
                blocks. Refer to 5.5.2.1.1 of the *3GPP TS 36.213* specification for more information about the number of channels in
                the physical uplink shared channel (PUSCH).

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
                attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_resource_block_offset(self, selector_string):
        r"""Gets the starting resource block number of a physical uplink shared channel (PUSCH) cluster.

        Use "cluster<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"/cluster<*l*>"  as the selector string to
        configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the starting resource block number of a physical uplink shared channel (PUSCH) cluster.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_resource_block_offset(self, selector_string, value):
        r"""Sets the starting resource block number of a physical uplink shared channel (PUSCH) cluster.

        Use "cluster<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"/cluster<*l*>"  as the selector string to
        configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the starting resource block number of a physical uplink shared channel (PUSCH) cluster.

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
                attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_number_of_resource_blocks(self, selector_string):
        r"""Gets the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster.

        Use "cluster<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"/cluster<*l*>"  as the selector string to
        configure or read this attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
        bandwidth are configured.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster.

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
                attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_number_of_resource_blocks(self, selector_string, value):
        r"""Sets the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster.

        Use "cluster<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"/cluster<*l*>"  as the selector string to
        configure or read this attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
        bandwidth are configured.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster.

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
                attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_n_dmrs_2(self, selector_string):
        r"""Gets the n_DMRS_2 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
        in a slot. The valid values for this attribute are, as defined in table 5.5.2.1.1-1 of the *3GPP TS 36.211*
        specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the n_DMRS_2 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
                in a slot. The valid values for this attribute are, as defined in table 5.5.2.1.1-1 of the *3GPP TS 36.211*
                specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_N_DMRS_2.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_n_dmrs_2(self, selector_string, value):
        r"""Sets the n_DMRS_2 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
        in a slot. The valid values for this attribute are, as defined in table 5.5.2.1.1-1 of the *3GPP TS 36.211*
        specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the n_DMRS_2 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
                in a slot. The valid values for this attribute are, as defined in table 5.5.2.1.1-1 of the *3GPP TS 36.211*
                specification.

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
                updated_selector_string, attributes.AttributeID.PUSCH_N_DMRS_2.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_cyclic_shift_field(self, selector_string):
        r"""Gets the cyclic shift field in uplink-related DCI format. When the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DMRS_OCC_ENABLED` attribute is set to **True**,
        the measurement uses the table 5.5.2.1.1-1 of *3GPP 36.211* specification to decide the valued of n(2)DMRS and
        [w(0) w(1)] for DMRS signal based on Cyclic Shift Field along with
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE`.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 7, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the cyclic shift field in uplink-related DCI format. When the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DMRS_OCC_ENABLED` attribute is set to **True**,
                the measurement uses the table 5.5.2.1.1-1 of *3GPP 36.211* specification to decide the valued of n(2)DMRS and
                [w(0) w(1)] for DMRS signal based on Cyclic Shift Field along with
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE`.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_CYCLIC_SHIFT_FIELD.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_cyclic_shift_field(self, selector_string, value):
        r"""Sets the cyclic shift field in uplink-related DCI format. When the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DMRS_OCC_ENABLED` attribute is set to **True**,
        the measurement uses the table 5.5.2.1.1-1 of *3GPP 36.211* specification to decide the valued of n(2)DMRS and
        [w(0) w(1)] for DMRS signal based on Cyclic Shift Field along with
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE`.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 7, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the cyclic shift field in uplink-related DCI format. When the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DMRS_OCC_ENABLED` attribute is set to **True**,
                the measurement uses the table 5.5.2.1.1-1 of *3GPP 36.211* specification to decide the valued of n(2)DMRS and
                [w(0) w(1)] for DMRS signal based on Cyclic Shift Field along with
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE`.

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
                attributes.AttributeID.PUSCH_CYCLIC_SHIFT_FIELD.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_power(self, selector_string):
        r"""Gets the power of the physical uplink shared channel (PUSCH) data relative to PUSCH DMRS for a component carrier.
        This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of the physical uplink shared channel (PUSCH) data relative to PUSCH DMRS for a component carrier.
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
                updated_selector_string, attributes.AttributeID.PUSCH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_power(self, selector_string, value):
        r"""Sets the power of the physical uplink shared channel (PUSCH) data relative to PUSCH DMRS for a component carrier.
        This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of the physical uplink shared channel (PUSCH) data relative to PUSCH DMRS for a component carrier.
                This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PUSCH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_enabled(self, selector_string):
        r"""Gets whether the LTE signal getting measured contains SRS transmission.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+------------------------------------------------------+
        | Name (Value) | Description                                          |
        +==============+======================================================+
        | False (0)    | Measurement expects signal without SRS transmission. |
        +--------------+------------------------------------------------------+
        | True (1)     | Measurement expects signal with SRS transmission.    |
        +--------------+------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SrsEnabled):
                Specifies whether the LTE signal getting measured contains SRS transmission.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_ENABLED.value
            )
            attr_val = enums.SrsEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_enabled(self, selector_string, value):
        r"""Sets whether the LTE signal getting measured contains SRS transmission.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+------------------------------------------------------+
        | Name (Value) | Description                                          |
        +==============+======================================================+
        | False (0)    | Measurement expects signal without SRS transmission. |
        +--------------+------------------------------------------------------+
        | True (1)     | Measurement expects signal with SRS transmission.    |
        +--------------+------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SrsEnabled, int):
                Specifies whether the LTE signal getting measured contains SRS transmission.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SrsEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_subframe_configuration(self, selector_string):
        r"""Gets the SRS subframe configuration specified in the Table 5.5.3.3-1 of *3GPP 36.211* specification. It is a
        cell-specific attribute. This attribute defines the subframes that are reserved for SRS transmission in a given cell.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute
        to **FDD**, valid values are from 0 to 14, and when you set the Duplex Scheme attribute to **TDD**, valid values are
        from 0 to 13.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the SRS subframe configuration specified in the Table 5.5.3.3-1 of *3GPP 36.211* specification. It is a
                cell-specific attribute. This attribute defines the subframes that are reserved for SRS transmission in a given cell.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_SUBFRAME_CONFIGURATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_subframe_configuration(self, selector_string, value):
        r"""Sets the SRS subframe configuration specified in the Table 5.5.3.3-1 of *3GPP 36.211* specification. It is a
        cell-specific attribute. This attribute defines the subframes that are reserved for SRS transmission in a given cell.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute
        to **FDD**, valid values are from 0 to 14, and when you set the Duplex Scheme attribute to **TDD**, valid values are
        from 0 to 13.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the SRS subframe configuration specified in the Table 5.5.3.3-1 of *3GPP 36.211* specification. It is a
                cell-specific attribute. This attribute defines the subframes that are reserved for SRS transmission in a given cell.

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
                attributes.AttributeID.SRS_SUBFRAME_CONFIGURATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_c_srs(self, selector_string):
        r"""Gets the cell-specific SRS bandwidth configuration *C\ :sub:`SRS*
        `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 7. Valid values are from 0 to 7, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the cell-specific SRS bandwidth configuration *C\ :sub:`SRS*
                `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_C_SRS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_c_srs(self, selector_string, value):
        r"""Sets the cell-specific SRS bandwidth configuration *C\ :sub:`SRS*
        `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 7. Valid values are from 0 to 7, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the cell-specific SRS bandwidth configuration *C\ :sub:`SRS*
                `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

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
                updated_selector_string, attributes.AttributeID.SRS_C_SRS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_b_srs(self, selector_string):
        r"""Gets the UE specific SRS bandwidth configuration *B\ :sub:`SRS*
        `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are from 0 to 3, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the UE specific SRS bandwidth configuration *B\ :sub:`SRS*
                `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_B_SRS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_b_srs(self, selector_string, value):
        r"""Sets the UE specific SRS bandwidth configuration *B\ :sub:`SRS*
        `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are from 0 to 3, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the UE specific SRS bandwidth configuration *B\ :sub:`SRS*
                `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

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
                updated_selector_string, attributes.AttributeID.SRS_B_SRS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_i_srs(self, selector_string):
        r"""Gets the SRS configuration index *I\ :sub:`SRS*
        `\. It is used to determine the SRS periodicity and SRS subframe offset. It is a UE specific attribute which
        defines whether the SRS is transmitted in the subframe reserved for SRS by SRS subframe configuration. Refer to *3GPP
        36.213* specification for more details.

        If the periodicity of the given SRS configuration is more than one frame, use the multi-frame generation with a
        digital trigger at the start of the first frame for accurate demodulation.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute
        to **FDD**, valid values are from 0 to 636, and when you set the Duplex Scheme attribute to **TDD**, valid values are
        from 0 to 644.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the SRS configuration index *I\ :sub:`SRS*
                `\. It is used to determine the SRS periodicity and SRS subframe offset. It is a UE specific attribute which
                defines whether the SRS is transmitted in the subframe reserved for SRS by SRS subframe configuration. Refer to *3GPP
                36.213* specification for more details.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_I_SRS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_i_srs(self, selector_string, value):
        r"""Sets the SRS configuration index *I\ :sub:`SRS*
        `\. It is used to determine the SRS periodicity and SRS subframe offset. It is a UE specific attribute which
        defines whether the SRS is transmitted in the subframe reserved for SRS by SRS subframe configuration. Refer to *3GPP
        36.213* specification for more details.

        If the periodicity of the given SRS configuration is more than one frame, use the multi-frame generation with a
        digital trigger at the start of the first frame for accurate demodulation.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute
        to **FDD**, valid values are from 0 to 636, and when you set the Duplex Scheme attribute to **TDD**, valid values are
        from 0 to 644.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the SRS configuration index *I\ :sub:`SRS*
                `\. It is used to determine the SRS periodicity and SRS subframe offset. It is a UE specific attribute which
                defines whether the SRS is transmitted in the subframe reserved for SRS by SRS subframe configuration. Refer to *3GPP
                36.213* specification for more details.

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
                updated_selector_string, attributes.AttributeID.SRS_I_SRS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_n_rrc(self, selector_string):
        r"""Gets the SRS frequency domain position *n\ :sub:`RRC*
        `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are from 0 to 23, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the SRS frequency domain position *n\ :sub:`RRC*
                `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_N_RRC.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_n_rrc(self, selector_string, value):
        r"""Sets the SRS frequency domain position *n\ :sub:`RRC*
        `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are from 0 to 23, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the SRS frequency domain position *n\ :sub:`RRC*
                `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

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
                updated_selector_string, attributes.AttributeID.SRS_N_RRC.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_n_srs_cs(self, selector_string):
        r"""Gets the cyclic shift value *n\ :sub:`SRS*
        \ :sup:`CS`\
        `\ used for generating SRS base sequence. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more
        details.
        
        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
        
        The default value is 0. Valid values are from 0 to 7, inclusive.

        Args:
            selector_string (string): 
                Pass an empty string.
        
        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the cyclic shift value *n\ :sub:`SRS*
                \ :sup:`CS`\
                `\ used for generating SRS base sequence. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more
                details.

            error_code (int): 
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_N_SRS_CS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_n_srs_cs(self, selector_string, value):
        r"""Sets the cyclic shift value *n\ :sub:`SRS*
        \ :sup:`CS`\
        `\ used for generating SRS base sequence. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more
        details.
        
        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
        
        The default value is 0. Valid values are from 0 to 7, inclusive.

        Args:
            selector_string (string): 
                Pass an empty string.

            value (int): 
                Specifies the cyclic shift value *n\ :sub:`SRS*
                \ :sup:`CS`\
                `\ used for generating SRS base sequence. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more
                details.

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
                updated_selector_string, attributes.AttributeID.SRS_N_SRS_CS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_b_hop(self, selector_string):
        r"""Gets the SRS hopping bandwidth b\ :sub:`hop`\. Frequency hopping for SRS signal is enabled when the value of SRS
        b_hop attribute is less than the value of :py:attr:`~nirfmxlte.attributes.AttributeID.SRS_B_SRS` attribute.

        If the given measurement interval is more than one frame, use the multi-frame generation with digital trigger
        at the start of the first frame for accurate demodulation, since hopping pattern will vary across frames.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 3. Valid values are from 0 to 3, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the SRS hopping bandwidth b\ :sub:`hop`\. Frequency hopping for SRS signal is enabled when the value of SRS
                b_hop attribute is less than the value of :py:attr:`~nirfmxlte.attributes.AttributeID.SRS_B_SRS` attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_B_HOP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_b_hop(self, selector_string, value):
        r"""Sets the SRS hopping bandwidth b\ :sub:`hop`\. Frequency hopping for SRS signal is enabled when the value of SRS
        b_hop attribute is less than the value of :py:attr:`~nirfmxlte.attributes.AttributeID.SRS_B_SRS` attribute.

        If the given measurement interval is more than one frame, use the multi-frame generation with digital trigger
        at the start of the first frame for accurate demodulation, since hopping pattern will vary across frames.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 3. Valid values are from 0 to 3, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the SRS hopping bandwidth b\ :sub:`hop`\. Frequency hopping for SRS signal is enabled when the value of SRS
                b_hop attribute is less than the value of :py:attr:`~nirfmxlte.attributes.AttributeID.SRS_B_SRS` attribute.

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
                updated_selector_string, attributes.AttributeID.SRS_B_HOP.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_k_tc(self, selector_string):
        r"""Gets the transmission comb index. If you set this attribute to 0, SRS is transmitted on the even subcarriers in
        the allocated region. If you set this attribute to 1, SRS is transmitted on the odd subcarriers in the allocated
        region.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the transmission comb index. If you set this attribute to 0, SRS is transmitted on the even subcarriers in
                the allocated region. If you set this attribute to 1, SRS is transmitted on the odd subcarriers in the allocated
                region.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_K_TC.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_k_tc(self, selector_string, value):
        r"""Sets the transmission comb index. If you set this attribute to 0, SRS is transmitted on the even subcarriers in
        the allocated region. If you set this attribute to 1, SRS is transmitted on the odd subcarriers in the allocated
        region.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the transmission comb index. If you set this attribute to 0, SRS is transmitted on the even subcarriers in
                the allocated region. If you set this attribute to 1, SRS is transmitted on the odd subcarriers in the allocated
                region.

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
                updated_selector_string, attributes.AttributeID.SRS_K_TC.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_maximum_up_pts_enabled(self, selector_string):
        r"""Gets SRS MaxUpPTS parameter which determines whether SRS is transmitted in all possible RBs of UpPTS symbols in
        LTE TDD. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+-------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                               |
        +==============+===========================================================================================+
        | False (0)    | In special subframe, SRS is transmitted in RBs specified by SRS bandwidth configurations. |
        +--------------+-------------------------------------------------------------------------------------------+
        | True (1)     | In special subframe, SRS is transmitted in all possible RBs.                              |
        +--------------+-------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SrsMaximumUpPtsEnabled):
                Specifies SRS MaxUpPTS parameter which determines whether SRS is transmitted in all possible RBs of UpPTS symbols in
                LTE TDD. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_MAXIMUM_UPPTS_ENABLED.value
            )
            attr_val = enums.SrsMaximumUpPtsEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_maximum_up_pts_enabled(self, selector_string, value):
        r"""Sets SRS MaxUpPTS parameter which determines whether SRS is transmitted in all possible RBs of UpPTS symbols in
        LTE TDD. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+-------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                               |
        +==============+===========================================================================================+
        | False (0)    | In special subframe, SRS is transmitted in RBs specified by SRS bandwidth configurations. |
        +--------------+-------------------------------------------------------------------------------------------+
        | True (1)     | In special subframe, SRS is transmitted in all possible RBs.                              |
        +--------------+-------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SrsMaximumUpPtsEnabled, int):
                Specifies SRS MaxUpPTS parameter which determines whether SRS is transmitted in all possible RBs of UpPTS symbols in
                LTE TDD. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SrsMaximumUpPtsEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SRS_MAXIMUM_UPPTS_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_subframe_1_n_ra(self, selector_string):
        r"""Gets the number of format 4 PRACH allocations in UpPTS for Subframe 1, first special subframe, in LTE TDD.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 6.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of format 4 PRACH allocations in UpPTS for Subframe 1, first special subframe, in LTE TDD.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_SUBFRAME1_N_RA.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_subframe_1_n_ra(self, selector_string, value):
        r"""Sets the number of format 4 PRACH allocations in UpPTS for Subframe 1, first special subframe, in LTE TDD.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 6.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of format 4 PRACH allocations in UpPTS for Subframe 1, first special subframe, in LTE TDD.

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
                updated_selector_string, attributes.AttributeID.SRS_SUBFRAME1_N_RA.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_subframe_6_n_ra(self, selector_string):
        r"""Gets the number of format 4 PRACH allocations in UpPTS for Subframe 6, second special subframe, in LTE TDD. It is
        ignored for UL/DL Configuration 3, 4, and 5.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 6.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of format 4 PRACH allocations in UpPTS for Subframe 6, second special subframe, in LTE TDD. It is
                ignored for UL/DL Configuration 3, 4, and 5.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SRS_SUBFRAME6_N_RA.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_subframe_6_n_ra(self, selector_string, value):
        r"""Sets the number of format 4 PRACH allocations in UpPTS for Subframe 6, second special subframe, in LTE TDD. It is
        ignored for UL/DL Configuration 3, 4, and 5.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 6.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of format 4 PRACH allocations in UpPTS for Subframe 6, second special subframe, in LTE TDD. It is
                ignored for UL/DL Configuration 3, 4, and 5.

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
                updated_selector_string, attributes.AttributeID.SRS_SUBFRAME6_N_RA.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_srs_power(self, selector_string):
        r"""Gets the average power of SRS transmission with respect to PUSCH DMRS power. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the average power of SRS transmission with respect to PUSCH DMRS power. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SRS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_srs_power(self, selector_string, value):
        r"""Sets the average power of SRS transmission with respect to PUSCH DMRS power. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the average power of SRS transmission with respect to PUSCH DMRS power. This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.SRS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pssch_modulation_type(self, selector_string):
        r"""Gets the modulation scheme used in physical sidelink shared channel (PSSCH) of the signal being measured.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **QPSK**.

        +--------------+---------------------------------------+
        | Name (Value) | Description                           |
        +==============+=======================================+
        | QPSK (0)     | Specifies a QPSK modulation scheme.   |
        +--------------+---------------------------------------+
        | 16 QAM (1)   | Specifies a 16-QAM modulation scheme. |
        +--------------+---------------------------------------+
        | 64 QAM (2)   | Specifies a 64-QAM modulation scheme. |
        +--------------+---------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PsschModulationType):
                Specifies the modulation scheme used in physical sidelink shared channel (PSSCH) of the signal being measured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PSSCH_MODULATION_TYPE.value
            )
            attr_val = enums.PsschModulationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pssch_modulation_type(self, selector_string, value):
        r"""Sets the modulation scheme used in physical sidelink shared channel (PSSCH) of the signal being measured.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **QPSK**.

        +--------------+---------------------------------------+
        | Name (Value) | Description                           |
        +==============+=======================================+
        | QPSK (0)     | Specifies a QPSK modulation scheme.   |
        +--------------+---------------------------------------+
        | 16 QAM (1)   | Specifies a 16-QAM modulation scheme. |
        +--------------+---------------------------------------+
        | 64 QAM (2)   | Specifies a 64-QAM modulation scheme. |
        +--------------+---------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PsschModulationType, int):
                Specifies the modulation scheme used in physical sidelink shared channel (PSSCH) of the signal being measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PsschModulationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PSSCH_MODULATION_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pssch_resource_block_offset(self, selector_string):
        r"""Gets the starting resource block number of a physical sidelink shared channel (PSSCH) allocation.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the starting resource block number of a physical sidelink shared channel (PSSCH) allocation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PSSCH_RESOURCE_BLOCK_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pssch_resource_block_offset(self, selector_string, value):
        r"""Sets the starting resource block number of a physical sidelink shared channel (PSSCH) allocation.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the starting resource block number of a physical sidelink shared channel (PSSCH) allocation.

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
                attributes.AttributeID.PSSCH_RESOURCE_BLOCK_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pssch_number_of_resource_blocks(self, selector_string):
        r"""Gets the number of consecutive resource blocks in a physical sidelink shared channel (PSSCH) allocation.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
        bandwidth are configured.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of consecutive resource blocks in a physical sidelink shared channel (PSSCH) allocation.

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
                attributes.AttributeID.PSSCH_NUMBER_OF_RESOURCE_BLOCKS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pssch_number_of_resource_blocks(self, selector_string, value):
        r"""Sets the number of consecutive resource blocks in a physical sidelink shared channel (PSSCH) allocation.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
        bandwidth are configured.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of consecutive resource blocks in a physical sidelink shared channel (PSSCH) allocation.

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
                attributes.AttributeID.PSSCH_NUMBER_OF_RESOURCE_BLOCKS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pssch_power(self, selector_string):
        r"""Gets the power of the physical sidelink shared channel (PSSCH) data relative to PSSCH DMRS for a component
        carrier. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of the physical sidelink shared channel (PSSCH) data relative to PSSCH DMRS for a component
                carrier. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PSSCH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pssch_power(self, selector_string, value):
        r"""Sets the power of the physical sidelink shared channel (PSSCH) data relative to PSSCH DMRS for a component
        carrier. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of the physical sidelink shared channel (PSSCH) data relative to PSSCH DMRS for a component
                carrier. This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PSSCH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_laa_starting_subframe(self, selector_string):
        r"""Gets the starting subframe of an LAA burst.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the starting subframe of an LAA burst.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.LAA_STARTING_SUBFRAME.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_laa_starting_subframe(self, selector_string, value):
        r"""Sets the starting subframe of an LAA burst.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the starting subframe of an LAA burst.

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
                updated_selector_string, attributes.AttributeID.LAA_STARTING_SUBFRAME.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_laa_number_of_subframes(self, selector_string):
        r"""Gets the number of subframes in an LAA burst including the starting subframe.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of subframes in an LAA burst including the starting subframe.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.LAA_NUMBER_OF_SUBFRAMES.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_laa_number_of_subframes(self, selector_string, value):
        r"""Sets the number of subframes in an LAA burst including the starting subframe.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of subframes in an LAA burst including the starting subframe.

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
                updated_selector_string, attributes.AttributeID.LAA_NUMBER_OF_SUBFRAMES.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_laa_uplink_start_position(self, selector_string):
        r"""Gets the starting position of symbol 0 in the first subframe of an LAA uplink burst. Refer to section 5.6 of the
        *3GPP 36.211* specification for more information regarding LAA uplink start position.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **00**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | 00 (0)       | The symbol 0 in the first subframe of an LAA uplink burst is completely occupied. There is no idle duration.             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 01 (1)       | The starting position of symbol 0 in the first subframe of an LAA uplink burst is calculated as per section 5.6 (frame   |
        |              | structure type 3) of the 3GPP 36.211 specification. The symbol is partially occupied.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 10 (2)       | The starting position of symbol 0 in the first subframe of an LAA uplink burst is calculated as per section 5.6 (frame   |
        |              | structure type 3) of the 3GPP 36.211 specification. The symbol is partially occupied.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 11 (3)       | The symbol 0 in the first subframe of an LAA uplink burst is completely idle. Symbol 0 is not transmitted in this case.  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LaaUplinkStartPosition):
                Specifies the starting position of symbol 0 in the first subframe of an LAA uplink burst. Refer to section 5.6 of the
                *3GPP 36.211* specification for more information regarding LAA uplink start position.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.LAA_UPLINK_START_POSITION.value
            )
            attr_val = enums.LaaUplinkStartPosition(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_laa_uplink_start_position(self, selector_string, value):
        r"""Sets the starting position of symbol 0 in the first subframe of an LAA uplink burst. Refer to section 5.6 of the
        *3GPP 36.211* specification for more information regarding LAA uplink start position.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **00**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | 00 (0)       | The symbol 0 in the first subframe of an LAA uplink burst is completely occupied. There is no idle duration.             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 01 (1)       | The starting position of symbol 0 in the first subframe of an LAA uplink burst is calculated as per section 5.6 (frame   |
        |              | structure type 3) of the 3GPP 36.211 specification. The symbol is partially occupied.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 10 (2)       | The starting position of symbol 0 in the first subframe of an LAA uplink burst is calculated as per section 5.6 (frame   |
        |              | structure type 3) of the 3GPP 36.211 specification. The symbol is partially occupied.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 11 (3)       | The symbol 0 in the first subframe of an LAA uplink burst is completely idle. Symbol 0 is not transmitted in this case.  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LaaUplinkStartPosition, int):
                Specifies the starting position of symbol 0 in the first subframe of an LAA uplink burst. Refer to section 5.6 of the
                *3GPP 36.211* specification for more information regarding LAA uplink start position.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.LaaUplinkStartPosition else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.LAA_UPLINK_START_POSITION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_laa_uplink_ending_symbol(self, selector_string):
        r"""Gets the ending symbol number in the last subframe of an LAA uplink burst. Refer to section 5.3.3.1.1A of the
        *3GPP 36.212* specification for more information regarding LAA uplink ending symbol.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **13**.

        +--------------+-------------------------------------------------------------+
        | Name (Value) | Description                                                 |
        +==============+=============================================================+
        | 12 (12)      | The last subframe of an LAA uplink burst ends at symbol 12. |
        +--------------+-------------------------------------------------------------+
        | 13 (13)      | The last subframe of an LAA uplink burst ends at symbol 13. |
        +--------------+-------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LaaUplinkEndingSymbol):
                Specifies the ending symbol number in the last subframe of an LAA uplink burst. Refer to section 5.3.3.1.1A of the
                *3GPP 36.212* specification for more information regarding LAA uplink ending symbol.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.LAA_UPLINK_ENDING_SYMBOL.value
            )
            attr_val = enums.LaaUplinkEndingSymbol(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_laa_uplink_ending_symbol(self, selector_string, value):
        r"""Sets the ending symbol number in the last subframe of an LAA uplink burst. Refer to section 5.3.3.1.1A of the
        *3GPP 36.212* specification for more information regarding LAA uplink ending symbol.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **13**.

        +--------------+-------------------------------------------------------------+
        | Name (Value) | Description                                                 |
        +==============+=============================================================+
        | 12 (12)      | The last subframe of an LAA uplink burst ends at symbol 12. |
        +--------------+-------------------------------------------------------------+
        | 13 (13)      | The last subframe of an LAA uplink burst ends at symbol 13. |
        +--------------+-------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LaaUplinkEndingSymbol, int):
                Specifies the ending symbol number in the last subframe of an LAA uplink burst. Refer to section 5.3.3.1.1A of the
                *3GPP 36.212* specification for more information regarding LAA uplink ending symbol.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.LaaUplinkEndingSymbol else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.LAA_UPLINK_ENDING_SYMBOL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_laa_downlink_starting_symbol(self, selector_string):
        r"""Gets the starting symbol number in the first subframe of an LAA downlink burst. Refer to section 13A of the *3GPP
        36.213* specification for more information regarding LAA downlink starting symbol.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **0**.

        +--------------+-----------------------------------------------------------------+
        | Name (Value) | Description                                                     |
        +==============+=================================================================+
        | 0 (0)        | The first subframe of an LAA downlink burst starts at symbol 0. |
        +--------------+-----------------------------------------------------------------+
        | 7 (7)        | The first subframe of an LAA downlink burst starts at symbol 7. |
        +--------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LaaDownlinkStartingSymbol):
                Specifies the starting symbol number in the first subframe of an LAA downlink burst. Refer to section 13A of the *3GPP
                36.213* specification for more information regarding LAA downlink starting symbol.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.LAA_DOWNLINK_STARTING_SYMBOL.value
            )
            attr_val = enums.LaaDownlinkStartingSymbol(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_laa_downlink_starting_symbol(self, selector_string, value):
        r"""Sets the starting symbol number in the first subframe of an LAA downlink burst. Refer to section 13A of the *3GPP
        36.213* specification for more information regarding LAA downlink starting symbol.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **0**.

        +--------------+-----------------------------------------------------------------+
        | Name (Value) | Description                                                     |
        +==============+=================================================================+
        | 0 (0)        | The first subframe of an LAA downlink burst starts at symbol 0. |
        +--------------+-----------------------------------------------------------------+
        | 7 (7)        | The first subframe of an LAA downlink burst starts at symbol 7. |
        +--------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LaaDownlinkStartingSymbol, int):
                Specifies the starting symbol number in the first subframe of an LAA downlink burst. Refer to section 13A of the *3GPP
                36.213* specification for more information regarding LAA downlink starting symbol.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.LaaDownlinkStartingSymbol else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.LAA_DOWNLINK_STARTING_SYMBOL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_laa_downlink_number_of_ending_symbols(self, selector_string):
        r"""Gets the number of ending symbols in the last subframe of an LAA downlink burst. Refer to section 4.3 of the *3GPP
        36.211* specification for more information regarding LAA downlink number of ending symbols.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **14**.

        +--------------+-----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                       |
        +==============+===================================================================================+
        | 3 (3)        | The number of ending symbols in the last subframe of an LAA downlink burst is 3.  |
        +--------------+-----------------------------------------------------------------------------------+
        | 6 (6)        | The number of ending symbols in the last subframe of an LAA downlink burst is 6.  |
        +--------------+-----------------------------------------------------------------------------------+
        | 9 (9)        | The number of ending symbols in the last subframe of an LAA downlink burst is 9.  |
        +--------------+-----------------------------------------------------------------------------------+
        | 10 (10)      | The number of ending symbols in the last subframe of an LAA downlink burst is 10. |
        +--------------+-----------------------------------------------------------------------------------+
        | 11 (11)      | The number of ending symbols in the last subframe of an LAA downlink burst is 11. |
        +--------------+-----------------------------------------------------------------------------------+
        | 12 (12)      | The number of ending symbols in the last subframe of an LAA downlink burst is 12. |
        +--------------+-----------------------------------------------------------------------------------+
        | 14 (14)      | The number of ending symbols in the last subframe of an LAA downlink burst is 14. |
        +--------------+-----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LaaDownlinkNumberOfEndingSymbols):
                Specifies the number of ending symbols in the last subframe of an LAA downlink burst. Refer to section 4.3 of the *3GPP
                36.211* specification for more information regarding LAA downlink number of ending symbols.

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
                attributes.AttributeID.LAA_DOWNLINK_NUMBER_OF_ENDING_SYMBOLS.value,
            )
            attr_val = enums.LaaDownlinkNumberOfEndingSymbols(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_laa_downlink_number_of_ending_symbols(self, selector_string, value):
        r"""Sets the number of ending symbols in the last subframe of an LAA downlink burst. Refer to section 4.3 of the *3GPP
        36.211* specification for more information regarding LAA downlink number of ending symbols.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **14**.

        +--------------+-----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                       |
        +==============+===================================================================================+
        | 3 (3)        | The number of ending symbols in the last subframe of an LAA downlink burst is 3.  |
        +--------------+-----------------------------------------------------------------------------------+
        | 6 (6)        | The number of ending symbols in the last subframe of an LAA downlink burst is 6.  |
        +--------------+-----------------------------------------------------------------------------------+
        | 9 (9)        | The number of ending symbols in the last subframe of an LAA downlink burst is 9.  |
        +--------------+-----------------------------------------------------------------------------------+
        | 10 (10)      | The number of ending symbols in the last subframe of an LAA downlink burst is 10. |
        +--------------+-----------------------------------------------------------------------------------+
        | 11 (11)      | The number of ending symbols in the last subframe of an LAA downlink burst is 11. |
        +--------------+-----------------------------------------------------------------------------------+
        | 12 (12)      | The number of ending symbols in the last subframe of an LAA downlink burst is 12. |
        +--------------+-----------------------------------------------------------------------------------+
        | 14 (14)      | The number of ending symbols in the last subframe of an LAA downlink burst is 14. |
        +--------------+-----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LaaDownlinkNumberOfEndingSymbols, int):
                Specifies the number of ending symbols in the last subframe of an LAA downlink burst. Refer to section 4.3 of the *3GPP
                36.211* specification for more information regarding LAA downlink number of ending symbols.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.LaaDownlinkNumberOfEndingSymbols else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.LAA_DOWNLINK_NUMBER_OF_ENDING_SYMBOLS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_n_cell_id(self, selector_string):
        r"""Gets the narrowband physical layer cell identity.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 503, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the narrowband physical layer cell identity.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NCELL_ID.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_n_cell_id(self, selector_string, value):
        r"""Sets the narrowband physical layer cell identity.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 503, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the narrowband physical layer cell identity.

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
                updated_selector_string, attributes.AttributeID.NCELL_ID.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_nb_iot_uplink_subcarrier_spacing(self, selector_string):
        r"""Gets the subcarrier bandwidth of an NB-IoT signal. This attribute specifies the spacing between adjacent
        subcarriers.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **15 kHz**.

        +--------------+-------------------------------------+
        | Name (Value) | Description                         |
        +==============+=====================================+
        | 15 kHz (0)   | The subcarrier spacing is 15 kHz.   |
        +--------------+-------------------------------------+
        | 3.75 kHz (1) | The subcarrier spacing is 3.75 kHz. |
        +--------------+-------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.NBIoTUplinkSubcarrierSpacing):
                Specifies the subcarrier bandwidth of an NB-IoT signal. This attribute specifies the spacing between adjacent
                subcarriers.

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
                attributes.AttributeID.NB_IOT_UPLINK_SUBCARRIER_SPACING.value,
            )
            attr_val = enums.NBIoTUplinkSubcarrierSpacing(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_nb_iot_uplink_subcarrier_spacing(self, selector_string, value):
        r"""Sets the subcarrier bandwidth of an NB-IoT signal. This attribute specifies the spacing between adjacent
        subcarriers.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **15 kHz**.

        +--------------+-------------------------------------+
        | Name (Value) | Description                         |
        +==============+=====================================+
        | 15 kHz (0)   | The subcarrier spacing is 15 kHz.   |
        +--------------+-------------------------------------+
        | 3.75 kHz (1) | The subcarrier spacing is 3.75 kHz. |
        +--------------+-------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.NBIoTUplinkSubcarrierSpacing, int):
                Specifies the subcarrier bandwidth of an NB-IoT signal. This attribute specifies the spacing between adjacent
                subcarriers.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.NBIoTUplinkSubcarrierSpacing else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.NB_IOT_UPLINK_SUBCARRIER_SPACING.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_npusch_channel_detection_enabled(self, selector_string):
        r"""Gets whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_TONE_OFFSET`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES`, and
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_MODULATION_TYPE` attributes are auto-detected by the measurement or
        specified by you.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement uses the values that you specify for the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod      |
        |              | Type attributes.                                                                                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the values of the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod Type attributes that   |
        |              | are auto-detected.                                                                                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoNPuschChannelDetectionEnabled):
                Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_TONE_OFFSET`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES`, and
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_MODULATION_TYPE` attributes are auto-detected by the measurement or
                specified by you.

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
                attributes.AttributeID.AUTO_NPUSCH_CHANNEL_DETECTION_ENABLED.value,
            )
            attr_val = enums.AutoNPuschChannelDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_npusch_channel_detection_enabled(self, selector_string, value):
        r"""Sets whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_TONE_OFFSET`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES`, and
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_MODULATION_TYPE` attributes are auto-detected by the measurement or
        specified by you.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement uses the values that you specify for the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod      |
        |              | Type attributes.                                                                                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the values of the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod Type attributes that   |
        |              | are auto-detected.                                                                                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoNPuschChannelDetectionEnabled, int):
                Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_TONE_OFFSET`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES`, and
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_MODULATION_TYPE` attributes are auto-detected by the measurement or
                specified by you.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AutoNPuschChannelDetectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.AUTO_NPUSCH_CHANNEL_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_format(self, selector_string):
        r"""Gets the NPUSCH format. A value of 1 indicates that narrowband physical uplink shared channel (NPUSCH) carries
        user data (UL-SCH) and a value of 2 indicates that NPUSCH carries uplink control information.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the NPUSCH format. A value of 1 indicates that narrowband physical uplink shared channel (NPUSCH) carries
                user data (UL-SCH) and a value of 2 indicates that NPUSCH carries uplink control information.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPUSCH_FORMAT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_format(self, selector_string, value):
        r"""Sets the NPUSCH format. A value of 1 indicates that narrowband physical uplink shared channel (NPUSCH) carries
        user data (UL-SCH) and a value of 2 indicates that NPUSCH carries uplink control information.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the NPUSCH format. A value of 1 indicates that narrowband physical uplink shared channel (NPUSCH) carries
                user data (UL-SCH) and a value of 2 indicates that NPUSCH carries uplink control information.

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
                updated_selector_string, attributes.AttributeID.NPUSCH_FORMAT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_starting_slot(self, selector_string):
        r"""Gets the starting slot number of the NPUSCH burst.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the starting slot number of the NPUSCH burst.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPUSCH_STARTING_SLOT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_starting_slot(self, selector_string, value):
        r"""Sets the starting slot number of the NPUSCH burst.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the starting slot number of the NPUSCH burst.

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
                updated_selector_string, attributes.AttributeID.NPUSCH_STARTING_SLOT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_tone_offset(self, selector_string):
        r"""Gets the location of the starting subcarrier (tone) within the 200 kHz bandwidth that is allocated to the
        narrowband physical uplink shared channel (NPUSCH).

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        For 15 kHz subcarrier spacing, the valid values are as follows:

        - for 1 tones, 0 to 11, inclusive

        - for 3 tones, 0, 3, 6, and 9

        - for 6 tones, 0 and 6

        - for 12 tones, 0

        For 3.75 kHz subcarrier spacing, the valid values are 0 to 47, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the location of the starting subcarrier (tone) within the 200 kHz bandwidth that is allocated to the
                narrowband physical uplink shared channel (NPUSCH).

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPUSCH_TONE_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_tone_offset(self, selector_string, value):
        r"""Sets the location of the starting subcarrier (tone) within the 200 kHz bandwidth that is allocated to the
        narrowband physical uplink shared channel (NPUSCH).

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        For 15 kHz subcarrier spacing, the valid values are as follows:

        - for 1 tones, 0 to 11, inclusive

        - for 3 tones, 0, 3, 6, and 9

        - for 6 tones, 0 and 6

        - for 12 tones, 0

        For 3.75 kHz subcarrier spacing, the valid values are 0 to 47, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the location of the starting subcarrier (tone) within the 200 kHz bandwidth that is allocated to the
                narrowband physical uplink shared channel (NPUSCH).

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
                updated_selector_string, attributes.AttributeID.NPUSCH_TONE_OFFSET.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_number_of_tones(self, selector_string):
        r"""Gets the number of subcarriers (tones) within the 200 kHz bandwidth that is allocated to the narrowband physical
        uplink shared channel (NPUSCH).

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 1.

        For Format 1 and 15 kHz subcarrier spacing, the valid values are 1, 3, 6, and 12.

        For Format 1, 3.75 kHz subcarrier spacing, and Format 2, the valid value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of subcarriers (tones) within the 200 kHz bandwidth that is allocated to the narrowband physical
                uplink shared channel (NPUSCH).

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPUSCH_NUMBER_OF_TONES.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_number_of_tones(self, selector_string, value):
        r"""Sets the number of subcarriers (tones) within the 200 kHz bandwidth that is allocated to the narrowband physical
        uplink shared channel (NPUSCH).

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 1.

        For Format 1 and 15 kHz subcarrier spacing, the valid values are 1, 3, 6, and 12.

        For Format 1, 3.75 kHz subcarrier spacing, and Format 2, the valid value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of subcarriers (tones) within the 200 kHz bandwidth that is allocated to the narrowband physical
                uplink shared channel (NPUSCH).

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
                updated_selector_string, attributes.AttributeID.NPUSCH_NUMBER_OF_TONES.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_modulation_type(self, selector_string):
        r"""Gets the modulation type that is used by the narrowband physical uplink shared channel (NPUSCH). This attribute is
        valid when :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` is equal to 1 and
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is equal to 1. The modulation type for other configurations
        is defined in Table 10.1.3.2-1 of the *3GPP TS 36.211* specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **BPSK**.

        +--------------+-------------------------------------+
        | Name (Value) | Description                         |
        +==============+=====================================+
        | BPSK (0)     | Specifies a BPSK modulation scheme. |
        +--------------+-------------------------------------+
        | QPSK (1)     | Specifies a QPSK modulation scheme. |
        +--------------+-------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.NPuschModulationType):
                Specifies the modulation type that is used by the narrowband physical uplink shared channel (NPUSCH). This attribute is
                valid when :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` is equal to 1 and
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is equal to 1. The modulation type for other configurations
                is defined in Table 10.1.3.2-1 of the *3GPP TS 36.211* specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPUSCH_MODULATION_TYPE.value
            )
            attr_val = enums.NPuschModulationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_modulation_type(self, selector_string, value):
        r"""Sets the modulation type that is used by the narrowband physical uplink shared channel (NPUSCH). This attribute is
        valid when :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` is equal to 1 and
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is equal to 1. The modulation type for other configurations
        is defined in Table 10.1.3.2-1 of the *3GPP TS 36.211* specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is **BPSK**.

        +--------------+-------------------------------------+
        | Name (Value) | Description                         |
        +==============+=====================================+
        | BPSK (0)     | Specifies a BPSK modulation scheme. |
        +--------------+-------------------------------------+
        | QPSK (1)     | Specifies a QPSK modulation scheme. |
        +--------------+-------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.NPuschModulationType, int):
                Specifies the modulation type that is used by the narrowband physical uplink shared channel (NPUSCH). This attribute is
                valid when :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` is equal to 1 and
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is equal to 1. The modulation type for other configurations
                is defined in Table 10.1.3.2-1 of the *3GPP TS 36.211* specification.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.NPuschModulationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPUSCH_MODULATION_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_dmrs_base_sequence_mode(self, selector_string):
        r"""Gets whether the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_INDEX` attribute is
        computed by the measurement or specified by you. This attribute is valid when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` attribute to 1, and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | The measurement uses the value that you specify for the NPUSCH DMRS Base Sequence Index attribute.                       |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement uses the value of NCell ID attribute to compute the NPUSCH DMRS Base Sequence Index as defined in        |
        |              | section 10.1.4.1.2 of the 3GPP TS 36.211 specification.                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.NPuschDmrsBaseSequenceMode):
                Specifies whether the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_INDEX` attribute is
                computed by the measurement or specified by you. This attribute is valid when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` attribute to 1, and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_MODE.value
            )
            attr_val = enums.NPuschDmrsBaseSequenceMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_dmrs_base_sequence_mode(self, selector_string, value):
        r"""Sets whether the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_INDEX` attribute is
        computed by the measurement or specified by you. This attribute is valid when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` attribute to 1, and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | The measurement uses the value that you specify for the NPUSCH DMRS Base Sequence Index attribute.                       |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement uses the value of NCell ID attribute to compute the NPUSCH DMRS Base Sequence Index as defined in        |
        |              | section 10.1.4.1.2 of the 3GPP TS 36.211 specification.                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.NPuschDmrsBaseSequenceMode, int):
                Specifies whether the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_INDEX` attribute is
                computed by the measurement or specified by you. This attribute is valid when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` attribute to 1, and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.NPuschDmrsBaseSequenceMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_dmrs_base_sequence_index(self, selector_string):
        r"""Gets the base sequence index of the Narrowband Physical Uplink Shared Channel (NPUSCH) DMRS as defined in section
        10.1.4.1.2 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_MODE` attribute to **Manual**, and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        - For 3 tones, valid values are 0 to 11, inclusive.

        - For 6 tones, valid values are 0 to 13, inclusive.

        - For 12 tones, valid values are 0 to 29, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the base sequence index of the Narrowband Physical Uplink Shared Channel (NPUSCH) DMRS as defined in section
                10.1.4.1.2 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_MODE` attribute to **Manual**, and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

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
                attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_dmrs_base_sequence_index(self, selector_string, value):
        r"""Sets the base sequence index of the Narrowband Physical Uplink Shared Channel (NPUSCH) DMRS as defined in section
        10.1.4.1.2 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_MODE` attribute to **Manual**, and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        - For 3 tones, valid values are 0 to 11, inclusive.

        - For 6 tones, valid values are 0 to 13, inclusive.

        - For 12 tones, valid values are 0 to 29, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the base sequence index of the Narrowband Physical Uplink Shared Channel (NPUSCH) DMRS as defined in section
                10.1.4.1.2 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_MODE` attribute to **Manual**, and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

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
                attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_INDEX.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_dmrs_cyclic_shift(self, selector_string):
        r"""Gets the cyclic shift of the narrowband physical uplink shared channel (NPUSCH) DMRS as defined in Table
        10.1.4.1.2-3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3 or 6. If the value of NPUSCH Num
        Tones attribute is 12, the NPUSCH DMRS Cyclic Shift attribute has a fixed value of 0.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        - For 3 tones, valid values are 0 to 2, inclusive.

        - For 6 tones, valid values are 0 to 3, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the cyclic shift of the narrowband physical uplink shared channel (NPUSCH) DMRS as defined in Table
                10.1.4.1.2-3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3 or 6. If the value of NPUSCH Num
                Tones attribute is 12, the NPUSCH DMRS Cyclic Shift attribute has a fixed value of 0.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPUSCH_DMRS_CYCLIC_SHIFT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_dmrs_cyclic_shift(self, selector_string, value):
        r"""Sets the cyclic shift of the narrowband physical uplink shared channel (NPUSCH) DMRS as defined in Table
        10.1.4.1.2-3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3 or 6. If the value of NPUSCH Num
        Tones attribute is 12, the NPUSCH DMRS Cyclic Shift attribute has a fixed value of 0.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        - For 3 tones, valid values are 0 to 2, inclusive.

        - For 6 tones, valid values are 0 to 3, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the cyclic shift of the narrowband physical uplink shared channel (NPUSCH) DMRS as defined in Table
                10.1.4.1.2-3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3 or 6. If the value of NPUSCH Num
                Tones attribute is 12, the NPUSCH DMRS Cyclic Shift attribute has a fixed value of 0.

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
                attributes.AttributeID.NPUSCH_DMRS_CYCLIC_SHIFT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_dmrs_group_hopping_enabled(self, selector_string):
        r"""Gets whether the group hopping is enabled for narrowband physical uplink shared channel (NPUSCH) DMRS. This
        attribute is valid only when the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is 1.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Group hopping is disabled.                                                                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Group hopping is enabled. The sequence group number is calculated as defined in section 10.1.4.1.3 of the 3GPP TS        |
        |              | 36.211 specification.                                                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.NPuschDmrsGroupHoppingEnabled):
                Specifies whether the group hopping is enabled for narrowband physical uplink shared channel (NPUSCH) DMRS. This
                attribute is valid only when the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is 1.

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
                attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED.value,
            )
            attr_val = enums.NPuschDmrsGroupHoppingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_dmrs_group_hopping_enabled(self, selector_string, value):
        r"""Sets whether the group hopping is enabled for narrowband physical uplink shared channel (NPUSCH) DMRS. This
        attribute is valid only when the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is 1.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Group hopping is disabled.                                                                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Group hopping is enabled. The sequence group number is calculated as defined in section 10.1.4.1.3 of the 3GPP TS        |
        |              | 36.211 specification.                                                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.NPuschDmrsGroupHoppingEnabled, int):
                Specifies whether the group hopping is enabled for narrowband physical uplink shared channel (NPUSCH) DMRS. This
                attribute is valid only when the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is 1.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.NPuschDmrsGroupHoppingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npusch_dmrs_delta_sequence_shift(self, selector_string):
        r"""Gets the delta sequence shift of the narrowband physical uplink shared channel (NPUSCH) DMRS, which is used to
        calculate the sequence shift pattern. This value is used to compute the sequence group number as defined in section
        10.1.4.1.3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **True**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 29, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the delta sequence shift of the narrowband physical uplink shared channel (NPUSCH) DMRS, which is used to
                calculate the sequence shift pattern. This value is used to compute the sequence group number as defined in section
                10.1.4.1.3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **True**.

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
                attributes.AttributeID.NPUSCH_DMRS_DELTA_SEQUENCE_SHIFT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npusch_dmrs_delta_sequence_shift(self, selector_string, value):
        r"""Sets the delta sequence shift of the narrowband physical uplink shared channel (NPUSCH) DMRS, which is used to
        calculate the sequence shift pattern. This value is used to compute the sequence group number as defined in section
        10.1.4.1.3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **True**.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0. Valid values are 0 to 29, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the delta sequence shift of the narrowband physical uplink shared channel (NPUSCH) DMRS, which is used to
                calculate the sequence shift pattern. This value is used to compute the sequence group number as defined in section
                10.1.4.1.3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **True**.

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
                attributes.AttributeID.NPUSCH_DMRS_DELTA_SEQUENCE_SHIFT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_nb_iot_downlink_channel_configuration_mode(self, selector_string):
        r"""Gets the downlink channel configuration mode for NB-IoT.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Test Model**.

        +------------------+--------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                  |
        +==================+==============================================================================================================+
        | User Defined (1) | You have to manually set all the signals and channels.                                                       |
        +------------------+--------------------------------------------------------------------------------------------------------------+
        | Test Model (2)   | Configures all the signals and channels automatically according to the 3GPP NB-IoT test model specification. |
        +------------------+--------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.NBIoTDownlinkChannelConfigurationMode):
                Specifies the downlink channel configuration mode for NB-IoT.

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
                attributes.AttributeID.NB_IOT_DOWNLINK_CHANNEL_CONFIGURATION_MODE.value,
            )
            attr_val = enums.NBIoTDownlinkChannelConfigurationMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_nb_iot_downlink_channel_configuration_mode(self, selector_string, value):
        r"""Sets the downlink channel configuration mode for NB-IoT.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Test Model**.

        +------------------+--------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                  |
        +==================+==============================================================================================================+
        | User Defined (1) | You have to manually set all the signals and channels.                                                       |
        +------------------+--------------------------------------------------------------------------------------------------------------+
        | Test Model (2)   | Configures all the signals and channels automatically according to the 3GPP NB-IoT test model specification. |
        +------------------+--------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.NBIoTDownlinkChannelConfigurationMode, int):
                Specifies the downlink channel configuration mode for NB-IoT.

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
                value.value if type(value) is enums.NBIoTDownlinkChannelConfigurationMode else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.NB_IOT_DOWNLINK_CHANNEL_CONFIGURATION_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npss_power(self, selector_string):
        r"""Gets the power of the NB-IoT primary synchronization signal (NPSS) relative to the power of the NB-IoT downlink
        reference signal (NRS). This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of the NB-IoT primary synchronization signal (NPSS) relative to the power of the NB-IoT downlink
                reference signal (NRS). This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.NPSS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npss_power(self, selector_string, value):
        r"""Sets the power of the NB-IoT primary synchronization signal (NPSS) relative to the power of the NB-IoT downlink
        reference signal (NRS). This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of the NB-IoT primary synchronization signal (NPSS) relative to the power of the NB-IoT downlink
                reference signal (NRS). This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.NPSS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_nsss_power(self, selector_string):
        r"""Gets the power of the NB-IoT secondary synchronization signal (NSSS) relative to the power of the NB-IoT downlink
        reference signal (NRS). This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power of the NB-IoT secondary synchronization signal (NSSS) relative to the power of the NB-IoT downlink
                reference signal (NRS). This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.NSSS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_nsss_power(self, selector_string, value):
        r"""Sets the power of the NB-IoT secondary synchronization signal (NSSS) relative to the power of the NB-IoT downlink
        reference signal (NRS). This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power of the NB-IoT secondary synchronization signal (NSSS) relative to the power of the NB-IoT downlink
                reference signal (NRS). This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.NSSS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npdsch_power(self, selector_string):
        r"""Gets the NB-IoT physical downlink shared channel (NPDSCH) power level relative to the power of the NB-IoT downlink
        reference signal (NRS). This value is expressed in dB.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the NB-IoT physical downlink shared channel (NPDSCH) power level relative to the power of the NB-IoT downlink
                reference signal (NRS). This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.NPDSCH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npdsch_power(self, selector_string, value):
        r"""Sets the NB-IoT physical downlink shared channel (NPDSCH) power level relative to the power of the NB-IoT downlink
        reference signal (NRS). This value is expressed in dB.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the NB-IoT physical downlink shared channel (NPDSCH) power level relative to the power of the NB-IoT downlink
                reference signal (NRS). This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.NPDSCH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_npdsch_enabled(self, selector_string):
        r"""Gets whether NPDSCH is active in a particular subframe. Note that in even-numbered frames, subframes 0, 5, and 9
        are reserved for NPBCH, NPSS, and NSSS. In odd-numbered frames, subframes 10 and 15 are reserved for NPBCH and NPSS.The
        measurement will return an error if you try to configure NPDSCH for those subframes.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                       |
        +==============+===================================================================================+
        | False (0)    | Indicates to the measurement that NPDSCH is not present in a particular subframe. |
        +--------------+-----------------------------------------------------------------------------------+
        | True (1)     | Indicates to the measurement that NPDSCH is present in a particular subframe.     |
        +--------------+-----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.NpdschEnabled):
                Specifies whether NPDSCH is active in a particular subframe. Note that in even-numbered frames, subframes 0, 5, and 9
                are reserved for NPBCH, NPSS, and NSSS. In odd-numbered frames, subframes 10 and 15 are reserved for NPBCH and NPSS.The
                measurement will return an error if you try to configure NPDSCH for those subframes.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPDSCH_ENABLED.value
            )
            attr_val = enums.NpdschEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_npdsch_enabled(self, selector_string, value):
        r"""Sets whether NPDSCH is active in a particular subframe. Note that in even-numbered frames, subframes 0, 5, and 9
        are reserved for NPBCH, NPSS, and NSSS. In odd-numbered frames, subframes 10 and 15 are reserved for NPBCH and NPSS.The
        measurement will return an error if you try to configure NPDSCH for those subframes.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                       |
        +==============+===================================================================================+
        | False (0)    | Indicates to the measurement that NPDSCH is not present in a particular subframe. |
        +--------------+-----------------------------------------------------------------------------------+
        | True (1)     | Indicates to the measurement that NPDSCH is present in a particular subframe.     |
        +--------------+-----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.NpdschEnabled, int):
                Specifies whether NPDSCH is active in a particular subframe. Note that in even-numbered frames, subframes 0, 5, and 9
                are reserved for NPBCH, NPSS, and NSSS. In odd-numbered frames, subframes 10 and 15 are reserved for NPBCH and NPSS.The
                measurement will return an error if you try to configure NPDSCH for those subframes.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.NpdschEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.NPDSCH_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_emtc_analysis_enabled(self, selector_string):
        r"""Gets whether the component carrier contains enhanced machine type communications (Cat-M1 or Cat-M2) transmission.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                           |
        +==============+=======================================================================================================================+
        | False (0)    | The measurement considers the signal as LTE FDD/TDD transmission.                                                     |
        +--------------+-----------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Detects the eMTC half duplex pattern, narrow band hopping, and eMTC guard symbols present in the uplink transmission. |
        +--------------+-----------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.EmtcAnalysisEnabled):
                Specifies whether the component carrier contains enhanced machine type communications (Cat-M1 or Cat-M2) transmission.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.EMTC_ANALYSIS_ENABLED.value
            )
            attr_val = enums.EmtcAnalysisEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_emtc_analysis_enabled(self, selector_string, value):
        r"""Sets whether the component carrier contains enhanced machine type communications (Cat-M1 or Cat-M2) transmission.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                           |
        +==============+=======================================================================================================================+
        | False (0)    | The measurement considers the signal as LTE FDD/TDD transmission.                                                     |
        +--------------+-----------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Detects the eMTC half duplex pattern, narrow band hopping, and eMTC guard symbols present in the uplink transmission. |
        +--------------+-----------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.EmtcAnalysisEnabled, int):
                Specifies whether the component carrier contains enhanced machine type communications (Cat-M1 or Cat-M2) transmission.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.EmtcAnalysisEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.EMTC_ANALYSIS_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_auto_npusch_channel_detection_enabled(
        self, selector_string, auto_npusch_channel_detection_enabled
    ):
        r"""Configures whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_TONE_OFFSET`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES`, and
        :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_MODULATION_TYPE` attributes for the NPUSCH channel are auto-detected
        by the measurement or specified by you.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            auto_npusch_channel_detection_enabled (enums.AutoNPuschChannelDetectionEnabled, int):
                This parameter specifies whether the values of NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod Type
                attributes are auto-detected by the measurement or specified by you. The default value is **True**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The measurement uses the values that you specify for the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH ModType  |
                |              | attributes.                                                                                                              |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement uses the values of the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod Type attributes that   |
                |              | are auto-detected.                                                                                                       |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            auto_npusch_channel_detection_enabled = (
                auto_npusch_channel_detection_enabled.value
                if type(auto_npusch_channel_detection_enabled)
                is enums.AutoNPuschChannelDetectionEnabled
                else auto_npusch_channel_detection_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_auto_npusch_channel_detection_enabled(
                updated_selector_string, auto_npusch_channel_detection_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_auto_resource_block_detection_enabled(
        self, selector_string, auto_resource_block_detection_enabled
    ):
        r"""Configures whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_MODULATION_TYPE`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET`, and
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attributes are automatically detected by
        the measurement or if you specify the values of these attributes.

        The measurement ignores this method, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            auto_resource_block_detection_enabled (enums.AutoResourceBlockDetectionEnabled, int):
                This parameter specifies whether the values of the  PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num
                RBs attributes are automatically detected by the measurement or if you specify the values of these attributes. The
                default value is **True**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The values of the PUSCH Mod Type, PUSCH Num RB Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes that you specify  |
                |              | are used for the measurement.                                                                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The values of the PUSCH Mod Type, PUSCH Num RB Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes are detected      |
                |              | automatically and used for the measurement.                                                                              |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            auto_resource_block_detection_enabled = (
                auto_resource_block_detection_enabled.value
                if type(auto_resource_block_detection_enabled)
                is enums.AutoResourceBlockDetectionEnabled
                else auto_resource_block_detection_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_auto_resource_block_detection_enabled(
                updated_selector_string, auto_resource_block_detection_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_cell_specific_ratio(self, selector_string, cell_specific_ratio):
        r"""Configures the **cell specific ratio** parameter.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            cell_specific_ratio (enums.DownlinkUserDefinedRatio, int):
                This parameter specifies the ratio P\ :sub:`b`\/P\ :sub:`a`\ for the cell-specific ratio of one, two, or four
                cell-specific antenna ports as described in Table 5.2-1 in section 5.2 of the *3GPP TS 36.213 Specifications*. This
                parameter determines the power of the channel resource element (RE) in the symbols that do not contain the reference
                symbols. The default value is **P_B=0**.

                +--------------+--------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                          |
                +==============+======================================================================================+
                | P_B=0 (0)    | Specifies a ratio of 1 for one antenna port and 5/4 for two or four antenna ports.   |
                +--------------+--------------------------------------------------------------------------------------+
                | P_B=1 (1)    | Specifies a ratio of 4/5 for one antenna port and 1 for two or four antenna ports.   |
                +--------------+--------------------------------------------------------------------------------------+
                | P_B=2 (2)    | Specifies a ratio of 3/5 for one antenna port and 3/4 for two or four antenna ports. |
                +--------------+--------------------------------------------------------------------------------------+
                | P_B=3 (3)    | Specifies a ratio of 2/5 for one antenna port and 1/2 for two or four antenna ports. |
                +--------------+--------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            cell_specific_ratio = (
                cell_specific_ratio.value
                if type(cell_specific_ratio) is enums.DownlinkUserDefinedRatio
                else cell_specific_ratio
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_cell_specific_ratio(
                updated_selector_string, cell_specific_ratio
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_array(
        self, selector_string, component_carrier_bandwidth, component_carrier_frequency, cell_id
    ):
        r"""Configures an array of bandwidths, carrier offset frequencies, and cell IDs of component carriers.

        Use "subblock<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.  The default is "" (empty
                string).

                Example:

                "subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            component_carrier_bandwidth (float):
                This parameter specifies the array of channel bandwidths of the signal being measured. The default value is **10 M**.

                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)  | Description                                                                                                              |
                +===============+==========================================================================================================================+
                | 200.0 k (2e5) | Indicates a channel bandwidth of 200 kHz. This value indicates that the received signal is an NB-IoT stand-alone         |
                |               | signal.                                                                                                                  |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 1.4 M (1.4e6) | Indicates a channel bandwidth of 1.4 MHz.                                                                                |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 3.0 M (3e6)   | Indicates a channel bandwidth of 3 MHz.                                                                                  |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 5.0 M (5e6)   | Indicates a channel bandwidth of 5 MHz.                                                                                  |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 10.0 M (10e6) | Indicates a channel bandwidth of 10 MHz.                                                                                 |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 15.0 M (15e6) | Indicates a channel bandwidth of 15 MHz.                                                                                 |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 20.0 M (20e6) | Indicates a channel bandwidth of 20 MHz.                                                                                 |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+

            component_carrier_frequency (float):
                This parameter specifies the array of offsets of the component carrier from the subblock center frequency that you
                configure in the :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` attribute. This parameter is applicable
                only if you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to **User**.
                The default value is 0.

            cell_id (int):
                This parameter specifies the array of the physical layer cell identities. The default value is 0.

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
            error_code = self._interpreter.configure_array(
                updated_selector_string,
                component_carrier_bandwidth,
                component_carrier_frequency,
                cell_id,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_spacing(
        self, selector_string, component_carrier_spacing_type, component_carrier_at_center_frequency
    ):
        r"""Configures the **Component Carrier Spacing Type** and **Component Carrier at Center Frequency** parameters, which help
        to set the spacing between adjacent component carriers within a subblock.

        Use "subblock<*n*>" as the selector string to configure this method.

        Refer to the `Channel Spacing <www.ni.com/docs/en-US/bundle/rfmx-lte/page/channel-spacing.html>`_ and `Carrier
        Frequency Offset Definition and Reference Frequency
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_ topics for
        more information about carrier spacing.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.  The default is "" (empty
                string).

                Example:

                "subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            component_carrier_spacing_type (enums.ComponentCarrierSpacingType, int):
                This parameter specifies the spacing between the two adjacent component carriers within a subblock. The default value
                is **Nominal**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | Nominal (0)  | Calculates the frequency spacing between component carriers as defined in section 5.4.1A of the 3GPP TS 36.521           |
                |              | specification, and sets the CC Freq attribute.                                                                           |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Minimum (1)  | Calculates the frequency spacing between component carriers as defined in section 5.4.1A of the 3GPP TS 36.521           |
                |              | specification, and sets the CC Freq attribute.                                                                           |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | User (2)     | The CC frequency that you configure in the CC Freq attribute is used.                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            component_carrier_at_center_frequency (int):
                This parameter specifies the index of the component carrier having its center at the user-configured center frequency.
                RFmxLTE uses this parameter along with the CC Spacing Type attribute to calculate the component carrier frequency.  The
                default value is -1. If the value is -1, the CC frequency values are calculated such that the center of aggregated
                carriers (subblock) lies at the subblock center frequency. This parameter is ignored if you set the **Component Carrier
                Spacing Type** parameter to **User**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            component_carrier_spacing_type = (
                component_carrier_spacing_type.value
                if type(component_carrier_spacing_type) is enums.ComponentCarrierSpacingType
                else component_carrier_spacing_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_spacing(
                updated_selector_string,
                component_carrier_spacing_type,
                component_carrier_at_center_frequency,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure(
        self, selector_string, component_carrier_bandwidth, component_carrier_frequency, cell_id
    ):
        r"""Configures the **Component Carrier Bandwidth**, **Component Carrier Frequency**, and **Cell ID** of the component
        carrier.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            component_carrier_bandwidth (float):
                This parameter specifies the channel bandwidths of the signal being measured. The default value is **10.0 M**.

                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)  | Description                                                                                                              |
                +===============+==========================================================================================================================+
                | 200.0 k (2e5) | Indicates a channel bandwidth of 200 kHz. This value indicates that the received signal is an NB-IoT stand-alone         |
                |               | signal.                                                                                                                  |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 1.4 M (1.4e6) | Indicates a channel bandwidth of 1.4 MHz.                                                                                |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 3.0 M (3e6)   | Indicates a channel bandwidth of 3 MHz.                                                                                  |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 5.0 M (5e6)   | Indicates a channel bandwidth of 5 MHz.                                                                                  |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 10.0 M (10e6) | Indicates a channel bandwidth of 10 MHz.                                                                                 |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 15.0 M (15e6) | Indicates a channel bandwidth of 15 MHz.                                                                                 |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | 20.0 M (20e6) | Indicates a channel bandwidth of 20 MHz.                                                                                 |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+

            component_carrier_frequency (float):
                This parameter specifies the offsets of the component carrier from the subblock center frequency that you configure in
                the :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` attribute. This parameter is applicable only if you
                set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to **User**. The default
                value is 0.

            cell_id (int):
                This parameter specifies the physical layer cell identities. The default value is 0. Valid values are 0 to 503,
                inclusive.

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
            error_code = self._interpreter.configure(
                updated_selector_string,
                component_carrier_bandwidth,
                component_carrier_frequency,
                cell_id,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_downlink_auto_cell_id_detection_enabled(
        self, selector_string, auto_cell_id_detection_enabled
    ):
        r"""Configures whether the cell ID is configured by the user or auto-detected by the measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            auto_cell_id_detection_enabled (enums.DownlinkAutoCellIDDetectionEnabled, int):
                This parameter specifies whether to enable autodetection the of cell ID. If signal being measured does not contain
                primary and secondary sync signal (PSS/SSS), autodetection of the cell ID is not possible. The default value is
                **True**.

                +--------------+-------------------------------------------------+
                | Name (Value) | Description                                     |
                +==============+=================================================+
                | False (0)    | The measurement uses the cell ID you configure. |
                +--------------+-------------------------------------------------+
                | True (1)     | The measurement auto detects the cell ID.       |
                +--------------+-------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            auto_cell_id_detection_enabled = (
                auto_cell_id_detection_enabled.value
                if type(auto_cell_id_detection_enabled) is enums.DownlinkAutoCellIDDetectionEnabled
                else auto_cell_id_detection_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_downlink_auto_cell_id_detection_enabled(
                updated_selector_string, auto_cell_id_detection_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_downlink_channel_configuration_mode(
        self, selector_string, channel_configuration_mode
    ):
        r"""Configures the downlink channel configuration mode.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            channel_configuration_mode (enums.DownlinkChannelConfigurationMode, int):
                This parameter specifies the channel configuration mode. The default value is **Test Model**.

                +------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)     | Description                                                                                                              |
                +==================+==========================================================================================================================+
                | User Defined (1) | You have to manually set all the signals and channels.                                                                   |
                +------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Test Model (2)   | You need to select a test model that will configure all the signals and channels automatically according to the 3GPP     |
                |                  | Specifications.                                                                                                          |
                +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            channel_configuration_mode = (
                channel_configuration_mode.value
                if type(channel_configuration_mode) is enums.DownlinkChannelConfigurationMode
                else channel_configuration_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_downlink_channel_configuration_mode(
                updated_selector_string, channel_configuration_mode
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_downlink_number_of_subframes(self, selector_string, number_of_subframes):
        r"""Configures the number of unique subframes that are transmitted from the DUT.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            number_of_subframes (int):
                This parameter specifies the number of subframes to be configured. If you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**, this
                parameter will be set to 10 for FDD and 20 for TDD by default. The default value is 10. Valid values are 10 to 20,
                inclusive.

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
            error_code = self._interpreter.configure_downlink_number_of_subframes(
                updated_selector_string, number_of_subframes
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_downlink_synchronization_signal(self, selector_string, pss_power, sss_power):
        r"""Configures the synchronization signal power relative to the cell-specific reference signal.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            pss_power (float):
                This parameter specifies the power of the primary synchronization signal (PSS) relative to the power of the
                cell-specific reference signal. This value is expressed in dB. The default value is 0.

            sss_power (float):
                This parameter specifies the power of the secondary synchronization signal (SSS) relative to the power of the
                cell-specific reference signal. This value is expressed in dB. The default value is 0.

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
            error_code = self._interpreter.configure_downlink_synchronization_signal(
                updated_selector_string, pss_power, sss_power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_downlink_test_model_array(self, selector_string, downlink_test_model):
        r"""Configures an array of the EUTRA test model type for each component carrier within the subblock.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.  The default is "" (empty
                string).

                Example:

                "subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            downlink_test_model (enums.DownlinkTestModel, int):
                This parameter specifies the array of EUTRA test model types when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
                section 6.1.1 of the *3GPP 36.141* specification for more information regarding test model configurations. The default
                value is **TM1.1**.

                +--------------+--------------------------------------+
                | Name (Value) | Description                          |
                +==============+======================================+
                | TM1.1 (0)    | Specifies an E-UTRA Test Model 1.1.  |
                +--------------+--------------------------------------+
                | TM1.2 (1)    | Specifies an E-UTRA Test Model 1.2.  |
                +--------------+--------------------------------------+
                | TM2 (2)      | Specifies an E-UTRA Test Model 2.    |
                +--------------+--------------------------------------+
                | TM2a (3)     | Specifies an E-UTRA Test Model 2a.   |
                +--------------+--------------------------------------+
                | TM2b (8)     | Specifies an E-UTRA Test Model 2b.   |
                +--------------+--------------------------------------+
                | TM3.1 (4)    | Specifies an E-UTRA Test Model 3.1.  |
                +--------------+--------------------------------------+
                | TM3.1a (7)   | Specifies an E-UTRA Test Model 3.1a. |
                +--------------+--------------------------------------+
                | TM3.1b (9)   | Specifies an E-UTRA Test Model 3.1b. |
                +--------------+--------------------------------------+
                | TM3.2 (5)    | Specifies an E-UTRA Test Model 3.2.  |
                +--------------+--------------------------------------+
                | TM3.3 (6)    | Specifies an E-UTRA Test Model 3.3.  |
                +--------------+--------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            downlink_test_model = (
                [v.value for v in downlink_test_model]
                if (
                    isinstance(downlink_test_model, list)
                    and all(isinstance(v, enums.DownlinkTestModel) for v in downlink_test_model)
                )
                else downlink_test_model
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_downlink_test_model_array(
                updated_selector_string, downlink_test_model
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_downlink_test_model(self, selector_string, downlink_test_model):
        r"""Configures the EUTRA test model type.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            downlink_test_model (enums.DownlinkTestModel, int):
                This parameter specifies the EUTRA test model type when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
                section 6.1.1 of the *3GPP 36.141* specification for more information regarding test model configurations. The default
                value is **TM1.1**.

                +--------------+--------------------------------------+
                | Name (Value) | Description                          |
                +==============+======================================+
                | TM1.1 (0)    | Specifies an E-UTRA Test Model 1.1.  |
                +--------------+--------------------------------------+
                | TM1.2 (1)    | Specifies an E-UTRA Test Model 1.2.  |
                +--------------+--------------------------------------+
                | TM2 (2)      | Specifies an E-UTRA Test Model 2.    |
                +--------------+--------------------------------------+
                | TM2a (3)     | Specifies an E-UTRA Test Model 2a.   |
                +--------------+--------------------------------------+
                | TM2b (8)     | Specifies an E-UTRA Test Model 2b.   |
                +--------------+--------------------------------------+
                | TM3.1 (4)    | Specifies an E-UTRA Test Model 3.1.  |
                +--------------+--------------------------------------+
                | TM3.1a (7)   | Specifies an E-UTRA Test Model 3.1a. |
                +--------------+--------------------------------------+
                | TM3.1b (9)   | Specifies an E-UTRA Test Model 3.1b. |
                +--------------+--------------------------------------+
                | TM3.2 (5)    | Specifies an E-UTRA Test Model 3.2.  |
                +--------------+--------------------------------------+
                | TM3.3 (6)    | Specifies an E-UTRA Test Model 3.3.  |
                +--------------+--------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            downlink_test_model = (
                downlink_test_model.value
                if type(downlink_test_model) is enums.DownlinkTestModel
                else downlink_test_model
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_downlink_test_model(
                updated_selector_string, downlink_test_model
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_emtc_analysis_enabled(self, selector_string, emtc_analysis_enabled):
        r"""Configures whether the component carrier contains an enhanced machine type communications (Cat-M1 or Cat-M2)
        transmission.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            emtc_analysis_enabled (enums.EmtcAnalysisEnabled, int):
                This parameter specifies whether the component carrier contains an eMTC transmission. The default value is **False**.

                +--------------+-----------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                           |
                +==============+=======================================================================================================================+
                | False (0)    | The measurement considers the signal as LTE FDD/TDD transmission.                                                     |
                +--------------+-----------------------------------------------------------------------------------------------------------------------+
                | True (1)     | Detects the eMTC half duplex pattern, narrow band hopping, and eMTC guard symbols present in the uplink transmission. |
                +--------------+-----------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            emtc_analysis_enabled = (
                emtc_analysis_enabled.value
                if type(emtc_analysis_enabled) is enums.EmtcAnalysisEnabled
                else emtc_analysis_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_emtc_analysis_enabled(
                updated_selector_string, emtc_analysis_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_nb_iot_component_carrier(
        self, selector_string, n_cell_id, uplink_subcarrier_spacing
    ):
        r"""Configures the Ncell ID and Uplink Subcarrier Spacing parameters for the NB-IoT signal.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            n_cell_id (int):
                This parameter specifies the narrowband physical layer cell identity. The default value is 0. Valid values are 0 to
                503, inclusive.

            uplink_subcarrier_spacing (enums.NBIoTUplinkSubcarrierSpacing, int):
                This parameter specifies the subcarrier bandwidth of an NB-IoT signal. This parameter specifies the spacing between
                adjacent subcarriers. The default value is **15 kHz**.

                +--------------+-------------------------------------+
                | Name (Value) | Description                         |
                +==============+=====================================+
                | 15 kHz (0)   | The subcarrier spacing is 15 kHz.   |
                +--------------+-------------------------------------+
                | 3.75 kHz (1) | The subcarrier spacing is 3.75 kHz. |
                +--------------+-------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            uplink_subcarrier_spacing = (
                uplink_subcarrier_spacing.value
                if type(uplink_subcarrier_spacing) is enums.NBIoTUplinkSubcarrierSpacing
                else uplink_subcarrier_spacing
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_nb_iot_component_carrier(
                updated_selector_string, n_cell_id, uplink_subcarrier_spacing
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_npusch_dmrs(
        self,
        selector_string,
        npusch_dmrs_base_sequence_mode,
        npusch_dmrs_base_sequence_index,
        npusch_dmrs_cyclic_shift,
        npusch_dmrs_group_hopping_enabled,
        npusch_dmrs_delta_ss,
    ):
        r"""Configures the base sequence mode, base sequence index, cyclic shift, delta sequence shift of the narrowband physical
        uplink shared channel (NPUSCH) DMRS and specifies whether group hopping is enabled.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            npusch_dmrs_base_sequence_mode (enums.NPuschDmrsBaseSequenceMode, int):
                This parameter specifies whether the **NPUSCH DMRS Base Sequence index** is computed by the measurement or
                user-specified. This parameter is valid when you set the **NPUSCH DMRS Group Hopping Enabled** parameter to **False**,
                the value of :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` attribute to 1, and the value of
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

                The default value is **Auto**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | Manual (0)   | The measurement uses the value that you specify for the NPUSCH DMRS Base Sequence Index parameter.                       |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Auto (1)     | The measurement uses the value of NCell ID attribute to compute the NPUSCH DMRS Base Sequence Index as defined in        |
                |              | section 10.1.4.1.2 of the 3GPP TS 36.211 specification.                                                                  |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            npusch_dmrs_base_sequence_index (int):
                This parameter specifies the base sequence index of the NPUSCH DMRS as defined in section 10.1.4.1.2 of the *3GPP TS
                36.211* specification. This parameter is valid when you set the **NPUSCH DMRS Group Hopping Enabled** parameter to
                **False**, the **NPUSCH DMRS Base Sequence Mode** parameter to **Manual**, and the value of
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.

                The default value is 0.

                - For 3 tones, valid values are 0 to 11, inclusive.

                - For 6 tones, valid values are 0 to 13, inclusive.

                - For 12 tones, valid values are 0 to 29, inclusive.

            npusch_dmrs_cyclic_shift (int):
                This parameter specifies the cyclic shift of the NPUSCH DMRS as defined in table 10.1.4.1.2-3 of the *3GPP TS 36.211*
                specification.

                This parameter is valid when you set the value of
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3 or 6. If the value of NPUSCH Num
                Tones attribute is 12, the NPUSCH DMRS Cyclic Shift parameter has a fixed value of 0.

                The default value is 0.

                - For 3 tones, valid values are 0 to 2, inclusive.

                - For 6 tones, valid values are 0 to 3, inclusive.

            npusch_dmrs_group_hopping_enabled (enums.NPuschDmrsGroupHoppingEnabled, int):
                This parameter specifies whether group hopping is enabled for the NPUSCH DMRS. This parameter is valid when the value
                of :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is equal to 1.

                The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | Group hopping is disabled.                                                                                               |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | Group hopping is enabled. The sequence group number is calculated as defined in section 10.1.4.1.3 of the 3GPP TS        |
                |              | 36.211 specification                                                                                                     |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            npusch_dmrs_delta_ss (int):
                This parameter specifies the delta sequence shift of the NPUSCH DMRS that is used to calculate the sequence shift
                pattern, which in turn is used to compute the sequence group number as defined in section 10.1.4.1.3 of the *3GPP TS
                36.211* specification. This parameter is valid when you set the **NPUSCH DMRS Group Hopping Enabled** parameter to
                **True**. The default value is 0. Valid values are 0 to 29, inclusive.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            npusch_dmrs_base_sequence_mode = (
                npusch_dmrs_base_sequence_mode.value
                if type(npusch_dmrs_base_sequence_mode) is enums.NPuschDmrsBaseSequenceMode
                else npusch_dmrs_base_sequence_mode
            )
            npusch_dmrs_group_hopping_enabled = (
                npusch_dmrs_group_hopping_enabled.value
                if type(npusch_dmrs_group_hopping_enabled) is enums.NPuschDmrsGroupHoppingEnabled
                else npusch_dmrs_group_hopping_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_npusch_dmrs(
                updated_selector_string,
                npusch_dmrs_base_sequence_mode,
                npusch_dmrs_base_sequence_index,
                npusch_dmrs_cyclic_shift,
                npusch_dmrs_group_hopping_enabled,
                npusch_dmrs_delta_ss,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_npusch_format(self, selector_string, format):
        r"""Configures the format of the narrowband physical uplink shared channel (NPUSCH).

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            format (int):
                This parameter specifies the NPUSCH format. A value of 1 indicates that NPUSCH carries user data (UL-SCH) and a value
                of 2 indicates, NPUSCH carries uplink control information. The default value is 1.

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
            error_code = self._interpreter.configure_npusch_format(updated_selector_string, format)
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_npusch_starting_slot(self, selector_string, starting_slot):
        r"""Configures the starting slot of the NPUSCH burst.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            starting_slot (int):
                This parameter specifies the starting slot number of the NPUSCH burst. The default value is 0.

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
            error_code = self._interpreter.configure_npusch_starting_slot(
                updated_selector_string, starting_slot
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_npusch_tones(
        self, selector_string, tone_offset, number_of_tones, modulation_type
    ):
        r"""Configures the values of **Tone Offset**, **Number of Tones**, and **Modulation Type** parameters for NPUSCH channel.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            tone_offset (int):
                This parameter specifies the location of the starting subcarrier (tone) within the 200 kHz bandwidth that is allocated
                to the NPUSCH channel. The default value is 0.

                For 15 kHz subcarrier spacing, the valid values are as follows:

                - for 1 tones, 0 to 11, inclusive

                - for 3 tones, 0, 3, 6, and 9

                - for 6 tones, 0 and 6

                - for 12 tones, 0

                For 3.75 kHz subcarrier spacing, the valid values are 0 to 47, inclusive.

            number_of_tones (int):
                This parameter specifies the number of subcarriers (tones) within the 200 kHz bandwidth that is allocated to the NPUSCH
                channel.

                The default value is 1.

                For Format 1 and 15 kHz subcarrier spacing, the valid values are 1, 3, 6, and 12.

                For Format 1, 3.75 kHz subcarrier spacing, and Format 2, the valid value is 1.

            modulation_type (enums.NPuschModulationType, int):
                This parameter specifies the modulation type that is used by the NPUSCH channel. The default value is **BPSK**.

                This parameter is valid when **Number of Tones** is equal to 1 and
                :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is equal to 1. The modulation type for other configurations
                is defined in Table 10.1.3.2-1 of the *3GPP TS 36.211* specification.

                +--------------+-------------------------------------+
                | Name (Value) | Description                         |
                +==============+=====================================+
                | BPSK (0)     | Specifies a BPSK modulation scheme. |
                +--------------+-------------------------------------+
                | QPSK (1)     | Specifies a QPSK modulation scheme. |
                +--------------+-------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            modulation_type = (
                modulation_type.value
                if type(modulation_type) is enums.NPuschModulationType
                else modulation_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_npusch_tones(
                updated_selector_string, tone_offset, number_of_tones, modulation_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_pdsch_channels(self, selector_string, number_of_pdsch_channels):
        r"""Configures the number of different physical downlink shared channel (PDSCH) allocations in a subframe.

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, carrier number, and subframe number.

                Example:

                "subblock0/carrier0/subframe0"

                You can use the :py:meth:`build_subframe_string` method to build the selector string.

            number_of_pdsch_channels (int):
                This parameter specifies the number of PDSCH allocations in a subframe. The default value is 1. Valid values are 0 to
                100, inclusive.

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
            error_code = self._interpreter.configure_number_of_pdsch_channels(
                updated_selector_string, number_of_pdsch_channels
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_pusch_resource_block_clusters(
        self, selector_string, number_of_resource_block_clusters
    ):
        r"""Configures the number of clusters of resource allocations.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            number_of_resource_block_clusters (int):
                This parameter specifies the number resource allocation clusters, with each cluster including one or more consecutive
                resource blocks. For more information about the physical uplink shared channel (PUSCH) number of clusters, refer to
                5.5.2.1.1 of the *3GPP TS 36.213* specification. The default value is 1.

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
            error_code = self._interpreter.configure_number_of_pusch_resource_block_clusters(
                updated_selector_string, number_of_resource_block_clusters
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_pbch(self, selector_string, pbch_power):
        r"""Configures the power of physical broadcast channel (PBCH) power relative to the cell-specific reference signal.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            pbch_power (float):
                This parameter specifies the power of the PBCH relative to the power of the cell-specific reference signal. This value
                is expressed in dB. The default value is 0.

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
            error_code = self._interpreter.configure_pbch(updated_selector_string, pbch_power)
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_pcfich(self, selector_string, cfi, power):
        r"""Configures the **CFI** and **Power** parameters of the physical control format indicator channel (PCFICH).

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, carrier number, and subframe number.

                Example:

                "subblock0/carrier0/subframe0"

                You can use the :py:meth:`build_subframe_string` method to build the selector string.

            cfi (int):
                This parameter specifies the control format indicator (CFI) carried by PCFICH. CFI is used to compute the number of
                OFDM symbols which will determine the size of physical downlink control channel (PDCCH) within a subframe. The default
                value is 1.

            power (float):
                This parameter specifies the power of the PCFICH relative to the power of the cell-specific reference signal. This
                value is expressed in dB. The default value is 0.

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
            error_code = self._interpreter.configure_pcfich(updated_selector_string, cfi, power)
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_pdcch(self, selector_string, pdcch_power):
        r"""Configures the physical downlink control channel (PDCCH) power relative to the cell-specific reference signal.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            pdcch_power (float):
                This parameter specifies the power of the PDCCH relative to the power of the cell-specific reference signal. This value
                is expressed in dB. The default value is 0.

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
            error_code = self._interpreter.configure_pdcch(updated_selector_string, pdcch_power)
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_pdsch(
        self, selector_string, cw0_modulation_type, resource_block_allocation, power
    ):
        r"""Configures the codeword0 modulation type, resource block, and relative power of a physical downlink shared channel
        (PDSCH) allocation.
        
        Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>" as the selector string to configure this method.
        
        Args:
            selector_string (string): 
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, carrier number, subframe number, and PDSCH number.
                
                Example:
                
                "subblock0/carrier0/subframe0/PDSCH0"
                
                You can use the :py:meth:`build_pdsch_string` method to build the selector string.
                
            cw0_modulation_type (enums.UserDefinedPdschCW0ModulationType, int): 
                This parameter specifies the modulation type of Codeword0 PDSCH allocation. The default value is **QPSK**.
                
                +--------------+-----------------------------------------+
                | Name (Value) | Description                             |
                +==============+=========================================+
                | QPSK (0)     | Specifies a QPSK modulation scheme.     |
                +--------------+-----------------------------------------+
                | 16 QAM (1)   | Specifies a 16-QAM modulation scheme.   |
                +--------------+-----------------------------------------+
                | 64 QAM (2)   | Specifies a 64-QAM modulation scheme.   |
                +--------------+-----------------------------------------+
                | 256 QAM (3)  | Specifies a 256-QAM modulation scheme.  |
                +--------------+-----------------------------------------+
                | 1024 QAM (4) | Specifies a 1024-QAM modulation scheme. |
                +--------------+-----------------------------------------+
                
            resource_block_allocation (string): 
                This parameter specifies the resource blocks of the PDSCH allocation. The default value is 0 - 49.
                
                The following string formats are supported for this parameter:
                
                1) *RB*
                \ :sub:`StartValue1`\-*RB*
                \ :sub:`StopValue1`\,*RB*
                \ :sub:`StartValue2`\-*RB*
                \ :sub:`StopValue2`\
                
                2) *RB*
                \ :sub:`1`\,*RB*
                \ :sub:`2`\
                
                3) *RB*
                \ :sub:`StartValue1`\-*RB*
                \ :sub:`StopValue1`\, *RB*
                \ :sub:`1`\,*RB*
                \ :sub:`StartValue2`\-*RB*
                \ :sub:`StopValue2`\,*RB*
                \ :sub:`2`\
                
                For example: If the RB allocation is 0-5,7,8,10-15, the RB allocation string specifies contiguous resource
                blocks from 0 to 5, resource block 7, resource block 8, and contiguous resource blocks from 10 to 15.
                
            power (float): 
                This parameter specifies the PDSCH power level (P\ :sub:`a`\) relative to the power of the cell-specific reference
                signal. This value is expressed in dB. Measurement uses the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO` attribute to calculate P\
                :sub:`b`\.
                Refer to section 3.3 of the *3GPP 36.521* specifications for more information about P\ :sub:`a`\. The default value
                is 0.
                
        Returns: 
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            cw0_modulation_type = (
                cw0_modulation_type.value
                if type(cw0_modulation_type) is enums.UserDefinedPdschCW0ModulationType
                else cw0_modulation_type
            )
            _helper.validate_not_none(resource_block_allocation, "resource_block_allocation")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_pdsch(
                updated_selector_string, cw0_modulation_type, resource_block_allocation, power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_phich(self, selector_string, resource, duration, power):
        r"""Configures the **Resource**, **Duration**, and **Power** parameters of the physical hybrid-ARQ indicator channel
        (PHICH).

        Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
        selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, carrier number, and subframe number.

                Example:

                "subblock0/carrier0/subframe0"

                You can use the :py:meth:`build_subframe_string` method to build the selector string.

            resource (enums.DownlinkUserDefinedPhichResource, int):
                This parameter specifies the PHICH resource value. This value is expressed in Ng. This parameter is used to calculate
                number of PHICH resource groups. Refer to section 6.9 of the *3GPP 36.211* specification for more information about
                PHICH. The default value is **1/6**.

                +--------------+-------------------------------------------------+
                | Name (Value) | Description                                     |
                +==============+=================================================+
                | 1/6 (0)      | Specifies that the PHICH resource value is 1/6. |
                +--------------+-------------------------------------------------+
                | 1/2 (1)      | Specifies that the PHICH resource value is 1/2. |
                +--------------+-------------------------------------------------+
                | 1 (2)        | Specifies that the PHICH resource value is 1.   |
                +--------------+-------------------------------------------------+
                | 2 (3)        | Specifies that the PHICH resource value is 2.   |
                +--------------+-------------------------------------------------+

            duration (enums.DownlinkUserDefinedPhichDuration, int):
                This parameter specifies the PHICH duration. The default value is **Normal**.

                +--------------+------------------------------------------------------------+
                | Name (Value) | Description                                                |
                +==============+============================================================+
                | Normal (0)   | Orthogonal sequences of length 4 is used to extract PHICH. |
                +--------------+------------------------------------------------------------+

            power (float):
                This parameter specifies the power of all BPSK symbols in a PHICH sequence. This value is expressed in dB. The default
                value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            resource = (
                resource.value
                if type(resource) is enums.DownlinkUserDefinedPhichResource
                else resource
            )
            duration = (
                duration.value
                if type(duration) is enums.DownlinkUserDefinedPhichDuration
                else duration
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_phich(
                updated_selector_string, resource, duration, power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_pssch_modulation_type(self, selector_string, modulation_type):
        r"""Configures the modulation scheme used in the physical sidelink shared channel (PSSCH) of the signal being measured.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            modulation_type (enums.PsschModulationType, int):
                This parameter specifies the modulation scheme used in the PSSCH channel of the signal being measured. The default
                value is **QPSK**.

                +--------------+---------------------------------------+
                | Name (Value) | Description                           |
                +==============+=======================================+
                | QPSK (0)     | Specifies a QPSK modulation scheme.   |
                +--------------+---------------------------------------+
                | 16 QAM (1)   | Specifies a 16-QAM modulation scheme. |
                +--------------+---------------------------------------+
                | 64 QAM (2)   | Specifies a 64-QAM modulation scheme. |
                +--------------+---------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            modulation_type = (
                modulation_type.value
                if type(modulation_type) is enums.PsschModulationType
                else modulation_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_pssch_modulation_type(
                updated_selector_string, modulation_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_pssch_resource_blocks(
        self, selector_string, resource_block_offset, number_of_resource_blocks
    ):
        r"""Configures the start and number of resource blocks allocated for the physical sidelink shared channel (PSSCH)
        allocation.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            resource_block_offset (int):
                This parameter specifies the starting resource block number of the PSSCH allocation. The default value is 0.

            number_of_resource_blocks (int):
                This parameter specifies the number of consecutive resource blocks in the PSSCH allocation. The default value is -1. If
                you set this parameter to -1, all available resource blocks for the specified bandwidth are configured.

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
            error_code = self._interpreter.configure_pssch_resource_blocks(
                updated_selector_string, resource_block_offset, number_of_resource_blocks
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_pusch_modulation_type(self, selector_string, modulation_type):
        r"""Configures the modulation scheme used in the physical uplink shared channel (PUSCH) channel of the signal being
        measured.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            modulation_type (enums.PuschModulationType, int):
                This parameter specifies the modulation scheme used in the PUSCH channel of the signal being measured.
                The default value is **QPSK**.

                +--------------+-----------------------------------------+
                | Name (Value) | Description                             |
                +==============+=========================================+
                | QPSK (0)     | Specifies a QPSK modulation scheme.     |
                +--------------+-----------------------------------------+
                | 16 QAM (1)   | Specifies a 16-QAM modulation scheme.   |
                +--------------+-----------------------------------------+
                | 64 QAM (2)   | Specifies a 64-QAM modulation scheme.   |
                +--------------+-----------------------------------------+
                | 256 QAM (3)  | Specifies a 256-QAM modulation scheme.  |
                +--------------+-----------------------------------------+
                | 1024 QAM (4) | Specifies a 1024-QAM modulation scheme. |
                +--------------+-----------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            modulation_type = (
                modulation_type.value
                if type(modulation_type) is enums.PuschModulationType
                else modulation_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_pusch_modulation_type(
                updated_selector_string, modulation_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_pusch_resource_blocks(
        self, selector_string, resource_block_offset, number_of_resource_blocks
    ):
        r"""Configures the start and number of resource blocks allocated for the physical uplink shared channel (PUSCH) cluster.

        Use "cluster<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>/cluster<*l*>" as the selector string to
        configure this result.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, carrier number, and the cluster number.  The default is "" (empty string).

                Example:

                "subblock0/carrier0/cluster0"

                You can use the :py:meth:`build_cluster_string` method to build the selector string.

            resource_block_offset (int):
                This parameter specifies the starting resource block number of a PUSCH cluster. The default value is 0.

            number_of_resource_blocks (int):
                This parameter specifies the number of consecutive resource blocks in a PUSCH cluster.  The default value is -1. If you
                set this parameter to -1, all available resource blocks for the specified bandwidth are configured.

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
            error_code = self._interpreter.configure_pusch_resource_blocks(
                updated_selector_string, resource_block_offset, number_of_resource_blocks
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_downlink_auto_channel_detection(
        self,
        selector_string,
        auto_pdsch_channel_detection_enabled,
        auto_control_channel_power_detection_enabled,
        auto_pcfich_cfi_detection_enabled,
    ):
        r"""Configures whether the values of physical downlink shared channel (PDSCH) parameters, control channel signal powers,
        and physical control format indicator channel (PCFICH) CFI are configured by a user or auto-detected by the
        measurement. The measurement ignores this method, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            auto_pdsch_channel_detection_enabled (enums.AutoPdschChannelDetectionEnabled, int):
                This parameter specifies whether the values of the
                :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_RESOURCE_BLOCK_ALLOCATION` attribute, the corresponding
                :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_CW0_MODULATION_TYPE` attribute, and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_POWER` attribute are
                auto-detected by the measurement or user-specified.

                This parameter is not valid, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The value of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation Type, and the PDSCH     |
                |              | Power attribute that you specify are used for the measurement.                                                           |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The value of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation Type, and the PDSCH     |
                |              | Power attribute are auto-detected and used for the measurement.                                                          |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            auto_control_channel_power_detection_enabled (enums.AutoControlChannelPowerDetectionEnabled, int):
                This parameter specifies whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PSS_POWER`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.SSS_POWER`, :py:attr:`~nirfmxlte.attributes.AttributeID.PBCH_POWER`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PDCCH_POWER`, and :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_POWER`
                attributes are
                auto-detected by the measurement or user-specified. Currently, auto-detection of
                :py:attr:`~nirfmxlte.attributes.AttributeID.PHICH_POWER` attribute is not supported.

                This parameter is not valid, when you set the DL Ch Configuration Mode attribute to **Test Model**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, PHICH Power, and PCFICH Power attributes that you        |
                |              | specify are used for the measurement.                                                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, and PCFICH Power attributes are auto-detected and used   |
                |              | for the measurement.                                                                                                     |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            auto_pcfich_cfi_detection_enabled (enums.AutoPcfichCfiDetectionEnabled, int):
                This parameter specifies whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_CFI` attribute is
                auto-detected by the measurement or user-specified.

                This parameter is not valid, when you set the DL Ch Configuration Mode attribute to **Test Model**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The value of PCFICH CFI attribute that you specify is used for the measurement.                                          |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The value of PCFICH CFI attribute is auto-detected and used for the measurement. This value is obtained by decoding the  |
                |              | PCFICH channel.                                                                                                          |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            auto_pdsch_channel_detection_enabled = (
                auto_pdsch_channel_detection_enabled.value
                if type(auto_pdsch_channel_detection_enabled)
                is enums.AutoPdschChannelDetectionEnabled
                else auto_pdsch_channel_detection_enabled
            )
            auto_control_channel_power_detection_enabled = (
                auto_control_channel_power_detection_enabled.value
                if type(auto_control_channel_power_detection_enabled)
                is enums.AutoControlChannelPowerDetectionEnabled
                else auto_control_channel_power_detection_enabled
            )
            auto_pcfich_cfi_detection_enabled = (
                auto_pcfich_cfi_detection_enabled.value
                if type(auto_pcfich_cfi_detection_enabled) is enums.AutoPcfichCfiDetectionEnabled
                else auto_pcfich_cfi_detection_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.configure_downlink_auto_channel_detection(
                updated_selector_string,
                auto_pdsch_channel_detection_enabled,
                auto_control_channel_power_detection_enabled,
                auto_pcfich_cfi_detection_enabled,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
