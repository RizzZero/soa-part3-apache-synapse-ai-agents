"""
Message Transformer Implementation

This module provides message transformation capabilities for Apache Synapse MCP,
handling XML/JSON transformations, XSLT processing, and custom transformations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import json
import xml.etree.ElementTree as ET
from lxml import etree
import xmltodict
from jinja2 import Template

logger = logging.getLogger(__name__)


@dataclass
class TransformerConfig:
    """Configuration for a message transformer."""
    name: str
    type: str  # xml-to-json, json-to-xml, xslt, template, custom
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class MessageTransformer:
    """
    Message transformer that handles various types of message transformations
    including XML/JSON conversions, XSLT processing, and custom transformations.
    """
    
    def __init__(self, name: str, config: Optional[TransformerConfig] = None):
        """Initialize the message transformer."""
        self.name = name
        self.config = config or TransformerConfig(name=name, type="custom")
        self.stats = {
            "transformations": 0,
            "errors": 0,
            "avg_transform_time": 0.0
        }
        
        # Initialize transformer based on type
        self._initialize_transformer()
    
    def _initialize_transformer(self):
        """Initialize the transformer based on its type."""
        if self.config.type == "xml-to-json":
            self._transformer = self._xml_to_json
        elif self.config.type == "json-to-xml":
            self._transformer = self._json_to_xml
        elif self.config.type == "xslt":
            self._transformer = self._xslt_transform
        elif self.config.type == "template":
            self._transformer = self._template_transform
        else:
            self._transformer = self._custom_transform
    
    async def transform(self, message: str, direction: str = "request") -> str:
        """
        Transform a message using the configured transformer.
        
        Args:
            message: The message to transform
            direction: The direction of transformation (request/response)
            
        Returns:
            The transformed message
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Run transformation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._transformer, message, direction
            )
            
            # Update statistics
            self._update_stats(start_time, success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in transformer '{self.name}': {e}")
            self._update_stats(start_time, success=False)
            raise
    
    def _xml_to_json(self, message: str, direction: str) -> str:
        """Transform XML to JSON."""
        try:
            # Parse XML
            root = ET.fromstring(message)
            
            # Convert to dictionary
            xml_dict = self._xml_to_dict(root)
            
            # Convert to JSON
            json_str = json.dumps(xml_dict, indent=2, ensure_ascii=False)
            
            return json_str
            
        except Exception as e:
            raise ValueError(f"Failed to transform XML to JSON: {e}")
    
    def _json_to_xml(self, message: str, direction: str) -> str:
        """Transform JSON to XML."""
        try:
            # Parse JSON
            json_data = json.loads(message)
            
            # Convert to XML
            xml_str = self._dict_to_xml(json_data)
            
            return xml_str
            
        except Exception as e:
            raise ValueError(f"Failed to transform JSON to XML: {e}")
    
    def _xslt_transform(self, message: str, direction: str) -> str:
        """Transform using XSLT."""
        try:
            # Get XSLT stylesheet
            stylesheet_path = self.config.config.get("stylesheet")
            if not stylesheet_path:
                raise ValueError("XSLT stylesheet path not configured")
            
            # Load XSLT stylesheet
            xslt_doc = etree.parse(stylesheet_path)
            xslt_transformer = etree.XSLT(xslt_doc)
            
            # Parse input XML
            xml_doc = etree.fromstring(message)
            
            # Apply transformation
            result = xslt_transformer(xml_doc)
            
            return str(result)
            
        except Exception as e:
            raise ValueError(f"Failed to apply XSLT transformation: {e}")
    
    def _template_transform(self, message: str, direction: str) -> str:
        """Transform using Jinja2 template."""
        try:
            # Get template
            template_content = self.config.config.get("template")
            if not template_content:
                raise ValueError("Template content not configured")
            
            # Create template
            template = Template(template_content)
            
            # Parse input (assume JSON for template input)
            try:
                input_data = json.loads(message)
            except json.JSONDecodeError:
                # If not JSON, treat as string
                input_data = {"content": message}
            
            # Add direction to context
            context = {
                "input": input_data,
                "direction": direction,
                "config": self.config.config
            }
            
            # Render template
            result = template.render(**context)
            
            return result
            
        except Exception as e:
            raise ValueError(f"Failed to apply template transformation: {e}")
    
    def _custom_transform(self, message: str, direction: str) -> str:
        """Custom transformation logic."""
        # Default implementation - return message as-is
        # Can be overridden by subclasses or configured
        return message
    
    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}
        
        # Handle attributes
        if element.attrib:
            result["@attributes"] = dict(element.attrib)
        
        # Handle text content
        if element.text and element.text.strip():
            if len(element) == 0:  # No children
                return element.text.strip()
            else:
                result["#text"] = element.text.strip()
        
        # Handle children
        for child in element:
            child_data = self._xml_to_dict(child)
            child_tag = child.tag
            
            if child_tag in result:
                # Multiple children with same tag
                if isinstance(result[child_tag], list):
                    result[child_tag].append(child_data)
                else:
                    result[child_tag] = [result[child_tag], child_data]
            else:
                result[child_tag] = child_data
        
        return result
    
    def _dict_to_xml(self, data: Union[Dict[str, Any], list], root_name: str = "root") -> str:
        """Convert dictionary to XML string."""
        if isinstance(data, list):
            # Handle list data
            root = ET.Element(root_name)
            for item in data:
                child = self._dict_to_xml_element(item, "item")
                root.append(child)
        else:
            root = self._dict_to_xml_element(data, root_name)
        
        return ET.tostring(root, encoding="unicode", method="xml")
    
    def _dict_to_xml_element(self, data: Any, tag_name: str) -> ET.Element:
        """Convert dictionary to XML element."""
        element = ET.Element(tag_name)
        
        if isinstance(data, dict):
            # Handle attributes
            if "@attributes" in data:
                for key, value in data["@attributes"].items():
                    element.set(key, str(value))
            
            # Handle text content
            if "#text" in data:
                element.text = str(data["#text"])
            
            # Handle other key-value pairs
            for key, value in data.items():
                if key not in ["@attributes", "#text"]:
                    if isinstance(value, list):
                        # Multiple children with same tag
                        for item in value:
                            child = self._dict_to_xml_element(item, key)
                            element.append(child)
                    else:
                        child = self._dict_to_xml_element(value, key)
                        element.append(child)
        else:
            # Simple value
            element.text = str(data)
        
        return element
    
    def _update_stats(self, start_time: float, success: bool):
        """Update transformer statistics."""
        self.stats["transformations"] += 1
        
        if not success:
            self.stats["errors"] += 1
        
        # Calculate average transformation time
        transform_time = asyncio.get_event_loop().time() - start_time
        current_avg = self.stats["avg_transform_time"]
        transform_count = self.stats["transformations"]
        
        self.stats["avg_transform_time"] = (
            (current_avg * (transform_count - 1) + transform_time) / transform_count
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transformer statistics."""
        return {
            "name": self.name,
            "type": self.config.type,
            "stats": self.stats.copy(),
            "config": self.config.config
        }
    
    def validate_config(self) -> bool:
        """Validate transformer configuration."""
        if self.config.type == "xslt":
            stylesheet_path = self.config.config.get("stylesheet")
            if not stylesheet_path:
                raise ValueError("XSLT transformer requires stylesheet path")
            # Could add file existence check here
        
        elif self.config.type == "template":
            template_content = self.config.config.get("template")
            if not template_content:
                raise ValueError("Template transformer requires template content")
        
        return True


class TransformerRegistry:
    """
    Registry for managing multiple message transformers.
    Provides centralized transformer management and discovery.
    """
    
    def __init__(self):
        """Initialize the transformer registry."""
        self.transformers: Dict[str, MessageTransformer] = {}
    
    def register(self, transformer: MessageTransformer):
        """Register a transformer."""
        if transformer.name in self.transformers:
            raise ValueError(f"Transformer '{transformer.name}' already registered")
        
        # Validate configuration
        transformer.validate_config()
        
        self.transformers[transformer.name] = transformer
        logger.info(f"Registered transformer '{transformer.name}' of type '{transformer.config.type}'")
    
    def unregister(self, name: str):
        """Unregister a transformer."""
        if name not in self.transformers:
            raise ValueError(f"Transformer '{name}' not found")
        
        del self.transformers[name]
        logger.info(f"Unregistered transformer '{name}'")
    
    def get(self, name: str) -> Optional[MessageTransformer]:
        """Get a transformer by name."""
        return self.transformers.get(name)
    
    def list(self) -> Dict[str, Dict[str, Any]]:
        """List all registered transformers."""
        return {
            name: {
                "type": transformer.config.type,
                "stats": transformer.get_stats()
            }
            for name, transformer in self.transformers.items()
        }
    
    def get_by_type(self, transformer_type: str) -> Dict[str, MessageTransformer]:
        """Get all transformers of a specific type."""
        return {
            name: transformer
            for name, transformer in self.transformers.items()
            if transformer.config.type == transformer_type
        }
    
    async def transform_with_chain(self, message: str, transformer_names: list, direction: str = "request") -> str:
        """
        Transform a message through a chain of transformers.
        
        Args:
            message: The message to transform
            transformer_names: List of transformer names to apply in order
            direction: The direction of transformation
            
        Returns:
            The transformed message
        """
        result = message
        
        for name in transformer_names:
            transformer = self.get(name)
            if not transformer:
                raise ValueError(f"Transformer '{name}' not found")
            
            result = await transformer.transform(result, direction)
        
        return result 