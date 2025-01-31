# SurfAi 🌐🤖

**AI-Powered Web Automation Agent**

SurfAi is an intelligent and lightweight web automation engine that leverages AI to interpret natural language instructions and automate web interactions using Playwright. It combines LLM capabilities with browser automation for complex task execution.

## Video Demo 
Discover the capabilities of SurfAi:
[Automate a Linkedin Post with Credentials](https://youtu.be/2-vUuPIWJ30).
[Automate a job application on LinkedIn](https://youtu.be/T3Ej4-eeDag).
[Automate the addition of a new work experience on LinkedIn](https://youtu.be/2-vUuPIWJ30).

## Features ✨

- **AI-Driven Task Generation**: Converts natural language prompts into executable Playwright commands
- **Self-Correcting Workflow**: Dynamic task adjustment based on execution results and page context
- **Interactive Element Highlighting**: Visual numbering system for precise element targeting
- **Multi-Strategy Execution**: Automatic fallback commands for reliable task completion
- **Context-Aware Scraping**: Real-time page analysis with intelligent content truncation
- **Comprehensive Logging**: Detailed execution tracking with memory buffering


## Installation 🛠️

Follow the steps below to set up and run the application using Docker. This setup ensures that all necessary services are built and started correctly, with session management handled seamlessly via a Redis database.

### Prerequisites
- **Docker**: Ensure that Docker is installed on your system. You can download it from [here](https://www.docker.com/get-started).
- **Docker Compose**: Typically included with Docker Desktop installations. Verify by running `docker-compose --version`. 

### Steps to Initialize the Application

1. Clone the repository:

```bash
git clone https://github.com/samugit83/SurfAi
```

2. Navigate to the project directory:
```bash
cd SurfAi
```

3. Build the Docker image:
```bash
docker-compose build
```

4. Run the Docker container:
```bash
docker-compose up -d
```

5. Check the backend logs:
```bash
docker logs -f surf_ai
```

6. Access the AI Agent chat interface:
```bash
http://localhost:5000
```

- if you want to rebuild and restart the application:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker logs -f surf_ai  
```

7. Environment Variables:
Create a file named .env in the root folder and insert all the following variables to ensure the application functions correctly:

```bash
OPENAI_API_KEY=open_ai_api_key
FLASK_PORT=5000
SURF_AI_JSON_TASK_MODEL=gpt-4o 
```

 
## Usage 🚀

To open the chat and send commands, go to http://localhost:5000/   
To view the automated navigation in the browser, go to http://localhost:6901/vnc.html


