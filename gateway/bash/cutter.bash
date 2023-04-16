###
. ./ngsild.bash

CUTTER_ID="urn:plasmacutter:1"
FILTER_ID="urn:filter:1"
FILTER_CARTRIDGE_ID="urn:cartridge:1"
ATTRIBUTE="https://industry-fusion.com/types/v0.9/state"
FILTER_CARTRIDGE_ATTRIBUTE="https://industry-fusion.com/types/v0.9/hasFilterCartridge"
WASTECLASS_ATTRIBUTE="https://industry-fusion.com/types/v0.9/wasteClass"
INUSEFROM_ATTRIBUTE="https://industry-fusion.com/types/v0.9/inUseFrom"
INUSEUNTIL_ATTRIBUTE="https://industry-fusion.com/types/v0.9/inUseUntil"
WORKPIECEATTRIBUTE="https://industry-fusion.com/types/v0.9/hasOutWorkpiece"
WORKPIECEINATTRIBUTE="https://industry-fusion.com/types/v0.9/hasInWorkpiece"
WORKPIECEID_PREFIX="urn:workpiece:"
WORKPIECEIN_ID=${WORKPIECEID_PREFIX}1
PROCESSING="https://industry-fusion.com/types/v0.9/state_PROCESSING"
OFF="https://industry-fusion.com/types/v0.9/state_OFF"
ON="https://industry-fusion.com/types/v0.9/state_ON"
BOOTSTRAP="my-cluster-kafka-bootstrap:9092"
TOPIC="iff.ngsild.attributes"

#------------------
# OEE
#------------------
OEE_ID=urn:oee:1
HASREFERENCEMASCHINE_ATTRIBUTE="https://industry-fusion.com/oee/v0.9/hasReferenceMachine"
AVAILABILITYTIMEAGG_ATTRIBUTE="https://industry-fusion.com/oee/v0.9/availabilityTimeAgg"
AVAILABILITYSTATE_ATTRIBUTE="https://industry-fusion.com/oee/v0.9/availabilityState"
ENDTIME_ATTRIBUTE="https://industry-fusion.com/types/v0.9/endTime"
STARTTIME_ATTRIBUTE="https://industry-fusion.com/types/v0.9/startTime"
TOTALCOUNT_ATTRIBUTE="https://industry-fusion.com/oee/v0.9/totalCount"
GOODCOUNT_ATTRIBUTE="https://industry-fusion.com/oee/v0.9/goodCount"

NAMESPACE=iff
CLIENT_ID=scorpio
USERSECRET=secret/credential-iff-realm-user-iff
USER=realm_user
KEYCLOAKURL=http://keycloak.local/auth/realms


declare -A statemap
statemap[0]=${OFF}
statemap[1]=${ON}
statemap[2]=${PROCESSING}


create_property_row(){
    ID=$1
    ATTRIBUTE=$2
    VALUE=$3
    echo "{\"id\":\"${ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${VALUE}\",\"nodeType\":\"@id\",\"index\":0}"
}

create_relationship_row(){
    ID=$1
    ATTRIBUTE=$2
    OBJECT=$3
    echo "{\"id\":\"${ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Relationship\",\"https://uri.etsi.org/ngsi-ld/hasObject\":\"${OBJECT}\",\"nodeType\":\"@id\",\"index\":0}"
}

declare -A device
device[0]="{\"id\":\"${CUTTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${OFF}\",\"nodeType\":\"@id\",\"index\":0}"
device[1]="{\"id\":\"${FILTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${FILTER_ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${OFF}\",\"nodeType\":\"@id\",\"index\":0}"
device[2]="{\"id\":\"${CUTTER_ID}\\\\${WORKPIECEATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${WORKPIECEATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Relationship\",\"https://uri.etsi.org/ngsi-ld/hasObject\":\"${WORKPIECEIN_ID}-out\",\"nodeType\":\"@id\",\"index\":0}"
device[3]="{\"id\":\"${CUTTER_ID}\\\\${WORKPIECEINATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${WORKPIECEINATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Relationship\",\"https://uri.etsi.org/ngsi-ld/hasObject\":\"${WORKPIECEIN_ID}\",\"nodeType\":\"@id\",\"index\":0}"
device[4]=$(create_property_row "$FILTER_ID" "$FILTER_CARTRIDGE_ATTRIBUTE" "$FILTER_CARTRIDGE_ID" )

