from sensapex import UMP
from ctypes import (
    c_float,
    c_int,
)

UMP.set_library_path(".")
um = UMP.get_ump()
devices = um.list_devices()
dev_id = devices[0]

step_x = 100.0
step_y = 0
step_z = 0
step_w = 0
spd_x = 10
spd_y = 0
spd_z = 0
spd_w = 0
mode = 0
max_acc = 10000

um.call("um_take_step", c_int(dev_id), c_float(step_x), c_float(step_y), c_float(step_z), c_float(step_w), c_int(spd_x), c_int(spd_y), c_int(spd_z), c_int(spd_w), c_int(mode), c_int(max_acc))