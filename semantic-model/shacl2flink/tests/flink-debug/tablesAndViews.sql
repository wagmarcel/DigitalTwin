
SET 'table.local-time-zone' = 'UTC';


-- ALERT Management
-- Consist of 3 tables, 2 bulk/filter tables and the bridge table
-- bulk tables are for cases when high frequency data needs to be filtered
-- For instance the alerts are only created when they change significant fields
-- A bulk consist of an insert table which must be upsert-kafka
drop table if exists alerts_bulk;
CREATE TABLE alerts_bulk (
  resource STRING,
  event STRING,
  environment STRING,
  service ARRAY<STRING>,
  severity STRING,
  customer STRING,
  `text` STRING,
  PRIMARY KEY (resource, event) NOT ENFORCED /*,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp',
    WATERMARK FOR ts AS ts*/
) WITH (
 'connector' = 'upsert-kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'value.format' = 'json',
  'key.format' = 'json',
  'topic' = 'iff.alerts.bulk'
);
-- second part of the bulk table is a plain kafka input table
drop table if exists alerts_filter;
CREATE TABLE alerts_filter (
  resource STRING,
  event STRING,
  environment STRING,
  service ARRAY<STRING>,
  severity STRING,
  customer STRING,
  `text` STRING,
  `offset` BIGINT METADATA VIRTUAL,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp',
   WATERMARK FOR `ts` AS `ts`
) WITH (
 'connector' = 'kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'format' = 'json',
   'scan.startup.mode' = 'latest-offset',
  'topic' = 'iff.alerts.bulk'
);


-- iff Alert table
-- ---------------
drop table if exists alerts;
CREATE TABLE alerts (
  resource STRING,
  event STRING,
  environment STRING,
  service ARRAY<STRING>,
  severity STRING,
  customer STRING,
  `text` STRING,
 -- `timestamp` TIMESTAMP(3) METADATA VIRTUAL,
  PRIMARY KEY (resource, event) NOT ENFORCED
) WITH (
 'connector' = 'upsert-kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'value.format' = 'json',
  'key.format' = 'json',
  'topic' = 'iff.alerts'
);


-- iff CloudEvents table
------------------------
drop table if exists cloud_events;
CREATE TABLE cloud_events (
  source STRING,
  specversion STRING,
  `type` STRING,
  data STRING,
 `time` TIMESTAMP(3) METADATA VIRTUAL,
  --watermark for `time` as `time`,
  PRIMARY KEY (source) NOT ENFORCED
) WITH (
 'connector' = 'upsert-kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'value.format' = 'json',
  'key.format' = 'json',
  'topic' = 'iff.cloud-events'
);


drop table if exists cloud_events_filter;
CREATE TABLE cloud_events_filter (
  source STRING,
  specversion STRING,
  `type` STRING,
  data STRING,
 `timestamp` TIMESTAMP(3) METADATA VIRTUAL,
  watermark for `timestamp` as `timestamp`
) WITH (
 'connector' = 'kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'format' = 'json',
   'scan.startup.mode' = 'latest-offset',
  'topic' = 'iff.cloud-events'
);


-- Metrics Table
------------------------
drop table if exists metrics;
CREATE TABLE metrics (
  eid STRING,
  pid STRING,
  `value` STRING,
  `on` BIGINT,
  ts AS to_timestamp_ltz(`on`, 3),
  WATERMARK FOR ts AS ts - INTERVAL '0.001' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'metrics',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json'
);



---------- Entity tables ---------------------
---------------------------------------------
-- consist of two Tables the normal kafka table
-- and the View
--
-- Machine
drop table if exists machine;
CREATE TABLE machine (
  `id` STRING,
  `type` STRING,
  `https://industry-fusion.com/types/v0.9/state` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
   WATERMARK FOR ts AS ts
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.entities.machine',
  'scan.startup.mode' = 'latest-offset',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true',
  'format' = 'json'
);
drop view if exists machine_view;
create view machine_view as
SELECT id, `type`, `https://industry-fusion.com/types/v0.9/state`, ts
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY `id`
         ORDER BY ts DESC) AS rownum
      FROM `machine` )
WHERE rownum = 1;

