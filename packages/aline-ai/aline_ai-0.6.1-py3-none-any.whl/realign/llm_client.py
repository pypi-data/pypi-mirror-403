#!/usr/bin/env python3
"""
Unified LLM Client for ReAlign.

This module provides a centralized interface for calling LLM providers (Claude, OpenAI)
with configurable models and parameters.
"""

import os
import sys
import time
import json
import logging
import tempfile
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, Callable, List
from pathlib import Path

# Setup dedicated LLM logger
logger = logging.getLogger(__name__)

# Setup detailed LLM call logger (logs to ~/.aline/.logs/llm.log)
_llm_call_logger = None


def _setup_llm_call_logger():
    """Setup dedicated logger for LLM calls with detailed logging."""
    global _llm_call_logger
    if _llm_call_logger is not None:
        return _llm_call_logger

    # Create logger
    _llm_call_logger = logging.getLogger("realign.llm_calls")
    _llm_call_logger.setLevel(logging.DEBUG)

    # Prevent propagation to avoid duplicate logs
    _llm_call_logger.propagate = False

    file_handler: logging.Handler | None = None
    log_dir_candidates = [
        Path.home() / ".aline" / ".logs",
        Path(tempfile.gettempdir()) / "aline" / ".logs",
    ]
    for log_dir in log_dir_candidates:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "llm.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            break
        except OSError:
            file_handler = None

    if file_handler is None:
        _llm_call_logger.addHandler(logging.NullHandler())
        return _llm_call_logger

    # Create formatter with detailed information
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    # Add handler
    _llm_call_logger.addHandler(file_handler)

    return _llm_call_logger


