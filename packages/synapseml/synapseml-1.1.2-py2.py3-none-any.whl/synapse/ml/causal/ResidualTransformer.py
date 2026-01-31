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
class ResidualTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        classIndex (int): The index of the class to compute residual for classification outputs. Default value is 1.
        observedCol (str): observed data (label column)
        outputCol (str): The name of the output column
        predictedCol (str): predicted data (prediction or probability columns
    """

    classIndex = Param(Params._dummy(), "classIndex", "The index of the class to compute residual for classification outputs. Default value is 1.", typeConverter=TypeConverters.toInt)
    
    observedCol = Param(Params._dummy(), "observedCol", "observed data (label column)", typeConverter=TypeConverters.toString)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    predictedCol = Param(Params._dummy(), "predictedCol", "predicted data (prediction or probability columns", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        classIndex=1,
        observedCol="label",
        outputCol="residual",
        predictedCol="prediction"
        ):
        super(ResidualTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.causal.ResidualTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(classIndex=1)
        self._setDefault(observedCol="label")
        self._setDefault(outputCol="residual")
        self._setDefault(predictedCol="prediction")
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
        classIndex=1,
        observedCol="label",
        outputCol="residual",
        predictedCol="prediction"
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
        return "com.microsoft.azure.synapse.ml.causal.ResidualTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=ResidualTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ResidualTransformer"
        return from_java(java_stage, module_name)

    def setClassIndex(self, value):
        """
        Args:
            classIndex: The index of the class to compute residual for classification outputs. Default value is 1.
        """
        self._set(classIndex=value)
        return self
    
    def setObservedCol(self, value):
        """
        Args:
            observedCol: observed data (label column)
        """
        self._set(observedCol=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setPredictedCol(self, value):
        """
        Args:
            predictedCol: predicted data (prediction or probability columns
        """
        self._set(predictedCol=value)
        return self

    
    def getClassIndex(self):
        """
        Returns:
            classIndex: The index of the class to compute residual for classification outputs. Default value is 1.
        """
        return self.getOrDefault(self.classIndex)
    
    
    def getObservedCol(self):
        """
        Returns:
            observedCol: observed data (label column)
        """
        return self.getOrDefault(self.observedCol)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getPredictedCol(self):
        """
        Returns:
            predictedCol: predicted data (prediction or probability columns
        """
        return self.getOrDefault(self.predictedCol)

    

    
        