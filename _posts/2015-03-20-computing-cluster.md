---
layout: post
title: Computing Cluster
categories: [work, cluster, tech]
---

My work often crosses the areas of verification and optimization, which often require a large amount of computing power or memory. This holds especially whenever a large amount of testcases shall be solved. However, in many cases, e.g. with independent testcases, these computations can be easily parallelized, simply by calling a separate script for every testcase.

In my current case, each testcase is a [PRISM](http://www.prismmodelchecker.org/) computation, which runs as a single thread, thus running on only one CPU core. The computations utilize this CPU core at 100%. As my workstation in the office has a quad core processor with Hyper-Threading, I have effectively 8 cores available to run these tasks in parallel. When the runtime of testcases increases to something like 24h, 8 cores can still be quite a bottleneck, when computing a higher number of testcases (e.g. 20). To speed up these computations, I implemented a small computing cluster, by utilizing all workstations with Linux-based operating systems that we have available at work.

Luckily, one does not need to re-invent the wheel, when doing such an implementation, cluster software is available off-the-shelve. However, the configuration of such software is far from trivial, especially for heterogeneous systems, such as ours. The following steps shall serve as a guideline for implementing such a mini computing cluster.

> The work here is in no way optimized for secure usage and based on trust among the participating machines. As we are using it in an internal network, we did not put much emphasize on security and many elements can be set to better security values, if you expect attacks or malicious use from your network or especially the people with access to your cluster username. We do not expect this and thus share a single username for cluster access. 

## Installation
We use [TORQUE](http://www.adaptivecomputing.com/products/open-source/torque/) to connect our nodes. Specifically we use TORQUE version 4.2.9. This is available via Arch Linux repositories or on the link above for systems with older package managers. We use e.g. also Ubuntu systems, whose package managers only offer version 2.4.16. 

As the protocol of TORQUE has changed over the years, it is not possible to have version 2 and version 4 interact with each other. This leads to computing nodes simply not correctly connecting to the cluster, although seemingly everything started up fine. 

We decided to go with version 4.2.9 for all systems. For Arch Linux systems (and Arch-based, such as Manjaro) the installation is pretty straight forward, as this version is available in the repositories:
```
pacman -S torque
```

For those systems, whose package managers do not offer version 4.2.9, we downloaded it from above website 
```
wget http://www.adaptivecomputing.com/download/torque/torque-4.2.9.tar.gz
tar -zxvf torque-4.2.9.tar.gz
```
and compiled it manually. Once all required packages are installed, the compilation takes some time, but should be quite straight forward. The required packages can be checked with the usual configure command:
```
cd torque-4.2.9
./configure
```

If not apparent, which package is missing, a simple Google search usually helps. Otherwise, TORQUE can be built and installed with
```
make && make install
```

## Configuration
It is conventional that a head node (the server) does not do computational tasks, but is only responsible for scheduling tasks to other machines. We do not follow this convention, as we do not want to set up a separate (virtual) machine for this task, but instead simply reserve one processor on one of the machines for this task.

### Preparation
TORQUE bases its communication on host names. These need to be set up correctly, before all other setup can be completed.
Two ways can be used to set up these host names:
1. /etc/hosts
This file hard codes all IP to host name assignments on every machine. If the IP addresses in the network where the computing nodes are running are fixed, this is a reasonable way to handle the host names. Should IP addresses be allocated dynamically (via DHCP), this method is not feasible, as the host files of every node need to be adjusted once the IP addresses change (e.g. on reboot).

It is also required that the own machine can be addressed by its host name (not localhost!). To do this, add the host names of all machines to their respective /etc/hosts in the lines starting with 127.0.0.1 and 127.0.1.1. In the following example we assume the host name to be *node*:
```
127.0.0.1 localhost node
127.0.1.1 node
```

2. DDNS
If IP addresses are dynamic, you might want to use a dynamic DNS (DDNS) service. This way, you can sync your IP addresses to a host name, which you can in turn use to connect TORQUE. DDNS can be efficiently implemented with ddclient and [FreeDNS](http://freedns.afraid.org/). A quick Google search should show you how to set this up. You want to use the interface IP for synchronization in ddclient, not the external IP.

I have to mention here that it is bad practice to use (external) DDNS services for internal IP addresses. It would be better to set up a proper naming service across the network, but this way is just so easy to set up, especially, if you already have a ddclient setup running.

#### Usernames
As TORQUE is executing given scripts on the different machines available, it needs the rights to access these scripts. In our simple setup, we added a specific user for the execution of TORQUE scripts on every machine. It is important that this user has the same user ID on every machine, such that access rights are managed correctly. Here is an example of creating a user *cluster* with ID 1100 and a home directory:
```
useradd –u 1100 cluster
mkdir /home/cluster
chown cluster:cluster /home/cluster
```

#### Network File System
To be able to load scripts on all machines, read input, as well as write output, a shared file system across all machines is advantageous. [Network File System (NFS)](http://en.wikipedia.org/wiki/Network_File_System) is the ideal candidate for such a file system. We utilize the storage of the headnode (*node1*) and mount this storage via NFS on all other machines.

##### Server
Setting up an NFS server is rather simple, just install the required package from your distribution (e.g. nfs-utils in Arch or nfs-kernel-server in Ubuntu). Then export the share to make it available to clients via an entry in **/etc/exports**:
```
/home/cluster/ 192.168.1.0/24 (rw,sync,no_subtree_check)
```
Note: This entry makes the share available to the whole 192.168.1.0/24 subnet. Change this value as required, consider using single IP addresses of your clients for security, if your cluster addresses are not dynamic.

##### Client
If not yet done, install the NFS package for the client of your distribution (e.g. nfs-utils in Arch, nfs-common in Ubuntu).

###### UPDATE 2015-04-30: For more flexible use of NFS use autofs:
install autofs (sudo pacman -S autofs in Arch, sudo apt-get install autofs in Ubuntu)
```
sudo echo "/home /etc/auto.home" >> /etc/auto.master
sudo echo "cluster -fstype=nfs4,rw,nosuid,soft node1:/home/cluster" > /etc/auto.home
Arch: systemctl restart autofs / Ubuntu: restart autofs
Arch: systemctl enable autofs
```

###### manual verison
This is not required when using autofs above. 
To mount the share for tests, use the following command:
```
mount -t nfs node1:/home/cluster /home/cluster
```

To permanently mount the share across reboots, add it to **/etc/fstab** like this:
```
node1:/home/cluster /home/cluster nfs users,noauto,x-systemd.automount,x-systemd.device-timeout=10,timeo=14,noatime 0 0
```

#### Assumptions going forward
In the following, we will assume that we have two machines available with the host names *node1* and *node2*. Node1 is both head node/server and client, while node2 connects as client to node1.

We further assume that both machines have compatible versions of TORQUE installed correctly.

### Server
All settings for TORQUE are located in **/var/spool/torque/**.

First, set the name of the head node in **/var/spool/torque/server_name**:
```
node1
```

The command 
```
pbs_server -t create
```
creates an empty server settings file.

Following the setup, as described in the [ArchLinux Wiki](https://wiki.archlinux.org/index.php/TORQUE), we use the following server settings:
```
qmgr -c "set server acl_hosts = node1"
qmgr -c "set server scheduling=true"
qmgr -c "create queue batch queue_type=execution"
qmgr -c "set queue batch started=true"
qmgr -c "set queue batch enabled=true"
qmgr -c "set queue batch resources_default.nodes=1"
qmgr -c "set queue batch resources_default.walltime=3600"
qmgr -c "set server default_queue=batch"
qmgr -c "set server keep_completed = 86400"
```

To add nodes to the server add them to **/var/spool/torque/server_priv/nodes**. You can specify the number of processors to be used, as well as the number of GPUs. As we are not using GPU computations, this will not be discussed here.
```
node2 np=8
```
The number of processors includes Hyper-Threading.

To start the server (and the required scheduler) simply run the following commands:
```
pbs_server
pbs_sched
```
Add these commands to your **/etc/rc.local** or other start scripts if you want to automatically start the TORQUE server with your machine. In this case, consider to also delete all jobs before starting the client. Otherwise you might end up with an overloaded machine that stops responding, even after restart. To do so add the following command to your start script after the start of the TORQUE server:
```
qdel -p all
```

### Client
The client configuration of TORQUE is located in **/var/spool/torque/mom_priv/config**. Here, for our example, the following settings should be set:
```
$pbsserver   node1   # note: this is the hostname of the headnode
$logevent    255     # bitmap of which events to log
```

To launch the client, run (or add to your start script) the following:
```
pbs_mom
```
In case you run headnode and client on the same machine, start the client only after starting the server and deleting all remaining jobs.

## Test
To see which nodes are connected to the headnode, run the following command on the headnode:
```
qnodes -a
```
All nodes shown as *free* are available, nodes shown as *down* are not available. In the latter case, check all settings again and otherwise jump to the Debug section below.

A quick test reveals if job scheduling works:
```
cd /home/cluster
echo "echo \"test\"" | qsub
```
This schedules a task printing "test" to the console. As there is no console available in this kind of setup, qsub takes care that all output of stdout and stderr are redirect to files named *.o and *.e and numbered with the process number.

A call to 
```
qstat -n
```
shows if and where the job is/was running. The above configuration keeps finished jobs listed for another 24 hours (86400 seconds). To change this parameter use 
```
qmgr -c "set server keep_completed = 86400"
```

Depending on your intended usage, you might also want to add your user as cluster manager, e.g. to purge the qstat list with qdel -p all. By default only root@localhost is allowed to do so (which might have a different job list and not be able to). Add a user like this:
```
qmgr -c 'set server managers+=cluster@localhost'
```

Check out the full references of [qsub](http://gridscheduler.sourceforge.net/htmlman/htmlman1/qsub.html) and [qstat](http://gridscheduler.sourceforge.net/htmlman/htmlman1/qstat.html) for all options. A good tutorial on the basic usage is available at [NYU](https://wikis.nyu.edu/display/NYUHPC/Tutorial+-+Submitting+a+job+using+qsub).

## Debug
Most errors we encountered when setting up our cluster where caused by either incompatible versions of TORQUE, NFS mounting or rights issues or wrong settings of hostnames.

These problems can be quickly resolved by running the client in verbose debug mode:
```
pbs_mom -D
```
Most of the errors are quite self-explanatory, otherwise Google usually helps.

We had some issues with TORQUE processes going from queuing (Q) to running (R) to queuing (Q) in qstat over and over again, which should usually not happen. In our case the user rights to the NFS directory were not set correctly and output files could not be created. No (understandable) error was given here. Should you experience this, have a look at these settings and try to create folders or files on the NFS manually as the cluster user to verify the issue.

Although I would not consider me an expert in TORQUE, feel free to post in the comments section below, should you have other problems, I will try my best to help.

## Operation
In normal operation it makes sense to create a hierarchy of scripts starting the single processes of your computation. The inner script starts your process with parameters it accepts from the command line, the outer script parametrizes the inner script and launches it as often as required. When launching the inner script with qsub, each process will be automatically submitted to the cluster:
```
qsub inner_script.sh
```
Make sure to run all these scripts in the shared NFS folder and as the cluster user. We also submit these jobs on the headnode via an SSH connection.

The output of the running inner scripts is stored in files named after the process number (check with qstat -f) and sorted by stderr and stdout into *.e and *.o files.

## Conclusion
I hope this article helps someone setting up a small home or office cluster and utilize the spare resources available. Please feel free to comment below should you find any errors in this article or have other remarks or comments.

Enjoy the x-fold speed-ups of your computations!