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
class VowpalWabbitInteractions(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        inputCols (list): The names of the input columns
        numBits (int): Number of bits used to mask
        outputCol (str): The name of the output column
        sumCollisions (bool): Sums collisions if true, otherwise removes them
    """

    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    numBits = Param(Params._dummy(), "numBits", "Number of bits used to mask", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    sumCollisions = Param(Params._dummy(), "sumCollisions", "Sums collisions if true, otherwise removes them", typeConverter=TypeConverters.toBoolean)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        inputCols=None,
        numBits=30,
        outputCol=None,
        sumCollisions=True
        ):
        super(VowpalWabbitInteractions, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.vw.VowpalWabbitInteractions", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(numBits=30)
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
        inputCols=None,
        numBits=30,
        outputCol=None,
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
        return "com.microsoft.azure.synapse.ml.vw.VowpalWabbitInteractions"

    @staticmethod
    def _from_java(java_stage):
        module_name=VowpalWabbitInteractions.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".VowpalWabbitInteractions"
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
    
    
    def getSumCollisions(self):
        """
        Returns:
            sumCollisions: Sums collisions if true, otherwise removes them
        """
        return self.getOrDefault(self.sumCollisions)

    

    
        