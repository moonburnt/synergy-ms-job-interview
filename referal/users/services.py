import logging
from pathlib import Path
from typing import Union, Optional
from users.models import ReferalUserModel
from json import load

log = logging.getLogger(__name__)


def _update_inveteers_from_dict(d: dict, invited_by: Optional[ReferalUserModel] = None, ref_list:Optional[list] = None) -> list:
    if not ref_list:
        ref_list = []

    ref_id = d["id"]
    print(f"Updating inviteer of user with ref id {ref_id}")
    ref_model = ReferalUserModel.objects.get(
        referal_id=ref_id,
    )
    ref_model.invited_by = invited_by
    ref_list.append(ref_model)
    # ref_model.save(
    #     update_fields = ("invited_by",)
    # )

    # This will take a while, coz its not a bulk create.
    # But going this way since bulk create does not trigger signals
    if isinstance(d["refs"], list) and len(d["refs"]) > 0:
        for i in d["refs"]:
            _update_inveteers_from_dict(
                d=i,
                invited_by=ref_model,
                ref_list = ref_list
            )

    return ref_list

def _get_bulk_add_user_data_from_json(d: dict, ref_list:Optional[list] = None) -> list:
    if not ref_list:
        ref_list = []
    # No safety checks for format validness, for now
    ref_id = d["id"]
    print(f"Adding user with ref id {ref_id}")
    ref_list.append(
        ReferalUserModel(referal_id = ref_id)
    )

    # This will take a while, coz its not a bulk create.
    # But going this way since bulk create does not trigger signals
    if isinstance(d["refs"], list) and len(d["refs"]) > 0:
        for i in d["refs"]:
            _get_bulk_add_user_data_from_json(
                d = i,
                ref_list = ref_list,
            )

    return ref_list


def add_users_from_json(path_to_json: Union[str, Path]):
    with open(path_to_json, "r") as fp:
        data = load(fp)

    # user_data = _get_bulk_add_user_data_from_json(
    #     d = data,
    # )

    # instances = ReferalUserModel.objects.bulk_create(user_data)
    # instances = ReferalUserModel.objects.all()


    # instances = _update_inveteers_from_dict(d = data)
    # ReferalUserModel.objects.bulk_update(instances, fields=("invited_by",))

    # print(ReferalUserModel.objects.filter(invited_by__isnull=False).count())


    print('a')
    update_lvls_instances = ReferalUserModel.objects.all()
    update_lvls_amount = ReferalUserModel.objects.count()
    curr: int = 0
    for i in update_lvls_instances:
        curr+=1
        print(f"Updating {curr}/{update_lvls_amount}")
        i.recursively_update_parent_lvls(save=False)

    print('aa')

    print("Done")
