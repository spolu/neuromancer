#!/bin/bash

EXPERIMENT=$1
TEMP=/tmp/$1

START=`date +%s`
DUMP_PERIOD=60

RUNTIME=$((`date +%s`-$START))
echo "[Update] experiment=$EXPERIMENT tempdir=$TEMP"
grep STEP $TEMP/out.log | cut -d' ' -f5 | gnuplot -p -e 'set terminal png; set output "'$TEMP'/mean.png"; plot "/dev/stdin";'
grep STEP $TEMP/out.log | cut -d' ' -f6 | gnuplot -p -e 'set terminal png; set output "'$TEMP'/min.png"; plot "/dev/stdin";'
grep STEP $TEMP/out.log | cut -d' ' -f7 | gnuplot -p -e 'set terminal png; set output "'$TEMP'/max.png"; plot "/dev/stdin";'
