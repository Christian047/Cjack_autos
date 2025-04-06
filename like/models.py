from django.db import models
from django.contrib.auth.models import User
from base.models import *
from reviews.models import Review


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    like_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'review')  # Ensures each user can only like a review once

    def __str__(self):
        return f'{self.user.username} likes {self.review.topic}'



