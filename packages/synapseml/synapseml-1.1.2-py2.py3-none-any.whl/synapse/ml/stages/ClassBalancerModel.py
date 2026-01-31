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
class ClassBalancerModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        broadcastJoin (bool): whether to broadcast join
        inputCol (str): The name of the input column
        outputCol (str): The name of the output column
        weights (object): the dataframe of weights
    """

    broadcastJoin = Param(Params._dummy(), "broadcastJoin", "whether to broadcast join", typeConverter=TypeConverters.toBoolean)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    weights = Param(Params._dummy(), "weights", "the dataframe of weights")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        broadcastJoin=None,
        inputCol=None,
        outputCol=None,
        weights=None
        ):
        super(ClassBalancerModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.ClassBalancerModel", self.uid)
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
        broadcastJoin=None,
        inputCol=None,
        outputCol=None,
        weights=None
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
        return "com.microsoft.azure.synapse.ml.stages.ClassBalancerModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=ClassBalancerModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ClassBalancerModel"
        return from_java(java_stage, module_name)

    def setBroadcastJoin(self, value):
        """
        Args:
            broadcastJoin: whether to broadcast join
        """
        self._set(broadcastJoin=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setWeights(self, value):
        """
        Args:
            weights: the dataframe of weights
        """
        self._set(weights=value)
        return self

    
    def getBroadcastJoin(self):
        """
        Returns:
            broadcastJoin: whether to broadcast join
        """
        return self.getOrDefault(self.broadcastJoin)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getWeights(self):
        """
        Returns:
            weights: the dataframe of weights
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getWeights(), sql_ctx)

    

    
        