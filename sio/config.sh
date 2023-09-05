#!/bin/bash

SCRIPT_PATH=$(dirname $(realpath $0))
# Define the path to the JSON file
JSON_FILE="${1:-${SCRIPT_PATH}/conf/sio.json}"

# Check JQ installation
if ! command -v jq &> /dev/null
then
    echo "jq could not be found, exiting..."
    exit 1
fi

# Define a function to display a summary of all sources
display_summary() {
    # Check if the JSON file exists
    if [[ ! -f $JSON_FILE ]]; then
        echo "The JSON file : $JSON_FILE does not exist!"
        exit 1
    fi

    # Display a summary of all sources and their URLs
    echo "Reading from $JSON_FILE"
    echo "Summary of all sources:"
    jq -r 'to_entries[] | "\(.key): \(.value.parameters.VIDEO_IN)"' $JSON_FILE
}

# Define a function to create a new source
create_source() {
    # Prompt the user for the sourceId
    read -p "Enter the sourceId: " sourceId

    # Prompt the user to select between TrafficAnalytics and VehicleAnalytics
    PS3="Select an option: "
    options=("TrafficAnalytics" "VehicleAnalytics")
    select opt in "${options[@]}"
    do
        case $opt in
            "TrafficAnalytics")
                pipeline="./share/pipelines/TrafficAnalytics/TrafficAnalyticsRTSP.yaml"
                break
                ;;
            "VehicleAnalytics")
                pipeline="./share/pipelines/VehicleAnalytics/VehicleAnalyticsRTSP.yaml"
                break
                ;;
            *) echo "Invalid option";;
        esac
    done

    # Prompt the user for the rtsp URL
    read -p "Enter the rtsp URL: " rtspUrl

    # Set default values for amqpUser and amqpPassword
    amqpUser="guest"
    amqpPassword="guest"

    # Prompt the user if they want to set a custom amqp user and pass
    read -p "Do you want to set a custom amqp user and pass? (y/n) " customAmqp
    if [[ $customAmqp == "y" ]]; then
        read -p "Enter the amqp user: " amqpUser
        read -p "Enter the amqp password: " amqpPassword
    fi

    # Create a new source object with the provided values
    newSource=$(jq -n \
                    --arg pipeline "$pipeline" \
                    --arg sourceId "$sourceId" \
                    --arg rtspUrl "$rtspUrl" \
                    --arg recordTo "/data/sighthound/media/output/video/$sourceId/" \
                    --arg imageSaveDir "/data/sighthound/media/output/image/$sourceId/" \
                    --arg amqpUser "$amqpUser" \
                    --arg amqpPassword "$amqpPassword" \
                    '{($sourceId): {"pipeline": $pipeline, "restartPolicy": "restart", "parameters": {"VIDEO_IN": $rtspUrl, "sourceId": $sourceId, "recordTo": $recordTo, "imageSaveDir": $imageSaveDir, "amqpHost": "rabbitmq", "amqpPort": "5672", "amqpExchange": "anypipe", "amqpUser": $amqpUser, "amqpPassword": $amqpPassword, "amqpErrorOnFailure": "true"}}}')

    # Check if the JSON file exists
    if [[ -f $JSON_FILE ]]; then
        # If the file exists, add the new source to it
        jq --argjson newSource "$newSource" '. += $newSource' $JSON_FILE > tmp.$$.json && mv tmp.$$.json $JSON_FILE
    else
        # If the file does not exist, create it with the new source as its content
        echo $newSource > $JSON_FILE
    fi

    echo "New source created successfully!"
}

