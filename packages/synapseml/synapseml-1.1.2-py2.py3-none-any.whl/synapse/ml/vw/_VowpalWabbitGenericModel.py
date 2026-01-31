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
class _VowpalWabbitGenericModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        inputCol (str): The name of the input column
        model (list): The VW model....
        oneStepAheadPredictions (object): 1-step ahead predictions collected during training
        performanceStatistics (object): Performance statistics collected during training
        testArgs (str): Additional arguments passed to VW at test time
    """

    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    model = Param(Params._dummy(), "model", "The VW model....")
    
    oneStepAheadPredictions = Param(Params._dummy(), "oneStepAheadPredictions", "1-step ahead predictions collected during training")
    
    performanceStatistics = Param(Params._dummy(), "performanceStatistics", "Performance statistics collected during training")
    
    testArgs = Param(Params._dummy(), "testArgs", "Additional arguments passed to VW at test time", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        inputCol=None,
        model=None,
        oneStepAheadPredictions=None,
        performanceStatistics=None,
        testArgs=""
        ):
        super(_VowpalWabbitGenericModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.vw.VowpalWabbitGenericModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(testArgs="")
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
        model=None,
        oneStepAheadPredictions=None,
        performanceStatistics=None,
        testArgs=""
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
        return "com.microsoft.azure.synapse.ml.vw.VowpalWabbitGenericModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_VowpalWabbitGenericModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".VowpalWabbitGenericModel"
        return from_java(java_stage, module_name)

    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setModel(self, value):
        """
        Args:
            model: The VW model....
        """
        self._set(model=value)
        return self
    
    def setOneStepAheadPredictions(self, value):
        """
        Args:
            oneStepAheadPredictions: 1-step ahead predictions collected during training
        """
        self._set(oneStepAheadPredictions=value)
        return self
    
    def setPerformanceStatistics(self, value):
        """
        Args:
            performanceStatistics: Performance statistics collected during training
        """
        self._set(performanceStatistics=value)
        return self
    
    def setTestArgs(self, value):
        """
        Args:
            testArgs: Additional arguments passed to VW at test time
        """
        self._set(testArgs=value)
        return self

    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getModel(self):
        """
        Returns:
            model: The VW model....
        """
        return self.getOrDefault(self.model)
    
    
    def getOneStepAheadPredictions(self):
        """
        Returns:
            oneStepAheadPredictions: 1-step ahead predictions collected during training
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getOneStepAheadPredictions(), sql_ctx)
    
    
    def getPerformanceStatistics(self):
        """
        Returns:
            performanceStatistics: Performance statistics collected during training
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getPerformanceStatistics(), sql_ctx)
    
    
    def getTestArgs(self):
        """
        Returns:
            testArgs: Additional arguments passed to VW at test time
        """
        return self.getOrDefault(self.testArgs)

    

    
        