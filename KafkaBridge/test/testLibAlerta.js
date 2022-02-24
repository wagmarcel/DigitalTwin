/**
* Copyright (c) 2022 Intel Corporation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/
'use strict';

const { assert } = require('chai');
const chai = require('chai');
global.should = chai.should();

const rewire = require('rewire');
const { rest } = require('underscore');
const toTest = rewire('../lib/alerta.js');

const logger = {
    debug: function () {},
    error: function () {}
  };
  

describe('Test sendAlerts', function () {
    it('Should post body with correct path and token', async function () {

        var config = {
            alerta: {
                accessKeyVariable: "ACCESS_KEY_VARIABLE",
                hostname: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var Rest = function() {
            return rest;
        }
        var process = {
            env: {
                "ACCESS_KEY_VARIABLE": "access_key"
            }
        }
        var body = {
            "key":  "value",
            "key2": "value2"
        }
        var expectedOptions = {
            hostname: "hostname",
            protocol: "http",
            path: '/api/alert',
            method: 'POST',

        }
        const rest = {
            postBody: function(obj) {
                obj.options.should.deepEqual(expectedOptions);
                obj.body.should.deepEqual(body);
                obj.disableChunks.should.deepEqual(true);
            }
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("process", process);
        toTest.__set__("Rest", Rest);
        var alerta = new toTest(config);
        var result = alerta.sendAlert(body);
        revert();
    });
});