from urllib.parse import urlparse, urlunparse

def create_base_url_openai(base_url: str) -> str:
    parsed = urlparse(base_url)

    netloc = parsed.netloc
    if netloc == 'mdb.ai':
        llm_host = 'llm.mdb.ai'
    else:
        llm_host = 'ai.' + netloc

    parsed = parsed._replace(path='', netloc=llm_host)

    return urlunparse(parsed)
    