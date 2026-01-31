from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

from ..attachment import Attachment

if TYPE_CHECKING:
    from ..profile_post_comment import ProfilePostComment
    from ..user import User

__all__ = ("ProfilePost",)


class ProfilePost(BaseModel):
    username: str
    message_parsed: str  # HTML parsed version of the message contents.
    can_edit: bool
    can_soft_delete: bool
    can_hard_delete: bool
    can_react: bool
    can_view_attachments: bool
    view_url: str
    profile_user: (
        Optional[
            "User"
        ]  # If requested by context, the user this profile post was left for.
    ) = Field(alias="ProfileUser", default=None)
    Attachments: Optional[List[Attachment]] = Field(
        alias="Attachments", default=None
    )  # 	 Attachments to this profile post, if it has any.
    latest_comments: Optional[List["ProfilePostComment"]] = Field(
        alias="LatestComments", default=None
    )  # If requested, the most recent comments on this profile post.
    is_reacted_to: bool  # True if the viewing user has reacted to this content
    visitor_reaction_id: Optional[
        int
    ]  # If the viewer reacted, the ID of the reaction they used
    profile_post_id: int
    profile_user_id: int
    user_id: int
    post_date: int
    message: str
    message_state: str
    warning_message: str
    comment_count: int
    first_comment_date: int
    last_comment_date: int
    reaction_score: int
    user: Optional["User"] = Field(alias="User", default=None)
