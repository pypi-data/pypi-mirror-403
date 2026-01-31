from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

from ..attachment import Attachment

if TYPE_CHECKING:
    from ..profile_post import ProfilePost
    from ..user import User


__all__ = ("ProfilePostComment",)


class ProfilePostComment(BaseModel):
    username: str
    message_parsed: str  # HTML parsed version of the message contents.
    can_edit: bool
    can_soft_delete: bool
    can_hard_delete: bool
    can_react: bool
    can_view_attachments: bool
    Attachments: Optional[List[Attachment]] = Field(
        alias="Attachments", default=None
    )  # 	 Attachments to this profile post, if it has any.
    ProfilePost: Optional[
        "ProfilePost"
    ]  #  If requested by context, the profile post this comment relates to.
    is_reacted_to: bool  # True if the viewing user has reacted to this content
    visitor_reaction_id: Optional[
        int
    ]  # If the viewer reacted, the ID of the reaction they used
    profile_post_comment_id: int
    profile_post_id: int
    user_id: int
    comment_date: int
    message: str
    message_state: str
    warning_message: str
    reaction_score: int
    User: "User"
