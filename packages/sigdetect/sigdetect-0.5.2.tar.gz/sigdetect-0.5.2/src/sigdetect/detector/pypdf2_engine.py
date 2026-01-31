from __future__ import annotations

import io
import re
import warnings
import zlib
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout, suppress
from pathlib import Path

from pypdf import PdfReader, generic
from pypdf.errors import PdfReadWarning

from ..config import DetectConfiguration
from ..utils import (
    AsDictionary,
    ChooseRole,
    GetFieldNameFromAncestry,
    HasSignatureFieldInAncestry,
    HasSignatureValue,
    LoadPatterns,
    NormalizeText,
    RolesFromGeneral,
    RolesFromLabels,
)
from .base import Detector, FileResult, Signature

# ────────────────────────── silence noisy pdf warnings ──────────────────────────
warnings.filterwarnings(
    "ignore",
    message=r"Multiple definitions in dictionary.*key /Subtype",
    category=PdfReadWarning,
)

# ---------------- fallbacks (used only if YAML omits them) ----------------
DEFAULT_VENDOR_BYTES = [
    r"/DocuSign",
    r"/Adobe\.PPKLite",
    r"/DocTimeStamp",
    r"/DSS",
    r"/AcrobatSign",
    r"/HelloSign",
    r"/Vinesign",
    r"/PandaDoc",
]
DEFAULT_VENDOR_TEXT = [
    r"DocuSign\s+Envelope\s+ID",
    r"Signature\s+Certificate",
    r"Electronic\s+Record\s+and\s+Signature\s+Disclosure",
    r"Adobe\s+Acrobat\s+Sign|Acrobat\s+Sign",
    r"HelloSign|Dropbox\s+Sign",
    r"Vinesign",
    r"Signed\s+with\s+PandaDoc",
    r"Reference\s+number",
    r"Digitally\s+signed\s+by",
]

DEFAULT_FIELDNAME_HINTS: dict[str, tuple[str, ...]] = {
    "patient": ("patient", "plaintiff", "self", "claimant"),
    "attorney": ("attorney", "lawyer", "counsel"),
    "representative": (
        "representative",
        "rep",
        "guardian",
        "parent",
        "executor",
        "custodian",
        "conservator",
        "poa",
        "powerofattorney",
    ),
    # retainer additions
    "client": ("client", "clientname", "clientsignature", "consumer"),
    "firm": ("firm", "lawfirm", "company", "corp", "authorizedsignatory"),
}

# Add robust “Parent/Guardian” label variant into representative labels.
REP_EXTRA = r"(signature\s+of\s+(the\s+)?(parent|guardian|parent\s*/\s*guardian))"

# Light retainer page cues (extra to YAML; safe defaults)
RETAIN_CLIENT_LABELS = [
    r"\bclient\s+signature\b",
    r"\bname\s+of\s+client\b",
    r"\bclient\b.*\bsignature\b",
    r"\bprint(?:ed)?\s+name\b.*\bclient\b",
]
RETAIN_FIRM_LABELS = [
    r"\bby:\b",
    r"\bfor\s+the\s+firm\b",
    r"\battorney'?s?\s+signature\b",
    r"\bcounsel\s+signature\b",
    r"\besq\.?\b",
]
RETAIN_FIRM_MARKERS = [
    r"\bLLP\b",
    r"\bLLC\b",
    r"\bP\.?C\.?\b",
    r"\bP\.?A\.?\b",
    r"\bAttorneys?\s+at\s+Law\b",
    r"\bLaw\b",
]

AP_DO_PATTERN = re.compile(r"/(?P<name>[^\s]+)\s+Do\b")
AP_TEXT_PATTERN = re.compile(r"\b(TJ|Tj)\b")
AP_VECTOR_PATTERN = re.compile(r"\b(m|l|c|re)\b", re.IGNORECASE)


@contextmanager
def _QuietIo():
    """Hide noisy stdout/stderr messages from PDF parsing/text extraction."""
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        yield


