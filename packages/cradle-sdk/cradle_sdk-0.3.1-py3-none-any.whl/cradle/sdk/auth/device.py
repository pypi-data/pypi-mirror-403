import contextlib
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal, Self
from urllib.parse import urlencode, urljoin

import httpx
import jwt
import keyring
import keyring.errors
from keyring.backends.chainer import ChainerBackend
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from typing_extensions import Generator

from cradle.sdk.exceptions import ClientError

logger = logging.getLogger(__name__)


class ClientAuthError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Authentication Error: {message}")


class ReauthenticationRequiredError(ClientAuthError):
    def __init__(self, logout_url):
        self.logout_url = logout_url
        super().__init__("Reauthentication required")


class DeviceAuthResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


class AuthenticateSuccessResponse(BaseModel):
    access_token: str
    refresh_token: str
    organization_id: str | None = None
    authentication_method: str
    user: dict


class AuthenticateAuthenticationErrorResponse(BaseModel):
    error: str
    error_description: str


class UnknownErrorResponse(BaseModel):
    response: dict


AuthenticateErrorResponse = AuthenticateAuthenticationErrorResponse | UnknownErrorResponse


class UnauthorizedResponse(BaseModel):
    authorized: Literal[False] = False
    can_reauth: bool
    org_id: str | None


class AuthorizedResponse(BaseModel):
    authorized: Literal[True] = True


CheckAuthResponse = Annotated[UnauthorizedResponse | AuthorizedResponse, Field(discriminator="authorized")]
CheckAuthResponseAdapter = TypeAdapter(CheckAuthResponse)


class _DeviceAuthStrategy(BaseModel):
    client_id: str
    app_url: str
    auth_api_url: str


