"""Sphinx directives."""

from pathlib import Path, PurePosixPath

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Figure, Image

from sphinx_thumb_image.lib import ThumbNodeRequest, format_replacement


class ThumbCommon(Image):
    """Common methods for both thumb image/figure subclassed directives."""

    __option_spec = {}
    __option_spec["resize-width"] = lambda arg: directives.nonnegative_int(arg.replace("px", ""))
    __option_spec["resize-height"] = __option_spec["resize-width"]
    __option_spec["no-resize"] = directives.flag
    __option_spec["target-format"] = directives.flag
    __option_spec["no-target-format"] = directives.flag
    __option_spec["no-default-target"] = directives.flag

    def __default_target(self):
        """Apply the thumb_image_default_target config."""
        if "target" in self.options:
            return
        if "no-default-target" in self.options:
            return
        config = self.state.document.settings.env.config
        default_target = config["thumb_image_default_target"]
        if default_target is not None:
            self.options["target"] = default_target

    def __format_target(self):
        """Apply the "target-format" option."""
        if "target" not in self.options:
            return
        if "no-target-format" in self.options:
            return
        config = self.state.document.settings.env.config
        if "target-format" not in self.options and not config["thumb_image_target_format"]:
            return
        # Build substitutions.
        doctree_source = Path(self.state.document["source"])
        env = self.state.document.settings.env
        subdir = PurePosixPath(doctree_source.parent.relative_to(env.srcdir).as_posix())
        substitutions = {
            "raw_path": self.arguments[0],
            "fullsize_path": str(subdir / self.arguments[0]),
        }
        substitutions.update(config["thumb_image_target_format_substitutions"])
        # Format.
        target = self.options["target"]
        for key, value in substitutions.items():
            if callable(value):
                kwargs = {
                    "self": self,
                    "substitutions": substitutions,
                    "target": target,
                    "env": env,
                }
                replacement = value(**kwargs)
            else:
                replacement = value
            target = format_replacement(target, key, replacement)
        if target == self.options["target"]:
            self.state.document.reporter.warning('no subtitutions made by "target-format" in "target"', line=self.lineno)
        else:
            self.options["target"] = target

    def __add_request(self, sphinx_nodes: list[nodes.Element]) -> list[nodes.Element]:
        """Build and add a ThumbRequest to the image node.

        :param sphinx_nodes: List of nodes returned by super().run(), one of which contains an image node to be modified.

        :return: The same node list as the input with an annotated image node.
        """
        config = self.state.document.settings.env.config

        if "no-resize" in self.options:
            request = ThumbNodeRequest(
                no_resize=True,
            )
        elif "resize-width" in self.options or "resize-height" in self.options:
            # Read width/height from directive options first.
            request = ThumbNodeRequest(
                width=self.options.get("resize-width", None),
                height=self.options.get("resize-height", None),
            )
        else:
            # Read width/height from Sphinx config.
            thumb_image_resize_width = config["thumb_image_resize_width"]
            thumb_image_resize_height = config["thumb_image_resize_height"]
            if thumb_image_resize_width is not None or thumb_image_resize_height is not None:
                request = ThumbNodeRequest(
                    width=thumb_image_resize_width,
                    height=thumb_image_resize_height,
                )
            else:
                # User has not provided the width/height.
                raise self.error('Error in %r directive: "resize-width" option is missing.' % self.name)

        # Add request to the node.
        for node in sphinx_nodes:
            for image_node in node.findall(nodes.image):
                image_node[request.KEY] = request

        return sphinx_nodes


class ThumbImage(ThumbCommon):
    """Thumbnail image directive."""

    option_spec = Image.option_spec | ThumbCommon._ThumbCommon__option_spec

    def run(self) -> list[nodes.Element]:
        """Entrypoint."""
        self._ThumbCommon__default_target()
        self._ThumbCommon__format_target()
        return self._ThumbCommon__add_request(super().run())


class ThumbFigure(Figure, ThumbCommon):
    """Thumbnail figure directive."""

    option_spec = Figure.option_spec | ThumbCommon._ThumbCommon__option_spec

    def run(self) -> list[nodes.Element]:
        """Entrypoint."""
        self._ThumbCommon__default_target()
        self._ThumbCommon__format_target()
        return self._ThumbCommon__add_request(super().run())
