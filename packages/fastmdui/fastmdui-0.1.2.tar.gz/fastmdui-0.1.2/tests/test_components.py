# File: tests/test_all_components.py
"""
Comprehensive test suite covering all fastMDUI components
This ensures every component can be instantiated and has correct attributes
"""

import pytest
from fasthtml.common import Div
from fastmdui import (
    # Core
    MDUI,
    # Form components
    Button, TextField, Select, Checkbox, Radio, Switch, Slider,
    # Display components
    Card, Icon, Avatar, Badge, Chip, Progress,
    # Navigation components
    TopAppBar, NavigationBar, NavigationDrawer, Fab,
    # Feedback components
    Dialog, Snackbar, Tooltip,
    # List components
    List, ListItem, Divider,
    # Tab components
    Tab, TabPanel,
    # Theme components
    ThemeToggle,
)


class TestAllComponentsInstantiation:
    """Test that all components can be instantiated without errors"""
    
    def test_button_all_variants(self):
        """Test all button variants"""
        variants = ["filled", "outlined", "text", "elevated", "tonal"]
        
        for variant in variants:
            btn = Button(f"{variant} button", variant=variant)
            assert btn is not None
            assert btn.tag == "mdui-button"
            assert btn.attrs.get("variant") == variant
    
    def test_button_with_all_icon_options(self):
        """Test button with all icon configurations"""
        # Icon at start
        btn1 = Button("Start", icon="home")
        assert btn1.attrs.get("icon") == "home"
        
        # Icon at end
        btn2 = Button("End", end_icon="arrow_forward")
        assert btn2.attrs.get("end-icon") == "arrow_forward"
        
        # Both icons
        btn3 = Button("Both", icon="arrow_back", end_icon="arrow_forward")
        assert btn3.attrs.get("icon") == "arrow_back"
        assert btn3.attrs.get("end-icon") == "arrow_forward"
        
        # Icon only
        btn4 = Button(icon="menu")
        assert btn4.attrs.get("icon") == "menu"
        
        # With icon slots
        btn5 = Button("Custom", 
                     icon_slot=Icon("download"),
                     end_icon_slot=Icon("check"))
        assert btn5 is not None
    
    def test_card_all_configurations(self):
        """Test card with all configuration options"""
        # Empty card
        card1 = Card()
        assert card1 is not None
        
        # Card with title only
        card2 = Card(title="Title")
        assert card2 is not None
        
        # Card with title and subtitle
        card3 = Card(title="Title", subtitle="Subtitle")
        assert card3 is not None
        
        # Card with content
        card4 = Card(content="Content")
        assert card4 is not None
        
        # Card with list content
        card5 = Card(content=["Item 1", "Item 2"])
        assert card5 is not None
        
        # Full card
        card6 = Card(
            title="Full Card",
            subtitle="With everything",
            content=[Button("Action")]
        )
        assert card6 is not None
    
    def test_textfield_all_types(self):
        """Test all text field types"""
        types = ["text", "email", "password", "number", "tel", "url", "search"]
        
        for field_type in types:
            field = TextField(type=field_type, label=f"{field_type} field")
            assert field is not None
            assert field.attrs.get("type") == field_type
    
    def test_textfield_with_attributes(self):
        """Test text field with various attributes"""
        field = TextField(
            label="Test Field",
            value="initial value",
            placeholder="Enter text",
            required=True
        )
        assert field.attrs.get("label") == "Test Field"
        assert field.attrs.get("value") == "initial value"
        assert field.attrs.get("placeholder") == "Enter text"
        assert field.attrs.get("required") is True
    
    def test_select_with_options(self):
        """Test select with different option formats"""
        # With options
        options = [
            {"text": "Option 1", "value": "opt1"},
            {"text": "Option 2", "value": "opt2"},
            {"text": "Option 3", "value": "opt3"}
        ]
        select = Select(label="Choose", options=options)
        assert select is not None
        
        # Empty select
        select2 = Select(label="Empty")
        assert select2 is not None
    
    def test_checkbox_variations(self):
        """Test checkbox with and without label"""
        # With label
        cb1 = Checkbox(label="Accept terms")
        assert cb1 is not None
        
        # Without label
        cb2 = Checkbox()
        assert cb2 is not None
        
        # Checked
        cb3 = Checkbox(checked=True)
        assert cb3 is not None
    
    def test_radio_buttons(self):
        """Test radio button creation"""
        radio1 = Radio(name="choice", value="1")
        radio2 = Radio(name="choice", value="2", checked=True)
        
        assert radio1.attrs.get("name") == "choice"
        assert radio2.attrs.get("checked") is True
    
    def test_switch_states(self):
        """Test switch in both states"""
        switch1 = Switch()
        switch2 = Switch(checked=True)
        
        assert switch1 is not None
        assert switch2.attrs.get("checked") is True
    
    def test_slider_with_values(self):
        """Test slider with different values"""
        slider1 = Slider(value=50, min=0, max=100)
        slider2 = Slider(value=25, min=0, max=50)
        
        assert slider1.attrs.get("value") == 50
        assert slider2.attrs.get("min") == 0
        assert slider2.attrs.get("max") == 50
    
    def test_icon_all_variants(self):
        """Test all icon variants"""
        variants = ["outlined", "filled", "rounded", "sharp"]
        
        for variant in variants:
            icon = Icon("home", variant=variant)
            assert icon is not None
            assert icon.attrs.get("name") == "home"
    
    def test_icon_with_styling(self):
        """Test icon with custom styling"""
        icon = Icon("favorite", variant="filled", 
                   style="color: red; font-size: 32px;")
        assert icon.attrs.get("style") == "color: red; font-size: 32px;"
    
    def test_avatar_variations(self):
        """Test avatar with different configurations"""
        # With label
        avatar1 = Avatar(label="AB")
        assert avatar1.attrs.get("label") == "AB"
        
        # With src
        avatar2 = Avatar(src="https://example.com/image.jpg")
        assert avatar2.attrs.get("src") == "https://example.com/image.jpg"
        
        # Both
        avatar3 = Avatar(src="image.jpg", label="AB")
        assert avatar3 is not None
    
    def test_badge_creation(self):
        """Test badge with content"""
        badge1 = Badge("5")
        badge2 = Badge("99+")
        badge3 = Badge("")
        
        assert badge1 is not None
        assert badge2 is not None
        assert badge3 is not None
    
    def test_chip_configurations(self):
        """Test chip with different configurations"""
        # Simple chip
        chip1 = Chip("Tag")
        assert chip1 is not None
        
        # With icon
        chip2 = Chip("Tag", icon="label")
        assert chip2.attrs.get("icon") == "label"
        
        # Selected
        chip3 = Chip("Selected", selected=True)
        assert chip3.attrs.get("selected") is True
        
        # All options
        chip4 = Chip("Full", icon="star", selected=True)
        assert chip4 is not None
    
    def test_progress_indicators(self):
        """Test progress with and without values"""
        # Determinate
        progress1 = Progress(value=75)
        assert progress1.attrs.get("value") == 75
        
        # Indeterminate
        progress2 = Progress()
        assert progress2 is not None
    
    def test_top_app_bar_variations(self):
        """Test TopAppBar with different configurations"""
        # Simple title
        bar1 = TopAppBar(title="My App")
        assert bar1 is not None
        
        # With children
        bar2 = TopAppBar(title="App")(
            Button(icon="menu", slot="start")
        )
        assert bar2 is not None
        
        # Without title, only children
        bar3 = TopAppBar()(
            Button(icon="arrow_back", slot="start"),
            Button(icon="search", slot="end")
        )
        assert bar3 is not None
        
        # Complex configuration
        bar4 = TopAppBar(title="Complex")(
            Button(icon="menu", variant="text", slot="start"),
        )
        assert bar4 is not None
    
    def test_navigation_bar(self):
        """Test NavigationBar creation"""
        nav1 = NavigationBar()
        nav2 = NavigationBar(style="position: fixed;")
        
        assert nav1 is not None
        assert nav2.attrs.get("style") == "position: fixed;"
    
    def test_navigation_drawer(self):
        """Test NavigationDrawer creation"""
        drawer1 = NavigationDrawer()
        drawer2 = NavigationDrawer(style="width: 250px;")
        
        assert drawer1 is not None
        assert drawer2 is not None
    
    def test_fab_creation(self):
        """Test Floating Action Button"""
        fab1 = Fab(icon="add")
        fab2 = Fab(icon="edit", variant="primary")
        
        assert fab1.attrs.get("icon") == "add"
        assert fab2.attrs.get("variant") == "primary"
    
    def test_dialog_configurations(self):
        """Test dialog with different configurations"""
        # Simple dialog
        dialog1 = Dialog()
        assert dialog1 is not None
        
        # With headline
        dialog2 = Dialog(headline="Confirm")
        assert dialog2 is not None
        
        # With description
        dialog3 = Dialog(description="Are you sure?")
        assert dialog3 is not None
        
        # Full dialog
        dialog4 = Dialog(
            headline="Delete Item",
            description="This action cannot be undone",
            open=False
        )
        assert dialog4 is not None
        
        # Open dialog
        dialog5 = Dialog(open=True)
        assert dialog5.attrs.get("open") is True
    
    def test_snackbar_variations(self):
        """Test snackbar with different configurations"""
        # Simple message
        snack1 = Snackbar("Message sent")
        assert snack1 is not None
        
        # With action
        snack2 = Snackbar("Deleted", action_text="Undo")
        assert snack2 is not None
    
    def test_tooltip_creation(self):
        """Test tooltip with content"""
        tooltip1 = Tooltip("Helpful text")
        tooltip2 = Tooltip("Another tip")
        
        assert tooltip1 is not None
        assert tooltip2 is not None
    
    def test_list_and_items(self):
        """Test list with items"""
        # Empty list
        list1 = List()
        assert list1 is not None
        
        # List with items
        list2 = List(
            ListItem("Item 1"),
            ListItem("Item 2", icon="check"),
            ListItem("Item 3")
        )
        assert list2 is not None
    
    def test_list_item_variations(self):
        """Test list items with different configurations"""
        # Simple item
        item1 = ListItem("Simple")
        assert item1 is not None
        
        # With icon
        item2 = ListItem("With icon", icon="star")
        assert item2.attrs.get("icon") == "star"
        
        # Empty
        item3 = ListItem("")
        assert item3 is not None
    
    def test_divider_creation(self):
        """Test divider element"""
        div1 = Divider()
        div2 = Divider(cls="p4")
        
        assert div1 is not None
        assert div2.attrs.get("class") == "p4"
    
    def test_tab_and_panel(self):
        """Test tab and tab panel creation"""
        # Tab
        tab1 = Tab(label="Tab 1", value="tab1")
        tab2 = Tab(label="Tab 2", value="tab2", icon="home")
        
        assert tab1.attrs.get("value") == "tab1"
        assert tab2.attrs.get("icon") == "home"
        
        # Tab panel
        panel1 = TabPanel("Content 1")
        panel2 = TabPanel("Content 2")
        
        assert panel1 is not None
        assert panel2 is not None
    
    def test_theme_toggle_variations(self):
        """Test theme toggle with different configurations"""
        # Default
        toggle1 = ThemeToggle()
        assert toggle1 is not None
        assert toggle1.attrs.get("onclick") == "toggleTheme()"
        
        # Custom icons
        toggle2 = ThemeToggle(icon_light="wb_sunny", icon_dark="nights_stay")
        assert toggle2 is not None
        
        # With custom attributes
        toggle3 = ThemeToggle(id="theme-btn", cls="custom-toggle")
        assert toggle3.attrs.get("id") == "theme-btn"
    
    def test_div_helper(self):
        """Test Div helper component"""
        # Empty div
        div1 = Div()
        assert div1 is not None
        
        # Div with children
        div2 = Div(Button("Click"), Button("Me"))
        assert div2 is not None
        
        # Div with attributes
        div3 = Div(
            slot="end",
            style="display: flex; gap: 8px;",
            cls="custom-class"
        )
        assert div3.attrs.get("slot") == "end"
        assert div3.attrs.get("style") == "display: flex; gap: 8px;"


