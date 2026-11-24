"""Compatibility entry point: a single client/registration path for all tools."""
def register_coo(mcp):
    from profile_tools import register_profile_tools
    return register_profile_tools(mcp)
