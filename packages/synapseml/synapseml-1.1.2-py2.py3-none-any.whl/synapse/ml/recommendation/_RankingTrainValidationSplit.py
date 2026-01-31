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
from synapse.ml.recommendation.RankingTrainValidationSplitModel import RankingTrainValidationSplitModel

@inherit_doc
class _RankingTrainValidationSplit(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        alpha (float): alpha for implicit preference
        blockSize (int): block size for stacking input data in matrices. Data is stacked within partitions. If block size is more than remaining data in a partition then it is adjusted to the size of this data.
        checkpointInterval (int): set checkpoint interval (>= 1) or disable checkpoint (-1). E.g. 10 means that the cache will get checkpointed every 10 iterations. Note: this setting will be ignored if the checkpoint directory is not set in the SparkContext
        coldStartStrategy (str): strategy for dealing with unknown or new users/items at prediction time. This may be useful in cross-validation or production scenarios, for handling user/item ids the model has not seen in the training data. Supported values: nan,drop.
        estimator (object): estimator for selection
        estimatorParamMaps (object): param maps for the estimator
        evaluator (object): evaluator used to select hyper-parameters that maximize the validated metric
        finalStorageLevel (str): StorageLevel for ALS model factors.
        implicitPrefs (bool): whether to use implicit preference
        intermediateStorageLevel (str): StorageLevel for intermediate datasets. Cannot be 'NONE'.
        itemCol (str): column name for item ids. Ids must be within the integer value range.
        maxIter (int): maximum number of iterations (>= 0)
        minRatingsI (int): min ratings for items > 0
        minRatingsU (int): min ratings for users > 0
        nonnegative (bool): whether to use nonnegative constraint for least squares
        numItemBlocks (int): number of item blocks
        numUserBlocks (int): number of user blocks
        parallelism (int): the number of threads to use when running parallel algorithms
        predictionCol (str): prediction column name
        rank (int): rank of the factorization
        ratingCol (str): column name for ratings
        regParam (float): regularization parameter (>= 0)
        seed (long): random seed
        trainRatio (float): ratio between training set and validation set (>= 0 and <= 1)
        userCol (str): column name for user ids. Ids must be within the integer value range.
    """

    alpha = Param(Params._dummy(), "alpha", "alpha for implicit preference", typeConverter=TypeConverters.toFloat)
    
    blockSize = Param(Params._dummy(), "blockSize", "block size for stacking input data in matrices. Data is stacked within partitions. If block size is more than remaining data in a partition then it is adjusted to the size of this data.", typeConverter=TypeConverters.toInt)
    
    checkpointInterval = Param(Params._dummy(), "checkpointInterval", "set checkpoint interval (>= 1) or disable checkpoint (-1). E.g. 10 means that the cache will get checkpointed every 10 iterations. Note: this setting will be ignored if the checkpoint directory is not set in the SparkContext", typeConverter=TypeConverters.toInt)
    
    coldStartStrategy = Param(Params._dummy(), "coldStartStrategy", "strategy for dealing with unknown or new users/items at prediction time. This may be useful in cross-validation or production scenarios, for handling user/item ids the model has not seen in the training data. Supported values: nan,drop.", typeConverter=TypeConverters.toString)
    
    estimator = Param(Params._dummy(), "estimator", "estimator for selection")
    
    estimatorParamMaps = Param(Params._dummy(), "estimatorParamMaps", "param maps for the estimator")
    
    evaluator = Param(Params._dummy(), "evaluator", "evaluator used to select hyper-parameters that maximize the validated metric")
    
    finalStorageLevel = Param(Params._dummy(), "finalStorageLevel", "StorageLevel for ALS model factors.", typeConverter=TypeConverters.toString)
    
    implicitPrefs = Param(Params._dummy(), "implicitPrefs", "whether to use implicit preference", typeConverter=TypeConverters.toBoolean)
    
    intermediateStorageLevel = Param(Params._dummy(), "intermediateStorageLevel", "StorageLevel for intermediate datasets. Cannot be 'NONE'.", typeConverter=TypeConverters.toString)
    
    itemCol = Param(Params._dummy(), "itemCol", "column name for item ids. Ids must be within the integer value range.", typeConverter=TypeConverters.toString)
    
    maxIter = Param(Params._dummy(), "maxIter", "maximum number of iterations (>= 0)", typeConverter=TypeConverters.toInt)
    
    minRatingsI = Param(Params._dummy(), "minRatingsI", "min ratings for items > 0", typeConverter=TypeConverters.toInt)
    
    minRatingsU = Param(Params._dummy(), "minRatingsU", "min ratings for users > 0", typeConverter=TypeConverters.toInt)
    
    nonnegative = Param(Params._dummy(), "nonnegative", "whether to use nonnegative constraint for least squares", typeConverter=TypeConverters.toBoolean)
    
    numItemBlocks = Param(Params._dummy(), "numItemBlocks", "number of item blocks", typeConverter=TypeConverters.toInt)
    
    numUserBlocks = Param(Params._dummy(), "numUserBlocks", "number of user blocks", typeConverter=TypeConverters.toInt)
    
    parallelism = Param(Params._dummy(), "parallelism", "the number of threads to use when running parallel algorithms", typeConverter=TypeConverters.toInt)
    
    predictionCol = Param(Params._dummy(), "predictionCol", "prediction column name", typeConverter=TypeConverters.toString)
    
    rank = Param(Params._dummy(), "rank", "rank of the factorization", typeConverter=TypeConverters.toInt)
    
    ratingCol = Param(Params._dummy(), "ratingCol", "column name for ratings", typeConverter=TypeConverters.toString)
    
    regParam = Param(Params._dummy(), "regParam", "regularization parameter (>= 0)", typeConverter=TypeConverters.toFloat)
    
    seed = Param(Params._dummy(), "seed", "random seed")
    
    trainRatio = Param(Params._dummy(), "trainRatio", "ratio between training set and validation set (>= 0 and <= 1)", typeConverter=TypeConverters.toFloat)
    
    userCol = Param(Params._dummy(), "userCol", "column name for user ids. Ids must be within the integer value range.", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        alpha=1.0,
        blockSize=4096,
        checkpointInterval=10,
        coldStartStrategy="nan",
        estimator=None,
        estimatorParamMaps=None,
        evaluator=None,
        finalStorageLevel="MEMORY_AND_DISK",
        implicitPrefs=False,
        intermediateStorageLevel="MEMORY_AND_DISK",
        itemCol="item",
        maxIter=10,
        minRatingsI=1,
        minRatingsU=1,
        nonnegative=False,
        numItemBlocks=10,
        numUserBlocks=10,
        parallelism=1,
        predictionCol="prediction",
        rank=10,
        ratingCol="rating",
        regParam=0.1,
        seed=-492944968,
        trainRatio=0.75,
        userCol="user"
        ):
        super(_RankingTrainValidationSplit, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.recommendation.RankingTrainValidationSplit", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(alpha=1.0)
        self._setDefault(blockSize=4096)
        self._setDefault(checkpointInterval=10)
        self._setDefault(coldStartStrategy="nan")
        self._setDefault(finalStorageLevel="MEMORY_AND_DISK")
        self._setDefault(implicitPrefs=False)
        self._setDefault(intermediateStorageLevel="MEMORY_AND_DISK")
        self._setDefault(itemCol="item")
        self._setDefault(maxIter=10)
        self._setDefault(minRatingsI=1)
        self._setDefault(minRatingsU=1)
        self._setDefault(nonnegative=False)
        self._setDefault(numItemBlocks=10)
        self._setDefault(numUserBlocks=10)
        self._setDefault(parallelism=1)
        self._setDefault(predictionCol="prediction")
        self._setDefault(rank=10)
        self._setDefault(ratingCol="rating")
        self._setDefault(regParam=0.1)
        self._setDefault(seed=-492944968)
        self._setDefault(trainRatio=0.75)
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
        alpha=1.0,
        blockSize=4096,
        checkpointInterval=10,
        coldStartStrategy="nan",
        estimator=None,
        estimatorParamMaps=None,
        evaluator=None,
        finalStorageLevel="MEMORY_AND_DISK",
        implicitPrefs=False,
        intermediateStorageLevel="MEMORY_AND_DISK",
        itemCol="item",
        maxIter=10,
        minRatingsI=1,
        minRatingsU=1,
        nonnegative=False,
        numItemBlocks=10,
        numUserBlocks=10,
        parallelism=1,
        predictionCol="prediction",
        rank=10,
        ratingCol="rating",
        regParam=0.1,
        seed=-492944968,
        trainRatio=0.75,
        userCol="user"
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
        return "com.microsoft.azure.synapse.ml.recommendation.RankingTrainValidationSplit"

    @staticmethod
    def _from_java(java_stage):
        module_name=_RankingTrainValidationSplit.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".RankingTrainValidationSplit"
        return from_java(java_stage, module_name)

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
    
    def setEstimator(self, value):
        """
        Args:
            estimator: estimator for selection
        """
        self._set(estimator=value)
        return self
    
    def setEstimatorParamMaps(self, value):
        """
        Args:
            estimatorParamMaps: param maps for the estimator
        """
        self._set(estimatorParamMaps=value)
        return self
    
    def setEvaluator(self, value):
        """
        Args:
            evaluator: evaluator used to select hyper-parameters that maximize the validated metric
        """
        self._set(evaluator=value)
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
    
    def setMaxIter(self, value):
        """
        Args:
            maxIter: maximum number of iterations (>= 0)
        """
        self._set(maxIter=value)
        return self
    
    def setMinRatingsI(self, value):
        """
        Args:
            minRatingsI: min ratings for items > 0
        """
        self._set(minRatingsI=value)
        return self
    
    def setMinRatingsU(self, value):
        """
        Args:
            minRatingsU: min ratings for users > 0
        """
        self._set(minRatingsU=value)
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
    
    def setParallelism(self, value):
        """
        Args:
            parallelism: the number of threads to use when running parallel algorithms
        """
        self._set(parallelism=value)
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
    
    def setTrainRatio(self, value):
        """
        Args:
            trainRatio: ratio between training set and validation set (>= 0 and <= 1)
        """
        self._set(trainRatio=value)
        return self
    
    def setUserCol(self, value):
        """
        Args:
            userCol: column name for user ids. Ids must be within the integer value range.
        """
        self._set(userCol=value)
        return self

    
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
    
    
    def getEstimator(self):
        """
        Returns:
            estimator: estimator for selection
        """
        return JavaParams._from_java(self._java_obj.getEstimator())
    
    
    def getEstimatorParamMaps(self):
        """
        Returns:
            estimatorParamMaps: param maps for the estimator
        """
        return self.getOrDefault(self.estimatorParamMaps)
    
    
    def getEvaluator(self):
        """
        Returns:
            evaluator: evaluator used to select hyper-parameters that maximize the validated metric
        """
        return self.getOrDefault(self.evaluator)
    
    
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
    
    
    def getMaxIter(self):
        """
        Returns:
            maxIter: maximum number of iterations (>= 0)
        """
        return self.getOrDefault(self.maxIter)
    
    
    def getMinRatingsI(self):
        """
        Returns:
            minRatingsI: min ratings for items > 0
        """
        return self.getOrDefault(self.minRatingsI)
    
    
    def getMinRatingsU(self):
        """
        Returns:
            minRatingsU: min ratings for users > 0
        """
        return self.getOrDefault(self.minRatingsU)
    
    
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
    
    
    def getParallelism(self):
        """
        Returns:
            parallelism: the number of threads to use when running parallel algorithms
        """
        return self.getOrDefault(self.parallelism)
    
    
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
    
    
    def getTrainRatio(self):
        """
        Returns:
            trainRatio: ratio between training set and validation set (>= 0 and <= 1)
        """
        return self.getOrDefault(self.trainRatio)
    
    
    def getUserCol(self):
        """
        Returns:
            userCol: column name for user ids. Ids must be within the integer value range.
        """
        return self.getOrDefault(self.userCol)

    def _create_model(self, java_model):
        try:
            model = RankingTrainValidationSplitModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = RankingTrainValidationSplitModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        