#!/bin/bash
# Copyright (c) 2022 Intel Corporation
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

# use specific k3s image to avoid surprises with k8s api changes
K3S_IMAGE=rancher/k3s:v1.22.6-k3s1-amd64


echo Installing kubectl
echo ----------------------
sudo snap install kubectl --classic

echo Installing K3d cluster
echo ----------------------
## k3d cluster with 2 nodes
curl -s https://raw.githubusercontent.com/rancher/k3d/main/install.sh | TAG=v4.4.8 bash
k3d registry create iff.localhost -p 12345
k3d cluster create --image ${K3S_IMAGE} -a 2 --registry-use iff.localhost:12345 iff-cluster

echo Install Helm v3.7.2
echo ---------------
 # helm v3.7.2
wget https://get.helm.sh/helm-v3.7.2-linux-amd64.tar.gz
tar -zxvf helm-v3.7.2-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/bin/helm

echo Install Helm diff plugin
echo ------------------------ 
helm plugin install https://github.com/databus23/helm-diff


echo Install Helmfile
echo ----------------
cd ../helm
# helmfile v0.143.0
wget https://github.com/roboll/helmfile/releases/download/v0.143.0/helmfile_linux_amd64
chmod u+x helmfile_linux_amd64

echo Install Java 11
echo ---------------
sudo apt update
sudo apt install -yq default-jre maven

echo Install shellcheck
echo ------------------
sudo apt install -yq shellcheck

echo Install jq
echo ------------------
sudo apt install -yq jq

echo Install bats
echo ------------------
sudo apt install -yq bats

if [ -z "${SELF_HOSTED_RUNNER}" ]; then
    echo Change group of /etc/hosts
    echo --------------------------
    sudo groupadd runner
    sudo chgroup runner /etc/hosts
    sudo usermod -a -G runner ${USER}
fi