import asyncio
from .oidc.oidc import OIDCClient

public_tests = [
    # (
    #     "284523826908311692",
    #     "pflw13U3o1RDXBPOHfDQtPJPfYUeqFWNLQekt8fSXjRiXLo8icmFwdkM0pWBgiNc",
    #     "https://idp.cypol.dev",
    # ),
    # (
    #     None,
    #     None,
    #     "https://idphydra-uat.beeline.ru",
    # ),
    (
        "1",
        "A",
        "https://www.certification.openid.net/test/a/test-1/.well-known/openid-configuration",
    ),
]


async def main():
    for CLIENT_ID, CLIENT_SECRET, DISCOVERY in public_tests:
        client = OIDCClient(discovery_endpoint=DISCOVERY, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        await client.init()
        auth_link = await client.authorization_code_flow_start(redirect_uri="http://127.0.0.1:9999")
        print(auth_link)


if __name__ == "__main__":
    asyncio.run(main())
