TSDB_TABLE=entityhistory
TSDB_DATABASE=tsdb
POSTGRES_SECRET=ngb.acid-cluster.credentials.postgresql.acid.zalan.do
DBUSER=ngb
NAMESPACE=iff
USER_SECRET=secret/credential-iff-realm-user-iff
USER=realm_user
REALM_ID=iff
KEYCLOAK_URL="http://keycloak.local/auth/realms"
MQTT_URL=emqx-listeners:1883
KAFKA_BOOTSTRAP=my-cluster-kafka-bootstrap:9092
EMQX_INGRESS=$(kubectl -n ${NAMESPACE} get svc/emqx-listeners -o jsonpath='{.status.loadBalancer.ingress[0].ip}')