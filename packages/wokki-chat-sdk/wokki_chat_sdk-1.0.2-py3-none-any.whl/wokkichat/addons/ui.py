"""
.. include:: ../../subdocs/ui.md
"""

from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Component:
    """
    The base class for any component used in an embed.

    Do not create directly.
    """
    label: str = ""
    """
    The text displayed on the component.
    """
    id: str = "placeholder"
    """
    Custom id for the component.
    """
    color: Optional[str] = None
    """
    The hex color of the component's background.
    """
    text_color: Optional[str] = None
    """
    The hex color of the component's text.
    """
    disabled: bool = False
    """
    Whether the component (if button) is
    unclickable or not.
    """

    def to_dict(self) -> dict:
        """
        @private
        """
        return asdict(self)


@dataclass
class Button(Component):
    """
    A component that can have a callback.
    """
    type: str = "button"


@dataclass
class Link(Component):
    """
    A component that can open a page upon click.
    """
    url: str = "https://example.com/"
    type: str = "link"

    def to_dict(self) -> dict:
        """
        @private
        """
        data = super().to_dict()
        data["url"] = self.url
        return data
    

class Embed:
    """
    The main element for UIs.
    """

    title: str = ""
    """
    The text displayed on top of the embed
    """
    description: str = ""
    """
    The text displayed below the title.
    """
    color: Optional[str] = None
    """
    The hex color on the embed's left side.
    """
    footer: str = ""
    """
    The text displayed below the fields.
    """

    def __init__(self,
                 title: str = "", description: str = "",
                 color: Optional[str] = None, footer: str = ""):
        self.title = title
        self.description = description
        self.color = color
        self.footer = footer

        self._fields = []
        self._components = [[]]

    def add_field(self, name: str = "", value: str = "") -> None:
        self._fields.append({'name': name, 'value': value})

    def add_component(self, component: Component) -> None:
        row = self._components[-1]

        if len(row) >= 3:
            row = []
            self._components.append(row)

        row.append(component)

    def to_dict(self) -> dict:
        """
        @private
        """
        return {
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "fields": self._fields,
            "components": [
                [comp.to_dict() for comp in row]
                for row in self._components if row
            ],
            "footer": self.footer
        }
    
class View:
    """
    The holder for embeds.
    """
    def __init__(self):
        self._embeds = []

    def add_embed(self, embed: Embed):
        self._embeds.append(embed)

    def to_list(self) -> list:
        """
        @private
        """
        return [embed.to_dict() for embed in self._embeds]
    
__all__ = ['View', 'Embed', 'Link', 'Button', 'Component']