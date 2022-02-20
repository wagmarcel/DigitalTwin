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

const GROUPID = "statekafkabridge";
const CLIENTID = "statekafkaclient";
const { Kafka } = require('kafkajs');
var config = require("../config/config.js");
var State = require("../lib/ngsildUpdates.js");
var Logger = require("../lib/logger.js");

var state = new State(config);
var logger = new Logger(config);

const kafka = new Kafka({
  clientId: CLIENTID,
  brokers: config.kafka.brokers
})

const consumer = kafka.consumer({ groupId: GROUPID })
console.log(JSON.stringify(config))

var startListener = async function() {

    await consumer.connect()
    await consumer.subscribe({ topic: config.ngsildUpdates.topic, fromBeginning: false })

    await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
            try {
                var body = JSON.parse(message.value);
                await state.ngsildUpdates(body);
                //.catch((err) => logger.error("Could not send model update: " + err))
            } catch (e) {
                logger.error("could not process message: " + e);
            }

        },
    }).catch(e => logger.error(`[StateUpdater/consumer] ${e.message}`, e))

    const errorTypes = ['unhandledRejection', 'uncaughtException']
    const signalTraps = ['SIGTERM', 'SIGINT', 'SIGUSR2']

    errorTypes.map(type => {
        process.on(type, async e => {
            try {
            console.log(`process.on ${type}`)
            console.error(e)
            await consumer.disconnect()
            process.exit(0)
            } catch (_) {
            process.exit(1)
            }
        })
    })

    signalTraps.map(type => {
        process.once(type, async () => {
            try {
                await consumer.disconnect()
            } finally {
                process.kill(process.pid, type)
            }
        })
    })
}

logger.info("Now starting Kafka listener");
startListener();