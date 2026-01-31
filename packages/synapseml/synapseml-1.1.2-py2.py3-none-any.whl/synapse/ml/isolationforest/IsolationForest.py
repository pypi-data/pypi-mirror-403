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
from synapse.ml.isolationforest.IsolationForestModel import IsolationForestModel

@inherit_doc
class IsolationForest(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        bootstrap (bool): If true, draw sample for each tree with replacement. If false, do not sample with replacement.
        contamination (float): The fraction of outliers in the training data set. If this is set to 0.0, it speeds up the training and all predicted labels will be false. The model and outlier scores are otherwise unaffected by this parameter.
        contaminationError (float): The error allowed when calculating the threshold required to achieve the specified contamination fraction. The default is 0.0, which forces an exact calculation of the threshold. The exact calculation is slow and can fail for large datasets. If there are issues with the exact calculation, a good choice for this parameter is often 1% of the specified contamination value.
        featuresCol (str): The feature vector.
        maxFeatures (float): The number of features used to train each tree. If this value is between 0.0 and 1.0, then it is treated as a fraction. If it is >1.0, then it is treated as a count.
        maxSamples (float): The number of samples used to train each tree. If this value is between 0.0 and 1.0, then it is treated as a fraction. If it is >1.0, then it is treated as a count.
        numEstimators (int): The number of trees in the ensemble.
        predictionCol (str): The predicted label.
        randomSeed (long): The seed used for the random number generator.
        scoreCol (str): The outlier score.
    """

    bootstrap = Param(Params._dummy(), "bootstrap", "If true, draw sample for each tree with replacement. If false, do not sample with replacement.", typeConverter=TypeConverters.toBoolean)
    
    contamination = Param(Params._dummy(), "contamination", "The fraction of outliers in the training data set. If this is set to 0.0, it speeds up the training and all predicted labels will be false. The model and outlier scores are otherwise unaffected by this parameter.", typeConverter=TypeConverters.toFloat)
    
    contaminationError = Param(Params._dummy(), "contaminationError", "The error allowed when calculating the threshold required to achieve the specified contamination fraction. The default is 0.0, which forces an exact calculation of the threshold. The exact calculation is slow and can fail for large datasets. If there are issues with the exact calculation, a good choice for this parameter is often 1% of the specified contamination value.", typeConverter=TypeConverters.toFloat)
    
    featuresCol = Param(Params._dummy(), "featuresCol", "The feature vector.", typeConverter=TypeConverters.toString)
    
    maxFeatures = Param(Params._dummy(), "maxFeatures", "The number of features used to train each tree. If this value is between 0.0 and 1.0, then it is treated as a fraction. If it is >1.0, then it is treated as a count.", typeConverter=TypeConverters.toFloat)
    
    maxSamples = Param(Params._dummy(), "maxSamples", "The number of samples used to train each tree. If this value is between 0.0 and 1.0, then it is treated as a fraction. If it is >1.0, then it is treated as a count.", typeConverter=TypeConverters.toFloat)
    
    numEstimators = Param(Params._dummy(), "numEstimators", "The number of trees in the ensemble.", typeConverter=TypeConverters.toInt)
    
    predictionCol = Param(Params._dummy(), "predictionCol", "The predicted label.", typeConverter=TypeConverters.toString)
    
    randomSeed = Param(Params._dummy(), "randomSeed", "The seed used for the random number generator.")
    
    scoreCol = Param(Params._dummy(), "scoreCol", "The outlier score.", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        bootstrap=False,
        contamination=0.0,
        contaminationError=0.0,
        featuresCol="features",
        maxFeatures=1.0,
        maxSamples=256.0,
        numEstimators=100,
        predictionCol="predictedLabel",
        randomSeed=1,
        scoreCol="outlierScore"
        ):
        super(IsolationForest, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.isolationforest.IsolationForest", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(bootstrap=False)
        self._setDefault(contamination=0.0)
        self._setDefault(contaminationError=0.0)
        self._setDefault(featuresCol="features")
        self._setDefault(maxFeatures=1.0)
        self._setDefault(maxSamples=256.0)
        self._setDefault(numEstimators=100)
        self._setDefault(predictionCol="predictedLabel")
        self._setDefault(randomSeed=1)
        self._setDefault(scoreCol="outlierScore")
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
        bootstrap=False,
        contamination=0.0,
        contaminationError=0.0,
        featuresCol="features",
        maxFeatures=1.0,
        maxSamples=256.0,
        numEstimators=100,
        predictionCol="predictedLabel",
        randomSeed=1,
        scoreCol="outlierScore"
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
        return "com.microsoft.azure.synapse.ml.isolationforest.IsolationForest"

    @staticmethod
    def _from_java(java_stage):
        module_name=IsolationForest.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".IsolationForest"
        return from_java(java_stage, module_name)

    def setBootstrap(self, value):
        """
        Args:
            bootstrap: If true, draw sample for each tree with replacement. If false, do not sample with replacement.
        """
        self._set(bootstrap=value)
        return self
    
    def setContamination(self, value):
        """
        Args:
            contamination: The fraction of outliers in the training data set. If this is set to 0.0, it speeds up the training and all predicted labels will be false. The model and outlier scores are otherwise unaffected by this parameter.
        """
        self._set(contamination=value)
        return self
    
    def setContaminationError(self, value):
        """
        Args:
            contaminationError: The error allowed when calculating the threshold required to achieve the specified contamination fraction. The default is 0.0, which forces an exact calculation of the threshold. The exact calculation is slow and can fail for large datasets. If there are issues with the exact calculation, a good choice for this parameter is often 1% of the specified contamination value.
        """
        self._set(contaminationError=value)
        return self
    
    def setFeaturesCol(self, value):
        """
        Args:
            featuresCol: The feature vector.
        """
        self._set(featuresCol=value)
        return self
    
    def setMaxFeatures(self, value):
        """
        Args:
            maxFeatures: The number of features used to train each tree. If this value is between 0.0 and 1.0, then it is treated as a fraction. If it is >1.0, then it is treated as a count.
        """
        self._set(maxFeatures=value)
        return self
    
    def setMaxSamples(self, value):
        """
        Args:
            maxSamples: The number of samples used to train each tree. If this value is between 0.0 and 1.0, then it is treated as a fraction. If it is >1.0, then it is treated as a count.
        """
        self._set(maxSamples=value)
        return self
    
    def setNumEstimators(self, value):
        """
        Args:
            numEstimators: The number of trees in the ensemble.
        """
        self._set(numEstimators=value)
        return self
    
    def setPredictionCol(self, value):
        """
        Args:
            predictionCol: The predicted label.
        """
        self._set(predictionCol=value)
        return self
    
    def setRandomSeed(self, value):
        """
        Args:
            randomSeed: The seed used for the random number generator.
        """
        self._set(randomSeed=value)
        return self
    
    def setScoreCol(self, value):
        """
        Args:
            scoreCol: The outlier score.
        """
        self._set(scoreCol=value)
        return self

    
    def getBootstrap(self):
        """
        Returns:
            bootstrap: If true, draw sample for each tree with replacement. If false, do not sample with replacement.
        """
        return self.getOrDefault(self.bootstrap)
    
    
    def getContamination(self):
        """
        Returns:
            contamination: The fraction of outliers in the training data set. If this is set to 0.0, it speeds up the training and all predicted labels will be false. The model and outlier scores are otherwise unaffected by this parameter.
        """
        return self.getOrDefault(self.contamination)
    
    
    def getContaminationError(self):
        """
        Returns:
            contaminationError: The error allowed when calculating the threshold required to achieve the specified contamination fraction. The default is 0.0, which forces an exact calculation of the threshold. The exact calculation is slow and can fail for large datasets. If there are issues with the exact calculation, a good choice for this parameter is often 1% of the specified contamination value.
        """
        return self.getOrDefault(self.contaminationError)
    
    
    def getFeaturesCol(self):
        """
        Returns:
            featuresCol: The feature vector.
        """
        return self.getOrDefault(self.featuresCol)
    
    
    def getMaxFeatures(self):
        """
        Returns:
            maxFeatures: The number of features used to train each tree. If this value is between 0.0 and 1.0, then it is treated as a fraction. If it is >1.0, then it is treated as a count.
        """
        return self.getOrDefault(self.maxFeatures)
    
    
    def getMaxSamples(self):
        """
        Returns:
            maxSamples: The number of samples used to train each tree. If this value is between 0.0 and 1.0, then it is treated as a fraction. If it is >1.0, then it is treated as a count.
        """
        return self.getOrDefault(self.maxSamples)
    
    
    def getNumEstimators(self):
        """
        Returns:
            numEstimators: The number of trees in the ensemble.
        """
        return self.getOrDefault(self.numEstimators)
    
    
    def getPredictionCol(self):
        """
        Returns:
            predictionCol: The predicted label.
        """
        return self.getOrDefault(self.predictionCol)
    
    
    def getRandomSeed(self):
        """
        Returns:
            randomSeed: The seed used for the random number generator.
        """
        return self.getOrDefault(self.randomSeed)
    
    
    def getScoreCol(self):
        """
        Returns:
            scoreCol: The outlier score.
        """
        return self.getOrDefault(self.scoreCol)

    def _create_model(self, java_model):
        try:
            model = IsolationForestModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = IsolationForestModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        