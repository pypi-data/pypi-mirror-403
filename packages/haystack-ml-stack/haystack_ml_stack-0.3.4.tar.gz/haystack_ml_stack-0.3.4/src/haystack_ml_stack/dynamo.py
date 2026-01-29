from typing import Any, Dict, List, NamedTuple, Literal
import logging
import time
import datetime
from boto3.dynamodb.types import TypeDeserializer
import newrelic.agent
import asyncio
from ._serializers import SerializerRegistry, FeatureRegistryId
from . import exceptions


logger = logging.getLogger(__name__)


class FloatDeserializer(TypeDeserializer):
    def _deserialize_n(self, value):
        return float(value)

    def _deserialize_b(self, value):
        return bytes(super()._deserialize_b(value))


_deser = FloatDeserializer()
IdType = Literal["STREAM", "USER"]


class FeatureRetrievalMeta(NamedTuple):
    cache_misses: int
    user_cache_misses: int
    stream_cache_misses: int
    retrieval_ms: float
    success: bool
    cache_delay_minutes: float
    dynamo_ms: float
    parsing_ms: float


async def async_batch_get(
    dynamo_client, table_name: str, keys: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Asynchronous batch_get_item with chunking for requests > 100 keys
    and handling for unprocessed keys.
    """
    # DynamoDB's BatchGetItem has a 100-item limit per request.
    CHUNK_SIZE = 100

    if len(keys) <= CHUNK_SIZE:
        all_items = await _fetch_chunk(dynamo_client, table_name, keys)
    else:
        chunks = [keys[i : i + CHUNK_SIZE] for i in range(0, len(keys), CHUNK_SIZE)]
        tasks = [_fetch_chunk(dynamo_client, table_name, chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)
        all_items = [item for batch in results for item in batch]
    return all_items


async def _fetch_chunk(dynamo_client, table_name: str, chunk_keys):
    """Fetch a single chunk of up to 100 keys with retry handling."""
    to_fetch = {table_name: {"Keys": chunk_keys}}
    retries = 3
    items = []

    while to_fetch and retries > 0:
        retries -= 1
        try:
            resp = await dynamo_client.batch_get_item(RequestItems=to_fetch)

            # Collect retrieved items
            if "Responses" in resp and table_name in resp["Responses"]:
                items.extend(resp["Responses"][table_name])

            # Check for unprocessed keys
            unprocessed = resp.get("UnprocessedKeys", {})
            if unprocessed and unprocessed.get(table_name):
                unp = unprocessed[table_name]["Keys"]
                logger.warning("Retrying %d unprocessed keys.", len(unp))
                to_fetch = {table_name: {"Keys": unp}}
            else:
                to_fetch = {}

        except Exception as e:
            logger.error("Error in batch_get_item chunk: %s", e)
            break

    return items


def parse_dynamo_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a DynamoDB attribute map (low-level) to Python types."""
    # out: Dict[str, Any] = {}
    return {k: _deser.deserialize(v) for k, v in item.items()}


@newrelic.agent.function_trace()
async def set_all_features(
    *,
    user: Dict[str, Any],
    streams: List[Dict[str, Any]],
    stream_features: List[str],
    user_features: List[str],
    stream_features_cache,
    user_features_cache,
    features_table: str,
    cache_sep: str,
    dynamo_client,
) -> FeatureRetrievalMeta:
    time_start = time.perf_counter_ns()
    if not streams or (not stream_features and not user_features):
        return FeatureRetrievalMeta(
            cache_misses=0,
            user_cache_misses=0,
            stream_cache_misses=0,
            retrieval_ms=(time.perf_counter_ns() - time_start) * 1e-6,
            success=True,
            cache_delay_minutes=0,
            dynamo_ms=0,
            parsing_ms=0,
        )
    cache_miss: Dict[str, Dict[str, Any]] = {}
    all_feature_keys = [*stream_features, *user_features]
    cache_delay_obj: dict[str, float] = {f: 0 for f in all_feature_keys}
    now = datetime.datetime.utcnow()
    for f in stream_features:
        for s in streams:
            cache_miss, cache_delay_obj = _check_cache(
                obj=s,
                id_type="STREAM",
                id_key=s["streamUrl"],
                feature_key=f,
                cache_sep=cache_sep,
                features_cache=stream_features_cache,
                cache_miss=cache_miss,
                cache_delay=cache_delay_obj,
                now=now,
            )
    stream_cache_misses = len(cache_miss)
    for f in user_features:
        cache_miss, cache_delay_obj = _check_cache(
            obj=user,
            id_type="USER",
            id_key=user["userid"],
            feature_key=f,
            cache_sep=cache_sep,
            features_cache=user_features_cache,
            cache_miss=cache_miss,
            cache_delay=cache_delay_obj,
            now=now,
        )
    user_cache_misses = len(cache_miss) - stream_cache_misses
    valid_cache_delays = list(v for v in cache_delay_obj.values() if v > 0)
    cache_delay = min(valid_cache_delays) if valid_cache_delays else 0

    if not cache_miss:
        return FeatureRetrievalMeta(
            user_cache_misses=0,
            stream_cache_misses=0,
            cache_misses=0,
            retrieval_ms=(time.perf_counter_ns() - time_start) * 1e-6,
            success=True,
            cache_delay_minutes=cache_delay / 60,
            dynamo_ms=0,
            parsing_ms=0,
        )
    cache_misses = len(cache_miss)

    logger.info(
        "Cache miss for %d items (%d stream items, %d user items)",
        cache_misses,
        stream_cache_misses,
        user_cache_misses,
    )
    keys = []
    for k in cache_miss.keys():
        id_type, id_key, sk = k.split(cache_sep, 2)
        pk = f"{id_type}#{id_key}"
        keys.append({"pk": {"S": pk}, "sk": {"S": sk}})

    dynamodb = dynamo_client
    dynamo_start = time.perf_counter_ns()
    try:
        items = await async_batch_get(dynamodb, features_table, keys)
    except Exception as e:
        logger.error("DynamoDB batch_get failed: %s", e)
        end_time = time.perf_counter_ns()
        return FeatureRetrievalMeta(
            user_cache_misses=user_cache_misses,
            stream_cache_misses=stream_cache_misses,
            cache_misses=0,
            retrieval_ms=(end_time - time_start) * 1e-6,
            success=False,
            cache_delay_minutes=cache_delay / 60,
            dynamo_ms=(end_time - dynamo_start) * 1e-6,
            parsing_ms=0,
        )
    dynamo_end = time.perf_counter_ns()
    updated_keys = set()
    for item in items:
        full_id = item["pk"]["S"]
        id_type, id_key = full_id.split("#")
        feature_name = item["sk"]["S"]
        if id_type == "STREAM":
            cache_to_use = stream_features_cache
        elif id_type == "USER":
            cache_to_use = user_features_cache
        else:
            raise ValueError(
                f"Unexpected id type. Expected either of 'STREAM' or 'USER', received {id_type}"
            )
        cache_key = _build_cache_key(
            id_type=id_type,
            id_key=id_key,
            feature_key=feature_name,
            cache_sep=cache_sep,
        )
        parsed = parse_dynamo_item(item)
        feature_version = parsed.get("version", "v0")
        feature_id = FeatureRegistryId(
            entity_type=id_type, feature_id=feature_name, version=feature_version
        )
        try:
            serializer = SerializerRegistry[feature_id]
        except KeyError as e:
            raise exceptions.InvalidFeaturesException(
                f"Could not find '{feature_id}' in serializer registry"
            ) from e
        try:
            value = (
                serializer.deserialize(parsed.get("value"))
                if parsed.get("value")
                else None
            )
        except TypeError as e:
            raise exceptions.DeserializationException(
                f"Ran into an error while deserializing {feature_id}. Error: {e}"
            ) from e
        cache_to_use[cache_key] = {
            "value": value,
            "cache_ttl_in_seconds": int(parsed.get("cache_ttl_in_seconds", -1)),
            "inserted_at": datetime.datetime.utcnow(),
        }

        if cache_key in cache_miss:
            cache_miss[cache_key][feature_name] = value
            updated_keys.add(cache_key)
    parsing_end = time.perf_counter_ns()
    # Save keys that were not found in DynamoDB with None value
    if len(updated_keys) < len(cache_miss):
        missing_keys = set(cache_miss.keys()) - updated_keys
        for k in missing_keys:
            id_type = _get_id_type_from_partition_key(k, sep=cache_sep)
            if id_type == "STREAM":
                stream_features_cache[k] = {"value": None, "cache_ttl_in_seconds": 300}
            elif id_type == "USER":
                user_features_cache[k] = {
                    "value": None,
                    "cache_ttl_in_seconds": 6 * 3600,
                }
    end_time = time.perf_counter_ns()
    return FeatureRetrievalMeta(
        cache_misses=user_cache_misses + stream_cache_misses,
        user_cache_misses=user_cache_misses,
        stream_cache_misses=stream_cache_misses,
        retrieval_ms=_perf_counter_ns_delta_in_ms(time_start, end_time),
        success=True,
        cache_delay_minutes=cache_delay / 60,
        dynamo_ms=_perf_counter_ns_delta_in_ms(dynamo_start, dynamo_end),
        parsing_ms=_perf_counter_ns_delta_in_ms(dynamo_end, parsing_end),
    )


def _check_cache(
    obj: dict,
    id_type: Literal["STREAM", "USER"],
    id_key: str,
    feature_key: str,
    cache_sep: str,
    features_cache,
    cache_miss: dict,
    cache_delay: dict,
    now: datetime.datetime,
) -> tuple[dict, dict]:
    """
    obj: dictionary (stream or user object at this point in time) in which to
         insert the feature.
    id_type: any of "STREAM" or "USER"
    id_key: The id of the object, either stream url or userid.
    feature_key: feature key used to get the feature from dynamo.
    cache_sep: literal used to separate keys in the cache key.
    features_cache: Cache in which to check whether feature already exists.
    cache_miss: dictionary to store feature keys which are not present in cache.
    cache_delay: dictionary to store cache delay.
    now: reference timestamp for cache delay measurement.
    """
    key = _build_cache_key(
        id_type=id_type, id_key=id_key, feature_key=feature_key, cache_sep=cache_sep
    )
    # STREAM--http://haystack.tv--PWATCHED
    # USER--ASDhAKSJDH--PWATCHED
    # (USER#weasdasd, PWATCHED)
    if key in features_cache:
        # Only set if value is not None
        cached = features_cache.get(key)
        if cached["value"] is not None:
            obj[feature_key] = cached["value"]
            cache_delay[feature_key] = max(
                cache_delay[feature_key],
                (now - cached["inserted_at"]).total_seconds(),
            )
    else:
        cache_miss[key] = obj
    return cache_miss, cache_delay


def _get_id_type_from_partition_key(pk: str, sep: str) -> IdType:
    return pk.split(sep, 1)[0]


def _perf_counter_ns_delta_in_ms(start, end):
    return (end - start) * 1e-6


def _build_cache_key(
    id_type: IdType, id_key: str, feature_key: str, cache_sep: str
) -> str:
    return f"{id_type}{cache_sep}{id_key}{cache_sep}{feature_key}"
