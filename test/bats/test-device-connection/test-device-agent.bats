# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

load "../lib/utils"
load "../lib/detik"
# shellcheck disable=SC2034 # these variables are used by detik
DETIK_CLIENT_NAME="kubectl"
# shellcheck disable=SC2034
DETIK_CLIENT_NAMESPACE="iff"
# shellcheck disable=SC2034
DETIK_DEBUG="true"

DEBUG=${DEBUG:-false}
SKIP=skip
NAMESPACE=iff
USER_SECRET=secret/credential-iff-realm-user-iff
USER=realm_user
REALM_ID=iff
KEYCLOAK_URL="http://keycloak.local/auth/realms"
TEST_DIR="$(dirname $BATS_TEST_FILENAME)"
DEVICE_CLIENT_ID="device"
CLIENT_ID=scorpio
GATEWAY_ID="testgateway"
GATEWAY_ID2="testgateway2"
DEVICE_ID="urn:iff:testdevice:1"
DEVICE_FILE="device.json"
DEVICES_NAMESPACE=devices
ONBOARDING_TOKEN="onboard-token.json"
NGSILD_AGENT_DIR=${TEST_DIR}/../../../NgsildAgent
DEVICE_ID2="testdevice2"
DEVICE_TOKEN_SCOPE="device_id gateway mqtt-broker offline_access"
DEVICE_TOKEN_AUDIENCE_FROM_EXCHANGE='["device","mqtt-broker","oisp-frontend"]'
DEVICE_TOKEN_AUDIENCE_FROM_DIRECT='mqtt-broker'
MQTT_URL=emqx-listeners:1883
MQTT_TOPIC_NAME="spBv1.0/${NAMESPACE}/DDATA/${GATEWAY_ID}/${DEVICE_ID}"
MQTT_MESSAGE='{"timestamp":1655974018778,"metrics":[{ "name":"Property/https://industry-fusion.com/types/v0.9/state","timestamp":1655974018777,"dataType":"string","value":"https://industry-fusion.com/types/v0.9/state_OFF"}],"seq":1}'
KAFKA_BOOTSTRAP=my-cluster-kafka-bootstrap:9092
KAFKACAT_ATTRIBUTES=/tmp/KAFKACAT_ATTRIBUTES
KAFKACAT_ATTRIBUTES_TOPIC=iff.ngsild.attributes
MQTT_SUB=/tmp/MQTT_SUB
MQTT_RESULT=/tmp/MQTT_RES
SECRET_FILENAME=/tmp/SECRET
AGENT_CONFIG1=/tmp/AGENT_CONFIG1
AGENT_CONFIG2=/tmp/AGENT_CONFIG2
PROPERTY1="http://example.com/property1"
PROPERTY2="http://example.com/property2"
PGREST_URL="http://pgrest.local/entityhistory"
PGREST_RESULT=/tmp/PGREST_RESULT
EMQX_INGRESS=$(kubectl -n ${NAMESPACE} get svc/emqx-listeners -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
MQTT_BRIDGE_DEPLOYMENT="deployment/mqtt-bridge"


cat << EOF > ${AGENT_CONFIG1}
{
        "data_directory": "./data",
        "listeners": {
                "udp_port": 41234,
                "tcp_port": 7070
        },
        "logger": {
                "level": "info",
                "path": "/tmp/",
                "max_size": 134217728
        },
        "dbManager": {
                "file": "metrics.db",
                "retentionInSeconds": 3600,
                "housekeepingIntervalInSeconds": 60,
                "enabled": false
        },
        "connector": {
                "mqtt": {
                        "host": "${EMQX_INGRESS}",
                        "port": 1883,
                        "websockets": false,
                        "qos": 1,
                        "retain": false,
                        "secure": false,
                        "retries": 5,
                        "strictSSL": false,
                        "sparkplugB": true,
                        "version": "spBv1.0"          
                }
        }
}
EOF


cat << EOF > ${AGENT_CONFIG2}
{
        "data_directory": "./data",
        "listeners": {
                "udp_port": 41234,
                "tcp_port": 7070
        },
        "logger": {
                "level": "info",
                "path": "/tmp/",
                "max_size": 134217728
        },
        "dbManager": {
                "file": "metrics.db",
                "retentionInSeconds": 3600,
                "housekeepingIntervalInSeconds": 600,
                "enabled": true
        },
        "connector": {
                "mqtt": {
                        "host": "${EMQX_INGRESS}",
                        "port": 1883,
                        "websockets": false,
                        "qos": 1,
                        "retain": false,
                        "secure": false,
                        "retries": 5,
                        "strictSSL": false,
                        "sparkplugB": true,
                        "version": "spBv1.0"          
                }
        }
}
EOF

check_device_file_contains() {
    deviceid=$(jq '.device_id' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    gatewayid=$(jq '.gateway_id' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    realmid=$(jq '.realm_id' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    keycloakurl=$(jq '.keycloak_url' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    [ $deviceid = $1 ] && [ $gatewayid = $2 ] && [ $realmid = $3 ] && [ $keycloakurl = $4 ]
}


init_device_file() {
    (cd ${NGSILD_AGENT_DIR}/data && pwd && rm -f ${DEVICE_FILE})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./init-device.sh "${DEVICE_ID}" "${GATEWAY_ID}")
}

get_password() {
    kubectl -n ${NAMESPACE} get ${USER_SECRET} -o jsonpath='{.data.password}' | base64 -d
}


check_onboarding_token() {
    access_token=$(jq '.access_token' ${NGSILD_AGENT_DIR}/data/${ONBOARDING_TOKEN} | tr -d '"')
    access_exp=$(echo $access_token | tr -d '"' | jq -R 'split(".") | .[1] | @base64d | fromjson| .exp' )
    cur_time=$(date +%s)
    [ $access_exp -gt $cur_time ]
}

check_device_file_token() {
    device_token=$(jq '.device_token' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    device_exp=$(echo $device_token | tr -d '"' | jq -R 'split(".") | .[1] | @base64d | fromjson| .exp' )
    cur_time=$(date +%s)
    [ $device_exp -gt $cur_time ]
}

get_token() {
        curl -XPOST  -d "client_id=${CLIENT_ID}" \
         -d "username=${USER}" \
         -d "password=$1" \
         -d 'grant_type=password' \
         "${KEYCLOAK_URL}/${NAMESPACE}/protocol/openid-connect/token" | jq ".access_token"| tr -d '"'
}

get_tsdb_samples() {
    entityId=$1
    limit=$2
    token=$3
    curl  -H "Authorization: Bearer $token" "${PGREST_URL}?limit=${limit}&order=observedAt.desc,attributeId.asc&entityId=eq.${entityId}" 2>/dev/null | jq -S 'map(del(.modifiedAt, .observedAt))'
}

# compare entity with reference
# $1: file to compare with
compare_pgrest_result1() {
    cat << EOF | jq | diff "$1" - >&3
[
  {
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "0",
    "valueType": null
  }
]
EOF
}

# compare entity with reference
# $1: file to compare with
compare_pgrest_result2() {
    cat << EOF | jq | diff "$1" - >&3
[
  {
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "1",
    "valueType": null
  },
  {
    "attributeId": "http://example.com/property2",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property2",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "2",
    "valueType": null
  }
]
EOF
}

compare_pgrest_result3() {
    cat << EOF | jq | diff "$1" - >&3
[
  {
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "5",
    "valueType": null
  },
  {
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "3",
    "valueType": null
  },
  {
    "attributeId": "http://example.com/property2",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property2",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "4",
    "valueType": null
  }
]
EOF
}


compare_pgrest_result4() {
    echo hello
    cat << EOF | jq | diff "$1" - >&3
[
  {
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "8",
    "valueType": null
  },

  { 
    "attributeId": "http://example.com/property2",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property2",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "9",
    "valueType": null
  },
  { 
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "6",
    "valueType": null
  },
  { 
    "attributeId": "http://example.com/property2",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property2",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "7",
    "valueType": null
  },
  {
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "4",
    "valueType": null
  },
  {
    "attributeId": "http://example.com/property2",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property2",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "5",
    "valueType": null
  }
]
EOF
}


compare_pgrest_result4() {
    echo hello
    cat << EOF | jq | diff "$1" - >&3
[
  {
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "12",
    "valueType": null
  },
  {
    "attributeId": "http://example.com/property1",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property1",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "10",
    "valueType": null
  },
  {
    "attributeId": "http://example.com/property2",
    "attributeType": "https://uri.etsi.org/ngsi-ld/Property",
    "datasetId": "urn:iff:testdevice:1\\\\http://example.com/property2",
    "entityId": "urn:iff:testdevice:1",
    "index": 0,
    "nodeType": "@value",
    "value": "11",
    "valueType": null
  }
]
EOF
}

setup() {
    # shellcheck disable=SC2086
    if [ "$DEBUG" != "true" ]; then
        echo "This test works only in debug mode. Set DEBUG=true."
        exit 1
    fi
}


@test "test init_device.sh" {
    $SKIP
    (cd ${NGSILD_AGENT_DIR}/data && pwd && rm -f ${DEVICE_FILE})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./init-device.sh ${DEVICE_ID} ${GATEWAY_ID})
    run check_device_file_contains ${DEVICE_ID} ${GATEWAY_ID} ${REALM_ID} ${KEYCLOAK_URL}
    [ "${status}" -eq "0" ]    
}

@test "test init_device.sh with deviceid no URN" {
    $SKIP
    (cd ${NGSILD_AGENT_DIR}/data && pwd && rm -f ${DEVICE_FILE})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./init-device.sh ${DEVICE_ID2} ${GATEWAY_ID} || echo "failed as expected")
    run [ ! -f ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} ]
    [ "${status}" -eq "0" ]    
}

@test "test get-onboarding-token.sh" {
    $SKIP
    init_device_file
    password=$(get_password)
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password ${USER})
    run check_onboarding_token
    [ "${status}" -eq "0" ]
}

@test "test basic activation" {
    $SKIP
    init_device_file
    password=$(get_password)
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password ${USER})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./activate.sh -f)
    run check_device_file_token
    [ "${status}" -eq "0" ]
}

