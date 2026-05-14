// ─── AJAX FRIEND REQUEST SENDING ───────────────────────
document.addEventListener('DOMContentLoaded', function () {
    const sentRequestsBody = document.getElementById('sent-requests-body');

    function removeEmptyRow(tbody) {
        if (!tbody) return;

        const emptyRow = tbody.querySelector('.empty-row');

        if (emptyRow) {
            emptyRow.remove();
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

    document.addEventListener('submit', function (event) {
        const form = event.target;

        if (!form.classList.contains('send-friend-request-form')) {
            return;
        }

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
    });
});