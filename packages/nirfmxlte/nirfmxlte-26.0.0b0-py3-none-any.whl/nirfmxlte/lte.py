"""Defines a root class which is used to identify and control Lte signal configuration."""

import functools
import math

import nirfmxinstr
import nirfmxlte.acp as acp
import nirfmxlte.attributes as attributes
import nirfmxlte.chp as chp
import nirfmxlte.component_carrier as component_carrier
import nirfmxlte.enums as enums
import nirfmxlte.errors as errors
import nirfmxlte.internal._helper as _helper
import nirfmxlte.modacc as modacc
import nirfmxlte.obw as obw
import nirfmxlte.pvt as pvt
import nirfmxlte.sem as sem
import nirfmxlte.slotphase as slotphase
import nirfmxlte.slotpower as slotpower
import nirfmxlte.txp as txp
from nirfmxlte.internal._helper import SignalConfiguration
from nirfmxlte.internal._library_interpreter import LibraryInterpreter


class _LteSignalConfiguration:
    """Contains static methods to create and delete Lte signal."""

    @staticmethod
    def get_lte_signal_configuration(instr_session, signal_name="", cloning=False):
        updated_signal_name = signal_name
        if signal_name:
            updated_signal_name = _helper.validate_and_remove_signal_qualifier(
                signal_name, "signal_name"
            )
            _helper.validate_signal_not_empty(updated_signal_name, "signal_name")
        return _LteSignalConfiguration.init(instr_session, updated_signal_name, cloning)  # type: ignore

    @staticmethod
    def init(instr_session, signal_name, cloning):
        with instr_session._signal_lock:
            if signal_name.lower() == Lte._default_signal_name_user_visible.lower():
                signal_name = Lte._default_signal_name

            existing_signal = instr_session._signal_manager.find_signal_configuration(
                Lte._signal_configuration_type, signal_name
            )
            if existing_signal is None:
                signal_configuration = Lte(instr_session, signal_name, cloning)  # type: ignore
                instr_session._signal_manager.add_signal_configuration(signal_configuration)
            else:
                signal_configuration = existing_signal
                # Checking if signal exists in C layer
                if signal_configuration._interpreter.check_if_current_signal_exists() is False:
                    if not signal_configuration.signal_configuration_name.lower():
                        instr_session._interpreter.create_default_signal_configuration(
                            Lte._default_signal_name_user_visible,
                            int(math.log(nirfmxinstr.Personalities.LTE.value, 2.0)) + 1,
                        )
                    else:
                        signal_configuration._interpreter.create_signal_configuration(signal_name)

            return signal_configuration

    @staticmethod
    def remove_signal_configuration(instr_session, signal_configuration):
        with instr_session._signal_lock:
            instr_session._signal_manager.remove_signal_configuration(signal_configuration)


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        signal = xs[0]  # parameter 0 is 'self' which is the signal object
        if signal.is_disposed:
            raise Exception("Cannot access a disposed Lte signal configuration")
        return f(*xs, **kws)

    return aux


