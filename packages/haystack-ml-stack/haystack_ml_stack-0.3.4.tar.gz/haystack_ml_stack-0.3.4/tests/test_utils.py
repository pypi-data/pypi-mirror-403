import pytest
import pandas as pd
from haystack_ml_stack import utils, SerializerRegistry
import numpy as np
from haystack_ml_stack.generated.v1 import features_pb2 as features_pb2_v1
from google.protobuf.json_format import ParseDict as ProtoParseDict


def test_sigmoid():
    values_to_test = np.array([-1, 0, 1])
    expected = np.array([0.26894142136992605, 0.5, 0.731058578630074])
    actual = utils.sigmoid(values_to_test)
    assert np.isclose(actual, expected).all()


def test_prob_to_logodds():
    values_to_test = np.array([0.25, 0.5, 0.75])
    expected = np.array([-1.0986122886681096, 0, 1.0986122886681096])
    actual = utils.prob_to_logodds(values_to_test)
    assert np.isclose(actual, expected).all(), print(actual - expected)


def test_generic_beta_adjust_features():
    data_to_test = pd.DataFrame(
        {
            "STREAM_AUTOPLAY_24H_TOTAL_ATTEMPTS": [1, 2],
            "STREAM_AUTOPLAY_24H_TOTAL_WATCHED": [0, 1],
            "STREAM_24H_TOTAL_SELECTS_UP_TO_4_BROWSED": [1, 1],
            "STREAM_24H_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": [0, 1],
            "STREAM_24H_TOTAL_BROWSED_UP_TO_4_BROWSED": [2, 0],
        },
        dtype=float,
    )
    actual = utils.generic_beta_adjust_features(
        data=data_to_test,
        prefix="STREAM",
        pwatched_beta_params={"AUTOPLAY_24H": (2, 1)},
        pselect_beta_params={"24H": (1, 1)},
        pslw_beta_params={"24H": (0.5, 1)},
        use_low_sample_flags=True,
    )
    expected = pd.DataFrame(
        {
            "STREAM_AUTOPLAY_24H_ADJ_PWATCHED": [
                (0 + 2) / (1 + 2 + 1),
                (1 + 2) / (2 + 2 + 1),
            ],
            "STREAM_24H_ADJ_PSELECT_UP_TO_4_BROWSED": [
                (1 + 1) / (1 + 2 + 1 + 1),
                (1 + 1) / (1 + 0 + 1 + 1),
            ],
            "STREAM_24H_ADJ_PSLW_UP_TO_4_BROWSED": [
                (0 + 0.5) / (1 + 2 + 0.5 + 1),
                (1 + 0.5) / (1 + 0 + 0.5 + 1),
            ],
            "STREAM_24H_PSelNotW_UP_TO_4_BROWSED": [
                (1 + 1) / (1 + 2 + 1 + 1) - (0 + 0.5) / (1 + 2 + 0.5 + 1),
                (1 + 1) / (1 + 0 + 1 + 1) - (1 + 0.5) / (1 + 0 + 0.5 + 1),
            ],
            "STREAM_AUTOPLAY_24H_LOW_SAMPLE": [1, 1],
            "STREAM_24H_PSELECT_LOW_SAMPLE_UP_TO_4_BROWSED": [1, 1],
        }
    )
    assert (actual[expected.columns] == expected).all(axis=None), actual - expected
    # test in place transformation
    output = pd.DataFrame(index=data_to_test.index)
    utils.generic_beta_adjust_features(
        data=data_to_test,
        prefix="STREAM",
        pwatched_beta_params={"AUTOPLAY_24H": (2, 1)},
        pselect_beta_params={"24H": (1, 1)},
        pslw_beta_params={"24H": (0.5, 1)},
        use_low_sample_flags=True,
        out=output,
    )
    assert (output[expected.columns] == expected).all(axis=None), output - expected


def test_generic_logistic_predict():
    features = pd.DataFrame({"feat1": [0, 1, 2], "feat2": [3, 3, 5]}, dtype=float)
    coeffs = pd.Series({"feat1": 1, "feat2": 2})
    intercept = 1
    expected = utils.sigmoid(
        pd.Series([0 * 1 + 2 * 3, 1 * 1 + 2 * 3, 2 * 1 + 5 * 2]) + 1
    )
    actual = utils.generic_logistic_predict(
        data=features, coeffs=coeffs, intercept=intercept
    )
    assert (expected == actual).all(), actual - expected


