# Copyright (C) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in project root for information.


import sys
if sys.version >= '3':
    basestring = str

from pyspark import SparkContext, SQLContext
from pyspark.sql import DataFrame
from pyspark.ml.param.shared import *
from pyspark import keyword_only
from pyspark.ml.util import JavaMLReadable, JavaMLWritable
from synapse.ml.core.platform import running_on_synapse_internal
from synapse.ml.core.serialize.java_params_patch import *
from pyspark.ml.wrapper import JavaTransformer, JavaEstimator, JavaModel
from pyspark.ml.evaluation import JavaEvaluator
from pyspark.ml.common import inherit_doc
from synapse.ml.core.schema.Utils import *
from pyspark.ml.param import TypeConverters
from synapse.ml.core.schema.TypeConversionUtils import generateTypeConverter, complexTypeConverter
from pyspark.ml import PipelineModel

@inherit_doc
class TextFeaturizer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        binary (bool): If true, all nonegative word counts are set to 1
        caseSensitiveStopWords (bool):  Whether to do a case sensitive comparison over the stop words
        defaultStopWordLanguage (str): Which language to use for the stop word remover, set this to custom to use the stopWords input
        inputCol (str): The name of the input column
        minDocFreq (int): The minimum number of documents in which a term should appear.
        minTokenLength (int): Minimum token length, >= 0.
        nGramLength (int): The size of the Ngrams
        numFeatures (int): Set the number of features to hash each document to
        outputCol (str): The name of the output column
        stopWords (str): The words to be filtered out.
        toLowercase (bool): Indicates whether to convert all characters to lowercase before tokenizing.
        tokenizerGaps (bool): Indicates whether regex splits on gaps (true) or matches tokens (false).
        tokenizerPattern (str): Regex pattern used to match delimiters if gaps is true or tokens if gaps is false.
        useIDF (bool): Whether to scale the Term Frequencies by IDF
        useNGram (bool): Whether to enumerate N grams
        useStopWordsRemover (bool): Whether to remove stop words from tokenized data
        useTokenizer (bool): Whether to tokenize the input
    """

    binary = Param(Params._dummy(), "binary", "If true, all nonegative word counts are set to 1", typeConverter=TypeConverters.toBoolean)
    
    caseSensitiveStopWords = Param(Params._dummy(), "caseSensitiveStopWords", " Whether to do a case sensitive comparison over the stop words", typeConverter=TypeConverters.toBoolean)
    
    defaultStopWordLanguage = Param(Params._dummy(), "defaultStopWordLanguage", "Which language to use for the stop word remover, set this to custom to use the stopWords input", typeConverter=TypeConverters.toString)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    minDocFreq = Param(Params._dummy(), "minDocFreq", "The minimum number of documents in which a term should appear.", typeConverter=TypeConverters.toInt)
    
    minTokenLength = Param(Params._dummy(), "minTokenLength", "Minimum token length, >= 0.", typeConverter=TypeConverters.toInt)
    
    nGramLength = Param(Params._dummy(), "nGramLength", "The size of the Ngrams", typeConverter=TypeConverters.toInt)
    
    numFeatures = Param(Params._dummy(), "numFeatures", "Set the number of features to hash each document to", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    stopWords = Param(Params._dummy(), "stopWords", "The words to be filtered out.", typeConverter=TypeConverters.toString)
    
    toLowercase = Param(Params._dummy(), "toLowercase", "Indicates whether to convert all characters to lowercase before tokenizing.", typeConverter=TypeConverters.toBoolean)
    
    tokenizerGaps = Param(Params._dummy(), "tokenizerGaps", "Indicates whether regex splits on gaps (true) or matches tokens (false).", typeConverter=TypeConverters.toBoolean)
    
    tokenizerPattern = Param(Params._dummy(), "tokenizerPattern", "Regex pattern used to match delimiters if gaps is true or tokens if gaps is false.", typeConverter=TypeConverters.toString)
    
    useIDF = Param(Params._dummy(), "useIDF", "Whether to scale the Term Frequencies by IDF", typeConverter=TypeConverters.toBoolean)
    
    useNGram = Param(Params._dummy(), "useNGram", "Whether to enumerate N grams", typeConverter=TypeConverters.toBoolean)
    
    useStopWordsRemover = Param(Params._dummy(), "useStopWordsRemover", "Whether to remove stop words from tokenized data", typeConverter=TypeConverters.toBoolean)
    
    useTokenizer = Param(Params._dummy(), "useTokenizer", "Whether to tokenize the input", typeConverter=TypeConverters.toBoolean)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        binary=False,
        caseSensitiveStopWords=False,
        defaultStopWordLanguage="english",
        inputCol=None,
        minDocFreq=1,
        minTokenLength=0,
        nGramLength=2,
        numFeatures=262144,
        outputCol="TextFeaturizer_1d1505c2f064_output",
        stopWords=None,
        toLowercase=True,
        tokenizerGaps=True,
        tokenizerPattern="\\s+",
        useIDF=True,
        useNGram=False,
        useStopWordsRemover=False,
        useTokenizer=True
        ):
        super(TextFeaturizer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.featurize.text.TextFeaturizer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(binary=False)
        self._setDefault(caseSensitiveStopWords=False)
        self._setDefault(defaultStopWordLanguage="english")
        self._setDefault(minDocFreq=1)
        self._setDefault(minTokenLength=0)
        self._setDefault(nGramLength=2)
        self._setDefault(numFeatures=262144)
        self._setDefault(outputCol="TextFeaturizer_1d1505c2f064_output")
        self._setDefault(toLowercase=True)
        self._setDefault(tokenizerGaps=True)
        self._setDefault(tokenizerPattern="\\s+")
        self._setDefault(useIDF=True)
        self._setDefault(useNGram=False)
        self._setDefault(useStopWordsRemover=False)
        self._setDefault(useTokenizer=True)
        if hasattr(self, "_input_kwargs"):
            kwargs = self._input_kwargs
        else:
            kwargs = self.__init__._input_kwargs
    
        if java_obj is None:
            for k,v in kwargs.items():
                if v is not None:
                    getattr(self, "set" + k[0].upper() + k[1:])(v)

    @keyword_only
    def setParams(
        self,
        binary=False,
        caseSensitiveStopWords=False,
        defaultStopWordLanguage="english",
        inputCol=None,
        minDocFreq=1,
        minTokenLength=0,
        nGramLength=2,
        numFeatures=262144,
        outputCol="TextFeaturizer_1d1505c2f064_output",
        stopWords=None,
        toLowercase=True,
        tokenizerGaps=True,
        tokenizerPattern="\\s+",
        useIDF=True,
        useNGram=False,
        useStopWordsRemover=False,
        useTokenizer=True
        ):
        """
        Set the (keyword only) parameters
        """
        if hasattr(self, "_input_kwargs"):
            kwargs = self._input_kwargs
        else:
            kwargs = self.__init__._input_kwargs
        return self._set(**kwargs)

    @classmethod
    def read(cls):
        """ Returns an MLReader instance for this class. """
        return JavaMMLReader(cls)

    @staticmethod
    def getJavaPackage():
        """ Returns package name String. """
        return "com.microsoft.azure.synapse.ml.featurize.text.TextFeaturizer"

    @staticmethod
    def _from_java(java_stage):
        module_name=TextFeaturizer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".TextFeaturizer"
        return from_java(java_stage, module_name)

    def setBinary(self, value):
        """
        Args:
            binary: If true, all nonegative word counts are set to 1
        """
        self._set(binary=value)
        return self
    
    def setCaseSensitiveStopWords(self, value):
        """
        Args:
            caseSensitiveStopWords:  Whether to do a case sensitive comparison over the stop words
        """
        self._set(caseSensitiveStopWords=value)
        return self
    
    def setDefaultStopWordLanguage(self, value):
        """
        Args:
            defaultStopWordLanguage: Which language to use for the stop word remover, set this to custom to use the stopWords input
        """
        self._set(defaultStopWordLanguage=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setMinDocFreq(self, value):
        """
        Args:
            minDocFreq: The minimum number of documents in which a term should appear.
        """
        self._set(minDocFreq=value)
        return self
    
    def setMinTokenLength(self, value):
        """
        Args:
            minTokenLength: Minimum token length, >= 0.
        """
        self._set(minTokenLength=value)
        return self
    
    def setNGramLength(self, value):
        """
        Args:
            nGramLength: The size of the Ngrams
        """
        self._set(nGramLength=value)
        return self
    
    def setNumFeatures(self, value):
        """
        Args:
            numFeatures: Set the number of features to hash each document to
        """
        self._set(numFeatures=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setStopWords(self, value):
        """
        Args:
            stopWords: The words to be filtered out.
        """
        self._set(stopWords=value)
        return self
    
    def setToLowercase(self, value):
        """
        Args:
            toLowercase: Indicates whether to convert all characters to lowercase before tokenizing.
        """
        self._set(toLowercase=value)
        return self
    
    def setTokenizerGaps(self, value):
        """
        Args:
            tokenizerGaps: Indicates whether regex splits on gaps (true) or matches tokens (false).
        """
        self._set(tokenizerGaps=value)
        return self
    
    def setTokenizerPattern(self, value):
        """
        Args:
            tokenizerPattern: Regex pattern used to match delimiters if gaps is true or tokens if gaps is false.
        """
        self._set(tokenizerPattern=value)
        return self
    
    def setUseIDF(self, value):
        """
        Args:
            useIDF: Whether to scale the Term Frequencies by IDF
        """
        self._set(useIDF=value)
        return self
    
    def setUseNGram(self, value):
        """
        Args:
            useNGram: Whether to enumerate N grams
        """
        self._set(useNGram=value)
        return self
    
    def setUseStopWordsRemover(self, value):
        """
        Args:
            useStopWordsRemover: Whether to remove stop words from tokenized data
        """
        self._set(useStopWordsRemover=value)
        return self
    
    def setUseTokenizer(self, value):
        """
        Args:
            useTokenizer: Whether to tokenize the input
        """
        self._set(useTokenizer=value)
        return self

    
    def getBinary(self):
        """
        Returns:
            binary: If true, all nonegative word counts are set to 1
        """
        return self.getOrDefault(self.binary)
    
    
    def getCaseSensitiveStopWords(self):
        """
        Returns:
            caseSensitiveStopWords:  Whether to do a case sensitive comparison over the stop words
        """
        return self.getOrDefault(self.caseSensitiveStopWords)
    
    
    def getDefaultStopWordLanguage(self):
        """
        Returns:
            defaultStopWordLanguage: Which language to use for the stop word remover, set this to custom to use the stopWords input
        """
        return self.getOrDefault(self.defaultStopWordLanguage)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getMinDocFreq(self):
        """
        Returns:
            minDocFreq: The minimum number of documents in which a term should appear.
        """
        return self.getOrDefault(self.minDocFreq)
    
    
    def getMinTokenLength(self):
        """
        Returns:
            minTokenLength: Minimum token length, >= 0.
        """
        return self.getOrDefault(self.minTokenLength)
    
    
    def getNGramLength(self):
        """
        Returns:
            nGramLength: The size of the Ngrams
        """
        return self.getOrDefault(self.nGramLength)
    
    
    def getNumFeatures(self):
        """
        Returns:
            numFeatures: Set the number of features to hash each document to
        """
        return self.getOrDefault(self.numFeatures)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getStopWords(self):
        """
        Returns:
            stopWords: The words to be filtered out.
        """
        return self.getOrDefault(self.stopWords)
    
    
    def getToLowercase(self):
        """
        Returns:
            toLowercase: Indicates whether to convert all characters to lowercase before tokenizing.
        """
        return self.getOrDefault(self.toLowercase)
    
    
    def getTokenizerGaps(self):
        """
        Returns:
            tokenizerGaps: Indicates whether regex splits on gaps (true) or matches tokens (false).
        """
        return self.getOrDefault(self.tokenizerGaps)
    
    
    def getTokenizerPattern(self):
        """
        Returns:
            tokenizerPattern: Regex pattern used to match delimiters if gaps is true or tokens if gaps is false.
        """
        return self.getOrDefault(self.tokenizerPattern)
    
    
    def getUseIDF(self):
        """
        Returns:
            useIDF: Whether to scale the Term Frequencies by IDF
        """
        return self.getOrDefault(self.useIDF)
    
    
    def getUseNGram(self):
        """
        Returns:
            useNGram: Whether to enumerate N grams
        """
        return self.getOrDefault(self.useNGram)
    
    
    def getUseStopWordsRemover(self):
        """
        Returns:
            useStopWordsRemover: Whether to remove stop words from tokenized data
        """
        return self.getOrDefault(self.useStopWordsRemover)
    
    
    def getUseTokenizer(self):
        """
        Returns:
            useTokenizer: Whether to tokenize the input
        """
        return self.getOrDefault(self.useTokenizer)

    def _create_model(self, java_model):
        try:
            model = PipelineModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = PipelineModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        