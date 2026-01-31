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
from synapse.ml.automl.BestModel import BestModel

@inherit_doc
class FindBestModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        evaluationMetric (str): Metric to evaluate models with
        models (object): List of models to be evaluated
    """

    evaluationMetric = Param(Params._dummy(), "evaluationMetric", "Metric to evaluate models with", typeConverter=TypeConverters.toString)
    
    models = Param(Params._dummy(), "models", "List of models to be evaluated")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        evaluationMetric="accuracy",
        models=None
        ):
        super(FindBestModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.automl.FindBestModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(evaluationMetric="accuracy")
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
        evaluationMetric="accuracy",
        models=None
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
        return "com.microsoft.azure.synapse.ml.automl.FindBestModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=FindBestModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".FindBestModel"
        return from_java(java_stage, module_name)

    def setEvaluationMetric(self, value):
        """
        Args:
            evaluationMetric: Metric to evaluate models with
        """
        self._set(evaluationMetric=value)
        return self
    
    def setModels(self, value):
        """
        Args:
            models: List of models to be evaluated
        """
        self._set(models=value)
        return self

    
    def getEvaluationMetric(self):
        """
        Returns:
            evaluationMetric: Metric to evaluate models with
        """
        return self.getOrDefault(self.evaluationMetric)
    
    
    def getModels(self):
        """
        Returns:
            models: List of models to be evaluated
        """
        return self.getOrDefault(self.models)

    def _create_model(self, java_model):
        try:
            model = BestModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = BestModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        