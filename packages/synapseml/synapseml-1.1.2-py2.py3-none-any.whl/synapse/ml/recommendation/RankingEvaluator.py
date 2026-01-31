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
class RankingEvaluator(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEvaluator):
    """
    Args:
        itemCol (str): Column of items
        k (int): number of items
        labelCol (str): label column name
        metricName (str): metric name in evaluation (ndcgAt|map|precisionAtk|recallAtK|diversityAtK|maxDiversity|mrr|fcp)
        nItems (long): number of items
        predictionCol (str): prediction column name
        ratingCol (str): Column of ratings
        userCol (str): Column of users
    """

    itemCol = Param(Params._dummy(), "itemCol", "Column of items", typeConverter=TypeConverters.toString)
    
    k = Param(Params._dummy(), "k", "number of items", typeConverter=TypeConverters.toInt)
    
    labelCol = Param(Params._dummy(), "labelCol", "label column name", typeConverter=TypeConverters.toString)
    
    metricName = Param(Params._dummy(), "metricName", "metric name in evaluation (ndcgAt|map|precisionAtk|recallAtK|diversityAtK|maxDiversity|mrr|fcp)", typeConverter=TypeConverters.toString)
    
    nItems = Param(Params._dummy(), "nItems", "number of items")
    
    predictionCol = Param(Params._dummy(), "predictionCol", "prediction column name", typeConverter=TypeConverters.toString)
    
    ratingCol = Param(Params._dummy(), "ratingCol", "Column of ratings", typeConverter=TypeConverters.toString)
    
    userCol = Param(Params._dummy(), "userCol", "Column of users", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        itemCol=None,
        k=10,
        labelCol="label",
        metricName="ndcgAt",
        nItems=-1,
        predictionCol="prediction",
        ratingCol=None,
        userCol=None
        ):
        super(RankingEvaluator, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.recommendation.RankingEvaluator", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(k=10)
        self._setDefault(labelCol="label")
        self._setDefault(metricName="ndcgAt")
        self._setDefault(nItems=-1)
        self._setDefault(predictionCol="prediction")
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
        itemCol=None,
        k=10,
        labelCol="label",
        metricName="ndcgAt",
        nItems=-1,
        predictionCol="prediction",
        ratingCol=None,
        userCol=None
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
        return "com.microsoft.azure.synapse.ml.recommendation.RankingEvaluator"

    @staticmethod
    def _from_java(java_stage):
        module_name=RankingEvaluator.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".RankingEvaluator"
        return from_java(java_stage, module_name)

    def setItemCol(self, value):
        """
        Args:
            itemCol: Column of items
        """
        self._set(itemCol=value)
        return self
    
    def setK(self, value):
        """
        Args:
            k: number of items
        """
        self._set(k=value)
        return self
    
    def setLabelCol(self, value):
        """
        Args:
            labelCol: label column name
        """
        self._set(labelCol=value)
        return self
    
    def setMetricName(self, value):
        """
        Args:
            metricName: metric name in evaluation (ndcgAt|map|precisionAtk|recallAtK|diversityAtK|maxDiversity|mrr|fcp)
        """
        self._set(metricName=value)
        return self
    
    def setNItems(self, value):
        """
        Args:
            nItems: number of items
        """
        self._set(nItems=value)
        return self
    
    def setPredictionCol(self, value):
        """
        Args:
            predictionCol: prediction column name
        """
        self._set(predictionCol=value)
        return self
    
    def setRatingCol(self, value):
        """
        Args:
            ratingCol: Column of ratings
        """
        self._set(ratingCol=value)
        return self
    
    def setUserCol(self, value):
        """
        Args:
            userCol: Column of users
        """
        self._set(userCol=value)
        return self

    
    def getItemCol(self):
        """
        Returns:
            itemCol: Column of items
        """
        return self.getOrDefault(self.itemCol)
    
    
    def getK(self):
        """
        Returns:
            k: number of items
        """
        return self.getOrDefault(self.k)
    
    
    def getLabelCol(self):
        """
        Returns:
            labelCol: label column name
        """
        return self.getOrDefault(self.labelCol)
    
    
    def getMetricName(self):
        """
        Returns:
            metricName: metric name in evaluation (ndcgAt|map|precisionAtk|recallAtK|diversityAtK|maxDiversity|mrr|fcp)
        """
        return self.getOrDefault(self.metricName)
    
    
    def getNItems(self):
        """
        Returns:
            nItems: number of items
        """
        return self.getOrDefault(self.nItems)
    
    
    def getPredictionCol(self):
        """
        Returns:
            predictionCol: prediction column name
        """
        return self.getOrDefault(self.predictionCol)
    
    
    def getRatingCol(self):
        """
        Returns:
            ratingCol: Column of ratings
        """
        return self.getOrDefault(self.ratingCol)
    
    
    def getUserCol(self):
        """
        Returns:
            userCol: Column of users
        """
        return self.getOrDefault(self.userCol)

    

    
        