#!/bin/bash

# Check for folder name here
if [ $# -eq 0 ]
then
    echo "Give the folder name corresponding to the test params"
    exit 1
fi

# Create folders
param=$1
mkdir -p ./testOPs/${param}

bws=("9M" "8M" "7M" "6M" "5M" "4M" "3M")

# Run tests and evals. Save to corresponding file
for j in {0..20}
do
    for i in "${bws[@]}"
    do
        echo "Running test iteration $j for BW = $i"
        ./simple_run.sh --nocli --iperft 30 --bw "${i}" > /dev/null 2>&1
        ./evaluate.sh 1> ./testOPs/${param}/test_${j}_bw_${i}.txt
    done
done

# Play sound to denote end of script
paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga
