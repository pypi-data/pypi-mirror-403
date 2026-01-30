from gen.client.configuration import Configuration
from gen.client.configuration_builder import ConfigurationBuilder
from gen.client.api_client import ApiClient
from six.moves.urllib.parse import urlencode
from six.moves.urllib.parse import urlunsplit
from six.moves.urllib.parse import quote
import os
from gen.client.controllers.manage_product_api import ManageProductApi
from gen.client.controllers.manage_product_image_api import ManageProductImageApi
from gen.client.controllers.manage_product_proscription_api import ManageProductProscriptionApi
from gen.client.controllers.search_product_api import SearchProductApi
from gen.client.controllers.search_product_image_api import SearchProductImageApi
from gen.client.controllers.search_product_metadata_api import SearchProductMetadataApi
from gen.client.controllers.search_product_proscription_api import SearchProductProscriptionApi



class CustomApiClient(ApiClient):
    SERVICE_NAME = 'lcdp-monolith-service'
    
    # ManageProductApi
    CREATE_PRODUCT_URI = {'uri': '/api/v1/products', 'method': 'POST'}
    SET_PRODUCT_VIDAL_PACKAGE_URI = {'uri': '/api/v1/products/{productId}/vidal-package', 'method': 'PUT'}
    UPDATE_PRODUCT_URI = {'uri': '/api/v1/products/{productId}', 'method': 'PATCH'}
    # ManageProductImageApi
    CREATE_PRODUCT_IMAGE_URI = {'uri': '/api/v1/products/{productId}/images', 'method': 'POST'}
    DELETE_PRODUCT_IMAGE_URI = {'uri': '/api/v1/products/{productId}/images/{imageId}', 'method': 'DELETE'}
    # ManageProductProscriptionApi
    CREATE_PRODUCT_PROSCRIPTION_URI = {'uri': '/api/v1/products/{productId}/proscriptions', 'method': 'POST'}
    DELETE_PRODUCT_PROSCRIPTION_URI = {'uri': '/api/v1/products/{productId}/proscriptions/{proscriptionId}', 'method': 'DELETE'}
    # SearchProductApi
    GET_PRODUCT_URI = {'uri': '/api/v1/products/{productId}', 'method': 'GET'}
    GET_PRODUCTS_URI = {'uri': '/api/v1/products', 'method': 'GET'}
    TEST_FREE_ACCESS_URI = {'uri': '/api/v1/products/testFreeAccess', 'method': 'GET'}
    # SearchProductImageApi
    GET_PRODUCT_IMAGE_URI = {'uri': '/api/v1/products/{productId}/images/{imageId}', 'method': 'GET'}
    GET_PRODUCT_IMAGES_URI = {'uri': '/api/v1/products/{productId}/images', 'method': 'GET'}
    # SearchProductMetadataApi
    GET_PRODUCT_SECONDARY_TYPES_URI = {'uri': '/api/v1/products/secondary-types', 'method': 'GET'}
    GET_PRODUCT_TYPES_URI = {'uri': '/api/v1/products/types', 'method': 'GET'}
    # SearchProductProscriptionApi
    GET_PRODUCT_PROSCRIPTIONS_URI = {'uri': '/api/v1/products/{productId}/proscriptions', 'method': 'GET'}

    def __init__(self, configuration=None, header_name=None, header_value=None, cookie=None):
        super().__init__(configuration, header_name, header_value, cookie)

    def forward_auth(self, headers):
        
        if 'Authorization' in headers:
            bearer, _, token = headers.get('Authorization').partition(' ')
            return self.create_auth_settings('bearerAuth', token)
        

    def create_auth_settings(self, scheme, value):
        
        if 'bearerAuth' == scheme:
            conf = Configuration()
            conf.access_token = value
            return conf.auth_settings()['bearerAuth']
        
        return None

    def build_url(self, request, resource_path, path_params, query_params, collection_formats=None):
        host = self._get_host(request)
        return self._generate_url(host, resource_path['uri'], path_params, query_params, collection_formats)

    def _generate_url(self, _host, resource_path, path_params, query_params, collection_formats=None):

        formatted_query_params = ''

        # path parameters
        if path_params:
            path_params = self.sanitize_for_serialization(path_params)
            path_params = self.parameters_to_tuples(path_params, collection_formats)
            for k, v in path_params:
                # specified safe chars, encode everything
                resource_path = resource_path.replace(
                    '{%s}' % k,
                    quote(str(v), safe=self.configuration.safe_chars_for_path_param)
                )

        # query parameters
        if query_params:
            query_params = self.sanitize_for_serialization(query_params)
            query_params = self.parameters_to_tuples(query_params,
                                                     collection_formats)
            formatted_query_params = '?' + urlencode(query_params)

        # request url
        if _host is None:
            return self.configuration.host + resource_path + formatted_query_params
        else:
            # use server/host defined in path or operation instead
            return _host + resource_path + formatted_query_params

    def __get_first_proxy_value(self, request, header_name, default_value):
        value = request.headers.get(header_name, None)
        if value:
            # Note: the header can contains multiple values if we get through multiple proxy, only take the first one (See : https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/x-forwarded-headers.html#x-forwarded-for)
            value = value.split(",")[0]

        if not value:
            value = default_value

        return value

    def _get_host(self, request):
        hostname = "localhost"
        scheme = "http"
        port = None
        if request:
            hostname = self.__get_first_proxy_value(request, "X-Forwarded-Host", request.host)
            scheme = self.__get_first_proxy_value(request, "X-Forwarded-Proto", request.scheme)
            port = self.__get_first_proxy_value(request, "X-Forwarded-Port", None)

            host_and_port = hostname.split(":", 1)
            if len(host_and_port) == 2:
                hostname = host_and_port[0]
                port = host_and_port[1]

        # Service mesh
        if hostname == "localhost":
            hostname = self.SERVICE_NAME
            scheme = ""
            port = None

        if (scheme == "http" and port == "80") \
            or (scheme == "https" and port == "443"):
            port = None

        netloc = hostname
        if port:
            netloc = netloc + ":" + port

        return urlunsplit((scheme, netloc, '', '', ''))



