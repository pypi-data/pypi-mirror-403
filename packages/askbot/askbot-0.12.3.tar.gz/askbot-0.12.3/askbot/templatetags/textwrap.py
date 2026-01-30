import textwrap
from jinja2_simple_tags import ContainerTag

TEXT_WRAPPER = textwrap.TextWrapper()
DEFAULTS = {
    'width': 70,
    'break_long_words': True,
    'break_on_hyphens': True
}

class TextWrapExtension(ContainerTag):
    tags = {'textwrap'}

    def render(self, caller=None, **kwargs):
        content = caller()
        options = DEFAULTS.copy()
        options.update(kwargs)
        for key, value in options.items():
            if key == 'width':
                value = int(value)
            setattr(TEXT_WRAPPER, key, value)
        return TEXT_WRAPPER.fill(content)
