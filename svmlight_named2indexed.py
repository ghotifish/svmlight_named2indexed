#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The SVM tool svmlight requires features to be represented by unique sorted indices, rather than by their names.
This script takes a data file where features are still given strings and converts them into such indices.
Optionally, the mapping from index to feature name can also be saved.

Input files must follow the regular svmlight format
    <line> .=. <target> <feature>:<value> <feature>:<value> ... <feature>:<value> # <info>
with the exception that instead of
    <feature> .=. <integer> | "qid"
you provide
    <feature> .=. <string> | "qid"

Tested for Python 2.7
"""
import sys
from getopt import gnu_getopt as getopt

__author__ = 'Marc Schulder'


def loadSVMLightData(filepath):
    """
    Load a file containing train/test data following the svmlight input format.
    :param filepath: The input data file
    :return: The tuple (ITEMS, COMMENTS), where ITEMS is a list of tuples (TARGET, [(FEATURE,VALUE)], INFO)
             and COMMENTS is a list of comment lines
    """
    data = list()
    comments = list()
    # DEBUG = 0
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                if line.startswith('#'):
                    comments.append(line)
                else:
                    item = _parseDataLine(line)
                    data.append(item)
            # if DEBUG < 10:
            #     DEBUG += 1
            # else:
            #     break
    return data, comments


def _parseDataLine(line):
    if len(line) == 0:
        return None

    # Get info entry, if there is one
    info = None
    if '#' in line:
        line, info = line.rsplit('#')
        info = '#'+info

    # Get target and features
    elems = line.split(' ')
    target = elems[0]
    features = [tuple(f.split(':', 1)) for f in elems[1:] if ':' in f]

    return target, features, info


def writeSVMLightData(filepath, data, comments=None):
    with open(filepath, 'w') as w:
        if comments is not None:
            for comment in comments:
                w.write(comment)
                w.write('\n')

        for target, features, info in data:
            featuresText = ' '.join(['{0}:{1}'.format(feature, value) for feature, value in features])
            line = '{0} {1} {2}\n'.format(target, featuresText, info)
            w.write(line)


def writeIndex2NameMapping(filepath, index2name):
    with open(filepath, 'w') as w:
        for index, name in index2name.iteritems():
            w.write('{0} {1}\n'.format(index, name))


def convertName2Index(namedData):
    indexedData = list()
    index2string = dict()
    string2index = dict()

    nextIndex = 1  # IMPORTANT: svmlight indices must start at 1, not 0!!!
    for target, namedFeatures, info in namedData:

        # Convert named features into indexed features
        indexedFeatures = list()
        for namedFeature, value in namedFeatures:
            if namedFeature == 'qid':
                # Special qid feature; receives no index
                indexedFeature = namedFeature
            elif namedFeature in string2index:
                # Encountered a known feature
                indexedFeature = string2index[namedFeature]
            else:
                # Encountered a new feature
                indexedFeature = nextIndex
                index2string[nextIndex] = namedFeature
                string2index[namedFeature] = nextIndex
                nextIndex += 1
            indexedFeatures.append((indexedFeature, value))

        # Ensure that indices are in ascending order
        indexedFeatures.sort()

        indexedData.append((target, indexedFeatures, info))

    return indexedData, index2string


def generateIndexedData(inputFile, outputfile, mappingFile):
    print "Loading data from", inputFile
    inputData, comments = loadSVMLightData(inputFile)
    print "Converting data"
    outputData, index2name = convertName2Index(inputData)
    print "Writing data to", outputfile
    writeSVMLightData(outputfile, outputData, comments)
    if mappingFile is not None:
        print "Writing mapping to", mappingFile
        writeIndex2NameMapping(mappingFile, index2name)


def main(args):
    optlist, args = getopt(args[1:], '')

    if 2 > len(args) > 3:
        print "USAGE: python svmlight_named2indexed.py INPUT_DATA OUTPUT_DATA [INDEX_MAPPING_FILE]"
    else:
        inputFile = args[0]
        outputfile = args[1]
        mappingFile = args[2] if len(args) > 2 else None

        generateIndexedData(inputFile, outputfile, mappingFile)

if __name__ == '__main__':
    main(sys.argv)
