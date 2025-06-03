import base64
import os
from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from coloring_pages.forms import GenerateColoringPageForm
from coloring_pages.models.coloring_page import ColoringPage
from coloring_pages.models.system_prompt import SystemPrompt
from coloring_pages.models.base import create_unique_slug
from coloring_pages.utils import generate_titles_and_descriptions, generate_coloring_page_image


class GenerateColoringPageView(View):
    """
    Admin view for generating a new coloring page using AI.
    """
    form_class = GenerateColoringPageForm
    template_name = 'admin/coloring_pages/coloringpage/generate_form.html'
    
    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = {
            'form': self.form_class(),
            'title': _('Generate New Coloring Page'),
            'opts': ColoringPage._meta,
        }
        context.update(kwargs)
        return context
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests."""
        return render(request, self.template_name, self.get_context_data())
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests."""
        form = self.form_class(request.POST or None)
        
        if not form.is_valid():
            return render(request, self.template_name, self.get_context_data(form=form))
            
        prompt = form.cleaned_data.get('prompt', '').strip()
        system_prompt = form.cleaned_data.get('system_prompt')
        
        if not prompt:
            messages.error(request, _('Please enter a prompt'))
            return render(request, self.template_name, self.get_context_data(form=form))
        
        try:
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
            
            # Generate the image and thumbnail using our utility function
            try:
                # Generate the image using the selected system prompt
                result = generate_coloring_page_image(
                    prompt, 
                    system_prompt=system_prompt,
                    generate_thumbnail=True
                )
                
                # Store the temporary file paths and other data in the session
                request.session['pending_page'] = {
                    'title_en': title_en,
                    'title_de': title_de,
                    'description_en': description_en,
                    'description_de': description_de,
                    'prompt': prompt,  # Store the original prompt for regeneration
                    'system_prompt_id': str(system_prompt.id) if system_prompt else None,
                    'image_path': result['image_path'],
                    'thumb_path': result['thumb_path'],
                    'temp_dir': result['temp_dir']
                }
                
                # Redirect to confirmation page
                return redirect('admin:confirm_coloring_page')
                
            except Exception as e:
                messages.error(request, _('Error generating image: %s') % str(e))
                return render(request, self.template_name, self.get_context_data(form=form))
                
        except Exception as e:
            import traceback
            error_message = f"Error generating coloring page: {str(e)}\n\n{traceback.format_exc()}"
            print(error_message)  # Log the full error to console
            messages.error(request, _('Error generating coloring page: %(error)s') % {'error': str(e)})
            return render(request, self.template_name, self.get_context_data(form=form))


