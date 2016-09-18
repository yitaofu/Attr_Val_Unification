#!/usr/bin/env python
#-*- coding:utf-8 -*-

fileRead = open("modifyResult_new_new_delete")
fileWrite = open("guiyiResult", 'w')

cid_attrDict = {}
for line in fileRead.readlines():
	if line.find("result:") == 0:
		tempArry = line.strip().split("result:")
		resultArry = tempArry[1].split("\t")
		if len(resultArry) != 3:
			continue
			print tempArry[1]

		cid = resultArry[0]
		attrResult = resultArry[1]
		attrDict = resultArry[2]

		attrStr = attrResult + "\t" + attrDict
		if cid in cid_attrDict:
			cid_attrDict[cid].append(attrStr)
		else:
			cid_attrDict[cid] = []
			cid_attrDict[cid].append(attrStr)

for cid in cid_attrDict:
	for i in range(len(cid_attrDict[cid])):
		result = cid + "\t" + cid_attrDict[cid][i]
		fileWrite.write(result + "\n")

fileRead.close()
fileWrite.close()
