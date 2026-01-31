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
class Translate(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        AADToken (object): AAD Token used for authentication
        CustomAuthHeader (object): A Custom Value for Authorization Header
        allowFallback (object): Specifies that the service is allowed to fall back to a general system when a custom system does not exist. 
        category (object): A string specifying the category (domain) of the translation. This parameter is used to get translations from a customized system built with Custom Translator. Add the Category ID from your Custom Translator project details to this parameter to use your deployed customized system. Default value is: general.
        concurrency (int): max number of concurrent calls
        concurrentTimeout (float): max number seconds to wait on futures if concurrency >= 1
        customHeaders (object): Map of Custom Header Key-Value Tuples.
        customUrlRoot (str): The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        errorCol (str): column to hold http errors
        fromLanguage (object): Specifies the language of the input text. Find which languages are available to translate from by looking up supported languages using the translation scope. If the from parameter is not specified, automatic language detection is applied to determine the source language. You must use the from parameter rather than autodetection when using the dynamic dictionary feature.
        fromScript (object): Specifies the script of the input text.
        handler (object): Which strategy to use when handling requests
        includeAlignment (object): Specifies whether to include alignment projection from source text to translated text.
        includeSentenceLength (object): Specifies whether to include sentence boundaries for the input text and the translated text. 
        outputCol (str): The name of the output column
        profanityAction (object): Specifies how profanities should be treated in translations. Possible values are: NoAction (default), Marked or Deleted. 
        profanityMarker (object): Specifies how profanities should be marked in translations. Possible values are: Asterisk (default) or Tag.
        subscriptionKey (object): the API key to use
        subscriptionRegion (object): the API region to use
        suggestedFrom (object): Specifies a fallback language if the language of the input text can't be identified. Language autodetection is applied when the from parameter is omitted. If detection fails, the suggestedFrom language will be assumed.
        telemHeaders (object): Map of Custom Header Key-Value Tuples.
        text (object): the string to translate
        textType (object): Defines whether the text being translated is plain text or HTML text. Any HTML needs to be a well-formed, complete element. Possible values are: plain (default) or html.
        timeout (float): number of seconds to wait before closing the connection
        toLanguage (object): Specifies the language of the output text. The target language must be one of the supported languages included in the translation scope. For example, use to=de to translate to German. It's possible to translate to multiple languages simultaneously by repeating the parameter in the query string. For example, use to=de and to=it to translate to German and Italian.
        toScript (object): Specifies the script of the translated text.
        url (str): Url of the service
    """

    AADToken = Param(Params._dummy(), "AADToken", "ServiceParam: AAD Token used for authentication")
    
    CustomAuthHeader = Param(Params._dummy(), "CustomAuthHeader", "ServiceParam: A Custom Value for Authorization Header")
    
    allowFallback = Param(Params._dummy(), "allowFallback", "ServiceParam: Specifies that the service is allowed to fall back to a general system when a custom system does not exist. ")
    
    category = Param(Params._dummy(), "category", "ServiceParam: A string specifying the category (domain) of the translation. This parameter is used to get translations from a customized system built with Custom Translator. Add the Category ID from your Custom Translator project details to this parameter to use your deployed customized system. Default value is: general.")
    
    concurrency = Param(Params._dummy(), "concurrency", "max number of concurrent calls", typeConverter=TypeConverters.toInt)
    
    concurrentTimeout = Param(Params._dummy(), "concurrentTimeout", "max number seconds to wait on futures if concurrency >= 1", typeConverter=TypeConverters.toFloat)
    
    customHeaders = Param(Params._dummy(), "customHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    customUrlRoot = Param(Params._dummy(), "customUrlRoot", "The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.", typeConverter=TypeConverters.toString)
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    fromLanguage = Param(Params._dummy(), "fromLanguage", "ServiceParam: Specifies the language of the input text. Find which languages are available to translate from by looking up supported languages using the translation scope. If the from parameter is not specified, automatic language detection is applied to determine the source language. You must use the from parameter rather than autodetection when using the dynamic dictionary feature.")
    
    fromScript = Param(Params._dummy(), "fromScript", "ServiceParam: Specifies the script of the input text.")
    
    handler = Param(Params._dummy(), "handler", "Which strategy to use when handling requests")
    
    includeAlignment = Param(Params._dummy(), "includeAlignment", "ServiceParam: Specifies whether to include alignment projection from source text to translated text.")
    
    includeSentenceLength = Param(Params._dummy(), "includeSentenceLength", "ServiceParam: Specifies whether to include sentence boundaries for the input text and the translated text. ")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    profanityAction = Param(Params._dummy(), "profanityAction", "ServiceParam: Specifies how profanities should be treated in translations. Possible values are: NoAction (default), Marked or Deleted. ")
    
    profanityMarker = Param(Params._dummy(), "profanityMarker", "ServiceParam: Specifies how profanities should be marked in translations. Possible values are: Asterisk (default) or Tag.")
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    subscriptionRegion = Param(Params._dummy(), "subscriptionRegion", "ServiceParam: the API region to use")
    
    suggestedFrom = Param(Params._dummy(), "suggestedFrom", "ServiceParam: Specifies a fallback language if the language of the input text can't be identified. Language autodetection is applied when the from parameter is omitted. If detection fails, the suggestedFrom language will be assumed.")
    
    telemHeaders = Param(Params._dummy(), "telemHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    text = Param(Params._dummy(), "text", "ServiceParam: the string to translate")
    
    textType = Param(Params._dummy(), "textType", "ServiceParam: Defines whether the text being translated is plain text or HTML text. Any HTML needs to be a well-formed, complete element. Possible values are: plain (default) or html.")
    
    timeout = Param(Params._dummy(), "timeout", "number of seconds to wait before closing the connection", typeConverter=TypeConverters.toFloat)
    
    toLanguage = Param(Params._dummy(), "toLanguage", "ServiceParam: Specifies the language of the output text. The target language must be one of the supported languages included in the translation scope. For example, use to=de to translate to German. It's possible to translate to multiple languages simultaneously by repeating the parameter in the query string. For example, use to=de and to=it to translate to German and Italian.")
    
    toScript = Param(Params._dummy(), "toScript", "ServiceParam: Specifies the script of the translated text.")
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        AADToken=None,
        AADTokenCol=None,
        CustomAuthHeader=None,
        CustomAuthHeaderCol=None,
        allowFallback=None,
        allowFallbackCol=None,
        category=None,
        categoryCol=None,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        errorCol="Translate_8d7b894a0960_error",
        fromLanguage=None,
        fromLanguageCol=None,
        fromScript=None,
        fromScriptCol=None,
        handler=None,
        includeAlignment=None,
        includeAlignmentCol=None,
        includeSentenceLength=None,
        includeSentenceLengthCol=None,
        outputCol="Translate_8d7b894a0960_output",
        profanityAction=None,
        profanityActionCol=None,
        profanityMarker=None,
        profanityMarkerCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        subscriptionRegion=None,
        subscriptionRegionCol=None,
        suggestedFrom=None,
        suggestedFromCol=None,
        telemHeaders=None,
        telemHeadersCol=None,
        text=None,
        textCol=None,
        textType=None,
        textTypeCol=None,
        timeout=60.0,
        toLanguage=None,
        toLanguageCol=None,
        toScript=None,
        toScriptCol=None,
        url=None
        ):
        super(Translate, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.translate.Translate", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(concurrency=1)
        self._setDefault(errorCol="Translate_8d7b894a0960_error")
        self._setDefault(outputCol="Translate_8d7b894a0960_output")
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
        allowFallback=None,
        allowFallbackCol=None,
        category=None,
        categoryCol=None,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        errorCol="Translate_8d7b894a0960_error",
        fromLanguage=None,
        fromLanguageCol=None,
        fromScript=None,
        fromScriptCol=None,
        handler=None,
        includeAlignment=None,
        includeAlignmentCol=None,
        includeSentenceLength=None,
        includeSentenceLengthCol=None,
        outputCol="Translate_8d7b894a0960_output",
        profanityAction=None,
        profanityActionCol=None,
        profanityMarker=None,
        profanityMarkerCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        subscriptionRegion=None,
        subscriptionRegionCol=None,
        suggestedFrom=None,
        suggestedFromCol=None,
        telemHeaders=None,
        telemHeadersCol=None,
        text=None,
        textCol=None,
        textType=None,
        textTypeCol=None,
        timeout=60.0,
        toLanguage=None,
        toLanguageCol=None,
        toScript=None,
        toScriptCol=None,
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
        return "com.microsoft.azure.synapse.ml.services.translate.Translate"

    @staticmethod
    def _from_java(java_stage):
        module_name=Translate.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".Translate"
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
    
    def setAllowFallback(self, value):
        """
        Args:
            allowFallback: Specifies that the service is allowed to fall back to a general system when a custom system does not exist. 
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
        self._java_obj = self._java_obj.setAllowFallback(value)
        return self
    
    def setAllowFallbackCol(self, value):
        """
        Args:
            allowFallback: Specifies that the service is allowed to fall back to a general system when a custom system does not exist. 
        """
        self._java_obj = self._java_obj.setAllowFallbackCol(value)
        return self
    
    def setCategory(self, value):
        """
        Args:
            category: A string specifying the category (domain) of the translation. This parameter is used to get translations from a customized system built with Custom Translator. Add the Category ID from your Custom Translator project details to this parameter to use your deployed customized system. Default value is: general.
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
        self._java_obj = self._java_obj.setCategory(value)
        return self
    
    def setCategoryCol(self, value):
        """
        Args:
            category: A string specifying the category (domain) of the translation. This parameter is used to get translations from a customized system built with Custom Translator. Add the Category ID from your Custom Translator project details to this parameter to use your deployed customized system. Default value is: general.
        """
        self._java_obj = self._java_obj.setCategoryCol(value)
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
    
    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setFromLanguage(self, value):
        """
        Args:
            fromLanguage: Specifies the language of the input text. Find which languages are available to translate from by looking up supported languages using the translation scope. If the from parameter is not specified, automatic language detection is applied to determine the source language. You must use the from parameter rather than autodetection when using the dynamic dictionary feature.
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
        self._java_obj = self._java_obj.setFromLanguage(value)
        return self
    
    def setFromLanguageCol(self, value):
        """
        Args:
            fromLanguage: Specifies the language of the input text. Find which languages are available to translate from by looking up supported languages using the translation scope. If the from parameter is not specified, automatic language detection is applied to determine the source language. You must use the from parameter rather than autodetection when using the dynamic dictionary feature.
        """
        self._java_obj = self._java_obj.setFromLanguageCol(value)
        return self
    
    def setFromScript(self, value):
        """
        Args:
            fromScript: Specifies the script of the input text.
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
        self._java_obj = self._java_obj.setFromScript(value)
        return self
    
    def setFromScriptCol(self, value):
        """
        Args:
            fromScript: Specifies the script of the input text.
        """
        self._java_obj = self._java_obj.setFromScriptCol(value)
        return self
    
    def setHandler(self, value):
        """
        Args:
            handler: Which strategy to use when handling requests
        """
        self._set(handler=value)
        return self
    
    def setIncludeAlignment(self, value):
        """
        Args:
            includeAlignment: Specifies whether to include alignment projection from source text to translated text.
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
        self._java_obj = self._java_obj.setIncludeAlignment(value)
        return self
    
    def setIncludeAlignmentCol(self, value):
        """
        Args:
            includeAlignment: Specifies whether to include alignment projection from source text to translated text.
        """
        self._java_obj = self._java_obj.setIncludeAlignmentCol(value)
        return self
    
    def setIncludeSentenceLength(self, value):
        """
        Args:
            includeSentenceLength: Specifies whether to include sentence boundaries for the input text and the translated text. 
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
        self._java_obj = self._java_obj.setIncludeSentenceLength(value)
        return self
    
    def setIncludeSentenceLengthCol(self, value):
        """
        Args:
            includeSentenceLength: Specifies whether to include sentence boundaries for the input text and the translated text. 
        """
        self._java_obj = self._java_obj.setIncludeSentenceLengthCol(value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setProfanityAction(self, value):
        """
        Args:
            profanityAction: Specifies how profanities should be treated in translations. Possible values are: NoAction (default), Marked or Deleted. 
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
        self._java_obj = self._java_obj.setProfanityAction(value)
        return self
    
    def setProfanityActionCol(self, value):
        """
        Args:
            profanityAction: Specifies how profanities should be treated in translations. Possible values are: NoAction (default), Marked or Deleted. 
        """
        self._java_obj = self._java_obj.setProfanityActionCol(value)
        return self
    
    def setProfanityMarker(self, value):
        """
        Args:
            profanityMarker: Specifies how profanities should be marked in translations. Possible values are: Asterisk (default) or Tag.
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
        self._java_obj = self._java_obj.setProfanityMarker(value)
        return self
    
    def setProfanityMarkerCol(self, value):
        """
        Args:
            profanityMarker: Specifies how profanities should be marked in translations. Possible values are: Asterisk (default) or Tag.
        """
        self._java_obj = self._java_obj.setProfanityMarkerCol(value)
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
    
    def setSubscriptionRegion(self, value):
        """
        Args:
            subscriptionRegion: the API region to use
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
        self._java_obj = self._java_obj.setSubscriptionRegion(value)
        return self
    
    def setSubscriptionRegionCol(self, value):
        """
        Args:
            subscriptionRegion: the API region to use
        """
        self._java_obj = self._java_obj.setSubscriptionRegionCol(value)
        return self
    
    def setSuggestedFrom(self, value):
        """
        Args:
            suggestedFrom: Specifies a fallback language if the language of the input text can't be identified. Language autodetection is applied when the from parameter is omitted. If detection fails, the suggestedFrom language will be assumed.
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
        self._java_obj = self._java_obj.setSuggestedFrom(value)
        return self
    
    def setSuggestedFromCol(self, value):
        """
        Args:
            suggestedFrom: Specifies a fallback language if the language of the input text can't be identified. Language autodetection is applied when the from parameter is omitted. If detection fails, the suggestedFrom language will be assumed.
        """
        self._java_obj = self._java_obj.setSuggestedFromCol(value)
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
            text: the string to translate
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
            text: the string to translate
        """
        self._java_obj = self._java_obj.setTextCol(value)
        return self
    
    def setTextType(self, value):
        """
        Args:
            textType: Defines whether the text being translated is plain text or HTML text. Any HTML needs to be a well-formed, complete element. Possible values are: plain (default) or html.
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
        self._java_obj = self._java_obj.setTextType(value)
        return self
    
    def setTextTypeCol(self, value):
        """
        Args:
            textType: Defines whether the text being translated is plain text or HTML text. Any HTML needs to be a well-formed, complete element. Possible values are: plain (default) or html.
        """
        self._java_obj = self._java_obj.setTextTypeCol(value)
        return self
    
    def setTimeout(self, value):
        """
        Args:
            timeout: number of seconds to wait before closing the connection
        """
        self._set(timeout=value)
        return self
    
    def setToLanguage(self, value):
        """
        Args:
            toLanguage: Specifies the language of the output text. The target language must be one of the supported languages included in the translation scope. For example, use to=de to translate to German. It's possible to translate to multiple languages simultaneously by repeating the parameter in the query string. For example, use to=de and to=it to translate to German and Italian.
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
        self._java_obj = self._java_obj.setToLanguage(value)
        return self
    
    def setToLanguageCol(self, value):
        """
        Args:
            toLanguage: Specifies the language of the output text. The target language must be one of the supported languages included in the translation scope. For example, use to=de to translate to German. It's possible to translate to multiple languages simultaneously by repeating the parameter in the query string. For example, use to=de and to=it to translate to German and Italian.
        """
        self._java_obj = self._java_obj.setToLanguageCol(value)
        return self
    
    def setToScript(self, value):
        """
        Args:
            toScript: Specifies the script of the translated text.
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
        self._java_obj = self._java_obj.setToScript(value)
        return self
    
    def setToScriptCol(self, value):
        """
        Args:
            toScript: Specifies the script of the translated text.
        """
        self._java_obj = self._java_obj.setToScriptCol(value)
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
    
    
    def getAllowFallback(self):
        """
        Returns:
            allowFallback: Specifies that the service is allowed to fall back to a general system when a custom system does not exist. 
        """
        return self._java_obj.getAllowFallback()
    
    
    def getCategory(self):
        """
        Returns:
            category: A string specifying the category (domain) of the translation. This parameter is used to get translations from a customized system built with Custom Translator. Add the Category ID from your Custom Translator project details to this parameter to use your deployed customized system. Default value is: general.
        """
        return self._java_obj.getCategory()
    
    
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
    
    
    def getErrorCol(self):
        """
        Returns:
            errorCol: column to hold http errors
        """
        return self.getOrDefault(self.errorCol)
    
    
    def getFromLanguage(self):
        """
        Returns:
            fromLanguage: Specifies the language of the input text. Find which languages are available to translate from by looking up supported languages using the translation scope. If the from parameter is not specified, automatic language detection is applied to determine the source language. You must use the from parameter rather than autodetection when using the dynamic dictionary feature.
        """
        return self._java_obj.getFromLanguage()
    
    
    def getFromScript(self):
        """
        Returns:
            fromScript: Specifies the script of the input text.
        """
        return self._java_obj.getFromScript()
    
    
    def getHandler(self):
        """
        Returns:
            handler: Which strategy to use when handling requests
        """
        return self.getOrDefault(self.handler)
    
    
    def getIncludeAlignment(self):
        """
        Returns:
            includeAlignment: Specifies whether to include alignment projection from source text to translated text.
        """
        return self._java_obj.getIncludeAlignment()
    
    
    def getIncludeSentenceLength(self):
        """
        Returns:
            includeSentenceLength: Specifies whether to include sentence boundaries for the input text and the translated text. 
        """
        return self._java_obj.getIncludeSentenceLength()
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getProfanityAction(self):
        """
        Returns:
            profanityAction: Specifies how profanities should be treated in translations. Possible values are: NoAction (default), Marked or Deleted. 
        """
        return self._java_obj.getProfanityAction()
    
    
    def getProfanityMarker(self):
        """
        Returns:
            profanityMarker: Specifies how profanities should be marked in translations. Possible values are: Asterisk (default) or Tag.
        """
        return self._java_obj.getProfanityMarker()
    
    
    def getSubscriptionKey(self):
        """
        Returns:
            subscriptionKey: the API key to use
        """
        return self._java_obj.getSubscriptionKey()
    
    
    def getSubscriptionRegion(self):
        """
        Returns:
            subscriptionRegion: the API region to use
        """
        return self._java_obj.getSubscriptionRegion()
    
    
    def getSuggestedFrom(self):
        """
        Returns:
            suggestedFrom: Specifies a fallback language if the language of the input text can't be identified. Language autodetection is applied when the from parameter is omitted. If detection fails, the suggestedFrom language will be assumed.
        """
        return self._java_obj.getSuggestedFrom()
    
    
    def getTelemHeaders(self):
        """
        Returns:
            telemHeaders: Map of Custom Header Key-Value Tuples.
        """
        return self._java_obj.getTelemHeaders()
    
    
    def getText(self):
        """
        Returns:
            text: the string to translate
        """
        return self._java_obj.getText()
    
    
    def getTextType(self):
        """
        Returns:
            textType: Defines whether the text being translated is plain text or HTML text. Any HTML needs to be a well-formed, complete element. Possible values are: plain (default) or html.
        """
        return self._java_obj.getTextType()
    
    
    def getTimeout(self):
        """
        Returns:
            timeout: number of seconds to wait before closing the connection
        """
        return self.getOrDefault(self.timeout)
    
    
    def getToLanguage(self):
        """
        Returns:
            toLanguage: Specifies the language of the output text. The target language must be one of the supported languages included in the translation scope. For example, use to=de to translate to German. It's possible to translate to multiple languages simultaneously by repeating the parameter in the query string. For example, use to=de and to=it to translate to German and Italian.
        """
        return self._java_obj.getToLanguage()
    
    
    def getToScript(self):
        """
        Returns:
            toScript: Specifies the script of the translated text.
        """
        return self._java_obj.getToScript()
    
    
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
        