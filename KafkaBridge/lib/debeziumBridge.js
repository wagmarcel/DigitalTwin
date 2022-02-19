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
   * Provide entitiy and attributes separated
   * @param {object} ba - before/after object from Debezium 
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
      // Delete all non-properties as defined by ETSI SPEC (ETSI GS CIM 009 V1.5.1 (2021-11))
      delete ba_entity["@id"];
      delete ba_entity["@type"];
      delete ba_entity["https://uri.etsi.org/ngsi-ld/createdAt"];
      delete ba_entity["https://uri.etsi.org/ngsi-ld/modifiedAt"];
      delete ba_entity["https://uri.etsi.org/ngsi-ld/obvervedAt"];
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
    
    // Determine all attributes which are found in beforeAttrs but not in afterAttrs
    // These attributes are added to deleteAttrs
    Object.keys(beforeAttrs).forEach(key => {
      if (afterAttrs[key] === undefined || afterAttrs[key] === null || !Array.isArray(afterAttrs[key]) || afterAttrs[key].length === 0) {
        var obj = beforeAttrs[key].reduce((accum, element) => {
          var obj = {}; 
          obj["id"] = element["id"]; 
          obj["index"] = element["index"]; 
          accum.push(obj); 
          return accum;
        }, [])
        deletedAttrs[key] = obj;
      }
    })

    // Determine all attributes which are changed and add them to updatedAttrs
    // Detect wheter before had higher index and add these to deleteAttrs
    Object.keys(afterAttrs).forEach(key => {
      // if the attributes are unequal
      // add every different attribute per index to the updatedAttrs
      // add every attribute which have indexes in before but not mentioned in after to deletedAttrs 
      if (!_.isEqual(afterAttrs[key], beforeAttrs[key])) {
        // delete all old elements with higher indexes
        // the attribute lists are sorted so length diff reveals what has to be deleted
        var delementArray = [];
        if (beforeAttrs.length > afterAttrs.length) {
          for(var i = afterAttrs.length; i < beforeAttrs.length; i++) {
            var delement = {};
            delement[id] = beforeAttrs[id];
            delement[index] = i;
            delementArray.push(delement);
          }
          deletedAttrs[key] = delementArray;
        }
        // and create new one
        updatedAttrs[key] = afterAttrs[key];
      }
    });
    return {updatedAttrs, deletedAttrs}
  }
}