from django.db import models
from typing import Optional
from django_lifecycle import LifecycleModelMixin, hook, AFTER_CREATE, AFTER_SAVE
from mptt.models import MPTTModel, TreeForeignKey
from decimal import Decimal

# Since we didn't get any user data, assuming referal info is a standalone model,
# either related to AUTH_USER_MODEL as OneToOne or unrelated at all
# class ReferalUserModel(LifecycleModelMixin, models.Model):
class ReferalUserModel(LifecycleModelMixin, MPTTModel):
    # Not touching the model's id, since it may negatively affect performance
    referal_id = models.CharField(
        unique=True,
        blank=False,
        null=False,
        # editable=False,
        max_length=26,
    )

    referal_lvl = models.IntegerField(
        default=1,
    )

    # parent = models.ForeignKey(
    parent = TreeForeignKey(
        to="self",
        related_name="children",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # Deposit is amount of money stored by our user.
    # Once it reach the hardcoded value of 120$, everyone who invited that
    # user get their referal money and affected_parents_deposit changes to True
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal(0.00),
    )
    # Bonus money, separated from deposit.
    # This won't trigger on_deposit hook and may come handy if deposit bonus
    # will later be needed to exhaust overtime or something like that
    bonus_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal(0.00),
    )
    affected_parents_deposit = models.BooleanField(
        default=False,
        editable=False,
    )

    def get_direct_descendants_amount(self, lvl: Optional[int] = None):
        if lvl is None:
            return self.children.count()
        else:
            return self.children.filter(referal_lvl=lvl).count()

    @property
    def direct_descendants(self) -> int:
        return self.get_direct_descendants_amount()

    @property
    def total_descendants(self) -> int:
        # Note that this can be optimized with a raw sql query
        # This can also be cached or stored as variable

        # desc = self.direct_descendants

        # for i in self.children.all():
        #     desc += i.total_descendants

        # return desc
        return self.get_descendant_count()

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
            if (
                self.direct_descendants >= 5
                and self.get_direct_descendants_amount(lvl=2) >= 3
            ):
                lvl = 3
        elif self.total_descendants >= 300:
            if (
                self.direct_descendants >= 8
                and self.get_direct_descendants_amount(lvl=3) >= 3
            ):
                lvl = 4
        elif self.total_descendants >= 800:
            if (
                self.direct_descendants >= 12
                and self.get_direct_descendants_amount(lvl=4) >= 3
            ):
                lvl = 5
        elif self.total_descendants >= 1500:
            if (
                self.direct_descendants >= 20
                and self.get_direct_descendants_amount(lvl=5) >= 3
            ):
                lvl = 6

        if lvl != self.referal_lvl:
            self.referal_lvl = lvl
            self.save(
                update_fields=("referal_lvl",),
            )

    def recursively_update_parent_lvls(self):
        if self.parent:
            self.parent.update_lvl()
            self.parent.recursively_update_parent_lvls()

    def grant_indirect_referal_deposit_bonuses(self):
        """Grant deposit bonus to parent, after user obtained its own"""

        print("Attempting to grant indirect referal deposit bonuses")

        # I assume this one is not recursive?
        if not self.parent:
            return

        if self.referal_lvl >= 3:
            if self.parent.referal_lvl <= self.referal_lvl:
                # Not doing anything, as members of lvl 3 or above don't grant
                # referal deposit money if their level match or beat their
                # inviteer's lvl
                return
        else:
            # I think there are some cases when this may not work the intended way?
            # Not quite sure, just a thought that struggled my mind #TODO

            bonus_money = Decimal(0.00)

            if self.parent.referal_lvl == 2:
                bonus_money = Decimal(10.00)
            elif self.parent.referal_lvl == 3:
                if self.referal_lvl == 1:
                    bonus_money = Decimal(20.00)
                elif self.referal_lvl == 2:
                    bonus_money = Decimal(10.00)
            elif self.parent.referal_lvl == 4:
                if self.referal_lvl == 1:
                    bonus_money = Decimal(30.00)
                elif self.referal_lvl == 2:
                    bonus_money = Decimal(20.00)
                elif self.referal_lvl == 3:
                    bonus_money = Decimal(10.00)
            elif self.parent.referal_lvl == 5:
                if self.referal_lvl == 1:
                    bonus_money = Decimal(35.00)
                elif self.referal_lvl == 2:
                    bonus_money = Decimal(25.00)
                elif self.referal_lvl == 3:
                    bonus_money = Decimal(15.00)
                elif self.referal_lvl == 4:
                    bonus_money = Decimal(5.00)
            elif self.parent.referal_lvl == 6:
                if self.referal_lvl == 1:
                    bonus_money = Decimal(40.00)
                elif self.referal_lvl == 2:
                    bonus_money = Decimal(30.00)
                elif self.referal_lvl == 3:
                    bonus_money = Decimal(20.00)
                elif self.referal_lvl == 4:
                    bonus_money = Decimal(10.00)
                elif self.referal_lvl == 5:
                    bonus_money = Decimal(5.00)

            if bonus_money > 0:
                print(
                    f"Granting {bonus_money} bonuses to {self.parent.referal_id} as indirect deposit bonus"
                )
                self.parent.bonus_deposit += bonus_money

                self.parent.save(update_fields=("bonus_deposit",))

    def grant_direct_referal_deposit_bonuses(self):
        if self.affected_parents_deposit:
            print(f"User {self.referal_id} has already granted bonuses to inviteers")
            return
        else:
            print("Attempting to grant direct referal deposit bonuses")

            if self.parent:
                bonus_money = Decimal(0.00)
                if self.parent.referal_lvl == 1:
                    bonus_money = Decimal(30.00)
                elif self.parent.referal_lvl == 2:
                    bonus_money = Decimal(40.00)
                elif self.parent.referal_lvl == 3:
                    bonus_money = Decimal(50.00)
                elif self.parent.referal_lvl == 4:
                    bonus_money = Decimal(60.00)
                elif self.parent.referal_lvl == 5:
                    bonus_money = Decimal(65.00)
                elif self.parent.referal_lvl == 6:
                    bonus_money = Decimal(70.00)

                self.parent.grant_indirect_referal_deposit_bonuses()

                print(
                    f"Granting {bonus_money} to {self.parent.referal_id} as direct deposit bonus"
                )
                self.parent.bonus_deposit += bonus_money
                self.parent.save(
                    update_fields=("bonus_deposit",),
                )

            self.affected_parents_deposit = True
            self.save(update_fields=("affected_parents_deposit",))

    # This may be slow if we create multiple users at once without batch_create
    # However, during normal workflow it *should* be fine
    @hook(
        AFTER_CREATE,
        on_commit=True,
    )
    def perform_after_create_hook(self):
        self.recursively_update_parent_lvls()

    @hook(
        AFTER_SAVE,
        when="deposit",
        has_changed=True,
        on_commit=True,
    )
    def perform_on_deposit_hook(self):
        print(f"Performing on deposit hook of {self.referal_id}")
        if not self.affected_parents_deposit and self.deposit >= 120:
            self.grant_direct_referal_deposit_bonuses()

            self.affected_parents_deposit = True
            self.save(
                update_fields=("affected_parents_deposit",),
            )

    def __str__(self):
        return (
            f"id: {self.referal_id}, "
            f"deposit: {self.deposit}, "
            f"lvl: V{self.referal_lvl}"
        )
