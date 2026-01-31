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
from synapse.ml.stages.ClassBalancerModel import ClassBalancerModel

@inherit_doc
class ClassBalancer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        broadcastJoin (bool): Whether to broadcast the class to weight mapping to the worker
        inputCol (str): The name of the input column
        outputCol (str): The name of the output column
    """

    broadcastJoin = Param(Params._dummy(), "broadcastJoin", "Whether to broadcast the class to weight mapping to the worker", typeConverter=TypeConverters.toBoolean)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        broadcastJoin=True,
        inputCol=None,
        outputCol="weight"
        ):
        super(ClassBalancer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.ClassBalancer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(broadcastJoin=True)
        self._setDefault(outputCol="weight")
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
        broadcastJoin=True,
        inputCol=None,
        outputCol="weight"
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
        return "com.microsoft.azure.synapse.ml.stages.ClassBalancer"

    @staticmethod
    def _from_java(java_stage):
        module_name=ClassBalancer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ClassBalancer"
        return from_java(java_stage, module_name)

    def setBroadcastJoin(self, value):
        """
        Args:
            broadcastJoin: Whether to broadcast the class to weight mapping to the worker
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

    
    def getBroadcastJoin(self):
        """
        Returns:
            broadcastJoin: Whether to broadcast the class to weight mapping to the worker
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

    def _create_model(self, java_model):
        try:
            model = ClassBalancerModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = ClassBalancerModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        