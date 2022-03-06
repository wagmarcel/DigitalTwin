#!/usr/bin/env bats

NAMESPACE=iff
USERSECRET=secret/credential-iff-realm-user-iff
USER=realm_user
CLIENT_ID=scorpio
KEYCLOAKURL=http://keycloak.local/auth/realms
UPSERT_FILTER=/tmp/UPSERT_FILTER
UPSERT_FILTER_OVERWRITE=/tmp/UPSERT_FILTER_OVERWRITE
UPSERT_FILTER_NON_OVERWRITE=/tmp/UPSERT_FILTER_NON_OVERWRITE
UPDATE_FILTER=/tmp/UPDATE_FILTER
UPDATE_FILTER_NO_OVERWRITE=/tmp/UPDATE_FILTER_NO_OVERWRITE
KAFKA_BOOTSTRAP=my-cluster-kafka-bootstrap:9092
KAFKACAT_NGSILD_UPDATES_TOPIC=iff.ngsildUpdates
FILTER_ID=urn:filter:1
RECEIVED_ENTITY=/tmp/RECEIVED_ENTITY

cat << EOF | tr -d '\n' > ${UPSERT_FILTER}
{
    "op": "upsert",
    "overwriteOrReplace": "false",
    "entities": [
        {
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
        "id": "${FILTER_ID}",
        "type": "https://industry-fusion.com/types/v0.9/filter",
        "https://industry-fusion.com/types/v0.9/state": {
          "type": "Property",
          "value": "OFFF"
        },
        "https://industry-fusion.com/types/v0.9/strength": {
          "type": "Property",
          "value": "0.9"
        },
        "https://industry-fusion.com/types/v0.9/hasCartridge": {
          "type": "Relationship",
          "object": "urn:filterCartridge:1"
        }
      }
    ]
}
EOF

cat << EOF | tr -d '\n' > ${UPSERT_FILTER_OVERWRITE}
{
    "op": "upsert",
    "overwriteOrReplace": "true",
    "entities": [
        {
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
        "id": "${FILTER_ID}",
        "type": "https://industry-fusion.com/types/v0.9/filter",
        "https://industry-fusion.com/types/v0.9/state": {
          "type": "Property",
          "value": "OFF"
        },
        "https://industry-fusion.com/types/v0.9/strength": {
          "type": "Property",
          "value": "0.1"
        },
        "https://industry-fusion.com/types/v0.9/strength2": {
          "type": "Property",
          "value": "0.1"
        },
        "https://industry-fusion.com/types/v0.9/hasCartridge": {
          "type": "Relationship",
          "object": "urn:filterCartridge:2"
        }
      }
    ]
}
EOF

cat << EOF | tr -d '\n' > ${UPSERT_FILTER_NON_OVERWRITE}
{
    "op": "upsert",
    "overwriteOrReplace": false,
    "entities": [
        {
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
        "id": "${FILTER_ID}",
        "type": "https://industry-fusion.com/types/v0.9/filter",
        "https://industry-fusion.com/types/v0.9/state": {
          "type": "Property",
          "value": "OFF"
        },
        "https://industry-fusion.com/types/v0.9/strength": {
          "type": "Property",
          "value": "0.1"
        },
        "https://industry-fusion.com/types/v0.9/strength2": {
          "type": "Property",
          "value": "0.5"
        },
        "https://industry-fusion.com/types/v0.9/hasCartridge": {
          "type": "Relationship",
          "object": "urn:filterCartridge:2"
        }
      }
    ]
}
EOF

cat << EOF | tr -d '\n' > ${UPDATE_FILTER}
{
    "op": "update",
    "overwriteOrReplace": "true",
    "entities": [
        {
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
        "id": "${FILTER_ID}",
        "type": "https://industry-fusion.com/types/v0.9/filter",
        "https://industry-fusion.com/types/v0.9/state": {
          "type": "Property",
          "value": "OFF"
        },
        "https://industry-fusion.com/types/v0.9/strength": {
          "type": "Property",
          "value": "0.5"
        },
        "https://industry-fusion.com/types/v0.9/hasCartridge": {
          "type": "Relationship",
          "object": "urn:filterCartridge:2"
        }
      }
    ]
}
EOF

cat << EOF | tr -d '\n' > ${UPDATE_FILTER_NO_OVERWRITE}
{
    "op": "update",
    "overwriteOrReplace": false,
    "entities": [
        {
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
        "id": "${FILTER_ID}",
        "type": "https://industry-fusion.com/types/v0.9/filter",
        "https://industry-fusion.com/types/v0.9/state": {
          "type": "Property",
          "value": "ON"
        },
        "https://industry-fusion.com/types/v0.9/strength": {
          "type": "Property",
          "value": "0.75"
        },
        "https://industry-fusion.com/types/v0.9/strength2": {
          "type": "Property",
          "value": "1.0"
        },
        "https://industry-fusion.com/types/v0.9/hasCartridge": {
          "type": "Relationship",
          "object": "urn:filterCartridge:7"
        }
      }
    ]
}
EOF

