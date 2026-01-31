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
class EnsembleByKey(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        colNames (list): Names of the result of each col
        collapseGroup (bool): Whether to collapse all items in group to one entry
        cols (list): Cols to ensemble
        keys (list): Keys to group by
        strategy (str): How to ensemble the scores, ex: mean
        vectorDims (dict): the dimensions of any vector columns, used to avoid materialization
    """

    colNames = Param(Params._dummy(), "colNames", "Names of the result of each col", typeConverter=TypeConverters.toListString)
    
    collapseGroup = Param(Params._dummy(), "collapseGroup", "Whether to collapse all items in group to one entry", typeConverter=TypeConverters.toBoolean)
    
    cols = Param(Params._dummy(), "cols", "Cols to ensemble", typeConverter=TypeConverters.toListString)
    
    keys = Param(Params._dummy(), "keys", "Keys to group by", typeConverter=TypeConverters.toListString)
    
    strategy = Param(Params._dummy(), "strategy", "How to ensemble the scores, ex: mean", typeConverter=TypeConverters.toString)
    
    vectorDims = Param(Params._dummy(), "vectorDims", "the dimensions of any vector columns, used to avoid materialization")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        colNames=None,
        collapseGroup=True,
        cols=None,
        keys=None,
        strategy="mean",
        vectorDims=None
        ):
        super(EnsembleByKey, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.EnsembleByKey", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(collapseGroup=True)
        self._setDefault(strategy="mean")
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
        colNames=None,
        collapseGroup=True,
        cols=None,
        keys=None,
        strategy="mean",
        vectorDims=None
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
        return "com.microsoft.azure.synapse.ml.stages.EnsembleByKey"

    @staticmethod
    def _from_java(java_stage):
        module_name=EnsembleByKey.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".EnsembleByKey"
        return from_java(java_stage, module_name)

    def setColNames(self, value):
        """
        Args:
            colNames: Names of the result of each col
        """
        self._set(colNames=value)
        return self
    
    def setCollapseGroup(self, value):
        """
        Args:
            collapseGroup: Whether to collapse all items in group to one entry
        """
        self._set(collapseGroup=value)
        return self
    
    def setCols(self, value):
        """
        Args:
            cols: Cols to ensemble
        """
        self._set(cols=value)
        return self
    
    def setKeys(self, value):
        """
        Args:
            keys: Keys to group by
        """
        self._set(keys=value)
        return self
    
    def setStrategy(self, value):
        """
        Args:
            strategy: How to ensemble the scores, ex: mean
        """
        self._set(strategy=value)
        return self
    
    def setVectorDims(self, value):
        """
        Args:
            vectorDims: the dimensions of any vector columns, used to avoid materialization
        """
        self._set(vectorDims=value)
        return self

    
    def getColNames(self):
        """
        Returns:
            colNames: Names of the result of each col
        """
        return self.getOrDefault(self.colNames)
    
    
    def getCollapseGroup(self):
        """
        Returns:
            collapseGroup: Whether to collapse all items in group to one entry
        """
        return self.getOrDefault(self.collapseGroup)
    
    
    def getCols(self):
        """
        Returns:
            cols: Cols to ensemble
        """
        return self.getOrDefault(self.cols)
    
    
    def getKeys(self):
        """
        Returns:
            keys: Keys to group by
        """
        return self.getOrDefault(self.keys)
    
    
    def getStrategy(self):
        """
        Returns:
            strategy: How to ensemble the scores, ex: mean
        """
        return self.getOrDefault(self.strategy)
    
    
    def getVectorDims(self):
        """
        Returns:
            vectorDims: the dimensions of any vector columns, used to avoid materialization
        """
        return self.getOrDefault(self.vectorDims)

    

    
        