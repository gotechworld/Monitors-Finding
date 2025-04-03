# Monitors Finding

</br>

### Installation
`pip install --no-cache-dir -r requirements.txt`

Create a `.env` file to store the `GEMINI_API_KEY=""` and the `SERPER_API_KEY=""`.

`streamlit run app.py`

Access the application at http://localhost:8501

</br>

### Containerize Streamlit app

+ Build the image:
`docker image build --no-cache -t eap-monitors:0.1 .`

+ Run the container:
`docker container run -d -p 8501:8501 -e GEMINI_API_KEY="" -e SERPER_API_KEY="" eap-monitors:0.1`

Access the application at http://localhost:8501

</br>

__Note__: When running the container, you'll need to provide your Google Gemini API KEY and Serper API KEY as an environment variable.
