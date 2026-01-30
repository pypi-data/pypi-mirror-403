from fasthtml.common import FastHTML, serve, Titled, Div, H2, H3
from fastmdui import MDUI, Button, Card, Icon, Divider

# Initialize with all icon variants
app = FastHTML(hdrs=MDUI.headers(theme="auto", primary_color="10, 30, 120"))

@app.get("/")
def home():
    return Titled(
        "Button Icons Demo - fastMDUI",
        
        Div(style="padding: 20px; max-width: 1200px; margin: 0 auto;")(
            H2("Button Icon Examples"),
            
            # Simple Icon Buttons
            Card(
                title="Simple Icon Buttons",
                subtitle="Using icon and end_icon attributes",
                content=Div(style="padding: 16px;")(
                    H3(style="margin-bottom: 16px;")("Start Icon Only"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;")(
                        Button("Search", variant="filled", icon="search"),
                        Button("Save", variant="outlined", icon="save"),
                        Button("Delete", variant="text", icon="delete"),
                        Button("Settings", variant="elevated", icon="settings"),
                        Button("Favorite", variant="tonal", icon="favorite"),
                    ),
                    
                    Divider(),
                    
                    H3(style="margin-bottom: 16px;")("End Icon Only"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;")(
                        Button("Next", variant="filled", end_icon="arrow_forward"),
                        Button("Send", variant="outlined", end_icon="send"),
                        Button("More", variant="text", end_icon="expand_more"),
                        Button("Open", variant="elevated", end_icon="open_in_new"),
                        Button("Download", variant="tonal", end_icon="download"),
                    ),
                    
                    Divider(),
                    
                    H3(style="margin-bottom: 16px;")("Both Start and End Icons"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap;")(
                        Button("Navigate", variant="filled", icon="arrow_back", end_icon="arrow_forward"),
                        Button("Transfer", variant="outlined", icon="upload", end_icon="download"),
                        Button("Sync", variant="elevated", icon="sync", end_icon="check"),
                    ),
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Custom Icon Slots
            Card(
                title="Custom Icon Slots",
                subtitle="Using icon_slot and end_icon_slot for advanced styling",
                content=Div(style="padding: 16px;")(
                    H3(style="margin-bottom: 16px;")("Different Icon Variants"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;")(
                        Button("Outlined Icons", variant="filled",
                               icon_slot=Icon("home", variant="outlined"),
                               end_icon_slot=Icon("star", variant="outlined")),
                        Button("Filled Icons", variant="outlined",
                               icon_slot=Icon("favorite", variant="filled"),
                               end_icon_slot=Icon("check", variant="filled")),
                        Button("Rounded Icons", variant="elevated",
                               icon_slot=Icon("settings", variant="rounded"),
                               end_icon_slot=Icon("done", variant="rounded")),
                        Button("Sharp Icons", variant="tonal",
                               icon_slot=Icon("menu", variant="sharp"),
                               end_icon_slot=Icon("close", variant="sharp")),
                    ),
                    
                    Divider(),
                    
                    H3(style="margin-bottom: 16px;")("Styled Custom Icons"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap;")(
                        Button("Success", variant="filled",
                               icon_slot=Icon("check_circle", variant="filled", style="color: #4caf50;"),
                               end_icon_slot=Icon("done", variant="filled", style="color: #4caf50;")),
                        Button("Warning", variant="outlined",
                               icon_slot=Icon("warning", variant="filled", style="color: #ff9800;"),
                               end_icon_slot=Icon("priority_high", variant="filled", style="color: #ff9800;")),
                        Button("Error", variant="elevated",
                               icon_slot=Icon("error", variant="filled", style="color: #f44336;"),
                               end_icon_slot=Icon("cancel", variant="filled", style="color: #f44336;")),
                        Button("Info", variant="tonal",
                               icon_slot=Icon("info", variant="filled", style="color: #2196f3;"),
                               end_icon_slot=Icon("help", variant="filled", style="color: #2196f3;")),
                    ),
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Action Buttons
            Card(
                title="Common Action Buttons",
                subtitle="Real-world button examples",
                content=Div(style="padding: 16px;")(
                    H3(style="margin-bottom: 16px;")("File Actions"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;")(
                        Button("Upload", variant="filled", icon="cloud_upload"),
                        Button("Download", variant="filled", icon="cloud_download"),
                        Button("Save", variant="outlined", icon="save"),
                        Button("Share", variant="outlined", icon="share"),
                        Button("Delete", variant="text", icon="delete"),
                    ),
                    
                    Divider(),
                    
                    H3(style="margin-bottom: 16px;")("Navigation Buttons"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;")(
                        Button("Back", variant="outlined", icon="arrow_back"),
                        Button("Next", variant="filled", end_icon="arrow_forward"),
                        Button("Home", variant="text", icon="home"),
                        Button("Refresh", variant="outlined", icon="refresh"),
                    ),
                    
                    Divider(),
                    
                    H3(style="margin-bottom: 16px;")("Social Actions"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;")(
                        Button("Like", variant="tonal", icon="thumb_up"),
                        Button("Favorite", variant="tonal", icon="favorite"),
                        Button("Comment", variant="outlined", icon="comment"),
                        Button("Share", variant="outlined", icon="share"),
                        Button("Bookmark", variant="text", icon="bookmark"),
                    ),
                    
                    Divider(),
                    
                    H3(style="margin-bottom: 16px;")("Media Controls"),
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap;")(
                        Button("Play", variant="filled", icon="play_arrow"),
                        Button("Pause", variant="outlined", icon="pause"),
                        Button("Stop", variant="outlined", icon="stop"),
                        Button("Previous", variant="text", icon="skip_previous"),
                        Button("Next", variant="text", icon="skip_next"),
                        Button("Volume", variant="text", icon="volume_up"),
                    ),
                )
            ),
            
            Div(style="height: 20px;"),
            
            # Icon-Only Buttons
            Card(
                title="Icon-Only Buttons",
                subtitle="Buttons without text labels",
                content=Div(style="padding: 16px;")(
                    Div(style="display: flex; gap: 8px; flex-wrap: wrap;")(
                        Button(icon="menu", variant="text"),
                        Button(icon="search", variant="text"),
                        Button(icon="notifications", variant="text"),
                        Button(icon="settings", variant="text"),
                        Button(icon="more_vert", variant="text"),
                        Button(icon="favorite", variant="filled"),
                        Button(icon="shopping_cart", variant="outlined"),
                        Button(icon="add", variant="elevated"),
                    ),
                )
            ),
        ),
    )


if __name__ == "__main__":
    serve()
