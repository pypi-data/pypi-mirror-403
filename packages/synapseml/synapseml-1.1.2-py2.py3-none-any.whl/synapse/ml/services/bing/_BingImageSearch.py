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
class _BingImageSearch(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        AADToken (object): AAD Token used for authentication
        CustomAuthHeader (object): A Custom Value for Authorization Header
        aspect (object): Filter images by the following aspect ratios: Square: Return images with standard aspect ratioWide: Return images with wide screen aspect ratioTall: Return images with tall aspect ratioAll: Do not filter by aspect. Specifying this value is the same as not specifying the aspect parameter.
        color (object): Filter images by the following color options:ColorOnly: Return color imagesMonochrome: Return black and white imagesReturn images with one of the following dominant colors:Black,Blue,Brown,Gray,Green,Orange,Pink,Purple,Red,Teal,White,Yellow
        concurrency (int): max number of concurrent calls
        concurrentTimeout (float): max number seconds to wait on futures if concurrency >= 1
        count (object): The number of image results to return in the response. The actual number delivered may be less than requested.
        customHeaders (object): Map of Custom Header Key-Value Tuples.
        customUrlRoot (str): The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        errorCol (str): column to hold http errors
        freshness (object): Filter images by the following discovery options:Day: Return images discovered by Bing within the last 24 hoursWeek: Return images discovered by Bing within the last 7 daysMonth: Return images discovered by Bing within the last 30 daysYear: Return images discovered within the last year2017-06-15..2018-06-15: Return images discovered within the specified range of dates
        handler (object): Which strategy to use when handling requests
        height (object): Filter images that have the specified height, in pixels.You may use this filter with the size filter to return small images that have a height of 150 pixels.
        imageContent (object): Filter images by the following content types:Face: Return images that show only a person's facePortrait: Return images that show only a person's head and shoulders
        imageType (object): Filter images by the following image types:AnimatedGif: return animated gif imagesAnimatedGifHttps: return animated gif images that are from an https addressClipart: Return only clip art imagesLine: Return only line drawingsPhoto: Return only photographs (excluding line drawings, animated Gifs, and clip art)Shopping: Return only images that contain items where Bing knows of a merchant that is selling the items. This option is valid in the en-US market only. Transparent: Return only images with a transparent background.
        license (object): Filter images by the following license types:Any: Return images that are under any license type. The response doesn't include images that do not specify a license or the license is unknown.Public: Return images where the creator has waived their exclusive rights, to the fullest extent allowed by law.Share: Return images that may be shared with others. Changing or editing the image might not be allowed. Also, modifying, sharing, and using the image for commercial purposes might not be allowed. Typically, this option returns the most images.ShareCommercially: Return images that may be shared with others for personal or commercial purposes. Changing or editing the image might not be allowed.Modify: Return images that may be modified, shared, and used. Changing or editing the image might not be allowed. Modifying, sharing, and using the image for commercial purposes might not be allowed. ModifyCommercially: Return images that may be modified, shared, and used for personal or commercial purposes. Typically, this option returns the fewest images.All: Do not filter by license type. Specifying this value is the same as not specifying the license parameter. For more information about these license types, see Filter Images By License Type.
        maxFileSize (object): Filter images that are less than or equal to the specified file size.The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly larger than the specified maximum.You may specify this filter and minFileSize to filter images within a range of file sizes.
        maxHeight (object): Filter images that have a height that is less than or equal to the specified height. Specify the height in pixels.You may specify this filter and minHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.
        maxWidth (object): Filter images that have a width that is less than or equal to the specified width. Specify the width in pixels.You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.
        minFileSize (object): Filter images that are greater than or equal to the specified file size. The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly smaller than the specified minimum. You may specify this filter and maxFileSize to filter images within a range of file sizes.
        minHeight (object): Filter images that have a height that is greater than or equal to the specified height. Specify the height in pixels.You may specify this filter and maxHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.
        minWidth (object): Filter images that have a width that is greater than or equal to the specified width. Specify the width in pixels. You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.
        mkt (object): The market where the results come from. Typically, this is the country where the user is making the request from; however, it could be a different country if the user is not located in a country where Bing delivers results. The market must be in the form -. For example, en-US. Full list of supported markets: es-AR,en-AU,de-AT,nl-BE,fr-BE,pt-BR,en-CA,fr-CA,es-CL,da-DK,fi-FI,fr-FR,de-DE,zh-HK,en-IN,en-ID,en-IE,it-IT,ja-JP,ko-KR,en-MY,es-MX,nl-NL,en-NZ,no-NO,zh-CN,pl-PL,pt-PT,en-PH,ru-RU,ar-SA,en-ZA,es-ES,sv-SE,fr-CH,de-CH,zh-TW,tr-TR,en-GB,en-US,es-US
        offset (object): The zero-based offset that indicates the number of image results to skip before returning results
        outputCol (str): The name of the output column
        q (object): The user's search query string
        size (object): Filter images by the following sizes:Small: Return images that are less than 200x200 pixelsMedium: Return images that are greater than or equal to 200x200 pixels but less than 500x500 pixelsLarge: Return images that are 500x500 pixels or largerWallpaper: Return wallpaper images.AllDo not filter by size. Specifying this value is the same as not specifying the size parameter.You may use this parameter along with the height or width parameters. For example, you may use height and size to request small images that are 150 pixels tall.
        subscriptionKey (object): the API key to use
        telemHeaders (object): Map of Custom Header Key-Value Tuples.
        timeout (float): number of seconds to wait before closing the connection
        url (str): Url of the service
        width (object): Filter images that have the specified width, in pixels.You may use this filter with the size filter to return small images that have a width of 150 pixels.
    """

    AADToken = Param(Params._dummy(), "AADToken", "ServiceParam: AAD Token used for authentication")
    
    CustomAuthHeader = Param(Params._dummy(), "CustomAuthHeader", "ServiceParam: A Custom Value for Authorization Header")
    
    aspect = Param(Params._dummy(), "aspect", "ServiceParam: Filter images by the following aspect ratios: Square: Return images with standard aspect ratioWide: Return images with wide screen aspect ratioTall: Return images with tall aspect ratioAll: Do not filter by aspect. Specifying this value is the same as not specifying the aspect parameter.")
    
    color = Param(Params._dummy(), "color", "ServiceParam: Filter images by the following color options:ColorOnly: Return color imagesMonochrome: Return black and white imagesReturn images with one of the following dominant colors:Black,Blue,Brown,Gray,Green,Orange,Pink,Purple,Red,Teal,White,Yellow")
    
    concurrency = Param(Params._dummy(), "concurrency", "max number of concurrent calls", typeConverter=TypeConverters.toInt)
    
    concurrentTimeout = Param(Params._dummy(), "concurrentTimeout", "max number seconds to wait on futures if concurrency >= 1", typeConverter=TypeConverters.toFloat)
    
    count = Param(Params._dummy(), "count", "ServiceParam: The number of image results to return in the response. The actual number delivered may be less than requested.")
    
    customHeaders = Param(Params._dummy(), "customHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    customUrlRoot = Param(Params._dummy(), "customUrlRoot", "The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.", typeConverter=TypeConverters.toString)
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    freshness = Param(Params._dummy(), "freshness", "ServiceParam: Filter images by the following discovery options:Day: Return images discovered by Bing within the last 24 hoursWeek: Return images discovered by Bing within the last 7 daysMonth: Return images discovered by Bing within the last 30 daysYear: Return images discovered within the last year2017-06-15..2018-06-15: Return images discovered within the specified range of dates")
    
    handler = Param(Params._dummy(), "handler", "Which strategy to use when handling requests")
    
    height = Param(Params._dummy(), "height", "ServiceParam: Filter images that have the specified height, in pixels.You may use this filter with the size filter to return small images that have a height of 150 pixels.")
    
    imageContent = Param(Params._dummy(), "imageContent", "ServiceParam: Filter images by the following content types:Face: Return images that show only a person's facePortrait: Return images that show only a person's head and shoulders")
    
    imageType = Param(Params._dummy(), "imageType", "ServiceParam: Filter images by the following image types:AnimatedGif: return animated gif imagesAnimatedGifHttps: return animated gif images that are from an https addressClipart: Return only clip art imagesLine: Return only line drawingsPhoto: Return only photographs (excluding line drawings, animated Gifs, and clip art)Shopping: Return only images that contain items where Bing knows of a merchant that is selling the items. This option is valid in the en-US market only. Transparent: Return only images with a transparent background.")
    
    license = Param(Params._dummy(), "license", "ServiceParam: Filter images by the following license types:Any: Return images that are under any license type. The response doesn't include images that do not specify a license or the license is unknown.Public: Return images where the creator has waived their exclusive rights, to the fullest extent allowed by law.Share: Return images that may be shared with others. Changing or editing the image might not be allowed. Also, modifying, sharing, and using the image for commercial purposes might not be allowed. Typically, this option returns the most images.ShareCommercially: Return images that may be shared with others for personal or commercial purposes. Changing or editing the image might not be allowed.Modify: Return images that may be modified, shared, and used. Changing or editing the image might not be allowed. Modifying, sharing, and using the image for commercial purposes might not be allowed. ModifyCommercially: Return images that may be modified, shared, and used for personal or commercial purposes. Typically, this option returns the fewest images.All: Do not filter by license type. Specifying this value is the same as not specifying the license parameter. For more information about these license types, see Filter Images By License Type.")
    
    maxFileSize = Param(Params._dummy(), "maxFileSize", "ServiceParam: Filter images that are less than or equal to the specified file size.The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly larger than the specified maximum.You may specify this filter and minFileSize to filter images within a range of file sizes.")
    
    maxHeight = Param(Params._dummy(), "maxHeight", "ServiceParam: Filter images that have a height that is less than or equal to the specified height. Specify the height in pixels.You may specify this filter and minHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.")
    
    maxWidth = Param(Params._dummy(), "maxWidth", "ServiceParam: Filter images that have a width that is less than or equal to the specified width. Specify the width in pixels.You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.")
    
    minFileSize = Param(Params._dummy(), "minFileSize", "ServiceParam: Filter images that are greater than or equal to the specified file size. The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly smaller than the specified minimum. You may specify this filter and maxFileSize to filter images within a range of file sizes.")
    
    minHeight = Param(Params._dummy(), "minHeight", "ServiceParam: Filter images that have a height that is greater than or equal to the specified height. Specify the height in pixels.You may specify this filter and maxHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.")
    
    minWidth = Param(Params._dummy(), "minWidth", "ServiceParam: Filter images that have a width that is greater than or equal to the specified width. Specify the width in pixels. You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.")
    
    mkt = Param(Params._dummy(), "mkt", "ServiceParam: The market where the results come from. Typically, this is the country where the user is making the request from; however, it could be a different country if the user is not located in a country where Bing delivers results. The market must be in the form -. For example, en-US. Full list of supported markets: es-AR,en-AU,de-AT,nl-BE,fr-BE,pt-BR,en-CA,fr-CA,es-CL,da-DK,fi-FI,fr-FR,de-DE,zh-HK,en-IN,en-ID,en-IE,it-IT,ja-JP,ko-KR,en-MY,es-MX,nl-NL,en-NZ,no-NO,zh-CN,pl-PL,pt-PT,en-PH,ru-RU,ar-SA,en-ZA,es-ES,sv-SE,fr-CH,de-CH,zh-TW,tr-TR,en-GB,en-US,es-US")
    
    offset = Param(Params._dummy(), "offset", "ServiceParam: The zero-based offset that indicates the number of image results to skip before returning results")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    q = Param(Params._dummy(), "q", "ServiceParam: The user's search query string")
    
    size = Param(Params._dummy(), "size", "ServiceParam: Filter images by the following sizes:Small: Return images that are less than 200x200 pixelsMedium: Return images that are greater than or equal to 200x200 pixels but less than 500x500 pixelsLarge: Return images that are 500x500 pixels or largerWallpaper: Return wallpaper images.AllDo not filter by size. Specifying this value is the same as not specifying the size parameter.You may use this parameter along with the height or width parameters. For example, you may use height and size to request small images that are 150 pixels tall.")
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    telemHeaders = Param(Params._dummy(), "telemHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    timeout = Param(Params._dummy(), "timeout", "number of seconds to wait before closing the connection", typeConverter=TypeConverters.toFloat)
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)
    
    width = Param(Params._dummy(), "width", "ServiceParam: Filter images that have the specified width, in pixels.You may use this filter with the size filter to return small images that have a width of 150 pixels.")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        AADToken=None,
        AADTokenCol=None,
        CustomAuthHeader=None,
        CustomAuthHeaderCol=None,
        aspect=None,
        aspectCol=None,
        color=None,
        colorCol=None,
        concurrency=1,
        concurrentTimeout=None,
        count=None,
        countCol=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        errorCol="BingImageSearch_ac0bd09986a5_error",
        freshness=None,
        freshnessCol=None,
        handler=None,
        height=None,
        heightCol=None,
        imageContent=None,
        imageContentCol=None,
        imageType=None,
        imageTypeCol=None,
        license=None,
        licenseCol=None,
        maxFileSize=None,
        maxFileSizeCol=None,
        maxHeight=None,
        maxHeightCol=None,
        maxWidth=None,
        maxWidthCol=None,
        minFileSize=None,
        minFileSizeCol=None,
        minHeight=None,
        minHeightCol=None,
        minWidth=None,
        minWidthCol=None,
        mkt=None,
        mktCol=None,
        offset=None,
        offsetCol=None,
        outputCol="BingImageSearch_ac0bd09986a5_output",
        q=None,
        qCol=None,
        size=None,
        sizeCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        telemHeaders=None,
        telemHeadersCol=None,
        timeout=60.0,
        url="https://api.bing.microsoft.com/v7.0/images/search",
        width=None,
        widthCol=None
        ):
        super(_BingImageSearch, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.bing.BingImageSearch", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(concurrency=1)
        self._setDefault(errorCol="BingImageSearch_ac0bd09986a5_error")
        self._setDefault(outputCol="BingImageSearch_ac0bd09986a5_output")
        self._setDefault(timeout=60.0)
        self._setDefault(url="https://api.bing.microsoft.com/v7.0/images/search")
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
        aspect=None,
        aspectCol=None,
        color=None,
        colorCol=None,
        concurrency=1,
        concurrentTimeout=None,
        count=None,
        countCol=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        errorCol="BingImageSearch_ac0bd09986a5_error",
        freshness=None,
        freshnessCol=None,
        handler=None,
        height=None,
        heightCol=None,
        imageContent=None,
        imageContentCol=None,
        imageType=None,
        imageTypeCol=None,
        license=None,
        licenseCol=None,
        maxFileSize=None,
        maxFileSizeCol=None,
        maxHeight=None,
        maxHeightCol=None,
        maxWidth=None,
        maxWidthCol=None,
        minFileSize=None,
        minFileSizeCol=None,
        minHeight=None,
        minHeightCol=None,
        minWidth=None,
        minWidthCol=None,
        mkt=None,
        mktCol=None,
        offset=None,
        offsetCol=None,
        outputCol="BingImageSearch_ac0bd09986a5_output",
        q=None,
        qCol=None,
        size=None,
        sizeCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        telemHeaders=None,
        telemHeadersCol=None,
        timeout=60.0,
        url="https://api.bing.microsoft.com/v7.0/images/search",
        width=None,
        widthCol=None
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
        return "com.microsoft.azure.synapse.ml.services.bing.BingImageSearch"

    @staticmethod
    def _from_java(java_stage):
        module_name=_BingImageSearch.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".BingImageSearch"
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
    
    def setAspect(self, value):
        """
        Args:
            aspect: Filter images by the following aspect ratios: Square: Return images with standard aspect ratioWide: Return images with wide screen aspect ratioTall: Return images with tall aspect ratioAll: Do not filter by aspect. Specifying this value is the same as not specifying the aspect parameter.
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
        self._java_obj = self._java_obj.setAspect(value)
        return self
    
    def setAspectCol(self, value):
        """
        Args:
            aspect: Filter images by the following aspect ratios: Square: Return images with standard aspect ratioWide: Return images with wide screen aspect ratioTall: Return images with tall aspect ratioAll: Do not filter by aspect. Specifying this value is the same as not specifying the aspect parameter.
        """
        self._java_obj = self._java_obj.setAspectCol(value)
        return self
    
    def setColor(self, value):
        """
        Args:
            color: Filter images by the following color options:ColorOnly: Return color imagesMonochrome: Return black and white imagesReturn images with one of the following dominant colors:Black,Blue,Brown,Gray,Green,Orange,Pink,Purple,Red,Teal,White,Yellow
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
        self._java_obj = self._java_obj.setColor(value)
        return self
    
    def setColorCol(self, value):
        """
        Args:
            color: Filter images by the following color options:ColorOnly: Return color imagesMonochrome: Return black and white imagesReturn images with one of the following dominant colors:Black,Blue,Brown,Gray,Green,Orange,Pink,Purple,Red,Teal,White,Yellow
        """
        self._java_obj = self._java_obj.setColorCol(value)
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
    
    def setCount(self, value):
        """
        Args:
            count: The number of image results to return in the response. The actual number delivered may be less than requested.
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
        self._java_obj = self._java_obj.setCount(value)
        return self
    
    def setCountCol(self, value):
        """
        Args:
            count: The number of image results to return in the response. The actual number delivered may be less than requested.
        """
        self._java_obj = self._java_obj.setCountCol(value)
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
    
    def setFreshness(self, value):
        """
        Args:
            freshness: Filter images by the following discovery options:Day: Return images discovered by Bing within the last 24 hoursWeek: Return images discovered by Bing within the last 7 daysMonth: Return images discovered by Bing within the last 30 daysYear: Return images discovered within the last year2017-06-15..2018-06-15: Return images discovered within the specified range of dates
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
        self._java_obj = self._java_obj.setFreshness(value)
        return self
    
    def setFreshnessCol(self, value):
        """
        Args:
            freshness: Filter images by the following discovery options:Day: Return images discovered by Bing within the last 24 hoursWeek: Return images discovered by Bing within the last 7 daysMonth: Return images discovered by Bing within the last 30 daysYear: Return images discovered within the last year2017-06-15..2018-06-15: Return images discovered within the specified range of dates
        """
        self._java_obj = self._java_obj.setFreshnessCol(value)
        return self
    
    def setHandler(self, value):
        """
        Args:
            handler: Which strategy to use when handling requests
        """
        self._set(handler=value)
        return self
    
    def setHeight(self, value):
        """
        Args:
            height: Filter images that have the specified height, in pixels.You may use this filter with the size filter to return small images that have a height of 150 pixels.
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
        self._java_obj = self._java_obj.setHeight(value)
        return self
    
    def setHeightCol(self, value):
        """
        Args:
            height: Filter images that have the specified height, in pixels.You may use this filter with the size filter to return small images that have a height of 150 pixels.
        """
        self._java_obj = self._java_obj.setHeightCol(value)
        return self
    
    def setImageContent(self, value):
        """
        Args:
            imageContent: Filter images by the following content types:Face: Return images that show only a person's facePortrait: Return images that show only a person's head and shoulders
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
        self._java_obj = self._java_obj.setImageContent(value)
        return self
    
    def setImageContentCol(self, value):
        """
        Args:
            imageContent: Filter images by the following content types:Face: Return images that show only a person's facePortrait: Return images that show only a person's head and shoulders
        """
        self._java_obj = self._java_obj.setImageContentCol(value)
        return self
    
    def setImageType(self, value):
        """
        Args:
            imageType: Filter images by the following image types:AnimatedGif: return animated gif imagesAnimatedGifHttps: return animated gif images that are from an https addressClipart: Return only clip art imagesLine: Return only line drawingsPhoto: Return only photographs (excluding line drawings, animated Gifs, and clip art)Shopping: Return only images that contain items where Bing knows of a merchant that is selling the items. This option is valid in the en-US market only. Transparent: Return only images with a transparent background.
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
        self._java_obj = self._java_obj.setImageType(value)
        return self
    
    def setImageTypeCol(self, value):
        """
        Args:
            imageType: Filter images by the following image types:AnimatedGif: return animated gif imagesAnimatedGifHttps: return animated gif images that are from an https addressClipart: Return only clip art imagesLine: Return only line drawingsPhoto: Return only photographs (excluding line drawings, animated Gifs, and clip art)Shopping: Return only images that contain items where Bing knows of a merchant that is selling the items. This option is valid in the en-US market only. Transparent: Return only images with a transparent background.
        """
        self._java_obj = self._java_obj.setImageTypeCol(value)
        return self
    
    def setLicense(self, value):
        """
        Args:
            license: Filter images by the following license types:Any: Return images that are under any license type. The response doesn't include images that do not specify a license or the license is unknown.Public: Return images where the creator has waived their exclusive rights, to the fullest extent allowed by law.Share: Return images that may be shared with others. Changing or editing the image might not be allowed. Also, modifying, sharing, and using the image for commercial purposes might not be allowed. Typically, this option returns the most images.ShareCommercially: Return images that may be shared with others for personal or commercial purposes. Changing or editing the image might not be allowed.Modify: Return images that may be modified, shared, and used. Changing or editing the image might not be allowed. Modifying, sharing, and using the image for commercial purposes might not be allowed. ModifyCommercially: Return images that may be modified, shared, and used for personal or commercial purposes. Typically, this option returns the fewest images.All: Do not filter by license type. Specifying this value is the same as not specifying the license parameter. For more information about these license types, see Filter Images By License Type.
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
        self._java_obj = self._java_obj.setLicense(value)
        return self
    
    def setLicenseCol(self, value):
        """
        Args:
            license: Filter images by the following license types:Any: Return images that are under any license type. The response doesn't include images that do not specify a license or the license is unknown.Public: Return images where the creator has waived their exclusive rights, to the fullest extent allowed by law.Share: Return images that may be shared with others. Changing or editing the image might not be allowed. Also, modifying, sharing, and using the image for commercial purposes might not be allowed. Typically, this option returns the most images.ShareCommercially: Return images that may be shared with others for personal or commercial purposes. Changing or editing the image might not be allowed.Modify: Return images that may be modified, shared, and used. Changing or editing the image might not be allowed. Modifying, sharing, and using the image for commercial purposes might not be allowed. ModifyCommercially: Return images that may be modified, shared, and used for personal or commercial purposes. Typically, this option returns the fewest images.All: Do not filter by license type. Specifying this value is the same as not specifying the license parameter. For more information about these license types, see Filter Images By License Type.
        """
        self._java_obj = self._java_obj.setLicenseCol(value)
        return self
    
    def setMaxFileSize(self, value):
        """
        Args:
            maxFileSize: Filter images that are less than or equal to the specified file size.The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly larger than the specified maximum.You may specify this filter and minFileSize to filter images within a range of file sizes.
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
        self._java_obj = self._java_obj.setMaxFileSize(value)
        return self
    
    def setMaxFileSizeCol(self, value):
        """
        Args:
            maxFileSize: Filter images that are less than or equal to the specified file size.The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly larger than the specified maximum.You may specify this filter and minFileSize to filter images within a range of file sizes.
        """
        self._java_obj = self._java_obj.setMaxFileSizeCol(value)
        return self
    
    def setMaxHeight(self, value):
        """
        Args:
            maxHeight: Filter images that have a height that is less than or equal to the specified height. Specify the height in pixels.You may specify this filter and minHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.
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
        self._java_obj = self._java_obj.setMaxHeight(value)
        return self
    
    def setMaxHeightCol(self, value):
        """
        Args:
            maxHeight: Filter images that have a height that is less than or equal to the specified height. Specify the height in pixels.You may specify this filter and minHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.
        """
        self._java_obj = self._java_obj.setMaxHeightCol(value)
        return self
    
    def setMaxWidth(self, value):
        """
        Args:
            maxWidth: Filter images that have a width that is less than or equal to the specified width. Specify the width in pixels.You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.
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
        self._java_obj = self._java_obj.setMaxWidth(value)
        return self
    
    def setMaxWidthCol(self, value):
        """
        Args:
            maxWidth: Filter images that have a width that is less than or equal to the specified width. Specify the width in pixels.You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.
        """
        self._java_obj = self._java_obj.setMaxWidthCol(value)
        return self
    
    def setMinFileSize(self, value):
        """
        Args:
            minFileSize: Filter images that are greater than or equal to the specified file size. The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly smaller than the specified minimum. You may specify this filter and maxFileSize to filter images within a range of file sizes.
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
        self._java_obj = self._java_obj.setMinFileSize(value)
        return self
    
    def setMinFileSizeCol(self, value):
        """
        Args:
            minFileSize: Filter images that are greater than or equal to the specified file size. The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly smaller than the specified minimum. You may specify this filter and maxFileSize to filter images within a range of file sizes.
        """
        self._java_obj = self._java_obj.setMinFileSizeCol(value)
        return self
    
    def setMinHeight(self, value):
        """
        Args:
            minHeight: Filter images that have a height that is greater than or equal to the specified height. Specify the height in pixels.You may specify this filter and maxHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.
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
        self._java_obj = self._java_obj.setMinHeight(value)
        return self
    
    def setMinHeightCol(self, value):
        """
        Args:
            minHeight: Filter images that have a height that is greater than or equal to the specified height. Specify the height in pixels.You may specify this filter and maxHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.
        """
        self._java_obj = self._java_obj.setMinHeightCol(value)
        return self
    
    def setMinWidth(self, value):
        """
        Args:
            minWidth: Filter images that have a width that is greater than or equal to the specified width. Specify the width in pixels. You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.
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
        self._java_obj = self._java_obj.setMinWidth(value)
        return self
    
    def setMinWidthCol(self, value):
        """
        Args:
            minWidth: Filter images that have a width that is greater than or equal to the specified width. Specify the width in pixels. You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.
        """
        self._java_obj = self._java_obj.setMinWidthCol(value)
        return self
    
    def setMkt(self, value):
        """
        Args:
            mkt: The market where the results come from. Typically, this is the country where the user is making the request from; however, it could be a different country if the user is not located in a country where Bing delivers results. The market must be in the form -. For example, en-US. Full list of supported markets: es-AR,en-AU,de-AT,nl-BE,fr-BE,pt-BR,en-CA,fr-CA,es-CL,da-DK,fi-FI,fr-FR,de-DE,zh-HK,en-IN,en-ID,en-IE,it-IT,ja-JP,ko-KR,en-MY,es-MX,nl-NL,en-NZ,no-NO,zh-CN,pl-PL,pt-PT,en-PH,ru-RU,ar-SA,en-ZA,es-ES,sv-SE,fr-CH,de-CH,zh-TW,tr-TR,en-GB,en-US,es-US
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
        self._java_obj = self._java_obj.setMkt(value)
        return self
    
    def setMktCol(self, value):
        """
        Args:
            mkt: The market where the results come from. Typically, this is the country where the user is making the request from; however, it could be a different country if the user is not located in a country where Bing delivers results. The market must be in the form -. For example, en-US. Full list of supported markets: es-AR,en-AU,de-AT,nl-BE,fr-BE,pt-BR,en-CA,fr-CA,es-CL,da-DK,fi-FI,fr-FR,de-DE,zh-HK,en-IN,en-ID,en-IE,it-IT,ja-JP,ko-KR,en-MY,es-MX,nl-NL,en-NZ,no-NO,zh-CN,pl-PL,pt-PT,en-PH,ru-RU,ar-SA,en-ZA,es-ES,sv-SE,fr-CH,de-CH,zh-TW,tr-TR,en-GB,en-US,es-US
        """
        self._java_obj = self._java_obj.setMktCol(value)
        return self
    
    def setOffset(self, value):
        """
        Args:
            offset: The zero-based offset that indicates the number of image results to skip before returning results
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
        self._java_obj = self._java_obj.setOffset(value)
        return self
    
    def setOffsetCol(self, value):
        """
        Args:
            offset: The zero-based offset that indicates the number of image results to skip before returning results
        """
        self._java_obj = self._java_obj.setOffsetCol(value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setQ(self, value):
        """
        Args:
            q: The user's search query string
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
        self._java_obj = self._java_obj.setQ(value)
        return self
    
    def setQCol(self, value):
        """
        Args:
            q: The user's search query string
        """
        self._java_obj = self._java_obj.setQCol(value)
        return self
    
    def setSize(self, value):
        """
        Args:
            size: Filter images by the following sizes:Small: Return images that are less than 200x200 pixelsMedium: Return images that are greater than or equal to 200x200 pixels but less than 500x500 pixelsLarge: Return images that are 500x500 pixels or largerWallpaper: Return wallpaper images.AllDo not filter by size. Specifying this value is the same as not specifying the size parameter.You may use this parameter along with the height or width parameters. For example, you may use height and size to request small images that are 150 pixels tall.
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
        self._java_obj = self._java_obj.setSize(value)
        return self
    
    def setSizeCol(self, value):
        """
        Args:
            size: Filter images by the following sizes:Small: Return images that are less than 200x200 pixelsMedium: Return images that are greater than or equal to 200x200 pixels but less than 500x500 pixelsLarge: Return images that are 500x500 pixels or largerWallpaper: Return wallpaper images.AllDo not filter by size. Specifying this value is the same as not specifying the size parameter.You may use this parameter along with the height or width parameters. For example, you may use height and size to request small images that are 150 pixels tall.
        """
        self._java_obj = self._java_obj.setSizeCol(value)
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
    
    def setWidth(self, value):
        """
        Args:
            width: Filter images that have the specified width, in pixels.You may use this filter with the size filter to return small images that have a width of 150 pixels.
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
        self._java_obj = self._java_obj.setWidth(value)
        return self
    
    def setWidthCol(self, value):
        """
        Args:
            width: Filter images that have the specified width, in pixels.You may use this filter with the size filter to return small images that have a width of 150 pixels.
        """
        self._java_obj = self._java_obj.setWidthCol(value)
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
    
    
    def getAspect(self):
        """
        Returns:
            aspect: Filter images by the following aspect ratios: Square: Return images with standard aspect ratioWide: Return images with wide screen aspect ratioTall: Return images with tall aspect ratioAll: Do not filter by aspect. Specifying this value is the same as not specifying the aspect parameter.
        """
        return self._java_obj.getAspect()
    
    
    def getColor(self):
        """
        Returns:
            color: Filter images by the following color options:ColorOnly: Return color imagesMonochrome: Return black and white imagesReturn images with one of the following dominant colors:Black,Blue,Brown,Gray,Green,Orange,Pink,Purple,Red,Teal,White,Yellow
        """
        return self._java_obj.getColor()
    
    
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
    
    
    def getCount(self):
        """
        Returns:
            count: The number of image results to return in the response. The actual number delivered may be less than requested.
        """
        return self._java_obj.getCount()
    
    
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
    
    
    def getFreshness(self):
        """
        Returns:
            freshness: Filter images by the following discovery options:Day: Return images discovered by Bing within the last 24 hoursWeek: Return images discovered by Bing within the last 7 daysMonth: Return images discovered by Bing within the last 30 daysYear: Return images discovered within the last year2017-06-15..2018-06-15: Return images discovered within the specified range of dates
        """
        return self._java_obj.getFreshness()
    
    
    def getHandler(self):
        """
        Returns:
            handler: Which strategy to use when handling requests
        """
        return self.getOrDefault(self.handler)
    
    
    def getHeight(self):
        """
        Returns:
            height: Filter images that have the specified height, in pixels.You may use this filter with the size filter to return small images that have a height of 150 pixels.
        """
        return self._java_obj.getHeight()
    
    
    def getImageContent(self):
        """
        Returns:
            imageContent: Filter images by the following content types:Face: Return images that show only a person's facePortrait: Return images that show only a person's head and shoulders
        """
        return self._java_obj.getImageContent()
    
    
    def getImageType(self):
        """
        Returns:
            imageType: Filter images by the following image types:AnimatedGif: return animated gif imagesAnimatedGifHttps: return animated gif images that are from an https addressClipart: Return only clip art imagesLine: Return only line drawingsPhoto: Return only photographs (excluding line drawings, animated Gifs, and clip art)Shopping: Return only images that contain items where Bing knows of a merchant that is selling the items. This option is valid in the en-US market only. Transparent: Return only images with a transparent background.
        """
        return self._java_obj.getImageType()
    
    
    def getLicense(self):
        """
        Returns:
            license: Filter images by the following license types:Any: Return images that are under any license type. The response doesn't include images that do not specify a license or the license is unknown.Public: Return images where the creator has waived their exclusive rights, to the fullest extent allowed by law.Share: Return images that may be shared with others. Changing or editing the image might not be allowed. Also, modifying, sharing, and using the image for commercial purposes might not be allowed. Typically, this option returns the most images.ShareCommercially: Return images that may be shared with others for personal or commercial purposes. Changing or editing the image might not be allowed.Modify: Return images that may be modified, shared, and used. Changing or editing the image might not be allowed. Modifying, sharing, and using the image for commercial purposes might not be allowed. ModifyCommercially: Return images that may be modified, shared, and used for personal or commercial purposes. Typically, this option returns the fewest images.All: Do not filter by license type. Specifying this value is the same as not specifying the license parameter. For more information about these license types, see Filter Images By License Type.
        """
        return self._java_obj.getLicense()
    
    
    def getMaxFileSize(self):
        """
        Returns:
            maxFileSize: Filter images that are less than or equal to the specified file size.The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly larger than the specified maximum.You may specify this filter and minFileSize to filter images within a range of file sizes.
        """
        return self._java_obj.getMaxFileSize()
    
    
    def getMaxHeight(self):
        """
        Returns:
            maxHeight: Filter images that have a height that is less than or equal to the specified height. Specify the height in pixels.You may specify this filter and minHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.
        """
        return self._java_obj.getMaxHeight()
    
    
    def getMaxWidth(self):
        """
        Returns:
            maxWidth: Filter images that have a width that is less than or equal to the specified width. Specify the width in pixels.You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.
        """
        return self._java_obj.getMaxWidth()
    
    
    def getMinFileSize(self):
        """
        Returns:
            minFileSize: Filter images that are greater than or equal to the specified file size. The maximum file size that you may specify is 520,192 bytes. If you specify a larger value, the API uses 520,192. It is possible that the response may include images that are slightly smaller than the specified minimum. You may specify this filter and maxFileSize to filter images within a range of file sizes.
        """
        return self._java_obj.getMinFileSize()
    
    
    def getMinHeight(self):
        """
        Returns:
            minHeight: Filter images that have a height that is greater than or equal to the specified height. Specify the height in pixels.You may specify this filter and maxHeight to filter images within a range of heights. This filter and the height filter are mutually exclusive.
        """
        return self._java_obj.getMinHeight()
    
    
    def getMinWidth(self):
        """
        Returns:
            minWidth: Filter images that have a width that is greater than or equal to the specified width. Specify the width in pixels. You may specify this filter and maxWidth to filter images within a range of widths. This filter and the width filter are mutually exclusive.
        """
        return self._java_obj.getMinWidth()
    
    
    def getMkt(self):
        """
        Returns:
            mkt: The market where the results come from. Typically, this is the country where the user is making the request from; however, it could be a different country if the user is not located in a country where Bing delivers results. The market must be in the form -. For example, en-US. Full list of supported markets: es-AR,en-AU,de-AT,nl-BE,fr-BE,pt-BR,en-CA,fr-CA,es-CL,da-DK,fi-FI,fr-FR,de-DE,zh-HK,en-IN,en-ID,en-IE,it-IT,ja-JP,ko-KR,en-MY,es-MX,nl-NL,en-NZ,no-NO,zh-CN,pl-PL,pt-PT,en-PH,ru-RU,ar-SA,en-ZA,es-ES,sv-SE,fr-CH,de-CH,zh-TW,tr-TR,en-GB,en-US,es-US
        """
        return self._java_obj.getMkt()
    
    
    def getOffset(self):
        """
        Returns:
            offset: The zero-based offset that indicates the number of image results to skip before returning results
        """
        return self._java_obj.getOffset()
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getQ(self):
        """
        Returns:
            q: The user's search query string
        """
        return self._java_obj.getQ()
    
    
    def getSize(self):
        """
        Returns:
            size: Filter images by the following sizes:Small: Return images that are less than 200x200 pixelsMedium: Return images that are greater than or equal to 200x200 pixels but less than 500x500 pixelsLarge: Return images that are 500x500 pixels or largerWallpaper: Return wallpaper images.AllDo not filter by size. Specifying this value is the same as not specifying the size parameter.You may use this parameter along with the height or width parameters. For example, you may use height and size to request small images that are 150 pixels tall.
        """
        return self._java_obj.getSize()
    
    
    def getSubscriptionKey(self):
        """
        Returns:
            subscriptionKey: the API key to use
        """
        return self._java_obj.getSubscriptionKey()
    
    
    def getTelemHeaders(self):
        """
        Returns:
            telemHeaders: Map of Custom Header Key-Value Tuples.
        """
        return self._java_obj.getTelemHeaders()
    
    
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
    
    
    def getWidth(self):
        """
        Returns:
            width: Filter images that have the specified width, in pixels.You may use this filter with the size filter to return small images that have a width of 150 pixels.
        """
        return self._java_obj.getWidth()

    

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
    
    def setLinkedService(self, value):
        self._java_obj = self._java_obj.setLinkedService(value)
        return self
        