#!/usr/bin/env python
#-*- coding: utf-8 -*-

import re
import math
import sys

###  预处理——加载词典  ###
wastAttrSet = set()  # 垃圾属性表
fileReadWastattr = open("filter_attr.txt")
for wastword in fileReadWastattr.readlines():
	wastword = wastword.strip()
	wastAttrSet.add(wastword)
fileReadWastattr.close()

prickleArry = []  #  计量单位表
fileReadPrickle = open("计量单位简写.txt")
for prickleword in fileReadPrickle.readlines():
	prickleword = prickleword.strip()
	prickleArry.append(prickleword)
fileReadPrickle.close()

antonymDict = {}  #  反义词表
fileReadAntonym = open("反义字表.txt")
for antonymword in fileReadAntonym.readlines():
	tempArry = antonymword.strip().split("\t")
	for i in range(len(tempArry)-1):
		word1 = tempArry[i].decode('utf-8')
		word2 = tempArry[i+1].decode('utf-8')
		for j in range(i+2, len(tempArry)):
			if tempArry[j] == "":
				continue
			word2 = word2 + "\t" + tempArry[j].decode('utf-8')
		if word1 in antonymDict:
			wordStr = antonymDict[word1]
			wordStr = wordStr + "\t" + word2
			antonymDict[word1] = wordStr
		else:
			antonymDict[word1] = word2

fileReadAntonym.close()
##############################

###  去掉垃圾属性  ###
def ClearWastattr(cid_attr_valArry):
	new_cid_attr_valArry = []
	wastWordArry = ["是否", "套餐", "编号"]  # 属性中不应该包含的垃圾词

	for i in range(len(cid_attr_valArry)):
		cid_attr_val = cid_attr_valArry[i]

		tempArry = cid_attr_val.strip().split("\t")
		if len(tempArry) < 3:
			continue
		cid = tempArry[0]
		attr = tempArry[1]
		val = tempArry[2]
		#  带有垃圾属性的过滤
		if attr in wastAttrSet:
			continue
		judge = 1
		for j in range(len(wastWordArry)):
			wastword = wastWordArry[j]
			if attr.find(wastword) != -1:
				judge = 0
				break
		if judge == 0:
			continue
		#
		#  属性和属性值变小写
#		attr = attr.lower()
		val = val.lower()
		#  数字->NUM
		numArry = re.findall(r"\d+\.?\d*", val)
		for j in range(len(numArry)):
			val = val.replace(numArry[j], "NUM")
		val = val.replace("NUM.NUM", "NUM")
		numArry = re.findall(r"\d+\.NUM", val)
		for j in range(len(numArry)):
			val = val.replace(numArry[j], "NUM")
		numArry = re.findall(r"NUM\.\d+", val)
		for j in range(len(numArry)):
			val = val.replace(numArry[j], "NUM")
		#  计量单位简写
		for i in range(len(prickleArry)):
			tempArry = prickleArry[i].split("\t")
			oriPrickle = tempArry[0]
			simplePrickle = tempArry[1]
			val = val.replace(oriPrickle, simplePrickle)

		#  将没被过滤的重新组合，放入new_cid_attr_valArry中
		new_cid_attr_val = cid + "\t" + attr + "\t" + val
		new_cid_attr_valArry.append(new_cid_attr_val)

	return new_cid_attr_valArry
####################################

########################  相似度的计算模块  ###################################

