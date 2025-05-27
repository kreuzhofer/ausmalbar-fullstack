from django.utils.translation import gettext_lazy as _

def get_coloring_page_prompt(prompt: str) -> str:
    """Generate a clean, simple prompt for creating coloring page images.
    
    Args:
        prompt: The subject of the coloring page
        
    Returns:
        str: A clean prompt for the image generation
    """
    return _(
        "Black line drawing of %(prompt)s. "
        "Black outlines on white background. "
        "No color, no shading, no text, no background. "
        "Simple and clear outlines only."
    ) % {'prompt': prompt}