@test "test activation though k8s" {
    $SKIP
    init_device_file
    password=$(get_password)
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password -s ${SECRET_FILENAME} ${USER})
    kubectl apply -f ${SECRET_FILENAME}
    (cd ${NGSILD_AGENT_DIR}/util && bash ./activate.sh -s)
    run check_device_file_token
    [ "${status}" -eq "0" ]
}

@test "test agent starting up and sending data" {
    $SKIP
    init_device_file
    password=$(get_password)
    token=$(get_token "$password")
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password ${USER})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./activate.sh -f)
    cp ${AGENT_CONFIG1} ${NGSILD_AGENT_DIR}/config/config.json
    (cd ${NGSILD_AGENT_DIR} && exec stdbuf -oL node ./iff-agent.js) &
    sleep 2
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh "${PROPERTY1}" 0 )
    sleep 2
    pkill -f iff-agent
    get_tsdb_samples "${DEVICE_ID}" 1 "${token}" > ${PGREST_RESULT}
    run compare_pgrest_result1 ${PGREST_RESULT}
    [ "${status}" -eq "0" ]
}

@test "test agent starting up and sending data array" {
    $SKIP
    init_device_file
    password=$(get_password)
    token=$(get_token "$password")
    echo $token Marcel $password
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password ${USER})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./activate.sh -f)
    cp ${AGENT_CONFIG1} ${NGSILD_AGENT_DIR}/config/config.json
    (cd ${NGSILD_AGENT_DIR} && exec stdbuf -oL node ./iff-agent.js) &
    sleep 2
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -a "${PROPERTY1}" 1 "${PROPERTY2}" 2 )
    sleep 2
    pkill -f iff-agent
    get_tsdb_samples "${DEVICE_ID}" 2 "${token}" > ${PGREST_RESULT}
    run compare_pgrest_result2 ${PGREST_RESULT}
    [ "${status}" -eq "0" ]
}