-- Cutter
drop table if exists cutter;
CREATE TABLE cutter (
  `id` STRING,
  `type` STRING,
  `https://industry-fusion.com/types/v0.9/hasInWorkpiece` STRING,
    `https://industry-fusion.com/types/v0.9/hasOutWorkpiece` STRING,
  `https://industry-fusion.com/types/v0.9/hasFilter` STRING,
  `https://industry-fusion.com/types/v0.9/state` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
   WATERMARK FOR ts AS ts
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.entities.cutter',
  'scan.startup.mode' = 'latest-offset',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true',
  'format' = 'json'
);
drop view if exists cutter_view;
create view cutter_view as
SELECT id, `type`, `https://industry-fusion.com/types/v0.9/hasInWorkpiece`, `https://industry-fusion.com/types/v0.9/hasOutWorkpiece`,
    `https://industry-fusion.com/types/v0.9/hasFilter`, `https://industry-fusion.com/types/v0.9/state`, ts
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY `id`
         ORDER BY ts DESC) AS rownum
      FROM `cutter` )
WHERE rownum = 1;

-- Filter
drop table if exists `filter`;
CREATE TABLE `filter` (
   id STRING,
  `type` STRING,
  `https://industry-fusion.com/types/v0.9/strength` STRING,
  `https://industry-fusion.com/types/v0.9/hasCartridge` STRING,
  `https://industry-fusion.com/types/v0.9/state` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
    WATERMARK FOR ts AS ts
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.entities.filter',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
   'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true',
  'format' = 'json'
);
drop view if exists filter_view;
create view filter_view as
SELECT id, `type`, `https://industry-fusion.com/types/v0.9/strength`, `https://industry-fusion.com/types/v0.9/hasCartridge`, `https://industry-fusion.com/types/v0.9/state`, ts
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY `id`
         ORDER BY ts DESC) AS rownum
      FROM `filter` )
WHERE rownum = 1;


-- Entity
drop table if exists `linked_entity`;
CREATE TABLE `linked_entity` (
   id STRING,
  `type` STRING,
  `https://industry-fusion.com/types/v0.9/jsonEntity` STRING,
  `https://industry-fusion.com/types/v0.9/linkedTo` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
   WATERMARK FOR ts AS ts
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.entities.linkedEntity',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
   'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true',
  'format' = 'json'
);
drop view if exists linked_entity_view;
create view linked_entity_view as
SELECT id, `type`, `https://industry-fusion.com/types/v0.9/jsonEntity`, `https://industry-fusion.com/types/v0.9/linkedTo`, ts
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY `id`
         ORDER BY ts DESC) AS rownum
      FROM `linked_entity` )
WHERE rownum = 1;


-- Workpiece
drop table if exists `workpiece`;
CREATE TABLE `workpiece` (
   id STRING,
  `type` STRING,
  `https://industry-fusion.com/types/v0.9/material` STRING,
  `https://schema.org/depth` STRING,
  `https://industry-fusion.com/types/v0.9/qualityCheck` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
   WATERMARK FOR ts AS ts
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.entities.workpiece',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
   'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true',
  'format' = 'json'
);
drop view if exists workpiece_view;
create view workpiece_view as
SELECT id, `type`, `https://industry-fusion.com/types/v0.9/material`, `https://schema.org/depth`, `https://industry-fusion.com/types/v0.9/qualityCheck`, ts
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY `id`
         ORDER BY ts DESC) AS rownum
      FROM `workpiece` )
WHERE rownum = 1;


-- Cartridge
drop table if exists `filter_cartridge`;
CREATE TABLE `filter_cartridge` (
   id STRING,
  `type` STRING,
  `https://industry-fusion.com/types/v0.9/wasteClass` STRING,
  `https://industry-fusion.com/types/v0.9/inUseFrom` STRING,
  `https://industry-fusion.com/types/v0.9/inUseUntil` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
   WATERMARK FOR ts AS ts
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.entities.filter_cartridge',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
   'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true',
  'format' = 'json'
);
drop view if exists filter_cartridge_view;
create view filter_cartridge_view as
SELECT id, `type`, `https://industry-fusion.com/types/v0.9/wasteClass`, `https://industry-fusion.com/types/v0.9/inUseFrom`, `https://industry-fusion.com/types/v0.9/inUseUntil`, ts
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY `id`
         ORDER BY ts DESC) AS rownum
      FROM `filter_cartridge` )
WHERE rownum = 1;

