from ..client import Client
from .context import Context


def explain_query(mdx: str, /, *, client: Client, context: Context) -> object:
    path = f"{client.get_path_and_version_id('activeviam/pivot')[0]}/cube/query/mdx/queryplan"
    response = client.http_client.post(
        path,
        json={"context": {**context}, "mdx": mdx},
    ).raise_for_status()
    return response.json()
