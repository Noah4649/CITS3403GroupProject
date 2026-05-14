// ─── AJAX FRIEND REQUEST MANAGEMENT ────────────────────
document.addEventListener('DOMContentLoaded', function () {
    const friendSearchForm = document.getElementById('friend-search-form');
    const friendSearchInput = document.getElementById('friend-search-input');
    const friendSearchResultsBody = document.getElementById('friend-search-results-body');
    const sentRequestsBody = document.getElementById('sent-requests-body');
    const incomingRequestsBody = document.getElementById('incoming-requests-body');
    const friendsTableBody = document.getElementById('friends-table-body');

    function renderFriendSearchResults(users) {
        if (!friendSearchResultsBody) return;

        if (!users.length) {
            friendSearchResultsBody.innerHTML = `
                <tr class="empty-row">
                    <td>-</td>
                    <td>No users found.</td>
                    <td>-</td>
                </tr>
            `;
            return;
        }

        friendSearchResultsBody.innerHTML = users.map(user => {
            let actionHtml = '';

            if (user.relationship_status === 'friends') {
                actionHtml = `
                    <button type="button" class="btn btn-outline-secondary btn-sm" disabled>
                        Friends
                    </button>
                `;
            } else if (user.relationship_status === 'pending_sent') {
                actionHtml = `
                    <button type="button" class="btn btn-outline-secondary btn-sm" disabled>
                        Pending
                    </button>
                `;
            } else if (user.relationship_status === 'pending_received') {
                actionHtml = `
                    <button type="button" class="btn btn-outline-secondary btn-sm" disabled>
                        Request Received
                    </button>
                `;
            } else {
                actionHtml = `
                    <form class="send-friend-request-form" method="POST" action="/friends/request/${user.id}">
                        <button type="submit" class="btn btn-outline-primary btn-sm">
                            Add Friend
                        </button>
                    </form>
                `;
            }

            return `
                <tr>
                    <td>${user.username}</td>
                    <td>${user.email}</td>
                    <td>${actionHtml}</td>
                </tr>
            `;
        }).join('');
    }

    function removeEmptyRow(tbody) {
        if (!tbody) return;

        const emptyRow = tbody.querySelector('.empty-row');

        if (emptyRow) {
            emptyRow.remove();
        }
    }

    function addEmptyRowIfNeeded(tbody, colspan, message) {
        if (!tbody) return;

        const realRows = tbody.querySelectorAll('tr:not(.empty-row)');

        if (realRows.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="${colspan}">${message}</td>
                </tr>
            `;
        }
    }

    function addSentRequestRow(request) {
        if (!sentRequestsBody) return;

        removeEmptyRow(sentRequestsBody);

        if (document.getElementById(`sent-request-row-${request.id}`)) {
            return;
        }

        const row = document.createElement('tr');
        row.id = `sent-request-row-${request.id}`;

        row.innerHTML = `
            <td>${request.receiver_username}</td>
            <td>Pending</td>
        `;

        sentRequestsBody.prepend(row);
    }

    function addFriendRow(friend) {
        if (!friendsTableBody) return;

        removeEmptyRow(friendsTableBody);

        if (document.getElementById(`friend-row-${friend.id}`)) {
            return;
        }

        const row = document.createElement('tr');
        row.id = `friend-row-${friend.id}`;

        row.innerHTML = `
            <td>${friend.username}</td>
            <td>${friend.email}</td>
            <td>
                <form class="remove-friend-form" method="POST" action="/friends/remove/${friend.id}">
                    <button type="submit" class="btn btn-outline-secondary btn-sm">
                        Remove
                    </button>
                </form>
            </td>
        `;

        friendsTableBody.prepend(row);
    }

    if (friendSearchForm && friendSearchInput && friendSearchResultsBody) {
        let searchTimeout = null;

        friendSearchForm.addEventListener('submit', function (event) {
            event.preventDefault();
        });

        friendSearchInput.addEventListener('input', function () {
            const query = friendSearchInput.value.trim();

            clearTimeout(searchTimeout);

            searchTimeout = setTimeout(function () {
                if (!query) {
                    friendSearchResultsBody.innerHTML = `
                        <tr class="empty-row">
                            <td>-</td>
                            <td>Start typing to search.</td>
                            <td>-</td>
                        </tr>
                    `;
                    return;
                }

                fetch(`/api/friends/search?q=${encodeURIComponent(query)}`, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert(data.message || 'Could not search for users.');
                        return;
                    }

                    renderFriendSearchResults(data.users);
                })
                .catch(error => {
                    console.error('Friend search error:', error);
                    alert('Something went wrong while searching for users.');
                });
            }, 250);
        });
    }

    document.addEventListener('submit', function (event) {
        const form = event.target;

        // Send friend request without refreshing
        if (form.classList.contains('send-friend-request-form')) {
            event.preventDefault();

            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert(data.message || 'Could not send friend request.');
                    return;
                }

                form.outerHTML = `
                    <button type="button" class="btn btn-outline-secondary btn-sm" disabled>
                        Pending
                    </button>
                `;

                addSentRequestRow(data.request);
            })
            .catch(error => {
                console.error('Send friend request error:', error);
                alert('Something went wrong while sending the friend request.');
            });
        }

        // Accept friend request without refreshing
        if (form.classList.contains('accept-friend-request-form')) {
            event.preventDefault();

            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert(data.message || 'Could not accept friend request.');
                    return;
                }

                const row = document.getElementById(`incoming-request-row-${data.friendship_id}`);

                if (row) {
                    row.remove();
                }

                addFriendRow(data.friend);
                addEmptyRowIfNeeded(incomingRequestsBody, 2, 'No incoming friend requests.');
            })
            .catch(error => {
                console.error('Accept friend request error:', error);
                alert('Something went wrong while accepting the friend request.');
            });
        }

        // Decline friend request without refreshing
        if (form.classList.contains('decline-friend-request-form')) {
            event.preventDefault();

            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert(data.message || 'Could not decline friend request.');
                    return;
                }

                const row = document.getElementById(`incoming-request-row-${data.friendship_id}`);

                if (row) {
                    row.remove();
                }

                addEmptyRowIfNeeded(incomingRequestsBody, 2, 'No incoming friend requests.');
            })
            .catch(error => {
                console.error('Decline friend request error:', error);
                alert('Something went wrong while declining the friend request.');
            });
        }

        // Confirm and remove friend without refreshing
        if (form.classList.contains('remove-friend-form')) {
            event.preventDefault();

            const confirmed = confirm('Are you sure you want to remove this friend?');

            if (!confirmed) {
                return;
            }

            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert(data.message || 'Could not remove friend.');
                    return;
                }

                const row = document.getElementById(`friend-row-${data.friend_id}`);

                if (row) {
                    row.remove();
                }

                addEmptyRowIfNeeded(friendsTableBody, 3, 'You have not added any friends yet.');
            })
            .catch(error => {
                console.error('Remove friend error:', error);
                alert('Something went wrong while removing this friend.');
            });
        }
    });
});