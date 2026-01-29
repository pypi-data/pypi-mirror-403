import os
import logging
import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
logger = logging.getLogger(__name__)


class STTManager:
    def __init__(self):
        """
        Initializes the STTManager.
        
        Note:
            The following must be set in your .env file:
            - OPENAI_API_KEY
            - AGENT_API_URL (If not set, posting to agent will be disabled)
        """
        self._api_key = os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY must be set in your .env file.")
        
        self._agent_api_url = os.getenv("AGENT_API_URL")
        if not self._agent_api_url:
            logger.warning("AGENT_API_URL is not set in .env. Posting to agent will be disabled.")
        
        self._openai_client = AsyncOpenAI(api_key=self._api_key)
        self._http_client = httpx.AsyncClient()

    async def close(self):
        """
        Cleans up resources used by the STTManager.
        """
        await self._http_client.aclose()
        await self._openai_client.close()

    async def transcribe_audio(self, file_path: str, model: str = "whisper-1") -> str:
        """
        Transcribes an audio file using OpenAI's whisper model.

        Args:
            file_path: The path to the audio file to transcribe. 
                       Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, and webm.
            model: The name of the whisper model to use.
                   Note: The OpenAI API currently only supports "whisper-1".
        Returns:
            The transcribed text as a string.
        """
        logger.info(f"Starting transcription for file: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at: {file_path}")

        with open(file_path, "rb") as audio_file:
            transcript = await self._openai_client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
        logger.info(f"Successfully transcribed file: {file_path}")

        return transcript.text

    async def transcribe_and_post(self, file_path: str):
        """
        Processes an audio file by transcribing it and posting the result to the agent API under a 'message' key.

        Args:
            file_path: The path to the audio file to process.
                       Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, and webm.
        Returns:
            A tuple containing the transcribed text (str) and the API response data (dict, str, or None).
        """
        try:
            # Transcribe the audio file
            transcript_text = await self.transcribe_audio(file_path)

            response = None
            # Post the transcribed text to the agent API
            if self._agent_api_url:
                response = await self._post_to_agent(transcript_text)
            else:
                logger.info("AGENT_API_URL not set, skipping post to agent.")
            
            return transcript_text, response

        except FileNotFoundError:
            logger.error(f"Audio file not found at: {file_path}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"An error occurred during processing of {file_path}: {e}", exc_info=True)
            raise

    async def _post_to_agent(self, text: str):
        """
        Posts the transcribed text to the agent API under a 'message' key.
        
        Args:
            text: The transcribed text to post.
        """
        payload = {"message": text}
        try:
            logger.info(f"Posting to agent with payload: {payload}")
            response = await self._http_client.post(self._agent_api_url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully posted to agent. Status: {response.status_code}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to post to agent API: {e}", exc_info=True)
            raise