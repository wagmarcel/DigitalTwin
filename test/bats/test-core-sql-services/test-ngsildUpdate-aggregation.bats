#!/usr/bin/env bats

if [ -z "${SELF_HOSTED_RUNNER}" ]; then
    SUDO="sudo -E"
fi

ATTRIBUTE1=/tmp/ATTRIBUTE1
ATTRIBUTE2=/tmp/ATTRIBUTE2
ATTRIBUTE3=/tmp/ATTRIBUTE3
ATTRIBUTE4=/tmp/ATTRIBUTE4
ATTRIBUTE5=/tmp/ATTRIBUTE5
FLUSH_ATTRIBUTE=/tmp/FLUSH_ATTRIBUTE
ATTRIBUTES_TOPIC=iff.ngsild.attributes
KAFKACAT_ATTRIBUTES=/tmp/KAFKACAT_ATTRIBUTES
KAFKACAT_ATTRIBUTES_FILTERED=/tmp/KAFKACAT_ATTRIBUTES_FILTERED
KAFKACAT_ATTRIBUTES_FROMJSON=/tmp/KAFKACAT_ATTRIBUTES_FROMJSON
KAFKA_BOOTSTRAP=my-cluster-kafka-bootstrap:9092
KAFKACAT_NGSILD_UPDATES_TOPIC=iff.ngsildUpdates
CUTTER_ID=urn:plasmacutter-test:12345

cat << EOF | tr -d '\n' > ${ATTRIBUTE1}
{
    "id": "${CUTTER_ID}\\\https://industry-fusion.com/types/v0.9/state",
    "entityId": "${CUTTER_ID}",
    "name": "https://industry-fusion.com/types/v0.9/state",
    "type": "https://uri.etsi.org/ngsi-ld/Property",
    "https://uri.etsi.org/ngsi-ld/hasValue": "ON",
    "index": 0
}
EOF
cat << EOF | tr -d '\n' > ${ATTRIBUTE2}
{
    "id": "${CUTTER_ID}\\\https://industry-fusion.com/types/v0.9/state",
    "entityId": "${CUTTER_ID}",
    "name": "https://industry-fusion.com/types/v0.9/state",
    "type": "https://uri.etsi.org/ngsi-ld/Property",
    "https://uri.etsi.org/ngsi-ld/hasValue": "OFF",
    "index": 0
}
EOF
cat << EOF | tr -d '\n' > ${FLUSH_ATTRIBUTE}
{
    "id": "flush\\\https://industry-fusion.com/types/v0.9/state",
    "entityId": "flush",
    "name": "https://industry-fusion.com/types/v0.9/flush",
    "type": "https://uri.etsi.org/ngsi-ld/Property",
    "https://uri.etsi.org/ngsi-ld/hasValue": "flush",
    "index": 0
}
EOF
cat << EOF | tr -d '\n' > ${ATTRIBUTE3}
{
    "id": "${CUTTER_ID}\\\https://industry-fusion.com/types/v0.9/state2",
    "entityId": "${CUTTER_ID}",
    "name": "https://industry-fusion.com/types/v0.9/state2",
    "type": "https://uri.etsi.org/ngsi-ld/Property",
    "https://uri.etsi.org/ngsi-ld/hasValue": "ON",
    "index": 0
}
EOF
cat << EOF | tr -d '\n' > ${ATTRIBUTE4}
{
    "id": "${CUTTER_ID}\\\https://industry-fusion.com/types/v0.9/hasWorkpiece",
    "entityId": "${CUTTER_ID}",
    "name": "https://industry-fusion.com/types/v0.9/hasWorkpiece",
    "type": "https://uri.etsi.org/ngsi-ld/Relationship",
    "nodeType": "@id",
    "https://uri.etsi.org/ngsi-ld/hasObject": "urn:workpiece:1",
    "index": 0
}
EOF
cat << EOF | tr -d '\n' > ${ATTRIBUTE5}
{
    "id": "${CUTTER_ID}\\\https://industry-fusion.com/types/v0.9/refState",
    "entityId": "${CUTTER_ID}",
    "name": "https://industry-fusion.com/types/v0.9/refState",
    "type": "https://uri.etsi.org/ngsi-ld/Property",
    "https://uri.etsi.org/ngsi-ld/hasValue": "https://industry-fusion.com/v0.9/refStateIRI",
    "nodeType": "@id",
    "index": 0
}
EOF

compare_attributes1() {
    cat << EOF | diff "$1" - >&3
{"op":"update","overwriteOrReplace":true,"entities":"[{\"id\": \"${CUTTER_ID}\",\"https://industry-fusion.com/types/v0.9/state\":[{\"type\": \"https://uri.etsi.org/ngsi-ld/Property\", \"value\": \"ON\"}]}]"}
EOF
}
compare_attributes2() {
    cat << EOF | diff "$1" - >&3
{"op":"update","overwriteOrReplace":true,"entities":"[{\"id\": \"${CUTTER_ID}\",\"https://industry-fusion.com/types/v0.9/state\":[{\"type\": \"https://uri.etsi.org/ngsi-ld/Property\", \"value\": \"OFF\"}]}]"}
EOF
}
compare_attributes3() {
    cat << EOF | diff "$1" - >&3
{
  "op": "update",
  "overwriteOrReplace": true
}
EOF
    cat << EOF | jq -S | diff "$2" - >&3
[
  {
    "id": "urn:plasmacutter-test:12345",
    "https://industry-fusion.com/types/v0.9/state": [{
      "type": "https://uri.etsi.org/ngsi-ld/Property",
      "value": "OFF"
    }],
    "https://industry-fusion.com/types/v0.9/state2": [{
      "type": "https://uri.etsi.org/ngsi-ld/Property",
      "value": "ON"
    }]
  }
]
EOF
}

