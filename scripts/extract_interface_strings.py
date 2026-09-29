"""List static assessment-page text and safe display attributes for translation."""
from html.parser import HTMLParser
from pathlib import Path


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.strings = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.stack.append((tag, values.get("id", "")))
        for key in ("placeholder", "aria-label", "title"):
            if values.get(key):
                self.strings.append(values[key].strip())

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        if any(tag in {"script", "style"} or element_id == "app-language" for tag, element_id in self.stack):
            return
        value = data.strip()
        if value and any(character.isalpha() for character in value):
            self.strings.append(value)


def source_interface_strings():
    parser = Collector()
    parser.feed((Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8"))
    return list(dict.fromkeys(parser.strings))


if __name__ == "__main__":
    for item in source_interface_strings():
        print(item)
