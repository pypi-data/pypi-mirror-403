def build_url(domain, port=None, username=None, password=None, protocol="https") -> str:
    endpoint = f"{domain}:{port}" if port else domain
    auth = f"{username}:{password}@" if password else ""
    return f"{protocol}://{auth}{endpoint}"

def build(http, https) -> dict:
    return {k: v for k, v in [('http', http), ('https', https)] if v is not None}