declare -A display
display[0]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${ATTRIBUTE}) \t Value: $(basename ${OFF})"
display[1]="Asset: ${FILTER_ID} \t Attribute: $(basename ${ATTRIBUTE}) \t Value: $(basename ${OFF})"
display[2]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${WORKPIECEATTRIBUTE}) \t Value: $(basename ${WORKPIECEIN_ID}-out)"
display[3]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${WORKPIECEINATTRIBUTE}) \t Value: $(basename ${WORKPIECEIN_ID})"
display[4]="Asset: ${FILTER_ID} \t Attribute: $(basename ${FILTER_CARTRIDGE_ATTRIBUTE}) \t Value: $(basename ${FILTER_CARTRIDGE_ID})"

init_ngsild_user(){
    PASSWORD=$(get_password_from_default_user $NAMESPACE $USERSECRET)
    TOKEN=$(get_token "$CLIENT_ID" "$USER" "$PASSWORD" "$KEYCLOAKURL" "$NAMESPACE")
}


print_filter_cartridge(){
    filter_cartridge=$(get_ngsild_entity "$TOKEN" "$FILTER_CARTRIDGE_ID")
    wasteclass=$(echo $filter_cartridge | jq ' ."'${WASTECLASS_ATTRIBUTE}'".value.id')
    inuseuntil=$(echo $filter_cartridge | jq ' ."'${INUSEUNTIL_ATTRIBUTE}'".value' | xargs)
    inusefrom=$(echo $filter_cartridge | jq ' ."'${INUSEFROM_ATTRIBUTE}'".value' | xargs)
    if [ ! -z "$inuseuntil" ]; then
        inuseuntildate=$(date --date @$(( $inuseuntil / 1000 )))
    fi
    if [ ! -z "$inusefrom" ]; then
        inusefromdate=$(date --date @$(( $inusefrom / 1000 )))
    fi
    #echo $filter_cartridge inusefrm: $inusefrom ${INUSEUNTIL_ATTRIBUTE}
    echo -ne "Asset: ${FILTER_CARTRIDGE_ID} \t"
    echo -ne "$(basename ${WASTECLASS_ATTRIBUTE}): $wasteclass\t"
    echo -ne "$(basename ${INUSEFROM_ATTRIBUTE}): $inusefromdate\t"
    echo -ne "$(basename ${INUSEUNTIL_ATTRIBUTE}): $inuseuntildate\n"
}


print_oee(){
    #declare -A valvars=( [hasreferencemachine]=HASREFERENCEMASCHINE_ATTRIBUTE [availabilitytimeagg]=AVAILABILITYTIMEAGG_ATTRIBUTE [availabilitystate]=AVAILABILITYSTATE_ATTRIBUTE )
    #declare -A valextract=( [hasreferencemachine]=".object" [availabilitytimeagg]=".value" [availabilitystate]=".value" )
    oee=$(get_ngsild_entity "$TOKEN" "$OEE_ID")
    #for key in "${!valvars[@]}"; do 
    #    eval "$'$(echo $oee | jq \' .\"\'${'${valvars[$key]}$'}\'\"'${valextract[$key]}$'\')'"
    #done
    hasreferencemachine=$(echo $oee | jq ' ."'${HASREFERENCEMASCHINE_ATTRIBUTE}'".object')
    availabilitytimeagg=$(echo $oee | jq ' ."'${AVAILABILITYTIMEAGG_ATTRIBUTE}'".value' | xargs)
    availabilitystate=$(echo $oee | jq ' ."'${AVAILABILITYSTATE_ATTRIBUTE}'".value' | xargs)
    starttime=$(echo $oee | jq ' ."'${STARTTIME_ATTRIBUTE}'".value' | xargs)
    endtime=$(echo $oee | jq ' ."'${ENDTIME_ATTRIBUTE}'".value' | xargs)
    totalcount=$(echo $oee | jq ' ."'${TOTALCOUNT_ATTRIBUTE}'".value' | xargs)
    goodcount=$(echo $oee | jq ' ."'${GOODCOUNT_ATTRIBUTE}'".value' | xargs)

    #echo $oee $(echo $oee | jq ' ."'${HASREFERENCEMASCHINE_ATTRIBUTE}'"')
    echo -ne "Asset: ${OEE_ID} \t"
    echo -ne "$(basename ${HASREFERENCEMASCHINE_ATTRIBUTE}): $hasreferencemachine\t"
    echo -ne "$(basename ${AVAILABILITYTIMEAGG_ATTRIBUTE}): $availabilitytimeagg\t"
    echo -ne "$(basename ${AVAILABILITYSTATE_ATTRIBUTE}): $availabilitystate\t"
    echo -ne "$(basename ${STARTTIME_ATTRIBUTE}): $starttime\n"
    echo -ne "\t$(basename ${ENDTIME_ATTRIBUTE}): $endtime"
    echo -ne "\t$(basename ${TOTALCOUNT_ATTRIBUTE}): $totalcount"
    echo -ne "\t$(basename ${GOODCOUNT_ATTRIBUTE}): $goodcount"
    echo
}

