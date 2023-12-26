#!/usr/bin/env bats
# shellcheck disable=SC2005
# if [ -z "${SELF_HOSTED_RUNNER}" ]; then
#    SUDO="sudo -E"
# fi

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
PROPERTY1="http://example.com/property1"
PGREST_URL="http://pgrest.local/entityhistory"
PGREST_RESULT=/tmp/PGREST_RESULT



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
                        "host": "emqx-listeners",
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
    curl  -H "Authorization: Bearer $token" "${PGREST_URL}?limit=${limit}&order=observedAt.desc&entityId=eq.${entityId}" 2>/dev/null | jq -S 'map(del(.modifiedAt, .observedAt))'
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
    #$SKIP
    init_device_file
    password=$(get_password)
    token=$(get_token "$password")
    echo $token Marcel $password
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
    #false
    [ "${status}" -eq "0" ]
}