"""
View for generating new coloring pages in the admin interface.
"""
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from coloring_pages.forms import GenerateColoringPageForm
from coloring_pages.models.coloring_page import ColoringPage


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
            from django.contrib import messages
            messages.error(request, _('Please enter a prompt'))
            return render(request, self.template_name, self.get_context_data(form=form))
        
        # Generate titles and descriptions
        from coloring_pages.utils import generate_titles_and_descriptions
        title_en, title_de, description_en, description_de = generate_titles_and_descriptions(prompt)
        
        # Ensure we have valid titles
        title_en = title_en or _('Coloring Page')
        title_de = title_de or title_en
        
        # Generate the coloring page image
        try:
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
            
            return redirect('admin:confirm_coloring_page')
            
        except Exception as e:
            # Clean up any temporary files if they were created
            if 'result' in locals() and os.path.exists(result.get('temp_dir', '')):
                import shutil
                shutil.rmtree(result['temp_dir'], ignore_errors=True)
                
            from django.contrib import messages
            messages.error(request, _('Error generating image: %(error)s') % {'error': str(e)})
            return render(request, self.template_name, self.get_context_data(form=form))
