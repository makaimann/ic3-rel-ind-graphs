#!/bin/bash

TO=3600

for aig in `ls ./hwmcc17/*`; do
    rm -f inv.cnf trans.cnf
    filename=$(basename -- $aig)
    filename="${filename%.*}"
    echo "Running IC3Ref on $aig"
    res=`timeout $TO ./IC3 -v --trans=trans.cnf --inv=inv.cnf < $aig | tail -c 2`
    if [ -z "${res// }" ]; then
        echo "timed out"
    elif [ "$res" -eq 0 ]; then
        echo "Property was proven within the timeout, generating graph..."
        ./gen_graph.py -t trans.cnf -i inv.cnf -ip inv-primed.cnf -o "$filename" --pickle
    elif [ "$res" -eq 1 ]; then
        echo "Property doesn't hold -- aborting"
    else
        echo "Unhandled case"
    fi
done
