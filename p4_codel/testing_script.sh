#!/bin/bash

# Check for folder name here
if [ $# -eq 0 ]
then
    echo "Give the folder name corresponding to the test params"
    exit 1
fi

for x in {1..12}
do
	# Move the simple_router_x to ./srcP4/simple_router.p4
	p4_file="simple_router_${x}.p4"
	# /home/abhi/Documents/MASTI_project/p4_codel/srcP4/simple_router.p4
	cp ~/${p4_file} ./srcP4/simple_router.p4

	combi=("20_70" "20_90" "20_110" "20_120" "40_90" "40_110" "60_70" "60_90" "60_110" "80_90" "80_110" "100_110")

	# Create folder
	param="${1}_${combi[$(($x-1))]}"
	mkdir -p ./testOPs/${param}

	bws=("9M" "8M" "7M" "6M" "5M" "4M" "3M")

	# Run tests and evals. Save to corresponding file
	for j in {0..19}
	do
	    	for i in "${bws[@]}"
	    	do
			echo "Running test iteration $j for BW = $i"
			./simple_run.sh --nocli --iperft 30 --bw "${i}" > /dev/null 2>&1
			./evaluate.sh 1> ./testOPs/${param}/test_${j}_bw_${i}.txt
	    	done
	done
done

# Play sound to denote end of script
paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga
