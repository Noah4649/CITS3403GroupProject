document.addEventListener('DOMContentLoaded', function () {
    const feedContainer = document.getElementById('feed-container');

    if (!feedContainer) {
        return;
    }

    const emptyMessage = document.getElementById('empty-feed-message');
    const postUsernameInput = document.getElementById('post-username');
    const postContentInput = document.getElementById('post-content');
    const addPostBtn = document.getElementById('add-post-btn');

    const currentUsername = feedContainer.dataset.currentUsername || '';

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

    function createCommentItem(commenter, text, timestamp) {
        const comment = document.createElement('div');

        comment.className = 'mb-3 border-bottom pb-2';
        comment.innerHTML =
            '<strong>' + escapeHtml(commenter) + '</strong> ' +
            '<span class="text-muted small">' + escapeHtml(timestamp) + '</span>' +
            '<p class="mb-0">' + escapeHtml(text) + '</p>';

        return comment;
    }

    function createPostCard(author, content, isOwner) {
        const postId = 'post-' + (++postCount);
        const card = document.createElement('div');

        card.className = 'card app-card mb-4 post-card';
        card.dataset.owner = author;

        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h3 class="card-title mb-1">${escapeHtml(author)}</h3>
                        <p class="text-muted small mb-0">${escapeHtml(formatTimestamp(new Date()))}</p>
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

        const author = postUsernameInput.value.trim() || currentUsername;
        const content = postContentInput.value.trim();

        if (!content) {
            alert('Please enter a post message before adding it to the feed.');
            return;
        }

        const isOwner = author === currentUsername;
        const postCard = createPostCard(author, content, isOwner);

        feedContainer.appendChild(postCard);
        postContentInput.value = '';

        updateEmptyState();
    }

    function handleFeedClick(event) {
        if (event.target.classList.contains('delete-post-btn')) {
            const card = event.target.closest('.post-card');

            if (!card) {
                return;
            }

            const owner = card.dataset.owner;

            if (owner !== currentUsername) {
                alert('Only the owner of this post can delete it.');
                return;
            }

            card.remove();
            updateEmptyState();
        }

        if (event.target.classList.contains('add-comment-btn')) {
            const cardBody = event.target.closest('.card-body');

            if (!cardBody) {
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

            const timestamp = formatTimestamp(new Date());
            const commentItem = createCommentItem(currentUsername, commentText, timestamp);

            commentsList.appendChild(commentItem);
            input.value = '';
        }
    }

    if (addPostBtn && postUsernameInput && postContentInput) {
        addPostBtn.addEventListener('click', addPost);
    }

    feedContainer.addEventListener('click', handleFeedClick);

    updateEmptyState();
});