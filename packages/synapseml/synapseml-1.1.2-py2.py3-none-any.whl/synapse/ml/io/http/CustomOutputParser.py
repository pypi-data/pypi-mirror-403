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
class CustomOutputParser(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        inputCol (str): The name of the input column
        outputCol (str): The name of the output column
        udfPython (object): User Defined Python Function to be applied to the DF input col
        udfScala (object): User Defined Function to be applied to the DF input col
    """

    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    udfPython = Param(Params._dummy(), "udfPython", "User Defined Python Function to be applied to the DF input col")
    
    udfScala = Param(Params._dummy(), "udfScala", "User Defined Function to be applied to the DF input col")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        inputCol=None,
        outputCol=None,
        udfPython=None,
        udfScala=None
        ):
        super(CustomOutputParser, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.io.http.CustomOutputParser", self.uid)
        else:
            self._java_obj = java_obj
        
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
        outputCol=None,
        udfPython=None,
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
        return "com.microsoft.azure.synapse.ml.io.http.CustomOutputParser"

    @staticmethod
    def _from_java(java_stage):
        module_name=CustomOutputParser.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".CustomOutputParser"
        return from_java(java_stage, module_name)

    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setUdfPython(self, value):
        """
        Args:
            udfPython: User Defined Python Function to be applied to the DF input col
        """
        self._set(udfPython=value)
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
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getUdfPython(self):
        """
        Returns:
            udfPython: User Defined Python Function to be applied to the DF input col
        """
        return self.getOrDefault(self.udfPython)
    
    
    def getUdfScala(self):
        """
        Returns:
            udfScala: User Defined Function to be applied to the DF input col
        """
        return self.getOrDefault(self.udfScala)

    

    
        