###  每个属性下的属性值做相似度  ###
def Val_Sim(valStr1, valStr2):
	temp_valList1 = valStr1.split("|")
	temp_valList2 = valStr2.split("|")
	# 过滤属性值
	valList1 = []
	valList2 = []
	filter_valSet = set(['other', 'NUM', '其他', '其他/other', 'NUM-NUM', ''])  # 属性值是set中的值时，不要
	for i in range(len(temp_valList1)):
		val = temp_valList1[i]
		if val in filter_valSet:
			continue
		else:
			valList1.append(val)
	if len(valList1) == 0:
		return 0.0

	for i in range(len(temp_valList2)):
		val = temp_valList2[i]
		if val in filter_valSet:
			continue
		else:
			valList2.append(val)
	if len(valList2) == 0:
		return 0.0
	#
	# 相似度
	valDict1 = {}
	valDict2 = {}
	total_valDict = {}
	# 放入属性1下的属性值
	for i in range(len(valList1)):
		val = valList1[i]
		if val == "":
			continue
		if val in valDict1:
			valDict1[val] = valDict1[val] + 1
		else:
			valDict1[val] = 1
		total_valDict[val] = 1
	# 放入属性2下的属性值
	for i in range(len(valList2)):
		val = valList2[i]
		if val == "":
			continue
		if val in valDict2:
			valDict2[val] = valDict2[val] + 1
		else:
			valDict2[val] = 1
		total_valDict[val] = 1
	'''
	# 计算cos值
	# 计算分子
	numer = 0
	for val in total_valDict:
		if (val in valDict1) and (val in valDict2):
			numer = numer + valDict1[val] * valDict2[val]
	# 计算分母
	denom = 0.0
	denom1 = 0
	denom2 = 0
	for val in valDict1:
		denom1 = denom1 + valDict1[val] * valDict1[val]
	for val in valDict2:
		denom2 = denom2 + valDict2[val] * valDict2[val]
	denom = math.sqrt(denom1) * math.sqrt(denom2)

	# 返回cos值
	if int(denom) == 0:
		return 0
	else:
		return float(numer) / denom
	'''
	# 计算重合度
	val_contactNum = 0
	min_leveDis = 0.7  # 编辑距离大于该值时可以认定两个属性值相同
	if len(valDict1) < len(valDict2):
		for val1 in valDict1:
			for val2 in valDict2:
				leve_dis = Levenshtein_Distance(val1, val2)
				if leve_dis >= min_leveDis:
					val_contactNum = val_contactNum + 1
					break
	else:
		for val2 in valDict2:
			for val1 in valDict1:
				leve_dis = Levenshtein_Distance(val1, val2)
				if leve_dis >= min_leveDis:
					val_contactNum = val_contactNum + 1
					break

	val_contactRatio = float(val_contactNum) / min(len(valDict1), len(valDict2))
	
	return val_contactRatio
	
###  属性之间做相似度（编辑距离） ###
def Levenshtein_Distance(attrStr1, attrStr2):
	if (len(attrStr1) == 0) and (len(attrStr2) == 0):
		return 0.0

	attrArry1 = []
	attrArry2 = []
	temp_attrStr1 = attrStr1.decode('utf-8')
	temp_attrStr2 = attrStr2.decode('utf-8')
	tempStr = "NUM"
	for s in temp_attrStr1:
		if s == "N" or s == "U":
			continue
		if s == "M":
			attrArry1.append(tempStr)
		else:
			attrArry1.append(s)
	for s in temp_attrStr2:
		if s == "N" or s == "U":
			continue
		if s == "M":
			attrArry2.append(tempStr)
		else:
			attrArry2.append(s)

	for i in range(len(attrArry1)):
		print attrArry1[i]
	print "-------------"
	for i in range(len(attrArry2)):
		print attrArry2[i]
	len_str1 = len(attrArry1) + 1
	len_str2 = len(attrArry2) + 1

	matrix = [0 for n in range(len_str1 * len_str2)]

	for i in range(len_str1):
		matrix[i] = i

	i = 0
	for j in range(0, len(matrix), len_str1):
		if j % len_str1 == 0:
			matrix[j] = i
			i = i + 1 
	
	for i in range(1, len_str1):
		for j in range(1, len_str2):
			if attrArry1[i-1] == attrArry2[j-1]:
				cost = 0
			else:
				cost = 1
			matrix[j*len_str1+i] = min(matrix[(j-1)*len_str1+i]+1, 
									matrix[j*len_str1+(i-1)]+1,
									matrix[(j-1)*len_str1+(i-1)]+cost)

	maxLen = max(len_str1, len_str2) - 1
	print "len_str1:", len_str1
	print "len_str2:", len_str2
	levedisSim = float(maxLen - matrix[-1]) / maxLen  # 概率值

	return levedisSim

