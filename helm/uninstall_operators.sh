NAMESPACE=digital-twin


printf "\n"
printf "\033[1mUninstalling operator subscriptions\""

printf "\n"
printf "\033[1mInstalling Zalando postgres-operator\n"
printf -- "------------------------\033[0m\n"

kubectl -n {NAMESPACE} delete subscription/postgres-operator subscription/keycloak-operator subscription/strimzi-operator operatorgroup/mygroup catalogsource/olm

printf "\n"
printf "\033[1mUnInstalling OLM\n"
printf -- "------------------------\033[0m\n"
export OLM_RELEASE=v0.20.0
kubectl delete apiservices.apiregistration.k8s.io v1.packages.operators.coreos.com
kubectl delete -f https://github.com/operator-framework/operator-lifecycle-manager/releases/download/${OLM_RELEASE}/crds.yaml
kubectl delete -f https://github.com/operator-framework/operator-lifecycle-manager/releases/download/${OLM_RELEASE}/olm.yaml


printf "\n"
printf "\033[1mDeleting Namespace ${NAMESPACE}\n"
printf -- "------------------------\033[0m\n"
kubectl delete ns/${NAMESPACE}

printf -- "\033[1mOperators uninstalled successfully.\033[0m\n"

