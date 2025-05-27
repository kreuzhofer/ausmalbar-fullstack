from django.utils.translation import gettext_lazy as _
import openai
import os

def generate_titles_and_descriptions(prompt: str) -> tuple[str, str, str, str]:
    """Generate English and German titles and descriptions for the coloring page based on the prompt.
    
    Args:
        prompt: The user's prompt for the coloring page
        
    Returns:
        tuple: (title_en, title_de, description_en, description_de)
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Generate English title and description
    response_en = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that creates titles and descriptions for coloring pages. "
                                      "The title should be short and descriptive (3-5 words). "
                                      "The description should be 1-2 sentences that clearly describe the scene or subject. "
                                      "Return the title and description in this exact format: 'TITLE: title here\nDESCRIPTION: description here'"},
            {"role": "user", "content": f"Create an English title and description for a coloring page with this prompt: {prompt}"}
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    # Generate German title and description
    response_de = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Titel und Beschreibungen für Malvorlagen erstellt. "
                                      "Der Titel sollte kurz und beschreibend sein (3-5 Wörter). "
                                      "Die Beschreibung sollte 1-2 Sätze umfassen, die die Szene oder das Motiv klar beschreiben. "
                                      "Antworte mit Titel und Beschreibung in genau diesem Format: 'TITEL: Titel hier\nBESCHREIBUNG: Beschreibung hier'"},
            {"role": "user", "content": f"Erstelle einen deutschen Titel und eine Beschreibung für eine Malvorlage mit diesem Thema: {prompt}"}
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    # Parse English response
    try:
        result_en = response_en.choices[0].message.content
        title_en = result_en.split('TITLE:')[1].split('DESCRIPTION:')[0].strip()
        description_en = result_en.split('DESCRIPTION:')[1].strip()
    except (IndexError, AttributeError):
        # Fallback if parsing fails
        title_en = prompt[:50] + ('...' if len(prompt) > 50 else '')
        description_en = f"A coloring page of {prompt}"
    
    # Parse German response
    try:
        result_de = response_de.choices[0].message.content
        title_de = result_de.split('TITEL:')[1].split('BESCHREIBUNG:')[0].strip()
        description_de = result_de.split('BESCHREIBUNG:')[1].strip()
    except (IndexError, AttributeError):
        # Fallback if parsing fails
        title_de = title_en  # Fallback to English if German parsing fails
        description_de = f"Eine Malvorlage von {prompt}"
    
    return title_en, title_de, description_en, description_de

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
