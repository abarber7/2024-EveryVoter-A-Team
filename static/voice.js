document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById('voice-button');
    const status = document.getElementById('voice-status');
    
    // Access candidates data from the hidden script tag
    const candidates = JSON.parse(document.getElementById('candidates-data').textContent);

    button.addEventListener('click', function() {
        if ('webkitSpeechRecognition' in window) {
            const recognition = new webkitSpeechRecognition();
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            // Update the button and status text when starting to listen
            button.textContent = 'Listening...';
            button.disabled = true;
            button.classList.remove('btn-secondary');
            button.classList.add('btn-warning');
            status.textContent = 'Please speak your vote.';

            recognition.onstart = function() {
                status.textContent = 'Listening... Please speak your vote.';
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript.toLowerCase();
                status.textContent = `You said: ${transcript}`;

                const candidate = candidates.find(c => transcript.includes(c.toLowerCase()));
                if (candidate) {
                    status.textContent += ` (Recognized: ${candidate})`;

                    // Send the recognized candidate to the backend for processing
                    fetch('/voice_vote', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ candidate })
                    })
                    .then(response => response.json())
                    .then(data => {
                        status.textContent = data.message;

                        // Reset button after vote is processed
                        button.textContent = 'Speak Now';
                        button.disabled = false;
                        button.classList.remove('btn-warning');
                        button.classList.add('btn-secondary');
                    });
                } else {
                    status.textContent = 'Candidate not recognized, please try again.';
                    button.textContent = 'Speak Now';
                    button.disabled = false;
                    button.classList.remove('btn-warning');
                    button.classList.add('btn-secondary');
                }
            };

            recognition.onerror = function(event) {
                status.textContent = `Error occurred: ${event.error}`;
                button.textContent = 'Speak Now';
                button.disabled = false;
                button.classList.remove('btn-warning');
                button.classList.add('btn-secondary');
            };

            recognition.start();
        } else {
            status.textContent = 'Your browser does not support speech recognition.';
        }
    });
});
