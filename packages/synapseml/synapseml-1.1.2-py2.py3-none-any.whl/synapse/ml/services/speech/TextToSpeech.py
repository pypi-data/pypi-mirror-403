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
class TextToSpeech(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        errorCol (str): column to hold http errors
        language (object): The name of the language used for synthesis
        locale (object): The locale of the input text
        outputFileCol (str): The location of the saved file as an HDFS compliant URI
        outputFormat (object): The format for the output audio can be one of ArraySeq(Raw8Khz8BitMonoMULaw, Riff16Khz16KbpsMonoSiren, Audio16Khz16KbpsMonoSiren, Audio16Khz32KBitRateMonoMp3, Audio16Khz128KBitRateMonoMp3, Audio16Khz64KBitRateMonoMp3, Audio24Khz48KBitRateMonoMp3, Audio24Khz96KBitRateMonoMp3, Audio24Khz160KBitRateMonoMp3, Raw16Khz16BitMonoTrueSilk, Riff16Khz16BitMonoPcm, Riff8Khz16BitMonoPcm, Riff24Khz16BitMonoPcm, Riff8Khz8BitMonoMULaw, Raw16Khz16BitMonoPcm, Raw24Khz16BitMonoPcm, Raw8Khz16BitMonoPcm, Ogg16Khz16BitMonoOpus, Ogg24Khz16BitMonoOpus, Raw48Khz16BitMonoPcm, Riff48Khz16BitMonoPcm, Audio48Khz96KBitRateMonoMp3, Audio48Khz192KBitRateMonoMp3, Ogg48Khz16BitMonoOpus, Webm16Khz16BitMonoOpus, Webm24Khz16BitMonoOpus, Raw24Khz16BitMonoTrueSilk, Raw8Khz8BitMonoALaw, Riff8Khz8BitMonoALaw, Webm24Khz16Bit24KbpsMonoOpus, Audio16Khz16Bit32KbpsMonoOpus, Audio24Khz16Bit48KbpsMonoOpus, Audio24Khz16Bit24KbpsMonoOpus, Raw22050Hz16BitMonoPcm, Riff22050Hz16BitMonoPcm, Raw44100Hz16BitMonoPcm, Riff44100Hz16BitMonoPcm, AmrWb16000Hz)
        subscriptionKey (object): the API key to use
        text (object): The text to synthesize
        url (str): Url of the service
        useSSML (object): whether to interpret the provided text input as SSML (Speech Synthesis Markup Language). The default value is false.
        voiceName (object): The name of the voice used for synthesis
    """

    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    language = Param(Params._dummy(), "language", "ServiceParam: The name of the language used for synthesis")
    
    locale = Param(Params._dummy(), "locale", "ServiceParam: The locale of the input text")
    
    outputFileCol = Param(Params._dummy(), "outputFileCol", "The location of the saved file as an HDFS compliant URI", typeConverter=TypeConverters.toString)
    
    outputFormat = Param(Params._dummy(), "outputFormat", "ServiceParam: The format for the output audio can be one of ArraySeq(Raw8Khz8BitMonoMULaw, Riff16Khz16KbpsMonoSiren, Audio16Khz16KbpsMonoSiren, Audio16Khz32KBitRateMonoMp3, Audio16Khz128KBitRateMonoMp3, Audio16Khz64KBitRateMonoMp3, Audio24Khz48KBitRateMonoMp3, Audio24Khz96KBitRateMonoMp3, Audio24Khz160KBitRateMonoMp3, Raw16Khz16BitMonoTrueSilk, Riff16Khz16BitMonoPcm, Riff8Khz16BitMonoPcm, Riff24Khz16BitMonoPcm, Riff8Khz8BitMonoMULaw, Raw16Khz16BitMonoPcm, Raw24Khz16BitMonoPcm, Raw8Khz16BitMonoPcm, Ogg16Khz16BitMonoOpus, Ogg24Khz16BitMonoOpus, Raw48Khz16BitMonoPcm, Riff48Khz16BitMonoPcm, Audio48Khz96KBitRateMonoMp3, Audio48Khz192KBitRateMonoMp3, Ogg48Khz16BitMonoOpus, Webm16Khz16BitMonoOpus, Webm24Khz16BitMonoOpus, Raw24Khz16BitMonoTrueSilk, Raw8Khz8BitMonoALaw, Riff8Khz8BitMonoALaw, Webm24Khz16Bit24KbpsMonoOpus, Audio16Khz16Bit32KbpsMonoOpus, Audio24Khz16Bit48KbpsMonoOpus, Audio24Khz16Bit24KbpsMonoOpus, Raw22050Hz16BitMonoPcm, Riff22050Hz16BitMonoPcm, Raw44100Hz16BitMonoPcm, Riff44100Hz16BitMonoPcm, AmrWb16000Hz)")
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    text = Param(Params._dummy(), "text", "ServiceParam: The text to synthesize")
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)
    
    useSSML = Param(Params._dummy(), "useSSML", "ServiceParam: whether to interpret the provided text input as SSML (Speech Synthesis Markup Language). The default value is false.")
    
    voiceName = Param(Params._dummy(), "voiceName", "ServiceParam: The name of the voice used for synthesis")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        errorCol="TextToSpeech_5638e010e51c_errors",
        language=None,
        languageCol=None,
        locale=None,
        localeCol=None,
        outputFileCol=None,
        outputFormat=None,
        outputFormatCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        text=None,
        textCol=None,
        url=None,
        useSSML=None,
        useSSMLCol=None,
        voiceName=None,
        voiceNameCol=None
        ):
        super(TextToSpeech, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.speech.TextToSpeech", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(errorCol="TextToSpeech_5638e010e51c_errors")
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
        errorCol="TextToSpeech_5638e010e51c_errors",
        language=None,
        languageCol=None,
        locale=None,
        localeCol=None,
        outputFileCol=None,
        outputFormat=None,
        outputFormatCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        text=None,
        textCol=None,
        url=None,
        useSSML=None,
        useSSMLCol=None,
        voiceName=None,
        voiceNameCol=None
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
        return "com.microsoft.azure.synapse.ml.services.speech.TextToSpeech"

    @staticmethod
    def _from_java(java_stage):
        module_name=TextToSpeech.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".TextToSpeech"
        return from_java(java_stage, module_name)

    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setLanguage(self, value):
        """
        Args:
            language: The name of the language used for synthesis
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
            language: The name of the language used for synthesis
        """
        self._java_obj = self._java_obj.setLanguageCol(value)
        return self
    
    def setLocale(self, value):
        """
        Args:
            locale: The locale of the input text
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
        self._java_obj = self._java_obj.setLocale(value)
        return self
    
    def setLocaleCol(self, value):
        """
        Args:
            locale: The locale of the input text
        """
        self._java_obj = self._java_obj.setLocaleCol(value)
        return self
    
    def setOutputFileCol(self, value):
        """
        Args:
            outputFileCol: The location of the saved file as an HDFS compliant URI
        """
        self._set(outputFileCol=value)
        return self
    
    def setOutputFormat(self, value):
        """
        Args:
            outputFormat: The format for the output audio can be one of ArraySeq(Raw8Khz8BitMonoMULaw, Riff16Khz16KbpsMonoSiren, Audio16Khz16KbpsMonoSiren, Audio16Khz32KBitRateMonoMp3, Audio16Khz128KBitRateMonoMp3, Audio16Khz64KBitRateMonoMp3, Audio24Khz48KBitRateMonoMp3, Audio24Khz96KBitRateMonoMp3, Audio24Khz160KBitRateMonoMp3, Raw16Khz16BitMonoTrueSilk, Riff16Khz16BitMonoPcm, Riff8Khz16BitMonoPcm, Riff24Khz16BitMonoPcm, Riff8Khz8BitMonoMULaw, Raw16Khz16BitMonoPcm, Raw24Khz16BitMonoPcm, Raw8Khz16BitMonoPcm, Ogg16Khz16BitMonoOpus, Ogg24Khz16BitMonoOpus, Raw48Khz16BitMonoPcm, Riff48Khz16BitMonoPcm, Audio48Khz96KBitRateMonoMp3, Audio48Khz192KBitRateMonoMp3, Ogg48Khz16BitMonoOpus, Webm16Khz16BitMonoOpus, Webm24Khz16BitMonoOpus, Raw24Khz16BitMonoTrueSilk, Raw8Khz8BitMonoALaw, Riff8Khz8BitMonoALaw, Webm24Khz16Bit24KbpsMonoOpus, Audio16Khz16Bit32KbpsMonoOpus, Audio24Khz16Bit48KbpsMonoOpus, Audio24Khz16Bit24KbpsMonoOpus, Raw22050Hz16BitMonoPcm, Riff22050Hz16BitMonoPcm, Raw44100Hz16BitMonoPcm, Riff44100Hz16BitMonoPcm, AmrWb16000Hz)
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
        self._java_obj = self._java_obj.setOutputFormat(value)
        return self
    
    def setOutputFormatCol(self, value):
        """
        Args:
            outputFormat: The format for the output audio can be one of ArraySeq(Raw8Khz8BitMonoMULaw, Riff16Khz16KbpsMonoSiren, Audio16Khz16KbpsMonoSiren, Audio16Khz32KBitRateMonoMp3, Audio16Khz128KBitRateMonoMp3, Audio16Khz64KBitRateMonoMp3, Audio24Khz48KBitRateMonoMp3, Audio24Khz96KBitRateMonoMp3, Audio24Khz160KBitRateMonoMp3, Raw16Khz16BitMonoTrueSilk, Riff16Khz16BitMonoPcm, Riff8Khz16BitMonoPcm, Riff24Khz16BitMonoPcm, Riff8Khz8BitMonoMULaw, Raw16Khz16BitMonoPcm, Raw24Khz16BitMonoPcm, Raw8Khz16BitMonoPcm, Ogg16Khz16BitMonoOpus, Ogg24Khz16BitMonoOpus, Raw48Khz16BitMonoPcm, Riff48Khz16BitMonoPcm, Audio48Khz96KBitRateMonoMp3, Audio48Khz192KBitRateMonoMp3, Ogg48Khz16BitMonoOpus, Webm16Khz16BitMonoOpus, Webm24Khz16BitMonoOpus, Raw24Khz16BitMonoTrueSilk, Raw8Khz8BitMonoALaw, Riff8Khz8BitMonoALaw, Webm24Khz16Bit24KbpsMonoOpus, Audio16Khz16Bit32KbpsMonoOpus, Audio24Khz16Bit48KbpsMonoOpus, Audio24Khz16Bit24KbpsMonoOpus, Raw22050Hz16BitMonoPcm, Riff22050Hz16BitMonoPcm, Raw44100Hz16BitMonoPcm, Riff44100Hz16BitMonoPcm, AmrWb16000Hz)
        """
        self._java_obj = self._java_obj.setOutputFormatCol(value)
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
    
    def setText(self, value):
        """
        Args:
            text: The text to synthesize
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
            text: The text to synthesize
        """
        self._java_obj = self._java_obj.setTextCol(value)
        return self
    
    def setUrl(self, value):
        """
        Args:
            url: Url of the service
        """
        self._set(url=value)
        return self
    
    def setUseSSML(self, value):
        """
        Args:
            useSSML: whether to interpret the provided text input as SSML (Speech Synthesis Markup Language). The default value is false.
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
        self._java_obj = self._java_obj.setUseSSML(value)
        return self
    
    def setUseSSMLCol(self, value):
        """
        Args:
            useSSML: whether to interpret the provided text input as SSML (Speech Synthesis Markup Language). The default value is false.
        """
        self._java_obj = self._java_obj.setUseSSMLCol(value)
        return self
    
    def setVoiceName(self, value):
        """
        Args:
            voiceName: The name of the voice used for synthesis
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
        self._java_obj = self._java_obj.setVoiceName(value)
        return self
    
    def setVoiceNameCol(self, value):
        """
        Args:
            voiceName: The name of the voice used for synthesis
        """
        self._java_obj = self._java_obj.setVoiceNameCol(value)
        return self

    
    def getErrorCol(self):
        """
        Returns:
            errorCol: column to hold http errors
        """
        return self.getOrDefault(self.errorCol)
    
    
    def getLanguage(self):
        """
        Returns:
            language: The name of the language used for synthesis
        """
        return self._java_obj.getLanguage()
    
    
    def getLocale(self):
        """
        Returns:
            locale: The locale of the input text
        """
        return self._java_obj.getLocale()
    
    
    def getOutputFileCol(self):
        """
        Returns:
            outputFileCol: The location of the saved file as an HDFS compliant URI
        """
        return self.getOrDefault(self.outputFileCol)
    
    
    def getOutputFormat(self):
        """
        Returns:
            outputFormat: The format for the output audio can be one of ArraySeq(Raw8Khz8BitMonoMULaw, Riff16Khz16KbpsMonoSiren, Audio16Khz16KbpsMonoSiren, Audio16Khz32KBitRateMonoMp3, Audio16Khz128KBitRateMonoMp3, Audio16Khz64KBitRateMonoMp3, Audio24Khz48KBitRateMonoMp3, Audio24Khz96KBitRateMonoMp3, Audio24Khz160KBitRateMonoMp3, Raw16Khz16BitMonoTrueSilk, Riff16Khz16BitMonoPcm, Riff8Khz16BitMonoPcm, Riff24Khz16BitMonoPcm, Riff8Khz8BitMonoMULaw, Raw16Khz16BitMonoPcm, Raw24Khz16BitMonoPcm, Raw8Khz16BitMonoPcm, Ogg16Khz16BitMonoOpus, Ogg24Khz16BitMonoOpus, Raw48Khz16BitMonoPcm, Riff48Khz16BitMonoPcm, Audio48Khz96KBitRateMonoMp3, Audio48Khz192KBitRateMonoMp3, Ogg48Khz16BitMonoOpus, Webm16Khz16BitMonoOpus, Webm24Khz16BitMonoOpus, Raw24Khz16BitMonoTrueSilk, Raw8Khz8BitMonoALaw, Riff8Khz8BitMonoALaw, Webm24Khz16Bit24KbpsMonoOpus, Audio16Khz16Bit32KbpsMonoOpus, Audio24Khz16Bit48KbpsMonoOpus, Audio24Khz16Bit24KbpsMonoOpus, Raw22050Hz16BitMonoPcm, Riff22050Hz16BitMonoPcm, Raw44100Hz16BitMonoPcm, Riff44100Hz16BitMonoPcm, AmrWb16000Hz)
        """
        return self._java_obj.getOutputFormat()
    
    
    def getSubscriptionKey(self):
        """
        Returns:
            subscriptionKey: the API key to use
        """
        return self._java_obj.getSubscriptionKey()
    
    
    def getText(self):
        """
        Returns:
            text: The text to synthesize
        """
        return self._java_obj.getText()
    
    
    def getUrl(self):
        """
        Returns:
            url: Url of the service
        """
        return self.getOrDefault(self.url)
    
    
    def getUseSSML(self):
        """
        Returns:
            useSSML: whether to interpret the provided text input as SSML (Speech Synthesis Markup Language). The default value is false.
        """
        return self._java_obj.getUseSSML()
    
    
    def getVoiceName(self):
        """
        Returns:
            voiceName: The name of the voice used for synthesis
        """
        return self._java_obj.getVoiceName()

    

    
    def setLocation(self, value):
        self._java_obj = self._java_obj.setLocation(value)
        return self
    
    def setLinkedService(self, value):
        self._java_obj = self._java_obj.setLinkedService(value)
        return self
        