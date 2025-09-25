
from typing import Optional, Self


class Embed:
    # TODO: Maybe refactor this with Image for a common Media class?
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        type = 'rich',
        timestamp: Optional[str] = None,
        color: Optional[int] = None
    ) -> None:
        self.title = title
        self.description = description
        self.url = url
        self.type = type
        self.timestamp = timestamp
        self.color = color
        self.footer: Optional[dict] = None
        self.image: Optional[dict] = None
        self.thumbnail: Optional[dict] = None
        self.video: Optional[dict] = None
        self.provider: Optional[dict] = None
        self.author: Optional[dict] = None
        self.fields: list[dict] = []

    def set_footer(self, text: str, icon_url: Optional[str], proxy_icon_url: Optional[str]) -> Self:
        self.footer = {'text': text}
        if icon_url is not None:
            self.footer['icon_url'] = icon_url
        if proxy_icon_url is not None:
            self.footer['proxy_icon_url'] = proxy_icon_url
        return self

    def set_video(
        self,
        url: Optional[str] = None,
        proxy_url: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Self:
        self.video = {}
        if url is not None:
            self.video['url'] = url
        if proxy_url is not None:
            self.video['proxy_url'] = proxy_url
        if width is not None:
            self.video['width'] = width
        if height is not None:
            self.video['height'] = height
        return self

    def set_image(
        self,
        url: str,
        proxy_url: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Self:
        self.image = {'url': url}
        if proxy_url is not None:
            self.image['proxy_url'] = proxy_url
        if width is not None:
            self.image['width'] = width
        if height is not None:
            self.image['height'] = height
        return self

    def set_thumbnail(
        self,
        url: str,
        proxy_url: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Self:
        self.thumbnail = {'url': url}
        if proxy_url is not None:
            self.thumbnail['proxy_url'] = proxy_url
        if width is not None:
            self.thumbnail['width'] = width
        if height is not None:
            self.thumbnail['height'] = height
        return self

    def set_provider(self, name: Optional[str] = None, url: Optional[str] = None) -> Self:
        self.provider = {}
        if name is not None:
            self.provider['name'] = name
        if url is not None:
            self.provider['url'] = url
        return self

    def set_author(
        self,
        name: str,
        url: Optional[str] = None,
        icon_url: Optional[str] = None,
        proxy_icon_url: Optional[str] = None
    ) -> Self:
        self.author = {'name': name}
        if url is not None:
            self.author['url'] = url
        if icon_url is not None:
            self.author['icon_url'] = icon_url
        if proxy_icon_url is not None:
            self.author['proxy_icon_url'] = proxy_icon_url
        return self

    def add_field(self, name: str, value: str, inline: Optional[bool] = None) -> Self:
        if len(self.fields) >= 25:
            return self
        new_field: dict = {'name': name, 'value': value}
        if inline is not None:
            new_field['inline'] = inline
        self.fields.append(new_field)
        return self

    def to_dict(self) -> dict:
        result: dict = {}
        if self.title is not None:
            result['title'] = self.title
        if self.type is not None:
            result['type'] = self.type
        if self.description is not None:
            result['description'] = self.description
        if self.url is not None:
            result['url'] = self.url
        if self.timestamp is not None:
            result['timestamp'] = self.timestamp
        if self.color is not None:
            result['color'] = self.color
        if self.image is not None:
            result['image'] = self.image
        if self.thumbnail is not None:
            result['thumbnail'] = self.thumbnail
        if self.video is not None:
            result['video'] = self.video
        if self.provider is not None:
            result['provider'] = self.provider
        if self.author is not None:
            result['author'] = self.author
        if len(self.fields) > 0:
            result['fields'] = self.fields
        return result
