#!/bin/bash

if [ $# -eq 0 ]
then
    echo "Give the folder name corresponding to the test params"
    exit 1
fi

param=$1
#echo `pwd`
mkdir -p ./testOPs/${param}
#sudo rm -rf out/*

#bws=("9M" "8M" "7M" "6M" "5M" "4M" "3M" "2M")
bws=("8M")

for j in {0..1}
do
    for i in "${bws[@]}"
    do
        echo "Running test iteration $j for BW = $i"
        ./simple_run.sh --nocli --iperft 30 --bw "${i}" > /dev/null 2>&1
	./evaluate.sh 1> ./testOPs/${param}/test_${j}_bw_${i}.txt
    done
done

paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga
