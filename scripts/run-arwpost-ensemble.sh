#!/usr/bin/env bash 

DIR=$(pwd)
echo $DIR
for filename in $DIR/wrfda/*; do
    sh $BIN_DIR/run-arwpost.sh $filename "$DIR/wrfda/ensemble-$(basename $filename)"
done
