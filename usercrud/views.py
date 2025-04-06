from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from base.models import *
from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View
from django.http import request


class ProfileView(View,LoginRequiredMixin):
    def get(self, request):
        try:
            user = User.objects.get(username=request.user.username)
            context = {'user': user}
            return render(request, 'usercrud/profile.html', context)


        except User.DoesNotExist:
            return redirect()
        

    def post(self,request, *args, **kwargs):
        pass

    




class ProfileUpdateView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        profile = get_object_or_404(User, user=request.user)
        context = {'profile': profile}
        return render(request, 'user', context)

    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(Userprofile, user=request.user)

        # Update profile fields based on POST data
        profile.fullname = request.POST.get('fullname')
        profile.address = request.POST.get('address')
        profile.dob = request.POST.get('dob')

        # Handle profile image
        profile_image = request.FILES.get('profile_image')
        if profile_image:
            profile.profile_image = profile_image

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profilepage')
    





