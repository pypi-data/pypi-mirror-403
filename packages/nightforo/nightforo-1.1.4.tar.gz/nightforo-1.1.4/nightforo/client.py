"""NightForo XenForo API Client."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO

from .errors import NoApiKeyProvidedError
from .http import HTTPClient
from .types.alert.response import (
    AlertGetResponse,
    AlertMarkResponse,
    AlertSendResponse,
    AlertsGetResponse,
    AlertsMarkAllResponse,
)
from .types.attachment.response import (
    AttachmentDeleteResponse,
    AttachmentGetDataResponse,
    AttachmentGetResponse,
    AttachmentGetThumbnailResponse,
    AttachmentsCreateNewKeyResponse,
    AttachmentsGetResponse,
    AttachmentUploadResponse,
)
from .types.auth.response import (
    AuthFromSessionResponse,
    AuthLoginTokenResponse,
    AuthTestResponse,
)
from .types.conversation.response import (
    ConversationCreateResponse,
    ConversationDeleteResponse,
    ConversationGetResponse,
    ConversationInviteResponse,
    ConversationMarkReadResponse,
    ConversationMarkUnreadResponse,
    ConversationMessagesGetResponse,
    ConversationsGetResponse,
    ConversationStarResponse,
    ConversationUpdateResponse,
)
from .types.conversation_message.response import (
    ConversationMessageGetResponse,
    ConversationMessageReactResponse,
    ConversationMessageReplyResponse,
    ConversationMessageUpdateResponse,
)
from .types.forum.response import (
    ForumGetResponse,
    ForumMarkReadResponse,
    ForumThreadsGetResponse,
)
from .types.me.response import (
    MeAvatarDeleteResponse,
    MeAvatarUpdateResponse,
    MeEmailUpdateResponse,
    MeGetResponse,
    MePasswordUpdateResponse,
    MeUpdateResponse,
)
from .types.node.response import (
    NodeCreateResponse,
    NodeDeleteResponse,
    NodeGetResponse,
    NodesFlattenedGetResponse,  # type: ignore  # noqa: F401
    NodesGetResponse,
    NodeUpdateResponse,
)
from .types.page.response import IndexGetResponse
from .types.post.response import (
    PostCreateResponse,
    PostDeleteResponse,
    PostGetResponse,
    PostMarkSolutionResponse,
    PostReactResponse,
    PostUpdateResponse,
    PostVoteResponse,
)
from .types.profile_post.response import (
    ProfilePostCommentsGetResponse,
    ProfilePostCreateResponse,
    ProfilePostDeleteResponse,
    ProfilePostGetResponse,
    ProfilePostReactResponse,
    ProfilePostUpdateResponse,
)
from .types.profile_post_comment.response import (
    ProfilePostCommentCreateResponse,
    ProfilePostCommentDeleteResponse,
    ProfilePostCommentGetResponse,
    ProfilePostCommentReactResponse,
    ProfilePostCommentUpdateResponse,
)
from .types.stats.response import StatsResponse
from .types.thread.response import (
    ThreadChangeTypeResponse,
    ThreadCreateResponse,
    ThreadDeleteResponse,
    ThreadGetResponse,
    ThreadMarkReadResponse,
    ThreadMoveResponse,
    ThreadPostsGetResponse,
    ThreadsGetResponse,
    ThreadUpdateResponse,
    ThreadVoteResponse,
)
from .types.user.params import UserDemoteParams, UserPromoteParams
from .types.user.response import (
    DemoteUserResponse,
    GetDemoteGroupsResponse,
    GetPromoteGroupsResponse,
    PromoteUserResponse,
    UserAvatarDeleteResponse,
    UserAvatarUpdateResponse,
    UserCreateResponse,
    UserDeleteResponse,
    UserFindEmailResponse,
    UserFindNameResponse,
    UserGetResponse,
    UserProfilePostsGetResponse,
    UsersGetResponse,
    UserUpdateResponse,
)

if TYPE_CHECKING:
    from .groups import ArzGuardGroupsIdsEnum
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
        UserGetParams,
        UserProfilePostsGetParams,
        UserRenameParams,
        UsersFindEmailParams,
        UsersFindNameParams,
        UsersGetParams,
        UserUpdateParams,
    )

__all__ = ("Client",)


class Client:
    """XenForo API Client

    Main client for interacting with XenForo REST API.

    Parameters
    ----------
    api_key : str
        XenForo API key for authentication

    Errors:
    ------
    NoApiKeyProvidedError
        If api_key is empty string
    """

    def __init__(self, api_key: str) -> None:
        if api_key == "":
            raise NoApiKeyProvidedError()

        self._http = HTTPClient(api_key)

    # ============================================================================
    # ALERTS
    # ============================================================================

    async def get_alerts(
        self, params: AlertsGetParams | None = None
    ) -> AlertsGetResponse:
        """GET alerts/ - Gets the API user's list of alerts

        Parameters
        ----------
        page : int, optional
            Page number of results
        cutoff : int, optional
            Unix timestamp of oldest alert to include
        unviewed : bool, optional
            If true, gets only unviewed alerts
        unread : bool, optional
            If true, gets only unread alerts

        Returns AlertsGetResponse:
        -------
        alerts : List[UserAlert]
            List of user alerts
        pagination : Pagination
            Pagination information
        """

        payload = await self._http.get_alerts(params)
        return AlertsGetResponse.model_validate(payload)

    async def send_alert(self, params: AlertSendParams) -> AlertSendResponse:
        """POST alerts/ - Sends an alert to the specified user

        Only available to super user keys.

        Parameters
        ----------
        to_user_id : int
            ID of the user to receive the alert
        alert : str
            Text of the alert
        from_user_id : int, optional
            If provided, the user to send the alert from. Otherwise, uses the current API user. May be 0 for an anonymous alert.
        link_url : str, optional
            URL user will be taken to when the alert is clicked.
        link_title : str, optional
            Text of the link URL that will be displayed. If no placeholder is present in the alert, will be automatically appended.

        Returns AlertSendResponse:
        -------
        success : bool
            True if alert was sent successfully
        """

        payload = await self._http.send_alert(params)
        return AlertSendResponse.model_validate(payload)

    async def mark_all_alerts(
        self, params: AlertsMarkAllParams
    ) -> AlertsMarkAllResponse:
        """POST alerts/mark-all - Marks all of the API user's alerts as read or viewed

        Parameters
        ----------
        read : bool, optional
            If specified, marks all alerts as read.
        viewed : bool, optional
            If specified, marks all alerts as viewed. This will remove the alert counter but keep unactioned alerts highlighted.

        Returns AlertsMarkAllResponse:
        -------
        success : bool
            True if operation was successful
        """

        payload = await self._http.mark_all_alerts(params)
        return AlertsMarkAllResponse.model_validate(payload)

    async def get_alert(self, alert_id: int) -> AlertGetResponse:
        """GET alerts/{id}/ - Gets information about the specified alert

        Parameters
        ----------
        alert_id : int
            ID of the alert

        Returns AlertGetResponse:
        -------
        alert : UserAlert
            Alert information
        """

        payload = await self._http.get_alert(alert_id)
        return AlertGetResponse.model_validate(payload)

    async def mark_alert(
        self, alert_id: int, params: AlertMarkParams
    ) -> AlertMarkResponse:
        """POST alerts/{id}/mark - Marks the alert as viewed/read/unread

        Parameters
        ----------
        alert_id : int
            ID of the alert
        read : bool, optional
            Marks the alert as read
        unread : bool, optional
            Marks the alert as unread
        viewed : bool, optional
            Marks all alerts as viewed

        Returns AlertMarkResponse:
        -------
        success : bool
            True if operation was successful
        """

        payload = await self._http.mark_alert(alert_id, params)
        return AlertMarkResponse.model_validate(payload)

    # ============================================================================
    # ATTACHMENTS
    # ============================================================================

    async def get_attachments(
        self, params: AttachmentsGetParams
    ) -> AttachmentsGetResponse:
        """GET attachments/ - Gets the attachments associated with the provided API attachment key

        Parameters
        ----------
        key : str
            The API attachment key

        Returns AttachmentsGetResponse:
        -------
        attachments : List[Attachment]
            List of attachments
        """

        payload = await self._http.get_attachments(params)
        return AttachmentsGetResponse.model_validate(payload)

    async def upload_attachment(
        self, params: AttachmentUploadParams, attachment: BinaryIO
    ) -> AttachmentUploadResponse:
        """POST attachments/ - Uploads an attachment

        Must be submitted using multipart/form-data encoding.

        Parameters
        ----------
        key : str
            The API attachment key
        attachment : BinaryIO
            The attachment file

        Returns AttachmentUploadResponse:
        -------
        attachment : Attachment
            Uploaded attachment information

        Errors:
        ------
            attachment_key_user_wrong:
                Triggered if the user making the request does not match the user that created the attachment key.
        """

        payload = await self._http.upload_attachment(params, attachment)
        return AttachmentUploadResponse.model_validate(payload)

    async def create_attachment_key(
        self,
        params: AttachmentsCreateNewKeyParams,
        attachment: BinaryIO | None = None,
    ) -> AttachmentsCreateNewKeyResponse:
        """POST attachments/new-key - Creates a new attachment key

        Parameters
        ----------
        type : str
            Content type of the attachment
        context : List[str], optional
            Key-value pairs representing context
        attachment : BinaryIO, optional
            First attachment to be associated

        Returns AttachmentsCreateNewKeyResponse:
        -------
        key : str
            The attachment key created
        attachment : Attachment, optional
            Attachment information if provided
        """

        payload = await self._http.create_attachment_key(params, attachment)
        return AttachmentsCreateNewKeyResponse.model_validate(payload)

    async def get_attachment(
        self, attachment_id: int
    ) -> AttachmentGetResponse:
        """GET attachments/{id}/ - Gets information about the specified attachment

        Parameters
        ----------
        attachment_id : int
            ID of the attachment

        Returns AttachmentGetResponse:
        -------
        attachment : Attachment
        """

        payload = await self._http.get_attachment(attachment_id)
        return AttachmentGetResponse.model_validate(payload)

    async def delete_attachment(
        self, attachment_id: int
    ) -> AttachmentDeleteResponse:
        """DELETE attachments/{id}/ - Deletes the specified attachment

        Parameters
        ----------
        attachment_id : int
            ID of the attachment

        Returns AttachmentDeleteResponse:
        -------
        success : bool
            True if deletion was successful
        """

        payload = await self._http.delete_attachment(attachment_id)
        return AttachmentDeleteResponse.model_validate(payload)

    async def get_attachment_data(
        self, attachment_id: int
    ) -> AttachmentGetDataResponse:
        """GET attachments/{id}/data - Gets the data that makes up the specified attachment

        Parameters
        ----------
        attachment_id : int
            ID of the attachment

        Returns AttachmentGetData:
        -------
        data : BinaryIO
            The binary data
        """

        payload = await self._http.get_attachment_data(attachment_id)
        return AttachmentGetDataResponse.model_validate(payload)

    async def get_attachment_thumbnail(
        self, attachment_id: int
    ) -> AttachmentGetThumbnailResponse:
        """GET attachments/{id}/thumbnail - Gets the URL to the attachment's thumbnail

        Parameters
        ----------
        attachment_id : int
            ID of the attachment

        Returns AttachmentGetThumbnail:
        -------
        url : str
            URL via 301 redirect

        Errors:
        ------
            not_found:
                Not found if the attachment does not have a thumbnail
        """

        payload = await self._http.get_attachment_thumbnail(attachment_id)
        return AttachmentGetThumbnailResponse.model_validate(payload)

    # ============================================================================
    # AUTH
    # ============================================================================

    async def test_auth(self, params: AuthTestParams) -> AuthTestResponse:
        """POST auth/ - Tests a login and password for validity

        Only available to super user keys.

        Parameters
        ----------
        login : str
            Username or email address
        password : str
            The password
        limit_ip : str, optional
            IP that should be considered making the request

        Returns AuthTestResponse:
        -------
        user : User
            User information if authentication successful
        """

        payload = await self._http.test_auth(params)
        return AuthTestResponse.model_validate(payload)

    async def auth_from_session(
        self, params: AuthFromSessionParams
    ) -> AuthFromSessionResponse:
        """POST auth/from-session - Looks up the active XenForo user based on session ID or remember cookie

        Parameters
        ----------
        session_id : str, optional
            Checks for active session
        remember_cookie : str, optional
            Checks for active "remember me" cookie

        Returns AuthFromSessionResponse:
        -------
        success : bool
                If false, no session or remember cookie could be found
        user : User
            If successful, the user record of the matching user. May be a guest.
        """

        payload = await self._http.auth_from_session(params)
        return AuthFromSessionResponse.model_validate(payload)

    async def create_login_token(
        self, params: AuthLoginTokenParams
    ) -> AuthLoginTokenResponse:
        """POST auth/login-token - Generates a token that can automatically log into a specific XenForo user

        Parameters
        ----------
        user_id : int
            User ID to generate token for
        limit_ip : str, optional
            Locks token to specified IP
        return_url : str, optional
            URL to return user after login
        force : bool, optional
            If provided, the login URL will forcibly replace the currently logged in user if a user is already logged in and different to the currently logged in user. Defaults to false.
        remember: bool
            Controls whether the a "remember me" cookie will be set when the user logs in. Defaults to true.

        Returns AuthLoginTokenResponse:
        -------
        login_token : str
            Generated login token
        login_url : str
            URL to use for login
        expiry_date : int
            Unix timestamp of expiration
        """

        payload = await self._http.create_login_token(params)
        return AuthLoginTokenResponse.model_validate(payload)

    # ============================================================================
    # CONVERSATION MESSAGES
    # ============================================================================

    async def reply_conversation_message(
        self, params: ConversationMessageReplyParams
    ) -> ConversationMessageReplyResponse:
        """POST conversation-messages/ - Replies to a conversation

        Parameters
        ----------
        conversation_id : int
            ID of the conversation
        message : str
            Message content
        attachment_key : str, optional
            API attachment key to upload files. Attachment key content type must be conversation_message with context[conversation_id] set to this conversation ID.

        Returns ConversationMessageReplyResponse:
        -------
        success : bool
            True if message was posted
        message : ConversationMessage
            The newly inserted message
        """

        payload = await self._http.reply_conversation_message(params)
        return ConversationMessageReplyResponse.model_validate(payload)

    async def get_conversation_message(
        self, message_id: int
    ) -> ConversationMessageGetResponse:
        """GET conversation-messages/{id}/ - Gets the specified conversation message

        Parameters
        ----------
        message_id : int
            ID of the conversation message

        Returns ConversationMessageGetResponse:
        -------
        message : ConversationMessage
            Message information
        """

        payload = await self._http.get_conversation_message(message_id)
        return ConversationMessageGetResponse.model_validate(payload)

    async def update_conversation_message(
        self, message_id: int, params: ConversationMessageUpdateParams
    ) -> ConversationMessageUpdateResponse:
        """POST conversation-messages/{id}/ - Updates the specified conversation message

        Parameters
        ----------
        message_id : int
            ID of the conversation message
        message : str
            Updated message content
        attachment_key : str, optional
            API attachment key to upload files. Attachment key content type must be conversation_message with context[message_id] set to this message ID.

        Returns ConversationMessageUpdateResponse:
        -------
        success : bool
            True if update was successful
        message : ConversationMessage
            Updated message information
        """

        payload = await self._http.update_conversation_message(
            message_id, params
        )
        return ConversationMessageUpdateResponse.model_validate(payload)

    async def react_conversation_message(
        self, message_id: int, params: ConversationMessageReactParams
    ) -> ConversationMessageReactResponse:
        """POST conversation-messages/{id}/react - Reacts to the specified conversation message.

        Parameters
        ----------
        message_id : int
            ID of the conversation message
        reaction_id : int
            ID of the reaction to use. Use the current reaction ID to undo.

        Returns ConversationMessageReactResponse:
        -------
        success : bool
            True if reaction was added/removed
        action : ConversationMessageReactActionEnum
            "insert" or "delete"
        """

        payload = await self._http.react_conversation_message(
            message_id, params
        )
        return ConversationMessageReactResponse.model_validate(payload)

    # ============================================================================
    # CONVERSATIONS
    # ============================================================================

    async def get_conversations(
        self, params: ConversationsGetParams | None = None
    ) -> ConversationsGetResponse:
        """GET conversations/ - Gets the API user's list of conversations.

        Parameters
        ----------
        page : int, optional
            Page number
        starter_id : int, optional
            Filter by starter user ID
        receiver_id : int, optional
            Filter by receiver user ID
        starred : bool, optional
            Only gets starred conversations
        unread : bool, optional
            Only gets unread conversations

        Returns ConversationsGetResponse:
        -------
        conversations : List[Conversation]
            List of conversations
        pagination : Pagination
            Pagination information
        """

        payload = await self._http.get_conversations(params)
        return ConversationsGetResponse.model_validate(payload)

    async def create_conversation(
        self, params: ConversationCreateParams
    ) -> ConversationCreateResponse:
        """POST conversations/ - Creates a conversation.

        Parameters
        ----------
        recipient_ids : List[int]
            IDs of recipient users
        title : str
            Conversation title
        message : str
            First message content
        attachment_key : str, optional
            Attachment key if including attachments
        conversation_open : bool, optional
            Whether conversation is open
        open_invite : bool, optional
            Whether open for invites

        Returns ConversationCreateResponse:
        -------
        success : bool
            True if conversation was created
        conversation : Conversation
            Created conversation information
        """

        payload = await self._http.create_conversation(params)
        return ConversationCreateResponse.model_validate(payload)

    async def get_conversation(
        self,
        conversation_id: int,
        params: ConversationGetParams | None = None,
    ) -> ConversationGetResponse:
        """GET conversations/{id}/ - Gets information about the specified conversation.

        Parameters
        ----------
        conversation_id : int
            ID of the conversation
        with_messages : bool, optional
            Include a page of messages
        page : int, optional
            Page number

        Returns ConversationGetResponse:
        -------
        conversation : Conversation
            Conversation information
        messages : List[ConversationMessage], optional
            Messages if requested
        pagination : Pagination, optional
            Pagination if messages included
        """
        payload = await self._http.get_conversation(conversation_id, params)
        return ConversationGetResponse.model_validate(payload)

    async def update_conversation(
        self, conversation_id: int, params: ConversationUpdateParams
    ) -> ConversationUpdateResponse:
        """POST conversations/{id}/ - Updates the specified conversation.

        Parameters
        ----------
        conversation_id : int
            ID of the conversation
        title : str, optional
            New conversation title
        open_invite : bool, optional
            Whether open for invites
        conversation_open : bool, optional
            Whether conversation is open

        Returns ConversationUpdateResponse:
        -------
        success : bool
            True if update was successful
        conversation : Conversation
            Updated conversation information
        """

        payload = await self._http.update_conversation(conversation_id, params)
        return ConversationUpdateResponse.model_validate(payload)

    async def delete_conversation(
        self,
        conversation_id: int,
        params: ConversationDeleteParams | None = None,
    ) -> ConversationDeleteResponse:
        """DELETE conversations/{id}/ - Deletes the specified conversation from the API user's list

        Parameters
        ----------
        conversation_id : int
            ID of the conversation
        params : ConversationDeleteParams, optional
            ignore : bool, optional
                Ignore further replies

        Returns:
        -------
        ConversationDeleteResponse
            success : bool
                True if deletion was successful
        """

        payload = await self._http.delete_conversation(conversation_id, params)
        return ConversationDeleteResponse.model_validate(payload)

    async def invite_conversation(
        self, conversation_id: int, params: ConversationInviteParams
    ) -> ConversationInviteResponse:
        """POST conversations/{id}/invite - Invites the specified users to this conversation

        Parameters
        ----------
        conversation_id : int
            ID of the conversation
        recipient_ids : List[int]
            IDs of users to invite

        Returns ConversationInviteResponse:
        -------
        ConversationInviteResponse
            success : bool
                True if invites were sent
        """

        payload = await self._http.invite_conversation(conversation_id, params)
        return ConversationInviteResponse.model_validate(payload)

    async def mark_conversation_read(
        self,
        conversation_id: int,
        params: ConversationMarkReadParams | None = None,
    ) -> ConversationMarkReadResponse:
        """POST conversations/{id}/mark-read - Marks the conversation as read up until the specified time

        Parameters
        ----------
        conversation_id : int
            ID of the conversation
        date : int, optional
            Unix timestamp

        Returns ConversationMarkReadResponse:
        -------
        success : bool
            True if operation was successful
        """

        payload = await self._http.mark_conversation_read(
            conversation_id, params
        )
        return ConversationMarkReadResponse.model_validate(payload)

    async def mark_conversation_unread(
        self, conversation_id: int
    ) -> ConversationMarkUnreadResponse:
        """POST conversations/{id}/mark-unread - Marks a conversation as unread

        Parameters
        ----------
        conversation_id : int
            ID of the conversation

        Returns ConversationMarkUnreadResponse:
        -------
        success : bool
            True if operation was successful
        """

        payload = await self._http.mark_conversation_unread(conversation_id)
        return ConversationMarkUnreadResponse.model_validate(payload)

    async def get_conversation_messages(
        self,
        conversation_id: int,
        params: ConversationGetMessagesParams | None = None,
    ) -> ConversationMessagesGetResponse:
        """GET conversations/{id}/messages - Gets a page of messages in the specified conversation

        Parameters
        ----------
        conversation_id : int
            ID of the conversation
        page : int, optional
            Page number

        Returns ConversationMessagesGetResponse:
        -------
        messages : List[ConversationMessage]
            List of messages
        pagination : Pagination
            Pagination information
        """

        payload = await self._http.get_conversation_messages(
            conversation_id, params
        )
        return ConversationMessagesGetResponse.model_validate(payload)

    async def star_conversation(
        self, conversation_id: int, params: ConversationStarParams
    ) -> ConversationStarResponse:
        """POST conversations/{id}/star - Sets the star status of the specified conversation

        Parameters
        ----------
        conversation_id : int
            ID of the conversation
        star : bool
            Sets the star status

        Returns ConversationStarResponse:
        -------
        success : bool
            True if operation was successful
        """

        payload = await self._http.star_conversation(conversation_id, params)
        return ConversationStarResponse.model_validate(payload)

    # ============================================================================
    # FORUMS
    # ============================================================================

    async def get_forum(
        self, forum_id: int, params: ForumGetParams | None = None
    ) -> ForumGetResponse:
        """GET forums/{id}/ - Gets information about the specified forum

        Parameters
        ----------
        forum_id : int
            ID of the forum
        with_threads : bool, optional
            Gets a page of threads
        page : int, optional
            Page number
        prefix_id : int, optional
            Filter by prefix
        starter_id : int, optional
            Filter by user ID
        last_days : int, optional
            Filter by reply in last X days
        unread : bool, optional
            Filter to unread threads
        thread_type : str, optional
            Filter by thread type
        order : str, optional
            Method of ordering
        direction : str, optional
            "asc" or "desc"

        Returns ForumGetResponse:
        -------
        forum : Forum
            Forum information
        threads : List[Thread], optional
            Threads if requested
        pagination : Pagination, optional
            Pagination if threads included
        sticky : List[Thread], optional
            Sticky threads
        """

        payload = await self._http.get_forum(forum_id, params)
        return ForumGetResponse.model_validate(payload)

    async def mark_forum_read(
        self, forum_id: int, params: ForumMarkReadParams | None = None
    ) -> ForumMarkReadResponse:
        """POST forums/{id}/mark-read - Marks the forum as read up until the specified time

        Parameters
        ----------
        forum_id : int
            ID of the forum
        date : int, optional
            Unix timestamp

        Returns ForumMarkReadResponse:
        -------
        success : bool
            True if operation was successful
        """

        payload = await self._http.mark_forum_read(forum_id, params)
        return ForumMarkReadResponse.model_validate(payload)

    async def get_forum_threads(
        self, forum_id: int, params: ForumThreadsGetParams | None = None
    ) -> ForumThreadsGetResponse:
        """GET forums/{id}/threads - Gets a page of threads from the specified forum

        Parameters
        ----------
        forum_id : int
            ID of the forum
        page : int, optional
            Page number
        prefix_id : int, optional
            Filter by prefix
        starter_id : int, optional
            Filter by user ID
        last_days : int, optional
            Filter by reply in last X days
        unread : bool, optional
            Filter to unread threads
        thread_type : str, optional
            Filter by thread type
        order : str, optional
            Method of ordering
        direction : str, optional
            "asc" or "desc"

        Returns ForumThreadsGetResponse:
        -------
        threads : List[Thread]
            List of threads
        pagination : Pagination
            Pagination information
        sticky : List[Thread], optional
            Sticky threads
        """

        payload = await self._http.get_forum_threads(forum_id, params)
        return ForumThreadsGetResponse.model_validate(payload)

    # ============================================================================
    # INDEX
    # ============================================================================

    async def get_index(self) -> IndexGetResponse:
        """GET index/ - Gets general information about the site and the API

        Returns IndexGetResponse:
        -------
        version_id : int
            XenForo version ID
        site_title : str
            Site title
        base_url : str
            Base URL
        api_url : str
            API URL
        key : ApiKey
            API key information
        """

        payload = await self._http.get_index()
        return IndexGetResponse.model_validate(payload)

    # ============================================================================
    # ME (Current User)
    # ============================================================================

    async def get_me(self) -> MeGetResponse:
        """GET me/ - Gets information about the current API user

        Returns MeGetResponse:
        -------
        me : User
            Current user information
        """

        payload = await self._http.get_me()
        return MeGetResponse.model_validate(payload)

    async def update_me(self, params: MeUpdateParams) -> MeUpdateResponse:
        """POST me/ - Updates information about the current user

        Parameters
        ----------
        option : dict with creation_watch_state, interaction_watch_state, etc.
        profile : dict with location, website, about, signature
        privacy : dict with allow_view_profile, allow_post_profile, etc.
        visible : bool
        activity_visible : bool
        timezone : str
        custom_title : str
        custom_fields : dict

        Returns MeUpdateResponse:
        -------
        success : bool
            True if update was successful
        """

        payload = await self._http.update_me(params)
        return MeUpdateResponse.model_validate(payload)

    async def update_my_avatar(
        self, avatar: BinaryIO
    ) -> MeAvatarUpdateResponse:
        """POST me/avatar - Updates the current user's avatar

        Parameters
        ----------
        avatar : BinaryIO
            Avatar file

        Returns MeAvatarUpdateResponse:
        -------
        success : bool
            True if update was successful
        """

        payload = await self._http.update_my_avatar(avatar)
        return MeAvatarUpdateResponse.model_validate(payload)

    async def delete_my_avatar(self) -> MeAvatarDeleteResponse:
        """DELETE me/avatar - Deletes the current user's avatar

        Returns:
        -------
        success : bool
            True if deletion was successful
        """

        payload = await self._http.delete_my_avatar()
        return MeAvatarDeleteResponse.model_validate(payload)

    async def update_my_email(
        self, params: MeEmailUpdateParams
    ) -> MeEmailUpdateResponse:
        """POST me/email - Updates the current user's email address

        Parameters
        ----------
        current_password : str
            Current password for verification
        email : str
            New email address

        Returns MeEmailUpdateResponse:
        -------
        success : bool
            True if update was successful
        confirmation_required : bool
            Whether email confirmation is required
        """

        payload = await self._http.update_my_email(params)
        return MeEmailUpdateResponse.model_validate(payload)

    async def update_my_password(
        self, params: MePasswordUpdateParams
    ) -> MePasswordUpdateResponse:
        """POST me/password - Updates the current user's password

        Parameters
        ----------
        current_password : str
            Current password
        new_password : str
            New password

        Returns MePasswordUpdateResponse:
        -------
        success : bool
            True if update was successful
        """

        payload = await self._http.update_my_password(params)
        return MePasswordUpdateResponse.model_validate(payload)

    # ============================================================================
    # NODES
    # ============================================================================

    async def get_nodes(self) -> NodesGetResponse:
        """GET nodes/ - Gets the node tree

        Returns NodesGetResponse:
        -------
        tree_map : List
            Tree structure mapping
        nodes : List[Node]
            List of nodes
        """

        payload = await self._http.get_nodes()
        return NodesGetResponse.model_validate(payload)

    async def create_node(
        self, params: NodeCreateParams
    ) -> NodeCreateResponse:
        """POST nodes/ - Creates a new node

        Parameters
        ----------
        node : dict with title, node_name, description, parent_node_id, display_order, display_in_list
        type_data : dict, optional
            Type-specific data
        node_type_id : str
            Node type ID

        Returns NodeCreateResponse:
        -------
            node : Node
                Created node information
        """

        payload = await self._http.create_node(params)
        return NodeCreateResponse.model_validate(payload)

    # async def get_nodes_flattened(self) -> NodesFlattenedGetResponse:
    #     """GET nodes/flattened - Gets a flattened node tree

    #     Returns NodesFlattenedGetResponse:
    #     -------
    #         nodes_flat : List
    #             Flattened node list
    #     """

    #     payload = await self._http.get_nodes_flattened()
    #     return NodesFlattenedGetResponse.model_validate(payload)

    async def get_node(self, node_id: int) -> NodeGetResponse:
        """GET nodes/{id}/ - Gets information about the specified node

        Parameters
        ----------
        node_id : int
            ID of the node

        Returns NodeGetResponse:
        -------
        node : Node
            Node information
        """
        payload = await self._http.get_node(node_id)
        return NodeGetResponse.model_validate(payload)

    async def update_node(
        self, node_id: int, params: NodeUpdateParams
    ) -> NodeUpdateResponse:
        """POST nodes/{id}/ - Updates the specified node

        Parameters
        ----------
        node_id : int
            ID of the node
        node : NodeCreateOrUpdate
        type_data : Dict[str, Any]
            Type-specific data

        Returns NodeUpdateResponse:
        -------
        node : Node
        """

        payload = await self._http.update_node(node_id, params)
        return NodeUpdateResponse.model_validate(payload)

    async def delete_node(
        self, node_id: int, params: NodeDeleteParams | None = None
    ) -> NodeDeleteResponse:
        """DELETE nodes/{id}/ - Deletes the specified node

        Parameters
        ----------
        node_id : int
            ID of the node
        delete_children : bool, optional
            Whether to delete child nodes

        Returns NodeDeleteResponse:
        -------
        success : bool
            True if deletion was successful
        """

        payload = await self._http.delete_node(node_id, params)
        return NodeDeleteResponse.model_validate(payload)

    # ============================================================================
    # POSTS
    # ============================================================================

    async def create_post(
        self, params: PostCreateParams
    ) -> PostCreateResponse:
        """POST posts/ - Adds a new reply to a thread.

        Parameters
        ----------
        thread_id : int
            ID of the thread to reply to
        message : str
            Post message content
        attachment_key : str, optional
            API attachment key to upload files. Attachment key context type must be post with context[thread_id] set to this thread ID.

        Returns PostCreateResponse:
        -------
        success : bool
            True if post was created
        post : Post
            Created post
        """

        payload = await self._http.create_post(params)
        return PostCreateResponse.model_validate(payload)

    async def get_post(self, post_id: int) -> PostGetResponse:
        """GET posts/{id}/ - Gets information about the specified post

        Parameters
        ----------
        post_id : int
            ID of the post

        Returns PostGetResponse:
        -------
        post : Post
            Post information
        """
        payload = await self._http.get_post(post_id)
        return PostGetResponse.model_validate(payload)

    async def update_post(
        self, post_id: int, params: PostUpdateParams
    ) -> PostUpdateResponse:
        """POST posts/{id}/ - Updates the specified post

        Parameters
        ----------
        post_id : int
            ID of the post
        message : str
            Updated message content
        silent : bool, optional
            Silent edit
        clear_edit : bool, optional
            Clear edit history
        author_alert : bool, optional
            Send alert to author
        author_alert_reason : str, optional
            Reason for alert
        attachment_key : str, optional
            Attachment key if including attachments

        Returns PostUpdateResponse:
        -------
        success : bool
            True if update was successful
        post : Post
            Updated post information
        """
        payload = await self._http.update_post(post_id, params)
        return PostUpdateResponse.model_validate(payload)

    async def delete_post(
        self, post_id: int, params: PostDeleteParams | None = None
    ) -> PostDeleteResponse:
        """DELETE posts/{id}/ - Deletes the specified post

        Default to soft deletion.

        Parameters
        ----------
        post_id : int
            ID of the post
        hard_delete : bool, optional
            Whether to hard delete
        reason : str, optional
            Deletion reason
        author_alert : bool, optional
            Send alert to author
        author_alert_reason : str, optional
            Reason for alert

        Returns PostDeleteResponse:
        -------
        success : bool
            True if deletion was successful
        """
        payload = await self._http.delete_post(post_id, params)
        return PostDeleteResponse.model_validate(payload)

    async def mark_post_solution(
        self, post_id: int
    ) -> PostMarkSolutionResponse:
        """POST posts/{id}/mark-solution - Toggle the specified post as the solution to its containing thread

        Parameters
        ----------
        post_id : int
            ID of the post

        Returns PostMarkSolutionResponse:
        -------
        true : Any
            Success indicator
        new_solution_post : Post, optional
            New solution post if set
        old_solution_post : Post, optional
            Old solution post if changed
        """
        payload = await self._http.mark_post_solution(post_id)
        return PostMarkSolutionResponse.model_validate(payload)

    async def react_post(
        self, post_id: int, params: PostReactParams
    ) -> PostReactResponse:
        """POST posts/{id}/react - Reacts to the specified post

        Parameters
        ----------
        post_id : int
            ID of the post
        reaction_id : int
            ID of the reaction

        Returns PostReactResponse:
        -------
        success : bool
            True if reaction was added/removed
        action : str
            "insert" or "delete"
        """
        payload = await self._http.react_post(post_id, params)
        return PostReactResponse.model_validate(payload)

    async def vote_post(
        self, post_id: int, params: PostVoteParams
    ) -> PostVoteResponse:
        """POST posts/{id}/vote - Votes on the specified post

        Parameters
        ----------
        post_id : int
            ID of the post
        type : str
            "up" or "down"

        Returns PostVoteResponse:
        -------
        success : bool
            True if vote was cast/removed
        action : str
            "insert" or "delete"
        """
        payload = await self._http.vote_post(post_id, params)
        return PostVoteResponse.model_validate(payload)

    # ============================================================================
    # PROFILE POST COMMENTS
    # ============================================================================

    async def create_profile_post_comment(
        self, params: ProfilePostCommentCreateParams
    ) -> ProfilePostCommentCreateResponse:
        """POST profile-post-comments/ - Creates a new profile post comment

        Parameters
        ----------
        profile_post_id : int
            ID of the profile post
        message : str
            Comment message content
        attachment_key : str, optional
            Attachment key if including attachments

        Returns ProfilePostCommentCreateResponse:
        -------
        success : bool
            True if comment was created
        comment : ProfilePostComment
            Created comment information
        """
        payload = await self._http.create_profile_post_comment(params)
        return ProfilePostCommentCreateResponse.model_validate(payload)

    async def get_profile_post_comment(
        self, comment_id: int
    ) -> ProfilePostCommentGetResponse:
        """GET profile-post-comments/{id}/ - Gets information about the specified profile post comment

        Parameters
        ----------
        comment_id : int
            ID of the comment

        Returns ProfilePostCommentGetResponse:
        -------
        comment : ProfilePostComment
            Comment information
        """
        payload = await self._http.get_profile_post_comment(comment_id)
        return ProfilePostCommentGetResponse.model_validate(payload)

    async def update_profile_post_comment(
        self, comment_id: int, params: ProfilePostCommentUpdateParams
    ) -> ProfilePostCommentUpdateResponse:
        """POST profile-post-comments/{id}/ - Updates the specified profile post comment

        Parameters
        ----------
        comment_id : int
            ID of the comment
        message : str
            Updated message content
        author_alert : bool, optional
            Send alert to author
        author_alert_reason : str, optional
            Reason for alert
        attachment_key : str, optional
            Attachment key if including attachments

        Returns ProfilePostCommentUpdateResponse:
        -------
        success : bool
            True if update was successful
        comment : ProfilePostComment
            Updated comment information
        """
        payload = await self._http.update_profile_post_comment(
            comment_id, params
        )
        return ProfilePostCommentUpdateResponse.model_validate(payload)

    async def delete_profile_post_comment(
        self,
        comment_id: int,
        params: ProfilePostCommentDeleteParams | None = None,
    ) -> ProfilePostCommentDeleteResponse:
        """DELETE profile-post-comments/{id}/ - Deletes the specified profile post comment

        Parameters
        ----------
        comment_id : int
            ID of the comment
        hard_delete : bool, optional
            Whether to hard delete
        reason : str, optional
            Deletion reason
        author_alert : bool, optional
            Send alert to author
        author_alert_reason : str, optional
            Reason for alert

        Returns ProfilePostCommentDeleteResponse:
        -------
        success : bool
            True if deletion was successful
        """
        payload = await self._http.delete_profile_post_comment(
            comment_id, params
        )
        return ProfilePostCommentDeleteResponse.model_validate(payload)

    async def react_profile_post_comment(
        self, comment_id: int, params: ProfilePostCommentReactParams
    ) -> ProfilePostCommentReactResponse:
        """POST profile-post-comments/{id}/react - Reacts to the specified profile post comment

        Parameters
        ----------
        comment_id : int
            ID of the comment
        reaction_id : int
            ID of the reaction

        Returns ProfilePostCommentReactResponse:
        -------
        success : bool
            True if reaction was added/removed
        action : str
            "insert" or "delete"
        """
        payload = await self._http.react_profile_post_comment(
            comment_id, params
        )
        return ProfilePostCommentReactResponse.model_validate(payload)

    # ============================================================================
    # PROFILE POSTS
    # ============================================================================

    async def create_profile_post(
        self, params: ProfilePostCreateParams
    ) -> ProfilePostCreateResponse:
        """POST profile-posts/ - Creates a new profile post

        Parameters
        ----------
        user_id : int
            ID of the user whose profile to post on
        message : str
            Post message content
        attachment_key : str, optional
            Attachment key if including attachments

        Returns ProfilePostCreateResponse:
        -------
        success : bool
            True if post was created
        profile_post : ProfilePost
            Created profile post information
        """
        payload = await self._http.create_profile_post(params)
        return ProfilePostCreateResponse.model_validate(payload)

    async def get_profile_post(
        self,
        profile_post_id: int,
        params: ProfilePostGetParams | None = None,
    ) -> ProfilePostGetResponse:
        """GET profile-posts/{id}/ - Gets information about the specified profile post

        Parameters
        ----------
        profile_post_id : int
            ID of the profile post
        with_comments : bool, optional
            Include comments
        page : int, optional
            Page number
        direction : str, optional
            "desc" or "asc"

        Returns ProfilePostGetResponse:
        -------
        profile_post : ProfilePost
            Profile post information
        comments : List[ProfilePostComment], optional
            Comments if requested
        pagination : Pagination, optional
            Pagination if comments included
        """
        payload = await self._http.get_profile_post(profile_post_id, params)
        return ProfilePostGetResponse.model_validate(payload)

    async def update_profile_post(
        self, profile_post_id: int, params: ProfilePostUpdateParams
    ) -> ProfilePostUpdateResponse:
        """POST profile-posts/{id}/ - Updates the specified profile post

        Parameters
        ----------
        profile_post_id : int
            ID of the profile post
        message : str
            Updated message content
        author_alert : bool, optional
            Send alert to author
        author_alert_reason : str, optional
            Reason for alert
        attachment_key : str, optional
            Attachment key if including attachments

        Returns ProfilePostUpdateResponse:
        -------
        success : bool
            True if update was successful
        profile_post : ProfilePost
            Updated profile post information
        """
        payload = await self._http.update_profile_post(profile_post_id, params)
        return ProfilePostUpdateResponse.model_validate(payload)

    async def delete_profile_post(
        self,
        profile_post_id: int,
        params: ProfilePostDeleteParams | None = None,
    ) -> ProfilePostDeleteResponse:
        """DELETE profile-posts/{id}/ - Deletes the specified profile post

        Parameters
        ----------
        profile_post_id : int
            ID of the profile post
        hard_delete : bool, optional
            Whether to hard delete
        reason : str, optional
            Deletion reason
        author_alert : bool, optional
            Send alert to author
        author_alert_reason : str, optional
            Reason for alert

        Returns ProfilePostDeleteResponse:
        -------
        success : bool
            True if deletion was successful
        """
        payload = await self._http.delete_profile_post(profile_post_id, params)
        return ProfilePostDeleteResponse.model_validate(payload)

    async def get_profile_post_comments(
        self,
        profile_post_id: int,
        params: ProfilePostCommentsGetParams | None = None,
    ) -> ProfilePostCommentsGetResponse:
        """GET profile-posts/{id}/comments - Gets a page of comments on the specified profile post

        Parameters
        ----------
        profile_post_id : int
            ID of the profile post
        page : int, optional
            Page number
        direction : str, optional
            "desc" or "asc"

        Returns ProfilePostCommentsGetResponse:
        -------
        comments : List[ProfilePostComment]
            List of comments
        pagination : Pagination
            Pagination information
        """
        payload = await self._http.get_profile_post_comments(
            profile_post_id, params
        )
        return ProfilePostCommentsGetResponse.model_validate(payload)

    async def react_profile_post(
        self, profile_post_id: int, params: ProfilePostReactParams
    ) -> ProfilePostReactResponse:
        """POST profile-posts/{id}/react - Reacts to the specified profile post

        Parameters
        ----------
        profile_post_id : int
            ID of the profile post
        reaction_id : int
            ID of the reaction

        Returns ProfilePostReactResponse:
        -------
        success : bool
            True if reaction was added/removed
        action : str
            "insert" or "delete"
        """
        payload = await self._http.react_profile_post(profile_post_id, params)
        return ProfilePostReactResponse.model_validate(payload)

    # ============================================================================
    # STATS
    # ============================================================================

    async def get_stats(self) -> StatsResponse:
        """GET stats/ - Gets site statistics and general activity information

        Returns StatsResponse:
        -------
        totals : dict
            Total counts for threads, messages, users
        latest_user : dict
            Latest registered user information
        online : dict
            Online user counts
        """
        payload = await self._http.get_stats()
        return StatsResponse.model_validate(payload)

    # ============================================================================
    # THREADS
    # ============================================================================

    async def get_threads(
        self, params: ThreadsGetParams | None = None
    ) -> ThreadsGetResponse:
        """GET threads/ - Gets a list of threads

        Parameters
        ----------
        page : int, optional
            Page number
        prefix_id : int, optional
            Filter by prefix
        starter_id : int, optional
            Filter by starter user ID
        last_days : int, optional
            Filter by reply in last X days
        unread : bool, optional
            Filter to unread threads
        thread_type : str, optional
            Filter by thread type
        order : str, optional
            Method of ordering
        direction : str, optional
            "asc" or "desc"

        Returns ThreadsGetResponse:
        -------
        threads : List[Thread]
            List of threads
        pagination : Pagination
            Pagination information
        """
        payload = await self._http.get_threads(params)
        return ThreadsGetResponse.model_validate(payload)

    async def create_thread(
        self, params: ThreadCreateParams
    ) -> ThreadCreateResponse:
        """POST threads/ - Creates a thread

        Parameters
        ----------
        node_id : int
            ID of the forum to create thread in
        title : str
            Thread title
        message : str
            First post message content
        discussion_type : str, optional
            Discussion type
        prefix_id : int, optional
            Thread prefix ID
        tags : List[str], optional
            Thread tags
        custom_fields : dict, optional
            Custom field values
        discussion_open : bool, optional
            Whether discussion is open
        sticky : bool, optional
            Whether thread is sticky
        attachment_key : str, optional
            Attachment key if including attachments

        Returns ThreadCreateResponse:
        -------
        success : bool
            True if thread was created
        thread : Thread
            Created thread information

        Errors:
        ------
            no_permission:
                No permission error.
        """
        payload = await self._http.create_thread(params)
        return ThreadCreateResponse.model_validate(payload)

    async def get_thread(
        self, thread_id: int, params: ThreadGetParams | None = None
    ) -> ThreadGetResponse:
        """GET threads/{id}/ - Gets information about the specified thread

        Parameters
        ----------
        thread_id : int
            ID of the thread
        params : ThreadGetParams, optional
            with_posts : bool, optional
                Include posts
            with_first_post : bool, optional
                Include first post
            page : int, optional
                Page number

        Returns ThreadGetResponse:
        -------
        thread : Thread
            Thread information
        posts : List[Post], optional
            Posts if requested
        pagination : Pagination, optional
            Pagination if posts included
        """
        payload = await self._http.get_thread(thread_id, params)
        return ThreadGetResponse.model_validate(payload)

    async def update_thread(
        self, thread_id: int, params: ThreadUpdateParams
    ) -> ThreadUpdateResponse:
        """POST threads/{id}/ - Updates the specified thread

        Parameters
        ----------
        thread_id : int
            ID of the thread
        title : str, optional
            New thread title
        prefix_id : int, optional
            Thread prefix ID
        tags : List[str], optional
            Thread tags
        custom_fields : dict, optional
            Custom field values
        discussion_open : bool, optional
            Whether discussion is open
        sticky : bool, optional
            Whether thread is sticky

        Returns ThreadUpdateResponse:
        -------
        success : bool
            True if update was successful
        thread : Thread
            Updated thread information
        """
        payload = await self._http.update_thread(thread_id, params)
        return ThreadUpdateResponse.model_validate(payload)

    async def delete_thread(
        self, thread_id: int, params: ThreadDeleteParams | None = None
    ) -> ThreadDeleteResponse:
        """DELETE threads/{id}/ - Deletes the specified thread

        Parameters
        ----------
        thread_id : int
            ID of the thread
        hard_delete : bool, optional
            Whether to hard delete
        reason : str, optional
            Deletion reason
        author_alert : bool, optional
            Send alert to author
        author_alert_reason : str, optional
            Reason for alert
        starter_alert : bool, optional
            Send alert to starter
        starter_alert_reason : str, optional
            Reason for starter alert

        Returns ThreadDeleteResponse:
        -------
        success : bool
            True if deletion was successful
        """
        payload = await self._http.delete_thread(thread_id, params)
        return ThreadDeleteResponse.model_validate(payload)

    async def change_thread_type(
        self, thread_id: int, params: ThreadChangeTypeParams
    ) -> ThreadChangeTypeResponse:
        """POST threads/{id}/change-type - Changes the thread type

        Parameters
        ----------
        thread_id : int
            ID of the thread
        discussion_type : str
            New discussion type

        Returns ThreadChangeTypeResponse:
        -------
        success : bool
            True if type was changed
        thread : Thread
            Updated thread information
        """
        payload = await self._http.change_thread_type(thread_id, params)
        return ThreadChangeTypeResponse.model_validate(payload)

    async def mark_thread_read(
        self, thread_id: int, params: ThreadMarkReadParams
    ) -> ThreadMarkReadResponse:
        """POST threads/{id}/mark-read - Marks the thread as read up until the specified time

        Parameters
        ----------
        thread_id : int
            ID of the thread
        date : int
            Unix timestamp

        Returns ThreadMarkReadResponse:
        -------
        success : bool
            True if operation was successful
        """
        payload = await self._http.mark_thread_read(thread_id, params)
        return ThreadMarkReadResponse.model_validate(payload)

    async def move_thread(
        self, thread_id: int, params: ThreadMoveParams
    ) -> ThreadMoveResponse:
        """POST threads/{id}/move - Moves the thread to a different forum

        Parameters
        ----------
        thread_id : int
            ID of the thread
        node_id : int
            ID of the target forum
        notify_watchers : bool, optional
            Notify watchers of move
        starter_alert : bool, optional
            Send alert to thread starter
        starter_alert_reason : str, optional
            Reason for starter alert
        prefix_id : int, optional
            New prefix ID

        Returns ThreadMoveResponse:
        -------
        success : bool
            True if move was successful
        thread : Thread
            Moved thread information
        """
        payload = await self._http.move_thread(thread_id, params)
        return ThreadMoveResponse.model_validate(payload)

    async def get_thread_posts(
        self, thread_id: int, params: ThreadPostsGetParams | None = None
    ) -> ThreadPostsGetResponse:
        """GET threads/{id}/posts - Gets a page of posts from the specified thread

        Parameters
        ----------
        thread_id : int
            ID of the thread
        page : int, optional
            Page number

        Returns ThreadPostsGetResponse:
        -------
        posts : List[Post]
            List of posts
        pagination : Pagination
            Pagination information
        """
        payload = await self._http.get_thread_posts(thread_id, params)
        return ThreadPostsGetResponse.model_validate(payload)

    async def vote_thread(
        self, thread_id: int, params: ThreadVoteParams
    ) -> ThreadVoteResponse:
        """POST threads/{id}/vote - Votes on the specified thread

        Parameters
        ----------
        thread_id : int
            ID of the thread
        type : str
            "up" or "down"

        Returns ThreadVoteResponse:
        -------
        success : bool
            True if vote was cast/removed
        action : str
            "insert" or "delete"
        """
        payload = await self._http.vote_thread(thread_id, params)
        return ThreadVoteResponse.model_validate(payload)

    # ============================================================================
    # USERS
    # ============================================================================

    async def get_users(
        self, params: UsersGetParams | None = None
    ) -> UsersGetResponse:
        """GET users/ - Gets a list of users

        Parameters
        ----------
        page : int, optional
            Page number

        Returns UsersGetResponse:
        -------
        users : List[User]
            List of users
        pagination : Pagination
            Pagination information
        """
        payload = await self._http.get_users(params)
        return UsersGetResponse.model_validate(payload)

    async def create_user(
        self, params: UserCreateParams
    ) -> UserCreateResponse:
        """POST users/ - Creates a new user

        Parameters
        ----------
        username : str
            Username
        email : str
            Email address
        password : str
            Password

        Returns UserCreateResponse:
        -------
        success : bool
            True if user was created
        user : User
            Created user information
        """
        payload = await self._http.create_user(params)
        return UserCreateResponse.model_validate(payload)

    async def find_user_by_email(
        self, params: UsersFindEmailParams
    ) -> UserFindEmailResponse:
        """GET users/find-email - Finds a user by email address

        Parameters
        ----------
        email : str
            Email address to search for

        Returns UserFindEmailResponse:
        -------
        user : User, optional
        """
        payload = await self._http.find_user_by_email(params)
        return UserFindEmailResponse.model_validate(payload)

    async def find_user_by_name(
        self, params: UsersFindNameParams
    ) -> UserFindNameResponse:
        """GET users/find-name - Finds users by username

        Parameters
        ----------
        username : str
            Username to search for

        Returns UserFindNameResponse:
        -------
        exact : User, optional
            Exact match user
        recommendations : List[User], optional
            Similar usernames
        """
        payload = await self._http.find_user_by_name(params)
        return UserFindNameResponse.model_validate(payload)

    async def get_user(
        self, user_id: int, params: UserGetParams | None = None
    ) -> UserGetResponse:
        """GET users/{id}/ - Gets information about the specified user

        Parameters
        ----------
        user_id : int
            ID of the user
        with_posts : bool, optional
            If specified, the response will include a page of profile posts.
        page : int
            The page of comments to include

        Returns UserGetResponse:
        -------
        user : User
            User information
        """
        payload = await self._http.get_user(user_id, params)
        return UserGetResponse.model_validate(payload)

    async def update_user(
        self, user_id: int, params: UserUpdateParams
    ) -> UserUpdateResponse:
        """POST users/{id}/ - Updates the specified user

        Parameters
        ----------
        user_id : int
            ID of the user
        username : str, optional
            New username
        email : str, optional
            New email
        user_group_id : int, optional
            Primary user group
        secondary_group_ids : List[int], optional
            Secondary groups
        custom_title : str, optional
            Custom title
        is_staff : bool, optional
            Staff status
        visible : bool, optional
            Visibility

        Returns UserUpdateResponse:
        -------
        success : bool
            True if update was successful
        user : User
            Updated user information
        """
        payload = await self._http.update_user(user_id, params)
        return UserUpdateResponse.model_validate(payload)

    async def delete_user(
        self, user_id: int, params: UserRenameParams | None = None
    ) -> UserDeleteResponse:
        """DELETE users/{id}/ - Deletes the specified user

        Parameters
        ----------
        user_id : int
            ID of the user
        rename_to : str, optional
            New name for content attribution

        Returns UserDeleteResponse:
        -------
        success : bool
            True if deletion was successful
        """
        payload = await self._http.delete_user(user_id, params)
        return UserDeleteResponse.model_validate(payload)

    async def update_user_avatar(
        self, user_id: int, avatar: BinaryIO
    ) -> UserAvatarUpdateResponse:
        """POST users/{id}/avatar - Updates the specified user's avatar

        Parameters
        ----------
        user_id : int
            ID of the user
        avatar : BinaryIO
            Avatar file

        Returns UserAvatarUpdateResponse:
        -------
        success : bool
            True if update was successful
        """
        payload = await self._http.update_user_avatar(user_id, avatar)
        return UserAvatarUpdateResponse.model_validate(payload)

    async def delete_user_avatar(
        self, user_id: int
    ) -> UserAvatarDeleteResponse:
        """DELETE users/{id}/avatar - Deletes the specified user's avatar

        Parameters
        ----------
        user_id : int
            ID of the user

        Returns UserAvatarDeleteResponse:
        -------
        success : bool
            True if deletion was successful
        """

        payload = await self._http.delete_user_avatar(user_id)
        return UserAvatarDeleteResponse.model_validate(payload)

    async def get_user_profile_posts(
        self, user_id: int, page: int | None
    ) -> UserProfilePostsGetResponse:
        """GET users/{id}/profile-posts - Gets a page of profile posts from the specified user's profile

        Parameters
        ----------
        user_id : int
            ID of the user
        page : int, optional
            Page number

        Returns UserProfilePostsGetResponse:
        -------
        profile_posts : List[ProfilePost]
            List of profile posts
        pagination : Pagination
            Pagination information
        """

        params = (
            UserProfilePostsGetParams(page=page) if page is not None else None
        )
        payload = await self._http.get_user_profile_posts(user_id, params)
        return UserProfilePostsGetResponse.model_validate(payload)

    # ============================================================================
    # ACTIONS
    # ============================================================================

    async def get_demote_groups(self) -> GetDemoteGroupsResponse:
        """GET demote/ - getting a list of available groups for removing.

        Returns GetDemoteGroupsResponse:
        -------
        success : bool
            Operation status
        groups : Dict[XenForoInternalGroupsEnum, ArzGuardGroupsEnum]
            Mapping of internal group enum values to ArzGuard groups

        """

        payload = await self._http.get_demote_groups()
        return GetDemoteGroupsResponse.model_validate(payload)

    async def demote_user(
        self, user_id: int, group_id: ArzGuardGroupsIdsEnum
    ) -> DemoteUserResponse:
        """POST demote/{user_id}/ - demoting a user from a group.

        Parameters
        ----------
        user_id : int
            ID of the user
        group_id : ArzGuardGroupsIdsEnum
            ID of the group to delete for the user

        Returns DemoteUserResponse:
        -------
        success : bool
            Operation status
        groups : List[ArzGuardGroupsNamesEnum]
            An array of group names that the user belongs to
        user : Optional[User]
            Detailed user information (included if the API key has the user:read permission)

        Errors
        ------
            user_id_not_valid:
                Неверный ID пользователя
            user_cannot_promote:
                The user cannot be changed
            group_not_allowed:
                There are no rights to delete from the specified group
        """

        params = UserDemoteParams(group=group_id)
        payload = await self._http.demote_user(user_id, params)
        return DemoteUserResponse.model_validate(payload)

    async def get_promote_groups(self) -> GetPromoteGroupsResponse:
        """GET promote/ - getting a list of available groups for adding.

        Returns GetPromoteGroupsResponse:
        -------
        success : bool
            Operation status
        groups : Dict[XenForoInternalGroupsEnum, ArzGuardGroupsEnum]
            Mapping of internal group enum values to ArzGuard groups
        """
        payload = await self._http.get_promote_groups()
        return GetPromoteGroupsResponse.model_validate(payload)

    async def promote_user(
        self, user_id: int, group_id: ArzGuardGroupsIdsEnum
    ) -> PromoteUserResponse:
        """POST promote/{user_id}/ - promotion of the user to the group.

        Parameters
        ----------
        user_id : int
            ID of the user
        group_id : ArzGuardGroupsIdsEnum
            ID of the group to add to the user

        Returns PromoteUserResponse:
        -------
        success : bool
            Operation status
        groups : List[ArzGuardGroupsNamesEnum]
            An array of group names that the user belongs to
        user : Optional[User]
            Detailed user information (included if the API key has the user:read permission)

        Errors:
        ------
            group_not_provided:
                The group is not specified
            user_id_not_valid:
                Invalid user ID
            user_cannot_promote:
                The user cannot be promoted
            group_not_allowed:
                No permissions to add to the specified group
        """

        params = UserPromoteParams(group=group_id)
        payload = await self._http.promote_user(user_id, params)
        return PromoteUserResponse.model_validate(payload)
