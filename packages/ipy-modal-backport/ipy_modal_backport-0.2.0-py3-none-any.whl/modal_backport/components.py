import typing_extensions as typing
import interactions as ipy
from interactions.models.discord.components import SelectDefaultValues
import uuid
import discord_typings

__all__ = (
    "BaseSelectMenu",
    "ChannelSelectMenu",
    "DefaultableSelectMenu",
    "MentionableSelectMenu",
    "RoleSelectMenu",
    "StringSelectMenu",
    "UserSelectMenu",
)


class BaseSelectMenu(ipy.InteractiveComponent):
    """
    Represents a select menu component

    Attributes:
        custom_id str: A developer-defined identifier for the button, max 100 characters.
        placeholder str: The custom placeholder text to show if nothing is selected, max 100 characters.
        min_values Optional[int]: The minimum number of items that must be chosen. (default 1, min 0, max 25)
        max_values Optional[int]: The maximum number of items that can be chosen. (default 1, max 25)
        disabled bool: Disable the select and make it not intractable, default false.
        type Union[ComponentType, int]: The type of component, as defined by discord. This cannot be modified.
        required bool: Whether this select menu is required to be filled out or not in modals.

    """

    def __init__(
        self,
        *,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        custom_id: str | None = None,
        disabled: bool = False,
        required: bool = True,
    ) -> None:
        self.custom_id: str = custom_id or str(uuid.uuid4())
        self.placeholder: str | None = placeholder
        self.min_values: int = min_values
        self.max_values: int = max_values
        self.disabled: bool = disabled
        self.required: bool = required

        self.type: ipy.ComponentType = ipy.MISSING

    @classmethod
    def from_dict(
        cls, data: discord_typings.SelectMenuComponentData
    ) -> "BaseSelectMenu":
        return cls(
            placeholder=data.get("placeholder"),
            min_values=data["min_values"],
            max_values=data["max_values"],
            custom_id=data["custom_id"],
            disabled=data.get("disabled", False),
            required=data.get("required", True),
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type} custom_id={self.custom_id} placeholder={self.placeholder} min_values={self.min_values} max_values={self.max_values} disabled={self.disabled} required={self.required}>"

    def to_dict(self) -> discord_typings.SelectMenuComponentData:
        return {
            "type": self.type.value,  # type: ignore
            "custom_id": self.custom_id,
            "placeholder": self.placeholder,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "disabled": self.disabled,
            "required": self.required,
        }


