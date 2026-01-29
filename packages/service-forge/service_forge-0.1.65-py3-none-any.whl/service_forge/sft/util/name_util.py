def get_metadata_file_name(name: str, version: str) -> str:
    return "sf-meta.yaml"

def get_service_name(name: str, version: str) -> str:
    return f"sf-{name}-{version.replace('.', '-')}v"

def get_service_url_name(name: str, version: str) -> str:
    return f"{name}-{version.replace('.', '-')}"

def get_url(entry_url: str, service_name: str = "", version: str = "", path: str = "", subdomain: str = "") -> str:
    if not entry_url:
        raise ValueError("entry_config.url is not set")

    url_parts = entry_url.split("://", 1)
    if len(url_parts) != 2:
        raise ValueError(f"Invalid entry_url format: {entry_url}")

    protocol = url_parts[0]
    rest = url_parts[1]

    parts = rest.split("/", 1)
    domain = parts[0]
    base_path = parts[1] if len(parts) > 1 else ""

    if subdomain:
        domain = f"{subdomain}.{domain}"

    url_path_parts = []
    if base_path and subdomain == "":
        url_path_parts.append(base_path)

    if service_name and version:
        service_url_name = get_service_url_name(service_name, version)
        url_path_parts.append(service_url_name)

    if path:
        path = path.lstrip("/")
        url_path_parts.append(path)

    final_url = f"{protocol}://{domain}"
    if url_path_parts:
        final_url += "/" + "/".join(url_path_parts)

    return final_url