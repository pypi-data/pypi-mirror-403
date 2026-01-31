from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

from sigdetect.config import DetectConfiguration
from sigdetect.detector.pypdf2_engine import PyPDF2Detector


def test_widget_fieldname_patient_role(tmp_path: Path):
    pdf = tmp_path / "widget_patient.pdf"
    w = PdfWriter()
    page = w.add_blank_page(400, 400)

    # 1) Create the field (FT/Sig, T = "sig_patient"), add it as an indirect object
    field = DictionaryObject()
    field.update(
        {
            NameObject("/FT"): NameObject("/Sig"),
            NameObject("/T"): TextStringObject("sig_patient"),
        }
    )
    field_ref = w._add_object(field)

    # 2) Create the widget annotation, point /Parent back to the field
    widget = DictionaryObject()
    widget.update(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/Rect"): ArrayObject(
                [
                    NumberObject(10),
                    NumberObject(10),
                    NumberObject(150),
                    NumberObject(40),
                ]
            ),
            NameObject("/Parent"): field_ref,  # crucial for name lookup up the tree
        }
    )
    widget_ref = w._add_object(widget)

    # 3) Wire the field’s /Kids to include the widget
    field.update({NameObject("/Kids"): ArrayObject([widget_ref])})

    # 4) Put widget on the page and field into /AcroForm
    page[NameObject("/Annots")] = ArrayObject([widget_ref])
    acro = DictionaryObject()
    acro.update({NameObject("/Fields"): ArrayObject([field_ref])})
    w._root_object.update({NameObject("/AcroForm"): acro})

    # Write file
    with open(pdf, "wb") as f:
        w.write(f)

    # Detect
    cfg = DetectConfiguration(pdf_root=tmp_path, out_dir=tmp_path, engine="pypdf2")
    res = PyPDF2Detector(cfg).Detect(pdf)

    assert res.ElectronicSignatureFound is True
    assert res.SignatureCount >= 1
    roles = [s.Role for s in res.Signatures]
    assert "patient" in roles  # "/T" == "sig_patient" should drive role inference
    bbox = res.Signatures[0].BoundingBox
    assert bbox == (10.0, 10.0, 150.0, 40.0)