# compare entity with reference
# $1: file to compare with
compare_inserted_entity() {
    cat << EOF | jq | diff $1 - >&3
{
  "id" : "urn:filter:1",
  "type" : "https://industry-fusion.com/types/v0.9/filter",
  "https://industry-fusion.com/types/v0.9/hasCartridge" : {
    "type" : "Relationship",
    "object" : "urn:filterCartridge:1"
  },
  "https://industry-fusion.com/types/v0.9/state" : {
    "type" : "Property",
    "value" : "OFFF"
  },
  "https://industry-fusion.com/types/v0.9/strength" : {
    "type" : "Property",
    "value" : "0.9"
  },
  "@context" : [ "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld" ]
}
EOF
}

# compare entity with reference
# $1: file to compare with
compare_upserted_overwritten_entity() {
    cat << EOF | jq | diff $1 - >&3
{
  "id" : "urn:filter:1",
  "type" : "https://industry-fusion.com/types/v0.9/filter",
  "https://industry-fusion.com/types/v0.9/hasCartridge" : {
    "type" : "Relationship",
    "object" : "urn:filterCartridge:2"
  },
  "https://industry-fusion.com/types/v0.9/state" : {
    "type" : "Property",
    "value" : "OFF"
  },
  "https://industry-fusion.com/types/v0.9/strength" : {
    "type" : "Property",
    "value" : "0.1"
  },
  "https://industry-fusion.com/types/v0.9/strength2": {
    "type": "Property",
    "value": "0.1"
  },
  "@context" : [ "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld" ]
}
EOF
}

# compare entity with reference
# $1: file to compare with
compare_upserted_non_overwritten_entity() {
    cat << EOF | jq | diff $1 - >&3
{
  "id" : "urn:filter:1",
  "type" : "https://industry-fusion.com/types/v0.9/filter",
  "https://industry-fusion.com/types/v0.9/hasCartridge" : {
    "type" : "Relationship",
    "object" : "urn:filterCartridge:2"
  },
  "https://industry-fusion.com/types/v0.9/state" : {
    "type" : "Property",
    "value" : "OFF"
  },
  "https://industry-fusion.com/types/v0.9/strength" : {
    "type" : "Property",
    "value" : "0.1"
  },
  "https://industry-fusion.com/types/v0.9/strength2": {
    "type": "Property",
    "value": "0.5"
  },
  "@context" : [ "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld" ]
}
EOF
}

# compare entity with reference
# $1: file to compare with
compare_updated_entity() {
    cat << EOF | jq | diff $1 - >&3
{
  "id" : "urn:filter:1",
  "type" : "https://industry-fusion.com/types/v0.9/filter",
  "https://industry-fusion.com/types/v0.9/hasCartridge" : {
    "type" : "Relationship",
    "object" : "urn:filterCartridge:2"
  },
  "https://industry-fusion.com/types/v0.9/state" : {
    "type" : "Property",
    "value" : "OFF"
  },
  "https://industry-fusion.com/types/v0.9/strength" : {
    "type" : "Property",
    "value" : "0.5"
  },
  "@context" : [ "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld" ]
}
EOF
}


# compare entity with reference
# $1: file to compare with
compare_updated_no_overwrite_entity() {
    cat << EOF | jq | diff $1 - >&3
{
  "id" : "urn:filter:1",
  "type" : "https://industry-fusion.com/types/v0.9/filter",
  "https://industry-fusion.com/types/v0.9/hasCartridge" : {
    "type" : "Relationship",
    "object" : "urn:filterCartridge:1"
  },
  "https://industry-fusion.com/types/v0.9/state" : {
    "type" : "Property",
    "value" : "OFFF"
  },
  "https://industry-fusion.com/types/v0.9/strength" : {
    "type" : "Property",
    "value" : "0.9"
  },
  "https://industry-fusion.com/types/v0.9/strength2" : {
    "type" : "Property",
    "value" : "1.0"
  },
  "@context" : [ "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld" ]
}
EOF
}

get_password() {
    kubectl -n ${NAMESPACE} get ${USERSECRET} -o jsonpath='{.data.password}'| base64 -d
}
get_token() {
    curl -d "client_id=${CLIENT_ID}" -d "username=${USER}" -d "password=$password" -d 'grant_type=password' "${KEYCLOAKURL}/${NAMESPACE}/protocol/openid-connect/token"| jq ".access_token"| tr -d '"' 2>/dev/null
}

# get ngsild entity
# $1: auth token
# $2: id of entity
get_ngsild() {
    curl -vv -X GET -H "Authorization: Bearer $1" http://ngsild.local/ngsi-ld/v1/entities/$2 -H "Content-Type: application/ld+json" 2>/dev/null
}

