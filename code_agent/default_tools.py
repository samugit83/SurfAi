import copy
import re
import os

DEFAULT_TOOLS = [
            {
                "tool_name": "helper_model",
                "lib_names": ["models"],
                "instructions": "An LLM usefull to elaborate any output from previous steps. Don't create loops, just use the LLM to elaborate the output for just one step.",
                "use_exaclty_code_example": True,
                "code_example": """
                    def call_helper_model(previous_output):
                        '''
                        previous_output input types:
                            "message": string
                        return types:
                            "elaborated_output": string
                        '''
                        from models.models import call_model
                        prompt = f"<here you describe how to elaborate the previous output>: <previous_output.message>"
                        llm_response = call_model(
                            chat_history=[{"role": "user", "content": prompt}],
                            model="{TOOL_HELPER_MODEL}"
                        )
                        return {"elaborated_output": llm_response}
                    except Exception as e:
                        logger.error(f"Error calling helper model: {e}")
                        return {"elaborated_output": ""}
                """
            },
            { 
                "tool_name": "ingest_simple_rag",
                "lib_names": ["rag.simple_rag"],
                "instructions": """This is a simple RAG ingestion tool. Ingest the text into the vector database.""",
              
                "use_exaclty_code_example": True,
                "code_example": """
                    def ingest_rag_db(previous_output):
                        # Ingest texts into the database
                        '''
                        previous_output input types:
                            "text": string
                        return types:
                            "ingest_result": string
                        '''
                        from rag.simple_rag.ingest import ingest_texts

                        text = previous_output.get("text", "")

                        ingest_result = ingest_texts([text], model="{SIMPLE_RAG_EMBEDDING_MODEL}")
                        ingest_result_string = str(ingest_result)
                        return {"ingest_result": ingest_result_string}
                    except Exception as e:
                        logger.error(f"Error ingesting texts: {e}")
                        return {"ingest_result": ""}
                """
            },
            {
                "tool_name": "retrieve_simple_rag",
                "lib_names": ["rag.simple_rag"],
                "instructions": """This is a simple RAG extraction tool. Extract only the information and provide a straightforward response with the acquired information. Do not create additional tools unless necessary. Retrieve the text from the vector database. Activate this tool when the client explicitly requests to retrieve the text from a database.""",
                "use_exaclty_code_example": True,
                "code_example": """
                    def retrieve_rag_db(previous_output):
                        # Function to retrieve content from the vector db
                        '''
                        previous_output input types:
                            "query": string
                        return types:
                            "retrieve_result": string
                        '''
                        try:
                            from rag.simple_rag.retrieve import retrieve_documents
                            query = previous_output.get("query", "")
                            retrieve_result = retrieve_documents(query, model="{SIMPLE_RAG_EMBEDDING_MODEL}")
                            retrieve_result_string = str(retrieve_result)
                            return {"retrieve_result": retrieve_result_string}
                        except Exception as e:
                            logger.error(f"Error extracting documents: {e}")
                            return {"retrieve_result": ""}
                """
            },
            {
                "tool_name": "ingest_hybrid_vector_graph_rag", 
                "lib_names": ["rag.hybrid_vector_graph_rag"],
                "instructions": """This is an Hybrid Vector Graph RAG ingestion tool. Ingest the text into the vector and graph database.""",
                "use_exaclty_code_example": True,
                "code_example": """
                    def ingest_hybrid_vector_graph_rag_db(previous_output):
                        # Ingest texts into the vector and graph database
                        '''
                        previous_output input types:
                            "text": string
                        return types:
                            "ingest_result": string
                        '''
                        from rag.hybrid_vector_graph_rag.engine import HybridVectorGraphRag

                        try:
                            engine = HybridVectorGraphRag()
                            text = previous_output.get("text", "")
                            ingest_result = engine.ingest([text])
                            return {"ingest_result": ingest_result} 
                        except Exception as e:
                            logger.error(f"Error ingesting texts: {e}")
                            return {"ingest_result": ""}
                """
            },
            {
                "tool_name": "retrieve_hybrid_vector_graph_rag",
                "lib_names": ["rag.hybrid_vector_graph_rag"],
                "instructions": """This is an Hybrid Vector Graph RAG extraction tool. Extract only the information and provide a straightforward response with the acquired information. 
                Do not create additional tools unless necessary. Retrieve the text from the vector database. Activate this tool when the client explicitly requests to retrieve the text from a database.""",
                "use_exaclty_code_example": True,
                "code_example": """
                    def retrieve_hybrid_vector_graph_rag_db(previous_output):
                        # function to retrieve content from the vector and graphg db
                        '''
                        previous_output input types:
                            "query": string
                        return types:
                            "retrieve_result": string
                        '''
                        from rag.hybrid_vector_graph_rag.engine import HybridVectorGraphRag

                        try:
                            engine = HybridVectorGraphRag()
                            question = previous_output.get("query", "")
                            result = engine.retrieve(question)
                            return {"retrieve_result": result}
                        except Exception as e:
                            logger.error(f"Error extracting documents: {e}")
                            return {"retrieve_result": ""}
                """
            },
            { 
                "tool_name": "search_web",
                "lib_names": ["duckduckgo_search", "beautifulsoup4",  "requests"],
                "instructions": "A library to scrape the web. Never use the regex or other specific method to extract the data, always output the whole page. The data must be extracted or summarized from the page with models lib.",
                "use_exaclty_code_example": True,
                "code_example": """
                    def search_web(previous_output, max_results=3, max_chars=10000):
                        #Perform a DuckDuckGo search for the specified query, then fetch the entire HTML of each result, capped at max_chars characters. Returns one long string containing the full HTML of all results.
                        #Instructions:
                        # If some page scrapes fail, it is not a critical issue. The final result can still be satisfactory if at least one page result is obtained.
                        # Never use urls with parameters, just scrape simple urls.
                        '''
                        previous_output input types:
                            "query": string
                        return types:
                            "html_content": string
                        '''
                        from duckduckgo_search import DDGS
                        import requests

                        ddgs = DDGS()
                        try:
                            # Use DuckDuckGo to get 'max_results' search results
                            results = ddgs.text(previous_output.get("query", ""), max_results=max_results)
                            full_html_output = []

                            # For each result, fetch the entire page with requests
                            for result in results:
                                href = result.get("href", "")
                                if not href:
                                    # Skip if there's no link
                                    continue

                                try:
                                    resp = requests.get(href, timeout=10)
                                    resp.raise_for_status()

                                    # Parse HTML and extract visible text using BeautifulSoup
                                    soup = BeautifulSoup(resp.text, 'html.parser')
                                    text_content = soup.get_text(separator=' ', strip=True)

                                    # Limit the extracted text to max_chars characters
                                    limited_text = text_content[:max_chars]

                                    # Optionally, prepend some metadata
                                    title = result.get("title", "")
                                    full_text_output.append(
                                        f"=== START OF ARTICLE ==="
                                        f"Title: {title} URL: {href}"
                                        f"{limited_text}"
                                        f"=== END OF ARTICLE ==="
                                    )

                                    successful_hrefs.append(href)

                                except Exception as fetch_err:
                                    logger.error(f"Error fetching page {href}: {fetch_err}")
                                    continue

                            # Join all the fetched content into a single string
                            logger.info(f"Retrieved {len(successful_hrefs)} pages. URLs: {successful_hrefs}")
                            return {"html_content": " ".join(full_text_output)}

                        except Exception as e:
                            logger.error(f"Error in search_web: {e}")
                            return {"html_content": "no data found"}
                """
            },
            {
            "tool_name": "send_email",
            "lib_names": ["smtplib", "email"],
            "instructions": "Send an email to the user with the given email, subject and html content.",
            "use_exaclty_code_example": True,
            "code_example": """
                def send_email(previous_output, GMAILUSER: str = "cronomegawatt@gmail.com", PASSGMAILAPP: str = "viyuqoeqhitzxtkl") -> dict:
                    '''
                    previous_output input types:
                        "email": string
                        "subject": string
                        "html": string
                    return types:
                        "info": string
                    '''

                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart

                    # Gmail credentials
                    usermail = GMAILUSER
                    passgmailapp = PASSGMAILAPP

                    # SMTP server configuration
                    smtp_server = "smtp.gmail.com"
                    port = 587  # For TLS encryption

                    try:
                        # Create the email message
                        message = MIMEMultipart()
                        message["From"] = usermail
                        message["To"] = previous_output.get("email", "")
                        message["Subject"] = previous_output.get("subject", "")

                        # Attach the HTML content
                        if previous_output.get("html", ""):
                            message.attach(MIMEText(previous_output.get("html", ""), "html"))

                        # Establish connection to the SMTP server
                        with smtplib.SMTP(smtp_server, port) as server:
                            server.starttls()  # Secure the connection
                            server.login(usermail, passgmailapp)  # Log in to the SMTP server
                            
                            # Send the email
                            server.sendmail(usermail, previous_output.get("email", ""), message.as_string())
                            logger.info(f"Email sent to {previous_output.get('email', '')} with subject {previous_output.get('subject', '')}")

                        return {"info": "Email sent successfully"}

                    except Exception as error:
                        logger.error(f"Error sending email: {error}")
                        return {"info": "Error sending email"}

                """
        }]



