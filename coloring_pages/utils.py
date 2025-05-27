from django.utils.translation import gettext_lazy as _

def get_coloring_page_prompt(prompt: str) -> str:
    """Generate a clean, simple prompt for creating coloring page images.
    
    Args:
        prompt: The subject of the coloring page
        
    Returns:
        str: A clean prompt for the image generation
    """
    return _(
        "Create a black and white line drawing of %(prompt)s. "
        "Use clean, continuous black lines on pure white background. "
        "No color, no shading, no gradients, no textures. "
        "No background elements, borders, shadows, or drop shadows. "
        "No text or labels. The image should be a single, clear outline drawing "
        "suitable for coloring. All lines should be connected and form complete shapes. "
        "The drawing should be centered and fill most of the frame without touching the edges."
    ) % {'prompt': prompt}
