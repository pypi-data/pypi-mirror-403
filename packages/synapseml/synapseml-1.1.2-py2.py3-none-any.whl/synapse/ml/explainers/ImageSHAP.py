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
class ImageSHAP(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        cellSize (float): Number that controls the size of the superpixels
        infWeight (float): The double value to represent infinite weight. Default: 1E8.
        inputCol (str): input column name
        metricsCol (str): Column name for fitting metrics
        model (object): The model to be interpreted.
        modifier (float): Controls the trade-off spatial and color distance
        numSamples (int): Number of samples to generate.
        outputCol (str): output column name
        superpixelCol (str): The column holding the superpixel decompositions
        targetClasses (list): The indices of the classes for multinomial classification models. Default: 0.For regression models this parameter is ignored.
        targetClassesCol (str): The name of the column that specifies the indices of the classes for multinomial classification models.
        targetCol (str): The column name of the prediction target to explain (i.e. the response variable). This is usually set to "prediction" for regression models and "probability" for probabilistic classification models. Default value: probability
    """

    cellSize = Param(Params._dummy(), "cellSize", "Number that controls the size of the superpixels", typeConverter=TypeConverters.toFloat)
    
    infWeight = Param(Params._dummy(), "infWeight", "The double value to represent infinite weight. Default: 1E8.", typeConverter=TypeConverters.toFloat)
    
    inputCol = Param(Params._dummy(), "inputCol", "input column name", typeConverter=TypeConverters.toString)
    
    metricsCol = Param(Params._dummy(), "metricsCol", "Column name for fitting metrics", typeConverter=TypeConverters.toString)
    
    model = Param(Params._dummy(), "model", "The model to be interpreted.")
    
    modifier = Param(Params._dummy(), "modifier", "Controls the trade-off spatial and color distance", typeConverter=TypeConverters.toFloat)
    
    numSamples = Param(Params._dummy(), "numSamples", "Number of samples to generate.", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "output column name", typeConverter=TypeConverters.toString)
    
    superpixelCol = Param(Params._dummy(), "superpixelCol", "The column holding the superpixel decompositions", typeConverter=TypeConverters.toString)
    
    targetClasses = Param(Params._dummy(), "targetClasses", "The indices of the classes for multinomial classification models. Default: 0.For regression models this parameter is ignored.", typeConverter=TypeConverters.toListInt)
    
    targetClassesCol = Param(Params._dummy(), "targetClassesCol", "The name of the column that specifies the indices of the classes for multinomial classification models.", typeConverter=TypeConverters.toString)
    
    targetCol = Param(Params._dummy(), "targetCol", "The column name of the prediction target to explain (i.e. the response variable). This is usually set to \"prediction\" for regression models and \"probability\" for probabilistic classification models. Default value: probability", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        cellSize=16.0,
        infWeight=1.0E+8,
        inputCol=None,
        metricsCol="r2",
        model=None,
        modifier=130.0,
        numSamples=None,
        outputCol="ImageSHAP_fc82105e6267__output",
        superpixelCol="superpixels",
        targetClasses=[],
        targetClassesCol=None,
        targetCol="probability"
        ):
        super(ImageSHAP, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.explainers.ImageSHAP", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(cellSize=16.0)
        self._setDefault(infWeight=1.0E+8)
        self._setDefault(metricsCol="r2")
        self._setDefault(modifier=130.0)
        self._setDefault(outputCol="ImageSHAP_fc82105e6267__output")
        self._setDefault(superpixelCol="superpixels")
        self._setDefault(targetClasses=[])
        self._setDefault(targetCol="probability")
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
        cellSize=16.0,
        infWeight=1.0E+8,
        inputCol=None,
        metricsCol="r2",
        model=None,
        modifier=130.0,
        numSamples=None,
        outputCol="ImageSHAP_fc82105e6267__output",
        superpixelCol="superpixels",
        targetClasses=[],
        targetClassesCol=None,
        targetCol="probability"
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
        return "com.microsoft.azure.synapse.ml.explainers.ImageSHAP"

    @staticmethod
    def _from_java(java_stage):
        module_name=ImageSHAP.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ImageSHAP"
        return from_java(java_stage, module_name)

    def setCellSize(self, value):
        """
        Args:
            cellSize: Number that controls the size of the superpixels
        """
        self._set(cellSize=value)
        return self
    
    def setInfWeight(self, value):
        """
        Args:
            infWeight: The double value to represent infinite weight. Default: 1E8.
        """
        self._set(infWeight=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: input column name
        """
        self._set(inputCol=value)
        return self
    
    def setMetricsCol(self, value):
        """
        Args:
            metricsCol: Column name for fitting metrics
        """
        self._set(metricsCol=value)
        return self
    
    def setModel(self, value):
        """
        Args:
            model: The model to be interpreted.
        """
        self._set(model=value)
        return self
    
    def setModifier(self, value):
        """
        Args:
            modifier: Controls the trade-off spatial and color distance
        """
        self._set(modifier=value)
        return self
    
    def setNumSamples(self, value):
        """
        Args:
            numSamples: Number of samples to generate.
        """
        self._set(numSamples=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: output column name
        """
        self._set(outputCol=value)
        return self
    
    def setSuperpixelCol(self, value):
        """
        Args:
            superpixelCol: The column holding the superpixel decompositions
        """
        self._set(superpixelCol=value)
        return self
    
    def setTargetClasses(self, value):
        """
        Args:
            targetClasses: The indices of the classes for multinomial classification models. Default: 0.For regression models this parameter is ignored.
        """
        self._set(targetClasses=value)
        return self
    
    def setTargetClassesCol(self, value):
        """
        Args:
            targetClassesCol: The name of the column that specifies the indices of the classes for multinomial classification models.
        """
        self._set(targetClassesCol=value)
        return self
    
    def setTargetCol(self, value):
        """
        Args:
            targetCol: The column name of the prediction target to explain (i.e. the response variable). This is usually set to "prediction" for regression models and "probability" for probabilistic classification models. Default value: probability
        """
        self._set(targetCol=value)
        return self

    
    def getCellSize(self):
        """
        Returns:
            cellSize: Number that controls the size of the superpixels
        """
        return self.getOrDefault(self.cellSize)
    
    
    def getInfWeight(self):
        """
        Returns:
            infWeight: The double value to represent infinite weight. Default: 1E8.
        """
        return self.getOrDefault(self.infWeight)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: input column name
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getMetricsCol(self):
        """
        Returns:
            metricsCol: Column name for fitting metrics
        """
        return self.getOrDefault(self.metricsCol)
    
    
    def getModel(self):
        """
        Returns:
            model: The model to be interpreted.
        """
        return JavaParams._from_java(self._java_obj.getModel())
    
    
    def getModifier(self):
        """
        Returns:
            modifier: Controls the trade-off spatial and color distance
        """
        return self.getOrDefault(self.modifier)
    
    
    def getNumSamples(self):
        """
        Returns:
            numSamples: Number of samples to generate.
        """
        return self.getOrDefault(self.numSamples)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: output column name
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getSuperpixelCol(self):
        """
        Returns:
            superpixelCol: The column holding the superpixel decompositions
        """
        return self.getOrDefault(self.superpixelCol)
    
    
    def getTargetClasses(self):
        """
        Returns:
            targetClasses: The indices of the classes for multinomial classification models. Default: 0.For regression models this parameter is ignored.
        """
        return self.getOrDefault(self.targetClasses)
    
    
    def getTargetClassesCol(self):
        """
        Returns:
            targetClassesCol: The name of the column that specifies the indices of the classes for multinomial classification models.
        """
        return self.getOrDefault(self.targetClassesCol)
    
    
    def getTargetCol(self):
        """
        Returns:
            targetCol: The column name of the prediction target to explain (i.e. the response variable). This is usually set to "prediction" for regression models and "probability" for probabilistic classification models. Default value: probability
        """
        return self.getOrDefault(self.targetCol)

    

    
        