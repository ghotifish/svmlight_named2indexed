# svmlight_named2indexed
Tested for Python 2.7

## Short version
If you have generated data for [svmlight](http://svmlight.joachims.org/), but haven't changed your feature names to indices yet, let this script take care of it for you.

## Long version
The SVM tool [svmlight](http://svmlight.joachims.org/) requires features to be represented by unique sorted indices, rather than by their names.
This script takes a data file where features are still given strings and converts them into such indices.
Optionally, the mapping from index to feature name can also be saved.

Input files must follow the regular svmlight format

`<line> .=. <target> <feature>:<value> <feature>:<value> ... <feature>:<value> # <info>`
    
with the exception that instead of

`<feature> .=. <integer> | "qid"`

you provide

`<feature> .=. <string> | "qid"`
