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
class _TuneHyperparametersModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        bestMetric (float): the best metric from the runs
        bestModel (object): the best model found
    """

    bestMetric = Param(Params._dummy(), "bestMetric", "the best metric from the runs", typeConverter=TypeConverters.toFloat)
    
    bestModel = Param(Params._dummy(), "bestModel", "the best model found")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        bestMetric=None,
        bestModel=None
        ):
        super(_TuneHyperparametersModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.automl.TuneHyperparametersModel", self.uid)
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
        bestMetric=None,
        bestModel=None
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
        return "com.microsoft.azure.synapse.ml.automl.TuneHyperparametersModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_TuneHyperparametersModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".TuneHyperparametersModel"
        return from_java(java_stage, module_name)

    def setBestMetric(self, value):
        """
        Args:
            bestMetric: the best metric from the runs
        """
        self._set(bestMetric=value)
        return self
    
    def setBestModel(self, value):
        """
        Args:
            bestModel: the best model found
        """
        self._set(bestModel=value)
        return self

    
    def getBestMetric(self):
        """
        Returns:
            bestMetric: the best metric from the runs
        """
        return self.getOrDefault(self.bestMetric)
    
    
    def getBestModel(self):
        """
        Returns:
            bestModel: the best model found
        """
        return JavaParams._from_java(self._java_obj.getBestModel())

    

    
        