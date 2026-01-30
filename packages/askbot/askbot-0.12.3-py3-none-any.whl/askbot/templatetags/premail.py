import premailer
from jinja2_simple_tags import ContainerTag

PREMAILER = premailer.Premailer()

class PremailerExtension(ContainerTag):
    tags = {'premailer'}

    def render(self, caller=None):
        content = caller()
        return PREMAILER.transform(content)
