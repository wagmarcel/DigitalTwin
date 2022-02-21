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
const Fiware = require("./ngsild.js");
const { exception } = require("console");
const Keycloak = require('keycloak-connect');

module.exports = function State(config) {
    var config = config;
    var fiware = new Fiware(config);
    var logger = new Logger(config);
    var authService = config.keycloak.ngsildUpdatesAuthService;
    authService.clientId = process.env[config.ngsildUpdates.clientIdVariable];
    authService.resource = process.env[config.ngsildUpdates.clientIdVariable];
    authService.secret = process.env[config.ngsildUpdates.clientSecretVariable];
    authService.realm = process.env[config.ngsildUpdates.clientRealmVariable];
    var keycloakAdapter = new Keycloak({}, authService);
    var token;
    var headers = {};
    var refreshIntervalInMs = config.ngsildUpdates.refreshIntervalInSeconds * 1000;

    this.updateToken = async function() {
      token = await keycloakAdapter.grantManager
            .obtainFromClientCredentials();
      logger.debug("Service token refreshed!");
      return token;
    }
    if (refreshIntervalInMs !== undefined && refreshIntervalInMs !== null) {
      setInterval(this.updateToken, refreshIntervalInMs);
    }
    this.updateToken();

  /**
   * 
   * @param {object} body - object from ngsildUpdate channel
   * 
   * body should contain:
   *  parentId: NGSI-LD id of parent of object - must be defined and !== null
   *  parentRel: parent relationship name which relates to childId (in NGIS-LD terminology)
   *  childObj: NGSI-LD object - either childObj or childId must be defined and !== null.
   */
  this.ngsildUpdates = async function(body) {

    if (token === undefined) {
      token = await this.updateToken();
    }

    headers = {};
    headers["Authorization"] = "Bearer " + token.access_token.token;
    
    if (body.op  === undefined || body.entity === undefined || body.id === undefined || body.overwrite === undefined){
      logger.error("Format of message " + JSON.stringify(body) + " is invalid! Ignoring!");
      return;
    }

    var op = body.op;
    var entity = body.entity;
    var id = body.id;
    var overwrite = body.overwrite;
    var result;

    try {
      // update the entity - do not create it
      if (op === "update") {
          result = await fiware.updateProperties(id, entity, !overwrite, {headers});
          if (result.statusCode !== 204 && result.statusCode !== 207) {
            throw new Error("Entity cannot update entity:" + JSON.stringify(result.body))
          } 
        
      } else if (op === "upsert") {
        // in this case, entity will be created if not existing
        result = await fiware.replaceEntities([entity], !overwrite, {headers});
        if (result.statusCode !== 204) {
          throw new Error("Cannot upsert entity:" + JSON.stringify(result.body));
        }
      }
    } catch(e) {
      throw new Error("Error in REST call: " + e); 
    }
  }
}