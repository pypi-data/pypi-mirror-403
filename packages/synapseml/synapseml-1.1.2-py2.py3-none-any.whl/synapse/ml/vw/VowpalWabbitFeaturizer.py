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


@inherit_doc
class VowpalWabbitFeaturizer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        inputCols (list): The names of the input columns
        numBits (int): Number of bits used to mask
        outputCol (str): The name of the output column
        prefixStringsWithColumnName (bool): Prefix string features with column name
        preserveOrderNumBits (int): Number of bits used to preserve the feature order. This will reduce the hash size. Needs to be large enough to fit count the maximum number of words
        seed (int): Hash seed
        stringSplitInputCols (list): Input cols that should be split at word boundaries
        sumCollisions (bool): Sums collisions if true, otherwise removes them
    """

    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    numBits = Param(Params._dummy(), "numBits", "Number of bits used to mask", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    prefixStringsWithColumnName = Param(Params._dummy(), "prefixStringsWithColumnName", "Prefix string features with column name", typeConverter=TypeConverters.toBoolean)
    
    preserveOrderNumBits = Param(Params._dummy(), "preserveOrderNumBits", "Number of bits used to preserve the feature order. This will reduce the hash size. Needs to be large enough to fit count the maximum number of words", typeConverter=TypeConverters.toInt)
    
    seed = Param(Params._dummy(), "seed", "Hash seed", typeConverter=TypeConverters.toInt)
    
    stringSplitInputCols = Param(Params._dummy(), "stringSplitInputCols", "Input cols that should be split at word boundaries", typeConverter=TypeConverters.toListString)
    
    sumCollisions = Param(Params._dummy(), "sumCollisions", "Sums collisions if true, otherwise removes them", typeConverter=TypeConverters.toBoolean)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        inputCols=[],
        numBits=30,
        outputCol="features",
        prefixStringsWithColumnName=True,
        preserveOrderNumBits=0,
        seed=0,
        stringSplitInputCols=[],
        sumCollisions=True
        ):
        super(VowpalWabbitFeaturizer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.vw.VowpalWabbitFeaturizer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(inputCols=[])
        self._setDefault(numBits=30)
        self._setDefault(outputCol="features")
        self._setDefault(prefixStringsWithColumnName=True)
        self._setDefault(preserveOrderNumBits=0)
        self._setDefault(seed=0)
        self._setDefault(stringSplitInputCols=[])
        self._setDefault(sumCollisions=True)
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
        inputCols=[],
        numBits=30,
        outputCol="features",
        prefixStringsWithColumnName=True,
        preserveOrderNumBits=0,
        seed=0,
        stringSplitInputCols=[],
        sumCollisions=True
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
        return "com.microsoft.azure.synapse.ml.vw.VowpalWabbitFeaturizer"

    @staticmethod
    def _from_java(java_stage):
        module_name=VowpalWabbitFeaturizer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".VowpalWabbitFeaturizer"
        return from_java(java_stage, module_name)

    def setInputCols(self, value):
        """
        Args:
            inputCols: The names of the input columns
        """
        self._set(inputCols=value)
        return self
    
    def setNumBits(self, value):
        """
        Args:
            numBits: Number of bits used to mask
        """
        self._set(numBits=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setPrefixStringsWithColumnName(self, value):
        """
        Args:
            prefixStringsWithColumnName: Prefix string features with column name
        """
        self._set(prefixStringsWithColumnName=value)
        return self
    
    def setPreserveOrderNumBits(self, value):
        """
        Args:
            preserveOrderNumBits: Number of bits used to preserve the feature order. This will reduce the hash size. Needs to be large enough to fit count the maximum number of words
        """
        self._set(preserveOrderNumBits=value)
        return self
    
    def setSeed(self, value):
        """
        Args:
            seed: Hash seed
        """
        self._set(seed=value)
        return self
    
    def setStringSplitInputCols(self, value):
        """
        Args:
            stringSplitInputCols: Input cols that should be split at word boundaries
        """
        self._set(stringSplitInputCols=value)
        return self
    
    def setSumCollisions(self, value):
        """
        Args:
            sumCollisions: Sums collisions if true, otherwise removes them
        """
        self._set(sumCollisions=value)
        return self

    
    def getInputCols(self):
        """
        Returns:
            inputCols: The names of the input columns
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getNumBits(self):
        """
        Returns:
            numBits: Number of bits used to mask
        """
        return self.getOrDefault(self.numBits)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getPrefixStringsWithColumnName(self):
        """
        Returns:
            prefixStringsWithColumnName: Prefix string features with column name
        """
        return self.getOrDefault(self.prefixStringsWithColumnName)
    
    
    def getPreserveOrderNumBits(self):
        """
        Returns:
            preserveOrderNumBits: Number of bits used to preserve the feature order. This will reduce the hash size. Needs to be large enough to fit count the maximum number of words
        """
        return self.getOrDefault(self.preserveOrderNumBits)
    
    
    def getSeed(self):
        """
        Returns:
            seed: Hash seed
        """
        return self.getOrDefault(self.seed)
    
    
    def getStringSplitInputCols(self):
        """
        Returns:
            stringSplitInputCols: Input cols that should be split at word boundaries
        """
        return self.getOrDefault(self.stringSplitInputCols)
    
    
    def getSumCollisions(self):
        """
        Returns:
            sumCollisions: Sums collisions if true, otherwise removes them
        """
        return self.getOrDefault(self.sumCollisions)

    

    
        