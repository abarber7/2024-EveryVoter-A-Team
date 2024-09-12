// Function to dynamically generate candidate input fields
function generateCandidateFields() {
    const numCandidates = document.getElementById('number_of_custom_candidates').value;
    const candidatesContainer = document.getElementById('custom_candidates_container');
    candidatesContainer.innerHTML = ""; // Clear previous candidate fields

    // Generate input fields based on the user's input
    for (let i = 0; i < numCandidates; i++) {
        const inputField = document.createElement('input');
        inputField.type = 'text';
        inputField.name = `candidate_${i + 1}`;
        inputField.classList.add('form-control', 'mb-2');
        inputField.placeholder = `Enter Candidate ${i + 1}`;
        inputField.required = true;
        candidatesContainer.appendChild(inputField);
    }
}