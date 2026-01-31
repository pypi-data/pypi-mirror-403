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
class _SARModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        activityTimeFormat (str): Time format for events, default: yyyy/MM/dd'T'h:mm:ss
        alpha (float): alpha for implicit preference
        blockSize (int): block size for stacking input data in matrices. Data is stacked within partitions. If block size is more than remaining data in a partition then it is adjusted to the size of this data.
        checkpointInterval (int): set checkpoint interval (>= 1) or disable checkpoint (-1). E.g. 10 means that the cache will get checkpointed every 10 iterations. Note: this setting will be ignored if the checkpoint directory is not set in the SparkContext
        coldStartStrategy (str): strategy for dealing with unknown or new users/items at prediction time. This may be useful in cross-validation or production scenarios, for handling user/item ids the model has not seen in the training data. Supported values: nan,drop.
        finalStorageLevel (str): StorageLevel for ALS model factors.
        implicitPrefs (bool): whether to use implicit preference
        intermediateStorageLevel (str): StorageLevel for intermediate datasets. Cannot be 'NONE'.
        itemCol (str): column name for item ids. Ids must be within the integer value range.
        itemDataFrame (object): Time of activity
        maxIter (int): maximum number of iterations (>= 0)
        nonnegative (bool): whether to use nonnegative constraint for least squares
        numItemBlocks (int): number of item blocks
        numUserBlocks (int): number of user blocks
        predictionCol (str): prediction column name
        rank (int): rank of the factorization
        ratingCol (str): column name for ratings
        regParam (float): regularization parameter (>= 0)
        seed (long): random seed
        similarityFunction (str): Defines the similarity function to be used by the model. Lift favors serendipity, Co-occurrence favors predictability, and Jaccard is a nice compromise between the two.
        startTime (str): Set time custom now time if using historical data
        startTimeFormat (str): Format for start time
        supportThreshold (int): Minimum number of ratings per item
        timeCol (str): Time of activity
        timeDecayCoeff (int): Use to scale time decay coeff to different half life dur
        userCol (str): column name for user ids. Ids must be within the integer value range.
        userDataFrame (object): Time of activity
    """

    activityTimeFormat = Param(Params._dummy(), "activityTimeFormat", "Time format for events, default: yyyy/MM/dd'T'h:mm:ss", typeConverter=TypeConverters.toString)
    
    alpha = Param(Params._dummy(), "alpha", "alpha for implicit preference", typeConverter=TypeConverters.toFloat)
    
    blockSize = Param(Params._dummy(), "blockSize", "block size for stacking input data in matrices. Data is stacked within partitions. If block size is more than remaining data in a partition then it is adjusted to the size of this data.", typeConverter=TypeConverters.toInt)
    
    checkpointInterval = Param(Params._dummy(), "checkpointInterval", "set checkpoint interval (>= 1) or disable checkpoint (-1). E.g. 10 means that the cache will get checkpointed every 10 iterations. Note: this setting will be ignored if the checkpoint directory is not set in the SparkContext", typeConverter=TypeConverters.toInt)
    
    coldStartStrategy = Param(Params._dummy(), "coldStartStrategy", "strategy for dealing with unknown or new users/items at prediction time. This may be useful in cross-validation or production scenarios, for handling user/item ids the model has not seen in the training data. Supported values: nan,drop.", typeConverter=TypeConverters.toString)
    
    finalStorageLevel = Param(Params._dummy(), "finalStorageLevel", "StorageLevel for ALS model factors.", typeConverter=TypeConverters.toString)
    
    implicitPrefs = Param(Params._dummy(), "implicitPrefs", "whether to use implicit preference", typeConverter=TypeConverters.toBoolean)
    
    intermediateStorageLevel = Param(Params._dummy(), "intermediateStorageLevel", "StorageLevel for intermediate datasets. Cannot be 'NONE'.", typeConverter=TypeConverters.toString)
    
    itemCol = Param(Params._dummy(), "itemCol", "column name for item ids. Ids must be within the integer value range.", typeConverter=TypeConverters.toString)
    
    itemDataFrame = Param(Params._dummy(), "itemDataFrame", "Time of activity")
    
    maxIter = Param(Params._dummy(), "maxIter", "maximum number of iterations (>= 0)", typeConverter=TypeConverters.toInt)
    
    nonnegative = Param(Params._dummy(), "nonnegative", "whether to use nonnegative constraint for least squares", typeConverter=TypeConverters.toBoolean)
    
    numItemBlocks = Param(Params._dummy(), "numItemBlocks", "number of item blocks", typeConverter=TypeConverters.toInt)
    
    numUserBlocks = Param(Params._dummy(), "numUserBlocks", "number of user blocks", typeConverter=TypeConverters.toInt)
    
    predictionCol = Param(Params._dummy(), "predictionCol", "prediction column name", typeConverter=TypeConverters.toString)
    
    rank = Param(Params._dummy(), "rank", "rank of the factorization", typeConverter=TypeConverters.toInt)
    
    ratingCol = Param(Params._dummy(), "ratingCol", "column name for ratings", typeConverter=TypeConverters.toString)
    
    regParam = Param(Params._dummy(), "regParam", "regularization parameter (>= 0)", typeConverter=TypeConverters.toFloat)
    
    seed = Param(Params._dummy(), "seed", "random seed")
    
    similarityFunction = Param(Params._dummy(), "similarityFunction", "Defines the similarity function to be used by the model. Lift favors serendipity, Co-occurrence favors predictability, and Jaccard is a nice compromise between the two.", typeConverter=TypeConverters.toString)
    
    startTime = Param(Params._dummy(), "startTime", "Set time custom now time if using historical data", typeConverter=TypeConverters.toString)
    
    startTimeFormat = Param(Params._dummy(), "startTimeFormat", "Format for start time", typeConverter=TypeConverters.toString)
    
    supportThreshold = Param(Params._dummy(), "supportThreshold", "Minimum number of ratings per item", typeConverter=TypeConverters.toInt)
    
    timeCol = Param(Params._dummy(), "timeCol", "Time of activity", typeConverter=TypeConverters.toString)
    
    timeDecayCoeff = Param(Params._dummy(), "timeDecayCoeff", "Use to scale time decay coeff to different half life dur", typeConverter=TypeConverters.toInt)
    
    userCol = Param(Params._dummy(), "userCol", "column name for user ids. Ids must be within the integer value range.", typeConverter=TypeConverters.toString)
    
    userDataFrame = Param(Params._dummy(), "userDataFrame", "Time of activity")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        activityTimeFormat="yyyy/MM/dd'T'h:mm:ss",
        alpha=1.0,
        blockSize=4096,
        checkpointInterval=10,
        coldStartStrategy="nan",
        finalStorageLevel="MEMORY_AND_DISK",
        implicitPrefs=False,
        intermediateStorageLevel="MEMORY_AND_DISK",
        itemCol="item",
        itemDataFrame=None,
        maxIter=10,
        nonnegative=False,
        numItemBlocks=10,
        numUserBlocks=10,
        predictionCol="prediction",
        rank=10,
        ratingCol="rating",
        regParam=0.1,
        seed=-1453370660,
        similarityFunction="jaccard",
        startTime=None,
        startTimeFormat="EEE MMM dd HH:mm:ss Z yyyy",
        supportThreshold=4,
        timeCol="time",
        timeDecayCoeff=30,
        userCol="user",
        userDataFrame=None
        ):
        super(_SARModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.recommendation.SARModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(activityTimeFormat="yyyy/MM/dd'T'h:mm:ss")
        self._setDefault(alpha=1.0)
        self._setDefault(blockSize=4096)
        self._setDefault(checkpointInterval=10)
        self._setDefault(coldStartStrategy="nan")
        self._setDefault(finalStorageLevel="MEMORY_AND_DISK")
        self._setDefault(implicitPrefs=False)
        self._setDefault(intermediateStorageLevel="MEMORY_AND_DISK")
        self._setDefault(itemCol="item")
        self._setDefault(maxIter=10)
        self._setDefault(nonnegative=False)
        self._setDefault(numItemBlocks=10)
        self._setDefault(numUserBlocks=10)
        self._setDefault(predictionCol="prediction")
        self._setDefault(rank=10)
        self._setDefault(ratingCol="rating")
        self._setDefault(regParam=0.1)
        self._setDefault(seed=-1453370660)
        self._setDefault(similarityFunction="jaccard")
        self._setDefault(startTimeFormat="EEE MMM dd HH:mm:ss Z yyyy")
        self._setDefault(supportThreshold=4)
        self._setDefault(timeCol="time")
        self._setDefault(timeDecayCoeff=30)
        self._setDefault(userCol="user")
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
        activityTimeFormat="yyyy/MM/dd'T'h:mm:ss",
        alpha=1.0,
        blockSize=4096,
        checkpointInterval=10,
        coldStartStrategy="nan",
        finalStorageLevel="MEMORY_AND_DISK",
        implicitPrefs=False,
        intermediateStorageLevel="MEMORY_AND_DISK",
        itemCol="item",
        itemDataFrame=None,
        maxIter=10,
        nonnegative=False,
        numItemBlocks=10,
        numUserBlocks=10,
        predictionCol="prediction",
        rank=10,
        ratingCol="rating",
        regParam=0.1,
        seed=-1453370660,
        similarityFunction="jaccard",
        startTime=None,
        startTimeFormat="EEE MMM dd HH:mm:ss Z yyyy",
        supportThreshold=4,
        timeCol="time",
        timeDecayCoeff=30,
        userCol="user",
        userDataFrame=None
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
        return "com.microsoft.azure.synapse.ml.recommendation.SARModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_SARModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SARModel"
        return from_java(java_stage, module_name)

    def setActivityTimeFormat(self, value):
        """
        Args:
            activityTimeFormat: Time format for events, default: yyyy/MM/dd'T'h:mm:ss
        """
        self._set(activityTimeFormat=value)
        return self
    
    def setAlpha(self, value):
        """
        Args:
            alpha: alpha for implicit preference
        """
        self._set(alpha=value)
        return self
    
    def setBlockSize(self, value):
        """
        Args:
            blockSize: block size for stacking input data in matrices. Data is stacked within partitions. If block size is more than remaining data in a partition then it is adjusted to the size of this data.
        """
        self._set(blockSize=value)
        return self
    
    def setCheckpointInterval(self, value):
        """
        Args:
            checkpointInterval: set checkpoint interval (>= 1) or disable checkpoint (-1). E.g. 10 means that the cache will get checkpointed every 10 iterations. Note: this setting will be ignored if the checkpoint directory is not set in the SparkContext
        """
        self._set(checkpointInterval=value)
        return self
    
    def setColdStartStrategy(self, value):
        """
        Args:
            coldStartStrategy: strategy for dealing with unknown or new users/items at prediction time. This may be useful in cross-validation or production scenarios, for handling user/item ids the model has not seen in the training data. Supported values: nan,drop.
        """
        self._set(coldStartStrategy=value)
        return self
    
    def setFinalStorageLevel(self, value):
        """
        Args:
            finalStorageLevel: StorageLevel for ALS model factors.
        """
        self._set(finalStorageLevel=value)
        return self
    
    def setImplicitPrefs(self, value):
        """
        Args:
            implicitPrefs: whether to use implicit preference
        """
        self._set(implicitPrefs=value)
        return self
    
    def setIntermediateStorageLevel(self, value):
        """
        Args:
            intermediateStorageLevel: StorageLevel for intermediate datasets. Cannot be 'NONE'.
        """
        self._set(intermediateStorageLevel=value)
        return self
    
    def setItemCol(self, value):
        """
        Args:
            itemCol: column name for item ids. Ids must be within the integer value range.
        """
        self._set(itemCol=value)
        return self
    
    def setItemDataFrame(self, value):
        """
        Args:
            itemDataFrame: Time of activity
        """
        self._set(itemDataFrame=value)
        return self
    
    def setMaxIter(self, value):
        """
        Args:
            maxIter: maximum number of iterations (>= 0)
        """
        self._set(maxIter=value)
        return self
    
    def setNonnegative(self, value):
        """
        Args:
            nonnegative: whether to use nonnegative constraint for least squares
        """
        self._set(nonnegative=value)
        return self
    
    def setNumItemBlocks(self, value):
        """
        Args:
            numItemBlocks: number of item blocks
        """
        self._set(numItemBlocks=value)
        return self
    
    def setNumUserBlocks(self, value):
        """
        Args:
            numUserBlocks: number of user blocks
        """
        self._set(numUserBlocks=value)
        return self
    
    def setPredictionCol(self, value):
        """
        Args:
            predictionCol: prediction column name
        """
        self._set(predictionCol=value)
        return self
    
    def setRank(self, value):
        """
        Args:
            rank: rank of the factorization
        """
        self._set(rank=value)
        return self
    
    def setRatingCol(self, value):
        """
        Args:
            ratingCol: column name for ratings
        """
        self._set(ratingCol=value)
        return self
    
    def setRegParam(self, value):
        """
        Args:
            regParam: regularization parameter (>= 0)
        """
        self._set(regParam=value)
        return self
    
    def setSeed(self, value):
        """
        Args:
            seed: random seed
        """
        self._set(seed=value)
        return self
    
    def setSimilarityFunction(self, value):
        """
        Args:
            similarityFunction: Defines the similarity function to be used by the model. Lift favors serendipity, Co-occurrence favors predictability, and Jaccard is a nice compromise between the two.
        """
        self._set(similarityFunction=value)
        return self
    
    def setStartTime(self, value):
        """
        Args:
            startTime: Set time custom now time if using historical data
        """
        self._set(startTime=value)
        return self
    
    def setStartTimeFormat(self, value):
        """
        Args:
            startTimeFormat: Format for start time
        """
        self._set(startTimeFormat=value)
        return self
    
    def setSupportThreshold(self, value):
        """
        Args:
            supportThreshold: Minimum number of ratings per item
        """
        self._set(supportThreshold=value)
        return self
    
    def setTimeCol(self, value):
        """
        Args:
            timeCol: Time of activity
        """
        self._set(timeCol=value)
        return self
    
    def setTimeDecayCoeff(self, value):
        """
        Args:
            timeDecayCoeff: Use to scale time decay coeff to different half life dur
        """
        self._set(timeDecayCoeff=value)
        return self
    
    def setUserCol(self, value):
        """
        Args:
            userCol: column name for user ids. Ids must be within the integer value range.
        """
        self._set(userCol=value)
        return self
    
    def setUserDataFrame(self, value):
        """
        Args:
            userDataFrame: Time of activity
        """
        self._set(userDataFrame=value)
        return self

    
    def getActivityTimeFormat(self):
        """
        Returns:
            activityTimeFormat: Time format for events, default: yyyy/MM/dd'T'h:mm:ss
        """
        return self.getOrDefault(self.activityTimeFormat)
    
    
    def getAlpha(self):
        """
        Returns:
            alpha: alpha for implicit preference
        """
        return self.getOrDefault(self.alpha)
    
    
    def getBlockSize(self):
        """
        Returns:
            blockSize: block size for stacking input data in matrices. Data is stacked within partitions. If block size is more than remaining data in a partition then it is adjusted to the size of this data.
        """
        return self.getOrDefault(self.blockSize)
    
    
    def getCheckpointInterval(self):
        """
        Returns:
            checkpointInterval: set checkpoint interval (>= 1) or disable checkpoint (-1). E.g. 10 means that the cache will get checkpointed every 10 iterations. Note: this setting will be ignored if the checkpoint directory is not set in the SparkContext
        """
        return self.getOrDefault(self.checkpointInterval)
    
    
    def getColdStartStrategy(self):
        """
        Returns:
            coldStartStrategy: strategy for dealing with unknown or new users/items at prediction time. This may be useful in cross-validation or production scenarios, for handling user/item ids the model has not seen in the training data. Supported values: nan,drop.
        """
        return self.getOrDefault(self.coldStartStrategy)
    
    
    def getFinalStorageLevel(self):
        """
        Returns:
            finalStorageLevel: StorageLevel for ALS model factors.
        """
        return self.getOrDefault(self.finalStorageLevel)
    
    
    def getImplicitPrefs(self):
        """
        Returns:
            implicitPrefs: whether to use implicit preference
        """
        return self.getOrDefault(self.implicitPrefs)
    
    
    def getIntermediateStorageLevel(self):
        """
        Returns:
            intermediateStorageLevel: StorageLevel for intermediate datasets. Cannot be 'NONE'.
        """
        return self.getOrDefault(self.intermediateStorageLevel)
    
    
    def getItemCol(self):
        """
        Returns:
            itemCol: column name for item ids. Ids must be within the integer value range.
        """
        return self.getOrDefault(self.itemCol)
    
    
    def getItemDataFrame(self):
        """
        Returns:
            itemDataFrame: Time of activity
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getItemDataFrame(), sql_ctx)
    
    
    def getMaxIter(self):
        """
        Returns:
            maxIter: maximum number of iterations (>= 0)
        """
        return self.getOrDefault(self.maxIter)
    
    
    def getNonnegative(self):
        """
        Returns:
            nonnegative: whether to use nonnegative constraint for least squares
        """
        return self.getOrDefault(self.nonnegative)
    
    
    def getNumItemBlocks(self):
        """
        Returns:
            numItemBlocks: number of item blocks
        """
        return self.getOrDefault(self.numItemBlocks)
    
    
    def getNumUserBlocks(self):
        """
        Returns:
            numUserBlocks: number of user blocks
        """
        return self.getOrDefault(self.numUserBlocks)
    
    
    def getPredictionCol(self):
        """
        Returns:
            predictionCol: prediction column name
        """
        return self.getOrDefault(self.predictionCol)
    
    
    def getRank(self):
        """
        Returns:
            rank: rank of the factorization
        """
        return self.getOrDefault(self.rank)
    
    
    def getRatingCol(self):
        """
        Returns:
            ratingCol: column name for ratings
        """
        return self.getOrDefault(self.ratingCol)
    
    
    def getRegParam(self):
        """
        Returns:
            regParam: regularization parameter (>= 0)
        """
        return self.getOrDefault(self.regParam)
    
    
    def getSeed(self):
        """
        Returns:
            seed: random seed
        """
        return self.getOrDefault(self.seed)
    
    
    def getSimilarityFunction(self):
        """
        Returns:
            similarityFunction: Defines the similarity function to be used by the model. Lift favors serendipity, Co-occurrence favors predictability, and Jaccard is a nice compromise between the two.
        """
        return self.getOrDefault(self.similarityFunction)
    
    
    def getStartTime(self):
        """
        Returns:
            startTime: Set time custom now time if using historical data
        """
        return self.getOrDefault(self.startTime)
    
    
    def getStartTimeFormat(self):
        """
        Returns:
            startTimeFormat: Format for start time
        """
        return self.getOrDefault(self.startTimeFormat)
    
    
    def getSupportThreshold(self):
        """
        Returns:
            supportThreshold: Minimum number of ratings per item
        """
        return self.getOrDefault(self.supportThreshold)
    
    
    def getTimeCol(self):
        """
        Returns:
            timeCol: Time of activity
        """
        return self.getOrDefault(self.timeCol)
    
    
    def getTimeDecayCoeff(self):
        """
        Returns:
            timeDecayCoeff: Use to scale time decay coeff to different half life dur
        """
        return self.getOrDefault(self.timeDecayCoeff)
    
    
    def getUserCol(self):
        """
        Returns:
            userCol: column name for user ids. Ids must be within the integer value range.
        """
        return self.getOrDefault(self.userCol)
    
    
    def getUserDataFrame(self):
        """
        Returns:
            userDataFrame: Time of activity
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getUserDataFrame(), sql_ctx)

    

    
        