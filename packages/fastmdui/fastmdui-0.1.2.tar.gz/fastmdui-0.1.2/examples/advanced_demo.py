from fasthtml.common import FastHTML, serve, Titled, Div, Script
from fastmdui import (
    MDUI, Button, Card, Dialog, Snackbar, TopAppBar,
    NavigationDrawer, Tab, TabPanel, Slider, Icon, List, ListItem
)

app = FastHTML(hdrs=MDUI.headers(icons="all"))

@app.get("/")
def home():
    return Titled(
        "Advanced fastMDUI Demo",
        
        TopAppBar(title="Advanced Features"),
        
        NavigationDrawer(
            style="width: 250px;",
        ),
        
        Div(style="padding: 20px;")(
            # Icon Variants Card
            Card(
                title="Icon Variants",
                subtitle="Compare different Material Icon styles",
                content=Div(style="padding: 16px;")(
                    Div(style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px;")(
                        Div(style="text-align: center;")(
                            Icon("home", variant="outlined", style="font-size: 48px;"),
                            Div(style="margin-top: 8px; font-weight: bold;")("Outlined"),
                            Div(style="font-size: 12px; color: #666;")("home")
                        ),
                        Div(style="text-align: center;")(
                            Icon("home", variant="filled", style="font-size: 48px;"),
                            Div(style="margin-top: 8px; font-weight: bold;")("Filled"),
                            Div(style="font-size: 12px; color: #666;")("home")
                        ),
                        Div(style="text-align: center;")(
                            Icon("home", variant="rounded", style="font-size: 48px;"),
                            Div(style="margin-top: 8px; font-weight: bold;")("Rounded"),
                            Div(style="font-size: 12px; color: #666;")("home")
                        ),
                        Div(style="text-align: center;")(
                            Icon("home", variant="sharp", style="font-size: 48px;"),
                            Div(style="margin-top: 8px; font-weight: bold;")("Sharp"),
                            Div(style="font-size: 12px; color: #666;")("home")
                        ),
                    )
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Popular Icons Showcase
            Card(
                title="Popular Icons",
                subtitle="Browse commonly used Material Icons",
                content=Div(style="padding: 16px;")(
                    Div(style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 16px;")(
                        *[
                            Div(style="text-align: center;")(
                                Icon(icon_name, variant="outlined", style="font-size: 32px; color: #1976d2;"),
                                Div(style="font-size: 10px; margin-top: 4px; color: #666;")({
                                    "favorite": "favorite",
                                    "star": "star",
                                    "shopping_cart": "cart",
                                    "account_circle": "account",
                                    "settings": "settings",
                                    "search": "search",
                                    "notifications": "notify",
                                    "mail": "mail",
                                    "delete": "delete",
                                    "edit": "edit",
                                    "share": "share",
                                    "download": "download",
                                    "cloud": "cloud",
                                    "lock": "lock",
                                    "visibility": "visible",
                                    "thumb_up": "like",
                                    "calendar_today": "calendar",
                                    "location_on": "location",
                                    "phone": "phone",
                                    "camera": "camera",
                                }[icon_name])
                            )
                            for icon_name in [
                                "favorite", "star", "shopping_cart", "account_circle",
                                "settings", "search", "notifications", "mail",
                                "delete", "edit", "share", "download",
                                "cloud", "lock", "visibility", "thumb_up",
                                "calendar_today", "location_on", "phone", "camera"
                            ]
                        ]
                    )
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Tabs example with icons
            Div(id="tabs-example")(
                Tab(label="Overview", value="tab1", icon="home"),
                Tab(label="Features", value="tab2", icon="star"),
                Tab(label="Settings", value="tab3", icon="settings"),
                
                TabPanel(value="tab1")(
                    Card(
                        title="Overview",
                        content=Div(style="padding: 16px;")(
                            List(
                                ListItem("Complete Material Design integration", icon="check_circle"),
                                ListItem("2000+ Material Icons available", icon="palette"),
                                ListItem("Multiple icon variants", icon="category"),
                                ListItem("Easy to use API", icon="code"),
                            )
                        )
                    )
                ),
                TabPanel(value="tab2")(
                    Card(
                        title="Features",
                        content=Div(style="padding: 16px;")(
                            "All Material Design components with full icon support."
                        )
                    )
                ),
                TabPanel(value="tab3")(
                    Card(
                        title="Settings",
                        content=Div(style="padding: 16px;")(
                            Div(style="margin-bottom: 16px;")(
                                Icon("volume_up", variant="outlined", style="vertical-align: middle;"),
                                " Volume"
                            ),
                            Slider(value=50, min=0, max=100),
                        )
                    )
                ),
            ),
            
            Div(style="height: 20px;"),
            
            # Dialog trigger
            Button(
                "Open Dialog",
                variant="filled",
                icon="chat",
                onclick="document.querySelector('#demo-dialog').open = true"
            ),
            
            Dialog(
                headline="Confirmation",
                description="Are you sure you want to proceed?",
                id="demo-dialog"
            )(
                Div(slot="action")(
                    Button("Cancel", variant="text", icon="close"),
                    Button("Confirm", variant="text", icon="check"),
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Snackbar trigger
            Button(
                "Show Notification",
                variant="outlined",
                icon="notifications",
                onclick="document.querySelector('#demo-snackbar').open = true"
            ),
            
            Snackbar(
                "This is a notification message",
                action_text="Undo",
                id="demo-snackbar"
            ),
        ),
    )


if __name__ == "__main__":
    serve()