###  判断两个属性是否包含反义字  ###
def isAntonymInAttr(attrStr1, attrStr2):
	temp_attrStr1 = attrStr1.decode('utf-8')
	temp_attrStr2 = attrStr2.decode('utf-8')
	#  对第一个属性遍历每个字
	for word1 in temp_attrStr1:
		#  一个属性中已经包含了一个反义字
		if word1 in antonymDict:
			tempArry = antonymDict[word1].split("\t")
			for tempword in tempArry:
				antonymWord1 = word1 + tempword  # 判断是否是两个反义字的组合
				antonymWord2 = tempword + word1  # 判断是否是两个反义字的组合
				#  两个属性有一个满足是包含两个反义字的组合就可以略过
				if (antonymWord1 in temp_attrStr1) or (antonymWord2 in temp_attrStr1):
					break
				if (antonymWord1 in temp_attrStr2) or (antonymWord2 in temp_attrStr2):
					break
				#  判断是否另一个反义字在另一个属性中
				if tempword in temp_attrStr2:
					return True

	#  对第二个属性遍历每个字
	for word2 in temp_attrStr2:
		#  一个属性中已经包含一个反义字
		if word2 in antonymDict:
			tempArry = antonymDict[word2].split("\t")
			for tempword in tempArry:
				antonymWord1 = word2 + tempword  # 判断是否是两个反义字的组合
				antonymWord2 = tempword + word2  # 判断是否是两个反义字的组合
				#  两个属性有一个满足是包含两个反义字的组合就可以略过
				if (antonymWord1 in temp_attrStr1) or (antonymWord2 in temp_attrStr1):
					break
				if (antonymWord1 in temp_attrStr2) or (antonymWord2 in temp_attrStr2):
					break
				#  判断是否另一个反义字在另一个属性中
				if tempword in temp_attrStr1:
					return True

	return False

###  判断两个属性是否符合条件  ###
def isAttrRight(attrStr1, attrStr2):
	#  判断两个属性是否都包含否定字或都不包含否定字
	negwordArry = ["不", "无"]
	boolAttr1 = True
	boolAttr2 = True
	for i in range(len(negwordArry)):
		negword = negwordArry[i]
		if negword in attrStr1:
			boolAttr1 = not boolAttr1
		if negword in attrStr2:
			boolAttr2 = not boolAttr2
	if boolAttr1 ^ boolAttr2:
		return False

	# 判断两个属性是否包含反义字
	if isAntonymInAttr(attrStr1, attrStr2):
		return False

	return True
###  相似度计算  ###
def CalSim(cidattrvalStr1, cidattrvalStr2):
	tempArry1 = cidattrvalStr1.strip().split("\t")
	tempArry2 = cidattrvalStr2.strip().split("\t")
	if len(tempArry1) < 3 or len(tempArry2) < 3:
		return 0.0
	attr1 = tempArry1[1]
	attr2 = tempArry2[1]
	val1 = tempArry1[2]
	val2 = tempArry2[2]

	# 计算相似度   #######
	# 属性的计算
	if not isAttrRight(attr1, attr2):
		return 0.0
	#  判断一个属性是否包含另一个属性
#	if (attr1 in attr2) or (attr2 in attr1):
#		attrSim = 0.7
#	else:
	min_attrSim = 0.55  # 属性相似度的最小阙值
	attr1 = attr1.lower()
	attr2 = attr2.lower()
	attrSim = Levenshtein_Distance(attr1, attr2)  # 属性相似度
	print "attr1:", attr1
	print "attr2:", attr2
	print "attrSim:", attrSim
	if attrSim < min_attrSim:  # 先判断属性是否符合最小相似度，不符合就不需要计算属性值的相似度
		return 0.0
	#############
	
	# 属性值的计算
	min_valSim = 0.4  # 属性值相似度(重合度)的最小阙值
	valSim = Val_Sim(val1, val2)
	print "val1:", val1
	print "val2:", val2
	print "valSim:", valSim
	if valSim < min_valSim:  # 属性值不满足最小阙值，不考虑两个属性之间的相似度
		return 0.0
	##############

	valSimRate = 0.5  # 属性值相似度占比
	totalSim = valSimRate * valSim + (1-valSimRate) * attrSim  # 总相似度
	print "totalSim:", totalSim

	return totalSim


