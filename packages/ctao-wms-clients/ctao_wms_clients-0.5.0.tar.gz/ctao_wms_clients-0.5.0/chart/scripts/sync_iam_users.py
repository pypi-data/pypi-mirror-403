"""Script for creating users, groups and VOs in DiracX configuration."""

import json
import logging
import os

import requests
import yaml
from DIRAC.ConfigurationSystem.Client.Config import gConfig
from DIRAC.ConfigurationSystem.Client.CSAPI import CSAPI
from DIRAC.Core.Base import Script
from diracx.cli.internal.config import (
    add_group,
    add_user,
    add_vo,
    get_config_from_repo_path,
    get_repo_path,
    update_config_and_commit,
)
from diracx.core.config.schema import Config as CSConfig
from pydantic import BaseModel, RootModel, field_validator

Script.parseCommandLine()

args = Script.getPositionalArgs()


class Client(BaseModel):
    """Client to create/update."""

    client_id: str | None = None
    client_secret: str | None = None
    client_name: str
    grant_types: list[str] | None = []
    scopes: list[str] | None = []
    redirect_uris: list[str] | None = []

    @field_validator("redirect_uris", mode="before")
    @classmethod
    def set_redirect_uris(cls, v, values):
        """Set redirect URIs based on grant types."""
        # redirect_uris is required if grant_types contains "authorization_code" or "device_code"
        grant_types = values.data.get("grant_types", []) if values.data else []
        if not v and (
            "authorization_code" in grant_types
            or "urn:ietf:params:oauth:grant-type:device_code" in grant_types
        ):
            raise ValueError("redirect_uris is required")
        return v


class User(BaseModel):
    """User to create."""

    username: str
    password: str
    given_name: str | None = None
    family_name: str | None = None
    email: str | None = None
    role: str | None = None
    subject_dn: str | None = None
    groups: list[str] | None = []
    cert: dict | None = None

    @field_validator("given_name", mode="before")
    @classmethod
    def set_given_name(cls, v, values):
        """Use the username to set the given_name if it's not provided."""
        if v is None and values.data and "username" in values.data:
            return values.data["username"].capitalize()
        return v

    @field_validator("family_name", mode="before")
    @classmethod
    def set_family_name(cls, v):
        """Set the family_name to an empty string if it's not provided."""
        return v or ""


class InitialClient(Client):
    """Initial client used to get an admin token and modify the IAM instance."""

    id: str
    grant_types: list[str] | None = ["client_credentials"]
    scope: list[str] | None = [
        "scim:read",
        "scim:write",
        "iam:admin.read",
        "iam:admin.write",
    ]


class Group(RootModel[dict[str, list[str]]]):
    """Group to create."""


class Config(BaseModel):
    """IAM helm values config."""

    issuer: str
    admin_user: User | None = None
    initial_client: InitialClient | None = None
    users: list[User] | None = []
    clients: list[Client] | None = []
    groups: dict[str, Group] | None = {}


def _extract_config(config_path: str):
    """Extract yaml config from file."""
    try:
        # Load and parse the configuration using Pydantic
        with open(config_path) as file:
            config_data = yaml.safe_load(file)
        return Config.model_validate(config_data)
    except FileNotFoundError:
        logging.error("Config file not found")
        raise RuntimeError("Config file not found")
    except ValueError as e:
        logging.error("Error parsing config file: %s", e)
        raise RuntimeError(f"Error parsing config file: {e}")
    except Exception as e:
        logging.error("Error parsing config file: %s", e)
        raise RuntimeError(f"Error parsing config file: {e}")


def _get_iam_token(issuer: str, client: Client) -> dict:
    """Get a token using the client credentials flow."""
    query = os.path.join(issuer, "token")
    params = {"grant_type": "client_credentials"}

    response = requests.post(
        query,
        auth=(client.client_id, client.client_secret),
        params=params,
        timeout=5,
    )
    if not response.ok:
        logging.error(
            "Failed to get an admin token: %s %s", response.status_code, response.reason
        )

        raise RuntimeError("Failed to get an admin token")
    return response.json()


def _update_iam_client(
    issuer: str,
    admin_access_token: str,
    client: Client,
) -> dict:
    """Update an IAM client."""
    headers = {
        "Authorization": f"Bearer {admin_access_token}",
        "Content-Type": "application/json",
    }
    if client.client_id:
        logging.info(
            "Client %s seems to exist, let's try to update it", {client.client_name}
        )

        # Get the configuration of the client
        query = os.path.join(issuer, "iam/api/clients", client.client_id)
        response = requests.get(
            query,
            headers=headers,
            timeout=5,
        )
        if not response.ok:
            logging.error(
                "Failed to get config for client %s: %s %s",
                client.client_name,
                response.status_code,
                response.reason,
            )
            raise RuntimeError(f"Failed to get config for client {client.client_name}")

        # Update the configuration with the provided values
        client_config = response.json()
        client_config["client_name"] = client.client_name
        client_config["scope"] = " ".join(client.scopes)
        client_config["grant_types"] = client.grant_types
        client_config["redirect_uris"] = client.redirect_uris
        client_config["code_challenge_method"] = "S256"
        if not client.client_secret:
            client_config["token_endpoint_auth_method"] = "none"

        # Update the client
        response = requests.put(
            query,
            headers=headers,
            data=json.dumps(client_config),
            timeout=5,
        )
        if not response.ok:
            logging.error(
                "Failed to update config for client %s: %s %s",
                client.client_name,
                response.status_code,
                response.reason,
            )
            raise RuntimeError(
                f"Failed to update config for client {client.client_name}"
            )
        return response.json()


