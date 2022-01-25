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
var assert = require("assert");
var expect = require('chai').expect;
var should = require('chai').should();
var rewire = require("rewire");
var toTest = rewire("../gateway.js");
var flinkVersion = "1.14.3";

var logger = {
    "debug": function(){},
    "error": function(){}
}

describe('Test health path', function() {
    it('Should return 200 and OK', function(){
        var response = {
            "status": function(val){
                val.should.equal(200);
                return {
                    "send": function(state) {
                    state.should.equal('OK');
                    }
                }
            }
        }
        var revert = toTest.__set__({ 
            "logger": logger
        });

        var appget = toTest.__get__("appget");
        appget(null, response);
        revert();
    });
    
});
describe('Test statement path', function() {
    it('Test exec command for sqlclient', function(){
        var fsWriteFilename;
        var statement = "select *;";
        var flinkSqlCommand = `./flink-${flinkVersion}/bin/sql-client.sh -l ./jars -f `;

        var response = {
            "status": function(val){
                
            }
        };
        var request = {
            "body": {
                "statement": statement
            }
        }
        var exec = function(command, output) {
            command.should.equal(flinkSqlCommand + fsWriteFilename);
        }
        var fs = {
            "writeFileSync": function(filename, data) {
                fsWriteFilename = filename;
                data.should.equal(statement);
            }
        }
        var revert = toTest.__set__({ 
            "logger": logger,
            "exec": exec,
            fs: fs
        });

        var apppost = toTest.__get__("apppost");
        apppost(request, response);
        revert();
    });
    it('Test empty body (should return 500)', function(){

        var response = {
            "status": function(val){
                val.should.equal(500);
            },
            "send": function(val){
                val.should.equal('Wrong format! No statement field in body')
            }
        };
        var request = {
        }
        var request2 = {
            "body": undefined
        }
        var request3 = {
            "body": null
        }
        var request4 = {
            "body": {
                statement: undefined
            }
        }
    
        var revert = toTest.__set__({ 
            "logger": logger,
        });

        var apppost = toTest.__get__("apppost");
        apppost(request, response);
        apppost(request2, response);
        apppost(request3, response);
        apppost(request4, response);
        revert();
    });
    it('Test exec output with exec error (should return 500)', function(){
        var error = 'error';

        var response = {
            "status": function(val){
                val.should.equal(500);
            },
            "send": function(val){
                val.should.equal('Error while executing sql-client: ' + error)
            }
        };
        var uuid = {
            "v4": () => "uuid"
        };
        var fs = {
            "unlinkSync": function(filename) {
                filename.should.equal('/tmp/script_uuid.sql');
            },
            "writeFileSync": () => {}
        }
        var request = {
            "body": {
                "statement": "select *;"
            }
        }
        var exec = function(command, output) {
            output(error, null, null)
        }
        var revert = toTest.__set__({ 
            "logger": logger,
            "exec": exec,
            "uuid": uuid,
            "fs": fs
        });

        var apppost = toTest.__get__("apppost");
        apppost(request, response);
        revert();
    });
    it('Test exec output with Job ID (should return 200)', function(){
        var stdout = 'Job ID: abcdef123456789';
        var response = {
            "status": function(val){
                val.should.equal(200);
                return {
                    "send": function(state) {
                    state.should.equal('{ "jobid": "abcdef123456789" }');
                    }
                }
            },
            "send": function(val){
                val.should.equal('Error while executing sql-client: ' + error)
            }
        };
        var uuid = {
            "v4": () => "uuid"
        };
        var fs = {
            "unlinkSync": function(filename) {
                filename.should.equal('/tmp/script_uuid.sql');
            },
            "writeFileSync": () => {}
        }
        var request = {
            "body": {
                "statement": "select *;"
            }
        }
        var exec = function(command, output) {
            output(null, stdout, null)
        }
        var revert = toTest.__set__({ 
            "logger": logger,
            "exec": exec,
            "uuid": uuid,
            "fs": fs
        });

        var apppost = toTest.__get__("apppost");
        apppost(request, response);
        revert();
    });
    it('Test exec output with no Job ID (should return 500)', function(){
        var stdout = 'Job : error';
        var response = {
            "status": function(val){
                val.should.equal(500);
            },
            "send": function(state) {
                state.should.equal('Not successfully submitted. No JOB ID found in server reply.');
            }
            
        };
        var uuid = {
            "v4": () => "uuid"
        };
        var fs = {
            "unlinkSync": function(filename) {
                filename.should.equal('/tmp/script_uuid.sql');
            },
            "writeFileSync": () => {}
        }
        var request = {
            "body": {
                "statement": "select *;"
            }
        }
        var exec = function(command, output) {
            output(null, stdout, null)
        }
        var revert = toTest.__set__({ 
            "logger": logger,
            "exec": exec,
            "uuid": uuid,
            "fs": fs
        });

        var apppost = toTest.__get__("apppost");
        apppost(request, response);
        revert();
    });
});