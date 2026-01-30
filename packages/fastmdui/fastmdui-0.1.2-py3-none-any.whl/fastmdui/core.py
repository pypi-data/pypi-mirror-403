from fasthtml.common import Script, Link, Style


class MDUI:
    """Core MDUI class for FastHTML integration"""
    
    VERSION = "2.0.3"
    CDN_CSS = f"https://unpkg.com/mdui@{VERSION}/mdui.css"
    CDN_JS = f"https://unpkg.com/mdui@{VERSION}/mdui.global.js"
    MATERIAL_ICONS_CSS = "https://fonts.googleapis.com/icon?family=Material+Icons"
    MATERIAL_ICONS_OUTLINED_CSS = "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0"
    MATERIAL_ICONS_ROUNDED_CSS = "https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0"
    MATERIAL_ICONS_SHARP_CSS = "https://fonts.googleapis.com/css2?family=Material+Symbols+Sharp:opsz,wght,FILL,GRAD@24,400,0,0"
    
    OPEN_SANS_FONT_CSS = "https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&display=swap"
    # TAILWIND_CSS = "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"
    TACHYONS_CSS = "https://unpkg.com/tachyons@4.12.0/css/tachyons.min.css"
    
    @classmethod
    def headers(
        cls, 
        theme="auto", 
        tachyons=False, 
        primary_light_color=None,
        primary_dark_color=None,
        icons="all", 
        font="open-sans"):
        """
        Generate required MDUI headers for FastHTML
        
        Args:
            theme: 'light', 'dark', or 'auto'
            primary_color: Optional primary color (e.g., '#1976d2')
            icons: Icon style - 'outlined', 'rounded', 'sharp', 'filled', or 'all'
            font: Font family - 'open-sans', 'roboto', 'default', or None
        Returns:
            List of FastHTML components for headers
        """
        headers = [
            Link(rel="stylesheet", href=cls.CDN_CSS),
            Script(src=cls.CDN_JS),
        ]
        if tachyons:
            headers.append(Link(rel="stylesheet", href=cls.TACHYONS_CSS))
        # Line ~25 - Load Open Sans font
        if font == "open-sans":
            headers.append(Link(rel="stylesheet", href=cls.OPEN_SANS_FONT_CSS))
        # Add Material Icons based on preference
        if icons == "all":
            headers.extend([
                Link(rel="stylesheet", href=cls.MATERIAL_ICONS_CSS),
                Link(rel="stylesheet", href=cls.MATERIAL_ICONS_OUTLINED_CSS),
                Link(rel="stylesheet", href=cls.MATERIAL_ICONS_ROUNDED_CSS),
                Link(rel="stylesheet", href=cls.MATERIAL_ICONS_SHARP_CSS),
            ])
        elif icons == "outlined":
            headers.append(Link(rel="stylesheet", href=cls.MATERIAL_ICONS_OUTLINED_CSS))
        elif icons == "rounded":
            headers.append(Link(rel="stylesheet", href=cls.MATERIAL_ICONS_ROUNDED_CSS))
        elif icons == "sharp":
            headers.append(Link(rel="stylesheet", href=cls.MATERIAL_ICONS_SHARP_CSS))
        elif icons == "filled":
            headers.append(Link(rel="stylesheet", href=cls.MATERIAL_ICONS_CSS))
        
        style_content = f"""
        html, body {{
            color-scheme: {theme};
            font-family: 'Open Sans', 'Roboto', sans-serif;
        }}
        """
        if primary_light_color or primary_dark_color:
            style_content += f"""
            :root {{
                --mdui-color-primary-light: {primary_light_color};
                --mdui-color-primary-dark: {primary_dark_color};
            }}
            """
        
        # Add theme initialization script
        style_content += """
        .mdui-theme-dark #theme-icon-light { display: none; }
        .mdui-theme-dark #theme-icon-dark { display: inline-flex; }
        """
        
        headers.append(Style(style_content))
        headers.append(cls.theme_script())
        return headers
    
    @classmethod
    def theme_script(cls):
        """Generate theme toggle script"""
        return Script("""
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('class')?.includes('mdui-theme-dark') ? 'dark' : 'light';
            const next = current === 'light' ? 'dark' : 'light';
            
            if (next === 'dark') {
                html.classList.add('mdui-theme-dark');
            } else {
                html.classList.remove('mdui-theme-dark');
            }
            
            // Save preference
            localStorage.setItem('theme', next);
        }
        
        function initTheme() {
            const html = document.documentElement;
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
                html.classList.add('mdui-theme-dark');
            }
        }
        
        // Initialize theme on page load
        initTheme();
        """)