def get_iam_users(token: str, issuer: str, start_index: int) -> dict:
    """Retrieve users and ids from IAM api."""
    query = os.path.join(issuer, "scim/Users")
    #  "filter": f"userName eq \"{user_name}\"" doesn't seems to work
    params = {"attributes": "userName", "startIndex": start_index}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.get(
        query,
        headers=headers,
        params=params,
        timeout=5,
    )
    if not response.ok:
        logging.error(
            "Failed to query scim/Users %s %s", response.status_code, response.reason
        )

        raise RuntimeError(
            f"Failed to query scim/Users: {response.status_code} { response.reason}"
        )
    return response.json()


def find_user_ids(token: str, iam_config: Config, users: set, max_index: int = 400):
    """Find IAM users id."""
    user_ids = {}
    for start_index in range(1, max_index, 100):
        iam_users = get_iam_users(token, iam_config.issuer, start_index)
        if iam_users["Resources"]:
            for resource in iam_users["Resources"]:
                if resource["userName"] in users:
                    user_ids[resource["userName"]] = resource["id"]
        else:
            logging.warning("get_iam_users returned no resources: %s", iam_users)
    if not user_ids:
        raise RuntimeError(f"Users {users} not found in IAM")
    return user_ids


def list_all_clients(issuer: str, access_token: str) -> dict:
    """List all clients (requires admin privileges)."""
    clients_url = f"{issuer.rstrip('/')}/iam/api/clients"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params = {"count": 25}
    response = requests.get(clients_url, headers=headers, params=params, timeout=10)

    if not response.ok:
        logging.error(
            "Failed to list clients: %s %s", response.status_code, response.reason
        )
        raise RuntimeError(
            f"Failed to list clients: {response.status_code}, reason: {response.reason}"
        )

    return response.json()


def find_client_by_id(
    issuer: str, access_token: str, client_config: Client
) -> dict | None:
    """Find a client by name."""
    client_response = list_all_clients(issuer, access_token)
    if not client_response["Resources"]:
        logging.warning("Client response do not contain Resources: %s", client_response)
        return None

    for client in client_response["Resources"]:
        if client.get("client_id") == client_config.client_id:
            return client


def get_groups_infos() -> dict:
    """Extract group infos from DIRAC api."""
    cs_api = CSAPI()
    res_group_list = cs_api.listGroups()
    if res_group_list["OK"]:
        group_list = res_group_list["Value"]
    else:
        logging.warning(res_group_list)
        exit(1)
    groups_infos = {}
    for group in group_list:
        res_group_info = cs_api.describeGroups(group)
        if res_group_info["OK"]:
            groups_infos.update(res_group_info["Value"])
        else:
            logging.warning(res_group_info)
    return groups_infos


def get_registry_vo():
    """Extract VOs from DIRAC registry."""
    res_vos = gConfig.getSections("/Registry/VO")
    if res_vos["OK"]:
        return res_vos["Value"]
    else:
        logging.warning(res_vos)


def get_default_group():
    """Extract default_group from DIRAC registry."""
    default_group = gConfig.getValue("/Registry/DefaultGroup")
    if default_group:
        return default_group
    else:
        logging.warning(default_group)


def set_idp_client_id(vo: str, client_id: str):
    """Set the IdP ClientID value in DIRAC cfg."""
    cs_api = CSAPI()
    res_modify = cs_api.modifyValue(
        f"/DiracX/CsSync/VOs/{vo}/IdP/ClientID", str(client_id)
    )
    if res_modify["OK"]:
        res_commit = cs_api.commit()
        if res_commit["OK"]:
            logging.info("DiracX IdP client ID set.")
        else:
            logging.warning("Did not commit: %s", res_commit)
    else:
        logging.warning("Cannot modify ClientID value: %s", res_modify)


def set_user_subjects(vo: str, users: dict):
    """Update DIRAC DiracX UserSubjects."""
    cs_api = CSAPI()
    for user_name, user_subject in users.items():
        res_modify = cs_api.modifyValue(
            f"/DiracX/CsSync/VOs/{vo}/UserSubjects/{user_name}", user_subject
        )
        if res_modify["OK"]:
            res_commit = cs_api.commit()
            if res_commit["OK"]:
                logging.info("UserSubject set for user %s.", user_name)
            else:
                logging.warning("Did not commit: %s", res_commit)
        else:
            logging.warning("Cannot modify %s subject: %s", user_name, res_modify)