class ConfirmColoringPageView(View):
    """
    Handle the confirmation page for generated coloring pages.
    """
    template_name = 'admin/coloring_pages/coloringpage/confirm_generation.html'
    
    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        pending_page = self.request.session.get('pending_page')
        
        # Read the thumbnail and encode it as base64
        if pending_page and os.path.exists(pending_page.get('thumb_path', '')):
            with open(pending_page['thumb_path'], 'rb') as f:
                pending_page['thumb_data'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        
        # Get all system prompts for the dropdown
        system_prompts = list(SystemPrompt.objects.all().order_by('name'))
        
        # Get the current system prompt ID from the form data or the pending page
        current_system_prompt_id = None
        if self.request.method == 'POST' and 'system_prompt' in self.request.POST:
            current_system_prompt_id = self.request.POST.get('system_prompt')
            if current_system_prompt_id == '':
                current_system_prompt_id = None
            pending_page['system_prompt_id'] = current_system_prompt_id
            self.request.session.modified = True
        else:
            current_system_prompt_id = pending_page.get('system_prompt_id')
        
        # Convert to string for template comparison
        current_system_prompt_id = str(current_system_prompt_id) if current_system_prompt_id is not None else ''
        
        context = {
            'pending_page': pending_page,
            'system_prompts': system_prompts,
            'current_system_prompt_id': current_system_prompt_id,
            'opts': ColoringPage._meta,
            'title': _('Confirm Coloring Page Generation'),
        }
        context.update(kwargs)
        return context
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests."""
        if 'pending_page' not in request.session:
            messages.error(request, _('No pending coloring page to confirm.'))
            return redirect('admin:coloring_pages_coloringpage_changelist')
            
        return render(request, self.template_name, self.get_context_data())
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests."""
        if 'pending_page' not in request.session:
            messages.error(request, _('No pending coloring page to confirm.'))
            return redirect('admin:coloring_pages_coloringpage_changelist')
            
        pending_page = request.session['pending_page']
        context = self.get_context_data()
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
                
                # Save the system prompt reference if one was used
                system_prompt_id = pending_page.get('system_prompt_id')
                if system_prompt_id:
                    try:
                        system_prompt = SystemPrompt.objects.get(id=system_prompt_id)
                        # Store in metadata
                        page.metadata = page.metadata or {}
                        page.metadata['system_prompt_id'] = system_prompt_id
                        page.metadata['system_prompt_name'] = system_prompt.name
                    except (SystemPrompt.DoesNotExist, ValueError):
                        pass  # Skip if system prompt not found
                
                # Save the main image
                with open(pending_page['image_path'], 'rb') as f:
                    image_content = ContentFile(f.read())
                    page.image.save(os.path.basename(pending_page['image_path']), image_content)
                
                # Save the thumbnail
                with open(pending_page['thumb_path'], 'rb') as f:
                    thumb_content = ContentFile(f.read())
                    page.thumbnail.save(os.path.basename(pending_page['thumb_path']), thumb_content)
                
                # Save the page first to get an ID
                page.save()
                
                # Generate and save SEO URLs
                page.seo_url_en = create_unique_slug(ColoringPage, page.title_en, 'title_en', 'seo_url_en')
                page.seo_url_de = create_unique_slug(ColoringPage, page.title_de, 'title_de', 'seo_url_de')
                page.save(update_fields=['seo_url_en', 'seo_url_de'])
                
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
            # Get the prompt and system prompt from the form or use the existing ones
            prompt = request.POST.get('prompt', pending_page['prompt'])
            system_prompt_id = request.POST.get('system_prompt')
            
            # Update the pending page with the new system prompt
            if system_prompt_id and system_prompt_id != 'None':
                pending_page['system_prompt_id'] = str(system_prompt_id)
            else:
                pending_page.pop('system_prompt_id', None)
                
            # Ensure the session is properly updated
            request.session['pending_page'] = pending_page
            request.session.modified = True
            
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
            
            # Get the system prompt object if an ID was provided
            system_prompt = None
            if system_prompt_id and system_prompt_id != 'None':
                try:
                    system_prompt = SystemPrompt.objects.get(id=system_prompt_id)
                except (SystemPrompt.DoesNotExist, ValueError):
                    # If system prompt not found, it will be None (use default)
                    pass
            
            # Initialize temp_dir at the beginning of the block
            temp_dir = None
            try:
                # Generate new image using our utility function with the selected system prompt
                result = generate_coloring_page_image(
                    prompt, 
                    system_prompt=system_prompt,  # This can be None to use default
                    generate_thumbnail=True
                )
                temp_dir = result['temp_dir']
                temp_image_path = result['image_path']
                temp_thumb_path = result['thumb_path']
                
                # Update the pending page data with new files and updated metadata
                pending_update = {
                    'title_en': title_en,
                    'title_de': title_de,
                    'description_en': description_en,
                    'description_de': description_de,
                    'prompt': prompt,  # Store the prompt that was used
                    'image_path': temp_image_path,
                    'thumb_path': temp_thumb_path,
                    'temp_dir': temp_dir,
                    'system_prompt_id': str(system_prompt.id) if system_prompt else None
                }
                # Preserve any existing session data we want to keep
                pending_update.update({
                    k: v for k, v in request.session.get('pending_page', {}).items()
                    if k not in pending_update
                })
                request.session['pending_page'] = pending_update
                
                # Redirect back to the confirmation page with the new image
                return redirect('admin:confirm_coloring_page')
                
            except Exception as e:
                # If regeneration fails, clean up and show error
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                
                messages.error(request, _('Error generating image: %(error)s') % {'error': str(e)})
                return redirect('admin:coloring_pages_coloringpage_changelist')
        
        # For any other case, just render the confirmation page
        return render(request, self.template_name, context)


# Keep the original function names for backwards compatibility
generate_coloring_page = GenerateColoringPageView.as_view()
confirm_coloring_page = ConfirmColoringPageView.as_view()
