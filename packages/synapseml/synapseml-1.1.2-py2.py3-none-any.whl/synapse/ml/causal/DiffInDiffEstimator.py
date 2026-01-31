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
from synapse.ml.causal.DiffInDiffModel import DiffInDiffModel

@inherit_doc
class DiffInDiffEstimator(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        outcomeCol (str): outcome column
        postTreatmentCol (str): post treatment indicator column
        treatmentCol (str): treatment column
    """

    outcomeCol = Param(Params._dummy(), "outcomeCol", "outcome column", typeConverter=TypeConverters.toString)
    
    postTreatmentCol = Param(Params._dummy(), "postTreatmentCol", "post treatment indicator column", typeConverter=TypeConverters.toString)
    
    treatmentCol = Param(Params._dummy(), "treatmentCol", "treatment column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        outcomeCol=None,
        postTreatmentCol=None,
        treatmentCol=None
        ):
        super(DiffInDiffEstimator, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.causal.DiffInDiffEstimator", self.uid)
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
        outcomeCol=None,
        postTreatmentCol=None,
        treatmentCol=None
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
        return "com.microsoft.azure.synapse.ml.causal.DiffInDiffEstimator"

    @staticmethod
    def _from_java(java_stage):
        module_name=DiffInDiffEstimator.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".DiffInDiffEstimator"
        return from_java(java_stage, module_name)

    def setOutcomeCol(self, value):
        """
        Args:
            outcomeCol: outcome column
        """
        self._set(outcomeCol=value)
        return self
    
    def setPostTreatmentCol(self, value):
        """
        Args:
            postTreatmentCol: post treatment indicator column
        """
        self._set(postTreatmentCol=value)
        return self
    
    def setTreatmentCol(self, value):
        """
        Args:
            treatmentCol: treatment column
        """
        self._set(treatmentCol=value)
        return self

    
    def getOutcomeCol(self):
        """
        Returns:
            outcomeCol: outcome column
        """
        return self.getOrDefault(self.outcomeCol)
    
    
    def getPostTreatmentCol(self):
        """
        Returns:
            postTreatmentCol: post treatment indicator column
        """
        return self.getOrDefault(self.postTreatmentCol)
    
    
    def getTreatmentCol(self):
        """
        Returns:
            treatmentCol: treatment column
        """
        return self.getOrDefault(self.treatmentCol)

    def _create_model(self, java_model):
        try:
            model = DiffInDiffModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = DiffInDiffModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        