# Define a function to edit an existing source
edit_source() {
    # Check if the JSON file exists
    if [[ ! -f $JSON_FILE ]]; then
        echo "The JSON file does not exist!"
        return 1
    fi

    # Prompt the user to select a source to edit from a list of available sources
    PS3="Select a source to edit: "
    
     sources=()
     while IFS= read -r line; do 
         sources+=("$line")
     done < <(jq -r 'keys[]' $JSON_FILE)
    
     select sourceId in "${sources[@]}"
     do 
         if [[ -n $sourceId ]]; then break; fi;
         echo "Invalid option"
     done

     # Display current value of pipeline and prompt user for changes 
     current_pipeline=$(jq -r --arg sourceId "$sourceId" '.[$sourceId].pipeline' $JSON_FILE)
     echo Current pipeline is : "$current_pipeline"
     read -p "Do you want to change the pipeline? (y/n) " change_pipeline
     if [[ $change_pipeline == "y" ]]; then
         # Prompt the user to select between TrafficAnalytics and VehicleAnalytics
         PS3="Select an option: "
         options=("TrafficAnalytics" "VehicleAnalytics")
         select opt in "${options[@]}"
         do
             case $opt in
                 "TrafficAnalytics")
                     pipeline="./share/pipelines/TrafficAnalytics/TrafficAnalyticsRTSP.yaml"
                     break
                     ;;
                 "VehicleAnalytics")
                     pipeline="./share/pipelines/VehicleAnalytics/VehicleAnalyticsRTSP.yaml"
                     break
                     ;;
                 *) echo "Invalid option";;
             esac
         done
     else
         pipeline=$current_pipeline
     fi

    # Display current value of rtsp URL and prompt user for changes 
    current_rtspUrl=$(jq -r --arg sourceId "$sourceId" '.[$sourceId].parameters.VIDEO_IN' $JSON_FILE)
    echo Current rtsp URL is : "$current_rtspUrl"
    read -p "Do you want to change the rtsp URL? (y/n) " change_rtspUrl
    if [[ $change_rtspUrl == "y" ]]; then
        # Prompt the user for the rtsp URL
        read -p "Enter the rtsp URL: " rtspUrl
    else
        rtspUrl=$current_rtspUrl
    fi

    # Set default values for amqpUser and amqpPassword
    amqpUser="guest"
    amqpPassword="guest"

    # Display current value of amqp user and prompt user for changes 
    current_amqpUser=$(jq -r --arg sourceId "$sourceId" '.[$sourceId].parameters.amqpUser' $JSON_FILE)
    echo Current amqp user is : "$current_amqpUser"
    read -p "Do you want to change the amqp user? (y/n) " change_amqpUser
    if [[ $change_amqpUser == "y" ]]; then
        read -p "Enter the amqp user: " amqpUser
    else
        amqpUser=$current_amqpUser
    fi

    # Display current value of amqp password and prompt user for changes 
    current_amqpPassword=$(jq -r --arg sourceId "$sourceId" '.[$sourceId].parameters.amqpPassword' $JSON_FILE)
    echo Current amqp password is : "$current_amqpPassword"
    read -p "Do you want to change the amqp password? (y/n) " change_amqpPassword
    if [[ $change_amqpPassword == "y" ]]; then
        read -p "Enter the amqp password: " amqpPassword
    else
        amqpPassword=$current_amqpPassword
    fi

    # Update the specified source with the provided values
    jq --arg sourceId "$sourceId" \
       --arg pipeline "$pipeline" \
       --arg rtspUrl "$rtspUrl" \
       --arg recordTo "/data/sighthound/media/output/video/$sourceId/" \
       --arg imageSaveDir "/data/sighthound/media/output/image/$sourceId/" \
       --arg amqpUser "$amqpUser" \
       --arg amqpPassword "$amqpPassword" \
       '.[$sourceId].pipeline = $pipeline | .[$sourceId].parameters.sourceId = $sourceId | .[$sourceId].parameters.VIDEO_IN = $rtspUrl | .[$sourceId].parameters.recordTo = $recordTo | .[$sourceId].parameters.imageSaveDir = $imageSaveDir | .[$sourceId].parameters.amqpUser = $amqpUser | .[$sourceId].parameters.amqpPassword = $amqpPassword' $JSON_FILE > tmp.$$.json && mv tmp.$$.json $JSON_FILE

    echo "Source edited successfully!"
}

# Display a summary of all sources when the tool is first opened
display_summary

# Main loop
while true; do
    # Prompt the user to select an option
    PS3="Select an option: "
    options=("Create a new source" "Edit an existing source" "Exit configuration tool")
    select opt in "${options[@]}"
    do
        case $opt in
            "Create a new source")
                create_source
                break
                ;;
            "Edit an existing source")
                edit_source
                break
                ;;
            "Exit configuration tool")
                exit 0
                ;;
            *) echo "Invalid option";;
        esac
    done
done

