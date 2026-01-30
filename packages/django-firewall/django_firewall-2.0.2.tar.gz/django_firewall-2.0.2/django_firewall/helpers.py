def get_client_ip(request):
    """
    Get the real client IP address from request headers.
    Handles CloudFlare and other proxy scenarios correctly.

    This function prioritizes headers in the following order:
    1. HTTP_CF_CONNECTING_IP (CloudFlare specific - real client IP)
    2. HTTP_X_FORWARDED_FOR (first IP in list - real client IP)
    3. HTTP_X_REAL_IP (may contain proxy IP)
    4. REMOTE_ADDR (fallback)

    Args:
        request: Django HttpRequest object

    Returns:
        str: The real client IP address, or None if not found
    """
    # CloudFlare specific header - contains the real client IP
    cf_connecting_ip = request.META.get("HTTP_CF_CONNECTING_IP")
    if cf_connecting_ip:
        return cf_connecting_ip

    # X-Forwarded-For header - first IP is usually the real client IP
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    # X-Real-IP header - may contain proxy IP instead of real client IP
    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        return x_real_ip

    # Fallback to REMOTE_ADDR
    return request.META.get("REMOTE_ADDR")
