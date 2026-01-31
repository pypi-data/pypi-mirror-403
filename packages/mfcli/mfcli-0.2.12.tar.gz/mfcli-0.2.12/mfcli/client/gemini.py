import asyncio
import os
import traceback
from pathlib import Path
from typing import Type, Literal, List

from google import genai
from google.genai.client import AsyncClient
from google.genai.types import GenerateContentConfig, HttpRetryOptionsDict, HttpOptions, File
from pydantic import BaseModel, ValidationError
from typing_extensions import TypeVar

from mfcli.agents.tools.general import format_instructions
from mfcli.utils.config import get_config
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar(name='T', bound=BaseModel)

GeminiSupportedModels = Literal['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-3-pro-preview']
DefaultGeminiModel = 'gemini-2.5-pro'


class GeminiFileEntity(BaseModel):
    path: Path
    mime_type: str


GeminiFileInput = GeminiFileEntity | str | Path


class Gemini:
    def __init__(self):
        self._config = get_config()
        self._client: AsyncClient = genai.Client(api_key=self._config.google_api_key).aio

    @staticmethod
    def _get_request_config(
            timeout: int,
            instructions: str,
            response_model: Type[T]
    ) -> GenerateContentConfig:
        retry_options = HttpRetryOptionsDict(
            attempts=3,
            initial_delay=1,
            max_delay=10,
            exp_base=2
        )
        http_options = HttpOptions(
            retry_options=retry_options,
            timeout=timeout * 1000
        )
        return GenerateContentConfig(
            system_instruction=instructions,
            response_mime_type="application/json",
            response_json_schema=response_model.model_json_schema(),
            http_options=http_options
        )

    @staticmethod
    def _file_access_check(file_path: str):
        file_path_obj = Path(file_path)

        # Validate file exists and is readable
        if not file_path_obj.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not os.access(file_path_obj, os.R_OK):
            raise ValueError(f"File is not readable: {file_path}")

    async def upload(self, file: GeminiFileInput) -> File:
        config = None
        if isinstance(file, GeminiFileEntity):
            file_path = str(file.path)
            config = {"mime_type": file.mime_type}
        else:
            file_path = str(file)
        self._file_access_check(file_path)
        return await self._client.files.upload(
            file=file_path,
            config=config
        )

    async def _generate_once(
            self,
            prompt: str,
            instructions: str,
            response_model: Type[T],
            model: GeminiSupportedModels,
            files: List[File] | None = None,
            timeout: int = 60
    ) -> str:
        contents = [prompt]
        if files:
            contents += files
        response = await self._client.models.generate_content(
            model=str(model),
            contents=contents,
            config=self._get_request_config(timeout, instructions, response_model),
        )
        return response.text

    async def _generate_with_retry(
            self,
            prompt: str,
            instructions: str,
            response_model: Type[T],
            model: GeminiSupportedModels,
            files: List[File] | None = None,
            timeout: int = 60
    ) -> T:

        attempts = 3
        backoff = 1.5
        delay = 1.0
        last_err = None

        for attempt in range(1, attempts + 1):

            try:
                # --- FIRST ATTEMPT (normal generation) ---
                raw = await self._generate_once(
                    prompt=prompt,
                    instructions=instructions,
                    response_model=response_model,
                    model=model,
                    files=files,
                    timeout=timeout
                )

                try:
                    # Try to parse normally
                    return response_model.model_validate_json(raw)

                except ValidationError as ve:
                    # --- SECOND CHANCE: RE-ASK THE MODEL TO FIX ITS OUTPUT ---
                    fix_prompt = (
                        "Your previous response did not match the required JSON schema.\n\n"
                        f"Validation error:\n{ve}\n\n"
                        f"Invalid response:\n{raw}\n\n"
                        "Please correct the response so that it validates successfully."
                    )

                    corrected_raw = await self._generate_once(
                        prompt=fix_prompt,
                        instructions=instructions,
                        response_model=response_model,
                        model=model,
                        files=files,
                        timeout=timeout
                    )

                    # Parse corrected output
                    return response_model.model_validate_json(corrected_raw)

            except Exception as e:
                # network/SDK/parsing failures that aren't validation-related
                last_err = e
                if attempt == attempts:
                    break

                logger.debug(f"[Gemini retry] Attempt {attempt}/{attempts} failed: {e}")
                await asyncio.sleep(delay)
                delay *= backoff

        raise RuntimeError(
            f"Gemini generate_with_retry failed after {attempts} attempts"
        ) from last_err

    async def generate_and_validate_with(
            self,
            prompt: str,
            instructions: str,
            response_model: Type[T],
            validation_func,
            model: GeminiSupportedModels = DefaultGeminiModel,
            files: List[File] | None = None,
            timeout: int = 60
    ) -> T:

        original_user_prompt = prompt

        async def run_generation(p: str) -> T:
            return await self.generate(
                prompt=p,
                instructions=instructions,
                response_model=response_model,
                model=model,
                files=files,
                timeout=timeout
            )

        # --- First attempt ---
        resp: T = await run_generation(original_user_prompt)

        try:
            validation_func(resp)
            return resp
        except Exception:
            first_error = traceback.format_exc()

        # --- Retry attempt ---
        retry_prompt = format_instructions(
            f"""
            You previously generated an invalid response.
            Correct it.
        
            User Prompt:
            {original_user_prompt}
        
            Error raised by validator:
            {first_error}
        
            Your previous output:
            {resp}
            """
        )

        resp_retry: T = await run_generation(retry_prompt)

        try:
            validation_func(resp_retry)
            return resp_retry
        except Exception as e:
            second_error = traceback.format_exc()
            raise RuntimeError(
                f"Model failed validation twice.\n"
                f"First error:\n{first_error}\n\n"
                f"Second error:\n{second_error}\n\n"
                f"Last model output:\n{resp_retry}"
            ) from e

    async def generate(
            self,
            prompt: str,
            instructions: str,
            response_model: Type[T],
            model: GeminiSupportedModels = DefaultGeminiModel,
            files: List[File] | None = None,
            timeout: int = 60
    ) -> T:
        logger.debug(f"Generating for model: {response_model}")
        parsed_response = await self._generate_with_retry(
            prompt=prompt,
            instructions=instructions,
            response_model=response_model,
            model=model,
            files=files,
            timeout=timeout
        )
        logger.debug(f"Finished generating for model: {response_model}")
        return parsed_response
