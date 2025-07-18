#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

time=200
bwnet=1.5
bwhost=1000
# TODO: If you want the RTT to be 20ms what should the delay on each
# link be?  Set this value correctly.
delay=5

iperf_port=5001

for qsize in 20 100; do
    sudo mn -c
    dir=reno-q$qsize

    # TODO: Run bufferbloat.py here...
    # python3 ...
    python3 bufferbloat.py -B $bwhost -b $bwnet --delay $delay -d $dir --time $time --maxq $qsize

    # TODO: Ensure the input file names match the ones you use in
    # bufferbloat.py script.  Also ensure the plot file names match
    # the required naming convention when submitting your tarball.
    python3 plot_queue.py -f $dir/buffer.txt -o $dir/reno-buffer-q$qsize.png
    python3 plot_ping.py -f $dir/ping.txt -o $dir/reno-rtt-q$qsize.png
done
