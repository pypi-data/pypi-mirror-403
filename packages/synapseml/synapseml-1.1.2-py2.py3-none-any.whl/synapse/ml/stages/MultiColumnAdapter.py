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
class MultiColumnAdapter(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        baseStage (object): base pipeline stage to apply to every column
        inputCols (list): list of column names encoded as a string
        outputCols (list): list of column names encoded as a string
    """

    baseStage = Param(Params._dummy(), "baseStage", "base pipeline stage to apply to every column")
    
    inputCols = Param(Params._dummy(), "inputCols", "list of column names encoded as a string", typeConverter=TypeConverters.toListString)
    
    outputCols = Param(Params._dummy(), "outputCols", "list of column names encoded as a string", typeConverter=TypeConverters.toListString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        baseStage=None,
        inputCols=None,
        outputCols=None
        ):
        super(MultiColumnAdapter, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.MultiColumnAdapter", self.uid)
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
        baseStage=None,
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
        return "com.microsoft.azure.synapse.ml.stages.MultiColumnAdapter"

    @staticmethod
    def _from_java(java_stage):
        module_name=MultiColumnAdapter.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".MultiColumnAdapter"
        return from_java(java_stage, module_name)

    def setBaseStage(self, value):
        """
        Args:
            baseStage: base pipeline stage to apply to every column
        """
        self._set(baseStage=value)
        return self
    
    def setInputCols(self, value):
        """
        Args:
            inputCols: list of column names encoded as a string
        """
        self._set(inputCols=value)
        return self
    
    def setOutputCols(self, value):
        """
        Args:
            outputCols: list of column names encoded as a string
        """
        self._set(outputCols=value)
        return self

    
    def getBaseStage(self):
        """
        Returns:
            baseStage: base pipeline stage to apply to every column
        """
        return JavaParams._from_java(self._java_obj.getBaseStage())
    
    
    def getInputCols(self):
        """
        Returns:
            inputCols: list of column names encoded as a string
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getOutputCols(self):
        """
        Returns:
            outputCols: list of column names encoded as a string
        """
        return self.getOrDefault(self.outputCols)

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

    
        