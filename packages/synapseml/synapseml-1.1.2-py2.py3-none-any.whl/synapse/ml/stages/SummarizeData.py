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
class SummarizeData(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        basic (bool): Compute basic statistics
        counts (bool): Compute count statistics
        errorThreshold (float): Threshold for quantiles - 0 is exact
        percentiles (bool): Compute percentiles
        sample (bool): Compute sample statistics
    """

    basic = Param(Params._dummy(), "basic", "Compute basic statistics", typeConverter=TypeConverters.toBoolean)
    
    counts = Param(Params._dummy(), "counts", "Compute count statistics", typeConverter=TypeConverters.toBoolean)
    
    errorThreshold = Param(Params._dummy(), "errorThreshold", "Threshold for quantiles - 0 is exact", typeConverter=TypeConverters.toFloat)
    
    percentiles = Param(Params._dummy(), "percentiles", "Compute percentiles", typeConverter=TypeConverters.toBoolean)
    
    sample = Param(Params._dummy(), "sample", "Compute sample statistics", typeConverter=TypeConverters.toBoolean)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        basic=True,
        counts=True,
        errorThreshold=0.0,
        percentiles=True,
        sample=True
        ):
        super(SummarizeData, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.SummarizeData", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(basic=True)
        self._setDefault(counts=True)
        self._setDefault(errorThreshold=0.0)
        self._setDefault(percentiles=True)
        self._setDefault(sample=True)
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
        basic=True,
        counts=True,
        errorThreshold=0.0,
        percentiles=True,
        sample=True
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
        return "com.microsoft.azure.synapse.ml.stages.SummarizeData"

    @staticmethod
    def _from_java(java_stage):
        module_name=SummarizeData.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SummarizeData"
        return from_java(java_stage, module_name)

    def setBasic(self, value):
        """
        Args:
            basic: Compute basic statistics
        """
        self._set(basic=value)
        return self
    
    def setCounts(self, value):
        """
        Args:
            counts: Compute count statistics
        """
        self._set(counts=value)
        return self
    
    def setErrorThreshold(self, value):
        """
        Args:
            errorThreshold: Threshold for quantiles - 0 is exact
        """
        self._set(errorThreshold=value)
        return self
    
    def setPercentiles(self, value):
        """
        Args:
            percentiles: Compute percentiles
        """
        self._set(percentiles=value)
        return self
    
    def setSample(self, value):
        """
        Args:
            sample: Compute sample statistics
        """
        self._set(sample=value)
        return self

    
    def getBasic(self):
        """
        Returns:
            basic: Compute basic statistics
        """
        return self.getOrDefault(self.basic)
    
    
    def getCounts(self):
        """
        Returns:
            counts: Compute count statistics
        """
        return self.getOrDefault(self.counts)
    
    
    def getErrorThreshold(self):
        """
        Returns:
            errorThreshold: Threshold for quantiles - 0 is exact
        """
        return self.getOrDefault(self.errorThreshold)
    
    
    def getPercentiles(self):
        """
        Returns:
            percentiles: Compute percentiles
        """
        return self.getOrDefault(self.percentiles)
    
    
    def getSample(self):
        """
        Returns:
            sample: Compute sample statistics
        """
        return self.getOrDefault(self.sample)

    

    
        