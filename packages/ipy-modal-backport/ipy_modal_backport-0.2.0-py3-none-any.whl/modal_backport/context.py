import re

import interactions as ipy
import typing_extensions as typing

from modal_backport.enums import ComponentType

__all__ = ("ModalContext", "UpdatedModalContextMixin")


class UpdatedModalContextMixin:
    responses: dict[str, typing.Any]
    """The responses of the modal. The key is the `custom_id` of the component."""

    @classmethod
    def from_dict(  # noqa: C901
        cls, client: "ipy.ClientT", payload: dict
    ) -> typing.Self:
        instance = ipy.InteractionContext.from_dict(client, payload)
        instance.responses = {}

        for component in payload["data"]["components"]:
            if component["type"] == ComponentType.ACTION_ROW:
                instance.responses[component["components"][0]["custom_id"]] = component[
                    "components"
                ][0]["value"]
            elif component["type"] == ComponentType.LABEL:
                held_component = component["component"]

                if held_component["type"] == ComponentType.INPUT_TEXT:
                    instance.responses[held_component["custom_id"]] = held_component[
                        "value"
                    ]
                elif held_component["type"] == ComponentType.STRING_SELECT:
                    instance.responses[held_component["custom_id"]] = held_component[
                        "values"
                    ]
                elif held_component["type"] in (
                    ComponentType.USER_SELECT,
                    ComponentType.CHANNEL_SELECT,
                    ComponentType.ROLE_SELECT,
                    ComponentType.MENTIONABLE_SELECT,
                ):
                    searches = {
                        "users": held_component["type"]
                        in (
                            ComponentType.USER_SELECT,
                            ComponentType.MENTIONABLE_SELECT,
                        ),
                        "members": instance.guild_id
                        and held_component["type"]
                        in (
                            ComponentType.USER_SELECT,
                            ComponentType.MENTIONABLE_SELECT,
                        ),
                        "channels": held_component["type"]
                        in (
                            ComponentType.CHANNEL_SELECT,
                            ComponentType.MENTIONABLE_SELECT,
                        ),
                        "roles": instance.guild_id
                        and held_component["type"]
                        in (
                            ComponentType.ROLE_SELECT,
                            ComponentType.MENTIONABLE_SELECT,
                        ),
                    }

                    values = held_component["values"]

                    for i, value in enumerate(held_component["values"]):
                        if re.match(r"\d{17,}", value):
                            key = ipy.Snowflake(value)

                            if resolved := instance.resolved.get(key):
                                values[i] = resolved
                            elif searches["members"] and (
                                member := instance.client.cache.get_member(
                                    instance.guild_id, key
                                )
                            ):
                                values[i] = member
                            elif searches["users"] and (
                                user := instance.client.cache.get_user(key)
                            ):
                                values[i] = user
                            elif searches["roles"] and (
                                role := instance.client.cache.get_role(key)
                            ):
                                values[i] = role
                            elif searches["channels"] and (
                                channel := instance.client.cache.get_channel(key)
                            ):
                                values[i] = channel

                    instance.responses[held_component["custom_id"]] = values
                elif held_component["type"] == ComponentType.FILE_UPLOAD:
                    values = held_component["values"]

                    for i, value in enumerate(held_component["values"]):
                        if re.match(r"\d{17,}", value):
                            if resolved := instance.resolved.get(ipy.Snowflake(value)):
                                values[i] = resolved

                    instance.responses[held_component["custom_id"]] = values
                else:
                    raise ValueError(
                        f"Unknown component type in modal: {held_component['type']}"
                    )

        instance.kwargs = instance.responses
        instance.custom_id = payload["data"]["custom_id"]
        instance.edit_origin = False
        return instance


class ModalContext(UpdatedModalContextMixin, ipy.ModalContext[ipy.ClientT]):
    pass
