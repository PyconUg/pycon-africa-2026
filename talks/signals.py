from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Proposal 
from home.models import EventYear  
from django.db.models.signals import pre_save
from registration.models import Profile
from django.urls import reverse
from django.contrib.sites.models import Site



@receiver(pre_save, sender=Proposal)
def send_status_change_email(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            if original.status != instance.status:
                is_poster = instance.talk_type == 'Poster'
                submission_label = 'Poster' if is_poster else 'Proposal'
                subject_templates = {
                    'A': f'PyCon Africa 2026 - Congratulations, Your {submission_label} Has Been Accepted',
                    'W': f'PyCon Africa 2026 - Your {submission_label} Is On The Waiting List',
                    'R': f'PyCon Africa 2026 - Your {submission_label} Has Not Been Selected',
                    'S': f'PyCon Africa 2026 - Your {submission_label} Has Been Submitted'
                }
                template_names = {
                    'A': 'emails/talks/proposal_accepted.html',
                    'W': 'emails/talks/proposal_waiting.html',
                    'R': 'emails/talks/proposal_rejected.html',
                    'S': 'emails/talks/proposal_submitted.html'
                }
                subject = subject_templates.get(instance.status, 'PyCon Africa 2026 - Your Proposal Status Update')
                html_template = template_names.get(instance.status, 'emails/talks/proposal_status_changed.html')

                # Retrieve the user's profile to get the full name
                try:
                    user_profile = Profile.objects.get(user=instance.user)
                    full_name = user_profile.get_full_name()
                except Profile.DoesNotExist:
                    full_name = instance.user.username  # Fallback to username if profile doesn't exist

                # Get the current site
                site = Site.objects.get_current()
                domain = site.domain

                # Generate the URL to the talk detail page
                talk_url = f"https://{domain}{reverse('talks:talk_details', kwargs={'year': instance.event_year.year, 'pk': instance.proposal_id.hashid})}"

                # Generate the URL to accept or reject the invitation
                response_url = f"https://{domain}{reverse('talks:respond_to_invitation', kwargs={'year': instance.event_year.year, 'pk': instance.proposal_id.hashid})}"


                html_content = render_to_string(html_template, {
                    'proposal': instance,
                    'user': instance.user,
                    'full_name': full_name,
                    'talk_url': talk_url,
                    'response_url': response_url
                })
                text_content = strip_tags(html_content)

                from_email = 'PyCon Africa 2026 Programme Team <program@pycon.ug>'
                
                email = EmailMultiAlternatives(
                    subject,
                    text_content,
                    from_email,  # Use the formatted sender's name and email
                    [instance.user.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
        except sender.DoesNotExist:
            pass  # Handle the case where the Proposal does not exist when the email is triggered

 