from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

from ..core.exceptions import ValidationError


class FrameExtractor(BaseModel):
    url: str = Field(..., description="视频 URL 链接")


class FrameExtractorByKeyFrameRequest(FrameExtractor):
    def to_api_request(self) -> dict:
        return {"url": self.url}


class FrameExtractorByIntervalRequest(FrameExtractor):
    interval_ms: int = Field(..., description="间隔抽帧时间，单位: ms")

    def to_api_request(self) -> dict:
        return {"url": self.url, "interval_ms": self.interval_ms}


class FrameExtractorByInterval(FrameExtractor):
    count: int = Field(..., description="抽取多少个帧")

    def to_api_request(self) -> dict:
        return {"url": self.url, "count": self.count}


class FrameChunk(BaseModel):
    index: int = Field(..., description="抽帧结果索引")
    screenshot: str = Field(..., description="抽帧结果 URL 链接")
    timestamp_ms: int = Field(..., description="抽帧在视频中的相对时间，单位: ms")


class FrameExtractorData(BaseModel):
    chunks: List[FrameChunk] = Field(..., description="抽帧结果列表")


class FrameExtractorResponse(BaseModel):
    code: int = Field(..., description="状态码")
    msg: str = Field(..., description="状态描述")
    log_id: str = Field(..., description="日志 ID")
    data: FrameExtractorData = Field(..., description="抽帧返回结果")


class FontPosConfig(BaseModel):
    height: Optional[str] = Field(default="10%", description="字幕显示高度，支持设置为百分比（相对于视频高度）或具体像素值")
    pos_x: Optional[str] = Field(default="0", description="字幕在水平方向（X 轴）的位置，以视频正上方居中位置为原点，单位：像素。例如值为 0 时，表示字幕在水平位置居中；值为 - 100 时，表示字幕向左移动 100 像素；值为 100 时，表示字幕向右移动 100 像素。")
    pos_y: Optional[str] = Field(default="90%", description="字幕在垂直方向（Y 轴）的位置，以视频正上方居中位置为原点，单位：像素。例如值为 0 时，表示字幕在视频顶部；值为 100 时，表示字幕向下移动 100 像素。")
    width: Optional[str] = Field(default="100%", description="字幕显示宽度，支持设置为百分比（相对于视频宽度）或具体像素值")


class SubtitleConfig(BaseModel):
    background_border_width: Optional[int] = Field(default=0, description="字幕背景边框大小。默认值为 0")
    font_type: Optional[str] = Field(default="1525745", description="字幕字体设置, 默认值方正雅宋")
    border_width: Optional[int] = Field(default=None, description="描边宽度")
    font_color: Optional[str] = Field(default="#FFFFFFFF", description="字幕字体颜色，默认为白色")
    font_pos_config: FontPosConfig = Field(..., description="字幕位置设置")
    font_size: Optional[int] = Field(default=36, description="字幕字体大小")
    background_color: Optional[str] = Field(default="#00000000", description="字幕背景颜色，默认为无色")
    border_color: Optional[str] = Field(default=None, description="描边颜色")


class TextItem(BaseModel):
    end_time: float = Field(..., description="文本结束时间，单位s")
    start_time: float = Field(..., description="文本开始时间，单位s")
    text: str = Field(..., description="输入文本")


