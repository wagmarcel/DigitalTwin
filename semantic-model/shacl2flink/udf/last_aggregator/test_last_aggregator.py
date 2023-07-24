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

import last_aggregator.sqlite_last_aggregator_v1 as sqlite_last_aggregator


def test_last_aggregator_init():
    la = sqlite_last_aggregator.Last_Aggregator()
    assert la.accum == [None, None]
    assert la.flink_last_aggregator is not None


def test_last_aggregator_init_step():
    la = sqlite_last_aggregator.Last_Aggregator()
    la.step("warning")
    assert la.accum == ['warning', 'warning']
    result = la.value()
    assert result == 'warning'

def test_last_aggregator_test_diff():
    la = sqlite_last_aggregator.Last_Aggregator()
    la.step("warning")
    result1 = la.value() 
    la.step("warning")
    result2 = la.value()
    assert result1 == 'warning'
    assert result2 == None

def test_last_aggregator_test_change():
    la = sqlite_last_aggregator.Last_Aggregator()
    la.step("warning test1")
    result1 = la.value() 
    la.step("warning test2")
    result2 = la.value()
    assert result1 == 'warning test1'
    assert result2 == 'warning test2'

def test_last_aggregator_more_changes():
    la = sqlite_last_aggregator.Last_Aggregator()
    la.step("warning test1!!")
    result1 = la.value() 
    la.step("warning test2&&")
    result2 = la.value()
    la.step("warning test2&&")
    result3 = la.value()
    la.step("warning test2&&")
    result4 = la.value()
    la.step("warning test1!!")
    result5 = la.value()
    la.step("warning test2&&")
    result6 = la.value()
    la.step("warning test1!!")
    result7 = la.value()
    la.step("warning test1!!")
    result8 = la.value()
    assert result1 == 'warning test1!!'
    assert result2 == 'warning test2&&'
    assert result3 == None
    assert result4 == None
    assert result5 == 'warning test1!!'
    assert result6 == 'warning test2&&'
    assert result7 == 'warning test1!!'
    assert result8 == None