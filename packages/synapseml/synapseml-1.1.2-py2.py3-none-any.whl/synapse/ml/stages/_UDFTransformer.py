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
class _UDFTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        inputCol (str): The name of the input column
        inputCols (list): The names of the input columns
        outputCol (str): The name of the output column
        udf (object): User Defined Python Function to be applied to the DF input col
        udfScala (object): User Defined Function to be applied to the DF input col
    """

    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    udf = Param(Params._dummy(), "udf", "User Defined Python Function to be applied to the DF input col")
    
    udfScala = Param(Params._dummy(), "udfScala", "User Defined Function to be applied to the DF input col")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        inputCol=None,
        inputCols=None,
        outputCol="UDFTransformer_1ba8b290ae4c_output",
        udf=None,
        udfScala=None
        ):
        super(_UDFTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.UDFTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(outputCol="UDFTransformer_1ba8b290ae4c_output")
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
        inputCol=None,
        inputCols=None,
        outputCol="UDFTransformer_1ba8b290ae4c_output",
        udf=None,
        udfScala=None
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
        return "com.microsoft.azure.synapse.ml.stages.UDFTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=_UDFTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".UDFTransformer"
        return from_java(java_stage, module_name)

    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setInputCols(self, value):
        """
        Args:
            inputCols: The names of the input columns
        """
        self._set(inputCols=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setUdf(self, value):
        """
        Args:
            udf: User Defined Python Function to be applied to the DF input col
        """
        self._set(udf=value)
        return self
    
    def setUdfScala(self, value):
        """
        Args:
            udfScala: User Defined Function to be applied to the DF input col
        """
        self._set(udfScala=value)
        return self

    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getInputCols(self):
        """
        Returns:
            inputCols: The names of the input columns
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getUdf(self):
        """
        Returns:
            udf: User Defined Python Function to be applied to the DF input col
        """
        return self.getOrDefault(self.udf)
    
    
    def getUdfScala(self):
        """
        Returns:
            udfScala: User Defined Function to be applied to the DF input col
        """
        return self.getOrDefault(self.udfScala)

    

    
        