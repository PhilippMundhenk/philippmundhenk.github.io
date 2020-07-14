---
layout: post
title: Home Network Upgrade - Basics
categories: [home, docker, tech, network]
---

In this article (and likely following ones) I will be setting up a new home network infrastructure, using cloud technologies such as distributed file systems, containers, and orchestration mechanisms to abstract from the hardware, allowing redundancy in the infrastructure, as well as easier scalability in future.

My current home network setup has grown over the years. It consists of a number of different services running on different machines. Some services are containerized, some running on native machines. Some devices are x86, some are ARM. While this is generally acceptable for a private context, handling failing devices can be a pain. Usually that hits the native devices, which require a bit more effort to set up again, and, of course, the services most used. Additionally, when more performance is required, additions to the network are not easily performed, as new devices need to be added, services migrated, etc.

In my case, part of the Docker containers I have running are located on a Network Attached Storage (NAS), a Synology 718+, which means that their constant data access (e.g., logs) are keeping the harddrives awake and spinning at all times. I do not want to get into the discussion of spinning harddrives or hibernating drives are better for the lifetime, but in any case, I want to reduce the amount of access there, by introducing a local cache, before data is read/written to the NAS. This will effectively move the NAS from one of my central servers back into the role of a storage device.

Note that this setup is not about scalability in terms of variable workloads or high-performance for many users, but rather reliability and extensibility. As we will see, the same means used for the first two can also be used to achieve the other two, as these are tightly coupled.

And as some people already asked when discussing my ideas: Yes, you may consider this overkill, especially for a home network. Part of the motivation is certainly: Because I can! Or, as a former colleague of mine liked to say: Hobbies are all about minimum utility at maximum effort.

## Design
### High-Level
The general idea of the re-design is to consolidate all services onto a cluster of (mostly) Raspberry Pis, maybe with an added x86 node, if I can't get everything ported to ARM. In the first iteration, this cluster will be local, accessible over VPN from other locations (see e.g., my older article on [Site-to-site VPN with OpenWrt and FRITZ!Box](/fritzbox-openwrt-vpn). In future iterations, I might add a remote components to this, utilizing also the additional Internet connections available there for fail-over. But this needs a bit more investigation.

I will start with a minimal setup and extend this in future. This also means that I will combine storage and compute nodes into one, where possible. In future iterations, there might be dedicated compute and storage nodes.

