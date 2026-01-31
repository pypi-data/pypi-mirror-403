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
class _VowpalWabbitRegressionModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        additionalFeatures (list): Additional feature columns
        featuresCol (str): features column name
        labelCol (str): label column name
        model (list): The VW model....
        oneStepAheadPredictions (object): 1-step ahead predictions collected during training
        performanceStatistics (object): Performance statistics collected during training
        predictionCol (str): prediction column name
        rawPredictionCol (str): raw prediction (a.k.a. confidence) column name
        testArgs (str): Additional arguments passed to VW at test time
    """

    additionalFeatures = Param(Params._dummy(), "additionalFeatures", "Additional feature columns", typeConverter=TypeConverters.toListString)
    
    featuresCol = Param(Params._dummy(), "featuresCol", "features column name", typeConverter=TypeConverters.toString)
    
    labelCol = Param(Params._dummy(), "labelCol", "label column name", typeConverter=TypeConverters.toString)
    
    model = Param(Params._dummy(), "model", "The VW model....")
    
    oneStepAheadPredictions = Param(Params._dummy(), "oneStepAheadPredictions", "1-step ahead predictions collected during training")
    
    performanceStatistics = Param(Params._dummy(), "performanceStatistics", "Performance statistics collected during training")
    
    predictionCol = Param(Params._dummy(), "predictionCol", "prediction column name", typeConverter=TypeConverters.toString)
    
    rawPredictionCol = Param(Params._dummy(), "rawPredictionCol", "raw prediction (a.k.a. confidence) column name", typeConverter=TypeConverters.toString)
    
    testArgs = Param(Params._dummy(), "testArgs", "Additional arguments passed to VW at test time", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        additionalFeatures=None,
        featuresCol="features",
        labelCol="label",
        model=None,
        oneStepAheadPredictions=None,
        performanceStatistics=None,
        predictionCol="prediction",
        rawPredictionCol="rawPrediction",
        testArgs=""
        ):
        super(_VowpalWabbitRegressionModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.vw.VowpalWabbitRegressionModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(featuresCol="features")
        self._setDefault(labelCol="label")
        self._setDefault(predictionCol="prediction")
        self._setDefault(rawPredictionCol="rawPrediction")
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
        additionalFeatures=None,
        featuresCol="features",
        labelCol="label",
        model=None,
        oneStepAheadPredictions=None,
        performanceStatistics=None,
        predictionCol="prediction",
        rawPredictionCol="rawPrediction",
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
        return "com.microsoft.azure.synapse.ml.vw.VowpalWabbitRegressionModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_VowpalWabbitRegressionModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".VowpalWabbitRegressionModel"
        return from_java(java_stage, module_name)

    def setAdditionalFeatures(self, value):
        """
        Args:
            additionalFeatures: Additional feature columns
        """
        self._set(additionalFeatures=value)
        return self
    
    def setFeaturesCol(self, value):
        """
        Args:
            featuresCol: features column name
        """
        self._set(featuresCol=value)
        return self
    
    def setLabelCol(self, value):
        """
        Args:
            labelCol: label column name
        """
        self._set(labelCol=value)
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
    
    def setPredictionCol(self, value):
        """
        Args:
            predictionCol: prediction column name
        """
        self._set(predictionCol=value)
        return self
    
    def setRawPredictionCol(self, value):
        """
        Args:
            rawPredictionCol: raw prediction (a.k.a. confidence) column name
        """
        self._set(rawPredictionCol=value)
        return self
    
    def setTestArgs(self, value):
        """
        Args:
            testArgs: Additional arguments passed to VW at test time
        """
        self._set(testArgs=value)
        return self

    
    def getAdditionalFeatures(self):
        """
        Returns:
            additionalFeatures: Additional feature columns
        """
        return self.getOrDefault(self.additionalFeatures)
    
    
    def getFeaturesCol(self):
        """
        Returns:
            featuresCol: features column name
        """
        return self.getOrDefault(self.featuresCol)
    
    
    def getLabelCol(self):
        """
        Returns:
            labelCol: label column name
        """
        return self.getOrDefault(self.labelCol)
    
    
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
    
    
    def getPredictionCol(self):
        """
        Returns:
            predictionCol: prediction column name
        """
        return self.getOrDefault(self.predictionCol)
    
    
    def getRawPredictionCol(self):
        """
        Returns:
            rawPredictionCol: raw prediction (a.k.a. confidence) column name
        """
        return self.getOrDefault(self.rawPredictionCol)
    
    
    def getTestArgs(self):
        """
        Returns:
            testArgs: Additional arguments passed to VW at test time
        """
        return self.getOrDefault(self.testArgs)

    

    
        