def test_user_author_pwatched_cleanup():
    user_data = {
        "version": 1,
        "data": {
            "cnn.": {
                "autoplay": {"attempts": 1, "watched": 0},
                "ch_swtch": {"attempts": 2, "watched": 1},
            },
            "amazelab.": {"sel_thumb": {"attempts": 3, "watched": 3}},
            "nbc.show1": {"ch_swtch": {"attempts": 3, "watched": 2}},
        },
    }
    user_author_pwatched_msg = features_pb2_v1.UserPersonalizingPWatched()
    user = {"PWATCHED#6M#AUTHOR_SHOW": user_author_pwatched_msg}
    ProtoParseDict(user_data, message=user_author_pwatched_msg)
    streams = [
        {"author": "cnn"},
        {"author": "amazelab", "show": "show2"},
        {"author": "amazelab"},
        {"author": "nbc", "show": "show1"},
    ]
    values = []
    for stream in streams:
        out = {}
        utils.user_author_show_count_cleanups(
            stream=stream,
            user=user,
            entry_contexts=["sel_thumb", "autoplay", "ch_swtch"],
            out=out,
        )
        values.append(out)
    actual = pd.DataFrame(values)
    expected = pd.DataFrame(
        [
            {
                "USER_AUTHOR_AUTOPLAY_6M_TOTAL_ATTEMPTS": 1,
                "USER_AUTHOR_AUTOPLAY_6M_TOTAL_WATCHED": 0,
                "USER_AUTHOR_CH_SWTCH_6M_TOTAL_ATTEMPTS": 2,
                "USER_AUTHOR_CH_SWTCH_6M_TOTAL_WATCHED": 1,
                "USER_AUTHOR_SEL_THUMB_6M_TOTAL_ATTEMPTS": 0,
                "USER_AUTHOR_SEL_THUMB_6M_TOTAL_WATCHED": 0,
            },
            {
                "USER_AUTHOR_AUTOPLAY_6M_TOTAL_ATTEMPTS": 0,
                "USER_AUTHOR_AUTOPLAY_6M_TOTAL_WATCHED": 0,
                "USER_AUTHOR_CH_SWTCH_6M_TOTAL_ATTEMPTS": 0,
                "USER_AUTHOR_CH_SWTCH_6M_TOTAL_WATCHED": 0,
                "USER_AUTHOR_SEL_THUMB_6M_TOTAL_ATTEMPTS": 0,
                "USER_AUTHOR_SEL_THUMB_6M_TOTAL_WATCHED": 0,
            },
            {
                "USER_AUTHOR_AUTOPLAY_6M_TOTAL_ATTEMPTS": 0,
                "USER_AUTHOR_AUTOPLAY_6M_TOTAL_WATCHED": 0,
                "USER_AUTHOR_CH_SWTCH_6M_TOTAL_ATTEMPTS": 0,
                "USER_AUTHOR_CH_SWTCH_6M_TOTAL_WATCHED": 0,
                "USER_AUTHOR_SEL_THUMB_6M_TOTAL_ATTEMPTS": 3,
                "USER_AUTHOR_SEL_THUMB_6M_TOTAL_WATCHED": 3,
            },
            {
                "USER_AUTHOR_AUTOPLAY_6M_TOTAL_ATTEMPTS": 0,
                "USER_AUTHOR_AUTOPLAY_6M_TOTAL_WATCHED": 0,
                "USER_AUTHOR_CH_SWTCH_6M_TOTAL_ATTEMPTS": 3,
                "USER_AUTHOR_CH_SWTCH_6M_TOTAL_WATCHED": 2,
                "USER_AUTHOR_SEL_THUMB_6M_TOTAL_ATTEMPTS": 0,
                "USER_AUTHOR_SEL_THUMB_6M_TOTAL_WATCHED": 0,
            },
        ]
    )
    assert (actual[expected.columns] == expected).all().all()


