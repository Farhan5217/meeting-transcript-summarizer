# Meeting Transcript Summarizer

A FastAPI application that automatically summarizes meeting transcripts using AI. The system processes meeting transcripts, extracts key information, and generates comprehensive summaries with references to the original content.

## Features

- **Transcript Processing**: Handles large meeting transcripts by breaking them into manageable chunks
- **Intelligent Summarization**: Extracts key points, decisions, tasks, next steps, and objections
- **Comprehensive Output**: Generates a final summary that consolidates all important information
- **Multiple Input Options**: Accept transcripts via URL or direct file upload
- **Reference Tracking**: Maintains links to the original transcript with timestamps
- **Flexible AI Backend**: Supports multiple AI providers (OpenAI, with code commented for Anthropic)

## Technology Stack

- **Backend**: FastAPI
- **AI Integration**: OpenAI GPT-4o (with option for Anthropic Claude)
- **Async Processing**: Asynchronous request handling for better performance
- **JSON Processing**: Structured data handling and transformation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/transcript-summarizer.git
cd transcript-summarizer
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys (see `.env.example` for required variables)

## Usage

### Starting the Server

```bash
uvicorn app:app --reload
```

The server will start at `http://localhost:8000`

### API Endpoints

#### 1. Summarize via URL

`POST /summarize_transcript/`

Request body:
```json
{
  "transcript_url": "https://example.com/path/to/transcript.json"
}
```

#### 2. Summarize via File Upload

`POST /summarize_transcript_file/`

Upload a JSON file containing the transcript data.

### Example Response

```json
{
  "final_summary": "...",
  "clean_summaries": "..."
}
```

## Input Format

The expected transcript JSON format:

```json
{
  "transcriptions": [
    {
      "transcriptionId": "unique-id",
      "speakerId": "speaker-id",
      "text": "Spoken text",
      "startTime": 0.0,
      "endTime": 10.0
    },
    ...
  ],
  "speakers": [
    {
      "speakerId": "speaker-id",
      "name": "Speaker Name"
    },
    ...
  ],
  "attendees": [
    {
      "attendeeId": "attendee-id",
      "email": "attendee@example.com"
    },
    ...
  ]
}
```

## Output Format

The summarizer generates a structured JSON output with the following sections:

- **Summary**: Overall meeting summary
- **Key Points**: Main ideas discussed
- **Decisions**: Decisions made during the meeting
- **Tasks**: Tasks assigned with responsible persons
- **Next Steps**: Follow-up actions
- **Objections**: Sales objections or concerns raised

Each section includes references to the original transcript with timestamps.

