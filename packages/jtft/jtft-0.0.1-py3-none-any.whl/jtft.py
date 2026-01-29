# -*- coding: utf-8 -*-

import os
import shutil
import json
from sys import argv as a

import base64

def bin_read(file_path, dirs = None):
	if dirs == None:
		try:
			with open(file_path, 'rb') as file:
				binary_data = file.read()
				base64_data = base64.b64encode(binary_data).decode('utf-8')
				return base64_data
		except FileNotFoundError:
			return "File not found"
		except Exception as e:
			return str(e)
	else:
		count = dirs[1] + 1
		ret = f'a{count}'
		os.rename(file_path,os.path.join(dirs[0], ret))
		ret = [ret, count]
		return ret

def bin_write(file_path, base64_data, dirs = None):
	if dirs == None:
		try:
			binary_data = base64.b64decode(base64_data)
			with open(file_path, 'wb') as file:
				file.write(binary_data)
			return "File successfully written"
		except Exception as e:
			return str(e)
	else:
		os.rename(os.path.join(dirs, 'a{}'.format(base64_data)), file_path)

#pip install chardet

import chardet

def is_utf8_encoding(file_path):
	try:
		with open(file_path, 'rb') as file:
			rawdata = file.read()
			result = chardet.detect(rawdata)
			if result['encoding'].lower() == 'utf-8':
				return True
			else:
				return result['encoding']
	except Exception as e:
		return None

class Counter:
	def __init__(self):
		self.__value = 0
	def gets(self):
		return self.__value
	def sets(self, data):
		self.__value = data
	def __call__(self):
		return self

def get_file(file_path, dirs = None):
	encoding = is_utf8_encoding(file_path)
	if not encoding and dirs == None:
		return [False, bin_read(file_path)]
	elif not encoding:
		dir2 = dirs
		dir2[1] = dir2[1].gets()
		ret, count = bin_read(file_path, dirs = dir2)
		dirs[1].sets(count)
		return ret
	elif isinstance(encoding, str):
		try:
			with open(file_path, 'r', encoding = encoding) as fp:
				ret = [encoding, fp.read()]
		except:
			if dirs == None:
				ret = [False, bin_read(file_path)]
			else:
				dir2 = dirs
				dir2[1] = dir2[1].gets()
				ret, count = bin_read(file_path, dirs = dir2)
				dirs[1].sets(count)
		return ret
	else:
		with open(file_path, 'r', encoding = 'utf-8') as fp:
			return fp.read()

def set_file(file_path, files, dirs = None):
	if isinstance(files, list):
		if files[0]:
			with open(file_path, 'w', encoding = files[0]) as fp:
				fp.write(files[1])
		elif dirs == None:bin_write(file_path, files[1])
		else:
			bin_write(file_path, files, dirs = dirs)
	else:
		with open(file_path, 'w', encoding = "utf-8") as fp:
				fp.write(files)

def jtft_to_directory(jtft_file, directory_path, dirs = False):
	# *.jtft 파일을 디렉토리로 변환
	with open(jtft_file, 'r', encoding = 'utf-8') as jtft:
		data = json.load(jtft)
	
	os.makedirs(directory_path, exist_ok=True)
	
	for file_name, file_content in data.items():
		set_file(file_name, file_content)

def directory_to_jtft(jtft_file, directory_path, dirs = False):
	# 디렉토리를 *.jtft 파일로 변환
	data = {}
	
	for root, _, files in os.walk(directory_path):
		for file_name in files:
			file_path = os.path.join(root, file_name)
			data[file_name] = get_file(file_path)
	
	with open(jtft_file, 'w', encoding = 'utf-8') as jtft:
		json.dump(data, jtft)

def unjdir(project2, dirs):
	project = project2 + 'copy'
	shutil.copytree(project2, project)
	project_join = lambda x : os.path.join(project, x)
	dirname, coredir, corefile = project_join('b'), project_join('a'), project_join('a.jtft')
	os.rename(coredir, corefile)
	jtft_to_directory(corefile, coredir, dirs = dirname)
	os.remove(corefile)
	shutil.copyfile(coredir, dirs)
	shutil.rmtree(project)

def jdir(project, dirs):
	os.mkdir(project)
	project_join = lambda x : os.path.join(project, x)
	dirname, coredir, corefile = project_join('b'), project_join('a'), project_join('a.jtft')
	os.mkdir(dirname)
	shutil.copytree(dirs, coredir)
	directory_to_jtft(corefile, coredir, dirs = dirname)
	shutil.rmtree(coredir)
	os.rename(corefile, coredir)

def main():
	if len(a) > 3:
		match = a[1]
		if 1:
			if match == "unjtft":
				jtft_to_directory(a[2], a[3])
			elif match == "jtft":
				directory_to_jtft(a[2], a[3])
			elif match == "unjdir":
				jtft_to_directory(a[2], a[3])
			elif match == "jdir":
				directory_to_jtft(a[2], a[3])
			else:
				print("Error : switch must be unjtft or jtft or jdir or unjdir")
	else:
		for i in ["switch : ","jtft project : ","dir : "]:
			a.append(input(i))
		main()

if __name__ == "__main__": main()