def test_user_gemini_pwatched_cleanup():
    user_data = {
        "version": 1,
        "data": {
            "arts_entertainment": {
                "autoplay": {"attempts": 1, "watched": 0},
                "ch_swtch": {"attempts": 2, "watched": 1},
            },
            "economy": {"sel_thumb": {"attempts": 3, "watched": 3}},
            "human_interest": {"ch_swtch": {"attempts": 3, "watched": 2}},
        },
    }
    user_author_pwatched_msg = features_pb2_v1.UserPersonalizingPWatched()
    user = {"PWATCHED#6M#GEMINI_CATEGORY": user_author_pwatched_msg}
    ProtoParseDict(user_data, message=user_author_pwatched_msg)
    streams = [
        {"GEMINI_CATEGORY": "arts_entertainment"},
        {
            "SIMILARITY": features_pb2_v1.StreamSimilarityScores(
                version=1,
                data={
                    "arts_entertainment": 0.1,
                    "economy": 0.9,
                    "human_interest": -0.3,
                },
            )
        },
        {},
        {"GEMINI_CATEGORY": "politics"},
    ]
    expected = pd.DataFrame(
        [
            {
                "USER_GEMINI_AUTOPLAY_6M_TOTAL_ATTEMPTS": 1,
                "USER_GEMINI_AUTOPLAY_6M_TOTAL_WATCHED": 0,
                "USER_GEMINI_CH_SWTCH_6M_TOTAL_ATTEMPTS": 2,
                "USER_GEMINI_CH_SWTCH_6M_TOTAL_WATCHED": 1,
                "USER_GEMINI_SEL_THUMB_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_SEL_THUMB_6M_TOTAL_WATCHED": 0,
            },
            {
                "USER_GEMINI_AUTOPLAY_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_AUTOPLAY_6M_TOTAL_WATCHED": 0,
                "USER_GEMINI_CH_SWTCH_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_CH_SWTCH_6M_TOTAL_WATCHED": 0,
                "USER_GEMINI_SEL_THUMB_6M_TOTAL_ATTEMPTS": 3,
                "USER_GEMINI_SEL_THUMB_6M_TOTAL_WATCHED": 3,
            },
            {
                "USER_GEMINI_AUTOPLAY_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_AUTOPLAY_6M_TOTAL_WATCHED": 0,
                "USER_GEMINI_CH_SWTCH_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_CH_SWTCH_6M_TOTAL_WATCHED": 0,
                "USER_GEMINI_SEL_THUMB_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_SEL_THUMB_6M_TOTAL_WATCHED": 0,
            },
            {
                "USER_GEMINI_AUTOPLAY_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_AUTOPLAY_6M_TOTAL_WATCHED": 0,
                "USER_GEMINI_CH_SWTCH_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_CH_SWTCH_6M_TOTAL_WATCHED": 0,
                "USER_GEMINI_SEL_THUMB_6M_TOTAL_ATTEMPTS": 0,
                "USER_GEMINI_SEL_THUMB_6M_TOTAL_WATCHED": 0,
            },
        ]
    )
    values = []
    for stream in streams:
        out = {}
        if "GEMINI_CATEGORY" in stream:
            out["GEMINI_CATEGORY"] = stream["GEMINI_CATEGORY"]
        utils.user_gemini_count_cleanups(
            stream=stream,
            user=user,
            entry_contexts=["sel_thumb", "autoplay", "ch_swtch"],
            out=out,
            similarity_key="SIMILARITY",
        )
        values.append(out)
    actual = pd.DataFrame(values)
    assert (actual[expected.columns] == expected).all().all()
    return


