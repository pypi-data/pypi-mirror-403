from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

__all__ = (
    "DateOfBirth",
    "Option",
    "Privacy",
    "Profile",
    "ProfileAvatars",
    "ProfileBanners",
    "User",
)


class DateOfBirth(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None


class ProfileAvatars(BaseModel):
    o: Optional[str] = None
    h: Optional[str] = None
    l: Optional[str] = None  # noqa: E741
    m: Optional[str] = None
    s: Optional[str] = None


class ProfileBanners(BaseModel):
    l: Optional[str] = None  # noqa: E741
    m: Optional[str] = None


class Option(BaseModel):
    creation_watch_state: Optional[str] = None
    interaction_watch_state: Optional[str] = None
    content_show_signature: Optional[bool] = None
    email_on_conversation: Optional[bool] = None
    push_on_conversation: Optional[bool] = None
    receive_admin_email: Optional[bool] = None
    show_dob_year: Optional[bool] = None
    show_dob_date: Optional[bool] = None


class Profile(BaseModel):
    location: Optional[str] = None
    website: Optional[str] = None
    about: Optional[str] = None
    signature: Optional[str] = None


class Privacy(BaseModel):
    allow_view_profile: Optional[str] = None
    allow_post_profile: Optional[str] = None
    allow_receive_news_feed: Optional[str] = None
    allow_send_personal_conversation: Optional[str] = None
    allow_view_identities: Optional[str] = None


class User(BaseModel):
    user_id: int
    username: str

    activity_visible: Optional[bool] = None
    age: Optional[int] = None
    alert_optout: Optional[List[str]] = None
    allow_post_profile: Optional[str] = None
    allow_receive_news_feed: Optional[str] = None
    allow_send_personal_conversation: Optional[str] = None
    allow_view_identities: Optional[str] = None
    allow_view_profile: Optional[str] = None
    avatar_urls: Optional[ProfileAvatars] = None
    profile_banner_urls: Optional[ProfileBanners] = None
    can_ban: Optional[bool] = None
    can_converse: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_follow: Optional[bool] = None
    can_ignore: Optional[bool] = None
    can_post_profile: Optional[bool] = None
    can_view_profile: Optional[bool] = None
    can_view_profile_posts: Optional[bool] = None
    can_warn: Optional[bool] = None
    content_show_signature: Optional[bool] = None
    creation_watch_state: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    custom_title: Optional[str] = None
    dob: Optional[DateOfBirth] = None
    email: Optional[str] = None
    email_on_conversation: Optional[bool] = None
    gravatar: Optional[str] = None
    interaction_watch_state: Optional[str] = None
    is_admin: Optional[bool] = None
    is_banned: Optional[bool] = None
    is_discouraged: Optional[bool] = None
    is_followed: Optional[bool] = None
    is_ignored: Optional[bool] = None
    is_moderator: Optional[bool] = None
    is_super_admin: Optional[bool] = None
    last_activity: Optional[int] = None
    location: Optional[str] = None
    push_on_conversation: Optional[bool] = None
    push_optout: Optional[List[str]] = None
    receive_admin_email: Optional[bool] = None
    secondary_group_ids: Optional[List[int]] = None
    show_dob_date: Optional[bool] = None
    show_dob_year: Optional[bool] = None
    signature: Optional[str] = None
    timezone: Optional[str] = None
    use_tfa: Optional[bool] = None
    user_group_id: Optional[int] = None
    user_state: Optional[str] = None

    user_title: Optional[Union[str, bool]] = None

    visible: Optional[bool] = None
    warning_points: Optional[int] = None
    website: Optional[str] = None
    view_url: Optional[str] = None
    message_count: Optional[int] = None
    question_solution_count: Optional[int] = None
    register_date: Optional[int] = None
    trophy_points: Optional[int] = None
    is_staff: Optional[bool] = None
    reaction_score: Optional[int] = None
    vote_score: Optional[int] = None
