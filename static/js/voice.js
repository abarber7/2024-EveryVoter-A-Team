document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById('voice-button');
    const status = document.getElementById('voice-status');
    const transcriptOutput = document.getElementById('transcript-output');
    const recordingDuration = 2000; // Define recording duration (in milliseconds)
    const electionId = window.election_id || null; // Ensure election ID is available

    if (!electionId) {
        console.error("Election ID is missing. Ensure election is selected or ongoing.");
        return;
    }

    if (button && status && transcriptOutput) {
        console.log("All elements found, proceeding with voice recognition...");

        button.addEventListener('click', handleVoiceButtonClick);

        async function handleVoiceButtonClick() {
            console.log("Voice button clicked");

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                status.textContent = 'Your browser does not support audio recording.';
                return;
            }

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const mediaRecorder = new MediaRecorder(stream);
                let audioChunks = [];

                updateButtonState('Listening...', true, 'btn-warning');

                mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
                mediaRecorder.onstop = async () => await handleRecordingStop(audioChunks);

                mediaRecorder.start();
                console.log("Recording started");

                setTimeout(() => mediaRecorder.stop(), recordingDuration);
            } catch (error) {
                console.error("Error accessing media devices:", error);
                status.textContent = 'Unable to access your microphone. Please check your browser settings.';
            }
        }

        async function handleRecordingStop(audioChunks) {
            console.log("Recording stopped");

            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice_vote.wav');
            formData.append('election_id', electionId);  // Pass election ID

            updateButtonState('Processing...', true);

            try {
                const transcript = await processAudio(formData);
                await submitTranscript(transcript);
            } catch (error) {
                console.error("Error during processing:", error);
                status.textContent = 'An error occurred. Please try again.';
                resetButtonState();
            }
        }

        async function processAudio(formData) {
            const response = await fetch('/process_audio', { 
                method: 'POST', 
                body: formData 
            });
            const data = await response.json();

            if (data.transcript) {
                const transcript = data.transcript.toLowerCase();
                status.textContent = `You said: ${transcript}`;
                transcriptOutput.textContent = `Transcription result: "${transcript}"`;
                return transcript;
            } else {
                throw new Error('Error processing audio.');
            }
        }

        async function submitTranscript(transcript) {
            const response = await fetch('/voice_vote', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transcript, election_id: electionId }) // Pass election ID
            });

            const data = await response.json();
            status.textContent = data.message;
            resetButtonState();
        }

        function updateButtonState(text, disabled, newClass = 'btn-secondary') {
            button.textContent = text;
            button.disabled = disabled;
            button.classList.remove('btn-secondary', 'btn-warning');
            button.classList.add(newClass);
        }

        function resetButtonState() {
            updateButtonState('Speak Now', false, 'btn-secondary');
        }
    } else {
        console.error('Voice button, status element, or transcript output not found.');
    }
});