def test_user_author_pselect_cleanup():
    user_data = {
        "version": 1,
        "data": {
            "cnn.": {
                "all_browsed": {
                    "second_pos": {
                        "total_selects": 0,
                        "total_selects_and_watched": 0,
                        "total_browsed": 3,
                    },
                    "rest_pos": {
                        "total_selects": 1,
                        "total_selects_and_watched": 1,
                        "total_browsed": 0,
                    },
                },
                "up_to_4_browsed": {
                    "second_pos": {
                        "total_selects": 0,
                        "total_selects_and_watched": 0,
                        "total_browsed": 2,
                    },
                    "rest_pos": {
                        "total_selects": 1,
                        "total_selects_and_watched": 1,
                        "total_browsed": 0,
                    },
                },
            },
            "nbc.show1": {
                "all_browsed": {
                    "second_pos": {
                        "total_selects": 1,
                        "total_selects_and_watched": 0,
                        "total_browsed": 2,
                    },
                    "rest_pos": {
                        "total_selects": 1,
                        "total_selects_and_watched": 1,
                        "total_browsed": 1,
                    },
                },
                "up_to_4_browsed": {
                    "second_pos": {
                        "total_selects": 1,
                        "total_selects_and_watched": 0,
                        "total_browsed": 2,
                    },
                    "rest_pos": {
                        "total_selects": 1,
                        "total_selects_and_watched": 1,
                        "total_browsed": 0,
                    },
                },
            },
        },
    }
    user_author_pselect_msg = features_pb2_v1.UserPersonalizingPSelect()
    ProtoParseDict(js_dict=user_data, message=user_author_pselect_msg)
    streams = [
        {"author": "cnn"},
        {"author": "amazelab", "show": "show2"},
        {"author": "nbc", "show": "show1"},
    ]
    values = []
    user = {"PSELECT#6M#AUTHOR_SHOW": user_author_pselect_msg}
    for stream in streams:
        out = {}
        utils.user_author_show_browsed_counting_features_cleanup(
            stream=stream, user=user, position_debiasing="up_to_4_browsed", out=out
        )
        values.append(out)
    expected = pd.DataFrame(
        [
            {
                "USER_AUTHOR_6M_TOTAL_SELECTS_UP_TO_4_BROWSED": 1,
                "USER_AUTHOR_6M_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 1,
                "USER_AUTHOR_6M_TOTAL_BROWSED_UP_TO_4_BROWSED": 2,
            },
            {
                "USER_AUTHOR_6M_TOTAL_SELECTS_UP_TO_4_BROWSED": 0,
                "USER_AUTHOR_6M_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 0,
                "USER_AUTHOR_6M_TOTAL_BROWSED_UP_TO_4_BROWSED": 0,
            },
            {
                "USER_AUTHOR_6M_TOTAL_SELECTS_UP_TO_4_BROWSED": 2,
                "USER_AUTHOR_6M_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 1,
                "USER_AUTHOR_6M_TOTAL_BROWSED_UP_TO_4_BROWSED": 2,
            },
        ]
    )
    actual = pd.DataFrame(values)
    assert (actual[expected.columns] == expected).all().all()
    return


def test_stream_pwatched_cleanup():
    stream_pwatched_data = {
        "version": 1,
        "data": {
            "autoplay": {"attempts": 1, "watched": 1},
            "ch_swtch": {"attempts": 2, "watched": 0},
        },
    }
    stream_pwatched = features_pb2_v1.StreamPWatched()
    ProtoParseDict(js_dict=stream_pwatched_data, message=stream_pwatched)
    stream = {"PWATCHED#24H": stream_pwatched}
    out = {}
    utils.watched_count_cleanups(
        stream=stream,
        entry_contexts=["autoplay", "ch_swtch", "sel_thumb"],
        out=out,
    )
    expected = pd.Series(
        {
            "STREAM_AUTOPLAY_24H_TOTAL_ATTEMPTS": 1,
            "STREAM_AUTOPLAY_24H_TOTAL_WATCHED": 1,
            "STREAM_CH_SWTCH_24H_TOTAL_ATTEMPTS": 2,
            "STREAM_CH_SWTCH_24H_TOTAL_WATCHED": 0,
            "STREAM_SEL_THUMB_24H_TOTAL_ATTEMPTS": 0,
            "STREAM_SEL_THUMB_24H_TOTAL_WATCHED": 0,
        }
    )
    actual = pd.Series(out).loc[expected.index]
    assert (actual == expected).all()


