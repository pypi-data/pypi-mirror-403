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
class _BestModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        allModelMetrics (object): all model metrics
        bestModel (object): the best model found
        bestModelMetrics (object): the metrics from the best model
        rocCurve (object): the roc curve of the best model
        scoredDataset (object): dataset scored by best model
    """

    allModelMetrics = Param(Params._dummy(), "allModelMetrics", "all model metrics")
    
    bestModel = Param(Params._dummy(), "bestModel", "the best model found")
    
    bestModelMetrics = Param(Params._dummy(), "bestModelMetrics", "the metrics from the best model")
    
    rocCurve = Param(Params._dummy(), "rocCurve", "the roc curve of the best model")
    
    scoredDataset = Param(Params._dummy(), "scoredDataset", "dataset scored by best model")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        allModelMetrics=None,
        bestModel=None,
        bestModelMetrics=None,
        rocCurve=None,
        scoredDataset=None
        ):
        super(_BestModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.automl.BestModel", self.uid)
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
        allModelMetrics=None,
        bestModel=None,
        bestModelMetrics=None,
        rocCurve=None,
        scoredDataset=None
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
        return "com.microsoft.azure.synapse.ml.automl.BestModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_BestModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".BestModel"
        return from_java(java_stage, module_name)

    def setAllModelMetrics(self, value):
        """
        Args:
            allModelMetrics: all model metrics
        """
        self._set(allModelMetrics=value)
        return self
    
    def setBestModel(self, value):
        """
        Args:
            bestModel: the best model found
        """
        self._set(bestModel=value)
        return self
    
    def setBestModelMetrics(self, value):
        """
        Args:
            bestModelMetrics: the metrics from the best model
        """
        self._set(bestModelMetrics=value)
        return self
    
    def setRocCurve(self, value):
        """
        Args:
            rocCurve: the roc curve of the best model
        """
        self._set(rocCurve=value)
        return self
    
    def setScoredDataset(self, value):
        """
        Args:
            scoredDataset: dataset scored by best model
        """
        self._set(scoredDataset=value)
        return self

    
    def getAllModelMetrics(self):
        """
        Returns:
            allModelMetrics: all model metrics
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getAllModelMetrics(), sql_ctx)
    
    
    def getBestModel(self):
        """
        Returns:
            bestModel: the best model found
        """
        return JavaParams._from_java(self._java_obj.getBestModel())
    
    
    def getBestModelMetrics(self):
        """
        Returns:
            bestModelMetrics: the metrics from the best model
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getBestModelMetrics(), sql_ctx)
    
    
    def getRocCurve(self):
        """
        Returns:
            rocCurve: the roc curve of the best model
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getRocCurve(), sql_ctx)
    
    
    def getScoredDataset(self):
        """
        Returns:
            scoredDataset: dataset scored by best model
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getScoredDataset(), sql_ctx)

    

    
        