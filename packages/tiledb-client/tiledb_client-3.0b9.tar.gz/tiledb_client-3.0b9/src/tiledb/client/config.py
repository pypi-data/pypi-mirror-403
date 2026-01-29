"""TileDB client session configuration

This module maintains the global state of client session configuration
and several methods for loading it from and saving it to profiles on
disk.

"""

# "config" is a dynamic attribute of this module. The actual state of
# the attribute is bound to "_config", which begins uninitialized.
# Looking up "config" from tiledb.client.config causes our stored
# configuration to be loaded just as needed, and makes calling login()
# unnecessary in many cases.

import logging
import warnings

import urllib3

import tiledb
from tiledb.client._common.api_v4 import configuration

logger = logging.getLogger(__name__)


class ConfigurationError(tiledb.TileDBError):
    """Raise for configuration-related errors"""


_config = None
_workspace_id = None
_workspace = None
_self_user = None


def __getattr__(name):
    if name == "config":
        if _config is None:
            load_configuration()
        return _config
    else:
        raise AttributeError


def load_configuration() -> None:
    """Loads parameters and configures the session's client.

    Configuration parameters are obtained from the user's default TileDB
    profile or from the environment via tiledb.Config.

    This enables login-free execution of Python applications using the
    default profile and/or properly configured environment. To use
    a different profile, one must call tiledb.client.login().

    Configuration parameters may come from several sources, in order of
    precedence:

    - user-configured config values
    - environment variables
    - profile values
    - default config values

    Raises
    ------
    ConfigurationError
        When configuration parameters are not sufficent and server
        requests are not possible.

    Notes
    -----
    This function is called once at most during any Python interpreter
    session or program lifetime, on the first access of
    tiledb.client.config, such as during the first HTTP server request.

    """
    config_py = tiledb.Config()
    token = config_py.get("rest.token", False)
    username = config_py.get("rest.username", False)
    password = config_py.get("rest.password", False)
    host = config_py.get("rest.server_address", False)
    verify_ssl = config_py.get("rest.verify_ssl", False)
    workspace = config_py.get("rest.workspace", False)
    ca_file = config_py.get("ssl.ca_file", False)

    if not token and not (username and password):
        raise ConfigurationError(
            "Authentication parameters were not found in the environment or default profile. Call tiledb.client.login() to continue."
        )

    if token:
        api_key = {"X-TILEDB-REST-API-KEY": token}
        # Attempt to parse workspace from the token.
        try:
            _, middle, _ = token.split("-")
            if middle.startswith("ws_"):
                workspace = middle
        except ValueError:
            logger.info("No workspace id detected in token.")
    else:
        api_key = {}

    if not workspace:
        raise ConfigurationError(
            "The workspace was not found in the environment or default profile. Call tiledb.client.login() to continue."
        )

    if not host:
        raise ConfigurationError(
            "The server host was not found in the environment or default profile. Call tiledb.client.login() to continue."
        )

    *_, hostname = host.split("/")
    if hostname.startswith("app."):
        warnings.warn(
            "The profile's host name starts with 'app.', which is usually reserved for the TileDB Web UI. If you experience client exceptions, use tiledb.client.configure() to update your profile with the correct host name. Ask your administrator for the correct value if necessary.",
            UserWarning,
        )

    setup_configuration(
        api_key=api_key,
        username=username,
        password=password,
        host=host,
        verify_ssl=verify_ssl,
        ca_file=ca_file,
        workspace=workspace,
    )


def setup_configuration(
    api_key=None,
    host="",
    username=None,
    password=None,
    verify_ssl=True,
    ca_file=None,
    workspace=None,
) -> None:
    """Configures the session's client."""
    global _config
    global _workspace_id

    # Re-initialize the global session configuration.
    cfg_kwds = {
        "api_key": api_key or {},
        "host": host,
    }
    if username and password:
        cfg_kwds.update(username=username, password=password)

    _config = configuration.Configuration(**cfg_kwds)

    if verify_ssl is False:
        _config.verify_ssl = verify_ssl

    if ca_file:
        _config.ssl_ca_cert = ca_file

    _config.retries = urllib3.Retry(
        total=3,
        backoff_factor=0.25,
        status_forcelist=[503],
        allowed_methods=[
            "HEAD",
            "GET",
            "PUT",
            "DELETE",
            "OPTIONS",
            "TRACE",
            "POST",
            "PATCH",
        ],
        raise_on_status=False,
        remove_headers_on_redirect=[],
    )

    _workspace_id = workspace


def setup_default_ctx() -> None:
    """Updates the TileDB-Py default context with the current profile's REST parameters.

    This function synchronizes the TileDB-Py default context with the REST parameters
    from the currently active profile (as specified by TILEDB_PROFILE_* environment
    variables). It preserves all non-REST configuration parameters while replacing all
    rest.* parameters with those from the new profile.

    """
    from tiledb.ctx import _ctx_var

    # Get existing default context if it exists
    try:
        old_ctx = _ctx_var.get()
        old_config = old_ctx.config()

        # Load new profile configuration from environment (TILEDB_PROFILE_NAME)
        config_py = tiledb.Config()

        # Profile-specific parameters that need to be explicitly updated
        profile_params = [
            "rest.token",
            "rest.username",
            "rest.password",
            "rest.workspace",
            "rest.server_address",
            "rest.verify_ssl",
            "ssl.ca_file",
        ]

        # Clear old profile-specific parameters
        for param in profile_params:
            try:
                del old_config[param]
            except (KeyError, tiledb.TileDBError):
                pass

        # Set new profile-specific parameters from new profile
        for param in profile_params:
            value = config_py.get(param, None)
            if value:
                old_config[param] = value

        # Create new context with updated config and set as default
        new_ctx = tiledb.Ctx(old_config)
        _ctx_var.set(new_ctx)

    except LookupError:
        # No default context exists yet
        # It will be created on first use with the new profile from environment
        logger.debug("setup_default_ctx: no default context exists yet")
        pass
