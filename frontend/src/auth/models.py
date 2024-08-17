# Copyright Jonathan AW.
# Licensed under the MIT License.

from typing import List

from pydantic import BaseModel


class User(BaseModel):
    id: str
    username: str
    salt: int
    hashpassword: str
    permissions: List[str]
    graphragindexes: List[str]
    accountstatus: str
