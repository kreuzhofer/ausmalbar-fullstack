import base64
import io
import os
import tempfile
import uuid
from io import BytesIO

import requests
from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.urls import reverse
from openai import OpenAI
from PIL import Image

from .forms import ColoringPageForm, GenerateColoringPageForm
from .models import ColoringPage


def get_coloring_page_prompt(prompt: str) -> str:
    """Generate a clean, simple prompt for creating coloring page images.
    
    Args:
        prompt: The subject of the coloring page
        
    Returns:
        str: A clean prompt for the image generation
    """
    return (
        f"Black line drawing of {prompt}. "
        "Black outlines on white background. "
        "No color, no shading, no text, no background. "
        "Simple and clear outlines only."
    )

def home(request):
    latest_pages = ColoringPage.objects.all()[:3]
    return render(request, 'coloring_pages/home.html', {'latest_pages': latest_pages})

def search(request):
    query = request.GET.get('q', '')
    pages = ColoringPage.objects.filter(description__icontains=query)
    
    paginator = Paginator(pages, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'coloring_pages/search.html', {
        'query': query,
        'page_obj': page_obj,
    })

def page_detail(request, pk):
    page = get_object_or_404(ColoringPage, pk=pk)
    return render(request, 'coloring_pages/detail.html', {'page': page})

