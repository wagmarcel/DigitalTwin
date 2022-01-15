NAMESPACE=digital-twin


printf "\n"
printf "\033[1mUninstalling Strimzi opereator\""

helm uninstall kafka -n ${NAMESPACE}

printf "\n"
printf "\033[1mInstalling Zalando postgres-operator\n"
printf -- "------------------------\033[0m\n"
# First, clone the repository and change to the directory
git clone https://github.com/zalando/postgres-operator.git
cd postgres-operator
git checkout v1.7.0

kubectl delete -f manifests/postgresql.crd.yaml 
kubectl delete -f manifests/configmap.yaml  # configuration
kubectl delete -f manifests/operator-service-account-rbac.yaml  # identiy and permissions
kubectl delete -f manifests/postgres-operator.yaml  # deployment
kubectl delete -f manifests/api-service.yaml  # operator API to be used by UI
cd ..
rm -rf postgres-operator
printf "\033[1mPostgres operator installed successfully.\033[0m\n"

kubectl delete -f https://operatorhub.io/install/alpha/keycloak-operator.yaml

printf "\n"
printf "\033[1mUnInstalling OLM\n"
printf -- "------------------------\033[0m\n"
export OLM_RELEASE=v0.20.0
kubectl delete apiservices.apiregistration.k8s.io v1.packages.operators.coreos.com
kubectl delete -f https://github.com/operator-framework/operator-lifecycle-manager/releases/download/${OLM_RELEASE}/crds.yaml
kubectl delete -f https://github.com/operator-framework/operator-lifecycle-manager/releases/download/${OLM_RELEASE}/olm.yaml

printf -- "\033[1mOperators uninstalled successfully.\033[0m\n"
