#!/bin/bash

#echo `pwd`
mkdir -p ./testOPs 
#sudo rm -rf out/*

bws=("16M" "14M" "12M" "10M" "8M" "6M" "4M" "2M")

for i in "${bws[@]}"
do
    echo "Running test for BW = $i"
    ./simple_run.sh --nocli --iperft 10 --bw "${i}" > /dev/null 2>&1
    ./evaluate.sh > ./testOPs/test_bw_${i}.txt 2>&1
done