def test_device_stream_pwatched_cleanup():
    stream_pwatched_data = {
        "version": 1,
        "data": {
            "autoplay": {"attempts": 1, "watched": 1},
            "ch_swtch": {"attempts": 2, "watched": 0},
        },
    }
    stream_pwatched = features_pb2_v1.StreamPWatched()
    ProtoParseDict(js_dict=stream_pwatched_data, message=stream_pwatched)
    stream = {"PWATCHED#24H#TV": stream_pwatched}
    out = {}
    utils.device_watched_count_cleanups(
        stream=stream,
        entry_contexts=["autoplay", "ch_swtch", "sel_thumb"],
        device_type="TV",
        out=out,
    )
    expected = pd.Series(
        {
            "STREAM_AUTOPLAY_TV_24H_TOTAL_ATTEMPTS": 1,
            "STREAM_AUTOPLAY_TV_24H_TOTAL_WATCHED": 1,
            "STREAM_CH_SWTCH_TV_24H_TOTAL_ATTEMPTS": 2,
            "STREAM_CH_SWTCH_TV_24H_TOTAL_WATCHED": 0,
            "STREAM_SEL_THUMB_TV_24H_TOTAL_ATTEMPTS": 0,
            "STREAM_SEL_THUMB_TV_24H_TOTAL_WATCHED": 0,
        }
    )
    actual = pd.Series(out).loc[expected.index]
    assert (actual == expected).all()
    stream = {"PWATCHED#24H#MOBILE": stream_pwatched}
    out = {}
    utils.device_watched_count_cleanups(
        stream=stream,
        entry_contexts=["autoplay", "ch_swtch", "sel_thumb"],
        device_type="MOBILE",
        out=out,
    )
    expected = pd.Series(
        {
            "STREAM_AUTOPLAY_MOBILE_24H_TOTAL_ATTEMPTS": 1,
            "STREAM_AUTOPLAY_MOBILE_24H_TOTAL_WATCHED": 1,
            "STREAM_CH_SWTCH_MOBILE_24H_TOTAL_ATTEMPTS": 2,
            "STREAM_CH_SWTCH_MOBILE_24H_TOTAL_WATCHED": 0,
            "STREAM_SEL_THUMB_MOBILE_24H_TOTAL_ATTEMPTS": 0,
            "STREAM_SEL_THUMB_MOBILE_24H_TOTAL_WATCHED": 0,
        }
    )
    actual = pd.Series(out).loc[expected.index]
    assert (actual == expected).all()


def test_stream_global_pselect_cleanup():
    stream_pselect_data = {
        "version": 1,
        "data": {
            "all_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 1,
                },
                "rest_pos": {
                    "total_selects": 2,
                    "total_selects_and_watched": 2,
                    "total_browsed": 1,
                },
            },
            "up_to_4_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 1,
                },
                "rest_pos": {
                    "total_selects": 2,
                    "total_selects_and_watched": 2,
                    "total_browsed": 0,
                },
            },
        },
    }
    msg = features_pb2_v1.StreamPSelect()
    ProtoParseDict(js_dict=stream_pselect_data, message=msg)
    out = {}
    stream = {"PSELECT#24H": msg}
    utils.browsed_count_cleanups(
        stream=stream, position_debiasing="up_to_4_browsed", out=out
    )
    expected = pd.Series(
        {
            "STREAM_24H_TOTAL_BROWSED_UP_TO_4_BROWSED": 1,
            "STREAM_24H_TOTAL_SELECTS_UP_TO_4_BROWSED": 2,
            "STREAM_24H_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 2,
        }
    )
    actual = pd.Series(out).loc[expected.index]
    assert (expected == actual).all()


def test_stream_split_pselect_cleanup():
    stream_pselect_data = {
        "version": 1,
        "data": {
            "all_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 1,
                },
                "rest_pos": {
                    "total_selects": 2,
                    "total_selects_and_watched": 2,
                    "total_browsed": 1,
                },
            },
            "up_to_4_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 1,
                },
                "rest_pos": {
                    "total_selects": 2,
                    "total_selects_and_watched": 2,
                    "total_browsed": 0,
                },
            },
        },
    }
    msg = features_pb2_v1.StreamPSelect()
    ProtoParseDict(js_dict=stream_pselect_data, message=msg)
    stream = {"PSELECT#24H#TV": msg}
    out = {}
    utils.device_split_browsed_count_cleanups(
        stream=stream, device_type="TV", position_debiasing="up_to_4_browsed", out=out
    )
    expected = pd.Series(
        {
            "STREAM_1ST_POS_TV_24H_TOTAL_BROWSED_UP_TO_4_BROWSED": 1,
            "STREAM_1ST_POS_TV_24H_TOTAL_SELECTS_UP_TO_4_BROWSED": 0,
            "STREAM_1ST_POS_TV_24H_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 0,
            "STREAM_2ND_POS_TV_24H_TOTAL_BROWSED_UP_TO_4_BROWSED": 0,
            "STREAM_2ND_POS_TV_24H_TOTAL_SELECTS_UP_TO_4_BROWSED": 0,
            "STREAM_2ND_POS_TV_24H_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 0,
            "STREAM_3RD_POS_TV_24H_TOTAL_BROWSED_UP_TO_4_BROWSED": 0,
            "STREAM_3RD_POS_TV_24H_TOTAL_SELECTS_UP_TO_4_BROWSED": 0,
            "STREAM_3RD_POS_TV_24H_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 0,
            "STREAM_REST_POS_TV_24H_TOTAL_BROWSED_UP_TO_4_BROWSED": 0,
            "STREAM_REST_POS_TV_24H_TOTAL_SELECTS_UP_TO_4_BROWSED": 2,
            "STREAM_REST_POS_TV_24H_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 2,
        }
    )
    actual = pd.Series(out).loc[expected.index]
    assert (expected == actual).all()