# deletes ngsild entity
# $1: auth token
# $2: id of entity to delete
delete_ngsild() {
    curl -vv -X DELETE -H "Authorization: Bearer $1" http://ngsild.local/ngsi-ld/v1/entities/$2 -H "Content-Type: application/ld+json" 2>/dev/null
}

setup() {
    (exec sudo -E kubefwd -n iff -l app.kubernetes.io/name=kafka svc 2>&1 >/dev/null) &
    echo "# launched kubefwd for kafka, wait some seconds to give kubefwd to launch the services"
    sleep 2
}
teardown(){
    echo "# now killing kubefwd"
    sudo killall kubefwd
}


@test "verify ngsild-update bridge is inserting ngsi-ld entitiy" {

    cat ${UPSERT_FILTER}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    echo "# Sent upsert object to ngsi-ld-updates-bridge, wait some time to let it settle"
    sleep 2
    password=$(get_password)
    token=$(get_token)
    get_ngsild ${token} ${FILTER_ID} | jq >${RECEIVED_ENTITY}
    delete_ngsild ${token} ${FILTER_ID}
    run compare_inserted_entity ${RECEIVED_ENTITY}
    [ "$status" -eq 0 ]
}

@test "verify ngsild-update bridge is upserting and overwriting ngsi-ld entitiy" {
    cat ${UPSERT_FILTER}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    echo "# Sent upsert object to ngsi-ld-updates-bridge, wait some time to let it settle"
    sleep 2
    password=$(get_password)
    token=$(get_token)
    get_ngsild ${token} ${FILTER_ID} | jq >${RECEIVED_ENTITY}
    run compare_inserted_entity ${RECEIVED_ENTITY}
    [ "$status" -eq 0 ]
    cat ${UPSERT_FILTER_OVERWRITE}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    sleep 2
    get_ngsild ${token} ${FILTER_ID} | jq >${RECEIVED_ENTITY}
    run compare_upserted_overwritten_entity ${RECEIVED_ENTITY}
    [ "$status" -eq 0 ]
    delete_ngsild ${token} ${FILTER_ID}
}

@test "verify ngsild-update bridge is upserting and non-overwriting ngsi-ld entitiy" {
    # This test is not working properlty the entityOperations/upsert?options=update should only update existing
    # property not create new ones
    cat ${UPSERT_FILTER}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    echo "# Sent upsert object to ngsi-ld-updates-bridge, wait some time to let it settle"
    sleep 2
    password=$(get_password)
    token=$(get_token)
    get_ngsild ${token} ${FILTER_ID} | jq >${RECEIVED_ENTITY}
    run compare_inserted_entity ${RECEIVED_ENTITY}
    [ "$status" -eq 0 ]
    cat ${UPSERT_FILTER_NON_OVERWRITE}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    sleep 2
    get_ngsild ${token} ${FILTER_ID} | jq >${RECEIVED_ENTITY}
    run compare_upserted_non_overwritten_entity ${RECEIVED_ENTITY}
    [ "$status" -eq 0 ]
    delete_ngsild ${token} ${FILTER_ID}
}

@test "verify ngsild-update bridge is updating ngsi-ld entitiy" {

    cat ${UPSERT_FILTER}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    echo "# Sent upsert object to ngsi-ld-updates-bridge, wait some time to let it settle" >&3
    sleep 2
    password=$(get_password)
    token=$(get_token)
    cat ${UPDATE_FILTER}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    echo "# Sent update object to ngsi-ld-updates-bridge, wait some time to let it settle" >&3
    sleep 2
    get_ngsild ${token} ${FILTER_ID} | jq >${RECEIVED_ENTITY}
    delete_ngsild ${token} ${FILTER_ID}
    run compare_updated_entity ${RECEIVED_ENTITY}
    [ "$status" -eq 0 ]
}

@test "verify ngsild-update bridge is updating with noOverwrite option ngsi-ld entitiy" {
    cat ${UPSERT_FILTER}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    echo "# Sent upsert object to ngsi-ld-updates-bridge, wait some time to let it settle" >&3
    sleep 2
    password=$(get_password)
    token=$(get_token)
    cat ${UPDATE_FILTER_NO_OVERWRITE}| kafkacat -P -t ${KAFKACAT_NGSILD_UPDATES_TOPIC} -b ${KAFKA_BOOTSTRAP}
    echo "# Sent update object to ngsi-ld-updates-bridge, wait some time to let it settle" >&3
    sleep 2
    get_ngsild ${token} ${FILTER_ID} | jq >${RECEIVED_ENTITY}
    delete_ngsild ${token} ${FILTER_ID}
    run compare_updated_no_overwrite_entity ${RECEIVED_ENTITY}
    [ "$status" -eq 0 ]
}