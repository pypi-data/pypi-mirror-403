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
class RecommendationIndexerModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        itemIndexModel (object): itemIndexModel
        itemInputCol (str): Item Input Col
        itemOutputCol (str): Item Output Col
        ratingCol (str): Rating Col
        userIndexModel (object): userIndexModel
        userInputCol (str): User Input Col
        userOutputCol (str): User Output Col
    """

    itemIndexModel = Param(Params._dummy(), "itemIndexModel", "itemIndexModel")
    
    itemInputCol = Param(Params._dummy(), "itemInputCol", "Item Input Col", typeConverter=TypeConverters.toString)
    
    itemOutputCol = Param(Params._dummy(), "itemOutputCol", "Item Output Col", typeConverter=TypeConverters.toString)
    
    ratingCol = Param(Params._dummy(), "ratingCol", "Rating Col", typeConverter=TypeConverters.toString)
    
    userIndexModel = Param(Params._dummy(), "userIndexModel", "userIndexModel")
    
    userInputCol = Param(Params._dummy(), "userInputCol", "User Input Col", typeConverter=TypeConverters.toString)
    
    userOutputCol = Param(Params._dummy(), "userOutputCol", "User Output Col", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        itemIndexModel=None,
        itemInputCol=None,
        itemOutputCol=None,
        ratingCol=None,
        userIndexModel=None,
        userInputCol=None,
        userOutputCol=None
        ):
        super(RecommendationIndexerModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.recommendation.RecommendationIndexerModel", self.uid)
        else:
            self._java_obj = java_obj
        
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
        itemIndexModel=None,
        itemInputCol=None,
        itemOutputCol=None,
        ratingCol=None,
        userIndexModel=None,
        userInputCol=None,
        userOutputCol=None
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
        return "com.microsoft.azure.synapse.ml.recommendation.RecommendationIndexerModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=RecommendationIndexerModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".RecommendationIndexerModel"
        return from_java(java_stage, module_name)

    def setItemIndexModel(self, value):
        """
        Args:
            itemIndexModel: itemIndexModel
        """
        self._set(itemIndexModel=value)
        return self
    
    def setItemInputCol(self, value):
        """
        Args:
            itemInputCol: Item Input Col
        """
        self._set(itemInputCol=value)
        return self
    
    def setItemOutputCol(self, value):
        """
        Args:
            itemOutputCol: Item Output Col
        """
        self._set(itemOutputCol=value)
        return self
    
    def setRatingCol(self, value):
        """
        Args:
            ratingCol: Rating Col
        """
        self._set(ratingCol=value)
        return self
    
    def setUserIndexModel(self, value):
        """
        Args:
            userIndexModel: userIndexModel
        """
        self._set(userIndexModel=value)
        return self
    
    def setUserInputCol(self, value):
        """
        Args:
            userInputCol: User Input Col
        """
        self._set(userInputCol=value)
        return self
    
    def setUserOutputCol(self, value):
        """
        Args:
            userOutputCol: User Output Col
        """
        self._set(userOutputCol=value)
        return self

    
    def getItemIndexModel(self):
        """
        Returns:
            itemIndexModel: itemIndexModel
        """
        return JavaParams._from_java(self._java_obj.getItemIndexModel())
    
    
    def getItemInputCol(self):
        """
        Returns:
            itemInputCol: Item Input Col
        """
        return self.getOrDefault(self.itemInputCol)
    
    
    def getItemOutputCol(self):
        """
        Returns:
            itemOutputCol: Item Output Col
        """
        return self.getOrDefault(self.itemOutputCol)
    
    
    def getRatingCol(self):
        """
        Returns:
            ratingCol: Rating Col
        """
        return self.getOrDefault(self.ratingCol)
    
    
    def getUserIndexModel(self):
        """
        Returns:
            userIndexModel: userIndexModel
        """
        return JavaParams._from_java(self._java_obj.getUserIndexModel())
    
    
    def getUserInputCol(self):
        """
        Returns:
            userInputCol: User Input Col
        """
        return self.getOrDefault(self.userInputCol)
    
    
    def getUserOutputCol(self):
        """
        Returns:
            userOutputCol: User Output Col
        """
        return self.getOrDefault(self.userOutputCol)

    

    
        