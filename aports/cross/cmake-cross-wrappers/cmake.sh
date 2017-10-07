#!/bin/sh
if [ "z$1" = "z-E" ]
then
	exec /usr/bin/cmake $@
fi
exec /usr/bin/cmake -DCMAKE_TOOLCHAIN_FILE="$(dirname $0)/toolchain.cmake" $@
