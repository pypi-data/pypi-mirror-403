from fasthtml.common import FastHTML, serve, Titled, Div, Pre, Code, HighlightJS, Table, Thead, Tbody, Tr, Th, Td
from fastmdui import (
    MDUI, Button, Card, TextField, Select, Checkbox, 
    Switch, TopAppBar, Chip, List, ListItem, Divider,
    NavigationBar, Fab, Progress, Icon, ThemeToggle,
    TopAppBarTitle,NavigationBarItem, NavigationRail, NavigationRailItem,
    RangeSlider, SegmentedButtonGroup, SegmentedButton, ButtonIcon,
)
from fastmdui.components import ListSubheader

# Initialize FastHTML app with MDUI headers and Material Icons
app = FastHTML(
    hdrs=(
        HighlightJS(
            langs=["python", "javascript", "css", "html"]
        ),
        MDUI.headers(
            tachyons=True, 
            primary_light_color="10, 20, 100",
            primary_dark_color="100, 200, 255"
        )
    )
)

@app.get("/")
def home():
    return (
        # "FastMDUI Demo",
        TopAppBar(
            TopAppBarTitle("Home"),
            ThemeToggle(),
            cls="relative"
        ),
        
        List(
            ListSubheader("Subheader"),
            ListItem(
                headline="Intro",
                rounded=True,
            ),
            ListItem(
                headline="Introduction",
                description="intro"
            ),
            ListItem(
                "Install",
                non_clickable=True
            ),
            ListItem(
                "Install w/ href",
                # href="/install",
                hx_get="/install"
            )
        ),
        Div(cls="")(
            # Hero Card
            Card(
                title="Welcome to fastMDUI",
                subtitle="Material Design components for FastHTML",
                content=Div(cls="pa3")(
                    Icon("celebration", variant="outlined", 
                         style="font-size: 48px; color: #6200ea; margin-bottom: 16px;"),
                    " Build beautiful, modern web applications with Material Design UI components and icons.",
                    ThemeToggle()
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Icons Showcase Card
            Card(
                title="Material Icons",
                subtitle="Multiple variants available",
                content=Div(cls="pa4")(
                    Div(style="display: flex; gap: 20px; align-items: center; flex-wrap: wrap;")(
                        Div(style="text-align: center;")(
                            Icon("home", variant="outlined", style="font-size: 36px;"),
                            Div(style="font-size: 12px; margin-top: 4px;")("Outlined")
                        ),
                        Div(style="text-align: center;")(
                            Icon("favorite", variant="filled", style="font-size: 36px; color: #e91e63;"),
                            Div(style="font-size: 12px; margin-top: 4px;")("Filled")
                        ),
                        Div(style="text-align: center;")(
                            Icon("star", variant="outlined", style="font-size: 36px; color: #ffc107;"),
                            Div(style="font-size: 12px; margin-top: 4px;")("Star")
                        ),
                        Div(style="text-align: center;")(
                            Icon("code", variant="outlined", style="font-size: 36px; color: #2196f3;"),
                            Div(style="font-size: 12px; margin-top: 4px;")("Code")
                        ),
                        Div(style="text-align: center;")(
                            Icon("palette", variant="outlined", style="font-size: 36px; color: #9c27b0;"),
                            Div(style="font-size: 12px; margin-top: 4px;")("Palette")
                        ),
                    )
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Form Card with Icons
            Card(
                title="Form Components",
                content=Div(style="padding: 16px;")(
                    Div(style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;")(
                        Icon("person", variant="outlined"),
                        TextField(
                            label="Full Name",
                            placeholder="Enter your name",
                            style="flex: 1;"
                        ),
                    ),
                    Div(style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;")(
                        Icon("email", variant="outlined"),
                        TextField(
                            label="Email",
                            type="email",
                            placeholder="your@email.com",
                            style="flex: 1;"
                        ),
                    ),
                    Div(style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;")(
                        Icon("language", variant="outlined"),
                        Select(
                            label="Country",
                            options=[
                                {"text": "United States", "value": "us"},
                                {"text": "United Kingdom", "value": "uk"},
                                {"text": "Canada", "value": "ca"},
                                {"text": "Australia", "value": "au"},
                            ],
                            style="flex: 1;"
                        ),
                    ),
                    Div(style="margin: 16px 0;")(
                        Checkbox(label="Subscribe to newsletter", checked=True),
                    ),
                    Div(style="margin: 16px 0;")(
                        Switch(checked=True),
                        " ",
                        Icon("notifications", variant="outlined", style="vertical-align: middle;"),
                        " Enable notifications"
                    ),
                    Div(style="margin-top: 20px;")(
                        Button("Submit", variant="filled", icon="send"),
                        " ",
                        Button("Cancel", variant="outlined", icon="close"),
                    )
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Chips Card with Icons
            Card(
                title="Chips & Tags",
                content=Div(style="padding: 16px; display: flex; gap: 8px; flex-wrap: wrap;")(
                    Chip("Python", icon="code"),
                    Chip("FastHTML", icon="flash_on"),
                    Chip("Material Design", icon="palette", selected=True),
                    Chip("Web Development", icon="web"),
                    Chip("Open Source", icon="favorite"),
                )
            ),
            
            Div(style="height: 20px;"),
            
            # List Card with Icons
            Card(
                title="Features List",
                content=List(
                    ListItem("Easy Integration", icon="check_circle"),
                    Divider(),
                    ListItem("Modern Design", icon="brush"),
                    Divider(),
                    ListItem("Fully Customizable", icon="settings"),
                    Divider(),
                    ListItem("Fast & Lightweight", icon="speed"),
                    Divider(),
                    ListItem("Icon Support", icon="emoji_emotions"),
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Progress Card
            Card(
                title="Progress Indicators",
                content=Div(style="padding: 16px;")(
                    Progress(value=75),
                    Div(style="height: 16px;"),
                    Progress(),  # Indeterminate
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Button Variants with Icons
            Card(
                title="Button Variants",
                content=Div(style="padding: 16px; display: flex; gap: 8px; flex-wrap: wrap;")(
                    Button("Filled", variant="filled", icon="done"),
                    Button("Outlined", variant="outlined", icon="star"),
                    Button("Text", variant="text", icon="info"),
                    Button("Elevated", variant="elevated", icon="cloud"),
                    Button("Tonal", variant="tonal", icon="palette"),
                    Button("Download", variant="filled", icon="download"),
                    Button("Share", variant="outlined", icon="share"),
                    Button("Delete", variant="text", icon="delete"),
                    Button("Custom", variant="filled", icon="custom", loading=True)
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Button Icon Positions
            Card(
                title="Button Icon Positions",
                subtitle="Icons can be placed at start, end, or both",
                content=Div(style="padding: 16px; display: flex; gap: 8px; flex-wrap: wrap;")(
                    Button("Icon Start", variant="filled", icon="arrow_back"),
                    Button("Icon End", variant="filled", end_icon="arrow_forward"),
                    Button("Both Icons", variant="outlined", icon="arrow_back", end_icon="arrow_forward"),
                    Button("Custom Slot", variant="elevated",
                           icon_slot=Icon("downloading", variant="outlined"),
                           end_icon_slot=Icon("check", variant="filled")),
                )
            ),
            
            Div(style="height: 80px;"),
        ),
        Card(
            title="code display",
            content=(
                Pre(Code(
                    """
                        from fastmdui import (
                            MDUI, Button, Card, TextField, Select, Checkbox, 
                            Switch, TopAppBar, Chip, List, ListItem, Divider,

                        )
                        def open_csb():
                            pass
                    """
                ))
            )
        ),
        # Floating Action Button with Icon
        Fab(icon="add", style="position: fixed; bottom: 16px; right: 16px;"),
        
        # Bottom Navigation
        NavigationBar(
            NavigationBarItem(icon="home", label="Home", hx_get="/", hx_target="wrapper"),
            NavigationBarItem(icon="search", label="Search", href="/search"),
            NavigationBarItem(icon="settings", label="Settings", href="/settings"),
            
        ),
        
        # Navigation Rail
        NavigationRail(
            NavigationRailItem(icon="home", label="Home", href="/"),
            NavigationRailItem(icon="search", label="Search", href="/search"),
            NavigationRailItem(icon="settings", label="Settings", href="/settings"),
            # cls="relative"
            
        ),
        
        # Range Slider
        RangeSlider(min=0, max=100, tickermarks=True, step=5, value=50),
        
        # Range Slider with Custom Label
        RangeSlider(min=0, max=100, tickermarks=True, step=5, value=50, label="Volume"),
        Select(label="Select", options=[{"value": "option1", "text": "Option 1"}, {"value": "option2", "text": "Option 2"}], value="option1"),
        Select(
            multiple=True,
            options=[
                {"value": "option1", "text": "Option 1"},
                {"value": "option2", "text": "Option 2"},
                {"value": "option3", "text": "Option 3"}
            ]
        ),
        # Segmented Button Group
        SegmentedButtonGroup(
            SegmentedButton(label="Button 1", value="button1"),
            SegmentedButton(label="Button 2", value="button2"),
            SegmentedButton(label="Button 3", value="button3"),
            full_width=True
        ),
        
        # Card with Button
        Card(
            title="Welcome to fastMDUI",
            subtitle="Material Design components for FastHTML",
            content=Div(style="padding: 16px;")(
                Icon("celebration", variant="outlined", 
                     style="font-size: 48px; color: #6200ea; margin-bottom: 16px;"),
                " Build beautiful, modern web applications with Material Design UI components and icons.",
            ),
            variant="outlined"
        ),
        Card(
            title="Card with Button",
            content=Button("Click Me", style="margin-top: 16px;"),
            variant="filled",
        ),
        Card(
            title="Card with Button",
            content=Button("Click Me", style="margin-top: 16px;"),
            variant="outlined",
            clickable=True,
        ),
        Card(
            title="Card with Button",
            content=(
                ButtonIcon("favorite", variant="standard", href="https://example.com"),
                ButtonIcon(
                    "search",
                    variant="outlined",
                ),
                ButtonIcon(
                    "info",
                    variant="text",
                )
            ),
            variant="outlined",
            clickable=True,
        ),
        Div(
            Table(
                Thead(
                    Tr(
                        Th("Name"),
                        Th("Age"),
                        Th("City"),
                    )
                ),
                Tbody(
                    Tr(
                        Td("John"),
                        Td("25"),
                        Td("New York"),
                    ),
                    Tr(
                        Td("Jane"),
                        Td("30"),
                        Td("Los Angeles"),
                    ),
                )
            ),
            cls="mdui-table"
        ),
        
    )


if __name__ == "__main__":
    serve()

