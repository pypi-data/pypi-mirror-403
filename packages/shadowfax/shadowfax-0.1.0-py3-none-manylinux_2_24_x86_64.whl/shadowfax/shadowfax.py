import ctypes 
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
from pathlib import Path

WINDOW_SIZE = 16384

class Context(ctypes.Structure):
    pass

class Flagstat(ctypes.Structure):
    _fields_ = [
        ('n_reads', ctypes.c_uint64),
        ('n_mapped', ctypes.c_uint64),
        ('n_pair_all', ctypes.c_uint64),
        ('n_pair_map', ctypes.c_uint64),
        ('n_pair_good', ctypes.c_uint64),
        ('n_sgltn', ctypes.c_uint64),
        ('n_read1', ctypes.c_uint64),
        ('n_read2', ctypes.c_uint64),
        ('n_dup', ctypes.c_uint64),
        ('n_diffchr', ctypes.c_uint64),
        ('n_diffhigh', ctypes.c_uint64),
        ('n_secondary', ctypes.c_uint64),
        ('n_supp', ctypes.c_uint64),
        ('n_primary', ctypes.c_uint64),
        ('n_pmapped', ctypes.c_uint64),
        ('n_pdup', ctypes.c_uint64),
    ]

class FlagstatStream(ctypes.Structure):
    pass

class PileupStreamC(ctypes.Structure):
    pass

class DepthStream(ctypes.Structure):
    pass

class _PileupBatchC(ctypes.Structure):
    _fields_ = [
        ('n_windows', ctypes.c_uint64),
        ('start_pos', ctypes.c_uint64),
        ('end_pos', ctypes.c_uint64),
        ('ref_id', ctypes.c_uint32),
        ('data', ctypes.c_void_p),
    ]

    def to_dict(self):
        return ctypes_to_dict(self)


class PileupBatch:
    __slots__ = ("_stream", "_ptr")

    def __init__(self, stream, ptr):
        self._stream = stream
        self._ptr = ptr

    def __del__(self):
        stream = getattr(self, "_stream", None)
        ptr = getattr(self, "_ptr", None)
        if stream is None or ptr is None:
            return
        lib.shadowfax_pileup_stream_batch_destroy(stream, ptr)

    def __getattr__(self, name):
        return getattr(self._ptr.contents, name)

    @property
    def has_data(self):
        return bool(self._ptr.contents.data)

class DepthBatch(ctypes.Structure):
    pass

class DepthBatchData(ctypes.Structure):
    _fields_ = [
        ('buffer', ctypes.POINTER(ctypes.c_uint32)),
        ('n_regions', ctypes.c_uint64),
    ]

    def to_buffer(self):
        array_type = ctypes.c_uint32 * self.n_regions * WINDOW_SIZE
        c_array = ctypes.cast(self.buffer, ctypes.POINTER(array_type)).contents
        return c_array


class _VariantC(ctypes.Structure):
    _fields_ = [
        ("pos", ctypes.c_uint32),
        ("ref", ctypes.c_char),
        ("alt", ctypes.c_char),
        ("_alignment_padding", ctypes.c_char * 2),
    ]


class _BaseCountsC(ctypes.Structure):
    _fields_ = [
        ("a_count", ctypes.c_uint32),
        ("c_count", ctypes.c_uint32),
        ("g_count", ctypes.c_uint32),
        ("t_count", ctypes.c_uint32),
    ]


class BaseCounts:
    __slots__ = ("a_count", "c_count", "g_count", "t_count")

    def __init__(self, a_count=0, c_count=0, g_count=0, t_count=0):
        self.a_count = a_count
        self.c_count = c_count
        self.g_count = g_count
        self.t_count = t_count

    def to_dict(self):
        return {
            "a_count": self.a_count,
            "c_count": self.c_count,
            "g_count": self.g_count,
            "t_count": self.t_count,
        }


class BamFlagstat(ctypes.Structure):
    _fields_ = [
        ('passed', Flagstat),
        ('failed', Flagstat),
    ]

    def to_dict(self):
        return ctypes_to_dict(self)

class FlagstatBatch(ctypes.Structure):
    _fields_ = [
        ('data', BamFlagstat),
        ('bytes_processed', ctypes.c_uint64),
        ('total_bytes', ctypes.c_uint64),
    ]

    def to_dict(self):
        return ctypes_to_dict(self)

def ctypes_to_dict(obj):
    result = {}
    for field, _ in obj._fields_:
        value = getattr(obj, field)
        if isinstance(value, ctypes.Structure):
            result[field] = ctypes_to_dict(value)
        else:
            result[field] = value
    return result

lib_path = Path(__file__).resolve().parent / '_native' / 'linux_x86_64' / 'libshadowfax.so'

#lib = ctypes.cdll.LoadLibrary('./shadowfax/lib/libshadowfax.so')
lib = ctypes.cdll.LoadLibrary(str(lib_path))

lib.shadowfax_context_create.restype = ctypes.POINTER(Context)


lib.shadowfax_flagstat_stream_create.argtypes = [
    ctypes.c_char_p,          # bam_path
    ctypes.c_uint64,          # input_batch_size
    ctypes.c_uint64,          # data_limit
]
lib.shadowfax_flagstat_stream_create.restype = ctypes.POINTER(FlagstatStream)

lib.shadowfax_flagstat_stream_next.argtypes = [
    ctypes.POINTER(FlagstatStream),
    ctypes.POINTER(FlagstatBatch),
]

lib.shadowfax_flagstat_stream_done.argtypes = [
    ctypes.POINTER(FlagstatStream),
]
lib.shadowfax_flagstat_stream_done.restype = ctypes.c_bool