drop view if exists filter_cartridge_diff;
create view filter_cartridge_diff as
SELECT id, `type`, `https://industry-fusion.com/types/v0.9/wasteClass`, 'https://industry-fusion.com/types/v0.9/usedFrom', 'https://industry-fusion.com/types/v0.9/usedUntil', rownum, ts
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY `id`
         ORDER BY ts DESC) AS rownum
      FROM `filter_cartridge` )
WHERE rownum <= 2;

-- Attribute table
-- ---------------
drop table if exists attributes;
CREATE TABLE attributes (
  id STRING,
  entityId STRING,
  name STRING,
  nodeType STRING,
  valueType STRING,
  index INTEGER,
  `type` STRING,
  `https://uri.etsi.org/ngsi-ld/hasValue` STRING,
  `https://uri.etsi.org/ngsi-ld/hasObject` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
  WATERMARK FOR ts AS ts
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.attributes',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true'
);


drop table if exists attributes_writeback;
CREATE TABLE attributes_writeback (
  id STRING,
  entityId STRING,
  name STRING,
  nodeType STRING,
  valueType STRING,
  index INTEGER,
  `type` STRING,
  `https://uri.etsi.org/ngsi-ld/hasValue` STRING,
  `https://uri.etsi.org/ngsi-ld/hasObject` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp',
  WATERMARK FOR ts AS ts,
  PRIMARY KEY (id, index) NOT ENFORCED
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'iff.ngsild.attributes',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'value.format' = 'json',
  'key.format' = 'json',
'value.json.fail-on-missing-field' = 'false',
  'value.json.ignore-parse-errors' = 'true'
);

drop table if exists attributes_insert;
CREATE TABLE attributes_insert (
  id STRING,
  entityId STRING,
  name STRING,
  nodeType STRING,
  valueType STRING,
  index INTEGER,
  `type` STRING,
  `https://uri.etsi.org/ngsi-ld/hasValue` STRING,
  `https://uri.etsi.org/ngsi-ld/hasObject` STRING,
  --`ts` TIMESTAMP(3) METADATA FROM 'timestamp',
   --WATERMARK FOR ts AS ts,
  PRIMARY KEY (id, index) NOT ENFORCED

) WITH (
 'connector' = 'upsert-kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'value.format' = 'json',
  'key.format' = 'json',
  'topic' = 'iff.ngsild.attributes_insert',
  'value.json.fail-on-missing-field' = 'false',
  'value.json.ignore-parse-errors' = 'true'
);

drop table if exists attributes_insert_filter;
CREATE TABLE attributes_insert_filter (
  id STRING,
  entityId STRING,
  name STRING,
  nodeType STRING,
  valueType STRING,
  index INTEGER,
  `type` STRING,
  `https://uri.etsi.org/ngsi-ld/hasValue` STRING,
  `https://uri.etsi.org/ngsi-ld/hasObject` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp',
  
  WATERMARK FOR ts AS ts
  --PRIMARY KEY (id, index) NOT ENFORCED

) WITH (
 'connector' = 'kafka',
  'topic' = 'iff.ngsild.attributes_insert',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'format' = 'json',
   'scan.startup.mode' = 'latest-offset',
   'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true'
);

drop view if exists attributes_view;
create view attributes_view as
SELECT id, entityId, name, nodeType, valueType, index, `type`, `https://uri.etsi.org/ngsi-ld/hasValue`, `https://uri.etsi.org/ngsi-ld/hasObject`, ts
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY `id`, index
         ORDER BY ts DESC) AS rownum
      FROM `attributes` )
WHERE rownum = 1 and entityId is NOT NULL;

--------- ngsild updates table
------------------------------
drop table if exists ngsild_updates;
CREATE TABLE ngsild_updates (
  op STRING,
  overwriteOrReplace BOOLEAN,
  noForward BOOLEAN,
  entities STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild-updates',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true'
);

drop table if exists ngsild_updates_bulk;
CREATE TABLE ngsild_updates_bulk (
  entityId STRING,
  name STRING,
  attributes STRING,
  PRIMARY KEY (entityId, name) NOT ENFORCED
) WITH (
 'connector' = 'upsert-kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'value.format' = 'json',
  'key.format' = 'json',
  'topic' = 'iff.ngsild-updates.bulk'
);