def call_llm(
    system_prompt: str,
    user_prompt: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    json_mode: bool = False,
    debug_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    purpose: str = "generic",
    silent: bool = False,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Unified LLM calling function.

    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        provider: LLM provider ("auto", "claude", "openai"), None = read from config
        model: Model name, None = use default from config
        max_tokens: Maximum tokens to generate, None = use default
        temperature: Temperature parameter, None = use default
        json_mode: Enable JSON mode (OpenAI only)
        debug_callback: Debug callback function
        purpose: Purpose string for logging
        silent: If True, suppress progress messages to stderr

    Returns:
        (model_name, response_text) or (None, None) on failure

    Raises:
        No exceptions raised - returns (None, None) on failure
    """
    # Load configuration
    from .config import ReAlignConfig

    config = ReAlignConfig.load()

    # Resolve provider from config if not specified
    if provider is None:
        provider = config.llm_provider

    # Resolve default parameters from config if not specified
    if max_tokens is None:
        max_tokens = config.llm_max_tokens
    if temperature is None:
        temperature = config.llm_temperature

    def _should_use_openai_responses(model_name: str) -> bool:
        """
        Decide if the OpenAI responses/reasoning API should be used for this model.
        """
        # Check explicit override
        if config.llm_openai_use_responses:
            return True

        # Also check environment variable for backwards compatibility
        override = os.getenv("REALIGN_OPENAI_USE_RESPONSES", "").strip().lower()
        if override in ("1", "true", "yes"):
            return True
        if override in ("0", "false", "no"):
            return False
        if not model_name:
            return False
        # Auto-detect: use responses API for GPT-5+ models
        lowered = model_name.lower()
        return lowered.startswith("gpt-5")

    def _collect_responses_output_text(response: Any) -> str:
        """
        Aggregate textual content from OpenAI responses API objects.
        """
        parts: List[str] = []
        output_items = getattr(response, "output", None) or []
        for item in output_items:
            content = getattr(item, "content", None) or []
            for block in content:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
        text = "".join(parts).strip()
        if text:
            return text
        fallback = getattr(response, "output_text", "") or ""
        return fallback.strip()

    def _emit_debug(payload: Dict[str, Any]) -> None:
        """Emit debug event if callback is provided."""
        if not debug_callback:
            return
        try:
            debug_callback(payload)
        except Exception:
            logger.debug("LLM debug callback failed for payload=%s", payload, exc_info=True)

    # Setup detailed logging
    call_logger = _setup_llm_call_logger()
    call_start_time = time.time()
    call_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log call initiation with all parameters
    call_logger.info("=" * 80)
    call_logger.info(f"LLM CALL INITIATED")
    call_logger.info(f"Timestamp: {call_timestamp}")
    call_logger.info(f"Purpose: {purpose}")
    call_logger.info(f"Provider: {provider}")
    call_logger.info(f"Model: {model or 'default from config'}")
    call_logger.info(f"Max Tokens: {max_tokens}")
    call_logger.info(f"Temperature: {temperature}")
    call_logger.info(f"JSON Mode: {json_mode}")
    call_logger.info("-" * 80)
    call_logger.info(f"SYSTEM PROMPT:\n{system_prompt}")
    call_logger.info("-" * 80)
    call_logger.info(f"USER PROMPT:\n{user_prompt}")
    call_logger.info("-" * 80)

    try_claude = provider in ("auto", "claude")
    try_openai = provider in ("auto", "openai")

    _emit_debug(
        {
            "event": "llm_prompt",
            "target_provider": provider,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "provider_options": {
                "try_claude": try_claude,
                "try_openai": try_openai,
            },
            "purpose": purpose,
        }
    )

    # Try Claude
    anthropic_key = config.anthropic_api_key
    if try_claude and anthropic_key:
        logger.debug("ANTHROPIC_API_KEY found, attempting Claude")
        if not silent:
            print("   → Trying Anthropic (Claude)...", file=sys.stderr)
        try:
            import anthropic

            start_time = time.time()
            client = anthropic.Anthropic(api_key=anthropic_key)

            # Use model parameter if specified, otherwise read from config/env
            claude_model = model or config.llm_anthropic_model

            response = client.messages.create(
                model=claude_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            elapsed = time.time() - start_time
            response_text = response.content[0].text.strip()
            logger.info(f"Claude API success: {len(response_text)} chars in {elapsed:.2f}s")
            logger.debug(f"Claude response: {response_text[:200]}...")
            _emit_debug(
                {
                    "event": "llm_response",
                    "provider": "anthropic",
                    "model": claude_model,
                    "elapsed_seconds": elapsed,
                    "raw_response": response_text,
                    "purpose": purpose,
                }
            )

            # Log successful response
            total_elapsed = time.time() - call_start_time
            call_logger.info(f"LLM CALL SUCCEEDED")
            call_logger.info(f"Provider: Anthropic (Claude)")
            call_logger.info(f"Model: {claude_model}")
            call_logger.info(f"Elapsed Time: {elapsed:.2f}s")
            call_logger.info(f"Total Time: {total_elapsed:.2f}s")
            call_logger.info(f"Response Length: {len(response_text)} chars")
            call_logger.info("-" * 80)
            call_logger.info(f"RESPONSE:\n{response_text}")
            call_logger.info("=" * 80 + "\n")

            return claude_model, response_text

        except ImportError:
            logger.warning("Anthropic package not installed")
            if provider == "claude":
                if not silent:
                    print("   ❌ Anthropic package not installed", file=sys.stderr)
                total_elapsed = time.time() - call_start_time
                call_logger.error(f"LLM CALL FAILED")
                call_logger.error(f"Provider: Anthropic (Claude)")
                call_logger.error(f"Reason: Anthropic package not installed")
                call_logger.error(f"Total Time: {total_elapsed:.2f}s")
                call_logger.error("=" * 80 + "\n")
                return None, None
            if not silent:
                print(
                    "   ❌ Anthropic package not installed, trying OpenAI...",
                    file=sys.stderr,
                )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Claude API error: {error_msg}", exc_info=True)
            if provider == "claude":
                if not silent:
                    if "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
                        print(
                            f"   ❌ Anthropic authentication failed (check API key)",
                            file=sys.stderr,
                        )
                    elif "quota" in error_msg.lower() or "credit" in error_msg.lower():
                        print(f"   ❌ Anthropic quota/credit issue", file=sys.stderr)
                    else:
                        print(f"   ❌ Anthropic API error: {e}", file=sys.stderr)
                total_elapsed = time.time() - call_start_time
                call_logger.error(f"LLM CALL FAILED")
                call_logger.error(f"Provider: Anthropic (Claude)")
                call_logger.error(f"Reason: {error_msg}")
                call_logger.error(f"Total Time: {total_elapsed:.2f}s")
                call_logger.error("=" * 80 + "\n")
                return None, None
            if not silent:
                print(f"   ❌ Anthropic API error: {e}, trying OpenAI...", file=sys.stderr)

    elif try_claude:
        logger.debug("Anthropic API key not configured in config file")
        if provider == "claude":
            if not silent:
                print(
                    "   ❌ Anthropic API key not configured in config file",
                    file=sys.stderr,
                )
            return None, None
        if not silent:
            print("Anthropic API key not configured, trying OpenAI...", file=sys.stderr)

    # Try OpenAI
    openai_key = config.openai_api_key
    if try_openai and openai_key:
        logger.debug("OPENAI_API_KEY found, attempting OpenAI")
        if not silent:
            print("Trying OpenAI (GPT)...", file=sys.stderr)
        try:
            import openai

            start_time = time.time()
            client = openai.OpenAI(api_key=openai_key)

            # Use model parameter if specified, otherwise read from config/env
            openai_model = model or config.llm_openai_model
            use_responses_api = _should_use_openai_responses(openai_model)

            def _call_openai_chat_completion() -> Tuple[Any, str]:
                use_completion_tokens = False
                temperature_value = temperature
                bad_request_error = getattr(openai, "BadRequestError", Exception)
                last_error: Optional[Exception] = None
                for _ in range(3):
                    completion_kwargs = {
                        "model": openai_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": temperature_value,
                    }

                    # Add JSON mode if requested
                    if json_mode:
                        completion_kwargs["response_format"] = {"type": "json_object"}

                    token_key = "max_completion_tokens" if use_completion_tokens else "max_tokens"
                    completion_kwargs[token_key] = max_tokens

                    try:
                        completion = client.chat.completions.create(**completion_kwargs)
                        text = (completion.choices[0].message.content or "").strip()
                        return completion, text
                    except bad_request_error as bad_request:
                        error_msg = str(bad_request)
                        last_error = bad_request
                        needs_completion_tokens = (
                            "max_tokens" in error_msg and "max_completion_tokens" in error_msg
                        )
                        needs_default_temp = (
                            "temperature" in error_msg
                            and "default (1)" in error_msg
                            and abs(temperature_value - 1) > 1e-6
                        )
                        if needs_completion_tokens and not use_completion_tokens:
                            use_completion_tokens = True
                            logger.info(
                                "OpenAI model %s requires max_completion_tokens; retrying request",
                                openai_model,
                            )
                            print(
                                "   ⓘ Retrying OpenAI call with max_completion_tokens...",
                                file=sys.stderr,
                            )
                            continue
                        if needs_default_temp:
                            temperature_value = 1.0
                            logger.info(
                                "OpenAI model %s requires default temperature; retrying request",
                                openai_model,
                            )
                            print(
                                "   ⓘ Retrying OpenAI call with temperature=1...",
                                file=sys.stderr,
                            )
                            continue
                        raise
                raise last_error or RuntimeError(
                    "Failed to obtain OpenAI response after multiple attempts"
                )

            def _call_openai_responses_api() -> Tuple[Any, str]:
                def _int_env(name: str, default: int) -> int:
                    value = os.getenv(name)
                    if not value:
                        return default
                    try:
                        return max(1, int(value))
                    except ValueError:
                        return default

                def _float_env(name: str, default: float) -> float:
                    value = os.getenv(name)
                    if not value:
                        return default
                    try:
                        return float(value)
                    except ValueError:
                        return default

                max_output_tokens = _int_env("REALIGN_OPENAI_MAX_OUTPUT_TOKENS", max_tokens)
                reasoning_effort = os.getenv("REALIGN_OPENAI_REASONING_EFFORT", "medium").strip()
                responses_temperature = _float_env(
                    "REALIGN_OPENAI_RESPONSES_TEMPERATURE", temperature
                )

                inputs: List[Dict[str, str]] = []
                if system_prompt:
                    inputs.append({"role": "developer", "content": system_prompt})
                inputs.append({"role": "user", "content": user_prompt})

                request_kwargs: Dict[str, Any] = {
                    "model": openai_model,
                    "input": inputs,
                    "max_output_tokens": max_output_tokens,
                    "temperature": responses_temperature,
                }
                if reasoning_effort:
                    request_kwargs["reasoning"] = {"effort": reasoning_effort}

                response = client.responses.create(**request_kwargs)
                text = _collect_responses_output_text(response)
                return response, text

            endpoint_type = "responses" if use_responses_api else "chat.completions"
            if use_responses_api:
                response, response_text = _call_openai_responses_api()
            else:
                response, response_text = _call_openai_chat_completion()

            elapsed = time.time() - start_time
            response_text = (response_text or "").strip()
            response_model = getattr(response, "model", openai_model)
            logger.info(
                f"OpenAI {endpoint_type} success: {len(response_text)} chars in {elapsed:.2f}s"
            )
            logger.debug(f"OpenAI response: {response_text[:200]}...")
            _emit_debug(
                {
                    "event": "llm_response",
                    "provider": "openai",
                    "model": response_model,
                    "elapsed_seconds": elapsed,
                    "raw_response": response_text,
                    "purpose": purpose,
                    "endpoint": endpoint_type,
                    "response_status": getattr(response, "status", None),
                }
            )

            # Log successful response
            total_elapsed = time.time() - call_start_time
            call_logger.info(f"LLM CALL SUCCEEDED")
            call_logger.info(f"Provider: OpenAI (GPT)")
            call_logger.info(f"Model: {response_model}")
            call_logger.info(f"Endpoint: {endpoint_type}")
            call_logger.info(f"Elapsed Time: {elapsed:.2f}s")
            call_logger.info(f"Total Time: {total_elapsed:.2f}s")
            call_logger.info(f"Response Length: {len(response_text)} chars")
            call_logger.info("-" * 80)
            call_logger.info(f"RESPONSE:\n{response_text}")
            call_logger.info("=" * 80 + "\n")

            return response_model, response_text

        except ImportError:
            logger.warning("OpenAI package not installed")
            if not silent:
                print("   ❌ OpenAI package not installed", file=sys.stderr)
            total_elapsed = time.time() - call_start_time
            call_logger.error(f"LLM CALL FAILED")
            call_logger.error(f"Provider: OpenAI (GPT)")
            call_logger.error(f"Reason: OpenAI package not installed")
            call_logger.error(f"Total Time: {total_elapsed:.2f}s")
            call_logger.error("=" * 80 + "\n")
            return None, None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"OpenAI API error: {error_msg}", exc_info=True)
            if not silent:
                if "authentication" in error_msg.lower():
                    print(
                        "   ❌ OpenAI authentication failed (check API key)",
                        file=sys.stderr,
                    )
                elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                    print("   ❌ OpenAI quota/billing issue", file=sys.stderr)
                else:
                    print(f"   ❌ OpenAI API error: {e}", file=sys.stderr)
            total_elapsed = time.time() - call_start_time
            call_logger.error(f"LLM CALL FAILED")
            call_logger.error(f"Provider: OpenAI (GPT)")
            call_logger.error(f"Reason: {error_msg}")
            call_logger.error(f"Total Time: {total_elapsed:.2f}s")
            call_logger.error("=" * 80 + "\n")
            return None, None

    elif try_openai:
        logger.debug("OpenAI API key not configured in config file")
        if not silent:
            print("   ❌ OpenAI API key not configured in config file", file=sys.stderr)
        return None, None

    logger.warning(f"No LLM API keys available (provider: {provider})")
    if provider == "auto" and not silent:
        print("   ❌ No LLM API keys configured", file=sys.stderr)

    # Log failure
    total_elapsed = time.time() - call_start_time
    call_logger.error(f"LLM CALL FAILED")
    call_logger.error(f"Reason: No LLM API keys available")
    call_logger.error(f"Provider: {provider}")
    call_logger.error(f"Total Time: {total_elapsed:.2f}s")
    call_logger.error("=" * 80 + "\n")

    return None, None


def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    debug_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    purpose: str = "generic",
    silent: bool = False,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Call LLM and parse JSON response.

    Args:
        Same as call_llm()

    Returns:
        (model_name, json_dict) where json_dict is None on failure
    """
    model_name, response_text = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        provider=provider,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        json_mode=True,  # Always enable JSON mode for this function
        debug_callback=debug_callback,
        purpose=purpose,
        silent=silent,
    )

    if not response_text:
        if not silent:
            print(
                f"   ⚠️  LLM returned empty response (purpose={purpose})",
                file=sys.stderr,
            )
        return model_name, None

    try:
        parsed = extract_json(response_text)
    except Exception as e:
        logger.warning("Failed to parse LLM JSON (purpose=%s): %s", purpose, e, exc_info=True)
        if not silent:
            print(f"   ⚠️  Failed to parse JSON (purpose={purpose}): {e}", file=sys.stderr)
            print(
                f"   ⚠️  Response text (first 500 chars): {response_text[:500]}",
                file=sys.stderr,
            )
            print(
                f"   ⚠️  Response text (last 500 chars): ...{response_text[-500:]}",
                file=sys.stderr,
            )
        return model_name, None

    if not isinstance(parsed, dict):
        logger.warning("LLM JSON was not an object (purpose=%s): %r", purpose, type(parsed))
        if not silent:
            print(
                f"   ⚠️  LLM returned {type(parsed)} instead of dict (purpose={purpose})",
                file=sys.stderr,
            )
        return model_name, None

    return model_name, parsed


def extract_json(response_text: str) -> Dict[str, Any]:
    """
    Extract JSON object from a raw LLM response, handling Markdown fences.
    Uses strict=False to tolerate control characters in JSON strings.

    Args:
        response_text: Raw LLM response

    Returns:
        Parsed JSON dict

    Raises:
        json.JSONDecodeError: If JSON parsing fails
    """
    if not response_text:
        raise json.JSONDecodeError("Empty response", "", 0)

    json_str = response_text.strip()

    # Remove markdown code fences if present
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        if json_end != -1:
            json_str = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        if json_end != -1:
            json_str = response_text[json_start:json_end].strip()

    if not json_str:
        raise json.JSONDecodeError("No JSON content found", response_text, 0)

    # Use strict=False to allow control characters in JSON strings
    return json.loads(json_str, strict=False)
