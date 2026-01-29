from .generated.v1 import features_pb2 as features_pb2_v1
from google.protobuf.message import Message
from google.protobuf.json_format import ParseDict as ProtoParseDict
import typing as _t
from abc import ABC, abstractmethod

MessageType = _t.TypeVar("MessageType", bound=Message)


class Serializer(ABC):
    @abstractmethod
    def serialize(self, value) -> bytes: ...

    @abstractmethod
    def deserialize(self, value: bytes) -> _t.Any: ...


class SimpleSerializer(Serializer, _t.Generic[MessageType]):
    """This simple serializer uses the function `ParseDict` provided by google
    to parse dictionaries. While it allows for simple code, it's very slow to run.
    This class should be used directly for PoCs only, production serializers should have
    custom implementations where fields are set directly. Early tests show that
    manual serialization can provide 10x speedup.

    Deserialization is fine since it deserializes from the binary into the message
    itself, it doesn't need to create a dictionary."""

    def __init__(self, msg_class: type[MessageType]):
        self.msg_class = msg_class
        return

    def serialize(self, value) -> bytes:
        msg = self.msg_class()
        return ProtoParseDict(value, message=msg).SerializeToString()

    def deserialize(self, value) -> MessageType:
        msg: Message = self.msg_class()
        msg.ParseFromString(value)
        return msg


class StreamPWatchedSerializerV1(SimpleSerializer):
    def __init__(self):
        super().__init__(msg_class=features_pb2_v1.StreamPWatched)

    def serialize(self, value):
        root_msg = self.build_msg(value)
        return root_msg.SerializeToString()

    def build_msg(self, value) -> features_pb2_v1.StreamPWatched:
        message = self.msg_class()
        assert value["version"] == 1, "Wrong version given!"
        message.version = value["version"]
        for entry_context, counts in value["data"].items():
            entry_context_msg: features_pb2_v1.EntryContextCounts = getattr(
                message.data, entry_context
            )
            entry_context_msg.attempts = int(counts["attempts"])
            entry_context_msg.watched = int(counts["watched"])
        return message


UserPWatchedSerializerV1 = StreamPWatchedSerializerV1


class StreamPWatchedSerializerV0(Serializer):
    serializer_v1 = StreamPWatchedSerializerV1()

    def serialize(self, value) -> bytes:
        raise NotImplementedError(
            "This serializer should never be used for serialization!"
        )

    def deserialize(self, value) -> features_pb2_v1.StreamPWatched:
        value = {
            "data": {
                entry_context.replace(" ", "_"): counts
                for entry_context, counts in value.items()
            },
            "version": 1,
        }
        return self.serializer_v1.build_msg(value)


class StreamPSelectSerializerV1(SimpleSerializer):
    def __init__(self):
        super().__init__(msg_class=features_pb2_v1.StreamPSelect)
        return

    def serialize(self, value) -> bytes:
        root_msg = self.build_msg(value)
        return root_msg.SerializeToString()

    def build_msg(self, value) -> features_pb2_v1.StreamPSelect:
        message: features_pb2_v1.StreamPSelect = self.msg_class()
        assert value["version"] == 1, "Wrong version given!"
        message.version = 1
        data = value["data"]
        for (
            browsed_debias_key,
            position_pselects,
        ) in data.items():
            position_pselects_msg: features_pb2_v1.PositionPSelect = getattr(
                message.data, browsed_debias_key
            )
            for position, select_counts in position_pselects.items():
                select_counts_msg = getattr(position_pselects_msg, position)
                select_counts_msg.total_selects = int(select_counts["total_selects"])
                select_counts_msg.total_browsed = int(select_counts["total_browsed"])
                select_counts_msg.total_selects_and_watched = int(
                    select_counts["total_selects_and_watched"]
                )
        return message


UserPSelectSerializerV1 = StreamPSelectSerializerV1


class StreamPSelectSerializerV0(Serializer):
    serializer_v1 = StreamPSelectSerializerV1()

    def serialize(self, value) -> bytes:
        raise NotImplementedError(
            "This serializer should never be used for serialization!"
        )

    def deserialize(self, value):
        key_mapping = {
            "0": "first_pos",
            "1": "second_pos",
            "2": "third_pos",
            "3+": "rest_pos",
        }
        for browsed_debiasing in value.keys():
            for old_key, new_key in key_mapping.items():
                if old_key not in value[browsed_debiasing]:
                    continue
                value[browsed_debiasing][new_key] = value[browsed_debiasing].pop(
                    old_key
                )
        out = {
            "data": {
                "up_to_4_browsed": value["4_browsed"],
                "all_browsed": value["all_browsed"],
            },
            "version": 1,
        }
        msg = self.serializer_v1.build_msg(value=out)
        return msg


