#!/usr/bin/env python
import sys
import re
import time
import fabric
from fabric.api import env, run


####### BEGIN SETTINGS #############
VMNAME = sys.argv[1]
IP = sys.argv[2]
USER = "root"
KEY = "~/.ssh/qa.key"
NTPSERVER = "10.80.16.236"
####### END SETTINGS #############

ssh_config_template = """
Host vcenter{c}
HostName {ip}
User {user}
IdentityFile {key}
"""

ntp_conf = """
# /etc/ntp.conf

driftfile /etc/ntp/drift
logfile /var/log/ntp.log

server {server}

#server 127.127.1.0
#fudge 127.127.1.0 stratum 10

restrict default ignore
restrict 127.0.0.1 mask 255.0.0.0
restrict {server} mask 255.255.255.255
"""


def write_local_vm_ssh_config(vm_name, ip, user, key):
    data = ssh_config_template.format(
        c=re.findall(r'\d+$', vm_name)[0],  # get unique ints from end
        ip=ip,
        user=user,
        key=key
    )
    with open("ssh_config", "a") as f:
        f.write(data)


def change_hostname(vm_name):
    run("echo %s > /etc/hostname" % vm_name)
    run("sed -i 's/127\.0\.1\.1/127\.0\.1\.1\t%s/' /etc/hosts" % vm_name)
    do_reboot()
    time.sleep(60)


def syncronize_ntp(ntp_server):
    run("apt-get -y install ntp")
    run("echo '%s' > /etc/ntp.conf" % ntp_conf.format(server=ntp_server))
    restart_ntp()
    time.sleep(60)


def restart_ntp():
    run("service ntp restart")


def verify_ntp():
    run("ntpq -p")


def do_reboot():
    fabric.operations.reboot(30)
    fabric.network.disconnect_all()  # because connection problems

if __name__ == "__main__":
    env['host_string'] = USER + '@' + IP
    env['key_filename'] = KEY
    fabric.tasks.execute(write_local_vm_ssh_config, VMNAME, IP, USER, KEY)
    fabric.tasks.execute(change_hostname, VMNAME)
    fabric.tasks.execute(syncronize_ntp, NTPSERVER)
    # fabric.tasks.execute(do_reboot)
    # fabric.tasks.execute(verify_ntp)
    fabric.network.disconnect_all()
    print "Done!"
