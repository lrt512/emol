"""Template tags for checking feature switch status in templates."""

from django import template
from feature_switches.helpers import is_enabled

register = template.Library()


@register.simple_tag
def switch_enabled(switch_name: str) -> bool:
    """Check if a feature switch is enabled.

    Usage in templates:
        {% load feature_switches %}
        {% switch_enabled "pin_required" as pin_required %}
        {% if pin_required %}
            ... PIN required content ...
        {% endif %}

    Args:
        switch_name: The name of the switch to check

    Returns:
        True if enabled, False otherwise
    """
    return is_enabled(switch_name)


class IfSwitchNode(template.Node):
    """Template node for conditional rendering based on feature switch."""

    def __init__(
        self,
        switch_name: str,
        nodelist_true: template.NodeList,
        nodelist_false: template.NodeList,
    ):
        self.switch_name = switch_name
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context) -> str:
        switch_name = (
            self.switch_name.resolve(context)
            if hasattr(self.switch_name, "resolve")
            else self.switch_name
        )
        if is_enabled(switch_name):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


@register.tag
def if_switch(parser, token):
    """Conditional block tag based on feature switch status.

    Usage in templates:
        {% load feature_switches %}
        {% if_switch "pin_required" %}
            ... shown when switch is ON ...
        {% else %}
            ... shown when switch is OFF ...
        {% endif_switch %}

    Args:
        parser: Template parser
        token: Template token

    Returns:
        IfSwitchNode for rendering
    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(
            f"'{bits[0]}' tag requires exactly one argument (switch name)"
        )

    switch_name = bits[1]
    if switch_name[0] in ('"', "'") and switch_name[-1] == switch_name[0]:
        switch_name = switch_name[1:-1]

    nodelist_true = parser.parse(("else", "endif_switch"))
    token = parser.next_token()

    if token.contents == "else":
        nodelist_false = parser.parse(("endif_switch",))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()

    return IfSwitchNode(switch_name, nodelist_true, nodelist_false)