class StreamSimilaritySerializerV1(SimpleSerializer):
    def __init__(self):
        super().__init__(msg_class=features_pb2_v1.StreamSimilarityScores)

    def serialize(self, value):
        msg = self.build_msg(value)
        return msg.SerializeToString()

    def build_msg(self, value) -> features_pb2_v1.StreamSimilarityScores:
        message = self.msg_class()
        assert value["version"] == 1, "Wrong version given!"
        message.version = value["version"]
        for key, score in value["data"].items():
            message.data[key] = score
        return message


class StreamSimilaritySerializerV0(Serializer):
    serializer_v1 = StreamSimilaritySerializerV1()

    def serialize(self, value):
        raise NotImplementedError(
            "This serializer should never be used for serialization!"
        )

    def deserialize(self, value):
        value = {"data": value, "version": 1}
        msg = self.serializer_v1.build_msg(value)
        return msg


class UserPersonalizingPWatchedSerializerV1(SimpleSerializer):
    def __init__(self):
        super().__init__(msg_class=features_pb2_v1.UserPersonalizingPWatched)

    def serialize(self, value: dict) -> bytes:
        root_msg = self.build_msg(value)
        return root_msg.SerializeToString()

    def build_msg(self, value) -> features_pb2_v1.UserPersonalizingPWatched:
        root_msg = features_pb2_v1.UserPersonalizingPWatched()
        assert value["version"] == 1, "Wrong version given!"
        root_msg.version = value["version"]
        data = value["data"]
        for personalizing_key, entry_context_pwatched in data.items():
            personalizing_msg = root_msg.data[personalizing_key]
            for entry_context, counts in entry_context_pwatched.items():
                entry_context_msg = getattr(personalizing_msg, entry_context)
                entry_context_msg.attempts = int(counts["attempts"])
                entry_context_msg.watched = int(counts["watched"])
        return root_msg


class UserPersonalizingPSelectSerializerV1(SimpleSerializer):
    def __init__(self):
        super().__init__(msg_class=features_pb2_v1.UserPersonalizingPSelect)

    def serialize(self, value):
        root_msg = features_pb2_v1.UserPersonalizingPSelect()
        root_msg.version = value["version"]
        data = value["data"]
        for personalizing_key, browsed_debiased_pselecs in data.items():
            personalizing_msg = root_msg.data[personalizing_key]
            for (
                browsed_debias_key,
                position_pselects,
            ) in browsed_debiased_pselecs.items():
                position_pselects_msg = getattr(personalizing_msg, browsed_debias_key)
                for position, select_counts in position_pselects.items():
                    select_counts_msg = getattr(position_pselects_msg, position)
                    select_counts_msg.total_selects = int(
                        select_counts["total_selects"]
                    )
                    select_counts_msg.total_browsed = int(
                        select_counts["total_browsed"]
                    )
                    select_counts_msg.total_selects_and_watched = int(
                        select_counts["total_selects_and_watched"]
                    )
        return root_msg.SerializeToString()


class PassThroughSerializer(Serializer):
    def serialize(self, value):
        return value

    def deserialize(self, value):
        return value


user_personalizing_pwatched_serializer_v1 = UserPersonalizingPWatchedSerializerV1()
user_pwatched_serializer_v1 = UserPWatchedSerializerV1()
user_personalizing_pselect_serializer_v1 = UserPersonalizingPSelectSerializerV1()
user_pselect_serializer_v1 = UserPSelectSerializerV1()
stream_pwatched_serializer_v0 = StreamPWatchedSerializerV0()
stream_pwatched_serializer_v1 = StreamPWatchedSerializerV1()
stream_pselect_serializer_v0 = StreamPSelectSerializerV0()
stream_pselect_serializer_v1 = StreamPSelectSerializerV1()
stream_similarity_scores_serializer_v0 = StreamSimilaritySerializerV0()
stream_similarity_scores_serializer_v1 = StreamSimilaritySerializerV1()


class FeatureRegistryId(_t.NamedTuple):
    entity_type: _t.Literal["STREAM", "USER"]
    feature_id: str
    version: str


stream_pwatched_v0_features: list[FeatureRegistryId] = [
    FeatureRegistryId(entity_type="STREAM", feature_id="PWATCHED#24H", version="v0"),
    FeatureRegistryId(entity_type="STREAM", feature_id="PWATCHED#24H#TV", version="v0"),
    FeatureRegistryId(
        entity_type="STREAM", feature_id="PWATCHED#24H#MOBILE", version="v0"
    ),
]

