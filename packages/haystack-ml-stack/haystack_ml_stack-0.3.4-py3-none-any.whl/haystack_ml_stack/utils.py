import pandas as pd
import numpy as np
import typing as _t
from .generated.v1.features_pb2 import (
    StreamPWatched,
    StreamPSelect,
    StreamSimilarityScores,
    SelectCounts,
    PositionPSelect,
    UserPWatched,
    EntryContextCounts,
    UserPersonalizingPWatched,
    UserPersonalizingPSelect,
    UserPSelect,
    EntryContextPWatched,
)
from ._serializers import SerializerRegistry
from . import exceptions


def stream_similarity_scores_cleanup(
    stream, similarity_key: str, similarity_prefix: str = "SIMILARITY", out: dict = None
) -> dict:
    if out is None:
        out = {}
    similarities: StreamSimilarityScores = stream.get(
        similarity_key, StreamSimilarityScores()
    )
    for category, score in similarities.data.items():
        out[f"{similarity_prefix.upper()}_{category.upper()}"] = score
    return out


def stream_similarity_top_category(
    stream, similarity_key: str, out: dict = None, output_key: str = "GEMINI_CATEGORY"
) -> dict:
    if out is None:
        out = {}
    similarity_scores: StreamSimilarityScores = stream.get(
        similarity_key, StreamSimilarityScores()
    )
    if similarity_scores.data:
        gemini_category = max(
            similarity_scores.data.keys(), key=lambda x: similarity_scores.data[x]
        )
    else:
        gemini_category = None
    out[output_key] = gemini_category
    return out


def stream_similarity_top_k_categories(
    stream,
    similarity_key: str,
    k: int,
    out: dict = None,
    output_key: str = "GEMINI_TOP_CATEGORIES",
) -> dict:
    if out is None:
        out = {}
    similarity_scores_map = stream.get(similarity_key, StreamSimilarityScores()).data
    if similarity_scores_map:
        sorted_keys = sorted(
            similarity_scores_map.keys(), key=lambda k: similarity_scores_map[k]
        )
        top_keys = sorted_keys[-k:][::-1]
    else:
        top_keys = None
    out[output_key] = top_keys
    return out


def stream_favorites_cleanup(
    stream,
    user_favorite_tags: list[str],
    user_favorite_authors: list[str],
    out: dict = None,
) -> dict:
    if out is None:
        out = {}
    stream_tags = stream.get("haystackTags", [])
    is_favorite_tag = (
        any(stream_tag in user_favorite_tags for stream_tag in stream_tags)
        if user_favorite_tags is not None
        else False
    )
    is_favorite_author = (
        stream.get("author", None) in user_favorite_authors
        if user_favorite_authors is not None
        else False
    )
    out["IS_FAVORITE_TAG"] = is_favorite_tag
    out["IS_FAVORITE_AUTHOR"] = is_favorite_author
    return out


def browsed_count_cleanups(
    stream,
    position_debiasing: _t.Literal[
        "up_to_4_browsed", "all_browsed"
    ] = "up_to_4_browsed",
    out: dict = None,
) -> dict:
    position_pselect: PositionPSelect = getattr(
        stream.get("PSELECT#24H", StreamPSelect()).data, position_debiasing
    )
    out = global_pselect_cleanup(
        position_pselect=position_pselect,
        feature_prefix="STREAM",
        lookback_period="24H",
        position_debiasing=position_debiasing,
        out=out,
    )
    return out


def device_split_browsed_count_cleanups(
    stream,
    device_type: _t.Literal["TV", "MOBILE"],
    position_debiasing: _t.Literal[
        "up_to_4_browsed", "all_browsed"
    ] = "up_to_4_browsed",
    out: dict = None,
) -> dict:
    position_alias_mapping = {
        "first_pos": "1ST_POS",
        "second_pos": "2ND_POS",
        "third_pos": "3RD_POS",
        "rest_pos": "REST_POS",
    }
    if position_debiasing == "up_to_4_browsed":
        suffix = "_UP_TO_4_BROWSED"
    elif position_debiasing == "all_browsed":
        suffix = ""
    else:
        raise ValueError(f"Unexpected position debiasing '{position_debiasing}'.")

    _validate_device_type(device_type)
    position_pselect: PositionPSelect = getattr(
        stream.get(f"PSELECT#24H#{device_type}", StreamPSelect()).data,
        position_debiasing,
    )
    total_selects = 0
    total_browsed = 0
    total_selects_and_watched = 0
    if out is None:
        out = {}
    for position, alias in position_alias_mapping.items():
        pos_counts: SelectCounts = getattr(position_pselect, position)
        total_browsed = pos_counts.total_browsed
        total_selects = pos_counts.total_selects
        total_selects_and_watched = pos_counts.total_selects_and_watched
        out[f"STREAM_{alias}_{device_type}_24H_TOTAL_BROWSED{suffix}"] = total_browsed
        out[f"STREAM_{alias}_{device_type}_24H_TOTAL_SELECTS{suffix}"] = total_selects
        out[f"STREAM_{alias}_{device_type}_24H_TOTAL_SELECTS_AND_WATCHED{suffix}"] = (
            total_selects_and_watched
        )
    return out


