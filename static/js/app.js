document.getElementById('emailForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const to = document.getElementById('to').value;
    const from_email = document.getElementById('from_email').value;
    const subject = document.getElementById('subject').value;
    const body = document.getElementById('body').value;

    const emailData = {
        to: to,
        from_email: from_email,
        subject: subject,
        body: body
    };

    try {
        const response = await fetch('/send-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(emailData)
        });

        const result = await response.json();
        document.getElementById('statusMessage').innerText = result.message;
    } catch (error) {
        document.getElementById('statusMessage').innerText = 'Failed to send email';
    }
});