class TestComponentsWithCustomAttributes:
    """Test that all components accept custom HTML attributes"""
    
    def test_components_accept_id(self):
        """Test that components accept id attribute"""
        components = [
            Button("Test", id="btn-1"),
            Card(id="card-1"),
            TextField(id="field-1"),
            Icon("home", id="icon-1"),
            Chip("Tag", id="chip-1"),
        ]
        
        for comp in components:
            assert comp.attrs.get("id") is not None
    
    def test_components_accept_class(self):
        """Test that components accept class attribute"""
        components = [
            Button("Test", cls="custom-btn"),
            Card(cls="p4"),
            List(cls="db"),
        ]
        
        for comp in components:
            assert comp.attrs.get("class") is not None
    
    def test_components_accept_style(self):
        """Test that components accept style attribute"""
        style = "margin: 10px; padding: 5px;"
        components = [
            Button("Test", style=style),
            Card(style=style),
            Icon("home", style=style),
        ]
        
        for comp in components:
            assert comp.attrs.get("style") == style
    
    def test_components_accept_onclick(self):
        """Test that components accept onclick attribute"""
        handler = "handleClick()"
        components = [
            Button("Click", onclick=handler),
            Chip("Click", onclick=handler),
        ]
        
        for comp in components:
            assert comp.attrs.get("onclick") == handler


