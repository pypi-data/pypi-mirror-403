from fasthtml.common import ft_hx


def _mdui_component(tag, *children, **kwargs):
    """Helper to create MDUI custom elements"""
    # ft_hx expects children as a tuple
    return ft_hx(tag, children, **kwargs)


def Div(*children, **kwargs):
    """
    Standard HTML Div element helper
    
    This is a convenience wrapper for creating div elements that works
    well with MDUI components, especially for grouping elements with slots.
    
    Examples:
        Div(slot="end")(Button("Click me"))
        Div(style="display: flex; gap: 8px;")(Button1, Button2)
    """
    return ft_hx("div", children, **kwargs)


def Button(text="", variant="filled", icon=None, end_icon=None, icon_slot=None, end_icon_slot=None, disabled=False, **kwargs):
    """
    MDUI Button component
    
    Args:
        text: Button text
        variant: 'filled', 'outlined', 'text', 'elevated', 'tonal'
        icon: Icon name for start icon (shorthand, uses icon attribute)
        end_icon: Icon name for end icon (shorthand, uses end-icon attribute)
        icon_slot: Custom icon element for start position (uses slot="icon")
        end_icon_slot: Custom icon element for end position (uses slot="end-icon")
        disabled: Whether button is disabled
    
    Examples:
        # Simple icon attribute
        Button("Search", icon="search")
        
        # Both start and end icons
        Button("Next", icon="arrow_back", end_icon="arrow_forward")
        
        # Custom icon with slot
        Button("Download", 
               icon_slot=Icon("downloading", variant="outlined"),
               end_icon_slot=Icon("attach_file", variant="outlined"))
    """
    attrs = {"variant": variant, **kwargs}
    children = []
    
    if disabled:
        attrs["disabled"] = True
    
    # Handle icon slots (custom icon elements) - these take priority
    if icon_slot:
        # Create icon with slot attribute
        if hasattr(icon_slot, 'attrs'):
            icon_slot.attrs = {**icon_slot.attrs, 'slot': 'icon'}
        children.append(icon_slot)
    elif icon:
        # Use icon attribute shorthand - MDUI will render the icon
        attrs["icon"] = icon
    
    # Add text
    if text:
        children.append(text)
    
    # Handle end-icon slots
    if end_icon_slot:
        # Create icon with slot attribute
        if hasattr(end_icon_slot, 'attrs'):
            end_icon_slot.attrs = {**end_icon_slot.attrs, 'slot': 'end-icon'}
        children.append(end_icon_slot)
    elif end_icon:
        # Use end-icon attribute shorthand - MDUI will render the icon
        attrs["end-icon"] = end_icon
    
    return _mdui_component("mdui-button", *children, **attrs)

def ButtonIcon(
    icon: str, 
    variant: str = "standard",
    href: str = None,
    selectable: bool = False,
    disabled: bool = False,
    loading: bool = False
):
    """MDUI Button Icon component"""
    attrs = {
        "icon": icon,
        "variant": variant,
        "selectable": selectable,
        "disabled": disabled,
        "loading": loading
    }
    if href:
        attrs["href"] = href
    return _mdui_component("mdui-button-icon", **attrs)

def Card(title=None, subtitle=None, content=None, variant="elevated", clickable=False, **kwargs):
    """MDUI Card component"""
    card_content = []
    attrs = {"variant": variant, "clickable": clickable, **kwargs}
    if title:
        card_content.append(_mdui_component("div", title, slot="header"))
    if subtitle:
        card_content.append(_mdui_component("div", subtitle, slot="subheader"))
    
    if content:
        if isinstance(content, list):
            card_content.extend(content)
        else:
            card_content.append(content)
    
    return _mdui_component("mdui-card", *card_content, **attrs)

def TextField(label="", value="", type="text", required=False, **kwargs):
    """MDUI Text Field component"""
    attrs = {"label": label, "value": value, "type": type, **kwargs}
    if required:
        attrs["required"] = True
    
    return _mdui_component("mdui-text-field", **attrs)


def Select(label="", variant="outlined", multiple=False, options=None, value="", **kwargs):
    """MDUI Select component"""
    opts = options or []
    attrs = {"label": label, "value": value, "multiple": multiple, **kwargs}
    
    if variant == "outlined":
        attrs["variant"] = "outlined"
    else:
        attrs["variant"] = "filled"
    
    option_elements = [
        _mdui_component("mdui-menu-item", opt.get("text", opt.get("value", "")), 
                       value=opt.get("value", opt.get("text", "")))
        for opt in opts
    ]
    
    return _mdui_component("mdui-select", *option_elements, **attrs)

def SegmentedButton(value="", **kwargs):
    """MDUI Segmented Button component"""
    attrs = {"value": value, **kwargs}
    return _mdui_component("mdui-segmented-button", **attrs)

