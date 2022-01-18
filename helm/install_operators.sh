
NAMESPACE=digital-twin
CM_NAMESPACE=cert-manager

printf "\n"
printf "\033[1mInstalling OLM\n"
printf -- "------------------------\033[0m\n"
curl -sL https://github.com/operator-framework/operator-lifecycle-manager/releases/download/v0.20.0/install.sh | bash -s v0.20.0


#printf "\n"
#printf "\033[1mInstalling Strimzi operator\n"
#printf -- "------------------------\033[0m\n"

#helm repo add strimzi https://strimzi.io/charts/
#helm install kafka strimzi/strimzi-kafka-operator --namespace="${NAMESPACE}"

#printf "\033[1mPostgres operator installed successfully.\033[0m\n"


#printf "\n"
#printf "\033[1mInstalling Zalando postgres-operator\n"
#printf -- "------------------------\033[0m\n"
# First, clone the repository and change to the directory
#git clone https://github.com/zalando/postgres-operator.git
#cd postgres-operator
#git checkout v1.7.0

#kubectl apply -f manifests/postgresql.crd.yaml
#kubectl create -f manifests/configmap.yaml  # configuration
#kubectl create -f manifests/operator-service-account-rbac.yaml  # identiy and permissions
#kubectl create -f manifests/postgres-operator.yaml  # deployment
#kubectl create -f manifests/api-service.yaml  # operator API to be used by UI
#cd ..
#rm -rf postgres-operator
#printf "\033[1mPostgres operator installed successfully.\033[0m\n"

printf "\n"
printf "\033[1mInstalling Subscriptions for Keycloak operator, Strimzi, Postgres-operator \n"
printf -- "------------------------\033[0m\n"
kubectl create ns ${NAMESPACE}
kubectl create ns ${CM_NAMESPACE}

cat << EOF  | kubectl apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: operatorhubio-catalog
  namespace: olm
spec:
  sourceType: grpc
  image: quay.io/operatorhubio/catalog:latest
  displayName: Community Operators
  publisher: OperatorHub.io
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: mygroup
  namespace: ${NAMESPACE}
spec:
  targetNamespaces:
  - ${NAMESPACE}
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: keycloak-operator
  namespace: ${NAMESPACE}
spec:
  name: keycloak-operator
  channel: alpha
  source: operatorhubio-catalog
  sourceNamespace: olm
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: postgres-operator
  namespace: ${NAMESPACE}
spec:
  name: postgres-operator
  channel: stable
  source: operatorhubio-catalog
  sourceNamespace: olm
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: strimzi-operator
  namespace: ${NAMESPACE}
spec:
  name: strimzi-kafka-operator
  channel: stable
  source: operatorhubio-catalog
  sourceNamespace: olm
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: cert-manager
  namespace: operators
spec:
  name: cert-manager
  channel: stable
  source: operatorhubio-catalog
  sourceNamespace: olm
EOF
#kubectl create -f https://operatorhub.io/install/alpha/keycloak-operator.yaml   
printf "\033[1mSubscriptions installed successfully.\033[0m\n"

printf -- "\033[1mOperators installed successfully.\033[0m\n"