stream_pwatched_v1_features: list[FeatureRegistryId] = [
    FeatureRegistryId(entity_type="STREAM", feature_id="PWATCHED#24H", version="v1"),
    FeatureRegistryId(entity_type="STREAM", feature_id="PWATCHED#24H#TV", version="v1"),
    FeatureRegistryId(
        entity_type="STREAM", feature_id="PWATCHED#24H#MOBILE", version="v1"
    ),
]

stream_pselect_v0_features: list[FeatureRegistryId] = [
    FeatureRegistryId(entity_type="STREAM", feature_id="PSELECT#24H", version="v0"),
    FeatureRegistryId(
        entity_type="STREAM", feature_id="PSELECT#24H#MOBILE", version="v0"
    ),
    FeatureRegistryId(entity_type="STREAM", feature_id="PSELECT#24H#TV", version="v0"),
]

stream_pselect_v1_features: list[FeatureRegistryId] = [
    FeatureRegistryId(entity_type="STREAM", feature_id="PSELECT#24H", version="v1"),
    FeatureRegistryId(
        entity_type="STREAM", feature_id="PSELECT#24H#MOBILE", version="v1"
    ),
    FeatureRegistryId(entity_type="STREAM", feature_id="PSELECT#24H#TV", version="v1"),
]

stream_similarity_v0_features: list[FeatureRegistryId] = [
    FeatureRegistryId(entity_type="STREAM", feature_id="SIMILARITY", version="v0"),
    FeatureRegistryId(
        entity_type="STREAM", feature_id="SIMILARITY#WEATHER_ALERT", version="v0"
    ),
]

stream_similarity_v1_features: list[FeatureRegistryId] = [
    FeatureRegistryId(
        entity_type="STREAM", feature_id="SIMILARITY#GEMINI", version="v1"
    ),
    FeatureRegistryId(
        entity_type="STREAM", feature_id="SIMILARITY#WEATHER_ALERT", version="v1"
    ),
]

user_personalizing_pwatched_v1_features: list[FeatureRegistryId] = [
    FeatureRegistryId(
        entity_type="USER", feature_id="PWATCHED#6M#CATEGORY", version="v1"
    ),
    FeatureRegistryId(
        entity_type="USER",
        feature_id="PWATCHED#6M#AUTHOR_SHOW",
        version="v1",
    ),
    FeatureRegistryId(
        entity_type="USER",
        feature_id="PWATCHED#6M#GEMINI_CATEGORY",
        version="v1",
    ),
]

user_personalizing_pselect_v1_features: list[FeatureRegistryId] = [
    FeatureRegistryId(
        entity_type="USER", feature_id="PSELECT#6M#CATEGORY", version="v1"
    ),
    FeatureRegistryId(
        entity_type="USER", feature_id="PSELECT#6M#AUTHOR_SHOW", version="v1"
    ),
    FeatureRegistryId(
        entity_type="USER", feature_id="PSELECT#6M#GEMINI_CATEGORY", version="v1"
    ),
]

user_bias_pwatched_v1_features: list[FeatureRegistryId] = [
    FeatureRegistryId(entity_type="USER", feature_id="PWATCHED#6M", version="v1")
]

user_bias_pselect_v1_features: list[FeatureRegistryId] = [
    FeatureRegistryId(entity_type="USER", feature_id="PSELECT#6M", version="v1")
]

features_serializer_tuples: list[tuple[list[FeatureRegistryId], Serializer]] = [
    (stream_pwatched_v0_features, stream_pwatched_serializer_v0),
    (stream_pwatched_v1_features, stream_pwatched_serializer_v1),
    (stream_pselect_v0_features, stream_pselect_serializer_v0),
    (stream_pselect_v1_features, stream_pselect_serializer_v1),
    (stream_similarity_v0_features, stream_similarity_scores_serializer_v0),
    (stream_similarity_v1_features, stream_similarity_scores_serializer_v1),
    (
        user_personalizing_pwatched_v1_features,
        user_personalizing_pwatched_serializer_v1,
    ),
    (user_bias_pwatched_v1_features, user_pwatched_serializer_v1),
    (user_personalizing_pselect_v1_features, user_personalizing_pselect_serializer_v1),
    (user_bias_pselect_v1_features, user_pselect_serializer_v1),
]

SerializerRegistry: dict[FeatureRegistryId, Serializer] = {
    FeatureRegistryId(
        entity_type="PASS_THROUGH", feature_id="PASS_THROUGH", version="v1"
    ): PassThroughSerializer()
}

for feature_ids, serializer in features_serializer_tuples:
    for feature_id in feature_ids:
        SerializerRegistry[feature_id] = serializer
