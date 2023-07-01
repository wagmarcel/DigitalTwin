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
import hash.sqlite_hash_v1 as sqlite_hash


def test_hash_init():
    hash = sqlite_hash.Hash()
    assert hash.flink_hash is not None


def test_hash_value():
    hashcode = sqlite_hash.Hash()
    result = hashcode.eval(10)
    assert result == 120
    result = hashcode.eval("hello world")
    assert result == hash("hello world") * 12
    result = hashcode.eval(12.34)
    assert result == hash(12.34) * 12
