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
class SyntheticControlEstimator(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        epsilon (float): This value is added to the weights when we fit the final linear model for SyntheticControlEstimator and SyntheticDiffInDiffEstimator in order to avoid zero weights.
        handleMissingOutcome (str): How to handle missing outcomes. Options are skip (which will filter out units with missing outcomes), zero (fill in missing outcomes with zero), or impute (impute with nearest available outcomes, or mean if two nearest outcomes are available)
        localSolverThreshold (long): threshold for using local solver on driver node. Local solver is faster but relies on part of data being collected on driver node.
        maxIter (int): maximum number of iterations (>= 0)
        numIterNoChange (int): Early termination when number of iterations without change reached.
        outcomeCol (str): outcome column
        postTreatmentCol (str): post treatment indicator column
        stepSize (float): Step size to be used for each iteration of optimization (> 0)
        timeCol (str): Specify the column that identifies the time when outcome is measured in the panel data. For example, if the outcome is measured daily, this column could be the Date column.
        tol (float): the convergence tolerance for iterative algorithms (>= 0)
        treatmentCol (str): treatment column
        unitCol (str): Specify the name of the column which contains an identifier for each observed unit in the panel data. For example, if the observed units are users, this column could be the UserId column.
    """

    epsilon = Param(Params._dummy(), "epsilon", "This value is added to the weights when we fit the final linear model for SyntheticControlEstimator and SyntheticDiffInDiffEstimator in order to avoid zero weights.", typeConverter=TypeConverters.toFloat)
    
    handleMissingOutcome = Param(Params._dummy(), "handleMissingOutcome", "How to handle missing outcomes. Options are skip (which will filter out units with missing outcomes), zero (fill in missing outcomes with zero), or impute (impute with nearest available outcomes, or mean if two nearest outcomes are available)", typeConverter=TypeConverters.toString)
    
    localSolverThreshold = Param(Params._dummy(), "localSolverThreshold", "threshold for using local solver on driver node. Local solver is faster but relies on part of data being collected on driver node.")
    
    maxIter = Param(Params._dummy(), "maxIter", "maximum number of iterations (>= 0)", typeConverter=TypeConverters.toInt)
    
    numIterNoChange = Param(Params._dummy(), "numIterNoChange", "Early termination when number of iterations without change reached.", typeConverter=TypeConverters.toInt)
    
    outcomeCol = Param(Params._dummy(), "outcomeCol", "outcome column", typeConverter=TypeConverters.toString)
    
    postTreatmentCol = Param(Params._dummy(), "postTreatmentCol", "post treatment indicator column", typeConverter=TypeConverters.toString)
    
    stepSize = Param(Params._dummy(), "stepSize", "Step size to be used for each iteration of optimization (> 0)", typeConverter=TypeConverters.toFloat)
    
    timeCol = Param(Params._dummy(), "timeCol", "Specify the column that identifies the time when outcome is measured in the panel data. For example, if the outcome is measured daily, this column could be the Date column.", typeConverter=TypeConverters.toString)
    
    tol = Param(Params._dummy(), "tol", "the convergence tolerance for iterative algorithms (>= 0)", typeConverter=TypeConverters.toFloat)
    
    treatmentCol = Param(Params._dummy(), "treatmentCol", "treatment column", typeConverter=TypeConverters.toString)
    
    unitCol = Param(Params._dummy(), "unitCol", "Specify the name of the column which contains an identifier for each observed unit in the panel data. For example, if the observed units are users, this column could be the UserId column.", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        epsilon=1.0E-10,
        handleMissingOutcome="zero",
        localSolverThreshold=1000000,
        maxIter=100,
        numIterNoChange=None,
        outcomeCol=None,
        postTreatmentCol=None,
        stepSize=1.0,
        timeCol=None,
        tol=0.001,
        treatmentCol=None,
        unitCol=None
        ):
        super(SyntheticControlEstimator, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.causal.SyntheticControlEstimator", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(epsilon=1.0E-10)
        self._setDefault(handleMissingOutcome="zero")
        self._setDefault(localSolverThreshold=1000000)
        self._setDefault(maxIter=100)
        self._setDefault(stepSize=1.0)
        self._setDefault(tol=0.001)
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
        epsilon=1.0E-10,
        handleMissingOutcome="zero",
        localSolverThreshold=1000000,
        maxIter=100,
        numIterNoChange=None,
        outcomeCol=None,
        postTreatmentCol=None,
        stepSize=1.0,
        timeCol=None,
        tol=0.001,
        treatmentCol=None,
        unitCol=None
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
        return "com.microsoft.azure.synapse.ml.causal.SyntheticControlEstimator"

    @staticmethod
    def _from_java(java_stage):
        module_name=SyntheticControlEstimator.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SyntheticControlEstimator"
        return from_java(java_stage, module_name)

    def setEpsilon(self, value):
        """
        Args:
            epsilon: This value is added to the weights when we fit the final linear model for SyntheticControlEstimator and SyntheticDiffInDiffEstimator in order to avoid zero weights.
        """
        self._set(epsilon=value)
        return self
    
    def setHandleMissingOutcome(self, value):
        """
        Args:
            handleMissingOutcome: How to handle missing outcomes. Options are skip (which will filter out units with missing outcomes), zero (fill in missing outcomes with zero), or impute (impute with nearest available outcomes, or mean if two nearest outcomes are available)
        """
        self._set(handleMissingOutcome=value)
        return self
    
    def setLocalSolverThreshold(self, value):
        """
        Args:
            localSolverThreshold: threshold for using local solver on driver node. Local solver is faster but relies on part of data being collected on driver node.
        """
        self._set(localSolverThreshold=value)
        return self
    
    def setMaxIter(self, value):
        """
        Args:
            maxIter: maximum number of iterations (>= 0)
        """
        self._set(maxIter=value)
        return self
    
    def setNumIterNoChange(self, value):
        """
        Args:
            numIterNoChange: Early termination when number of iterations without change reached.
        """
        self._set(numIterNoChange=value)
        return self
    
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
    
    def setStepSize(self, value):
        """
        Args:
            stepSize: Step size to be used for each iteration of optimization (> 0)
        """
        self._set(stepSize=value)
        return self
    
    def setTimeCol(self, value):
        """
        Args:
            timeCol: Specify the column that identifies the time when outcome is measured in the panel data. For example, if the outcome is measured daily, this column could be the Date column.
        """
        self._set(timeCol=value)
        return self
    
    def setTol(self, value):
        """
        Args:
            tol: the convergence tolerance for iterative algorithms (>= 0)
        """
        self._set(tol=value)
        return self
    
    def setTreatmentCol(self, value):
        """
        Args:
            treatmentCol: treatment column
        """
        self._set(treatmentCol=value)
        return self
    
    def setUnitCol(self, value):
        """
        Args:
            unitCol: Specify the name of the column which contains an identifier for each observed unit in the panel data. For example, if the observed units are users, this column could be the UserId column.
        """
        self._set(unitCol=value)
        return self

    
    def getEpsilon(self):
        """
        Returns:
            epsilon: This value is added to the weights when we fit the final linear model for SyntheticControlEstimator and SyntheticDiffInDiffEstimator in order to avoid zero weights.
        """
        return self.getOrDefault(self.epsilon)
    
    
    def getHandleMissingOutcome(self):
        """
        Returns:
            handleMissingOutcome: How to handle missing outcomes. Options are skip (which will filter out units with missing outcomes), zero (fill in missing outcomes with zero), or impute (impute with nearest available outcomes, or mean if two nearest outcomes are available)
        """
        return self.getOrDefault(self.handleMissingOutcome)
    
    
    def getLocalSolverThreshold(self):
        """
        Returns:
            localSolverThreshold: threshold for using local solver on driver node. Local solver is faster but relies on part of data being collected on driver node.
        """
        return self.getOrDefault(self.localSolverThreshold)
    
    
    def getMaxIter(self):
        """
        Returns:
            maxIter: maximum number of iterations (>= 0)
        """
        return self.getOrDefault(self.maxIter)
    
    
    def getNumIterNoChange(self):
        """
        Returns:
            numIterNoChange: Early termination when number of iterations without change reached.
        """
        return self.getOrDefault(self.numIterNoChange)
    
    
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
    
    
    def getStepSize(self):
        """
        Returns:
            stepSize: Step size to be used for each iteration of optimization (> 0)
        """
        return self.getOrDefault(self.stepSize)
    
    
    def getTimeCol(self):
        """
        Returns:
            timeCol: Specify the column that identifies the time when outcome is measured in the panel data. For example, if the outcome is measured daily, this column could be the Date column.
        """
        return self.getOrDefault(self.timeCol)
    
    
    def getTol(self):
        """
        Returns:
            tol: the convergence tolerance for iterative algorithms (>= 0)
        """
        return self.getOrDefault(self.tol)
    
    
    def getTreatmentCol(self):
        """
        Returns:
            treatmentCol: treatment column
        """
        return self.getOrDefault(self.treatmentCol)
    
    
    def getUnitCol(self):
        """
        Returns:
            unitCol: Specify the name of the column which contains an identifier for each observed unit in the panel data. For example, if the observed units are users, this column could be the UserId column.
        """
        return self.getOrDefault(self.unitCol)

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

    
        