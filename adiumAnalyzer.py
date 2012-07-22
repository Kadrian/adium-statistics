#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError
import sys, os, operator

# inizialize logging
import logging
logger = logging.getLogger('adiumAnalyzer')
hdlr = logging.FileHandler('errors.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.WARNING)

id = 0

def extractMessage(node):
    while node.hasChildNodes():
        node = node.firstChild
    return node.data 

def extractSender(node):
    alias = node.getAttribute('alias')
    return alias

def parseFile(content, filename):
    """append (id, sender, message) to content and return it again"""
    global id
    # parse file
    f = open(filename, 'r')
    dom = None
    try:
        dom = parse(f)
    except ExpatError:
        print "Warning: Unparsable file, see log file for details"
        logger.warn("Could not parse file: " + filename)
        return content
    f.close()
    nodes = dom.getElementsByTagName('message')
    # scan all message nodes
    for node in nodes:
        message = ''
        try:
            message = extractMessage(node)
        except AttributeError:
            print "Warning: Unparsable Message, see log file for details"
            logger.warn(node.toxml())
        sender = extractSender(node)
        if message != '' and sender != '':
            content.append((id, sender, message))
            id+=1
    return content

def scanDirectory(path):
    content = []
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('.xml'):
                content = parseFile(content, dirname + "/" +  filename)
    return content

def analyze(content):
    # content looks like
    # [(1, "John", "hey how are you"),
    #  (2, "Tim", "fine and you?"),
    #  (3, "John", "i'm fine too!"),]
    # -----------
    # create a dictionary that looks like
    # {'John':{'hello': 1, 'I':10, 'am':5}}
    # -----------
    usedwords = {}
    for entry in content:
        for word in entry[2].split(' '):
            if entry[1] not in usedwords:
                usedwords[entry[1]] = {}
            if word not in usedwords[entry[1]]:
                usedwords[entry[1]][word] = 0
            usedwords[entry[1]][word] += 1
    # sort
    # before {'John':{'hello': 1, 'I':10, 'am':5}}
    for entry in usedwords:
        usedwords[entry] = sorted(usedwords[entry].iteritems(), key=operator.itemgetter(1), reverse=True)
    # after {'John':[('I', 10), ('am', 5), (hello', 1)]}
    # -----------
    # determine total word count
    totalwords = 0
    for sender in usedwords:
        for word, count in usedwords[sender]:
            totalwords += count

    return (usedwords, totalwords)

def printResults(results):
    for sender in results[0]:
        print "Top 10 Words for: " + sender
        i = 0
        for word, value in results[0][sender]:
            if i == 10:
                break
            print word + " : "+ str(value)
            i += 1
        print

    print "Total words spoken: " + str(results[1])

# -----------------------------------------------
# ---------------- Main Program -----------------
# -----------------------------------------------
if len(sys.argv) != 2:
    print "Please supply the path to the adium logs, see readme on github for details"
    sys.exit()

path = sys.argv[1] 
content = scanDirectory(path)
result = analyze(content)
printResults(result)
