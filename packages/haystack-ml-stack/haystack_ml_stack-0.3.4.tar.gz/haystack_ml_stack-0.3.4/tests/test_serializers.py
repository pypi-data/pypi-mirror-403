from google.protobuf.json_format import ParseDict as ProtoParseDict
from haystack_ml_stack import SerializerRegistry
from haystack_ml_stack.generated.v1 import features_pb2 as features_pb2_v1


def test_v0_serializers():
    stream_pwatched_v0 = {
        "autoplay": {"attempts": 3, "watched": 3},
        "ch swtch": {"attempts": 4, "watched": 2},
        "choose next": {"attempts": 4, "watched": 1},
        "sel thumb": {"attempts": 5, "watched": 4},
        "launch first in session": {"attempts": 1, "watched": 1},
    }
    expected_v1 = {
        "version": 1,
        "data": {
            "autoplay": {"attempts": 3, "watched": 3},
            "ch_swtch": {"attempts": 4, "watched": 2},
            "choose_next": {"attempts": 4, "watched": 1},
            "sel_thumb": {"attempts": 5, "watched": 4},
            "launch_first_in_session": {"attempts": 1, "watched": 1},
        },
    }
    expected_v1_msg = features_pb2_v1.StreamPWatched()
    ProtoParseDict(js_dict=expected_v1, message=expected_v1_msg)
    serializer = SerializerRegistry[("STREAM", "PWATCHED#24H", "v0")]
    actual = serializer.deserialize(stream_pwatched_v0)
    assert expected_v1_msg == actual, "PWatched deserialization failed!"

    stream_pselect_v0 = {
        "4_browsed": {
            "0": {
                "total_selects": 0,
                "total_selects_and_watched": 0,
                "total_browsed": 2,
            },
            "3+": {
                "total_selects": 2,
                "total_selects_and_watched": 0,
                "total_browsed": 2,
            },
        },
        "all_browsed": {
            "0": {
                "total_selects": 0,
                "total_selects_and_watched": 0,
                "total_browsed": 4,
            },
            "3+": {
                "total_selects": 2,
                "total_selects_and_watched": 0,
                "total_browsed": 3,
            },
        },
    }
    expected_v1 = {
        "version": 1,
        "data": {
            "up_to_4_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 2,
                },
                "rest_pos": {
                    "total_selects": 2,
                    "total_selects_and_watched": 0,
                    "total_browsed": 2,
                },
            },
            "all_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 4,
                },
                "rest_pos": {
                    "total_selects": 2,
                    "total_selects_and_watched": 0,
                    "total_browsed": 3,
                },
            },
        },
    }
    expected_v1_msg = features_pb2_v1.StreamPSelect()
    ProtoParseDict(js_dict=expected_v1, message=expected_v1_msg)
    serializer = SerializerRegistry[("STREAM", "PSELECT#24H", "v0")]
    actual = serializer.deserialize(stream_pselect_v0)
    assert expected_v1_msg == actual, "PSelect deserialization failed!"

    stream_similarities_v0 = {"cat1": 0.5, "cat2": 0.3, "cat3": 0.7, "cat4": -0.3}
    expected_v1_msg = features_pb2_v1.StreamSimilarityScores()
    ProtoParseDict(
        js_dict={
            "version": 1,
            "data": {"cat1": 0.5, "cat2": 0.3, "cat3": 0.7, "cat4": -0.3},
        },
        message=expected_v1_msg,
    )
    serializer = SerializerRegistry[("STREAM", "SIMILARITY", "v0")]
    actual = serializer.deserialize(stream_similarities_v0)
    assert expected_v1_msg == actual, "Similarity scores deserialization failed!"


def test_user_bias_serializers():
    raw_pwatched_value = {
        "version": 1,
        "data": {
            "autoplay": {"attempts": 1, "watched": 1},
            "choose_next": {"attempts": 5, "watched": 2},
            "sel_thumb": {"attempts": 2, "watched": 0},
        },
    }
    serializer = SerializerRegistry[("USER", "PWATCHED#6M", "v1")]
    actual = serializer.serialize(raw_pwatched_value)
    expected_msg = features_pb2_v1.UserPWatched()
    expected = ProtoParseDict(
        js_dict=raw_pwatched_value, message=expected_msg
    ).SerializeToString()
    assert actual == expected, (
        "User pwatched serialization does not match expected value."
    )

    raw_pselect_value = {
        "version": 1,
        "data": {
            "all_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 2,
                }
            },
            "up_to_4_browsed": {
                "first_pos": {
                    "total_selects": 0,
                    "total_selects_and_watched": 0,
                    "total_browsed": 1,
                }
            },
        },
    }
    serializer = SerializerRegistry[("USER", "PSELECT#6M", "v1")]
    actual = serializer.serialize(raw_pselect_value)
    expected_msg = features_pb2_v1.UserPSelect()
    expected = ProtoParseDict(
        js_dict=raw_pselect_value, message=expected_msg
    ).SerializeToString()
    assert actual == expected, (
        "User pselect serialization does not match expected value."
    )
    return
