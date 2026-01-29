import logging
import os
import random
import sys
from http import HTTPStatus
from typing import Any, Dict, List, Optional
import time
from contextlib import asynccontextmanager, AsyncExitStack
import traceback
import json

import aiobotocore.session
from aiobotocore.config import AioConfig
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
import newrelic.agent


from .cache import make_features_cache
from .dynamo import set_all_features, FeatureRetrievalMeta
from .model_store import download_and_load_model
from .settings import Settings
from . import exceptions
from ._serializers import SerializerRegistry
from google.protobuf import text_format

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(process)d] %(name)s : %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

logger = logging.getLogger(__name__)
MAX_POOL_CONNECTIONS = int(os.environ.get("MAX_POOL_CONNECTIONS", 50))


class StreamLoggerProxy:
    def __init__(self, stream, feature_ids):
        self._stream = stream
        self._feature_ids = feature_ids

    def __repr__(self):
        parts = []
        for k, v in self._stream.items():
            if k in self._feature_ids:
                # Format only when needed for the log output
                formatted_v = text_format.MessageToString(v, as_one_line=True)
                parts.append(f"'{k}': '{formatted_v}'")
            else:
                parts.append(f"'{k}': {repr(v)}")
        return "{" + ", ".join(parts) + "}"


async def load_model(state, cfg: Settings) -> None:
    if not cfg.s3_model_path:
        logger.critical("S3_MODEL_PATH not set; service will be unhealthy.")
    else:
        try:
            # Pass the persistent session/client if needed
            state["model"] = await download_and_load_model(
                cfg.s3_model_path, aio_session=state["session"]
            )
            state["stream_features"] = state["model"].get("stream_features", [])
            state["user_features"] = state["model"].get("user_features", [])
            valid_features = set(
                (entity_type, feature_id)
                for entity_type, feature_id, _ in SerializerRegistry.keys()
            )
            all_features = set(
                [("STREAM", feature_name) for feature_name in state["stream_features"]]
                + [("USER", feature_name) for feature_name in state["user_features"]]
            )
            invalid_features = all_features.difference(valid_features)
            if invalid_features:
                raise exceptions.InvalidFeaturesException(
                    f"Received invalid features: {invalid_features}"
                )
            newrelic.agent.add_custom_attribute(
                "total_stream_features", len(state["stream_features"])
            )
            newrelic.agent.add_custom_attribute(
                "total_user_features", len(state["user_features"])
            )
            logger.info("Model loaded successfully.")
        except exceptions.InvalidFeaturesException as e:
            logger.error("%s", e)
            raise e
        except Exception as e:
            logger.critical("Failed to load model: %s", e)


