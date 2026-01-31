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
class StratifiedRepartition(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        labelCol (str): The name of the label column
        mode (str): Specify equal to repartition with replacement across all labels, specify original to keep the ratios in the original dataset, or specify mixed to use a heuristic
        seed (long): random seed
    """

    labelCol = Param(Params._dummy(), "labelCol", "The name of the label column", typeConverter=TypeConverters.toString)
    
    mode = Param(Params._dummy(), "mode", "Specify equal to repartition with replacement across all labels, specify original to keep the ratios in the original dataset, or specify mixed to use a heuristic", typeConverter=TypeConverters.toString)
    
    seed = Param(Params._dummy(), "seed", "random seed")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        labelCol=None,
        mode="mixed",
        seed=1518410069
        ):
        super(StratifiedRepartition, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.StratifiedRepartition", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(mode="mixed")
        self._setDefault(seed=1518410069)
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
        labelCol=None,
        mode="mixed",
        seed=1518410069
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
        return "com.microsoft.azure.synapse.ml.stages.StratifiedRepartition"

    @staticmethod
    def _from_java(java_stage):
        module_name=StratifiedRepartition.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".StratifiedRepartition"
        return from_java(java_stage, module_name)

    def setLabelCol(self, value):
        """
        Args:
            labelCol: The name of the label column
        """
        self._set(labelCol=value)
        return self
    
    def setMode(self, value):
        """
        Args:
            mode: Specify equal to repartition with replacement across all labels, specify original to keep the ratios in the original dataset, or specify mixed to use a heuristic
        """
        self._set(mode=value)
        return self
    
    def setSeed(self, value):
        """
        Args:
            seed: random seed
        """
        self._set(seed=value)
        return self

    
    def getLabelCol(self):
        """
        Returns:
            labelCol: The name of the label column
        """
        return self.getOrDefault(self.labelCol)
    
    
    def getMode(self):
        """
        Returns:
            mode: Specify equal to repartition with replacement across all labels, specify original to keep the ratios in the original dataset, or specify mixed to use a heuristic
        """
        return self.getOrDefault(self.mode)
    
    
    def getSeed(self):
        """
        Returns:
            seed: random seed
        """
        return self.getOrDefault(self.seed)

    

    
        