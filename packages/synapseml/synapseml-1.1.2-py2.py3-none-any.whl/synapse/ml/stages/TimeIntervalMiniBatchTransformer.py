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
class TimeIntervalMiniBatchTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        maxBatchSize (int): The max size of the buffer
        millisToWait (int): The time to wait before constructing a batch
    """

    maxBatchSize = Param(Params._dummy(), "maxBatchSize", "The max size of the buffer", typeConverter=TypeConverters.toInt)
    
    millisToWait = Param(Params._dummy(), "millisToWait", "The time to wait before constructing a batch", typeConverter=TypeConverters.toInt)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        maxBatchSize=2147483647,
        millisToWait=None
        ):
        super(TimeIntervalMiniBatchTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.TimeIntervalMiniBatchTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(maxBatchSize=2147483647)
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
        maxBatchSize=2147483647,
        millisToWait=None
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
        return "com.microsoft.azure.synapse.ml.stages.TimeIntervalMiniBatchTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=TimeIntervalMiniBatchTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".TimeIntervalMiniBatchTransformer"
        return from_java(java_stage, module_name)

    def setMaxBatchSize(self, value):
        """
        Args:
            maxBatchSize: The max size of the buffer
        """
        self._set(maxBatchSize=value)
        return self
    
    def setMillisToWait(self, value):
        """
        Args:
            millisToWait: The time to wait before constructing a batch
        """
        self._set(millisToWait=value)
        return self

    
    def getMaxBatchSize(self):
        """
        Returns:
            maxBatchSize: The max size of the buffer
        """
        return self.getOrDefault(self.maxBatchSize)
    
    
    def getMillisToWait(self):
        """
        Returns:
            millisToWait: The time to wait before constructing a batch
        """
        return self.getOrDefault(self.millisToWait)

    

    
        