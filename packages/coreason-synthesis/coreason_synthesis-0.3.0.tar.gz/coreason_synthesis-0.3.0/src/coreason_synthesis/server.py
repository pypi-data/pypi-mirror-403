# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_synthesis

"""
Synthesis API Server.

This module exposes the coreason-synthesis pipeline as a FastAPI microservice.
"""

import contextlib
import os
from typing import Any, AsyncIterator, Dict, List

import httpx
from coreason_identity.models import UserContext
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

from coreason_synthesis.analyzer import PatternAnalyzerImpl
from coreason_synthesis.appraiser import AppraiserImpl
from coreason_synthesis.clients.mcp import HttpMCPClient
from coreason_synthesis.clients.openai import OpenAIEmbeddingService, OpenAITeacherModel
from coreason_synthesis.compositor import CompositorImpl
from coreason_synthesis.extractor import ExtractorImpl
from coreason_synthesis.forager import ForagerImpl
from coreason_synthesis.interfaces import (
    EmbeddingService,
    MCPClient,
    TeacherModel,
)
from coreason_synthesis.mocks.embedding import DummyEmbeddingService
from coreason_synthesis.mocks.mcp import MockMCPClient
from coreason_synthesis.mocks.teacher import MockTeacher
from coreason_synthesis.models import SeedCase, SyntheticTestCase
from coreason_synthesis.perturbator import PerturbatorImpl
from coreason_synthesis.pipeline import SynthesisPipelineAsync


# Request model
class SynthesisRequest(BaseModel):
    """Request model for the synthesis run endpoint."""

    seeds: List[SeedCase]
    config: Dict[str, Any]
    user_context: UserContext


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for the FastAPI application.

    Initializes the SynthesisPipelineAsync and its components on startup,
    and handles resource cleanup on shutdown.
    """
    logger.info("Initializing Synthesis Service...")

    # Create separate clients to prevent header contamination (security/stability)
    openai_http_client = httpx.AsyncClient()
    mcp_http_client = httpx.AsyncClient()
    # Shared client for general pipeline use if needed, or re-use one that doesn't carry auth.
    # Since MCP client and OpenAI client might have distinct auth headers, we keep them separate.
    # The pipeline itself uses a client if provided.
    pipeline_http_client = httpx.AsyncClient()

    try:
        # 1. Initialize Clients (Adapters)

        # Teacher & Embedder (OpenAI or Mock)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        teacher: TeacherModel
        embedder: EmbeddingService

        if openai_api_key:
            logger.info("Using OpenAI implementations.")
            teacher = OpenAITeacherModel(api_key=openai_api_key, client=openai_http_client)
            embedder = OpenAIEmbeddingService(api_key=openai_api_key, client=openai_http_client)
        else:
            logger.warning("OPENAI_API_KEY not found. Using Mock implementations.")
            teacher = MockTeacher()
            embedder = DummyEmbeddingService()

        # MCP Client (Http or Mock)
        mcp_base_url = os.getenv("MCP_BASE_URL")
        mcp_client: MCPClient

        if mcp_base_url:
            logger.info(f"Using HttpMCPClient connected to {mcp_base_url}")
            mcp_client = HttpMCPClient(base_url=mcp_base_url, client=mcp_http_client)
        else:
            logger.warning("MCP_BASE_URL not found. Using MockMCPClient.")
            mcp_client = MockMCPClient()

        # 2. Initialize Components
        # Using the provided Implementations
        analyzer = PatternAnalyzerImpl(teacher=teacher, embedder=embedder)
        forager = ForagerImpl(mcp_client=mcp_client, embedder=embedder)
        extractor = ExtractorImpl()
        compositor = CompositorImpl(teacher=teacher)
        perturbator = PerturbatorImpl()
        appraiser = AppraiserImpl(teacher=teacher, embedder=embedder)

        # 3. Assemble Pipeline
        pipeline = SynthesisPipelineAsync(
            analyzer=analyzer,
            forager=forager,
            extractor=extractor,
            compositor=compositor,
            perturbator=perturbator,
            appraiser=appraiser,
            client=pipeline_http_client,
        )

        app.state.pipeline = pipeline

        yield

    finally:
        logger.info("Shutting down Synthesis Service...")
        # Close all clients
        await openai_http_client.aclose()
        await mcp_http_client.aclose()
        await pipeline_http_client.aclose()


app = FastAPI(title="CoReason Synthesis API", lifespan=lifespan)


@app.post("/synthesis/run", response_model=List[SyntheticTestCase])
async def run_synthesis(request: SynthesisRequest) -> List[SyntheticTestCase]:
    """Runs the synthesis pipeline.

    Accepts seeds, config, and user context. Returns generated synthetic test cases.
    """
    if not hasattr(app.state, "pipeline"):
        raise HTTPException(status_code=500, detail="Pipeline not initialized.")

    pipeline: SynthesisPipelineAsync = app.state.pipeline
    try:
        results = await pipeline.run(seeds=request.seeds, config=request.config, user_context=request.user_context)
        return results
    except Exception as e:
        logger.exception("Synthesis failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.

    Returns status and component readiness.
    """
    return {"status": "active", "components": "ready"}
