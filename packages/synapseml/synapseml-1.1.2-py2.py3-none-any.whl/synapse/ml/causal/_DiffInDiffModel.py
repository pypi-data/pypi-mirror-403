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
class _DiffInDiffModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        timeCol (str): Specify the column that identifies the time when outcome is measured in the panel data. For example, if the outcome is measured daily, this column could be the Date column.
        timeIndex (object): time index
        timeIndexCol (str): time index column
        unitCol (str): Specify the name of the column which contains an identifier for each observed unit in the panel data. For example, if the observed units are users, this column could be the UserId column.
        unitIndex (object): unit index
        unitIndexCol (str): unit index column
    """

    timeCol = Param(Params._dummy(), "timeCol", "Specify the column that identifies the time when outcome is measured in the panel data. For example, if the outcome is measured daily, this column could be the Date column.", typeConverter=TypeConverters.toString)
    
    timeIndex = Param(Params._dummy(), "timeIndex", "time index")
    
    timeIndexCol = Param(Params._dummy(), "timeIndexCol", "time index column", typeConverter=TypeConverters.toString)
    
    unitCol = Param(Params._dummy(), "unitCol", "Specify the name of the column which contains an identifier for each observed unit in the panel data. For example, if the observed units are users, this column could be the UserId column.", typeConverter=TypeConverters.toString)
    
    unitIndex = Param(Params._dummy(), "unitIndex", "unit index")
    
    unitIndexCol = Param(Params._dummy(), "unitIndexCol", "unit index column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        timeCol=None,
        timeIndex=None,
        timeIndexCol=None,
        unitCol=None,
        unitIndex=None,
        unitIndexCol=None
        ):
        super(_DiffInDiffModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.causal.DiffInDiffModel", self.uid)
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
        timeCol=None,
        timeIndex=None,
        timeIndexCol=None,
        unitCol=None,
        unitIndex=None,
        unitIndexCol=None
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
        return "com.microsoft.azure.synapse.ml.causal.DiffInDiffModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_DiffInDiffModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".DiffInDiffModel"
        return from_java(java_stage, module_name)

    def setTimeCol(self, value):
        """
        Args:
            timeCol: Specify the column that identifies the time when outcome is measured in the panel data. For example, if the outcome is measured daily, this column could be the Date column.
        """
        self._set(timeCol=value)
        return self
    
    def setTimeIndex(self, value):
        """
        Args:
            timeIndex: time index
        """
        self._set(timeIndex=value)
        return self
    
    def setTimeIndexCol(self, value):
        """
        Args:
            timeIndexCol: time index column
        """
        self._set(timeIndexCol=value)
        return self
    
    def setUnitCol(self, value):
        """
        Args:
            unitCol: Specify the name of the column which contains an identifier for each observed unit in the panel data. For example, if the observed units are users, this column could be the UserId column.
        """
        self._set(unitCol=value)
        return self
    
    def setUnitIndex(self, value):
        """
        Args:
            unitIndex: unit index
        """
        self._set(unitIndex=value)
        return self
    
    def setUnitIndexCol(self, value):
        """
        Args:
            unitIndexCol: unit index column
        """
        self._set(unitIndexCol=value)
        return self

    
    def getTimeCol(self):
        """
        Returns:
            timeCol: Specify the column that identifies the time when outcome is measured in the panel data. For example, if the outcome is measured daily, this column could be the Date column.
        """
        return self.getOrDefault(self.timeCol)
    
    
    def getTimeIndex(self):
        """
        Returns:
            timeIndex: time index
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getTimeIndex(), sql_ctx)
    
    
    def getTimeIndexCol(self):
        """
        Returns:
            timeIndexCol: time index column
        """
        return self.getOrDefault(self.timeIndexCol)
    
    
    def getUnitCol(self):
        """
        Returns:
            unitCol: Specify the name of the column which contains an identifier for each observed unit in the panel data. For example, if the observed units are users, this column could be the UserId column.
        """
        return self.getOrDefault(self.unitCol)
    
    
    def getUnitIndex(self):
        """
        Returns:
            unitIndex: unit index
        """
        ctx = SparkContext._active_spark_context
        sql_ctx = SQLContext.getOrCreate(ctx)
        return DataFrame(self._java_obj.getUnitIndex(), sql_ctx)
    
    
    def getUnitIndexCol(self):
        """
        Returns:
            unitIndexCol: unit index column
        """
        return self.getOrDefault(self.unitIndexCol)

    

    
        