###  对打分矩阵进行整合并对分值做平均  ########
def AverMatrixScore(matrix, attrList, maxRate):
	averscoreList = []  # 每个属性与其他属性的相似度大于maxRate的加和平均值
	for i in range(len(matrix)):
		score = 0.0
		count = 0
		for j in range(len(matrix)):
			if matrix[i][j] >= maxRate:
				score = score + matrix[i][j]
				count = count + 1
		if count == 0:
			averscoreList.append(0.0)
		else:
			averscoreList.append(float(score) / count)

	deleteSet = set()  # 存放已经聚合在一起的属性
	attr_scoreDict = {}  # 聚合的属性和相应的得分平均值
	for row in range(len(matrix)-1):
		if row in deleteSet:
			continue
		deleteSet.add(row)
		classifyStr = ""
		attrDict = {}
		attrDict[row] = 1
		for col in range(row+1, len(matrix)):
			if (matrix[row][col] >= maxRate) and (col not in deleteSet):
				attrDict[col] = 1
				deleteSet.add(col)
		while True:
			judge = 1
			for attr in attrDict.keys():
				if attr == row:
					continue
				for col in range(attr+1, len(matrix)):
					if (matrix[attr][col] >= maxRate) and (col not in deleteSet):
						if col not in attrDict:
							attrDict[col] = 1
							deleteSet.add(col)
							judge = 0
			if judge == 1:
				break

		if len(attrDict) < 2:
			continue
		score = 0.0
		count = 0
		for attr in attrDict:
			classifyStr = classifyStr + attrList[attr] + " "
			count = count + 1
			score = score + averscoreList[attr]

		attr_scoreDict[classifyStr] = float(score) / count

		if len(deleteSet) == len(matrix):
			break

	return attr_scoreDict

###  对聚合好的属性的分值进行排序  ###
def AttrscoreSorted(attr_scoreDict):
	classifyResult = []
	if len(attr_scoreDict) == 0:
		return classifyResult
	while True:
		maxScore = -100000
		maxAttr = ""
		if len(attr_scoreDict) == 1:
			for attr_score in attr_scoreDict:
				classifyResult.append(attr_score + "\t" + str(attr_scoreDict[attr_score]))
			break
		for attr_score in attr_scoreDict:
			if attr_scoreDict[attr_score] > maxScore:
				maxScore = attr_scoreDict[attr_score]
				maxAttr = attr_score
		classifyResult.append(maxAttr + "\t" + str(maxScore))
		attr_scoreDict.pop(maxAttr)

	return classifyResult

###  对每个cid下的属性做相似度，并进行归类  ###
def AttrClassify(filter_cid_attr_valArry):
	#  相似度矩阵
	matrixLen = len(filter_cid_attr_valArry)
	matrix = [[] for i in range(matrixLen)]
	for i in range(matrixLen):
		for j in range(matrixLen):
			matrix[i].append(0)

	for i in range(matrixLen):
		for j in range(i+1, matrixLen):
			cidattrvalStr1 = filter_cid_attr_valArry[i]
			cidattrvalStr2 = filter_cid_attr_valArry[j]
			sim = CalSim(cidattrvalStr1, cidattrvalStr2)
			matrix[i][j] = sim
			matrix[j][i] = sim

	# 获得属性列表
	attrList = []
	for i in range(matrixLen):
		tempArry = filter_cid_attr_valArry[i].strip().split("\t")
		attr = tempArry[1]
		attrList.append(attr)
	###
	# 存放相似的属性
	maxRate = 0.6  # 相似度大于maxRate，证明两个属性可以归类
	
	attr_scoreDict = AverMatrixScore(matrix, attrList, maxRate)
	classifyResult = AttrscoreSorted(attr_scoreDict)
	
	'''
	attr_classifyArry = [[] for i in range(matrixLen)]
	for i in range(matrixLen):
		attr_classifyArry[i].append(attrList[i])
		for j in range(matrixLen):
			if matrix[i][j] >= maxRate:
				attr_classifyArry[i].append(attrList[j])
	return attr_classifyArry
	'''	

	return classifyResult
####################################################

