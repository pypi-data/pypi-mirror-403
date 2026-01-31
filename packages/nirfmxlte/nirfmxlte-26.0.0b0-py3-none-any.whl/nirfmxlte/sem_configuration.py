"""Provides methods to configure the Sem measurement."""

import functools

import nirfmxlte.attributes as attributes
import nirfmxlte.enums as enums
import nirfmxlte.errors as errors
import nirfmxlte.internal._helper as _helper
import nirfmxlte.sem_component_carrier_configuration as component_carrier


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        meas_obj = xs[0]  # parameter 0 is 'self' which is the measurement object
        if meas_obj._signal_obj.is_disposed:
            raise Exception("Cannot access a disposed Lte signal configuration")
        return f(*xs, **kws)

    return aux


class SemConfiguration(object):
    """Provides methods to configure the Sem measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the Sem measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter
        self.component_carrier = component_carrier.SemComponentCarrierConfiguration(signal_obj)  # type: ignore

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal and result
        instances. Refer to the Selector String topic for information about the string syntax for named signals and named
        results.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable the SEM measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal and result
        instances. Refer to the Selector String topic for information about the string syntax for named signals and named
        results.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the SEM measurement.

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
                attributes.AttributeID.SEM_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_uplink_mask_type(self, selector_string):
        r"""Gets the spectrum emission mask used in the measurement for uplink. Each mask type refers to a different Network
        Signalled (NS) value. **General CA Class B**, **CA_NS_04**, **CA_NC_NS_01**, **CA_NS_09**, and **CA_NS_10** refers to
        the carrier aggregation case. You must set the mask type to **Custom** to configure the custom offset masks.
        Refer to section 6.6.2.1 of the *3GPP 36.521* specification for more information about standard-defined mask
        types.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **General (NS_01)**.

        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                         | Description                                                                                                              |
        +======================================+==========================================================================================================================+
        | General (NS_01) (0)                  | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1.5-1, 6.6.2.1.5-2,      |
        |                                      | 6.6.2.1A.5-1, 6.6.2.1A.1.5-2, 6.6.2.1A.1.5-3, and 6.6.2.1A.5-4 in section 6.6.2 of the 3GPP TS 36.521-1 specification.   |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_03 or NS_11 or NS_20 or NS_21 (1) | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.1-1 and              |
        |                                      | 6.6.2.2.5.1-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                    |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_04 (2)                            | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.3.2-3 in section       |
        |                                      | 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                             |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_06 or NS_07 (3)                   | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.3-1 and              |
        |                                      | 6.6.2.2.5.3-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                    |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | CA_NS_04 (4)                         | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.1.5.1-1 in section    |
        |                                      | 6.6.2 of the 3GPP TS 36.521-1 specification. This mask applies only for aggregated carriers.                             |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (5)                           | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
        |                                      | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type,  |
        |                                      | and SEM Offset BW Integral attributes for each offset.                                                                   |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | General CA Class B (6)               | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.1A.1.5-3 and 6.6.2.1A.1.5-4  |
        |                                      | in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                  |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | CA_NC_NS_01 (7)                      | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.3.5-1 and 6.6.2.2A.3.5-2  |
        |                                      | in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                  |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_27 or NS_43 (8)                   | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5-1 in section 6.6.2.2.5   |
        |                                      | of the 3GPP TS 36.101-1 specification.                                                                                   |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_35 (9)                            | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.5-1 in section           |
        |                                      | 6.6.2.2.5.5 of the 3GPP TS 36.521-1 specification.                                                                       |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_28 (10)                           | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.6-1 in section 6.6.2.2.6   |
        |                                      | of the 3GPP TS 36.101-1 specification.                                                                                   |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | CA_NS_09 (11)                        | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.2-1 in section            |
        |                                      | 6.6.2.2A.2, and Table 6.6.2.2A.3-1 in section 6.6.2.2A.3 of the 3GPP TS 36.101-1 specification.                          |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | CA_NS_10 (12)                        | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.4-1 in section            |
        |                                      | 6.6.2.2A.4 of the 3GPP TS 36.101-1 specification.                                                                        |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemUplinkMaskType):
                Specifies the spectrum emission mask used in the measurement for uplink. Each mask type refers to a different Network
                Signalled (NS) value. **General CA Class B**, **CA_NS_04**, **CA_NC_NS_01**, **CA_NS_09**, and **CA_NS_10** refers to
                the carrier aggregation case. You must set the mask type to **Custom** to configure the custom offset masks.
                Refer to section 6.6.2.1 of the *3GPP 36.521* specification for more information about standard-defined mask
                types.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_UPLINK_MASK_TYPE.value
            )
            attr_val = enums.SemUplinkMaskType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_uplink_mask_type(self, selector_string, value):
        r"""Sets the spectrum emission mask used in the measurement for uplink. Each mask type refers to a different Network
        Signalled (NS) value. **General CA Class B**, **CA_NS_04**, **CA_NC_NS_01**, **CA_NS_09**, and **CA_NS_10** refers to
        the carrier aggregation case. You must set the mask type to **Custom** to configure the custom offset masks.
        Refer to section 6.6.2.1 of the *3GPP 36.521* specification for more information about standard-defined mask
        types.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **General (NS_01)**.

        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                         | Description                                                                                                              |
        +======================================+==========================================================================================================================+
        | General (NS_01) (0)                  | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1.5-1, 6.6.2.1.5-2,      |
        |                                      | 6.6.2.1A.5-1, 6.6.2.1A.1.5-2, 6.6.2.1A.1.5-3, and 6.6.2.1A.5-4 in section 6.6.2 of the 3GPP TS 36.521-1 specification.   |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_03 or NS_11 or NS_20 or NS_21 (1) | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.1-1 and              |
        |                                      | 6.6.2.2.5.1-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                    |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_04 (2)                            | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.3.2-3 in section       |
        |                                      | 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                             |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_06 or NS_07 (3)                   | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.3-1 and              |
        |                                      | 6.6.2.2.5.3-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                    |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | CA_NS_04 (4)                         | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.1.5.1-1 in section    |
        |                                      | 6.6.2 of the 3GPP TS 36.521-1 specification. This mask applies only for aggregated carriers.                             |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (5)                           | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
        |                                      | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type,  |
        |                                      | and SEM Offset BW Integral attributes for each offset.                                                                   |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | General CA Class B (6)               | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.1A.1.5-3 and 6.6.2.1A.1.5-4  |
        |                                      | in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                  |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | CA_NC_NS_01 (7)                      | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.3.5-1 and 6.6.2.2A.3.5-2  |
        |                                      | in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                  |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_27 or NS_43 (8)                   | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5-1 in section 6.6.2.2.5   |
        |                                      | of the 3GPP TS 36.101-1 specification.                                                                                   |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_35 (9)                            | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.5-1 in section           |
        |                                      | 6.6.2.2.5.5 of the 3GPP TS 36.521-1 specification.                                                                       |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_28 (10)                           | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.6-1 in section 6.6.2.2.6   |
        |                                      | of the 3GPP TS 36.101-1 specification.                                                                                   |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | CA_NS_09 (11)                        | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.2-1 in section            |
        |                                      | 6.6.2.2A.2, and Table 6.6.2.2A.3-1 in section 6.6.2.2A.3 of the 3GPP TS 36.101-1 specification.                          |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | CA_NS_10 (12)                        | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.4-1 in section            |
        |                                      | 6.6.2.2A.4 of the 3GPP TS 36.101-1 specification.                                                                        |
        +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemUplinkMaskType, int):
                Specifies the spectrum emission mask used in the measurement for uplink. Each mask type refers to a different Network
                Signalled (NS) value. **General CA Class B**, **CA_NS_04**, **CA_NC_NS_01**, **CA_NS_09**, and **CA_NS_10** refers to
                the carrier aggregation case. You must set the mask type to **Custom** to configure the custom offset masks.
                Refer to section 6.6.2.1 of the *3GPP 36.521* specification for more information about standard-defined mask
                types.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SemUplinkMaskType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_UPLINK_MASK_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_mask_type(self, selector_string):
        r"""Gets the limits to be used in the measurement for downlink. Refer to section 6.6.3 of the *3GPP 36.141*
        specification for more information about standard-defined mask types.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **eNodeB Category Based**.

        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                                                              |
        +===========================+==========================================================================================================================+
        | eNodeB Category Based (0) | The limits are applied based on eNodeB Category attribute.                                                               |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Band 46 (1)               | The limits are applied based on Band 46 test requirements.                                                               |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (5)                | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
        |                           | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Rel Limit Start,                                       |
        |                           | SEM Offset Rel Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type, and SEM Offset BW Integral   |
        |                           | attributes for each offset.                                                                                              |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemDownlinkMaskType):
                Specifies the limits to be used in the measurement for downlink. Refer to section 6.6.3 of the *3GPP 36.141*
                specification for more information about standard-defined mask types.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE.value
            )
            attr_val = enums.SemDownlinkMaskType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_mask_type(self, selector_string, value):
        r"""Sets the limits to be used in the measurement for downlink. Refer to section 6.6.3 of the *3GPP 36.141*
        specification for more information about standard-defined mask types.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **eNodeB Category Based**.

        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                                                              |
        +===========================+==========================================================================================================================+
        | eNodeB Category Based (0) | The limits are applied based on eNodeB Category attribute.                                                               |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Band 46 (1)               | The limits are applied based on Band 46 test requirements.                                                               |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (5)                | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
        |                           | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Rel Limit Start,                                       |
        |                           | SEM Offset Rel Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type, and SEM Offset BW Integral   |
        |                           | attributes for each offset.                                                                                              |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemDownlinkMaskType, int):
                Specifies the limits to be used in the measurement for downlink. Refer to section 6.6.3 of the *3GPP 36.141*
                specification for more information about standard-defined mask types.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SemDownlinkMaskType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sidelink_mask_type(self, selector_string):
        r"""Gets the spectrum emission mask used in the measurement for sidelink. Each mask type refers to a different Network
        Signalled (NS) value. You must set the mask type to **Custom** to configure the custom offset masks.
        Refer to section 6.6.2 of the *3GPP 36.521* specification for more information about standard-defined mask
        types.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **General (NS_01)**.

        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)        | Description                                                                                                              |
        +=====================+==========================================================================================================================+
        | General (NS_01) (0) | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1G.1.5-1 and Table       |
        |                     | 6.6.2.1G.3.5-1 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                   |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_33 or NS_34 (1)  | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2G.1.5-1 in section      |
        |                     | 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                             |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (5)          | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
        |                     | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type,  |
        |                     | and SEM Offset BW Integral attributes for each offset.                                                                   |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemSidelinkMaskType):
                Specifies the spectrum emission mask used in the measurement for sidelink. Each mask type refers to a different Network
                Signalled (NS) value. You must set the mask type to **Custom** to configure the custom offset masks.
                Refer to section 6.6.2 of the *3GPP 36.521* specification for more information about standard-defined mask
                types.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_SIDELINK_MASK_TYPE.value
            )
            attr_val = enums.SemSidelinkMaskType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sidelink_mask_type(self, selector_string, value):
        r"""Sets the spectrum emission mask used in the measurement for sidelink. Each mask type refers to a different Network
        Signalled (NS) value. You must set the mask type to **Custom** to configure the custom offset masks.
        Refer to section 6.6.2 of the *3GPP 36.521* specification for more information about standard-defined mask
        types.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **General (NS_01)**.

        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)        | Description                                                                                                              |
        +=====================+==========================================================================================================================+
        | General (NS_01) (0) | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1G.1.5-1 and Table       |
        |                     | 6.6.2.1G.3.5-1 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                   |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_33 or NS_34 (1)  | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2G.1.5-1 in section      |
        |                     | 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                             |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (5)          | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
        |                     | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type,  |
        |                     | and SEM Offset BW Integral attributes for each offset.                                                                   |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemSidelinkMaskType, int):
                Specifies the spectrum emission mask used in the measurement for sidelink. Each mask type refers to a different Network
                Signalled (NS) value. You must set the mask type to **Custom** to configure the custom offset masks.
                Refer to section 6.6.2 of the *3GPP 36.521* specification for more information about standard-defined mask
                types.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SemSidelinkMaskType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_SIDELINK_MASK_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_delta_f_maximum(self, selector_string):
        r"""Gets the stop frequency for the last offset segment to be used in the measurement. This value is expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 15 MHz. The minimum value is 9.5 MHz.

        .. note::
           This attribute is considered for downlink only when you set the
           :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to either **eNodeB Category Based** or
           **Band 46**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the stop frequency for the last offset segment to be used in the measurement. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SEM_DELTA_F_MAXIMUM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_delta_f_maximum(self, selector_string, value):
        r"""Sets the stop frequency for the last offset segment to be used in the measurement. This value is expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 15 MHz. The minimum value is 9.5 MHz.

        .. note::
           This attribute is considered for downlink only when you set the
           :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to either **eNodeB Category Based** or
           **Band 46**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the stop frequency for the last offset segment to be used in the measurement. This value is expressed in Hz.

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
                updated_selector_string, attributes.AttributeID.SEM_DELTA_F_MAXIMUM.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_aggregated_maximum_power(self, selector_string):
        r"""Gets the aggregated maximum output power of all transmit antenna connectors. This value is expressed in dBm. Refer
        to the Section 6.6.3 of *3GPP 36.141* specification for more details.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. Valid values are within 20, inclusive.

        .. note::
           This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
           attribute to **Downlink**, :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute to **Home Base
           Station**, and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **eNodeB Category
           Based**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the aggregated maximum output power of all transmit antenna connectors. This value is expressed in dBm. Refer
                to the Section 6.6.3 of *3GPP 36.141* specification for more details.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SEM_AGGREGATED_MAXIMUM_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_aggregated_maximum_power(self, selector_string, value):
        r"""Sets the aggregated maximum output power of all transmit antenna connectors. This value is expressed in dBm. Refer
        to the Section 6.6.3 of *3GPP 36.141* specification for more details.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. Valid values are within 20, inclusive.

        .. note::
           This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
           attribute to **Downlink**, :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute to **Home Base
           Station**, and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **eNodeB Category
           Based**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the aggregated maximum output power of all transmit antenna connectors. This value is expressed in dBm. Refer
                to the Section 6.6.3 of *3GPP 36.141* specification for more details.

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
                attributes.AttributeID.SEM_AGGREGATED_MAXIMUM_POWER.value,
                value,
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
                Returns the integration bandwidth of the subblock. This value is expressed in Hz. Integration bandwidth is the span
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
                attributes.AttributeID.SEM_SUBBLOCK_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_aggregated_channel_bandwidth(self, selector_string):
        r"""Gets the aggregated channel bandwidth of a configured subblock. This value is expressed in Hz. The aggregated
        channel bandwidth is the sum of the subblock integration bandwidth and the guard bands on either side of the subblock
        integration bandwidth.

        Use "subblock<*n*>" as the selector string to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the aggregated channel bandwidth of a configured subblock. This value is expressed in Hz. The aggregated
                channel bandwidth is the sum of the subblock integration bandwidth and the guard bands on either side of the subblock
                integration bandwidth.

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
                attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_number_of_offsets(self, selector_string):
        r"""Gets the number of SEM offset segments.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of SEM offset segments.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_NUMBER_OF_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_offsets(self, selector_string, value):
        r"""Sets the number of SEM offset segments.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of SEM offset segments.

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
                updated_selector_string, attributes.AttributeID.SEM_NUMBER_OF_OFFSETS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_start_frequency(self, selector_string):
        r"""Gets the start frequency of an offset segment relative to the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
        :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
        is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the start frequency of an offset segment relative to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
                is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_START_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_start_frequency(self, selector_string, value):
        r"""Sets the start frequency of an offset segment relative to the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
        :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
        is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the start frequency of an offset segment relative to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
                is expressed in Hz.

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
                attributes.AttributeID.SEM_OFFSET_START_FREQUENCY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_stop_frequency(self, selector_string):
        r"""Gets the stop frequency of an offset segment relative to the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
        :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
        is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is 1 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the stop frequency of an offset segment relative to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
                is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_STOP_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_stop_frequency(self, selector_string, value):
        r"""Sets the stop frequency of an offset segment relative to the
        :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
        :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
        is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is 1 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the stop frequency of an offset segment relative to the
                :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
                is expressed in Hz.

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
                attributes.AttributeID.SEM_OFFSET_STOP_FREQUENCY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_sideband(self, selector_string):
        r"""Gets whether the offset segment is present either on one side or on both sides of a carrier.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is **Both**.

        +--------------+---------------------------------------------------------------------------+
        | Name (Value) | Description                                                               |
        +==============+===========================================================================+
        | Neg (0)      | Configures a lower offset segment to the left of the leftmost carrier.    |
        +--------------+---------------------------------------------------------------------------+
        | Pos (1)      | Configures an upper offset segment to the right of the rightmost carrier. |
        +--------------+---------------------------------------------------------------------------+
        | Both (2)     | Configures both the negative and the positive offset segments.            |
        +--------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemOffsetSideband):
                Specifies whether the offset segment is present either on one side or on both sides of a carrier.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_SIDEBAND.value
            )
            attr_val = enums.SemOffsetSideband(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_sideband(self, selector_string, value):
        r"""Sets whether the offset segment is present either on one side or on both sides of a carrier.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is **Both**.

        +--------------+---------------------------------------------------------------------------+
        | Name (Value) | Description                                                               |
        +==============+===========================================================================+
        | Neg (0)      | Configures a lower offset segment to the left of the leftmost carrier.    |
        +--------------+---------------------------------------------------------------------------+
        | Pos (1)      | Configures an upper offset segment to the right of the rightmost carrier. |
        +--------------+---------------------------------------------------------------------------+
        | Both (2)     | Configures both the negative and the positive offset segments.            |
        +--------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemOffsetSideband, int):
                Specifies whether the offset segment is present either on one side or on both sides of a carrier.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SemOffsetSideband else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_SIDEBAND.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_rbw_filter_bandwidth(self, selector_string):
        r"""Gets the bandwidth of an RBW filter used to sweep an acquired offset segment. This value is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is 30000 Hz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the bandwidth of an RBW filter used to sweep an acquired offset segment. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_OFFSET_RBW_FILTER_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_rbw_filter_bandwidth(self, selector_string, value):
        r"""Sets the bandwidth of an RBW filter used to sweep an acquired offset segment. This value is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is 30000 Hz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the bandwidth of an RBW filter used to sweep an acquired offset segment. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_OFFSET_RBW_FILTER_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_rbw_filter_type(self, selector_string):
        r"""Gets the shape of a digital RBW filter.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is **Gaussian**.

        +---------------+-----------------------------------------+
        | Name (Value)  | Description                             |
        +===============+=========================================+
        | FFT Based (0) | No RBW filtering is performed.          |
        +---------------+-----------------------------------------+
        | Gaussian (1)  | The RBW filter has a Gaussian response. |
        +---------------+-----------------------------------------+
        | Flat (2)      | The RBW filter has a flat response.     |
        +---------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemOffsetRbwFilterType):
                Specifies the shape of a digital RBW filter.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_RBW_FILTER_TYPE.value
            )
            attr_val = enums.SemOffsetRbwFilterType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_rbw_filter_type(self, selector_string, value):
        r"""Sets the shape of a digital RBW filter.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is **Gaussian**.

        +---------------+-----------------------------------------+
        | Name (Value)  | Description                             |
        +===============+=========================================+
        | FFT Based (0) | No RBW filtering is performed.          |
        +---------------+-----------------------------------------+
        | Gaussian (1)  | The RBW filter has a Gaussian response. |
        +---------------+-----------------------------------------+
        | Flat (2)      | The RBW filter has a flat response.     |
        +---------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemOffsetRbwFilterType, int):
                Specifies the shape of a digital RBW filter.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SemOffsetRbwFilterType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SEM_OFFSET_RBW_FILTER_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_bandwidth_integral(self, selector_string):
        r"""Gets the resolution of a spectrum to compare with the spectral mask limits as an integer multiple of the RBW.

        When you set this attribute to a value greater than 1, the measurement acquires the spectrum with a narrow
        resolution and then processes it digitally to get a wider resolution that is equal to the product of a bandwidth
        integral and a RBW.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the resolution of a spectrum to compare with the spectral mask limits as an integer multiple of the RBW.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_BANDWIDTH_INTEGRAL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_bandwidth_integral(self, selector_string, value):
        r"""Sets the resolution of a spectrum to compare with the spectral mask limits as an integer multiple of the RBW.

        When you set this attribute to a value greater than 1, the measurement acquires the spectrum with a narrow
        resolution and then processes it digitally to get a wider resolution that is equal to the product of a bandwidth
        integral and a RBW.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the resolution of a spectrum to compare with the spectral mask limits as an integer multiple of the RBW.

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
                attributes.AttributeID.SEM_OFFSET_BANDWIDTH_INTEGRAL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_limit_fail_mask(self, selector_string):
        r"""Gets the criteria to determine the measurement fail status.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is **Absolute**.

        .. note::
           When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, all the values
           of limit fail mask are supported but when you set the Link Direction attribute to **Uplink**, the measurement
           internally sets the value of limit fail mask to **Absolute**.

        +-----------------+-------------------------------------------------------------------------------------------------------------+
        | Name (Value)    | Description                                                                                                 |
        +=================+=============================================================================================================+
        | Abs AND Rel (0) | Specifies the fail in measurement if the power in the segment exceeds both the absolute and relative masks. |
        +-----------------+-------------------------------------------------------------------------------------------------------------+
        | Abs OR Rel (1)  | Specifies the fail in measurement if the power in the segment exceeds either the absolute or relative mask. |
        +-----------------+-------------------------------------------------------------------------------------------------------------+
        | Absolute (2)    | Specifies the fail in measurement if the power in the segment exceeds the absolute mask.                    |
        +-----------------+-------------------------------------------------------------------------------------------------------------+
        | Relative (3)    | Specifies the fail in measurement if the power in the segment exceeds the relative mask.                    |
        +-----------------+-------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemOffsetLimitFailMask):
                Specifies the criteria to determine the measurement fail status.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_LIMIT_FAIL_MASK.value
            )
            attr_val = enums.SemOffsetLimitFailMask(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_limit_fail_mask(self, selector_string, value):
        r"""Sets the criteria to determine the measurement fail status.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is **Absolute**.

        .. note::
           When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, all the values
           of limit fail mask are supported but when you set the Link Direction attribute to **Uplink**, the measurement
           internally sets the value of limit fail mask to **Absolute**.

        +-----------------+-------------------------------------------------------------------------------------------------------------+
        | Name (Value)    | Description                                                                                                 |
        +=================+=============================================================================================================+
        | Abs AND Rel (0) | Specifies the fail in measurement if the power in the segment exceeds both the absolute and relative masks. |
        +-----------------+-------------------------------------------------------------------------------------------------------------+
        | Abs OR Rel (1)  | Specifies the fail in measurement if the power in the segment exceeds either the absolute or relative mask. |
        +-----------------+-------------------------------------------------------------------------------------------------------------+
        | Absolute (2)    | Specifies the fail in measurement if the power in the segment exceeds the absolute mask.                    |
        +-----------------+-------------------------------------------------------------------------------------------------------------+
        | Relative (3)    | Specifies the fail in measurement if the power in the segment exceeds the relative mask.                    |
        +-----------------+-------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemOffsetLimitFailMask, int):
                Specifies the criteria to determine the measurement fail status.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SemOffsetLimitFailMask else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SEM_OFFSET_LIMIT_FAIL_MASK.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_absolute_limit_start(self, selector_string):
        r"""Gets the absolute power limit corresponding to the beginning of an offset segment. This value is expressed in dBm.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is -16.5.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the absolute power limit corresponding to the beginning of an offset segment. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_START.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_absolute_limit_start(self, selector_string, value):
        r"""Sets the absolute power limit corresponding to the beginning of an offset segment. This value is expressed in dBm.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is -16.5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the absolute power limit corresponding to the beginning of an offset segment. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_START.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_absolute_limit_stop(self, selector_string):
        r"""Gets the absolute power limit corresponding to the end of an offset segment. This value is expressed in dBm.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is -16.5.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the absolute power limit corresponding to the end of an offset segment. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_STOP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_absolute_limit_stop(self, selector_string, value):
        r"""Sets the absolute power limit corresponding to the end of an offset segment. This value is expressed in dBm.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is -16.5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the absolute power limit corresponding to the end of an offset segment. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_STOP.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_relative_limit_start(self, selector_string):
        r"""Gets the relative power limit corresponding to the beginning of the offset segment. This value is expressed in dB.

        This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Downlink**.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is -51.5.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the relative power limit corresponding to the beginning of the offset segment. This value is expressed in dB.

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
                attributes.AttributeID.SEM_OFFSET_RELATIVE_LIMIT_START.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_relative_limit_start(self, selector_string, value):
        r"""Sets the relative power limit corresponding to the beginning of the offset segment. This value is expressed in dB.

        This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Downlink**.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is -51.5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the relative power limit corresponding to the beginning of the offset segment. This value is expressed in dB.

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
                attributes.AttributeID.SEM_OFFSET_RELATIVE_LIMIT_START.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_relative_limit_stop(self, selector_string):
        r"""Gets the relative power limit corresponding to the end of the offset segment. This value is expressed in dB.

        This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Downlink**.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is -58.5.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the relative power limit corresponding to the end of the offset segment. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SEM_OFFSET_RELATIVE_LIMIT_STOP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_relative_limit_stop(self, selector_string, value):
        r"""Sets the relative power limit corresponding to the end of the offset segment. This value is expressed in dB.

        This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Downlink**.

        Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.

        The default value is -58.5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the relative power limit corresponding to the end of the offset segment. This value is expressed in dB.

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
                attributes.AttributeID.SEM_OFFSET_RELATIVE_LIMIT_STOP.value,
                value,
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
        | False (0)    | The measurement uses the sweep time that you specify in the SEM Sweep Time attribute. |
        +--------------+---------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemSweepTimeAuto):
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
                updated_selector_string, attributes.AttributeID.SEM_SWEEP_TIME_AUTO.value
            )
            attr_val = enums.SemSweepTimeAuto(attr_val)
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
        | False (0)    | The measurement uses the sweep time that you specify in the SEM Sweep Time attribute. |
        +--------------+---------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemSweepTimeAuto, int):
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
            value = value.value if type(value) is enums.SemSweepTimeAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_SWEEP_TIME_AUTO.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sweep_time_interval(self, selector_string):
        r"""Gets the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SWEEP_TIME_AUTO` attribute to
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
                Specifies the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SWEEP_TIME_AUTO` attribute to
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
                updated_selector_string, attributes.AttributeID.SEM_SWEEP_TIME_INTERVAL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sweep_time_interval(self, selector_string, value):
        r"""Sets the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SWEEP_TIME_AUTO` attribute to
        **False**. This value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 ms.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SWEEP_TIME_AUTO` attribute to
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
                updated_selector_string, attributes.AttributeID.SEM_SWEEP_TIME_INTERVAL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The SEM measurement uses the value of the SEM Averaging Count attribute as the number of acquisitions over which the     |
        |              | SEM measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemAveragingEnabled):
                Specifies whether to enable averaging for the SEM measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_AVERAGING_ENABLED.value
            )
            attr_val = enums.SemAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The SEM measurement uses the value of the SEM Averaging Count attribute as the number of acquisitions over which the     |
        |              | SEM measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemAveragingEnabled, int):
                Specifies whether to enable averaging for the SEM measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SemAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_AVERAGING_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_AVERAGING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.SEM_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_type(self, selector_string):
        r"""Gets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for SEM
        measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RMS**.

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

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemAveragingType):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for SEM
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
                updated_selector_string, attributes.AttributeID.SEM_AVERAGING_TYPE.value
            )
            attr_val = enums.SemAveragingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_type(self, selector_string, value):
        r"""Sets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for SEM
        measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RMS**.

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

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SemAveragingType, int):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for SEM
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
            value = value.value if type(value) is enums.SemAveragingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_AVERAGING_TYPE.value, value
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

            attr_val (enums.SemAmplitudeCorrectionType):
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
                updated_selector_string, attributes.AttributeID.SEM_AMPLITUDE_CORRECTION_TYPE.value
            )
            attr_val = enums.SemAmplitudeCorrectionType(attr_val)
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

            value (enums.SemAmplitudeCorrectionType, int):
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
            value = value.value if type(value) is enums.SemAmplitudeCorrectionType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.SEM_AMPLITUDE_CORRECTION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the SEM measurement.

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
                Specifies whether to enable the traces to be stored and retrieved after performing the SEM measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the SEM measurement.

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
                attributes.AttributeID.SEM_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the SEM measurement.

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
                Specifies the maximum number of threads used for parallelism for the SEM measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_NUMBER_OF_ANALYSIS_THREADS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the SEM measurement.

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
                Specifies the maximum number of threads used for parallelism for the SEM measurement.

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
                attributes.AttributeID.SEM_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        r"""Configures averaging for the SEM measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.SemAveragingEnabled, int):
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

            averaging_type (enums.SemAveragingType, int):
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
                if type(averaging_enabled) is enums.SemAveragingEnabled
                else averaging_enabled
            )
            averaging_type = (
                averaging_type.value
                if type(averaging_type) is enums.SemAveragingType
                else averaging_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count, averaging_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_downlink_mask(
        self, selector_string, downlink_mask_type, delta_f_maximum, aggregated_maximum_power
    ):
        r"""Configures the **Downlink Mask Type**, **Delta F_max**, and **Aggregated Maximum Output Power** parameters for the SEM
        measurement in LTE downlink.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            downlink_mask_type (enums.SemDownlinkMaskType, int):
                This parameter specifies the standard-defined spectrum emission mask used in the measurement for the downlink. You must
                set the mask type to **CUSTOM** to configure the custom offsets and the masks.
                Refer to section 6.6.3 of the *3GPP 36.141* specification for more information about standard-defined mask
                types. The default value is **eNodeB Category Based**. Valid values are 0, 1, and 5.

                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)              | Description                                                                                                              |
                +===========================+==========================================================================================================================+
                | eNodeB Category Based (0) | Specifies limits are applied based on eNodeB Category attribute.                                                         |
                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Band 46 (1)               | Specifies that limits are applied based on Band 46 test requirements.                                                    |
                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Custom (5)                | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
                |                           | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Rel Limit Start ,SEM Offset Rel Limit Stop,            |
                |                           | SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type, and SEM Offset BW Integral attributes for each offset.  |
                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

            delta_f_maximum (float):
                This parameter specifies the stop frequency for the last offset segment to be used in the measurement. This value is
                expressed in Hz. The default value is 15 MHz. The minimum value is 9.5 MHz.

            aggregated_maximum_power (float):
                This parameter specifies the aggregated maximum output power of all the transmit antenna connectors. This value is
                expressed in dBm. The default value is 0. Valid values are within 20, inclusive.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            downlink_mask_type = (
                downlink_mask_type.value
                if type(downlink_mask_type) is enums.SemDownlinkMaskType
                else downlink_mask_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_downlink_mask(
                updated_selector_string,
                downlink_mask_type,
                delta_f_maximum,
                aggregated_maximum_power,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_offsets(self, selector_string, number_of_offsets):
        r"""Configures the number of offset segments for the SEM measurement.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and subblock number.

                Example:

                "subblock0"

                "result::r1/subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            number_of_offsets (int):
                This parameter specifies the number of SEM offset segments. The default value is 1.

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
            error_code = self._interpreter.sem_configure_number_of_offsets(
                updated_selector_string, number_of_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_absolute_limit_array(
        self, selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
    ):
        r"""Configures the array of the start limit and the stop limit of the offset segments.

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

            offset_absolute_limit_start (float):
                This parameter specifies the array of the absolute power limits corresponding to the beginning of an offset segment.
                This value is expressed in dBm. The default value is -16.5.

            offset_absolute_limit_stop (float):
                This parameter specifies the array of the absolute power limits corresponding to the end of an offset segment. This
                value is expressed in dBm. The default value is -16.5.

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
            error_code = self._interpreter.sem_configure_offset_absolute_limit_array(
                updated_selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_absolute_limit(
        self, selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
    ):
        r"""Configures the start and the stop limit of an offset segment.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, and offset number.

                Example:

                "subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            offset_absolute_limit_start (float):
                This parameter specifies the absolute power limit corresponding to the beginning of an offset segment. This value is
                expressed in dBm. The default value is -16.5.

            offset_absolute_limit_stop (float):
                This parameter specifies the absolute power limit corresponding to the end of an offset segment. This value is
                expressed in dBm. The default value is -16.5.

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
            error_code = self._interpreter.sem_configure_offset_absolute_limit(
                updated_selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_bandwidth_integral_array(self, selector_string, offset_bandwidth_integral):
        r"""Configures the array of the bandwidth integral of the offset segments.

        Use "subblock<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and subblock number.

                Example:

                "subblock0"

                "result::r1/subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            offset_bandwidth_integral (int):
                This parameter specifies the array of the resolution values of the spectrum to compare with the spectral mask limits as
                an integer multiple of the RBW. The default value is 1.

                When you set this parameter to a value greater than 1, the measurement acquires the spectrum with a narrow
                resolution and then processes it digitally to get a wider resolution that is equal to the product of a bandwidth
                integral and an RBW.

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
            error_code = self._interpreter.sem_configure_offset_bandwidth_integral_array(
                updated_selector_string, offset_bandwidth_integral
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_bandwidth_integral(self, selector_string, offset_bandwidth_integral):
        r"""Configures the bandwidth integral of the offset segments.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, and offset number.

                Example:

                "subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            offset_bandwidth_integral (int):
                This parameter specifies the resolution of the spectrum to compare with the spectral mask limits as an integer multiple
                of the RBW. The default value is 1.

                When you set this parameter to a value greater than 1, the measurement acquires the spectrum with a narrow
                resolution and then processes it digitally to get a wider resolution that is equal to the product of a bandwidth
                integral and a RBW.

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
            error_code = self._interpreter.sem_configure_offset_bandwidth_integral(
                updated_selector_string, offset_bandwidth_integral
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_frequency_array(
        self, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
    ):
        r"""Configures the arrays of the start and stop frequencies and the sideband of an offset segment.

        Use "subblock<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and subblock number.

                Example:

                "subblock0"

                "result::r1/subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            offset_start_frequency (float):
                This parameter specifies the array of the start frequency values of the offset segment relative to the carrier channel
                bandwidth edge (single-carrier) or the subblock aggregated channel bandwidth edge (multi-carrier). This value is
                expressed in Hz. The default value is 0.

            offset_stop_frequency (float):
                This parameter specifies the array of the stop frequency values of the offset segment relative to the carrier channel
                bandwidth edge (single-carrier) or the subblock aggregated channel bandwidth edge (multi-carrier). This value is
                expressed in Hz. The default value is 1 MHz.

            offset_sideband (enums.SemOffsetSideband, int):
                This parameter specifies whether the offset segment is present on one side, or on both sides of the carrier for each
                offset. The default value is **Both**.

                +--------------+---------------------------------------------------------------------------+
                | Name (Value) | Description                                                               |
                +==============+===========================================================================+
                | Neg (0)      | Configures a lower offset segment to the left of the leftmost carrier.    |
                +--------------+---------------------------------------------------------------------------+
                | Pos (1)      | Configures an upper offset segment to the right of the rightmost carrier. |
                +--------------+---------------------------------------------------------------------------+
                | Both (2)     | Configures both the negative and the positive offset segments.            |
                +--------------+---------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            offset_sideband = (
                [v.value for v in offset_sideband]
                if (
                    isinstance(offset_sideband, list)
                    and all(isinstance(v, enums.SemOffsetSideband) for v in offset_sideband)
                )
                else offset_sideband
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_offset_frequency_array(
                updated_selector_string,
                offset_start_frequency,
                offset_stop_frequency,
                offset_sideband,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_frequency(
        self, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
    ):
        r"""Configures the start and stop frequencies and the sideband of an offset segment.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to configure from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, and offset number.

                Example:

                "subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            offset_start_frequency (float):
                This parameter specifies the start frequency of an offset segment relative to the carrier channel bandwidth edge
                (single-carrier) or the subblock aggregated channel bandwidth edge (multi-carrier). This value is expressed in Hz. The
                default value is 0.

            offset_stop_frequency (float):
                This parameter specifies the stop frequency of an offset segment relative to the carrier channel bandwidth edge
                (single-carrier) or the subblock aggregated channel bandwidth edge (multi-carrier). This value is expressed in Hz. The
                default value is 1 MHz.

            offset_sideband (enums.SemOffsetSideband, int):
                This parameter specifies whether the offset segment is present on one side, or on both sides of the carrier. The
                default value is **Both**.

                +--------------+---------------------------------------------------------------------------+
                | Name (Value) | Description                                                               |
                +==============+===========================================================================+
                | Neg (0)      | Configures a lower offset segment to the left of the leftmost carrier.    |
                +--------------+---------------------------------------------------------------------------+
                | Pos (1)      | Configures an upper offset segment to the right of the rightmost carrier. |
                +--------------+---------------------------------------------------------------------------+
                | Both (2)     | Configures both the negative and the positive offset segments.            |
                +--------------+---------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            offset_sideband = (
                offset_sideband.value
                if type(offset_sideband) is enums.SemOffsetSideband
                else offset_sideband
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_offset_frequency(
                updated_selector_string,
                offset_start_frequency,
                offset_stop_frequency,
                offset_sideband,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_limit_fail_mask_array(self, selector_string, limit_fail_mask):
        r"""Configures the array of limit fail mask of the offset segments that specifies the criteria to determine the measurement
        fail status.

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

            limit_fail_mask (enums.SemOffsetLimitFailMask, int):
                This parameter specifies the array of criterion to determine the measurement fail status. The default value is
                **Absolute**.

                .. note::
                   When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, all the values
                   of limit fail mask are supported but when you set the Link Direction attribute to **Uplink**, the measurement
                   internally sets the value of limit fail mask to **Absolute**.

                +-----------------+-------------------------------------------------------------------------------------------------------------+
                | Name (Value)    | Description                                                                                                 |
                +=================+=============================================================================================================+
                | Abs AND Rel (0) | Specifies the fail in measurement if the power in the segment exceeds both the absolute and relative masks. |
                +-----------------+-------------------------------------------------------------------------------------------------------------+
                | Abs OR Rel (1)  | Specifies the fail in measurement if the power in the segment exceeds either the absolute or relative mask. |
                +-----------------+-------------------------------------------------------------------------------------------------------------+
                | Absolute (2)    | Specifies the fail in measurement if the power in the segment exceeds the absolute mask.                    |
                +-----------------+-------------------------------------------------------------------------------------------------------------+
                | Relative (3)    | Specifies the fail in measurement if the power in the segment exceeds the relative mask.                    |
                +-----------------+-------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            limit_fail_mask = (
                [v.value for v in limit_fail_mask]
                if (
                    isinstance(limit_fail_mask, list)
                    and all(isinstance(v, enums.SemOffsetLimitFailMask) for v in limit_fail_mask)
                )
                else limit_fail_mask
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_offset_limit_fail_mask_array(
                updated_selector_string, limit_fail_mask
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_limit_fail_mask(self, selector_string, limit_fail_mask):
        r"""Configures the limit fail mask of the offset segments that specify the criteria to determine the measurement fail
        status.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, and offset number.

                Example:

                "subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            limit_fail_mask (enums.SemOffsetLimitFailMask, int):
                This parameter specifies the criteria to determine the measurement fail status. The default value is **Absolute**.

                .. note::
                   When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, all the values
                   of limit fail mask are supported but when you set the Link Direction attribute to **Uplink**, the measurement
                   internally sets the value of limit fail mask to **Absolute**.

                +-----------------+-------------------------------------------------------------------------------------------------------------+
                | Name (Value)    | Description                                                                                                 |
                +=================+=============================================================================================================+
                | Abs AND Rel (0) | Specifies the fail in measurement if the power in the segment exceeds both the absolute and relative masks. |
                +-----------------+-------------------------------------------------------------------------------------------------------------+
                | Abs OR Rel (1)  | Specifies the fail in measurement if the power in the segment exceeds either the absolute or relative mask. |
                +-----------------+-------------------------------------------------------------------------------------------------------------+
                | Absolute (2)    | Specifies the fail in measurement if the power in the segment exceeds the absolute mask.                    |
                +-----------------+-------------------------------------------------------------------------------------------------------------+
                | Relative (3)    | Specifies the fail in measurement if the power in the segment exceeds the relative mask.                    |
                +-----------------+-------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            limit_fail_mask = (
                limit_fail_mask.value
                if type(limit_fail_mask) is enums.SemOffsetLimitFailMask
                else limit_fail_mask
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_offset_limit_fail_mask(
                updated_selector_string, limit_fail_mask
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_rbw_filter_array(
        self, selector_string, offset_rbw, offset_rbw_filter_type
    ):
        r"""Configures the offset RBW and the offset RBW filter type arrays.

        Use "subblock<*n*>" as the selector string to configure from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and subblock number.

                Example:

                "subblock0"

                "result::r1/subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            offset_rbw (float):
                This parameter specifies the array of the RBW filter bandwidth values used to sweep the acquired offset segment, when
                you set the SEM Offset RBW Auto attribute to False. This value is expressed in Hz. The default value is 30000.

            offset_rbw_filter_type (enums.SemOffsetRbwFilterType, int):
                This parameter specifies the array of the shape of a digital RBW filter. The default value is **Gaussian**.

                +---------------+-----------------------------------------+
                | Name (Value)  | Description                             |
                +===============+=========================================+
                | FFT Based (0) | No RBW filtering is performed.          |
                +---------------+-----------------------------------------+
                | Gaussian (1)  | The RBW filter has a Gaussian response. |
                +---------------+-----------------------------------------+
                | Flat (2)      | The RBW filter has a flat response.     |
                +---------------+-----------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            offset_rbw_filter_type = (
                [v.value for v in offset_rbw_filter_type]
                if (
                    isinstance(offset_rbw_filter_type, list)
                    and all(
                        isinstance(v, enums.SemOffsetRbwFilterType) for v in offset_rbw_filter_type
                    )
                )
                else offset_rbw_filter_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_offset_rbw_filter_array(
                updated_selector_string, offset_rbw, offset_rbw_filter_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_rbw_filter(self, selector_string, offset_rbw, offset_rbw_filter_type):
        r"""Configures the offset RBW and the offset RBW filter type.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, and offset number.

                Example:

                "subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            offset_rbw (float):
                This parameter specifies the bandwidth of an RBW filter used to sweep an acquired offset segment. This value is
                expressed in Hz.

                The default value is 30000 Hz.

            offset_rbw_filter_type (enums.SemOffsetRbwFilterType, int):
                This parameter specifies the shape of the digital RBW filter. The default value is **Gaussian**.

                +---------------+-----------------------------------------+
                | Name (Value)  | Description                             |
                +===============+=========================================+
                | FFT Based (0) | No RBW filtering is performed.          |
                +---------------+-----------------------------------------+
                | Gaussian (1)  | The RBW filter has a Gaussian response. |
                +---------------+-----------------------------------------+
                | Flat (2)      | The RBW filter has a flat response.     |
                +---------------+-----------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            offset_rbw_filter_type = (
                offset_rbw_filter_type.value
                if type(offset_rbw_filter_type) is enums.SemOffsetRbwFilterType
                else offset_rbw_filter_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_offset_rbw_filter(
                updated_selector_string, offset_rbw, offset_rbw_filter_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_relative_limit_array(
        self, selector_string, relative_limit_start, relative_limit_stop
    ):
        r"""Configures the array of start and stop relative limits of the offset segments.

        Use "subblock<*n*>" as the selector string to read results from this method.

        .. note::
           This method is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute
           to **Downlink** and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Custom**.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and subblock number.

                Example:

                "subblock0"

                "result::r1/subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            relative_limit_start (float):
                This parameter specifies the array of relative power limits corresponding to the beginning of the offset segment. This
                value is expressed in dB. The default value is -51.5.

            relative_limit_stop (float):
                This parameter specifies the array of relative power limits corresponding to the end of the offset segment. This value
                is expressed in dB. The default value is -51.5.

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
            error_code = self._interpreter.sem_configure_offset_relative_limit_array(
                updated_selector_string, relative_limit_start, relative_limit_stop
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_relative_limit(
        self, selector_string, relative_limit_start, relative_limit_stop
    ):
        r"""Configures the start and stop relative limit of the offset segment.

        Use "offset<*n*>" or "subblock<*n*>/offset<*n*>" as the selector string to read results from this method.

        .. note::
           This method is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute
           to **Downlink** and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Custom**.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number, and offset number.

                Example:

                "subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            relative_limit_start (float):
                This parameter specifies the relative power limit corresponding to the beginning of the offset segment. This value is
                expressed in dB. The default value is -51.5.

            relative_limit_stop (float):
                This parameter specifies the relative power limit corresponding to the end of the offset segment. This value is
                expressed in dB. The default value is -51.5.

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
            error_code = self._interpreter.sem_configure_offset_relative_limit(
                updated_selector_string, relative_limit_start, relative_limit_stop
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

            sweep_time_auto (enums.SemSweepTimeAuto, int):
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
                if type(sweep_time_auto) is enums.SemSweepTimeAuto
                else sweep_time_auto
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_sweep_time(
                updated_selector_string, sweep_time_auto, sweep_time_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_uplink_mask_type(self, selector_string, uplink_mask_type):
        r"""Configures the standard defined mask type that has to be used in the measurement for uplink.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            uplink_mask_type (enums.SemUplinkMaskType, int):
                This parameter specifies the standard-defined spectrum emission mask used in the measurement for uplink. The following
                mask types are supported: **General (NS_01)**, **NS_03 or NS_11 or NS_20 or NS_21**, **NS_04**, **NS_06 or NS_07**,
                **CA_NS_04**,
                **Custom**, **General CA Class B**, **CA_NC_NS_01**, **NS_27**, and **NS_35**. Each mask type refers to a different
                Network Signalled (NS) value. **CA_NS_04** and **CA_NC_NS_01** refers to carrier aggregation case. You must set the
                mask type to **CUSTOM** to configure the custom offset masks.
                Refer to section 6.6.2.1 of the *3GPP 36.521* specification for more information about standard-defined mask
                types.

                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)                         | Description                                                                                                              |
                +======================================+==========================================================================================================================+
                | General (NS_01) (0)                  | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1.5-1, 6.6.2.1.5-2,      |
                |                                      | 6.6.2.1A.5-1, and 6.6.2.1A.5-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                   |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | NS_03 or NS_11 or NS_20 or NS_21 (1) | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.1-1 and              |
                |                                      | 6.6.2.2.5.1-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                    |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | NS_04 (2)                            | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.3.2-3 in section       |
                |                                      | 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                             |
                |                                      | When CC Bandwidth is 1.4 M or 3.0 M, the measurement selects the offset frequencies and limits for the SEM as defined    |
                |                                      | in Table 6.6.2.2.5.2-1 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                           |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | NS_06 or NS_07 (3)                   | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.3-1 and              |
                |                                      | 6.6.2.2.5.3-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                    |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | CA_NS_04 (4)                         | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.1.5.1-1 in section    |
                |                                      | 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                             |
                |                                      | This mask applies only for aggregated carriers.                                                                          |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Custom (5)                           | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
                |                                      | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type,  |
                |                                      | and SEM Offset BW Integral attributes for each offset.                                                                   |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | General CA Class B (6)               | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.1A.1.5-3 and 6.6.2.1A.1.5-4  |
                |                                      | in section 6.6.2 of 3GPP TS 36.521-1 specification.                                                                      |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | CA_NC_NS_01 (7)                      | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.3.5-1 and 6.6.2.2A.3.5-2  |
                |                                      | in section 6.6.2 of 3GPP TS 36.521-1 specification.                                                                      |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | NS_27 (8)                            | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.4-1 in section           |
                |                                      | 6.6.2.2.5.4 of 3GPP TS 36.521-1 specification.                                                                           |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | NS_35 (9)                            | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.5-1 in section           |
                |                                      | 6.6.2.2.5.5 of 3GPP TS 36.521-1 specification.                                                                           |
                +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            uplink_mask_type = (
                uplink_mask_type.value
                if type(uplink_mask_type) is enums.SemUplinkMaskType
                else uplink_mask_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_uplink_mask_type(
                updated_selector_string, uplink_mask_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
