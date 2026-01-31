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
from synapse.ml.train.TrainedRegressorModel import TrainedRegressorModel

@inherit_doc
class TrainRegressor(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        featuresCol (str): The name of the features column
        inputCols (list): The names of the input columns
        labelCol (str): The name of the label column
        model (object): Regressor to run
        numFeatures (int): Number of features to hash to
    """

    featuresCol = Param(Params._dummy(), "featuresCol", "The name of the features column", typeConverter=TypeConverters.toString)
    
    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    labelCol = Param(Params._dummy(), "labelCol", "The name of the label column", typeConverter=TypeConverters.toString)
    
    model = Param(Params._dummy(), "model", "Regressor to run")
    
    numFeatures = Param(Params._dummy(), "numFeatures", "Number of features to hash to", typeConverter=TypeConverters.toInt)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        featuresCol="TrainRegressor_cfe1035453c8_features",
        inputCols=None,
        labelCol=None,
        model=None,
        numFeatures=0
        ):
        super(TrainRegressor, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.train.TrainRegressor", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(featuresCol="TrainRegressor_cfe1035453c8_features")
        self._setDefault(numFeatures=0)
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
        featuresCol="TrainRegressor_cfe1035453c8_features",
        inputCols=None,
        labelCol=None,
        model=None,
        numFeatures=0
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
        return "com.microsoft.azure.synapse.ml.train.TrainRegressor"

    @staticmethod
    def _from_java(java_stage):
        module_name=TrainRegressor.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".TrainRegressor"
        return from_java(java_stage, module_name)

    def setFeaturesCol(self, value):
        """
        Args:
            featuresCol: The name of the features column
        """
        self._set(featuresCol=value)
        return self
    
    def setInputCols(self, value):
        """
        Args:
            inputCols: The names of the input columns
        """
        self._set(inputCols=value)
        return self
    
    def setLabelCol(self, value):
        """
        Args:
            labelCol: The name of the label column
        """
        self._set(labelCol=value)
        return self
    
    def setModel(self, value):
        """
        Args:
            model: Regressor to run
        """
        self._set(model=value)
        return self
    
    def setNumFeatures(self, value):
        """
        Args:
            numFeatures: Number of features to hash to
        """
        self._set(numFeatures=value)
        return self

    
    def getFeaturesCol(self):
        """
        Returns:
            featuresCol: The name of the features column
        """
        return self.getOrDefault(self.featuresCol)
    
    
    def getInputCols(self):
        """
        Returns:
            inputCols: The names of the input columns
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getLabelCol(self):
        """
        Returns:
            labelCol: The name of the label column
        """
        return self.getOrDefault(self.labelCol)
    
    
    def getModel(self):
        """
        Returns:
            model: Regressor to run
        """
        return JavaParams._from_java(self._java_obj.getModel())
    
    
    def getNumFeatures(self):
        """
        Returns:
            numFeatures: Number of features to hash to
        """
        return self.getOrDefault(self.numFeatures)

    def _create_model(self, java_model):
        try:
            model = TrainedRegressorModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = TrainedRegressorModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        