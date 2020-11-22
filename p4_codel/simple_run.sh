# Copyright 2018-present Ralf Kundel, Jeremias Blendin, Nikolas Eller
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

argsCommand=""

if [ "$1" = "--bw" ]; then
  argsCommand="$1 $2 "
fi

if [ "$1" = "--nopcap" ] || [ "$1" = "--nocli" ]; then
  argsCommand=$1" True"
fi

if [ "$1" = "--iperft" ]; then 
  argsCommand="--iperft $2"
fi

if [ "$2" = "--nopcap" ] || [ "$2" = "--nocli" ]; then
  argsCommand=$argsCommand" "$2" True"
fi

if [ "$2" = "--iperft" ]; then 
  argsCommand=$argsCommand" --iperft "$3
fi

if [ "$2" = "--bw" ]; then
  argsCommand="$argsCommand $2 $3"
fi

if [ "$3" = "--nopcap" ] || [ "$3" = "--nocli" ]; then
  argsCommand=$argsCommand" "$3" True"
fi

if [ "$3" = "--iperft" ]; then 
  argsCommand=$argsCommand" --iperft "$4
fi

if [ "$3" = "--bw" ]; then
  argsCommand="$argsCommand $3 $4"
fi

if [ "$4" = "--nopcap" ] || [ "$4" = "--nocli" ]; then
  argsCommand=$argsCommand" "$4" True"
fi

if [ "$4" = "--bw" ]; then
  argsCommand="$argsCommand $4 $5"
fi

echo "$argsCommand"

#compile p4 file
[ -e router_compiled.json ] && sudo rm -f router_compiled.json
p4c-bm2-ss srcP4/router.p4 --std p4-16 -o router_compiled.json

sudo killall ovs-testcontroller
sudo mn -c
#start mininet environment
sudo PYTHONPATH=$PYTHONPATH:../../behavioral-model/mininet/ \
    python srcPython/toposetup.py \
    --swpath ../../behavioral-model/targets/simple_switch/simple_switch \
    -p4 \
    --json ./router_compiled.json \
    --cli ../../behavioral-model/targets/simple_switch/sswitch_CLI  \
    --cliCmd srcP4/commandsRouterSimple_r0.txt,srcP4/commandsRouterSimple_r1.txt,srcP4/commandsRouterSimple_r2.txt \
    $argsCommand
