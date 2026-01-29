from interactions.models.discord.enums import CursedIntEnum

__all__ = ("ComponentType",)


class ComponentType(CursedIntEnum):
    """The types of components supported by discord."""

    ACTION_ROW = 1
    """Container for other components"""
    BUTTON = 2
    """Button object"""
    STRING_SELECT = 3
    """Select menu for picking from text choices"""
    INPUT_TEXT = 4
    """Text input object"""
    USER_SELECT = 5
    """Select menu for picking from users"""
    ROLE_SELECT = 6
    """Select menu for picking from roles"""
    MENTIONABLE_SELECT = 7
    """Select menu for picking from mentionable objects"""
    CHANNEL_SELECT = 8
    """Select menu for picking from channels"""
    SECTION = 9
    """Section component for grouping together text and thumbnails/buttons"""
    TEXT_DISPLAY = 10
    """Text component for displaying text"""
    THUMBNAIL = 11
    """Thumbnail component for displaying a thumbnail for an image"""
    MEDIA_GALLERY = 12
    """Media gallery component for displaying multiple images"""
    FILE = 13
    """File component for uploading files"""
    SEPARATOR = 14
    """Separator component for visual separation"""
    CONTAINER = 17
    """Container component for grouping together other components"""
    LABEL = 18
    """Label component for modals"""
    FILE_UPLOAD = 19
    """File upload component for modals"""

    # TODO: this is hacky, is there a better way to do this?
    @staticmethod
    def v2_component_types() -> set["ComponentType"]:
        return {
            ComponentType.SECTION,
            ComponentType.TEXT_DISPLAY,
            ComponentType.THUMBNAIL,
            ComponentType.MEDIA_GALLERY,
            ComponentType.FILE,
            ComponentType.SEPARATOR,
            ComponentType.CONTAINER,
        }

    @property
    def v2_component(self) -> bool:
        """Whether this component is a v2 component."""
        return self.value in self.v2_component_types()
