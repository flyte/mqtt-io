from unittest.mock import Mock

from .. import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection, PinPUD

REQUIREMENTS = ()
CONFIG_SCHEMA = dict(test=dict(type="boolean", required=False, default=False))


class GPIO(GenericGPIO):
    INTERRUPT_SUPPORT = (
        InterruptSupport.SOFTWARE_CALLBACK,
        InterruptSupport.FLAG_REGISTER,
        InterruptSupport.CAPTURE_REGISTER,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interrupt_callbacks = {}

    setup_module = Mock()
    setup_pin = Mock()

    def setup_interrupt(self, pin, edge, callback, in_conf):
        self.interrupt_edges[pin] = edge
        self.interrupt_callbacks[pin] = callback

    setup_interrupt = Mock()
    set_pin = Mock()
    get_pin = Mock(return_value=1)
    get_int_pins = Mock(return_value=1)
    get_captured_int_pin_values = Mock(return_value={1: 1})
