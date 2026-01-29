import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict

@dataclass
class Peak:
    fs_px: float
    ss_px: float
    inv_nm: float
    intensity: float
    panel: str

@dataclass
class Reflection:
    h: int
    k: int
    l: int
    intensity: float
    sigma: float
    peak_counts: float
    background_counts: float
    fs_px: float
    ss_px: float
    panel: str

@dataclass
class PredictRefine:
    initial_residual: float
    final_residual: float
    total_shifts: Tuple[float, float, float]
    det_shift_x: float
    det_shift_y: float

@dataclass
class Crystal:
    cell: Tuple[float, float, float, float, float, float]
    astar: Tuple[float, float, float]
    bstar: Tuple[float, float, float]
    cstar: Tuple[float, float, float]
    lattice_type: str
    centering: str
    unique_axis: Optional[str]
    profile_radius: float
    predict_refine: PredictRefine
    diffraction_resolution_limit: float  # stored as (1/d) in nm^-1 from the stream
    diffraction_resolution_limit_A: Optional[float] = None
    num_reflections: int = 0
    num_saturated: int = 0
    num_implausible: int = 0
    reflections: List[Reflection] = field(default_factory=list)

    @property
    def indexed_reflections(self) -> List[Reflection]:
        return self.reflections

    @property
    def predict_refine_final_residual(self) -> float:
        return self.predict_refine.final_residual

@dataclass
class Geometry:
    params: Dict[str, str] = field(default_factory=dict)
    coseda: Dict[str, str] = field(default_factory=dict)

    def __getattr__(self, name: str):
        if name in self.params:
            raw = self.params[name]
            token = raw.split()[0]
            try:
                return float(token)
            except ValueError:
                return raw
        raise AttributeError(f"{self.__class__.__name__!r} has no attribute {name!r}")

@dataclass
class UnitCell:
    lattice_type: str
    centering: str
    unique_axis: Optional[str]
    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float

@dataclass
class StreamChunk:
    filename: str
    event: int
    serial: int
    hit: bool
    indexed_by: str
    n_indexing_tries: int
    photon_energy_eV: float
    beam_divergence: float
    beam_bandwidth: float
    det_shift_x_mm: float
    det_shift_y_mm: float
    camera_length_m: float
    num_peaks: int
    peak_resolution_nm_inv: float
    peak_resolution_A: Optional[float] = None
    peaks: List[Peak] = field(default_factory=list)
    crystals: List[Crystal] = field(default_factory=list)

    def __getitem__(self, idx: int) -> Crystal:
        return self.crystals[idx]

@dataclass
class ParsedStream:
    chunks: List[StreamChunk]
    geometry: Optional[Geometry]
    unit_cell: Optional[UnitCell]

    @property
    def uc(self) -> Optional[UnitCell]:
        return self.unit_cell

    @property
    def geom(self) -> Optional[Geometry]:
        return self.geometry

    def get_chunk_by_event(self, event_num: int) -> Optional[StreamChunk]:
        return next((c for c in self.chunks if c.event == event_num), None)

