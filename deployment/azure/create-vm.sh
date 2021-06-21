#!/bin/bash

source $(xargs < .env)

az vm create --name "materialProcessor" --image UbuntuLTS --admin-username mota-engil --generate-ssh-keys
PublicIpAddress=$(az vm list-ip-addresses --query [0].virtualMachine.network.publicIpAddresses[0].ipAddress)

cd deployment/ansible/

sed "s/<SEC1>/$SERVER_NAME/g;s/<SEC2>/$DATABASE_NAME/g;s/<SEC3>/$DB_LOGIN/g;s/<SEC4>/$DB_PASSWORD/g" group_vars/all_template -i[backup]

ansible-playbook -i hosts machine_initial_setup.yml
ansible-playbook -i hosts set_up_task.yml