def update_dirac_diracx_section(registry_infos: dict, client_id: str):
    """Update DIRAC DiracX section with registry information."""
    for vo, infos in registry_infos.items():
        set_idp_client_id(vo, client_id)
        set_user_subjects(vo, infos.get("users"))


def delete_registry_section(config_repo):
    """Delete DiracX cfg registry section."""
    repo_path = get_repo_path(config_repo)
    config = get_config_from_repo_path(repo_path)

    if config.Registry:
        config = CSConfig(**config.model_dump(exclude={"Registry"}), Registry={})
        update_config_and_commit(
            repo_path=repo_path,
            config=config,
            message="Empty Registry section.",
        )
        logging.info("Successfully empty Registry section in Diracx CS")


def _add_vo(client_id, config_repo, issuer, default_group, vo):
    try:
        add_vo(
            config_repo=config_repo,
            vo=vo,
            default_group=default_group,
            idp_url=issuer,
            idp_client_id=client_id,
        )
    except Exception as e:
        if "already exists" in str(e):
            logging.warning("VO %s already exists, skipping creation", vo)
        else:
            logging.warning("Pass adding vo step. Error: %s", e)


def _add_group(config_repo, registry, users, vo):
    user_group_map = {}
    for group_name, group_values in registry["groups"].items():
        if group_name == registry["default_group"]:
            continue
        properties = group_values["Properties"]
        for user in users:
            if user in group_values["Users"]:
                user_group_map.setdefault(user, []).append(group_name)

        logging.info(
            "Creating group %s , with properties %s in DiracX cfg",
            group_name,
            properties,
        )
        try:
            add_group(
                config_repo=config_repo,
                vo=vo,
                group=group_name,
                properties=properties,
            )
            logging.info("group %s created, with properties %s", group_name, properties)
        except Exception as e:
            if "already exists" in str(e):
                logging.warning(
                    "group %s already exists, skipping creation", group_name
                )
            else:
                continue

    return user_group_map


def _add_user(users, user_group_map, config_repo, vo):
    for username, sub in users.items():
        logging.info("Creating user %s in DiracX cfg", username)
        if username in user_group_map:
            try:
                add_user(
                    config_repo=config_repo,
                    vo=vo,
                    groups=user_group_map[username],
                    sub=sub,
                    preferred_username=username,
                )
                logging.info("user %s created", username)
            except Exception as e:
                if "already exists" in str(e):
                    logging.warning(
                        "user %s already exists, skipping creation", username
                    )
                else:
                    continue


def update_diracx_cs(
    registry_config: dict,
    iam_config: Config,
    users: dict,
    client_id: str,
    config_repo: str,
):
    """Add vo, users and groups to the DiracX cfg."""
    logging.info("Updating DiracX config")
    # We first need to reset the Registry section in DiracX CS
    # otherwise we can't set the IdP client id using add_vo
    delete_registry_section(config_repo)
    for vo, registry in registry_config.items():
        _add_vo(
            client_id, config_repo, iam_config.issuer, registry["default_group"], vo
        )

        user_group_map = _add_group(config_repo, registry, users, vo)

        _add_user(users, user_group_map, config_repo, vo)


def create_users():
    """Create VO, Users and Groups in DiracX configuration."""
    iam_config = _extract_config(os.getenv("IAM_CONFIG_PATH"))
    if iam_config.clients and len(iam_config.clients) == 1:
        client_config = iam_config.clients[0]
    else:
        raise NotImplementedError("Multiple Clients config.")
    token = _get_iam_token(iam_config.issuer, client_config)
    admin_access_token = token.get("access_token")
    _update_iam_client(iam_config.issuer, admin_access_token, client_config)

    # We updated the client so we ask for a new token
    token = _get_iam_token(iam_config.issuer, client_config)
    admin_access_token = token.get("access_token")

    logging.info("Looking for client named: %s", client_config.client_name)
    client = find_client_by_id(iam_config.issuer, admin_access_token, client_config)
    if client:
        logging.info(
            "Found client: %s (ID: %s)", client["client_name"], client["client_id"]
        )
    else:
        logging.warning("Client named '%s' not found", client_config.client_name)
        raise RuntimeError(f"Client named '{client_config.client_name}' not found")

    groups_infos = get_groups_infos()
    users = {user for info in groups_infos.values() for user in info["Users"]}

    users_infos = find_user_ids(admin_access_token, iam_config, users)
    vos = get_registry_vo()
    registry_infos = {}
    default_group = get_default_group()

    for vo in vos:
        registry_infos[vo] = {
            "default_group": default_group,
            "users": users_infos,
            "groups": groups_infos,
        }

    update_diracx_cs(
        registry_config=registry_infos,
        iam_config=iam_config,
        users=users_infos,
        client_id=client["client_id"],
        config_repo=os.getenv("DIRACX_CS_PATH"),
    )
    update_dirac_diracx_section(registry_infos, client["client_id"])


if __name__ == "__main__":
    create_users()
