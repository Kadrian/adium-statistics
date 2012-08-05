#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError
import sys, os, operator
import math

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
            print "Warning: Unparsable message, see log file for details"
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

    # ----------- 1 --------------
    # determine words used and count them per chat partner
    # create a dictionary that looks like
    # {'John':{'hello': 1, 'I':10, 'am':5}}
    # -----------
    usedwords = {}
    for line in content:
        for word in line[2].split(' '):
            if line[1] not in usedwords:
                usedwords[line[1]] = {}
            if word not in usedwords[line[1]]:
                usedwords[line[1]][word] = 0
            usedwords[line[1]][word] += 1
    # sort
    # before {'John':{'hello': 1, 'I':10, 'am':5}}
    for line in usedwords:
        usedwords[line] = sorted(usedwords[line].iteritems(), key=operator.itemgetter(1), reverse=True)
    # after {'John':[('I', 10), ('am', 5), (hello', 1)]}

    # ----------- 2 --------------
    # determine total word count
    totalwords = 0
    for sender in usedwords:
        for word, count in usedwords[sender]:
            totalwords += count

    # ----------- 3 --------------
    # determine interesting words
    interestingwords = {}
    for sender in usedwords:
        word, count = usedwords[sender][0]
        onepercent = math.ceil(count / 1000.0)
        counter = 0
        for w, c in reversed(usedwords[sender]):
            if c >= onepercent:
                if sender not in interestingwords:
                    interestingwords[sender] = []
                interestingwords[sender].append(w)
                counter += 1
            if counter >= 5:
                break

    # ----------- 4 + 5 ----------
    # determine average + maximum message length per chat partner
    averages = {}
    maxima = {}
    for line in content:
        wordcount = len(line[2].split(' '))
        if line[1] not in averages:
            averages[line[1]] = wordcount
        averages[line[1]] += wordcount
        averages[line[1]] /= 2.0 
        if (line[1] not in maxima) or (wordcount > maxima[line[1]][0]):
            maxima[line[1]] = (wordcount, line[2])

    # ----------- 6 + 7 ----------
    # determine average + maximum number of consecutive messages per chat partner
    consecutiveAvgs = {}
    consecutiveMaxs = {}
    counter = 0
    lastAuthor = content[0][1]
    for line in content:
        counter += 1
        if lastAuthor != line[1]:
            if line[1] not in consecutiveAvgs:
                consecutiveAvgs[line[1]] = counter
            consecutiveAvgs[line[1]] += counter 
            consecutiveAvgs[line[1]] /= 2.0
            lastAuthor = line[1]
            if (line[1] not in consecutiveMaxs) or (counter > consecutiveMaxs[line[1]]):
                consecutiveMaxs[line[1]] = counter
            counter = 0

    return (usedwords, totalwords, averages, maxima, consecutiveAvgs, consecutiveMaxs, interestingwords)

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

    for sender in results[6]:
        print "Interesting words for: " + sender
        for word in results[6][sender]:
            print word
        print

    for sender in results[2]:
        print "Average message length for: " + sender + ": " + str(results[2][sender])
    print
    for sender in results[3]:
        print "Maximum message length for: " + sender + ": " + str(results[3][sender][0]) + " with:"
        print results[3][sender][1]
    for sender in results[4]:
        print "Average number of consecutive messages written for " + sender + ": " + str(results[4][sender])
    for sender in results[5]:
        print "Maximum number of consecutive messages written for " + sender + ": " + str(results[5][sender])

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