def parse_stream_file(filepath: str) -> ParsedStream:
    with open(filepath, 'r') as f:
        lines = [l.rstrip('\n') for l in f]

    # 1) Global geometry
    geometry = None
    try:
        start = next(i for i,l in enumerate(lines) if l.startswith("----- Begin geometry file"))
        geom = Geometry()
        j = start + 1
        while not lines[j].startswith("----- End geometry file"):
            ln = lines[j].strip()
            if ln.lower().startswith(';coseda:'):
                body = ln.split(':',1)[1].strip()
                if '=' in body:
                    k,v = body.split('=',1)
                    geom.coseda[k.strip()] = v.strip()
            elif ln.startswith(';'):
                pass
            elif '=' in ln:
                k,v = ln.split('=',1)
                geom.params[k.strip()] = v.strip()
            j += 1
        geometry = geom
    except StopIteration:
        pass

    # 2) Global unit cell
    unit_cell = None
    try:
        start = next(i for i,l in enumerate(lines) if l.startswith("----- Begin unit cell"))
        uc_map: Dict[str,str] = {}
        j = start + 1
        while not lines[j].startswith("----- End unit cell"):
            ln = lines[j].strip()
            if ln and not ln.startswith(';') and '=' in ln:
                k,v = ln.split('=',1)
                uc_map[k.strip()] = v.strip()
            j += 1
        unit_cell = UnitCell(
            lattice_type=uc_map.get('lattice_type',''),
            centering=uc_map.get('centering',''),
            unique_axis=uc_map.get('unique_axis'),
            a=float(uc_map.get('a','0').split()[0]),
            b=float(uc_map.get('b','0').split()[0]),
            c=float(uc_map.get('c','0').split()[0]),
            alpha=float(uc_map.get('al','0').split()[0]),
            beta=float(uc_map.get('be','0').split()[0]),
            gamma=float(uc_map.get('ga','0').split()[0]),
        )
    except StopIteration:
        pass

    # 3) Per-frame chunks
    chunks: List[StreamChunk] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("Image filename:"):
            chunk = StreamChunk(
                filename="", event=0, serial=0, hit=False,
                indexed_by="", n_indexing_tries=0,
                photon_energy_eV=0.0, beam_divergence=0.0, beam_bandwidth=0.0,
                det_shift_x_mm=0.0, det_shift_y_mm=0.0,
                camera_length_m=0.0, num_peaks=0, peak_resolution_nm_inv=0.0, peak_resolution_A=None
            )
            # metadata
            while not lines[i].startswith("Peaks from peak search"):
                ln = lines[i].strip()
                if ln.startswith("Image filename:"):
                    chunk.filename = ln.split(":",1)[1].strip()
                elif ln.startswith("Event:"):
                    chunk.event = int(re.search(r'//?(\d+)', ln).group(1))
                elif ln.startswith("Image serial number:"):
                    chunk.serial = int(ln.split(":",1)[1])
                elif ln.startswith("hit"):
                    chunk.hit = bool(int(ln.split("=",1)[1]))
                elif ln.startswith("indexed_by"):
                    chunk.indexed_by = ln.split("=",1)[1].strip()
                elif ln.startswith("n_indexing_tries"):
                    chunk.n_indexing_tries = int(ln.split("=",1)[1])
                elif ln.startswith("photon_energy_eV"):
                    chunk.photon_energy_eV = float(ln.split("=",1)[1])
                elif ln.startswith("beam_divergence"):
                    chunk.beam_divergence = float(ln.split("=",1)[1].split()[0])
                elif ln.startswith("beam_bandwidth"):
                    chunk.beam_bandwidth = float(ln.split("=",1)[1].split()[0])
                elif "det_shift_x_mm" in ln:
                    chunk.det_shift_x_mm = float(ln.split("=",1)[1])
                elif "det_shift_y_mm" in ln:
                    chunk.det_shift_y_mm = float(ln.split("=",1)[1])
                elif ln.startswith("average_camera_length"):
                    chunk.camera_length_m = float(ln.split("=",1)[1].split()[0])
                elif ln.startswith("num_peaks"):
                    chunk.num_peaks = int(ln.split("=",1)[1])
                elif ln.startswith("peak_resolution"):
                    # CrystFEL prints both 1/d in nm^-1 and d in Å, e.g.
                    # "peak_resolution = 14.240697 nm^-1 or 0.702213 A"
                    rhs = ln.split("=", 1)[1].strip()
                    chunk.peak_resolution_nm_inv = float(rhs.split()[0])
                    mA = re.search(r"\bor\s*([\-\d\.Ee\+]+)\s*A\b", rhs)
                    if mA:
                        chunk.peak_resolution_A = float(mA.group(1))
                    else:
                        # If Å is not printed, compute d[Å] from inv_nm: d[Å] = 10 / (1/d)[nm^-1]
                        inv_nm = chunk.peak_resolution_nm_inv
                        chunk.peak_resolution_A = (10.0 / inv_nm) if inv_nm > 0 else None
                i += 1

            # peaks
            while not lines[i].startswith("Peaks from peak search"):
                i += 1
            i += 2
            while not lines[i].startswith("End of peak list"):
                parts = lines[i].split()
                try:
                    fs = float(parts[0])
                except:
                    i += 1
                    continue
                chunk.peaks.append(Peak(
                    fs_px=fs,
                    ss_px=float(parts[1]),
                    inv_nm=float(parts[2]),
                    intensity=float(parts[3]),
                    panel=parts[4]
                ))
                i += 1

            # one or more crystal blocks
            while i+1 < len(lines) and lines[i+1].startswith("--- Begin crystal"):
                i += 2
                pr = PredictRefine(0.0, 0.0, (0,0,0), 0.0, 0.0)
                xtl = Crystal(
                    cell=(0,0,0,0,0,0),
                    astar=(0,0,0), bstar=(0,0,0), cstar=(0,0,0),
                    lattice_type="", centering="", unique_axis=None,
                    profile_radius=0.0, predict_refine=pr,
                    diffraction_resolution_limit=0.0, diffraction_resolution_limit_A=None,
                    num_reflections=0, num_saturated=0, num_implausible=0
                )
                # header
                while not lines[i].startswith("Reflections measured after indexing"):
                    ln = lines[i].strip()
                    if ln.startswith("Cell parameters"):
                        vals = list(map(float, re.findall(r'[-+]?\d*\.\d+|\d+', ln)))
                        xtl.cell = tuple(vals[:6])
                    elif ln.startswith("astar"):
                        xtl.astar = tuple(map(float, re.findall(r'[-+]?\d*\.\d+|\d+', ln)))
                    elif ln.startswith("bstar"):
                        xtl.bstar = tuple(map(float, re.findall(r'[-+]?\d*\.\d+|\d+', ln)))
                    elif ln.startswith("cstar"):
                        xtl.cstar = tuple(map(float, re.findall(r'[-+]?\d*\.\d+|\d+', ln)))
                    elif ln.startswith("lattice_type"):
                        xtl.lattice_type = ln.split("=",1)[1].strip()
                    elif ln.startswith("centering"):
                        xtl.centering = ln.split("=",1)[1].strip()
                    elif ln.startswith("unique_axis"):
                        xtl.unique_axis = ln.split("=",1)[1].strip()
                    elif ln.startswith("profile_radius"):
                        xtl.profile_radius = float(ln.split("=",1)[1].split()[0])
                    elif ln.startswith("predict_refine/initial_residual"):
                        pr.initial_residual = float(re.search(r'=\s*([-\d\.Ee\+]+)', ln).group(1))
                    elif ln.startswith("predict_refine/final_residual"):
                        pr.final_residual = float(re.search(r'=\s*([-\d\.Ee\+]+)', ln).group(1))
                    elif ln.startswith("predict_refine/total_shifts"):
                        pr.total_shifts = tuple(map(float, re.findall(r'[-+]?\d*\.\d+|\d+', ln)))
                    elif ln.startswith("predict_refine/det_shift"):
                        x,y = re.search(r'x\s*=\s*([-\d\.Ee\+]+)\s*y\s*=\s*([-\d\.Ee\+]+)', ln).groups()
                        pr.det_shift_x, pr.det_shift_y = float(x), float(y)
                    elif ln.startswith("diffraction_resolution_limit"):
                        # CrystFEL prints both 1/d in nm^-1 and d in Å, e.g.
                        # "diffraction_resolution_limit = 12.07 nm^-1 or 0.83 A"
                        rhs = ln.split("=", 1)[1].strip()
                        xtl.diffraction_resolution_limit = float(rhs.split()[0])  # inv_nm
                        mA = re.search(r"\bor\s*([\-\d\.Ee\+]+)\s*A\b", rhs)
                        if mA:
                            xtl.diffraction_resolution_limit_A = float(mA.group(1))
                        else:
                            inv_nm = xtl.diffraction_resolution_limit
                            xtl.diffraction_resolution_limit_A = (10.0 / inv_nm) if inv_nm > 0 else None
                    elif ln.startswith("num_reflections"):
                        xtl.num_reflections = int(ln.split("=",1)[1])
                    elif ln.startswith("num_saturated_reflections"):
                        xtl.num_saturated = int(ln.split("=",1)[1])
                    elif ln.startswith("num_implausible_reflections"):
                        xtl.num_implausible = int(ln.split("=",1)[1])
                    i += 1

                # reflections
                i += 2  # skip header line
                while True:
                    ln = lines[i].strip()
                    if not ln or ln.startswith("End of reflections") or ln.startswith("--- End crystal"):
                        break
                    parts = ln.split()
                    xtl.reflections.append(Reflection(
                        h=int(parts[0]), k=int(parts[1]), l=int(parts[2]),
                        intensity=float(parts[3]), sigma=float(parts[4]),
                        peak_counts=float(parts[5]), background_counts=float(parts[6]),
                        fs_px=float(parts[7]), ss_px=float(parts[8]), panel=parts[9]
                    ))
                    i += 1

                chunk.crystals.append(xtl)
            chunks.append(chunk)
        else:
            i += 1

    return ParsedStream(chunks=chunks,
                        geometry=geometry,
                        unit_cell=unit_cell)