lib.shadowfax_pileup_stream_create.argtypes = [
    ctypes.POINTER(Context),
    ctypes.c_char_p,          # bam_path
    ctypes.c_uint64,          # input_batch_size
    ctypes.c_uint64,          # data_limit
]
lib.shadowfax_pileup_stream_create.restype = ctypes.POINTER(PileupStreamC)

lib.shadowfax_pileup_stream_done.argtypes = [
    ctypes.POINTER(PileupStreamC),
]
lib.shadowfax_pileup_stream_done.restype = ctypes.c_bool

lib.shadowfax_pileup_stream_next.argtypes = [
    ctypes.POINTER(PileupStreamC),
]
lib.shadowfax_pileup_stream_next.restype = ctypes.POINTER(_PileupBatchC)

lib.shadowfax_pileup_stream_batch_destroy.argtypes = [
    ctypes.POINTER(PileupStreamC),
    ctypes.POINTER(_PileupBatchC),
]

lib.shadowfax_depth_stream_create.argtypes = [
    ctypes.POINTER(Context),
]
lib.shadowfax_depth_stream_create.restype = ctypes.POINTER(DepthStream)

lib.shadowfax_depth_batch_create.argtypes = [
]
lib.shadowfax_depth_batch_create.restype = ctypes.POINTER(DepthBatch)



lib.shadowfax_depth_stream_done.argtypes = [
    ctypes.POINTER(DepthStream),
]
lib.shadowfax_depth_stream_done.restype = ctypes.c_bool

lib.shadowfax_depth_stream_next.argtypes = [
    ctypes.POINTER(DepthStream),
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.POINTER(DepthBatch),
]

lib.shadowfax_depth_batch_get_data.argtypes = [
    ctypes.POINTER(DepthBatch),
    ctypes.POINTER(DepthBatchData),
]

lib.shadowfax_count_bases.argtypes = [
    ctypes.POINTER(Context),
    ctypes.POINTER(_VariantC),
    ctypes.c_uint64,
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.POINTER(_BaseCountsC),
]
lib.shadowfax_count_bases.restype = None


executor = ThreadPoolExecutor()

ctx = None
def get_context():
    global ctx
    if ctx is None:
        ctx = lib.shadowfax_context_create()
    return ctx


def _flagstat_thread(q, bam_path):
    stats = lib.shadowfax_flagstat_stream_create(bam_path.encode(), ctypes.c_uint64(128), ctypes.c_uint64(1))
    #print(stats.n_reads[0])
    return stats


def flagstat(bam_path):
    q = queue.Queue()

    future = executor.submit(_flagstat_thread, q, bam_path)

    return future

def flagstat_stream(bam_path='', batch_size=128*1024*1024):

    stream = lib.shadowfax_flagstat_stream_create(bam_path.encode(), batch_size, 1*1024*1024*1024)

    def gen():
        batch = FlagstatBatch()

        while not lib.shadowfax_flagstat_stream_done(stream):
            lib.shadowfax_flagstat_stream_next(stream, ctypes.byref(batch))
            yield batch

    return gen()

class Stream(ABC):
    def __init__(self):
        self.q = queue.Queue(maxsize=1)
        self.started = False

    def __iter__(self):
        return self

    def __next__(self):
        if not self.started:
            t = threading.Thread(target=self.thread, daemon=True)
            t.start()
            self.started = True
        item = self.q.get()
        if item is None:
            raise StopIteration
        return item

    def __ror__(self, input_stream):
        self.input_stream = input_stream
        return self

    @abstractmethod
    def thread(self):
        pass


class PileupStream(Stream):
    def __init__(self, bam_path='', input_batch_size=1*1024*1024*1024, output_batch_size=1*1024*1024*1024):
        super().__init__()

        ctx = get_context()
        self.stream = lib.shadowfax_pileup_stream_create(ctx, bam_path.encode(), input_batch_size, output_batch_size)
    def thread(self):
        while not lib.shadowfax_pileup_stream_done(self.stream):
            batch_ptr = lib.shadowfax_pileup_stream_next(self.stream)
            if not batch_ptr:
                continue
            batch = PileupBatch(self.stream, batch_ptr)
            self.q.put(batch)
        self.q.put(None)


class ReadDepthStream(Stream):
    def __init__(self):
        super().__init__()

        ctx = get_context()
        self.stream = lib.shadowfax_depth_stream_create(ctx)

    def thread(self):
        batch = lib.shadowfax_depth_batch_create()
        batch_data = DepthBatchData()

        for pileup_batch in self.input_stream:
            lib.shadowfax_depth_stream_next(self.stream, pileup_batch.data, pileup_batch.n_windows, batch)
            lib.shadowfax_depth_batch_get_data(batch, ctypes.byref(batch_data))
            self.q.put(batch_data)


def count_bases(variants, pileup_batch):
    if not variants:
        return []

    if not isinstance(pileup_batch, PileupBatch):
        raise TypeError("pileup_batch must be a PileupBatch")

    if not pileup_batch.data:
        return []

    variant_arr = (_VariantC * len(variants))()
    counts_arr = (_BaseCountsC * len(variants))()
    for idx, (pos, ref, alt) in enumerate(variants):
        variant_arr[idx].pos = pos
        variant_arr[idx].ref = ref.encode("ascii")
        variant_arr[idx].alt = alt.encode("ascii")

    lib.shadowfax_count_bases(
        get_context(),
        variant_arr,
        len(variants),
        pileup_batch.data,
        pileup_batch.n_windows,
        counts_arr,
    )

    return [
        BaseCounts(
            counts_arr[idx].a_count,
            counts_arr[idx].c_count,
            counts_arr[idx].g_count,
            counts_arr[idx].t_count,
        )
        for idx in range(len(variants))
    ]
