import uuid
import typing_extensions as typing

import discord_typings
import interactions as ipy

import modal_backport.components as components
from modal_backport.enums import ComponentType

__all__ = (
    "FileUploadComponent",
    "LabelComponent",
    "Modal",
)


class FileUploadComponent(ipy.BaseComponent):
    """
    An interactive component that allows users to upload files in modals.

    Attributes:
        custom_id: A unique identifier for the component.
        min_value: The minimum number of files that can be uploaded.
        max_value: The maximum number of files that can be uploaded.
        required: Whether the file upload is required.

    """

    def __init__(
        self,
        custom_id: typing.Optional[str] = None,
        min_value: int = 1,
        max_value: int = 1,
        required: bool = True,
    ):
        self.custom_id = custom_id or str(uuid.uuid4())
        self.min_value = min_value
        self.max_value = max_value
        self.required = required
        self.type = ComponentType.FILE_UPLOAD

    def to_dict(self) -> dict:
        return ipy.utils.dict_filter_none(
            {
                "type": self.type,
                "custom_id": self.custom_id,
                "min_value": self.min_value,
                "max_value": self.max_value,
                "required": self.required,
            }
        )

    @classmethod
    def from_dict(cls, data: dict) -> typing.Self:
        return cls(
            custom_id=data.get("custom_id"),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            required=data.get("required", True),
        )


class LabelComponent(ipy.BaseComponent):
    """
    A top-level layout component that wraps modal components with text as a label and optional description.

    Attributes:
        label: The text label for the component.
        description: An optional description for the component.
        component: The component to be wrapped.
        type: The type of the component, always ComponentType.LABEL.

    """

    def __init__(
        self,
        *,
        label: str,
        description: typing.Optional[str] = None,
        component: (
            ipy.BaseSelectMenu
            | components.BaseSelectMenu
            | ipy.InputText
            | FileUploadComponent
        ),
    ):
        self.label = label
        self.component = component
        self.description = description
        self.type = ComponentType.LABEL

    def to_dict(self) -> dict:
        return ipy.utils.dict_filter_none(
            {
                "type": self.type,
                "label": self.label,
                "description": self.description,
                "component": (
                    self.component.to_dict()
                    if hasattr(self.component, "to_dict")
                    else self.component
                ),
            }
        )

    @classmethod
    def from_dict(cls, data: dict) -> typing.Self:
        return cls(
            label=data["label"],
            description=data.get("description"),
            component=ipy.BaseComponent.from_dict_factory(
                data["component"],
                alternate_mapping={
                    ComponentType.INPUT_TEXT: ipy.InputText,
                    ComponentType.CHANNEL_SELECT: components.ChannelSelectMenu,
                    ComponentType.STRING_SELECT: components.StringSelectMenu,
                    ComponentType.USER_SELECT: components.UserSelectMenu,
                    ComponentType.ROLE_SELECT: components.RoleSelectMenu,
                    ComponentType.MENTIONABLE_SELECT: components.MentionableSelectMenu,
                    ComponentType.FILE_UPLOAD: FileUploadComponent,
                },
            ),
        )


class Modal:
    def __init__(
        self,
        *components: ipy.InputText | LabelComponent,
        title: str,
        custom_id: typing.Optional[str] = None,
    ) -> None:
        self.title: str = title
        self.components: list[ipy.InputText | LabelComponent] = list(components)
        self.custom_id: str = custom_id or str(uuid.uuid4())

        self.type = ipy.CallbackType.MODAL

    def to_dict(self) -> discord_typings.ModalInteractionData:
        dict_components: list[dict] = []

        for component in self.components:
            if isinstance(component, ipy.InputText):
                dict_components.append(
                    {
                        "type": ComponentType.ACTION_ROW,
                        "components": [component.to_dict()],
                    }
                )
            elif isinstance(component, LabelComponent):
                dict_components.append(component.to_dict())
            else:
                # backwards compatibility behavior, remove in v6
                dict_components.append(
                    {
                        "type": ComponentType.ACTION_ROW,
                        "components": [component],
                    }
                )

        return {
            "type": self.type,
            "data": {
                "title": self.title,
                "custom_id": self.custom_id,
                "components": dict_components,
            },
        }

    def add_components(self, *components: ipy.InputText | LabelComponent) -> None:
        """
        Add components to the modal.

        Args:
            *components: The components to add.

        """
        if len(components) == 1 and isinstance(components[0], (list, tuple)):
            components = components[0]
        self.components.extend(components)
