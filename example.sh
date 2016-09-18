#!/bin/bash

if [ $# != 2 ]
then
	echo "demo: "$0" file_folder runner";
	exit 1;
fi

folder=$1;
runner=$2;

filelist=`ls ${folder}`;

for file in ${filelist}
do
	cat ${folder}/${file} |  ${runner};
done
