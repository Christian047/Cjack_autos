from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Review, Like

@require_POST
def like_review(request):
    review_id = request.POST.get('review_id')
    review = get_object_or_404(Review, pk=review_id)

    if request.user.is_authenticated:
        like, created = Like.objects.get_or_create(user=request.user, review=review)
        if created:
            like.like_count += 1
            like.save()
            liked = True
        else:
            if like.like_count == 0:
                like.like_count = 1
                like.save()
                liked = True
            else:
                like.like_count = 0
                like.delete()
                liked = False

        return JsonResponse({'like_count': like.like_count, 'liked': liked})
    else:
        return JsonResponse({'error': 'Authentication required.'}, status=401)
