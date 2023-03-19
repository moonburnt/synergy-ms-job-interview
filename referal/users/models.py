from django.db import models, connection
from typing import Optional
from django_lifecycle import LifecycleModelMixin, hook, AFTER_CREATE, AFTER_SAVE
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
        default=1,
    )

    invited_by = models.ForeignKey(
        to="users.ReferalUserModel",
        related_name="invited",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # Deposit is amount of money stored by our user.
    # Each time it reaches the hardcoded value of 120$, everyone who invited that
    # user get their referal money
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

    def get_direct_descendants_amount(self, lvl: Optional[int] = None):
        if lvl is None:
            return self.invited.count()
        else:
            return self.invited.filter(referal_lvl=lvl).count()

    @property
    def direct_descendants(self) -> int:
        return self.get_direct_descendants_amount()

    @property
    def total_descendants(self) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                with RECURSIVE get_descendants as (
                    select id, invited_by_id
                    from users_referalusermodel
                    where id = %s
                    union all
                    select c.id, c.invited_by_id
                    from users_referalusermodel c
                        join get_descendants p on p.id = c.invited_by_id
                )
                select COUNT(*)
                from get_descendants
                where id <> %s;
            """,
                [self.id, self.id],
            )
            counter: int = cursor.fetchone()[0]

        return counter

    @staticmethod
    def calculate_user_lvl(
        total_desc: int, direct_desc: int, desc_storage, get_descendants: callable
    ) -> int:
        lvl = 1
        if (
            total_desc >= 1500
            and direct_desc >= 20
            and get_descendants(desc_storage, 5) >= 3
        ):
            lvl = 6
        elif (
            total_desc >= 800
            and direct_desc >= 12
            and get_descendants(desc_storage, 4) >= 3
        ):
            lvl = 5
        elif (
            total_desc >= 300
            and direct_desc >= 8
            and get_descendants(desc_storage, 3) >= 3
        ):
            lvl = 4
        elif (
            total_desc >= 100
            and direct_desc >= 5
            and get_descendants(desc_storage, 2) >= 3
        ):
            lvl = 3
        elif total_desc >= 20 and direct_desc >= 3:
            lvl = 2

        return lvl

    def update_lvl(self, save: bool = True):
        lvl = ReferalUserModel.calculate_user_lvl(
            total_desc=self.total_descendants,
            direct_desc=self.direct_descendants,
            desc_storage=self,
            get_descendants=ReferalUserModel.get_direct_descendants_amount,
        )

        if lvl != self.referal_lvl:
            self.referal_lvl = lvl
            if save:
                self.save(
                    update_fields=("referal_lvl",),
                )

    def recursively_update_parent_lvls(self):
        if self.invited_by:
            self.invited_by.update_lvl()
            self.invited_by.recursively_update_parent_lvls()

    def grant_indirect_referal_deposit_bonuses(self, from_deposit:bool) -> Optional[Decimal]:
        """Grant deposit bonus to parent, after user obtained its own"""

        print("Attempting to grant indirect referal deposit bonuses")

        # I assume this one is not recursive?
        if not self.invited_by:
            return

        referal_lvl = self.referal_lvl

        if referal_lvl >= 3:
            if self.invited_by.referal_lvl <= referal_lvl:
                # Not doing anything, as members of lvl 3 or above don't grant
                # referal deposit money if their level match or beat their
                # inviteer's lvl
                return
        else:
            # I think there are some cases when this may not work the intended way?
            # Not quite sure, just a thought that struggled my mind #TODO

            bonus_money = Decimal(0.00)

            if self.invited_by.referal_lvl == 2:
                if referal_lvl == 1:
                    bonus_money = Decimal(10.00)
            elif self.invited_by.referal_lvl == 3:
                if referal_lvl == 1:
                    bonus_money = Decimal(20.00)
                elif referal_lvl == 2:
                    bonus_money = Decimal(10.00)
            elif self.invited_by.referal_lvl == 4:
                if referal_lvl == 1:
                    bonus_money = Decimal(30.00)
                elif referal_lvl == 2:
                    bonus_money = Decimal(20.00)
                elif referal_lvl == 3:
                    bonus_money = Decimal(10.00)
            elif self.invited_by.referal_lvl == 5:
                if referal_lvl == 1:
                    bonus_money = Decimal(35.00)
                elif referal_lvl == 2:
                    bonus_money = Decimal(25.00)
                elif referal_lvl == 3:
                    bonus_money = Decimal(15.00)
                elif referal_lvl == 4:
                    bonus_money = Decimal(5.00)
            elif self.invited_by.referal_lvl == 6:
                if referal_lvl == 1:
                    bonus_money = Decimal(40.00)
                elif referal_lvl == 2:
                    bonus_money = Decimal(30.00)
                elif referal_lvl == 3:
                    bonus_money = Decimal(20.00)
                elif referal_lvl == 4:
                    bonus_money = Decimal(10.00)
                elif referal_lvl == 5:
                    bonus_money = Decimal(5.00)

            if bonus_money > 0:
                print(
                    f"Granting {bonus_money} bonuses to {self.invited_by.referal_id} as indirect deposit bonus"
                )
                self.invited_by.bonus_deposit += bonus_money
                self.invited_by.save(update_fields=("bonus_deposit",))


            total_bonuses = bonus_money
            parent_bonuses = ReferalUserModel.grant_indirect_referal_deposit_bonuses(
                self.invited_by,
                from_deposit=False,
            )
            if parent_bonuses is not None:
                if not from_deposit:
                    self.bonus_deposit -= parent_bonuses
                    self.save(
                        update_fields=("bonus_deposit",)
                    )
                else:
                    total_bonuses += parent_bonuses

            return total_bonuses

    def grant_direct_referal_deposit_bonuses(self):
        print("Attempting to grant direct referal deposit bonuses")

        if self.invited_by:
            bonus_money = Decimal(0.00)
            if self.invited_by.referal_lvl == 1:
                bonus_money = Decimal(30.00)
            elif self.invited_by.referal_lvl == 2:
                bonus_money = Decimal(40.00)
            elif self.invited_by.referal_lvl == 3:
                bonus_money = Decimal(50.00)
            elif self.invited_by.referal_lvl == 4:
                bonus_money = Decimal(60.00)
            elif self.invited_by.referal_lvl == 5:
                bonus_money = Decimal(65.00)
            elif self.invited_by.referal_lvl == 6:
                bonus_money = Decimal(70.00)

            reduce_by: Decimal = bonus_money
            indirect_reduce: Optional[
                Decimal
            ] = self.invited_by.grant_indirect_referal_deposit_bonuses(True)
            if indirect_reduce is not None:
                reduce_by += indirect_reduce
            self.deposit -= reduce_by
            self.save(update_fields=("deposit",))

            print(
                f"Granting {bonus_money} to {self.invited_by.referal_id} as direct deposit bonus"
            )
            self.invited_by.bonus_deposit += bonus_money
            self.invited_by.save(
                update_fields=("bonus_deposit",),
            )

    # This may be slow if we create multiple users at once without batch_create
    # However, during normal workflow it *should* be fine
    @hook(
        AFTER_CREATE,
        on_commit=True,
    )
    def perform_after_create_hook(self):
        self.recursively_update_parent_lvls()

    def __str__(self):
        return (
            f"id: {self.referal_id}, "
            f"deposit: {self.deposit}, "
            f"lvl: V{self.referal_lvl}"
        )
