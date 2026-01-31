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
from pyspark.ml import PipelineModel

@inherit_doc
class Featurize(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        imputeMissing (bool): Whether to impute missing values
        inputCols (list): The names of the input columns
        numFeatures (int): Number of features to hash string columns to
        oneHotEncodeCategoricals (bool): One-hot encode categorical columns
        outputCol (str): The name of the output column
    """

    imputeMissing = Param(Params._dummy(), "imputeMissing", "Whether to impute missing values", typeConverter=TypeConverters.toBoolean)
    
    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    numFeatures = Param(Params._dummy(), "numFeatures", "Number of features to hash string columns to", typeConverter=TypeConverters.toInt)
    
    oneHotEncodeCategoricals = Param(Params._dummy(), "oneHotEncodeCategoricals", "One-hot encode categorical columns", typeConverter=TypeConverters.toBoolean)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        imputeMissing=True,
        inputCols=None,
        numFeatures=262144,
        oneHotEncodeCategoricals=True,
        outputCol=None
        ):
        super(Featurize, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.featurize.Featurize", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(imputeMissing=True)
        self._setDefault(numFeatures=262144)
        self._setDefault(oneHotEncodeCategoricals=True)
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
        imputeMissing=True,
        inputCols=None,
        numFeatures=262144,
        oneHotEncodeCategoricals=True,
        outputCol=None
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
        return "com.microsoft.azure.synapse.ml.featurize.Featurize"

    @staticmethod
    def _from_java(java_stage):
        module_name=Featurize.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".Featurize"
        return from_java(java_stage, module_name)

    def setImputeMissing(self, value):
        """
        Args:
            imputeMissing: Whether to impute missing values
        """
        self._set(imputeMissing=value)
        return self
    
    def setInputCols(self, value):
        """
        Args:
            inputCols: The names of the input columns
        """
        self._set(inputCols=value)
        return self
    
    def setNumFeatures(self, value):
        """
        Args:
            numFeatures: Number of features to hash string columns to
        """
        self._set(numFeatures=value)
        return self
    
    def setOneHotEncodeCategoricals(self, value):
        """
        Args:
            oneHotEncodeCategoricals: One-hot encode categorical columns
        """
        self._set(oneHotEncodeCategoricals=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self

    
    def getImputeMissing(self):
        """
        Returns:
            imputeMissing: Whether to impute missing values
        """
        return self.getOrDefault(self.imputeMissing)
    
    
    def getInputCols(self):
        """
        Returns:
            inputCols: The names of the input columns
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getNumFeatures(self):
        """
        Returns:
            numFeatures: Number of features to hash string columns to
        """
        return self.getOrDefault(self.numFeatures)
    
    
    def getOneHotEncodeCategoricals(self):
        """
        Returns:
            oneHotEncodeCategoricals: One-hot encode categorical columns
        """
        return self.getOrDefault(self.oneHotEncodeCategoricals)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)

    def _create_model(self, java_model):
        try:
            model = PipelineModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = PipelineModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        