class AddSubtitlesRequest(BaseModel):
    video: str = Field(..., description="视频输入地址")
    subtitle_config: SubtitleConfig = Field(..., description="字幕描述")
    subtitle_url: Optional[str] = Field(default=None, description="字幕地址")
    text_list: Optional[List[TextItem]] = Field(default=None, description="文本序列")
    url_expire: Optional[int] = Field(default=86400, description="产物地址有效时间，单位秒，默认一天，最大30天")

    @field_validator('url_expire')
    @classmethod
    def validate_url_expire(cls, v: Optional[int]) -> int:
        if v is None:
            return 86400
        if v < 1 or v > 2592000:
            raise ValidationError(
                "url_expire 必须在 [1, 2592000] 范围内（最大30天）",
                field="url_expire",
                value=v
            )
        return v

    def to_api_request(self) -> dict:
        request_data = {
            "video": self.video,
            "subtitle_config": {
                "background_border_width": self.subtitle_config.background_border_width,
                "font_type": self.subtitle_config.font_type,
                "font_pos_config": {
                    "height": self.subtitle_config.font_pos_config.height,
                    "pos_x": self.subtitle_config.font_pos_config.pos_x,
                    "pos_y": self.subtitle_config.font_pos_config.pos_y,
                    "width": self.subtitle_config.font_pos_config.width,
                }
            },
            "url_expire": self.url_expire,
        }

        if self.subtitle_config.border_width is not None:
            request_data["subtitle_config"]["border_width"] = self.subtitle_config.border_width
        if self.subtitle_config.font_color is not None:
            request_data["subtitle_config"]["font_color"] = self.subtitle_config.font_color
        if self.subtitle_config.font_size is not None:
            request_data["subtitle_config"]["font_size"] = self.subtitle_config.font_size
        if self.subtitle_config.background_color is not None:
            request_data["subtitle_config"]["background_color"] = self.subtitle_config.background_color
        if self.subtitle_config.border_color is not None:
            request_data["subtitle_config"]["border_color"] = self.subtitle_config.border_color

        if self.subtitle_url is not None:
            request_data["subtitle_url"] = self.subtitle_url

        if self.text_list is not None:
            request_data["text_list"] = [
                {
                    "end_time": item.end_time,
                    "start_time": item.start_time,
                    "text": item.text,
                }
                for item in self.text_list
            ]

        return request_data


