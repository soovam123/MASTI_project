#!/bin/bash

#echo `pwd`
mkdir -p ./testOPs 
# rm -rf out/*

bws=("16m" "14m" "12m" "10m" "8m" "6m")

for i in "${bws[@]}"
do
    echo "Running test for BW = $i"
    ./simple_run.sh --nocli --iperft 50 --bw "${i}" > /dev/null 2>&1
    ./evaluate.sh > ./testOPs/test_bw_${i}.txt 2>&1
done
