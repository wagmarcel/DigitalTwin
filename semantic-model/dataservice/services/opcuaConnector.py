#
# Copyright (c) 2024 Intel Corporation
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

import os
import asyncio
from asyncua import Client

import random
from random import randint
from rdflib import Literal
from rdflib.namespace import XSD

#url = os.environ.get('OPCUA_TCP_CONNECT') or "opc.tcp://localhost:4840/"
url = "opc.tcp://localhost:4840/"

async def update_namespace_parameter(client, connector_attribute_dict):
    nodeid = connector_attribute_dict['connectorParameter']
    if not 'nsu=' in nodeid:
        return nodeid
    ns_index = 0
    try:
        ns_part, i_part = nodeid.split(';')
    except:
        ns_part = None
        i_part = nodeid
    if ns_part is not None:
        namespace = ns_part.split('=')[1]
    nsidx = await client.get_namespace_index(namespace)
    nodeid = f'ns={nsidx};{i_part}'
    return nodeid

##########################################################################################
# This function will receive an array of dictionaries containing the needed parameters
# to read out data from machines or databases.
# It will update the values in regular intervals
##########################################################################################
async def subscribe(connector_attribute_dict, firmware):
    async with Client(url=url) as client:
        # first resolve explicit namespace when given
        connector_attribute_dict['connectorParameter'] = await update_namespace_parameter(client, connector_attribute_dict)
        while True:
            logic_var_type = connector_attribute_dict['logicVarType']
            nodeset = connector_attribute_dict['connectorParameter']
            var = client.get_node(nodeset)
            value = await var.get_value()
            print(f'In OPCUA Connector with parameters {nodeset} and value {value}')
            #connector_attribute_dict['value'] = Literal(float(randint(0, 100000)) / 100.0)
            connector_attribute_dict['value'] = Literal(value)
            connector_attribute_dict['updated'] = True
            await asyncio.sleep(1)
