# Quick Install of Kubernetes
Steps for installing Kubernetes as superuser (unless otherwise
mentioned). Tested with Ubuntu 16.04.

## Install generic prereqs
```sh
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
```

## Install Docker-ce
```sh
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository \
   "deb https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
   $(lsb_release -cs) \
   stable"
apt-get update && apt-get install -y docker-ce=$(apt-cache madison docker-ce | grep 17.03 | head -1 | awk '{print $3}')
```

## Install Kubernetes
```sh
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF
apt-get update && apt-get install -y kubelet kubeadm kubectl 
```

## Setup cluster
Swap needs to be turned off. It is better to turn it off permanently in `/etc/fstab`
```sh
swapoff -a
kubeadm init --pod-network-cidr=10.244.0.0/16
```
Login as a regular user and perform following to enable local user to
access cluster info:
```sh
mkdir $HOME/.kube
sudo cp  /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
kubectl taint nodes --all=true node-role.kubernetes.io/master:NoSchedule-
```
The last taint step is required if you're running a single node cluster
and master should be enabled to run pods too.

## Verify cluster
Run following command and ensure that the master says "Ready". Also
ensure that all pods are listed as "Running". If something is not right,
check /var/log/syslog
```sh
kubectl get nodes
kubectl get pods --all-namespaces
```

## Add worker nodes to cluster
In other worker nodes you want to add to cluster, install Kubernetes and
then perform the `kubeadm join` command that was printed as the output
of the `kubeadm init` command above.
