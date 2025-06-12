"""
View for generating new coloring pages in the admin interface.
"""
import os
import json
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from coloring_pages.forms import GenerateColoringPageForm
from coloring_pages.models.coloring_page import ColoringPage


def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


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
            if is_ajax(request):
                return JsonResponse({'error': form.errors}, status=400)
            return render(request, self.template_name, self.get_context_data(form=form))
            
        prompt = form.cleaned_data.get('prompt', '').strip()
        system_prompt = form.cleaned_data.get('system_prompt')
        
        if not prompt:
            if is_ajax(request):
                return JsonResponse({'error': _('Please enter a prompt')}, status=400)
            
            from django.contrib import messages
            messages.error(request, _('Please enter a prompt'))
            return render(request, self.template_name, self.get_context_data(form=form))
        
        # Generate titles and descriptions
        try:
            from coloring_pages.utils import generate_titles_and_descriptions
            title_en, title_de, description_en, description_de = generate_titles_and_descriptions(prompt)
            
            # Ensure we have valid titles
            title_en = title_en or _('Coloring Page')
            title_de = title_de or title_en
            
            # Generate the coloring page image
            from coloring_pages.utils import generate_coloring_page_image
            result = generate_coloring_page_image(
                prompt,
                system_prompt=system_prompt,
                generate_thumbnail=True
            )
            
            # Store the generated data in the session
            request.session['pending_page'] = {
                'title_en': title_en,
                'title_de': title_de,
                'description_en': description_en,
                'description_de': description_de,
                'prompt': prompt,
                'image_path': result['image_path'],
                'thumb_path': result['thumb_path'],
                'temp_dir': result['temp_dir'],
                'system_prompt_id': str(system_prompt.id) if system_prompt else None,
            }
            
            if is_ajax(request):
                return JsonResponse({
                    'redirect': reverse('admin:confirm_coloring_page')
                })
                
            return redirect('admin:confirm_coloring_page')
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating image: {error_msg}")
            
            # Clean up any temporary files if they were created
            if 'result' in locals() and 'temp_dir' in result and os.path.exists(result.get('temp_dir', '')):
                import shutil
                try:
                    shutil.rmtree(result['temp_dir'], ignore_errors=True)
                except Exception as cleanup_error:
                    print(f"Error cleaning up temp directory: {cleanup_error}")
            
            if is_ajax(request):
                return JsonResponse({
                    'error': _('Error generating image: %(error)s') % {'error': error_msg}
                }, status=500)
                
            from django.contrib import messages
            messages.error(request, _('Error generating image: %(error)s') % {'error': error_msg})
            return render(request, self.template_name, self.get_context_data(form=form))
