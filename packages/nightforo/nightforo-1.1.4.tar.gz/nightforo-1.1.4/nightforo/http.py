"""HTTP client for XenForo API."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO

import aiohttp

from .endpoint import HTTPMethod
from .endpoints import (
    endpoint_alert,
    endpoint_alert_mark,
    endpoint_alerts,
    endpoint_alerts_mark_all,
    endpoint_attachment,
    endpoint_attachment_data,
    endpoint_attachment_thumbnail,
    endpoint_attachments,
    endpoint_attachments_new_key,
    endpoint_auth,
    endpoint_auth_from_session,
    endpoint_auth_login_token,
    endpoint_conversation,
    endpoint_conversation_invite,
    endpoint_conversation_mark_read,
    endpoint_conversation_mark_unread,
    endpoint_conversation_message,
    endpoint_conversation_message_react,
    endpoint_conversation_messages,
    endpoint_conversation_messages_list,
    endpoint_conversation_star,
    endpoint_conversations,
    endpoint_demote,
    endpoint_demote_user,
    endpoint_forum,
    endpoint_forum_mark_read,
    endpoint_forum_threads,
    endpoint_index,
    endpoint_me,
    endpoint_me_avatar,
    endpoint_me_email,
    endpoint_me_password,
    endpoint_node,
    endpoint_nodes,
    endpoint_nodes_flattened,
    endpoint_post,
    endpoint_post_mark_solution,
    endpoint_post_react,
    endpoint_post_vote,
    endpoint_posts,
    endpoint_profile_post,
    endpoint_profile_post_comment,
    endpoint_profile_post_comment_react,
    endpoint_profile_post_comments,
    endpoint_profile_post_comments_list,
    endpoint_profile_post_react,
    endpoint_profile_posts,
    endpoint_promote,
    endpoint_promote_user,
    endpoint_stats,
    endpoint_thread,
    endpoint_thread_change_type,
    endpoint_thread_mark_read,
    endpoint_thread_move,
    endpoint_thread_posts,
    endpoint_thread_vote,
    endpoint_threads,
    endpoint_user,
    endpoint_user_avatar,
    endpoint_user_profile_posts,
    endpoint_users,
    endpoint_users_find_email,
    endpoint_users_find_name,
)
from .errors import UnsupportedEndpointMethodError, XenForoError
from .types.file import XenforoFile

if TYPE_CHECKING:
    from typing import Any

    from pydantic import BaseModel

    from .endpoint import Endpoint
    from .types.alert.params import (
        AlertMarkParams,
        AlertSendParams,
        AlertsGetParams,
        AlertsMarkAllParams,
    )
    from .types.attachment.params import (
        AttachmentsCreateNewKeyParams,
        AttachmentsGetParams,
        AttachmentUploadParams,
    )
    from .types.auth.params import (
        AuthFromSessionParams,
        AuthLoginTokenParams,
        AuthTestParams,
    )
    from .types.conversation.params import (
        ConversationCreateParams,
        ConversationDeleteParams,
        ConversationGetMessagesParams,
        ConversationGetParams,
        ConversationInviteParams,
        ConversationMarkReadParams,
        ConversationsGetParams,
        ConversationStarParams,
        ConversationUpdateParams,
    )
    from .types.conversation_message.params import (
        ConversationMessageReactParams,
        ConversationMessageReplyParams,
        ConversationMessageUpdateParams,
    )
    from .types.forum.params import (
        ForumGetParams,
        ForumMarkReadParams,
        ForumThreadsGetParams,
    )
    from .types.me.params import (
        MeEmailUpdateParams,
        MePasswordUpdateParams,
        MeUpdateParams,
    )
    from .types.node.params import (
        NodeCreateParams,
        NodeDeleteParams,
        NodeUpdateParams,
    )
    from .types.post.params import (
        PostCreateParams,
        PostDeleteParams,
        PostReactParams,
        PostUpdateParams,
        PostVoteParams,
    )
    from .types.profile_post.params import (
        ProfilePostCreateParams,
        ProfilePostDeleteParams,
        ProfilePostGetParams,
        ProfilePostReactParams,
        ProfilePostUpdateParams,
    )
    from .types.profile_post_comment.params import (
        ProfilePostCommentCreateParams,
        ProfilePostCommentDeleteParams,
        ProfilePostCommentReactParams,
        ProfilePostCommentsGetParams,
        ProfilePostCommentUpdateParams,
    )
    from .types.thread.params import (
        ThreadChangeTypeParams,
        ThreadCreateParams,
        ThreadDeleteParams,
        ThreadGetParams,
        ThreadMarkReadParams,
        ThreadMoveParams,
        ThreadPostsGetParams,
        ThreadsGetParams,
        ThreadUpdateParams,
        ThreadVoteParams,
    )
    from .types.user.params import (
        UserCreateParams,
        UserDemoteParams,
        UserGetParams,
        UserProfilePostsGetParams,
        UserPromoteParams,
        UserRenameParams,
        UsersFindEmailParams,
        UsersFindNameParams,
        UsersGetParams,
        UserUpdateParams,
    )


class HTTPClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def _request(
        self,
        endpoint: Endpoint,
        method: HTTPMethod,
        params: BaseModel | None = None,
        content_type: str = "application/json",
        file: XenforoFile | None = None,
    ) -> Any:
        headers: dict[str, str] = {}
        req: dict[str, Any] = {}

        headers["XF-Api-Key"] = self.api_key

        req["headers"] = headers

        data = None

        if params is not None:
            dump = params.model_dump(by_alias=True, exclude_none=True)

            if content_type == "application/json":
                headers["Content-Type"] = content_type
                req["json"] = dump

            elif content_type == "multipart/form-data":
                data = aiohttp.FormData()
                for k, v in dump.items():
                    data.add_field(name=k, value=str(v))

        if file is not None:
            if data is None:
                data = aiohttp.FormData()

            data.add_field(file.name, file.stream)

        if method not in endpoint.supported_methods:
            raise UnsupportedEndpointMethodError(method)

        async with aiohttp.ClientSession() as session, session.request(
            method.value, endpoint.url, data=data, **req
        ) as response:
            try:
                payload = await response.json()
            except aiohttp.ContentTypeError:
                raise XenForoError(  # noqa: B904
                    f"Response is not JSON. Status: {response.status}"
                )

            if (errors := payload.get("errors", None)) is not None:
                raise XenForoError(errors)

            if (errors := payload.get("error", None)) is not None:
                raise XenForoError(errors)

            return payload

    # ============================================================================
    # ALERTS
    # ============================================================================

    async def get_alerts(self, params: AlertsGetParams | None = None) -> Any:
        return await self._request(
            endpoint=endpoint_alerts, method=HTTPMethod.GET, params=params
        )

    async def send_alert(self, params: AlertSendParams) -> Any:
        return await self._request(
            endpoint=endpoint_alerts, method=HTTPMethod.POST, params=params
        )

    async def mark_all_alerts(self, params: AlertsMarkAllParams) -> Any:
        return await self._request(
            endpoint=endpoint_alerts_mark_all,
            method=HTTPMethod.POST,
            params=params,
        )

    async def get_alert(self, alert_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_alert(alert_id), method=HTTPMethod.GET
        )

    async def mark_alert(self, alert_id: int, params: AlertMarkParams) -> Any:
        return await self._request(
            endpoint=endpoint_alert_mark(alert_id),
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # ATTACHMENTS
    # ============================================================================

    async def get_attachments(self, params: AttachmentsGetParams) -> Any:
        return await self._request(
            endpoint=endpoint_attachments, method=HTTPMethod.GET, params=params
        )

    async def upload_attachment(
        self, params: AttachmentUploadParams, attachment: BinaryIO
    ) -> Any:
        file = XenforoFile(attachment, "attachment")
        return await self._request(
            endpoint=endpoint_attachments,
            method=HTTPMethod.POST,
            params=params,
            file=file,
        )

    async def create_attachment_key(
        self,
        params: AttachmentsCreateNewKeyParams,
        attachment: BinaryIO | None,
    ) -> Any:
        file = XenforoFile(attachment, "attachment") if attachment else None
        return await self._request(
            endpoint=endpoint_attachments_new_key,
            method=HTTPMethod.POST,
            params=params,
            file=file,
        )

    async def get_attachment(self, attachment_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_attachment(attachment_id), method=HTTPMethod.GET
        )

    async def delete_attachment(self, attachment_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_attachment(attachment_id),
            method=HTTPMethod.DELETE,
        )

    async def get_attachment_data(self, attachment_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_attachment_data(attachment_id),
            method=HTTPMethod.GET,
        )

    async def get_attachment_thumbnail(self, attachment_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_attachment_thumbnail(attachment_id),
            method=HTTPMethod.GET,
        )

    # ============================================================================
    # AUTH
    # ============================================================================

    async def test_auth(self, params: AuthTestParams) -> Any:
        return await self._request(
            endpoint=endpoint_auth, method=HTTPMethod.POST, params=params
        )

    async def auth_from_session(self, params: AuthFromSessionParams) -> Any:
        return await self._request(
            endpoint=endpoint_auth_from_session,
            method=HTTPMethod.POST,
            params=params,
        )

    async def create_login_token(self, params: AuthLoginTokenParams) -> Any:
        return await self._request(
            endpoint=endpoint_auth_login_token,
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # CONVERSATION MESSAGES
    # ============================================================================

    async def reply_conversation_message(
        self, params: ConversationMessageReplyParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_messages,
            method=HTTPMethod.POST,
            params=params,
        )

    async def get_conversation_message(self, message_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_message(message_id),
            method=HTTPMethod.GET,
        )

    async def update_conversation_message(
        self, message_id: int, params: ConversationMessageUpdateParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_message(message_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def react_conversation_message(
        self, message_id: int, params: ConversationMessageReactParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_message_react(message_id),
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # CONVERSATIONS
    # ============================================================================

    async def get_conversations(
        self, params: ConversationsGetParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversations,
            method=HTTPMethod.GET,
            params=params,
        )

    async def create_conversation(
        self, params: ConversationCreateParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversations,
            method=HTTPMethod.POST,
            params=params,
        )

    async def get_conversation(
        self,
        conversation_id: int,
        params: ConversationGetParams | None = None,
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation(conversation_id),
            method=HTTPMethod.GET,
            params=params,
        )

    async def update_conversation(
        self, conversation_id: int, params: ConversationUpdateParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation(conversation_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def delete_conversation(
        self,
        conversation_id: int,
        params: ConversationDeleteParams | None = None,
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation(conversation_id),
            method=HTTPMethod.DELETE,
            params=params,
        )

    async def invite_conversation(
        self, conversation_id: int, params: ConversationInviteParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_invite(conversation_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def mark_conversation_read(
        self,
        conversation_id: int,
        params: ConversationMarkReadParams | None = None,
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_mark_read(conversation_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def mark_conversation_unread(self, conversation_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_mark_unread(conversation_id),
            method=HTTPMethod.POST,
        )

    async def get_conversation_messages(
        self,
        conversation_id: int,
        params: ConversationGetMessagesParams | None = None,
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_messages_list(conversation_id),
            method=HTTPMethod.GET,
            params=params,
        )

    async def star_conversation(
        self, conversation_id: int, params: ConversationStarParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_conversation_star(conversation_id),
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # FORUMS
    # ============================================================================

    async def get_forum(
        self, forum_id: int, params: ForumGetParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_forum(forum_id),
            method=HTTPMethod.GET,
            params=params,
        )

    async def mark_forum_read(
        self, forum_id: int, params: ForumMarkReadParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_forum_mark_read(forum_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def get_forum_threads(
        self, forum_id: int, params: ForumThreadsGetParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_forum_threads(forum_id),
            method=HTTPMethod.GET,
            params=params,
        )

    # ============================================================================
    # INDEX
    # ============================================================================

    async def get_index(self) -> Any:
        return await self._request(
            endpoint=endpoint_index, method=HTTPMethod.GET
        )

    # ============================================================================
    # ME (Current User)
    # ============================================================================

    async def get_me(self) -> Any:
        return await self._request(endpoint=endpoint_me, method=HTTPMethod.GET)

    async def update_me(self, params: MeUpdateParams) -> Any:
        return await self._request(
            endpoint=endpoint_me, method=HTTPMethod.POST, params=params
        )

    async def update_my_avatar(self, avatar: BinaryIO) -> Any:
        file = XenforoFile(avatar, "avatar")
        return await self._request(
            endpoint=endpoint_me_avatar,
            method=HTTPMethod.POST,
            file=file,
        )

    async def delete_my_avatar(self) -> Any:
        return await self._request(
            endpoint=endpoint_me_avatar, method=HTTPMethod.DELETE
        )

    async def update_my_email(self, params: MeEmailUpdateParams) -> Any:
        return await self._request(
            endpoint=endpoint_me_email, method=HTTPMethod.POST, params=params
        )

    async def update_my_password(self, params: MePasswordUpdateParams) -> Any:
        return await self._request(
            endpoint=endpoint_me_password,
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # NODES
    # ============================================================================

    async def get_nodes(self) -> Any:
        return await self._request(
            endpoint=endpoint_nodes, method=HTTPMethod.GET
        )

    async def create_node(self, params: NodeCreateParams) -> Any:
        return await self._request(
            endpoint=endpoint_nodes, method=HTTPMethod.POST, params=params
        )

    async def get_nodes_flattened(self) -> Any:
        return await self._request(
            endpoint=endpoint_nodes_flattened, method=HTTPMethod.GET
        )

    async def get_node(self, node_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_node(node_id), method=HTTPMethod.GET
        )

    async def update_node(self, node_id: int, params: NodeUpdateParams) -> Any:
        return await self._request(
            endpoint=endpoint_node(node_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def delete_node(
        self, node_id: int, params: NodeDeleteParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_node(node_id),
            method=HTTPMethod.DELETE,
            params=params,
        )

    # ============================================================================
    # POSTS
    # ============================================================================

    async def create_post(self, params: PostCreateParams) -> Any:
        return await self._request(
            endpoint=endpoint_posts,
            method=HTTPMethod.POST,
            params=params,
            content_type="multipart/form-data",
        )

    async def get_post(self, post_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_post(post_id), method=HTTPMethod.GET
        )

    async def update_post(self, post_id: int, params: PostUpdateParams) -> Any:
        return await self._request(
            endpoint=endpoint_post(post_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def delete_post(
        self, post_id: int, params: PostDeleteParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_post(post_id),
            method=HTTPMethod.DELETE,
            params=params,
        )

    async def mark_post_solution(self, post_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_post_mark_solution(post_id),
            method=HTTPMethod.POST,
        )

    async def react_post(self, post_id: int, params: PostReactParams) -> Any:
        return await self._request(
            endpoint=endpoint_post_react(post_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def vote_post(self, post_id: int, params: PostVoteParams) -> Any:
        return await self._request(
            endpoint=endpoint_post_vote(post_id),
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # PROFILE POST COMMENTS
    # ============================================================================

    async def create_profile_post_comment(
        self, params: ProfilePostCommentCreateParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post_comments,
            method=HTTPMethod.POST,
            params=params,
        )

    async def get_profile_post_comment(self, comment_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post_comment(comment_id),
            method=HTTPMethod.GET,
        )

    async def update_profile_post_comment(
        self, comment_id: int, params: ProfilePostCommentUpdateParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post_comment(comment_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def delete_profile_post_comment(
        self,
        comment_id: int,
        params: ProfilePostCommentDeleteParams | None = None,
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post_comment(comment_id),
            method=HTTPMethod.DELETE,
            params=params,
        )

    async def react_profile_post_comment(
        self, comment_id: int, params: ProfilePostCommentReactParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post_comment_react(comment_id),
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # PROFILE POSTS
    # ============================================================================

    async def create_profile_post(
        self, params: ProfilePostCreateParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_posts,
            method=HTTPMethod.POST,
            params=params,
        )

    async def get_profile_post(
        self,
        profile_post_id: int,
        params: ProfilePostGetParams | None = None,
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post(profile_post_id),
            method=HTTPMethod.GET,
            params=params,
        )

    async def update_profile_post(
        self, profile_post_id: int, params: ProfilePostUpdateParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post(profile_post_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def delete_profile_post(
        self,
        profile_post_id: int,
        params: ProfilePostDeleteParams | None = None,
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post(profile_post_id),
            method=HTTPMethod.DELETE,
            params=params,
        )

    async def get_profile_post_comments(
        self,
        profile_post_id: int,
        params: ProfilePostCommentsGetParams | None = None,
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post_comments_list(profile_post_id),
            method=HTTPMethod.GET,
            params=params,
        )

    async def react_profile_post(
        self, profile_post_id: int, params: ProfilePostReactParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_profile_post_react(profile_post_id),
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # STATS
    # ============================================================================

    async def get_stats(self) -> Any:
        return await self._request(
            endpoint=endpoint_stats, method=HTTPMethod.GET
        )

    # ============================================================================
    # THREADS
    # ============================================================================

    async def get_threads(self, params: ThreadsGetParams | None = None) -> Any:
        return await self._request(
            endpoint=endpoint_threads, method=HTTPMethod.GET, params=params
        )

    async def create_thread(self, params: ThreadCreateParams) -> Any:
        return await self._request(
            endpoint=endpoint_threads, method=HTTPMethod.POST, params=params
        )

    async def get_thread(
        self, thread_id: int, params: ThreadGetParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_thread(thread_id),
            method=HTTPMethod.GET,
            params=params,
        )

    async def update_thread(
        self, thread_id: int, params: ThreadUpdateParams
    ) -> Any:
        content_type = "multipart/form-data"

        return await self._request(
            endpoint=endpoint_thread(thread_id),
            method=HTTPMethod.POST,
            params=params,
            content_type=content_type
        )

    async def delete_thread(
        self, thread_id: int, params: ThreadDeleteParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_thread(thread_id),
            method=HTTPMethod.DELETE,
            params=params,
        )

    async def change_thread_type(
        self, thread_id: int, params: ThreadChangeTypeParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_thread_change_type(thread_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def mark_thread_read(
        self, thread_id: int, params: ThreadMarkReadParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_thread_mark_read(thread_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def move_thread(
        self, thread_id: int, params: ThreadMoveParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_thread_move(thread_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def get_thread_posts(
        self, thread_id: int, params: ThreadPostsGetParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_thread_posts(thread_id),
            method=HTTPMethod.GET,
            params=params,
        )

    async def vote_thread(
        self, thread_id: int, params: ThreadVoteParams
    ) -> Any:
        return await self._request(
            endpoint=endpoint_thread_vote(thread_id),
            method=HTTPMethod.POST,
            params=params,
        )

    # ============================================================================
    # USERS
    # ============================================================================

    async def get_users(self, params: UsersGetParams | None = None) -> Any:
        return await self._request(
            endpoint=endpoint_users, method=HTTPMethod.GET, params=params
        )

    async def create_user(self, params: UserCreateParams) -> Any:
        return await self._request(
            endpoint=endpoint_users, method=HTTPMethod.POST, params=params
        )

    async def find_user_by_email(self, params: UsersFindEmailParams) -> Any:
        return await self._request(
            endpoint=endpoint_users_find_email,
            method=HTTPMethod.GET,
            params=params,
        )

    async def find_user_by_name(self, params: UsersFindNameParams) -> Any:
        return await self._request(
            endpoint=endpoint_users_find_name,
            method=HTTPMethod.GET,
            params=params,
        )

    async def get_user(
        self, user_id: int, params: UserGetParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_user(user_id),
            method=HTTPMethod.GET,
            params=params,
        )

    async def update_user(self, user_id: int, params: UserUpdateParams) -> Any:
        return await self._request(
            endpoint=endpoint_user(user_id),
            method=HTTPMethod.POST,
            params=params,
        )

    async def delete_user(
        self, user_id: int, params: UserRenameParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_user(user_id),
            method=HTTPMethod.DELETE,
            params=params,
        )

    async def update_user_avatar(self, user_id: int, avatar: BinaryIO) -> Any:
        file = XenforoFile(avatar, "avatar")
        return await self._request(
            endpoint=endpoint_user_avatar(user_id),
            method=HTTPMethod.POST,
            file=file,
        )

    async def delete_user_avatar(self, user_id: int) -> Any:
        return await self._request(
            endpoint=endpoint_user_avatar(user_id), method=HTTPMethod.DELETE
        )

    async def get_user_profile_posts(
        self, user_id: int, params: UserProfilePostsGetParams | None = None
    ) -> Any:
        return await self._request(
            endpoint=endpoint_user_profile_posts(user_id),
            method=HTTPMethod.GET,
            params=params,
        )

    # ============================================================================
    # ACTIONS
    # ============================================================================

    async def get_demote_groups(self) -> Any:
        return await self._request(
            endpoint=endpoint_demote, method=HTTPMethod.GET
        )

    async def demote_user(self, user_id: int, params: UserDemoteParams) -> Any:
        content_type = "multipart/form-data"

        return await self._request(
            endpoint=endpoint_demote_user(user_id),
            method=HTTPMethod.POST,
            params=params,
            content_type=content_type,
        )

    async def get_promote_groups(self) -> Any:
        return await self._request(
            endpoint=endpoint_promote, method=HTTPMethod.GET
        )

    async def promote_user(
        self, user_id: int, params: UserPromoteParams
    ) -> Any:
        content_type = "multipart/form-data"

        return await self._request(
            endpoint=endpoint_promote_user(user_id),
            method=HTTPMethod.POST,
            params=params,
            content_type=content_type,
        )