get_kafka_string(){

    if [ "$1" = "c" ]; then
        VALUE=${statemap[$2]}
        echo value $VALUE
        device[0]="{\"id\":\"${CUTTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${VALUE}\",\"nodeType\":\"@id\",\"index\":0}"
        display[0]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${ATTRIBUTE}) \t Value: $(basename ${VALUE})"
    elif [ "$1" = "f" ]; then
        VALUE=${statemap[$2]}
        echo value $VALUE
        device[1]="{\"id\":\"${FILTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${FILTER_ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${VALUE}\",\"nodeType\":\"@id\",\"index\":0}"
        display[1]="Asset: ${FILTER_ID} \t Attribute: $(basename ${ATTRIBUTE}) \t Value: $(basename ${VALUE})"
    elif [ "$1" = "w" ]; then
        WORKPIECEIN_ID=${WORKPIECEID_PREFIX}$2
        device[2]="{\"id\":\"${CUTTER_ID}\\\\${WORKPIECEATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${WORKPIECEATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Relationship\",\"https://uri.etsi.org/ngsi-ld/hasObject\":\"${WORKPIECEIN_ID}-out\",\"nodeType\":\"@id\",\"index\":0}"
        device[3]="{\"id\":\"${CUTTER_ID}\\\\${WORKPIECEINATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${WORKPIECEINATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Relationship\",\"https://uri.etsi.org/ngsi-ld/hasObject\":\"${WORKPIECEIN_ID}\",\"nodeType\":\"@id\",\"index\":0}"
        display[2]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${WORKPIECEATTRIBUTE}) \t Value: ${WORKPIECEIN_ID}-out"
        display[3]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${WORKPIECEINATTRIBUTE}) \t Value: ${WORKPIECEIN_ID}"
        echo "${device[2]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
        echo "${device[3]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
    fi
}


display_regular_updates(){
    tput clear
    tput cup 0 0 
    echo -e "${display[0]}"
    echo -e "${display[1]}"
    echo -e "${display[2]}"
    echo -e "${display[3]}"
    echo -e "${display[4]}"
    echo "--------------------------------------------------------------------"
}

display_result_assets(){
tput cup 8 0
print_filter_cartridge
print_oee    
}

send_regular_updates(){

    echo "${device[0]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
    echo "${device[1]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
    echo "${device[2]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
    echo "${device[3]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
    echo "${device[4]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
}

init_ngsild_user
echo ${device[4]}
print_filter_cartridge
print_oee
#exit 1
VALUE=${OFF}
#CUTTER="{\"id\":\"${CUTTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${VALUE}\",\"nodeType\":\"@id\",\"index\":0}"
#FILTER="{\"id\":\"${FILTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${VALUE}\",\"nodeType\":\"@id\",\"index\":0}"
while [ 1 ]; do

    send_regular_updates
    display_regular_updates
    display_result_assets
    #print_filter_cartridge
    #print_oee

    tput cup 20 0
    read -t 5 -n2 -s -r -p $'(c0, c1, c2) cutter off/on/processing, (f0, f1, f2) filter off/on/processing, (wx) workpiece x\n' key
    if [ ! -z "$key" ] && [ ${#key} -eq 2 ]; then
        keys=($(echo $key| grep -o .))

        echo $key "${keys[0]}" "${keys[1]}"
        get_kafka_string "${keys[0]}" "${keys[1]}"
    fi
done