#!/bin/bash

REDIS_VERSION=5.0.5
REDIS_DIR=redis-${REDIS_VERSION}
REDIS_ARCHIVE=${REDIS_DIR}.tar.gz
REDIS_URL=http://download.redis.io/releases/${REDIS_ARCHIVE}

if [[ $# -gt 0 ]]
then
	OBJDIR=$1
else
	OBJDIR=obj
fi

mkdir -p $OBJDIR
cd $OBJDIR

if [[ ! -d "${OBJDIR}/redis-${REDIS_VERSION}" ]]
then
	echo retrievinug ${REDIS_DIR}...
	wget ${REDIS_URL}

	echo extracting ${REDIS_ARCHIVE}...
	tar xf ${REDIS_ARCHIVE}
fi

echo building ${REDIS_DIR}...
make -C ${REDIS_DIR}

echo linking redis-cli...
ln -s -f  ${REDIS_DIR}/src/redis-cli

echo linking redis-server...
ln -s -f ${REDIS_DIR}/src/redis-server

echo linking redis-benchmark...
ln -s -f ${REDIS_DIR}/src/redis-benchmark
