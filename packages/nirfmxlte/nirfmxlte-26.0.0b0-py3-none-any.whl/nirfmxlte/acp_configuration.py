"""Provides methods to configure the Acp measurement."""

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


class AcpConfiguration(object):
    """Provides methods to configure the Acp measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the Acp measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the ACP measurement.

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
                Specifies whether to enable the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the ACP measurement.

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
                attributes.AttributeID.ACP_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subblock_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of the subblock. This value is expressed in Hz. Integration bandwidth is the span
        from the left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock.

        Use "subblock<*n*>" as the selector string to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the integration bandwidth of the subblock. This value is expressed in Hz. Integration bandwidth is the span
                from the left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock.

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
                attributes.AttributeID.ACP_SUBBLOCK_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of the component carrier (CC). This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        The default value is 9 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the integration bandwidth of the component carrier (CC). This value is expressed in Hz.

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
                attributes.AttributeID.ACP_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_configurable_number_of_offsets_enabled(self, selector_string):
        r"""Gets whether the number of offsets is computed by measurement or configured by you.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        When the carrier bandwidth is 200 kHz or the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` is
        **Downlink**, the default value is **False**. The default value is **True**, otherwise.

        .. note::
           In case of downlink, this attribute is valid only for number of E-UTRA offsets. For the number of UTRA offsets, only
           3GPP specification defined values are supported.

        +--------------+-----------------------------------------------------------------------+
        | Name (Value) | Description                                                           |
        +==============+=======================================================================+
        | False (0)    | Measurement will set the number of offsets.                           |
        +--------------+-----------------------------------------------------------------------+
        | True (1)     | Measurement will use the user configured value for number of offsets. |
        +--------------+-----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpConfigurableNumberOfOffsetsEnabled):
                Specifies whether the number of offsets is computed by measurement or configured by you.

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
                attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED.value,
            )
            attr_val = enums.AcpConfigurableNumberOfOffsetsEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_configurable_number_of_offsets_enabled(self, selector_string, value):
        r"""Sets whether the number of offsets is computed by measurement or configured by you.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        When the carrier bandwidth is 200 kHz or the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` is
        **Downlink**, the default value is **False**. The default value is **True**, otherwise.

        .. note::
           In case of downlink, this attribute is valid only for number of E-UTRA offsets. For the number of UTRA offsets, only
           3GPP specification defined values are supported.

        +--------------+-----------------------------------------------------------------------+
        | Name (Value) | Description                                                           |
        +==============+=======================================================================+
        | False (0)    | Measurement will set the number of offsets.                           |
        +--------------+-----------------------------------------------------------------------+
        | True (1)     | Measurement will use the user configured value for number of offsets. |
        +--------------+-----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpConfigurableNumberOfOffsetsEnabled, int):
                Specifies whether the number of offsets is computed by measurement or configured by you.

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
                value.value if type(value) is enums.AcpConfigurableNumberOfOffsetsEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_utra_offsets(self, selector_string):
        r"""Gets the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
        positions, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED`
        attribute to **True**.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` to **Uplink**.

        The default value is 0, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` to **Downlink**.

        The default value is 0, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.BAND` attribute to 46 or
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute to **LAA**.

        The default value is 2 for all other configurations.

        .. note::
           In case of downlink, only 3GPP specification defined values are supported. In case of non-contiguous carrier
           aggregation, the configured value will be used only for the outer offsets and the offset channels in the gap region are
           defined as per the 3GPP specification. Offset power reference for the outer UTRA offsets are set according to the value
           of :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
                positions, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED`
                attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_UTRA_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_utra_offsets(self, selector_string, value):
        r"""Sets the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
        positions, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED`
        attribute to **True**.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` to **Uplink**.

        The default value is 0, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` to **Downlink**.

        The default value is 0, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.BAND` attribute to 46 or
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute to **LAA**.

        The default value is 2 for all other configurations.

        .. note::
           In case of downlink, only 3GPP specification defined values are supported. In case of non-contiguous carrier
           aggregation, the configured value will be used only for the outer offsets and the offset channels in the gap region are
           defined as per the 3GPP specification. Offset power reference for the outer UTRA offsets are set according to the value
           of :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
                positions, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED`
                attribute to **True**.

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
                attributes.AttributeID.ACP_NUMBER_OF_UTRA_OFFSETS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_eutra_offsets(self, selector_string):
        r"""Gets the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
        at offset positions, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 0, when carrier bandwidth is 200 kHz. The default value is 2 for downlink and 1 for
        uplink, otherwise.

        .. note::
           In case of non-contiguous carrier aggregation, the configured value will be used only for the outer offsets and the
           offset channels in the gap region are defined as per the 3GPP specification. Offset integration bandwidth and offset
           power reference for the outer E-UTRA offsets are set according to the value of
           :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
                at offset positions, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_EUTRA_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_eutra_offsets(self, selector_string, value):
        r"""Sets the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
        at offset positions, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 0, when carrier bandwidth is 200 kHz. The default value is 2 for downlink and 1 for
        uplink, otherwise.

        .. note::
           In case of non-contiguous carrier aggregation, the configured value will be used only for the outer offsets and the
           offset channels in the gap region are defined as per the 3GPP specification. Offset integration bandwidth and offset
           power reference for the outer E-UTRA offsets are set according to the value of
           :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
                at offset positions, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

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
                attributes.AttributeID.ACP_NUMBER_OF_EUTRA_OFFSETS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_eutra_offset_definition(self, selector_string):
        r"""Gets the evolved universal terrestrial radio access (E-UTRA) offset channel definition.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        .. note::
           In case of non-contiguous, the inner offset channel definition will be configured internally as per the 3GPP
           specification. Offset power reference for the outer UTRA offsets are set according to ACP EUTRA Offset Definition
           attribute.

        The default value is **Auto**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | Auto (0)      | Measurement will set the E-UTRA definition and offset power reference based on the link direction. For downlink, the     |
        |               | definition is Closest and for uplink, it is Composite.                                                                   |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Closest (1)   | Integration bandwidth is derived from the closest LTE carrier. Offset power reference is set to Closest internally.      |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Composite (2) | Integration bandwidth is derived from the aggregated sub-block bandwidth. Offset power reference is set as Composite     |
        |               | Sub-Block.                                                                                                               |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpEutraOffsetDefinition):
                Specifies the evolved universal terrestrial radio access (E-UTRA) offset channel definition.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION.value
            )
            attr_val = enums.AcpEutraOffsetDefinition(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_eutra_offset_definition(self, selector_string, value):
        r"""Sets the evolved universal terrestrial radio access (E-UTRA) offset channel definition.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        .. note::
           In case of non-contiguous, the inner offset channel definition will be configured internally as per the 3GPP
           specification. Offset power reference for the outer UTRA offsets are set according to ACP EUTRA Offset Definition
           attribute.

        The default value is **Auto**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | Auto (0)      | Measurement will set the E-UTRA definition and offset power reference based on the link direction. For downlink, the     |
        |               | definition is Closest and for uplink, it is Composite.                                                                   |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Closest (1)   | Integration bandwidth is derived from the closest LTE carrier. Offset power reference is set to Closest internally.      |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Composite (2) | Integration bandwidth is derived from the aggregated sub-block bandwidth. Offset power reference is set as Composite     |
        |               | Sub-Block.                                                                                                               |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpEutraOffsetDefinition, int):
                Specifies the evolved universal terrestrial radio access (E-UTRA) offset channel definition.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpEutraOffsetDefinition else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_gsm_offsets(self, selector_string):
        r"""Gets the number of GSM adjacent channel offsets to be configured when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

        The frequency offset from the center of NB-IOT carrier to the center of the first offset is 300 kHz as defined
        in the 3GPP specification. The center of every other offset is placed at 200 kHz from the previous offset's center.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1, when you set the CC Bandwidth attribute to is **200.0 k** and Link Direction to
        **Uplink**. The default value is 0, otherwise.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of GSM adjacent channel offsets to be configured when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_GSM_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_gsm_offsets(self, selector_string, value):
        r"""Sets the number of GSM adjacent channel offsets to be configured when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

        The frequency offset from the center of NB-IOT carrier to the center of the first offset is 300 kHz as defined
        in the 3GPP specification. The center of every other offset is placed at 200 kHz from the previous offset's center.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1, when you set the CC Bandwidth attribute to is **200.0 k** and Link Direction to
        **Uplink**. The default value is 0, otherwise.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of GSM adjacent channel offsets to be configured when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

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
                attributes.AttributeID.ACP_NUMBER_OF_GSM_OFFSETS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_frequency(self, selector_string):
        r"""Gets the offset frequency of an offset channel. This value is expressed in Hz. When you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Uplink**, the offset frequency is computed
        from the center of a reference component carrier/subblock to the center of the nearest RBW filter of the offset
        channel.
        When you set the Link Direction attribute to **Downlink**, the offset frequency is computed from the center of
        the closest component carrier to the center of the nearest RBW filter of the offset channel.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        The default value is 10 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset frequency of an offset channel. This value is expressed in Hz. When you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Uplink**, the offset frequency is computed
                from the center of a reference component carrier/subblock to the center of the nearest RBW filter of the offset
                channel.
                When you set the Link Direction attribute to **Downlink**, the offset frequency is computed from the center of
                the closest component carrier to the center of the nearest RBW filter of the offset channel.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_OFFSET_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_offset_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of an offset carrier. This value is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.

        The default value is 9 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the integration bandwidth of an offset carrier. This value is expressed in Hz.

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
                attributes.AttributeID.ACP_OFFSET_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rbw_filter_auto_bandwidth(self, selector_string):
        r"""Gets whether the measurement computes the RBW.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | False (0)    | The measurement uses the RBW that you specify in the ACP RBW attribute. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | The measurement computes the RBW.                                       |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpRbwAutoBandwidth):
                Specifies whether the measurement computes the RBW.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH.value
            )
            attr_val = enums.AcpRbwAutoBandwidth(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_auto_bandwidth(self, selector_string, value):
        r"""Sets whether the measurement computes the RBW.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | False (0)    | The measurement uses the RBW that you specify in the ACP RBW attribute. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | The measurement computes the RBW.                                       |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpRbwAutoBandwidth, int):
                Specifies whether the measurement computes the RBW.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpRbwAutoBandwidth else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rbw_filter_bandwidth(self, selector_string):
        r"""Gets the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
        expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30000.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
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
                updated_selector_string, attributes.AttributeID.ACP_RBW_FILTER_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_bandwidth(self, selector_string, value):
        r"""Sets the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
        expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30000.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
                expressed in Hz.

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
                attributes.AttributeID.ACP_RBW_FILTER_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rbw_filter_type(self, selector_string):
        r"""Gets the shape of the RBW filter.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **FFT Based**.

        +---------------+----------------------------------------------------+
        | Name (Value)  | Description                                        |
        +===============+====================================================+
        | FFT Based (0) | No RBW filtering is performed.                     |
        +---------------+----------------------------------------------------+
        | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
        +---------------+----------------------------------------------------+
        | Flat (2)      | An RBW filter with a flat response is applied.     |
        +---------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpRbwFilterType):
                Specifies the shape of the RBW filter.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_RBW_FILTER_TYPE.value
            )
            attr_val = enums.AcpRbwFilterType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_type(self, selector_string, value):
        r"""Sets the shape of the RBW filter.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **FFT Based**.

        +---------------+----------------------------------------------------+
        | Name (Value)  | Description                                        |
        +===============+====================================================+
        | FFT Based (0) | No RBW filtering is performed.                     |
        +---------------+----------------------------------------------------+
        | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
        +---------------+----------------------------------------------------+
        | Flat (2)      | An RBW filter with a flat response is applied.     |
        +---------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpRbwFilterType, int):
                Specifies the shape of the RBW filter.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpRbwFilterType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_RBW_FILTER_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sweep_time_auto(self, selector_string):
        r"""Gets whether the measurement computes the sweep time.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                           |
        +==============+=======================================================================================+
        | False (0)    | The measurement uses the sweep time that you specify in the ACP Sweep Time attribute. |
        +--------------+---------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpSweepTimeAuto):
                Specifies whether the measurement computes the sweep time.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_SWEEP_TIME_AUTO.value
            )
            attr_val = enums.AcpSweepTimeAuto(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sweep_time_auto(self, selector_string, value):
        r"""Sets whether the measurement computes the sweep time.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                           |
        +==============+=======================================================================================+
        | False (0)    | The measurement uses the sweep time that you specify in the ACP Sweep Time attribute. |
        +--------------+---------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpSweepTimeAuto, int):
                Specifies whether the measurement computes the sweep time.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpSweepTimeAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_SWEEP_TIME_AUTO.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sweep_time_interval(self, selector_string):
        r"""Gets the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
        **False**. This value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 ms.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
                **False**. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_SWEEP_TIME_INTERVAL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sweep_time_interval(self, selector_string, value):
        r"""Sets the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
        **False**. This value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 ms.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
                **False**. This value is expressed in seconds.

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
                updated_selector_string, attributes.AttributeID.ACP_SWEEP_TIME_INTERVAL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_units(self, selector_string):
        r"""Gets the units for absolute power.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **dBm**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | dBm (0)      | The absolute powers are reported in dBm.    |
        +--------------+---------------------------------------------+
        | dBm/Hz (1)   | The absolute powers are reported in dBm/Hz. |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpPowerUnits):
                Specifies the units for absolute power.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_POWER_UNITS.value
            )
            attr_val = enums.AcpPowerUnits(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_units(self, selector_string, value):
        r"""Sets the units for absolute power.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **dBm**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | dBm (0)      | The absolute powers are reported in dBm.    |
        +--------------+---------------------------------------------+
        | dBm/Hz (1)   | The absolute powers are reported in dBm/Hz. |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpPowerUnits, int):
                Specifies the units for absolute power.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpPowerUnits else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_POWER_UNITS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_method(self, selector_string):
        r"""Gets the method for performing the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)       | Description                                                                                                              |
        +====================+==========================================================================================================================+
        | Normal (0)         | The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this        |
        |                    | method when measurement speed is desirable over higher dynamic range.                                                    |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Dynamic Range (1)  | The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use   |
        |                    | this method to get the best dynamic range. Supported Devices: PXIe-5665/5668                                             |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Sequential FFT (2) | The ACP measurement acquires all the samples specified by the ACP Sweep Time attribute and divides them in to smaller    |
        |                    | chunks of equal size defined by the ACP Sequential FFT Size attribute.                                                   |
        |                    | FFT is computed for each chunk. The resultant FFTs are averaged to get the spectrum used to compute the ACP.             |
        |                    | If the total acquired samples is not an integer multiple of the FFT size, the remaining samples at the end of the        |
        |                    | acquisition are not used.                                                                                                |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpMeasurementMethod):
                Specifies the method for performing the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_METHOD.value
            )
            attr_val = enums.AcpMeasurementMethod(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_method(self, selector_string, value):
        r"""Sets the method for performing the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)       | Description                                                                                                              |
        +====================+==========================================================================================================================+
        | Normal (0)         | The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this        |
        |                    | method when measurement speed is desirable over higher dynamic range.                                                    |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Dynamic Range (1)  | The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use   |
        |                    | this method to get the best dynamic range. Supported Devices: PXIe-5665/5668                                             |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Sequential FFT (2) | The ACP measurement acquires all the samples specified by the ACP Sweep Time attribute and divides them in to smaller    |
        |                    | chunks of equal size defined by the ACP Sequential FFT Size attribute.                                                   |
        |                    | FFT is computed for each chunk. The resultant FFTs are averaged to get the spectrum used to compute the ACP.             |
        |                    | If the total acquired samples is not an integer multiple of the FFT size, the remaining samples at the end of the        |
        |                    | acquisition are not used.                                                                                                |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpMeasurementMethod, int):
                Specifies the method for performing the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpMeasurementMethod else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_METHOD.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_calibration_mode(self, selector_string):
        r"""Gets whether the noise calibration and measurement is performed automatically by the measurement or by you.  Refer
        to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | When you set the ACP Meas Mode attribute to Calibrate Noise Floor, you can initiate instrument noise calibration for     |
        |              | ACP measurement manually. When you set the ACP Meas Mode attribute to Measure, you can initiate the ACP measurement      |
        |              | manually.                                                                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | When you set the ACP Noise Comp Enabled attribute to True, RFmx sets the Input Isolation Enabled attribute to Enabled    |
        |              | and calibrates the instrument noise in the current state of the instrument. RFmx then resets Input Isolation Enabled     |
        |              | attribute and performs the ACP measurement including compensation for the noise contribution of the instrument. RFmx     |
        |              | skips noise calibration in this mode if valid noise calibration data is already cached.                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpNoiseCalibrationMode):
                Specifies whether the noise calibration and measurement is performed automatically by the measurement or by you.  Refer
                to the measurement guidelines section in the `Noise Compensation Algorithm
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE.value
            )
            attr_val = enums.AcpNoiseCalibrationMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_calibration_mode(self, selector_string, value):
        r"""Sets whether the noise calibration and measurement is performed automatically by the measurement or by you.  Refer
        to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | When you set the ACP Meas Mode attribute to Calibrate Noise Floor, you can initiate instrument noise calibration for     |
        |              | ACP measurement manually. When you set the ACP Meas Mode attribute to Measure, you can initiate the ACP measurement      |
        |              | manually.                                                                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | When you set the ACP Noise Comp Enabled attribute to True, RFmx sets the Input Isolation Enabled attribute to Enabled    |
        |              | and calibrates the instrument noise in the current state of the instrument. RFmx then resets Input Isolation Enabled     |
        |              | attribute and performs the ACP measurement including compensation for the noise contribution of the instrument. RFmx     |
        |              | skips noise calibration in this mode if valid noise calibration data is already cached.                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpNoiseCalibrationMode, int):
                Specifies whether the noise calibration and measurement is performed automatically by the measurement or by you.  Refer
                to the measurement guidelines section in the `Noise Compensation Algorithm
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpNoiseCalibrationMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_calibration_averaging_auto(self, selector_string):
        r"""Gets whether RFmx automatically computes the averaging count used for instrument noise calibration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | RFmx uses the averages that you set for ACP Noise Cal Averaging Count attribute. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | RFmx uses the following averaging counts:                                        |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpNoiseCalibrationAveragingAuto):
                Specifies whether RFmx automatically computes the averaging count used for instrument noise calibration.

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
                attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO.value,
            )
            attr_val = enums.AcpNoiseCalibrationAveragingAuto(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_calibration_averaging_auto(self, selector_string, value):
        r"""Sets whether RFmx automatically computes the averaging count used for instrument noise calibration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | RFmx uses the averages that you set for ACP Noise Cal Averaging Count attribute. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | RFmx uses the following averaging counts:                                        |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpNoiseCalibrationAveragingAuto, int):
                Specifies whether RFmx automatically computes the averaging count used for instrument noise calibration.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpNoiseCalibrationAveragingAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_calibration_averaging_count(self, selector_string):
        r"""Gets the averaging count used for noise calibration when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 32.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the averaging count used for noise calibration when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

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
                attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_COUNT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_calibration_averaging_count(self, selector_string, value):
        r"""Sets the averaging count used for noise calibration when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 32.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the averaging count used for noise calibration when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

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
                attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_COUNT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_enabled(self, selector_string):
        r"""Gets whether RFmx compensates for the instrument noise while performing the measurement when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set the ACP
        Noise Cal Mode attribute to **Manual** and the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_MODE`
        attribute to **Measure**. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Disables compensation of the channel powers for the noise floor of the signal analyzer.                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Enables compensation of the channel powers for the noise floor of the signal analyzer. The noise floor of the signal     |
        |              | analyzer is measured for the RF path used by the ACP measurement and cached for future use. If the signal analyzer or    |
        |              | the measurement parameters change, noise floors are remeasured.                                                          |
        |              | Supported Devices: PXIe-5663/5665/5668, PXIe-5830/5831/5832/5842/5860                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpNoiseCompensationEnabled):
                Specifies whether RFmx compensates for the instrument noise while performing the measurement when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set the ACP
                Noise Cal Mode attribute to **Manual** and the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_MODE`
                attribute to **Measure**. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NOISE_COMPENSATION_ENABLED.value
            )
            attr_val = enums.AcpNoiseCompensationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_enabled(self, selector_string, value):
        r"""Sets whether RFmx compensates for the instrument noise while performing the measurement when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set the ACP
        Noise Cal Mode attribute to **Manual** and the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_MODE`
        attribute to **Measure**. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Disables compensation of the channel powers for the noise floor of the signal analyzer.                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Enables compensation of the channel powers for the noise floor of the signal analyzer. The noise floor of the signal     |
        |              | analyzer is measured for the RF path used by the ACP measurement and cached for future use. If the signal analyzer or    |
        |              | the measurement parameters change, noise floors are remeasured.                                                          |
        |              | Supported Devices: PXIe-5663/5665/5668, PXIe-5830/5831/5832/5842/5860                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpNoiseCompensationEnabled, int):
                Specifies whether RFmx compensates for the instrument noise while performing the measurement when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set the ACP
                Noise Cal Mode attribute to **Manual** and the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_MODE`
                attribute to **Measure**. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpNoiseCompensationEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_COMPENSATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_type(self, selector_string):
        r"""Gets the noise compensation type. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Analyzer and Termination**.

        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                                              |
        +==============================+==========================================================================================================================+
        | Analyzer and Termination (0) | Compensates for noise from the analyzer and the 50 ohm termination. The measured power values are in excess of the       |
        |                              | thermal noise floor.                                                                                                     |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Analyzer Only (1)            | Compensates for analyzer noise only.                                                                                     |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpNoiseCompensationType):
                Specifies the noise compensation type. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NOISE_COMPENSATION_TYPE.value
            )
            attr_val = enums.AcpNoiseCompensationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_type(self, selector_string, value):
        r"""Sets the noise compensation type. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Analyzer and Termination**.

        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                                              |
        +==============================+==========================================================================================================================+
        | Analyzer and Termination (0) | Compensates for noise from the analyzer and the 50 ohm termination. The measured power values are in excess of the       |
        |                              | thermal noise floor.                                                                                                     |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Analyzer Only (1)            | Compensates for analyzer noise only.                                                                                     |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpNoiseCompensationType, int):
                Specifies the noise compensation type. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpNoiseCompensationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_COMPENSATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The ACP measurement uses the value of the ACP Averaging Count attribute as the number of acquisitions over which the     |
        |              | ACP measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpAveragingEnabled):
                Specifies whether to enable averaging for the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_ENABLED.value
            )
            attr_val = enums.AcpAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The ACP measurement uses the value of the ACP Averaging Count attribute as the number of acquisitions over which the     |
        |              | ACP measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpAveragingEnabled, int):
                Specifies whether to enable averaging for the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_type(self, selector_string):
        r"""Gets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
        measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Default value is **RMS**.

        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                  |
        +==============+==============================================================================================================+
        | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations, but not the noise floor. |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Scalar (2)   | The square root of the power spectrum is averaged.                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.           |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.         |
        +--------------+--------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpAveragingType):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
                measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_TYPE.value
            )
            attr_val = enums.AcpAveragingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_type(self, selector_string, value):
        r"""Sets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
        measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Default value is **RMS**.

        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                  |
        +==============+==============================================================================================================+
        | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations, but not the noise floor. |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Scalar (2)   | The square root of the power spectrum is averaged.                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.           |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.         |
        +--------------+--------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpAveragingType, int):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
                measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpAveragingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_mode(self, selector_string):
        r"""Gets whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement. Refer to the
        measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+---------------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                           |
        +===========================+=======================================================================================+
        | Measure (0)               | ACP measurement is performed on the acquired signal.                                  |
        +---------------------------+---------------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | Manual noise calibration of the signal analyzer is performed for the ACP measurement. |
        +---------------------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpMeasurementMode):
                Specifies whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement. Refer to the
                measurement guidelines section in the `Noise Compensation Algorithm
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_MODE.value
            )
            attr_val = enums.AcpMeasurementMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_mode(self, selector_string, value):
        r"""Sets whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement. Refer to the
        measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+---------------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                           |
        +===========================+=======================================================================================+
        | Measure (0)               | ACP measurement is performed on the acquired signal.                                  |
        +---------------------------+---------------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | Manual noise calibration of the signal analyzer is performed for the ACP measurement. |
        +---------------------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpMeasurementMode, int):
                Specifies whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement. Refer to the
                measurement guidelines section in the `Noise Compensation Algorithm
                <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpMeasurementMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_overlap_mode(self, selector_string):
        r"""Gets the overlap mode when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
        attribute to **Sequential FFT**. In Sequential FFT method, the measurement divides all the acquired samples into
        smaller FFT chunks of equal size.  Then the FFT is computed for each chunk. The resultant FFTs are averaged to get the
        spectrum used to compute the ACP.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Disabled (0)     | Disables the overlap between the FFT chunks.                                                                             |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Automatic (1)    | Measurement sets the                                                                                                     |
        |                  | number of overlapped samples between consecutive FFT chunks to 50% of the ACP Sequential FFT Size attribute value.       |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | User Defined (2) | Measurement uses the overlap that you specify in the ACP FFT Overlap attribute.                                          |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpFftOverlapMode):
                Specifies the overlap mode when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
                attribute to **Sequential FFT**. In Sequential FFT method, the measurement divides all the acquired samples into
                smaller FFT chunks of equal size.  Then the FFT is computed for each chunk. The resultant FFTs are averaged to get the
                spectrum used to compute the ACP.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_FFT_OVERLAP_MODE.value
            )
            attr_val = enums.AcpFftOverlapMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_overlap_mode(self, selector_string, value):
        r"""Sets the overlap mode when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
        attribute to **Sequential FFT**. In Sequential FFT method, the measurement divides all the acquired samples into
        smaller FFT chunks of equal size.  Then the FFT is computed for each chunk. The resultant FFTs are averaged to get the
        spectrum used to compute the ACP.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Disabled (0)     | Disables the overlap between the FFT chunks.                                                                             |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Automatic (1)    | Measurement sets the                                                                                                     |
        |                  | number of overlapped samples between consecutive FFT chunks to 50% of the ACP Sequential FFT Size attribute value.       |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | User Defined (2) | Measurement uses the overlap that you specify in the ACP FFT Overlap attribute.                                          |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpFftOverlapMode, int):
                Specifies the overlap mode when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
                attribute to **Sequential FFT**. In Sequential FFT method, the measurement divides all the acquired samples into
                smaller FFT chunks of equal size.  Then the FFT is computed for each chunk. The resultant FFTs are averaged to get the
                spectrum used to compute the ACP.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpFftOverlapMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_FFT_OVERLAP_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_overlap(self, selector_string):
        r"""Gets the samples to overlap between the consecutive chunks as a percentage of the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute value when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the samples to overlap between the consecutive chunks as a percentage of the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute value when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_FFT_OVERLAP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_overlap(self, selector_string, value):
        r"""Sets the samples to overlap between the consecutive chunks as a percentage of the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute value when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the samples to overlap between the consecutive chunks as a percentage of the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute value when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**.

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
                updated_selector_string, attributes.AttributeID.ACP_FFT_OVERLAP.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_if_output_power_offset_auto(self, selector_string):
        r"""Gets whether the measurement computes an appropriate IF output power level offset for the offset channels to
        improve the dynamic range of the ACP measurement. This attribute is valid only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement sets the IF output power level offset using the values of the ACP Near IF Output Pwr Offset and ACP Far  |
        |              | IF Output Pwr Offset attributes.                                                                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement automatically computes an IF output power level offset for the offset channels to improve the dynamic    |
        |              | range of the ACP measurement.                                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpIFOutputPowerOffsetAuto):
                Specifies whether the measurement computes an appropriate IF output power level offset for the offset channels to
                improve the dynamic range of the ACP measurement. This attribute is valid only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

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
                attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO.value,
            )
            attr_val = enums.AcpIFOutputPowerOffsetAuto(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_if_output_power_offset_auto(self, selector_string, value):
        r"""Sets whether the measurement computes an appropriate IF output power level offset for the offset channels to
        improve the dynamic range of the ACP measurement. This attribute is valid only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement sets the IF output power level offset using the values of the ACP Near IF Output Pwr Offset and ACP Far  |
        |              | IF Output Pwr Offset attributes.                                                                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement automatically computes an IF output power level offset for the offset channels to improve the dynamic    |
        |              | range of the ACP measurement.                                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpIFOutputPowerOffsetAuto, int):
                Specifies whether the measurement computes an appropriate IF output power level offset for the offset channels to
                improve the dynamic range of the ACP measurement. This attribute is valid only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpIFOutputPowerOffsetAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_near_if_output_power_offset(self, selector_string):
        r"""Gets the offset that is needed to adjust the IF output power levels for the offset channels that are near the
        carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
        the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are near the
                carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
                the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

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
                attributes.AttributeID.ACP_NEAR_IF_OUTPUT_POWER_OFFSET.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_near_if_output_power_offset(self, selector_string, value):
        r"""Sets the offset that is needed to adjust the IF output power levels for the offset channels that are near the
        carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
        the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are near the
                carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
                the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

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
                attributes.AttributeID.ACP_NEAR_IF_OUTPUT_POWER_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_far_if_output_power_offset(self, selector_string):
        r"""Gets the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
        carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
        the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 20.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
                carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
                the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_FAR_IF_OUTPUT_POWER_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_far_if_output_power_offset(self, selector_string, value):
        r"""Sets the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
        carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
        the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 20.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
                carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
                the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

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
                attributes.AttributeID.ACP_FAR_IF_OUTPUT_POWER_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sequential_fft_size(self, selector_string):
        r"""Gets the FFT size, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute
        to **Sequential FFT**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 512.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the FFT size, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute
                to **Sequential FFT**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sequential_fft_size(self, selector_string, value):
        r"""Sets the FFT size, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute
        to **Sequential FFT**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 512.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the FFT size, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute
                to **Sequential FFT**.

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
                updated_selector_string, attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_amplitude_correction_type(self, selector_string):
        r"""Gets whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
        the RF center frequency, or at the individual frequency bins. Use the
        :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
        attenuation table.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RF Center Frequency**.

        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)               | Description                                                                                                              |
        +============================+==========================================================================================================================+
        | RF Center Frequency (0)    | All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the  |
        |                            | RF center frequency.                                                                                                     |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Spectrum Frequency Bin (1) | An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that     |
        |                            | frequency.                                                                                                               |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpAmplitudeCorrectionType):
                Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
                the RF center frequency, or at the individual frequency bins. Use the
                :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
                attenuation table.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AMPLITUDE_CORRECTION_TYPE.value
            )
            attr_val = enums.AcpAmplitudeCorrectionType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_amplitude_correction_type(self, selector_string, value):
        r"""Sets whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
        the RF center frequency, or at the individual frequency bins. Use the
        :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
        attenuation table.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RF Center Frequency**.

        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)               | Description                                                                                                              |
        +============================+==========================================================================================================================+
        | RF Center Frequency (0)    | All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the  |
        |                            | RF center frequency.                                                                                                     |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Spectrum Frequency Bin (1) | An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that     |
        |                            | frequency.                                                                                                               |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpAmplitudeCorrectionType, int):
                Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
                the RF center frequency, or at the individual frequency bins. Use the
                :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
                attenuation table.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpAmplitudeCorrectionType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_AMPLITUDE_CORRECTION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the ACP measurement.

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
                Specifies whether to enable the traces to be stored and retrieved after performing the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the ACP measurement.

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
                attributes.AttributeID.ACP_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the ACP measurement.

        The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
        be used in calculations. The actual number of threads used depends on the problem size, system resources, data
        availability, and other considerations.

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
                Specifies the maximum number of threads used for parallelism for the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the ACP measurement.

        The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
        be used in calculations. The actual number of threads used depends on the problem size, system resources, data
        availability, and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the maximum number of threads used for parallelism for the ACP measurement.

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
                attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        r"""Configures averaging for the ACP measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.AcpAveragingEnabled, int):
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

            averaging_type (enums.AcpAveragingType, int):
                This parameter specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used
                for the measurement. The default value is **RMS**.

                +--------------+-------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                 |
                +==============+=============================================================================================================+
                | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor. |
                +--------------+-------------------------------------------------------------------------------------------------------------+
                | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                      |
                +--------------+-------------------------------------------------------------------------------------------------------------+
                | Scalar (2)   | The square root of the power spectrum is averaged.                                                          |
                +--------------+-------------------------------------------------------------------------------------------------------------+
                | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.          |
                +--------------+-------------------------------------------------------------------------------------------------------------+
                | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.        |
                +--------------+-------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            averaging_enabled = (
                averaging_enabled.value
                if type(averaging_enabled) is enums.AcpAveragingEnabled
                else averaging_enabled
            )
            averaging_type = (
                averaging_type.value
                if type(averaging_type) is enums.AcpAveragingType
                else averaging_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count, averaging_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_configurable_number_of_offsets_enabled(
        self, selector_string, configurable_number_of_offsets_enabled
    ):
        r"""Configures whether the number of offsets will be computed by the measurement or configured by the user.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            configurable_number_of_offsets_enabled (enums.AcpConfigurableNumberOfOffsetsEnabled, int):
                This parameter specifies whether the number of offsets is computed by measurement or configured by you. When the
                carrier bandwidth is 200 kHz or the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` is **Downlink**, the
                default value is **False**. The default value is **True**, otherwise.

                .. note::
                   Incase of downlink, this attribute is applicable only for number of EUTRA offsets. For the number of UTRA offsets, only
                   3GPP specification defined values are supported.

                +--------------+-----------------------------------------------------------------------+
                | Name (Value) | Description                                                           |
                +==============+=======================================================================+
                | False (0)    | Measurement will set the number of offsets.                           |
                +--------------+-----------------------------------------------------------------------+
                | True (1)     | Measurement will use the user configured value for number of offsets. |
                +--------------+-----------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            configurable_number_of_offsets_enabled = (
                configurable_number_of_offsets_enabled.value
                if type(configurable_number_of_offsets_enabled)
                is enums.AcpConfigurableNumberOfOffsetsEnabled
                else configurable_number_of_offsets_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_configurable_number_of_offsets_enabled(
                updated_selector_string, configurable_number_of_offsets_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_measurement_method(self, selector_string, measurement_method):
        r"""Configures the method for performing the ACP measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_method (enums.AcpMeasurementMethod, int):
                This parameter specifies the method for performing the ACP measurement. The default value is **Normal**.

                +--------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)       | Description                                                                                                              |
                +====================+==========================================================================================================================+
                | Normal (0)         | The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this        |
                |                    | method when measurement speed is desirable over higher dynamic range.                                                    |
                +--------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Dynamic Range (1)  | The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use   |
                |                    | this method to get the best dynamic range. Supported Devices: PXIe-5665/5668                                             |
                +--------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Sequential FFT (2) | The ACP measurement acquires I/Q samples specified by the ACP Sweep Time attribute. These samples are divided into       |
                |                    | smaller chunks defined by the ACP Sequential FFT Size attribute, and FFT is computed on each of these chunks. The        |
                |                    | resultant FFTs are averaged to get the spectrum and is used to compute ACP.                                              |
                |                    | If the total acquired samples is not an integer multiple of the FFT size, the remaining samples at the end of the        |
                |                    | acquisition are not used.                                                                                                |
                +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            measurement_method = (
                measurement_method.value
                if type(measurement_method) is enums.AcpMeasurementMethod
                else measurement_method
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_measurement_method(
                updated_selector_string, measurement_method
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_noise_compensation_enabled(self, selector_string, noise_compensation_enabled):
        r"""Configures compensation of the channel powers for the inherent noise floor of the signal analyzer.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            noise_compensation_enabled (enums.AcpNoiseCompensationEnabled, int):
                This parameter specifies whether to enable compensation of the channel powers for the inherent noise floor of the
                signal analyzer. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | Disables compensation of the channel powers for the noise floor of the signal analyzer.                                  |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | Enables compensation of the channel powers for the noise floor of the signal analyzer. The noise floor of the signal     |
                |              | analyzer is measured for the RF path used by the ACP measurement and cached for future use. If signal analyzer or        |
                |              | measurement parameters change, noise floors are remeasured.                                                              |
                |              | Supported Devices: PXIe-5663/5665/5668R, PXIe-5830/5831/5832/5842/5860                                                   |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            noise_compensation_enabled = (
                noise_compensation_enabled.value
                if type(noise_compensation_enabled) is enums.AcpNoiseCompensationEnabled
                else noise_compensation_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_noise_compensation_enabled(
                updated_selector_string, noise_compensation_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_eutra_offsets(self, selector_string, number_of_eutra_offsets):
        r"""Configures the number of evolved universal terrestrial radio access adjacent channels of the subblock, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

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

            number_of_eutra_offsets (int):
                This parameter specifies the number of E-UTRA adjacent channel offsets to be configured at offset positions, when you
                set the ACP Configurable Number of Offset Enabled attribute to **True**.

                In case of non-contiguous carrier aggregation, the configured value will be used only for the outer offsets and
                the offset channels in the gap region are defined as per the 3GPP specification. Offset integration bandwidth and
                offset power reference for the outer E-UTRA offsets are set according to the value of
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute.

                The default value is 0, when carrier bandwidth is 200 kHz. The default value is 2 for downlink and 1 for
                uplink, otherwise.

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
            error_code = self._interpreter.acp_configure_number_of_eutra_offsets(
                updated_selector_string, number_of_eutra_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_gsm_offsets(self, selector_string, number_of_gsm_offsets):
        r"""Configures the number of GSM adjacent channels of the subblock, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

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

            number_of_gsm_offsets (int):
                This parameter specifies the number of GSM adjacent channel offsets to be configured when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and when you set the ACP
                Configurable Number of Offset Enabled attribute to **True**.

                The frequency offset from the center of NB-IOT carrier to the center of the first offset is 300 kHz as defined
                in the 3GPP specification. The center of every other offset is placed at 200 kHz from the previous offset's center.

                The default value is 1, when you set the CC Bandwidth attribute to is **200.0 k**. The default value is 0,
                otherwise.

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
            error_code = self._interpreter.acp_configure_number_of_gsm_offsets(
                updated_selector_string, number_of_gsm_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_utra_offsets(self, selector_string, number_of_utra_offsets):
        r"""Configures the number of universal terrestrial radio access (UTRA) adjacent channels of the subblock, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.

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

            number_of_utra_offsets (int):
                This parameter specifies the number of UTRA adjacent channel offsets to be configured at offset positions, when you set
                the ACP Configurable Number of Offset Enabled attribute to **True**.

                In case of downlink, only 3GPP specification defined values are supported. In case of non-contiguous carrier
                aggregation, the configured value will be used only for the outer offsets and the offset channels in the gap region are
                defined as per the 3GPP specification. Offset power reference for the outer UTRA offsets are set according to the value
                of :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute.

                The default value is 1, when carrier bandwidth is 200 kHz.

                The default value is 0, when the band is 46 or when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute to **LAA**.

                The default value is 2 for all other configurations.

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
            error_code = self._interpreter.acp_configure_number_of_utra_offsets(
                updated_selector_string, number_of_utra_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        r"""Configures the RBW filter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            rbw_auto (enums.AcpRbwAutoBandwidth, int):
                This parameter specifies whether the measurement computes the RBW. The default value is **True**.

                +--------------+---------------------------------------------------------------------+
                | Name (Value) | Description                                                         |
                +==============+=====================================================================+
                | False (0)    | The measurement uses the RBW that you specify in the RBW parameter. |
                +--------------+---------------------------------------------------------------------+
                | True (1)     | The measurement computes the RBW.                                   |
                +--------------+---------------------------------------------------------------------+

            rbw (float):
                This parameter specifies the bandwidth of the RBW filter used to sweep the acquired signal, when you set the **RBW
                Auto** parameter to **False**. This value is expressed in Hz. The default value is 30 kHz.

            rbw_filter_type (enums.AcpRbwFilterType, int):
                This parameter specifies the shape of the digital RBW filter. The default value is **FFT Based**.

                +---------------+----------------------------------------------------+
                | Name (Value)  | Description                                        |
                +===============+====================================================+
                | FFT Based (0) | No RBW filtering is performed.                     |
                +---------------+----------------------------------------------------+
                | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
                +---------------+----------------------------------------------------+
                | Flat (2)      | An RBW filter with a flat response is applied.     |
                +---------------+----------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            rbw_auto = rbw_auto.value if type(rbw_auto) is enums.AcpRbwAutoBandwidth else rbw_auto
            rbw_filter_type = (
                rbw_filter_type.value
                if type(rbw_filter_type) is enums.AcpRbwFilterType
                else rbw_filter_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_rbw_filter(
                updated_selector_string, rbw_auto, rbw, rbw_filter_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        r"""Configures the sweep time.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            sweep_time_auto (enums.AcpSweepTimeAuto, int):
                This parameter specifies whether the measurement computes the sweep time. The default value is **True**.

                +--------------+--------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                |
                +==============+============================================================================================+
                | False (0)    | The measurement uses the sweep time that you specify in the Sweep Time Interval parameter. |
                +--------------+--------------------------------------------------------------------------------------------+
                | True (1)     | The measurement uses a sweep time of 1 ms.                                                 |
                +--------------+--------------------------------------------------------------------------------------------+

            sweep_time_interval (float):
                This parameter specifies the sweep time when you set the **Sweep Time Auto** parameter to **False**. This value is
                expressed in seconds. The default value is 1 ms.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            sweep_time_auto = (
                sweep_time_auto.value
                if type(sweep_time_auto) is enums.AcpSweepTimeAuto
                else sweep_time_auto
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_sweep_time(
                updated_selector_string, sweep_time_auto, sweep_time_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_utra_and_eutra_offsets(
        self, selector_string, number_of_utra_offsets, number_of_eutra_offsets
    ):
        r"""Configures the number of universal terrestrial radio access (UTRA) and evolved universal terrestrial radio access
        (E-UTRA) adjacent channels of the subblock.
        This method is valid only for uplink single carrier, and contiguous carrier aggregation. In case of uplink
        non-contiguous multi-carrier and downlink, the number of UTRA/EUTRA offsets are determined from the 3GPP specification.

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

            number_of_utra_offsets (int):
                This parameter specifies the number of UTRA adjacent channel offsets to be configured at offset positions as defined in
                the 3GPP specification.
                The default value is 2.

            number_of_eutra_offsets (int):
                This parameter specifies the number of E-UTRA adjacent channel offsets to be configured at offset positions as defined
                in the 3GPP specification.
                The default value is 1.

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
            error_code = self._interpreter.acp_configure_utra_and_eutra_offsets(
                updated_selector_string, number_of_utra_offsets, number_of_eutra_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_power_units(self, selector_string, power_units):
        r"""Configures the units for absolute power.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            power_units (enums.AcpPowerUnits, int):
                This parameter specifies the units for absolute power. The default value is **dBm**.

                +--------------+---------------------------------------------+
                | Name (Value) | Description                                 |
                +==============+=============================================+
                | dBm (0)      | The absolute powers are reported in dBm.    |
                +--------------+---------------------------------------------+
                | dBm/Hz (1)   | The absolute powers are reported in dBm/Hz. |
                +--------------+---------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            power_units = (
                power_units.value if type(power_units) is enums.AcpPowerUnits else power_units
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_power_units(
                updated_selector_string, power_units
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def validate_noise_calibration_data(self, selector_string):
        r"""Indicates whether calibration data is valid for the configuration specified by the signal name in the **Selector
        string** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (noise_calibration_data_valid, error_code):

            noise_calibration_data_valid (enums.AcpNoiseCalibrationDataValid):
                This parameter returns whether the calibration data is valid.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | Returns false if the calibration data is not present for the specified configuration or if the difference between the    |
                |              | current device temperature and the calibration temperature exceeds the [-5 °C, 5 °C] range.                              |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | Returns true if the calibration data is present for the configuration specified by the signal name in the Selector       |
                |              | string parameter.                                                                                                        |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            noise_calibration_data_valid, error_code = (
                self._interpreter.acp_validate_noise_calibration_data(updated_selector_string)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return noise_calibration_data_valid, error_code
