class Embed:
    def __init__(self):
        self.data = {}
    
    def set_title(self, title: str):
        self.data['title'] = title
        return self
    
    def set_description(self, description: str):
        self.data['description'] = description
        return self
    
    def set_color(self, color: int):
        self.data['color'] = color
        return self
    
    def set_url(self, url: str):
        self.data['url'] = url
        return self
    
    def set_thumbnail(self, url: str):
        self.data['thumbnail'] = {'url': url}
        return self
    
    def set_image(self, url: str):
        self.data['image'] = {'url': url}
        return self
    
    def add_field(self, name: str, value: str, inline: bool = False):
        if 'fields' not in self.data:
            self.data['fields'] = []
        self.data['fields'].append({
            'name': name,
            'value': value,
            'inline': inline
        })
        return self
    
    def set_footer(self, text: str, icon_url: str = None):
        self.data['footer'] = {'text': text}
        if icon_url:
            self.data['footer']['icon_url'] = icon_url
        return self
    
    def set_timestamp(self, timestamp: str = None):
        from datetime import datetime
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        self.data['timestamp'] = timestamp
        return self
    
    def to_dict(self):
        return self.data


class ContainerUI:
    @staticmethod
    def create_container(content: str, accent_color: int = None) -> dict:
        container = {
            "type": 17,
            "components": []
        }
        if accent_color:
            container["accent_color"] = accent_color
        
        lines = content.split('\n')
        current_section = []
        
        for line in lines:
            if line.strip() == '---':
                if current_section:
                    container["components"].append({
                        "type": 9,
                        "components": [{
                            "type": 10,
                            "content": '\n'.join(current_section)
                        }]
                    })
                    current_section = []
            else:
                current_section.append(line)
        
        if current_section:
            container["components"].append({
                "type": 9,
                "components": [{
                    "type": 10,
                    "content": '\n'.join(current_section)
                }]
            })
        
        return container
    
    @staticmethod
    def ansi_block(text: str, language: str = "") -> str:
        return f"```{language}\n{text}\n```"
    
    @staticmethod
    def ansi_bold(text: str) -> str:
        return f"**{text}**"
    
    @staticmethod
    def ansi_italic(text: str) -> str:
        return f"*{text}*"
    
    @staticmethod
    def ansi_code(text: str) -> str:
        return f"`{text}`"
    
    @staticmethod
    def ansi_color(text: str, color: str) -> str:
        colors = {
            'gray': '30', 'red': '31', 'green': '32', 'yellow': '33',
            'blue': '34', 'pink': '35', 'cyan': '36', 'white': '37'
        }
        code = colors.get(color, '37')
        return f"\u001b[{code}m{text}\u001b[0m"