class TestComponentCombinations:
    """Test realistic component combinations"""
    
    def test_card_with_form_components(self):
        """Test card containing form components"""
        card = Card(
            title="User Form",
            subtitle="Enter your details",
            content=[
                TextField(label="Name", type="text"),
                TextField(label="Email", type="email"),
                Select(
                    label="Country",
                    options=[
                        {"text": "USA", "value": "us"},
                        {"text": "UK", "value": "uk"}
                    ]
                ),
                Checkbox(label="Subscribe"),
                Button("Submit", variant="filled", icon="send")
            ]
        )
        assert card is not None
    
    def test_list_with_complex_items(self):
        """Test list with various item types"""
        lst = List(
            ListItem("Home", icon="home"),
            Divider(),
            ListItem("Settings", icon="settings"),
            Divider(),
            ListItem("Profile", icon="person"),
        )
        assert lst is not None
    
    def test_navigation_with_multiple_elements(self):
        """Test navigation bar with multiple components"""
        nav = TopAppBar(title="My App")(
            Button(icon="menu", variant="text", slot="start"),
            Div(slot="end")(
                Button(icon="search", variant="text"),
                Button(icon="notifications", variant="text"),
                ThemeToggle()
            )
        )
        assert nav is not None
    
    def test_dialog_with_actions(self):
        """Test dialog with action buttons"""
        dialog = Dialog(
            headline="Confirm Delete",
            description="This cannot be undone"
        )(
            Div(slot="action")(
                Button("Cancel", variant="text"),
                Button("Delete", variant="text", icon="delete")
            )
        )
        assert dialog is not None
    
    def test_tabbed_interface(self):
        """Test complete tabbed interface"""
        interface = Div()(
            Tab(label="Overview", value="tab1", icon="home"),
            Tab(label="Settings", value="tab2", icon="settings"),
            TabPanel("Overview content"),
            TabPanel("Settings content")
        )
        assert interface is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_string_values(self):
        """Test components with empty string values"""
        btn = Button("")
        field = TextField(label="", value="")
        chip = Chip("")
        
        assert btn is not None
        assert field is not None
        assert chip is not None
    
    def test_none_values(self):
        """Test components with None values"""
        select = Select(options=None)
        card = Card(content=None)
        
        assert select is not None
        assert card is not None
    
    def test_special_characters(self):
        """Test components with special characters"""
        special = "Test <>&\"' characters"
        btn = Button(special)
        field = TextField(value=special)
        
        assert btn is not None
        assert field is not None
    
    def test_long_text_values(self):
        """Test components with very long text"""
        long_text = "A" * 1000
        btn = Button(long_text)
        field = TextField(value=long_text)
        
        assert btn is not None
        assert field is not None
    
    def test_unicode_characters(self):
        """Test components with unicode characters"""
        unicode_text = "Hello 世界 🌍 مرحبا"
        btn = Button(unicode_text)
        chip = Chip(unicode_text)
        
        assert btn is not None
        assert chip is not None


