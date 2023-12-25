#!/usr/bin/env bats
# shellcheck disable=SC2005
# if [ -z "${SELF_HOSTED_RUNNER}" ]; then
#    SUDO="sudo -E"
# fi

DEBUG=${DEBUG:-false}
SKIP=
NAMESPACE=iff
USER_SECRET=secret/credential-iff-realm-user-iff
USER=realm_user
REALM_ID=iff
KEYCLOAK_URL="http://keycloak.local/auth/realms/iff"
TEST_DIR="$(dirname $BATS_TEST_FILENAME)"
DEVICE_CLIENT_ID="device"
GATEWAY_ID="testgateway"
GATEWAY_ID2="testgateway2"
DEVICE_ID="urn:iff:testdevice:1"
DEVICE_FILE="device.json"
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
TAINTED='TAINTED'
onboarding_token=


check_device_file_contains() {
    deviceid=$(jq '.device_id' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    gatewayid=$(jq '.gateway_id' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    realmid=$(jq '.realm_id' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    keycloakurl=$(jq '.keycloak_url' ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} | tr -d '"')
    [ $deviceid = $1 ] && [ $gatewayid = $2 ] && [ $realmid = $3 ] && [ $keycloakurl = $4 ]
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
    #$SKIP
    (cd ${NGSILD_AGENT_DIR}/data && pwd && rm -f ${DEVICE_FILE})
    (cd ${NGSILD_AGENT_DIR}/util && bash ./init-device.sh ${DEVICE_ID2} ${GATEWAY_ID} || echo "failed as expected")
    run [ ! -f ${NGSILD_AGENT_DIR}/data/${DEVICE_FILE} ]
    [ "${status}" -eq "0" ]    
}