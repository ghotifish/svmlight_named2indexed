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
from os import path
from getopt import gnu_getopt as getopt
from timer import Timer

__author__ = 'Marc Schulder'


class Indexer:
    def __init__(self):
        self.knownFeatures = list()
        self.string2index = dict()
        self.nextIndex = 1  # IMPORTANT: svmlight indices must start at 1, not 0!!!
        self.mappingWriter = None

    def getIndex4Feature(self, feature):
        """
        Convert named features into indexed features
        :param feature: A named feature
        :return: Index for the feature
        """
        if feature == 'qid':
            # Special qid feature; receives no index
            featureIndex = feature
        elif feature in self.string2index:
            # Encountered a known feature
            featureIndex = self.string2index[feature]
        else:
            # Encountered a new feature
            featureIndex = self.nextIndex
            self.knownFeatures.append(feature)
            self.string2index[feature] = featureIndex
            self.nextIndex += 1
            if self.mappingWriter is not None:
                self._addIndex2NameMapping(self.mappingWriter, featureIndex, feature)
        return featureIndex

    def getIndicesForFeatureList(self, featureValuePairs):
        """
        Replace named features with their indices
        :param featureValuePairs: List of tuples (featureName, value)
        :return: List of tuples (featureIndex, value)
        """
        indexedFeatures = list()
        usedIndices = set()
        for namedFeature, value in featureValuePairs:
            indexedFeature = self.getIndex4Feature(namedFeature)
            indexedFeatures.append((indexedFeature, value))
            if indexedFeature in usedIndices:
                raise ValueError("Duplicate feature: {0}".format(namedFeature))
            else:
                usedIndices.add(indexedFeature)

        # Ensure that indices are in ascending order
        indexedFeatures.sort()

        return indexedFeatures

    def getIndexedDataItem(self, target, featureValuePairs, info):
        """
        Create a new data item that replaces named features with their indices.
        :param target: Label of the data item
        :param featureValuePairs: List of tuples (featureName, value)
        :param info: Info comment for data item
        :return: (target, [(featureIndex, value)], info)
        """
        # Convert named features into indexed features
        indexedFeatures = self.getIndicesForFeatureList(featureValuePairs)
        return target, indexedFeatures, info

    def saveIndex2NameMapping(self, filename):
        """
        Save the mapping from feature indices to feature names that the indexer has generated so far
        """
        with open(filename, 'w') as w:
            self._saveIndex2NameMapping(w)

    def _saveIndex2NameMapping(self, writer=None):
        """
        Given a file writer, save mapping from feature indices to feature names that the indexer has generated so far.
        If no writer is provided, it is checked whether a live writer was activated via
            activateIndex2NameMappingLiveWriting(). If that is not the case, nothing happens.
        """
        if writer is None:
            writer = self.mappingWriter

        if writer is not None:
            for i, name in enumerate(self.knownFeatures):
                index = i + 1  # IMPORTANT: svmlight indices start at 1, not 0!!!
                self._addIndex2NameMapping(writer, index, name)

    @staticmethod
    def _addIndex2NameMapping(writer, index, name):
        writer.write('{0} {1}\n'.format(index, name))

    def activateIndex2NameMappingLiveWriting(self, filename):
        """
        Continuously save the mappings from feature indices to feature names as they are generated.
        If mappings exist before function is activated, they are instantly saved when this function is called.
        Remember to call deactivateIndex2NameMappingLiveWriting() to close the file writer.
        """
        if filename is not None:
            self.mappingWriter = open(filename, 'w')
            if len(self.knownFeatures) > 0:
                self._saveIndex2NameMapping()

    def deactivateIndex2NameMappingLiveWriting(self):
        """
        Stop the constant writing of "index to feature name" mappings and close the file writer.
        :return:
        """
        if self.mappingWriter is not None:
            self.mappingWriter.close()
            self.mappingWriter = None


def loadSVMLightData(filename):
    """
    Load a file containing train/test data following the svmlight input format.
    :param filename: The input data file
    :return: The tuple (ITEMS, COMMENTS), where ITEMS is a list of tuples (TARGET, [(FEATURE,VALUE)], INFO)
             and COMMENTS is a list of comment lines
    """
    data = list()
    comments = list()
    for dataitem, comment in loadSVMLightDataIter(filename):
        if dataitem is not None:
            data.append(dataitem)

        if comment is not None:
            comments.append(comment)
    return data, comments