def watched_count_cleanups(
    stream, entry_contexts: list[str] = None, out: dict = None
) -> dict:
    if entry_contexts is None:
        entry_contexts = [
            "autoplay",
            "choose_next",
            "ch_swtch",
            "sel_thumb",
            "launch_first_in_session",
        ]
    _validate_pwatched_entry_context(entry_contexts)

    counts_obj: EntryContextPWatched = stream.get(
        f"PWATCHED#24H", StreamPWatched()
    ).data
    if out is None:
        out = {}
    out = _cleanup_entry_context_counts(
        counts_obj=counts_obj,
        entry_contexts=entry_contexts,
        feature_prefix="STREAM_",
        device_suffix="",
        lookback_period="24H",
        out=out,
    )
    return out


def device_watched_count_cleanups(
    stream, device_type: str, entry_contexts: list[str] = None, out: dict = None
) -> dict:
    if entry_contexts is None:
        entry_contexts = [
            "autoplay",
            "choose_next",
            "ch_swtch",
            "sel_thumb",
            "launch_first_in_session",
        ]

    _validate_pwatched_entry_context(entry_contexts)
    _validate_device_type(device_type)

    counts_obj: StreamPWatched = stream.get(
        f"PWATCHED#24H#{device_type}", StreamPWatched()
    ).data
    if out is None:
        out = {}
    out = _cleanup_entry_context_counts(
        counts_obj=counts_obj,
        entry_contexts=entry_contexts,
        feature_prefix="STREAM_",
        device_suffix=f"_{device_type}",
        lookback_period="24H",
        out=out,
    )
    return out


def user_author_show_count_cleanups(
    stream, user, entry_contexts: list[str] = None, out: dict = None
) -> dict:
    return user_personalizing_pwatched_cleanup(
        stream=stream,
        user=user,
        feature_id="PWATCHED#6M#AUTHOR_SHOW",
        feature_prefix="USER_AUTHOR_",
        lookup_key=stream.get("author", "") + "." + stream.get("show", ""),
        entry_contexts=entry_contexts,
        out=out,
    )


def user_stream_category_count_cleanups(
    stream, user, entry_contexts: list[str] = None, out: dict = None
) -> dict:
    return user_personalizing_pwatched_cleanup(
        stream=stream,
        user=user,
        feature_id="PWATCHED#6M#CATEGORY",
        feature_prefix="USER_STREAMCAT_",
        lookup_key="category",
        entry_contexts=entry_contexts,
        out=out,
    )


def user_gemini_count_cleanups(
    stream,
    user,
    entry_contexts: list[str] = None,
    out: dict = None,
    similarity_key: str = "SIMILARITY",
) -> dict:
    """If `out` is given and contains a `GEMINI_CATEGORY` key then it will use
    the value mapped to that key to match the stream to the user pwatched counts.
    Otherwise it will compute which category has the highest score."""
    if out is None:
        out = {}
    if "GEMINI_CATEGORY" in out.keys():
        gemini_category = out["GEMINI_CATEGORY"]
    else:
        gemini_category = stream_similarity_top_category(
            stream, similarity_key=similarity_key, out=out
        )["GEMINI_CATEGORY"]
    return user_personalizing_pwatched_cleanup(
        stream=stream,
        user=user,
        feature_id="PWATCHED#6M#GEMINI_CATEGORY",
        feature_prefix="USER_GEMINI_",
        lookup_key=gemini_category,
        entry_contexts=entry_contexts,
        out=out,
    )


