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
const sinon = require("sinon");
const rewire = require('rewire');
const toTest = rewire('../lib/rest.js');

const logger = {
    debug: function () {},
    error: function () {}
  };
  

describe('Test postBody', function () {
    it('Should write body', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var options = {
            option: "option"
        };
        var expOptions = {
            option: "option"
        };

        var body = "body";
        var evmap = {};
        var req = {
            on: function(ev, cb) {
                ev.should.equal('error');
            },
            write: function(bo) {
                bo.should.equal(JSON.stringify(body));
            },
            end: function() {

            }
        };
        var http = {
            request: function(options, callback) {
                assert.deepEqual(options, expOptions);
                var res = {
                    on: function(ev, cb) {
                        evmap[ev] = cb;
                    },
                    statusCode: 200
                };
                callback(res);
                return req;
            }
        }
        var resBody = {
            body: "body"
        }
        var expResult = {
            statusCode: 200,
            body: resBody
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("http", http);
        const reqSpy = sinon.spy(req, "end")
        var rest = new toTest(config);
        setTimeout(function(){ 
            evmap['data'](JSON.stringify(resBody))
            evmap['end']();
        }, 1000);
        var result = await rest.postBody({options, body, noStringify: false, disableChunks: false});
        assert.deepEqual(result, expResult);
        assert(reqSpy.calledOnce, "req.end not called once!");
        revert();
    });
    it('Should write body, no stringify', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var options = {
            option: "option"
        };
        var expOptions = {
            option: "option"
        };        
        var body = "body";
        var evmap = {};
        var req = {
            on: function(ev, cb) {
                ev.should.equal('error');
            },
            write: function(bo) {
                bo.should.equal(body);
            },
            end: function() {

            }
        };
        var http = {
            request: function(options, callback) {
                assert.deepEqual(options, expOptions);
                var res = {
                    on: function(ev, cb) {
                        evmap[ev] = cb;
                    },
                    statusCode: 200
                };
                callback(res);
                return req;
            }
        }
        var resBody = {
            body: "body"
        }
        var expResult = {
            statusCode: 200,
            body: resBody
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("http", http);
        const reqSpy = sinon.spy(req, "end")
        var rest = new toTest(config);
        setTimeout(function(){ 
            evmap['data'](JSON.stringify(resBody))
            evmap['end']();
        }, 1000);
        var result = await rest.postBody({options, body, noStringify: true, disableChunks: false});
        assert.deepEqual(result, expResult);
        assert(reqSpy.calledOnce, "req.end not called once!");
        revert();
    });
    it('Should write body, with explicit length header', async function () {

        var config = {
            ngsildServer: {
                host: "hostname",
                protocol: "http" 
            }
        }
        var Logger = function() {
            return logger;
        }
        var expOptions = {
            option: "option",
            headers: {
                "Content-Length": 6
            }
        };
        var options = {
            option: "option",
            headers: {}
        }
        var body = "body";
        var evmap = {};
        var req = {
            on: function(ev, cb) {
                ev.should.equal('error');
            },
            write: function(bo) {
                bo.should.equal(JSON.stringify(body));
            },
            end: function() {

            }
        };
        var http = {
            request: function(options, callback) {
                assert.deepEqual(options, expOptions);
                var res = {
                    on: function(ev, cb) {
                        evmap[ev] = cb;
                    },
                    statusCode: 200
                };
                callback(res);
                return req;
            }
        }
        var resBody = {
            body: "body"
        }
        var expResult = {
            statusCode: 200,
            body: resBody
        }
        var revert = toTest.__set__("Logger", Logger);
        toTest.__set__("http", http);
        const reqSpy = sinon.spy(req, "end")
        var rest = new toTest(config);
        setTimeout(function(){ 
            evmap['data'](JSON.stringify(resBody))
            evmap['end']();
        }, 1000);
        var result = await rest.postBody({options, body, noStringify: false, disableChunks: true});
        assert.deepEqual(result, expResult);
        assert(reqSpy.calledOnce, "req.end not called once!");
        revert();
    });
});
