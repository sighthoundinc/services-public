PROGNAME=$(basename $0)
docker_args=
initial_args="$@"
usage()
{
    cat >&2 <<EOF
run scriptname [arguments] host
Options:
    -h, --h             Print this usage message
    -s, --sensors_json  Specify sensors json file
    -c, --capture_dir   Specify capture dir

All other parameters are passed to the python script as-is,
including the first parameter which specifies the script to
run.

Examples:
docker/run.sh MCPEvents.py --sensors_json /storage/sensors/10G-BAI_0000647-sensors.json --capture_dir /storage/mcpevents/10G-BAI_0000647/test 10.1.10.99


EOF
}

if [ "$1" == "MCPEvents.py" ]; then
    docker_args="${docker_args} --restart=always"
else
    docker_args="${docker_args} --rm"
fi

# get command line options
SHORTOPTS="hs:c:"
LONGOPTS="help,sensors_json:,capture_dir:"
ARGS=$(getopt --options $SHORTOPTS --longoptions $LONGOPTS --name $PROGNAME -- "$@" )
if [ $? != 0 ]; then
   usage
   exit 1
fi

if [ $# -eq 0 ]; then
    echo "Must specify at least one argument"
    usage
    exit 1
fi

eval set -- "$ARGS"
while true;
do
    case $1 in
        -h | --help)       usage; exit 0 ;;
        -s | --sensors_json )   docker_args="${docker_args} -v $2:$2"; shift 2;;
        -c | --capture_dir)     docker_args="${docker_args} -v $2:$2"; shift 2;;
        -- )               shift; break ;;
        * )                break ;;
    esac
done

container_name="$(echo "$1-$2" | tr '.' '-' )"
docker_args="${docker_args} --name ${container_name}"

docker rm ${container_name} > /dev/null 2>&1

set -e

docker run -d  \
    ${docker_args} \
    mcpevents python3 ${initial_args}

echo "Container ${container_name} started for ${initial_args}"