@test "sending data over tcp" {
    $SKIP
    init_device_file
    password=$(get_password)
    token=$(get_token "$password")
    echo $token Marcel $password
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password ${USER})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./activate.sh -f)
    cp ${AGENT_CONFIG1} ${NGSILD_AGENT_DIR}/config/config.json
    (cd ${NGSILD_AGENT_DIR} && exec stdbuf -oL node ./iff-agent.js) &
    sleep 2
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -at "${PROPERTY1}" 3 "${PROPERTY2}" 4 )
    sleep 1
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -t "${PROPERTY1}" 5 )
    sleep 1
    pkill -f iff-agent
    get_tsdb_samples "${DEVICE_ID}" 3 "${token}" > ${PGREST_RESULT}
    run compare_pgrest_result3 ${PGREST_RESULT}
    [ "${status}" -eq "0" ]
}

@test "sending data without utils directly to TCP/UDP API" {
    $SKIP
    init_device_file
    password=$(get_password)
    token=$(get_token "$password")
    echo $token Marcel $password
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password ${USER})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./activate.sh -f)
    cp ${AGENT_CONFIG1} ${NGSILD_AGENT_DIR}/config/config.json
    (cd ${NGSILD_AGENT_DIR} && exec stdbuf -oL node ./iff-agent.js) &
    sleep 2
    echo -n '[{"n": "'$PROPERTY1'", "v": "4"},{"n": "'$PROPERTY2'", "v": "5"}]' >/dev/tcp/127.0.0.1/7070
    sleep 1
    echo -n '[{"n": "'$PROPERTY1'", "v": "6"},{"n": "'$PROPERTY2'", "v": "7"}]' >/dev/udp/127.0.0.1/41234
    sleep 1
    echo -n '{"n": "'$PROPERTY1'", "v": "8"}' >/dev/tcp/127.0.0.1/7070
    echo '{"n": "'$PROPERTY2'", "v": "9"}' >/dev/udp/127.0.0.1/41234
    sleep 1
    pkill -f iff-agent
    get_tsdb_samples "${DEVICE_ID}" 6 "${token}" > ${PGREST_RESULT}
    run compare_pgrest_result4 ${PGREST_RESULT}
    [ "${status}" -eq "0" ]
}

