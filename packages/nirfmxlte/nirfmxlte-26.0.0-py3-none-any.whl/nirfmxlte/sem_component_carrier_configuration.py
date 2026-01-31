""""""

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


class SemComponentCarrierConfiguration(object):
    """"""

    def __init__(self, signal_obj):
        """"""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of a component carrier. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.

        The default value is 9 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the integration bandwidth of a component carrier. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_maximum_output_power(self, selector_string):
        r"""Gets the maximum output power, P\ :sub:`max,c`\, per carrier that is used only to choose the limit table for
        Medium Range Base Station. For more details please refer to the section 6.6.3 of *3GPP 36.141* specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are within 38, inclusive.

        .. note::
           This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
           attribute to **Downlink**, :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute to **Medium Range
           Base Station**, and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **eNodeB Category
           Based**. When you set Bandwidth to  **200k**  the maximum output power, P\ :sub:`max,c`\, per carrier used to choose
           limit table and to calculate the mask.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the maximum output power, P\ :sub:`max,c`\, per carrier that is used only to choose the limit table for
                Medium Range Base Station. For more details please refer to the section 6.6.3 of *3GPP 36.141* specification.

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
                attributes.AttributeID.SEM_COMPONENT_CARRIER_MAXIMUM_OUTPUT_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_maximum_output_power(self, selector_string, value):
        r"""Sets the maximum output power, P\ :sub:`max,c`\, per carrier that is used only to choose the limit table for
        Medium Range Base Station. For more details please refer to the section 6.6.3 of *3GPP 36.141* specification.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.

        The default value is 0. Valid values are within 38, inclusive.

        .. note::
           This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
           attribute to **Downlink**, :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute to **Medium Range
           Base Station**, and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **eNodeB Category
           Based**. When you set Bandwidth to  **200k**  the maximum output power, P\ :sub:`max,c`\, per carrier used to choose
           limit table and to calculate the mask.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the maximum output power, P\ :sub:`max,c`\, per carrier that is used only to choose the limit table for
                Medium Range Base Station. For more details please refer to the section 6.6.3 of *3GPP 36.141* specification.

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
                attributes.AttributeID.SEM_COMPONENT_CARRIER_MAXIMUM_OUTPUT_POWER.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_maximum_output_power_array(
        self, selector_string, component_carrier_maximum_output_power
    ):
        r"""Configures the array of maximum output power of the component carrier.

        Use "subblock<*n*>" as the selector string to configure this method.

        .. note::
           This method is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute
           to **Downlink**, :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute to **Medium Range Base
           Station**, and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **eNodeB Category
           Based**.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.  The default is "" (empty
                string).

                Example:

                "subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            component_carrier_maximum_output_power (float):
                This parameter specifies the array of maximum output power per carrier, which is used only to choose the limit table
                for Medium Range Base Station. This value is expressed in dBm. Refer to the section 6.6.3 of the *3GPP 36.141*
                specification for more details. The default value is 0. Valid values are 0 to 38, inclusive.

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
            error_code = self._interpreter.sem_configure_maximum_output_power_array(
                updated_selector_string, component_carrier_maximum_output_power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_maximum_output_power(
        self, selector_string, component_carrier_maximum_output_power
    ):
        r"""Configures the maximum output power of the component carrier.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        .. note::
           This method is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute
           to **Downlink**, :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute to **Medium Range Base
           Station**, and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **eNodeB Category
           Based**.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number. The default
                value is "subblock0/carrier0".

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            component_carrier_maximum_output_power (float):
                This parameter specifies the maximum output power per carrier, which is used only to choose the limit table for Medium
                Range Base Station. This value is expressed in dBm. Refer to the section 6.6.3 of the *3GPP 36.141* specification for
                more details. The default value is 0. Valid values are 0 to 38, inclusive.

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
            error_code = self._interpreter.sem_configure_maximum_output_power(
                updated_selector_string, component_carrier_maximum_output_power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
