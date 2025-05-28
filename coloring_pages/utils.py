from django.utils.translation import gettext_lazy as _
import openai
import os
import base64
import uuid
import tempfile
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.conf import settings

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
            {"role": "system", "content": "You are a helpful assistant that creates titles and descriptions for line art coloring pages. "
                                      "The title should be short and descriptive (3-5 words) of the main subject only. "
                                      "The description should be 1-2 sentences that clearly describe the main subject. "
                                      "Do not include any references to coloring, drawing, or art supplies. "
                                      "Focus only on describing the subject itself. "
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
                                      "Der Titel sollte kurz und beschreibend sein (3-5 Wörter) und nur das Hauptmotiv beschreiben. "
                                      "Die Beschreibung sollte 1-2 Sätze umfassen, die das Hauptmotiv klar beschreiben. "
                                      "Erwähne nicht, dass es sich um eine Malvorlage oder Zeichnung handelt. "
                                      "Konzentriere dich nur auf die Beschreibung des Motivs selbst. "
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
        "Create a clean black and white line drawing of %(prompt)s. "
        "Use smooth, continuous black lines on pure white background. "
        "No color, shading, gradients, textures, or patterns. "
        "No background elements, borders, frames, shadows, or drop shadows. "
        "No text, labels, or additional objects. Focus only on the main subject. "
        "The image should be a single, clear outline drawing with all lines connected. "
        "The subject should be centered and fill most of the frame WITHOUT TOUCHING THE EDGES. Avoid cutting off the main subject. "
        "Do not include any elements that suggest it's a coloring page unless those are explicitly part of the prompt (NO PENCILS, CRAYONS, ETC.). "
        "If you are asked for example for 'a cat' this means 'one cat' not multiple cats. avoid duplication of objects if not asked for."
        "If the object is likely to have a highly detailed pattern, such as a flower or a leaf or the fur of a pet, do not include it so it can be colored. "
    ) % {'prompt': prompt}


def generate_coloring_page_image(prompt, generate_thumbnail=True):
    """
    Generate a coloring page image using DALL-E 3 and optionally create a thumbnail.
    
    Args:
        prompt (str): The prompt to generate the image from
        generate_thumbnail (bool): Whether to generate a thumbnail (default: True)
        
    Returns:
        dict: Dictionary containing:
            - 'image_bytes': Bytes of the generated image
            - 'thumbnail_bytes': Bytes of the generated thumbnail (if generate_thumbnail=True)
            - 'temp_dir': Path to the temporary directory containing the files
            - 'image_path': Path to the generated image file
            - 'thumb_path': Path to the generated thumbnail file (if generate_thumbnail=True)
    """
    temp_dir = tempfile.mkdtemp()
    result = {
        'temp_dir': temp_dir,
        'image_path': None,
        'thumb_path': None,
        'image_bytes': None,
        'thumbnail_bytes': None
    }
    
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Generate the image using DALL-E 3
        prompt_text = get_coloring_page_prompt(prompt)
        response = client.images.generate(
            #model="dall-e-3",
            model="gpt-image-1",
            prompt=prompt_text,
            size="1024x1024",
            quality="medium",
            n=1,
            #response_format="b64_json"
        )
        
        # Get the base64 image data
        image_data = response.data[0].b64_json
        image_bytes = base64.b64decode(image_data)
        result['image_bytes'] = image_bytes
        
        # Save the image to a temporary file
        image_name = f"coloring_{uuid.uuid4()}.png"
        image_path = os.path.join(temp_dir, image_name)
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        result['image_path'] = image_path
        
        # Generate thumbnail if requested
        if generate_thumbnail:
            img = Image.open(BytesIO(image_bytes))
            img.thumbnail((300, 300), Image.LANCZOS)
            
            # Save thumbnail to bytes
            thumb_io = BytesIO()
            img.save(thumb_io, format='PNG')
            thumb_bytes = thumb_io.getvalue()
            result['thumbnail_bytes'] = thumb_bytes
            
            # Also save to file
            thumb_name = f"thumb_{uuid.uuid4()}.png"
            thumb_path = os.path.join(temp_dir, thumb_name)
            with open(thumb_path, 'wb') as f:
                f.write(thumb_bytes)
            result['thumb_path'] = thumb_path
        
        return result
        
    except Exception as e:
        # Clean up temp directory if it exists
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise e
