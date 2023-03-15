import logging
from pathlib import Path
from typing import Union, Optional, List, Tuple, Generator
from decimal import Decimal
from users.models import ReferalUserModel
from json import load

log = logging.getLogger(__name__)


def _get_descendants_from_list(storage: list, lvl: int) -> int:
    return len([i for i in storage if i == lvl])


def _get_flat_user_data_from_json(
    d: dict, ref_list: list, invited_by: Optional[ReferalUserModel] = None
) -> Tuple[int, int]:
    # No safety checks for format validness, for now
    ref_id = d["id"]
    user_info = [ref_id, invited_by]
    ref_list.append(user_info)

    direct_desc = len(d["refs"])
    total_desc = direct_desc
    direct_desc_levels = []

    desc_data = []

    if isinstance(d["refs"], list) and direct_desc > 0:
        for i in d["refs"]:
            desc_count, desc_lvl = _get_flat_user_data_from_json(
                d=i,
                invited_by=ref_id,
                ref_list=ref_list,
            )
            direct_desc_levels.append(desc_lvl)
            total_desc += desc_count

    lvl = ReferalUserModel.calculate_user_lvl(
        total_desc=total_desc,
        direct_desc=direct_desc,
        desc_storage=direct_desc_levels,
        get_descendants=_get_descendants_from_list,
    )

    user_info.append(total_desc)
    user_info.append(lvl)

    return total_desc, lvl


def _batch_update_users(user_data):
    for i in user_data:
        instance = ReferalUserModel.objects.get(referal_id=i[0])
        referal_id = i[1]
        if referal_id is not None:
            instance.invited_by = ReferalUserModel.objects.get(referal_id=referal_id)
        instance.referal_lvl = i[3]
        instance.deposit = 120
        yield instance


def grant_indirect_referal_deposit_bonuses(
    item: dict, storage: dict
) -> Optional[Decimal]:
    """Grant deposit bonus to parent, after user obtained its own"""

    invited_by = item["invited_by"]
    if invited_by is None:
        return
    else:
        invited_by = storage[invited_by]

    referal_lvl = item["referal_lvl"]
    invited_by_lvl = invited_by["referal_lvl"]

    if referal_lvl >= 3:
        if invited_by_lvl <= referal_lvl:
            return
    else:
        # I think there are some cases when this may not work the intended way?
        # Not quite sure, just a thought that struggled my mind #TODO

        bonus_money = Decimal(0.00)

        if invited_by_lvl == 2:
            if referal_lvl == 1:
                bonus_money = Decimal(10.00)
        elif invited_by_lvl == 3:
            if referal_lvl == 1:
                bonus_money = Decimal(20.00)
            elif referal_lvl == 2:
                bonus_money = Decimal(10.00)
        elif invited_by_lvl == 4:
            if referal_lvl == 1:
                bonus_money = Decimal(30.00)
            elif referal_lvl == 2:
                bonus_money = Decimal(20.00)
            elif referal_lvl == 3:
                bonus_money = Decimal(10.00)
        elif invited_by_lvl == 5:
            if referal_lvl == 1:
                bonus_money = Decimal(35.00)
            elif referal_lvl == 2:
                bonus_money = Decimal(25.00)
            elif referal_lvl == 3:
                bonus_money = Decimal(15.00)
            elif referal_lvl == 4:
                bonus_money = Decimal(5.00)
        elif invited_by_lvl == 6:
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
            invited_by["bonus_deposit"] += bonus_money

        return bonus_money


def grant_direct_referal_deposit_bonuses(i: dict, storage: dict):
    if i["invited_by"] is not None:
        invited_by = storage[i["invited_by"]]
        bonus_money = Decimal(0.00)

        invited_by_lvl = invited_by["referal_lvl"]

        if invited_by_lvl == 1:
            bonus_money = Decimal(30.00)
        elif invited_by_lvl == 2:
            bonus_money = Decimal(40.00)
        elif invited_by_lvl == 3:
            bonus_money = Decimal(50.00)
        elif invited_by_lvl == 4:
            bonus_money = Decimal(60.00)
        elif invited_by_lvl == 5:
            bonus_money = Decimal(65.00)
        elif invited_by_lvl == 6:
            bonus_money = Decimal(70.00)

        reduce_by: Decimal = bonus_money
        indirect_reduce: Optional[Decimal] = grant_indirect_referal_deposit_bonuses(
            invited_by, storage
        )
        if indirect_reduce is not None:
            reduce_by += indirect_reduce
        i["deposit"] -= reduce_by

        invited_by["bonus_deposit"] += bonus_money


def _batch_update_ref_rewards(references: dict):
    for i in references.values():
        _id = i.pop("id")
        instance = ReferalUserModel.objects.get(id=_id)
        instance.deposit = i["deposit"]
        instance.bonus_deposit = i["bonus_deposit"]
        yield instance


def add_users_from_json(path_to_json: Union[str, Path]):
    with open(path_to_json, "r") as fp:
        data = load(fp)

    print("Fetching users")
    user_data = []
    _get_flat_user_data_from_json(
        d=data,
        ref_list=user_data,
    )

    print("Creating users")
    create_user_data = (ReferalUserModel(referal_id=i[0]) for i in user_data)
    ReferalUserModel.objects.bulk_create(create_user_data)

    print("Updating users")
    ReferalUserModel.objects.bulk_update(
        _batch_update_users(user_data),
        fields=(
            "invited_by",
            "referal_lvl",
            "deposit",
        ),
    )

    print("Granting referal bonuses (may take a while)")
    references = {}
    for i in ReferalUserModel.objects.all():
        references[i.id] = {
            "id": i.id,
            "invited_by": i.invited_by.id if i.invited_by else None,
            "referal_lvl": i.referal_lvl,
            "deposit": i.deposit,
            "bonus_deposit": i.bonus_deposit,
        }

    for i in references.keys():
        grant_direct_referal_deposit_bonuses(references[i], references)

    ReferalUserModel.objects.bulk_update(
        _batch_update_ref_rewards(references),
        fields=(
            "deposit",
            "bonus_deposit",
        ),
    )

    print("Done")