def SegmentedButtonGroup(label="", options=None, selects=None, full_width=False, value="", **kwargs):
    """MDUI Segmented Button component"""
    opts = options or []
    button_elements = [
        _mdui_component("mdui-segmented-button", value=opt.get("value", opt.get("text", "")), **opt)
        for opt in opts
    ]
    attrs = {"label": label, "value": value, **kwargs}
    if selects:
        attrs["selects"] = selects
    if full_width:
        attrs["full-width"] = True
    return _mdui_component("mdui-segmented-button-group", *button_elements, **attrs)

def RangeSlider(min=0, max=100, tickermarks=False, step=1, value=50, **kwargs):
    """MDUI Range Slider component"""
    attrs = {"min": min, "max": max, "tickermarks": tickermarks, "step": step, "value": value, **kwargs}
    
    return _mdui_component("mdui-range-slider", **attrs)

def Checkbox(label="", checked=False, **kwargs):
    """MDUI Checkbox component"""
    attrs = {**kwargs}
    if checked:
        attrs["checked"] = True
    
    checkbox = _mdui_component("mdui-checkbox", **attrs)
    if label:
        return ft_hx("label", checkbox, " ", label)
    return checkbox


def Radio(name="", value="", checked=False, **kwargs):
    """MDUI Radio button component"""
    attrs = {"name": name, "value": value, **kwargs}
    if checked:
        attrs["checked"] = True
    
    return _mdui_component("mdui-radio", **attrs)


def Switch(checked=False, **kwargs):
    """MDUI Switch component"""
    attrs = {**kwargs}
    if checked:
        attrs["checked"] = True
    
    return _mdui_component("mdui-switch", **attrs)


def ThemeToggle(icon_light="light_mode", icon_dark="dark_mode", **kwargs):
    """
    Theme toggle button component
    
    Args:
        icon_light: Icon to show in light mode
        icon_dark: Icon to show in dark mode
    
    Example:
        ThemeToggle()
        ThemeToggle(icon_light="wb_sunny", icon_dark="nights_stay")
    """
    attrs = {
        "onclick": "toggleTheme()",
        "variant": "text",
        **kwargs
    }
    
    return _mdui_component("mdui-button-icon", 
                          Icon(icon_dark, id="theme-icon-dark", cls="dn"),
                          Icon(icon_light, id="theme-icon-light"),
                          **attrs)


def Dialog(headline="", description="", open=False, **kwargs):
    """MDUI Dialog component"""
    attrs = {**kwargs}
    if open:
        attrs["open"] = True
    
    content = []
    if headline:
        content.append(_mdui_component("div", headline, slot="headline"))
    if description:
        content.append(_mdui_component("div", description, slot="description"))
    
    return _mdui_component("mdui-dialog", *content, **attrs)


def Snackbar(message="", action_text=None, **kwargs):
    """MDUI Snackbar component"""
    content = [message]
    if action_text:
        content.append(_mdui_component("mdui-button", action_text, slot="action"))
    
    return _mdui_component("mdui-snackbar", *content, **kwargs)

def NavigationBarItem(icon="", label="", href="", **kwargs):
    """MDUI Navigation Bar Item component"""
    attrs = {**kwargs}
    if icon:
        attrs["icon"] = icon
    if label:
        attrs["label"] = label
    if href:
        attrs["href"] = href
    
    return _mdui_component("mdui-navigation-bar-item", **attrs)

def NavigationBar(*items, **kwargs):
    """MDUI Navigation Bar component"""
    return _mdui_component("mdui-navigation-bar", *items, **kwargs)


def NavigationDrawer(*items, **kwargs):
    """MDUI Navigation Drawer component"""
    return _mdui_component("mdui-navigation-drawer", *items, **kwargs)

def NavigationRail(*items, **kwargs):
    """MDUI Navigation Rail component"""
    return _mdui_component("mdui-navigation-rail", *items, **kwargs)

def NavigationRailItem(icon="", label="", href="", **kwargs):
    """MDUI Navigation Rail Item component"""
    attrs = {**kwargs}
    if icon:
        attrs["icon"] = icon
    if label:
        attrs["label"] = label
    if href:
        attrs["href"] = href
    
    return _mdui_component("mdui-navigation-rail-item", **attrs)

def TopAppBarTitle(title: str):
    return _mdui_component("mdui-top-app-bar-title", title)


def TopAppBar(*children, **kwargs):
    """
    MDUI Top App Bar component
    
    Args:
        title: App bar title
        *children: Additional child elements (buttons, icons, etc.)
    
    Examples:
        # Simple title
        TopAppBar(title="My App")
        
        # With title and children
        TopAppBar(title="My App")(
            Button(icon="menu", variant="text", slot="start"),
            Div(slot="end")(
                Button(icon="search", variant="text"),
                ThemeToggle()
            )
        )
        
        # Title as child with custom styling
        TopAppBar()(
            _mdui_component("mdui-top-app-bar-title", "Custom Title", 
                          style="color: red;"),
            Button(icon="more_vert", variant="text", slot="end")
        )
    """
    
    return _mdui_component("mdui-top-app-bar", *children, **kwargs)



