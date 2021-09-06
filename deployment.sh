#!/bin/bash
#
# Bash deployment file for creating the virtual machine
# and deploying the material multiprocessing code.

az vm create \
    --name "material_processor" \
    --image UbuntuLTS \
    --admin-username mota-engil \
    --generate-ssh-keys \
    --output none

VM_IP=$(az vm list-ip-addresses --query [0].virtualMachine.network.publicIpAddresses[0].ipAddress -o tsv)

az sql server firewall-rule create \
    --server $SERVER_NAME \
    -n AllowMyIP \
    --start-ip-address $VM_IP \
    --end-ip-address $VM_IP \
    --output none

cd deployment/ansible/

sed "s/<SEC1>/$SERVER_NAME/g;s/<SEC2>/$DATABASE/g;s/<SEC3>/$LOGIN_INPUT/g;s/<SEC4>/$PASSWORD_INPUT/g" group_vars/all -i_template
sed "s/IP/$VM_IP/g" hosts -i

ansible-playbook -i hosts machine_initial_setup.yml
ansible-playbook -i hosts set_up_task.yml