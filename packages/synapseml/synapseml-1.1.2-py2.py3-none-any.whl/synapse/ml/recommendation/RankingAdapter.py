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
from synapse.ml.recommendation.RankingAdapterModel import RankingAdapterModel

@inherit_doc
class RankingAdapter(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        itemCol (str): Column of items
        k (int): number of items
        labelCol (str): The name of the label column
        minRatingsPerItem (int): min ratings for items > 0
        minRatingsPerUser (int): min ratings for users > 0
        mode (str): recommendation mode
        ratingCol (str): Column of ratings
        recommender (object): estimator for selection
        userCol (str): Column of users
    """

    itemCol = Param(Params._dummy(), "itemCol", "Column of items", typeConverter=TypeConverters.toString)
    
    k = Param(Params._dummy(), "k", "number of items", typeConverter=TypeConverters.toInt)
    
    labelCol = Param(Params._dummy(), "labelCol", "The name of the label column", typeConverter=TypeConverters.toString)
    
    minRatingsPerItem = Param(Params._dummy(), "minRatingsPerItem", "min ratings for items > 0", typeConverter=TypeConverters.toInt)
    
    minRatingsPerUser = Param(Params._dummy(), "minRatingsPerUser", "min ratings for users > 0", typeConverter=TypeConverters.toInt)
    
    mode = Param(Params._dummy(), "mode", "recommendation mode", typeConverter=TypeConverters.toString)
    
    ratingCol = Param(Params._dummy(), "ratingCol", "Column of ratings", typeConverter=TypeConverters.toString)
    
    recommender = Param(Params._dummy(), "recommender", "estimator for selection")
    
    userCol = Param(Params._dummy(), "userCol", "Column of users", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        itemCol=None,
        k=10,
        labelCol="label",
        minRatingsPerItem=1,
        minRatingsPerUser=1,
        mode="allUsers",
        ratingCol=None,
        recommender=None,
        userCol=None
        ):
        super(RankingAdapter, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.recommendation.RankingAdapter", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(k=10)
        self._setDefault(labelCol="label")
        self._setDefault(minRatingsPerItem=1)
        self._setDefault(minRatingsPerUser=1)
        self._setDefault(mode="allUsers")
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
        minRatingsPerItem=1,
        minRatingsPerUser=1,
        mode="allUsers",
        ratingCol=None,
        recommender=None,
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
        return "com.microsoft.azure.synapse.ml.recommendation.RankingAdapter"

    @staticmethod
    def _from_java(java_stage):
        module_name=RankingAdapter.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".RankingAdapter"
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
            labelCol: The name of the label column
        """
        self._set(labelCol=value)
        return self
    
    def setMinRatingsPerItem(self, value):
        """
        Args:
            minRatingsPerItem: min ratings for items > 0
        """
        self._set(minRatingsPerItem=value)
        return self
    
    def setMinRatingsPerUser(self, value):
        """
        Args:
            minRatingsPerUser: min ratings for users > 0
        """
        self._set(minRatingsPerUser=value)
        return self
    
    def setMode(self, value):
        """
        Args:
            mode: recommendation mode
        """
        self._set(mode=value)
        return self
    
    def setRatingCol(self, value):
        """
        Args:
            ratingCol: Column of ratings
        """
        self._set(ratingCol=value)
        return self
    
    def setRecommender(self, value):
        """
        Args:
            recommender: estimator for selection
        """
        self._set(recommender=value)
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
            labelCol: The name of the label column
        """
        return self.getOrDefault(self.labelCol)
    
    
    def getMinRatingsPerItem(self):
        """
        Returns:
            minRatingsPerItem: min ratings for items > 0
        """
        return self.getOrDefault(self.minRatingsPerItem)
    
    
    def getMinRatingsPerUser(self):
        """
        Returns:
            minRatingsPerUser: min ratings for users > 0
        """
        return self.getOrDefault(self.minRatingsPerUser)
    
    
    def getMode(self):
        """
        Returns:
            mode: recommendation mode
        """
        return self.getOrDefault(self.mode)
    
    
    def getRatingCol(self):
        """
        Returns:
            ratingCol: Column of ratings
        """
        return self.getOrDefault(self.ratingCol)
    
    
    def getRecommender(self):
        """
        Returns:
            recommender: estimator for selection
        """
        return JavaParams._from_java(self._java_obj.getRecommender())
    
    
    def getUserCol(self):
        """
        Returns:
            userCol: Column of users
        """
        return self.getOrDefault(self.userCol)

    def _create_model(self, java_model):
        try:
            model = RankingAdapterModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = RankingAdapterModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        