compare_attributes4() {
    cat << EOF | diff "$1" - >&3
{"op":"update","overwriteOrReplace":true,"entities":"[{\"id\": \"${CUTTER_ID}\",\"https://industry-fusion.com/types/v0.9/hasWorkpiece\":[{\"type\": \"https://uri.etsi.org/ngsi-ld/Relationship\", \"object\": \"urn:workpiece:1\"}]}]"}
EOF
}

compare_attributes5() {
    cat << EOF | diff "$1" - >&3
{"op":"update","overwriteOrReplace":true,"entities":"[{\"id\": \"${CUTTER_ID}\",\"https://industry-fusion.com/types/v0.9/refState\":[{\"type\": \"https://uri.etsi.org/ngsi-ld/Property\", \"value\": {\"@id\": \"https://industry-fusion.com/v0.9/refStateIRI\"}}]}]"}
EOF
}

setup() {
    # shellcheck disable=SC2086
    (exec ${SUDO} kubefwd -n iff -l app.kubernetes.io/name=kafka svc  >/dev/null 2>&1) &
    echo "# launched kubefwd for kafka, wait some seconds to give kubefwd to launch the services"
    sleep 2
}
teardown(){
    echo "# now killing kubefwd"
    # shellcheck disable=SC2086
    ${SUDO} killall kubefwd
}


@test "verify attribute is forwarded to ngsild-update bridge" {
    skip
    (exec stdbuf -oL kafkacat -C -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP} -o end >${KAFKACAT_ATTRIBUTES}) &
    sleep 2 # wait for next aggregation window
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${ATTRIBUTE1}
    echo "# Sent attribute to attribute topic, wait some time for aggregation"
    sleep 2 # wait until current window is over and send trigger
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${FLUSH_ATTRIBUTE}
    sleep 1
    killall kafkacat
    grep -v flush > ${KAFKACAT_ATTRIBUTES_FILTERED} < ${KAFKACAT_ATTRIBUTES}
    run compare_attributes1 ${KAFKACAT_ATTRIBUTES_FILTERED}
    [ "$status" -eq 0 ]
}
@test "verify last of 2 same attributes is forwarded to ngsild-update bridge" {
    skip
    (exec stdbuf -oL kafkacat -C -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP} -o end >${KAFKACAT_ATTRIBUTES}) &
    sleep 2 # wait for next aggregation window
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${ATTRIBUTE1}
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${ATTRIBUTE2}
    echo "# Sent attribute to attribute topic, wait some time for aggregation"
    sleep 2 # wait until current window is over and send trigger
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${FLUSH_ATTRIBUTE}
    sleep 1
    killall kafkacat
    grep -v flush > ${KAFKACAT_ATTRIBUTES_FILTERED} < ${KAFKACAT_ATTRIBUTES}
    run compare_attributes2 ${KAFKACAT_ATTRIBUTES_FILTERED}
    [ "$status" -eq 0 ]
}
@test "verify last of 2 same attributes and 1 other attribute are jointly forwarded to ngsild-update bridge" {
    skip
    (exec stdbuf -oL kafkacat -C -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP} -o end >${KAFKACAT_ATTRIBUTES}) &
    sleep 2 # wait for next aggregation window
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${ATTRIBUTE1}
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${ATTRIBUTE3}
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${ATTRIBUTE2}
    echo "# Sent attribute to attribute topic, wait some time for aggregation"
    sleep 2 # wait until current window is over and send trigger
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${FLUSH_ATTRIBUTE}
    sleep 1
    killall kafkacat
    grep -v flush < ${KAFKACAT_ATTRIBUTES} | jq -S 'del (.entities)'> ${KAFKACAT_ATTRIBUTES_FILTERED}
    grep -v flush < ${KAFKACAT_ATTRIBUTES} | jq -S '.entities | fromjson'> ${KAFKACAT_ATTRIBUTES_FROMJSON} 
    run compare_attributes3 ${KAFKACAT_ATTRIBUTES_FILTERED} ${KAFKACAT_ATTRIBUTES_FROMJSON}
    [ "$status" -eq 0 ]
}
@test "verify attribute is forwarded to ngsild-update bridge as relationship" {
    skip
    (exec stdbuf -oL kafkacat -C -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP} -o end >${KAFKACAT_ATTRIBUTES}) &
    sleep 2 # wait for next aggregation window
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${ATTRIBUTE4}
    echo "# Sent attribute to attribute topic, wait some time for aggregation"
    sleep 2 # wait until current window is over and send trigger
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${FLUSH_ATTRIBUTE}
    sleep 1
    killall kafkacat
    grep -v flush > ${KAFKACAT_ATTRIBUTES_FILTERED} < ${KAFKACAT_ATTRIBUTES}
    run compare_attributes4 ${KAFKACAT_ATTRIBUTES_FILTERED}
    [ "$status" -eq 0 ]
}
@test "verify attribute is forwarded to ngsild-update bridge as iri" {
    (exec stdbuf -oL kafkacat -C -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP} -o end >${KAFKACAT_ATTRIBUTES}) &
    sleep 2 # wait for next aggregation window
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${ATTRIBUTE5}
    echo "# Sent attribute to attribute topic, wait some time for aggregation"
    sleep 2 # wait until current window is over and send trigger
    kafkacat -P -t ${ATTRIBUTES_TOPIC} -b ${KAFKA_BOOTSTRAP} <${FLUSH_ATTRIBUTE}
    sleep 1
    killall kafkacat
    grep -v flush > ${KAFKACAT_ATTRIBUTES_FILTERED} < ${KAFKACAT_ATTRIBUTES}
    run compare_attributes5 ${KAFKACAT_ATTRIBUTES_FILTERED}
    [ "$status" -eq 0 ]
}
