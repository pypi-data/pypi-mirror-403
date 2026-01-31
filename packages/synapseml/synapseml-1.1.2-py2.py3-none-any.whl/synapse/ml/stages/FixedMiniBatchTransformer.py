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
class FixedMiniBatchTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        batchSize (int): The max size of the buffer
        buffered (bool): Whether or not to buffer batches in memory
        maxBufferSize (int): The max size of the buffer
    """

    batchSize = Param(Params._dummy(), "batchSize", "The max size of the buffer", typeConverter=TypeConverters.toInt)
    
    buffered = Param(Params._dummy(), "buffered", "Whether or not to buffer batches in memory", typeConverter=TypeConverters.toBoolean)
    
    maxBufferSize = Param(Params._dummy(), "maxBufferSize", "The max size of the buffer", typeConverter=TypeConverters.toInt)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        batchSize=None,
        buffered=False,
        maxBufferSize=2147483647
        ):
        super(FixedMiniBatchTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.FixedMiniBatchTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(buffered=False)
        self._setDefault(maxBufferSize=2147483647)
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
        batchSize=None,
        buffered=False,
        maxBufferSize=2147483647
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
        return "com.microsoft.azure.synapse.ml.stages.FixedMiniBatchTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=FixedMiniBatchTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".FixedMiniBatchTransformer"
        return from_java(java_stage, module_name)

    def setBatchSize(self, value):
        """
        Args:
            batchSize: The max size of the buffer
        """
        self._set(batchSize=value)
        return self
    
    def setBuffered(self, value):
        """
        Args:
            buffered: Whether or not to buffer batches in memory
        """
        self._set(buffered=value)
        return self
    
    def setMaxBufferSize(self, value):
        """
        Args:
            maxBufferSize: The max size of the buffer
        """
        self._set(maxBufferSize=value)
        return self

    
    def getBatchSize(self):
        """
        Returns:
            batchSize: The max size of the buffer
        """
        return self.getOrDefault(self.batchSize)
    
    
    def getBuffered(self):
        """
        Returns:
            buffered: Whether or not to buffer batches in memory
        """
        return self.getOrDefault(self.buffered)
    
    
    def getMaxBufferSize(self):
        """
        Returns:
            maxBufferSize: The max size of the buffer
        """
        return self.getOrDefault(self.maxBufferSize)

    

    
        