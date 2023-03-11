import logging
from pathlib import Path
from typing import Union, Optional
from users.models import ReferalUserModel
from json import load

log = logging.getLogger(__name__)

def _add_user_from_dict(d: dict, invited_by: Optional[ReferalUserModel] = None):
    # No safety checks for format validness, for now
    ref_id = d["id"]
    print(f"Adding user with ref id {ref_id}")
    ref_model = ReferalUserModel.objects.get_or_create(
        referal_id = ref_id,
        invited_by=invited_by,
    )[0]

    # This will take a while, coz its not a bulk create.
    # But going this way since bulk create does not trigger signals
    if isinstance(d["refs"], list) and len(d["refs"]) > 0:
        for i in d["refs"]:
            _add_user_from_dict(
                d = i,
                invited_by = ref_model,
            )


def add_users_from_json(path_to_json: Union[str, Path]):
    with open(path_to_json, "r") as fp:
        data = load(fp)

    _add_user_from_dict(data)

    print(ReferalUserModel.objects.count())

    # for


    # Now, lets build relations