def user_personalizing_pwatched_cleanup(
    stream,
    user,
    feature_id: str,
    feature_prefix: str,
    lookup_key: str | _t.Callable[[dict], str],
    entry_contexts,
    out,
) -> dict:
    # validation
    if entry_contexts is None:
        entry_contexts = [
            "autoplay",
            "choose_next",
            "ch_swtch",
            "sel_thumb",
            "launch_first_in_session",
        ]
    _validate_pwatched_entry_context(entry_contexts)
    if out is None:
        out = {}
    feature_is_invalid = "PWATCHED" not in feature_id and feature_id not in set(
        k.feature_id for k in SerializerRegistry.keys() if k.entity_type == "USER"
    )
    if feature_is_invalid:
        raise exceptions.InvalidFeaturesException(
            f"Unexpected feature id: {feature_id}"
        )

    # execution
    personalizing_pwatched = user.get(feature_id, UserPersonalizingPWatched())
    if lookup_key is None:
        lookup_key = "__LOOKUP_NOT_AVAILABLE__"
    elif not isinstance(lookup_key, str):
        lookup_key = lookup_key(stream)
    counts_obj = personalizing_pwatched.data[lookup_key]
    out = _cleanup_entry_context_counts(
        counts_obj=counts_obj,
        entry_contexts=entry_contexts,
        feature_prefix=feature_prefix,
        device_suffix="",
        lookback_period="6M",
        out=out,
    )
    return out


def user_pwatched_cleanup(
    user, entry_contexts: list[str] = None, out: dict = None
) -> dict:
    if out is None:
        out = {}
    if entry_contexts is None:
        entry_contexts = [
            "autoplay",
            "choose_next",
            "ch_swtch",
            "sel_thumb",
            "launch_first_in_session",
        ]
    _validate_pwatched_entry_context(entry_contexts)
    counts_obj = user.get("PWATCHED#6M", UserPWatched()).data
    out = _cleanup_entry_context_counts(
        counts_obj=counts_obj,
        entry_contexts=entry_contexts,
        feature_prefix="USER_",
        device_suffix="",
        lookback_period="6M",
        out=out,
    )
    return out


def user_pselect_cleanup(
    user,
    position_debiasing: _t.Literal[
        "up_to_4_browsed", "all_browsed"
    ] = "up_to_4_browsed",
    out: dict = None,
) -> dict:
    position_pselect: PositionPSelect = getattr(
        user.get("PSELECT#6M", UserPSelect()).data, position_debiasing
    )
    out = global_pselect_cleanup(
        position_pselect=position_pselect,
        feature_prefix="USER",
        lookback_period="6M",
        position_debiasing=position_debiasing,
        out=out,
    )
    return out


def _cleanup_entry_context_counts(
    counts_obj: EntryContextPWatched,
    entry_contexts: list[str],
    feature_prefix: str,
    device_suffix: str,
    lookback_period: str,
    out: dict,
) -> dict:
    if out is None:
        out = {}
    for entry_context in entry_contexts:
        attempts = getattr(counts_obj, entry_context).attempts
        watched = getattr(counts_obj, entry_context).watched
        context_key = entry_context if "launch" not in entry_context else "launch"
        context_key = context_key.upper()
        out[
            f"{feature_prefix}{context_key}{device_suffix}_{lookback_period}_TOTAL_WATCHED"
        ] = watched
        out[
            f"{feature_prefix}{context_key}{device_suffix}_{lookback_period}_TOTAL_ATTEMPTS"
        ] = attempts
    return out


def user_author_show_browsed_counting_features_cleanup(
    stream: dict,
    user: dict,
    position_debiasing: _t.Literal[
        "up_to_4_browsed", "all_browsed"
    ] = "up_to_4_browsed",
    out: dict = None,
) -> dict:
    return user_personalizing_pselect_cleanup(
        user=user,
        feature_id="PSELECT#6M#AUTHOR_SHOW",
        lookup_key=stream.get("author", "") + "." + stream.get("show", ""),
        feature_prefix="USER_AUTHOR",
        lookback_period="6M",
        position_debiasing=position_debiasing,
        out=out,
    )


def user_stream_category_browsed_counting_features_cleanup(
    stream: dict,
    user: dict,
    position_debiasing: _t.Literal[
        "up_to_4_browsed", "all_browsed"
    ] = "up_to_4_browsed",
    out: dict = None,
) -> dict:
    return user_personalizing_pselect_cleanup(
        user=user,
        feature_id="PSELECT#6M#CATEGORY",
        lookup_key=stream.get("category", ""),
        feature_prefix="USER_STREAMCAT",
        lookback_period="6M",
        position_debiasing=position_debiasing,
        out=out,
    )


