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
class AnalyzeTextLongRunningOperations(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        AADToken (object): AAD Token used for authentication
        CustomAuthHeader (object): A Custom Value for Authorization Header
        apiVersion (object): version of the api
        backoffs (list): array of backoffs to use in the handler
        batchSize (int): The max size of the buffer
        concurrency (int): max number of concurrent calls
        concurrentTimeout (float): max number seconds to wait on futures if concurrency >= 1
        customHeaders (object): Map of Custom Header Key-Value Tuples.
        customUrlRoot (str): The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        deploymentName (object): This field indicates the deployment name for the model. This is a required field.
        domain (object): The domain of the PII entity recognition request.
        errorCol (str): column to hold http errors
        excludeNormalizedValues (object): (Optional) request parameter that allows the user to provide settings for running the inference. If set to true, the service will exclude normalized
        exclusionList (object): (Optional) request parameter that filters out any entities that are included the excludeList. When a user specifies an excludeList, they cannot get a prediction returned with an entity in that list. We will apply inclusionList before exclusionList
        inclusionList (object): (Optional) request parameter that limits the output to the requested entity types included in this list. We will apply inclusionList before exclusionList
        initialPollingDelay (int): number of milliseconds to wait before first poll for result
        kind (str): Enumeration of supported Text Analysis tasks
        language (object): the language code of the text (optional for some services)
        loggingOptOut (object): loggingOptOut for task
        maxPollingRetries (int): number of times to poll
        modelVersion (object): Version of the model
        opinionMining (object): Whether to use opinion mining in the request or not.
        outputCol (str): The name of the output column
        overlapPolicy (object): (Optional) describes the type of overlap policy to apply to the ner output.
        piiCategories (object): describes the PII categories to return
        pollingDelay (int): number of milliseconds to wait between polling
        projectName (object): This field indicates the project name for the model. This is a required field
        sentenceCount (object): Specifies the number of sentences in the extracted summary.
        showStats (object): Whether to include detailed statistics in the response
        sortBy (object): Specifies how to sort the extracted summaries. This can be either 'Rank' or 'Offset'.
        stringIndexType (object): Specifies the method used to interpret string offsets. Defaults to Text Elements(Graphemes) according to Unicode v8.0.0.For more information see https://aka.ms/text-analytics-offsets
        subscriptionKey (object): the API key to use
        summaryLength (object): (NOTE: Recommended to use summaryLength over sentenceCount) Controls the approximate length of the output summaries.
        suppressMaxRetriesException (bool): set true to suppress the maxumimum retries exception and report in the error column
        telemHeaders (object): Map of Custom Header Key-Value Tuples.
        text (object): the text in the request body
        timeout (float): number of seconds to wait before closing the connection
        url (str): Url of the service
    """

    AADToken = Param(Params._dummy(), "AADToken", "ServiceParam: AAD Token used for authentication")
    
    CustomAuthHeader = Param(Params._dummy(), "CustomAuthHeader", "ServiceParam: A Custom Value for Authorization Header")
    
    apiVersion = Param(Params._dummy(), "apiVersion", "ServiceParam: version of the api")
    
    backoffs = Param(Params._dummy(), "backoffs", "array of backoffs to use in the handler", typeConverter=TypeConverters.toListInt)
    
    batchSize = Param(Params._dummy(), "batchSize", "The max size of the buffer", typeConverter=TypeConverters.toInt)
    
    concurrency = Param(Params._dummy(), "concurrency", "max number of concurrent calls", typeConverter=TypeConverters.toInt)
    
    concurrentTimeout = Param(Params._dummy(), "concurrentTimeout", "max number seconds to wait on futures if concurrency >= 1", typeConverter=TypeConverters.toFloat)
    
    customHeaders = Param(Params._dummy(), "customHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    customUrlRoot = Param(Params._dummy(), "customUrlRoot", "The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.", typeConverter=TypeConverters.toString)
    
    deploymentName = Param(Params._dummy(), "deploymentName", "ServiceParam: This field indicates the deployment name for the model. This is a required field.")
    
    domain = Param(Params._dummy(), "domain", "ServiceParam: The domain of the PII entity recognition request.")
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    excludeNormalizedValues = Param(Params._dummy(), "excludeNormalizedValues", "ServiceParam: (Optional) request parameter that allows the user to provide settings for running the inference. If set to true, the service will exclude normalized")
    
    exclusionList = Param(Params._dummy(), "exclusionList", "ServiceParam: (Optional) request parameter that filters out any entities that are included the excludeList. When a user specifies an excludeList, they cannot get a prediction returned with an entity in that list. We will apply inclusionList before exclusionList")
    
    inclusionList = Param(Params._dummy(), "inclusionList", "ServiceParam: (Optional) request parameter that limits the output to the requested entity types included in this list. We will apply inclusionList before exclusionList")
    
    initialPollingDelay = Param(Params._dummy(), "initialPollingDelay", "number of milliseconds to wait before first poll for result", typeConverter=TypeConverters.toInt)
    
    kind = Param(Params._dummy(), "kind", "Enumeration of supported Text Analysis tasks", typeConverter=TypeConverters.toString)
    
    language = Param(Params._dummy(), "language", "ServiceParam: the language code of the text (optional for some services)")
    
    loggingOptOut = Param(Params._dummy(), "loggingOptOut", "ServiceParam: loggingOptOut for task")
    
    maxPollingRetries = Param(Params._dummy(), "maxPollingRetries", "number of times to poll", typeConverter=TypeConverters.toInt)
    
    modelVersion = Param(Params._dummy(), "modelVersion", "ServiceParam: Version of the model")
    
    opinionMining = Param(Params._dummy(), "opinionMining", "ServiceParam: Whether to use opinion mining in the request or not.")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    overlapPolicy = Param(Params._dummy(), "overlapPolicy", "ServiceParam: (Optional) describes the type of overlap policy to apply to the ner output.")
    
    piiCategories = Param(Params._dummy(), "piiCategories", "ServiceParam: describes the PII categories to return")
    
    pollingDelay = Param(Params._dummy(), "pollingDelay", "number of milliseconds to wait between polling", typeConverter=TypeConverters.toInt)
    
    projectName = Param(Params._dummy(), "projectName", "ServiceParam: This field indicates the project name for the model. This is a required field")
    
    sentenceCount = Param(Params._dummy(), "sentenceCount", "ServiceParam: Specifies the number of sentences in the extracted summary.")
    
    showStats = Param(Params._dummy(), "showStats", "ServiceParam: Whether to include detailed statistics in the response")
    
    sortBy = Param(Params._dummy(), "sortBy", "ServiceParam: Specifies how to sort the extracted summaries. This can be either 'Rank' or 'Offset'.")
    
    stringIndexType = Param(Params._dummy(), "stringIndexType", "ServiceParam: Specifies the method used to interpret string offsets. Defaults to Text Elements(Graphemes) according to Unicode v8.0.0.For more information see https://aka.ms/text-analytics-offsets")
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    summaryLength = Param(Params._dummy(), "summaryLength", "ServiceParam: (NOTE: Recommended to use summaryLength over sentenceCount) Controls the approximate length of the output summaries.")
    
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
        apiVersion=None,
        apiVersionCol=None,
        backoffs=[100,500,1000],
        batchSize=10,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        deploymentName=None,
        deploymentNameCol=None,
        domain=None,
        domainCol=None,
        errorCol="AnalyzeTextLongRunningOperations_39ffd54e8f02_error",
        excludeNormalizedValues=None,
        excludeNormalizedValuesCol=None,
        exclusionList=None,
        exclusionListCol=None,
        inclusionList=None,
        inclusionListCol=None,
        initialPollingDelay=300,
        kind=None,
        language=None,
        languageCol=None,
        loggingOptOut=None,
        loggingOptOutCol=None,
        maxPollingRetries=1000,
        modelVersion=None,
        modelVersionCol=None,
        opinionMining=None,
        opinionMiningCol=None,
        outputCol="AnalyzeTextLongRunningOperations_39ffd54e8f02_output",
        overlapPolicy=None,
        overlapPolicyCol=None,
        piiCategories=None,
        piiCategoriesCol=None,
        pollingDelay=1000,
        projectName=None,
        projectNameCol=None,
        sentenceCount=None,
        sentenceCountCol=None,
        showStats=None,
        showStatsCol=None,
        sortBy=None,
        sortByCol=None,
        stringIndexType=None,
        stringIndexTypeCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        summaryLength=None,
        summaryLengthCol=None,
        suppressMaxRetriesException=False,
        telemHeaders=None,
        telemHeadersCol=None,
        text=None,
        textCol=None,
        timeout=60.0,
        url=None
        ):
        super(AnalyzeTextLongRunningOperations, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.language.AnalyzeTextLongRunningOperations", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(backoffs=[100,500,1000])
        self._setDefault(batchSize=10)
        self._setDefault(concurrency=1)
        self._setDefault(errorCol="AnalyzeTextLongRunningOperations_39ffd54e8f02_error")
        self._setDefault(initialPollingDelay=300)
        self._setDefault(maxPollingRetries=1000)
        self._setDefault(outputCol="AnalyzeTextLongRunningOperations_39ffd54e8f02_output")
        self._setDefault(pollingDelay=1000)
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
        apiVersion=None,
        apiVersionCol=None,
        backoffs=[100,500,1000],
        batchSize=10,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        deploymentName=None,
        deploymentNameCol=None,
        domain=None,
        domainCol=None,
        errorCol="AnalyzeTextLongRunningOperations_39ffd54e8f02_error",
        excludeNormalizedValues=None,
        excludeNormalizedValuesCol=None,
        exclusionList=None,
        exclusionListCol=None,
        inclusionList=None,
        inclusionListCol=None,
        initialPollingDelay=300,
        kind=None,
        language=None,
        languageCol=None,
        loggingOptOut=None,
        loggingOptOutCol=None,
        maxPollingRetries=1000,
        modelVersion=None,
        modelVersionCol=None,
        opinionMining=None,
        opinionMiningCol=None,
        outputCol="AnalyzeTextLongRunningOperations_39ffd54e8f02_output",
        overlapPolicy=None,
        overlapPolicyCol=None,
        piiCategories=None,
        piiCategoriesCol=None,
        pollingDelay=1000,
        projectName=None,
        projectNameCol=None,
        sentenceCount=None,
        sentenceCountCol=None,
        showStats=None,
        showStatsCol=None,
        sortBy=None,
        sortByCol=None,
        stringIndexType=None,
        stringIndexTypeCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        summaryLength=None,
        summaryLengthCol=None,
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
        return "com.microsoft.azure.synapse.ml.services.language.AnalyzeTextLongRunningOperations"

    @staticmethod
    def _from_java(java_stage):
        module_name=AnalyzeTextLongRunningOperations.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".AnalyzeTextLongRunningOperations"
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
    
    def setApiVersion(self, value):
        """
        Args:
            apiVersion: version of the api
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
        self._java_obj = self._java_obj.setApiVersion(value)
        return self
    
    def setApiVersionCol(self, value):
        """
        Args:
            apiVersion: version of the api
        """
        self._java_obj = self._java_obj.setApiVersionCol(value)
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
    
    def setDeploymentName(self, value):
        """
        Args:
            deploymentName: This field indicates the deployment name for the model. This is a required field.
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
        self._java_obj = self._java_obj.setDeploymentName(value)
        return self
    
    def setDeploymentNameCol(self, value):
        """
        Args:
            deploymentName: This field indicates the deployment name for the model. This is a required field.
        """
        self._java_obj = self._java_obj.setDeploymentNameCol(value)
        return self
    
    def setDomain(self, value):
        """
        Args:
            domain: The domain of the PII entity recognition request.
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
        self._java_obj = self._java_obj.setDomain(value)
        return self
    
    def setDomainCol(self, value):
        """
        Args:
            domain: The domain of the PII entity recognition request.
        """
        self._java_obj = self._java_obj.setDomainCol(value)
        return self
    
    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setExcludeNormalizedValues(self, value):
        """
        Args:
            excludeNormalizedValues: (Optional) request parameter that allows the user to provide settings for running the inference. If set to true, the service will exclude normalized
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
        self._java_obj = self._java_obj.setExcludeNormalizedValues(value)
        return self
    
    def setExcludeNormalizedValuesCol(self, value):
        """
        Args:
            excludeNormalizedValues: (Optional) request parameter that allows the user to provide settings for running the inference. If set to true, the service will exclude normalized
        """
        self._java_obj = self._java_obj.setExcludeNormalizedValuesCol(value)
        return self
    
    def setExclusionList(self, value):
        """
        Args:
            exclusionList: (Optional) request parameter that filters out any entities that are included the excludeList. When a user specifies an excludeList, they cannot get a prediction returned with an entity in that list. We will apply inclusionList before exclusionList
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
        self._java_obj = self._java_obj.setExclusionList(value)
        return self
    
    def setExclusionListCol(self, value):
        """
        Args:
            exclusionList: (Optional) request parameter that filters out any entities that are included the excludeList. When a user specifies an excludeList, they cannot get a prediction returned with an entity in that list. We will apply inclusionList before exclusionList
        """
        self._java_obj = self._java_obj.setExclusionListCol(value)
        return self
    
    def setInclusionList(self, value):
        """
        Args:
            inclusionList: (Optional) request parameter that limits the output to the requested entity types included in this list. We will apply inclusionList before exclusionList
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
        self._java_obj = self._java_obj.setInclusionList(value)
        return self
    
    def setInclusionListCol(self, value):
        """
        Args:
            inclusionList: (Optional) request parameter that limits the output to the requested entity types included in this list. We will apply inclusionList before exclusionList
        """
        self._java_obj = self._java_obj.setInclusionListCol(value)
        return self
    
    def setInitialPollingDelay(self, value):
        """
        Args:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        self._set(initialPollingDelay=value)
        return self
    
    def setKind(self, value):
        """
        Args:
            kind: Enumeration of supported Text Analysis tasks
        """
        self._set(kind=value)
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
    
    def setLoggingOptOut(self, value):
        """
        Args:
            loggingOptOut: loggingOptOut for task
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
        self._java_obj = self._java_obj.setLoggingOptOut(value)
        return self
    
    def setLoggingOptOutCol(self, value):
        """
        Args:
            loggingOptOut: loggingOptOut for task
        """
        self._java_obj = self._java_obj.setLoggingOptOutCol(value)
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
    
    def setOpinionMining(self, value):
        """
        Args:
            opinionMining: Whether to use opinion mining in the request or not.
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
        self._java_obj = self._java_obj.setOpinionMining(value)
        return self
    
    def setOpinionMiningCol(self, value):
        """
        Args:
            opinionMining: Whether to use opinion mining in the request or not.
        """
        self._java_obj = self._java_obj.setOpinionMiningCol(value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setOverlapPolicy(self, value):
        """
        Args:
            overlapPolicy: (Optional) describes the type of overlap policy to apply to the ner output.
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
        self._java_obj = self._java_obj.setOverlapPolicy(value)
        return self
    
    def setOverlapPolicyCol(self, value):
        """
        Args:
            overlapPolicy: (Optional) describes the type of overlap policy to apply to the ner output.
        """
        self._java_obj = self._java_obj.setOverlapPolicyCol(value)
        return self
    
    def setPiiCategories(self, value):
        """
        Args:
            piiCategories: describes the PII categories to return
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
        self._java_obj = self._java_obj.setPiiCategories(value)
        return self
    
    def setPiiCategoriesCol(self, value):
        """
        Args:
            piiCategories: describes the PII categories to return
        """
        self._java_obj = self._java_obj.setPiiCategoriesCol(value)
        return self
    
    def setPollingDelay(self, value):
        """
        Args:
            pollingDelay: number of milliseconds to wait between polling
        """
        self._set(pollingDelay=value)
        return self
    
    def setProjectName(self, value):
        """
        Args:
            projectName: This field indicates the project name for the model. This is a required field
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
        self._java_obj = self._java_obj.setProjectName(value)
        return self
    
    def setProjectNameCol(self, value):
        """
        Args:
            projectName: This field indicates the project name for the model. This is a required field
        """
        self._java_obj = self._java_obj.setProjectNameCol(value)
        return self
    
    def setSentenceCount(self, value):
        """
        Args:
            sentenceCount: Specifies the number of sentences in the extracted summary.
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
        self._java_obj = self._java_obj.setSentenceCount(value)
        return self
    
    def setSentenceCountCol(self, value):
        """
        Args:
            sentenceCount: Specifies the number of sentences in the extracted summary.
        """
        self._java_obj = self._java_obj.setSentenceCountCol(value)
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
    
    def setSortBy(self, value):
        """
        Args:
            sortBy: Specifies how to sort the extracted summaries. This can be either 'Rank' or 'Offset'.
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
        self._java_obj = self._java_obj.setSortBy(value)
        return self
    
    def setSortByCol(self, value):
        """
        Args:
            sortBy: Specifies how to sort the extracted summaries. This can be either 'Rank' or 'Offset'.
        """
        self._java_obj = self._java_obj.setSortByCol(value)
        return self
    
    def setStringIndexType(self, value):
        """
        Args:
            stringIndexType: Specifies the method used to interpret string offsets. Defaults to Text Elements(Graphemes) according to Unicode v8.0.0.For more information see https://aka.ms/text-analytics-offsets
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
        self._java_obj = self._java_obj.setStringIndexType(value)
        return self
    
    def setStringIndexTypeCol(self, value):
        """
        Args:
            stringIndexType: Specifies the method used to interpret string offsets. Defaults to Text Elements(Graphemes) according to Unicode v8.0.0.For more information see https://aka.ms/text-analytics-offsets
        """
        self._java_obj = self._java_obj.setStringIndexTypeCol(value)
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
    
    def setSummaryLength(self, value):
        """
        Args:
            summaryLength: (NOTE: Recommended to use summaryLength over sentenceCount) Controls the approximate length of the output summaries.
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
        self._java_obj = self._java_obj.setSummaryLength(value)
        return self
    
    def setSummaryLengthCol(self, value):
        """
        Args:
            summaryLength: (NOTE: Recommended to use summaryLength over sentenceCount) Controls the approximate length of the output summaries.
        """
        self._java_obj = self._java_obj.setSummaryLengthCol(value)
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
    
    
    def getApiVersion(self):
        """
        Returns:
            apiVersion: version of the api
        """
        return self._java_obj.getApiVersion()
    
    
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
    
    
    def getDeploymentName(self):
        """
        Returns:
            deploymentName: This field indicates the deployment name for the model. This is a required field.
        """
        return self._java_obj.getDeploymentName()
    
    
    def getDomain(self):
        """
        Returns:
            domain: The domain of the PII entity recognition request.
        """
        return self._java_obj.getDomain()
    
    
    def getErrorCol(self):
        """
        Returns:
            errorCol: column to hold http errors
        """
        return self.getOrDefault(self.errorCol)
    
    
    def getExcludeNormalizedValues(self):
        """
        Returns:
            excludeNormalizedValues: (Optional) request parameter that allows the user to provide settings for running the inference. If set to true, the service will exclude normalized
        """
        return self._java_obj.getExcludeNormalizedValues()
    
    
    def getExclusionList(self):
        """
        Returns:
            exclusionList: (Optional) request parameter that filters out any entities that are included the excludeList. When a user specifies an excludeList, they cannot get a prediction returned with an entity in that list. We will apply inclusionList before exclusionList
        """
        return self._java_obj.getExclusionList()
    
    
    def getInclusionList(self):
        """
        Returns:
            inclusionList: (Optional) request parameter that limits the output to the requested entity types included in this list. We will apply inclusionList before exclusionList
        """
        return self._java_obj.getInclusionList()
    
    
    def getInitialPollingDelay(self):
        """
        Returns:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        return self.getOrDefault(self.initialPollingDelay)
    
    
    def getKind(self):
        """
        Returns:
            kind: Enumeration of supported Text Analysis tasks
        """
        return self.getOrDefault(self.kind)
    
    
    def getLanguage(self):
        """
        Returns:
            language: the language code of the text (optional for some services)
        """
        return self._java_obj.getLanguage()
    
    
    def getLoggingOptOut(self):
        """
        Returns:
            loggingOptOut: loggingOptOut for task
        """
        return self._java_obj.getLoggingOptOut()
    
    
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
    
    
    def getOpinionMining(self):
        """
        Returns:
            opinionMining: Whether to use opinion mining in the request or not.
        """
        return self._java_obj.getOpinionMining()
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getOverlapPolicy(self):
        """
        Returns:
            overlapPolicy: (Optional) describes the type of overlap policy to apply to the ner output.
        """
        return self._java_obj.getOverlapPolicy()
    
    
    def getPiiCategories(self):
        """
        Returns:
            piiCategories: describes the PII categories to return
        """
        return self._java_obj.getPiiCategories()
    
    
    def getPollingDelay(self):
        """
        Returns:
            pollingDelay: number of milliseconds to wait between polling
        """
        return self.getOrDefault(self.pollingDelay)
    
    
    def getProjectName(self):
        """
        Returns:
            projectName: This field indicates the project name for the model. This is a required field
        """
        return self._java_obj.getProjectName()
    
    
    def getSentenceCount(self):
        """
        Returns:
            sentenceCount: Specifies the number of sentences in the extracted summary.
        """
        return self._java_obj.getSentenceCount()
    
    
    def getShowStats(self):
        """
        Returns:
            showStats: Whether to include detailed statistics in the response
        """
        return self._java_obj.getShowStats()
    
    
    def getSortBy(self):
        """
        Returns:
            sortBy: Specifies how to sort the extracted summaries. This can be either 'Rank' or 'Offset'.
        """
        return self._java_obj.getSortBy()
    
    
    def getStringIndexType(self):
        """
        Returns:
            stringIndexType: Specifies the method used to interpret string offsets. Defaults to Text Elements(Graphemes) according to Unicode v8.0.0.For more information see https://aka.ms/text-analytics-offsets
        """
        return self._java_obj.getStringIndexType()
    
    
    def getSubscriptionKey(self):
        """
        Returns:
            subscriptionKey: the API key to use
        """
        return self._java_obj.getSubscriptionKey()
    
    
    def getSummaryLength(self):
        """
        Returns:
            summaryLength: (NOTE: Recommended to use summaryLength over sentenceCount) Controls the approximate length of the output summaries.
        """
        return self._java_obj.getSummaryLength()
    
    
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
        