def download_image(request, pk):
    coloring_page = get_object_or_404(ColoringPage, pk=pk)
    if not coloring_page.image:
        raise Http404("Image not found")
    
    response = HttpResponse(coloring_page.image.read(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{coloring_page.title}.png"'
    return response


def page_not_found(request, exception=None, template_name='404.html'):
    """Custom 404 error handler."""
    return render(request, '404.html', status=404)


def server_error(request, template_name='500.html'):
    """Custom 500 error handler."""
    return render(request, '500.html', status=500)

# Admin view for generating new coloring pages
def generate_coloring_page(request):
    # Handle form submission
    if request.method == 'POST':
        # Use our custom form that only has the prompt field
        form = GenerateColoringPageForm(request.POST or None)
        
        if form.is_valid():
            prompt = form.cleaned_data.get('prompt', '').strip()
            
            # Ensure the prompt is not empty
            if not prompt:
                messages.error(request, 'Please enter a prompt')
                return render(request, 'admin/coloring_pages/coloringpage/generate_form.html', {
                    'form': form,
                    'title': 'Generate New Coloring Page',
                    'opts': ColoringPage._meta,
                })
            
            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                # Generate title and description using GPT-4o-mini
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": """You are an AI that helps create content for images. 
                        Always respond with just a 5-word title on the first line and a 1-2 sentence description on the second line. 
                        The title should be exactly 5 words describing the image content only.
                        Do not mention that it's a coloring page, line art, or anything about coloring.
                        Do not use any markdown formatting, quotes, or special characters."""},
                        {"role": "user", "content": f"""Create a 5-word title and short description for an image based on this: {prompt}
                        
                        Rules:
                        - Title must be exactly 5 words
                        - Title should describe only the image content
                        - Do not mention coloring, line art, or that it's a page
                        - Description should be 1-2 simple sentences
                        - No markdown, quotes, or special characters
                        
                        Example:
                        Happy dog playing in park
                        A joyful golden retriever running through a sunny park with a ball in its mouth.
                        
                        Now create for: {prompt}"""}
                    ],
                    max_tokens=100,
                    temperature=0.5
                )
                
                # Parse the response to extract title and description
                result = response.choices[0].message.content.strip()
                print(f"AI Response: {result}")  # Debug log
                
                # Initialize with default values based on the prompt
                default_title = ' '.join(prompt.split()[:5])  # First 5 words of prompt as fallback
                default_description = f"Image featuring {prompt}."
                
                # Initialize with defaults
                title = default_title
                description = default_description
                
                # Clean up the response
                cleaned_result = result.strip()
                
                # Try to parse the response
                try:
                    # Remove any markdown formatting and quotes
                    cleaned_result = (
                        cleaned_result
                        .replace('**', '')
                        .replace('*', '')
                        .replace('"', '')
                        .replace('\'', '')
                        .strip()
                    )
                    
                    # Split by newlines and remove empty lines
                    lines = [line.strip() for line in cleaned_result.split('\n') if line.strip()]
                    
                    if lines:
                        # Get title from first line and ensure it's 5 words
                        title_words = lines[0].split()
                        if len(title_words) > 5:
                            title = ' '.join(title_words[:5])
                        else:
                            title = ' '.join(title_words)
                        
                        # If we have more lines, use them for description
                        if len(lines) > 1:
                            description = ' '.join(line.strip() for line in lines[1:] if line.strip())
                    
                    # Ensure title is exactly 5 words
                    title_words = title.split()
                    if len(title_words) < 5:
                        # If title is too short, pad with words from prompt
                        prompt_words = [w for w in prompt.split() if w.lower() not in ['a', 'an', 'the', 'and', 'or']]
                        title = ' '.join(title_words + prompt_words)[:5]
                    elif len(title_words) > 5:
                        # If title is too long, truncate to 5 words
                        title = ' '.join(title_words[:5])
                    
                    # Final cleanup
                    title = title.strip(' .-,').capitalize()
                    description = description.strip(' .-,').capitalize()
                    
                    # Ensure we don't have empty values
                    if not title:
                        title = default_title
                    if not description:
                        description = default_description
                        
                except Exception as e:
                    print(f"Error parsing AI response: {e}")
                    # Use the default values if parsing fails
                
                # Generate the image using DALL·E 3 with explicit instructions
                prompt_text = get_coloring_page_prompt(prompt)
                
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt_text,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                    response_format="b64_json"
                )
                
                # Get the base64 image data
                image_data = response.data[0].b64_json
                image_bytes = base64.b64decode(image_data)
                
                # Create a new ColoringPage instance
                page = ColoringPage(
                    title=title,
                    description=description,
                    prompt=prompt
                )
                
                # Save images to temporary files
                temp_dir = tempfile.mkdtemp()
                image_name = f"coloring_{uuid.uuid4()}.png"
                temp_image_path = os.path.join(temp_dir, image_name)
                
                # Save the main image
                with open(temp_image_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Generate thumbnail
                from io import BytesIO
                from PIL import Image as PILImage
                
                # Create thumbnail
                img = PILImage.open(BytesIO(image_bytes))
                img.thumbnail((256, 256), PILImage.LANCZOS)
                
                # Save thumbnail to temp file
                thumb_name = f"thumb_{uuid.uuid4()}.png"
                temp_thumb_path = os.path.join(temp_dir, thumb_name)
                img.save(temp_thumb_path, format='PNG')
                
                # Store data in session for confirmation
                request.session['pending_page'] = {
                    'title': title,
                    'description': description,
                    'prompt': prompt,
                    'image_path': temp_image_path,
                    'thumb_path': temp_thumb_path,
                    'temp_dir': temp_dir
                }
                
                # Redirect to confirmation page
                return redirect('admin:confirm_coloring_page')
            
            except Exception as e:
                import traceback
                error_message = f"Error generating coloring page: {str(e)}\n\n{traceback.format_exc()}"
                print(error_message)  # Log the full error to console
                messages.error(request, f'Error generating coloring page: {str(e)}')
                return render(request, 'admin/coloring_pages/coloringpage/generate_form.html', {
                    'form': form,
                    'title': 'Generate New Coloring Page',
                    'opts': ColoringPage._meta,
                })
    else:
        # For GET requests, show the form with just the prompt field
        form = GenerateColoringPageForm()
    
    # Use our custom template that only shows the prompt field
    return render(request, 'admin/coloring_pages/coloringpage/generate_form.html', {
        'form': form,
        'title': 'Generate New Coloring Page',
        'opts': ColoringPage._meta,
    })


def confirm_coloring_page(request):
    """Handle the confirmation page for generated coloring pages."""
    if 'pending_page' not in request.session:
        messages.error(request, 'No pending coloring page to confirm.')
        return redirect('admin:coloring_pages_coloringpage_changelist')
    
    pending_page = request.session['pending_page']
    
    # Read the thumbnail and encode it as base64
    if os.path.exists(pending_page.get('thumb_path', '')):
        with open(pending_page['thumb_path'], 'rb') as f:
            pending_page['thumb_data'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            # Save the page to the database
            try:
                # Create a new ColoringPage instance
                page = ColoringPage(
                    title=pending_page['title'],
                    description=pending_page['description'],
                    prompt=pending_page['prompt']
                )
                
                # Save the main image
                with open(pending_page['image_path'], 'rb') as f:
                    image_content = ContentFile(f.read())
                    page.image.save(os.path.basename(pending_page['image_path']), image_content)
                
                # Save the thumbnail
                with open(pending_page['thumb_path'], 'rb') as f:
                    thumb_content = ContentFile(f.read())
                    page.thumbnail.save(os.path.basename(pending_page['thumb_path']), thumb_content)
                
                # Save the page
                page.save()
                
                # Clean up temp files
                if os.path.exists(pending_page['temp_dir']):
                    import shutil
                    shutil.rmtree(pending_page['temp_dir'])
                
                # Clear the session
                del request.session['pending_page']
                
                messages.success(request, 'Coloring page saved successfully!')
                return redirect('admin:coloring_pages_coloringpage_changelist')
                
            except Exception as e:
                messages.error(request, f'Error saving coloring page: {str(e)}')
                return redirect('admin:coloring_pages_coloringpage_changelist')
        
        elif action == 'regenerate':
            # Keep the prompt and regenerate the content
            prompt = pending_page['prompt']
            
            # Clean up old temp files
            if os.path.exists(pending_page['temp_dir']):
                import shutil
                shutil.rmtree(pending_page['temp_dir'], ignore_errors=True)
            
            # Initialize temp_dir at the beginning of the block
            temp_dir = None
            try:
                # Generate new image using the same prompt
                client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                
                # Generate the image using DALL·E 3 with explicit instructions
                prompt_text = get_coloring_page_prompt(prompt)
                
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt_text,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                
                # Download the generated image
                image_url = response.data[0].url
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                image_bytes = image_response.content
                
                # Create new temp directory
                temp_dir = tempfile.mkdtemp()
                image_name = f"coloring_{uuid.uuid4()}.png"
                temp_image_path = os.path.join(temp_dir, image_name)
                
                # Save the main image
                with open(temp_image_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Generate thumbnail
                img = Image.open(BytesIO(image_bytes))
                img.thumbnail((256, 256), Image.LANCZOS)
                
                # Save thumbnail to temp file
                thumb_name = f"thumb_{uuid.uuid4()}.png"
                temp_thumb_path = os.path.join(temp_dir, thumb_name)
                img.save(temp_thumb_path, format='PNG')
                
                # Update the pending page data with new files
                request.session['pending_page'] = {
                    'title': pending_page.get('title', 'New Coloring Page'),
                    'description': pending_page.get('description', ''),
                    'prompt': prompt,
                    'image_path': temp_image_path,
                    'thumb_path': temp_thumb_path,
                    'temp_dir': temp_dir
                }
                
                # Redirect back to the confirmation page with the new image
                return redirect('admin:confirm_coloring_page')
                
            except Exception as e:
                # If regeneration fails, clean up and show error
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                
                messages.error(request, f'Error regenerating image: {str(e)}')
                return redirect('admin:coloring_pages_coloringpage_changelist')
        
        elif action == 'reject':
            # Clean up temp files
            if os.path.exists(pending_page['temp_dir']):
                import shutil
                shutil.rmtree(pending_page['temp_dir'])
            
            # Clear the session
            del request.session['pending_page']
            
            messages.info(request, 'Coloring page generation cancelled.')
            return redirect('admin:coloring_pages_coloringpage_changelist')
    
    # For GET requests, show the confirmation page
    return render(request, 'admin/coloring_pages/coloringpage/confirm_generation.html', {
        'title': 'Confirm Coloring Page Generation',
        'opts': ColoringPage._meta,
        'page_data': pending_page,
    })