def user_gemini_category_browsed_counting_features_cleanup(
    stream: dict,
    user: dict,
    similarity_key: str,
    position_debiasing: _t.Literal[
        "up_to_4_browsed", "all_browsed"
    ] = "up_to_4_browsed",
    out: dict = None,
) -> dict:
    if "GEMINI_CATEGORY" in out.keys():
        gemini_category = out["GEMINI_CATEGORY"]
    else:
        gemini_category = stream_similarity_top_category(
            stream, similarity_key=similarity_key, out=out, output_key="GEMINI_CATEGORY"
        )["GEMINI_CATEGORY"]
    return user_personalizing_pselect_cleanup(
        user=user,
        feature_id="PSELECT#6M#GEMINI_CATEGORY",
        lookup_key=gemini_category,
        feature_prefix="USER_GEMINI",
        lookback_period="6M",
        position_debiasing=position_debiasing,
        out=out,
    )


def user_personalizing_pselect_cleanup(
    user: dict,
    feature_id: str,
    lookup_key: str,
    feature_prefix: str,
    lookback_period: str,
    position_debiasing: str,
    out: dict,
) -> dict:
    personalizing_pselect: UserPersonalizingPSelect = user.get(
        feature_id, UserPersonalizingPSelect()
    )
    if lookup_key is None:
        lookup_key = "__LOOKUP_NOT_AVAILABLE__"
    position_pselect: PositionPSelect = getattr(
        personalizing_pselect.data[lookup_key], position_debiasing
    )
    out = global_pselect_cleanup(
        position_pselect=position_pselect,
        feature_prefix=feature_prefix,
        lookback_period=lookback_period,
        position_debiasing=position_debiasing,
        out=out,
    )
    return out


def global_pselect_cleanup(
    position_pselect: PositionPSelect,
    feature_prefix: str,
    lookback_period: str,
    position_debiasing: str,
    out: dict,
) -> dict:
    if out is None:
        out = {}
    if position_debiasing == "up_to_4_browsed":
        suffix = "_UP_TO_4_BROWSED"
    elif position_debiasing == "all_browsed":
        suffix = ""
    else:
        raise ValueError(f"Unexpected position debiasing '{position_debiasing}'.")
    position_alias_mapping = {
        "first_pos": "1ST_POS",
        "second_pos": "2ND_POS",
        "third_pos": "3RD_POS",
        "rest_pos": "REST_POS",
    }
    total_selects = 0
    total_browsed = 0
    total_selects_and_watched = 0
    for position in position_alias_mapping.keys():
        pos_counts: SelectCounts = getattr(position_pselect, position)
        total_browsed += pos_counts.total_browsed
        total_selects += pos_counts.total_selects
        total_selects_and_watched += pos_counts.total_selects_and_watched
    out[f"{feature_prefix}_{lookback_period}_TOTAL_BROWSED{suffix}"] = total_browsed
    out[f"{feature_prefix}_{lookback_period}_TOTAL_SELECTS{suffix}"] = total_selects
    out[f"{feature_prefix}_{lookback_period}_TOTAL_SELECTS_AND_WATCHED{suffix}"] = (
        total_selects_and_watched
    )
    return out


