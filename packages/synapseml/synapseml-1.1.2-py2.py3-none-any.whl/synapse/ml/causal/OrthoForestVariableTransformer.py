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
class OrthoForestVariableTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        outcomeResidualCol (str): Outcome Residual Col
        outputCol (str): The name of the output column
        treatmentResidualCol (str): Treatment Residual Col
        weightsCol (str): Weights Col
    """

    outcomeResidualCol = Param(Params._dummy(), "outcomeResidualCol", "Outcome Residual Col", typeConverter=TypeConverters.toString)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    treatmentResidualCol = Param(Params._dummy(), "treatmentResidualCol", "Treatment Residual Col", typeConverter=TypeConverters.toString)
    
    weightsCol = Param(Params._dummy(), "weightsCol", "Weights Col", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        outcomeResidualCol="OResid",
        outputCol="_tmp_tsOutcome",
        treatmentResidualCol="TResid",
        weightsCol="_tmp_twOutcome"
        ):
        super(OrthoForestVariableTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.causal.OrthoForestVariableTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(outcomeResidualCol="OResid")
        self._setDefault(outputCol="_tmp_tsOutcome")
        self._setDefault(treatmentResidualCol="TResid")
        self._setDefault(weightsCol="_tmp_twOutcome")
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
        outcomeResidualCol="OResid",
        outputCol="_tmp_tsOutcome",
        treatmentResidualCol="TResid",
        weightsCol="_tmp_twOutcome"
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
        return "com.microsoft.azure.synapse.ml.causal.OrthoForestVariableTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=OrthoForestVariableTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".OrthoForestVariableTransformer"
        return from_java(java_stage, module_name)

    def setOutcomeResidualCol(self, value):
        """
        Args:
            outcomeResidualCol: Outcome Residual Col
        """
        self._set(outcomeResidualCol=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setTreatmentResidualCol(self, value):
        """
        Args:
            treatmentResidualCol: Treatment Residual Col
        """
        self._set(treatmentResidualCol=value)
        return self
    
    def setWeightsCol(self, value):
        """
        Args:
            weightsCol: Weights Col
        """
        self._set(weightsCol=value)
        return self

    
    def getOutcomeResidualCol(self):
        """
        Returns:
            outcomeResidualCol: Outcome Residual Col
        """
        return self.getOrDefault(self.outcomeResidualCol)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getTreatmentResidualCol(self):
        """
        Returns:
            treatmentResidualCol: Treatment Residual Col
        """
        return self.getOrDefault(self.treatmentResidualCol)
    
    
    def getWeightsCol(self):
        """
        Returns:
            weightsCol: Weights Col
        """
        return self.getOrDefault(self.weightsCol)

    

    
        