#!/bin/bash

rm -rf IC3ref

git clone -b invarcheck https://github.com/makaimann/IC3ref.git
cd IC3ref/

git clone https://github.com/niklasso/minisat.git
cd minisat
make
cd ../

wget http://fmv.jku.at/aiger/aiger-1.9.4.tar.gz
tar -xzvf aiger-1.9.4.tar.gz
mv aiger-1.9.4/ aiger/
make