drop table if exists ngsild_updates_filter;
CREATE TABLE ngsild_updates_filter (
  entityId STRING,
  name STRING,
  attributes STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp',
   WATERMARK FOR `ts` AS `ts`
) WITH (
 'connector' = 'kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'format' = 'json',
   'scan.startup.mode' = 'latest-offset',
  'topic' = 'iff.ngsild-updates.bulk'
);


DROP TABLE IF EXISTS `schedule_entity`;
CREATE TABLE `schedule_entity` (
`id` STRING,
`type` STRING,
`https://industry-fusion.com/types/v0.9/startTime` STRING,
`https://industry-fusion.com/types/v0.9/endTime` STRING,
`https://industry-fusion.com/types/v0.9/activeState` STRING,
`ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
  WATERMARK FOR ts AS ts - INTERVAL '0.001' SECOND
  ) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.entities.schedule_entity',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true'
);


DROP VIEW IF EXISTS `schedule_entity_view`;
CREATE VIEW `schedule_entity_view` AS
SELECT `id`,`type`,
`https://industry-fusion.com/types/v0.9/startTime`,
`https://industry-fusion.com/types/v0.9/endTime`,
`https://industry-fusion.com/types/v0.9/activeState`,
`ts` FROM (
  SELECT *,
ROW_NUMBER() OVER (PARTITION BY `id`
ORDER BY ts DESC) AS rownum
FROM `schedule_entity` )
WHERE rownum = 1;

DROP TABLE IF EXISTS `rdf`;
CREATE TABLE `rdf` (
`subject` STRING,
`predicate` STRING,
`object` STRING,
`index` INTEGER,
PRIMARY KEY(`subject`,`predicate`,`index`)
 NOT ENFORCED
) WITH (
 'connector' = 'upsert-kafka',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'topic' = 'iff.rdf',
   'value.format' = 'json',
  'key.format' = 'json',
  'key.json.fail-on-missing-field' = 'false',
  'key.json.ignore-parse-errors' = 'true',
  'value.json.fail-on-missing-field' = 'false',
  'value.json.ignore-parse-errors' = 'true'
);

DROP TABLE IF EXISTS `oee_template`;
CREATE TABLE `oee_template` (
`id` STRING,
`type` STRING,
`https://industry-fusion.com/types/v0.9/startTime` STRING,
`https://industry-fusion.com/types/v0.9/endTime` STRING,
`https://industry-fusion.com/oee/v0.9/availabilityState` STRING,
`https://industry-fusion.com/oee/v0.9/availabilityTimeAgg` STRING,
`https://industry-fusion.com/oee/v0.9/runTime` STRING,
`https://industry-fusion.com/oee/v0.9/netRunTime` STRING,
`https://industry-fusion.com/oee/v0.9/goodCount` STRING,
`https://industry-fusion.com/oee/v0.9/totalCount` STRING,
`https://industry-fusion.com/oee/v0.9/hasReferenceMachine` STRING,
`https://industry-fusion.com/types/v0.9/activeState` STRING,
`https://industry-fusion.com/oee/v0.9/oeeSummary` STRING,
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
   WATERMARK FOR ts AS ts
) WITH (
  'connector' = 'kafka',
  'topic' = 'iff.ngsild.entities.oee_template',
  'properties.bootstrap.servers' = 'my-cluster-kafka-bootstrap:9092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.fail-on-missing-field' = 'false',
  'json.ignore-parse-errors' = 'true'
);

DROP VIEW IF EXISTS `oee_template_view`;
CREATE VIEW `oee_template_view` AS
SELECT `id`,`type`,
`https://industry-fusion.com/types/v0.9/startTime`,
`https://industry-fusion.com/types/v0.9/endTime`,
`https://industry-fusion.com/oee/v0.9/availabilityState`,
`https://industry-fusion.com/oee/v0.9/availabilityTimeAgg`,
`https://industry-fusion.com/oee/v0.9/runTime`,
`https://industry-fusion.com/oee/v0.9/netRunTime`,
`https://industry-fusion.com/oee/v0.9/goodCount`,
`https://industry-fusion.com/oee/v0.9/totalCount`,
`https://industry-fusion.com/oee/v0.9/hasReferenceMachine`,
`https://industry-fusion.com/types/v0.9/activeState`,
`https://industry-fusion.com/oee/v0.9/oeeSummary`,
`ts` FROM (
  SELECT *,
ROW_NUMBER() OVER (PARTITION BY `id`
ORDER BY ts DESC) AS rownum
FROM `oee_template` )
WHERE rownum = 1;
