"""模板管理器"""

import os
from jinja2 import Template, FileSystemLoader, Environment
from typing import Dict, Any, Optional


class TemplateManager:
    """模板管理器"""
    
    def __init__(self):
        """初始化模板管理器"""
        self.templates_dir = os.path.join(os.path.dirname(__file__), "default")
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    
    def get_template(self, template_name: str) -> Template:
        """获取模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            Template: Jinja2 模板对象
        """
        return self.env.get_template(template_name)
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """渲染模板
        
        Args:
            template_name: 模板名称
            context: 模板上下文
            
        Returns:
            str: 渲染后的内容
        """
        template = self.get_template(template_name)
        return template.render(**context)
    
    def render_file(self, template_name: str, output_path: str, context: Dict[str, Any]) -> None:
        """渲染模板到文件
        
        Args:
            template_name: 模板名称
            output_path: 输出文件路径
            context: 模板上下文
        """
        content = self.render_template(template_name, context)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)


# 创建模板管理器实例
template_manager = TemplateManager()
