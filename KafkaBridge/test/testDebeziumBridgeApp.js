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
const { resolve } = require('path/posix');
global.should = chai.should();

const rewire = require('rewire');
const toTest = rewire('../debeziumBridge/app.js');

const logger = {
    debug: function () {},
    error: function () {}
  };
  
describe('Test GetTopic', function () {
    it('Should return last part of url', async function () {
        const getTopic = toTest.__get__('getTopic');
        var result = getTopic("http://example/Device");
        result.should.equal("Device");
    });
});  

describe('Test getSubclasses', function () {
    it('Should construct queryterm and use right rdfSource', async function () {
        var config = {
            debeziumBridge: {
                rdfSource: "rdfSource"
            }
        }
        var klass = "klass";
        var queryTermExpected = `
    PREFIX iff: <https://industry-fusion.com/types/v0.9/>
    SELECT ?o WHERE {
    <${klass}> rdfs:subClassOf* ?o.
    } LIMIT 100`;
        var res = {
            bindings: () => new Promise(function(resolve, reject) {
                resolve([
                    {
                        get: (arg) => {arg.should.equal("?o"); return { value: "subklass"}}
                    }
                ]);
            })
        }
        var iffEngine = {
            query: function (queryTerm, {sources}) { 
                return new Promise(function(resolve, reject) { 
                    assert(sources === config.debeziumBridge.rdfSources);
                    queryTerm.should.equal(queryTermExpected)
                    resolve(res);
                })
            }
        }
        var revert = toTest.__set__('iffEngine', iffEngine);
        toTest.__set__('config', config); 
        const getSubClasses = toTest.__get__('getSubClasses');
        var result = await getSubClasses(klass);
        result[0].should.equal("subklass");
    });
});