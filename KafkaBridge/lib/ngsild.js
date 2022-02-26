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


module.exports =
function fiwareApi(config) {
  var config = config;
  var rest = new Rest(config);
  var logger = new Logger(config);

  this.getNgsildEntity = function(id){
    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: '/ngsi-ld/v1/entities/' + id,
      method: 'GET',
      headers: {
        "Accept": "application/ld+json"
      }
    };
    return rest.getBody(options);
  };

  /**
   * Gets list of objects defined by urns
   * @param {Array[String]} ids - list of urns to retrieve
   * @param {String} idPattern - Ngsi Pattern
   * @param {Array[String]} attrs - list of attributes (must be defined if type is not defined)
   * @param {Array[String]} type - list of ngsi-ld types  (must be defined if attrs is not defined)
   * @param {Array[String]} queries - list of query parameters
   */
  this.getNgsildEntities = function(params){
    var ids = params.ids;
    var idPattern = params.idPattern;
    var attrs = params.attrs;
    var type = params.type;
    var queries = params.queries;

    if ((attrs == undefined || attrs == null) && (type == undefined || type == null)) {
      throw new Error("Neither attrs nor type is defined. But either of one has to be provided.");
    }
    var listOfIds = null;
    if (ids !== null && ids !== undefined) {
      listOfIds = ids.reduce((list, id) => list += id + ",", "");
      listOfIds = listOfIds.slice(0, -1);
    }
    var listOfAttrs = null;
    if (attrs !== null && attrs !== undefined) {
      listOfAttrs = attrs.reduce((list, id) => list += id + ",", "");
      listOfAttrs = listOfAttrs.slice(0, -1);
    }
    var listOfTypes = null;
    if (type !== null && type !== undefined) {
      listOfTypes = type.reduce((list, id) => list += id + ",", "");
      listOfTypes = listOfTypes.slice(0, -1);
    }
    var listOfQueries = null;
    if (queries !== null && queries !== undefined) {
      listOfQueries = queries.reduce((list, id) => list += id + "|", "");
      listOfQueries = listOfQueries.slice(0, -1);
    }
    var queryString = "?";
    if (listOfIds !== null) {
      queryString += "id=" + listOfIds;
    }
    if (idPattern !== undefined && idPattern !== null) {
      if (queryString.length > 1) {
        queryString += "&"
      }
      queryString += "idPattern=" + idPattern;
    }
    if (listOfAttrs !== undefined && listOfAttrs !== null) {
      if (queryString.length > 1) {
        queryString += "&"
      }
      queryString += "attrs=" + listOfAttrs;
    }
    if (listOfTypes !== undefined && listOfTypes !== null) {
      if (queryString.length > 1) {
        queryString += "&"
      }
      queryString += "type=" + listOfTypes;
    }
    if (listOfQueries !== undefined && listOfQueries !== null) {
      if (queryString.length > 1) {
        queryString += "&"
      }
      queryString += "q=" + listOfQueries;
    }
    
    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: '/ngsi-ld/v1/entities' + queryString,
      method: 'GET',
      headers: {
        "Accept": "application/ld+json"
      }
    };
    return rest.getBody(options);
  };

  /**
   * Gets list of Context Source Registrations for a tenant
   * @param {Array[String]} ids - list of urns to retrieve
   * @param {String} idPattern - Ngsi Pattern
   * @param {Array[String]} attrs - ngsi-ld attributes of monitored(!) entities (NOT of csourceregistration)
   * @param {Array[String]} types - ngsi-ld types of monitored(!) entities
   */
  this.getNgsildCSourceRegistrations = function(params){
    var ids = params.ids;
    var idPattern = params.idPattern;
    var attrs = params.attrs;
    var types = params.types;

    var listOfIds = null;
    if (ids !== null && ids !== undefined) {
      listOfIds = ids.reduce((list, id) => list += id + ",", "");
      listOfIds = listOfIds.slice(0, -1);
    }
  
    var listOfAttrs = null;
    if (attrs !== null && attrs !== undefined) {
      listOfAttrs = attrs.reduce((list, id) => list += id + ",", "");
      listOfAttrs = listOfAttrs.slice(0, -1);
    }

    var listOfTypes = null;
    if (types !== null && types !== undefined) {
      listOfTypes = types.reduce((list, id) => list += id + ",", "");
      listOfTypes = listOfTypes.slice(0, -1);
    }

    var queryString = "?";
    if (listOfIds !== null) {
      queryString += "id=" + listOfIds;
    }
    if (idPattern !== undefined && idPattern !== null) {
      if (queryString.length > 1) {
        queryString += "&"
      }
      queryString += "idPattern=" + idPattern;
    }
    if (listOfAttrs !== undefined && listOfAttrs !== null) {
      if (queryString.length > 1) {
        queryString += "&"
      }
      queryString += "attrs=" + listOfAttrs;
    }
    if (listOfTypes !== undefined && listOfTypes !== null) {
      if (queryString.length > 1) {
        queryString += "&"
      }
      queryString += "type=" + listOfTypes;
    }

    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: '/ngsi-ld/v1/csourceRegistrations' + queryString,
      method: 'GET',
      headers: {
        "Content-type": "application/ld+json",
        "Accept": "application/ld+json"
      }
    };
    return rest.getBody(options);
  };

  /**
   * Deletes a Context Source Registrations for a tenant
   */
  this.deleteNgsildCSourceRegistration = function(id){
  
    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: '/ngsi-ld/v1/csourceRegistrations/' + id,
      method: 'DELETE'
      
    };
    return rest.getBody(options);
  };

  /**
   * Updates a Context Source Registrations for a tenant
   * @param {Object} entity - ngsi-ld context registration entity
   * @param {Boolean} isJsonLd - true if entity contains @context
   */
  this.updateNgsildCSourceRegistration = function(entity, isJsonLd){
    var id = entity.id;
    delete entity["id"];
    delete entity["type"]
    var data = entity;
    var headers = {};
    if (isJsonLd === true) {
      headers["Content-Type"] = "application/ld+json";
    } else {
      headers["Content-Type"] = "application/json";
    }
    const options = {
      hostname: config.ngsildServer.host,
      port: config.ngsildServer.port,
      path: '/ngsi-ld/v1/csourceRegistrations/' + id,
      headers: headers,
      method: 'PATCH'
    };
    return rest.postBody(options, data);
  };

  /**
   * Create CSourceRegistration defined by array
   * @param {Object} entity- CSourceRegistration to create
   * @param {Boolean} isJsonLd - true if it contains @context
   */
  this.createNgsildCSourceRegistration = function(entity, isJsonLd){
    var data = entity;

    var headers = {};
    if (isJsonLd === true) {
      headers["Content-Type"] = "application/ld+json";
    } else {
      headers["Content-Type"] = "application/json";
    }
    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: `/ngsi-ld/v1/csourceRegistrations`,
      headers: headers,
      method: 'POST',
    };
    return rest.postBody(options, data);
  };

  /**
   * 
   * @param {*} type - NGSI-LD type e.g. https://myontolgy/type
   */
  this.getAllObjectsOfType = function(type){
    logger.debug(`getAllObjectsOfType type: ${type}`);
    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: '/ngsi-ld/v1/entities' + "?type=" + type,
      method: 'GET',
      headers: {
        "Accept": "application/ld+json"
      }
    };
    return rest.getBody(options);
    
  };

  /**
   * Deletes list of objects defined by urns
   * @param {Array[String]} ids - list of urns to delete
   */
  this.deleteEntities = function(ids){
    var data = ids;

    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: `/ngsi-ld/v1/entityOperations/delete`,
      headers: {
        "Content-Type": "application/json"
      },
      method: 'POST',
    };
    return rest.postBody(options, data);
  };

  /**
   * Create Entities defined by array
   * @param {array[Object]} entities- Array of entities to create
   */
  this.createEntities = function(entities){
    var data = entities;

    //return new Promise(function(resolve, reject) {
    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: `/ngsi-ld/v1/entityOperations/create`,
      headers: {
        "Content-Type": "application/ld+json"
      },
      method: 'POST',
    };
    return rest.postBody(options, data);
  };

  /**
   * Create Entity defined by array
   * @param {array[Object]} entitiy- Array of entities to create
   */
  this.createEntity = function(entity){
    var data = entity;

    const options = {
      hostname: config.ngsildServer.host,
      port: config.ngsildServer.port,
      path: `/ngsi-ld/v1/entities`,
      headers: {
        "Content-Type": "application/ld+json"
      },
      method: 'POST',
    };
    return rest.postBody(options, data);
  };

  /**
   * Replace Entities defined by array
   * @param {array[Object]} entities - Array of entities to create or update
   * @param {boolean} isUpdate - if this is true, the objects are only updated, not replaced
   * @param {array[Object]} headers - additional headers
   */
  this.replaceEntities = function(entities, isUpdate, {headers}){
    var data = entities;

    var queryString = "";
    if (isUpdate === true) {
      queryString = "?options=update";
    }
    headers = headers || {};
    headers["Content-Type"] = "application/ld+json";
    const options = {
      hostname: config.ngsildServer.host,
      protocol: config.ngsildServer.protocol,
      path: `/ngsi-ld/v1/entityOperations/upsert${queryString}`,
      headers: headers,
      method: 'POST',
    };
    return rest.postBody({options, "body": entities});
  };


  this.updateProperties = function(id, updateObject, noOverwrite, {headers}){
    logger.debug(`updateProperties with id ${id}, updateObject ${JSON.stringify(updateObject)}, noUpdate ${noOverwrite}`)
    var data = updateObject;
    var path = `/ngsi-ld/v1/entities/${id}/attrs`;
    var contentType = "application/json";


    if (noOverwrite) {
        path += "?options=noOverwrite"
    }
    if (updateObject["@context"] !== undefined) {
      contentType = "application/ld+json";
    }

    headers = headers || {};
    headers["Content-Type"] = contentType;

    const options = {
      hostname: config.ngsildServer.host,
      port: config.ngsildServer.port,
      path: path,
      method: 'POST',
      headers: headers
    };
    return rest.postBody(options, data, false, {"noStringify": "true"})

  };

  this.updateProperty = function(id, propertyKey, propertyValue, isRelation, noOverwrite){
    logger.debug(`updateProperty with id ${id}, propertyKey ${propertyKey}, propertyValue ${propertyValue}`)
    var data = {};
    if (isRelation) {
      data[propertyKey] = {
        "type": "Relationship",
        "object": propertyValue
      }
    } else {
      data[propertyKey] = {
          "type": "Property",
          "value": propertyValue
      }
    }
    
    return this.updateProperties(id, data, noOverwrite);
  };

  /**
   *
   * @param {String} id - id of subscription Config
   * @param {String} type - type to subscribe changes to
   * @param {Int} interval - regular interval of updates (or null)
   */
  this.subscribe = function(id, type, interval) {
    var typeUrl = new URL(type);
    var typeOnly = typeUrl.pathname.substring(1);
    typeUrl.pathname="";
    var prefix = typeUrl.toString().slice(0, -1);
    var data = getSubscriptionConfig(typeOnly, prefix);
    logger.debug("subscriptionConfig: " + JSON.stringify(data));
    data.id = id;
    if (interval !== undefined && interval !== null) {
      data.timeInterval = interval;
    }
    logger.debug(`subscribing id: ${id} type: ${type}`);
    const options = {
      hostname: config.ngsildServer.host,
      port: config.ngsildServer.port,
      path: '/ngsi-ld/v1/subscriptions/',
      headers: {"Content-Type": "application/ld+json"},
      method: 'POST'
    };
    return rest.postBody(options, data);
  };

  this.updateSubscription = function(id, type, interval) {
    var typeUrl = new URL(type);
    var typeOnly = typeUrl.pathname.substring(1);
    typeUrl.pathname="";
    var prefix = typeUrl.toString().slice(0, -1);
    var data = getSubscriptionConfig(typeOnly, prefix);
    delete data.id;
    if (interval !== undefined && interval !== null) {
      data.timeInterval = interval;
    }

    const options = {
      hostname: config.ngsildServer.host,
      port: config.ngsildServer.port,
      path: '/ngsi-ld/v1/subscriptions/' + id,
      headers: {"Content-Type": "application/ld+json"},
      method: 'PATCH'
    };
    return rest.postBody(options, data);
  };


  /**
   * Helpers
   */
  var jsonldFilesForTypes = {
    "https://oisp.info": "oisp.jsonld",
    "https://ibn40": "ibn40.jsonld",
    "https://industry-fusion.com": "ibn40.jsonld"
  }
  
  var getSubscriptionConfig = function(type, typePrefix) {
    return {
      "description": "Notify me if " + type + " are changed",
      "id": "urn:ngsi-ld:Subscription:fwbridge001",
      "type": "Subscription",
      "entities": [{"type": `${typePrefix}/${type}`}],
      "notification": {
        "endpoint": {
          "uri": config.bridgeConfig.host + ":" + config.bridgeConfig.port + "/subscription",
          "accept": "application/json"
        }
      },
      "@context": [
          "https://fiware.github.io/data-models/context.jsonld",
          "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.3.jsonld",
          config.bridgeConfig.host + ":" + config.bridgeConfig.port + "/jsonld/" + jsonldFilesForTypes[typePrefix]
      ]
    };
  }
  
  
}
