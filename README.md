# SurfAi 🌐🤖

**AI-Powered Web Automation Agent** - Version 1.1.1

SurfAi is an intelligent and lightweight web automation engine that leverages AI to interpret natural language instructions and automate web interactions using Playwright. It combines LLM capabilities with browser automation for complex task execution.

## Video Demo 
Discover the capabilities of SurfAi:
[Task: Post on Linkedin](https://youtu.be/n2jnfNpV6BQ).
[Task: Job application on LinkedIn](https://youtu.be/T3Ej4-eeDag).
[Task: Add a new work experience on LinkedIn](https://youtu.be/hR73ftZ4t_4).
[Task: Search for an available hotel on Booking.com and get info](https://youtu.be/o5Gn-XVv_h8).

## Features ✨

- **AI-Driven Task Generation**: Converts natural language prompts into executable Playwright commands
- **Self-Correcting Workflow**: Dynamic task adjustment based on execution results and page context
- **Interactive Element Highlighting**: Visual numbering system for precise element targeting
- **Multi-Strategy Execution**: Automatic fallback commands for reliable task completion
- **Context-Aware Scraping**: Real-time page analysis with intelligent content truncation
- **Comprehensive Logging**: Detailed execution tracking with memory buffering
- **Data Extraction**: Extract data from the page and store it in the tasks to provide a final answer
- **Multi-Tab Navigation**: Navigate on multiple tabs and switch between them


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

7. Access the automated navigation in the browser:
```bash
http://localhost:6901/vnc.html
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

8. Some prompt example:
- Go to Amazon and search for an iPhone 13 smartphone. Navigate to the page of the first result and tell me the vendor name in the buy box, the selling price, and if it offers Prime.
- Go to https://www.linkedin.com/feed, log in with email: 'mymail' and password: 'mypassword'. Comment on the first 2 posts with intelligent and contextually relevant comments based on the text and image of the post, with a minimum of 40 words.
- Visit 4 different electronics e-commerce websites to obtain the average price of the top 3 search results for the query: iPhone 13 Pro. The websites are: https://www.bestbuy.com/, https://www.croma.com/, https://www.mediaworld.it/, https://www.boulanger.com/. Then, provide me with a comparison report of the prices found. If you find a currency other than the euro, search on Google for the latest exchange rate and convert it.



## Contribution Guidelines 

We welcome contributions from the community! If you'd like to contribute, please follow these guidelines:

### How to Contribute
1. **Fork the Repository** – Click the "Fork" button at the top right of this page and clone the forked repository to your local machine.
2. **Create a Branch** – Use a descriptive branch name related to the feature or fix (e.g., `feature-new-component` or `fix-bug-123`).
3. **Make Your Changes** – Implement your feature, bug fix, or improvements, ensuring the code follows the project's coding style.
4. **Test Your Changes** – Run all tests to ensure that nothing is broken.
5. **Commit Your Changes** – Use clear and concise commit messages (e.g., `fix: resolve issue with user authentication`).
6. **Push to GitHub** – Push your branch to your forked repository.
7. **Submit a Pull Request (PR)** – Open a PR against the `main` or `develop` branch with a clear description of your changes.

### Contribution Guidelines
- Follow the coding standards and style used in the project.
- Keep PRs focused and small for easier review.
- Ensure new features or fixes are well-tested.
- Provide clear documentation if introducing a new feature.

By contributing, you agree that your changes will be licensed under the same license as the project.

Thank you for helping improve this project! 🚀