### Software Choices
I did not perform a detailed analysis here, but went a bit with gut feeling and some experiences I made in the past. I will be using:
- [Raspbian](https://www.raspberrypi.org/downloads/raspbian/) as the underlying OS. Detailed again later.
- [GlusterFS](https://www.gluster.org/) as distributed filesystem. I have chosen this based on good experiences in the past. It is simple and works fine on Raspberry Pi.
- [Kubernetes](https://kubernetes.io/) as orchestrator. Since this officially supports ARM today, it sounds like a good choice.
And many more in future articles of this series. I will explain those in due course.

## Hardware
As always, I don't want to invest too much money until I am sure that this setup works for me. And even then I want to keep the cost minimal, both in acquisition and operation. Thus, I am basing on hardware, which I already have available. In this case, I will be basing on two Raspberry Pi (RPi) 3B+. Of course a Raspberry Pi 4 would be better, especially due to USB 3 and the networking performance, and this might be the next upgrade stage. However, for now, the 3B+ must suffice. You may also start with an RPi2, though performance will be even worse. I do not recommend to use an RPi1, other than maybe a special compute node, as it uses ARMv6 instruction set and it is tough to obtain containers for this, as Docker only started supporting ARM shortly before ARMv7 was mainstream.

Additionally, I acquired two used 120GB SATA SSDs (Samsung and Crucial) and two no-name USB3-SATA adapters. These will serve as working file systems for the cluster. Long-term data storage will remain on my Network Attached Storage (NAS).

A existing Netgear switch is used for Ethernet and an Anker USB power supply is used for powering the RPis.

## Base Software
While for a scalable system, an operating system that can be upgraded continuously would probably be a good choice, I decided to anyway go with the standard Raspbian setup. In my case Raspbian Buster Lite. I hope that support and stability there is a little better.
It is important to note that this limits me to a 32-Bit operating system! While the RPi has a 64-Bit processor supporting ARMv8 (aarch64) instruction set, due to the choice of Raspbian, I can only use ARMv7. This can be checked by running ```uname -m``` once your nodes are set up.

Since there is a sheer infinite number of guides out there how to do a basic SD-Card setup for the RPi, I will not be covering this here (see e.g., [here](https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up)). Just one note: If you want to perform a headless setup, don't forget to add a file named "ssh" to the boot partition. 

For higher performance and longer lifetime, I decided to also move the operating system to the external drive (see also [here](https://jamesachambers.com/raspberry-pi-3b-microsd-vs-ssd-speed-benchmarks/)).
For this, I divided the SSD into two partitions, one of about 12GB, one for the remaining 100GB.
I moved Raspbian to the smaller partition and will use the other for data with a distributed file system.
This is fairly simple, you may follow [this guide](https://www.tomshardware.com/news/boot-raspberry-pi-from-usb,39782.html) or the following steps. To format the external drive with two partitions with ext4:
```bash
sudo fdisk /dev/sda
# delete all existing partitions: d
# ensure DOS partition table: o
# create new primary partition with 12GB: n, p, <enter>, <enter>, +12G
# create new primary partition with the remaining size: n, p, <enter>, <enter>, <enter>
# persist all changes: w

sudo mkfs.ext4 /dev/sda1
sudo mkfs.ext4 /dev/sda2 
```

Then, to run Raspbian off the first partition:
```bash
sudo mkdir /mnt/ssd1
sudo mount /dev/sda1 /mnt/ssd1
sudo rsync -avx / /mnt/ssd1
sudo nano /boot/cmdlinetxt
# add to end of line: root=/dev/sda1 rootfstype=ext4 rootwait
```

Then, reboot and perform the same steps on the other device.

Don't forget to also adjust hostnames and IPs. In my case, I will be using the following setup:
- hostname: node01, IPv4: 192.168.44.51
- hostname: node02, IPv4: 192.168.44.52

This concludes the basic setup. We now need to set up the GlusterFS and Kubernetes.

## GlusterFS
### Preparations
As distributed file system, I will be using GlusterFS. This offers a fairly good performance, also on limited devices, such as the RPi. It is furthermore very easy to configure.
While it is possible to use GlusterFS in an extremely configurable way via REST, e.g., through the use of [heketi](https://github.com/heketi/heketi). I decided against using such a setup, for two reasons: Firstly, heketi needs at least a replication of three, which does not work well with two devices. Secondly, it seems to be over-complicating my setup, as I might only need some simple volumes.

Now, we can prepare for GlusterFS (see e.g., [here](https://www.howtoforge.com/tutorial/high-availability-storage-with-glusterfs-on-ubuntu-1804/), and [official documentation](https://docs.gluster.org/en/latest/)). First, make sure that the second partition on the SSD is always mounted:
```bash
sudo mkdir /mnt/ssd2
sudo chmod 777 /mnt/ssd2
sudo nano /etc/fstab
# add the following line:
# UUID=<UUID>  /mnt/ssd2       ext4    defaults        0       2
# where <UUID> can be found by running: blkid | grep dev/sda2
sudo mount -a
```
Note that you might want to adjust permissions to something a little less permissive, but suitable to your use case.

Then, create some folders for file storage. I intend to have one GlusterFS volume being replicated across both devices and a second volume striped across both devices:
```bash
mkdir /mnt/ssd2/brick1
mkdir /mnt/ssd2/brick2
```

Now, also set this up on the other device.

You also want to make sure that hostnames are defined on all nodes, in my case:
```bash
sudo nano /etc/hosts
# Add these lines:
# 192.168.44.51   node01
# 192.168.44.52   node02

sudo nano /etc/hostname
#node01/node02
```

### Setup Server
Now we can finally start working on GlusterFS. Since we want both devices to be server and client, we will install both packages on both nodes:
```bash
sudo apt install glusterfs-server glusterfs-client
sudo systemctl start glusterd
sudo systemctl enable glusterd
```

We will now set up the cluster. The following command will only need to be run on node01:
```bash
sudo gluster peer probe node02

sudo gluster volume create vol01 replica 2 transport tcp node01:/mnt/ssd2/brick1 node02:/mnt/ssd2/brick1 force
sudo gluster volume start vol01

sudo gluster volume create vol02 transport tcp node01:/mnt/ssd2/brick2 node02:/mnt/ssd2/brick2 force
sudo gluster volume start vol02
```

You may now check the status of your two volumes with:
```bash
sudo gluster volume info vol01
sudo gluster volume info vol02
```

### Setup Client
To use them, we need to mount these volumes. To do so, we create mount points on both nodes:
```bash
sudo mkdir -p /mnt/replicated
sudo mkdir -p /mnt/striped
```
and mount the volumes on both nodes:
```bash
sudo mount -t glusterfs node01:/vol01 /mnt/replicated
sudo mount -t glusterfs node01:/vol02 /mnt/striped
```
Node that it does not matter which node you use in the address here. This is only used for setup anyway, data transfer will be optimized automatically.

You can now check the sizes of your new volumes with 
```bash
df -h /mnt/replicated/ /mnt/striped/
```
Note that the striped volume should have double the size of the replicated volume. In my case 100 GB and 200GB.

If all of this has worked, we can now make the mount point persistent. To do so, add the following to /etc/fstab on both nodes:
```bash
node01:/vol01 /mnt/replicated glusterfs defaults,_netdev 0 0
node01:/vol02 /mnt/striped glusterfs defaults,_netdev 0 0
```

### Extending storage
Take not that when you want to extend these replicated volume (vol01), you will always need a multiple of two bricks (```replica 2```) for the replicated volume, ideally both of same size, to utilize full capacity. They can be of different size than the existing drives. You likely want to distribute these across two devices as well. Thus, adding a single harddrive to the replicated volume is not possible.

## Kubernetes
### Setup
While GlusterFS is used for the storage cluster, Kubernetes is used for the orchestration of containers. There are multiple ways to set up Kubernetes on a machine. I will be using ```kubeadm```. I guess this is not the simplest way to set it up, but you certainly learn a lot more than when taking one of the more packaged approaches.

I rely on some guides specific to Raspberry Pi (e.g., [this](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)) and also heavily on the excellent Kubernetes documentation, which I can only recommend to refer to whenever you are in doubt (see also [here](https://medium.com/nycdev/k8s-on-pi-9cc14843d43)).

Lets get started by preparing the system. As we are using Raspbian Buster, which comes with comes with iptables 1.8.2 at time of this writing, offering a different interface than before version 1.8, we need to switch it to legacy mode. Until further notice, the following commands need to be run on both nodes:
```bash
sudo apt-get install -y iptables arptables ebtables

sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
sudo update-alternatives --set arptables /usr/sbin/arptables-legacy
sudo update-alternatives --set ebtables /usr/sbin/ebtables-legacy
```

We can then install the required Kubernetes components:
```bash
sudo apt-get update && sudo apt-get install -y apt-transport-https curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

We will be using Docker as the container engine for Kubernetes and adjust the Pi user to be allowed to use Docker, by adding it to the Docker group:
```bash
curl -sSL get.docker.com | sh
sudo usermod pi -aG docker
```

Raspbian uses a swap file, which we need to turn off, as Kubernetes does not operate on systems with swap enabled:
```bash
sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
sudo update-rc.d dphys-swapfile remove
```

Don't forget to disable it also for future startups:
```bash
sudo systemctl disable dphys-swapfile.service
```

We now need to enable cgroup settings to allow Docker (which is underlying Kubernetes) to control resource allocation. To do so add to the end of first line of ```/boot/cmdline.txt```:
```
cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory
```

Now, reboot your nodes:
```bash
sudo reboot
```

Lets go on by setting up Kubernetes. Run the following commands on node01, which will become the master node. This may take some time to complete and will download the required Docker images for you:
```bash
sudo kubeadm init
```

The previous command outputs a few commands to run on the master node (node01). Run these now:
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

Then, on node02 run the join command also given as output of ```kubeadm init```. I shorten the token and hash here:
```bash
sudo kubeadm join node01:6443 --token <token> --discovery-token-ca-cert-hash <hash>
```

Kubernetes can be used with different network implementations (see also [here](https://kubernetes.io/docs/concepts/cluster-administration/networking/)). Reasonable choices for the RPi are Flannel and Weave Net. I will be using the latter. On node one run:
```bash
kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"
```

Wait a few minutes and then run and look for status ready:
```bash
pi@node01:~ $ kubectl get nodes
NAME     STATUS   ROLES    AGE     VERSION
node01   Ready    master   10m     v1.17.4
node02   Ready    <none>   7m29s   v1.17.4
```

By default, Kubernetes only schedules workloads on the worker node (node02), and not on the master node (node01). As I want to also use the master node for computation, I run:
```bash
kubectl taint node node01 node-role.kubernetes.io/master:NoSchedule-
```

Done! That was surprisingly easy! In my case everything was rather straight-forward. Depending on your setup, you might experience a hiccup here and there. In that case, refer to the Kubernetes documentation (see [here](https://kubernetes.io/docs/home/)).
We now have a running Kubernetes cluster on Raspberry Pi!

### Kubernetes Dashboard
The first service we will be running is the Kubernetes Dashboard. This simplifies understanding and configuration of the newly set up cluster a lot. To do so, run on node01:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-beta8/aio/deploy/recommended.yaml
```
This will do download the Kubernetes definition and set up everything you need.

We will be using the API Server to access the dashboard. For this to work, we need to install client certificates in the browser (see [here](https://github.com/kubernetes/dashboard/blob/master/docs/user/accessing-dashboard/1.7.x-and-above.md)). We will be extracting the certificates from kubeconfig for this purpose (see [here](https://www.australtech.net/kubernetes-unable-to-login-to-the-dashboard/)):
```bash
grep 'client-certificate-data' ~/.kube/config | head -n 1 | awk '{print $2}' | base64 -d >> kubecfg.crt
grep 'client-key-data' ~/.kube/config | head -n 1 | awk '{print $2}' | base64 -d >> kubecfg.key
openssl pkcs12 -export -clcerts -inkey kubecfg.key -in kubecfg.crt -out kubecfg.p12
```
Now use your favorite SCP tool or similar to download the certificates and install them in your browser.

You can now use your browser and access the dashboard at ```https://192.168.44.51:6443/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/login```

However, as you can see, we need a token to access the dashboard. So lets generate this token now (see also [here](https://medium.com/@kanrangsan/creating-admin-user-to-access-kubernetes-dashboard-723d6c9764e4)).

First, lets create an admin user. To do so, save the following to ```adminuser.yml```:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kube-system
```
and run
```bash
kubectl apply -f adminuser.yml
```

Now we need to bind this user to cluster-admin role for correct permissions. Place the following in ```binding.yml```:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kube-system
```
and apply:
```bash
kubectl apply -f binding.yml
```

You can now retrieve the token by running:
```bash
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep admin-user | awk '{print $1}')
```
It is listed in the "Data" section of the output.

You can now log in to the dashboard with this token at ```https://192.168.44.51:6443/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/login```.

### Test Server
In a last step, we will be combining GlusterFS and Kubernetes by running a simple webserver, reading data from the replicated GlusterFS volume. Add the following to ```test.yml```:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: httpd
  labels:
    app: httpd
spec:
  type: NodePort
  ports:
    - port: 80
      protocol: TCP
      targetPort: 80
      nodePort: 30000
  selector:
    app: httpd
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpd
  labels:
   app: httpd
spec:
  replicas: 1
  selector:
    matchLabels:
      app: httpd
  template:
    metadata:
      labels:
        app: httpd
    spec:
      containers:
      - name: httpd
        image: armhf/httpd:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 80
          protocol: TCP
        volumeMounts:
        - mountPath: /usr/local/apache2/htdocs/
          name: test-volume
      volumes:
      - name: test-volume
        hostPath:
          # directory location on host
          path: /mnt/replicated
          # this field is optional
          type: Directory
```
Note how we are using an image denoted ```armhf/``` here. This is a remnant of the early days of Docker on ARM. Back then, only armhf existed to mark images as suitable for ARM. Only later this was specified more clearly as armv6, armv7 and armv8. Since we are running Raspbian with ARMv7 support and this is backward compatible with ARMv6, we should be able to run all armhf images.

Now, run the following to create the webserver and an ```index.html``` page to serve:
```bash
kubectl apply -f test.yml
echo "<h1>My great webserver test<h1>" >> /mnt/replicated/index.html
```

If all worked out, you should now be able to see the text we just added to index.html when opening any of the node IPs in the browser, together with port 8080. E.g., http://192.168.44.51:30000 or http://192.168.44.52:30000

To test writing permissions to the GlusterFS volume, you launch a shell in the pod we just created and write to a file from there:
```bash
pi@node01:~ $ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
httpd-5b6c6bb6f9-w858q   1/1     Running   0          18h

pi@node01:~ $ kubectl exec -it httpd-5b6c6bb6f9-w858q bash

root@httpd-5b6c6bb6f9-w858q:/usr/local/apache2# echo "test" > /usr/local/apache2/htdocs/test
root@httpd-5b6c6bb6f9-w858q: exit
pi@node01:~ $ cat /mnt/replicated/test
```

### GlusterFS in Kubernetes
While the above works nicely with these two nodes, when adding more nodes, we need to take care to also mount the required GlusterFS volumes there (e.g., to ```/mnt/replicated```). Otherwise, the data required for the pod will not be available. This is an additional step to take on the host that can be avoided. We can instead use the Kubernetes support for GlusterFS (see [here](https://kubernetes.io/docs/concepts/storage/volumes/#glusterfs)) to avoid that extra step on the host. This has the additional advantage of more resilience, as the entry in ```/etc/fstab``` is no longer required, avoiding a failed boot, in case the given node is not available. Additionally, the GlusterFS plugin also automatically falls back to the next node, in case one should not be available. It also distributes the requests to GlusterFS across the given nodes.

To set this connection up, I follow [this guide](https://github.com/kubernetes/examples/tree/master/volumes/glusterfs). First, create your endpoints file ```endpoints.yml```, in my case, it looks like this:
```yaml
apiVersion: v1
kind: Endpoints
metadata:
  name: glusterfs-cluster
subsets:
- addresses:
  - ip: 192.168.44.51
  ports:
  - port: 1
- addresses:
  - ip: 192.168.44.52
  ports:
  - port: 1
```
Note that the field port here has no meaning. Any value between 1 and 65535 can be entered.

Now, load the file with:
```bash
kubectl apply -f endpoints.yml
```

Now, we need to adjust the pod to use the GlusterFS cluster. Change the ```volumes:``` statement in your ```test.yml``` to look like this:
```yaml
      volumes:
      - name: test-volume
        glusterfs:
          endpoints: glusterfs-cluster
          path: vol01
          readOnly: true
```
where path is the volume name given in GlusterFS.

You can now apply the ```test.yml``` again:
```bash
kubectl apply -f test.yml
```

When changing the content of ```/mnt/replicated/index.html```, you should be able to see the changed output when opening ```http://192.168.44.51:30000``` or ```http://192.168.44.52:30000```.

If you do not require any access to the volumes on the host, you can now remove the entries added to ```/etc/fstab``` above.

## Next Steps
We now have a running cluster and distributed filesystem, all on Raspberry Pis, running of attached SSDs. While I would consider this a feat in itself, we have not yet addressed parts of the motivation. Particularly, the following items need to be addressed:
- Fail-Over: The cluster we have here is still very weak in terms of high-availability. With a single master node for Kubernetes, we still have a single point of failure. Thus, in future, this shall be extended to a multi-master cluster.
- Automated Setup: This setup has been performed mostly manually as a learning exercise. That is not great, e.g., in case a new node needs to be added quickly. I shall set up some scripts to automate the process. Ansible, etc. are the tools that come to mind there.
- Extension/Replacement Test: Part of the motivation was to have an extensible cluster, where new nodes can be added for more performance or in case of failure of other nodes. I need to test if this really works as easy as planned and what exactly are the necessary steps.
- Load Balancing: Currently, always one of the node IPs need to be used to access the cluster. As I am lazy, I will likely always use the first IP address. And although all services will be accessible through this, thanks to Kubernetes IP table magic, this will add unnecessary strain on the first node. I might go with keepalived to remedy this situation, setting up a virtual IP address for all nodes, which is answered in round-robin fashion. This is not ideal, but simple enough for my use case and will help to distribute load. It will also come in handy when using multiple master nodes (see e.g., [here](https://medium.com/velotio-perspectives/demystifying-high-availability-in-kubernetes-using-kubeadm-3d83ed8c458b)).
- Data Management: By using the Kubernetes plugin for GlusterFS, we already achieve a higher reliability than with /etc/fstab mounts. However, we need to specify all the GlusterFS nodes in the endpoints definition. In future, I want to replace also the GlusterFS access with a central virtual IP, served round robin by all GlusterFS nodes. Then, fail-over can be handled distributed in the GlusterFS nodes, rather than in Kubernetes. I will also be using keepalived for this.
- Reverse Proxy: Instead of using dedicated ports for every service, it would be nice to have HTTP(S) all services addressable on port 80. This would also terminate HTTPS traffic in a point.
- Data Storage: I mentioned above that the data storage on SSDs is supposed to be a short-term cache. Thus, some of the services need to transfer data to a NAS running in the network, as well. This data needs to be copied/moved there. Ideally, this will of course also run in a container, not natively. 
- Migration: Last, but not least, my existing services need to be ported into the cluster. I am sure some challenges are waiting there for me, as well.
- Upgrades: Updating system and containers should be done as automated as possible.
- Security: As all of this is in my home network, security was not even mentioned in this article. However, with a running cluster, that might need to serve also on the Internet, security is becoming a big concern. Basic security means, like certificates, etc. need to be put into place and the cluster shall be analyzed for its security and hardened where required.
- SHONITH Device(s): Sometimes it can be useful to hard-reset individual nodes. With the RPis running on 5V at low power, the required circuits are rather easy. I might add such circuits as SHONITH (SHoot the Other Node In The Head) devices in future.
- Hardware & Case: Add a dedicated switch and USB power supply not shared with other devices and a nice scalable case, rather than having everything dumped onto a shelf.
- Many more: I am sure on the journey building this setup, I will have many more ideas what I can add, both in terms of infrastructure, as well as functionality.