if __package__ or "." in __name__:
    from . import Vc6Utils
    from . import codec
else:
    import Vc6Utils
    import codec

from pathlib import Path
import json

class VideoReader:
    def __init__(self, video_path : str):
        self._reader = Vc6Utils.vc6_il_util_video_reader_create(video_path)

    def __del__(self):
        if self._reader is not None:
            Vc6Utils.vc6_il_util_vr_destroy(self._reader)


    @property
    def size(self): return Vc6Utils.vc6_il_util_vr_get_frame_size(self._reader)
    @property
    def frame_count(self): return Vc6Utils.vc6_il_util_vr_get_length(self._reader)
    @property
    def fps(self): return Vc6Utils.vc6_il_util_vr_get_rate(self._reader)
    @property
    def version(self): return Vc6Utils.vc6_il_util_vr_get_frame_version(self._reader)

    def tell(self): return Vc6Utils.vc6_il_util_vr_get_position(self._reader)
    def seek(self, idx: int): return Vc6Utils.vc6_il_util_vr_set_position(self._reader, idx)
    def seek_relative(self, delta:int): return Vc6Utils.vc6_il_util_vr_set_position_relative(self._reader, delta)
    def eof(self): return Vc6Utils.vc6_il_util_vr_is_eof(self._reader)

    def frame_size(self, echelon_idx: int | None = None):
        if echelon_idx is None:
            return Vc6Utils.vc6_il_util_vr_get_frame_size(self._reader)
        return Vc6Utils.vc6_il_util_vr_get_frame_size_echelon(self._reader, echelon_idx)

    def read(self, echelon_idx: int | None = None) -> bytearray:
        size = self.frame_size(echelon_idx)
        if size <= 0:
            print("invalid frame size")
            return bytearray()
        buffer = bytearray(size)

        if echelon_idx is None:
            ok = Vc6Utils.vc6_il_util_vr_read(self._reader, buffer)
        else:
            ok = Vc6Utils.vc6_il_util_vr_read_echelon(self._reader, buffer, echelon_idx)
        if ok:
            return buffer
        else:
            print("failed to read");
            return bytearray()

    def readinto(self, buffer: "bytes | bytearray | memoryview", echelon_idx: int | None = None):
        if buffer is None:
            print("invalid buffer")
            return
        else:
            if echelon_idx is None:
                ok = Vc6Utils.vc6_il_util_vr_read(self._reader, buffer)
            else:
                ok = Vc6Utils.vc6_il_util_vr_read_echelon(self._reader, buffer, echelon_idx)
            if not ok:
                print("failed to read");
                return

class VideoWriter:
    def __init__(self, video_path : str, format : codec.PictureFormat, width: int, height: int, target_bitdepth:int , fps:int, fps_den:int = 1):
        path = Path(video_path)
        self._writer = None
        if path.suffix == ".mxf":
            self._writer = Vc6Utils.vc6_il_util_video_writer_create_mxf(str(path), format.value, width, height, target_bitdepth, fps, fps_den)
        elif path.suffix == ".vc6":
            self._writer = Vc6Utils.vc6_il_util_video_writer_create_generic(str(path))
        else: 
            print("invalid extension")

    def __del__(self):
        Vc6Utils.vc6_il_util_video_writer_destroy(self._writer)

    def _build_metadata_json(self, input_buffer: "bytes | bytearray | memoryview") -> str:
        probe = codec.ProbeFrame(input_buffer)
        echelons = []
        echelon_width = probe.width
        echelon_height = probe.height
        for echelon in range(probe.num_echelons):
            required_size = codec.GetRequiredSizeForTargetEchelon(input_buffer, echelon)
            echelons.append({
                "echelon": int(echelon),
                "required_size_bytes": int(required_size),
                "width": int(echelon_width),
                "height": int(echelon_height),
            })
            echelon_width = (echelon_width + 1) // 2
            echelon_height = (echelon_height + 1) // 2
        return json.dumps({"version": 1, "echelons": echelons})

    def write_frame(self, input_buffer: "bytes | bytearray | memoryview") -> bool:
        metadata = self._build_metadata_json(input_buffer)
        return Vc6Utils.vc6_il_util_video_writer_write_frame_with_metadata(self._writer, input_buffer, metadata)

    def finalize(self) -> bool:
        return Vc6Utils.vc6_il_util_video_writer_finalise(self._writer);