def create_manage_product_api(configurations=None, client_settings=None):
    """
        Create client with configuration

        :param configurations: Dict of desired configuration see ConfigurationBuilder and Configuration class
        :param client_settings: Dict of desired api client settings see ApiClient class

        :return: Configured api client
    """
    if configurations:
        conf = ConfigurationBuilder(**configurations).build_configuration_from_upstream()
    else:
        conf = ConfigurationBuilder().build_configuration_from_upstream()

    custom_client_settings = {}
    if client_settings:
        custom_client_settings=client_settings

    custom_api_client = CustomApiClient(configuration=conf, **custom_client_settings)

    service_version = os.getenv("SERVICE_VERSION")
    if service_version:
        custom_api_client.set_default_header("x-version", service_version)

    return ManageProductApi(custom_api_client)


def create_manage_product_image_api(configurations=None, client_settings=None):
    """
        Create client with configuration

        :param configurations: Dict of desired configuration see ConfigurationBuilder and Configuration class
        :param client_settings: Dict of desired api client settings see ApiClient class

        :return: Configured api client
    """
    if configurations:
        conf = ConfigurationBuilder(**configurations).build_configuration_from_upstream()
    else:
        conf = ConfigurationBuilder().build_configuration_from_upstream()

    custom_client_settings = {}
    if client_settings:
        custom_client_settings=client_settings

    custom_api_client = CustomApiClient(configuration=conf, **custom_client_settings)

    service_version = os.getenv("SERVICE_VERSION")
    if service_version:
        custom_api_client.set_default_header("x-version", service_version)

    return ManageProductImageApi(custom_api_client)


