document.addEventListener('DOMContentLoaded', function () {
    const feedContainer = document.getElementById('feed-container');

    if (!feedContainer) {
        return;
    }

    const emptyMessage = document.getElementById('empty-feed-message');
    const postContentInput = document.getElementById('post-content');
    const addPostBtn = document.getElementById('add-post-btn');

    // Friend feed ownership uses immutable user IDs; usernames are display text only.
    const currentUserId = feedContainer.dataset.currentUserId || '';
    const currentDisplayUsername = feedContainer.dataset.currentDisplayUsername || '';

    let postCount = 0;

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatTimestamp(date) {
        return date.toLocaleString('en-AU', {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function updateEmptyState() {
        if (!emptyMessage) {
            return;
        }

        const postCards = feedContainer.querySelectorAll('.post-card');
        emptyMessage.style.display = postCards.length ? 'none' : 'block';
    }

    function createCommentItem(ownerId, commenter, text, timestamp) {
        const comment = document.createElement('div');

        comment.className = 'mb-3 border-bottom pb-2';
        comment.dataset.ownerId = ownerId;
        comment.innerHTML =
            '<strong>' + escapeHtml(commenter) + '</strong> ' +
            '<span class="text-muted small">' + escapeHtml(timestamp) + '</span>' +
            '<p class="mb-0">' + escapeHtml(text) + '</p>';

        return comment;
    }

    async function saveFeedPost(content) {
        // Persist manual feed posts so refreshes keep text-only updates.
        const response = await fetch('/friends-feed/posts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: content })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Unable to save post.');
        }

        return data.post;
    }

    async function deleteFeedPost(feedPostId) {
        const response = await fetch('/friends-feed/posts/' + encodeURIComponent(feedPostId), {
            method: 'DELETE'
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Unable to delete post.');
        }
    }

    async function saveWorkoutComment(workoutId, text) {
        // Persist comments for saved workout posts so other users see them after refresh.
        const response = await fetch('/friends-feed/' + encodeURIComponent(workoutId) + '/comments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Unable to save comment.');
        }

        return data.comment;
    }

    async function saveFeedPostComment(feedPostId, text) {
        // Persist comments on manual feed posts separately from workout comments.
        const response = await fetch('/friends-feed/posts/' + encodeURIComponent(feedPostId) + '/comments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Unable to save comment.');
        }

        return data.comment;
    }

    function createPostCard(ownerId, author, content, isOwner, feedPostId, timestamp) {
        const postId = feedPostId ? 'saved-post-' + feedPostId : 'post-' + (++postCount);
        const card = document.createElement('div');

        card.className = 'card app-card mb-4 post-card';
        card.dataset.ownerId = ownerId;

        if (feedPostId) {
            card.dataset.feedPostId = feedPostId;
        }

        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h3 class="card-title mb-1">${escapeHtml(author)}</h3>
                        <p class="text-muted small mb-0">${escapeHtml(timestamp || formatTimestamp(new Date()))}</p>
                    </div>

                    <div class="btn-group" role="group" aria-label="Post actions">
                        ${isOwner ? '<button type="button" class="btn btn-sm btn-outline-danger delete-post-btn">Delete</button>' : ''}
                        <button type="button" class="btn btn-sm btn-outline-primary comment-toggle-btn" data-bs-toggle="collapse" data-bs-target="#comments-${postId}" aria-expanded="false">Comment</button>
                    </div>
                </div>

                <p class="card-text mb-3">${escapeHtml(content)}</p>

                <div class="collapse" id="comments-${postId}">
                    <div class="card card-body bg-light">
                        <div class="comments-list mb-3"></div>
                        <div class="input-group">
                            <input type="text" class="form-control comment-input" placeholder="Write a comment..." aria-label="Comment text">
                            <button type="button" class="btn btn-primary add-comment-btn">Add</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        return card;
    }

    function addPost(event) {
        event.preventDefault();

        const author = currentDisplayUsername;
        const content = postContentInput.value.trim();

        if (!content) {
            alert('Please enter a post message before adding it to the feed.');
            return;
        }

        const isOwner = currentUserId !== '';
        addPostBtn.disabled = true;

        saveFeedPost(content)
            .then(function (savedPost) {
                const postCard = createPostCard(
                    savedPost.owner_id,
                    savedPost.username || author,
                    savedPost.content,
                    isOwner,
                    savedPost.id,
                    savedPost.timestamp
                );
                const firstPost = feedContainer.querySelector('.post-card');

                if (firstPost) {
                    feedContainer.insertBefore(postCard, firstPost);
                } else {
                    feedContainer.appendChild(postCard);
                }

                postContentInput.value = '';
                updateEmptyState();
            })
            .catch(function (error) {
                alert(error.message);
            })
            .finally(function () {
                addPostBtn.disabled = false;
            });
    }

    function handleFeedClick(event) {
        if (event.target.classList.contains('delete-post-btn')) {
            const card = event.target.closest('.post-card');

            if (!card) {
                return;
            }

            const ownerId = card.dataset.ownerId;

            if (ownerId !== currentUserId) {
                alert('Only the owner of this post can delete it.');
                return;
            }

            const feedPostId = card.dataset.feedPostId;

            if (!feedPostId) {
                card.remove();
                updateEmptyState();
                return;
            }

            event.target.disabled = true;

            deleteFeedPost(feedPostId)
                .then(function () {
                    card.remove();
                    updateEmptyState();
                })
                .catch(function (error) {
                    alert(error.message);
                })
                .finally(function () {
                    event.target.disabled = false;
                });
        }

        if (event.target.classList.contains('add-comment-btn')) {
            const cardBody = event.target.closest('.card-body');
            const postCard = event.target.closest('.post-card');

            if (!cardBody || !postCard) {
                return;
            }

            const input = cardBody.querySelector('.comment-input');
            const commentsList = cardBody.querySelector('.comments-list');

            if (!input || !commentsList) {
                return;
            }

            const commentText = input.value.trim();

            if (!commentText) {
                alert('Please enter a comment before adding it.');
                return;
            }

            const workoutId = postCard.dataset.workoutId;
            const feedPostId = postCard.dataset.feedPostId;

            if (!workoutId && !feedPostId) {
                const timestamp = formatTimestamp(new Date());
                const commentItem = createCommentItem(currentUserId, currentDisplayUsername, commentText, timestamp);

                commentsList.appendChild(commentItem);
                input.value = '';
                return;
            }

            event.target.disabled = true;

            const saveComment = workoutId ? saveWorkoutComment(workoutId, commentText) : saveFeedPostComment(feedPostId, commentText);

            saveComment
                .then(function (savedComment) {
                    const commentItem = createCommentItem(
                        savedComment.owner_id,
                        savedComment.username,
                        savedComment.text,
                        savedComment.timestamp
                    );

                    commentsList.appendChild(commentItem);
                    input.value = '';
                })
                .catch(function (error) {
                    alert(error.message);
                })
                .finally(function () {
                    event.target.disabled = false;
                });
        }
    }

    if (addPostBtn && postContentInput) {
        addPostBtn.addEventListener('click', addPost);
    }

    feedContainer.addEventListener('click', handleFeedClick);

    updateEmptyState();
});
