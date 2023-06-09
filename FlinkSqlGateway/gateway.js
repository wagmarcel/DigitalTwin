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
const express = require('express');
const { exec } = require('child_process');
const uuid = require('uuid');
const fs = require('fs');
const app = express();
const bodyParser = require('body-parser');

const logger = require('./lib/logger.js');
const port = process.env.SIMPLE_FLINK_SQL_GATEWAY_PORT || 9000;
const flinkVersion = '1.14.3';
const flinkRoot = process.env.SIMPLE_FLINK_SQL_GATEWAY_ROOT || `./flink-${flinkVersion}`;
const flinkSqlClient = '/bin/sql-client.sh -l ';
const sqlJars = process.env.SIMPLE_FLINK_SQL_GATEWAY_JARS || './jars';
const runningAsMain = require.main === module;

const udfdir = "/tmp/udf"



function appget (_, response) {
  response.status(200).send('OK');
  logger.debug('Health Endpoint was requested.');
};



function apppost (request, response) {
  // for now ignore session_id
  const body = request.body;
  if (body === undefined || body === null || body.statement === undefined) {
    response.status(500);
    response.send('Wrong format! No statement field in body');
    return;
  }
  const id = uuid.v4();
  const filename = '/tmp/script_' + id + '.sql';
  fs.writeFileSync(filename, body.statement.toString());
  const command = flinkRoot + flinkSqlClient + sqlJars + ' -f ' + filename;
  logger.debug('Now executing ' + command);
  exec(command, (error, stdout, stderr) => {
    fs.unlinkSync(filename);
    if (error) {
      logger.error('Error while executing sql-client: ' + error);
      response.status(500);
      response.send('Error while executing sql-client: ' + error);
      return;
    }
    // find Job ID ind stdout, e.g.
    // Job ID: e1ebb6b314c82b27cf81cbc812300d97
    const regexp = /Job ID: ([0-9a-f]*)/i;
    const found = stdout.match(regexp);
    logger.debug('Server output: ' + stdout);
    if (found !== null && found !== undefined) {
      const jobId = found[1];
      logger.debug('jobId found:' + jobId);
      response.status(200).send('{ "jobid": "' + jobId + '" }');
    } else { // no JOB ID found, unsuccessful
      response.status(500);
      response.send('Not successfully submitted. No JOB ID found in server reply.');
    }
  });
}


function udfget (req, res) {
  var filename = req.params.filename;
  logger.debug('python_udf get was requested for: ' + filename);
  var fullname = `${udfdir}/${filename}.py`;
  try {
    fs.readFileSync(fullname);
  } catch (err) {
    res.status(404).send('File not Found');
    logger.info('File not found: ' + fullname)
    return
  }
  res.status(200).send('OK')
};


function udfpost(req, res){
  var filename = req.params.filename;
  var body = req.body;
  if (body === undefined || body === null) {
    response.status(500);
    response.send('No body received!');
    return;
  }
  logger.debug(`python_udf with name ${filename}`);
  var fullname = `${udfdir}/${filename}.py`;
  try {
    fs.writeFileSync(fullname, body);
  } catch (err) {
    res.status(500).send('Could not write file: ' + err);
    logger.error('WriteSync failed:' + err);
    return
  }
  res.status(201).send('CREATED')
}

if(!fs.existsSync(udfdir)){
  fs.mkdirSync(udfdir)
}

app.use(express.json({ limit: '10mb' }));

app.get('/health', appget);
app.get('/v1/python_udf/:filename', udfget);

app.post('/v1/sessions/:session_id/statements', apppost);
app.post('/v1/python_udf/:filename', bodyParser.text(), udfpost);

if (runningAsMain) {
  app.listen(port, function () {
    console.log('Listening on port ' + port);
  });
}
