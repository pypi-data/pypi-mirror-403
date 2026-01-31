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
class VowpalWabbitCSETransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        maxImportanceWeight (float): Clip importance weight at this upper bound. Defaults to 100.
        metricsStratificationCols (list): Optional list of column names to stratify rewards by.
        minImportanceWeight (float): Clip importance weight at this lower bound. Defaults to 0.
    """

    maxImportanceWeight = Param(Params._dummy(), "maxImportanceWeight", "Clip importance weight at this upper bound. Defaults to 100.", typeConverter=TypeConverters.toFloat)
    
    metricsStratificationCols = Param(Params._dummy(), "metricsStratificationCols", "Optional list of column names to stratify rewards by.", typeConverter=TypeConverters.toListString)
    
    minImportanceWeight = Param(Params._dummy(), "minImportanceWeight", "Clip importance weight at this lower bound. Defaults to 0.", typeConverter=TypeConverters.toFloat)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        maxImportanceWeight=100.0,
        metricsStratificationCols=[],
        minImportanceWeight=0.0
        ):
        super(VowpalWabbitCSETransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.vw.VowpalWabbitCSETransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(maxImportanceWeight=100.0)
        self._setDefault(metricsStratificationCols=[])
        self._setDefault(minImportanceWeight=0.0)
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
        maxImportanceWeight=100.0,
        metricsStratificationCols=[],
        minImportanceWeight=0.0
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
        return "com.microsoft.azure.synapse.ml.vw.VowpalWabbitCSETransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=VowpalWabbitCSETransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".VowpalWabbitCSETransformer"
        return from_java(java_stage, module_name)

    def setMaxImportanceWeight(self, value):
        """
        Args:
            maxImportanceWeight: Clip importance weight at this upper bound. Defaults to 100.
        """
        self._set(maxImportanceWeight=value)
        return self
    
    def setMetricsStratificationCols(self, value):
        """
        Args:
            metricsStratificationCols: Optional list of column names to stratify rewards by.
        """
        self._set(metricsStratificationCols=value)
        return self
    
    def setMinImportanceWeight(self, value):
        """
        Args:
            minImportanceWeight: Clip importance weight at this lower bound. Defaults to 0.
        """
        self._set(minImportanceWeight=value)
        return self

    
    def getMaxImportanceWeight(self):
        """
        Returns:
            maxImportanceWeight: Clip importance weight at this upper bound. Defaults to 100.
        """
        return self.getOrDefault(self.maxImportanceWeight)
    
    
    def getMetricsStratificationCols(self):
        """
        Returns:
            metricsStratificationCols: Optional list of column names to stratify rewards by.
        """
        return self.getOrDefault(self.metricsStratificationCols)
    
    
    def getMinImportanceWeight(self):
        """
        Returns:
            minImportanceWeight: Clip importance weight at this lower bound. Defaults to 0.
        """
        return self.getOrDefault(self.minImportanceWeight)

    

    
        