###  整理归一化结果  ###
def ReArrangeResult(attrclassifyMatrix):
	# 将有归类的属性进行整理
	attrclassify = {}
	for i in range(len(attrclassifyMatrix)):
		if len(attrclassifyMatrix[i]) > 1:
			attrHead = attrclassifyMatrix[i][0]
			attrclassify[attrHead] = set()
			for j in range(1, len(attrclassifyMatrix[i])):
				attrTail = attrclassifyMatrix[i][j]
				attrclassify[attrHead].add(attrTail)
	# 将有联系的属性归为一类
	classifyResult = []
	while True:
		keyList = attrclassify.keys()
		if len(keyList) == 0:
			break
		key = keyList[0]
		classifyResult.append({})
		local = len(classifyResult) - 1
		# 第一步，将key中的所以属性（包括key）放入字典中
		classifyResult[local][key] = 1
		for val in attrclassify[key]:
			classifyResult[local][val] = 1
		attrclassify.pop(key)
		# 第二步，对字典中所有的属性进行整合
		while True:
			judge = 1
			for val in classifyResult[local].keys():
				if val not in attrclassify:
					continue
				judge = 0
				for tempVal in attrclassify[val]:
					classifyResult[local][tempVal] = 1
				attrclassify.pop(val)
			if judge == 1:
				break

	return classifyResult
#############################

###  属性归一化  ###
def AttrUnifor():
	fileReadAttrName = "/Users/fuyitao/Desktop/PythonTrain/attr_val_unification/Random/fileList/part-00119"
	fileWriteAttrName = fileReadAttrName + "Result_New_New"
	fileWriteRecallName = fileReadAttrName + "_召回结果"
	fileReadAttr = open(fileReadAttrName)
	fileWriteAttr = open(fileWriteAttrName, 'w')
	fileWriteRecall = open(fileWriteRecallName, 'a')

	cid_attr_valArry = []
	attr_lineDict = {}  # 属性对应的line
	title = ""
	count = 1
	classifyNum = 0
	for line in fileReadAttr.readlines():
		line = line.strip()
		if line == "-------------------":
			filter_cid_attr_valArry = ClearWastattr(cid_attr_valArry)
			### 每个cid下的属性归类
#			attrclassifyMatrix = AttrClassify(filter_cid_attr_valArry)
#			classifyResult = ReArrangeResult(attrclassifyMatrix)
			classifyResult = AttrClassify(filter_cid_attr_valArry)
			###

			if len(classifyResult) > 0:
				fileWriteAttr.write(title + "\n")
				### 写入归类结果
				fileWriteAttr.write("分类结果:\n")
				for i in range(len(classifyResult)):
					classifyNum = classifyNum + 1

					attr_scoreArry = classifyResult[i].split("\t")
					attrStr = attr_scoreArry[0]
					score = attr_scoreArry[1]
					fileWriteAttr.write("score: " + score + "\n")
					fileWriteAttr.write(attrStr + "\n")
					
					attrArry = attrStr.split(" ")
					for i in range(len(attrArry)):
						attr_word = attrArry[i]
						if attr_word == "":
							continue
						attr_line = attr_lineDict[attr_word]
						fileWriteAttr.write(attr_line + "\n")

					'''		
					temp = ""
					for attr_word in classifyResult[i]:
						temp = temp + attr_word + " "
					fileWriteAttr.write(temp + "\n")
					for attr_word in classifyResult[i]:
						attr_line = attr_lineDict[attr_word]
						fileWriteAttr.write(attr_line + "\n")
					'''
					fileWriteAttr.write(str(classifyNum) + "\n")
					fileWriteAttr.write("\n")
				fileWriteAttr.write("-------------------\n")

			###  计数
			print "完成", count, "个cid"
			count = count + 1
			###

			cid_attr_valArry = []
			attr_lineDict = {}
			title = ""
		elif re.match("--\d+--", line) != None:
			title = line
		else:
			tempArry = line.strip().split("\t")
			if len(tempArry) < 3:
				continue
			attr = tempArry[1]
			val = tempArry[2]
			valList = val.split("|")
			if len(valList) > 20:
				continue
			cid_attr_valArry.append(line)
#			attr = attr.lower()
			attr_lineDict[attr] = line
	
	fileWriteRecall.write(str(classifyNum) + "\n")

	fileReadAttr.close()
	fileWriteAttr.close()
	fileWriteRecall.close()
