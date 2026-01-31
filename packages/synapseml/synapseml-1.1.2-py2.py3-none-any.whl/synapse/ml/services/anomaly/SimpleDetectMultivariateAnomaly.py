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
class SimpleDetectMultivariateAnomaly(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        backoffs (list): array of backoffs to use in the handler
        diagnosticsInfo (object): diagnosticsInfo for training a multivariate anomaly detection model
        endTime (str): A required field, end time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        errorCol (str): column to hold http errors
        handler (object): Which strategy to use when handling requests
        initialPollingDelay (int): number of milliseconds to wait before first poll for result
        inputCols (list): The names of the input columns
        intermediateSaveDir (str): Blob storage location in HDFS where intermediate data is saved while training.
        maxPollingRetries (int): number of times to poll
        modelId (str): Format - uuid. Model identifier.
        outputCol (str): The name of the output column
        pollingDelay (int): number of milliseconds to wait between polling
        startTime (str): A required field, start time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        subscriptionKey (object): the API key to use
        suppressMaxRetriesException (bool): set true to suppress the maxumimum retries exception and report in the error column
        timestampCol (str): Timestamp column name
        topContributorCount (int): This is a number that you could specify N from 1 to 30, which will give you the details of top N contributed variables in the anomaly results. For example, if you have 100 variables in the model, but you only care the top five contributed variables in detection results, then you should fill this field with 5. The default number is 10.
        url (str): Url of the service
    """

    backoffs = Param(Params._dummy(), "backoffs", "array of backoffs to use in the handler", typeConverter=TypeConverters.toListInt)
    
    diagnosticsInfo = Param(Params._dummy(), "diagnosticsInfo", "diagnosticsInfo for training a multivariate anomaly detection model")
    
    endTime = Param(Params._dummy(), "endTime", "A required field, end time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.", typeConverter=TypeConverters.toString)
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    handler = Param(Params._dummy(), "handler", "Which strategy to use when handling requests")
    
    initialPollingDelay = Param(Params._dummy(), "initialPollingDelay", "number of milliseconds to wait before first poll for result", typeConverter=TypeConverters.toInt)
    
    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    intermediateSaveDir = Param(Params._dummy(), "intermediateSaveDir", "Blob storage location in HDFS where intermediate data is saved while training.", typeConverter=TypeConverters.toString)
    
    maxPollingRetries = Param(Params._dummy(), "maxPollingRetries", "number of times to poll", typeConverter=TypeConverters.toInt)
    
    modelId = Param(Params._dummy(), "modelId", "Format - uuid. Model identifier.", typeConverter=TypeConverters.toString)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    pollingDelay = Param(Params._dummy(), "pollingDelay", "number of milliseconds to wait between polling", typeConverter=TypeConverters.toInt)
    
    startTime = Param(Params._dummy(), "startTime", "A required field, start time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.", typeConverter=TypeConverters.toString)
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    suppressMaxRetriesException = Param(Params._dummy(), "suppressMaxRetriesException", "set true to suppress the maxumimum retries exception and report in the error column", typeConverter=TypeConverters.toBoolean)
    
    timestampCol = Param(Params._dummy(), "timestampCol", "Timestamp column name", typeConverter=TypeConverters.toString)
    
    topContributorCount = Param(Params._dummy(), "topContributorCount", "This is a number that you could specify N from 1 to 30, which will give you the details of top N contributed variables in the anomaly results. For example, if you have 100 variables in the model, but you only care the top five contributed variables in detection results, then you should fill this field with 5. The default number is 10.", typeConverter=TypeConverters.toInt)
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        backoffs=[100,500,1000],
        diagnosticsInfo=None,
        endTime=None,
        errorCol="SimpleDetectMultivariateAnomaly_0bb9a87fe345_error",
        handler=None,
        initialPollingDelay=300,
        inputCols=None,
        intermediateSaveDir=None,
        maxPollingRetries=1000,
        modelId=None,
        outputCol="SimpleDetectMultivariateAnomaly_0bb9a87fe345_output",
        pollingDelay=300,
        startTime=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        suppressMaxRetriesException=False,
        timestampCol="timestamp",
        topContributorCount=10,
        url=None
        ):
        super(SimpleDetectMultivariateAnomaly, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.anomaly.SimpleDetectMultivariateAnomaly", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(backoffs=[100,500,1000])
        self._setDefault(errorCol="SimpleDetectMultivariateAnomaly_0bb9a87fe345_error")
        self._setDefault(initialPollingDelay=300)
        self._setDefault(maxPollingRetries=1000)
        self._setDefault(outputCol="SimpleDetectMultivariateAnomaly_0bb9a87fe345_output")
        self._setDefault(pollingDelay=300)
        self._setDefault(suppressMaxRetriesException=False)
        self._setDefault(timestampCol="timestamp")
        self._setDefault(topContributorCount=10)
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
        backoffs=[100,500,1000],
        diagnosticsInfo=None,
        endTime=None,
        errorCol="SimpleDetectMultivariateAnomaly_0bb9a87fe345_error",
        handler=None,
        initialPollingDelay=300,
        inputCols=None,
        intermediateSaveDir=None,
        maxPollingRetries=1000,
        modelId=None,
        outputCol="SimpleDetectMultivariateAnomaly_0bb9a87fe345_output",
        pollingDelay=300,
        startTime=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        suppressMaxRetriesException=False,
        timestampCol="timestamp",
        topContributorCount=10,
        url=None
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
        return "com.microsoft.azure.synapse.ml.services.anomaly.SimpleDetectMultivariateAnomaly"

    @staticmethod
    def _from_java(java_stage):
        module_name=SimpleDetectMultivariateAnomaly.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SimpleDetectMultivariateAnomaly"
        return from_java(java_stage, module_name)

    def setBackoffs(self, value):
        """
        Args:
            backoffs: array of backoffs to use in the handler
        """
        self._set(backoffs=value)
        return self
    
    def setDiagnosticsInfo(self, value):
        """
        Args:
            diagnosticsInfo: diagnosticsInfo for training a multivariate anomaly detection model
        """
        self._set(diagnosticsInfo=value)
        return self
    
    def setEndTime(self, value):
        """
        Args:
            endTime: A required field, end time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        """
        self._set(endTime=value)
        return self
    
    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setHandler(self, value):
        """
        Args:
            handler: Which strategy to use when handling requests
        """
        self._set(handler=value)
        return self
    
    def setInitialPollingDelay(self, value):
        """
        Args:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        self._set(initialPollingDelay=value)
        return self
    
    def setInputCols(self, value):
        """
        Args:
            inputCols: The names of the input columns
        """
        self._set(inputCols=value)
        return self
    
    def setIntermediateSaveDir(self, value):
        """
        Args:
            intermediateSaveDir: Blob storage location in HDFS where intermediate data is saved while training.
        """
        self._set(intermediateSaveDir=value)
        return self
    
    def setMaxPollingRetries(self, value):
        """
        Args:
            maxPollingRetries: number of times to poll
        """
        self._set(maxPollingRetries=value)
        return self
    
    def setModelId(self, value):
        """
        Args:
            modelId: Format - uuid. Model identifier.
        """
        self._set(modelId=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setPollingDelay(self, value):
        """
        Args:
            pollingDelay: number of milliseconds to wait between polling
        """
        self._set(pollingDelay=value)
        return self
    
    def setStartTime(self, value):
        """
        Args:
            startTime: A required field, start time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        """
        self._set(startTime=value)
        return self
    
    def setSubscriptionKey(self, value):
        """
        Args:
            subscriptionKey: the API key to use
        """
        if isinstance(value, list):
            value = SparkContext._active_spark_context._jvm.com.microsoft.azure.synapse.ml.param.ServiceParam.toSeq(value)
        elif isinstance(value, dict):
            # Recursively convert Python dict/list to Java LinkedHashMap/ArrayList to preserve order
            sc = SparkContext._active_spark_context
            jvm = sc._jvm
            def _convert(val):
                if isinstance(val, dict):
                    jmap = jvm.java.util.LinkedHashMap()
                    for k, v in val.items():
                        jmap.put(k, _convert(v))
                    return jmap
                elif isinstance(val, list):
                    jlist = jvm.java.util.ArrayList()
                    for it in val:
                        jlist.add(_convert(it))
                    return jlist
                else:
                    return val
            value = jvm.com.microsoft.azure.synapse.ml.param.ServiceParam.toMap(_convert(value))
        self._java_obj = self._java_obj.setSubscriptionKey(value)
        return self
    
    def setSubscriptionKeyCol(self, value):
        """
        Args:
            subscriptionKey: the API key to use
        """
        self._java_obj = self._java_obj.setSubscriptionKeyCol(value)
        return self
    
    def setSuppressMaxRetriesException(self, value):
        """
        Args:
            suppressMaxRetriesException: set true to suppress the maxumimum retries exception and report in the error column
        """
        self._set(suppressMaxRetriesException=value)
        return self
    
    def setTimestampCol(self, value):
        """
        Args:
            timestampCol: Timestamp column name
        """
        self._set(timestampCol=value)
        return self
    
    def setTopContributorCount(self, value):
        """
        Args:
            topContributorCount: This is a number that you could specify N from 1 to 30, which will give you the details of top N contributed variables in the anomaly results. For example, if you have 100 variables in the model, but you only care the top five contributed variables in detection results, then you should fill this field with 5. The default number is 10.
        """
        self._set(topContributorCount=value)
        return self
    
    def setUrl(self, value):
        """
        Args:
            url: Url of the service
        """
        self._set(url=value)
        return self

    
    def getBackoffs(self):
        """
        Returns:
            backoffs: array of backoffs to use in the handler
        """
        return self.getOrDefault(self.backoffs)
    
    
    def getDiagnosticsInfo(self):
        """
        Returns:
            diagnosticsInfo: diagnosticsInfo for training a multivariate anomaly detection model
        """
        return self.getOrDefault(self.diagnosticsInfo)
    
    
    def getEndTime(self):
        """
        Returns:
            endTime: A required field, end time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        """
        return self.getOrDefault(self.endTime)
    
    
    def getErrorCol(self):
        """
        Returns:
            errorCol: column to hold http errors
        """
        return self.getOrDefault(self.errorCol)
    
    
    def getHandler(self):
        """
        Returns:
            handler: Which strategy to use when handling requests
        """
        return self.getOrDefault(self.handler)
    
    
    def getInitialPollingDelay(self):
        """
        Returns:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        return self.getOrDefault(self.initialPollingDelay)
    
    
    def getInputCols(self):
        """
        Returns:
            inputCols: The names of the input columns
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getIntermediateSaveDir(self):
        """
        Returns:
            intermediateSaveDir: Blob storage location in HDFS where intermediate data is saved while training.
        """
        return self.getOrDefault(self.intermediateSaveDir)
    
    
    def getMaxPollingRetries(self):
        """
        Returns:
            maxPollingRetries: number of times to poll
        """
        return self.getOrDefault(self.maxPollingRetries)
    
    
    def getModelId(self):
        """
        Returns:
            modelId: Format - uuid. Model identifier.
        """
        return self.getOrDefault(self.modelId)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getPollingDelay(self):
        """
        Returns:
            pollingDelay: number of milliseconds to wait between polling
        """
        return self.getOrDefault(self.pollingDelay)
    
    
    def getStartTime(self):
        """
        Returns:
            startTime: A required field, start time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        """
        return self.getOrDefault(self.startTime)
    
    
    def getSubscriptionKey(self):
        """
        Returns:
            subscriptionKey: the API key to use
        """
        return self._java_obj.getSubscriptionKey()
    
    
    def getSuppressMaxRetriesException(self):
        """
        Returns:
            suppressMaxRetriesException: set true to suppress the maxumimum retries exception and report in the error column
        """
        return self.getOrDefault(self.suppressMaxRetriesException)
    
    
    def getTimestampCol(self):
        """
        Returns:
            timestampCol: Timestamp column name
        """
        return self.getOrDefault(self.timestampCol)
    
    
    def getTopContributorCount(self):
        """
        Returns:
            topContributorCount: This is a number that you could specify N from 1 to 30, which will give you the details of top N contributed variables in the anomaly results. For example, if you have 100 variables in the model, but you only care the top five contributed variables in detection results, then you should fill this field with 5. The default number is 10.
        """
        return self.getOrDefault(self.topContributorCount)
    
    
    def getUrl(self):
        """
        Returns:
            url: Url of the service
        """
        return self.getOrDefault(self.url)

    

    
    def setLocation(self, value):
        self._java_obj = self._java_obj.setLocation(value)
        return self
    
    def cleanUpIntermediateData(self):
        self._java_obj.cleanUpIntermediateData()
        return
        