def generic_beta_adjust_features(
    data: pd.DataFrame,
    prefix: str,
    pwatched_beta_params: dict = None,
    pselect_beta_params: dict = None,
    pslw_beta_params: dict = None,
    use_low_sample_flags: bool = False,
    low_sample_threshold: int = 3,
    use_attempt_features: bool = False,
    max_attempt_cap: int = 100,
    debiased_pselect: bool = True,
    use_logodds: bool = False,
    out: pd.DataFrame = None,
) -> pd.DataFrame:
    features = {}
    counting_feature_cols = [
        c
        for c in data.columns
        if "TOTAL_WATCHED" in c
        or "TOTAL_ATTEMPTS" in c
        or "SELECT" in c
        or "BROWSED" in c
    ]
    data_arr = data[counting_feature_cols].to_numpy(dtype=float)
    col_to_idx = {col: i for i, col in enumerate(counting_feature_cols)}
    if pwatched_beta_params is not None:
        for context, (alpha, beta) in pwatched_beta_params.items():
            total_watched = np.nan_to_num(
                data_arr[:, col_to_idx[f"{prefix}_{context}_TOTAL_WATCHED"]]
            )
            total_attempts = np.nan_to_num(
                data_arr[:, col_to_idx[f"{prefix}_{context}_TOTAL_ATTEMPTS"]]
            )
            features[f"{prefix}_{context}_ADJ_PWATCHED"] = (total_watched + alpha) / (
                total_attempts + alpha + beta
            )
            low_sample_arr = np.empty_like(total_attempts, dtype=float)
            if use_low_sample_flags:
                features[f"{prefix}_{context}_LOW_SAMPLE"] = np.less_equal(
                    total_attempts, low_sample_threshold, out=low_sample_arr
                )
            if use_attempt_features:
                features[f"{prefix}_{context}_ATTEMPTS"] = np.clip(
                    total_attempts, a_min=None, a_max=max_attempt_cap
                )

    debias_suffix = "_UP_TO_4_BROWSED" if debiased_pselect else ""
    if pselect_beta_params is not None or pslw_beta_params is not None:
        for key, (alpha, beta) in pselect_beta_params.items():
            total_selects_idx = col_to_idx[
                f"{prefix}_{key}_TOTAL_SELECTS{debias_suffix}"
            ]
            total_browsed_idx = col_to_idx[
                f"{prefix}_{key}_TOTAL_BROWSED{debias_suffix}"
            ]
            total_slw_idx = col_to_idx[
                f"{prefix}_{key}_TOTAL_SELECTS_AND_WATCHED{debias_suffix}"
            ]
            total_selects = np.nan_to_num(data_arr[:, total_selects_idx])
            total_browsed = np.nan_to_num(data_arr[:, total_browsed_idx])
            total_slw = np.nan_to_num(data_arr[:, total_slw_idx])
            if pselect_beta_params is not None:
                features[f"{prefix}_{key}_ADJ_PSELECT{debias_suffix}"] = (
                    total_selects + alpha
                ) / (total_selects + total_browsed + alpha + beta)
            if use_low_sample_flags:
                low_sample_arr = np.empty_like(total_selects, dtype=float)
                features[f"{prefix}_{key}_PSELECT_LOW_SAMPLE{debias_suffix}"] = (
                    np.less_equal(
                        total_selects + total_browsed,
                        low_sample_threshold,
                        out=low_sample_arr,
                    )
                )
            if use_attempt_features:
                features[f"{prefix}_{key}_PSELECT_ATTEMPTS{debias_suffix}"] = np.clip(
                    total_selects + total_browsed, a_min=0, a_max=max_attempt_cap
                )
            if pslw_beta_params is not None:
                pslw_alpha, pslw_beta = pslw_beta_params[key]
                features[f"{prefix}_{key}_ADJ_PSLW{debias_suffix}"] = (
                    total_slw + pslw_alpha
                ) / (total_selects + total_browsed + pslw_alpha + pslw_beta)
            if pslw_beta_params is not None and pselect_beta_params is not None:
                features[f"{prefix}_{key}_PSelNotW{debias_suffix}"] = (
                    features[f"{prefix}_{key}_ADJ_PSELECT{debias_suffix}"]
                    - features[f"{prefix}_{key}_ADJ_PSLW{debias_suffix}"]
                )
    if out is None:
        out = pd.DataFrame(features, index=data.index)
    else:
        keys = list(features.keys())
        intermediate = np.column_stack([features[k] for k in keys])
        out[keys] = intermediate
    if use_logodds:
        arr = out.to_numpy()
        col_idxs = [
            i
            for i, c in enumerate(out.columns)
            if ("PSELECT" in c or "PSLW" in c or "PWATCHED" in c or "PSelNotW" in c)
            and ("LOW_SAMPLE" not in c and "ATTEMPTS" not in c)
            and c in features
        ]
        arr[:, col_idxs] = prob_to_logodds(
            np.clip(arr[:, col_idxs], a_min=0.001, a_max=None)
        )
    return out


def prob_to_logodds(prob: float) -> float:
    return np.log(prob) - np.log(1 - prob)


def scale_preds(
    preds: pd.Series,
    original_mean: float,
    original_std: float,
    target_mean: float,
    target_std: float,
) -> pd.Series:
    z_score = (preds - original_mean) / original_std
    return z_score * target_std + target_mean


def sigmoid(x: float) -> float:
    return 1 / (1 + np.exp(-x))


def generic_logistic_predict(
    data: pd.DataFrame, coeffs: pd.Series, intercept: float
) -> pd.Series:
    scores = (data[coeffs.index] * coeffs).sum(axis=1) + intercept
    raw_arr = scores.to_numpy()
    raw_arr[:] = sigmoid(raw_arr)
    return scores


def _validate_device_type(device_type: str):
    if device_type not in ("TV", "MOBILE"):
        raise ValueError(f"Invalid device type '{device_type}")


def _validate_pwatched_entry_context(entry_contexts: list[str]):
    valid_contexts = [
        "autoplay",
        "choose_next",
        "ch_swtch",
        "sel_thumb",
        "launch_first_in_session",
    ]
    invalid_contexts = [c for c in entry_contexts if c not in valid_contexts]
    if invalid_contexts:
        raise ValueError(f"Invalid entry contexts found: {invalid_contexts}")
