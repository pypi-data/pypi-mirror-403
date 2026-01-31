from simple_rest_client.api import API
from simple_rest_client.resource import Resource

from vgscli._version import __version__

CERT_MANAGER_URLS = {
    "dev": "https://cert-manager-api.verygoodsecurity.io",
    "prod": "https://cert-manager.apps.verygoodvault.com",
}


class CertificatesResource(Resource):
    actions = {"list": {"method": "GET", "url": "api/certificates"}}


def create_cert_manager_api(vault_id, environment, token):
    env = (environment or "prod").lower()
    base_url = CERT_MANAGER_URLS.get(env, CERT_MANAGER_URLS["prod"])
    api = API(
        api_root_url=base_url,
        params={},
        headers={
            "VGS-Tenant": vault_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"VGS CLI {__version__}",
            "Authorization": f"Bearer {token}",
        },
        timeout=30,
        append_slash=False,
        json_encode_body=True,
    )
    api.add_resource(resource_name="certificates", resource_class=CertificatesResource)
    return api
