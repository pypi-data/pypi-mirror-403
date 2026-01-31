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
class _LightGBMRankerModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        featuresCol (str): features column name
        featuresShapCol (str): Output SHAP vector column name after prediction containing the feature contribution values
        labelCol (str): label column name
        leafPredictionCol (str): Predicted leaf indices's column name
        lightGBMBooster (object): The trained LightGBM booster
        numIterations (int): Sets the total number of iterations used in the prediction.If <= 0, all iterations from ``start_iteration`` are used (no limits).
        predictDisableShapeCheck (bool): control whether or not LightGBM raises an error when you try to predict on data with a different number of features than the training data
        predictionCol (str): prediction column name
        startIteration (int): Sets the start index of the iteration to predict. If <= 0, starts from the first iteration.
    """

    featuresCol = Param(Params._dummy(), "featuresCol", "features column name", typeConverter=TypeConverters.toString)
    
    featuresShapCol = Param(Params._dummy(), "featuresShapCol", "Output SHAP vector column name after prediction containing the feature contribution values", typeConverter=TypeConverters.toString)
    
    labelCol = Param(Params._dummy(), "labelCol", "label column name", typeConverter=TypeConverters.toString)
    
    leafPredictionCol = Param(Params._dummy(), "leafPredictionCol", "Predicted leaf indices's column name", typeConverter=TypeConverters.toString)
    
    lightGBMBooster = Param(Params._dummy(), "lightGBMBooster", "The trained LightGBM booster")
    
    numIterations = Param(Params._dummy(), "numIterations", "Sets the total number of iterations used in the prediction.If <= 0, all iterations from ``start_iteration`` are used (no limits).", typeConverter=TypeConverters.toInt)
    
    predictDisableShapeCheck = Param(Params._dummy(), "predictDisableShapeCheck", "control whether or not LightGBM raises an error when you try to predict on data with a different number of features than the training data", typeConverter=TypeConverters.toBoolean)
    
    predictionCol = Param(Params._dummy(), "predictionCol", "prediction column name", typeConverter=TypeConverters.toString)
    
    startIteration = Param(Params._dummy(), "startIteration", "Sets the start index of the iteration to predict. If <= 0, starts from the first iteration.", typeConverter=TypeConverters.toInt)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        featuresCol="features",
        featuresShapCol="",
        labelCol="label",
        leafPredictionCol="",
        lightGBMBooster=None,
        numIterations=-1,
        predictDisableShapeCheck=False,
        predictionCol="prediction",
        startIteration=0
        ):
        super(_LightGBMRankerModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.lightgbm.LightGBMRankerModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(featuresCol="features")
        self._setDefault(featuresShapCol="")
        self._setDefault(labelCol="label")
        self._setDefault(leafPredictionCol="")
        self._setDefault(numIterations=-1)
        self._setDefault(predictDisableShapeCheck=False)
        self._setDefault(predictionCol="prediction")
        self._setDefault(startIteration=0)
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
        featuresCol="features",
        featuresShapCol="",
        labelCol="label",
        leafPredictionCol="",
        lightGBMBooster=None,
        numIterations=-1,
        predictDisableShapeCheck=False,
        predictionCol="prediction",
        startIteration=0
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
        return "com.microsoft.azure.synapse.ml.lightgbm.LightGBMRankerModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_LightGBMRankerModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".LightGBMRankerModel"
        return from_java(java_stage, module_name)

    def setFeaturesCol(self, value):
        """
        Args:
            featuresCol: features column name
        """
        self._set(featuresCol=value)
        return self
    
    def setFeaturesShapCol(self, value):
        """
        Args:
            featuresShapCol: Output SHAP vector column name after prediction containing the feature contribution values
        """
        self._set(featuresShapCol=value)
        return self
    
    def setLabelCol(self, value):
        """
        Args:
            labelCol: label column name
        """
        self._set(labelCol=value)
        return self
    
    def setLeafPredictionCol(self, value):
        """
        Args:
            leafPredictionCol: Predicted leaf indices's column name
        """
        self._set(leafPredictionCol=value)
        return self
    
    def setLightGBMBooster(self, value):
        """
        Args:
            lightGBMBooster: The trained LightGBM booster
        """
        self._set(lightGBMBooster=value)
        return self
    
    def setNumIterations(self, value):
        """
        Args:
            numIterations: Sets the total number of iterations used in the prediction.If <= 0, all iterations from ``start_iteration`` are used (no limits).
        """
        self._set(numIterations=value)
        return self
    
    def setPredictDisableShapeCheck(self, value):
        """
        Args:
            predictDisableShapeCheck: control whether or not LightGBM raises an error when you try to predict on data with a different number of features than the training data
        """
        self._set(predictDisableShapeCheck=value)
        return self
    
    def setPredictionCol(self, value):
        """
        Args:
            predictionCol: prediction column name
        """
        self._set(predictionCol=value)
        return self
    
    def setStartIteration(self, value):
        """
        Args:
            startIteration: Sets the start index of the iteration to predict. If <= 0, starts from the first iteration.
        """
        self._set(startIteration=value)
        return self

    
    def getFeaturesCol(self):
        """
        Returns:
            featuresCol: features column name
        """
        return self.getOrDefault(self.featuresCol)
    
    
    def getFeaturesShapCol(self):
        """
        Returns:
            featuresShapCol: Output SHAP vector column name after prediction containing the feature contribution values
        """
        return self.getOrDefault(self.featuresShapCol)
    
    
    def getLabelCol(self):
        """
        Returns:
            labelCol: label column name
        """
        return self.getOrDefault(self.labelCol)
    
    
    def getLeafPredictionCol(self):
        """
        Returns:
            leafPredictionCol: Predicted leaf indices's column name
        """
        return self.getOrDefault(self.leafPredictionCol)
    
    
    def getLightGBMBooster(self):
        """
        Returns:
            lightGBMBooster: The trained LightGBM booster
        """
        return self.getOrDefault(self.lightGBMBooster)
    
    
    def getNumIterations(self):
        """
        Returns:
            numIterations: Sets the total number of iterations used in the prediction.If <= 0, all iterations from ``start_iteration`` are used (no limits).
        """
        return self.getOrDefault(self.numIterations)
    
    
    def getPredictDisableShapeCheck(self):
        """
        Returns:
            predictDisableShapeCheck: control whether or not LightGBM raises an error when you try to predict on data with a different number of features than the training data
        """
        return self.getOrDefault(self.predictDisableShapeCheck)
    
    
    def getPredictionCol(self):
        """
        Returns:
            predictionCol: prediction column name
        """
        return self.getOrDefault(self.predictionCol)
    
    
    def getStartIteration(self):
        """
        Returns:
            startIteration: Sets the start index of the iteration to predict. If <= 0, starts from the first iteration.
        """
        return self.getOrDefault(self.startIteration)

    

    
        