class _LteBase(SignalConfiguration):
    """Defines a base class for Lte."""

    _default_signal_name = ""
    _default_signal_name_user_visible = "default@LTE"
    _signal_configuration_type = "<'nirfmxlte.lte.Lte'>"

    def __init__(self, session, signal_name="", cloning=False):
        self.is_disposed = False
        self._rfmxinstrsession = session
        self._rfmxinstrsession_interpreter = session._interpreter
        self.signal_configuration_name = signal_name
        self.signal_configuration_type = type(self)  # type: ignore
        self._signal_configuration_mode = "Signal"
        if session._is_remote_session:
            import nirfmxlte.internal._grpc_stub_interpreter as _grpc_stub_interpreter

            interpreter = _grpc_stub_interpreter.GrpcStubInterpreter(session._grpc_options, session, self)  # type: ignore
        else:
            interpreter = LibraryInterpreter("windows-1251", session, self)  # type: ignore

        self._interpreter = interpreter
        self._interpreter.set_session_handle(self._rfmxinstrsession_interpreter._vi)  # type: ignore
        self._session_function_lock = _helper.SessionFunctionLock()

        # Measurements object
        self.acp = acp.Acp(self)  # type: ignore
        self.chp = chp.Chp(self)  # type: ignore
        self.modacc = modacc.ModAcc(self)  # type: ignore
        self.obw = obw.Obw(self)  # type: ignore
        self.sem = sem.Sem(self)  # type: ignore
        self.pvt = pvt.Pvt(self)  # type: ignore
        self.slotphase = slotphase.SlotPhase(self)  # type: ignore
        self.slotpower = slotpower.SlotPower(self)  # type: ignore
        self.txp = txp.Txp(self)  # type: ignore
        self.component_carrier = component_carrier.ComponentCarrier(self)  # type: ignore

        if not signal_name and not cloning:
            signal_exists, personality, _ = (
                self._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._default_signal_name_user_visible
                )
            )
            if not (signal_exists and personality.value == nirfmxinstr.Personalities.LTE.value):
                self._rfmxinstrsession_interpreter.create_default_signal_configuration(
                    self._default_signal_name_user_visible,
                    int(math.log(nirfmxinstr.Personalities.LTE.value, 2.0)) + 1,
                )
        elif signal_name and not cloning:
            signal_exists, personality, _ = (
                self._rfmxinstrsession_interpreter.check_if_signal_exists(signal_name)
            )
            if not (signal_exists and personality.value == nirfmxinstr.Personalities.LTE.value):
                self._interpreter.create_signal_configuration(signal_name)  # type: ignore

    def __enter__(self):
        """Enters the context of the Lte signal configuration."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context of the Lte signal configuration."""
        self.dispose()  # type: ignore
        pass

    def dispose(self):
        r"""Deletes the signal configuration if it is not the default signal configuration
        and clears any trace of the current signal configuration, if any.

        .. note::
            You can call this function safely more than once, even if the signal is already deleted.
        """
        if not self.is_disposed:
            if self.signal_configuration_name == self._default_signal_name:
                self.is_disposed = True
                return
            else:
                _ = self._delete_signal_configuration(True)  # type: ignore
                self.is_disposed = True

    @_raise_if_disposed
    def delete_signal_configuration(self):
        r"""Deletes the current instance of a signal.

        Returns:
            error_code:
                Returns the status code of this method.
                The status code either indicates success or describes a warning condition.
        """
        error_code = self._delete_signal_configuration(False)  # type: ignore
        return error_code

    def _delete_signal_configuration(self, ignore_driver_error):
        error_code = 0
        try:
            if not self.is_disposed:
                self._session_function_lock.enter_write_lock()
                error_code = self._interpreter.delete_signal_configuration(ignore_driver_error)  # type: ignore
                _LteSignalConfiguration.remove_signal_configuration(self._rfmxinstrsession, self)  # type: ignore
                self.is_disposed = True
        finally:
            self._session_function_lock.exit_write_lock()

        return error_code

    @_raise_if_disposed
    def get_warning(self):
        r"""Retrieves and then clears the warning information for the session.

        Returns:
            Tuple (warning_code, warning_message):

            warning_code (int):
                Contains the latest warning code.

            warning_message (string):
                Contains the latest warning description.
        """
        try:
            self._session_function_lock.enter_read_lock()
            warning_code, warning_message = self._interpreter.get_error()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return warning_code, warning_message

    @_raise_if_disposed
    def get_error_string(self, error_code):
        r"""Gets the description of a driver error code.

        Args:
            error_code (int):
                Specifies an error or warning code.

        Returns:
            string:
                Contains the error description.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_message = self._interpreter.get_error_string(error_code)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_message

    @_raise_if_disposed
    def reset_attribute(self, selector_string, attribute_id):
        r"""Resets the attribute to its default value.

        Args:
            selector_string (string):
                Specifies the selector string for the property being reset.

            attribute_id (PropertyId):
                Specifies an attribute identifier.

        Returns:
            int:
                Returns the status code of this method.
                The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attribute_id = (
                attribute_id.value if type(attribute_id) is attributes.AttributeID else attribute_id
            )
            error_code = self._interpreter.reset_attribute(  # type: ignore
                updated_selector_string, attribute_id
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_selected_ports(self, selector_string):
        r"""Gets the instrument port to be configured to acquire a signal. Use
        :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Valid values**

        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (value)   | Description                                                                                                              |
        +================+==========================================================================================================================+
        | PXIe-5830      | if0, if1                                                                                                                 |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | PXIe-5831/5832 | if0, if1, rf<0-1>/port<x>, where 0-1 indicates one (0) or two (1) mmRH-5582 connections and x is the port number on the  |
        |                | mmRH-5582 front panel                                                                                                    |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Other devices  | "" (empty string)                                                                                                        |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+

        **Default values**

        +---------------------+-------------------+
        | Name (value)        | Description       |
        +=====================+===================+
        | PXIe-5830/5831/5832 | if1               |
        +---------------------+-------------------+
        | Other devices       | "" (empty string) |
        +---------------------+-------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the instrument port to be configured to acquire a signal. Use
                :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.SELECTED_PORTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_selected_ports(self, selector_string, value):
        r"""Sets the instrument port to be configured to acquire a signal. Use
        :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Valid values**

        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (value)   | Description                                                                                                              |
        +================+==========================================================================================================================+
        | PXIe-5830      | if0, if1                                                                                                                 |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | PXIe-5831/5832 | if0, if1, rf<0-1>/port<x>, where 0-1 indicates one (0) or two (1) mmRH-5582 connections and x is the port number on the  |
        |                | mmRH-5582 front panel                                                                                                    |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Other devices  | "" (empty string)                                                                                                        |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+

        **Default values**

        +---------------------+-------------------+
        | Name (value)        | Description       |
        +=====================+===================+
        | PXIe-5830/5831/5832 | if1               |
        +---------------------+-------------------+
        | Other devices       | "" (empty string) |
        +---------------------+-------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the instrument port to be configured to acquire a signal. Use
                :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.SELECTED_PORTS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_center_frequency(self, selector_string):
        r"""Gets the center frequency of the acquired RF signal for a single carrier.

        For intra-band carrier aggregation, this attribute specifies the reference frequency of the subblock. This
        value is expressed in Hz.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the center frequency of the acquired RF signal for a single carrier.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_center_frequency(self, selector_string, value):
        r"""Sets the center frequency of the acquired RF signal for a single carrier.

        For intra-band carrier aggregation, this attribute specifies the reference frequency of the subblock. This
        value is expressed in Hz.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the center frequency of the acquired RF signal for a single carrier.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_level(self, selector_string):
        r"""Gets the reference level which represents the maximum expected power of the RF input signal. This value is
        configured in dBm for RF devices and as Vpk-pk for baseband devices.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
                configured in dBm for RF devices and as Vpk-pk for baseband devices.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_level(self, selector_string, value):
        r"""Sets the reference level which represents the maximum expected power of the RF input signal. This value is
        configured in dBm for RF devices and as Vpk-pk for baseband devices.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
                configured in dBm for RF devices and as Vpk-pk for baseband devices.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_external_attenuation(self, selector_string):
        r"""Gets the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer. This value is
        expressed in dB. Refer to the RF Attenuation and Signal Levels topic for your device in the *NI RF Vector Signal
        Analyzers Help* for more information about attenuation.

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
                Specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer. This value is
                expressed in dB. Refer to the RF Attenuation and Signal Levels topic for your device in the *NI RF Vector Signal
                Analyzers Help* for more information about attenuation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.EXTERNAL_ATTENUATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_external_attenuation(self, selector_string, value):
        r"""Sets the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer. This value is
        expressed in dB. Refer to the RF Attenuation and Signal Levels topic for your device in the *NI RF Vector Signal
        Analyzers Help* for more information about attenuation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer. This value is
                expressed in dB. Refer to the RF Attenuation and Signal Levels topic for your device in the *NI RF Vector Signal
                Analyzers Help* for more information about attenuation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.EXTERNAL_ATTENUATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_level_headroom(self, selector_string):
        r"""Gets the margin RFmx adds to the :py:attr:`~nirfmxlte.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
        margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
        power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
        power of the signal precisely or previously included the margin in the Reference Level, you could improve the
        signal-to-noise ratio by reducing the Reference Level Headroom.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Supported devices: **PXIe-5668, PXIe-5830/5831/5832/5840/5841/5842/5860.

        **Default values**

        +------------------------------------+-------------+
        | Name (value)                       | Description |
        +====================================+=============+
        | PXIe-5668                          | 6 dB        |
        +------------------------------------+-------------+
        | PXIe-5830/5831/5832/5841/5842/5860 | 1 dB        |
        +------------------------------------+-------------+
        | PXIe-5840                          | 0 dB        |
        +------------------------------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the margin RFmx adds to the :py:attr:`~nirfmxlte.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
                margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL_HEADROOM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_level_headroom(self, selector_string, value):
        r"""Sets the margin RFmx adds to the :py:attr:`~nirfmxlte.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
        margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
        power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
        power of the signal precisely or previously included the margin in the Reference Level, you could improve the
        signal-to-noise ratio by reducing the Reference Level Headroom.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Supported devices: **PXIe-5668, PXIe-5830/5831/5832/5840/5841/5842/5860.

        **Default values**

        +------------------------------------+-------------+
        | Name (value)                       | Description |
        +====================================+=============+
        | PXIe-5668                          | 6 dB        |
        +------------------------------------+-------------+
        | PXIe-5830/5831/5832/5841/5842/5860 | 1 dB        |
        +------------------------------------+-------------+
        | PXIe-5840                          | 0 dB        |
        +------------------------------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the margin RFmx adds to the :py:attr:`~nirfmxlte.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
                margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.REFERENCE_LEVEL_HEADROOM.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_type(self, selector_string):
        r"""Gets the trigger type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **None**.

        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                                                              |
        +===================+==========================================================================================================================+
        | None (0)          | No Reference Trigger is configured.                                                                                      |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Digital Edge (1)  | The Reference Trigger is not asserted until a digital edge is detected. The source of the digital edge is specified      |
        |                   | using the Digital Edge Source attribute.                                                                                 |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | IQ Power Edge (2) | The Reference Trigger is asserted when the signal changes past the level specified by the slope (rising or falling),     |
        |                   | which is configured using the IQ Power Edge Slope attribute.                                                             |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Software (3)      | The Reference Trigger is not asserted until a software trigger occurs.                                                   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerType):
                Specifies the trigger type.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_TYPE.value
            )
            attr_val = enums.TriggerType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_type(self, selector_string, value):
        r"""Sets the trigger type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **None**.

        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                                                              |
        +===================+==========================================================================================================================+
        | None (0)          | No Reference Trigger is configured.                                                                                      |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Digital Edge (1)  | The Reference Trigger is not asserted until a digital edge is detected. The source of the digital edge is specified      |
        |                   | using the Digital Edge Source attribute.                                                                                 |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | IQ Power Edge (2) | The Reference Trigger is asserted when the signal changes past the level specified by the slope (rising or falling),     |
        |                   | which is configured using the IQ Power Edge Slope attribute.                                                             |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Software (3)      | The Reference Trigger is not asserted until a software trigger occurs.                                                   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerType, int):
                Specifies the trigger type.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_digital_edge_trigger_source(self, selector_string):
        r"""Gets the source terminal for the digital edge trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_digital_edge_trigger_source(self, selector_string, value):
        r"""Sets the source terminal for the digital edge trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_digital_edge_trigger_edge(self, selector_string):
        r"""Gets the active edge for the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Edge**.

        +------------------+--------------------------------------------------------+
        | Name (Value)     | Description                                            |
        +==================+========================================================+
        | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
        +------------------+--------------------------------------------------------+
        | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
        +------------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DigitalEdgeTriggerEdge):
                Specifies the active edge for the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIGITAL_EDGE_TRIGGER_EDGE.value
            )
            attr_val = enums.DigitalEdgeTriggerEdge(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_digital_edge_trigger_edge(self, selector_string, value):
        r"""Sets the active edge for the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Edge**.

        +------------------+--------------------------------------------------------+
        | Name (Value)     | Description                                            |
        +==================+========================================================+
        | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
        +------------------+--------------------------------------------------------+
        | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
        +------------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DigitalEdgeTriggerEdge, int):
                Specifies the active edge for the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.DigitalEdgeTriggerEdge else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DIGITAL_EDGE_TRIGGER_EDGE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_source(self, selector_string):
        r"""Gets the channel from which the device monitors the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the channel from which the device monitors the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SOURCE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_source(self, selector_string, value):
        r"""Sets the channel from which the device monitors the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the channel from which the device monitors the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SOURCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_level(self, selector_string):
        r"""Gets the power level at which the device triggers. This value is expressed in dB when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm when
        you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
        the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
        used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power level at which the device triggers. This value is expressed in dB when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm when
                you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
                the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
                used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_level(self, selector_string, value):
        r"""Sets the power level at which the device triggers. This value is expressed in dB when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm when
        you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
        the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
        used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power level at which the device triggers. This value is expressed in dB when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm when
                you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
                the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
                used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_level_type(self, selector_string):
        r"""Gets the reference for the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
        IQ Power Edge Level Type attribute is used only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Relative**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
        +--------------+----------------------------------------------------------------------------------------------+
        | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.IQPowerEdgeTriggerLevelType):
                Specifies the reference for the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
                IQ Power Edge Level Type attribute is used only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE.value,
            )
            attr_val = enums.IQPowerEdgeTriggerLevelType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_level_type(self, selector_string, value):
        r"""Sets the reference for the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
        IQ Power Edge Level Type attribute is used only when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Relative**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
        +--------------+----------------------------------------------------------------------------------------------+
        | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.IQPowerEdgeTriggerLevelType, int):
                Specifies the reference for the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
                IQ Power Edge Level Type attribute is used only when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.IQPowerEdgeTriggerLevelType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_slope(self, selector_string):
        r"""Gets whether the device asserts the trigger when the signal power is rising or when it is falling. The device
        asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
        used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Slope**.

        +-------------------+-------------------------------------------------------+
        | Name (Value)      | Description                                           |
        +===================+=======================================================+
        | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
        +-------------------+-------------------------------------------------------+
        | Falling Slope (1) | The trigger asserts when the signal power is falling. |
        +-------------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.IQPowerEdgeTriggerSlope):
                Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
                asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
                used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE.value
            )
            attr_val = enums.IQPowerEdgeTriggerSlope(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_slope(self, selector_string, value):
        r"""Sets whether the device asserts the trigger when the signal power is rising or when it is falling. The device
        asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
        used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Slope**.

        +-------------------+-------------------------------------------------------+
        | Name (Value)      | Description                                           |
        +===================+=======================================================+
        | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
        +-------------------+-------------------------------------------------------+
        | Falling Slope (1) | The trigger asserts when the signal power is falling. |
        +-------------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.IQPowerEdgeTriggerSlope, int):
                Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
                asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
                used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.IQPowerEdgeTriggerSlope else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_delay(self, selector_string):
        r"""Gets the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
        acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.

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
                Specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
                acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_DELAY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_delay(self, selector_string, value):
        r"""Sets the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
        acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
                acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_DELAY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_minimum_quiet_time_mode(self, selector_string):
        r"""Gets whether the measurement computes the minimum quiet time used for triggering.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+---------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                 |
        +==============+=============================================================================================+
        | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time attribute. |
        +--------------+---------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                        |
        +--------------+---------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerMinimumQuietTimeMode):
                Specifies whether the measurement computes the minimum quiet time used for triggering.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_MODE.value,
            )
            attr_val = enums.TriggerMinimumQuietTimeMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_minimum_quiet_time_mode(self, selector_string, value):
        r"""Sets whether the measurement computes the minimum quiet time used for triggering.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+---------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                 |
        +==============+=============================================================================================+
        | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time attribute. |
        +--------------+---------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                        |
        +--------------+---------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerMinimumQuietTimeMode, int):
                Specifies whether the measurement computes the minimum quiet time used for triggering.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerMinimumQuietTimeMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_minimum_quiet_time_duration(self, selector_string):
        r"""Gets the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
        trigger. This value is expressed in seconds.

        If you set the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising
        Slope**, the signal is quiet below the trigger level. If you set the IQ Power Edge Slope attribute to **Falling
        Slope**, the signal is quiet above the trigger level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
                trigger. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_minimum_quiet_time_duration(self, selector_string, value):
        r"""Sets the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
        trigger. This value is expressed in seconds.

        If you set the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising
        Slope**, the signal is quiet below the trigger level. If you set the IQ Power Edge Slope attribute to **Falling
        Slope**, the signal is quiet above the trigger level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
                trigger. This value is expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_link_direction(self, selector_string):
        r"""Gets the link direction of the received signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Uplink**.

        +--------------+---------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                           |
        +==============+=======================================================================================+
        | Downlink (0) | The measurement uses 3GPP LTE downlink specification to measure the received signal.  |
        +--------------+---------------------------------------------------------------------------------------+
        | Uplink (1)   | The measurement uses 3GPP LTE uplink specification to measure the received signal.    |
        +--------------+---------------------------------------------------------------------------------------+
        | Sidelink (2) | The measurement uses 3GPP LTE sidelink specifications to measure the received signal. |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LinkDirection):
                Specifies the link direction of the received signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.LINK_DIRECTION.value
            )
            attr_val = enums.LinkDirection(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_link_direction(self, selector_string, value):
        r"""Sets the link direction of the received signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Uplink**.

        +--------------+---------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                           |
        +==============+=======================================================================================+
        | Downlink (0) | The measurement uses 3GPP LTE downlink specification to measure the received signal.  |
        +--------------+---------------------------------------------------------------------------------------+
        | Uplink (1)   | The measurement uses 3GPP LTE uplink specification to measure the received signal.    |
        +--------------+---------------------------------------------------------------------------------------+
        | Sidelink (2) | The measurement uses 3GPP LTE sidelink specifications to measure the received signal. |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LinkDirection, int):
                Specifies the link direction of the received signal.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.LinkDirection else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.LINK_DIRECTION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_duplex_scheme(self, selector_string):
        r"""Gets the duplexing technique of the signal being measured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **FDD**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | FDD (0)      | Specifies that the duplexing technique is frequency-division duplexing. |
        +--------------+-------------------------------------------------------------------------+
        | TDD (1)      | Specifies that the duplexing technique is time-division duplexing.      |
        +--------------+-------------------------------------------------------------------------+
        | LAA (2)      | Specifies that the duplexing technique is license assisted access.      |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DuplexScheme):
                Specifies the duplexing technique of the signal being measured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DUPLEX_SCHEME.value
            )
            attr_val = enums.DuplexScheme(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_duplex_scheme(self, selector_string, value):
        r"""Sets the duplexing technique of the signal being measured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **FDD**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | FDD (0)      | Specifies that the duplexing technique is frequency-division duplexing. |
        +--------------+-------------------------------------------------------------------------+
        | TDD (1)      | Specifies that the duplexing technique is time-division duplexing.      |
        +--------------+-------------------------------------------------------------------------+
        | LAA (2)      | Specifies that the duplexing technique is license assisted access.      |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DuplexScheme, int):
                Specifies the duplexing technique of the signal being measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.DuplexScheme else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DUPLEX_SCHEME.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_uplink_downlink_configuration(self, selector_string):
        r"""Gets the configuration of the LTE frame structure in the time division duplex (TDD) mode. Refer to table 4.2-2 of
        the *3GPP TS 36.211* specification to configure the LTE frame.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **0**.

        +--------------+---------------------------------------------------------------------------+
        | Name (Value) | Description                                                               |
        +==============+===========================================================================+
        | 0 (0)        | The configuration of the LTE frame structure in the TDD duplex mode is 0. |
        +--------------+---------------------------------------------------------------------------+
        | 1 (1)        | The configuration of the LTE frame structure in the TDD duplex mode is 1. |
        +--------------+---------------------------------------------------------------------------+
        | 2 (2)        | The configuration of the LTE frame structure in the TDD duplex mode is 2. |
        +--------------+---------------------------------------------------------------------------+
        | 3 (3)        | The configuration of the LTE frame structure in the TDD duplex mode is 3. |
        +--------------+---------------------------------------------------------------------------+
        | 4 (4)        | The configuration of the LTE frame structure in the TDD duplex mode is 4. |
        +--------------+---------------------------------------------------------------------------+
        | 5 (5)        | The configuration of the LTE frame structure in the TDD duplex mode is 5. |
        +--------------+---------------------------------------------------------------------------+
        | 6 (6)        | The configuration of the LTE frame structure in the TDD duplex mode is 6. |
        +--------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.UplinkDownlinkConfiguration):
                Specifies the configuration of the LTE frame structure in the time division duplex (TDD) mode. Refer to table 4.2-2 of
                the *3GPP TS 36.211* specification to configure the LTE frame.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.UPLINK_DOWNLINK_CONFIGURATION.value
            )
            attr_val = enums.UplinkDownlinkConfiguration(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_uplink_downlink_configuration(self, selector_string, value):
        r"""Sets the configuration of the LTE frame structure in the time division duplex (TDD) mode. Refer to table 4.2-2 of
        the *3GPP TS 36.211* specification to configure the LTE frame.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **0**.

        +--------------+---------------------------------------------------------------------------+
        | Name (Value) | Description                                                               |
        +==============+===========================================================================+
        | 0 (0)        | The configuration of the LTE frame structure in the TDD duplex mode is 0. |
        +--------------+---------------------------------------------------------------------------+
        | 1 (1)        | The configuration of the LTE frame structure in the TDD duplex mode is 1. |
        +--------------+---------------------------------------------------------------------------+
        | 2 (2)        | The configuration of the LTE frame structure in the TDD duplex mode is 2. |
        +--------------+---------------------------------------------------------------------------+
        | 3 (3)        | The configuration of the LTE frame structure in the TDD duplex mode is 3. |
        +--------------+---------------------------------------------------------------------------+
        | 4 (4)        | The configuration of the LTE frame structure in the TDD duplex mode is 4. |
        +--------------+---------------------------------------------------------------------------+
        | 5 (5)        | The configuration of the LTE frame structure in the TDD duplex mode is 5. |
        +--------------+---------------------------------------------------------------------------+
        | 6 (6)        | The configuration of the LTE frame structure in the TDD duplex mode is 6. |
        +--------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.UplinkDownlinkConfiguration, int):
                Specifies the configuration of the LTE frame structure in the time division duplex (TDD) mode. Refer to table 4.2-2 of
                the *3GPP TS 36.211* specification to configure the LTE frame.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.UplinkDownlinkConfiguration else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.UPLINK_DOWNLINK_CONFIGURATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_enodeb_category(self, selector_string):
        r"""Gets the downlink eNodeB (Base station) category. Refer to the *3GPP 36.141* specification for more details.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Wide Area Base Station - Category A**.

        +--------------------------------------------------+------------------------------------------------------------------+
        | Name (Value)                                     | Description                                                      |
        +==================================================+==================================================================+
        | Wide Area Base Station - Category A (0)          | Specifies eNodeB is Wide Area Base Station - Category A.         |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Wide Area Base Station - Category B Option 1 (1) | Specifies eNodeB is Wide Area Base Station - Category B Option1. |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Wide Area Base Station - Category B Option 2 (2) | Specifies eNodeB is Wide Area Base Station - Category B Option2. |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Local Area Base Station (3)                      | Specifies eNodeB is Local Area Base Station.                     |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Home Base Station (4)                            | Specifies eNodeB is Home Base Station.                           |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Medium Range Base Station (5)                    | Specifies eNodeB is Medium Range Base Station.                   |
        +--------------------------------------------------+------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.eNodeBCategory):
                Specifies the downlink eNodeB (Base station) category. Refer to the *3GPP 36.141* specification for more details.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.ENODEB_CATEGORY.value
            )
            attr_val = enums.eNodeBCategory(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_enodeb_category(self, selector_string, value):
        r"""Sets the downlink eNodeB (Base station) category. Refer to the *3GPP 36.141* specification for more details.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Wide Area Base Station - Category A**.

        +--------------------------------------------------+------------------------------------------------------------------+
        | Name (Value)                                     | Description                                                      |
        +==================================================+==================================================================+
        | Wide Area Base Station - Category A (0)          | Specifies eNodeB is Wide Area Base Station - Category A.         |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Wide Area Base Station - Category B Option 1 (1) | Specifies eNodeB is Wide Area Base Station - Category B Option1. |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Wide Area Base Station - Category B Option 2 (2) | Specifies eNodeB is Wide Area Base Station - Category B Option2. |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Local Area Base Station (3)                      | Specifies eNodeB is Local Area Base Station.                     |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Home Base Station (4)                            | Specifies eNodeB is Home Base Station.                           |
        +--------------------------------------------------+------------------------------------------------------------------+
        | Medium Range Base Station (5)                    | Specifies eNodeB is Medium Range Base Station.                   |
        +--------------------------------------------------+------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.eNodeBCategory, int):
                Specifies the downlink eNodeB (Base station) category. Refer to the *3GPP 36.141* specification for more details.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.eNodeBCategory else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.ENODEB_CATEGORY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_special_subframe_configuration(self, selector_string):
        r"""Gets the special subframe configuration index. It defines the length of DwPTS, GP, and UpPTS for TDD transmission
        as defined in the section 4.2 of *3GPP 36.211* specification.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. Valid values are 0 to 9, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the special subframe configuration index. It defines the length of DwPTS, GP, and UpPTS for TDD transmission
                as defined in the section 4.2 of *3GPP 36.211* specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.SPECIAL_SUBFRAME_CONFIGURATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_special_subframe_configuration(self, selector_string, value):
        r"""Sets the special subframe configuration index. It defines the length of DwPTS, GP, and UpPTS for TDD transmission
        as defined in the section 4.2 of *3GPP 36.211* specification.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. Valid values are 0 to 9, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the special subframe configuration index. It defines the length of DwPTS, GP, and UpPTS for TDD transmission
                as defined in the section 4.2 of *3GPP 36.211* specification.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.SPECIAL_SUBFRAME_CONFIGURATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_dut_antennas(self, selector_string):
        r"""Gets the number of physical antennas available at the DUT for transmission in a MIMO setup.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1. Valid values are 1, 2, and 4.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of physical antennas available at the DUT for transmission in a MIMO setup.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_DUT_ANTENNAS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_dut_antennas(self, selector_string, value):
        r"""Sets the number of physical antennas available at the DUT for transmission in a MIMO setup.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1. Valid values are 1, 2, and 4.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of physical antennas available at the DUT for transmission in a MIMO setup.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_DUT_ANTENNAS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_transmit_antenna_to_analyze(self, selector_string):
        r"""Gets the physical antenna connected to the analyzer.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. Valid values are from 0 to N-1, where N is the number of DUT antennas.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the physical antenna connected to the analyzer.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_transmit_antenna_to_analyze(self, selector_string, value):
        r"""Sets the physical antenna connected to the analyzer.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0. Valid values are from 0 to N-1, where N is the number of DUT antennas.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the physical antenna connected to the analyzer.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_subblocks(self, selector_string):
        r"""Gets the number of subblocks that are configured in intra-band non-contiguous carrier aggregation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1. Set this attribute to 1 for single carrier and intra-band contiguous carrier
        aggregation.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of subblocks that are configured in intra-band non-contiguous carrier aggregation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_SUBBLOCKS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_subblocks(self, selector_string, value):
        r"""Sets the number of subblocks that are configured in intra-band non-contiguous carrier aggregation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1. Set this attribute to 1 for single carrier and intra-band contiguous carrier
        aggregation.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of subblocks that are configured in intra-band non-contiguous carrier aggregation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_SUBBLOCKS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subblock_frequency(self, selector_string):
        r"""Gets the offset of the subblock from the center frequency. This value is expressed in Hz.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset of the subblock from the center frequency. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.SUBBLOCK_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_subblock_frequency(self, selector_string, value):
        r"""Sets the offset of the subblock from the center frequency. This value is expressed in Hz.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset of the subblock from the center frequency. This value is expressed in Hz.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.SUBBLOCK_FREQUENCY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_band(self, selector_string):
        r"""Gets the evolved universal terrestrial radio access (E-UTRA) operating frequency band of a subblock, as defined in
        section 5.2 of the *3GPP TS 36.521* specification.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1. Valid values are from 1 to 256, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the evolved universal terrestrial radio access (E-UTRA) operating frequency band of a subblock, as defined in
                section 5.2 of the *3GPP TS 36.521* specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.BAND.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_band(self, selector_string, value):
        r"""Sets the evolved universal terrestrial radio access (E-UTRA) operating frequency band of a subblock, as defined in
        section 5.2 of the *3GPP TS 36.521* specification.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1. Valid values are from 1 to 256, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the evolved universal terrestrial radio access (E-UTRA) operating frequency band of a subblock, as defined in
                section 5.2 of the *3GPP TS 36.521* specification.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.BAND.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_mi_configuration(self, selector_string):
        r"""Gets whether the Mi parameter is specified by section 6.1.2.6 of *3GPP TS 36.141* specification for testing E-TMs
        or in the Table 6.9-1 of *3GPP TS 36.211* specification.
        The Mi parameter determines the number of PHICH groups in each downlink subframe, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute to **TDD**.

        This attribute is not valid, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
        measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Standard**.

        +----------------+-------------------------------------------------------------------------------------------+
        | Name (Value)   | Description                                                                               |
        +================+===========================================================================================+
        | Test Model (0) | Mi parameter is set to 1 as specified in section 6.1.2.6 of 3GPP TS 36.141 specification. |
        +----------------+-------------------------------------------------------------------------------------------+
        | Standard (1)   | Mi parameter is specified by the Table 6.9-1 of 3GPP TS 36.211 specification.             |
        +----------------+-------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.MiConfiguration):
                Specifies whether the Mi parameter is specified by section 6.1.2.6 of *3GPP TS 36.141* specification for testing E-TMs
                or in the Table 6.9-1 of *3GPP TS 36.211* specification.
                The Mi parameter determines the number of PHICH groups in each downlink subframe, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute to **TDD**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.MI_CONFIGURATION.value
            )
            attr_val = enums.MiConfiguration(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_mi_configuration(self, selector_string, value):
        r"""Sets whether the Mi parameter is specified by section 6.1.2.6 of *3GPP TS 36.141* specification for testing E-TMs
        or in the Table 6.9-1 of *3GPP TS 36.211* specification.
        The Mi parameter determines the number of PHICH groups in each downlink subframe, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute to **TDD**.

        This attribute is not valid, when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
        measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
        attribute to **Uplink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Standard**.

        +----------------+-------------------------------------------------------------------------------------------+
        | Name (Value)   | Description                                                                               |
        +================+===========================================================================================+
        | Test Model (0) | Mi parameter is set to 1 as specified in section 6.1.2.6 of 3GPP TS 36.141 specification. |
        +----------------+-------------------------------------------------------------------------------------------+
        | Standard (1)   | Mi parameter is specified by the Table 6.9-1 of 3GPP TS 36.211 specification.             |
        +----------------+-------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.MiConfiguration, int):
                Specifies whether the Mi parameter is specified by section 6.1.2.6 of *3GPP TS 36.141* specification for testing E-TMs
                or in the Table 6.9-1 of *3GPP TS 36.211* specification.
                The Mi parameter determines the number of PHICH groups in each downlink subframe, when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute to **TDD**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.MiConfiguration else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.MI_CONFIGURATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_dmrs_detection_enabled(self, selector_string):
        r"""Gets whether you configure the values of the demodulation reference signal (DMRS) parameters, such as
        :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_GROUP_HOPPING_ENABLED`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_SEQUENCE_HOPPING_ENABLED`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.CELL_ID`, :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_1`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_2`, and
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_DELTA_SEQUENCE_SHIFT` properties, or if the values of these
        attributes are auto-detected by the measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The user-specified DMRS parameters are used.                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The values of the DMRS parameters are automatically detected. Measurement returns an error if you set the ModAcc Sync    |
        |              | Mode attribute to Frame, since it is not possible to get the frame boundary when RFmx detects DMRS parameters            |
        |              | automatically.                                                                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoDmrsDetectionEnabled):
                Specifies whether you configure the values of the demodulation reference signal (DMRS) parameters, such as
                :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_GROUP_HOPPING_ENABLED`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_SEQUENCE_HOPPING_ENABLED`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.CELL_ID`, :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_1`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_2`, and
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_DELTA_SEQUENCE_SHIFT` properties, or if the values of these
                attributes are auto-detected by the measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.AUTO_DMRS_DETECTION_ENABLED.value
            )
            attr_val = enums.AutoDmrsDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_dmrs_detection_enabled(self, selector_string, value):
        r"""Sets whether you configure the values of the demodulation reference signal (DMRS) parameters, such as
        :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_GROUP_HOPPING_ENABLED`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_SEQUENCE_HOPPING_ENABLED`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.CELL_ID`, :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_1`,
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_2`, and
        :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_DELTA_SEQUENCE_SHIFT` properties, or if the values of these
        attributes are auto-detected by the measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The user-specified DMRS parameters are used.                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The values of the DMRS parameters are automatically detected. Measurement returns an error if you set the ModAcc Sync    |
        |              | Mode attribute to Frame, since it is not possible to get the frame boundary when RFmx detects DMRS parameters            |
        |              | automatically.                                                                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoDmrsDetectionEnabled, int):
                Specifies whether you configure the values of the demodulation reference signal (DMRS) parameters, such as
                :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_GROUP_HOPPING_ENABLED`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_SEQUENCE_HOPPING_ENABLED`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.CELL_ID`, :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_1`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_2`, and
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_DELTA_SEQUENCE_SHIFT` properties, or if the values of these
                attributes are auto-detected by the measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.AutoDmrsDetectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_DMRS_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_level_initial_reference_level(self, selector_string):
        r"""Gets the initial reference level that the :py:meth:`auto_level` method uses to estimate the peak power of the
        input signal. This value is expressed in dBm.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the initial reference level that the :py:meth:`auto_level` method uses to estimate the peak power of the
                input signal. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_level_initial_reference_level(self, selector_string, value):
        r"""Sets the initial reference level that the :py:meth:`auto_level` method uses to estimate the peak power of the
        input signal. This value is expressed in dBm.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the initial reference level that the :py:meth:`auto_level` method uses to estimate the peak power of the
                input signal. This value is expressed in dBm.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_acquisition_bandwidth_optimization_enabled(self, selector_string):
        r"""Gets whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
        oscillator (LO) to be placed at different position than you configured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Refer to the `Acquisition Bandwidth Optimization Enabled
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/acquisition-bandwidth-optimization.html>`_ topic for more
        information.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | RFmx does not optimize acquisition bandwidth and will be based on the Nyquist criterion. The value of the acquisition    |
        |              | center frequency is the same as the value of the Center Frequency that you configure.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | RFmx positions the acquisition center frequency to acquire the least bandwidth based on the configuration and span       |
        |              | needed for the measurement. This helps in reducing the amount of data to process for the measurement, thus improving     |
        |              | the speed. However this might cause the LO to be positioned at a non-dc subcarrier position, hence the measurement       |
        |              | sensitive to it should have this attribute disabled.                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcquisitionBandwidthOptimizationEnabled):
                Specifies whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
                oscillator (LO) to be placed at different position than you configured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED.value,
            )
            attr_val = enums.AcquisitionBandwidthOptimizationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_acquisition_bandwidth_optimization_enabled(self, selector_string, value):
        r"""Sets whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
        oscillator (LO) to be placed at different position than you configured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Refer to the `Acquisition Bandwidth Optimization Enabled
        <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/acquisition-bandwidth-optimization.html>`_ topic for more
        information.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | RFmx does not optimize acquisition bandwidth and will be based on the Nyquist criterion. The value of the acquisition    |
        |              | center frequency is the same as the value of the Center Frequency that you configure.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | RFmx positions the acquisition center frequency to acquire the least bandwidth based on the configuration and span       |
        |              | needed for the measurement. This helps in reducing the amount of data to process for the measurement, thus improving     |
        |              | the speed. However this might cause the LO to be positioned at a non-dc subcarrier position, hence the measurement       |
        |              | sensitive to it should have this attribute disabled.                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcquisitionBandwidthOptimizationEnabled, int):
                Specifies whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
                oscillator (LO) to be placed at different position than you configured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = (
                value.value
                if type(value) is enums.AcquisitionBandwidthOptimizationEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_transmitter_architecture(self, selector_string):
        r"""Gets the RF architecture at the transmitter in case of a multicarrier. 3GPP defines different options, each
        component carriers within a subblock can have separate LO or one common LO for an entire subblock. Based upon the
        selected option, the additional results are calculated.

        The measurement ignores this attribute when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **LO per Component Carrier**.

        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                                              |
        +==============================+==========================================================================================================================+
        | LO per Component Carrier (0) | IQ impairments and In-band emission are calculated per component carrier.                                                |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | LO per Subblock (1)          | Additional subblock based results such as Subblock IQ Offset and Subblock In band emission are calculated apart from     |
        |                              | per carrier results.                                                                                                     |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TransmitterArchitecture):
                Specifies the RF architecture at the transmitter in case of a multicarrier. 3GPP defines different options, each
                component carriers within a subblock can have separate LO or one common LO for an entire subblock. Based upon the
                selected option, the additional results are calculated.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRANSMITTER_ARCHITECTURE.value
            )
            attr_val = enums.TransmitterArchitecture(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_transmitter_architecture(self, selector_string, value):
        r"""Sets the RF architecture at the transmitter in case of a multicarrier. 3GPP defines different options, each
        component carriers within a subblock can have separate LO or one common LO for an entire subblock. Based upon the
        selected option, the additional results are calculated.

        The measurement ignores this attribute when you set the
        :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **LO per Component Carrier**.

        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                                              |
        +==============================+==========================================================================================================================+
        | LO per Component Carrier (0) | IQ impairments and In-band emission are calculated per component carrier.                                                |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | LO per Subblock (1)          | Additional subblock based results such as Subblock IQ Offset and Subblock In band emission are calculated apart from     |
        |                              | per carrier results.                                                                                                     |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TransmitterArchitecture, int):
                Specifies the RF architecture at the transmitter in case of a multicarrier. 3GPP defines different options, each
                component carriers within a subblock can have separate LO or one common LO for an entire subblock. Based upon the
                selected option, the additional results are calculated.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TransmitterArchitecture else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRANSMITTER_ARCHITECTURE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_limited_configuration_change(self, selector_string):
        r"""Gets the set of attributes that are considered by RFmx in the locked signal configuration state.

        If your test system performs the same measurement at different selected ports, multiple frequencies and/or
        power levels repeatedly, enabling this attribute can help achieve faster measurements. When you set this attribute to a
        value other than **Disabled**, RFmx will use an optimized code path and skip some checks. Because RFmx skips some
        checks when you use this attribute, you need to be aware of the limitations of this feature, which are listed in the
        `Limitations of the Limited Configuration Change Property
        <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.

        You can also use this attribute to lock a specific instrument configuration for a signal so that every time
        that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.

        NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
        configurations for each measurement configuration in your test program and set this attribute to a value other than
        **Disabled** for one or more of the named signal configurations. This allows RFmx to pre-compute the acquisition
        settings for your measurement configurations and re-use the precomputed settings each time you initiate the
        measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
        in your test program during test sequence initialization and do not change any RFmxInstr or personality attributes
        while testing each device under test. RFmx automatically optimizes that use case.

        Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
        need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
        Selector String topic for information about the string syntax for named signals.

        The default value is **Disabled**.

        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                           | Description                                                                                                              |
        +========================================+==========================================================================================================================+
        | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
        |                                        | attributes will be applied during RFmx Commit.                                                                           |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | No Change (1)                          | Signal configuration is locked after the first Commit of the named signal configuration. Any configuration change        |
        |                                        | thereafter either in RFmxInstr attributes or personality attributes will not be considered by subsequent RFmx Commits    |
        |                                        | or Initiates of this signal.                                                                                             |
        |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
        |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
        |                                        | about the limitations of using this mode.                                                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frequency (2)                          | Signal configuration, other than center frequency and external attenuation, is locked after first Commit of the named    |
        |                                        | signal configuration. Thereafter, only the Center Frequency and External Attenuation attribute value changes will be     |
        |                                        | considered by subsequent driver Commits or Initiates of this signal.                                                     |
        |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
        |                                        | using this mode.                                                                                                         |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference Level (3)                    | Signal configuration, other than the reference level, is locked after first Commit of the named signal configuration.    |
        |                                        | Thereafter only the Reference Level attribute value change will be considered by subsequent driver Commits or Initiates  |
        |                                        | of this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends that you set the IQ    |
        |                                        | Power Edge Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference        |
        |                                        | level. Refer to the Limitations of the Limited Configuration Change Property topic for more details about the            |
        |                                        | limitations of using this mode.                                                                                          |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, and external attenuation, is locked after first      |
        |                                        | Commit of the named signal configuration. Thereafter only Center Frequency, Reference Level, and External Attenuation    |
        |                                        | attribute value changes will be considered by subsequent driver Commits or Initiates of this signal. If you have         |
        |                                        | configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power Edge Level Type attribute to  |
        |                                        | Relative so that the trigger level is automatically adjusted as you adjust the reference level. Refer to the             |
        |                                        | Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this      |
        |                                        | mode.                                                                                                                    |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than Selected Ports, Center frequency, Reference level, External attenuation, and RFmxInstr  |
        |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
        |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
        |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
        |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type attribute to Relative so that the trigger level is           |
        |                                        | automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change   |
        |                                        | Property topic for more details about the limitations of using this mode.                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LimitedConfigurationChange):
                Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.LIMITED_CONFIGURATION_CHANGE.value
            )
            attr_val = enums.LimitedConfigurationChange(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_limited_configuration_change(self, selector_string, value):
        r"""Sets the set of attributes that are considered by RFmx in the locked signal configuration state.

        If your test system performs the same measurement at different selected ports, multiple frequencies and/or
        power levels repeatedly, enabling this attribute can help achieve faster measurements. When you set this attribute to a
        value other than **Disabled**, RFmx will use an optimized code path and skip some checks. Because RFmx skips some
        checks when you use this attribute, you need to be aware of the limitations of this feature, which are listed in the
        `Limitations of the Limited Configuration Change Property
        <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.

        You can also use this attribute to lock a specific instrument configuration for a signal so that every time
        that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.

        NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
        configurations for each measurement configuration in your test program and set this attribute to a value other than
        **Disabled** for one or more of the named signal configurations. This allows RFmx to pre-compute the acquisition
        settings for your measurement configurations and re-use the precomputed settings each time you initiate the
        measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
        in your test program during test sequence initialization and do not change any RFmxInstr or personality attributes
        while testing each device under test. RFmx automatically optimizes that use case.

        Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
        need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
        Selector String topic for information about the string syntax for named signals.

        The default value is **Disabled**.

        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                           | Description                                                                                                              |
        +========================================+==========================================================================================================================+
        | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
        |                                        | attributes will be applied during RFmx Commit.                                                                           |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | No Change (1)                          | Signal configuration is locked after the first Commit of the named signal configuration. Any configuration change        |
        |                                        | thereafter either in RFmxInstr attributes or personality attributes will not be considered by subsequent RFmx Commits    |
        |                                        | or Initiates of this signal.                                                                                             |
        |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
        |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
        |                                        | about the limitations of using this mode.                                                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frequency (2)                          | Signal configuration, other than center frequency and external attenuation, is locked after first Commit of the named    |
        |                                        | signal configuration. Thereafter, only the Center Frequency and External Attenuation attribute value changes will be     |
        |                                        | considered by subsequent driver Commits or Initiates of this signal.                                                     |
        |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
        |                                        | using this mode.                                                                                                         |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference Level (3)                    | Signal configuration, other than the reference level, is locked after first Commit of the named signal configuration.    |
        |                                        | Thereafter only the Reference Level attribute value change will be considered by subsequent driver Commits or Initiates  |
        |                                        | of this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends that you set the IQ    |
        |                                        | Power Edge Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference        |
        |                                        | level. Refer to the Limitations of the Limited Configuration Change Property topic for more details about the            |
        |                                        | limitations of using this mode.                                                                                          |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, and external attenuation, is locked after first      |
        |                                        | Commit of the named signal configuration. Thereafter only Center Frequency, Reference Level, and External Attenuation    |
        |                                        | attribute value changes will be considered by subsequent driver Commits or Initiates of this signal. If you have         |
        |                                        | configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power Edge Level Type attribute to  |
        |                                        | Relative so that the trigger level is automatically adjusted as you adjust the reference level. Refer to the             |
        |                                        | Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this      |
        |                                        | mode.                                                                                                                    |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than Selected Ports, Center frequency, Reference level, External attenuation, and RFmxInstr  |
        |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
        |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
        |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
        |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type attribute to Relative so that the trigger level is           |
        |                                        | automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change   |
        |                                        | Property topic for more details about the limitations of using this mode.                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LimitedConfigurationChange, int):
                Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.LimitedConfigurationChange else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.LIMITED_CONFIGURATION_CHANGE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_center_frequency_for_limits(self, selector_string):
        r"""Gets the frequency that determines the SEM mask, IBE limits, and spectral flatness ranges. If you do not set a
        value for this attribute, the measurement internally uses the
        :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` for determining SEM mask, IBE limits, and spectral
        flatness ranges. This value is expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the frequency that determines the SEM mask, IBE limits, and spectral flatness ranges. If you do not set a
                value for this attribute, the measurement internally uses the
                :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` for determining SEM mask, IBE limits, and spectral
                flatness ranges. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY_FOR_LIMITS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_center_frequency_for_limits(self, selector_string, value):
        r"""Sets the frequency that determines the SEM mask, IBE limits, and spectral flatness ranges. If you do not set a
        value for this attribute, the measurement internally uses the
        :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` for determining SEM mask, IBE limits, and spectral
        flatness ranges. This value is expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the frequency that determines the SEM mask, IBE limits, and spectral flatness ranges. If you do not set a
                value for this attribute, the measurement internally uses the
                :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` for determining SEM mask, IBE limits, and spectral
                flatness ranges. This value is expressed in Hz.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CENTER_FREQUENCY_FOR_LIMITS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_result_fetch_timeout(self, selector_string):
        r"""Gets the time to wait before results are available in the RFmxLTE Attribute. This value is expressed in seconds.
        Set this value to a time longer than expected for fetching the measurement. A value of -1 specifies that the  RFmx
        Attribute waits until the measurement is complete.

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
                Specifies the time to wait before results are available in the RFmxLTE Attribute. This value is expressed in seconds.
                Set this value to a time longer than expected for fetching the measurement. A value of -1 specifies that the  RFmx
                Attribute waits until the measurement is complete.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.RESULT_FETCH_TIMEOUT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_result_fetch_timeout(self, selector_string, value):
        r"""Sets the time to wait before results are available in the RFmxLTE Attribute. This value is expressed in seconds.
        Set this value to a time longer than expected for fetching the measurement. A value of -1 specifies that the  RFmx
        Attribute waits until the measurement is complete.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time to wait before results are available in the RFmxLTE Attribute. This value is expressed in seconds.
                Set this value to a time longer than expected for fetching the measurement. A value of -1 specifies that the  RFmx
                Attribute waits until the measurement is complete.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.RESULT_FETCH_TIMEOUT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def abort_measurements(self, selector_string):
        r"""Stops acquisition and measurements  associated with signal instance that you specify in the  **Selector String**
        parameter, which were previously initiated by the :py:meth:`initiate` method or measurement read methods. Calling this
        method is optional, unless you want to stop a measurement before it is complete. This method executes even if there is
        an incoming error.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.abort_measurements(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_level(self, selector_string, measurement_interval):
        r"""Examines the input signal to calculate the peak power level and sets it as the value of the
        :py:attr:`~nirfmxlte.attributes.AttributeID.REFERENCE_LEVEL` attribute. Use this method to calculate an approximate
        setting for the reference level.

        RFmxLTE Auto Level method completes the following tasks:
        #. Resets the mixer level, mixer level offset, and IF output power offset.

        #. Sets the starting reference level to the maximum reference level supported by the device based on the current RF attenuation, mechanical attenuation, and preamplifier enabled settings.

        #. Iterates to adjust the reference level based on the input signal peak power.

        #. Uses immediate triggering and restores the trigger settings back to user setting after the execution.

        You can also specify the starting reference level using
        :py:attr:`~nirfmxlte.attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL` attribute.

        When using PXIe-5663, PXIe-5665, or PXIe-5668 devices, NI recommends that you set an appropriate value for
        mechanical attenuation before calling RFmxLTE Auto Level method. Setting an appropriate value for mechanical
        attenuation reduces the number of times the attenuator settings are changed by this function; thus reducing wear and
        tear, and maximizing the life time of the attenuator.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_interval (float):
                This parameter specifies the acquisition length. This value is expressed in seconds. Use this value to compute the
                number of samples to acquire from the signal analyzer. The default value is 10 ms.

                Auto Level method does not use any trigger for acquisition. It ignores the user-configured trigger attributes.
                NI recommends that you set a sufficiently high measurement interval to ensure that the acquired waveform is at least as
                long as one period of the signal.

        Returns:
            Tuple (reference_level, error_code):

            reference_level (float):
                This parameter returns the estimated peak power level of the input signal. This value is configured in dBm for RF
                devices and as Vpk-pk for baseband devices. The default value of this parameter is hardware dependent.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            reference_level, error_code = self._interpreter.auto_level(  # type: ignore
                updated_selector_string, measurement_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return reference_level, error_code

    @_raise_if_disposed
    def check_measurement_status(self, selector_string):
        r"""Checks the status of the measurement. Use this method to check for any errors that may occur during measurement or to
        check whether the measurement is complete and results are available.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

        Returns:
            Tuple (is_done, error_code):

            is_done (bool):
                This parameter indicates whether the measurement is complete.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            is_done, error_code = self._interpreter.check_measurement_status(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return is_done, error_code

    @_raise_if_disposed
    def clear_all_named_results(self, selector_string):
        r"""Clears all results for the signal that you specify in the **Selector String** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_all_named_results(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def clear_named_result(self, selector_string):
        r"""Clears a result instance specified by the result name in the **Selector String** parameter.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_named_result(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def commit(self, selector_string):
        r"""Commits settings to the hardware. Calling this method is optional. RFmxLTE commits settings to the hardware when you
        call the :py:meth:`initiate` method.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.commit(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_auto_dmrs_detection_enabled(self, selector_string, auto_dmrs_detection_enabled):
        r"""Configures whether the demodulation reference signal (DMRS) parameters are configured by a user or automatically
        detected by a measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            auto_dmrs_detection_enabled (enums.AutoDmrsDetectionEnabled, int):
                This parameter specifies whether you need to configure the DMRS parameters, such as the values of the
                :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_GROUP_HOPPING_ENABLED`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_SEQUENCE_HOPPING_ENABLED`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.CELL_ID`, :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_1`,
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_2`, and
                :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_2` properties, or if the measurement should automatically
                detect the values of these attributes. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The user-defined DMRS parameters are used.                                                                               |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The DMRS parameters are automatically detected. Measurements returns an error if you set the ModAcc Sync Mode attribute  |
                |              | to Frame because it is not possible to get the frame boundary when RFmx automatically detects the DMRS parameters.       |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            auto_dmrs_detection_enabled = (
                auto_dmrs_detection_enabled.value
                if type(auto_dmrs_detection_enabled) is enums.AutoDmrsDetectionEnabled
                else auto_dmrs_detection_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_auto_dmrs_detection_enabled(  # type: ignore
                updated_selector_string, auto_dmrs_detection_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_band(self, selector_string, band):
        r"""Configures the evolved universal terrestrial radio access (E-UTRA) operating frequency band of a subblock.

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

            band (int):
                This parameter specifies the E-UTRA operating frequency band of a subblock as defined in section 5.2 of the *3GPP TS
                36.521* specification. Valid values are from 1 to 256, inclusive. The default value is 1.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_band(  # type: ignore
                updated_selector_string, band
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_digital_edge_trigger(
        self, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        r"""Configures the device to wait for a digital edge trigger and then marks a reference point within the record.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            digital_edge_source (string):
                This parameter specifies the source terminal for the digital edge trigger. This parameter is used when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**. The default value of this
                parameter is hardware dependent.

                +---------------------------+-----------------------------------------------------------+
                | Name (Value)              | Description                                               |
                +===========================+===========================================================+
                | PFI0 (PFI0)               | The trigger is received on PFI 0.                         |
                +---------------------------+-----------------------------------------------------------+
                | PFI1 (PFI1)               | The trigger is received on PFI 1.                         |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig0 (PXI_Trig0)     | The trigger is received on PXI trigger line 0.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig1 (PXI_Trig1)     | The trigger is received on PXI trigger line 1.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig2 (PXI_Trig2)     | The trigger is received on PXI trigger line 2.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig3 (PXI_Trig3)     | The trigger is received on PXI trigger line 3.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig4 (PXI_Trig4)     | The trigger is received on PXI trigger line 4.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig5 (PXI_Trig5)     | The trigger is received on PXI trigger line 5.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig6 (PXI_Trig6)     | The trigger is received on PXI trigger line 6.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig7 (PXI_Trig7)     | The trigger is received on PXI trigger line 7.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_STAR (PXI_STAR)       | The trigger is received on the PXI star trigger line.     |
                +---------------------------+-----------------------------------------------------------+
                | PXIe_DStarB (PXIe_DStarB) | The trigger is received on the PXIe DStar B trigger line. |
                +---------------------------+-----------------------------------------------------------+
                | TimerEvent (TimerEvent)   | The trigger is received from the Timer Event.             |
                +---------------------------+-----------------------------------------------------------+

            digital_edge (enums.DigitalEdgeTriggerEdge, int):
                This parameter specifies the source terminal for the digital edge trigger. This parameter is used when you set the
                :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**. The default value is **Rising
                Edge**.

                +------------------+--------------------------------------------------------+
                | Name (Value)     | Description                                            |
                +==================+========================================================+
                | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
                +------------------+--------------------------------------------------------+
                | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
                +------------------+--------------------------------------------------------+

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the
                measurement acquires pretrigger samples. If the delay is positive, the measurement acquires post-trigger samples. The
                default value is 0.

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(digital_edge_source, "digital_edge_source")
            digital_edge = (
                digital_edge.value
                if type(digital_edge) is enums.DigitalEdgeTriggerEdge
                else digital_edge
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_digital_edge_trigger(  # type: ignore
                updated_selector_string,
                digital_edge_source,
                digital_edge,
                trigger_delay,
                int(enable_trigger),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_duplex_scheme(
        self, selector_string, duplex_scheme, uplink_downlink_configuration
    ):
        r"""Configures the duplexing technique of the signal being measured.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            duplex_scheme (enums.DuplexScheme, int):
                This parameter specifies the duplexing technique of the signal being measured. The default value is **FDD**.

                +--------------+-------------------------------------------------------------------------+
                | Name (Value) | Description                                                             |
                +==============+=========================================================================+
                | FDD (0)      | Specifies that the duplexing technique is frequency-division duplexing. |
                +--------------+-------------------------------------------------------------------------+
                | TDD (1)      | Specifies that the duplexing technique is time-division duplexing.      |
                +--------------+-------------------------------------------------------------------------+
                | LAA (2)      | Specifies that the duplexing technique is license assisted access.      |
                +--------------+-------------------------------------------------------------------------+

            uplink_downlink_configuration (enums.UplinkDownlinkConfiguration, int):
                This parameter specifies the configuration of the LTE frame structure in the time division duplex (TDD) mode. To
                configure the LTE frame, refer to table 4.2-2 of the *3GPP TS 36.211* specification.

                The default value is **0**.

                +--------------+---------------------------------------------------------------------------+
                | Name (Value) | Description                                                               |
                +==============+===========================================================================+
                | 0 (0)        | The configuration of the LTE frame structure in the TDD duplex mode is 0. |
                +--------------+---------------------------------------------------------------------------+
                | 1 (1)        | The configuration of the LTE frame structure in the TDD duplex mode is 1. |
                +--------------+---------------------------------------------------------------------------+
                | 2 (2)        | The configuration of the LTE frame structure in the TDD duplex mode is 2. |
                +--------------+---------------------------------------------------------------------------+
                | 3 (3)        | The configuration of the LTE frame structure in the TDD duplex mode is 3. |
                +--------------+---------------------------------------------------------------------------+
                | 4 (4)        | The configuration of the LTE frame structure in the TDD duplex mode is 4. |
                +--------------+---------------------------------------------------------------------------+
                | 5 (5)        | The configuration of the LTE frame structure in the TDD duplex mode is 5. |
                +--------------+---------------------------------------------------------------------------+
                | 6 (6)        | The configuration of the LTE frame structure in the TDD duplex mode is 6. |
                +--------------+---------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            duplex_scheme = (
                duplex_scheme.value if type(duplex_scheme) is enums.DuplexScheme else duplex_scheme
            )
            uplink_downlink_configuration = (
                uplink_downlink_configuration.value
                if type(uplink_downlink_configuration) is enums.UplinkDownlinkConfiguration
                else uplink_downlink_configuration
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_duplex_scheme(  # type: ignore
                updated_selector_string, duplex_scheme, uplink_downlink_configuration
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_enodeb_category(self, selector_string, enodeb_category):
        r"""Configures the eNodeB category of the signal being measured.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            enodeb_category (enums.eNodeBCategory, int):
                This parameter specifies the downlink eNodeB (Base Station) category. The default value is **Wide Area Base Station -
                Category A (0)**.

                +-------------------------------------------------+----------------------------------------------------------------------+
                | Name (Value)                                    | Description                                                          |
                +=================================================+======================================================================+
                | Wide Area Base Station - Category A (0)         | Specifies the eNodeB is Wide Area Base Station - Category A.         |
                +-------------------------------------------------+----------------------------------------------------------------------+
                | Wide Area Base Station - Category B Option1 (1) | Specifies the eNodeB is Wide Area Base Station - Category B Option1. |
                +-------------------------------------------------+----------------------------------------------------------------------+
                | Wide Area Base Station - Category B Option2 (2) | Specifies the eNodeB is Wide Area Base Station - Category B Option2. |
                +-------------------------------------------------+----------------------------------------------------------------------+
                | Local Area Base Station (3)                     | Specifies the eNodeB is Local Area Base Station.                     |
                +-------------------------------------------------+----------------------------------------------------------------------+
                | Home Base Station (4)                           | Specifies the eNodeB is Home Base Station.                           |
                +-------------------------------------------------+----------------------------------------------------------------------+
                | Medium Range Base Station (5)                   | Specifies the eNodeB is Medium Range Base Station.                   |
                +-------------------------------------------------+----------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            enodeb_category = (
                enodeb_category.value
                if type(enodeb_category) is enums.eNodeBCategory
                else enodeb_category
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_enodeb_category(  # type: ignore
                updated_selector_string, enodeb_category
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_external_attenuation(self, selector_string, external_attenuation):
        r"""Specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            external_attenuation (float):
                This parameter specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer.
                This value is expressed in dB. For more information about attenuation, refer to the RF Attenuation and Signal Levels
                topic for your device in the* NI RF Vector Signal Analyzers Help*. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_external_attenuation(  # type: ignore
                updated_selector_string, external_attenuation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_frequency_earfcn(self, selector_string, link_direction, band, earfcn):
        r"""Configures the expected carrier frequency of the RF signal to acquire. The signal analyzer tunes to the E-UTRA absolute
        radio frequency channel number (EARFCN) frequency.

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

            link_direction (enums.LinkDirection, int):
                This parameter specifies the link direction of the received signal. The default value is **Uplink**.

                +--------------+--------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                          |
                +==============+======================================================================================+
                | Downlink (0) | The measurement uses 3GPP LTE downlink specification to measure the received signal. |
                +--------------+--------------------------------------------------------------------------------------+
                | Uplink (1)   | The measurement uses 3GPP LTE uplink specification to measure the received signal.   |
                +--------------+--------------------------------------------------------------------------------------+

            band (int):
                This parameter specifies the E-UTRA operating frequency band of a subblock as defined in section 5.2 of the *3GPP TS
                36.521* specification. Valid values are from 1 to 256, inclusive. The default value is 1.

            earfcn (int):
                This parameter specifies the  evolved universal terrestrial radio access (E-UTRA) absolute radio frequency channel
                number. The default value is 18100.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            link_direction = (
                link_direction.value
                if type(link_direction) is enums.LinkDirection
                else link_direction
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_frequency_earfcn(  # type: ignore
                updated_selector_string, link_direction, band, earfcn
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_frequency(self, selector_string, center_frequency):
        r"""Configures the expected carrier frequency of the RF signal to acquire. The signal analyzer tunes to this frequency.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            center_frequency (float):
                This parameter specifies the center frequency of the acquired RF signal for a single carrier. The parameter specifies
                the reference frequency of the subblock for intra-band carrier aggregation. The default value of this parameter is
                hardware dependent.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_frequency(  # type: ignore
                updated_selector_string, center_frequency
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_iq_power_edge_trigger(
        self,
        selector_string,
        iq_power_edge_source,
        iq_power_edge_slope,
        iq_power_edge_level,
        trigger_delay,
        trigger_min_quiet_time_mode,
        trigger_min_quiet_time_duration,
        iq_power_edge_level_type,
        enable_trigger,
    ):
        r"""Configures the device to wait for the complex power of the I/Q data to cross the specified threshold and then marks a
        reference point within the record.

        To trigger on bursty signals, specify a minimum quiet time, which ensures that the trigger does not occur in
        the middle of the burst signal. The quiet time must be set to a value smaller than the time between bursts, but large
        enough to ignore power changes within a burst.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            iq_power_edge_source (string):
                This parameter specifies the channel from which the device monitors the trigger. This parameter is used only when you
                set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**. The default value of
                this parameter is hardware dependent.

            iq_power_edge_slope (enums.IQPowerEdgeTriggerSlope, int):
                This parameter specifies whether the device asserts the trigger when the signal power is rising or when it is falling.
                The device asserts the trigger when the signal power exceeds the specified level with the slope you specify. This
                parameter is used only when you set the Trigger Type attribute to **IQ Power Edge**. The default value is **Rising
                Slope**.

                +-------------------+-------------------------------------------------------+
                | Name (Value)      | Description                                           |
                +===================+=======================================================+
                | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
                +-------------------+-------------------------------------------------------+
                | Falling Slope (1) | The trigger asserts when the signal power is falling. |
                +-------------------+-------------------------------------------------------+

            iq_power_edge_level (float):
                This parameter specifies the power level at which the device triggers. This value is expressed in dB when you set the
                **IQ Power Edge Level Type** parameter to **Relative**, and this value is expressed in dBm when you set the **IQ Power
                Edge Level Type** parameter to **Absolute**. The device asserts the trigger when the signal exceeds the level specified
                by the value of this parameter, taking into consideration the specified slope.
                This parameter is used only when you set the Trigger Type attribute to **IQ Power Edge**. The default value of this
                parameter is hardware dependent.

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the
                measurement acquires pretrigger samples. If the delay is positive, the measurement acquires post-trigger samples. The
                default value is 0.

            trigger_min_quiet_time_mode (enums.TriggerMinimumQuietTimeMode, int):
                This parameter specifies whether the measurement computes the minimum quiet time used for triggering. The default value
                is **Auto**.

                +--------------+-------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                         |
                +==============+=====================================================================================+
                | Manual (0)   | The minimum quiet time for triggering is the value of the Min Quiet Time parameter. |
                +--------------+-------------------------------------------------------------------------------------+
                | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                |
                +--------------+-------------------------------------------------------------------------------------+

            trigger_min_quiet_time_duration (float):
                This parameter specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q
                power edge trigger. This value is expressed in seconds. If you set the **IQ Power Edge Slope** parameter to **Rising
                Slope**, the signal is quiet below the trigger level. If you set the **IQ Power Edge Slope** parameter to **Falling
                Slope**, the signal is quiet above the trigger level.

                The default value of this parameter is hardware dependent.

            iq_power_edge_level_type (enums.IQPowerEdgeTriggerLevelType, int):
                This parameter specifies the reference for the** IQ Power Edge Level** parameter. The **IQ Power Edge Level Type**
                parameter is used only when you set the Trigger Type attribute to **IQ Power Edge**.

                +--------------+----------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                  |
                +==============+==============================================================================================+
                | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
                +--------------+----------------------------------------------------------------------------------------------+
                | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
                +--------------+----------------------------------------------------------------------------------------------+

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(iq_power_edge_source, "iq_power_edge_source")
            iq_power_edge_slope = (
                iq_power_edge_slope.value
                if type(iq_power_edge_slope) is enums.IQPowerEdgeTriggerSlope
                else iq_power_edge_slope
            )
            trigger_min_quiet_time_mode = (
                trigger_min_quiet_time_mode.value
                if type(trigger_min_quiet_time_mode) is enums.TriggerMinimumQuietTimeMode
                else trigger_min_quiet_time_mode
            )
            iq_power_edge_level_type = (
                iq_power_edge_level_type.value
                if type(iq_power_edge_level_type) is enums.IQPowerEdgeTriggerLevelType
                else iq_power_edge_level_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_iq_power_edge_trigger(  # type: ignore
                updated_selector_string,
                iq_power_edge_source,
                iq_power_edge_slope,
                iq_power_edge_level,
                trigger_delay,
                trigger_min_quiet_time_mode,
                trigger_min_quiet_time_duration,
                iq_power_edge_level_type,
                int(enable_trigger),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_link_direction(self, selector_string, link_direction):
        r"""Configures the link direction of the signal being measured.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            link_direction (enums.LinkDirection, int):
                This parameter specifies the link direction of the received signal. The default value is **Uplink**.

                +--------------+---------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                           |
                +==============+=======================================================================================+
                | Downlink (0) | The measurement uses 3GPP LTE downlink specification to measure the received signal.  |
                +--------------+---------------------------------------------------------------------------------------+
                | Uplink (1)   | The measurement uses 3GPP LTE uplink specification to measure the received signal.    |
                +--------------+---------------------------------------------------------------------------------------+
                | Sidelink (2) | The measurement uses 3GPP LTE sidelink specifications to measure the received signal. |
                +--------------+---------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            link_direction = (
                link_direction.value
                if type(link_direction) is enums.LinkDirection
                else link_direction
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_link_direction(  # type: ignore
                updated_selector_string, link_direction
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_component_carriers(self, selector_string, number_of_component_carriers):
        r"""Configures the number of component carriers within a subblock.

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

            number_of_component_carriers (int):
                This parameter specifies the number of component carriers configured within a subblock. The default value is 1.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_number_of_component_carriers(  # type: ignore
                updated_selector_string, number_of_component_carriers
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_dut_antennas(self, selector_string, number_of_dut_antennas):
        r"""Configures the number of physical antennas used for transmission by the DUT in a MIMO setup.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            number_of_dut_antennas (int):
                This parameter specifies the number of physical antennas available at the DUT for transmission in a MIMO setup. The
                default value is 1. Valid values are 1, 2, and 4.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_number_of_dut_antennas(  # type: ignore
                updated_selector_string, number_of_dut_antennas
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_subblocks(self, selector_string, number_of_subblocks):
        r"""Configures the number of subblocks.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            number_of_subblocks (int):
                This parameter specifies the number of subblocks that are configured in the intra-band noncontiguous carrier
                aggregation. The default value is 1.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_number_of_subblocks(  # type: ignore
                updated_selector_string, number_of_subblocks
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_reference_level(self, selector_string, reference_level):
        r"""Configures the reference level, which represents the maximum expected power of an RF input signal.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            reference_level (float):
                This parameter specifies the reference level which represents the maximum expected power of the RF input signal. This
                value is configured in dBm for RF devices and as Vpk-pk for baseband devices. The default value of this parameter is
                hardware dependent.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_reference_level(  # type: ignore
                updated_selector_string, reference_level
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_rf(
        self, selector_string, center_frequency, reference_level, external_attenuation
    ):
        r"""Configures the RF attributes of the signal specified by the selector string.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            center_frequency (float):
                This parameter specifies the center frequency of the acquired RF signal for a single carrier. The parameter specifies
                the reference frequency of the subblock for intra-band carrier aggregation. The default value of this parameter is
                hardware dependent.

            reference_level (float):
                This parameter specifies the reference level which represents the maximum expected power of the RF input signal. This
                value is configured in dBm for RF devices and as Vpk-pk for baseband devices. The default value of this parameter is
                hardware dependent.

            external_attenuation (float):
                This parameter specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer.
                This value is expressed in dB. For more information about attenuation, refer to the RF Attenuation and Signal Levels
                topic for your device in the* NI RF Vector Signal Analyzers Help*. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_rf(  # type: ignore
                updated_selector_string, center_frequency, reference_level, external_attenuation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_software_edge_trigger(self, selector_string, trigger_delay, enable_trigger):
        r"""Configures the device to wait for a software trigger and then marks a reference point within the record.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the
                measurement acquires pretrigger samples. If the delay is positive, the measurement acquires post-trigger samples. The
                default value is 0.

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_software_edge_trigger(  # type: ignore
                updated_selector_string, trigger_delay, int(enable_trigger)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_transmit_antenna_to_analyze(self, selector_string, transmit_antenna_to_analyze):
        r"""Configures the current physical antenna of the DUT in the MIMO setup being tested.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            transmit_antenna_to_analyze (int):
                This parameter specifies the physical antenna connected to the analyzer. The default value is 0. Valid values are from
                0 to N-1, where N is the number of DUT antennas.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_transmit_antenna_to_analyze(  # type: ignore
                updated_selector_string, transmit_antenna_to_analyze
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def disable_trigger(self, selector_string):
        r"""Configures the device to not wait for a trigger to mark a reference point within a record. This method defines the
        signal triggering as immediate.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.disable_trigger(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def initiate(self, selector_string, result_name):
        r"""Initiates all enabled measurements. Call this method after configuring the signal and measurement. This method
        asynchronously launches measurements in the background and immediately returns to the caller program. You can fetch
        measurement results using the Fetch methods or result attributes in the attribute node. To get the status of
        measurements, use the :py:meth:`wait_for_measurement_complete` method or :py:meth:`check_measurement_status` method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.  The result name can either be specified through this input or the **Result Name** parameter. If you do not specify the result name in this input,
                either the result name specified by **Result Name** parameter or the default result instance is used.  The default is
                "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string) which refers to default result instance.

                Example:

                "result::r1"

                "r1"

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.initiate(  # type: ignore
                updated_selector_string, result_name
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def reset_to_default(self, selector_string):
        r"""Resets a signal to the default values.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.reset_to_default(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def select_measurements(self, selector_string, measurements, enable_all_traces):
        r"""Enables all the measurements that you specify in the **Measurements** parameter and disables all other measurements.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurements (enums.MeasurementTypes, int):
                This parameter specifies the measurements to perform. You can specify one or more of the following measurements. The
                default value is an empty array.

                +---------------+------------------------------------+
                | Name (Value)  | Description                        |
                +===============+====================================+
                | ACP (0)       | Enables the ACP measurement.       |
                +---------------+------------------------------------+
                | CHP (1)       | Enables the CHP measurement.       |
                +---------------+------------------------------------+
                | ModAcc (2)    | Enables the ModAcc measurement.    |
                +---------------+------------------------------------+
                | OBW (3)       | Enables the OBW measurement.       |
                +---------------+------------------------------------+
                | SEM (4)       | Enables the SEM measurement.       |
                +---------------+------------------------------------+
                | PVT (5)       | Enables the PVT measurement.       |
                +---------------+------------------------------------+
                | SlotPhase (6) | Enables the SlotPhase measurement. |
                +---------------+------------------------------------+
                | SlotPower (7) | Enables the SlotPower measurement. |
                +---------------+------------------------------------+

            enable_all_traces (bool):
                This parameter specifies whether to enable all traces for the selected measurement. The default value is FALSE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            measurements = (
                measurements.value if type(measurements) is enums.MeasurementTypes else measurements
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.select_measurements(  # type: ignore
                updated_selector_string, measurements, int(enable_all_traces)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def wait_for_measurement_complete(self, selector_string, timeout):
        r"""Waits for the specified number for seconds for all the measurements to complete.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for which the method waits for the measurement to complete. This value is
                expressed in seconds. A value of -1 specifies that the method waits until the measurement is complete.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.wait_for_measurement_complete(  # type: ignore
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @staticmethod
    def build_result_string(result_name):
        r"""Creates selector string for use with configuration or fetch.

        Args:
            result_name (string):
                Specifies the result name for building the selector string.
                This input accepts the result name with or without the "result::" prefix.
                Example: "", "result::r1", "r1".

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(result_name, "result_name")
        return _helper.build_result_string(result_name)

    @staticmethod
    def build_carrier_string(selector_string, carrier_number):
        r"""Creates a carrier string to use as a selector string with the SEM and ACP carrier configurations or fetch attributes
        and methods.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            carrier_number (int):
                This parameter specifies the carrier number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_carrier_string(selector_string, carrier_number)  # type: ignore

    @staticmethod
    def build_cluster_string(selector_string, cluster_number):
        r"""Creates a cluster string to use as a selector string with the ModAcc cluster configuration or fetch attributes and
        methods.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            cluster_number (int):
                This parameter specifies the cluster number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_cluster_string(selector_string, cluster_number)  # type: ignore

    @staticmethod
    def build_offset_string(selector_string, offset_number):
        r"""Creates an offset string to use as a selector string with SEM and ACP offset configuration or fetch attributes and
        methods.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            offset_number (int):
                This parameter specifies the offset number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_offset_string(selector_string, offset_number)  # type: ignore

    @staticmethod
    def build_pdsch_string(selector_string, pdsch_number):
        r"""Creates a PDSCH string to use as a selector string with the configuration or fetch attributes and methods.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            pdsch_number (int):
                This parameter specifies the PDSCH channel number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_pdsch_string(selector_string, pdsch_number)  # type: ignore

    @staticmethod
    def build_subblock_string(selector_string, subblock_number):
        r"""Creates a subblock string to use as a selector string with the subblock configuration or fetch attributes and methods.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            subblock_number (int):
                This parameter specifies the number of subblocks that are configured in the intra-band noncontiguous carrier
                aggregation. Set this parameter to 1, which is the default, for single carrier and intra-band contiguous carrier
                aggregation.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_subblock_string(selector_string, subblock_number)  # type: ignore

    @staticmethod
    def build_subframe_string(selector_string, subframe_number):
        r"""Creates a subframe string to use as a selector string with the configuration or fetch attributes and methods.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            subframe_number (int):
                This parameter specifies the subframe number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_subframe_string(selector_string, subframe_number)  # type: ignore

    @_raise_if_disposed
    def clone_signal_configuration(self, new_signal_name):
        r"""Creates a new instance of a signal by copying all the properties from an existing signal instance.

        Args:
            new_signal_name (string):
                This parameter specifies the name of the new signal. This parameter accepts the signal name with or without the \"signal::\" prefix.

                Example:

                \"signal::NewSigName\"

                \"NewSigName\"

        Returns:
            Tuple (cloned_signal, error_code):

            cloned_signal (lte):
                Contains a new Wlan signal instance.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(new_signal_name, "new_signal_name")
            updated_new_signal_name = _helper.validate_and_remove_signal_qualifier(
                new_signal_name, self
            )
            cloned_signal, error_code = self._interpreter.clone_signal_configuration(  # type: ignore
                self.signal_configuration_name, updated_new_signal_name
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return cloned_signal, error_code

    @_raise_if_disposed
    def send_software_edge_trigger(self):
        r"""Sends a trigger to the device when you use the [RFmxWLAN Configure Trigger](RFmxLTE_Configure_Trigger.html) function to choose a software version of a trigger and the device is waiting for the trigger to be sent. You can also use this function to override a hardware trigger.

        This function returns an error in the following situations:

        - You configure an invalid trigger.

        - You have not previously called the initiate function.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_code = self._interpreter.send_software_edge_trigger()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_named_result_names(self, selector_string):
        r"""Returns all the named result names of the signal that you specify in the Selector String parameter.

        Args:
            selector_string (string):
                Pass an empty string. The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (result_names, default_result_exists, error_code):

            result_names (string):
                Returns an array of result names.

            default_result_exists (bool):
                Indicates whether the default result exists.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            result_names, default_result_exists, error_code = (
                self._interpreter.get_all_named_result_names(updated_selector_string)  # type: ignore
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return result_names, default_result_exists, error_code

    @_raise_if_disposed
    def analyze_iq_1_waveform(self, selector_string, result_name, x0, dx, iq, reset):
        r"""Performs the enabled measurements on the  I/Q complex waveform  that you specify in the **IQ** parameter. Call this
        method after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch
        methods or result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **IQ** or **IQ or Spectral**.
        When using the Analysis-Only mode in RFmxWLAN, the RFmx driver ignores the RFmx hardware settings such as reference level
        and attenuation. The only RF hardware settings that are not ignored are the center frequency and trigger type, since it is
        needed for spectral measurement traces as well as some measurements such as ModAcc, ACP, and SEM.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the result name. The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start time of the input **y** array. This value is expressed in seconds.

            dx (float):
                This parameter specifies the time interval between the samples in the input **y** array. This value is expressed in
                seconds. The reciprocal of **dx** indicates the I/Q rate of the input signal.

            iq (numpy.complex64):
                This parameter specifies an array of complex-valued time domain data. The real and imaginary parts of this complex data
                array correspond to the in-phase (I) and quadrature-phase (Q) data, respectively.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_iq_1_waveform(  # type: ignore
                updated_selector_string, result_name, x0, dx, iq, reset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def analyze_spectrum_1_waveform(self, selector_string, result_name, x0, dx, spectrum, reset):
        r"""Performs the enabled measurements on the spectrum that you specify in the **Spectrum** parameter. Call this method
        after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch methods or
        result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **Spectral** or **IQ or Spectral**.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start frequency of the spectrum. This value is expressed in Hz.

            dx (float):
                This parameter specifies the frequency interval between data points in the spectrum.

            spectrum (numpy.float32):
                This parameter specifies the data for a spectrum waveform.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_spectrum_1_waveform(  # type: ignore
                updated_selector_string, result_name, x0, dx, spectrum, reset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code


class Lte(_LteBase):
    """Defines a root class which is used to identify and control Lte signal configuration."""

    def __init__(self, session, signal_name="", cloning=False):
        """Initializes a Lte signal configuration."""
        super(Lte, self).__init__(
            session=session,
            signal_name=signal_name,
            cloning=cloning,
        )  # type: ignore

    def __enter__(self):
        """Enters the context of the Lte signal configuration."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context of the Lte signal configuration."""
        self.dispose()  # type: ignore
        pass
