#!/usr/bin/python3
import sys
import re
import json
import pprint


my_file = open(sys.argv[1], 'r')
data = my_file.readlines()
outjson = []
val ={}
for line in data:
    out=line.split(":")
    if(len(out)==3):
      val["line"]=out[1]
      val["data"]=out[2]
      outjson.append(val)
      val={}

print(json.dumps(outjson))

