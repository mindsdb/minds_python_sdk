from urllib.parse import urlparse, urlunparse

def get_openai_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)

    netloc = parsed.netloc
    if netloc == 'mdb.ai':
        llm_host = 'llm.mdb.ai'
    else:
        llm_host = 'ai.' + netloc

    parsed = parsed._replace(path='', netloc=llm_host)

    return urlunparse(parsed)
    