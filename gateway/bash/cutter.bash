CUTTER_ID="urn:plasmacutter:1"
FILTER_ID="urn:filter:1"
ATTRIBUTE="https://industry-fusion.com/types/v0.9/state"
WORKPIECEATTRIBUTE="https://industry-fusion.com/types/v0.9/hasInWorkpiece"
WORKPIECEID_PREFIX="urn:workpiece:"
WORKPIECE_ID=${WORKPIECEID_PREFIX}1
PROCESSING="https://industry-fusion.com/types/v0.9/state_PROCESSING"
OFF="https://industry-fusion.com/types/v0.9/state_OFF"
ON="https://industry-fusion.com/types/v0.9/state_ON"
BOOTSTRAP="my-cluster-kafka-bootstrap:9092"
TOPIC="iff.ngsild.attributes"
declare -A statemap
statemap[0]=${OFF}
statemap[1]=${ON}
statemap[2]=${PROCESSING}

declare -A device
device[0]="{\"id\":\"${CUTTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${OFF}\",\"nodeType\":\"@id\",\"index\":0}"
device[1]="{\"id\":\"${FILTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${FILTER_ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${OFF}\",\"nodeType\":\"@id\",\"index\":0}"
device[2]="{\"id\":\"${CUTTER_ID}\\\\${WORKPIECEATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${WORKPIECEATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Relationship\",\"https://uri.etsi.org/ngsi-ld/hasObject\":\"${WORKPIECE_ID}\",\"nodeType\":\"@id\",\"index\":0}"
declare -A display
display[0]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${ATTRIBUTE}) \t Value: $(basename ${OFF})"
display[1]="Asset: ${FILTER_ID} \t Attribute: $(basename ${ATTRIBUTE}) \t Value: $(basename ${OFF})"
display[2]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${WORKPIECEATTRIBUTE}) \t Value: $(basename ${WORKPIECE_ID})"

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
        WORKPIECE_ID=${WORKPIECEID_PREFIX}$2
        device[2]="{\"id\":\"${CUTTER_ID}\\\\${WORKPIECEATTRIBUTE}\",\"entityId\":\"${CUTTER_ID}\",\"name\":\"${WORKPIECEATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Relationship\",\"https://uri.etsi.org/ngsi-ld/hasObject\":\"${WORKPIECE_ID}\",\"nodeType\":\"@id\",\"index\":0}"
        display[2]="Asset: ${CUTTER_ID} \t Attribute: $(basename ${WORKPIECEATTRIBUTE}) \t Value: $(basename ${WORKPIECE_ID})"
    fi

}

VALUE=${OFF}
#CUTTER="{\"id\":\"${CUTTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${VALUE}\",\"nodeType\":\"@id\",\"index\":0}"
#FILTER="{\"id\":\"${FILTER_ID}\\\\${ATTRIBUTE}\",\"entityId\":\"${ID}\",\"name\":\"${ATTRIBUTE}\",\"type\":\"https://uri.etsi.org/ngsi-ld/Property\",\"https://uri.etsi.org/ngsi-ld/hasValue\":\"${VALUE}\",\"nodeType\":\"@id\",\"index\":0}"
while [ 1 ]; do
    tput clear
    tput cup 0 0 
    echo -e "${display[0]}"
    echo -e "${display[1]}"
    echo -e "${display[2]}"
    echo "--------------------------------------------------------------------"
    
    echo "${device[0]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
    echo "${device[1]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
    echo "${device[2]}" | kafkacat -P -b ${BOOTSTRAP} -t ${TOPIC}
    read -t 1 -n2 -s -r -p $'(c0, c1, c2) cutter off/on/processing, (f0, f1, f2) filter off/on/processing, (wx) workpiece x\n' key
    if [ ! -z "$key" ] && [ ${#key} -eq 2 ]; then
        keys=($(echo $key| grep -o .))

        echo $key "${keys[0]}" "${keys[1]}"
        get_kafka_string "${keys[0]}" "${keys[1]}"
    fi
done