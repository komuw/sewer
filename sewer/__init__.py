### FIX ME ### one last vestige of sewer-used-to-be-one-module (no?)
###            remove when I'm ready to slog through many tests, ugh

from .client import Client  # noqa: F401

### the new & improved auth_providers support

import importlib

from . import auth_providers

catalog = auth_providers.catalog


def create_auth_provider(name, **kwargs):
    """
    this is the most direct substitute for the old API usage

        dns_class = sewer.ThisProviderDns(**kwargs)

    which becomes

        dns_class = sewer.create_auth_provider("thisprovider", **kwargs)
    """

    authp = lookup_authp(name)

    # check what we can - have all required args and no invalid ones
    if any((r not in kwargs) for r in authp.req_args):
        raise ValueError("create_auth_provider: missing required arg %s" % r)
    if any((k not in authp.req_args and k not in authp.opt_args) for k in kwargs):
        raise ValueError("create_auth_provider: unknown keyword arg in %s" % list(kwargs))

    auth_module = import_auth_module(authp)
    auth_class = getattr(auth_module, authp.class_name)
    return auth_class(**kwargs)


def import_auth_module(authp):
    """
    Instead of the old-fashioned

        import sewer.ThisProvider

        something = sewer.ThisProvider.not_the_class

    just replace the import statement with

        auth_module = sewer.import_auth_module("thisprovider")

        something = auth_module.not_the_class
    """

    auth_module = importlib.import_module("sewer." + authp.module_name)
    return auth_module


### FIX ME ### can this be adapted to accept filepath and/or dotted module path?
###            would have to construct an AuthProviderInfo for either case...


def lookup_authp(name):
    """
    Find catalog entry for the given name.

    Currently checks the name and class_name fields from the catalog, skipping any
    class_names that have the designated "future use" name AuthProvider.
    """

    for authp in catalog:
        if name == authp.name:
            return authp
        if authp.class_name != "AuthProvider" and name == authp.class_name:
            return authp
    raise ValueError("get_auth_provider: unknown provider name: %s" % name)
