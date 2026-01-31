#!/bin/bash
filename=${0%.sh}
job_dir=`dirname "$(realpath $0)"`
docker_container_name={docker_container_name}
license_server_port=27000

# flags needed for the license checker
docker_flags="-v /etc/passwd:/etc/passwd:ro -v /etc/group:/etc/group:ro --add-host=host.docker.internal:host-gateway -e ACELLERA_LICENCE_SERVER=$license_server_port@host.docker.internal" 

# If the CI envvar is set, pass it to the container
docker run --user $(id -u):$(id -g) --rm $docker_flags -v $job_dir:/data $docker_container_name --input-json $filename/inputs.json /data 

if [ $? -ne 0 ]; then
    echo "Error in running application. Check logs..."
    exit 1
fi