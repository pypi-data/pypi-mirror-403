from collections import deque
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.frames.frames import (
    InputAudioRawFrame,
    LLMContextFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)


class AudioContextAggregator(FrameProcessor):
    def __init__(
        self, context: LLMContext, *, start_secs: float = 0.2, text: str | None = None
    ):
        super().__init__()
        self._context = context
        self._audio_frames = deque()
        self._audio_duration = 0
        self._start_secs = start_secs
        self._is_user_speaking = False
        self._text = text

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, UserStartedSpeakingFrame):
            self._is_user_speaking = True
        elif isinstance(frame, UserStoppedSpeakingFrame):
            self._is_user_speaking = False

            message = await self._context.create_audio_message(
                audio_frames=self._audio_frames, text=self._text or ""
            )

            if self._text is None:
                assert message["content"][0]["type"] == "text"
                del message["content"][0]

            self._context.add_message(message)

            await self.push_frame(LLMContextFrame(context=self._context))
        elif isinstance(frame, InputAudioRawFrame):
            self._audio_frames.append(frame)
            self._audio_duration += self._get_duration(frame)

            if not self._is_user_speaking:
                while self._audio_duration > self._start_secs:
                    popped_frame = self._audio_frames.popleft()
                    self._audio_duration -= self._get_duration(popped_frame)

        await self.push_frame(frame, direction)

    @staticmethod
    def _get_duration(frame: InputAudioRawFrame) -> float:
        return len(frame.audio) / 16 * frame.num_channels / frame.sample_rate
