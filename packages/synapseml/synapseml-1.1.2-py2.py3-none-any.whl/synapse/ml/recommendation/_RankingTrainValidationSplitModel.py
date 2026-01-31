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
class _RankingTrainValidationSplitModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        bestModel (object): The internal ALS model used splitter
        validationMetrics (object): Best Model
    """

    bestModel = Param(Params._dummy(), "bestModel", "The internal ALS model used splitter")
    
    validationMetrics = Param(Params._dummy(), "validationMetrics", "Best Model")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        bestModel=None,
        validationMetrics=None
        ):
        super(_RankingTrainValidationSplitModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.recommendation.RankingTrainValidationSplitModel", self.uid)
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
        bestModel=None,
        validationMetrics=None
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
        return "com.microsoft.azure.synapse.ml.recommendation.RankingTrainValidationSplitModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_RankingTrainValidationSplitModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".RankingTrainValidationSplitModel"
        return from_java(java_stage, module_name)

    def setBestModel(self, value):
        """
        Args:
            bestModel: The internal ALS model used splitter
        """
        self._set(bestModel=value)
        return self
    
    def setValidationMetrics(self, value):
        """
        Args:
            validationMetrics: Best Model
        """
        self._set(validationMetrics=value)
        return self

    
    def getBestModel(self):
        """
        Returns:
            bestModel: The internal ALS model used splitter
        """
        return self.getOrDefault(self.bestModel)
    
    
    def getValidationMetrics(self):
        """
        Returns:
            validationMetrics: Best Model
        """
        return self.getOrDefault(self.validationMetrics)

    

    
        