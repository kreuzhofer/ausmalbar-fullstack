import base64
import io
import os
import tempfile
import uuid
from io import BytesIO
from django.views.generic import TemplateView
from django.conf import settings
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View
from django.contrib import messages
from django.db.models import Q
from django.db.models.fields.files import ImageFieldFile
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from openai import OpenAI
from PIL import Image

from .forms import ColoringPageForm, GenerateColoringPageForm
from .models import ColoringPage
from .utils import get_coloring_page_prompt, generate_titles_and_descriptions


# Moved to utils.py

def home(request):
    latest_pages = ColoringPage.objects.all()[:3]
    return render(request, 'coloring_pages/home.html', {'latest_pages': latest_pages})

def search(request):
    query = request.GET.get('q', '')
    
    # Search in both English and German fields
    if query:
        pages = ColoringPage.objects.filter(
            Q(title_en__icontains=query) |
            Q(description_en__icontains=query) |
            Q(title_de__icontains=query) |
            Q(description_de__icontains=query) |
            Q(prompt__icontains=query)
        ).distinct()
    else:
        pages = ColoringPage.objects.all()
    
    # Order by most recent first
    pages = pages.order_by('-created_at')
    
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
    
    # Get the appropriate title based on the current language
    language = request.LANGUAGE_CODE or 'en'
    title = getattr(coloring_page, f'title_{language[:2]}', 'coloring_page')
    
    # Clean up the filename to be URL-safe
    import re
    filename = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    
    response = HttpResponse(coloring_page.image.read(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{filename}.png"'
    return response


def page_not_found(request, exception=None, template_name='404.html'):
    """Custom 404 error handler."""
    return render(request, '404.html', status=404)


def server_error(request, template_name='500.html'):
    """Custom 500 error handler."""
    return render(request, '500.html', status=500)


class ImprintView(TemplateView):
    template_name = 'imprint.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add imprint information from environment variables
        context.update({
            'imprint_name': settings.IMPRINT_NAME,
            'imprint_street': settings.IMPRINT_STREET,
            'imprint_city': settings.IMPRINT_CITY,
            'imprint_country': settings.IMPRINT_COUNTRY,
            'imprint_email': settings.IMPRINT_EMAIL,
            'imprint_phone': settings.IMPRINT_PHONE,
        })
        return context

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
                messages.error(request, _('Please enter a prompt'))
                return render(request, 'admin/coloring_pages/coloringpage/generate_form.html', {
                    'form': form,
                    'title': _('Generate New Coloring Page'),
                    'opts': ColoringPage._meta,
                })
            
            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                # Generate titles and descriptions in both English and German
                title_en, title_de, description_en, description_de = generate_titles_and_descriptions(prompt)
                
                # Ensure titles are not too long (max 100 chars)
                title_en = title_en[:100]
                title_de = title_de[:100] if title_de else title_en  # Fallback to English if German is empty
                
                # Ensure we have at least basic descriptions
                if not description_en:
                    description_en = _('A coloring page of ') + prompt[:90] + ('...' if len(prompt) > 90 else '')
                if not description_de:
                    description_de = _('Eine Malvorlage von ') + prompt[:90] + ('...' if len(prompt) > 90 else '')
                
                # Generate the image using DALL·E 3 with the original user prompt
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
                
                # Create a temporary directory to store the generated files
                temp_dir = tempfile.mkdtemp()
                image_name = f"coloring_{uuid.uuid4()}.png"
                temp_image_path = os.path.join(temp_dir, image_name)
                
                # Save the image to a temporary file
                with open(temp_image_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Generate thumbnail
                img = Image.open(BytesIO(image_bytes))
                img.thumbnail((256, 256), Image.LANCZOS)
                
                # Save thumbnail to temp file
                thumb_name = f"thumb_{uuid.uuid4()}.png"
                temp_thumb_path = os.path.join(temp_dir, thumb_name)
                img.save(temp_thumb_path, format='PNG')
                
                # Store the temporary file paths and other data in the session
                request.session['pending_page'] = {
                    'title_en': title_en,
                    'title_de': title_de,
                    'description_en': description_en,
                    'description_de': description_de,
                    'prompt': prompt,  # Store the original prompt for regeneration
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
                messages.error(request, _('Error generating coloring page: %(error)s') % {'error': str(e)})
                return render(request, 'admin/coloring_pages/coloringpage/generate_form.html', {
                    'form': form,
                    'title': _('Generate New Coloring Page'),
                    'opts': ColoringPage._meta,
                })
    else:
        # For GET requests, show the form with just the prompt field
        form = GenerateColoringPageForm()
    
    # Use our custom template that only shows the prompt field
    return render(request, 'admin/coloring_pages/coloringpage/generate_form.html', {
        'form': form,
        'title': _('Generate New Coloring Page'),
        'opts': ColoringPage._meta,
    })


def confirm_coloring_page(request):
    """Handle the confirmation page for generated coloring pages."""
    if 'pending_page' not in request.session:
        messages.error(request, _('No pending coloring page to confirm.'))
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
                # Create a new ColoringPage instance with all language fields
                page = ColoringPage(
                    title_en=pending_page.get('title_en', ''),
                    title_de=pending_page.get('title_de', pending_page.get('title_en', '')),
                    description_en=pending_page.get('description_en', ''),
                    description_de=pending_page.get('description_de', pending_page.get('description_en', '')),
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
                
                messages.success(request, _('Coloring page saved successfully!'))
                return redirect('admin:coloring_pages_coloringpage_changelist')
                
            except Exception as e:
                messages.error(request, _('Failed to save the coloring page. Please try again.'))
                return redirect('admin:coloring_pages_coloringpage_changelist')
        
        elif action == 'regenerate':
            # Get the prompt from the form or use the existing one
            prompt = request.POST.get('prompt', pending_page['prompt'])
            
            # Generate new titles and descriptions based on the updated prompt
            title_en, title_de, description_en, description_de = generate_titles_and_descriptions(prompt)
            
            # Ensure titles are not too long (max 100 chars)
            title_en = title_en[:100]
            title_de = title_de[:100] if title_de else title_en
            
            # Ensure we have at least basic descriptions
            if not description_en:
                description_en = _('A coloring page of ') + prompt[:90] + ('...' if len(prompt) > 90 else '')
            if not description_de:
                description_de = _('Eine Malvorlage von ') + prompt[:90] + ('...' if len(prompt) > 90 else '')
            
            # Clean up old temp files
            if os.path.exists(pending_page['temp_dir']):
                import shutil
                shutil.rmtree(pending_page['temp_dir'], ignore_errors=True)
            
            # Initialize temp_dir at the beginning of the block
            temp_dir = None
            try:
                # Generate new image using the same prompt
                client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                
                # Generate the image using DALL·E 3 with the user's original prompt
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
                
                # Update the pending page data with new files and updated metadata
                request.session['pending_page'] = {
                    'title_en': title_en,
                    'title_de': title_de,
                    'description_en': description_en,
                    'description_de': description_de,
                    'prompt': prompt,  # Store the prompt that was used
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
                
                messages.error(request, _('Error generating image: %(error)s') % {'error': str(e)})
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