@test "Test agent reconnects" {
    $SKIP
    init_device_file
    password=$(get_password)
    token=$(get_token "$password")
    echo $token Marcel $password
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password ${USER})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./activate.sh -f)
    cp ${AGENT_CONFIG1} ${NGSILD_AGENT_DIR}/config/config.json
    (cd ${NGSILD_AGENT_DIR} && exec stdbuf -oL node ./iff-agent.js) &
    sleep 2
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -at "${PROPERTY1}" 10 "${PROPERTY2}" 11 )
    sleep 1
    kubectl -n${NAMESPACE} -l apps.emqx.io/instance=emqx delete pod
    run try "at most 30 times every 5s to find 1 pod named 'emqx-core' with 'status.containerStatuses[0].ready' being 'true'"
    [ "${status}" -eq "0" ]
    sleep 15 # give mqtt-bridge time to settle
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -t "${PROPERTY1}" 12 )
    sleep 1
    pkill -f iff-agent
    get_tsdb_samples "${DEVICE_ID}" 3 "${token}" > ${PGREST_RESULT}
    run compare_pgrest_result4 ${PGREST_RESULT}
    [ "${status}" -eq "0" ]
}

@test "Test agent reconnects with offline storage" {
    #$SKIP
    init_device_file
    password=$(get_password)
    token=$(get_token "$password")
    echo $token Marcel $password
    (cd ${NGSILD_AGENT_DIR}/util && bash ./get-onboarding-token.sh -p $password ${USER})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./activate.sh -f)
    cp ${AGENT_CONFIG2} ${NGSILD_AGENT_DIR}/config/config.json
    (cd ${NGSILD_AGENT_DIR} && exec stdbuf -oL node ./iff-agent.js) &
    sleep 2
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -at "${PROPERTY1}" 13 "${PROPERTY2}" 14 )
    sleep 1
    kubectl -n${NAMESPACE} -l apps.emqx.io/instance=emqx delete pod
    sleep 2
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -at "${PROPERTY1}" 15 "${PROPERTY2}" 16)
    sleep 1
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -t "${PROPERTY1}" 17 )
    sleep 1
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -t "${PROPERTY1}" 18 )
    run try "at most 30 times every 5s to find 1 pod named 'emqx-core' with 'status.containerStatuses[0].ready' being 'true'"
    [ "${status}" -eq "0" ]
    sleep 15
    (cd ${NGSILD_AGENT_DIR}/util && bash ./send_data.sh -t "${PROPERTY1}" 19 )
    sleep 1
    pkill -f iff-agent
    get_tsdb_samples "${DEVICE_ID}" 3 "${token}" > ${PGREST_RESULT}
    run compare_pgrest_result4 ${PGREST_RESULT}
    [ "${status}" -eq "0" ]
}