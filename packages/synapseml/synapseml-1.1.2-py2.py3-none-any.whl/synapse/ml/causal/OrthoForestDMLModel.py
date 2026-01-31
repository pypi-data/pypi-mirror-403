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
class OrthoForestDMLModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        confidenceLevel (float): confidence level, default value is 0.975
        confounderVecCol (str): Confounders to control for
        featuresCol (str): The name of the features column
        forest (object): Forest Trees produced in Ortho Forest DML Estimator
        heterogeneityVecCol (str): Vector to divide the treatment by
        maxDepth (int): Max Depth of Tree
        maxIter (int): maximum number of iterations (>= 0)
        minSamplesLeaf (int): Max Depth of Tree
        numTrees (int): Number of trees
        outcomeCol (str): outcome column
        outcomeModel (object): outcome model to run
        outcomeResidualCol (str): Outcome Residual Column
        outputCol (str): The name of the output column
        outputHighCol (str): Output Confidence Interval Low
        outputLowCol (str): Output Confidence Interval Low
        parallelism (int): the number of threads to use when running parallel algorithms
        sampleSplitRatio (list): Sample split ratio for cross-fitting. Default: [0.5, 0.5].
        treatmentCol (str): treatment column
        treatmentModel (object): treatment model to run
        treatmentResidualCol (str): Treatment Residual Column
        weightCol (str): The name of the weight column
    """

    confidenceLevel = Param(Params._dummy(), "confidenceLevel", "confidence level, default value is 0.975", typeConverter=TypeConverters.toFloat)
    
    confounderVecCol = Param(Params._dummy(), "confounderVecCol", "Confounders to control for", typeConverter=TypeConverters.toString)
    
    featuresCol = Param(Params._dummy(), "featuresCol", "The name of the features column", typeConverter=TypeConverters.toString)
    
    forest = Param(Params._dummy(), "forest", "Forest Trees produced in Ortho Forest DML Estimator")
    
    heterogeneityVecCol = Param(Params._dummy(), "heterogeneityVecCol", "Vector to divide the treatment by", typeConverter=TypeConverters.toString)
    
    maxDepth = Param(Params._dummy(), "maxDepth", "Max Depth of Tree", typeConverter=TypeConverters.toInt)
    
    maxIter = Param(Params._dummy(), "maxIter", "maximum number of iterations (>= 0)", typeConverter=TypeConverters.toInt)
    
    minSamplesLeaf = Param(Params._dummy(), "minSamplesLeaf", "Max Depth of Tree", typeConverter=TypeConverters.toInt)
    
    numTrees = Param(Params._dummy(), "numTrees", "Number of trees", typeConverter=TypeConverters.toInt)
    
    outcomeCol = Param(Params._dummy(), "outcomeCol", "outcome column", typeConverter=TypeConverters.toString)
    
    outcomeModel = Param(Params._dummy(), "outcomeModel", "outcome model to run")
    
    outcomeResidualCol = Param(Params._dummy(), "outcomeResidualCol", "Outcome Residual Column", typeConverter=TypeConverters.toString)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    outputHighCol = Param(Params._dummy(), "outputHighCol", "Output Confidence Interval Low", typeConverter=TypeConverters.toString)
    
    outputLowCol = Param(Params._dummy(), "outputLowCol", "Output Confidence Interval Low", typeConverter=TypeConverters.toString)
    
    parallelism = Param(Params._dummy(), "parallelism", "the number of threads to use when running parallel algorithms", typeConverter=TypeConverters.toInt)
    
    sampleSplitRatio = Param(Params._dummy(), "sampleSplitRatio", "Sample split ratio for cross-fitting. Default: [0.5, 0.5].", typeConverter=TypeConverters.toListFloat)
    
    treatmentCol = Param(Params._dummy(), "treatmentCol", "treatment column", typeConverter=TypeConverters.toString)
    
    treatmentModel = Param(Params._dummy(), "treatmentModel", "treatment model to run")
    
    treatmentResidualCol = Param(Params._dummy(), "treatmentResidualCol", "Treatment Residual Column", typeConverter=TypeConverters.toString)
    
    weightCol = Param(Params._dummy(), "weightCol", "The name of the weight column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        confidenceLevel=0.975,
        confounderVecCol="XW",
        featuresCol=None,
        forest=None,
        heterogeneityVecCol="X",
        maxDepth=5,
        maxIter=1,
        minSamplesLeaf=10,
        numTrees=20,
        outcomeCol=None,
        outcomeModel=None,
        outcomeResidualCol="OutcomeResidual",
        outputCol="EffectAverage",
        outputHighCol="EffectUpperBound",
        outputLowCol="EffectLowerBound",
        parallelism=10,
        sampleSplitRatio=[0.5,0.5],
        treatmentCol=None,
        treatmentModel=None,
        treatmentResidualCol="TreatmentResidual",
        weightCol=None
        ):
        super(OrthoForestDMLModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.causal.OrthoForestDMLModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(confidenceLevel=0.975)
        self._setDefault(confounderVecCol="XW")
        self._setDefault(heterogeneityVecCol="X")
        self._setDefault(maxDepth=5)
        self._setDefault(maxIter=1)
        self._setDefault(minSamplesLeaf=10)
        self._setDefault(numTrees=20)
        self._setDefault(outcomeResidualCol="OutcomeResidual")
        self._setDefault(outputCol="EffectAverage")
        self._setDefault(outputHighCol="EffectUpperBound")
        self._setDefault(outputLowCol="EffectLowerBound")
        self._setDefault(parallelism=10)
        self._setDefault(sampleSplitRatio=[0.5,0.5])
        self._setDefault(treatmentResidualCol="TreatmentResidual")
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
        confidenceLevel=0.975,
        confounderVecCol="XW",
        featuresCol=None,
        forest=None,
        heterogeneityVecCol="X",
        maxDepth=5,
        maxIter=1,
        minSamplesLeaf=10,
        numTrees=20,
        outcomeCol=None,
        outcomeModel=None,
        outcomeResidualCol="OutcomeResidual",
        outputCol="EffectAverage",
        outputHighCol="EffectUpperBound",
        outputLowCol="EffectLowerBound",
        parallelism=10,
        sampleSplitRatio=[0.5,0.5],
        treatmentCol=None,
        treatmentModel=None,
        treatmentResidualCol="TreatmentResidual",
        weightCol=None
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
        return "com.microsoft.azure.synapse.ml.causal.OrthoForestDMLModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=OrthoForestDMLModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".OrthoForestDMLModel"
        return from_java(java_stage, module_name)

    def setConfidenceLevel(self, value):
        """
        Args:
            confidenceLevel: confidence level, default value is 0.975
        """
        self._set(confidenceLevel=value)
        return self
    
    def setConfounderVecCol(self, value):
        """
        Args:
            confounderVecCol: Confounders to control for
        """
        self._set(confounderVecCol=value)
        return self
    
    def setFeaturesCol(self, value):
        """
        Args:
            featuresCol: The name of the features column
        """
        self._set(featuresCol=value)
        return self
    
    def setForest(self, value):
        """
        Args:
            forest: Forest Trees produced in Ortho Forest DML Estimator
        """
        self._set(forest=value)
        return self
    
    def setHeterogeneityVecCol(self, value):
        """
        Args:
            heterogeneityVecCol: Vector to divide the treatment by
        """
        self._set(heterogeneityVecCol=value)
        return self
    
    def setMaxDepth(self, value):
        """
        Args:
            maxDepth: Max Depth of Tree
        """
        self._set(maxDepth=value)
        return self
    
    def setMaxIter(self, value):
        """
        Args:
            maxIter: maximum number of iterations (>= 0)
        """
        self._set(maxIter=value)
        return self
    
    def setMinSamplesLeaf(self, value):
        """
        Args:
            minSamplesLeaf: Max Depth of Tree
        """
        self._set(minSamplesLeaf=value)
        return self
    
    def setNumTrees(self, value):
        """
        Args:
            numTrees: Number of trees
        """
        self._set(numTrees=value)
        return self
    
    def setOutcomeCol(self, value):
        """
        Args:
            outcomeCol: outcome column
        """
        self._set(outcomeCol=value)
        return self
    
    def setOutcomeModel(self, value):
        """
        Args:
            outcomeModel: outcome model to run
        """
        self._set(outcomeModel=value)
        return self
    
    def setOutcomeResidualCol(self, value):
        """
        Args:
            outcomeResidualCol: Outcome Residual Column
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
    
    def setOutputHighCol(self, value):
        """
        Args:
            outputHighCol: Output Confidence Interval Low
        """
        self._set(outputHighCol=value)
        return self
    
    def setOutputLowCol(self, value):
        """
        Args:
            outputLowCol: Output Confidence Interval Low
        """
        self._set(outputLowCol=value)
        return self
    
    def setParallelism(self, value):
        """
        Args:
            parallelism: the number of threads to use when running parallel algorithms
        """
        self._set(parallelism=value)
        return self
    
    def setSampleSplitRatio(self, value):
        """
        Args:
            sampleSplitRatio: Sample split ratio for cross-fitting. Default: [0.5, 0.5].
        """
        self._set(sampleSplitRatio=value)
        return self
    
    def setTreatmentCol(self, value):
        """
        Args:
            treatmentCol: treatment column
        """
        self._set(treatmentCol=value)
        return self
    
    def setTreatmentModel(self, value):
        """
        Args:
            treatmentModel: treatment model to run
        """
        self._set(treatmentModel=value)
        return self
    
    def setTreatmentResidualCol(self, value):
        """
        Args:
            treatmentResidualCol: Treatment Residual Column
        """
        self._set(treatmentResidualCol=value)
        return self
    
    def setWeightCol(self, value):
        """
        Args:
            weightCol: The name of the weight column
        """
        self._set(weightCol=value)
        return self

    
    def getConfidenceLevel(self):
        """
        Returns:
            confidenceLevel: confidence level, default value is 0.975
        """
        return self.getOrDefault(self.confidenceLevel)
    
    
    def getConfounderVecCol(self):
        """
        Returns:
            confounderVecCol: Confounders to control for
        """
        return self.getOrDefault(self.confounderVecCol)
    
    
    def getFeaturesCol(self):
        """
        Returns:
            featuresCol: The name of the features column
        """
        return self.getOrDefault(self.featuresCol)
    
    
    def getForest(self):
        """
        Returns:
            forest: Forest Trees produced in Ortho Forest DML Estimator
        """
        return self.getOrDefault(self.forest)
    
    
    def getHeterogeneityVecCol(self):
        """
        Returns:
            heterogeneityVecCol: Vector to divide the treatment by
        """
        return self.getOrDefault(self.heterogeneityVecCol)
    
    
    def getMaxDepth(self):
        """
        Returns:
            maxDepth: Max Depth of Tree
        """
        return self.getOrDefault(self.maxDepth)
    
    
    def getMaxIter(self):
        """
        Returns:
            maxIter: maximum number of iterations (>= 0)
        """
        return self.getOrDefault(self.maxIter)
    
    
    def getMinSamplesLeaf(self):
        """
        Returns:
            minSamplesLeaf: Max Depth of Tree
        """
        return self.getOrDefault(self.minSamplesLeaf)
    
    
    def getNumTrees(self):
        """
        Returns:
            numTrees: Number of trees
        """
        return self.getOrDefault(self.numTrees)
    
    
    def getOutcomeCol(self):
        """
        Returns:
            outcomeCol: outcome column
        """
        return self.getOrDefault(self.outcomeCol)
    
    
    def getOutcomeModel(self):
        """
        Returns:
            outcomeModel: outcome model to run
        """
        return JavaParams._from_java(self._java_obj.getOutcomeModel())
    
    
    def getOutcomeResidualCol(self):
        """
        Returns:
            outcomeResidualCol: Outcome Residual Column
        """
        return self.getOrDefault(self.outcomeResidualCol)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getOutputHighCol(self):
        """
        Returns:
            outputHighCol: Output Confidence Interval Low
        """
        return self.getOrDefault(self.outputHighCol)
    
    
    def getOutputLowCol(self):
        """
        Returns:
            outputLowCol: Output Confidence Interval Low
        """
        return self.getOrDefault(self.outputLowCol)
    
    
    def getParallelism(self):
        """
        Returns:
            parallelism: the number of threads to use when running parallel algorithms
        """
        return self.getOrDefault(self.parallelism)
    
    
    def getSampleSplitRatio(self):
        """
        Returns:
            sampleSplitRatio: Sample split ratio for cross-fitting. Default: [0.5, 0.5].
        """
        return self.getOrDefault(self.sampleSplitRatio)
    
    
    def getTreatmentCol(self):
        """
        Returns:
            treatmentCol: treatment column
        """
        return self.getOrDefault(self.treatmentCol)
    
    
    def getTreatmentModel(self):
        """
        Returns:
            treatmentModel: treatment model to run
        """
        return JavaParams._from_java(self._java_obj.getTreatmentModel())
    
    
    def getTreatmentResidualCol(self):
        """
        Returns:
            treatmentResidualCol: Treatment Residual Column
        """
        return self.getOrDefault(self.treatmentResidualCol)
    
    
    def getWeightCol(self):
        """
        Returns:
            weightCol: The name of the weight column
        """
        return self.getOrDefault(self.weightCol)

    

    
        