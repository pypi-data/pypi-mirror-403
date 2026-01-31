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
class TextAnalyze(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        AADToken (object): AAD Token used for authentication
        CustomAuthHeader (object): A Custom Value for Authorization Header
        backoffs (list): array of backoffs to use in the handler
        batchSize (int): The max size of the buffer
        concurrency (int): max number of concurrent calls
        concurrentTimeout (float): max number seconds to wait on futures if concurrency >= 1
        customHeaders (object): Map of Custom Header Key-Value Tuples.
        customUrlRoot (str): The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        disableServiceLogs (object): disableServiceLogs option
        entityLinkingParams (dict): the parameters to pass to the entityLinking model
        entityRecognitionParams (dict): the parameters to pass to the entity recognition model
        errorCol (str): column to hold http errors
        includeEntityLinking (bool): Whether to perform EntityLinking
        includeEntityRecognition (bool): Whether to perform entity recognition
        includeKeyPhraseExtraction (bool): Whether to perform EntityLinking
        includePii (bool): Whether to perform PII Detection
        includeSentimentAnalysis (bool): Whether to perform SentimentAnalysis
        initialPollingDelay (int): number of milliseconds to wait before first poll for result
        keyPhraseExtractionParams (dict): the parameters to pass to the keyPhraseExtraction model
        language (object): the language code of the text (optional for some services)
        maxPollingRetries (int): number of times to poll
        modelVersion (object): Version of the model
        outputCol (str): The name of the output column
        piiParams (dict): the parameters to pass to the PII model
        pollingDelay (int): number of milliseconds to wait between polling
        sentimentAnalysisParams (dict): the parameters to pass to the sentimentAnalysis model
        showStats (object): Whether to include detailed statistics in the response
        subscriptionKey (object): the API key to use
        suppressMaxRetriesException (bool): set true to suppress the maxumimum retries exception and report in the error column
        telemHeaders (object): Map of Custom Header Key-Value Tuples.
        text (object): the text in the request body
        timeout (float): number of seconds to wait before closing the connection
        url (str): Url of the service
    """

    AADToken = Param(Params._dummy(), "AADToken", "ServiceParam: AAD Token used for authentication")
    
    CustomAuthHeader = Param(Params._dummy(), "CustomAuthHeader", "ServiceParam: A Custom Value for Authorization Header")
    
    backoffs = Param(Params._dummy(), "backoffs", "array of backoffs to use in the handler", typeConverter=TypeConverters.toListInt)
    
    batchSize = Param(Params._dummy(), "batchSize", "The max size of the buffer", typeConverter=TypeConverters.toInt)
    
    concurrency = Param(Params._dummy(), "concurrency", "max number of concurrent calls", typeConverter=TypeConverters.toInt)
    
    concurrentTimeout = Param(Params._dummy(), "concurrentTimeout", "max number seconds to wait on futures if concurrency >= 1", typeConverter=TypeConverters.toFloat)
    
    customHeaders = Param(Params._dummy(), "customHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    customUrlRoot = Param(Params._dummy(), "customUrlRoot", "The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.", typeConverter=TypeConverters.toString)
    
    disableServiceLogs = Param(Params._dummy(), "disableServiceLogs", "ServiceParam: disableServiceLogs option")
    
    entityLinkingParams = Param(Params._dummy(), "entityLinkingParams", "the parameters to pass to the entityLinking model")
    
    entityRecognitionParams = Param(Params._dummy(), "entityRecognitionParams", "the parameters to pass to the entity recognition model")
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    includeEntityLinking = Param(Params._dummy(), "includeEntityLinking", "Whether to perform EntityLinking", typeConverter=TypeConverters.toBoolean)
    
    includeEntityRecognition = Param(Params._dummy(), "includeEntityRecognition", "Whether to perform entity recognition", typeConverter=TypeConverters.toBoolean)
    
    includeKeyPhraseExtraction = Param(Params._dummy(), "includeKeyPhraseExtraction", "Whether to perform EntityLinking", typeConverter=TypeConverters.toBoolean)
    
    includePii = Param(Params._dummy(), "includePii", "Whether to perform PII Detection", typeConverter=TypeConverters.toBoolean)
    
    includeSentimentAnalysis = Param(Params._dummy(), "includeSentimentAnalysis", "Whether to perform SentimentAnalysis", typeConverter=TypeConverters.toBoolean)
    
    initialPollingDelay = Param(Params._dummy(), "initialPollingDelay", "number of milliseconds to wait before first poll for result", typeConverter=TypeConverters.toInt)
    
    keyPhraseExtractionParams = Param(Params._dummy(), "keyPhraseExtractionParams", "the parameters to pass to the keyPhraseExtraction model")
    
    language = Param(Params._dummy(), "language", "ServiceParam: the language code of the text (optional for some services)")
    
    maxPollingRetries = Param(Params._dummy(), "maxPollingRetries", "number of times to poll", typeConverter=TypeConverters.toInt)
    
    modelVersion = Param(Params._dummy(), "modelVersion", "ServiceParam: Version of the model")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    piiParams = Param(Params._dummy(), "piiParams", "the parameters to pass to the PII model")
    
    pollingDelay = Param(Params._dummy(), "pollingDelay", "number of milliseconds to wait between polling", typeConverter=TypeConverters.toInt)
    
    sentimentAnalysisParams = Param(Params._dummy(), "sentimentAnalysisParams", "the parameters to pass to the sentimentAnalysis model")
    
    showStats = Param(Params._dummy(), "showStats", "ServiceParam: Whether to include detailed statistics in the response")
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    suppressMaxRetriesException = Param(Params._dummy(), "suppressMaxRetriesException", "set true to suppress the maxumimum retries exception and report in the error column", typeConverter=TypeConverters.toBoolean)
    
    telemHeaders = Param(Params._dummy(), "telemHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    text = Param(Params._dummy(), "text", "ServiceParam: the text in the request body")
    
    timeout = Param(Params._dummy(), "timeout", "number of seconds to wait before closing the connection", typeConverter=TypeConverters.toFloat)
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        AADToken=None,
        AADTokenCol=None,
        CustomAuthHeader=None,
        CustomAuthHeaderCol=None,
        backoffs=[100,500,1000],
        batchSize=10,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        disableServiceLogs=None,
        disableServiceLogsCol=None,
        entityLinkingParams={"model-version":"latest"},
        entityRecognitionParams={"model-version":"latest"},
        errorCol="TextAnalyze_de80a2de51d9_error",
        includeEntityLinking=True,
        includeEntityRecognition=True,
        includeKeyPhraseExtraction=True,
        includePii=True,
        includeSentimentAnalysis=True,
        initialPollingDelay=300,
        keyPhraseExtractionParams={"model-version":"latest"},
        language=None,
        languageCol=None,
        maxPollingRetries=1000,
        modelVersion=None,
        modelVersionCol=None,
        outputCol="TextAnalyze_de80a2de51d9_output",
        piiParams={"model-version":"latest"},
        pollingDelay=300,
        sentimentAnalysisParams={"model-version":"latest"},
        showStats=None,
        showStatsCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        suppressMaxRetriesException=False,
        telemHeaders=None,
        telemHeadersCol=None,
        text=None,
        textCol=None,
        timeout=60.0,
        url=None
        ):
        super(TextAnalyze, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.text.TextAnalyze", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(backoffs=[100,500,1000])
        self._setDefault(batchSize=10)
        self._setDefault(concurrency=1)
        self._setDefault(entityLinkingParams={"model-version":"latest"})
        self._setDefault(entityRecognitionParams={"model-version":"latest"})
        self._setDefault(errorCol="TextAnalyze_de80a2de51d9_error")
        self._setDefault(includeEntityLinking=True)
        self._setDefault(includeEntityRecognition=True)
        self._setDefault(includeKeyPhraseExtraction=True)
        self._setDefault(includePii=True)
        self._setDefault(includeSentimentAnalysis=True)
        self._setDefault(initialPollingDelay=300)
        self._setDefault(keyPhraseExtractionParams={"model-version":"latest"})
        self._setDefault(maxPollingRetries=1000)
        self._setDefault(outputCol="TextAnalyze_de80a2de51d9_output")
        self._setDefault(piiParams={"model-version":"latest"})
        self._setDefault(pollingDelay=300)
        self._setDefault(sentimentAnalysisParams={"model-version":"latest"})
        self._setDefault(suppressMaxRetriesException=False)
        self._setDefault(timeout=60.0)
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
        AADToken=None,
        AADTokenCol=None,
        CustomAuthHeader=None,
        CustomAuthHeaderCol=None,
        backoffs=[100,500,1000],
        batchSize=10,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        disableServiceLogs=None,
        disableServiceLogsCol=None,
        entityLinkingParams={"model-version":"latest"},
        entityRecognitionParams={"model-version":"latest"},
        errorCol="TextAnalyze_de80a2de51d9_error",
        includeEntityLinking=True,
        includeEntityRecognition=True,
        includeKeyPhraseExtraction=True,
        includePii=True,
        includeSentimentAnalysis=True,
        initialPollingDelay=300,
        keyPhraseExtractionParams={"model-version":"latest"},
        language=None,
        languageCol=None,
        maxPollingRetries=1000,
        modelVersion=None,
        modelVersionCol=None,
        outputCol="TextAnalyze_de80a2de51d9_output",
        piiParams={"model-version":"latest"},
        pollingDelay=300,
        sentimentAnalysisParams={"model-version":"latest"},
        showStats=None,
        showStatsCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        suppressMaxRetriesException=False,
        telemHeaders=None,
        telemHeadersCol=None,
        text=None,
        textCol=None,
        timeout=60.0,
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
        return "com.microsoft.azure.synapse.ml.services.text.TextAnalyze"

    @staticmethod
    def _from_java(java_stage):
        module_name=TextAnalyze.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".TextAnalyze"
        return from_java(java_stage, module_name)

    def setAADToken(self, value):
        """
        Args:
            AADToken: AAD Token used for authentication
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
        self._java_obj = self._java_obj.setAADToken(value)
        return self
    
    def setAADTokenCol(self, value):
        """
        Args:
            AADToken: AAD Token used for authentication
        """
        self._java_obj = self._java_obj.setAADTokenCol(value)
        return self
    
    def setCustomAuthHeader(self, value):
        """
        Args:
            CustomAuthHeader: A Custom Value for Authorization Header
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
        self._java_obj = self._java_obj.setCustomAuthHeader(value)
        return self
    
    def setCustomAuthHeaderCol(self, value):
        """
        Args:
            CustomAuthHeader: A Custom Value for Authorization Header
        """
        self._java_obj = self._java_obj.setCustomAuthHeaderCol(value)
        return self
    
    def setBackoffs(self, value):
        """
        Args:
            backoffs: array of backoffs to use in the handler
        """
        self._set(backoffs=value)
        return self
    
    def setBatchSize(self, value):
        """
        Args:
            batchSize: The max size of the buffer
        """
        self._set(batchSize=value)
        return self
    
    def setConcurrency(self, value):
        """
        Args:
            concurrency: max number of concurrent calls
        """
        self._set(concurrency=value)
        return self
    
    def setConcurrentTimeout(self, value):
        """
        Args:
            concurrentTimeout: max number seconds to wait on futures if concurrency >= 1
        """
        self._set(concurrentTimeout=value)
        return self
    
    def setCustomHeaders(self, value):
        """
        Args:
            customHeaders: Map of Custom Header Key-Value Tuples.
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
        self._java_obj = self._java_obj.setCustomHeaders(value)
        return self
    
    def setCustomHeadersCol(self, value):
        """
        Args:
            customHeaders: Map of Custom Header Key-Value Tuples.
        """
        self._java_obj = self._java_obj.setCustomHeadersCol(value)
        return self
    
    def setCustomUrlRoot(self, value):
        """
        Args:
            customUrlRoot: The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        """
        self._set(customUrlRoot=value)
        return self
    
    def setDisableServiceLogs(self, value):
        """
        Args:
            disableServiceLogs: disableServiceLogs option
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
        self._java_obj = self._java_obj.setDisableServiceLogs(value)
        return self
    
    def setDisableServiceLogsCol(self, value):
        """
        Args:
            disableServiceLogs: disableServiceLogs option
        """
        self._java_obj = self._java_obj.setDisableServiceLogsCol(value)
        return self
    
    def setEntityLinkingParams(self, value):
        """
        Args:
            entityLinkingParams: the parameters to pass to the entityLinking model
        """
        self._set(entityLinkingParams=value)
        return self
    
    def setEntityRecognitionParams(self, value):
        """
        Args:
            entityRecognitionParams: the parameters to pass to the entity recognition model
        """
        self._set(entityRecognitionParams=value)
        return self
    
    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setIncludeEntityLinking(self, value):
        """
        Args:
            includeEntityLinking: Whether to perform EntityLinking
        """
        self._set(includeEntityLinking=value)
        return self
    
    def setIncludeEntityRecognition(self, value):
        """
        Args:
            includeEntityRecognition: Whether to perform entity recognition
        """
        self._set(includeEntityRecognition=value)
        return self
    
    def setIncludeKeyPhraseExtraction(self, value):
        """
        Args:
            includeKeyPhraseExtraction: Whether to perform EntityLinking
        """
        self._set(includeKeyPhraseExtraction=value)
        return self
    
    def setIncludePii(self, value):
        """
        Args:
            includePii: Whether to perform PII Detection
        """
        self._set(includePii=value)
        return self
    
    def setIncludeSentimentAnalysis(self, value):
        """
        Args:
            includeSentimentAnalysis: Whether to perform SentimentAnalysis
        """
        self._set(includeSentimentAnalysis=value)
        return self
    
    def setInitialPollingDelay(self, value):
        """
        Args:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        self._set(initialPollingDelay=value)
        return self
    
    def setKeyPhraseExtractionParams(self, value):
        """
        Args:
            keyPhraseExtractionParams: the parameters to pass to the keyPhraseExtraction model
        """
        self._set(keyPhraseExtractionParams=value)
        return self
    
    def setLanguage(self, value):
        """
        Args:
            language: the language code of the text (optional for some services)
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
        self._java_obj = self._java_obj.setLanguage(value)
        return self
    
    def setLanguageCol(self, value):
        """
        Args:
            language: the language code of the text (optional for some services)
        """
        self._java_obj = self._java_obj.setLanguageCol(value)
        return self
    
    def setMaxPollingRetries(self, value):
        """
        Args:
            maxPollingRetries: number of times to poll
        """
        self._set(maxPollingRetries=value)
        return self
    
    def setModelVersion(self, value):
        """
        Args:
            modelVersion: Version of the model
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
        self._java_obj = self._java_obj.setModelVersion(value)
        return self
    
    def setModelVersionCol(self, value):
        """
        Args:
            modelVersion: Version of the model
        """
        self._java_obj = self._java_obj.setModelVersionCol(value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setPiiParams(self, value):
        """
        Args:
            piiParams: the parameters to pass to the PII model
        """
        self._set(piiParams=value)
        return self
    
    def setPollingDelay(self, value):
        """
        Args:
            pollingDelay: number of milliseconds to wait between polling
        """
        self._set(pollingDelay=value)
        return self
    
    def setSentimentAnalysisParams(self, value):
        """
        Args:
            sentimentAnalysisParams: the parameters to pass to the sentimentAnalysis model
        """
        self._set(sentimentAnalysisParams=value)
        return self
    
    def setShowStats(self, value):
        """
        Args:
            showStats: Whether to include detailed statistics in the response
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
        self._java_obj = self._java_obj.setShowStats(value)
        return self
    
    def setShowStatsCol(self, value):
        """
        Args:
            showStats: Whether to include detailed statistics in the response
        """
        self._java_obj = self._java_obj.setShowStatsCol(value)
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
    
    def setTelemHeaders(self, value):
        """
        Args:
            telemHeaders: Map of Custom Header Key-Value Tuples.
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
        self._java_obj = self._java_obj.setTelemHeaders(value)
        return self
    
    def setTelemHeadersCol(self, value):
        """
        Args:
            telemHeaders: Map of Custom Header Key-Value Tuples.
        """
        self._java_obj = self._java_obj.setTelemHeadersCol(value)
        return self
    
    def setText(self, value):
        """
        Args:
            text: the text in the request body
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
        self._java_obj = self._java_obj.setText(value)
        return self
    
    def setTextCol(self, value):
        """
        Args:
            text: the text in the request body
        """
        self._java_obj = self._java_obj.setTextCol(value)
        return self
    
    def setTimeout(self, value):
        """
        Args:
            timeout: number of seconds to wait before closing the connection
        """
        self._set(timeout=value)
        return self
    
    def setUrl(self, value):
        """
        Args:
            url: Url of the service
        """
        self._set(url=value)
        return self

    
    def getAADToken(self):
        """
        Returns:
            AADToken: AAD Token used for authentication
        """
        return self._java_obj.getAADToken()
    
    
    def getCustomAuthHeader(self):
        """
        Returns:
            CustomAuthHeader: A Custom Value for Authorization Header
        """
        return self._java_obj.getCustomAuthHeader()
    
    
    def getBackoffs(self):
        """
        Returns:
            backoffs: array of backoffs to use in the handler
        """
        return self.getOrDefault(self.backoffs)
    
    
    def getBatchSize(self):
        """
        Returns:
            batchSize: The max size of the buffer
        """
        return self.getOrDefault(self.batchSize)
    
    
    def getConcurrency(self):
        """
        Returns:
            concurrency: max number of concurrent calls
        """
        return self.getOrDefault(self.concurrency)
    
    
    def getConcurrentTimeout(self):
        """
        Returns:
            concurrentTimeout: max number seconds to wait on futures if concurrency >= 1
        """
        return self.getOrDefault(self.concurrentTimeout)
    
    
    def getCustomHeaders(self):
        """
        Returns:
            customHeaders: Map of Custom Header Key-Value Tuples.
        """
        return self._java_obj.getCustomHeaders()
    
    
    def getCustomUrlRoot(self):
        """
        Returns:
            customUrlRoot: The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        """
        return self.getOrDefault(self.customUrlRoot)
    
    
    def getDisableServiceLogs(self):
        """
        Returns:
            disableServiceLogs: disableServiceLogs option
        """
        return self._java_obj.getDisableServiceLogs()
    
    
    def getEntityLinkingParams(self):
        """
        Returns:
            entityLinkingParams: the parameters to pass to the entityLinking model
        """
        return self.getOrDefault(self.entityLinkingParams)
    
    
    def getEntityRecognitionParams(self):
        """
        Returns:
            entityRecognitionParams: the parameters to pass to the entity recognition model
        """
        return self.getOrDefault(self.entityRecognitionParams)
    
    
    def getErrorCol(self):
        """
        Returns:
            errorCol: column to hold http errors
        """
        return self.getOrDefault(self.errorCol)
    
    
    def getIncludeEntityLinking(self):
        """
        Returns:
            includeEntityLinking: Whether to perform EntityLinking
        """
        return self.getOrDefault(self.includeEntityLinking)
    
    
    def getIncludeEntityRecognition(self):
        """
        Returns:
            includeEntityRecognition: Whether to perform entity recognition
        """
        return self.getOrDefault(self.includeEntityRecognition)
    
    
    def getIncludeKeyPhraseExtraction(self):
        """
        Returns:
            includeKeyPhraseExtraction: Whether to perform EntityLinking
        """
        return self.getOrDefault(self.includeKeyPhraseExtraction)
    
    
    def getIncludePii(self):
        """
        Returns:
            includePii: Whether to perform PII Detection
        """
        return self.getOrDefault(self.includePii)
    
    
    def getIncludeSentimentAnalysis(self):
        """
        Returns:
            includeSentimentAnalysis: Whether to perform SentimentAnalysis
        """
        return self.getOrDefault(self.includeSentimentAnalysis)
    
    
    def getInitialPollingDelay(self):
        """
        Returns:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        return self.getOrDefault(self.initialPollingDelay)
    
    
    def getKeyPhraseExtractionParams(self):
        """
        Returns:
            keyPhraseExtractionParams: the parameters to pass to the keyPhraseExtraction model
        """
        return self.getOrDefault(self.keyPhraseExtractionParams)
    
    
    def getLanguage(self):
        """
        Returns:
            language: the language code of the text (optional for some services)
        """
        return self._java_obj.getLanguage()
    
    
    def getMaxPollingRetries(self):
        """
        Returns:
            maxPollingRetries: number of times to poll
        """
        return self.getOrDefault(self.maxPollingRetries)
    
    
    def getModelVersion(self):
        """
        Returns:
            modelVersion: Version of the model
        """
        return self._java_obj.getModelVersion()
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getPiiParams(self):
        """
        Returns:
            piiParams: the parameters to pass to the PII model
        """
        return self.getOrDefault(self.piiParams)
    
    
    def getPollingDelay(self):
        """
        Returns:
            pollingDelay: number of milliseconds to wait between polling
        """
        return self.getOrDefault(self.pollingDelay)
    
    
    def getSentimentAnalysisParams(self):
        """
        Returns:
            sentimentAnalysisParams: the parameters to pass to the sentimentAnalysis model
        """
        return self.getOrDefault(self.sentimentAnalysisParams)
    
    
    def getShowStats(self):
        """
        Returns:
            showStats: Whether to include detailed statistics in the response
        """
        return self._java_obj.getShowStats()
    
    
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
    
    
    def getTelemHeaders(self):
        """
        Returns:
            telemHeaders: Map of Custom Header Key-Value Tuples.
        """
        return self._java_obj.getTelemHeaders()
    
    
    def getText(self):
        """
        Returns:
            text: the text in the request body
        """
        return self._java_obj.getText()
    
    
    def getTimeout(self):
        """
        Returns:
            timeout: number of seconds to wait before closing the connection
        """
        return self.getOrDefault(self.timeout)
    
    
    def getUrl(self):
        """
        Returns:
            url: Url of the service
        """
        return self.getOrDefault(self.url)

    

    def setCustomServiceName(self, value):
        self._java_obj = self._java_obj.setCustomServiceName(value)
        return self
    
    def setEndpoint(self, value):
        self._java_obj = self._java_obj.setEndpoint(value)
        return self
    
    def setDefaultInternalEndpoint(self, value):
        self._java_obj = self._java_obj.setDefaultInternalEndpoint(value)
        return self
    
    def _transform(self, dataset: DataFrame) -> DataFrame:
        return super()._transform(dataset)
    
    def setLocation(self, value):
        self._java_obj = self._java_obj.setLocation(value)
        return self
    
    def setLinkedService(self, value):
        self._java_obj = self._java_obj.setLinkedService(value)
        return self
        