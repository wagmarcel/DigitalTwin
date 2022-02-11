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
var Logger = require("./logger.js");
const Rest = require("./rest.js");
const Keycloak = require('keycloak-connect');

module.exports = function Alerta(config) {
  var config = config;
  var logger = new Logger(config);
  var rest = new Rest(config);
  var authService = config.keycloak.alertaAuthService;
  var keycloakAdapter = new Keycloak({}, authService);

  var token = config.alerta.accessKey;
  var headers;

  //setInterval(this.updateToken, config.alerta.tokenRefreshInterval * 1000);

  /*this.updateToken = async function() {
    token = await keycloakAdapter.grantManager
          .obtainFromClientCredentials();
    return token;
  }*/

  this.sendAlert = async function(body){
    /*if (token === undefined) {
        token = await this.updateToken();
    }*/
    headers = {};
    headers["Authorization"] = "Key " + token;

    logger.debug(`send alert with body ${JSON.stringify(body)}`)
    headers["Content-type"] = "application/json";
    
    const options = {
      hostname: config.alerta.hostname,
      port: config.alerta.port,
      protocol: config.alerta.protocol,
      path: `/api/alert`,
      method: 'POST',
      headers: headers
    };
    return rest.postBody({options, body, "disableChunks": true})
  
  };
}
  

  