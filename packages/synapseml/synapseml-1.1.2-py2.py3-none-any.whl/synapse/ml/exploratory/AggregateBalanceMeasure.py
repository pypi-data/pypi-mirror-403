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
class AggregateBalanceMeasure(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        epsilon (float): Epsilon value for Atkinson Index. Inverse of alpha (1 - alpha).
        errorTolerance (float): Error tolerance value for Atkinson Index.
        outputCol (str): output column name
        sensitiveCols (list): Sensitive columns to use.
        verbose (bool): Whether to show intermediate measures and calculations, such as Positive Rate.
    """

    epsilon = Param(Params._dummy(), "epsilon", "Epsilon value for Atkinson Index. Inverse of alpha (1 - alpha).", typeConverter=TypeConverters.toFloat)
    
    errorTolerance = Param(Params._dummy(), "errorTolerance", "Error tolerance value for Atkinson Index.", typeConverter=TypeConverters.toFloat)
    
    outputCol = Param(Params._dummy(), "outputCol", "output column name", typeConverter=TypeConverters.toString)
    
    sensitiveCols = Param(Params._dummy(), "sensitiveCols", "Sensitive columns to use.", typeConverter=TypeConverters.toListString)
    
    verbose = Param(Params._dummy(), "verbose", "Whether to show intermediate measures and calculations, such as Positive Rate.", typeConverter=TypeConverters.toBoolean)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        epsilon=1.0,
        errorTolerance=1.0E-12,
        outputCol="AggregateBalanceMeasure",
        sensitiveCols=None,
        verbose=False
        ):
        super(AggregateBalanceMeasure, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.exploratory.AggregateBalanceMeasure", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(epsilon=1.0)
        self._setDefault(errorTolerance=1.0E-12)
        self._setDefault(outputCol="AggregateBalanceMeasure")
        self._setDefault(verbose=False)
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
        epsilon=1.0,
        errorTolerance=1.0E-12,
        outputCol="AggregateBalanceMeasure",
        sensitiveCols=None,
        verbose=False
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
        return "com.microsoft.azure.synapse.ml.exploratory.AggregateBalanceMeasure"

    @staticmethod
    def _from_java(java_stage):
        module_name=AggregateBalanceMeasure.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".AggregateBalanceMeasure"
        return from_java(java_stage, module_name)

    def setEpsilon(self, value):
        """
        Args:
            epsilon: Epsilon value for Atkinson Index. Inverse of alpha (1 - alpha).
        """
        self._set(epsilon=value)
        return self
    
    def setErrorTolerance(self, value):
        """
        Args:
            errorTolerance: Error tolerance value for Atkinson Index.
        """
        self._set(errorTolerance=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: output column name
        """
        self._set(outputCol=value)
        return self
    
    def setSensitiveCols(self, value):
        """
        Args:
            sensitiveCols: Sensitive columns to use.
        """
        self._set(sensitiveCols=value)
        return self
    
    def setVerbose(self, value):
        """
        Args:
            verbose: Whether to show intermediate measures and calculations, such as Positive Rate.
        """
        self._set(verbose=value)
        return self

    
    def getEpsilon(self):
        """
        Returns:
            epsilon: Epsilon value for Atkinson Index. Inverse of alpha (1 - alpha).
        """
        return self.getOrDefault(self.epsilon)
    
    
    def getErrorTolerance(self):
        """
        Returns:
            errorTolerance: Error tolerance value for Atkinson Index.
        """
        return self.getOrDefault(self.errorTolerance)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: output column name
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getSensitiveCols(self):
        """
        Returns:
            sensitiveCols: Sensitive columns to use.
        """
        return self.getOrDefault(self.sensitiveCols)
    
    
    def getVerbose(self):
        """
        Returns:
            verbose: Whether to show intermediate measures and calculations, such as Positive Rate.
        """
        return self.getOrDefault(self.verbose)

    

    
        