class PyPDF2Detector(Detector):
    Name = "pypdf2"

    def __init__(self, configuration: DetectConfiguration):
        self.Configuration = configuration
        self.Profile = (
            getattr(configuration, "Profile", getattr(configuration, "profile", "hipaa")) or "hipaa"
        )
        pats = LoadPatterns(self.Profile)

        # Vendor patterns (fallback to defaults if missing)
        vb = pats.get("bytes") or DEFAULT_VENDOR_BYTES
        vt = pats.get("text") or DEFAULT_VENDOR_TEXT
        self.VendorBytePatterns = [re.compile(p.encode(), re.I) for p in vb]
        self.VendorTextPatterns = [re.compile(p, re.I) for p in vt]

        # Allow callers to disable expensive XObject recursion if desired
        self.RecurseXObjects = bool(
            getattr(
                configuration, "RecurseXObjects", getattr(configuration, "recurse_xobjects", True)
            )
        )

        # Role patterns (labels + general)
        labels = dict(pats.get("labels", {}))
        # Ensure HIPAA representative includes Parent/Guardian phrasing
        if "representative" in labels:
            labels["representative"] = f"(?:{labels['representative']}|{REP_EXTRA})"
        else:
            labels["representative"] = REP_EXTRA

        # Retainer: ensure 'client' and 'firm' buckets exist
        if self.Profile == "retainer":
            if "client" not in labels:
                labels["client"] = "|".join(RETAIN_CLIENT_LABELS)
            if "firm" not in labels:
                labels["firm"] = "|".join(RETAIN_FIRM_LABELS)

        self.RoleLabelPatterns = {k: re.compile(v, re.I) for k, v in labels.items()}
        self.GeneralRolePatterns = {
            k: re.compile(v, re.I) for k, v in pats.get("general", {}).items()
        }

        # Field hints (accept either key name)
        raw_field_hints = (
            pats.get("field_hints") or pats.get("fieldname_hints") or DEFAULT_FIELDNAME_HINTS
        )
        self.FieldHints: dict[str, tuple[str, ...]] = {
            k: tuple(v) for k, v in raw_field_hints.items()
        }

        # Doc hard rules + weights
        self.DocumentHardRules = {
            k: re.compile(v, re.I) for k, v in pats.get("doc_hard", {}).items()
        }
        self.WeightConfiguration = pats.get(
            "weights",
            {
                "field": 3,
                "page_label": 2,
                "general": 1,
                "doc_hint_strong": 3,
                "doc_hint_weak": 2,
            },
        )

        # Precompile retainer extras
        if self.Profile == "retainer":
            self._ClientPagePatterns = [re.compile(p, re.I) for p in RETAIN_CLIENT_LABELS]
            self._FirmPagePatterns = [re.compile(p, re.I) for p in RETAIN_FIRM_LABELS]
            self._FirmMarkerPatterns = [re.compile(p, re.I) for p in RETAIN_FIRM_MARKERS]
            self._SignatureWord = re.compile(r"\bsignature\b", re.I)
            self._DateWord = re.compile(r"\bdate\b", re.I)
            self._ByWord = re.compile(r"\bby:\b", re.I)

        # Heuristic to drop false widgets like DocuSign envelope ID
        self._EnvelopeNoise = re.compile(r"envelope[_\s-]*id|envelopeid|certificate|docid", re.I)

    # ---------------- vendor scanning helpers ----------------
    def _ScanRaw(self, raw: bytes) -> set[str]:
        """Scan bytes (already decompressed if needed) for vendor markers & text."""
        hits: set[str] = set()
        if not raw:
            return hits
        for rx in self.VendorBytePatterns:
            if rx.search(raw):
                try:
                    pat = rx.pattern.decode("ascii", "ignore")
                except Exception:
                    pat = str(rx.pattern)
                hits.add(f"VendorBytes:{pat}")
        # also search text markers inside bytes
        textish = raw.decode("latin1", "ignore")
        for rx in self.VendorTextPatterns:
            if rx.search(textish):
                hits.add(f"VendorText:{rx.pattern}")
        return hits

    def _ScanPageVendors(self, page) -> tuple[set[str], str]:
        """Return vendor hits along with the extracted page text."""

        found: set[str] = set()

        with _QuietIo():
            cont = page.get_contents()
            raws: list[bytes] = []
            if cont is None:
                pass
            elif isinstance(cont, list):
                raws.extend(c.get_data() for c in cont if hasattr(c, "get_data"))
            elif hasattr(cont, "get_data"):
                raws.append(cont.get_data())

        for raw in raws:
            found |= self._ScanRaw(raw)

        with _QuietIo():
            txt = page.extract_text() or ""
        for rx in self.VendorTextPatterns:
            if rx.search(txt):
                found.add(f"VendorText:{rx.pattern}")

        return found, txt

    def _IterateFormXObjects(self, page) -> Iterator[generic.DictionaryObject]:
        """Yield Form XObject dictionaries recursively from page resources."""
        with suppress(KeyError):
            xobjs = page["/Resources"]["/XObject"]
            visited = set()

            def walk(xo):
                d = AsDictionary(xo)
                if not isinstance(d, generic.DictionaryObject):
                    return
                key = (id(d), d.get("/Subtype"))
                if key in visited:
                    return
                visited.add(key)
                if d.get("/Subtype") == "/Form":
                    yield d
                    with suppress(KeyError):
                        nested = d["/Resources"]["/XObject"]
                        for n in nested.values():
                            yield from walk(n)

            for ob in xobjs.values():
                yield from walk(ob)

    def _CollectXObjectVendorAndText(self, page) -> tuple[set[str], str]:
        """Scan Form XObjects regardless of whether they're drawn."""
        hits: set[str] = set()
        parts: list[str] = []
        for xo in self._IterateFormXObjects(page):
            if hasattr(xo, "get_data"):
                with suppress(Exception), _QuietIo():
                    raw = xo.get_data()
                if raw:
                    hits |= self._ScanRaw(raw)
                    parts.append(raw.decode("latin1", "ignore"))
        return hits, " ".join(parts)

    # ---------------- appearance classification helpers ----------------
    def _ExtractAppearanceStreams(self, candidate: object) -> list[object]:
        """Return decoded appearance stream objects from an ``/AP`` entry."""

        streams: list[object] = []

        def visit(node: object | None) -> None:
            if node is None:
                return
            obj = AsDictionary(node)
            if isinstance(obj, generic.IndirectObject):
                with suppress(Exception):
                    obj = obj.get_object()
            obj = AsDictionary(obj)
            if obj is None:
                return
            if hasattr(obj, "get_data"):
                streams.append(obj)
                return
            if isinstance(obj, generic.DictionaryObject):
                for value in obj.values():
                    visit(value)
            elif isinstance(obj, generic.ArrayObject):
                for value in obj:
                    visit(value)

        visit(candidate)
        return streams

    def _ResolveResources(self, stream, page) -> generic.DictionaryObject | None:
        """Return the resource dictionary for the given appearance stream."""

        resources = AsDictionary(getattr(stream, "get", lambda *_: None)("/Resources"))  # type: ignore[arg-type]
        if isinstance(resources, generic.IndirectObject):
            with suppress(Exception):
                resources = resources.get_object()
        resources = AsDictionary(resources)
        if not isinstance(resources, generic.DictionaryObject) and page is not None:
            page_resources = AsDictionary(page.get("/Resources")) if page else None
            if isinstance(page_resources, generic.IndirectObject):
                with suppress(Exception):
                    page_resources = page_resources.get_object()
            if isinstance(page_resources, generic.DictionaryObject):
                resources = page_resources
        return resources if isinstance(resources, generic.DictionaryObject) else None

    def _DoTargetsImage(self, name: str, resources: generic.DictionaryObject | None) -> bool:
        """Determine whether ``name`` resolves to an Image XObject."""

        normalized = name.lstrip("/")
        if resources is not None:
            xobjects = AsDictionary(resources.get("/XObject"))
            if isinstance(xobjects, generic.IndirectObject):
                with suppress(Exception):
                    xobjects = xobjects.get_object()
            if isinstance(xobjects, generic.DictionaryObject):
                for key, value in xobjects.items():
                    key_name = str(key)
                    if key_name.startswith("/"):
                        key_name = key_name[1:]
                    if key_name == normalized:
                        target = AsDictionary(value)
                        if isinstance(target, generic.IndirectObject):
                            with suppress(Exception):
                                target = target.get_object()
                        target = AsDictionary(target)
                        if isinstance(target, generic.DictionaryObject):
                            if target.get("/Subtype") == "/Image":
                                return True
        # Fallback heuristic: appearance streams typically prefix image XObjects with "Im".
        return normalized.lower().startswith("im")

    def _ClassifyAppearance(self, widget: generic.DictionaryObject, page) -> str:
        """Classify the widget's appearance as drawn or typed."""

        ap_dict = AsDictionary(widget.get("/AP"))
        if not isinstance(ap_dict, generic.DictionaryObject):
            return "unknown"
        normal = ap_dict.get("/N")
        streams = self._ExtractAppearanceStreams(normal)
        if not streams:
            return "typed"

        has_text = False
        has_vector = False
        has_image = False

        for stream in streams:
            try:
                data = stream.get_data()  # type: ignore[attr-defined]
            except Exception:
                continue
            if not data:
                continue

            text = data.decode("latin1", "ignore")
            if AP_TEXT_PATTERN.search(text):
                has_text = True
            if AP_VECTOR_PATTERN.search(text):
                has_vector = True

            names = {match.group("name").lstrip("/") for match in AP_DO_PATTERN.finditer(text)}
            if names:
                resources = self._ResolveResources(stream, page)
                for name in names:
                    if self._DoTargetsImage(name, resources):
                        has_image = True
                        break

        if has_image:
            return "drawn"
        if has_text or has_vector:
            return "typed"
        return "typed"

    # ---- file-wide stream scan (compressed or not)
    def _ScanFileStreamsForVendors(self, file_bytes: bytes) -> tuple[set[str], str]:
        """
        Find all 'stream ... endstream' blocks, test raw and decompressed (zlib/gzip),
        and return (vendor_hits, decoded_text_blob).
        """
        hits: set[str] = set()
        texts: list[str] = []
        if not file_bytes:
            return hits, ""

        # quick pass on the whole file
        hits |= self._ScanRaw(file_bytes)

        for m in re.finditer(rb"stream\s*[\r\n]+(.*?)\s*endstream", file_bytes, re.DOTALL):
            chunk = m.group(1)
            if not chunk:
                continue

            # raw scan + raw text
            hits |= self._ScanRaw(chunk)
            texts.append(chunk.decode("latin1", "ignore"))

            # try decompress with multiple wbits
            for wbits in (15, -15, 31):
                try:
                    dec = zlib.decompress(chunk, wbits)
                    if dec:
                        hits |= self._ScanRaw(dec)
                        texts.append(dec.decode("latin1", "ignore"))
                        break
                except Exception:
                    continue
        return hits, " ".join(texts)

    # ---------------- helpers for widgets ----------------
    def _FieldNameForWidget(self, wdict: generic.DictionaryObject) -> str:
        nm = self._PickNameAny(wdict)
        if nm:
            return nm
        p = AsDictionary(wdict.get("/Parent"))
        if isinstance(p, generic.DictionaryObject):
            nm = self._PickNameAny(p)
            if nm:
                return nm
        nm = GetFieldNameFromAncestry(wdict)
        return "" if nm is None else str(nm)

    def _WidgetBoundingBox(
        self, wdict: generic.DictionaryObject
    ) -> tuple[float, float, float, float] | None:
        """Return the widget's ``/Rect`` coordinates normalized as (x0, y0, x1, y1)."""

        rect = self._RectToTuple(wdict.get("/Rect"))
        if rect:
            return rect
        parent = AsDictionary(wdict.get("/Parent"))
        if isinstance(parent, generic.DictionaryObject):
            return self._RectToTuple(parent.get("/Rect"))
        return None

    def _RectToTuple(self, candidate) -> tuple[float, float, float, float] | None:
        if candidate is None:
            return None
        if isinstance(candidate, generic.IndirectObject):
            with suppress(Exception):
                candidate = candidate.get_object()
        if isinstance(candidate, generic.ArrayObject) and len(candidate) == 4:
            coords: list[float] = []
            for item in candidate:
                try:
                    coords.append(float(item))
                except Exception:
                    return None
            x0, y0, x1, y1 = coords
            if x1 < x0:
                x0, x1 = x1, x0
            if y1 < y0:
                y0, y1 = y1, y0
            return x0, y0, x1, y1
        return None

    @staticmethod
    def _PickNameAny(d: generic.DictionaryObject) -> str | None:
        for key in ("/T", "/TU", "/TM"):
            v = d.get(key)
            if v:
                try:
                    return str(v)
                except Exception:
                    return None
        return None

    def _IsSignatureWidget(self, wdict: generic.DictionaryObject) -> bool:
        """Strictly identify real signature widgets and ignore envelope/metadata fields."""
        try:
            if wdict.get("/FT") == "/Sig" or HasSignatureFieldInAncestry(wdict):
                return True
            # value object might be an indirect sig dict
            v = wdict.get("/V")
            if isinstance(v, generic.IndirectObject):
                v = v.get_object()
            dv = AsDictionary(v)
            if isinstance(dv, generic.DictionaryObject) and dv.get("/Type") == "/Sig":
                return True
            # Heuristic: drop known non-signature fields (DocuSign envelope, cert refs, etc.)
            fname = (self._FieldNameForWidget(wdict) or "").strip()
            if fname and self._EnvelopeNoise.search(fname):
                return False
        except Exception:
            pass
        return False

    def _iter_widgets_with_ref(
        self, annots_obj
    ) -> Iterator[tuple[generic.DictionaryObject, generic.IndirectObject | None]]:
        if annots_obj is None:
            return
        stack = [annots_obj]
        while stack:
            cur = stack.pop()
            if isinstance(cur, generic.IndirectObject):
                obj = cur.get_object()
                if isinstance(obj, generic.DictionaryObject) and obj.get("/Subtype") == "/Widget":
                    yield obj, cur
                    continue
                if isinstance(obj, generic.ArrayObject):
                    stack.extend(list(obj))
                    continue
            elif isinstance(cur, generic.ArrayObject):
                stack.extend(list(cur))
            elif isinstance(cur, generic.DictionaryObject) and cur.get("/Subtype") == "/Widget":
                yield cur, None

    def _CollectAcroSignatures(self, reader: PdfReader) -> list[tuple[str, int | None, bool]]:
        """
        Return a list of (field_name, page_index_or_None, has_kids_widget).
        has_kids_widget = True when /Kids exists on the /Sig field (real widget).
        """
        results: list[tuple[str, int | None, bool]] = []
        with suppress(Exception):
            root = reader.trailer["/Root"]
            acro = root.get("/AcroForm")
            fields = AsDictionary(acro).get("/Fields") if acro else None
            if not isinstance(fields, generic.ArrayObject):
                return results

            def walk(fobj):
                fd = AsDictionary(fobj)
                if not isinstance(fd, generic.DictionaryObject):
                    return
                if (
                    fd.get("/FT") == "/Sig"
                    or HasSignatureFieldInAncestry(fd)
                    or HasSignatureValue(fd)
                ):
                    name = (
                        self._PickNameAny(fd) or (GetFieldNameFromAncestry(fd) or "") or "AcroSig"
                    )
                    page_idx: int | None = None
                    has_kids_widget = False

                    kids = AsDictionary(fd.get("/Kids"))
                    if isinstance(kids, generic.ArrayObject):
                        has_kids_widget = len(kids) > 0
                        for kid in kids:
                            kd = AsDictionary(kid)
                            if isinstance(kd, generic.DictionaryObject):
                                with suppress(KeyError, AttributeError):
                                    p = kd.get("/P")
                                    if isinstance(p, generic.IndirectObject):
                                        try:
                                            for i, pg in enumerate(reader.pages, start=1):
                                                if pg.indirect_reference == p:
                                                    page_idx = i
                                                    break
                                        except Exception:
                                            pass
                    results.append((str(name), page_idx, has_kids_widget))

                kids = AsDictionary(fd.get("/Kids"))
                if isinstance(kids, generic.ArrayObject):
                    for k in kids:
                        walk(k)

            for f in fields:
                walk(f)

        return results

    # ---------------- role scoring (HIPAA) ----------------
    def _RolesFromField(self, field_name: str) -> set[str]:
        roles: set[str] = set()
        compact = re.sub(r"[^a-z0-9]+", "", (field_name or "").lower())
        if not compact:
            return roles
        for role, keys in self.FieldHints.items():
            if any(k in compact for k in keys):
                roles.add(role)
        return roles

    def _InferRole(self, field_name: str, page_text: str):
        scores: dict[str, int] = defaultdict(int)
        evidence: list[str] = []

        for r in self._RolesFromField(field_name):
            scores[r] += self.WeightConfiguration["field"]
            evidence.append(f"field:{r}")

        for r in RolesFromLabels(page_text, self.RoleLabelPatterns):
            scores[r] += self.WeightConfiguration["page_label"]
            evidence.append(f"page_label:{r}")

        for r in RolesFromGeneral(page_text, self.GeneralRolePatterns):
            scores[r] += self.WeightConfiguration["general"]
            evidence.append(f"general:{r}")

        role = ChooseRole(scores)
        return role, evidence, dict(scores), sum(scores.values())

    # ---------------- retainer utilities (pseudo, vendor-only) ----------------
    def _RetainerPageScores(
        self,
        text: str,
        vendor_count: int,
        page_index0: int,
        total_pages: int,
    ) -> tuple[int, int, list[str]]:
        """Return (client_score, firm_score, evidence[]) for a single page."""
        t = NormalizeText(text)
        ev: list[str] = []
        cs = fs = 0

        # explicit labels
        for rx in self._ClientPagePatterns:
            if rx.search(t):
                cs += self.WeightConfiguration["page_label"]
                ev.append("label:client")

        firm_label_hit = False
        for rx in self._FirmPagePatterns:
            if rx.search(t):
                fs += self.WeightConfiguration["page_label"]
                firm_label_hit = True
        if firm_label_hit:
            ev.append("label:firm")

        # firm markers (LLP/LLC/etc.) boost — BUT ignore on page 1 unless a real signature cue exists
        marker_boosted = False
        for rx in self._FirmMarkerPatterns:
            if rx.search(t):
                if page_index0 > 0 or self._SignatureWord.search(t) or self._ByWord.search(t):
                    fs += self.WeightConfiguration["general"]  # light boost
                    ev.append("marker:firm")
                    marker_boosted = True
        # If only marker on page 1 with no cue, we do not add any boost.

        # signature & date co-occurrence (stronger confidence)
        sig_hit = bool(self._SignatureWord.search(t))
        date_hit = bool(self._DateWord.search(t))
        if sig_hit and re.search(r"\bclient\b", t, re.I):
            cs += 1
            ev.append("word:signature+client")
        if sig_hit and (
            self._ByWord.search(t) or re.search(r"\b(attorney|counsel|firm)\b", t, re.I)
        ):
            fs += 1
            ev.append("word:signature+firm")
        if sig_hit and date_hit:
            # common signature block layout has both
            cs += 1
            fs += 1
            ev.append("word:signature+date")

        # vendor hits seen on this page (from content/xobject) – weak but helpful
        if vendor_count > 0:
            cs += 1
            fs += 1
            ev.append("vendor:page_hit")

        # position prior: end of the doc tends to host signature blocks
        if total_pages >= 3 and page_index0 >= (2 * total_pages) // 3 - 1:
            cs += 1
            fs += 1
            ev.append("prior:end_of_doc")

        # general role regex (if YAML provided)
        for r in RolesFromGeneral(t, self.GeneralRolePatterns):
            if r == "client":
                cs += self.WeightConfiguration["general"]
                ev.append("general:client")
            if r in {"firm", "attorney"}:
                fs += self.WeightConfiguration["general"]
                ev.append("general:firm")

        # FINAL dampener for page 1:
        # If page 1 had only weak firm markers (LLP/LLC) and no signature cues, wipe that boost.
        if page_index0 == 0 and not sig_hit and not self._ByWord.search(t):
            if marker_boosted:
                fs = max(0, fs - self.WeightConfiguration["general"])
                ev.append("dampen:front_matter")

        return cs, fs, ev

    # ---------------- main ----------------
    def Detect(self, pdf_path: Path) -> FileResult:
        try:
            with _QuietIo():
                reader = PdfReader(str(pdf_path))
            size_kb = round(pdf_path.stat().st_size / 1024, 1)
            pages = len(reader.pages)

            # file-wide vendor scan (+decompressed streams)
            try:
                _file_bytes = pdf_path.read_bytes()
            except Exception:
                _file_bytes = b""
            file_vendor_hits, _stream_text_blob = self._ScanFileStreamsForVendors(_file_bytes)

            acro_sig_list = self._CollectAcroSignatures(reader)

            page_texts: list[str] = []
            vendor_hints: set[str] = set()
            vendor_hits_per_page: list[int] = []
            images_per_page: list[int] = []
            any_text, img_pages = False, 0

            for page in reader.pages:
                # per-page vendor
                pv, page_text = self._ScanPageVendors(page)
                x_hits: set[str] = set()
                x_text = ""
                if self.RecurseXObjects:
                    x_hits, x_text = self._CollectXObjectVendorAndText(page)
                vendor_hints |= pv | x_hits
                vendor_hits_per_page.append(len(pv) + len(x_hits))

                if x_text:
                    page_text = f"{page_text} {x_text}".strip() if page_text else x_text.strip()
                page_texts.append(page_text)
                any_text = any_text or bool(page_text)

                # image counting
                img_count = 0
                with suppress(KeyError):
                    xobjs = page["/Resources"]["/XObject"]
                    img_count = sum(
                        1 for obj in xobjs.values() if AsDictionary(obj).get("/Subtype") == "/Image"
                    )
                images_per_page.append(img_count)
                img_pages += 1 if img_count > 0 else 0

            # Merge file-level vendor hits (catches unpainted & compressed streams)
            vendor_hints |= file_vendor_hits

            scanned_pdf = (not any_text) and (img_pages > 0)

            # --- find signature widgets on pages (strict)
            page_widgets: list[
                tuple[int, generic.DictionaryObject, generic.IndirectObject | None]
            ] = []
            for idx, page in enumerate(reader.pages, start=1):
                for wdict, ref in self._iter_widgets_with_ref(page.get("/Annots")):
                    if self._IsSignatureWidget(wdict):
                        page_widgets.append((idx, wdict, ref))
                    # else: ignore envelope/cert widgets

            has_page_widgets = len(page_widgets) > 0
            has_acro = len(acro_sig_list) > 0
            has_vendor = len(vendor_hints) > 0
            acro_has_kids = any(hk for _, __, hk in acro_sig_list)

            # ───────────────────────────── HIPAA branch ─────────────────────────────
            if self.Profile == "hipaa":
                return self._DetectHipaaPath(
                    pdf_path=pdf_path,
                    reader=reader,
                    page_texts=page_texts,
                    vendor_hints=vendor_hints,
                    scanned_pdf=scanned_pdf,
                    page_widgets=page_widgets,
                    acro_sig_list=acro_sig_list,
                    has_page_widgets=has_page_widgets,
                    has_acro=has_acro,
                    has_vendor=has_vendor,
                    acro_has_kids=acro_has_kids,
                    size_kb=size_kb,
                    pages=pages,
                )

            # ───────────────────────────── Retainer branch ─────────────────────────────
            signatures: list[Signature] = []

            if has_page_widgets:
                # Real widgets: infer role from page text; avoid envelope-id noise already filtered
                seen_refs: set[str] = set()
                seen_page_name: set[tuple[int, str]] = set()

                for idx, wdict, ref in page_widgets:
                    field_name = self._FieldNameForWidget(wdict)
                    page_obj = reader.pages[idx - 1] if 0 <= (idx - 1) < len(reader.pages) else None
                    render_type = self._ClassifyAppearance(wdict, page_obj)
                    bounding_box = self._WidgetBoundingBox(wdict)

                    # de-dup by object ref (if present) and (page, name)
                    if isinstance(ref, generic.IndirectObject):
                        key = f"{ref.idnum}:{ref.generation}"
                        if key in seen_refs:
                            continue
                        seen_refs.add(key)

                    if field_name:
                        key2 = (idx, field_name)
                        if key2 in seen_page_name:
                            continue
                        seen_page_name.add(key2)

                    page_text = page_texts[idx - 1] if 0 <= (idx - 1) < len(page_texts) else ""
                    c, f, ev = self._RetainerPageScores(
                        page_text, vendor_hits_per_page[idx - 1], idx - 1, pages
                    )
                    role = "client" if c >= f and c > 0 else ("firm" if f > 0 else "unknown")

                    # fall back to generic role inference if indecisive
                    if role == "unknown":
                        role, evidence, scores, total = self._InferRole(field_name, page_text)
                        evidence = evidence or ev
                        scores = scores or ({role: 1} if role != "unknown" else {})
                        total = total or sum(scores.values())
                    else:
                        evidence = ev
                        scores = {role: (c if role == "client" else f)}
                        total = scores[role]

                    signatures.append(
                        Signature(
                            Page=idx,
                            FieldName=field_name,
                            Role=role,
                            Score=total,
                            Scores=scores,
                            Evidence=evidence,
                            Hint=(f"AcroSig:{field_name}" if field_name else "AcroSig"),
                            RenderType=render_type,
                            BoundingBox=bounding_box,
                        )
                    )

                # If only one role but page text clearly indicates both, add the second role pseudo.
                if len(signatures) == 1:
                    pg = signatures[0].Page or 1
                    c, f, ev = self._RetainerPageScores(
                        page_texts[pg - 1], vendor_hits_per_page[pg - 1], pg - 1, pages
                    )
                    want = None
                    have = {signatures[0].Role}
                    if "client" not in have and c > 0:
                        want = ("client", c)
                    elif "firm" not in have and f > 0:
                        want = ("firm", f)
                    if want:
                        r, sc = want
                        signatures.append(
                            Signature(
                                Page=pg,
                                FieldName="vendor_or_acro_detected",
                                Role=r,
                                Score=sc,
                                Scores={r: sc},
                                Evidence=ev + ["pseudo:true"],
                                Hint="VendorOrAcroOnly",
                                RenderType="typed",
                            )
                        )

            else:
                # No widgets found. Retainers usually have two signees; pick likely pages.
                if self.Configuration.PseudoSignatures and (has_acro or has_vendor):
                    totals = []
                    for i, text in enumerate(page_texts):
                        c, f, ev = self._RetainerPageScores(text, vendor_hits_per_page[i], i, pages)
                        totals.append((i, c, f, ev))

                    # Pages with any signal
                    candidates = [i for i, c, f, _ in totals if (c > 0 or f > 0)]

                    # If page 1 is in candidates but has no signature cue, drop it (anti front-matter).
                    def HasSignatureCue(i: int) -> bool:
                        t = page_texts[i]
                        return bool(self._SignatureWord.search(t) or self._ByWord.search(t))

                    candidates = [i for i in candidates if not (i == 0 and not HasSignatureCue(i))]

                    # If still empty, prefer the last page(s)
                    if not candidates:
                        candidates = [p for p in range(max(0, pages - 2), pages)]

                    # best client & firm pages
                    c_best = max(candidates, key=lambda i: totals[i][1]) if candidates else None
                    f_best = max(candidates, key=lambda i: totals[i][2]) if candidates else None

                    def emit(page_idx: int | None, role: str, score: int, ev: list[str]):
                        pg = (page_idx + 1) if page_idx is not None else pages
                        signatures.append(
                            Signature(
                                Page=pg,
                                FieldName="vendor_or_acro_detected",
                                Role=role,
                                Score=score,
                                Scores={role: score} if score > 0 else {},
                                Evidence=ev + ["pseudo:true"],
                                Hint="VendorOrAcroOnly",
                                RenderType="typed",
                            )
                        )

                    if c_best is not None and totals[c_best][1] > 0:
                        emit(c_best, "client", totals[c_best][1], totals[c_best][3])
                    if f_best is not None and totals[f_best][2] > 0:
                        emit(f_best, "firm", totals[f_best][2], totals[f_best][3])

                    # If nothing yet, emit both roles on the last page as a conservative fallback.
                    if not signatures:
                        emit(pages - 1, "client", 0, [])
                        emit(pages - 1, "firm", 0, [])

            # doc-level names for hints
            acro_names = {name for name, _pg, _hk in acro_sig_list if name}

            # scanned/mixed refinement for retainer:
            # If we emitted only pseudo signatures (no widgets on those pages and no vendor on them),
            # and those pages have images, mark scanned and mixed.
            if self.Profile == "retainer" and not has_page_widgets:
                pseudo_pages = [s.Page for s in signatures if s.Page]
                if pseudo_pages:
                    pvendors = all(
                        vendor_hits_per_page[p - 1] == 0 for p in pseudo_pages if p - 1 >= 0
                    )
                    pimages = any(images_per_page[p - 1] > 0 for p in pseudo_pages if p - 1 >= 0)
                else:
                    pvendors = False
                    pimages = False
                if pimages and pvendors:
                    scanned_pdf = True  # scanned signatures present

            esign_found = (len(signatures) > 0) or has_vendor or has_acro
            mixed = esign_found and scanned_pdf

            doc_roles: set[str] = {s.Role for s in signatures if s.Role != "unknown"}

            hints: set[str] = set()
            hints |= {f"AcroSig:{n}" for n in acro_names}
            hints |= set(vendor_hints)
            hints |= {s.Hint for s in signatures}

            return FileResult(
                File=pdf_path.name,
                SizeKilobytes=size_kb,
                PageCount=pages,
                ElectronicSignatureFound=esign_found,
                ScannedPdf=scanned_pdf,
                MixedContent=mixed,
                SignatureCount=len(signatures),
                SignaturePages=",".join(
                    map(str, sorted({signature.Page for signature in signatures if signature.Page}))
                ),
                Roles=";".join(sorted(doc_roles)) if doc_roles else "unknown",
                Hints=";".join(sorted(hints)),
                Signatures=signatures,
            )

        except Exception as exc:  # capture errors per file
            return FileResult(
                File=pdf_path.name,
                SizeKilobytes=None,
                PageCount=0,
                ElectronicSignatureFound=False,
                ScannedPdf=None,
                MixedContent=None,
                SignatureCount=0,
                SignaturePages="",
                Roles="error",
                Hints=f"ERROR:{exc}",
                Signatures=[],
            )

    # ───────────────────────── HIPAA path  ─────────────────────────
    def _DetectHipaaPath(
        self,
        *,
        pdf_path: Path,
        reader: PdfReader,
        page_texts: list[str],
        vendor_hints: set[str],
        scanned_pdf: bool,
        page_widgets: list[tuple[int, generic.DictionaryObject, generic.IndirectObject | None]],
        acro_sig_list: list[tuple[str, int | None, bool]],
        has_page_widgets: bool,
        has_acro: bool,
        has_vendor: bool,
        acro_has_kids: bool,
        size_kb: float,
        pages: int,
    ) -> FileResult:
        signatures: list[Signature] = []

        if has_page_widgets:
            # --- real widgets path (NO pseudo allowed later)
            seen_refs: set[str] = set()
            seen_page_name: set[tuple[int, str]] = set()

            for idx, wdict, ref in page_widgets:
                field_name = self._FieldNameForWidget(wdict)
                page_obj = reader.pages[idx - 1] if 0 <= (idx - 1) < len(reader.pages) else None
                render_type = self._ClassifyAppearance(wdict, page_obj)
                bounding_box = self._WidgetBoundingBox(wdict)

                # de-dup by object ref (if present) and (page, name)
                if isinstance(ref, generic.IndirectObject):
                    key = f"{ref.idnum}:{ref.generation}"
                    if key in seen_refs:
                        continue
                    seen_refs.add(key)

                if field_name:
                    key2 = (idx, field_name)
                    if key2 in seen_page_name:
                        continue
                    seen_page_name.add(key2)

                page_text = page_texts[idx - 1] if 0 <= (idx - 1) < len(page_texts) else ""
                role, evidence, scores, total = self._InferRole(field_name, page_text)
                signatures.append(
                    Signature(
                        Page=idx,
                        FieldName=field_name,
                        Role=role,
                        Score=total,
                        Scores=scores,
                        Evidence=evidence,
                        Hint=(f"AcroSig:{field_name}" if field_name else "AcroSig"),
                        RenderType=render_type,
                        BoundingBox=bounding_box,
                    )
                )

        elif acro_has_kids:
            # There are real /Widget(s) attached to /Sig fields, but we didn't
            # locate them on pages (e.g., /Annots not visible). Emit NON-pseudo
            # signatures from the field names so mixed cases don't get pseudo.
            whole_text = NormalizeText("\n".join(page_texts))
            for fname, pg, _hk in acro_sig_list:
                page_text = page_texts[pg - 1] if pg and pg - 1 < len(page_texts) else ""
                # fallback to whole doc text if page unknown
                base_text = page_text or whole_text
                role, evidence, scores, total = self._InferRole(fname, base_text)
                signatures.append(
                    Signature(
                        Page=pg,
                        FieldName=fname,
                        Role=role,
                        Score=total,
                        Scores=scores,
                        Evidence=evidence,
                        Hint=f"AcroSig:{fname}" if fname else "AcroSig",
                        RenderType="typed",
                    )
                )

        else:
            # --- vendor/acro pseudo path (only when NO page widgets or acro-kids)
            if self.Configuration.PseudoSignatures and (has_acro or has_vendor):
                # IMPORTANT: use only page text (not raw decompressed stream dump).
                text_norm = NormalizeText("\n".join(page_texts))
                scores: dict[str, int] = defaultdict(int)
                evidence: list[str] = []

                # Hard rules
                rel = self.DocumentHardRules.get("rel_label")
                kin = self.DocumentHardRules.get("kin")
                minor = self.DocumentHardRules.get("minor")
                firstp = self.DocumentHardRules.get("first_person")

                rel_hit = bool(rel and rel.search(text_norm))
                kin_hit = bool(kin and kin.search(text_norm))
                if rel_hit and kin_hit:
                    scores["representative"] += 100
                    evidence.append("rule:relationship+kin")
                if minor and minor.search(text_norm):
                    scores["representative"] += 50
                    evidence.append("rule:minor/unable_to_sign")
                if scores.get("representative", 0) == 0 and firstp and (firstp.search(text_norm)):
                    scores["patient"] += 30
                    evidence.append("rule:first_person_authorize")

                # Labels across doc
                for r in RolesFromLabels(text_norm, self.RoleLabelPatterns):
                    scores[r] += self.WeightConfiguration["page_label"]
                    evidence.append(f"page_label:{r}")

                # General — ignore weak attorney in pseudo
                for r in RolesFromGeneral(text_norm, self.GeneralRolePatterns):
                    if r == "attorney":
                        continue
                    scores[r] += self.WeightConfiguration["general"]
                    evidence.append(f"general:{r}")

                # Boost from acro field names, if any
                for fname, _pg, _hk in acro_sig_list:
                    for r in self._RolesFromField(fname):
                        scores[r] += self.WeightConfiguration["field"]
                        evidence.append(f"field:{r}")

                role = ChooseRole(scores)
                if role == "unknown":
                    if rel_hit and kin_hit:
                        role = "representative"
                        evidence.append("tie:relationship+kin")
                    elif firstp and firstp.search(text_norm):
                        role = "patient"
                        evidence.append("tie:first_person")

                signatures.append(
                    Signature(
                        Page=None,
                        FieldName="vendor_or_acro_detected",
                        Role=role,
                        Score=sum(scores.values()),
                        Scores=dict(scores),
                        Evidence=evidence + ["pseudo:true"],
                        Hint="VendorOrAcroOnly",
                        RenderType="typed",
                    )
                )

        # doc-level hints
        acro_names = {name for name, _pg, _hk in acro_sig_list if name}
        esign_found = (len(signatures) > 0) or (len(vendor_hints) > 0) or (len(acro_names) > 0)
        mixed = esign_found and scanned_pdf

        doc_roles: set[str] = {s.Role for s in signatures if s.Role != "unknown"}

        hints: set[str] = set()
        hints |= {f"AcroSig:{n}" for n in acro_names}
        hints |= set(vendor_hints)
        hints |= {s.Hint for s in signatures}

        return FileResult(
            File=pdf_path.name,
            SizeKilobytes=size_kb,
            PageCount=pages,
            ElectronicSignatureFound=esign_found,
            ScannedPdf=scanned_pdf,
            MixedContent=mixed,
            SignatureCount=len(signatures),
            SignaturePages=",".join(
                map(str, sorted({signature.Page for signature in signatures if signature.Page}))
            ),
            Roles=";".join(sorted(doc_roles)) if doc_roles else "unknown",
            Hints=";".join(sorted(hints)),
            Signatures=signatures,
        )
