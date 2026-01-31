"""
AI Writer resource for Nemati AI SDK.
"""

from typing import Any, Dict, List, Optional

from ..models.writer import WriterResponse, Template


class Writer:
    """
    AI Writer resource.
    
    Generate various types of content including blog posts, articles,
    social media posts, product descriptions, and more.
    
    Usage:
        content = client.writer.generate(
            prompt="Write a blog post about AI",
            content_type="blog_post"
        )
        print(content.text)
    """
    
    def __init__(self, http_client):
        self._http = http_client
        self.templates = Templates(http_client)
    
    def generate(
        self,
        prompt: str,
        content_type: str = "general",
        tone: str = "professional",
        max_tokens: Optional[int] = None,
        model: str = "gpt-4",
        language: str = "en",
        **kwargs,
    ) -> WriterResponse:
        """
        Generate content using AI Writer.
        
        Args:
            prompt: The prompt or topic to write about.
            content_type: Type of content to generate. Options include:
                - 'blog_post': Blog article
                - 'article': News/informational article
                - 'social_media': Social media post
                - 'product_description': Product description
                - 'email': Email content
                - 'ad_copy': Advertising copy
                - 'general': General content
            tone: Writing tone. Options include:
                - 'professional': Business/formal tone
                - 'casual': Friendly/informal tone
                - 'persuasive': Marketing/sales tone
                - 'informative': Educational tone
                - 'creative': Artistic/creative tone
            max_tokens: Maximum tokens in response.
            model: Model to use for generation.
            language: Output language code (e.g., 'en', 'es', 'fr').
            **kwargs: Additional parameters.
        
        Returns:
            WriterResponse with generated content.
        
        Example:
            content = client.writer.generate(
                prompt="Benefits of renewable energy",
                content_type="blog_post",
                tone="informative",
                max_tokens=1000
            )
            print(content.text)
        """
        payload = {
            "prompt": prompt,
            "content_type": content_type,
            "tone": tone,
            "model": model,
            "language": language,
            **kwargs,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = self._http.request("POST", "/writer/generate", json=payload)
        return WriterResponse.from_dict(response.get("data", response))
    
    def rewrite(
        self,
        text: str,
        instructions: Optional[str] = None,
        tone: Optional[str] = None,
        **kwargs,
    ) -> WriterResponse:
        """
        Rewrite existing content.
        
        Args:
            text: The text to rewrite.
            instructions: Specific instructions for rewriting.
            tone: Target tone for the rewritten content.
            **kwargs: Additional parameters.
        
        Returns:
            WriterResponse with rewritten content.
        """
        payload = {
            "text": text,
            **kwargs,
        }
        
        if instructions:
            payload["instructions"] = instructions
        if tone:
            payload["tone"] = tone
        
        response = self._http.request("POST", "/writer/rewrite", json=payload)
        return WriterResponse.from_dict(response.get("data", response))
    
    def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        format: str = "paragraph",
        **kwargs,
    ) -> WriterResponse:
        """
        Summarize content.
        
        Args:
            text: The text to summarize.
            max_length: Maximum length of summary in words.
            format: Output format ('paragraph', 'bullets', 'key_points').
            **kwargs: Additional parameters.
        
        Returns:
            WriterResponse with summary.
        """
        payload = {
            "text": text,
            "format": format,
            **kwargs,
        }
        
        if max_length:
            payload["max_length"] = max_length
        
        response = self._http.request("POST", "/writer/summarize", json=payload)
        return WriterResponse.from_dict(response.get("data", response))


class Templates:
    """Manage AI Writer templates."""
    
    def __init__(self, http_client):
        self._http = http_client
    
    def list(
        self,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Template]:
        """
        List available templates.
        
        Args:
            category: Filter by category.
            limit: Maximum number of templates to return.
        
        Returns:
            List of Template objects.
        """
        params = {"limit": limit}
        if category:
            params["category"] = category
        
        response = self._http.request("GET", "/writer/templates", params=params)
        return [
            Template.from_dict(t)
            for t in response.get("data", response.get("items", []))
        ]
    
    def get(self, template_id: str) -> Template:
        """
        Get a specific template.
        
        Args:
            template_id: The template ID.
        
        Returns:
            Template object.
        """
        response = self._http.request("GET", f"/writer/templates/{template_id}")
        return Template.from_dict(response.get("data", response))
    
    def generate(
        self,
        template_id: str,
        variables: Dict[str, Any],
        **kwargs,
    ) -> WriterResponse:
        """
        Generate content from a template.
        
        Args:
            template_id: The template ID to use.
            variables: Dictionary of template variables.
            **kwargs: Additional parameters.
        
        Returns:
            WriterResponse with generated content.
        
        Example:
            content = client.writer.templates.generate(
                template_id="product-description",
                variables={
                    "product_name": "AI Assistant",
                    "features": ["Smart", "Fast", "Reliable"],
                    "target_audience": "Developers"
                }
            )
        """
        payload = {
            "template_id": template_id,
            "variables": variables,
            **kwargs,
        }
        
        response = self._http.request("POST", f"/writer/templates/{template_id}/generate", json=payload)
        return WriterResponse.from_dict(response.get("data", response))
