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
from synapse.ml.vw.VowpalWabbitClassificationModel import VowpalWabbitClassificationModel

@inherit_doc
class _VowpalWabbitClassifier(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        additionalFeatures (list): Additional feature columns
        featuresCol (str): features column name
        hashSeed (int): Seed used for hashing
        ignoreNamespaces (str): Namespaces to be ignored (first letter only)
        initialModel (list): Initial model to start from
        interactions (list): Interaction terms as specified by -q
        l1 (float): l_1 lambda
        l2 (float): l_2 lambda
        labelCol (str): label column name
        labelConversion (bool): Convert 0/1 Spark ML style labels to -1/1 VW style labels. Defaults to false.
        learningRate (float): Learning rate
        numBits (int): Number of bits used
        numClasses (int): Number of classes. Defaults to binary. Needs to match oaa/csoaa/multilabel_oaa/...
        numPasses (int): Number of passes over the data
        numSyncsPerPass (int): Number of times weights should be synchronized within each pass. 0 disables inter-pass synchronization.
        passThroughArgs (str): VW command line arguments passed
        powerT (float): t power value
        predictionCol (str): prediction column name
        predictionIdCol (str): The ID column returned for predictions
        probabilityCol (str): Column name for predicted class conditional probabilities. Note: Not all models output well-calibrated probability estimates! These probabilities should be treated as confidences, not precise probabilities
        rawPredictionCol (str): raw prediction (a.k.a. confidence) column name
        splitCol (str): The column to split on for inter-pass sync
        splitColValues (list): Sorted values to use to select each split to train on. If not specified, computed from data
        thresholds (list): Thresholds in multi-class classification to adjust the probability of predicting each class. Array must have length equal to the number of classes, with values > 0 excepting that at most one value may be 0. The class with largest value p/t is predicted, where p is the original probability of that class and t is the class's threshold
        useBarrierExecutionMode (bool): Use barrier execution mode, on by default.
        weightCol (str): The name of the weight column
    """

    additionalFeatures = Param(Params._dummy(), "additionalFeatures", "Additional feature columns", typeConverter=TypeConverters.toListString)
    
    featuresCol = Param(Params._dummy(), "featuresCol", "features column name", typeConverter=TypeConverters.toString)
    
    hashSeed = Param(Params._dummy(), "hashSeed", "Seed used for hashing", typeConverter=TypeConverters.toInt)
    
    ignoreNamespaces = Param(Params._dummy(), "ignoreNamespaces", "Namespaces to be ignored (first letter only)", typeConverter=TypeConverters.toString)
    
    initialModel = Param(Params._dummy(), "initialModel", "Initial model to start from")
    
    interactions = Param(Params._dummy(), "interactions", "Interaction terms as specified by -q", typeConverter=TypeConverters.toListString)
    
    l1 = Param(Params._dummy(), "l1", "l_1 lambda", typeConverter=TypeConverters.toFloat)
    
    l2 = Param(Params._dummy(), "l2", "l_2 lambda", typeConverter=TypeConverters.toFloat)
    
    labelCol = Param(Params._dummy(), "labelCol", "label column name", typeConverter=TypeConverters.toString)
    
    labelConversion = Param(Params._dummy(), "labelConversion", "Convert 0/1 Spark ML style labels to -1/1 VW style labels. Defaults to false.", typeConverter=TypeConverters.toBoolean)
    
    learningRate = Param(Params._dummy(), "learningRate", "Learning rate", typeConverter=TypeConverters.toFloat)
    
    numBits = Param(Params._dummy(), "numBits", "Number of bits used", typeConverter=TypeConverters.toInt)
    
    numClasses = Param(Params._dummy(), "numClasses", "Number of classes. Defaults to binary. Needs to match oaa/csoaa/multilabel_oaa/...", typeConverter=TypeConverters.toInt)
    
    numPasses = Param(Params._dummy(), "numPasses", "Number of passes over the data", typeConverter=TypeConverters.toInt)
    
    numSyncsPerPass = Param(Params._dummy(), "numSyncsPerPass", "Number of times weights should be synchronized within each pass. 0 disables inter-pass synchronization.", typeConverter=TypeConverters.toInt)
    
    passThroughArgs = Param(Params._dummy(), "passThroughArgs", "VW command line arguments passed", typeConverter=TypeConverters.toString)
    
    powerT = Param(Params._dummy(), "powerT", "t power value", typeConverter=TypeConverters.toFloat)
    
    predictionCol = Param(Params._dummy(), "predictionCol", "prediction column name", typeConverter=TypeConverters.toString)
    
    predictionIdCol = Param(Params._dummy(), "predictionIdCol", "The ID column returned for predictions", typeConverter=TypeConverters.toString)
    
    probabilityCol = Param(Params._dummy(), "probabilityCol", "Column name for predicted class conditional probabilities. Note: Not all models output well-calibrated probability estimates! These probabilities should be treated as confidences, not precise probabilities", typeConverter=TypeConverters.toString)
    
    rawPredictionCol = Param(Params._dummy(), "rawPredictionCol", "raw prediction (a.k.a. confidence) column name", typeConverter=TypeConverters.toString)
    
    splitCol = Param(Params._dummy(), "splitCol", "The column to split on for inter-pass sync", typeConverter=TypeConverters.toString)
    
    splitColValues = Param(Params._dummy(), "splitColValues", "Sorted values to use to select each split to train on. If not specified, computed from data", typeConverter=TypeConverters.toListString)
    
    thresholds = Param(Params._dummy(), "thresholds", "Thresholds in multi-class classification to adjust the probability of predicting each class. Array must have length equal to the number of classes, with values > 0 excepting that at most one value may be 0. The class with largest value p/t is predicted, where p is the original probability of that class and t is the class's threshold", typeConverter=TypeConverters.toListFloat)
    
    useBarrierExecutionMode = Param(Params._dummy(), "useBarrierExecutionMode", "Use barrier execution mode, on by default.", typeConverter=TypeConverters.toBoolean)
    
    weightCol = Param(Params._dummy(), "weightCol", "The name of the weight column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        additionalFeatures=[],
        featuresCol="features",
        hashSeed=0,
        ignoreNamespaces=None,
        initialModel=None,
        interactions=None,
        l1=None,
        l2=None,
        labelCol="label",
        labelConversion=False,
        learningRate=None,
        numBits=18,
        numClasses=2,
        numPasses=1,
        numSyncsPerPass=0,
        passThroughArgs="",
        powerT=None,
        predictionCol="prediction",
        predictionIdCol=None,
        probabilityCol="probability",
        rawPredictionCol="rawPrediction",
        splitCol=None,
        splitColValues=None,
        thresholds=None,
        useBarrierExecutionMode=True,
        weightCol=None
        ):
        super(_VowpalWabbitClassifier, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.vw.VowpalWabbitClassifier", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(additionalFeatures=[])
        self._setDefault(featuresCol="features")
        self._setDefault(hashSeed=0)
        self._setDefault(labelCol="label")
        self._setDefault(labelConversion=False)
        self._setDefault(numBits=18)
        self._setDefault(numClasses=2)
        self._setDefault(numPasses=1)
        self._setDefault(numSyncsPerPass=0)
        self._setDefault(passThroughArgs="")
        self._setDefault(predictionCol="prediction")
        self._setDefault(probabilityCol="probability")
        self._setDefault(rawPredictionCol="rawPrediction")
        self._setDefault(useBarrierExecutionMode=True)
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
        additionalFeatures=[],
        featuresCol="features",
        hashSeed=0,
        ignoreNamespaces=None,
        initialModel=None,
        interactions=None,
        l1=None,
        l2=None,
        labelCol="label",
        labelConversion=False,
        learningRate=None,
        numBits=18,
        numClasses=2,
        numPasses=1,
        numSyncsPerPass=0,
        passThroughArgs="",
        powerT=None,
        predictionCol="prediction",
        predictionIdCol=None,
        probabilityCol="probability",
        rawPredictionCol="rawPrediction",
        splitCol=None,
        splitColValues=None,
        thresholds=None,
        useBarrierExecutionMode=True,
        weightCol=None
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
        return "com.microsoft.azure.synapse.ml.vw.VowpalWabbitClassifier"

    @staticmethod
    def _from_java(java_stage):
        module_name=_VowpalWabbitClassifier.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".VowpalWabbitClassifier"
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
    
    def setHashSeed(self, value):
        """
        Args:
            hashSeed: Seed used for hashing
        """
        self._set(hashSeed=value)
        return self
    
    def setIgnoreNamespaces(self, value):
        """
        Args:
            ignoreNamespaces: Namespaces to be ignored (first letter only)
        """
        self._set(ignoreNamespaces=value)
        return self
    
    def setInitialModel(self, value):
        """
        Args:
            initialModel: Initial model to start from
        """
        self._set(initialModel=value)
        return self
    
    def setInteractions(self, value):
        """
        Args:
            interactions: Interaction terms as specified by -q
        """
        self._set(interactions=value)
        return self
    
    def setL1(self, value):
        """
        Args:
            l1: l_1 lambda
        """
        self._set(l1=value)
        return self
    
    def setL2(self, value):
        """
        Args:
            l2: l_2 lambda
        """
        self._set(l2=value)
        return self
    
    def setLabelCol(self, value):
        """
        Args:
            labelCol: label column name
        """
        self._set(labelCol=value)
        return self
    
    def setLabelConversion(self, value):
        """
        Args:
            labelConversion: Convert 0/1 Spark ML style labels to -1/1 VW style labels. Defaults to false.
        """
        self._set(labelConversion=value)
        return self
    
    def setLearningRate(self, value):
        """
        Args:
            learningRate: Learning rate
        """
        self._set(learningRate=value)
        return self
    
    def setNumBits(self, value):
        """
        Args:
            numBits: Number of bits used
        """
        self._set(numBits=value)
        return self
    
    def setNumClasses(self, value):
        """
        Args:
            numClasses: Number of classes. Defaults to binary. Needs to match oaa/csoaa/multilabel_oaa/...
        """
        self._set(numClasses=value)
        return self
    
    def setNumPasses(self, value):
        """
        Args:
            numPasses: Number of passes over the data
        """
        self._set(numPasses=value)
        return self
    
    def setNumSyncsPerPass(self, value):
        """
        Args:
            numSyncsPerPass: Number of times weights should be synchronized within each pass. 0 disables inter-pass synchronization.
        """
        self._set(numSyncsPerPass=value)
        return self
    
    def setPassThroughArgs(self, value):
        """
        Args:
            passThroughArgs: VW command line arguments passed
        """
        self._set(passThroughArgs=value)
        return self
    
    def setPowerT(self, value):
        """
        Args:
            powerT: t power value
        """
        self._set(powerT=value)
        return self
    
    def setPredictionCol(self, value):
        """
        Args:
            predictionCol: prediction column name
        """
        self._set(predictionCol=value)
        return self
    
    def setPredictionIdCol(self, value):
        """
        Args:
            predictionIdCol: The ID column returned for predictions
        """
        self._set(predictionIdCol=value)
        return self
    
    def setProbabilityCol(self, value):
        """
        Args:
            probabilityCol: Column name for predicted class conditional probabilities. Note: Not all models output well-calibrated probability estimates! These probabilities should be treated as confidences, not precise probabilities
        """
        self._set(probabilityCol=value)
        return self
    
    def setRawPredictionCol(self, value):
        """
        Args:
            rawPredictionCol: raw prediction (a.k.a. confidence) column name
        """
        self._set(rawPredictionCol=value)
        return self
    
    def setSplitCol(self, value):
        """
        Args:
            splitCol: The column to split on for inter-pass sync
        """
        self._set(splitCol=value)
        return self
    
    def setSplitColValues(self, value):
        """
        Args:
            splitColValues: Sorted values to use to select each split to train on. If not specified, computed from data
        """
        self._set(splitColValues=value)
        return self
    
    def setThresholds(self, value):
        """
        Args:
            thresholds: Thresholds in multi-class classification to adjust the probability of predicting each class. Array must have length equal to the number of classes, with values > 0 excepting that at most one value may be 0. The class with largest value p/t is predicted, where p is the original probability of that class and t is the class's threshold
        """
        self._set(thresholds=value)
        return self
    
    def setUseBarrierExecutionMode(self, value):
        """
        Args:
            useBarrierExecutionMode: Use barrier execution mode, on by default.
        """
        self._set(useBarrierExecutionMode=value)
        return self
    
    def setWeightCol(self, value):
        """
        Args:
            weightCol: The name of the weight column
        """
        self._set(weightCol=value)
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
    
    
    def getHashSeed(self):
        """
        Returns:
            hashSeed: Seed used for hashing
        """
        return self.getOrDefault(self.hashSeed)
    
    
    def getIgnoreNamespaces(self):
        """
        Returns:
            ignoreNamespaces: Namespaces to be ignored (first letter only)
        """
        return self.getOrDefault(self.ignoreNamespaces)
    
    
    def getInitialModel(self):
        """
        Returns:
            initialModel: Initial model to start from
        """
        return self.getOrDefault(self.initialModel)
    
    
    def getInteractions(self):
        """
        Returns:
            interactions: Interaction terms as specified by -q
        """
        return self.getOrDefault(self.interactions)
    
    
    def getL1(self):
        """
        Returns:
            l1: l_1 lambda
        """
        return self.getOrDefault(self.l1)
    
    
    def getL2(self):
        """
        Returns:
            l2: l_2 lambda
        """
        return self.getOrDefault(self.l2)
    
    
    def getLabelCol(self):
        """
        Returns:
            labelCol: label column name
        """
        return self.getOrDefault(self.labelCol)
    
    
    def getLabelConversion(self):
        """
        Returns:
            labelConversion: Convert 0/1 Spark ML style labels to -1/1 VW style labels. Defaults to false.
        """
        return self.getOrDefault(self.labelConversion)
    
    
    def getLearningRate(self):
        """
        Returns:
            learningRate: Learning rate
        """
        return self.getOrDefault(self.learningRate)
    
    
    def getNumBits(self):
        """
        Returns:
            numBits: Number of bits used
        """
        return self.getOrDefault(self.numBits)
    
    
    def getNumClasses(self):
        """
        Returns:
            numClasses: Number of classes. Defaults to binary. Needs to match oaa/csoaa/multilabel_oaa/...
        """
        return self.getOrDefault(self.numClasses)
    
    
    def getNumPasses(self):
        """
        Returns:
            numPasses: Number of passes over the data
        """
        return self.getOrDefault(self.numPasses)
    
    
    def getNumSyncsPerPass(self):
        """
        Returns:
            numSyncsPerPass: Number of times weights should be synchronized within each pass. 0 disables inter-pass synchronization.
        """
        return self.getOrDefault(self.numSyncsPerPass)
    
    
    def getPassThroughArgs(self):
        """
        Returns:
            passThroughArgs: VW command line arguments passed
        """
        return self.getOrDefault(self.passThroughArgs)
    
    
    def getPowerT(self):
        """
        Returns:
            powerT: t power value
        """
        return self.getOrDefault(self.powerT)
    
    
    def getPredictionCol(self):
        """
        Returns:
            predictionCol: prediction column name
        """
        return self.getOrDefault(self.predictionCol)
    
    
    def getPredictionIdCol(self):
        """
        Returns:
            predictionIdCol: The ID column returned for predictions
        """
        return self.getOrDefault(self.predictionIdCol)
    
    
    def getProbabilityCol(self):
        """
        Returns:
            probabilityCol: Column name for predicted class conditional probabilities. Note: Not all models output well-calibrated probability estimates! These probabilities should be treated as confidences, not precise probabilities
        """
        return self.getOrDefault(self.probabilityCol)
    
    
    def getRawPredictionCol(self):
        """
        Returns:
            rawPredictionCol: raw prediction (a.k.a. confidence) column name
        """
        return self.getOrDefault(self.rawPredictionCol)
    
    
    def getSplitCol(self):
        """
        Returns:
            splitCol: The column to split on for inter-pass sync
        """
        return self.getOrDefault(self.splitCol)
    
    
    def getSplitColValues(self):
        """
        Returns:
            splitColValues: Sorted values to use to select each split to train on. If not specified, computed from data
        """
        return self.getOrDefault(self.splitColValues)
    
    
    def getThresholds(self):
        """
        Returns:
            thresholds: Thresholds in multi-class classification to adjust the probability of predicting each class. Array must have length equal to the number of classes, with values > 0 excepting that at most one value may be 0. The class with largest value p/t is predicted, where p is the original probability of that class and t is the class's threshold
        """
        return self.getOrDefault(self.thresholds)
    
    
    def getUseBarrierExecutionMode(self):
        """
        Returns:
            useBarrierExecutionMode: Use barrier execution mode, on by default.
        """
        return self.getOrDefault(self.useBarrierExecutionMode)
    
    
    def getWeightCol(self):
        """
        Returns:
            weightCol: The name of the weight column
        """
        return self.getOrDefault(self.weightCol)

    def _create_model(self, java_model):
        try:
            model = VowpalWabbitClassificationModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = VowpalWabbitClassificationModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        