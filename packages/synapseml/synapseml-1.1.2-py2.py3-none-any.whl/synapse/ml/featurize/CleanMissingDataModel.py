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
class CleanMissingDataModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        colsToFill (list): The columns to fill with
        fillValues (object): what to replace in the columns
        inputCols (list): The names of the input columns
        outputCols (list): The names of the output columns
    """

    colsToFill = Param(Params._dummy(), "colsToFill", "The columns to fill with", typeConverter=TypeConverters.toListString)
    
    fillValues = Param(Params._dummy(), "fillValues", "what to replace in the columns")
    
    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    outputCols = Param(Params._dummy(), "outputCols", "The names of the output columns", typeConverter=TypeConverters.toListString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        colsToFill=None,
        fillValues=None,
        inputCols=None,
        outputCols=None
        ):
        super(CleanMissingDataModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.featurize.CleanMissingDataModel", self.uid)
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
        colsToFill=None,
        fillValues=None,
        inputCols=None,
        outputCols=None
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
        return "com.microsoft.azure.synapse.ml.featurize.CleanMissingDataModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=CleanMissingDataModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".CleanMissingDataModel"
        return from_java(java_stage, module_name)

    def setColsToFill(self, value):
        """
        Args:
            colsToFill: The columns to fill with
        """
        self._set(colsToFill=value)
        return self
    
    def setFillValues(self, value):
        """
        Args:
            fillValues: what to replace in the columns
        """
        self._set(fillValues=value)
        return self
    
    def setInputCols(self, value):
        """
        Args:
            inputCols: The names of the input columns
        """
        self._set(inputCols=value)
        return self
    
    def setOutputCols(self, value):
        """
        Args:
            outputCols: The names of the output columns
        """
        self._set(outputCols=value)
        return self

    
    def getColsToFill(self):
        """
        Returns:
            colsToFill: The columns to fill with
        """
        return self.getOrDefault(self.colsToFill)
    
    
    def getFillValues(self):
        """
        Returns:
            fillValues: what to replace in the columns
        """
        return self.getOrDefault(self.fillValues)
    
    
    def getInputCols(self):
        """
        Returns:
            inputCols: The names of the input columns
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getOutputCols(self):
        """
        Returns:
            outputCols: The names of the output columns
        """
        return self.getOrDefault(self.outputCols)

    

    
        