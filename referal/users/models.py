from django.db import models
# from django.contrib.auth.models import AbstractUser


# class CustomUser(AbstractUser):
#     pass


# Since we didn't get any user data, assuming referal info is a standalone model,
# either related to AUTH_USER_MODEL as OneToOne or unrelated at all

class ReferalUserModel(models.Model):
    # Not touching the model's id, since it may negatively affect performance
    referal_id = models.CharField(
        unique=True,
        blank=False,
        null=False,
        # editable=False,
        max_length=26,
    )

    referal_lvl = models.IntegerField(
        default = 1,
    )

    invited_by = models.ForeignKey(
        to = "users.ReferalUserModel",
        related_name="invited",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"id: {self.referal_id}, lvl: V{self.referal_lvl}"