class DeviceAuth(httpx.Auth):
    def __init__(
        self,
        client_id: str,
        cradle_app_url: str,
        cradle_api_base_url: str,
        auth_base_url: str,
        workspace: str | None = None,
        use_keyring: bool = True,
        user_agent: str | None = None,
    ):
        self.client_id = client_id
        self.cradle_app_url = cradle_app_url
        self.use_keyring = use_keyring
        self._keyring_servicename: str = __name__
        self.workspace = workspace
        self.cradle_api_base_url = cradle_api_base_url
        self.token: AuthenticateSuccessResponse | None = None

        self.checked_for_reauth = False
        self.force_org_id = None

        self.auth_base_url = auth_base_url
        self.user_agent = user_agent

        # Try to load token from keyring on initialization
        if self.use_keyring:
            self._load_token_from_keyring()

    @classmethod
    def from_strategy(
        cls,
        client: httpx.Client,
        base_url: str,
        workspace: str | None,
        use_keyring: bool = True,
    ) -> Self:
        """Create device auth with parameters looked up in the API."""
        api_strategy_url = f"{base_url}/auth:apiStrategy"

        try:
            response = client.get(api_strategy_url)
            response.raise_for_status()
            strategy = _DeviceAuthStrategy.model_validate(response.json())
        except Exception as exc:
            raise RuntimeError(f"Failed to retreive auth strategy from {api_strategy_url}") from exc

        return cls(
            workspace=workspace,
            cradle_api_base_url=base_url,
            client_id=strategy.client_id,
            cradle_app_url=strategy.app_url,
            auth_base_url="https://auth.cradle.bio",
            use_keyring=use_keyring,
            user_agent=client.headers.get("User-Agent"),
        )

    @property
    def access_token(self) -> str | None:
        return self.token.access_token if self.token else None

    @property
    def refresh_token(self) -> str | None:
        return self.token.refresh_token if self.token else None

    @property
    def session_id(self) -> str | None:
        return self.jwt_payload.get("sid") if self.jwt_payload else None

    @property
    def authorized_workspace_id(self) -> str | None:
        return self.jwt_payload.get("urn:cradle:workspace_id") if self.jwt_payload else None

    @property
    def jwks_url(self) -> str:
        return f"{self.auth_base_url}/sso/jwks/{self.client_id}"

    @property
    def jwt_payload(self) -> dict | None:
        if self.token is None:
            return None

        # Per https://github.com/jpadilla/pyjwt/issues/939 - we should not be verifying the `iat` time here
        # as it could be slightly in the future.
        return jwt.decode(self.token.access_token, options={"verify_signature": False, "verify_iat": False})

    @property
    def expires_at(self) -> datetime | None:
        if self.jwt_payload is None:
            return None
        return datetime.fromtimestamp(self.jwt_payload["exp"], tz=UTC)

    @property
    def org_id(self) -> str | None:
        if self.jwt_payload is None:
            return None
        return self.jwt_payload.get("org_id")

    @property
    def logout_url(self) -> str | None:
        session_id = self.session_id
        if session_id is None:
            return None

        logout_path = "/user_management/sessions/logout"
        return_to = f"{self.cradle_app_url}/_/sdk/post-logout"
        query = urlencode({"session_id": session_id, "return_to": return_to})
        return urljoin(self.auth_base_url, logout_path) + f"?{query}"

    def _needs_refresh(self) -> bool:
        if self.access_token is None or self.expires_at is None:
            return False

        if self.force_org_id is not None and self.org_id != self.force_org_id:
            return True

        # access_token is valid until expires_at (which I think is currently issue time + 5 min)
        # We refresh the access_token 10 seconds before expiration to avoid race conditions
        return datetime.now(tz=UTC) > self.expires_at - timedelta(seconds=10)

    def _save_token_to_keyring(self, token: AuthenticateSuccessResponse) -> None:
        """Save token data to keyring."""
        if not self.use_keyring:
            return

        # The backends built into keyring are secure.
        # They will only be in the list of chainer backends if they are "viable"
        # If this list is empty, it likely means we have no secure keyrings available.
        has_keyring_backend = any(x.__class__.__module__.startswith("keyring.") for x in ChainerBackend.backends)
        # The backends built into keyrings.alt are insecure.
        has_alt_backend = any(x.__class__.__module__.startswith("keyrings.alt") for x in ChainerBackend.backends)

        if not has_keyring_backend and has_alt_backend:
            logger.warning(
                "Keyring is likely using a backend from `keyrings.alt`. This is an *insecure* way to save your authentication for a limited period of time."
            )

        # Store the token response, don't worry if saving to keyring fails - maybe this system doesn't support it
        #
        # Some systems don't support keyring, such as a headless linux machine (because there is no GUI to pop up the
        # "do you want to allow this application to access your keyring?" dialog). This can be a problem when people run
        # code on a remote machine.
        #
        # In those cases, a user can install `keyrings.alt` into their notebook or environment, and a new backend called
        # `keyrings.alt.file.PlaintextKeyring` will be available. Because this is insecure, we don't do it by default.
        # However, all a user needs to do is install `keyrings.alt` into their notebook or environment, and it will automatically
        # be added to the resolution order of keyring backends.
        #
        # If the system does not support any secure keyrings, and no alternate backends are installed, we will get a NoKeyringError.
        #
        # If there is a keyring that does not support set_password in the resolution order - such as keyrings.gauth.GooglePythonAuth
        # aka `keyrings.google-artifactregistry-auth`, we will get a NotImplementedError. If there is another keyring below it in the
        # order, like PlaintextKeyring that does, then the ChainerBackend will fall through to the PlaintextKeyring.
        try:
            keyring.set_password(self._keyring_servicename, self.client_id, token.model_dump_json())
        except (NotImplementedError, keyring.errors.NoKeyringError):
            logger.warning("""No keyring available. You will need to re-authenticate every time you run this code.

To save your authentication for a limited period of time in an *insecure* way, install python package `keyrings.alt` into your notebook or environment and re-run this code.
""")

    def _load_token_from_keyring(self) -> None:
        """Load token data from keyring."""
        if not self.use_keyring:
            return

        with contextlib.suppress(keyring.errors.KeyringError):
            token_json = keyring.get_password(self._keyring_servicename, self.client_id)
            if token_json is not None:
                self._update_token(AuthenticateSuccessResponse.model_validate(json.loads(token_json)))

    def _clear_token_from_keyring(self) -> None:
        """Clear token data from keyring."""
        if not self.use_keyring:
            return

        # Don't worry if deleting from keyring fails - maybe this system doesn't support it
        with contextlib.suppress(keyring.errors.KeyringError):
            keyring.delete_password(self._keyring_servicename, self.client_id)

    def _update_token(self, success_response: AuthenticateSuccessResponse) -> None:
        self.token = success_response
        # Save to keyring for persistence
        self._save_token_to_keyring(success_response)

    @staticmethod
    def parse_response(response: httpx.Response) -> AuthenticateSuccessResponse | AuthenticateErrorResponse:
        if response.is_success:
            return AuthenticateSuccessResponse.model_validate(response.json())
        try:
            return AuthenticateAuthenticationErrorResponse.model_validate(response.json())
        except ValidationError:
            return UnknownErrorResponse(response=response.json())

    def _authenticate(
        self, data: dict[str, str]
    ) -> Generator[httpx.Request, httpx.Response, AuthenticateSuccessResponse | AuthenticateErrorResponse]:
        response = yield httpx.Request(
            method="POST",
            url=f"{self.auth_base_url}/user_management/authenticate",
            headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": self.user_agent or "unknown"},
            data={**data, "client_id": self.client_id},
        )
        response.read()

        return self.parse_response(response)

    def _refresh_token(self) -> Generator[httpx.Request, httpx.Response, None]:
        if self.refresh_token is None:
            raise ClientAuthError("No refresh token available")

        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        if self.force_org_id is not None:
            refresh_data["organization_id"] = self.force_org_id

        response = yield from self._authenticate(refresh_data)

        match response:
            case AuthenticateAuthenticationErrorResponse(error="invalid_grant"):
                # This might mean the refresh token has expired, so let's clear keyring and re-run the device flow
                self._clear_token_from_keyring()
                self.token = None
                yield from self._start_device_flow()
            case AuthenticateAuthenticationErrorResponse(error="sso_required"):
                # This means the token cannot be refreshed for a different org that requires SSO,
                # so let's clear keyring and re-run the device flow
                self._clear_token_from_keyring()
                self.token = None
                yield from self._start_device_flow()
            case AuthenticateAuthenticationErrorResponse(error="mfa_enrollment"):
                # It might not be possible to refresh a token to a different organization if the new
                # organization has a different security policy in place, e.g. regarding MFA.
                # In this case we need to log out and re-authenticate to the new workspace.
                # Unfortunately this requires the user to manually click a logout link.
                logout_url = self.logout_url
                if logout_url is None:
                    raise ClientAuthError("No session ID available to log out.")

                print(
                    "Access to the requested workspace requires re-authentication. "
                    "Please log out under the following link and then retry the request.\n\n"
                    f"{logout_url}"
                )

                raise ReauthenticationRequiredError(logout_url)
            case AuthenticateAuthenticationErrorResponse():
                raise ClientAuthError(response.error_description)
            case UnknownErrorResponse():
                raise ClientAuthError(json.dumps(response.response))
            case AuthenticateSuccessResponse():
                self._update_token(response)

    def _poll_for_tokens(
        self, device_code: str, expires_in: int = 300, interval: int = 5
    ) -> Generator[httpx.Request, httpx.Response, AuthenticateSuccessResponse]:
        """Poll for authentication tokens using device code flow.

        Args:
            device_code: The device code from the initial auth request
            expires_in: Timeout in seconds (default 300)
            interval: Polling interval in seconds (default 5)

        Returns:
            AuthenticateSuccessResponse: access and refresh tokens

        Raises:
            Exception: If polling for access/refresh tokens fails or times out
        """
        start_time = time.monotonic()

        while True:
            # Check timeout
            if time.monotonic() - start_time > expires_in:
                raise ClientAuthError("Authentication timed out")

            try:
                refresh_data = {
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "organization_id": self.force_org_id,
                }
                response = yield from self._authenticate(refresh_data)

            except httpx.TimeoutException as e:
                raise ClientAuthError("Authentication timed out") from e

            match response:
                case AuthenticateSuccessResponse():
                    return response
                case AuthenticateAuthenticationErrorResponse(error="authorization_pending"):
                    time.sleep(interval)
                case AuthenticateAuthenticationErrorResponse(error="slow_down"):
                    interval += 1
                case AuthenticateAuthenticationErrorResponse():
                    raise ClientAuthError(response.error_description)
                case UnknownErrorResponse():
                    raise ClientAuthError(json.dumps(response.response))

    def _start_device_flow(self) -> Generator[httpx.Request, httpx.Response, None]:
        device_auth_http_response: httpx.Response = yield httpx.Request(
            method="POST",
            url=f"{self.auth_base_url}/user_management/authorize/device",
            json={
                "client_id": self.client_id,
            },
            headers={"user-agent": self.user_agent or "unknown"},
        )
        device_auth_http_response.read()
        device_auth_http_response.raise_for_status()
        device_auth_response = DeviceAuthResponse.model_validate(device_auth_http_response.json())

        print(f"""
Please click the following URL to complete authentication

{device_auth_response.verification_uri_complete}

and verify that the code matches: {device_auth_response.user_code}
""")

        # Poll for tokens using the device code
        token_data = yield from self._poll_for_tokens(
            device_code=device_auth_response.device_code,
            expires_in=device_auth_response.expires_in,
            interval=device_auth_response.interval,
        )
        self._update_token(token_data)

    def _check_auth(self) -> Generator[httpx.Request, httpx.Response, None | CheckAuthResponse]:
        if self.cradle_api_base_url is None or self.workspace is None or self.access_token is None:
            return None

        needs_reauth_response: httpx.Response = yield httpx.Request(
            method="GET",
            url=f"{self.cradle_api_base_url}/auth:checkAuth",
            params={"workspace": self.workspace},
            headers={"Authorization": f"Bearer ca_{self.access_token}", "User-Agent": self.user_agent or "unknown"},
        )

        needs_reauth_response.read()
        needs_reauth_response.raise_for_status()
        return CheckAuthResponseAdapter.validate_python(needs_reauth_response.json())

    def auth_flow(self, request):
        if not self.access_token:
            yield from self._start_device_flow()

        # If we loaded the token from keyring, the access_token is almost certainly expired,
        # so we need to refresh it *before* hitting the checkAuth endpoint, which is authenticated
        # otherwise we get a 403.
        if self._needs_refresh():
            yield from self._refresh_token()

        # Only check for reauth once - the requested workspace that this client is constructed with
        # will not change, so we won't need to check if we need to reauth to a different workspace/org
        # more than once
        if not self.checked_for_reauth:
            check_auth_response = yield from self._check_auth()
            # can_reauth=True means that we are a member of the workspace we want to access, but need to reauthorize
            # our access_token to the correct org
            if check_auth_response and check_auth_response.authorized == False and check_auth_response.can_reauth:  # noqa: E712
                # This will force _refresh_token to request access to the correct org
                self.force_org_id = check_auth_response.org_id

            self.checked_for_reauth = True

        # After checking if we need to reauth, this will fire if we need to re-auth the token to a different org
        # from the one it was issued for.
        if self._needs_refresh():
            yield from self._refresh_token()

        request.headers["Authorization"] = f"Bearer ca_{self.access_token}"
        yield request

    def suggest_logout(self, workspace: str) -> None:  # noqa: ARG002 - might use workspace in the future
        """Print logout URL."""
        logout_url = self.logout_url
        if logout_url is None:
            raise ClientAuthError("No session ID available to log out.")

        # Don't clear token in case this is caused by fetching a workspace immediately after
        # creating it.
        #
        # Don't clear keyring in case the user decides to recreate the client with a different
        # workspace name.

        # Reset this check in case we just created a workspace and now need to auth to it
        self.checked_for_reauth = False

        message = (
            f'Authorized workspace "{self.authorized_workspace_id}" does not match requested workspace "{self.workspace}"\n'
            f"If you believe this is an error, you can log out of this session at {logout_url} and then try the request again."
        )
        raise ClientError(403, message, [])