def create_manage_product_proscription_api(configurations=None, client_settings=None):
    """
        Create client with configuration

        :param configurations: Dict of desired configuration see ConfigurationBuilder and Configuration class
        :param client_settings: Dict of desired api client settings see ApiClient class

        :return: Configured api client
    """
    if configurations:
        conf = ConfigurationBuilder(**configurations).build_configuration_from_upstream()
    else:
        conf = ConfigurationBuilder().build_configuration_from_upstream()

    custom_client_settings = {}
    if client_settings:
        custom_client_settings=client_settings

    custom_api_client = CustomApiClient(configuration=conf, **custom_client_settings)

    service_version = os.getenv("SERVICE_VERSION")
    if service_version:
        custom_api_client.set_default_header("x-version", service_version)

    return ManageProductProscriptionApi(custom_api_client)


def create_search_product_api(configurations=None, client_settings=None):
    """
        Create client with configuration

        :param configurations: Dict of desired configuration see ConfigurationBuilder and Configuration class
        :param client_settings: Dict of desired api client settings see ApiClient class

        :return: Configured api client
    """
    if configurations:
        conf = ConfigurationBuilder(**configurations).build_configuration_from_upstream()
    else:
        conf = ConfigurationBuilder().build_configuration_from_upstream()

    custom_client_settings = {}
    if client_settings:
        custom_client_settings=client_settings

    custom_api_client = CustomApiClient(configuration=conf, **custom_client_settings)

    service_version = os.getenv("SERVICE_VERSION")
    if service_version:
        custom_api_client.set_default_header("x-version", service_version)

    return SearchProductApi(custom_api_client)


def create_search_product_image_api(configurations=None, client_settings=None):
    """
        Create client with configuration

        :param configurations: Dict of desired configuration see ConfigurationBuilder and Configuration class
        :param client_settings: Dict of desired api client settings see ApiClient class

        :return: Configured api client
    """
    if configurations:
        conf = ConfigurationBuilder(**configurations).build_configuration_from_upstream()
    else:
        conf = ConfigurationBuilder().build_configuration_from_upstream()

    custom_client_settings = {}
    if client_settings:
        custom_client_settings=client_settings

    custom_api_client = CustomApiClient(configuration=conf, **custom_client_settings)

    service_version = os.getenv("SERVICE_VERSION")
    if service_version:
        custom_api_client.set_default_header("x-version", service_version)

    return SearchProductImageApi(custom_api_client)


def create_search_product_metadata_api(configurations=None, client_settings=None):
    """
        Create client with configuration

        :param configurations: Dict of desired configuration see ConfigurationBuilder and Configuration class
        :param client_settings: Dict of desired api client settings see ApiClient class

        :return: Configured api client
    """
    if configurations:
        conf = ConfigurationBuilder(**configurations).build_configuration_from_upstream()
    else:
        conf = ConfigurationBuilder().build_configuration_from_upstream()

    custom_client_settings = {}
    if client_settings:
        custom_client_settings=client_settings

    custom_api_client = CustomApiClient(configuration=conf, **custom_client_settings)

    service_version = os.getenv("SERVICE_VERSION")
    if service_version:
        custom_api_client.set_default_header("x-version", service_version)

    return SearchProductMetadataApi(custom_api_client)


def create_search_product_proscription_api(configurations=None, client_settings=None):
    """
        Create client with configuration

        :param configurations: Dict of desired configuration see ConfigurationBuilder and Configuration class
        :param client_settings: Dict of desired api client settings see ApiClient class

        :return: Configured api client
    """
    if configurations:
        conf = ConfigurationBuilder(**configurations).build_configuration_from_upstream()
    else:
        conf = ConfigurationBuilder().build_configuration_from_upstream()

    custom_client_settings = {}
    if client_settings:
        custom_client_settings=client_settings

    custom_api_client = CustomApiClient(configuration=conf, **custom_client_settings)

    service_version = os.getenv("SERVICE_VERSION")
    if service_version:
        custom_api_client.set_default_header("x-version", service_version)

    return SearchProductProscriptionApi(custom_api_client)


