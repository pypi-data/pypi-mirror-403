import traceback
import types
from functools import wraps

import click
from click import Context, UsageError
from click.exceptions import Abort, Exit
from simple_rest_client import exceptions


def is_debug(ctx) -> bool:
    return bool(
        getattr(ctx, "obj", None) and getattr(getattr(ctx, "obj", None), "debug", False)
    )


def get_error_details(e):
    resp = getattr(e, "response", None)
    body = getattr(resp, "body", None)
    if isinstance(body, dict) and body.get("errors"):
        return [x.get("detail") for x in body["errors"] if isinstance(x, dict)]
    return None


class VgsCliError(UsageError):
    def __init__(self, message, ctx=None):
        self.message = message
        self.ctx = ctx

    def show(self, file=None):
        self.show_message()

    def show_message(self):
        debug = is_debug(self.ctx)
        if debug:
            click.echo(traceback.format_exc(), err=True)
        click.echo(self.message, err=True)


class VaultNotFoundError(VgsCliError):
    def __init__(self, vault_id, ctx=None):
        self.message = "Vault " + vault_id + " doesn't exist."
        self.ctx = ctx


class TokenNotValidError(VgsCliError):
    def __init__(self, message=None, ctx=None):
        self.message = (
            message or "Please run `vgs login` because your session has been expired."
        )
        self.ctx = ctx


class AuthenticationRequiredError(VgsCliError):
    def __init__(self, ctx=None):
        self.message = "Please run `vgs login` because your session has been expired."
        self.ctx = ctx


class AuthenticationError(VgsCliError):
    def __init__(self, ctx=None, details=None):
        debug = is_debug(ctx)
        self.message = (
            "Authentication error occurred"
            if debug
            else "Authentication error occurred."
        )
        if details:
            self.message = "{message} {details}".format(
                message=self.message, details=details
            )
        self.ctx = ctx


class ClientCredentialsAuthenticationError(VgsCliError):
    def __init__(self, ctx=None):
        debug = is_debug(ctx)
        self.message = (
            """Authentication error occurred.

NOTE: You may see this error if you're using an account with enabled OTP.
Auto login via environment variables with OTP is not supported.
 """
            if debug
            else """Authentication error occurred. (Run with --debug for a traceback.)

NOTE: You may see this error if you're using an account with enabled OTP.
Auto login via environment variables with OTP is not supported.
 """
        )
        self.ctx = ctx


class ApiError(VgsCliError):
    def __init__(self, e, ctx=None):
        details = get_error_details(e)
        debug = is_debug(ctx)
        if details:
            self.message = f"API error occurred: {details}"
        elif debug:
            self.message = "API error occurred."
        else:
            self.message = "API error occurred. (Run with --debug for a traceback.)"
        self.ctx = ctx


class UnhandledError(VgsCliError):
    def __init__(self, ctx=None):
        debug = is_debug(ctx)
        self.message = (
            "An unexpected error occurred."
            if debug
            else "An unexpected error occurred. (Run with --debug for a traceback.)"
        )
        self.ctx = ctx


class RouteNotValidError(VgsCliError):
    def __init__(self, error_message: str, ctx=None):
        debug = is_debug(ctx)
        error_message = f"Route cannot be applied due to errors:\n{error_message}"
        self.message = (
            error_message
            if debug
            else f"{error_message} (Run with --debug for a traceback.)"
        )
        self.ctx = ctx


class SchemaValidationError(VgsCliError):
    def __init__(self, message, ctx=None):
        self.message = f"Error during validation of the file input: {message}."
        self.ctx = ctx


class ServiceClientCreationError(VgsCliError):
    def __init__(self, e, ctx=None):
        details = get_error_details(e)
        self.message = f"Service Account creation failed with error: {details}"
        self.ctx = ctx


class ServiceClientDeletionError(VgsCliError):
    def __init__(self, e, ctx=None):
        details = get_error_details(e)
        self.message = f"Service Account deletion failed with error: {details}"
        self.ctx = ctx


class ServiceClientListingError(VgsCliError):
    def __init__(self, e, ctx=None):
        details = get_error_details(e)
        self.message = f"Service Account listing failed with error: {details}"
        self.ctx = ctx


class NoSuchFileOrDirectoryError(VgsCliError):
    def __init__(self, message, ctx=None):
        self.message = f"No such file or directory: {message}"
        self.ctx = ctx


class InsufficientPermissionsError(VgsCliError):
    def __init__(self, ctx=None):
        self.message = (
            "You don't have enough permissions to perform this operation. Please contact "
            "support@verygoodsecurity.com. "
        )
        self.ctx = ctx


class PermissionDeniedError(VgsCliError):
    def __init__(self, ctx=None):
        self.message = "You don't have enough permissions to the requested resource"
        self.ctx = ctx


class MaxNumberOfCredentialsExceededError(VgsCliError):
    def __init__(self, ctx=None):
        self.message = (
            "Maximum number of access credentials (10 per vault) reached.. Please contact "
            "support@verygoodsecurity.com to increase the limit. "
        )
        self.ctx = ctx


def status_code_error(**kwargs):
    def init(self, e, ctx=None):
        status = getattr(getattr(e, "response", None), "status_code", None)
        error_handler = kwargs.get(f"e{status}")
        if error_handler:
            self.message = (
                error_handler(e)
                if isinstance(error_handler, types.FunctionType)
                else error_handler
            )
            self.ctx = ctx
        else:
            ApiError.__init__(self, e, ctx=ctx)

    return type(
        "StatusCodeError",
        (ApiError,),
        {"__init__": init},
    )


def handle_errors(**outer_kwargs):
    def decorator_handle_errors(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (Abort, Exit):
                raise
            except exceptions.ClientError as e:
                ctx = args[0] if args and isinstance(args[0], Context) else None
                if ctx:
                    status = getattr(getattr(e, "response", None), "status_code", None)
                    if status == 401:
                        raise outer_kwargs.get(
                            "TokenNotValidError", TokenNotValidError
                        )(ctx=ctx)
                    if status == 403:
                        body = getattr(getattr(e, "response", None), "body", None)
                        errors = body.get("errors") if isinstance(body, dict) else None
                        detail = (
                            (
                                errors
                                and isinstance(errors, list)
                                and errors
                                and errors[0].get("detail")
                            )
                            if errors
                            else None
                        )
                        if detail and "Maximum number of access credentials" in detail:
                            raise outer_kwargs.get(
                                "MaxNumberOfCredentialsExceededError",
                                MaxNumberOfCredentialsExceededError,
                            )(ctx=ctx)
                        if errors:
                            raise outer_kwargs.get(
                                "InsufficientPermissionsError",
                                InsufficientPermissionsError,
                            )(ctx=ctx)
                        raise outer_kwargs.get(
                            "PermissionDeniedError", PermissionDeniedError
                        )(ctx=ctx)
                    raise outer_kwargs.get("ApiError", ApiError)(e, ctx=ctx)
                # No click.Context available; re-raise original error
                raise
            except (VgsCliError, click.BadParameter, click.BadArgumentUsage):
                raise
            except Exception:
                ctx = args[0] if args and isinstance(args[0], Context) else None
                if ctx:
                    raise UnhandledError(ctx=ctx)
                raise

        return wrapper

    return decorator_handle_errors
