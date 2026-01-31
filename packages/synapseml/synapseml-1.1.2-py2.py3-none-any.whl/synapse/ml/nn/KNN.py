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
from synapse.ml.nn.KNNModel import KNNModel

@inherit_doc
class KNN(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        featuresCol (str): The name of the features column
        k (int): number of matches to return
        leafSize (int): max size of the leaves of the tree
        outputCol (str): The name of the output column
        valuesCol (str): column holding values for each feature (key) that will be returned when queried
    """

    featuresCol = Param(Params._dummy(), "featuresCol", "The name of the features column", typeConverter=TypeConverters.toString)
    
    k = Param(Params._dummy(), "k", "number of matches to return", typeConverter=TypeConverters.toInt)
    
    leafSize = Param(Params._dummy(), "leafSize", "max size of the leaves of the tree", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    valuesCol = Param(Params._dummy(), "valuesCol", "column holding values for each feature (key) that will be returned when queried", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        featuresCol="features",
        k=5,
        leafSize=50,
        outputCol="KNN_0d63a4573aae_output",
        valuesCol="values"
        ):
        super(KNN, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.nn.KNN", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(featuresCol="features")
        self._setDefault(k=5)
        self._setDefault(leafSize=50)
        self._setDefault(outputCol="KNN_0d63a4573aae_output")
        self._setDefault(valuesCol="values")
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
        k=5,
        leafSize=50,
        outputCol="KNN_0d63a4573aae_output",
        valuesCol="values"
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
        return "com.microsoft.azure.synapse.ml.nn.KNN"

    @staticmethod
    def _from_java(java_stage):
        module_name=KNN.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".KNN"
        return from_java(java_stage, module_name)

    def setFeaturesCol(self, value):
        """
        Args:
            featuresCol: The name of the features column
        """
        self._set(featuresCol=value)
        return self
    
    def setK(self, value):
        """
        Args:
            k: number of matches to return
        """
        self._set(k=value)
        return self
    
    def setLeafSize(self, value):
        """
        Args:
            leafSize: max size of the leaves of the tree
        """
        self._set(leafSize=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setValuesCol(self, value):
        """
        Args:
            valuesCol: column holding values for each feature (key) that will be returned when queried
        """
        self._set(valuesCol=value)
        return self

    
    def getFeaturesCol(self):
        """
        Returns:
            featuresCol: The name of the features column
        """
        return self.getOrDefault(self.featuresCol)
    
    
    def getK(self):
        """
        Returns:
            k: number of matches to return
        """
        return self.getOrDefault(self.k)
    
    
    def getLeafSize(self):
        """
        Returns:
            leafSize: max size of the leaves of the tree
        """
        return self.getOrDefault(self.leafSize)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getValuesCol(self):
        """
        Returns:
            valuesCol: column holding values for each feature (key) that will be returned when queried
        """
        return self.getOrDefault(self.valuesCol)

    def _create_model(self, java_model):
        try:
            model = KNNModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = KNNModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        