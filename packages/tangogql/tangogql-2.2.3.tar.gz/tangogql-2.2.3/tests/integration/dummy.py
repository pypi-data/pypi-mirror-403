import time

import tango
from tango.server import Device, attribute, command, run


class Dummy(Device):
    def init_device(self):
        self._attr_int_writable = 0
        self.set_state(tango.DevState.RUNNING)

    @attribute(dtype=float, unit="mm")
    def attr_float(self):
        return 17.3

    @attribute(dtype=float, unit="count")
    def attr_int(self):
        return -24

    @attribute(dtype=[float], unit="cm", max_dim_x=3)
    def attr_float_array(self):
        return [1.2, 3.4, 5.6]

    @attribute(dtype=int, label="Hello!")
    def attr_int_writable(self):
        return self._attr_int_writable

    @attribute(dtype=int)
    def attr_raising(self):
        raise RuntimeError("oops!")

    @attribute(dtype=int)
    def attr_slow(self):
        time.sleep(3.5)

    @attr_int_writable.write
    def _write(self, value):
        self._attr_int_writable = value

    @attribute(dtype=float)
    def attr_broken(self):
        raise RuntimeError("Oops")

    @attribute(dtype=float)
    def attr_dIfFeReNtCaSe(self):
        return 123.456

    @command(dtype_in=int, doc_in="in", dtype_out=int, doc_out="out")
    def CommandInt(self, arg):
        return arg

    @command(dtype_out=tango.DevVarLongStringArray)
    def DevVarLongStringArray(self):
        return [[1, 2, 3], ["a", "b", "c"]]


if __name__ == "__main__":
    run((Dummy,))
