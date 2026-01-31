"""Requires `sys/tg_test/1` device running"""

import inspect
import os
from numbers import Number

import pytest
from sardana import State
from sardana.pool.test.util import ActionEvent

# Setting pool_path won't be necessary when SEP19 gets implemented
current_dir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe()))
)
parent_dir = os.path.dirname(current_dir)
pool_path = os.path.join(parent_dir, "sardana_tango/ctrl")

pool_mark = pytest.mark.attrs({"pool": {"pool_path": [pool_path]}})

ctrl_mark = pytest.mark.kwargs(
    {
        "motctrl01": {
            "klass": "TangoAttrMotorController",
            "library": "TangoAttrMotorCtrl.py",
        }
    }
)

mot_mark = pytest.mark.attribute_values(
    {
        "mot01": {
            "TangoAttribute": "sys/tg_test/1/ampli",
        }
    }
)

pytestmark = [pool_mark, ctrl_mark, mot_mark]

#############
# Alternatively you could create your own fixtures
# using the "Factory as fixture" e.g. `create_motor_ctrl`
# or `create_motor`.


# @pytest.fixture()
# def pool(create_pool):
#     pool = create_pool()
#     pool.pool_path = [pool_path]
#     return pool


# @pytest.fixture()
# def motctrl01(create_motor_ctrl):
#     kwargs = {
#         "klass": "TangoAttrMotorController",
#         "library": "TangoAttrMotorCtrl.py"
#     }
#     return create_motor_ctrl(kwargs)


# @pytest.fixture()
# def mot01(motctrl01, create_motor):
#     axis = 1
#     mot = create_motor(motctrl01, axis)
#     mot.init_attribute_values({
#         "TangoAttribute": "sys/tg_test/1/ampli"
#     })
#     return mot
##############


def test_init(motctrl01):
    assert motctrl01.is_online()


def test_get_state(mot01):
    assert mot01.state == State.On


def test_get_position(mot01):
    assert isinstance(mot01.position.value, Number)


def test_set_position(mot01):
    mot01.position = 10
    motion_event = ActionEvent(mot01)
    motion_event.started.wait(1)
    motion_event.done.wait(1)
    assert mot01.position.value == 10


def test_stop(mot01):
    mot01.position = 10
    motion_event = ActionEvent(mot01)
    motion_event.started.wait(1)
    mot01.stop()
    motion_event.done.wait(1)
    assert mot01.state == State.On
