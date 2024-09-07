# Team Name: TopQuality-A-Team
# Application Name:EveryVoter
### NO VOTES LEFT BEHIND
## System Overview
EveryVoter is an electronic and highly accessible voting system designed to enable secure remote voting from any location. The system ensures accessibility, configurability, and early result determination to provide a comprehensive solution for modern voting needs.

## Configurability
EveryVoter allows election administrators to configure various aspects of the voting process, including:
- **Candidate Specification**: Administrators can specify the candidates running in the election.
- **Total Available Votes**: Set the total number of votes that can be cast.
- **Voting Date Range**: Define the start and end dates for the voting period.
- **Winning Criteria**: Determine the winning candidate based on a predefined vote threshold.

## Voting Methods
EveryVoter supports multiple voting methods to accommodate different voter preferences and accessibility needs:
- **Touch-Based Voting**: Users can cast their votes using touch input.
- **Voice-Based Voting**: Voice commands allow users to vote hands-free.
- **Text-Based Voting**: Voters can also use text input to cast their votes.

## Multilingual Support, Acessibility, & Built-In Chat
To bring everyone along, EveryVoter integrates LangChain and language models (LLMs) to:
- Enable voting for non-English speaking users by translating the user interface and instructions into various languages.
- Provide a multilingual experience.
- Enable built-in chatbots to assist voters in their voting experience.

## Early Determination of Results
EveryVoter implements logic to declare a winner once a candidate reaches the required number of votes before the end of the voting period. This feature allows for quicker determination of election outcomes, improving efficiency.

---

EveryVoter is developed with a focus on the universe of potential voters, everywhere.

## Steps to Run the Application

This project is built using Python and managed with Poetry. Below are the instructions for setting up your development environment.

To install Poetry on Linux, run the following command in your terminal: `curl -sSL https://install.python-poetry.org | python3 -`. To install Poetry on Windows, open PowerShell and run: `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -`.

After installing Poetry, you need to ensure that the Poetry executable is in your system's PATH. 

For Linux, add the following line to your `~/.bashrc`, `~/.zshrc`, or equivalent shell configuration file: `export PATH="$HOME/.local/bin:$PATH"`. Then, reload your shell configuration by running: `source ~/.bashrc` or, if you're using Zsh, `source ~/.zshrc`. 

On Windows, Poetry is usually added to the PATH automatically. If it isn’t, you can add it manually: 1. Open the Start menu, search for "Environment Variables", and select "Edit the system environment variables". 2. In the System Properties window, click on the "Environment Variables" button. 3. In the Environment Variables window, find the "Path" variable under "System variables" and click "Edit". 4. Click "New" and add the path to Poetry's installation directory, usually `C:\Users\YourUsername\AppData\Roaming\Python\Scripts`.

After installing Poetry and ensuring it's in your PATH, navigate to the root of this repository and install the dependencies by running `poetry install`.

Next, create a `.env` file in the root of the repository and add the following environment variables: `FLASK_APP=application:app` and `OPENAI_API_KEY=your_openai_api_key_here`. Replace `your_openai_api_key_here` with your actual OpenAI API key.

Now you can run the application using `poetry run flask run`. This command will start the Flask development server.

To remove squiggly warning lines from files where LangChain is used, run `poetry shell` and copy the virtual environment path that appears in the console(e.g. C:\Users\YOURUSER\AppData\Local\pypoetry\Cache\virtualenvs\everyvoter-a-team-7zgR628F-py3.12). This is the interpreter path. Add it to your VS Code settings: "Enter interpreter path" and paste the path.

To run the tests, run `python -m unittest discover tests`.

For the current version, you can enter restaurant information, select Generate Restaurants, then begin the election.

To test voting by voice, enter basic candidates in the Choose Your Candidates form, press Speak Now and speak clearly. 