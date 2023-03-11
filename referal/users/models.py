from django.db import models
from typing import Optional
from django_lifecycle import LifecycleModelMixin, hook, AFTER_CREATE
from decimal import Decimal

# Since we didn't get any user data, assuming referal info is a standalone model,
# either related to AUTH_USER_MODEL as OneToOne or unrelated at all
class ReferalUserModel(LifecycleModelMixin, models.Model):
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

    # Deposit is amount of money stored by our user.
    # Once it reach the hardcoded value of 120$, everyone who invited that
    # user get their referal money and affected_parents_deposit changes to True
    deposit = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
        default = Decimal(0.00),
    )
    affected_parents_deposit = models.BooleanField(
        default=False,
        editable=False,
    )

    def get_direct_descendants_amount(self, lvl:Optional[int] = None):
        if lvl is None:
            return self.invited.count()
        else:
            return self.invited.filter(referal_lvl=lvl).count()

    @property
    def direct_descendants(self) -> int:
        return self.get_direct_descendants_amount()

    @property
    def total_descendants(self) -> int:
        # Note that this can be optimized with a raw sql query
        # This can also be cached or stored as variable

        desc = self.direct_descendants

        for i in self.invited.all():
            desc += i.total_descendants

        return desc

    # These can be optimized better or re-done at all.
    # The way I see this, is:
    # - If we don't use referal lvls for filtering and don't do any batch processing
    # with it, these may be moved to serializer-only fields
    def update_lvl(self):
        lvl = 1

        if self.total_descendants >= 20:
            if self.direct_descendants >= 3:
                lvl = 2
        elif self.total_descendants >= 100:
            if self.direct_descendants >= 5 and self.get_direct_descendants_amount(lvl=2) >= 3:
                lvl = 3
        elif self.total_descendants >= 300:
            if self.direct_descendants >= 8 and self.get_direct_descendants_amount(lvl=3) >= 3:
                lvl = 4
        elif self.total_descendants >= 800:
            if self.direct_descendants >= 12 and self.get_direct_descendants_amount(lvl=4) >= 3:
                lvl = 5
        elif self.total_descendants >= 1500:
            if self.direct_descendants >= 20 and self.get_direct_descendants_amount(lvl=5) >= 3:
                lvl = 6

        if lvl != self.referal_lvl:
            self.referal_lvl = lvl
            self.save(
                update_fields=("referal_lvl",),
            )

    def recursively_update_parent_lvls(self):
        if self.invited_by:
            self.invited_by.update_lvl()
            self.invited_by.recursively_update_parent_lvls()

    # This may be slow if we create multiple users at once without batch_create
    # However, during normal workflow it *should* be fine
    @hook(
        AFTER_CREATE,
        on_commit=True,
    )
    def perform_after_create_hook(self):
        self.recursively_update_parent_lvls()

    def __str__(self):
        return f"id: {self.referal_id}, lvl: V{self.referal_lvl}"