def test_stream_similarity_top_category_functions():
    similarity_scores = {
        "version": 1,
        "data": {
            "cat1": 0.4,
            "cat2": 0.3,
            "cat3": -0.5,
            "cat5": 0.2,
            "cat6": 0.5,
            "cat7": 0.1,
        },
    }
    similarity_scores_msg = features_pb2_v1.StreamSimilarityScores()
    ProtoParseDict(js_dict=similarity_scores, message=similarity_scores_msg)
    stream = {"SIMILARITY#GEMINI": similarity_scores_msg}
    actual = utils.stream_similarity_top_category(
        stream, similarity_key="SIMILARITY#GEMINI", output_key="GEMINI_CATEGORY"
    )["GEMINI_CATEGORY"]
    expected = "cat6"
    assert actual == expected

    actual = utils.stream_similarity_top_k_categories(
        stream=stream,
        k=2,
        similarity_key="SIMILARITY#GEMINI",
        output_key="GEMINI_TOP_CATEGORY",
    )["GEMINI_TOP_CATEGORY"]
    expected = ["cat6", "cat1"]
    assert all(
        actual_key == expected_key for actual_key, expected_key in zip(actual, expected)
    )


def test_user_pwatched_cleanup():
    user_pwatched_data = {
        "version": 1,
        "data": {
            "sel_thumb": {"attempts": 1, "watched": 1},
            "ch_swtch": {"attempts": 2, "watched": 0},
        },
    }
    user_pwatched_msg = features_pb2_v1.UserPWatched()
    ProtoParseDict(js_dict=user_pwatched_data, message=user_pwatched_msg)
    user = {"PWATCHED#6M": user_pwatched_msg}
    out = {}
    utils.user_pwatched_cleanup(
        user=user, entry_contexts=["autoplay", "sel_thumb", "ch_swtch"], out=out
    )
    expected = pd.Series(
        {
            "USER_AUTOPLAY_6M_TOTAL_ATTEMPTS": 0,
            "USER_AUTOPLAY_6M_TOTAL_WATCHED": 0,
            "USER_SEL_THUMB_6M_TOTAL_ATTEMPTS": 1,
            "USER_SEL_THUMB_6M_TOTAL_WATCHED": 1,
            "USER_CH_SWTCH_6M_TOTAL_ATTEMPTS": 2,
            "USER_CH_SWTCH_6M_TOTAL_WATCHED": 0,
        }
    )
    actual = pd.Series(out).loc[expected.index]
    assert (expected == actual).all()


def test_user_pselect_cleanup():
    user_pselect_data = {
        "version": 1,
        "data": {
            "all_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 1,
                },
                "rest_pos": {
                    "total_selects": 2,
                    "total_selects_and_watched": 2,
                    "total_browsed": 1,
                },
            },
            "up_to_4_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 1,
                },
                "rest_pos": {
                    "total_selects": 2,
                    "total_selects_and_watched": 2,
                    "total_browsed": 0,
                },
            },
        },
    }
    user_pselect_msg = features_pb2_v1.UserPSelect()
    ProtoParseDict(js_dict=user_pselect_data, message=user_pselect_msg)
    user = {"PSELECT#6M": user_pselect_msg}
    out = {}
    utils.user_pselect_cleanup(user=user, position_debiasing="up_to_4_browsed", out=out)
    expected = pd.Series(
        {
            "USER_6M_TOTAL_BROWSED_UP_TO_4_BROWSED": 1,
            "USER_6M_TOTAL_SELECTS_UP_TO_4_BROWSED": 2,
            "USER_6M_TOTAL_SELECTS_AND_WATCHED_UP_TO_4_BROWSED": 2,
        }
    )
    actual = pd.Series(out).loc[expected.index]
    assert (actual == expected).all()