def loadSVMLightDataIter(filename):
    """
    Iterator that loads a file containing train/test data following the svmlight input format.
    Returns a tuple (DATAITEM, COMMENT), one of which is always None.
    When not None, DATAITEM is a tuple (TARGET, FEATURES, INFO) where FEATURES is a list of tuples (FEATURE,VALUE)
    When not None, COMMENT is a string.
    """
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                if line.startswith('#'):  # Comment line
                    yield None, line
                else:
                    item = _parseDataLine(line)  # Data line
                    yield item, None


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
        for comment in comments:
            _writeSVMLightData_Comment(w, comment)

        for target, features, info in data:
            _writeSVMLightData_DataItem(w, target, features, info)


def _writeSVMLightData_DataItem(writer, target, features, info):
    featuresText = ' '.join(['{0}:{1}'.format(feature, value) for feature, value in features])
    line = '{0} {1} {2}\n'.format(target, featuresText, info)
    writer.write(line)


def _writeSVMLightData_Comment(writer, comment):
    if comment is not None:
        writer.write(comment)
        writer.write('\n')


def writeIndex2NameMapping(filepath, index2name):
    with open(filepath, 'w') as w:
        for index, name in index2name.iteritems():
            w.write('{0} {1}\n'.format(index, name))


def convertName2Index(namedData):
    indexer = Indexer()
    indexedData = [indexer.getIndexedDataItem(target, features, info) for target, features, info in namedData]
    index2string = {i+1: feature for i, feature in enumerate(indexer.knownFeatures)}
    return indexedData, index2string


def generateIndexedData(inputFile, outputFile, mappingFile=None, verbose=False):
    with Timer('Conversion took', verbose=verbose):
        indexer = Indexer()
        if mappingFile is not None:
            indexer.activateIndex2NameMappingLiveWriting(mappingFile)

        if verbose:
            if mappingFile is None:
                print "Loading named data from:", inputFile
                print "Saving indexed data to: ", outputFile
            else:
                print "Loading named data from:        ", inputFile
                print "Saving indexed data to:         ", outputFile
                print "Saving index-to-name mapping to:", mappingFile

        with open(outputFile, 'w') as w:
            # Iterate over all data items
            i = 0
            for dataitem, comment in loadSVMLightDataIter(inputFile):
                if comment is not None:
                    _writeSVMLightData_Comment(w, comment)

                if dataitem is not None:
                    i += 1
                    if verbose and i % 1000 == 0:
                        print "Processed {0} entries".format(i)
                    target, namedFeatures, info = dataitem
                    namedFeatures = indexer.getIndicesForFeatureList(namedFeatures)
                    _writeSVMLightData_DataItem(w, target, namedFeatures, info)
            if verbose:
                print "Finished after processing a total of {0} entries".format(i+1)

        if mappingFile is not None:
            indexer.deactivateIndex2NameMappingLiveWriting()


def generateIndexedData4File(outputName, dataDir):
    """
    Convenience function to generate indexed data for a given stringdata file.
    Output files will have same location and name as input file, except for their file extension.
    :param outputName: Name of the input and output files, without the respective file extensions
    :param dataDir: Directory for input and output files
    """
    outStringDataFile = path.join(dataDir, '{0}.stringdata'.format(outputName))
    outDataFile = path.join(dataDir, '{0}.data'.format(outputName))
    mappingFile = path.join(dataDir, '{0}.features'.format(outputName))

    generateIndexedData(outStringDataFile, outDataFile, mappingFile)


def main(args):
    optlist, args = getopt(args[1:], 'v', ['verbose'])

    verbose = False
    for opt, _ in optlist:
        if opt in ['-v', '--verbose']:
            verbose = True

    if 2 > len(args) > 3:
        print "USAGE: python svmlight_named2indexed.py INPUT_DATA OUTPUT_DATA [INDEX_MAPPING_FILE]"
        print "OPTIONS: -v/--verbose: Add verbose output"
    else:
        inputFile = args[0]
        outputfile = args[1]
        mappingFile = args[2] if len(args) > 2 else None

        generateIndexedData(inputFile, outputfile, mappingFile, verbose)

if __name__ == '__main__':
    main(sys.argv)
