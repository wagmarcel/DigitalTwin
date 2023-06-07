#
# Copyright (c) 2022 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os.path
from unittest.mock import patch, MagicMock
import statetime.sqlite_statetime as sqlite_statetime


def test_statetime_init():
    statetime = sqlite_statetime.Statetime()
    assert statetime.accum == [None, None, None, None, None]
    assert statetime.flink_statetime is not None


def test_statetime_init_step():
    statetime = sqlite_statetime.Statetime()
    statetime.step(1, 10)
    assert statetime.accum == [None, 1, 10, None, None]


def test_statetime_true_step():
    statetime = sqlite_statetime.Statetime()
    statetime.accum = [10, 1, 10, None, None]
    statetime.step(1, 17)
    assert statetime.accum == [17, 1, 17, None, None]
    statetime.accum = [None, 1, 10, None, None]
    statetime.step(1, 15)
    assert statetime.accum == [5, 1, 15, None, None]
    statetime.accum = [None, 0, 10, None, None]
    statetime.step(1, 15)
    assert statetime.accum == [None, 1, 15, None, None]
    statetime.accum = [11, 0, 10, None, None]
    statetime.step(1, 13)
    assert statetime.accum == [11, 1, 13, None, None]


def test_statetime_false_step():
    statetime = sqlite_statetime.Statetime()
    statetime.accum = [10, 0, 10, None, None]
    statetime.step(0, 17)
    assert statetime.accum == [10, 0, 17, None, None]
    statetime.accum = [None, 1, 10, None, None]
    statetime.step(0, 15)
    assert statetime.accum == [5, 0, 15, None, None]
    statetime.accum = [None, 0, 3318, None, None]
    statetime.step(0, 3325)
    assert statetime.accum == [None, 0, 3325, None, None]


def test_inverse_all_true():
    statetime = sqlite_statetime.Statetime()
    statetime.step(1, 11)
    statetime.step(1, 13)
    statetime.step(1, 17)
    statetime.inverse(1,11)
    statetime.inverse(1,13)
    result = statetime.finalize()
    assert result == 4


def test_inverse_all_false():
    statetime = sqlite_statetime.Statetime()
    statetime.step(0, 11)
    statetime.step(0, 13)
    statetime.step(0, 17)
    statetime.inverse(0,11)
    statetime.inverse(0,13)
    result = statetime.finalize()
    assert result == None


def test_inverse_all_mixed():
    statetime = sqlite_statetime.Statetime()
    statetime.step(1, 1100)
    statetime.step(0, 1300)
    statetime.step(1, 1700)
    statetime.step(0, 1900)
    statetime.step(0, 2300)
    statetime.step(1, 2900)
    statetime.step(1, 3100)
    result = statetime.finalize()
    assert result == 600 
    statetime.inverse(1,1100)
    statetime.inverse(0,1300)
    result = statetime.finalize()
    assert result == 400
    statetime.inverse(1,1700)
    result = statetime.finalize()
    assert result == 400
    statetime.inverse(0,1900)
    result = statetime.finalize()
    assert result == 200
    statetime.inverse(0,2300)
    result = statetime.finalize()
    assert result == 200
    statetime.inverse(1,2900)
    result = statetime.finalize()
    assert result == 200
    statetime.inverse(1,3100)
    result = statetime.finalize()
    assert result == 0
def test_flow():
    statetime = sqlite_statetime.Statetime()
    statetime.step(1, 10000)
    statetime.step(1, 20000)
    statetime.step(1, 23000)
    statetime.step(0, 28000)
    statetime.step(1, 30000)
    statetime.step(0, 32000)
    result = statetime.finalize()
    assert result == 20000