def create_app(
    settings: Optional[Settings] = None,
    *,
    preloaded_model: Optional[Dict[str, Any]] = None,
) -> FastAPI:
    """
    Build a FastAPI app with injectable settings and model.
    If `preloaded_model` is None, the app will load from S3 on startup.
    """
    cfg = settings or Settings()

    # Mutable state: cache + model
    stream_features_cache = make_features_cache(cfg.stream_cache_maxsize)
    user_features_cache = make_features_cache(cfg.user_cache_maxsize)
    aws_session = aiobotocore.session.get_session()
    state: Dict[str, Any] = {
        "model": preloaded_model,
        "session": aws_session,
        "model_name": (
            os.path.basename(cfg.s3_model_path) if cfg.s3_model_path else None
        ),
    }

    @asynccontextmanager
    async def lifespan(app_server: FastAPI):
        """
        Handles startup and shutdown logic.
        Everything before 'yield' runs on startup.
        Everything after 'yield' runs on shutdown.
        """
        # 1. Load ML Model
        if state["model"] is None:
            await load_model(state, cfg)
        async with AsyncExitStack() as stack:
            # 2. Initialize DynamoDB Client (Persistent Pool)
            session = state["session"]
            state["dynamo_client"] = await stack.enter_async_context(
                session.create_client(
                    "dynamodb",
                    # Ensure the pool is large enough for ML concurrency
                    config=AioConfig(max_pool_connections=MAX_POOL_CONNECTIONS),
                )
            )
            logger.info("DynamoDB persistent client initialized.")
            yield

            # 3. Shutdown Logic
            # The AsyncExitStack automatically closes the DynamoDB client pool here
            logger.info("Shutting down: Connection pools closed.")

    app = FastAPI(
        title="ML Stream Scorer",
        description="Scores video streams using a pre-trained ML model and DynamoDB features.",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/health", status_code=HTTPStatus.OK)
    async def health():
        model_ok = state["model"] is not None
        if not model_ok:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="ML Model not loaded",
            )
        return {
            "status": "ok",
            "model_loaded": True,
            "stream_cache_size": len(stream_features_cache),
            "user_cache_size": len(user_features_cache),
            "model_name": state.get("model_name"),
            "stream_features": state.get("stream_features", []),
            "user_features": state.get("user_features", []),
        }

    @app.post("/score", status_code=HTTPStatus.OK)
    async def score_stream(request: Request, response: Response):
        if state["model"] is None:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="ML Model not loaded",
            )

        try:
            data = await request.json()
        except json.JSONDecodeError as e:
            body = await request.body()
            logger.error(
                "Received malformed json. Raw body: %s\n%s",
                body.decode(errors="replace"),
                traceback.format_exc(),
            )
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid JSON payload"
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected exception when parsing request.\n %s", traceback.format_exc()
            )
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Unknown exception"
            ) from e
        query_params = {}
        for k in request.query_params.keys():
            values = request.query_params.getlist(k)
            # flatten single-element lists
            query_params[k] = values[0] if len(values) == 1 else values
        user = data.get("user", {})
        streams: List[Dict[str, Any]] = data.get("streams", [])
        playlist = data.get("playlist", {})

        if not streams:
            logger.warning("No streams provided for user %s", user.get("userid", ""))
            return {}

        # Feature fetch (optional based on model)
        model = state["model"]
        stream_features = model.get("stream_features", []) or []
        user_features = model.get("user_features", []) or []
        retrieval_meta = FeatureRetrievalMeta(
            cache_misses=0,
            stream_cache_misses=0,
            user_cache_misses=0,
            retrieval_ms=0,
            success=True,
            cache_delay_minutes=0,
            dynamo_ms=0,
            parsing_ms=0,
        )
        if stream_features:
            try:
                retrieval_meta = await set_all_features(
                    dynamo_client=state["dynamo_client"],
                    user=user,
                    streams=streams,
                    stream_features=stream_features,
                    user_features=user_features,
                    stream_features_cache=stream_features_cache,
                    user_features_cache=user_features_cache,
                    features_table=cfg.features_table,
                    cache_sep=cfg.cache_separator,
                )
            except exceptions.InvalidFeaturesException as e:
                logger.error(
                    "The following features are not present in the SerializerRegistry %s",
                    e,
                )
                raise HTTPException(
                    status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                    detail=f"Received invalid features from feature store: {e}",
                ) from e

        random_number = random.random()
        userid = user.get("userid", "")
        # Sampling logs
        if random_number < cfg.logs_fraction:
            logger.info(
                "User %s streams: %s",
                user.get("userid", ""),
                [
                    StreamLoggerProxy(s, stream_features + user_features)
                    for s in streams
                ],
            )

        # Synchronous model execution (user code)
        try:
            preprocess_start = time.perf_counter_ns()
            model["params"]["query_params"] = query_params
            model_input = model["preprocess"](
                user,
                streams,
                playlist,
                model["params"],
            )
            predict_start = time.perf_counter_ns()
            model_output = model["predict"](model_input, model["params"])
            predict_end = time.perf_counter_ns()
        except Exception as e:
            logger.error("Model prediction failed: \n%s", traceback.format_exc())
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Model prediction failed",
            ) from e

        newrelic.agent.record_custom_event(
            "Inference",
            {
                "cache_misses": retrieval_meta.cache_misses,
                "user_cache_misses": retrieval_meta.user_cache_misses,
                "stream_cache_misses": retrieval_meta.stream_cache_misses,
                "retrieval_success": int(retrieval_meta.success),
                "cache_delay_minutes": retrieval_meta.cache_delay_minutes,
                "dynamo_ms": retrieval_meta.dynamo_ms,
                "dynamo_parse_ms": retrieval_meta.parsing_ms,
                "retrieval_ms": retrieval_meta.retrieval_ms,
                "preprocess_ms": (predict_start - preprocess_start) * 1e-6,
                "predict_ms": (predict_end - predict_start) * 1e-6,
                "total_streams": len(model_output),
            },
        )
        if model_output:
            if random_number < cfg.logs_fraction:
                logger.info(
                    "User %s - model output %s",
                    userid,
                    model_output,
                )
            return jsonable_encoder(model_output)

        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="No model output generated"
        )

    @app.get("/", status_code=HTTPStatus.OK)
    async def root():
        return {
            "message": "ML Scoring Service is running.",
            "model_name": state.get("model_name"),
        }

    return app