def generate_default_tools(tools=DEFAULT_TOOLS):
    """
    Applies dynamic variables to any string fields within the tools that contain matching placeholders.

    Args:
        tools (list): The list of tool dictionaries.
        variables (dict): A dictionary of variables to replace in the tool configurations.

    Returns:
        list: A new list of tools with variables applied.
    """
    updated_tools = copy.deepcopy(tools)
    placeholder_pattern = re.compile(r"\{(\w+)\}")  # Matches {VAR_NAME}

    variables = {
        "TOOL_HELPER_MODEL": os.getenv("TOOL_HELPER_MODEL"),
        "JSON_PLAN_MODEL": os.getenv("JSON_PLAN_MODEL"),
        "EVALUATION_MODEL": os.getenv("EVALUATION_MODEL"),
        "SIMPLE_RAG_EMBEDDING_MODEL": os.getenv("SIMPLE_RAG_EMBEDDING_MODEL")
    }

    for tool in updated_tools:
        for key, value in tool.items():
            if isinstance(value, str):
                matches = placeholder_pattern.findall(value)
                for match in matches:
                    if match in variables:
                        placeholder = f"{{{match}}}"
                        value = value.replace(placeholder, variables[match])
                tool[key] = value
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, str):
                        matches = placeholder_pattern.findall(item)
                        for match in matches:
                            if match in variables:
                                placeholder = f"{{{match}}}"
                                item = item.replace(placeholder, variables[match])
                    new_list.append(item)
                tool[key] = new_list
    return updated_tools