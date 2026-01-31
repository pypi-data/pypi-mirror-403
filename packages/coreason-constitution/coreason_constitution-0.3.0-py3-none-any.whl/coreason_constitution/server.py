from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

import coreason_constitution
from coreason_constitution.archive import LegislativeArchive
from coreason_constitution.core import ConstitutionalSystem
from coreason_constitution.exceptions import SecurityException
from coreason_constitution.judge import ConstitutionalJudge
from coreason_constitution.revision import RevisionEngine
from coreason_constitution.schema import ConstitutionalTrace, Law
from coreason_constitution.sentinel import Sentinel
from coreason_constitution.simulation import SimulatedLLMClient
from coreason_constitution.utils.logger import logger


class ComplianceRequest(BaseModel):
    input_prompt: str
    draft_response: str
    context_tags: Optional[List[str]] = None
    max_retries: int = Field(default=3)


class SentinelRequest(BaseModel):
    content: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize components
    logger.info("Initializing Constitutional System...")

    archive = LegislativeArchive()
    archive.load_defaults()

    sentinel = Sentinel(archive.get_sentinel_rules())

    # Use SimulatedLLMClient for now as per instructions
    llm_client = SimulatedLLMClient()

    judge = ConstitutionalJudge(llm_client)
    revision_engine = RevisionEngine(llm_client)

    system = ConstitutionalSystem(
        archive=archive,
        sentinel=sentinel,
        judge=judge,
        revision_engine=revision_engine,
    )

    app.state.system = system

    logger.info("Constitutional System initialized.")
    yield
    # Cleanup if needed (none for now)


app = FastAPI(
    lifespan=lifespan,
    title="CoReason Constitution",
    version=coreason_constitution.__version__,
)


@app.post("/govern/compliance-cycle", response_model=ConstitutionalTrace)  # type: ignore
async def run_compliance_cycle(request: Request, body: ComplianceRequest) -> ConstitutionalTrace:
    system: ConstitutionalSystem = request.app.state.system

    # run_compliance_cycle returns ConstitutionalTrace
    trace = system.run_compliance_cycle(
        input_prompt=body.input_prompt,
        draft_response=body.draft_response,
        context_tags=body.context_tags,
        max_retries=body.max_retries,
    )

    return trace


@app.post("/govern/sentinel")  # type: ignore
async def run_sentinel(request: Request, body: SentinelRequest) -> Dict[str, str]:
    system: ConstitutionalSystem = request.app.state.system
    try:
        system.sentinel.check(body.content)
        return {"status": "allowed"}
    except SecurityException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@app.get("/laws", response_model=List[Law])  # type: ignore
async def get_laws(request: Request) -> List[Law]:
    system: ConstitutionalSystem = request.app.state.system
    return system.archive.get_laws()


@app.get("/health")  # type: ignore
async def health_check() -> Dict[str, Any]:
    return {"status": "ready", "version": coreason_constitution.__version__}