######################################

###  主函数  ###
def main():
	AttrUnifor()

if __name__ == '__main__':
#	main()
	'''
	cidattrvalStr1 = "cid1\t容量\t|编号|属性|属性值|类别"
	cidattrvalStr2 = "cid2\t商品系列\t|类别|其他|小样"
	print CalSim(cidattrvalStr1, cidattrvalStr2)

	attrStr1 = "容量型123"
	attrStr2 = "商品类型abc"
	print Levenshtein_Distance(attrStr1, attrStr2)
	valStr1 = "NUMmm-NUMmm|other|属性值|NUM|商品类型"
	valStr2 = "|其他|NUM-"
	print 'valStr1:', valStr1
	print 'valStr2:', valStr2
	print Val_Sim(valStr1, valStr2)
	'''
	'''
	print "--------------------------------"
	filter_matrix = ["cid1\t容量\t|编号|属性|属性值|类别|编码|编程|编译|边|变|便便比", 
					"cid2\t商品系列\t|类别|其他|小样",
					"cid3\t商品\t|类别|其他|",
					"cid4\t容积\t|类别|其他|编号"]

	for i in range(len(filter_matrix)):
		cidattrvalStr1 = filter_matrix[i]
		tempArry1 = cidattrvalStr1.strip().split("\t")
		cid1 = tempArry1[0]
		attr1 = tempArry1[1]
		val1 = tempArry1[2]
		cosVal = []
		leveVal = []
		print cidattrvalStr1, ":"
		temp = ""
		for j in range(i+1, len(filter_matrix)):
			cidattrvalStr2 = filter_matrix[j]
			tempArry2 = cidattrvalStr2.strip().split("\t")
			cid2 = tempArry2[0]
			attr2 = tempArry2[1]
			val2 = tempArry2[2]
			temp = temp + " " + str(Val_Sim(val1, val2))
			cosVal.append(Val_Sim(val1, val2))
		print "contact:", temp
		temp = ""
		for j in range(i+1, len(filter_matrix)):
			cidattrvalStr2 = filter_matrix[j]
			tempArry2 = cidattrvalStr2.strip().split("\t")
			cid2 = tempArry2[0]
			attr2 = tempArry2[1]
			val2 = tempArry2[2]
			temp = temp + " " + str(Levenshtein_Distance(attr1, attr2))
			leveVal.append(Levenshtein_Distance(attr1, attr2))
		print "levedis:", temp
		temp = ""
		for i in range(len(cosVal)):
			temp = temp + " " + str((cosVal[i]+leveVal[i])/2) 
		print "totalsim:", temp
	print "---------------------------------------"
	matrix = AttrClassify(filter_matrix)
	for i in range(len(matrix)):
		temp = ""
		for j in range(len(matrix[i])):
			temp = temp + " " + str(matrix[i][j])
		print temp
	'''
	'''
	attrclassifyMatrix = [[] for i in range(11)]
	attrclassifyMatrix[0].append("情侣手链1对")	
	attrclassifyMatrix[0].append("情侣项链1对")
	attrclassifyMatrix[1].append("手围14厘米")
	attrclassifyMatrix[1].append("手围16厘米")
	attrclassifyMatrix[1].append("手围18厘米")
	attrclassifyMatrix[2].append("手围16厘米")
	attrclassifyMatrix[2].append("手围14厘米")
	attrclassifyMatrix[2].append("手围18厘米")
	attrclassifyMatrix[3].append("情侣项链1对")
	attrclassifyMatrix[3].append("情侣手链1对")
	attrclassifyMatrix[4].append("手链长度")
	attrclassifyMatrix[4].append("戒指/手链长度")
	attrclassifyMatrix[4].append("链子长度")
	attrclassifyMatrix[4].append("项链长度")
	attrclassifyMatrix[5].append("戒指/手链长度")
	attrclassifyMatrix[5].append("手链长度")
	attrclassifyMatrix[5].append("链子长度")
	attrclassifyMatrix[5].append("项链长度")
	attrclassifyMatrix[6].append("链子长度")
	attrclassifyMatrix[6].append("单圈")
	attrclassifyMatrix[6].append("双圈")
	attrclassifyMatrix[6].append("戒指/手链长度")
	attrclassifyMatrix[6].append("手链长度")
	attrclassifyMatrix[6].append("项链长度")
	attrclassifyMatrix[7].append("项链长度")
	attrclassifyMatrix[7].append("单圈")
	attrclassifyMatrix[7].append("双圈")
	attrclassifyMatrix[7].append("戒指/手链长度")
	attrclassifyMatrix[7].append("手链长度")
	attrclassifyMatrix[7].append("链子长度")
	attrclassifyMatrix[8].append("手围18厘米")
	attrclassifyMatrix[8].append("手围14厘米")
	attrclassifyMatrix[8].append("手围16厘米")
	attrclassifyMatrix[9].append("单圈")
	attrclassifyMatrix[9].append("双圈")
	attrclassifyMatrix[9].append("链子长度")
	attrclassifyMatrix[9].append("项链长度")
	attrclassifyMatrix[10].append("双圈")
	attrclassifyMatrix[10].append("单圈")
	attrclassifyMatrix[10].append("链子长度")
	attrclassifyMatrix[10].append("项链长度")
	
	for i in range(len(attrclassifyMatrix)):
		temp = attrclassifyMatrix[i][0] + ":"
		for j in range(1, len(attrclassifyMatrix[i])):
			temp = temp + " " + attrclassifyMatrix[i][j]
		print temp
	classifyResult = ReArrangeResult(attrclassifyMatrix)

	print "---------------------------------"
	for i in range(len(classifyResult)):
		temp = ""
		for word in classifyResult[i]:
			temp = temp + word + " "
		print temp
	'''
	'''
	cid_attr_valArry = ["50011043	宝贝尺寸	|8.5cm*5cm|7.5cm*5cm|9cm*5cm|9cm*6cm|6cm|7cm*4cm|8cm*5cm|",
					"50011043	直径	|0.4cm|7.5cm|6.5m|7cm|8cm|6.5cm|5.5cm|4.5cm|3毫米|5.8cm|5.8",
					"50011043	孔直径	|3毫米",
					"0014571	千斤顶的吨位	|2吨|2吨-3吨",
					"50021348	重量	|约142千克|142克|约180千克|145克|180克",
					"50006478	跨度	|30-90厘米可调"]
	new_cid_attr_valArry = ClearWastattr(cid_attr_valArry)
	for i in range(len(cid_attr_valArry)):
		print "cid:", cid_attr_valArry[i]
		print "new_cid:", new_cid_attr_valArry[i]
		p
		print "--------------------------------------"
	'''
	'''
	cid_attr_valArry = ["50015053	温度范围	|5-35℃|-30摄氏度至+50摄氏度|-20-50℃|99|0∼40℃，测量精度：±1℃",
						"50015053	测量温度范围	|5-35",
						"50015053	测量湿度范围	|20-100%",
						"50015053	湿度范围	|20%-100%RH|0%-100%|99|20%-90%Rh"]
	filter_cid_attr_valArry = ClearWastattr(cid_attr_valArry)
	classifyResult = AttrClassify(filter_cid_attr_valArry)
	for i in range(len(classifyResult)):
		print classifyResult[i]
	'''
	print Levenshtein_Distance("NUM-3NUM", "NUM-NUM%")
	'''
	attrStr1 = "无结果"
	attrStr2 = "不火龙果"
	print isAttrRight(attrStr1, attrStr2)
	'''
	'''
	matrix = [[0, 0.5, 0.5, 0.8, 0.5], 
			  [0.5, 0, 0.6, 0.5, 0.3],
			  [0.5, 0.6, 0, 0.4, 0.6],
			  [0.8, 0.5, 0.4, 0, 0.7],
			  [0.5, 0.3, 0.6, 0.7, 0]]
	attrList = ["电容", "重量", "跨度", "直径", "宝贝"]
	maxRate = 0.6
	attr_scoreDict = AverMatrixScore(matrix, attrList, maxRate)
	for attr_score in attr_scoreDict:
		print attr_score, attr_scoreDict[attr_score]
	print "----------------------------"
	classifyResult = AttrscoreSorted(attr_scoreDict)
	for i in range(len(classifyResult)):
		print classifyResult[i]
	'''
