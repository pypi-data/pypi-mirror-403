from gen.client.configuration import Configuration
from gen.client.configuration_builder import ConfigurationBuilder
from gen.client.api_client import ApiClient
from six.moves.urllib.parse import urlencode
from six.moves.urllib.parse import urlunsplit
from six.moves.urllib.parse import quote
import os
from gen.client.controllers.search_sale_offer_api import SearchSaleOfferApi



class CustomApiClient(ApiClient):
    SERVICE_NAME = 'LCDP REST API'
    
    # SearchSaleOfferApi
    GET_SALE_OFFERS_URI = {'uri': '/v1/sale-offers', 'method': 'GET'}
    GET_SALE_OFFERS_BY_STATUS_URI = {'uri': '/v1/sale-offers/{saleOfferStatus}', 'method': 'GET'}

    def __init__(self, configuration=None, header_name=None, header_value=None, cookie=None):
        super().__init__(configuration, header_name, header_value, cookie)

    def forward_auth(self, headers):

    def create_auth_settings(self, scheme, value):
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



def create_search_sale_offer_api(configurations=None, client_settings=None):
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

    return SearchSaleOfferApi(custom_api_client)


