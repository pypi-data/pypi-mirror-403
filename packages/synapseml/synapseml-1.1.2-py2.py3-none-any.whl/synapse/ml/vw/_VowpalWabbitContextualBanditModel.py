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
class _VowpalWabbitContextualBanditModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        additionalFeatures (list): Additional feature columns
        additionalSharedFeatures (list): Additional namespaces for the shared example
        featuresCol (str): features column name
        hashSeed (int): Seed used for hashing
        ignoreNamespaces (str): Namespaces to be ignored (first letter only)
        initialModel (list): Initial model to start from
        interactions (list): Interaction terms as specified by -q
        l1 (float): l_1 lambda
        l2 (float): l_2 lambda
        labelCol (str): label column name
        learningRate (float): Learning rate
        model (list): The VW model....
        numBits (int): Number of bits used
        numPasses (int): Number of passes over the data
        numSyncsPerPass (int): Number of times weights should be synchronized within each pass. 0 disables inter-pass synchronization.
        oneStepAheadPredictions (object): 1-step ahead predictions collected during training
        passThroughArgs (str): VW command line arguments passed
        performanceStatistics (object): Performance statistics collected during training
        powerT (float): t power value
        predictionCol (str): prediction column name
        predictionIdCol (str): The ID column returned for predictions
        rawPredictionCol (str): raw prediction (a.k.a. confidence) column name
        sharedCol (str): Column name of shared features
        splitCol (str): The column to split on for inter-pass sync
        splitColValues (list): Sorted values to use to select each split to train on. If not specified, computed from data
        testArgs (str): Additional arguments passed to VW at test time
        useBarrierExecutionMode (bool): Use barrier execution mode, on by default.
        weightCol (str): The name of the weight column
    """

    additionalFeatures = Param(Params._dummy(), "additionalFeatures", "Additional feature columns", typeConverter=TypeConverters.toListString)
    
    additionalSharedFeatures = Param(Params._dummy(), "additionalSharedFeatures", "Additional namespaces for the shared example", typeConverter=TypeConverters.toListString)
    
    featuresCol = Param(Params._dummy(), "featuresCol", "features column name", typeConverter=TypeConverters.toString)
    
    hashSeed = Param(Params._dummy(), "hashSeed", "Seed used for hashing", typeConverter=TypeConverters.toInt)
    
    ignoreNamespaces = Param(Params._dummy(), "ignoreNamespaces", "Namespaces to be ignored (first letter only)", typeConverter=TypeConverters.toString)
    
    initialModel = Param(Params._dummy(), "initialModel", "Initial model to start from")
    
    interactions = Param(Params._dummy(), "interactions", "Interaction terms as specified by -q", typeConverter=TypeConverters.toListString)
    
    l1 = Param(Params._dummy(), "l1", "l_1 lambda", typeConverter=TypeConverters.toFloat)
    
    l2 = Param(Params._dummy(), "l2", "l_2 lambda", typeConverter=TypeConverters.toFloat)
    
    labelCol = Param(Params._dummy(), "labelCol", "label column name", typeConverter=TypeConverters.toString)
    
    learningRate = Param(Params._dummy(), "learningRate", "Learning rate", typeConverter=TypeConverters.toFloat)
    
    model = Param(Params._dummy(), "model", "The VW model....")
    
    numBits = Param(Params._dummy(), "numBits", "Number of bits used", typeConverter=TypeConverters.toInt)
    
    numPasses = Param(Params._dummy(), "numPasses", "Number of passes over the data", typeConverter=TypeConverters.toInt)
    
    numSyncsPerPass = Param(Params._dummy(), "numSyncsPerPass", "Number of times weights should be synchronized within each pass. 0 disables inter-pass synchronization.", typeConverter=TypeConverters.toInt)
    
    oneStepAheadPredictions = Param(Params._dummy(), "oneStepAheadPredictions", "1-step ahead predictions collected during training")
    
    passThroughArgs = Param(Params._dummy(), "passThroughArgs", "VW command line arguments passed", typeConverter=TypeConverters.toString)
    
    performanceStatistics = Param(Params._dummy(), "performanceStatistics", "Performance statistics collected during training")
    
    powerT = Param(Params._dummy(), "powerT", "t power value", typeConverter=TypeConverters.toFloat)
    
    predictionCol = Param(Params._dummy(), "predictionCol", "prediction column name", typeConverter=TypeConverters.toString)
    
    predictionIdCol = Param(Params._dummy(), "predictionIdCol", "The ID column returned for predictions", typeConverter=TypeConverters.toString)
    
    rawPredictionCol = Param(Params._dummy(), "rawPredictionCol", "raw prediction (a.k.a. confidence) column name", typeConverter=TypeConverters.toString)
    
    sharedCol = Param(Params._dummy(), "sharedCol", "Column name of shared features", typeConverter=TypeConverters.toString)
    
    splitCol = Param(Params._dummy(), "splitCol", "The column to split on for inter-pass sync", typeConverter=TypeConverters.toString)
    
    splitColValues = Param(Params._dummy(), "splitColValues", "Sorted values to use to select each split to train on. If not specified, computed from data", typeConverter=TypeConverters.toListString)
    
    testArgs = Param(Params._dummy(), "testArgs", "Additional arguments passed to VW at test time", typeConverter=TypeConverters.toString)
    
    useBarrierExecutionMode = Param(Params._dummy(), "useBarrierExecutionMode", "Use barrier execution mode, on by default.", typeConverter=TypeConverters.toBoolean)
    
    weightCol = Param(Params._dummy(), "weightCol", "The name of the weight column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        additionalFeatures=[],
        additionalSharedFeatures=[],
        featuresCol="features",
        hashSeed=0,
        ignoreNamespaces=None,
        initialModel=None,
        interactions=None,
        l1=None,
        l2=None,
        labelCol="label",
        learningRate=None,
        model=None,
        numBits=18,
        numPasses=1,
        numSyncsPerPass=0,
        oneStepAheadPredictions=None,
        passThroughArgs="",
        performanceStatistics=None,
        powerT=None,
        predictionCol="prediction",
        predictionIdCol=None,
        rawPredictionCol="rawPrediction",
        sharedCol="shared",
        splitCol=None,
        splitColValues=None,
        testArgs="",
        useBarrierExecutionMode=True,
        weightCol=None
        ):
        super(_VowpalWabbitContextualBanditModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.vw.VowpalWabbitContextualBanditModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(additionalFeatures=[])
        self._setDefault(additionalSharedFeatures=[])
        self._setDefault(featuresCol="features")
        self._setDefault(hashSeed=0)
        self._setDefault(labelCol="label")
        self._setDefault(numBits=18)
        self._setDefault(numPasses=1)
        self._setDefault(numSyncsPerPass=0)
        self._setDefault(passThroughArgs="")
        self._setDefault(predictionCol="prediction")
        self._setDefault(rawPredictionCol="rawPrediction")
        self._setDefault(sharedCol="shared")
        self._setDefault(testArgs="")
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
        additionalSharedFeatures=[],
        featuresCol="features",
        hashSeed=0,
        ignoreNamespaces=None,
        initialModel=None,
        interactions=None,
        l1=None,
        l2=None,
        labelCol="label",
        learningRate=None,
        model=None,
        numBits=18,
        numPasses=1,
        numSyncsPerPass=0,
        oneStepAheadPredictions=None,
        passThroughArgs="",
        performanceStatistics=None,
        powerT=None,
        predictionCol="prediction",
        predictionIdCol=None,
        rawPredictionCol="rawPrediction",
        sharedCol="shared",
        splitCol=None,
        splitColValues=None,
        testArgs="",
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
        return "com.microsoft.azure.synapse.ml.vw.VowpalWabbitContextualBanditModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_VowpalWabbitContextualBanditModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".VowpalWabbitContextualBanditModel"
        return from_java(java_stage, module_name)

    def setAdditionalFeatures(self, value):
        """
        Args:
            additionalFeatures: Additional feature columns
        """
        self._set(additionalFeatures=value)
        return self
    
    def setAdditionalSharedFeatures(self, value):
        """
        Args:
            additionalSharedFeatures: Additional namespaces for the shared example
        """
        self._set(additionalSharedFeatures=value)
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
    
    def setLearningRate(self, value):
        """
        Args:
            learningRate: Learning rate
        """
        self._set(learningRate=value)
        return self
    
    def setModel(self, value):
        """
        Args:
            model: The VW model....
        """
        self._set(model=value)
        return self
    
    def setNumBits(self, value):
        """
        Args:
            numBits: Number of bits used
        """
        self._set(numBits=value)
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
    
    def setOneStepAheadPredictions(self, value):
        """
        Args:
            oneStepAheadPredictions: 1-step ahead predictions collected during training
        """
        self._set(oneStepAheadPredictions=value)
        return self
    
    def setPassThroughArgs(self, value):
        """
        Args:
            passThroughArgs: VW command line arguments passed
        """
        self._set(passThroughArgs=value)
        return self
    
    def setPerformanceStatistics(self, value):
        """
        Args:
            performanceStatistics: Performance statistics collected during training
        """
        self._set(performanceStatistics=value)
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
    
    def setRawPredictionCol(self, value):
        """
        Args:
            rawPredictionCol: raw prediction (a.k.a. confidence) column name
        """
        self._set(rawPredictionCol=value)
        return self
    
    def setSharedCol(self, value):
        """
        Args:
            sharedCol: Column name of shared features
        """
        self._set(sharedCol=value)
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
    
    def setTestArgs(self, value):
        """
        Args:
            testArgs: Additional arguments passed to VW at test time
        """
        self._set(testArgs=value)
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
    
    
    def getAdditionalSharedFeatures(self):
        """
        Returns:
            additionalSharedFeatures: Additional namespaces for the shared example
        """
        return self.getOrDefault(self.additionalSharedFeatures)
    
    
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
    
    
    def getLearningRate(self):
        """
        Returns:
            learningRate: Learning rate
        """
        return self.getOrDefault(self.learningRate)
    
    
    def getModel(self):
        """
        Returns:
            model: The VW model....
        """
        return self.getOrDefault(self.model)
    
    
    def getNumBits(self):
        """
        Returns:
            numBits: Number of bits used
        """
        return self.getOrDefault(self.numBits)
    
    
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
    
    
    def getOneStepAheadPredictions(self):
        """
        Returns:
            oneStepAheadPredictions: 1-step ahead predictions collected during training
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getOneStepAheadPredictions(), sql_ctx)
    
    
    def getPassThroughArgs(self):
        """
        Returns:
            passThroughArgs: VW command line arguments passed
        """
        return self.getOrDefault(self.passThroughArgs)
    
    
    def getPerformanceStatistics(self):
        """
        Returns:
            performanceStatistics: Performance statistics collected during training
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getPerformanceStatistics(), sql_ctx)
    
    
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
    
    
    def getRawPredictionCol(self):
        """
        Returns:
            rawPredictionCol: raw prediction (a.k.a. confidence) column name
        """
        return self.getOrDefault(self.rawPredictionCol)
    
    
    def getSharedCol(self):
        """
        Returns:
            sharedCol: Column name of shared features
        """
        return self.getOrDefault(self.sharedCol)
    
    
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
    
    
    def getTestArgs(self):
        """
        Returns:
            testArgs: Additional arguments passed to VW at test time
        """
        return self.getOrDefault(self.testArgs)
    
    
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

    

    
        