class ConcatVideosRequest(BaseModel):
    videos: List[str] = Field(..., description="视频列表，每个元素为视频 URL 地址")
    transitions: Optional[List[str]] = Field(default=None,
                                             description="转场ID列表，已支持转场见官网文档（本插件只支持非交叠转场）")
    url_expire: Optional[int] = Field(default=86400, description="产物有效时间，单位秒，默认一天，最长30天")

    @field_validator('url_expire')
    @classmethod
    def validate_url_expire(cls, v: Optional[int]) -> int:
        if v is None:
            return 86400
        if v < 1 or v > 2592000:
            raise ValidationError(
                "url_expire 必须在 [1, 2592000] 范围内（最大30天）",
                field="url_expire",
                value=v
            )
        return v

    @field_validator('videos')
    @classmethod
    def validate_videos(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValidationError(
                "videos 列表不能为空",
                field="videos",
                value=v
            )
        return v

    def to_api_request(self) -> dict:
        request_data = {
            "videos": self.videos,
            "url_expire": self.url_expire,
        }

        if self.transitions is not None and len(self.transitions) > 0:
            request_data["transitions"] = self.transitions

        return request_data


class OutputSync(BaseModel):
    sync_method: Optional[Literal["speed", "trim"]] = Field(default="trim",
                                                            description="对齐方式，裁剪 or 倍速，参数取值范围是 'speed'、'trim'，默认值 trim")
    sync_mode: Optional[Literal["video", "audio"]] = Field(default="video",
                                                           description="输出基准，音频 or 视频，参数取值范围是 'video'、'audio'，默认值 video")


class CompileVideoAudioRequest(BaseModel):
    video: str = Field(..., description="输入视频 URL")
    audio: str = Field(..., description="输入音频 URL")
    is_video_audio_sync: Optional[bool] = Field(default=False,
                                                description="是否执行音频视频对齐，默认保持原样输出，不做音视频对齐")
    output_sync: Optional[OutputSync] = Field(default=None, description="输出模式，与 is_video_audio_sync 配合使用")
    is_audio_reserve: Optional[bool] = Field(default=False, description="是否保留原视频流中的音频")
    url_expire: Optional[int] = Field(default=86400, description="产物有效时间，单位秒，默认一天，最大30天")

    @field_validator('url_expire')
    @classmethod
    def validate_url_expire(cls, v: Optional[int]) -> int:
        if v is None:
            return 86400
        if v < 1 or v > 2592000:
            raise ValidationError(
                "url_expire 必须在 [1, 2592000] 范围内（最大30天）",
                field="url_expire",
                value=v
            )
        return v

    def to_api_request(self) -> dict:
        request_data = {
            "video": self.video,
            "audio": self.audio,
            "url_expire": self.url_expire,
        }

        if self.is_video_audio_sync is not None:
            request_data["is_video_audio_sync"] = self.is_video_audio_sync

        if self.output_sync is not None:
            request_data["output_sync"] = {
                "sync_method": self.output_sync.sync_method,
                "sync_mode": self.output_sync.sync_mode,
            }

        if self.is_audio_reserve is not None:
            request_data["is_audio_reserve"] = self.is_audio_reserve

        return request_data


class AudioToSubtitleRequest(BaseModel):
    source: str = Field(..., description="输入视频 URL")
    subtitle_type: Optional[Literal["webvtt", "srt"]] = Field(default="srt",
                                                              description="字幕类型，可选值 [webvtt, srt]")
    url_expire: Optional[int] = Field(default=86400, description="产物超时时间，单位秒，默认一天，最长30天")

    @field_validator('url_expire')
    @classmethod
    def validate_url_expire(cls, v: Optional[int]) -> int:
        if v is None:
            return 86400
        if v < 1 or v > 2592000:
            raise ValidationError(
                "url_expire 必须在 [1, 2592000] 范围内（最大30天）",
                field="url_expire",
                value=v
            )
        return v

    def to_api_request(self) -> dict:
        request_data = {
            "source": self.source,
            "url_expire": self.url_expire,
        }

        if self.subtitle_type is not None:
            request_data["subtitle_type"] = self.subtitle_type

        return request_data


class AudioExtractRequest(BaseModel):
    video: str = Field(..., description="输入视频 URL")
    format: Optional[Literal["m4a", "mp3"]] = Field(default="m4a", description="输出格式，默认 m4a，可选值 [m4a, mp3]")
    url_expire: Optional[int] = Field(default=86400, description="产物有效时间，单位秒，默认一天，最大30天，最小1小时")

    @field_validator('url_expire')
    @classmethod
    def validate_url_expire(cls, v: Optional[int]) -> int:
        if v is None:
            return 86400
        if v < 3600 or v > 2592000:
            raise ValidationError(
                "url_expire 必须在 [3600, 2592000] 范围内（最小1小时，最大30天）",
                field="url_expire",
                value=v
            )
        return v

    def to_api_request(self) -> dict:
        request_data = {
            "video": self.video,
            "url_expire": self.url_expire,
        }

        if self.format is not None:
            request_data["format"] = self.format

        return request_data


class VideoTrimRequest(BaseModel):
    video: str = Field(..., description="视频输入地址")
    start_time: Optional[float] = Field(default=0, description="裁剪开始时间，单位：秒，默认为0")
    end_time: Optional[float] = Field(default=None, description="裁剪结束时间，单位：秒；默认为片源结尾")
    url_expire: Optional[int] = Field(default=86400, description="产物有效时间，单位为秒，默认一天，最大30天")

    @field_validator('url_expire')
    @classmethod
    def validate_url_expire(cls, v: Optional[int]) -> int:
        if v is None:
            return 86400
        if v < 1 or v > 2592000:
            raise ValidationError(
                "url_expire 必须在 [1, 2592000] 范围内（最大30天）",
                field="url_expire",
                value=v
            )
        return v

    @field_validator('start_time')
    @classmethod
    def validate_start_time(cls, v: Optional[float]) -> float:
        if v is None:
            return 0
        if v < 0:
            raise ValidationError(
                "start_time 必须大于等于 0",
                field="start_time",
                value=v
            )
        return v

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValidationError(
                "end_time 必须大于等于 0",
                field="end_time",
                value=v
            )
        return v

    def to_api_request(self) -> dict:
        request_data = {
            "video": self.video,
            "url_expire": self.url_expire,
        }

        if self.start_time is not None:
            request_data["start_time"] = self.start_time

        if self.end_time is not None:
            request_data["end_time"] = self.end_time

        return request_data


class VideoMeta(BaseModel):
    duration: float = Field(..., description="音视频时长，单位s")
    resolution: str = Field(..., description="视频分辨率，若为音频则为 'unknown'")
    type: str = Field(..., description="输出结果的类型，[video, audio]")


class BillInfo(BaseModel):
    duration: float = Field(..., description="处理的音视频时长，单位s")
    ratio: float = Field(..., description="计费的抵扣系数")


class VideoEditResponse(BaseModel):
    req_id: str = Field(..., description="请求 ID")
    url: str = Field(..., description="处理后的视频/字幕/音频 URL。URL 有效期为 1 ~ 30 天，由输入参数 url_expire 决定。")
    message: Optional[str] = Field(default=None, description="执行插件时的状态描述或错误提示信息")
    video_meta: Optional[VideoMeta] = Field(default=None, description="视频/音频元数据")
    bill_info: Optional[BillInfo] = Field(default=None, description="计费参考信息")
