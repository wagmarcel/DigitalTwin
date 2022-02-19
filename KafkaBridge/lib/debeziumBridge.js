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
const { exception } = require("console");
const { forEach } = require("underscore");
var _ = require('underscore');

module.exports = function DebeziumBridge(config) {
    var config = config;
    var logger = new Logger(config);
  /**
   * 
   * @param {object} body - object from stateUpdate
   * 
   * body should be in debezium format:
   *  before: entity before
   *  after: entity after
   */
  this.parse = function(body) {
    //var before = body.before;
    //var beforeObj = {};
    //var beforeAttrs = {};
    var result =  {
      "entity": null,
      "updatedAttrs": null,
      "deletedAttrs":  null
  }
    if (body === null || body === undefined) {
      return result;
    }
    var before = this.parseBeforeAfterEntity(body.before);
    var beforeEntity = before.entity;
    var beforeAttrs = before.attributes;
    var after = this.parseBeforeAfterEntity(body.after);
    var afterEntity = after.entity;
    var afterAttrs = after.attributes; 
    var isEntityUpdated = this.diffEntity(beforeEntity, afterEntity);
    const {updatedAttrs, deletedAttrs} = this.diffAttributes(beforeAttrs, afterAttrs);
    console.log("Marcel552 " + JSON.stringify(updatedAttrs) + "----------" + JSON.stringify(deletedAttrs))
    var isChanged = isEntityUpdated || Object.keys(updatedAttrs).length > 0 || Object.keys(deletedAttrs).length > 0;
    if (isChanged && Object.keys(afterEntity).length === 0) {
      afterEntity.id = beforeEntity.id;
    }
    result =  {
      "entity": isChanged ? afterEntity : null,
      "updatedAttrs": isChanged ? afterAttrs : null,
      "deletedAttrs": isChanged ? deletedAttrs : null
  }
    return result;
  };

  /**
   * 
   * @param {object} ba - before/after object
   * 
   */
  this.parseBeforeAfterEntity = function(ba) {
    var ba_entity =  {};
    var ba_attrs =  {};
    if (ba == null || ba == undefined) {
      return {"entity": {}, "attributes": {}}
    }
    
    try {
      ba_entity = JSON.parse(ba.data);
      delete ba_entity["@id"];
      delete ba_entity["@type"]
      ba_entity.id = ba.id;
      ba_entity.type = ba.type;
    } catch (e) { logger.error(`Cannot parse debezium before field ${e}`); return;} // not throwing an error due to the fact that it cannot be fixed in next try
    
    // create entity table
    var id = ba_entity.id;
    var res_entity = {};
    Object.keys(ba_entity).filter(key => key != "type" && key != "id").forEach(key => res_entity[key] = id + "\\" + key );
    res_entity.id = ba_entity.id;
    res_entity.type = ba_entity.type;

    // create attribute table
    var id = ba_entity.id;
    Object.keys(ba_entity).filter(key => key != "type" && key != "id").forEach(
      key => {
        var refId = id + "\\" + key;
        var refObjArray = ba_entity[key];
        if (!Array.isArray(refObjArray)) {
          refObjArray = [refObjArray];
        }
        //console.log("Marcel443 " + JSON.stringify(refObjArray))
        ba_attrs[key] = [];
        refObjArray.forEach((refObj, index) => {
          var obj = {};
          obj.id = refId;
          obj.entityId = id;
          obj.synchronized = true;
          obj.name = key;
          if (refObj["https://uri.etsi.org/ngsi-ld/hasValue"] !== undefined) {
            obj["type"] = "https://uri.etsi.org/ngsi-ld/Property";
            obj["https://uri.etsi.org/ngsi-ld/hasValue"] = refObj["https://uri.etsi.org/ngsi-ld/hasValue"][0]["@value"];
            obj["valuetype"] = refObj["https://uri.etsi.org/ngsi-ld/hasValue"][0]["@type"];
          }
          else if (refObj["https://uri.etsi.org/ngsi-ld/hasObject"] !== undefined) {
            obj["type"] = "https://uri.etsi.org/ngsi-ld/Relationship";
            obj["https://uri.etsi.org/ngsi-ld/hasObject"] = refObj["https://uri.etsi.org/ngsi-ld/hasObject"][0]["@id"];
          } else {
            return
          }
          obj.index = index;
          ba_attrs[key].push(obj);
          //console.log("Marcel442 " + JSON.stringify(obj));
        })
      });
    return {"entity": res_entity, "attributes": ba_attrs}
  }

  /**
   * 
   * @param {object} before - before object
   * @param {object} after - after object
   * @returns true if Entities are different
   */
  this.diffEntity = function(before, after) {
    return !_.isEqual(before, after); 
   }

  /**
   * 
   * @param {object} beforeAttrs - object with atrributes
   * @param {object} afterAttrs - object with attributes
   * @returns list with updated and deleted atributes {updatedAttrs, deletedAttrs}
   */
  this.diffAttributes = function(beforeAttrs, afterAttrs) {
    var updatedAttrs =  {};
    var deletedAttrs = {};
    Object.keys(beforeAttrs).forEach(key => {
      //var obj = {};
      if (afterAttrs[key] === undefined || afterAttrs[key] === null || !Array.isArray(afterAttrs[key]) || afterAttrs[key].length === 0) {
        var obj = beforeAttrs[key].reduce((accum, element) => {var obj = {}; obj["id"] = element["id"]; obj["index"] = element["index"]; accum.push(obj); return accum}, [])
        //obj["id"] = beforeAttrs[key]["id"];
        deletedAttrs[key] = obj;
      }
    })
    Object.keys(afterAttrs).forEach(key => {
      //var obj = {};
      if (!_.isEqual(afterAttrs[key], beforeAttrs[key])) {
        // delete all old elements
        var obj = afterAttrs[key].reduce((accum, element) => {var obj = {}; obj["id"] = element["id"]; obj["index"] = element["index"]; accum.push(obj); return accum}, [])
        deletedAttrs[key] = obj;
        // and create new one
        updatedAttrs[key] = afterAttrs[key];
      }
    });
    return {updatedAttrs, deletedAttrs}
  }
}