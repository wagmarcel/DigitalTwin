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
    assert statetime.accum == [None, None, None]
    assert statetime.flink_statetime is not None


def test_statetime_init_step():
    statetime = sqlite_statetime.Statetime()
    statetime.step(1, 10)
    assert statetime.accum == [None, 1, 10]


def test_statetime_true_step():
    statetime = sqlite_statetime.Statetime()
    statetime.accum = [10, 1, 10]
    statetime.step(1, 17)
    assert statetime.accum == [17, 1, 17]
    statetime.accum = [None, 1, 10]
    statetime.step(1, 15)
    assert statetime.accum == [5, 1, 15]

def test_statetime_false_step():
    statetime = sqlite_statetime.Statetime()
    statetime.accum = [10, 1, 10]
    statetime.step(1, 17)
    assert statetime.accum == [17, 1, 17]
     