class DefaultableSelectMenu(BaseSelectMenu):
    default_values: (
        list[
            typing.Union[
                "ipy.BaseUser",
                "ipy.Role",
                "ipy.BaseChannel",
                "ipy.Member",
                SelectDefaultValues,
            ]
        ]
        | None
    ) = None

    def __init__(
        self,
        defaults: (
            list[
                typing.Union[
                    "ipy.BaseUser",
                    "ipy.Role",
                    "ipy.BaseChannel",
                    "ipy.Member",
                    SelectDefaultValues,
                ]
            ]
            | None
        ) = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.default_values = defaults

    def add_default_value(
        self,
        value: typing.Union[
            "ipy.BaseUser",
            "ipy.Role",
            "ipy.BaseChannel",
            "ipy.Member",
            SelectDefaultValues,
        ],
    ) -> None:
        if self.default_values is None:
            self.default_values = []
        self.default_values.append(value)

    def to_dict(self) -> discord_typings.SelectMenuComponentData:
        data = super().to_dict()
        if self.default_values is not None:
            data["default_values"] = [  # type: ignore # waiting on discord typings to update
                (
                    value.to_dict()
                    if isinstance(value, SelectDefaultValues)
                    else SelectDefaultValues.from_object(value).to_dict()
                )
                for value in self.default_values
            ]

        # Discord handles the type checking, no need to do it here
        return data


class StringSelectMenu(BaseSelectMenu):
    """
    Represents a string select component.

    Attributes:
        options List[dict]: The choices in the select, max 25.
        custom_id str: A developer-defined identifier for the select, max 100 characters.
        placeholder str: The custom placeholder text to show if nothing is selected, max 100 characters.
        min_values Optional[int]: The minimum number of items that must be chosen. (default 1, min 0, max 25)
        max_values Optional[int]: The maximum number of items that can be chosen. (default 1, max 25)
        disabled bool: Disable the select and make it not intractable, default false.
        type Union[ComponentType, int]: The type of component, as defined by discord. This cannot be modified.
        required bool: Whether this select menu is required to be filled out or not in modals.

    """

    def __init__(
        self,
        *options: ipy.StringSelectOption
        | str
        | discord_typings.SelectMenuOptionData
        | list[ipy.StringSelectOption | str | discord_typings.SelectMenuOptionData],
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        custom_id: str | None = None,
        disabled: bool = False,
        required: bool = True,
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            custom_id=custom_id,
            disabled=disabled,
            required=required,
        )
        if (
            isinstance(options, (list, tuple))
            and len(options) == 1
            and isinstance(options[0], (list, tuple))
        ):
            # user passed in a list of options, expand it out
            options = options[0]

        self.options: list[ipy.StringSelectOption] = [
            ipy.StringSelectOption.converter(option) for option in options
        ]
        self.type: ipy.ComponentType = ipy.ComponentType.STRING_SELECT

    @classmethod
    def from_dict(
        cls, data: discord_typings.SelectMenuComponentData
    ) -> "StringSelectMenu":
        return cls(
            *data["options"],
            placeholder=data.get("placeholder"),
            min_values=data["min_values"],
            max_values=data["max_values"],
            custom_id=data["custom_id"],
            disabled=data.get("disabled", False),
            required=data.get("required", True),
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type} custom_id={self.custom_id} placeholder={self.placeholder} min_values={self.min_values} max_values={self.max_values} disabled={self.disabled} required={self.required} options={self.options}>"

    def to_dict(self) -> discord_typings.SelectMenuComponentData:
        return {
            **super().to_dict(),
            "options": [option.to_dict() for option in self.options],
        }


class UserSelectMenu(DefaultableSelectMenu):
    """
    Represents a user select component.

    Attributes:
        placeholder str: The custom placeholder text to show if nothing is selected, max 100 characters.
        min_values Optional[int]: The minimum number of items that must be chosen. (default 1, min 0, max 25)
        max_values Optional[int]: The maximum number of items that can be chosen. (default 1, max 25)
        custom_id str: A developer-defined identifier for the select, max 100 characters.
        default_values list[BaseUser, Member, SelectDefaultValues]: A list of default values to pre-select in the select.
        disabled bool: Disable the select and make it not intractable, default false.
        type Union[ComponentType, int]: The type of component, as defined by discord. This cannot be modified.
        required bool: Whether this select menu is required to be filled out or not in modals.

    """

    def __init__(
        self,
        *,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        custom_id: str | None = None,
        default_values: (
            list[
                typing.Union[
                    "ipy.BaseUser",
                    "ipy.Member",
                    SelectDefaultValues,
                ],
            ]
            | None
        ) = None,
        disabled: bool = False,
        required: bool = True,
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            custom_id=custom_id,
            disabled=disabled,
            required=required,
            defaults=default_values,
        )

        self.type: ipy.ComponentType = ipy.ComponentType.USER_SELECT


class RoleSelectMenu(DefaultableSelectMenu):
    """
    Represents a role select component.

    Attributes:
        placeholder str: The custom placeholder text to show if nothing is selected, max 100 characters.
        min_values Optional[int]: The minimum number of items that must be chosen. (default 1, min 0, max 25)
        max_values Optional[int]: The maximum number of items that can be chosen. (default 1, max 25)
        custom_id str: A developer-defined identifier for the select, max 100 characters.
        default_values list[Role, SelectDefaultValues]: A list of default values to pre-select in the select.
        disabled bool: Disable the select and make it not intractable, default false.
        type Union[ComponentType, int]: The type of component, as defined by discord. This cannot be modified.
        required bool: Whether this select menu is required to be filled out or not in modals.

    """

    def __init__(
        self,
        *,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        custom_id: str | None = None,
        disabled: bool = False,
        required: bool = True,
        default_values: (
            list[
                typing.Union[
                    "ipy.Role",
                    SelectDefaultValues,
                ],
            ]
            | None
        ) = None,
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            custom_id=custom_id,
            disabled=disabled,
            required=required,
            defaults=default_values,
        )

        self.type: ipy.ComponentType = ipy.ComponentType.ROLE_SELECT


class MentionableSelectMenu(DefaultableSelectMenu):
    """
    Represents a mentional select component, which includes users, roles, and channels.

    Attributes:
        placeholder str: The custom placeholder text to show if nothing is selected, max 100 characters.
        min_values Optional[int]: The minimum number of items that must be chosen. (default 1, min 0, max 25)
        max_values Optional[int]: The maximum number of items that can be chosen. (default 1, max 25)
        custom_id str: A developer-defined identifier for the select, max 100 characters.
        default_values list[BaseUser, Role, BaseChannel, Member, SelectDefaultValues]: A list of default values to pre-select in the select.
        disabled bool: Disable the select and make it not intractable, default false.
        type Union[ComponentType, int]: The type of component, as defined by discord. This cannot be modified.
        required bool: Whether this select menu is required to be filled out or not in modals.

    """

    def __init__(
        self,
        *,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        custom_id: str | None = None,
        disabled: bool = False,
        required: bool = True,
        default_values: (
            list[
                typing.Union[
                    "ipy.BaseUser",
                    "ipy.Role",
                    "ipy.BaseChannel",
                    "ipy.Member",
                    SelectDefaultValues,
                ],
            ]
            | None
        ) = None,
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            custom_id=custom_id,
            disabled=disabled,
            required=required,
            defaults=default_values,
        )

        self.type: ipy.ComponentType = ipy.ComponentType.MENTIONABLE_SELECT


class ChannelSelectMenu(DefaultableSelectMenu):
    """
    Represents a chanel select component.

    Attributes:
        placeholder str: The custom placeholder text to show if nothing is selected, max 100 characters.
        min_values Optional[int]: The minimum number of items that must be chosen. (default 1, min 0, max 25)
        max_values Optional[int]: The maximum number of items that can be chosen. (default 1, max 25)
        custom_id str: A developer-defined identifier for the select, max 100 characters.
        default_values list[BaseChannel, SelectDefaultValues]: A list of default values to pre-select in the select.
        disabled bool: Disable the select and make it not intractable, default false.
        type Union[ComponentType, int]: The type of component, as defined by discord. This cannot be modified.
        required bool: Whether this select menu is required to be filled out or not in modals.

    """

    def __init__(
        self,
        *,
        channel_types: list[ipy.ChannelType] | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        custom_id: str | None = None,
        disabled: bool = False,
        required: bool = True,
        default_values: (
            list[
                typing.Union[
                    "ipy.BaseChannel",
                    SelectDefaultValues,
                ],
            ]
            | None
        ) = None,
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            custom_id=custom_id,
            disabled=disabled,
            required=required,
            defaults=default_values,
        )

        self.channel_types: list[ipy.ChannelType] | None = channel_types or []
        self.type: ipy.ComponentType = ipy.ComponentType.CHANNEL_SELECT

    ChannelTypes: ipy.ChannelType = ipy.ChannelType

    @classmethod
    def from_dict(
        cls, data: discord_typings.SelectMenuComponentData
    ) -> "ChannelSelectMenu":
        return cls(
            placeholder=data.get("placeholder"),
            min_values=data["min_values"],
            max_values=data["max_values"],
            custom_id=data["custom_id"],
            disabled=data.get("disabled", False),
            required=data.get("required", True),
            channel_types=data.get("channel_types", []),
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type} custom_id={self.custom_id} placeholder={self.placeholder} min_values={self.min_values} max_values={self.max_values} disabled={self.disabled} required={self.required} channel_types={self.channel_types}>"

    def to_dict(self) -> discord_typings.SelectMenuComponentData:
        return {
            **super().to_dict(),
            "channel_types": self.channel_types,
        }