def Chip(text="", icon=None, selected=False, **kwargs):
    """MDUI Chip component"""
    attrs = {**kwargs}
    if icon:
        attrs["icon"] = icon
    if selected:
        attrs["selected"] = True
    
    return _mdui_component("mdui-chip", text, **attrs)

def ListSubheader(*items, **kw):
    """MDUI List Subheader Component"""
    return _mdui_component("mdui-list-subheader", *items, **kw)

def List(*items, **kwargs):
    """MDUI List component"""
    return _mdui_component("mdui-list", *items, **kwargs)


def ListItem(
    headline: str = "", 
    description: str = "", 
    icon=None,
    end_icon=None,
    headline_line: str = "",
    description_line: str = "",
    href: str = "",
    target: str = "",
    disabled: bool = False,
    non_clickable: bool = False,
    rounded: bool = False,
    **kwargs):
    """MDUI List Item component"""
    attrs = {**kwargs}
    if icon:
        attrs["icon"] = icon
    if end_icon:
        attrs["end-icon"] = end_icon
    if headline:
        attrs["headline"] = headline
    if description:
        attrs["description"] = description
    if headline_line:
        attrs["headline-line"] = headline_line
    if description_line:
        attrs["description-line"] = description_line
    if href:
        attrs["href"] = href
    if target:
        attrs["target"] = target
    if disabled:
        attrs["disabled"] = disabled
    if non_clickable:
        attrs["nonclickable"] = non_clickable
    if rounded:
        attrs["rounded"] = rounded
    
    return _mdui_component("mdui-list-item", **attrs)


def Divider(vertical=False, **kw):
    """MDUI Divider component"""
    attrs = {**kw}
    if vertical:
        attrs["vertical"] = True
    return _mdui_component("mdui-divider", **attrs)


def Icon(name, variant="outlined", **kwargs):
    """
    MDUI Icon component
    
    Args:
        name: Icon name (e.g., 'home', 'search', 'favorite')
        variant: Icon style - 'outlined', 'rounded', 'sharp', 'filled'
    
    Examples:
        Icon("home")
        Icon("favorite", variant="filled")
        Icon("search", style="color: blue;")
    """
    attrs = {"name": name, **kwargs}
    
    # Map variant to Material Icons class
    if variant == "outlined":
        # Add class if not already present
        existing_class = attrs.get("class", "")
        if "material-symbols" not in existing_class:
            attrs["class"] = f"{existing_class} material-symbols-outlined".strip()
    elif variant == "rounded":
        existing_class = attrs.get("class", "")
        if "material-symbols" not in existing_class:
            attrs["class"] = f"{existing_class} material-symbols-rounded".strip()
    elif variant == "sharp":
        existing_class = attrs.get("class", "")
        if "material-symbols" not in existing_class:
            attrs["class"] = f"{existing_class} material-symbols-sharp".strip()
    elif variant == "filled":
        existing_class = attrs.get("class", "")
        if "material-icons" not in existing_class:
            attrs["class"] = f"{existing_class} material-icons".strip()
    
    return _mdui_component("mdui-icon", **attrs)


def Avatar(src=None, label=None, **kwargs):
    """MDUI Avatar component"""
    attrs = {**kwargs}
    if src:
        attrs["src"] = src
    if label:
        attrs["label"] = label
    
    return _mdui_component("mdui-avatar", **attrs)


def Badge(content="", **kwargs):
    """MDUI Badge component"""
    return _mdui_component("mdui-badge", content, **kwargs)


def Fab(icon, variant="primary", **kwargs):
    """MDUI Floating Action Button component"""
    return _mdui_component("mdui-fab", icon=icon, variant=variant, **kwargs)


def Progress(value=None, **kwargs):
    """MDUI Progress component"""
    attrs = {**kwargs}
    if value is not None:
        attrs["value"] = value
    
    return _mdui_component("mdui-linear-progress", **attrs)


def Slider(value=0, min=0, max=100, **kwargs):
    """MDUI Slider component"""
    return _mdui_component("mdui-slider", value=value, min=min, max=max, **kwargs)


def Tab(label="", value="", icon=None, **kwargs):
    """MDUI Tab component"""
    attrs = {"value": value, **kwargs}
    if icon:
        attrs["icon"] = icon
    
    return _mdui_component("mdui-tab", label, **attrs)


def TabPanel(value="", *content, **kwargs):
    """MDUI Tab Panel component"""
    return _mdui_component("mdui-tab-panel", *content, value=value, **kwargs)


def Tooltip(content, **kwargs):
    """MDUI Tooltip component"""
    return _mdui_component("mdui-tooltip", content, **kwargs)

