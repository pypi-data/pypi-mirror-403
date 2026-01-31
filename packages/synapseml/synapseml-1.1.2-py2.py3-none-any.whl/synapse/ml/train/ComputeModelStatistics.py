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
class ComputeModelStatistics(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        evaluationMetric (str): Metric to evaluate models with
        labelCol (str): The name of the label column
        scoredLabelsCol (str): Scored labels column name, only required if using SparkML estimators
        scoresCol (str): Scores or raw prediction column name, only required if using SparkML estimators
    """

    evaluationMetric = Param(Params._dummy(), "evaluationMetric", "Metric to evaluate models with", typeConverter=TypeConverters.toString)
    
    labelCol = Param(Params._dummy(), "labelCol", "The name of the label column", typeConverter=TypeConverters.toString)
    
    scoredLabelsCol = Param(Params._dummy(), "scoredLabelsCol", "Scored labels column name, only required if using SparkML estimators", typeConverter=TypeConverters.toString)
    
    scoresCol = Param(Params._dummy(), "scoresCol", "Scores or raw prediction column name, only required if using SparkML estimators", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        evaluationMetric="all",
        labelCol=None,
        scoredLabelsCol=None,
        scoresCol=None
        ):
        super(ComputeModelStatistics, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.train.ComputeModelStatistics", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(evaluationMetric="all")
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
        evaluationMetric="all",
        labelCol=None,
        scoredLabelsCol=None,
        scoresCol=None
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
        return "com.microsoft.azure.synapse.ml.train.ComputeModelStatistics"

    @staticmethod
    def _from_java(java_stage):
        module_name=ComputeModelStatistics.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ComputeModelStatistics"
        return from_java(java_stage, module_name)

    def setEvaluationMetric(self, value):
        """
        Args:
            evaluationMetric: Metric to evaluate models with
        """
        self._set(evaluationMetric=value)
        return self
    
    def setLabelCol(self, value):
        """
        Args:
            labelCol: The name of the label column
        """
        self._set(labelCol=value)
        return self
    
    def setScoredLabelsCol(self, value):
        """
        Args:
            scoredLabelsCol: Scored labels column name, only required if using SparkML estimators
        """
        self._set(scoredLabelsCol=value)
        return self
    
    def setScoresCol(self, value):
        """
        Args:
            scoresCol: Scores or raw prediction column name, only required if using SparkML estimators
        """
        self._set(scoresCol=value)
        return self

    
    def getEvaluationMetric(self):
        """
        Returns:
            evaluationMetric: Metric to evaluate models with
        """
        return self.getOrDefault(self.evaluationMetric)
    
    
    def getLabelCol(self):
        """
        Returns:
            labelCol: The name of the label column
        """
        return self.getOrDefault(self.labelCol)
    
    
    def getScoredLabelsCol(self):
        """
        Returns:
            scoredLabelsCol: Scored labels column name, only required if using SparkML estimators
        """
        return self.getOrDefault(self.scoredLabelsCol)
    
    
    def getScoresCol(self):
        """
        Returns:
            scoresCol: Scores or raw prediction column name, only required if using SparkML estimators
        """
        return self.getOrDefault(self.scoresCol)

    

    
        