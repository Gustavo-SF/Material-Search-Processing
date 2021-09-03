#!/bin/bash

az vm create \
    --name "material_processor" \
    --image UbuntuLTS \
    --admin-username mota-engil \
    --generate-ssh-keys \
    --output none

PublicIpAddress=$(az vm list-ip-addresses --query [0].virtualMachine.network.publicIpAddresses[0].ipAddress)

cd deployment/ansible/

sed "s/<SEC1>/$SERVER_NAME/g;s/<SEC2>/$DATABASE/g;s/<SEC3>/$LOGIN_INPUT/g;s/<SEC4>/$PASSWORD_INPUT/g" group_vars/all_template -i_template
sed "s/IP/$PublicIpAddress/g" ../hosts

ansible-playbook -i hosts machine_initial_setup.yml
ansible-playbook -i hosts set_up_task.yml