class TestMDUICore:
    """Test MDUI core functionality"""
    
    def test_headers_default(self):
        """Test default header generation"""
        headers = MDUI.headers()
        assert len(headers) > 0
    
    def test_headers_with_all_options(self):
        """Test headers with all configuration options"""
        headers = MDUI.headers(
            theme="dark",
            primary_light_color="100, 200, 12",
            font="open-sans"
        )
        assert len(headers) > 0
    
    def test_headers_with_different_themes(self):
        """Test headers with different themes"""
        for theme in ["light", "dark", "auto"]:
            headers = MDUI.headers(theme=theme)
            assert len(headers) > 0
    
    def test_headers_with_different_icon_styles(self):
        """Test headers with different icon styles"""
        for icons in ["outlined", "filled", "rounded", "sharp", "all"]:
            headers = MDUI.headers(icons=icons)
            assert len(headers) > 0
    
    def test_headers_with_different_fonts(self):
        """Test headers with different fonts"""
        for font in ["open-sans", "roboto", "default", None]:
            headers = MDUI.headers(font=font)
            assert len(headers) > 0
    
    def test_theme_script_generation(self):
        """Test theme script generation"""
        script = MDUI.theme_script()
        assert script is not None
        assert script.tag == "script"


class TestComponentTagNames:
    """Verify all components have correct MDUI tag names"""
    
    def test_tag_names(self):
        """Test that all components have correct MDUI tags"""
        tag_mapping = {
            Button("test"): "mdui-button",
            Card(): "mdui-card",
            TextField(): "mdui-text-field",
            Select(): "mdui-select",
            Checkbox(): "mdui-checkbox",
            Radio(name="test", value="1"): "mdui-radio",
            Switch(): "mdui-switch",
            Dialog(): "mdui-dialog",
            Snackbar("test"): "mdui-snackbar",
            NavigationBar(): "mdui-navigation-bar",
            NavigationDrawer(): "mdui-navigation-drawer",
            TopAppBar(): "mdui-top-app-bar",
            Chip("test"): "mdui-chip",
            List(): "mdui-list",
            ListItem("test"): "mdui-list-item",
            Divider(): "mdui-divider",
            Icon("home"): "mdui-icon",
            Avatar(): "mdui-avatar",
            Badge("1"): "mdui-badge",
            Fab(icon="add"): "mdui-fab",
            Progress(): "mdui-linear-progress",
            Slider(): "mdui-slider",
            Tab(value="1"): "mdui-tab",
            TabPanel(value="1"): "mdui-tab-panel",
            Tooltip("test"): "mdui-tooltip",
        }
        
        for component, expected_tag in tag_mapping.items():
            assert component.tag == expected_tag, f"{component} has wrong tag"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])