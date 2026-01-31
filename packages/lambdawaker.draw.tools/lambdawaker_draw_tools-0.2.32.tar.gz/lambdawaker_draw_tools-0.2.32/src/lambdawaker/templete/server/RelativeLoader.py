import os
from pathlib import PurePosixPath

import jinja2
from jinja2 import FileSystemLoader


class RelativeLoader(FileSystemLoader):
    def get_source(self, environment, template):
        # template may be like "../partials/header.html.j2"
        print(">>>")
        return super().get_source(environment, template)

    def join_path(self, template, parent):
        # parent = current template path
        parent_path = PurePosixPath(parent).parent

        print("<<<", str(parent_path / template))
        return str(parent_path / template)


class RelativeEnvironment(jinja2.Environment):
    """Override join_path() to enable relative template paths."""

    def join_path(self, template, parent):
        return os.path.join(os.path.dirname(parent), template).replace("\\", "/")
