from django.utils.translation import gettext_lazy as _
import openai
import os

def generate_title_and_description(prompt: str) -> tuple[str, str]:
    """Generate a title and description for the coloring page based on the prompt.
    
    Args:
        prompt: The user's prompt for the coloring page
        
    Returns:
        tuple: (title, description)
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that creates titles and descriptions for coloring pages. "
                                      "The title should be short and descriptive (3-5 words). "
                                      "The description should be 1-2 sentences that clearly describe the scene or subject. "
                                      "Return the title and description in this exact format: 'TITLE: title here\nDESCRIPTION: description here'"},
            {"role": "user", "content": f"Create a title and description for a coloring page with this prompt: {prompt}"}
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    # Parse the response
    result = response.choices[0].message.content
    try:
        title = result.split('TITLE:')[1].split('DESCRIPTION:')[0].strip()
        description = result.split('DESCRIPTION:')[1].strip()
        return title, description
    except (IndexError, AttributeError):
        # Fallback if parsing fails
        default_title = prompt[:50] + ('...' if len(prompt) > 50 else '')
        default_description = f"A coloring page of {prompt}"
        return default_title, default_description

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
