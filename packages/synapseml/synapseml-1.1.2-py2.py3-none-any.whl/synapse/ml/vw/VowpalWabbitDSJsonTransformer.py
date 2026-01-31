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
class VowpalWabbitDSJsonTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        dsJsonColumn (str): Column containing ds-json. defaults to "value".
        rewards (dict): Extract bandit reward(s) from DS json. Defaults to _label_cost.
    """

    dsJsonColumn = Param(Params._dummy(), "dsJsonColumn", "Column containing ds-json. defaults to \"value\".", typeConverter=TypeConverters.toString)
    
    rewards = Param(Params._dummy(), "rewards", "Extract bandit reward(s) from DS json. Defaults to _label_cost.")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        dsJsonColumn="value",
        rewards={"reward":"_label_cost"}
        ):
        super(VowpalWabbitDSJsonTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.vw.VowpalWabbitDSJsonTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(dsJsonColumn="value")
        self._setDefault(rewards={"reward":"_label_cost"})
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
        dsJsonColumn="value",
        rewards={"reward":"_label_cost"}
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
        return "com.microsoft.azure.synapse.ml.vw.VowpalWabbitDSJsonTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=VowpalWabbitDSJsonTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".VowpalWabbitDSJsonTransformer"
        return from_java(java_stage, module_name)

    def setDsJsonColumn(self, value):
        """
        Args:
            dsJsonColumn: Column containing ds-json. defaults to "value".
        """
        self._set(dsJsonColumn=value)
        return self
    
    def setRewards(self, value):
        """
        Args:
            rewards: Extract bandit reward(s) from DS json. Defaults to _label_cost.
        """
        self._set(rewards=value)
        return self

    
    def getDsJsonColumn(self):
        """
        Returns:
            dsJsonColumn: Column containing ds-json. defaults to "value".
        """
        return self.getOrDefault(self.dsJsonColumn)
    
    
    def getRewards(self):
        """
        Returns:
            rewards: Extract bandit reward(s) from DS json. Defaults to _label_cost.
        """
        return self.getOrDefault(self.rewards)

    

    
        